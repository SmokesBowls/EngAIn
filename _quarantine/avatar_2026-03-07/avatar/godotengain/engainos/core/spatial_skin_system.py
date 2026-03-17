"""
spatial_skin_system.py - Engine-Agnostic Spatial Skin System

Separates game logic (placeholder meshes) from visual art (skins).

Philosophy:
- Placeholder mesh = the REAL game object (collision, logic, AP)
- Art skins = optional visual overlays (2D sprites, 3D models)
- Renderer decides priority: 3D skin > 2D skin > colored placeholder

This is pure Python - no Godot/Blender/engine dependencies.
The renderer (Godot, etc.) consumes RenderPlan and creates actual nodes.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Literal, List

# Placeholder mesh types (canonical game objects)
PlaceholderMesh = Literal["cube", "capsule", "cylinder", "plane", "sphere"]


@dataclass
class Transform3D:
    """3D transform (position, rotation, scale)"""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    rx: float = 0.0  # Rotation X (radians)
    ry: float = 0.0  # Rotation Y (radians)
    rz: float = 0.0  # Rotation Z (radians)
    sx: float = 1.0  # Scale X
    sy: float = 1.0  # Scale Y
    sz: float = 1.0  # Scale Z
    
    @classmethod
    def from_data(cls, position=(0,0,0), rotation=(0,0,0), scale=(1,1,1)):
        """Create from tuples/lists (like the ones from ZON or YAML)"""
        return cls(
            x=position[0], y=position[1], z=position[2],
            rx=rotation[0], ry=rotation[1], rz=rotation[2],
            sx=scale[0], sy=scale[1], sz=scale[2]
        )

    def to_dict(self) -> dict:
        """Export for serialization (nested structure)"""
        return {
            "position": {"x": float(self.x), "y": float(self.y), "z": float(self.z)},
            "rotation": {"x": float(self.rx), "y": float(self.ry), "z": float(self.rz)},
            "scale": {"x": float(self.sx), "y": float(self.sy), "z": float(self.sz)},
        }


@dataclass
class ColorRGB:
    """RGB color (0.0 to 1.0 range)"""
    r: float = 1.0
    g: float = 1.0
    b: float = 1.0
    
    def to_hex(self) -> str:
        """Convert to hex string for debugging"""
        r = int(self.r * 255)
        g = int(self.g * 255)
        b = int(self.b * 255)
        return f"#{r:02x}{g:02x}{b:02x}"


@dataclass
class Entity3D:
    """
    3D entity with logic and optional art.
    """
    # LOGIC (required)
    zw_concept: str                      # e.g., "guard", "merchant", "door"
    ap_profile: str                      # e.g., "damageable_npc", "interactable"
    kernel_bindings: Dict[str, Any]      # Bindings for combat, physics, etc.
    placeholder_mesh: PlaceholderMesh    # The canonical game object (cube, capsule, etc.)
    transform: Transform3D
    
    # Semantic Bridge
    collision_role: str = "solid"        # "solid", "trigger", "none"
    semantic_tags: List[str] = field(default_factory=list)
    source_data: Dict[str, Any] = field(default_factory=dict)
    
    # ART (optional)
    skin_2d_id: Optional[str] = None     # Reference to sprite asset
    skin_3d_id: Optional[str] = None     # Reference to 3D model asset
    color: ColorRGB = field(default_factory=ColorRGB)  # Fallback color
    
    # Metadata
    entity_id: Optional[str] = None      # Unique identifier
    tags: List[str] = field(default_factory=list)  # Legacy/additional tags


@dataclass
class RenderPlan:
    """
    Engine-agnostic render instructions for one entity.
    
    A client (Godot, Unity, etc.) turns this into actual scene nodes.
    
    Priority chain:
    1. Create placeholder mesh (REQUIRED - this is the game object)
    2. If skin_3d_id exists → overlay 3D model (visual only)
    3. Else if skin_2d_id exists → billboard sprite
    4. Else → use color tint on placeholder
    """
    mesh_type: PlaceholderMesh           # The canonical game object
    transform: Transform3D               # Where to place it
    color: ColorRGB                      # Fallback visual
    
    # Art overlays (optional)
    skin_3d_id: Optional[str]            # 3D model to overlay
    skin_2d_id: Optional[str]            # 2D sprite to billboard
    
    # Logic metadata (for engine to attach)
    logic_tags: Dict[str, Any]           # ZW concept, AP profile, etc.
    
    def has_3d_art(self) -> bool:
        """Check if 3D art is available"""
        return self.skin_3d_id is not None
    
    def has_2d_art(self) -> bool:
        """Check if 2D art is available"""
        return self.skin_2d_id is not None
    
    def has_any_art(self) -> bool:
        """Check if any art is available"""
        return self.has_3d_art() or self.has_2d_art()
    
    def art_priority(self) -> str:
        """Return which art layer to use"""
        if self.has_3d_art():
            return "3d"
        elif self.has_2d_art():
            return "2d"
        else:
            return "placeholder"


def build_render_plan(entity: Entity3D) -> RenderPlan:
    """
    Build engine-agnostic render plan from entity.
    
    The placeholder mesh is ALWAYS present (it's the game object).
    Skins are purely visual hints for the renderer.
    
    Args:
        entity: Entity3D with logic and optional art
    
    Returns:
        RenderPlan that renderer can execute
    """
    logic_tags = {
        "zw_concept": entity.zw_concept,
        "ap_profile": entity.ap_profile,
        "kernel_bindings": entity.kernel_bindings,
        "entity_id": entity.entity_id,
        "tags": entity.tags,
    }
    
    return RenderPlan(
        mesh_type=entity.placeholder_mesh,
        transform=entity.transform,
        color=entity.color,
        skin_3d_id=entity.skin_3d_id,
        skin_2d_id=entity.skin_2d_id,
        logic_tags=logic_tags,
    )


def build_scene_render_plans(entities: List[Entity3D]) -> List[RenderPlan]:
    """
    Build render plans for entire scene.
    
    Args:
        entities: List of entities to render
    
    Returns:
        List of render plans in same order
    """
    return [build_render_plan(entity) for entity in entities]


# ================================================================
# ASSET REGISTRY (Optional Helper)
# ================================================================

class SkinRegistry:
    """
    Optional helper to track available art assets.
    
    Engines can use this to validate skin references or
    provide asset browsing/selection UI.
    """
    
    def __init__(self):
        self.skins_2d: Dict[str, str] = {}  # id -> file path
        self.skins_3d: Dict[str, str] = {}  # id -> file path
    
    def register_2d(self, skin_id: str, filepath: str):
        """Register 2D sprite asset"""
        self.skins_2d[skin_id] = filepath
    
    def register_3d(self, skin_id: str, filepath: str):
        """Register 3D model asset"""
        self.skins_3d[skin_id] = filepath
    
    def get_2d(self, skin_id: str) -> Optional[str]:
        """Get 2D sprite path"""
        return self.skins_2d.get(skin_id)
    
    def get_3d(self, skin_id: str) -> Optional[str]:
        """Get 3D model path"""
        return self.skins_3d.get(skin_id)
    
    def has_2d(self, skin_id: str) -> bool:
        """Check if 2D sprite exists"""
        return skin_id in self.skins_2d
    
    def has_3d(self, skin_id: str) -> bool:
        """Check if 3D model exists"""
        return skin_id in self.skins_3d


# Global registry instance (optional)
_global_registry = SkinRegistry()


def register_2d_skin(skin_id: str, filepath: str):
    """Register 2D skin in global registry"""
    _global_registry.register_2d(skin_id, filepath)


def register_3d_skin(skin_id: str, filepath: str):
    """Register 3D skin in global registry"""
    _global_registry.register_3d(skin_id, filepath)


def get_skin_registry() -> SkinRegistry:
    """Get global skin registry"""
    return _global_registry
