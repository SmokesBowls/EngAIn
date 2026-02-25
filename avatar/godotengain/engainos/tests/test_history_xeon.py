"""Test Causality Ledger - Historical events"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))

from history_xeon import (
    commit_event, get_history, get_canonical_history,
    query_by_cause, get_timeline_summary, _global_history
)

def test_history_xeon():
    print("=== HISTORY XEON TEST ===\n")
    
    # Clear any previous state
    _global_history.clear()
    
    # TEST 1: Commit canonical event
    print("TEST 1: Commit canonical event")
    
    event_data = {"action": "attack", "source": "player", "target": "warden"}
    before = {"warden": {"health": 100}}
    after = {"warden": {"health": 75}}
    
    event = commit_event(
        scene_id="tower_defense",
        event_data=event_data,
        snapshot_before=before,
        snapshot_after=after,
        cause="Player defending tower; AI chose optimal target",
        mode="CANON"
    )
    
    assert event.mode == "CANON"
    assert event.cause == "Player defending tower; AI chose optimal target"
    print("  ✓ Canonical event committed")
    
    # TEST 2: Distinguish canon from test
    print("\nTEST 2: Distinguish CANON from TEST")
    
    # Add test run
    commit_event(
        scene_id="tower_defense",
        event_data={"action": "flee"},
        snapshot_before=before,
        snapshot_after=before,  # No change in test
        cause="Testing escape route",
        mode="TEST"
    )
    
    # Add dream run
    commit_event(
        scene_id="tower_defense",
        event_data={"action": "summon_dragon"},
        snapshot_before=before,
        snapshot_after={"dragon": "appeared"},
        cause="Dream state exploration",
        mode="DREAM"
    )
    
    canon_only = get_canonical_history("tower_defense")
    assert len(canon_only) == 1
    print(f"  ✓ Canon events: {len(canon_only)}, Total: {len(get_history('tower_defense'))}")
    
    # TEST 3: Query by causality
    print("\nTEST 3: Query by causality (WHY)")
    
    ai_decisions = query_by_cause("AI chose")
    assert len(ai_decisions) == 1
    assert "optimal target" in ai_decisions[0].cause
    print(f"  ✓ Found {len(ai_decisions)} events caused by AI decisions")
    
    # TEST 4: Timeline summary
    print("\nTEST 4: Timeline summary")
    
    summary = get_timeline_summary("tower_defense")
    
    assert summary["total_events"] == 3
    assert summary["canon_events"] == 1
    assert summary["test_events"] == 1
    assert summary["dream_events"] == 1
    
    print(f"  ✓ Timeline: {summary['canon_events']} canon, "
          f"{summary['test_events']} test, {summary['dream_events']} dream")
    
    # TEST 5: History records causality, not just mechanics
    print("\nTEST 5: Causality vs mechanics")
    
    # This is the KEY difference from replay logs
    # Replay: "player attacked warden" (mechanical)
    # History: "player attacked warden BECAUSE defending tower AND AI chose optimal" (meaningful)
    
    first_event = canon_only[0]
    assert "AI chose" in first_event.cause
    assert first_event.snapshot_before != first_event.snapshot_after
    print("  ✓ History includes causality (WHY), not just mechanics (WHAT)")
    
    # TEST 6: Clear by mode
    print("\nTEST 6: Clear non-canonical history")
    
    _global_history.clear(mode="TEST")
    _global_history.clear(mode="DREAM")
    
    remaining = get_history("tower_defense")
    assert len(remaining) == 1
    assert remaining[0].mode == "CANON"
    print("  ✓ Test/Dream cleared, Canon preserved")
    
    print("\n✅ HISTORY XEON: ALL TESTS PASS")

if __name__ == "__main__":
    test_history_xeon()
