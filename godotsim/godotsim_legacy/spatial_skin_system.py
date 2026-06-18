#!/usr/bin/env python3
"""spatial_skin_system.py — 3D entity data models for EngAIn semantic bridge.

Defines the output types that the semantic bridge produces.
These are pure data containers — no Godot, no rendering, no side effects.
Godot reads the serialized form via HTTP and spawns the actual nodes.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class ColorRGB:
    """Linear RGB color (0.0–1.0 per channel)."""
    r: float = 1.0
    g: float = 1.0
    b: float = 1.0

    def to_dict(self) -> Dict[str, float]:
        return {"r": self.r, "g": self.g, "b": self.b}

    def to_hex(self) -> str:
        return "#{:02x}{:02x}{:02x}".format(
            int(self.r * 255), int(self.g * 255), int(self.b * 255)
        )


@dataclass
class Transform3D:
    """Position, rotation, scale in 3D space."""
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    rotation: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    scale: Tuple[float, float, float] = (1.0, 1.0, 1.0)

    @classmethod
    def from_data(cls, position=None, rotation=None, scale=None) -> 'Transform3D':
        """Flexible constructor: accepts tuples, lists, dicts, or None."""
        def _to_tuple(val, default=(0.0, 0.0, 0.0)):
            if val is None:
                return default
            if isinstance(val, (list, tuple)):
                return tuple(float(v) for v in val[:3])
            if isinstance(val, dict):
                return (float(val.get("x", 0)), float(val.get("y", 0)), float(val.get("z", 0)))
            return default

        return cls(
            position=_to_tuple(position, (0.0, 0.0, 0.0)),
            rotation=_to_tuple(rotation, (0.0, 0.0, 0.0)),
            scale=_to_tuple(scale, (1.0, 1.0, 1.0)),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "position": {"x": self.position[0], "y": self.position[1], "z": self.position[2]},
            "rotation": {"x": self.rotation[0], "y": self.rotation[1], "z": self.rotation[2]},
            "scale": {"x": self.scale[0], "y": self.scale[1], "z": self.scale[2]},
        }


@dataclass
class Entity3D:
    """
    A fully-resolved 3D entity ready for Godot rendering.
    
    Created by the semantic bridge from ZON entity data.
    Godot reads the serialized form and spawns the appropriate node.
    """
    # Semantic identity
    zw_concept: str = "unknown"
    ap_profile: str = "generic_static"
    entity_id: Optional[str] = None

    # Kernel bindings (which AP rules apply)
    kernel_bindings: Dict[str, str] = field(default_factory=dict)

    # Visual representation
    placeholder_mesh: str = "cube"          # "capsule", "cube", "cylinder", "plane", "sphere"
    skin_3d_id: Optional[str] = None        # Trixel mesh hash if available
    color: ColorRGB = field(default_factory=lambda: ColorRGB(1.0, 0.0, 1.0))

    # Spatial
    transform: Transform3D = field(default_factory=Transform3D)
    collision_role: str = "solid"           # "solid", "trigger", "none"

    # Metadata
    semantic_tags: List[str] = field(default_factory=list)
    source_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for HTTP transport to Godot."""
        return {
            "entity_id": self.entity_id,
            "zw_concept": self.zw_concept,
            "ap_profile": self.ap_profile,
            "placeholder_mesh": self.placeholder_mesh,
            "skin_3d_id": self.skin_3d_id,
            "color": self.color.to_dict(),
            "color_hex": self.color.to_hex(),
            "transform": self.transform.to_dict(),
            "collision_role": self.collision_role,
            "semantic_tags": self.semantic_tags,
            "kernel_bindings": self.kernel_bindings,
            "is_placeholder": self.skin_3d_id is None,
            "source_data": self.source_data,
        }
