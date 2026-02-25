"""
core/slices/types.py - Canonical slice types for MR kernels
Guarantees shape, no guessing
"""
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple

Vec3 = Tuple[float, float, float]

@dataclass(frozen=True)
class EntityKViewV1:
    """Kernel view of single entity - guaranteed fields"""
    eid: str
    pos: Vec3
    vel: Vec3
    rot: Vec3 = (0.0, 0.0, 0.0)
    health: float = 100.0
    max_health: float = 100.0
    flags: Dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class SpatialSliceV1:
    """Spatial kernel input - self + nearby entities"""
    tick: float
    self: EntityKViewV1
    nearby: Tuple[EntityKViewV1, ...] = ()
    world: Dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class PerceptionSliceV1:
    """Perception kernel input"""
    tick: float
    self: EntityKViewV1
    visible_entities: Tuple[str, ...] = ()
    focus_target: Optional[str] = None
    stimuli: Dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class BehaviorSliceV1:
    """Behavior kernel input"""
    tick: float
    self: EntityKViewV1
    perception: Dict[str, Any] = field(default_factory=dict)
    spatial: Dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class NavigationSliceV1:
    """Navigation kernel input - self + goal + nav grid"""
    tick: float
    self: EntityKViewV1
    goal: Optional[Vec3] = None
    nav_grid: Dict[str, Any] = field(default_factory=dict)
    world: Dict[str, Any] = field(default_factory=dict)
