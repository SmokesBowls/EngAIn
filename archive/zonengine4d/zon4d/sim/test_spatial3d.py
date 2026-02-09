#!/usr/bin/env python3
"""
Test file for Spatial3D Adapter
Fixed version - includes velocity field
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from spatial3d_adapter import Spatial3DStateViewAdapter

print("\n" + "="*60)
print("SPATIAL3D ADAPTER - VALIDATION TESTS (FIXED)")
print("="*60)

def test_spawn_and_physics():
    print("\n" + "="*60)
    print("TEST 1: SPAWN + PHYSICS")
    print("="*60)
    
    # Create adapter
    adapter = Spatial3DStateViewAdapter({"entities": {}})
    
    # Spawn a player
    success = adapter.spawn_entity(
        "player",
        pos=(0, 0, 0),
        radius=1.0,
        solid=True,
        tags=["player"],
        has_perceiver=True
    )
    
    print(f"Spawn success: {success}")
    
    # Get initial state
    player = adapter.get_entity("player")
    print(f"Player initial position: {player.get('pos', 'No pos')}")
    print(f"Player initial velocity: {player.get('vel', (0, 0, 0))}")
    
    # Apply physics step (gravity, etc.)
    alerts = adapter.physics_step(1.0/60.0)  # 16ms delta
    
    print(f"Physics alerts: {len(alerts)}")
    
    # Get updated state
    player = adapter.get_entity("player")
    print(f"Player position after physics: {player.get('pos', 'No pos')}")
    print(f"Player velocity after physics: {player.get('vel', (0, 0, 0))}")
    
    return True

def test_movement():
    print("\n" + "="*60)
    print("TEST 2: MOVEMENT")
    print("="*60)
    
    adapter = Spatial3DStateViewAdapter({"entities": {}})
    
    # Spawn entity
    adapter.spawn_entity("npc", pos=(0, 0, 0))
    
    # Move entity
    success, alerts = adapter.move_entity("npc", target_pos=(10, 0, 0), speed=5.0)
    
    print(f"Move success: {success}")
    print(f"Move alerts: {len(alerts)}")
    
    # Process physics (apply movement)
    adapter.physics_step(1.0)
    
    npc = adapter.get_entity("npc")
    print(f"NPC position after move: {npc.get('pos', 'No pos')}")
    
    return True

def test_multiple_entities():
    print("\n" + "="*60)
    print("TEST 3: MULTIPLE ENTITIES")
    print("="*60)
    
    adapter = Spatial3DStateViewAdapter({"entities": {}})
    
    # Spawn multiple entities
    entities = [
        ("player", (0, 0, 0), True),
        ("enemy", (5, 0, 0), True),
        ("wall", (2, 0, 0), False),
    ]
    
    for eid, pos, perceiver in entities:
        adapter.spawn_entity(eid, pos=pos, has_perceiver=perceiver)
    
    # Check all entities exist
    for eid, _, _ in entities:
        entity = adapter.get_entity(eid)
        if entity:
            print(f"✓ {eid}: pos={entity.get('pos', 'No pos')}, "
                  f"perceiver={entity.get('perceiver', False)}, "
                  f"vel={entity.get('vel', (0, 0, 0))}")
        else:
            print(f"✗ {eid}: NOT FOUND")
    
    return True

def test_state_persistence():
    print("\n" + "="*60)
    print("TEST 4: STATE PERSISTENCE")
    print("="*60)
    
    adapter = Spatial3DStateViewAdapter({"entities": {}})
    
    # Spawn entity
    adapter.spawn_entity("test_entity", pos=(1, 2, 3))
    
    # Save state
    saved_state = adapter.save_to_state()
    print(f"Saved state has {len(saved_state.get('entities', {}))} entities")
    
    # Create new adapter with saved state
    new_adapter = Spatial3DStateViewAdapter(saved_state)
    
    # Check entity exists in new adapter
    entity = new_adapter.get_entity("test_entity")
    if entity:
        print(f"✓ Entity restored: pos={entity.get('pos', 'No pos')}")
        return True
    else:
        print("✗ Entity not restored")
        return False

def run_all_tests():
    tests = [
        ("Spawn & Physics", test_spawn_and_physics),
        ("Movement", test_movement),
        ("Multiple Entities", test_multiple_entities),
        ("State Persistence", test_state_persistence),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            print(f"\n>>> Running: {test_name}")
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"ERROR in {test_name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    print("\n" + "="*60)
    print("TEST RESULTS")
    print("="*60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print("="*60)
    
    return all_passed

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
