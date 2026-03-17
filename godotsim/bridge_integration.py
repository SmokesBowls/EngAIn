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


# === COORD-CONVERT v1 (Godot->UPBGE) ===
def _godot_to_upbge_pos(pos):
    """Convert Godot 3D position to UPBGE/Blender coords.

    Godot (common usage): x right, y up, z depth (forward is -z)
    UPBGE/Blender:        x right, y forward, z up

    Mapping:
      x' =  x
      y' = -z
      z' =  y
    """
    if not isinstance(pos, dict):
        return {"x": 0.0, "y": 0.0, "z": 0.0}
    x = float(pos.get("x", 0.0))
    y = float(pos.get("y", 0.0))
    z = float(pos.get("z", 0.0))
    return {"x": round(x, 4), "y": round(-z, 4), "z": round(y, 4)}


def _godot_to_upbge_scale(scale):
    """Convert axis-aligned scale from Godot to UPBGE/Blender axes."""
    if not isinstance(scale, dict):
        return {"x": 1.0, "y": 1.0, "z": 1.0}
    sx = float(scale.get("x", 1.0))
    sy = float(scale.get("y", 1.0))
    sz = float(scale.get("z", 1.0))
    # x->x, y(up)->z, z(depth)->y (sign irrelevant for scale)
    return {"x": round(sx, 4), "y": round(sz, 4), "z": round(sy, 4)}


def _godot_to_upbge_transform(transform):
    """Convert a Godot-style transform dict to UPBGE/Blender axes.

    Note: rotation conversion is NOT applied here (kept as-is) because
    proper handedness + basis conversion depends on your consumer.
    """
    if not isinstance(transform, dict):
        transform = {}
    pos_g = transform.get("position") or {"x": 0.0, "y": 0.0, "z": 0.0}
    rot = transform.get("rotation") or {"x": 0, "y": 0, "z": 0}
    scl_g = transform.get("scale") or {"x": 1.0, "y": 1.0, "z": 1.0}
    return {
        "position": _godot_to_upbge_pos(pos_g),
        "rotation": rot,
        "scale": _godot_to_upbge_scale(scl_g),
    }
# === END COORD-CONVERT v1 ===


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

        eid = str(ent.get("@id") or ent.get("id") or ent.get("entity_id") or ent.get("name") or f"entity_{i}")
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
                godot_pos = (result.get("transform") or {}).get("position") or {"x": 0.0, "y": 0.0, "z": 0.0}
                result["position_godot"] = godot_pos
                result["position"] = _godot_to_upbge_pos(godot_pos)
                result["transform_upbge"] = _godot_to_upbge_transform(result.get("transform") or {})

                result["entity_id"] = eid
                result["name"] = str(ent.get("name") or eid)
                result["inferred_type"] = concept_type
                
                # Forward mechanics-first metadata
                result["presence"] = ent.get("presence", "visible")
                result["importance"] = ent.get("importance", 50)
                result["behavior"] = ent.get("behavior")
                result["behavior_params"] = ent.get("behavior_params", {})
                result["dialogue"] = ent.get("dialogue", {})
                
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
    """Produce minimal render data when the bridge isn't available.

    Output conventions:
      - "transform" is Godot-space (for Godot renderer).
      - "position" is UPBGE/Blender-space (for UPBGE spawners).
      - "position_godot" preserves the original Godot position.
      - "transform_upbge" provides a converted transform for UPBGE/Blender.
    """
    pos = _auto_layout_position(index, total)

    out = {
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
        # position is overwritten below to be UPBGE/Blender-space
        "position": pos,
        "collision_role": "solid",
        "semantic_tags": ["fallback"],
        "is_placeholder": True,
        "source_data": {"raw_concept": concept_type},
        
        # Forward mechanics-first metadata
        "presence": ent.get("presence", "visible"),
        "importance": ent.get("importance", 50),
        "behavior": ent.get("behavior"),
        "behavior_params": ent.get("behavior_params", {}),
        "dialogue": ent.get("dialogue", {}),
    }

    # Export UPBGE-friendly coordinates without breaking Godot consumers.
    out["position_godot"] = out["transform"]["position"]
    out["position"] = _godot_to_upbge_pos(out["transform"]["position"])
    out["transform_upbge"] = _godot_to_upbge_transform(out["transform"])
    return out


