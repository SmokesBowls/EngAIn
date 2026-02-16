# faction3d_adapter.gd
# Deep contract adapter for Faction3D subsystem
# Wraps faction3d_kernel.gd with AP validation, state persistence, and delta queuing
# Pattern: Contract enforcement → kernel call → state sync → delta queue

class_name Faction3DAdapter
extends Node

# ============================================================================
# DEPENDENCIES
# ============================================================================

const Kernel = preload("res://faction3d_kernel.gd")

# ============================================================================
# STATE
# ============================================================================

var _current_snapshot: Dictionary = {}
var _delta_queue: Array = []
var _contract_violations: Array = []

# ============================================================================
# INITIALIZATION
# ============================================================================

func _ready() -> void:
	_current_snapshot = Kernel.mr_create_snapshot()
	print("[Faction3D] Adapter initialized with %d factions" % Kernel.FactionID.size())

# ============================================================================
# PUBLIC API (Contract-Validated)
# ============================================================================

func get_faction_state(faction_id: int) -> Dictionary:
	"""Get current state of a faction"""
	_validate_faction_id(faction_id)
	return Kernel.mr_get_faction_state(_current_snapshot, faction_id)

func modify_faction_influence(faction_id: int, delta: float, reason: String) -> bool:
	"""Modify faction influence with AP validation"""
	# AP Contract: Valid faction ID
	if not _validate_faction_id(faction_id):
		return false
	
	# AP Contract: Bounded delta
	if abs(delta) > 1.0:
		_log_violation("influence_delta_out_of_bounds", {"faction": faction_id, "delta": delta})
		return false
	
	# Call kernel
	var new_snapshot = Kernel.mr_set_faction_influence(_current_snapshot, faction_id, delta)
	
	# Validate new state
	if not Kernel.validate_snapshot(new_snapshot):
		_log_violation("snapshot_invalid_after_influence_change", {"faction": faction_id})
		return false
	
	# Commit
	_commit_snapshot(new_snapshot, {
		"action": "modify_influence",
		"faction": faction_id,
		"delta": delta,
		"reason": reason,
	})
	
	return true

func check_interaction_available(faction_id: int, interaction_mode: String) -> bool:
	"""Check if an interaction mode is currently available for a faction"""
	_validate_faction_id(faction_id)
	
	var modes = Kernel.mr_get_interaction_modes(_current_snapshot, faction_id)
	return interaction_mode in modes

func attempt_interaction(faction_id: int, action: String) -> Dictionary:
	"""Attempt faction interaction with constraint checking"""
	# AP Contract: Valid faction
	if not _validate_faction_id(faction_id):
		return {"success": false, "reason": "invalid_faction_id"}
	
	# AP Contract: Check constraints
	if Kernel.mr_check_constraint_violated(_current_snapshot, faction_id, action):
		_log_violation("constraint_violated", {"faction": faction_id, "action": action})
		return {"success": false, "reason": "constraint_violation"}
	
	# AP Contract: Check phase visibility
	var global_phase = _current_snapshot.get("global_phase", Kernel.Phase.DORMANT)
	if not Kernel.mr_check_phase_visibility(_current_snapshot, faction_id, global_phase):
		return {"success": false, "reason": "faction_not_visible_in_phase"}
	
	# AP Contract: Check interaction mode available
	var available_modes = Kernel.mr_get_interaction_modes(_current_snapshot, faction_id)
	if action not in available_modes:
		return {"success": false, "reason": "interaction_mode_not_available"}
	
	# Success
	_queue_delta({
		"type": "interaction",
		"faction": faction_id,
		"action": action,
		"timestamp": Time.get_ticks_msec(),
	})
	
	return {"success": true, "modes": available_modes}

func escalate_to_phase(target_phase: int) -> bool:
	"""Escalate game to new phase (major state transition)"""
	# AP Contract: Valid phase progression
	var current_phase = _current_snapshot.get("global_phase", Kernel.Phase.DORMANT)
	if target_phase <= current_phase:
		_log_violation("invalid_phase_escalation", {"current": current_phase, "target": target_phase})
		return false
	
	# Call kernel
	var new_snapshot = Kernel.mr_escalate_phase(_current_snapshot, target_phase)
	
	# Validate
	if not Kernel.validate_snapshot(new_snapshot):
		_log_violation("snapshot_invalid_after_phase_escalation", {"target_phase": target_phase})
		return false
	
	# Commit
	_commit_snapshot(new_snapshot, {
		"action": "escalate_phase",
		"from_phase": current_phase,
		"to_phase": target_phase,
	})
	
	print("[Faction3D] Phase escalated: %s → %s" % [
		Kernel.Phase.keys()[current_phase],
		Kernel.Phase.keys()[target_phase]
	])
	
	return true

func modify_federation_alignment(delta: float, reason: String) -> bool:
	"""Modify Federation alignment (volatile)"""
	# AP Contract: Bounded delta
	if abs(delta) > 1.0:
		_log_violation("federation_delta_out_of_bounds", {"delta": delta})
		return false
	
	# Call kernel
	var new_snapshot = Kernel.mr_modify_federation_alignment(_current_snapshot, delta)
	
	# Validate
	if not Kernel.validate_snapshot(new_snapshot):
		_log_violation("snapshot_invalid_after_federation_change", {})
		return false
	
	# Commit
	_commit_snapshot(new_snapshot, {
		"action": "modify_federation_alignment",
		"delta": delta,
		"reason": reason,
		"new_alignment": new_snapshot["federation_alignment"],
	})
	
	return true

func increase_graviton_pressure(delta: float, source: String) -> bool:
	"""Increase graviton pressure (physics abuse accumulator)"""
	# AP Contract: Positive delta only
	if delta < 0.0:
		_log_violation("negative_graviton_pressure_delta", {"delta": delta})
		return false
	
	# Call kernel
	var new_snapshot = Kernel.mr_increase_graviton_pressure(_current_snapshot, delta)
	
	# Validate
	if not Kernel.validate_snapshot(new_snapshot):
		_log_violation("snapshot_invalid_after_graviton_pressure", {})
		return false
	
	# Commit
	_commit_snapshot(new_snapshot, {
		"action": "increase_graviton_pressure",
		"delta": delta,
		"source": source,
		"new_pressure": new_snapshot["graviton_pressure"],
	})
	
	# Warning if approaching threshold
	if new_snapshot["graviton_pressure"] >= 0.7:
		print("[Faction3D] WARNING: Graviton pressure at %.1f%% - enforcement imminent" % 
			(new_snapshot["graviton_pressure"] * 100.0))
	
	return true

func unlock_layer(layer: int) -> bool:
	"""Unlock a new layer (requires traversal)"""
	# AP Contract: Valid layer
	if layer < 0 or layer >= Kernel.Layer.size():
		_log_violation("invalid_layer_id", {"layer": layer})
		return false
	
	# AP Contract: Not already unlocked
	if Kernel.mr_check_layer_accessible(_current_snapshot, layer):
		return true # Already unlocked, no-op
	
	# Call kernel
	var new_snapshot = Kernel.mr_unlock_layer(_current_snapshot, layer)
	
	# Validate
	if not Kernel.validate_snapshot(new_snapshot):
		_log_violation("snapshot_invalid_after_layer_unlock", {"layer": layer})
		return false
	
	# Commit
	_commit_snapshot(new_snapshot, {
		"action": "unlock_layer",
		"layer": layer,
		"layer_name": Kernel.Layer.keys()[layer],
	})
	
	print("[Faction3D] Layer unlocked: %s" % Kernel.Layer.keys()[layer])
	
	return true

func get_faction_relationships(faction_id: int) -> Dictionary:
	"""Get faction alliances and rivalries"""
	_validate_faction_id(faction_id)
	return Kernel.mr_get_faction_relationships(_current_snapshot, faction_id)

func get_global_phase() -> int:
	"""Get current global phase"""
	return _current_snapshot.get("global_phase", Kernel.Phase.DORMANT)

func get_federation_alignment() -> float:
	"""Get current Federation alignment"""
	return _current_snapshot.get("federation_alignment", 0.0)

func get_graviton_pressure() -> float:
	"""Get current graviton pressure"""
	return _current_snapshot.get("graviton_pressure", 0.0)

func is_layer_accessible(layer: int) -> bool:
	"""Check if layer is accessible"""
	return Kernel.mr_check_layer_accessible(_current_snapshot, layer)

func get_all_factions_summary() -> Array:
	"""Get summary of all factions"""
	var summary := []
	for faction_id in Kernel.FactionID.values():
		var state = Kernel.mr_get_faction_state(_current_snapshot, faction_id)
		var def = Kernel.FACTION_DEFS.get(faction_id, {})
		summary.append({
			"id": faction_id,
			"name": def.get("name", "Unknown"),
			"influence": state.get("influence", 0.0),
			"phase": state.get("phase", Kernel.Phase.DORMANT),
			"layer": def.get("layer", -1),
			"alignment": def.get("alignment", -1),
		})
	return summary

# ============================================================================
# STATE MANAGEMENT
# ============================================================================

func _commit_snapshot(new_snapshot: Dictionary, delta_info: Dictionary) -> void:
	"""Commit new snapshot and queue delta"""
	_current_snapshot = new_snapshot
	_queue_delta(delta_info)

func _queue_delta(delta: Dictionary) -> void:
	"""Queue delta for event system"""
	delta["timestamp"] = Time.get_ticks_msec()
	_delta_queue.append(delta)

func flush_deltas() -> Array:
	"""Flush delta queue and return all deltas"""
	var deltas = _delta_queue.duplicate()
	_delta_queue.clear()
	return deltas

func export_snapshot() -> Dictionary:
	"""Export current snapshot (for save/load)"""
	return _current_snapshot.duplicate(true)

func import_snapshot(snapshot: Dictionary) -> bool:
	"""Import snapshot (for save/load)"""
	# AP Contract: Validate snapshot
	if not Kernel.validate_snapshot(snapshot):
		_log_violation("imported_snapshot_invalid", {})
		return false
	
	_current_snapshot = snapshot.duplicate(true)
	print("[Faction3D] Snapshot imported successfully")
	return true

# ============================================================================
# VALIDATION HELPERS
# ============================================================================

func _validate_faction_id(faction_id: int) -> bool:
	"""Validate faction ID exists"""
	if faction_id < 0 or faction_id >= Kernel.FactionID.size():
		_log_violation("invalid_faction_id", {"id": faction_id})
		return false
	return true

func _log_violation(violation_type: String, context: Dictionary) -> void:
	"""Log contract violation"""
	var violation = {
		"type": violation_type,
		"context": context,
		"timestamp": Time.get_ticks_msec(),
	}
	_contract_violations.append(violation)
	print("[Faction3D] CONTRACT VIOLATION: %s - %s" % [violation_type, str(context)])

func get_contract_violations() -> Array:
	"""Get all contract violations"""
	return _contract_violations.duplicate()

func clear_contract_violations() -> void:
	"""Clear violation log"""
	_contract_violations.clear()

# ============================================================================
# DEBUG / INSPECTOR
# ============================================================================

func debug_print_state() -> void:
	"""Print current state for debugging"""
	print("\n=== FACTION3D STATE ===")
	print("Global Phase: %s" % Kernel.Phase.keys()[_current_snapshot["global_phase"]])
	print("Federation Alignment: %.2f" % _current_snapshot["federation_alignment"])
	print("Graviton Pressure: %.2f" % _current_snapshot["graviton_pressure"])
	print("\nLayer Accessibility:")
	for layer in Kernel.Layer.values():
		var accessible = _current_snapshot["layer_visibility"].get(layer, false)
		print("  %s: %s" % [Kernel.Layer.keys()[layer], "YES" if accessible else "NO"])
	print("\nTop 5 Factions by Influence:")
	var factions = get_all_factions_summary()
	factions.sort_custom(func(a, b): return a["influence"] > b["influence"])
	for i in range(min(5, factions.size())):
		var f = factions[i]
		print("  %s: %.2f" % [f["name"], f["influence"]])
	print("=======================\n")
