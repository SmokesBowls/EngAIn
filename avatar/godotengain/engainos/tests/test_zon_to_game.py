"""Test ZON to Game Converter"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))

from zon_to_game import ZONToGameConverter, convert_zon_to_scene
from pathlib import Path
import json
import tempfile

def test_zon_to_game():
    print("=== ZON TO GAME CONVERTER TEST ===\n")
    
    converter = ZONToGameConverter()
    
    # TEST 1: Extract characters
    print("TEST 1: Extract characters from ZON")
    
    zon_data = {
        'scene_id': 'tower_defense',
        'description': 'Warden defends tower from intruder',
        'entities': {
            'warden': {
                'name': 'Tower Warden',
                'health': 100.0,
                'max_health': 100.0,
                'position': {'x': 0, 'y': 0, 'z': 0},
                'type': 'npc'
            },
            'intruder': {
                'name': 'Intruder',
                'health': 80.0,
                'max_health': 80.0,
                'position': {'x': 10, 'y': 0, 'z': 5},
                'type': 'enemy'
            }
        },
        'events': [
            {
                'type': 'combat_attack',
                'actor': 'warden',
                'target': 'intruder',
                'amount': 25.0
            }
        ]
    }
    
    scene = converter.extract_scene(zon_data)
    
    assert scene.scene_id == 'tower_defense'
    assert len(scene.characters) == 2
    assert scene.characters[0]['id'] in ['warden', 'intruder']
    print(f"  ✓ Extracted {len(scene.characters)} characters")
    
    # TEST 2: Extract events
    print("\nTEST 2: Extract narrative events")
    
    assert len(scene.events) == 1
    assert scene.events[0]['type'] == 'combat_attack'
    assert scene.events[0]['actor'] == 'warden'
    assert scene.events[0]['target'] == 'intruder'
    print(f"  ✓ Extracted {len(scene.events)} event(s)")
    
    # TEST 3: Build initial state
    print("\nTEST 3: Build initial game state")
    
    assert 'combat' in scene.initial_state
    assert 'entities' in scene.initial_state['combat']
    assert 'warden' in scene.initial_state['combat']['entities']
    print("  ✓ Initial state built")
    print(f"  ✓ Combat entities: {list(scene.initial_state['combat']['entities'].keys())}")
    
    # TEST 4: Generate Empire commands
    print("\nTEST 4: Generate Empire commands")
    
    commands = converter.generate_empire_commands(scene)
    
    assert len(commands) > 0
    assert commands[0]['system'] == 'combat'
    assert commands[0]['authority_level'] == 2  # Narrative authority
    print(f"  ✓ Generated {len(commands)} command(s)")
    
    # TEST 5: Export Godot scene
    print("\nTEST 5: Export Godot-compatible JSON")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_scene.json"
        godot_scene = converter.export_godot_scene(scene, output_path)
        
        assert output_path.exists()
        
        # Verify JSON structure
        with output_path.open('r') as f:
            loaded = json.load(f)
        
        assert loaded['scene_id'] == 'tower_defense'
        assert len(loaded['entities']) == 2
        assert loaded['entities'][0]['id'] in ['warden', 'intruder']
        
        print(f"  ✓ Exported to {output_path.name}")
        print(f"  ✓ JSON valid and complete")
    
    print("\n" + "="*60)
    print("✅ ZON TO GAME CONVERTER: ALL TESTS PASS")
    print("="*60)
    print("\nThe Missing Link: OPERATIONAL")
    print("  ✓ ZON → Scene extraction working")
    print("  ✓ Empire command generation working")
    print("  ✓ Godot export working")
    print("\n🎯 READY TO CONVERT NARRATIVE TO GAMEPLAY")

if __name__ == "__main__":
    test_zon_to_game()
