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

import glob
import os
import json
import logging
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)

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
        "keen", "caelum", "isla",
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


def _coerce_position(value: Any, fallback: Any) -> Dict[str, float]:
    """Normalize dict/list position shapes into a Godot-style x/y/z dict."""
    if isinstance(value, dict):
        return {
            "x": float(value.get("x", 0.0)),
            "y": float(value.get("y", 0.0)),
            "z": float(value.get("z", 0.0)),
        }

    if isinstance(value, (list, tuple)) and len(value) >= 3:
        return {"x": float(value[0]), "y": float(value[1]), "z": float(value[2])}

    if isinstance(fallback, dict):
        return {
            "x": float(fallback.get("x", 0.0)),
            "y": float(fallback.get("y", 0.0)),
            "z": float(fallback.get("z", 0.0)),
        }

    if isinstance(fallback, (list, tuple)) and len(fallback) >= 3:
        return {"x": float(fallback[0]), "y": float(fallback[1]), "z": float(fallback[2])}

    return {"x": 0.0, "y": 0.0, "z": 0.0}


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


def _has_position(value: Any) -> bool:
    return isinstance(value, dict) or (isinstance(value, (list, tuple)) and len(value) >= 3)


def _is_origin_position(value: Any) -> bool:
    if isinstance(value, dict):
        return (
            float(value.get("x", 0.0)) == 0.0
            and float(value.get("y", 0.0)) == 0.0
            and float(value.get("z", 0.0)) == 0.0
        )
    if isinstance(value, (list, tuple)) and len(value) >= 3:
        return float(value[0]) == 0.0 and float(value[1]) == 0.0 and float(value[2]) == 0.0
    return False


def _resolve_position_with_source(ent: Dict[str, Any], index: int, total: int) -> tuple[Dict[str, float], str]:
    """Resolve bridge placement while preserving placement provenance."""
    source = str(ent.get("placement_source") or "").strip()

    if source == "spatial3d" and _has_position(ent.get("pos")):
        return _coerce_position(ent.get("pos"), None), "spatial3d"
    if source == "spawn_pos" and _has_position(ent.get("spawn_pos")):
        return _coerce_position(ent.get("spawn_pos"), None), "spawn_pos"
    if source == "spawn_pos" and _has_position(ent.get("pos")):
        return _coerce_position(ent.get("pos"), None), "spawn_pos"
    if source == "authored_pos" and _has_position(ent.get("position")):
        return _coerce_position(ent.get("position"), None), "authored_pos"
    if source == "authored_pos" and _has_position(ent.get("pos")):
        return _coerce_position(ent.get("pos"), None), "authored_pos"

    if source == "unplaced":
        return _auto_layout_position(index, total), "fallback_grid"

    if _has_position(ent.get("spawn_pos")):
        return _coerce_position(ent.get("spawn_pos"), None), "spawn_pos"
    if _has_position(ent.get("position")):
        return _coerce_position(ent.get("position"), None), "authored_pos"
    if _has_position(ent.get("pos")) and not _is_origin_position(ent.get("pos")):
        return _coerce_position(ent.get("pos"), None), "authored_pos"

    return _auto_layout_position(index, total), "fallback_grid"


def _load_event_actors(scene_id: str) -> Set[str]:
    """
    Find the matching out_events_<scene>.json and return the set of actor names
    that appear in its event list.  Never raises — returns empty set on any error.

    Search order:
      1. <EngAIn root>/mettaext/compiled/pipeline_work/out_events_<scene>.json
      2. Glob for out_events_*<scene>*.json anywhere under mettaext/
    """
    actors: Set[str] = set()
    if not scene_id:
        return actors

    print(f"[bridge] scene_id: {scene_id}")

    # Derive a slug: strip common prefixes/suffixes, lower-case for matching
    slug = scene_id.replace("/", "_").replace(" ", "_").lower()

    if slug.startswith("scene."):
        slug = slug[len("scene."):]
    if slug.startswith("scene_"):
        slug = slug[len("scene_"):]

    # Build candidate paths
    root = _THIS_DIR.parent / "mettaext"
    candidates: List[Path] = [
        root / "compiled" / "pipeline_work" / f"out_events_{slug}.json",
        root / "compiled" / "pipeline_work" / f"out_events_{scene_id}.json",
    ]

    # Glob fallback across mettaext subtree
    glob_pattern = str(root / "**" / f"out_events_*{slug}*.json")
    for match in glob.glob(glob_pattern, recursive=True):
        candidates.append(Path(match))

    for path in candidates:
        if not path.exists():
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            events = data.get("events", [])
            for evt in events:
                actor = evt.get("actor")
                if actor and isinstance(actor, str):
                    actors.add(actor)
            if actors:
                print(f"[BRIDGE] Loaded {len(actors)} event actors from {path.name}")
            print(f"[bridge] event actors: {sorted(actors)}")
            return actors
        except Exception as e:
            print(f"[BRIDGE] Could not read event file {path}: {e}")

    print(f"[bridge] event actors: {sorted(actors)}")
    return actors


def declared_entity_ids(scene_doc: dict) -> set[str]:
    ids: set[str] = set()

    for key in ("entities", "@entities"):
        items = scene_doc.get(key, [])
        if not isinstance(items, list):
            continue

        for item in items:
            if isinstance(item, str):
                entity_id = item.strip().lower()
                if entity_id:
                    ids.add(entity_id)
                continue

            if not isinstance(item, dict):
                continue

            raw_id = item.get("id") or item.get("entity_id") or item.get("@id")

            if raw_id is None:
                logger.warning(
                    "[BRIDGE_ENTITY_FILTER] malformed declared entity without id key=%s item=%r",
                    key,
                    item,
                )
                continue

            entity_id = str(raw_id).strip().lower()
            if entity_id:
                ids.add(entity_id)

    return ids


def declared_spawn_command_ids(scene_doc: dict) -> set[str]:
    ids: set[str] = set()

    commands = scene_doc.get("spawn_commands", [])
    if not isinstance(commands, list):
        return ids

    for cmd in commands:
        if not isinstance(cmd, dict):
            continue

        raw_id = cmd.get("id") or cmd.get("entity_id") or cmd.get("@id")
        if raw_id is None:
            logger.warning(
                "[BRIDGE_ENTITY_FILTER] malformed spawn_command without id: %r",
                cmd,
            )
            continue

        entity_id = str(raw_id).strip().lower()
        if entity_id:
            ids.add(entity_id)

    return ids


def filter_bridge_entities_by_declared_ids(
    scene_id: str,
    scene_doc: dict,
    bridge_entities: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    allowed_ids = declared_entity_ids(scene_doc)
    allowed_ids |= declared_spawn_command_ids(scene_doc)

    if not allowed_ids:
        logger.warning(
            "[BRIDGE_ENTITY_FILTER] scene_id=%s has no declared entities/spawn_commands — returning empty bridge list",
            scene_id,
        )
        return []

    filtered: list[dict] = []
    dropped: list[str] = []

    for entity in bridge_entities:
        if not isinstance(entity, dict):
            continue

        raw_id = entity.get("entity_id") or entity.get("id") or entity.get("@id")
        if raw_id is None:
            logger.warning(
                "[BRIDGE_ENTITY_FILTER] dropping bridge entity without id scene_id=%s entity=%r",
                scene_id,
                entity,
            )
            continue

        entity_id = str(raw_id).strip().lower()

        if entity_id not in allowed_ids:
            dropped.append(entity_id)
            continue

        filtered.append(entity)

    logger.info(
        "[BRIDGE_ENTITY_FILTER] scene_id=%s declared=%d before=%d after=%d dropped=%d dropped_ids=%s",
        scene_id,
        len(allowed_ids),
        len(bridge_entities),
        len(filtered),
        len(dropped),
        dropped[:40],
    )

    return filtered


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

    # ── 1. Collect strict declared semantic scene entities ──────────────────────
    raw_entities = scene_doc.get("entities", [])
    if not isinstance(raw_entities, list):
        raw_entities = []
    if not raw_entities:
        raw_entities = scene_doc.get("@entities", [])
        if not isinstance(raw_entities, list):
            raw_entities = []

    spawn_commands = scene_doc.get("spawn_commands", [])
    if isinstance(spawn_commands, list):
        raw_entities = list(raw_entities) + [cmd for cmd in spawn_commands if isinstance(cmd, dict)]

    # Normalize string entities into minimal dicts
    raw_entities = [
        {"@id": e, "id": e, "name": e} if isinstance(e, str) else e
        for e in raw_entities
    ]

    # ── 2. Observe event actors for diagnostics only; they are not identity authority.
    scene_id: str = str(
        scene_doc.get("scene_id")
        or scene_doc.get("@id")
        or scene_doc.get("id")
        or ""
    )
    print(f"[TRACE_SCENE030][BRIDGE_INTEGRATION_ENTER] scene_id={scene_id} raw_entities={len(raw_entities) if isinstance(raw_entities, list) else 0} entity_cards={len(entity_cards) if isinstance(entity_cards, dict) else 0}")
    event_actors = _load_event_actors(scene_id)

    # Build a set of already-known ids to avoid duplicates. Name is display text,
    # not identity authority, so it is intentionally excluded here.
    known_ids: Set[str] = set()
    for ent in raw_entities:
        if isinstance(ent, dict):
            eid = (
                ent.get("@id")
                or ent.get("id")
                or ent.get("entity_id")
            )
            if eid:
                known_ids.add(str(eid))

    if not raw_entities:
        return filter_bridge_entities_by_declared_ids(scene_id, scene_doc, [])


    registry = _get_registry()
    results = []

    for i, ent in enumerate(raw_entities):
        if not isinstance(ent, dict):
            continue

        raw_id = ent.get("@id") or ent.get("id") or ent.get("entity_id")
        if raw_id is None:
            logger.warning(
                "[BRIDGE_ENTITY_FILTER] skipping source entity without id scene_id=%s entity=%r",
                scene_id,
                ent,
            )
            continue

        eid = str(raw_id).strip()
        if not eid:
            logger.warning(
                "[BRIDGE_ENTITY_FILTER] skipping source entity with empty id scene_id=%s entity=%r",
                scene_id,
                ent,
            )
            continue

        concept_type = _infer_entity_type(ent)

        if registry and _HAS_BRIDGE:
            # Full bridge resolution
            try:
                zon_position, placement_source = _resolve_position_with_source(ent, i, len(raw_entities))
                zon_entity = {
                    "id": eid,
                    "type": concept_type,
                    "position": zon_position,
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
                result["placement_source"] = placement_source
                print(f"[BRIDGE_POSITION_AUDIT] entity={result['name']} source={placement_source} pos={godot_pos}")
                
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
    filtered_results = filter_bridge_entities_by_declared_ids(scene_id, scene_doc, results)
    print(f"[TRACE_SCENE030][BRIDGE_INTEGRATION_RETURN] scene_id={scene_id} results={len(filtered_results)} known_ids={len(known_ids)} event_actors={len(event_actors)}")

    return filtered_results


def _fallback_entity(eid: str, ent: Dict, concept_type: str, index: int, total: int) -> Dict[str, Any]:
    """Produce minimal render data when the bridge isn't available.

    Output conventions:
      - "transform" is Godot-space (for Godot renderer).
      - "position" is UPBGE/Blender-space (for UPBGE spawners).
      - "position_godot" preserves the original Godot position.
      - "transform_upbge" provides a converted transform for UPBGE/Blender.
    """
    pos, placement_source = _resolve_position_with_source(ent, index, total)
    name = str(ent.get("name") or eid)
    print(f"[BRIDGE_POSITION_AUDIT] entity={name} source={placement_source} pos={pos}")

    out = {
        "entity_id": eid,
        "name": name,
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
        "placement_source": placement_source,
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


