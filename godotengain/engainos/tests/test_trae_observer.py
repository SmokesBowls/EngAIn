"""Test Trae Observer - Automated Failure Analysis"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))

from trae_observer import (
    TraeObserver, ShadowReport, 
    analyze_and_report, get_latest_learning_signal,
    print_shadow_report
)
from intent_shadow import record_intent, _global_shadow
from history_xeon import get_history, _global_history
from reality_mode import set_mode, RealityMode

def test_trae_observer():
    print("=== TRAE OBSERVER TEST (Defense Layer 3) ===\n")
    
    # Clear state
    _global_shadow.clear()
    _global_history.clear()
    
    observer = TraeObserver(min_pattern_threshold=2)
    
    # TEST 1: Analyze empty shadow memory
    print("TEST 1: Empty shadow memory")
    report = observer.analyze_shadow()
    assert report.total_failures == 0
    assert len(report.top_patterns) == 0
    print("  ✓ Empty report generated correctly")
    
    # TEST 2: Record failures and analyze
    print("\nTEST 2: Detect failure patterns")
    
    # Simulate failures from Trae
    record_intent("trae", {"action": "attack"}, "Insufficient stamina", scene_id="combat1")
    record_intent("trae", {"action": "attack"}, "Insufficient stamina", scene_id="combat1")
    record_intent("trae", {"action": "attack"}, "Insufficient stamina", scene_id="combat1")
    record_intent("trae", {"action": "move"}, "FINALIZED - requires Tier 3", scene_id="combat1")
    record_intent("trae", {"action": "move"}, "FINALIZED - requires Tier 3", scene_id="combat1")
    record_intent("human", {"action": "test"}, "REPLAY mode - mutations not allowed", scene_id="test1")
    
    report = observer.analyze_shadow()
    
    assert report.total_failures == 6
    assert report.unique_reasons == 3
    assert len(report.top_patterns) >= 2
    
    # Most common should be "Insufficient stamina"
    top_pattern = report.top_patterns[0]
    assert top_pattern.reason == "Insufficient stamina"
    assert top_pattern.count == 3
    assert top_pattern.percentage == 50.0
    
    print(f"  ✓ Detected {report.unique_reasons} unique failure patterns")
    print(f"  ✓ Top pattern: '{top_pattern.reason}' ({top_pattern.count} occurrences)")
    
    # TEST 3: Recommendations generated
    print("\nTEST 3: Actionable recommendations")
    
    assert len(report.recommendations) > 0
    stamina_rec = [r for r in report.recommendations if "resource" in r.lower()][0]
    assert "stamina" in stamina_rec.lower() or "resource" in stamina_rec.lower()
    
    print(f"  ✓ {len(report.recommendations)} recommendation(s) generated")
    print(f"  ✓ Example: '{report.recommendations[0][:60]}...'")
    
    # TEST 4: Commit to HistoryXeon in DREAM mode
    print("\nTEST 4: Commit report to history (DREAM mode)")
    
    success = observer.commit_report_to_history(report, scene_id="shadow_analysis")
    assert success
    
    # Verify it's in DREAM mode history
    dream_events = get_history("shadow_analysis", mode="DREAM")
    assert len(dream_events) > 0
    
    # Verify NOT in canonical history
    from history_xeon import get_canonical_history
    canonical = get_canonical_history("shadow_analysis")
    assert len(canonical) == 0  # Should be empty (DREAM only)
    
    print("  ✓ Report committed to HistoryXeon")
    print("  ✓ Correctly in DREAM mode (not canon)")
    
    # TEST 5: Retrieve learning signal
    print("\nTEST 5: Retrieve latest learning signal")
    
    signal = get_latest_learning_signal("shadow_analysis")
    assert signal is not None
    assert signal["type"] == "shadow_analysis"
    assert signal["total_failures"] == 6
    assert len(signal["recommendations"]) > 0
    
    print("  ✓ Learning signal retrieved")
    print(f"  ✓ Contains {len(signal['recommendations'])} actionable recommendations")
    
    # TEST 6: Filter by issuer
    print("\nTEST 6: Filter analysis by issuer")
    
    trae_report = observer.analyze_shadow(issuer="trae")
    assert trae_report.total_failures == 5  # Only Trae's failures
    
    human_report = observer.analyze_shadow(issuer="human")
    assert human_report.total_failures == 1  # Only human's failures
    
    print(f"  ✓ Trae failures: {trae_report.total_failures}")
    print(f"  ✓ Human failures: {human_report.total_failures}")
    
    # TEST 7: Filter by scene
    print("\nTEST 7: Filter analysis by scene")
    
    combat_report = observer.analyze_shadow(scene_id="combat1")
    assert combat_report.total_failures == 5  # Only combat1 scene
    
    test_report = observer.analyze_shadow(scene_id="test1")
    assert test_report.total_failures == 1  # Only test1 scene
    
    print(f"  ✓ Combat1 failures: {combat_report.total_failures}")
    print(f"  ✓ Test1 failures: {test_report.total_failures}")
    
    # TEST 8: Print report (visual check)
    print("\nTEST 8: Generate formatted report")
    print_shadow_report(report)
    
    # TEST 9: Convenience function
    print("TEST 9: Convenience function (auto-commit)")
    _global_history.clear()
    
    new_report = analyze_and_report(commit_to_history=True)
    assert new_report.total_failures == 6
    
    # Should auto-commit
    dream_events = get_history("shadow_analysis", mode="DREAM")
    assert len(dream_events) > 0
    
    print("  ✓ analyze_and_report() works with auto-commit")
    
    print("\n" + "="*60)
    print("✅ TRAE OBSERVER: ALL TESTS PASS")
    print("="*60)
    print("\nDefense Layer 3: OPERATIONAL")
    print("  ✓ Pattern detection working")
    print("  ✓ Recommendations generated")
    print("  ✓ DREAM mode separation working")
    print("  ✓ Learning signal retrieval working")
    print("  ✓ Filtering (issuer/scene) working")
    print("\n🧠 AI Learning Loop: CLOSED")
    print("   Trae can now learn from failures automatically!")

if __name__ == "__main__":
    test_trae_observer()
