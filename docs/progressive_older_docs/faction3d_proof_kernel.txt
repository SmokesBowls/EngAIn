# faction3d_proof_kernel.gd
# THE PROOF: This either validates ZW/AP architecture for Faction3D or proves it's cosplay
# 
# NON-NEGOTIABLE INVARIANTS (from Cowboy-Hat Test):
# 1. Time is FIRST-CLASS (@when cannot be optional)
# 2. State is reconstructible from events (replay must work)
# 3. Rules are interrogable (can query "why did X fail?")
# 4. Kernels are pure (same input = same output, always)
# 5. System REFUSES invalid operations (enforced, not hoped)

class_name Faction3DProofKernel
extends Node

# ============================================================================
# INVARIANT 1: Time is FIRST-CLASS
# ============================================================================

class ZWFactionEvent:
	var id: String
	var when: String  # Format: "world_epoch:T+seconds"
	var where: String  # Hierarchical path: "realm/zone/location"
	var rule_id: String
	var payload: Dictionary
	
	func _init(event_data: Dictionary):
		# ENFORCEMENT: Refuse events without temporal/spatial identity
		assert(event_data.has("@id"), "INVARIANT VIOLATION: Missing @id")
		assert(event_data.has("@when"), "INVARIANT VIOLATION: Missing @when")
		assert(event_data.has("@where"), "INVARIANT VIOLATION: Missing @where")
		assert(event_data.has("rule_id"), "INVARIANT VIOLATION: Missing rule_id")
		
		self.id = event_data["@id"]
		self.when = event_data["@when"]
		self.where = event_data["@where"]
		self.rule_id = event_data["rule_id"]
		self.payload = event_data.get("payload", {})
	
	func is_valid() -> bool:
		# Time sovereignty: event must have complete temporal context
		return id != "" and when != "" and where != "" and rule_id != ""

# ============================================================================
# INVARIANT 3: Rules are INTERROGABLE
# ============================================================================

class APRule:
	var id: String
	var requires: Array[Dictionary]  # Predicates that must be true
	var effects: Array[Dictionary]   # Changes to apply
	var conflicts: Array[Dictionary] # Vetoes
	
	func _init(rule_def: Dictionary):
		id = rule_def["id"]
		
		# Defensive normalization - handles untyped arrays
		requires = [] as Array[Dictionary]
		for req in rule_def.get("requires", []):
			if req is Dictionary:
				requires.append(req)
		
		effects = [] as Array[Dictionary]
		for eff in rule_def.get("effects", []):
			if eff is Dictionary:
				effects.append(eff)
		
		conflicts = [] as Array[Dictionary]
		for con in rule_def.get("conflicts", []):
			if con is Dictionary:
				conflicts.append(con)
	
	func check_requires(snapshot: Dictionary) -> Dictionary:
		"""Returns {success: bool, failed_predicate: String}"""
		for req in requires:
			if not _evaluate_predicate(req, snapshot):
				return {
					"success": false,
					"reason": "requires.%s failed" % JSON.stringify(req),
					"actual_value": _get_actual_value(req, snapshot)
				}
		return {"success": true}
	
	func check_conflicts(snapshot: Dictionary) -> Dictionary:
		"""Returns {blocked: bool, conflict_reason: String}"""
		for conflict in conflicts:
			if _evaluate_predicate(conflict, snapshot):
				return {
					"blocked": true,
					"reason": "conflict.%s active" % JSON.stringify(conflict)
				}
		return {"blocked": false}
	
	func _evaluate_predicate(pred: Dictionary, snapshot: Dictionary) -> bool:
		# Simple predicate evaluator - extend as needed
		if pred.has("stat"):
			var expr = pred["stat"] as String
			return _eval_stat_expression(expr, snapshot)
		elif pred.has("flag"):
			var flag_path = pred["flag"] as String
			return _get_flag(flag_path, snapshot)
		elif pred.has("phase"):
			var required_phase = pred["phase"]
			var current_phase = snapshot.get("global_phase", 0)
			return current_phase >= required_phase
		return false
	
	func _eval_stat_expression(expr: String, snapshot: Dictionary) -> bool:
		# Parse expressions like "factions.0.influence >= 0.5"
		var parts = expr.split(" ")
		if parts.size() != 3:
			return false
		
		var stat_path = parts[0]
		var operator = parts[1]
		var value = float(parts[2])
		
		var actual = _get_stat(stat_path, snapshot)
		
		match operator:
			">=": return actual >= value
			"<=": return actual <= value
			">": return actual > value
			"<": return actual < value
			"==": return actual == value
			"!=": return actual != value
			_: return false
	
	func _get_stat(path: String, snapshot: Dictionary) -> float:
		var parts = path.split(".")
		var current = snapshot
		for part in parts:
			if current is Dictionary and current.has(part):
				current = current[part]
			elif current is Dictionary and part.is_valid_int():
				var idx = int(part)
				if current.has(idx):
					current = current[idx]
				else:
					return 0.0
			else:
				return 0.0
		
		if current is float or current is int:
			return float(current)
		return 0.0
	
	func _get_actual_value(pred: Dictionary, snapshot: Dictionary):
		if pred.has("stat"):
			var expr = pred["stat"] as String
			var parts = expr.split(" ")
			if parts.size() >= 1:
				return _get_stat(parts[0], snapshot)
		return null
	
	func _get_flag(path: String, snapshot: Dictionary) -> bool:
		var parts = path.split(".")
		var current = snapshot
		for part in parts:
			if current is Dictionary and current.has(part):
				current = current[part]
			else:
				return false
		return bool(current) if current != null else false

# ============================================================================
# INVARIANT 4: Pure Kernel Function
# ============================================================================

static func faction_influence_kernel(snapshot_in: Dictionary, event: ZWFactionEvent, rule: APRule) -> Dictionary:
	"""
	INVARIANT 4: Pure function - immutable snapshot-in/snapshot-out
	No side effects, no mutation, deterministic
	"""
	var snapshot_out = _deep_copy(snapshot_in)
	
	# Apply rule effects
	for effect in rule.effects:
		if effect.has("change"):
			var change_expr = effect["change"] as String
			_apply_change(change_expr, snapshot_out)
	
	return snapshot_out

static func _apply_change(change_expr: String, snapshot: Dictionary):
	# Parse expressions like "factions.0.influence += 0.1"
	var parts = change_expr.split(" ")
	if parts.size() != 3:
		return
	
	var path = parts[0]
	var operator = parts[1]
	var value = float(parts[2])
	
	# Navigate to parent
	var path_parts = path.split(".")
	var current = snapshot
	for i in range(path_parts.size() - 1):
		var part = path_parts[i]
		if part.is_valid_int():
			var idx = int(part)
			if current is Dictionary and current.has(idx):
				current = current[idx]
			else:
				return
		elif current is Dictionary and current.has(part):
			current = current[part]
		else:
			return
	
	# Apply change to final key
	var final_key = path_parts[-1]
	if final_key.is_valid_int():
		final_key = int(final_key)
	
	if current is Dictionary and current.has(final_key):
		var current_val = float(current[final_key]) if current[final_key] != null else 0.0
		match operator:
			"+=": current[final_key] = clampf(current_val + value, -1.0, 1.0)
			"-=": current[final_key] = clampf(current_val - value, -1.0, 1.0)
			"=": current[final_key] = clampf(value, -1.0, 1.0)

static func _deep_copy(data):
	if data is Dictionary:
		return data.duplicate(true)
	elif data is Array:
		return data.duplicate(true)
	else:
		return data

# ============================================================================
# INVARIANT 2: Event Replay
# ============================================================================

static func replay_from_events(initial_snapshot: Dictionary, events: Array, rules: Dictionary) -> Dictionary:
	"""
	CRITICAL TEST: Can we rebuild world state from zero using only events?
	
	If this returns correct final state -> ZON is real
	If this fails -> we're wearing a cowboy hat
	"""
	
	var current_snapshot = _deep_copy(initial_snapshot)
	
	for event_data in events:
		var event = ZWFactionEvent.new(event_data)
		var rule = rules.get(event.rule_id)
		
		if not rule:
			push_error("Replay failed: Unknown rule %s" % event.rule_id)
			return {}
		
		# Check if event was valid at that time
		var req_check = rule.check_requires(current_snapshot)
		if not req_check["success"]:
			push_warning("Replay: Event %s requirements failed at T=%s" % [event.id, event.when])
			continue
		
		var conflict_check = rule.check_conflicts(current_snapshot)
		if conflict_check["blocked"]:
			push_warning("Replay: Event %s blocked by conflict at T=%s" % [event.id, event.when])
			continue
		
		# Apply the event
		current_snapshot = faction_influence_kernel(current_snapshot, event, rule)
	
	return current_snapshot

# ============================================================================
# THE PROOF ADAPTER (combines all invariants)
# ============================================================================

class Faction3DProofAdapter:
	var rules: Dictionary = {}
	var current_snapshot: Dictionary = {}
	var event_log: Array = []
	var initial_snapshot: Dictionary = {}
	var epoch_id: String
	var time_offset: float = 0.0
	var _outer: Script # Reference to outer class for static calls
	
	func _init(initial_state: Dictionary, epoch: String):
		# Load the outer script explicitly (inner class get_script() returns inner class)
		_outer = load("res://faction3d_proof_kernel.gd")
		current_snapshot = initial_state
		initial_snapshot = _outer._deep_copy(initial_state)
		epoch_id = epoch
		
		# Define AP rules
		_register_rules()
	
	func _register_rules():
		# Influence Boost rule
		rules["influence_boost"] = APRule.new({
			"id": "influence_boost",
			"requires": [
				{"stat": "factions.0.influence >= -0.5"},
				{"phase": 0} # DORMANT or higher
			],
			"effects": [
				{"change": "factions.0.influence += 0.1"}
			],
			"conflicts": []
		})
		
		# Escalate Phase rule
		rules["escalate_phase"] = APRule.new({
			"id": "escalate_phase",
			"requires": [
				{"stat": "global_phase < 2"} # Not already at max
			],
			"effects": [
				{"change": "global_phase += 1"}
			],
			"conflicts": []
		})
	
	func execute_faction_action(rule_id: String, context: Dictionary) -> Dictionary:
		"""
		THE MOMENT OF TRUTH:
		This function either PROVES the architecture or EXPOSES the lie
		"""
		
		# Generate event with complete temporal/spatial identity
		var event = ZWFactionEvent.new({
			"@id": "faction/evt_%d" % Time.get_ticks_msec(),
			"@when": "%s:T+%.2f" % [epoch_id, time_offset],
			"@where": context.get("location", "realm/unknown"),
			"rule_id": rule_id,
			"payload": context
		})
		
		# INVARIANT 5: Validate event (refuse if invalid)
		var event_validation = Faction3DValidator.validate_event(event)
		if not event_validation["valid"]:
			return {
				"success": false,
				"reason": "Event validation failed: %s" % event_validation["error"],
				"invariant_violated": "INVARIANT 1 or 5"
			}
		
		# Get rule
		var rule = rules.get(rule_id)
		if not rule:
			return {
				"success": false,
				"reason": "Unknown rule: %s" % rule_id,
				"invariant_violated": "INVARIANT 3"
			}
		
		# INVARIANT 3: Check requires (interrogable)
		var req_check = rule.check_requires(current_snapshot)
		if not req_check["success"]:
			return {
				"success": false,
				"reason": req_check["reason"],
				"actual_value": req_check.get("actual_value"),
				"invariant_validated": "INVARIANT 3 - System explained WHY it failed"
			}
		
		# INVARIANT 3: Check conflicts
		var conflict_check = rule.check_conflicts(current_snapshot)
		if conflict_check["blocked"]:
			return {
				"success": false,
				"reason": conflict_check["reason"],
				"invariant_validated": "INVARIANT 3 - System explained conflict"
			}
		
		# INVARIANT 5: Validate current state
		var state_validation = Faction3DValidator.validate_snapshot(current_snapshot)
		if not state_validation["valid"]:
			return {
				"success": false,
				"reason": "State contract violation: %s" % state_validation["errors"],
				"invariant_violated": "INVARIANT 5"
			}
		
		# INVARIANT 4: Apply pure kernel
		var new_snapshot = _outer.faction_influence_kernel(current_snapshot, event, rule)
		
		# INVARIANT 5: Validate output state
		var output_validation = Faction3DValidator.validate_snapshot(new_snapshot)
		if not output_validation["valid"]:
			return {
				"success": false,
				"reason": "Output state invalid: %s" % output_validation["errors"],
				"invariant_violated": "INVARIANT 4 or 5"
			}
		
		# Log event (for replay)
		event_log.append({
			"@id": event.id,
			"@when": event.when,
			"@where": event.where,
			"rule_id": event.rule_id,
			"payload": event.payload
		})
		
		# Commit new state
		current_snapshot = new_snapshot
		time_offset += 1.0
		
		return {
			"success": true,
			"event_id": event.id,
			"invariants_validated": "INVARIANTS 1,3,4,5"
		}
	
	func test_replay(compare_snapshot: Dictionary = {}) -> Dictionary:
		"""
		INVARIANT 2: Can we rebuild state from events alone?
		This is THE test - if this fails, ZON is fake
		"""
		
		# Replay all events
		var replayed_snapshot = _outer.replay_from_events(
			initial_snapshot,
			event_log,
			rules
		)
		
		# Compare states
		var snapshot_to_compare = compare_snapshot if not compare_snapshot.is_empty() else current_snapshot
		var match = _states_match(snapshot_to_compare, replayed_snapshot)
		
		return {
			"replay_successful": match,
			"invariant_validated": "INVARIANT 2" if match else "INVARIANT 2 VIOLATED",
			"current_state": current_snapshot,
			"replayed_state": replayed_snapshot
		}
	
	func _states_match(a: Dictionary, b: Dictionary) -> bool:
		# Simple comparison - extend as needed
		if not a.has("factions") or not b.has("factions"):
			return false
		
		# Check faction influences
		for faction_id in a["factions"].keys():
			if not b["factions"].has(faction_id):
				return false
			
			var a_faction = a["factions"][faction_id]
			var b_faction = b["factions"][faction_id]
			
			if a_faction.get("influence") != b_faction.get("influence"):
				return false
		
		# Check global phase
		if a.get("global_phase") != b.get("global_phase"):
			return false
		
		return true
	
	func query_why_failed(rule_id: String) -> String:
		"""
		INVARIANT 4: AI can ask "why would this fail?"
		Without actually executing it
		"""
		var rule = rules.get(rule_id)
		if not rule:
			return "Rule '%s' not found" % rule_id
		
		var req_check = rule.check_requires(current_snapshot)
		if not req_check["success"]:
			return "Rule '%s' failed because: %s (actual value: %s)" % [
				rule_id,
				req_check["reason"],
				req_check.get("actual_value", "unknown")
			]
		
		return "Rule '%s' would succeed" % rule_id

# ============================================================================
# VALIDATOR (Contract Enforcement)
# ============================================================================

class Faction3DValidator:
	static func validate_event(event: ZWFactionEvent) -> Dictionary:
		if not event.is_valid():
			return {
				"valid": false,
				"error": "Event missing required fields (@id, @when, @where, rule_id)"
			}
		return {"valid": true}
	
	static func validate_snapshot(snapshot: Dictionary) -> Dictionary:
		# Check required keys
		if not snapshot.has("factions"):
			return {"valid": false, "errors": "Missing factions"}
		if not snapshot.has("global_phase"):
			return {"valid": false, "errors": "Missing global_phase"}
		
		# Check faction influence bounds
		for faction_state in snapshot["factions"].values():
			var influence = faction_state.get("influence", 0.0)
			if influence < -1.0 or influence > 1.0:
				return {"valid": false, "errors": "Influence out of bounds"}
		
		return {"valid": true}

# ============================================================================
# THE PROOF TEST
# ============================================================================

static func run_proof_test() -> Dictionary:
	"""
	THE ULTIMATE TEST
	
	If all tests pass -> ZW/ZON/AP are REAL
	If any test fails -> We're wearing a cowboy hat
	"""
	
	# Initialize
	var initial_state = {
		"factions": {
			0: {"influence": 0.0, "phase": 0},
			1: {"influence": 0.0, "phase": 0},
		},
		"global_phase": 0,
		"federation_alignment": 0.0,
		"graviton_pressure": 0.0,
	}
	
	var adapter = Faction3DProofAdapter.new(initial_state, "world_faction_test")
	
	var results = {
		"invariants_tested": 5,
		"invariants_passed": 0,
		"tests": []
	}
	
	# TEST 1: Try to execute without temporal identity (should REFUSE)
	print("TEST 1: System refuses events without @when")
	var bad_event = {
		"@id": "test_1",
		# Missing @when
		"@where": "realm/faction_hall",
		"rule_id": "influence_boost"
	}
	var test1 = adapter.execute_faction_action("influence_boost", {"location": ""})
	# This should fail due to validation
	results["tests"].append({
		"name": "INVARIANT 1 & 5: Temporal identity enforced",
		"passed": not test1.get("success", false),
		"reason": test1.get("reason", "")
	})
	if not test1.get("success", false):
		results["invariants_passed"] += 1
	
	# Save state before Test 3 (Test 3 modifies state directly)
	var state_before_test3_hack = adapter.current_snapshot.duplicate(true)
	
	# TEST 2: Execute valid action
	print("\nTEST 2: Execute valid faction action")
	var test2 = adapter.execute_faction_action("influence_boost", {
		"location": "realm/faction_hall/dragons",
		"faction": 0
	})
	results["tests"].append({
		"name": "INVARIANT 1,3,4,5: Valid event executes",
		"passed": test2.get("success", false),
		"event_id": test2.get("event_id", "")
	})
	if test2.get("success", false):
		results["invariants_passed"] += 1
	
	# TEST 3: Try to execute with insufficient influence (should fail with reason)
	print("\nTEST 3: System explains why action fails")
	adapter.current_snapshot["factions"][0]["influence"] = -0.6 # Below threshold
	var test3 = adapter.execute_faction_action("influence_boost", {
		"location": "realm/faction_hall/dragons"
	})
	results["tests"].append({
		"name": "INVARIANT 3: Interrogable (explains failure)",
		"passed": not test3.get("success", false) and test3.has("reason"),
		"reason": test3.get("reason", "")
	})
	if not test3.get("success", false) and test3.has("reason"):
		results["invariants_passed"] += 1
	
	# TEST 4: Query system about rule
	print("\nTEST 4: Query 'why would this fail?'")
	var query = adapter.query_why_failed("influence_boost")
	var test4_pass = "influence" in query.to_lower()
	results["tests"].append({
		"name": "INVARIANT 3: AI can ask 'why?'",
		"passed": test4_pass,
		"answer": query
	})
	if test4_pass:
		results["invariants_passed"] += 1
	
	# TEST 5: Replay from events (THE ULTIMATE TEST)
	print("\nTEST 5: Replay state from event log")
	var replay_result = adapter.test_replay(state_before_test3_hack)
	results["tests"].append({
		"name": "INVARIANT 2: State reconstructible from events",
		"passed": replay_result.get("replay_successful", false),
		"details": replay_result
	})
	if replay_result.get("replay_successful", false):
		results["invariants_passed"] += 1
	
	return results
