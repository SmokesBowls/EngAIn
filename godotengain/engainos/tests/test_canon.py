"""Test Canon lifecycle management"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))

from canon import (
    create_scene, imbue_scene, finalize_scene, 
    can_edit, is_canonical, add_violation, get_scene
)

def test_canon():
    print("TEST 1: Create scene in DRAFT state")
    scene = create_scene("tower_defense")
    assert scene.state == "DRAFT"
    assert can_edit("tower_defense")
    assert not is_canonical("tower_defense")
    print("  ✓ Scene created in DRAFT")
    
    print("\nTEST 2: Transition DRAFT → IMBUED")
    scene = imbue_scene("tower_defense")
    assert scene.state == "IMBUED"
    assert scene.imbued_at is not None
    assert can_edit("tower_defense")  # Still editable
    print("  ✓ Scene imbued")
    
    print("\nTEST 3: Transition IMBUED → FINALIZED")
    scene = finalize_scene("tower_defense")
    assert scene.state == "FINALIZED"
    assert scene.finalized_at is not None
    assert not can_edit("tower_defense")  # No longer editable
    assert is_canonical("tower_defense")
    print("  ✓ Scene finalized (locked)")
    
    print("\nTEST 4: Cannot finalize with violations")
    scene2 = create_scene("broken_scene")
    imbue_scene("broken_scene")
    add_violation("broken_scene", "Test violation")
    
    try:
        finalize_scene("broken_scene")
        assert False, "Should not allow finalization with violations"
    except ValueError as e:
        assert "violations" in str(e).lower()
        print(f"  ✓ Violations block finalization: {e}")
    
    print("\nTEST 5: Can force finalize with violations_ok")
    scene2 = finalize_scene("broken_scene", violations_ok=True)
    assert scene2.state == "FINALIZED"
    print("  ✓ Force finalization works")
    
    print("\n✅ CANON: ALL TESTS PASS")

if __name__ == "__main__":
    test_canon()
