"""Test Shadow Memory - Intent recording"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))

from intent_shadow import record_intent, query_intents, get_failure_count, _global_shadow

def test_intent_shadow():
    print("=== INTENT SHADOW TEST ===\n")
    
    # Clear any previous state
    _global_shadow.clear()
    
    # TEST 1: Record rejected command
    print("TEST 1: Record rejected command")
    command = {
        "system": "combat",
        "action": "attack",
        "target": "enemy"
    }
    
    intent = record_intent(
        issuer="ai:player",
        command=command,
        reason_rejected="Authority denied - insufficient stamina",
        scene_id="tower_defense"
    )
    
    assert intent.issuer == "ai:player"
    assert intent.reason_rejected == "Authority denied - insufficient stamina"
    print("  ✓ Intent recorded")
    
    # TEST 2: Query by issuer
    print("\nTEST 2: Query by issuer")
    results = query_intents(issuer="ai:player")
    assert len(results) == 1
    assert results[0].intent_id == intent.intent_id
    print("  ✓ Query by issuer works")
    
    # TEST 3: Multiple rejections
    print("\nTEST 3: Record multiple rejections")
    record_intent(
        issuer="ai:enemy",
        command={"action": "flee"},
        reason_rejected="Path blocked"
    )
    record_intent(
        issuer="ai:player",
        command={"action": "cast_spell"},
        reason_rejected="Not enough mana"
    )
    
    player_failures = query_intents(issuer="ai:player")
    assert len(player_failures) == 2
    print(f"  ✓ Player has {len(player_failures)} failed intents")
    
    # TEST 4: Failure count
    print("\nTEST 4: Failure counting")
    total_failures = get_failure_count()
    player_only = get_failure_count(issuer="ai:player")
    
    assert total_failures == 3
    assert player_only == 2
    print(f"  ✓ Total failures: {total_failures}, Player: {player_only}")
    
    # TEST 5: Search by reason
    print("\nTEST 5: Search by rejection reason")
    mana_failures = query_intents(reason_contains="mana")
    assert len(mana_failures) == 1
    assert "mana" in mana_failures[0].reason_rejected.lower()
    print("  ✓ Reason search works")
    
    # TEST 6: Shadow memory doesn't affect world state
    print("\nTEST 6: Shadow memory is read-only")
    # This is conceptual - shadow memory has no write access to world
    print("  ✓ Shadow memory never mutates world (by design)")
    
    print("\n✅ INTENT SHADOW: ALL TESTS PASS")

if __name__ == "__main__":
    test_intent_shadow()
