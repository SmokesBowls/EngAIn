# semantic_bridge.py
"""
Translates book concepts (ZW/ZON) → runtime entities automatically.
No manual placement, only semantic mapping.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, List, Any
import json
import yaml
from pathlib import Path
from spatial_skin_system import Entity3D, Transform3D, ColorRGB

@dataclass
class ConceptProfile:
    """Defines how a semantic concept manifests in 3D space."""
    zw_concept: str
    placeholder_mesh: str  # "capsule", "cube", "cylinder", "plane", "sphere"
    ap_profile: str       # Kernel behavior: "damageable_npc", "door_rule", "container", etc.
    collision_role: str   # "solid", "trigger", "none"
    default_color: ColorRGB
    default_scale: tuple = (1.0, 1.0, 1.0)
    tags: List[str] = field(default_factory=list)

class SemanticRegistry:
    """Master registry of all known concepts and their 3D representations."""
    
    def __init__(self):
        self.concepts: Dict[str, ConceptProfile] = {}
        self.skin_lookup: Dict[str, str] = {}  # concept → mesh_hash
        self.partial_matchers = {}
        
    def load_concepts_from_config(self, config_path: Path):
        """Load concept definitions from JSON/YAML config."""
        with open(config_path) as f:
            if config_path.suffix in ['.yaml', '.yml']:
                data = yaml.safe_load(f)
            else:
                data = json.load(f)
            
        for concept_name, concept_data in data["concepts"].items():
            color_data = concept_data["default_color"]
            self.concepts[concept_name] = ConceptProfile(
                zw_concept=concept_name,
                placeholder_mesh=concept_data["placeholder_mesh"],
                ap_profile=concept_data["ap_profile"],
                collision_role=concept_data["collision_role"],
                default_color=ColorRGB(*color_data),
                default_scale=tuple(concept_data.get("default_scale", [1.0, 1.0, 1.0])),
                tags=concept_data.get("tags", [])
            )
            
        # Load partial match patterns
        self.partial_matchers = data.get("partial_matches", {})
        
    def index_available_skins(self, manifest_dir: Path):
        """Scan all .trixel manifests and build skin lookup."""
        if not manifest_dir.exists():
            return
            
        for manifest_file in manifest_dir.glob("*.trixel"):
            with open(manifest_file) as f:
                manifest = json.load(f)
                concept = manifest.get("zw_concept")
                mesh_hash = manifest.get("mesh_hash")
                if concept and mesh_hash:
                    self.skin_lookup[concept] = mesh_hash
    
    def resolve_concept(self, raw_concept: str) -> ConceptProfile:
        """Translate raw concept string to concrete profile."""
        # 1. Try exact match
        if raw_concept in self.concepts:
            return self.concepts[raw_concept]
        
        # 2. Try partial matches (e.g., "tower_guard" → "guard")
        lower_concept = raw_concept.lower()
        
        # Check predefined partial patterns
        for pattern, target in self.partial_matchers.items():
            if pattern in lower_concept:
                return self.concepts.get(target, self._fallback(raw_concept))
        
        # 3. Try substring in existing concepts
        for concept_name, profile in self.concepts.items():
            if concept_name in lower_concept:
                return profile
        
        # 4. Fallback based on semantic analysis
        return self._semantic_fallback(raw_concept)
    
    def _semantic_fallback(self, raw_concept: str) -> ConceptProfile:
        """Intelligent fallback using word analysis."""
        words = raw_concept.lower().split('_')
        
        # Check for known semantic patterns
        if any(w in words for w in ['guard', 'soldier', 'warrior', 'knight']):
            return self.concepts.get('guard', self._fallback(raw_concept))
        elif any(w in words for w in ['door', 'gate', 'portal']):
            return self.concepts.get('door', self._fallback(raw_concept))
        elif any(w in words for w in ['barrel', 'crate', 'chest', 'container']):
            return self.concepts.get('container', self._fallback(raw_concept))
        elif any(w in words for w in ['table', 'desk', 'furniture']):
            return self.concepts.get('furniture', self._fallback(raw_concept))
            
        return self._fallback(raw_concept)
    
    def _fallback(self, raw_concept: str) -> ConceptProfile:
        """Ultimate fallback for unknown concepts."""
        return ConceptProfile(
            zw_concept=raw_concept,
            placeholder_mesh="cube",
            ap_profile="generic_static",
            collision_role="solid",
            default_color=ColorRGB(1.0, 0.0, 1.0),  # Magenta for visibility
            tags=["unknown", "fallback"]
        )
    
    def get_skin_for_concept(self, concept: str) -> Optional[str]:
        """Return mesh_hash if a 3D skin exists for this concept."""
        # Try exact match first
        if concept in self.skin_lookup:
            return self.skin_lookup[concept]
        
        # Try concept resolution to get base concept
        profile = self.resolve_concept(concept)
        if profile.zw_concept in self.skin_lookup:
            return self.skin_lookup[profile.zw_concept]
        
        return None

# --- Bridge between ZON and Entity3D ---

def zon_to_entity3d(zon_entity: dict, registry: SemanticRegistry) -> Entity3D:
    """Translate a ZON entity to fully-formed Entity3D automatically."""
    
    # Extract concept from ZON
    raw_concept = zon_entity.get("type") or zon_entity.get("concept") or "unknown"
    
    # Resolve to concrete profile
    profile = registry.resolve_concept(raw_concept)
    
    # Check for 3D skin
    skin_3d_id = registry.get_skin_for_concept(raw_concept)
    
    # Extract transform from ZON (with defaults)
    transform_data = zon_entity.get("transform", {})
    
    # Flexible transform extraction
    pos = transform_data.get("position", zon_entity.get("position", (0, 0, 0)))
    rot = transform_data.get("rotation", zon_entity.get("rotation", (0, 0, 0)))
    scl = transform_data.get("scale", zon_entity.get("scale", profile.default_scale))
    
    transform = Transform3D.from_data(
        position=pos,
        rotation=rot,
        scale=scl
    )
    
    # Create the entity
    entity = Entity3D(
        zw_concept=profile.zw_concept,
        ap_profile=profile.ap_profile,
        kernel_bindings={"profile": profile.ap_profile},
        placeholder_mesh=profile.placeholder_mesh,
        transform=transform,
        collision_role=profile.collision_role,
        semantic_tags=profile.tags.copy(),
        skin_3d_id=skin_3d_id,
        color=profile.default_color,
        entity_id=zon_entity.get("id"),
        source_data={
            "raw_concept": raw_concept,
            "zon_id": zon_entity.get("id"),
            "is_placeholder": skin_3d_id is None
        }
    )
    
    return entity

def generate_world_from_zon(zon_data: List[dict], registry: SemanticRegistry) -> List[Entity3D]:
    """Generate entire world from ZON data."""
    entities = []
    
    for zon_entity in zon_data:
        entity = zon_to_entity3d(zon_entity, registry)
        entities.append(entity)
    
    return entities
