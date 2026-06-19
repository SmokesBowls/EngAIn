# world_builder.py
"""
Orchestrates the entire pipeline from book → 3D world.
"""

from pathlib import Path
from typing import List, Dict, Any
from semantic_bridge import SemanticRegistry, generate_world_from_zon
from spatial_skin_system import Entity3D

class World:
    """Represents a collection of entities forming a world/scene."""
    def __init__(self, entities: List[Entity3D]):
        self.entities = entities

class WorldBuilder:
    def __init__(self, config_path: str = "configs/concepts.yaml", asset_dir: str = "assets/trixels"):
        self.registry = SemanticRegistry()
        
        # Resolve paths relative to project root if needed
        self.config_path = Path(config_path)
        self.asset_dir = Path(asset_dir)
        
        if self.config_path.exists():
            self.registry.load_concepts_from_config(self.config_path)
        
        if self.asset_dir.exists():
            self.registry.index_available_skins(self.asset_dir)
    
    def build_from_zon(self, zon_data: List[Dict[str, Any]]) -> World:
        """Translate ZON data to a World containing Entity3D objects."""
        entities = generate_world_from_zon(zon_data, self.registry)
        world = World(entities=entities)
        
        # Optional: auto-bind kernel behaviors can be added here
        self._bind_kernel_actions(world)
        
        return world
    
    def on_asset_added(self, trixel_path: Path):
        """Called when new 3D asset is imported."""
        # Refresh skin lookup
        self.registry.index_available_skins(self.asset_dir)
    
    def _bind_kernel_actions(self, world: World):
        """
        Placeholder for connecting entity AP profiles to kernel behaviors.
        In a real scenario, this would interface with the active kernel instance.
        """
        for entity in world.entities:
            # Logic for binding kernels based on ap_profile...
            # e.g., if entity.ap_profile == "damageable_npc": ...
            pass

# Usage Example:
# builder = WorldBuilder()
# world = builder.build_from_zon(zon_data)
