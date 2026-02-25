"""
core/slices/builders.py - ONE PLACE to read raw snapshot dicts
All validation/normalization happens here, never in kernels

CONTAMINATION GUARD: This module is the ONLY place allowed to read raw snapshot dicts.
MR kernels MUST receive typed slices. Any violation is a critical architecture bug.
"""
from typing import Any, Dict, Iterable, Optional, Tuple
from slice_types import EntityKViewV1, SpatialSliceV1, PerceptionSliceV1, BehaviorSliceV1, NavigationSliceV1, Vec3

class SliceError(ValueError):
    """Raised when snapshot doesn't match contract"""
    pass

class ContaminationError(RuntimeError):
    """Raised when raw snapshot dict reaches MR kernel (architecture violation)"""
    pass

def assert_no_raw_dict_contamination(value: Any, context: str):
    """
    ENFORCEMENT: Detect if a raw snapshot dict leaked into MR kernel.
    
    MR kernels should ONLY receive typed slices (dataclasses).
    If a plain dict reaches the kernel, the slice protection layer was bypassed.
    
    This is a CRITICAL architectural violation.
    """
    if isinstance(value, dict):
        # Check if it looks like a raw snapshot (has entities/world/etc)
        snapshot_keys = {"entities", "world", "spatial", "perception", "behavior"}
        if any(key in value for key in snapshot_keys):
            raise ContaminationError(
                f"RAW SNAPSHOT DICT reached {context}! "
                f"This is an architecture violation. "
                f"MR kernels must receive typed slices, not raw dicts. "
                f"Keys found: {list(value.keys())}"
            )
    
    # Also check if it's a plain dict when it should be a dataclass
    if isinstance(value, dict) and not hasattr(value, '__dataclass_fields__'):
        # Could be a legitimate dict field (like flags), so just warn
        pass  # Allow for now, but could be stricter

def _as_vec3(value: Any, *, field: str, eid: str) -> Vec3:
    """Convert to Vec3 or raise SliceError"""
    if value is None:
        return (0.0, 0.0, 0.0)
    
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise SliceError(f"{field} invalid for {eid}: expected len-3 list/tuple, got {type(value)}")
    
    try:
        return (float(value[0]), float(value[1]), float(value[2]))
    except (ValueError, TypeError) as e:
        raise SliceError(f"{field} non-numeric for {eid}: {value}") from e

def build_entity_kview_v1(
    world: Dict[str, Any], 
    eid: str, 
    *, 
    normalize_missing_vel: bool = True
) -> EntityKViewV1:
    """
    Build guaranteed EntityKViewV1 from raw snapshot.
    This is the ONLY place allowed to read world["entities"][eid]
    """
    entities = world.get("entities")
    if not isinstance(entities, dict):
        raise SliceError(f"world.entities missing or not dict")
    
    if eid not in entities:
        raise SliceError(f"entity {eid} not found in snapshot")
    
    e = entities[eid]
    if not isinstance(e, dict):
        raise SliceError(f"entity {eid} is not dict")
    
    # Position - REQUIRED
    pos_raw = e.get("pos") or e.get("position")
    if pos_raw is None:
        raise SliceError(f"position missing for {eid}")
    pos = _as_vec3(pos_raw, field="position", eid=eid)
    
    # Velocity - normalize to (0,0,0) if missing
    vel_raw = e.get("vel") or e.get("velocity")
    if vel_raw is None:
        if normalize_missing_vel:
            vel = (0.0, 0.0, 0.0)
        else:
            raise SliceError(f"velocity missing for {eid}")
    else:
        vel = _as_vec3(vel_raw, field="velocity", eid=eid)
    
    # Rotation - optional
    rot_raw = e.get("rot") or e.get("rotation")
    rot = _as_vec3(rot_raw, field="rotation", eid=eid) if rot_raw else (0.0, 0.0, 0.0)
    
    # Health
    health = float(e.get("health", 100.0))
    max_health = float(e.get("max_health", 100.0))
    
    # Flags - optional metadata
    flags = e.get("flags", {})
    if not isinstance(flags, dict):
        flags = {}
    
    return EntityKViewV1(
        eid=eid,
        pos=pos,
        vel=vel,
        rot=rot,
        health=health,
        max_health=max_health,
        flags=flags
    )

def build_spatial_slice_v1(
    world: Dict[str, Any],
    tick: float,
    eid: str,
    *,
    nearby_eids: Optional[Iterable[str]] = None
) -> SpatialSliceV1:
    """Build spatial slice for one entity"""
    self_view = build_entity_kview_v1(world, eid)
    
    nearby = ()
    if nearby_eids:
        nearby = tuple(build_entity_kview_v1(world, nid) for nid in nearby_eids)
    
    world_meta = world.get("spatial", {})
    if not isinstance(world_meta, dict):
        world_meta = {}
    
    return SpatialSliceV1(
        tick=tick,
        self=self_view,
        nearby=nearby,
        world=world_meta
    )

def build_perception_slice_v1(
    world: Dict[str, Any],
    tick: float,
    eid: str
) -> PerceptionSliceV1:
    """Build perception slice for one entity"""
    self_view = build_entity_kview_v1(world, eid)
    
    perception_data = world.get("perception", {})
    if not isinstance(perception_data, dict):
        perception_data = {}
    
    entity_perception = perception_data.get(eid, {})
    if not isinstance(entity_perception, dict):
        entity_perception = {}
    
    visible = entity_perception.get("visible_entities", [])
    if not isinstance(visible, (list, tuple)):
        visible = []
    
    focus = entity_perception.get("focus_target")
    
    return PerceptionSliceV1(
        tick=tick,
        self=self_view,
        visible_entities=tuple(visible),
        focus_target=focus,
        stimuli=entity_perception
    )

def build_behavior_slice_v1(
    world: Dict[str, Any],
    tick: float,
    eid: str
) -> BehaviorSliceV1:
    """Build behavior slice for one entity"""
    self_view = build_entity_kview_v1(world, eid)
    
    perception_data = world.get("perception", {}).get(eid, {})
    if not isinstance(perception_data, dict):
        perception_data = {}
    
    spatial_data = world.get("spatial", {})
    if not isinstance(spatial_data, dict):
        spatial_data = {}
    
    return BehaviorSliceV1(
        tick=tick,
        self=self_view,
        perception=perception_data,
        spatial=spatial_data
    )

def build_nav_slice_v1(
    world: Dict[str, Any],
    tick: float,
    eid: str,
    *,
    goal: Optional[Vec3] = None
) -> NavigationSliceV1:
    """
    Build navigation slice for one entity.
    Guarantees position/velocity exist, normalizes goal.
    """
    self_view = build_entity_kview_v1(world, eid)
    
    # Extract nav grid if present
    nav_data = world.get("spatial", {})
    if not isinstance(nav_data, dict):
        nav_data = {}
    
    nav_grid = nav_data.get("navigation", {})
    if not isinstance(nav_grid, dict):
        nav_grid = {}
    
    world_meta = world.get("world", {})
    if not isinstance(world_meta, dict):
        world_meta = {}
    
    return NavigationSliceV1(
        tick=tick,
        self=self_view,
        goal=goal,
        nav_grid=nav_grid,
        world=world_meta
    )
