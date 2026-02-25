"""
zon_to_game.py - The Missing Link

Connects narrative pipeline output to game engine.

Flow:
  Narrative (Pass 4) → ZON Memory Fabric
    ↓
  zon_to_game.py (THIS FILE - semantic extraction)
    ↓
  Empire Commands → Game State
    ↓
  Godot Rendering

Purpose: Convert semantic atoms into playable game events.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from pathlib import Path
import json


@dataclass
class GameScene:
    """
    Complete game scene extracted from ZON.
    
    Ready for Empire execution and Godot rendering.
    """
    scene_id: str
    description: str
    characters: List[Dict[str, Any]]
    locations: List[Dict[str, Any]]
    events: List[Dict[str, Any]]
    initial_state: Dict[str, Any]


class ZONToGameConverter:
    """
    Converts ZON memory fabric into playable game scenes.
    
    Extracts:
    - Characters (who exists)
    - Locations (where they are)
    - Events (what happens)
    - Initial state (starting conditions)
    
    Generates:
    - Empire commands (for execution)
    - Game scene JSON (for Godot)
    """
    
    def __init__(self):
        self.scenes = []
    
    def load_zon_file(self, path: Path) -> Dict[str, Any]:
        """Load ZON file (from Pass 4 output)"""
        with path.open("r") as f:
            if path.suffix == ".json" or path.name.endswith(".zonj.json"):
                return json.load(f)
            else:
                # Would need ZON text parser
                # For now, assume JSON
                return json.load(f)
    
    def extract_scene(self, zon_data: Dict[str, Any]) -> GameScene:
        """
        Extract game scene from ZON memory fabric.
        
        Args:
            zon_data: ZON output from narrative pipeline
        
        Returns: GameScene ready for game engine
        """
        
        # Extract scene metadata
        scene_id = zon_data.get("scene_id", "unknown_scene")
        description = zon_data.get("description", "")
        
        # Extract characters
        characters = self._extract_characters(zon_data)
        
        # Extract locations
        locations = self._extract_locations(zon_data)
        
        # Extract events
        events = self._extract_events(zon_data)
        
        # Build initial state
        initial_state = self._build_initial_state(characters, locations)
        
        scene = GameScene(
            scene_id=scene_id,
            description=description,
            characters=characters,
            locations=locations,
            events=events,
            initial_state=initial_state
        )
        
        self.scenes.append(scene)
        return scene
    
    def _extract_characters(self, zon_data: Dict) -> List[Dict[str, Any]]:
        """Extract character entities from ZON"""
        characters = []
        
        # Look for entities in ZON structure
        entities = zon_data.get("entities", {})
        
        for entity_id, entity_data in entities.items():
            character = {
                "id": entity_id,
                "name": entity_data.get("name", entity_id),
                "health": entity_data.get("health", 100.0),
                "max_health": entity_data.get("max_health", 100.0),
                "position": entity_data.get("position", {"x": 0, "y": 0, "z": 0}),
                "type": entity_data.get("type", "character")
            }
            characters.append(character)
        
        return characters
    
    def _extract_locations(self, zon_data: Dict) -> List[Dict[str, Any]]:
        """Extract location data from ZON"""
        locations = []
        
        # Look for location markers
        locs = zon_data.get("locations", [])
        
        for loc_data in locs:
            location = {
                "id": loc_data.get("id", "unknown"),
                "name": loc_data.get("name", "Unknown Location"),
                "description": loc_data.get("description", ""),
                "bounds": loc_data.get("bounds", {}),
                "type": loc_data.get("type", "area")
            }
            locations.append(location)
        
        return locations
    
    def _extract_events(self, zon_data: Dict) -> List[Dict[str, Any]]:
        """Extract narrative events from ZON"""
        events = []
        
        # Look for event sequences
        event_list = zon_data.get("events", [])
        
        for event_data in event_list:
            event = {
                "type": event_data.get("type", "unknown"),
                "timestamp": event_data.get("timestamp", 0),
                "actor": event_data.get("actor", event_data.get("source", event_data.get("attacker"))),
                "target": event_data.get("target"),
                "action": event_data.get("action", event_data.get("type")),
                "data": event_data
            }
            events.append(event)
        
        return events
    
    def _build_initial_state(self, 
                            characters: List[Dict], 
                            locations: List[Dict]) -> Dict[str, Any]:
        """Build initial game state from extracted data"""
        
        # Build combat state
        combat_entities = {}
        for char in characters:
            combat_entities[char["id"]] = {
                "health": char["health"],
                "max_health": char["max_health"]
            }
        
        return {
            "combat": {
                "entities": combat_entities
            },
            "spatial": {
                "entities": {
                    char["id"]: char["position"]
                    for char in characters
                }
            },
            "locations": locations
        }
    
    def generate_empire_commands(self, scene: GameScene) -> List[Dict[str, Any]]:
        """
        Generate Empire commands from scene events.
        
        Args:
            scene: GameScene with events
        
        Returns: List of Empire command dicts
        """
        commands = []
        
        for event in scene.events:
            # Map event type to system
            system = self._map_event_to_system(event)
            
            if system == "combat":
                # Generate damage event
                command = {
                    "issuer": "narrative",
                    "authority_level": 2,  # Narrative has soft authority
                    "system": "combat",
                    "events": [{
                        "source_id": event["actor"],
                        "target_id": event["target"],
                        "amount": event["data"].get("amount", 10.0)
                    }]
                }
                commands.append(command)
            
            # Add more system mappings as needed
        
        return commands
    
    def _map_event_to_system(self, event: Dict) -> str:
        """Map narrative event to game system"""
        event_type = event["type"].lower()
        
        if "attack" in event_type or "damage" in event_type or "combat" in event_type:
            return "combat"
        elif "move" in event_type or "position" in event_type:
            return "spatial"
        elif "speak" in event_type or "say" in event_type or "dialogue" in event_type:
            return "dialogue"
        else:
            return "unknown"
    
    def export_godot_scene(self, scene: GameScene, output_path: Path):
        """
        Export scene as Godot-compatible JSON.
        
        Args:
            scene: GameScene to export
            output_path: Where to save JSON
        """
        godot_scene = {
            "scene_id": scene.scene_id,
            "description": scene.description,
            "entities": [
                {
                    "id": char["id"],
                    "name": char["name"],
                    "position": char["position"],
                    "health": char["health"],
                    "max_health": char["max_health"],
                    "type": char["type"]
                }
                for char in scene.characters
            ],
            "locations": scene.locations,
            "events": scene.events,
            "initial_state": scene.initial_state
        }
        
        with output_path.open("w") as f:
            json.dump(godot_scene, f, indent=2)
        
        return godot_scene


def convert_zon_to_scene(zon_path: Path) -> GameScene:
    """
    Convert ZON file to GameScene.
    
    Args:
        zon_path: Path to .zon or .zonj.json file
    
    Returns: GameScene
    """
    converter = ZONToGameConverter()
    zon_data = converter.load_zon_file(zon_path)
    return converter.extract_scene(zon_data)


# ================================================================
# CLI INTERFACE
# ================================================================

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python zon_to_game.py <zon_file.json> [output_dir]")
        sys.exit(1)
    
    zon_path = Path(sys.argv[1])
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path('./game_scenes')
    
    print(f"Converting: {zon_path.name}")
    print(f"Output to: {output_dir}")
    print()
    
    # Convert
    converter = ZONToGameConverter()
    zon_data = converter.load_zon_file(zon_path)
    scene = converter.extract_scene(zon_data)
    
    # Export
    output_dir.mkdir(parents=True, exist_ok=True)
    godot_path = output_dir / f"{scene.scene_id}.json"
    converter.export_godot_scene(scene, godot_path)
    
    print(f"✓ Converted: {zon_path.name} → {godot_path.name}")
    print(f"  Scene ID: {scene.scene_id}")
    print(f"  Characters: {len(scene.characters)}")
    print(f"  Events: {len(scene.events)}")
    print(f"  Locations: {len(scene.locations)}")
    print()
    print(f"✓ Scene ready at: {godot_path}")
