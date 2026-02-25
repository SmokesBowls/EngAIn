"""
zon_to_entities.py - ZON → Entity3D Wiring

Pure glue code that connects:
- ZON narrative extraction (GameScene)
- spatial_skin_system (Entity3D, Transform3D)
- mesh_manifest (TrixelManifest for skin_3d_id)

This is the bridge: Story → Playable Scene
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from spatial_skin_system import Entity3D, Transform3D, ColorRGB
from mesh_manifest import load_trixel_manifest


# ================================================================
# MAPPING RULES: ZON Concepts → Entity Properties
# ================================================================

@dataclass
class ConceptMapping:
    """Maps a ZW concept to Entity3D properties"""
    zw_concept: str
    ap_profile: str
    placeholder_mesh: str
    collision_role: str
    default_color: ColorRGB
    kernel_bindings: Dict[str, Any]


# Default mappings (can be extended)
CONCEPT_MAPPINGS: Dict[str, ConceptMapping] = {
    # Characters
    "guard": ConceptMapping(
        zw_concept="guard",
        ap_profile="damageable_npc",
        placeholder_mesh="capsule",
        collision_role="solid",
        default_color=ColorRGB(0.8, 0.2, 0.2),  # Red
        kernel_bindings={"combat": True, "faction": "Empire"}
    ),
    "merchant": ConceptMapping(
        zw_concept="merchant",
        ap_profile="interactable",
        placeholder_mesh="capsule",
        collision_role="solid",
        default_color=ColorRGB(0.2, 0.8, 0.2),  # Green
        kernel_bindings={"dialogue": True, "inventory": True}
    ),
    "player": ConceptMapping(
        zw_concept="player",
        ap_profile="player_character",
        placeholder_mesh="capsule",
        collision_role="solid",
        default_color=ColorRGB(0.2, 0.2, 0.8),  # Blue
        kernel_bindings={"combat": True, "inventory": True}
    ),
    
    # Props
    "door": ConceptMapping(
        zw_concept="door",
        ap_profile="destructible",
        placeholder_mesh="cube",
        collision_role="solid",
        default_color=ColorRGB(0.6, 0.4, 0.2),  # Brown
        kernel_bindings={"physics": True}
    ),
    "chest": ConceptMapping(
        zw_concept="chest",
        ap_profile="interactable",
        placeholder_mesh="cube",
        collision_role="solid",
        default_color=ColorRGB(0.7, 0.5, 0.2),  # Golden
        kernel_bindings={"inventory": True}
    ),
    "barrel": ConceptMapping(
        zw_concept="barrel",
        ap_profile="destructible",
        placeholder_mesh="cylinder",
        collision_role="solid",
        default_color=ColorRGB(0.5, 0.3, 0.1),  # Dark brown
        kernel_bindings={"physics": True}
    ),
    
    # Environment
    "tower": ConceptMapping(
        zw_concept="tower",
        ap_profile="structure",
        placeholder_mesh="cylinder",
        collision_role="static",
        default_color=ColorRGB(0.6, 0.6, 0.6),  # Gray
        kernel_bindings={}
    ),
    "wall": ConceptMapping(
        zw_concept="wall",
        ap_profile="structure",
        placeholder_mesh="cube",
        collision_role="static",
        default_color=ColorRGB(0.5, 0.5, 0.5),  # Gray
        kernel_bindings={}
    ),
    
    # Generic fallback
    "unknown": ConceptMapping(
        zw_concept="unknown",
        ap_profile="generic",
        placeholder_mesh="cube",
        collision_role="solid",
        default_color=ColorRGB(1.0, 0.0, 1.0),  # Magenta (error color)
        kernel_bindings={}
    )
}


def get_concept_mapping(concept: str) -> ConceptMapping:
    """
    Get mapping for a ZW concept.
    
    Args:
        concept: ZW concept string (e.g., "guard", "door")
    
    Returns:
        ConceptMapping with defaults for this concept
    """
    # Normalize concept (lowercase, strip whitespace)
    concept = concept.lower().strip()
    
    # Check for exact match
    if concept in CONCEPT_MAPPINGS:
        return CONCEPT_MAPPINGS[concept]
    
    # Check for partial matches (e.g., "tower_guard" → "guard")
    for known_concept, mapping in CONCEPT_MAPPINGS.items():
        if known_concept in concept:
            return mapping
    
    # Fallback to unknown
    return CONCEPT_MAPPINGS["unknown"]


def register_concept_mapping(mapping: ConceptMapping):
    """
    Register a new concept mapping (for user-defined concepts).
    
    Args:
        mapping: ConceptMapping to register
    """
    CONCEPT_MAPPINGS[mapping.zw_concept] = mapping


# ================================================================
# ZON → Entity3D Conversion
# ================================================================

def zon_entity_to_entity3d(
    zon_entity: Dict[str, Any],
    *,
    trixel_search_paths: Optional[List[Path]] = None,
    auto_bind_skins: bool = True
) -> Entity3D:
    """
    Convert a single ZON entity to Entity3D.
    
    Args:
        zon_entity: ZON entity dict with keys like:
            - type: ZW concept (e.g., "guard")
            - position: [x, y, z]
            - rotation: [rx, ry, rz] (optional)
            - scale: [sx, sy, sz] (optional)
            - id: Entity identifier (optional)
            - tags: List of additional tags (optional)
        trixel_search_paths: Where to look for .trixel manifests
        auto_bind_skins: If True, automatically find and bind skin_3d_id
    
    Returns:
        Entity3D with placeholder mesh and optional skin
    """
    # Extract ZW concept
    concept = zon_entity.get("type", "unknown")
    mapping = get_concept_mapping(concept)
    
    # Extract transform
    position = zon_entity.get("position", [0.0, 0.0, 0.0])
    rotation = zon_entity.get("rotation", [0.0, 0.0, 0.0])
    scale = zon_entity.get("scale", [1.0, 1.0, 1.0])
    
    transform = Transform3D(
        x=position[0], y=position[1], z=position[2],
        rx=rotation[0], ry=rotation[1], rz=rotation[2],
        sx=scale[0], sy=scale[1], sz=scale[2]
    )
    
    # Extract optional fields
    entity_id = zon_entity.get("id")
    tags = zon_entity.get("tags", [])
    
    # Try to find matching .trixel manifest for skin
    skin_3d_id = None
    if auto_bind_skins and trixel_search_paths:
        skin_3d_id = find_skin_for_concept(concept, trixel_search_paths)
    
    # Build Entity3D
    entity = Entity3D(
        zw_concept=mapping.zw_concept,
        ap_profile=mapping.ap_profile,
        kernel_bindings=mapping.kernel_bindings.copy(),
        placeholder_mesh=mapping.placeholder_mesh,
        transform=transform,
        skin_3d_id=skin_3d_id,
        color=mapping.default_color,
        entity_id=entity_id,
        tags=tags
    )
    
    return entity


def zon_scene_to_entities(
    zon_scene: Dict[str, Any],
    *,
    trixel_search_paths: Optional[List[Path]] = None,
    auto_bind_skins: bool = True
) -> List[Entity3D]:
    """
    Convert a ZON GameScene to list of Entity3D.
    
    Args:
        zon_scene: ZON scene dict with structure:
            {
                "scene_id": "chapter1_opening",
                "entities": [
                    {"type": "guard", "position": [10, 0, 5], ...},
                    {"type": "door", "position": [0, 0, 15], ...},
                    ...
                ]
            }
        trixel_search_paths: Where to look for .trixel manifests
        auto_bind_skins: If True, automatically bind skin_3d_id
    
    Returns:
        List of Entity3D instances ready for rendering
    """
    entities = []
    
    zon_entities = zon_scene.get("entities", [])
    
    for zon_entity in zon_entities:
        entity = zon_entity_to_entity3d(
            zon_entity,
            trixel_search_paths=trixel_search_paths,
            auto_bind_skins=auto_bind_skins
        )
        entities.append(entity)
    
    return entities


def find_skin_for_concept(
    concept: str,
    search_paths: List[Path]
) -> Optional[str]:
    """
    Find a .trixel manifest matching this concept.
    
    Searches for files like:
    - assets/trixels/{concept}.trixel
    - assets/trixels/{concept}_lod0.trixel
    
    Args:
        concept: ZW concept to search for
        search_paths: List of directories to search
    
    Returns:
        skin_3d_id reference if found, None otherwise
    """
    for search_path in search_paths:
        if not search_path.exists():
            continue
        
        # Try exact match
        manifest_path = search_path / f"{concept}.trixel"
        if manifest_path.exists():
            try:
                manifest = load_trixel_manifest(str(manifest_path))
                return manifest.to_skin_reference()
            except Exception:
                continue
        
        # Try LOD0 variant
        manifest_path = search_path / f"{concept}_lod0.trixel"
        if manifest_path.exists():
            try:
                manifest = load_trixel_manifest(str(manifest_path))
                return manifest.to_skin_reference()
            except Exception:
                continue
    
    return None


# ================================================================
# Batch Conversion
# ================================================================

def convert_zon_chapter_to_scenes(
    chapter_zon: Dict[str, Any],
    trixel_search_paths: Optional[List[Path]] = None
) -> Dict[str, List[Entity3D]]:
    """
    Convert an entire ZON chapter to scene entities.
    
    Args:
        chapter_zon: Full chapter ZON with multiple scenes
        trixel_search_paths: Where to look for .trixel manifests
    
    Returns:
        Dict mapping scene_id → List[Entity3D]
    """
    scenes = {}
    
    for scene in chapter_zon.get("scenes", []):
        scene_id = scene.get("scene_id", "unknown")
        entities = zon_scene_to_entities(
            scene,
            trixel_search_paths=trixel_search_paths
        )
        scenes[scene_id] = entities
    
    return scenes


# ================================================================
# Statistics & Reporting
# ================================================================

def get_entity_statistics(entities: List[Entity3D]) -> Dict[str, Any]:
    """
    Get statistics about a list of entities.
    
    Args:
        entities: List of Entity3D instances
    
    Returns:
        Dict with counts, types, skin coverage, etc.
    """
    total = len(entities)
    
    # Count by concept
    concept_counts = {}
    for entity in entities:
        concept = entity.zw_concept
        concept_counts[concept] = concept_counts.get(concept, 0) + 1
    
    # Count with skins
    with_skins = sum(1 for e in entities if e.skin_3d_id is not None)
    skin_coverage = (with_skins / total * 100) if total > 0 else 0
    
    # Count by placeholder type
    placeholder_counts = {}
    for entity in entities:
        mesh = entity.placeholder_mesh
        placeholder_counts[mesh] = placeholder_counts.get(mesh, 0) + 1
    
    return {
        "total_entities": total,
        "concept_counts": concept_counts,
        "with_skins": with_skins,
        "without_skins": total - with_skins,
        "skin_coverage_percent": skin_coverage,
        "placeholder_counts": placeholder_counts
    }
