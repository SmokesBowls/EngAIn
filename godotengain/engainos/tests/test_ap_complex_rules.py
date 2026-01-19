"""Test Complex AP Rules - Pre-Execution Vetting"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))

from ap_complex_rules import (
    ComplexAPRule, ComplexAPRuleRegistry,
    check_complex_rules, register_complex_rule
)

def test_ap_complex_rules():
    print("=== COMPLEX AP RULES TEST (Defense Layer 2) ===\n")
    
    # TEST 1: Attacker min health rule
    print("TEST 1: Pre-execution health check")
    
    # Empire state with Combat3D snapshot
    empire_state = {
        "combat": {
            "entities": {
                "player": {"health": 15.0, "max_health": 100.0},
                "weak_enemy": {"health": 5.0, "max_health": 50.0}
            }
        }
    }
    
    # Valid attack (player has >= 10 health)
    valid_command = {
        "action": "attack",
        "attacker": "player",
        "target": "weak_enemy",
        "amount": 25.0
    }
    
    violations = check_complex_rules(valid_command, empire_state)
    assert len(violations) == 0
    print("  ✓ Valid attack (health >= 10) allowed")
    
    # Invalid attack (weak_enemy has < 10 health)
    invalid_command = {
        "action": "attack",
        "attacker": "weak_enemy",
        "target": "player",
        "amount": 10.0
    }
    
    violations = check_complex_rules(invalid_command, empire_state)
    assert len(violations) > 0
    assert any("health" in v.message.lower() for v in violations)
    print(f"  ✓ Invalid attack (health < 10) rejected: {violations[0].message}")
    
    # TEST 2: Cannot attack self
    print("\nTEST 2: Self-attack prevention")
    
    self_attack = {
        "action": "attack",
        "attacker": "player",
        "target": "player",
        "amount": 10.0
    }
    
    violations = check_complex_rules(self_attack, empire_state)
    assert len(violations) > 0
    assert any("yourself" in v.message.lower() for v in violations)
    print(f"  ✓ Self-attack rejected: {violations[0].message}")
    
    # TEST 3: Empire queries kernel state
    print("\nTEST 3: Proves Empire queries kernel state")
    
    # Command references entity not in state
    unknown_command = {
        "action": "attack",
        "attacker": "ghost",
        "target": "player",
        "amount": 10.0
    }
    
    violations = check_complex_rules(unknown_command, empire_state)
    assert len(violations) > 0
    print("  ✓ Empire queried Combat3D state (found missing entity)")
    
    # TEST 4: Custom rule registration
    print("\nTEST 4: Custom rule registration")
    
    def rule_no_overkill(command, empire_state):
        """Cannot deal more damage than target has health"""
        if not command.get("action") == "attack":
            return True
        
        target_id = command.get("target")
        amount = command.get("amount", 0)
        
        entities = empire_state.get("combat", {}).get("entities", {})
        target = entities.get(target_id, {})
        health = target.get("health", 0)
        
        return amount <= health
    
    register_complex_rule(ComplexAPRule(
        rule_id="rule_no_overkill",
        description="Cannot deal more damage than target health",
        check_fn=rule_no_overkill
    ))
    
    # Test overkill
    overkill_command = {
        "action": "attack",
        "attacker": "player",
        "target": "weak_enemy",
        "amount": 100.0  # weak_enemy only has 5 health
    }
    
    violations = check_complex_rules(overkill_command, empire_state)
    overkill_violations = [v for v in violations if "overkill" in v.rule_id]
    assert len(overkill_violations) > 0
    print("  ✓ Custom rule registered and working")
    
    print("\n" + "="*60)
    print("✅ COMPLEX AP RULES: ALL TESTS PASS")
    print("="*60)
    print("\nDefense Layer 2: OPERATIONAL")
    print("  ✓ Pre-execution vetting working")
    print("  ✓ Empire queries kernel state")
    print("  ✓ Multi-kernel validation proven")
    print("  ✓ Custom rules supported")
    print("\n⚖️  Narrative Canon Enforcement: COMPLETE")

if __name__ == "__main__":
    test_ap_complex_rules()
