#!/usr/bin/env python3
"""
Test AP Runtime Scene Loading
Verifies that AP runtime can load test_scene.json and extract rules properly
"""

import json
import sys
from pathlib import Path

# Add core to path
sys.path.insert(0, str(Path(__file__).parent))

from ap_runtime import APRuntimeIntegration


def test_scene_loading():
    """Test loading test_scene.json"""
    print("="*70)
    print("Testing AP Runtime Scene Loading")
    print("="*70)
    
    # Create test scene file if it doesn't exist
    test_scene_path = Path("game_scenes/test_scene.json")
    if not test_scene_path.exists():
        print(f"\n[ERROR] Scene file not found: {test_scene_path}")
        print("Creating test scene...")
        
        test_scene_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy from outputs if available
        output_scene = Path("/mnt/user-data/outputs/test_scene.json")
        if output_scene.exists():
            import shutil
            shutil.copy(output_scene, test_scene_path)
            print(f"[OK] Copied test scene to {test_scene_path}")
        else:
            print("[ERROR] Cannot find test_scene.json in outputs")
            return False
    
    # Test loading
    print(f"\n[1/4] Loading scene from: {test_scene_path}")
    with open(test_scene_path, 'r') as f:
        scene_data = json.load(f)
    
    print(f"  ✓ Scene ID: {scene_data.get('scene_id')}")
    print(f"  ✓ Entities: {len(scene_data.get('entities', []))}")
    print(f"  ✓ Events: {len(scene_data.get('events', []))}")
    
    # Test AP runtime initialization
    print("\n[2/4] Initializing AP Runtime")
    ap = APRuntimeIntegration(scenes_dir="game_scenes")
    
    # Load rules manually to see what happens
    print("\n[3/4] Extracting rules from scene")
    rules = ap._extract_rules_from_scene_dict(scene_data)
    
    print(f"  ✓ Extracted {len(rules)} rules:")
    for rule_id, rule in rules.items():
        print(f"    - {rule_id}")
        print(f"      Priority: {rule.get('priority', 0)}")
        print(f"      Requires: {len(rule.get('requires', []))} predicates")
        print(f"      Effects: {len(rule.get('effects', []))} effects")
        print(f"      Read set: {rule.get('read_set', [])}")
        print(f"      Write set: {rule.get('write_set', [])}")
    
    # Test full initialization
    print("\n[4/4] Full AP Runtime initialization")
    
    # Extract initial state
    initial_state = {
        'flags': {},
        'stats': {},
        'locations': {},
        'inventory': {}
    }
    
    for entity in scene_data.get('entities', []):
        entity_id = entity.get('id')
        
        if entity.get('flags'):
            initial_state['flags'][entity_id] = entity['flags']
        
        if entity.get('stats'):
            initial_state['stats'][entity_id] = entity['stats']
        
        if entity.get('location'):
            initial_state['locations'][entity_id] = entity['location']
        
        if entity.get('inventory'):
            initial_state['inventory'][entity_id] = entity['inventory']
    
    print(f"  Initial state:")
    print(f"    Flags: {initial_state['flags']}")
    print(f"    Locations: {initial_state['locations']}")
    
    # Initialize AP
    ap.initialize(initial_state, rules)
    
    print(f"\n  ✓ AP Engine initialized with {len(ap.engine.list_rules())} rules")
    
    # Test a query
    print("\n[BONUS] Testing rule evaluation")
    context = {'player': 'player', 'door': 'door'}
    
    for rule_dict in ap.engine.list_rules()[:2]:
        rule_id = rule_dict['id']
        result = ap.engine.evaluate_rule_explain(rule_id, context)
        print(f"\n  Rule: {rule_id}")
        print(f"    Eligible: {result.get('eligible', False)}")
        print(f"    Reason: {result.get('reason', 'N/A')}")
    
    print("\n" + "="*70)
    print("Test Complete - AP Runtime is working!")
    print("="*70)
    
    return True


if __name__ == '__main__':
    try:
        success = test_scene_loading()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
