"""Test AP rule enforcement"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))

from ap_core import register_rule, check_ap, is_valid, Violation

def test_ap_core():
    print("TEST 1: Valid delta passes")
    snapshot = {"entities": {"player": {"health": 100}}}
    delta = {"entities": {"player": {"health": 90}}}
    
    violations = check_ap(snapshot, delta)
    assert len(violations) == 0, f"Expected no violations, got {violations}"
    print("  ✓ Valid delta accepted")
    
    print("\nTEST 2: Invalid delta rejected")
    bad_delta = {"entities": {"player": {"health": -10}}}
    
    violations = check_ap(snapshot, bad_delta)
    assert len(violations) > 0, "Expected violations for negative health"
    assert not is_valid(snapshot, bad_delta)
    print(f"  ✓ Violation detected: {violations[0].message}")
    
    print("\nTEST 3: Custom rule registration")
    def rule_max_health(snapshot, delta):
        if "entities" in delta:
            for entity_id, entity_data in delta["entities"].items():
                if "health" in entity_data:
                    if entity_data["health"] > 200:
                        return f"Entity {entity_id} health exceeds maximum (200)"
        return None
    
    register_rule("max_health", rule_max_health)
    
    over_delta = {"entities": {"player": {"health": 250}}}
    violations = check_ap(snapshot, over_delta)
    assert len(violations) > 0
    print(f"  ✓ Custom rule works: {violations[0].message}")
    
    print("\n✅ AP CORE: ALL TESTS PASS")

if __name__ == "__main__":
    test_ap_core()
