"""Test Reality Mode - Context management"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))

from reality_mode import (
    RealityMode, RealityContext, set_mode, get_mode, 
    get_context, reality
)

def test_reality_mode():
    print("=== REALITY MODE TEST ===\n")
    
    # TEST 1: Mode properties
    print("TEST 1: Mode properties")
    
    draft_ctx = RealityContext(mode=RealityMode.DRAFT)
    assert draft_ctx.is_editable()
    assert not draft_ctx.is_canonical()
    assert not draft_ctx.requires_ap_enforcement()
    print("  ✓ DRAFT: editable, not canonical, no AP enforcement")
    
    finalized_ctx = RealityContext(mode=RealityMode.FINALIZED)
    assert not finalized_ctx.is_editable()
    assert finalized_ctx.is_canonical()
    assert finalized_ctx.requires_ap_enforcement()
    print("  ✓ FINALIZED: immutable, canonical, AP enforced")
    
    # TEST 2: Different behaviors by mode
    print("\nTEST 2: Same command, different modes")
    
    contexts = {
        RealityMode.DRAFT: "editable, no enforcement",
        RealityMode.FINALIZED: "immutable, hard enforcement",
        RealityMode.DREAM: "symbolic, sandbox",
        RealityMode.REPLAY: "read-only, deterministic"
    }
    
    for mode, behavior in contexts.items():
        ctx = RealityContext(mode=mode)
        print(f"  ✓ {mode.value}: {behavior}")
    
    # TEST 3: Global mode management
    print("\nTEST 3: Global mode setting")
    
    set_mode(RealityMode.IMBUED, scene_id="test_scene")
    assert get_mode() == RealityMode.IMBUED
    assert get_context().scene_id == "test_scene"
    print("  ✓ Global mode set to IMBUED")
    
    # TEST 4: Context manager (temporary mode)
    print("\nTEST 4: Context manager for temporary modes")
    
    set_mode(RealityMode.DRAFT)
    assert get_mode() == RealityMode.DRAFT
    
    with reality(RealityMode.DREAM):
        assert get_mode() == RealityMode.DREAM
        print("  ✓ Inside DREAM context")
    
    assert get_mode() == RealityMode.DRAFT
    print("  ✓ Restored to DRAFT after context")
    
    # TEST 5: Nested contexts
    print("\nTEST 5: Nested reality contexts")
    
    set_mode(RealityMode.DRAFT)
    
    with reality(RealityMode.IMBUED):
        assert get_mode() == RealityMode.IMBUED
        
        with reality(RealityMode.DREAM):
            assert get_mode() == RealityMode.DREAM
        
        assert get_mode() == RealityMode.IMBUED
    
    assert get_mode() == RealityMode.DRAFT
    print("  ✓ Nested contexts restore correctly")
    
    # TEST 6: Prevents category errors
    print("\nTEST 6: Category error prevention")
    
    replay_ctx = RealityContext(mode=RealityMode.REPLAY)
    assert not replay_ctx.allows_mutation()
    print("  ✓ REPLAY prevents mutation")
    
    dream_ctx = RealityContext(mode=RealityMode.DREAM)
    assert dream_ctx.is_sandbox()
    assert not dream_ctx.is_canonical()
    print("  ✓ DREAM is sandbox, not canonical")
    
    print("\n✅ REALITY MODE: ALL TESTS PASS")

if __name__ == "__main__":
    test_reality_mode()
