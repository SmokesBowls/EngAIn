"""Test ZON Bridge - Contract Enforcement"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))

from zon_bridge import (
    ZONBridge, ZONBridgeError,
    deserialize_combat_snapshot, serialize_combat_snapshot
)
from combat3d_mr import CombatSnapshot, CombatEntity
from pathlib import Path
import json

def test_zon_bridge():
    print("=== ZON BRIDGE TEST (Defense Layer 1) ===\n")
    
    bridge = ZONBridge(strict=True, audit=True)
    
    # TEST 1: Valid ZON → CombatSnapshot
    print("TEST 1: Deserialize valid ZON data")
    valid_zon = {
        "entities": {
            "player": {"health": 100.0, "max_health": 100.0},
            "enemy": {"health": 75.0, "max_health": 100.0}
        }
    }
    
    snapshot = bridge.deserialize_combat_snapshot(valid_zon)
    assert len(snapshot.entities) == 2
    assert snapshot.entities["player"].health == 100.0
    print("  ✓ Valid ZON deserialized correctly")
    
    # TEST 2: Invalid ZON (missing entities) → Error
    print("\nTEST 2: Reject invalid ZON (missing field)")
    invalid_zon = {"characters": {}}  # Wrong field name
    
    try:
        bridge.deserialize_combat_snapshot(invalid_zon)
        assert False, "Should have raised error"
    except ZONBridgeError as e:
        assert "entities" in e.message
        print(f"  ✓ Rejected: {e.message}")
    
    # TEST 3: Invalid ZON (wrong type) → Error
    print("\nTEST 3: Reject invalid ZON (wrong type)")
    invalid_zon2 = {"entities": ["player", "enemy"]}  # List instead of dict
    
    try:
        bridge.deserialize_combat_snapshot(invalid_zon2)
        assert False, "Should have raised error"
    except ZONBridgeError as e:
        assert "dict" in e.message
        print(f"  ✓ Rejected: {e.message}")
    
    # TEST 4: CombatSnapshot → ZON (serialization)
    print("\nTEST 4: Serialize CombatSnapshot → ZON")
    snapshot = CombatSnapshot(entities={
        "warden": CombatEntity("warden", 100.0, 100.0),
        "intruder": CombatEntity("intruder", 50.0, 80.0)
    })
    
    zon_output = bridge.serialize_combat_snapshot(snapshot)
    assert "entities" in zon_output
    assert "warden" in zon_output["entities"]
    assert zon_output["entities"]["warden"]["health"] == 100.0
    print("  ✓ Serialized correctly")
    
    # TEST 5: Round-trip (ZON → Snapshot → ZON)
    print("\nTEST 5: Round-trip conversion")
    original_zon = {
        "entities": {
            "a": {"health": 10.0, "max_health": 10.0},
            "b": {"health": 20.0, "max_health": 20.0}
        }
    }
    
    # ZON → Snapshot
    snapshot = bridge.deserialize_combat_snapshot(original_zon)
    
    # Snapshot → ZON
    result_zon = bridge.serialize_combat_snapshot(snapshot)
    
    # Should match
    assert result_zon == original_zon
    print("  ✓ Round-trip successful (data integrity preserved)")
    
    # TEST 6: Audit log
    print("\nTEST 6: Audit log records conversions")
    log = bridge.get_audit_log()
    assert len(log) > 0
    print(f"  ✓ Audit log: {len(log)} conversions recorded")
    
    # TEST 7: File I/O
    print("\nTEST 7: File save/load")
    test_file = Path("/tmp/test_combat.zonj.json")
    
    # Save
    bridge.save_zon_file(original_zon, test_file)
    assert test_file.exists()
    print(f"  ✓ Saved to {test_file}")
    
    # Load
    loaded_zon = bridge.load_zon_file(test_file)
    assert loaded_zon == original_zon
    print("  ✓ Loaded and verified")
    
    # Cleanup
    test_file.unlink()
    
    print("\n" + "="*50)
    print("✅ ZON BRIDGE: ALL TESTS PASS")
    print("="*50)
    print("\nDefense Layer 1: OPERATIONAL")
    print("  ✓ Contract enforcement working")
    print("  ✓ Type validation working")
    print("  ✓ Audit trail working")
    print("  ✓ Round-trip integrity verified")
    print("\n🛡️  Engine-agnostic boundary HARDENED")

if __name__ == "__main__":
    test_zon_bridge()
