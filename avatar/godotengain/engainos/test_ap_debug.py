#!/usr/bin/env python3
"""
Debug launcher - keeps engine running and shows all output
Run from: /home/burdens/Downloads/EngAIn/godotengain/engainos
"""

import sys
import time
from pathlib import Path

# Make sure we can import from core
sys.path.insert(0, str(Path.cwd() / "core"))

def test_ap_loading():
    """Test AP loading without starting full engine"""
    print("="*70)
    print("AP Debug Test")
    print("="*70)
    
    # Test 1: Can we import?
    print("\n[1/4] Testing imports...")
    try:
        from ap_runtime import APRuntimeIntegration
        from ap_engine import ZWAPEngine, StateProvider
        print("  ✓ AP modules import successfully")
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        return False
    
    # Test 2: Can we load the scene?
    print("\n[2/4] Loading test_scene.json...")
    import json
    
    scene_path = Path("game_scenes/test_scene.json")
    if not scene_path.exists():
        print(f"  ✗ File not found: {scene_path}")
        return False
    
    try:
        with open(scene_path, 'r') as f:
            scene_data = json.load(f)
        print(f"  ✓ Loaded scene: {scene_data.get('scene_id')}")
        print(f"    Entities: {len(scene_data.get('entities', []))}")
        print(f"    Events: {len(scene_data.get('events', []))}")
    except Exception as e:
        print(f"  ✗ Failed to load: {e}")
        return False
    
    # Test 3: Can we extract rules?
    print("\n[3/4] Extracting AP rules...")
    try:
        ap = APRuntimeIntegration(scenes_dir="game_scenes")
        rules = ap._extract_rules_from_scene_dict(scene_data)
        print(f"  ✓ Extracted {len(rules)} rules")
        
        for rule_id, rule in list(rules.items())[:3]:
            print(f"    - {rule_id}")
            print(f"      Requires: {rule.get('requires', [])}")
            print(f"      Effects: {rule.get('effects', [])}")
    except Exception as e:
        print(f"  ✗ Extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 4: Can we initialize AP?
    print("\n[4/4] Initializing AP engine...")
    try:
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
        
        # Initialize AP
        ap.initialize(initial_state, rules)
        
        print(f"  ✓ AP engine initialized")
        print(f"    Rules loaded: {len(ap.engine.list_rules())}")
        
        # Test a query
        if len(ap.engine.list_rules()) > 0:
            first_rule = ap.engine.list_rules()[0]
            print(f"\n  Testing rule evaluation...")
            context = {'player': 'player'}
            result = ap.engine.evaluate_rule_explain(first_rule['id'], context)
            print(f"    Rule: {first_rule['id']}")
            print(f"    Eligible: {result.get('eligible', False)}")
            print(f"    Reason: {result.get('reason', 'N/A')}")
        
    except Exception as e:
        print(f"  ✗ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "="*70)
    print("✅ AP system is working!")
    print("="*70)
    print("\nThe issue is likely with scene_server, not AP.")
    print("Try: python3 launch_engine.py")
    print("And keep this terminal open to see what happens.")
    
    return True

if __name__ == '__main__':
    success = test_ap_loading()
    if not success:
        print("\n❌ AP test failed - see errors above")
        sys.exit(1)
    
    print("\n" + "="*70)
    print("Keep this window open and try running:")
    print("  python3 launch_engine.py")
    print("in another terminal")
    print("="*70)
    
    # Keep running so you can see output
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopped.")
