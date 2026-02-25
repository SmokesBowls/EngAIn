# faction3d_validator.gd
# Validator and test harness for Faction3D subsystem
# Enforces 5/5 invariants: immutability, determinism, contract compliance, bounds, phase coherence

class_name Faction3DValidator
extends Node

# ============================================================================
# DEPENDENCIES
# ============================================================================

const Kernel = preload("res://faction3d_kernel.gd")
const Adapter = preload("res://faction3d_adapter.gd")

# ============================================================================
# TEST STATE
# ============================================================================

var _test_results: Array = []
var _adapter: Adapter = null

# ============================================================================
# MAIN VALIDATION
# ============================================================================

func run_full_validation() -> Dictionary:
	"""Run complete validation suite - returns 5/5 invariant check"""
	print("\n" + "=".repeat(60))
	print("FACTION3D VALIDATION SUITE")
	print("=".repeat(60))
	
	_test_results.clear()
	_adapter = Adapter.new()
	add_child(_adapter)
	
	# Run all tests
	_test_invariant_1_immutability()
	_test_invariant_2_determinism()
	_test_invariant_3_contract_compliance()
	_test_invariant_4_bounds_enforcement()
	_test_invariant_5_phase_coherence()
	
	# Calculate results
	var passed = _test_results.filter(func(r): return r["passed"]).size()
	var failed = _test_results.filter(func(r): return not r["passed"]).size()
	var total = _test_results.size()
	
	# Invariant check
	var invariants_ok = (failed == 0)
	
	# Print summary
	print("\n" + "-".repeat(60))
	print("RESULTS: %d/%d tests passed" % [passed, total])
	if invariants_ok:
		print("✓ ALL 5 INVARIANTS VALIDATED")
	else:
		print("✗ INVARIANT VIOLATIONS DETECTED")
		for result in _test_results:
			if not result["passed"]:
				print("  FAIL: %s - %s" % [result["test"], result.get("reason", "Unknown")])
	print("=".repeat(60) + "\n")
	
	_adapter.queue_free()
	_adapter = null
	
	return {
		"invariants_ok": invariants_ok,
		"passed": passed,
		"failed": failed,
		"total": total,
		"results": _test_results.duplicate(),
	}

# ============================================================================
# INVARIANT 1: IMMUTABILITY
# ============================================================================

func _test_invariant_1_immutability() -> void:
	"""Test that kernel functions don't mutate input snapshots"""
	print("\n[INVARIANT 1] Testing Immutability...")
	
	# Test 1.1: mr_set_faction_influence doesn't mutate input
	var original_snapshot = Kernel.mr_create_snapshot()
	var original_influence = Kernel.mr_get_faction_state(original_snapshot, Kernel.FactionID.PLEADIANS)["influence"]
	var new_snapshot = Kernel.mr_set_faction_influence(original_snapshot, Kernel.FactionID.PLEADIANS, 0.5)
	var original_after = Kernel.mr_get_faction_state(original_snapshot, Kernel.FactionID.PLEADIANS)["influence"]
	
	_record_test("1.1: mr_set_faction_influence immutability", 
		original_influence == original_after,
		"Original snapshot mutated" if original_influence != original_after else "")
	
	# Test 1.2: mr_escalate_phase doesn't mutate input
	original_snapshot = Kernel.mr_create_snapshot()
	var original_phase = original_snapshot["global_phase"]
	new_snapshot = Kernel.mr_escalate_phase(original_snapshot, Kernel.Phase.ACTIVE)
	var original_phase_after = original_snapshot["global_phase"]
	
	_record_test("1.2: mr_escalate_phase immutability",
		original_phase == original_phase_after,
		"Original snapshot mutated" if original_phase != original_phase_after else "")
	
	# Test 1.3: mr_modify_federation_alignment doesn't mutate input
	original_snapshot = Kernel.mr_create_snapshot()
	var original_fed = original_snapshot["federation_alignment"]
	new_snapshot = Kernel.mr_modify_federation_alignment(original_snapshot, 0.3)
	var original_fed_after = original_snapshot["federation_alignment"]
	
	_record_test("1.3: mr_modify_federation_alignment immutability",
		original_fed == original_fed_after,
		"Original snapshot mutated" if original_fed != original_fed_after else "")

# ============================================================================
# INVARIANT 2: DETERMINISM
# ============================================================================

func _test_invariant_2_determinism() -> void:
	"""Test that kernel functions are deterministic"""
	print("\n[INVARIANT 2] Testing Determinism...")
	
	# Test 2.1: Same inputs produce same outputs
	var snapshot1 = Kernel.mr_create_snapshot()
	var snapshot2 = Kernel.mr_create_snapshot()
	
	_record_test("2.1: mr_create_snapshot determinism",
		_snapshots_equal(snapshot1, snapshot2),
		"Snapshots not identical" if not _snapshots_equal(snapshot1, snapshot2) else "")
	
	# Test 2.2: Influence modification determinism
	var base = Kernel.mr_create_snapshot()
	var result1 = Kernel.mr_set_faction_influence(base, Kernel.FactionID.NORDICS, 0.42)
	var result2 = Kernel.mr_set_faction_influence(base, Kernel.FactionID.NORDICS, 0.42)
	
	_record_test("2.2: mr_set_faction_influence determinism",
		_snapshots_equal(result1, result2),
		"Different outputs for same input" if not _snapshots_equal(result1, result2) else "")
	
	# Test 2.3: Phase escalation determinism
	base = Kernel.mr_create_snapshot()
	result1 = Kernel.mr_escalate_phase(base, Kernel.Phase.ACTIVE)
	result2 = Kernel.mr_escalate_phase(base, Kernel.Phase.ACTIVE)
	
	_record_test("2.3: mr_escalate_phase determinism",
		_snapshots_equal(result1, result2),
		"Different outputs for same input" if not _snapshots_equal(result1, result2) else "")

# ============================================================================
# INVARIANT 3: CONTRACT COMPLIANCE
# ============================================================================

func _test_invariant_3_contract_compliance() -> void:
	"""Test that adapter enforces contracts correctly"""
	print("\n[INVARIANT 3] Testing Contract Compliance...")
	
	# Test 3.1: Invalid faction ID rejected
	var result = _adapter.modify_faction_influence(999, 0.1, "test")
	_record_test("3.1: Invalid faction ID rejected",
		not result,
		"Invalid faction ID not rejected" if result else "")
	
	# Test 3.2: Out-of-bounds influence delta rejected
	result = _adapter.modify_faction_influence(Kernel.FactionID.PLEADIANS, 2.0, "test")
	_record_test("3.2: Out-of-bounds delta rejected",
		not result,
		"Out-of-bounds delta not rejected" if result else "")
	
	# Test 3.3: Constraint violation detected (Dragons non-recruitable)
	var interaction_result = _adapter.attempt_interaction(Kernel.FactionID.DRAGONS, "recruit")
	_record_test("3.3: Dragon recruit constraint enforced",
		not interaction_result["success"],
		"Dragon recruit not blocked" if interaction_result["success"] else "")
	
	# Test 3.4: Valid operations succeed
	result = _adapter.modify_faction_influence(Kernel.FactionID.MARTIANS, 0.3, "test")
	_record_test("3.4: Valid influence modification succeeds",
		result,
		"Valid operation failed" if not result else "")
	
	# Test 3.5: Phase escalation validation
	result = _adapter.escalate_to_phase(Kernel.Phase.DORMANT) # Invalid (can't go backwards)
	_record_test("3.5: Backward phase escalation rejected",
		not result,
		"Backward phase escalation not rejected" if result else "")

# ============================================================================
# INVARIANT 4: BOUNDS ENFORCEMENT
# ============================================================================

func _test_invariant_4_bounds_enforcement() -> void:
	"""Test that all values stay within defined bounds"""
	print("\n[INVARIANT 4] Testing Bounds Enforcement...")
	
	# Test 4.1: Influence clamped to [-1.0, 1.0]
	_adapter.modify_faction_influence(Kernel.FactionID.PLEADIANS, 0.8, "test")
	_adapter.modify_faction_influence(Kernel.FactionID.PLEADIANS, 0.8, "test") # Should clamp
	var influence = _adapter.get_faction_state(Kernel.FactionID.PLEADIANS)["influence"]
	_record_test("4.1: Influence clamped to bounds",
		influence >= -1.0 and influence <= 1.0,
		"Influence out of bounds: %.2f" % influence if influence < -1.0 or influence > 1.0 else "")
	
	# Test 4.2: Federation alignment clamped to [-1.0, 1.0]
	_adapter.modify_federation_alignment(0.9, "test")
	_adapter.modify_federation_alignment(0.9, "test") # Should clamp
	var fed_alignment = _adapter.get_federation_alignment()
	_record_test("4.2: Federation alignment clamped",
		fed_alignment >= -1.0 and fed_alignment <= 1.0,
		"Federation alignment out of bounds: %.2f" % fed_alignment if fed_alignment < -1.0 or fed_alignment > 1.0 else "")
	
	# Test 4.3: Graviton pressure clamped to [0.0, 1.0]
	_adapter.increase_graviton_pressure(0.7, "test")
	_adapter.increase_graviton_pressure(0.7, "test") # Should clamp
	var grav_pressure = _adapter.get_graviton_pressure()
	_record_test("4.3: Graviton pressure clamped",
		grav_pressure >= 0.0 and grav_pressure <= 1.0,
		"Graviton pressure out of bounds: %.2f" % grav_pressure if grav_pressure < 0.0 or grav_pressure > 1.0 else "")
	
	# Test 4.4: Snapshot validation after operations
	var snapshot = _adapter.export_snapshot()
	_record_test("4.4: Snapshot validates after operations",
		Kernel.validate_snapshot(snapshot),
		"Snapshot validation failed" if not Kernel.validate_snapshot(snapshot) else "")

# ============================================================================
# INVARIANT 5: PHASE COHERENCE
# ============================================================================

func _test_invariant_5_phase_coherence() -> void:
	"""Test that phase transitions maintain coherence"""
	print("\n[INVARIANT 5] Testing Phase Coherence...")
	
	# Test 5.1: Phase escalation updates all factions
	_adapter.escalate_to_phase(Kernel.Phase.ACTIVE)
	var all_factions = _adapter.get_all_factions_summary()
	var all_in_phase = all_factions.all(func(f): return f["phase"] == Kernel.Phase.ACTIVE)
	_record_test("5.1: All factions updated on phase escalation",
		all_in_phase,
		"Not all factions in ACTIVE phase" if not all_in_phase else "")
	
	# Test 5.2: Interaction modes update with phase
	var dragon_modes_active = _adapter.check_interaction_available(Kernel.FactionID.DRAGONS, "quest_assign")
	_record_test("5.2: Dragon quest_assign available in ACTIVE phase",
		dragon_modes_active,
		"Dragon quest_assign not available in ACTIVE" if not dragon_modes_active else "")
	
	# Test 5.3: Ethereal Keepers respect layer constraints
	var keeper_interaction = _adapter.attempt_interaction(Kernel.FactionID.ETHEREAL_KEEPERS, "quest_assign")
	var material_layer_blocked = not keeper_interaction["success"]
	_record_test("5.3: Ethereal Keepers blocked in Material layer",
		material_layer_blocked,
		"Ethereal Keepers can quest in Material layer" if not material_layer_blocked else "")
	
	# Test 5.4: Layer unlock enables access
	_adapter.unlock_layer(Kernel.Layer.ETHEREAL)
	var ethereal_accessible = _adapter.is_layer_accessible(Kernel.Layer.ETHEREAL)
	_record_test("5.4: Layer unlock enables access",
		ethereal_accessible,
		"Ethereal layer not accessible after unlock" if not ethereal_accessible else "")
	
	# Test 5.5: Graviton enforcement activates at threshold
	_adapter.escalate_to_phase(Kernel.Phase.ENFORCING)
	_adapter.increase_graviton_pressure(0.85, "test") # Above 0.8 threshold
	var graviton_modes = Kernel.mr_get_interaction_modes(_adapter.export_snapshot(), Kernel.FactionID.GRAVITONS)
	var enforcing = "hard_override" in graviton_modes
	_record_test("5.5: Graviton enforcement activates at high pressure",
		enforcing,
		"Graviton hard_override not active at high pressure" if not enforcing else "")

# ============================================================================
# TEST HELPERS
# ============================================================================

func _record_test(test_name: String, passed: bool, reason: String = "") -> void:
	"""Record test result"""
	_test_results.append({
		"test": test_name,
		"passed": passed,
		"reason": reason,
	})
	var status = "✓" if passed else "✗"
	print("  %s %s" % [status, test_name])
	if not passed and reason:
		print("    Reason: %s" % reason)

func _snapshots_equal(s1: Dictionary, s2: Dictionary) -> bool:
	"""Deep equality check for snapshots"""
	# Quick hash comparison
	return str(s1) == str(s2)

# ============================================================================
# STANDALONE USAGE
# ============================================================================

func _ready() -> void:
	# Auto-run if this is the main scene
	if get_tree().current_scene == self:
		await get_tree().create_timer(0.1).timeout
		var result = run_full_validation()
		if result["invariants_ok"]:
			print("\n✓✓✓ FACTION3D SUBSYSTEM VALIDATED ✓✓✓")
			print("Ready for runtime integration")
		else:
			print("\n✗✗✗ VALIDATION FAILED ✗✗✗")
			print("Fix errors before integration")
		
		# Exit after validation
		get_tree().quit()
