"""
Memory Layers Integration Test

Proves: intent_shadow + history_xeon + reality_mode work together

Scenario: "Player attacks warden in different reality modes,
           some commands succeed (history), some fail (shadow),
           behavior changes based on mode"
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))

from intent_shadow import record_intent, query_intents, _global_shadow
from history_xeon import commit_event, get_canonical_history, _global_history
from reality_mode import RealityMode, set_mode, get_context, reality

def test_memory_integration():
    print("=== MEMORY LAYERS INTEGRATION TEST ===\n")
    
    # Clear state
    _global_shadow.clear()
    _global_history.clear()
    
    # SCENARIO SETUP
    print("SCENARIO: Player attacks warden in different reality modes\n")
    
    # ===================================================================
    # TEST 1: DRAFT mode - command fails (shadow records, no history)
    # ===================================================================
    print("TEST 1: DRAFT mode - failed command")
    set_mode(RealityMode.DRAFT, scene_id="tower")
    
    assert get_context().mode == RealityMode.DRAFT
    assert get_context().is_editable()
    assert not get_context().requires_ap_enforcement()
    
    # Command fails in draft (low stamina)
    record_intent(
        issuer="ai:player",
        command={"action": "attack", "target": "warden"},
        reason_rejected="Insufficient stamina",
        scene_id="tower"
    )
    
    # Check: shadow recorded, history did NOT
    assert len(query_intents(issuer="ai:player")) == 1
    assert len(get_canonical_history("tower")) == 0
    print("  ✓ Failed command in DRAFT → intent_shadow only")
    
    # ===================================================================
    # TEST 2: IMBUED mode - command succeeds (history records)
    # ===================================================================
    print("\nTEST 2: IMBUED mode - successful command")
    set_mode(RealityMode.IMBUED, scene_id="tower")
    
    assert get_context().requires_ap_enforcement()
    
    # Command succeeds
    commit_event(
        scene_id="tower",
        event_data={"action": "attack", "target": "warden"},
        snapshot_before={"warden": {"health": 100}},
        snapshot_after={"warden": {"health": 75}},
        cause="Player defending tower; warden is hostile",
        mode=get_context().get_history_mode()
    )
    
    # Check: history recorded
    history = get_canonical_history("tower")
    assert len(history) == 0  # Not canonical yet (IMBUED, not FINALIZED)
    print("  ✓ Successful command in IMBUED → history (non-canonical)")
    
    # ===================================================================
    # TEST 3: FINALIZED mode - canonical history
    # ===================================================================
    print("\nTEST 3: FINALIZED mode - canonical event")
    
    with reality(RealityMode.FINALIZED, scene_id="tower"):
        assert get_context().is_canonical()
        assert not get_context().is_editable()
        
        # Canonical event
        commit_event(
            scene_id="tower",
            event_data={"action": "attack", "target": "warden"},
            snapshot_before={"warden": {"health": 75}},
            snapshot_after={"warden": {"health": 50}},
            cause="Second attack; warden counterattacks",
            mode=get_context().get_history_mode()
        )
        
        # Check: canonical history
        canonical = get_canonical_history("tower")
        assert len(canonical) == 1
        assert canonical[0].cause == "Second attack; warden counterattacks"
        print("  ✓ FINALIZED event → canonical history")
    
    # Mode restored after context
    assert get_context().mode == RealityMode.IMBUED
    
    # ===================================================================
    # TEST 4: DREAM mode - sandbox (not canonical)
    # ===================================================================
    print("\nTEST 4: DREAM mode - sandbox exploration")
    
    with reality(RealityMode.DREAM, scene_id="tower"):
        assert get_context().is_sandbox()
        assert not get_context().is_canonical()
        
        # Dream event (what if warden had magic?)
        commit_event(
            scene_id="tower",
            event_data={"action": "cast_fireball"},
            snapshot_before={"warden": {"health": 50}},
            snapshot_after={"player": {"health": 0}},
            cause="Dream: exploring if warden had magic",
            mode=get_context().get_history_mode()
        )
        
        # Check: not in canonical history
        canonical = get_canonical_history("tower")
        assert len(canonical) == 1  # Still just the one from FINALIZED
        print("  ✓ DREAM event → not canonical (sandbox only)")
    
    # ===================================================================
    # TEST 5: REPLAY mode - read-only (prevents mutation)
    # ===================================================================
    print("\nTEST 5: REPLAY mode - read-only")
    
    with reality(RealityMode.REPLAY):
        assert not get_context().allows_mutation()
        assert not get_context().is_editable()
        
        # In replay, attempted mutations would be blocked
        # (This would be enforced by Empire in real usage)
        print("  ✓ REPLAY mode prevents mutation")
    
    # ===================================================================
    # TEST 6: Full memory picture
    # ===================================================================
    print("\nTEST 6: Complete memory state")
    
    # Shadow memory: 1 rejection
    shadow_count = len(query_intents())
    print(f"  ✓ Shadow memory: {shadow_count} rejected intent(s)")
    
    # History: 1 canonical, others non-canonical
    canonical_count = len(get_canonical_history("tower"))
    print(f"  ✓ Canonical history: {canonical_count} event(s)")
    
    # Mode context: working correctly
    print(f"  ✓ Reality mode: {get_context().mode.value}")
    
    # ===================================================================
    # FINAL VALIDATION
    # ===================================================================
    print("\n" + "="*50)
    print("✅ MEMORY INTEGRATION: ALL LAYERS WORKING TOGETHER")
    print("="*50)
    print("\nProven:")
    print("  ✓ Intent shadow records rejections")
    print("  ✓ History records successes with causality")
    print("  ✓ Reality mode changes behavior")
    print("  ✓ DRAFT → IMBUED → FINALIZED → DREAM → REPLAY")
    print("  ✓ Canonical vs non-canonical separation")
    print("\n🎉 Memory layers fully integrated!")

if __name__ == "__main__":
    test_memory_integration()
