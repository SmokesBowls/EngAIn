#!/usr/bin/env python3
"""bridge_integration.py — Wires semantic_bridge.py into the EngAIn runtime.

Called by SceneManager after entity extraction.
Resolves each entity through the SemanticRegistry → ConceptProfile → Entity3D.
Writes serialized render data to runtime.snapshot["bridge_entities"] for Godot.

Usage in scene_manager.py:
    from bridge_integration import bridge_entities_for_scene
    ...
    self.runtime.snapshot["bridge_entities"] = bridge_entities_for_scene(scene_doc, entity_cards)
"""

import os
import json
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional

# ── Import the bridge (graceful if missing) ──────────────────────
try:
    from semantic_bridge import SemanticRegistry, zon_to_entity3d
    _HAS_BRIDGE = True
except ImportError as e:
    _HAS_BRIDGE = False
    print(f"[BRIDGE] semantic_bridge not available: {e}")

# ── Locate config ────────────────────────────────────────────────
_THIS_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
_DEFAULT_CONFIG = _THIS_DIR / "concept_profiles.json"

# ── Singleton registry ───────────────────────────────────────────
_registry: Optional['SemanticRegistry'] = None


def _get_registry() -> Optional['SemanticRegistry']:
    """Lazy-init the semantic registry from concept_profiles.json."""
    global _registry
    if _registry is not None:
        return _registry

    if not _HAS_BRIDGE:
        return None

    config_path = _DEFAULT_CONFIG
    if not config_path.exists():
        # Try parent dir
        config_path = _THIS_DIR.parent / "concept_profiles.json"
    if not config_path.exists():
        print(f"[BRIDGE] concept_profiles.json not found at {_DEFAULT_CONFIG}")
        return None

    try:
        _registry = SemanticRegistry()
        _registry.load_concepts_from_config(config_path)

        # Try to index any available trixel skins
        skin_dir = _THIS_DIR / "skins"
        if skin_dir.exists():
            _registry.index_available_skins(skin_dir)

        concept_count = len(_registry.concepts)
        print(f"[BRIDGE] Loaded {concept_count} concept profiles from {config_path.name}")
        return _registry
    except Exception as e:
        print(f"[BRIDGE] Failed to load registry: {e}")
        traceback.print_exc()
        return None


def _infer_entity_type(entity: Dict[str, Any]) -> str:
    """
    Infer the best concept type from a ZONJ entity dict.
    Checks: type, concept, role, @type, name (for known patterns).
    """
    # Explicit type
    for key in ("type", "concept", "@type", "role"):
        val = entity.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip().lower()

    # Infer from name
    name = str(entity.get("name") or entity.get("@id") or entity.get("id") or "").lower()

    # Known character names from the books
    known_characters = {
        "senareth", "vairis", "elyraen", "kyreth", "torhh",
        "keen", "caelum", "isla", "trae", "mrlore",
    }
    if name in known_characters:
        return "character"

    # Known faction/species patterns
    if any(w in name for w in ("neferati", "nefari")):
        return "neferati"
    if any(w in name for w in ("nephilim", "nephi")):
        return "nephilim"
    if any(w in name for w in ("giant",)):
        return "giant"

    return "character"  # Safe default for entities in a narrative


def _auto_layout_position(index: int, total: int) -> Dict[str, float]:
    """
    Generate a grid layout for entities so they don't stack on (0,0,0).
    Grid allows for many entities to be visible at once.
    """
    if total <= 1:
        return {"x": 0.0, "y": 0.0, "z": 0.0}

    # Grid: 5 per row, 3m spacing
    x = (index % 5) * 3.0 - 6.0
    y = 0.0
    z = (index // 5) * -3.0
    
    return {"x": round(x, 2), "y": round(y, 2), "z": round(z, 2)}


def bridge_entities_for_scene(
    scene_doc: Optional[Dict[str, Any]],
    entity_cards: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Resolve all entities in a scene through the semantic bridge.

    Returns a list of serialized Entity3D dicts ready for Godot.
    Each dict contains: entity_id, placeholder_mesh, color, transform, ap_profile, etc.

    If the bridge isn't available, returns a fallback list with basic data.
    """
    if not scene_doc:
        return []

    # Collect entities from scene doc
    raw_entities = scene_doc.get("entities", [])
    if isinstance(raw_entities, dict):
        raw_entities = list(raw_entities.values())
    if not raw_entities:
        raw_entities = scene_doc.get("@entities", [])

    if not raw_entities:
        return []

    registry = _get_registry()
    results = []

    for i, ent in enumerate(raw_entities):
        if isinstance(ent, str):
            # Entity is just a name string
            ent = {"name": ent, "id": ent}
        if not isinstance(ent, dict):
            continue

        eid = str(ent.get("@id") or ent.get("id") or ent.get("name") or f"entity_{i}")
        concept_type = _infer_entity_type(ent)

        if registry and _HAS_BRIDGE:
            # Full bridge resolution
            try:
                zon_entity = {
                    "id": eid,
                    "type": concept_type,
                    "position": _auto_layout_position(i, len(raw_entities)),
                }
                entity3d = zon_to_entity3d(zon_entity, registry)
                result = entity3d.to_dict()
                # Expose position at top level for UPBGE/legacy bridge compatibility
                result["position"] = result["transform"]["position"]
                result["entity_id"] = eid
                result["name"] = str(ent.get("name") or eid)
                result["inferred_type"] = concept_type
                results.append(result)
            except Exception as e:
                print(f"[BRIDGE] Failed to resolve '{eid}': {e}")
                results.append(_fallback_entity(eid, ent, concept_type, i, len(raw_entities)))
        else:
            # No bridge available — produce basic fallback data
            results.append(_fallback_entity(eid, ent, concept_type, i, len(raw_entities)))

    if results:
        print(f"[BRIDGE] Resolved {len(results)} entities for Godot rendering")

    return results


def _fallback_entity(eid: str, ent: Dict, concept_type: str, index: int, total: int) -> Dict[str, Any]:
    """Produce minimal render data when the bridge isn't available."""
    pos = _auto_layout_position(index, total)
    return {
        "entity_id": eid,
        "name": str(ent.get("name") or eid),
        "zw_concept": concept_type,
        "inferred_type": concept_type,
        "ap_profile": "generic_static",
        "placeholder_mesh": "capsule",
        "skin_3d_id": None,
        "color": {"r": 1.0, "g": 0.0, "b": 1.0},
        "color_hex": "#ff00ff",
        "transform": {
            "position": pos,
            "rotation": {"x": 0, "y": 0, "z": 0},
            "scale": {"x": 0.5, "y": 1.8, "z": 0.5},
        },
        "position": pos,  # Top-level for UPBGE compatibility
        "collision_role": "solid",
        "semantic_tags": ["fallback"],
        "is_placeholder": True,
        "source_data": {"raw_concept": concept_type},
    }
