#!/usr/bin/env python3
"""
Fix and verify test_scene.json
Run from: /home/burdens/Downloads/EngAIn/godotengain/engainos
"""

import json
import sys
from pathlib import Path

def fix_scene_file():
    scene_path = Path("game_scenes/test_scene.json")
    
    print("="*70)
    print("Scene File Diagnostic & Fix")
    print("="*70)
    
    # Check if file exists
    if not scene_path.exists():
        print(f"\n✗ ERROR: {scene_path} does not exist")
        print("\nCreating it now...")
        
        scene_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create valid scene
        scene_data = {
            "scene_id": "test_scene",
            "title": "Test Scene",
            "type": "scene",
            "entities": [
                {
                    "id": "player",
                    "type": "character",
                    "flags": {"has_key": False},
                    "stats": {"health": 100},
                    "location": "entrance"
                }
            ],
            "events": [
                {
                    "id": "test_event",
                    "tags": ["test"],
                    "conditions": [
                        {"type": "location", "entity": "player", "location": "table"}
                    ],
                    "actions": [
                        {"type": "set_flag", "entity": "player", "flag": "has_key", "value": True}
                    ],
                    "priority": 5
                }
            ]
        }
        
        with open(scene_path, 'w') as f:
            json.dump(scene_data, f, indent=2)
        
        print(f"✓ Created {scene_path}")
    
    # Try to load and validate
    print(f"\n[1/3] Loading {scene_path}...")
    
    try:
        with open(scene_path, 'r') as f:
            content = f.read()
            print(f"  File size: {len(content)} bytes")
            
        # Try to parse
        data = json.loads(content)
        print(f"  ✓ Valid JSON")
        
    except json.JSONDecodeError as e:
        print(f"  ✗ INVALID JSON: {e}")
        print(f"\n  Attempting to fix...")
        
        # Try to fix common issues
        content = content.strip()
        
        try:
            data = json.loads(content)
            print(f"  ✓ Fixed by stripping whitespace")
        except:
            print(f"  ✗ Cannot auto-fix. Manual edit required.")
            return False
    
    # Validate structure
    print(f"\n[2/3] Validating structure...")
    
    required_fields = ["scene_id", "entities"]
    for field in required_fields:
        if field in data:
            print(f"  ✓ Has '{field}'")
        else:
            print(f"  ✗ Missing '{field}'")
            data[field] = [] if field == "entities" else "unknown"
    
    # Check entities
    entities = data.get("entities", [])
    print(f"  ✓ {len(entities)} entities")
    
    # Check events
    events = data.get("events", [])
    print(f"  ✓ {len(events)} events")
    
    if events == 0:
        print(f"  ⚠ Warning: No events means no AP rules will be extracted")
    
    # Ensure it's saved properly
    print(f"\n[3/3] Saving validated scene...")
    
    with open(scene_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"  ✓ Saved {scene_path}")
    
    # Print summary
    print(f"\n" + "="*70)
    print("Scene file is now valid!")
    print("="*70)
    print(f"\nScene ID: {data.get('scene_id')}")
    print(f"Entities: {len(data.get('entities', []))}")
    print(f"Events:   {len(data.get('events', []))}")
    
    if len(data.get('events', [])) > 0:
        print(f"\nAP should extract {len(data.get('events', []))} rules")
    
    return True

if __name__ == '__main__':
    try:
        success = fix_scene_file()
        if success:
            print("\n✅ Scene file ready. Try launch_engine.py again.")
            sys.exit(0)
        else:
            print("\n❌ Could not fix scene file.")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
