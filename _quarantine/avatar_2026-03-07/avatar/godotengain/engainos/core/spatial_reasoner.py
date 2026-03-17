"""
spatial_reasoner.py - AI-Native Spatial Placement

Given semantic entities and location type,
reasons about proper spatial arrangement.
"""

import random
from typing import Dict, List, Tuple
import math


class SpatialReasoner:
    """Semantic spatial reasoning for scene entities"""
    
    def reason_placement(self, scene: Dict) -> Dict:
        """
        Apply semantic reasoning to entity positions
        
        Args:
            scene: Game scene with entities
        
        Returns: Scene with reasoned positions
        """
        location = scene.get('metadata', {}).get('location', '')
        entities = scene.get('spawn_commands', [])
        
        # Infer terrain type
        terrain_type = self._infer_terrain(location)
        
        # Apply terrain-specific placement
        if terrain_type == 'beach':
            entities = self._place_beach_entities(entities)
        elif terrain_type == 'forest':
            entities = self._place_forest_entities(entities)
        elif terrain_type == 'indoor':
            entities = self._place_indoor_entities(entities)
        else:
            # Default: casual cluster
            entities = self._place_default(entities)
        
        scene['spawn_commands'] = entities
        return scene
    
    def _infer_terrain(self, location: str) -> str:
        """Infer terrain type from location string"""
        location_lower = location.lower()
        
        if 'beach' in location_lower or 'shore' in location_lower:
            return 'beach'
        elif 'forest' in location_lower or 'woods' in location_lower:
            return 'forest'
        elif 'room' in location_lower or 'hall' in location_lower:
            return 'indoor'
        else:
            return 'outdoor'
    
    def _place_beach_entities(self, entities: List[Dict]) -> List[Dict]:
        """
        Beach placement reasoning:
        - Characters cluster near center
        - Casual spacing (not rigid line)
        - All on ground level
        - Face inward (social gathering)
        """
        num_entities = len(entities)
        
        if num_entities == 0:
            return entities
        
        # Generate casual cluster positions
        center = [0, 0, 0]
        radius = max(3.0, num_entities * 0.8)  # Scale with group size
        
        for i, entity in enumerate(entities):
            # Random angle around center
            angle = (i / num_entities) * 2 * math.pi + random.uniform(-0.3, 0.3)
            
            # Random distance (cluster, not circle)
            dist = radius * random.uniform(0.6, 1.0)
            
            entity['position'] = [
                center[0] + dist * math.cos(angle),
                0.0,  # Ground level
                center[2] + dist * math.sin(angle)
            ]
        
        return entities
    
    def _place_forest_entities(self, entities: List[Dict]) -> List[Dict]:
        """Forest: More spread out, uneven terrain"""
        for i, entity in enumerate(entities):
            entity['position'] = [
                random.uniform(-10, 10),
                random.uniform(-0.2, 0.2),  # Slight terrain variation
                random.uniform(-10, 10)
            ]
        return entities
    
    def _place_indoor_entities(self, entities: List[Dict]) -> List[Dict]:
        """Indoor: Structured, along walls or around table"""
        # Simple: line them along one wall
        for i, entity in enumerate(entities):
            entity['position'] = [
                i * 2.0 - len(entities),
                0.0,
                -5.0  # Against back wall
            ]
        return entities
    
    def _place_default(self, entities: List[Dict]) -> List[Dict]:
        """Default: Simple cluster"""
        return self._place_beach_entities(entities)


# Integration with scene_loader
def apply_spatial_reasoning(scene: Dict) -> Dict:
    """Apply spatial reasoning to loaded scene"""
    reasoner = SpatialReasoner()
    return reasoner.reason_placement(scene)
