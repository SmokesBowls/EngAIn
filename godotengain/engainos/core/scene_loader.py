"""
scene_loader.py - Load game scene JSON and send to Godot

Bridges narrative pipeline output to runtime visualization.
"""

import json
from pathlib import Path
from typing import Dict, List, Any
from spatial_reasoner import apply_spatial_reasoning


class SceneLoader:
    """Load narrative-generated scenes into Godot runtime"""
    
    def __init__(self, scenes_dir: Path = None):
        if scenes_dir is None:
            # Default to mettaext game_scenes
            self.scenes_dir = Path.home() / "Downloads/EngAIn/mettaext/game_scenes"
        else:
            self.scenes_dir = Path(scenes_dir)
    
    def load_scene(self, scene_id: str) -> Dict[str, Any]:
        """
        Load a scene by ID
        
        Args:
            scene_id: Scene identifier (e.g., "03_Fist_contact")
        
        Returns: Complete scene data
        """
        scene_path = self.scenes_dir / f"{scene_id}.json"
        
        if not scene_path.exists():
            raise FileNotFoundError(f"Scene not found: {scene_path}")
        
        with scene_path.open('r') as f:
            return json.load(f)
    
    def list_available_scenes(self) -> List[str]:
        """List all available scene IDs"""
        return [
            p.stem for p in self.scenes_dir.glob("*.json")
        ]
    
    def extract_spawn_data(self, scene: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract entity spawn data for Godot
        
        Args:
            scene: Loaded scene data
        
        Returns: List of spawn commands for Godot
        """
        spawn_commands = []
        
        for entity in scene.get('entities', []):
            spawn_commands.append({
                'type': 'spawn_entity',
                'id': entity['id'],
                'name': entity['name'],
                'position': [
                    entity['position']['x'],
                    entity['position']['y'],
                    entity['position']['z']
                ],
                'health': entity['health'],
                'max_health': entity['max_health'],
                'entity_type': entity['type']
            })
        
        return spawn_commands
    
    def extract_dialogue_events(self, scene: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract dialogue events in order
        
        Args:
            scene: Loaded scene data
        
        Returns: List of dialogue events
        """
        return [
            event for event in scene.get('events', [])
            if event['type'] in ['dialogue', 'thought']
        ]
    
    def get_scene_metadata(self, scene: Dict[str, Any]) -> Dict[str, str]:
        """Extract scene metadata"""
        return {
            'scene_id': scene.get('scene_id', 'unknown'),
            'description': scene.get('description', ''),
            'location': scene.get('metadata', {}).get('where', 'Unknown')
        }


# ================================================================
# GODOT BRIDGE INTEGRATION
# ================================================================

def format_for_godot(scene: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format scene data for Godot consumption
    
    Returns dict ready to send via HTTP to Godot
    """
    loader = SceneLoader()
    
    formatted = {
        'metadata': loader.get_scene_metadata(scene),
        'spawn_commands': loader.extract_spawn_data(scene),
        'events': loader.extract_dialogue_events(scene),
        'initial_state': scene.get('initial_state', {})
    }
    
    # Apply AI spatial reasoning
    formatted = apply_spatial_reasoning(formatted)
    
    return formatted


# ================================================================
# CLI INTERFACE
# ================================================================

if __name__ == '__main__':
    import sys
    
    loader = SceneLoader()
    
    if len(sys.argv) < 2:
        print("Available scenes:")
        for scene_id in loader.list_available_scenes():
            print(f"  - {scene_id}")
        sys.exit(0)
    
    scene_id = sys.argv[1]
    
    print(f"Loading scene: {scene_id}")
    scene = loader.load_scene(scene_id)
    
    print(f"\nMetadata:")
    metadata = loader.get_scene_metadata(scene)
    for key, value in metadata.items():
        print(f"  {key}: {value}")
    
    print(f"\nEntities: {len(scene.get('entities', []))}")
    for entity in scene.get('entities', [])[:5]:  # First 5
        print(f"  - {entity['name']} at ({entity['position']['x']}, {entity['position']['y']}, {entity['position']['z']})")
    
    print(f"\nEvents: {len(scene.get('events', []))}")
    for event in scene.get('events', [])[:3]:  # First 3
        print(f"  - {event['type']}: {event['actor']} - {event['data'].get('text', '')[:50]}...")
