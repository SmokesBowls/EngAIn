extends Node
class_name ZWValidator

# --- Configuration ---
@export var enable_profiling: bool = false
@export var validation_timeout_ms: int = 1000  # Max time for validation

# --- Validation Registries ---
var block_validators := {}
var action_validators := {}
var rule_validators := {}
var known_ids := {}
var block_types := {}

# --- Signal for validation events ---
signal validation_started(block_count: int)
signal validation_completed(issues: Array)
signal validation_progress(current: int, total: int)

# --- Public API ---
func validate_all(blocks: Array) -> Array:
	known_ids.clear()
	block_types.clear()
	var issues := []
	
	# Populate known IDs
	for block in blocks:
		if block is Dictionary and block.has("id"):
			known_ids[block.id] = true
			
	# Initialize with built-in validators if not already set
	_initialize_default_validators()
	
	# Emit start signal
	emit_signal("validation_started", blocks.size())
	
	# Validate each block
	var start_time = Time.get_ticks_msec()
	for i in range(blocks.size()):
		var block = blocks[i]
		
		# Check for timeout
		if enable_profiling and Time.get_ticks_msec() - start_time > validation_timeout_ms:
			issues.append("Validation timeout after %d ms" % validation_timeout_ms)
			break
			
		if block is Dictionary:
			var result = validate_block(block)
			if result.size() > 0:
				issues += result
		else:
			issues.append("Non-dictionary block encountered: %s" % str(block))
			
		# Emit progress signal
		emit_signal("validation_progress", i + 1, blocks.size())
	
	# Emit completion signal
	emit_signal("validation_completed", issues)
	return issues

# --- Block Validation Dispatcher ---
func validate_block(block: Dictionary) -> Array:
	var issues := []
	
	if not block.has("id"):
		issues.append("Block missing 'id' field: %s" % str(block))
		return issues
		
	var id := str(block.id)
	var type := str(block.get("type", "unknown"))
	block_types[id] = type
	
	# Common validation for all blocks
	issues += _check_string(block, "id")
	issues += _check_optional_string(block, "location", id)
	issues += _validate_rules_if_present(block, id, "rules")
	issues += _validate_effects_if_present(block, id, "effects")
	
	# Type-specific validation
	if block_validators.has(type):
		var validator_func = block_validators[type]
		if validator_func is Callable:
			var t0 = Time.get_ticks_usec() if enable_profiling else 0
			issues += validator_func.call(block)
			if enable_profiling:
				var elapsed = Time.get_ticks_usec() - t0
				if elapsed > 200:  # microseconds
					print("Slow block validator for %s: %dμs" % [type, elapsed])
		else:
			issues.append("Invalid validator for block type: %s" % type)
	else:
		if OS.is_debug_build():
			issues.append("Unrecognized block type: %s (id: %s)" % [type, id])
				
	return issues

# --- Registry Management ---
func register_block_type(type_name: String, validator_func: Callable) -> void:
	block_validators[type_name] = validator_func

func register_action_type(action_name: String, validator_func: Callable) -> void:
	action_validators[action_name] = validator_func

func register_rule_type(rule_name: String, validator_func: Callable) -> void:
	rule_validators[rule_name] = validator_func

func get_registered_block_types() -> Array:
	return block_validators.keys()

func get_registered_action_types() -> Array:
	return action_validators.keys()

func get_registered_rule_types() -> Array:
	return rule_validators.keys()

# --- Default Validators Initialization ---
func _initialize_default_validators() -> void:
	# Only initialize if registries are empty
	if block_validators.is_empty():
		block_validators = {
			"npc_dialogue": _validate_dialogue_block,
			"shop_interface": _validate_shop_block,
			"spawn": _validate_spawn_block,
			"gate": _validate_gate_block,
			"evaluator": _validate_evaluator_block
		}
	
	if action_validators.is_empty():
		action_validators = {
			"show_text": _validate_show_text_action,
			"play_music": _validate_play_music_action,
			"give_item": _validate_give_item_action,
			"set_flag": _validate_set_flag_action
		}
	
	if rule_validators.is_empty():
		rule_validators = {
			"flag": _validate_flag_rule,
			"item": _validate_item_rule,
			"not_item": _validate_not_item_rule,
			"reputation": _validate_reputation_rule,
			"time_window": _validate_time_window_rule,
			"location": _validate_location_rule,
			"player_stat": _validate_player_stat_rule
		}

# --- Default Block Validators ---
func _validate_dialogue_block(block: Dictionary) -> Array:
	var issues := []
	var id := str(block.id)
	
	if block.has("leads_to"):
		var target = str(block.leads_to)
		if target != "" and not known_ids.has(target):
			_missing_ref(id, "leads_to", target)
			issues.append("Missing reference for 'leads_to': %s" % target)
			
	if block.has("choices") and typeof(block.choices) == TYPE_ARRAY:
		for i in range(block.choices.size()):
			var choice = block.choices[i]
			if typeof(choice) != TYPE_DICTIONARY:
				_warn("Choice must be dictionary", {"block_id": id, "choice_index": i})
				issues.append("Choice must be dictionary at index %d" % i)
				continue
				
			if not choice.has("text"):
				_warn("Choice missing text", {"block_id": id, "choice_index": i})
				issues.append("Choice missing text at index %d" % i)
				
			if choice.has("leads_to"):
				var target = str(choice.leads_to)
				if target != "" and not known_ids.has(target):
					_missing_ref(id, "choices[%d].leads_to" % i, target)
					issues.append("Missing reference for choice leads_to: %s" % target)
					
	if block.has("requires"):
		issues += _validate_requires(block.requires, id, "requires")
		
	return issues

func _validate_shop_block(block: Dictionary) -> Array:
	var issues := []
	var id := str(block.id)
	
	if not block.has("inventory"):
		_warn("Shop block missing 'inventory' field", {"block_id": id})
		issues.append("Shop block missing 'inventory' field")
		return issues
		
	if typeof(block.inventory) != TYPE_ARRAY:
		_warn("'inventory' must be an array", {"block_id": id})
		issues.append("'inventory' must be an array")
		return issues
		
	for i in range(block.inventory.size()):
		var item = block.inventory[i]
		if typeof(item) != TYPE_DICTIONARY:
			_warn("Inventory item must be dictionary", {"block_id": id, "item_index": i})
			issues.append("Inventory item must be dictionary at index %d" % i)
			continue
			
		var item_id = item.get("item_id", "")
		var price = item.get("price", null)
		
		if item_id == "" or typeof(item_id) != TYPE_STRING:
			_warn("Missing or invalid 'item_id'", {"block_id": id, "item_index": i})
			issues.append("Missing or invalid 'item_id' at index %d" % i)
			
		if price == null or typeof(price) not in [TYPE_INT, TYPE_FLOAT]:
			_warn("Missing or invalid 'price'", {"block_id": id, "item_index": i})
			issues.append("Missing or invalid 'price' at index %d" % i)
			
	return issues

func _validate_spawn_block(block: Dictionary) -> Array:
	var issues := []
	var id := str(block.id)
	
	issues += _check_string(block, "location", id)
	issues += _check_string(block, "entity", id)
	issues += _validate_rules_if_present(block, id, "rules")
	
	return issues

func _validate_gate_block(block: Dictionary) -> Array:
	var issues := []
	var id := str(block.id)
	
	issues += _check_string(block, "location", id)
	
	if not block.has("rules"):
		_warn("Gate missing rules", {"block_id": id})
		issues.append("Gate missing rules")
	else:
		issues += _validate_rules(block.rules, id, "rules")
		
	issues += _validate_effects_if_present(block, id, "effects")
	
	return issues

func _validate_evaluator_block(block: Dictionary) -> Array:
	var issues := []
	var id := str(block.id)
	
	if block.has("mode"):
		var mode := str(block.mode)
		if not mode in ["any_of", "all_of", "none_of"]:
			_warn("Evaluator 'mode' should be any_of/all_of/none_of", {"block_id": id})
			issues.append("Evaluator 'mode' should be any_of/all_of/none_of")
			
	if block.has("rules"):
		issues += _validate_rules(block.rules, id, "rules")
		
	for k in ["on_true", "on_false"]:
		if block.has(k) and block[k] is Dictionary and block[k].has("actions"):
			issues += _validate_actions_array(block[k].actions, id, "%s.actions" % k)
			
	return issues

# --- Default Action Validators ---
func _validate_show_text_action(action: Dictionary, id: String, path: String) -> Array:
	var issues := []
	if typeof(action.get("text", null)) != TYPE_STRING: 
		var msg = "show_text requires 'text'"
		issues.append(msg)
		_warn(msg, {"block_id": id, "path": path})
	return issues

func _validate_play_music_action(action: Dictionary, id: String, path: String) -> Array:
	var issues := []
	if typeof(action.get("track", null)) != TYPE_STRING: 
		var msg = "play_music requires 'track'"
		issues.append(msg)
		_warn(msg, {"block_id": id, "path": path})
	return issues

func _validate_give_item_action(action: Dictionary, id: String, path: String) -> Array:
	var issues := []
	if typeof(action.get("item_id", null)) != TYPE_STRING or typeof(action.get("quantity", null)) not in [TYPE_INT, TYPE_FLOAT]:
		var msg = "give_item requires item_id:string and quantity:number"
		issues.append(msg)
		_warn(msg, {"block_id": id, "path": path})
	return issues

func _validate_set_flag_action(action: Dictionary, id: String, path: String) -> Array:
	var issues := []
	if typeof(action.get("flag", null)) != TYPE_STRING: 
		var msg = "set_flag requires 'flag'"
		issues.append(msg)
		_warn(msg, {"block_id": id, "path": path})
	return issues

# --- Default Rule Validators ---
func _validate_flag_rule(rule: Dictionary, _id: String, _path: String) -> Array:
	var issues := []
	if typeof(rule.get("flag", "")) != TYPE_STRING: 
		issues.append("Flag rule requires 'flag' field")
	return issues

func _validate_item_rule(rule: Dictionary, _id: String, _path: String) -> Array:
	var issues := []
	if typeof(rule.get("item", "")) != TYPE_STRING: 
		issues.append("Item rule requires 'item' field")
	if typeof(rule.get("quantity", 1)) not in [TYPE_INT, TYPE_FLOAT]: 
		issues.append("Item rule requires numeric 'quantity' field")
	return issues

func _validate_not_item_rule(rule: Dictionary, _id: String, _path: String) -> Array:
	var issues := []
	if typeof(rule.get("item", "")) != TYPE_STRING: 
		issues.append("Not item rule requires 'item' field")
	if typeof(rule.get("quantity", 1)) not in [TYPE_INT, TYPE_FLOAT]: 
		issues.append("Not item rule requires numeric 'quantity' field")
	return issues

func _validate_reputation_rule(rule: Dictionary, _id: String, _path: String) -> Array:
	var issues := []
	if typeof(rule.get("faction", "")) != TYPE_STRING: 
		issues.append("Reputation rule requires 'faction' field")
	if typeof(rule.get("min", 0)) not in [TYPE_INT, TYPE_FLOAT]: 
		issues.append("Reputation rule requires numeric 'min' field")
	if typeof(rule.get("max", 100)) not in [TYPE_INT, TYPE_FLOAT]: 
		issues.append("Reputation rule requires numeric 'max' field")
	return issues

func _validate_time_window_rule(rule: Dictionary, _id: String, _path: String) -> Array:
	var issues := []
	if typeof(rule.get("start", "")) != TYPE_STRING: 
		issues.append("Time window rule requires 'start' field")
	if typeof(rule.get("end", "")) != TYPE_STRING: 
		issues.append("Time window rule requires 'end' field")
	return issues

func _validate_location_rule(rule: Dictionary, _id: String, _path: String) -> Array:
	var issues := []
	if typeof(rule.get("location", "")) != TYPE_STRING: 
		issues.append("Location rule requires 'location' field")
	return issues

func _validate_player_stat_rule(rule: Dictionary, _id: String, _path: String) -> Array:
	var issues := []
	if typeof(rule.get("stat", "")) != TYPE_STRING: 
		issues.append("Player stat rule requires 'stat' field")
	if typeof(rule.get("min", 0)) not in [TYPE_INT, TYPE_FLOAT]: 
		issues.append("Player stat rule requires numeric 'min' field")
	if typeof(rule.get("max", 100)) not in [TYPE_INT, TYPE_FLOAT]: 
		issues.append("Player stat rule requires numeric 'max' field")
	return issues

# --- Utility Functions ---
func _check_string(block: Dictionary, key: String, _id: String = "") -> Array:
	var issues := []
	if not block.has(key) or typeof(block[key]) != TYPE_STRING:
		var msg = "Expected string for key '%s'" % key
		issues.append(msg)
		if OS.is_debug_build():
			_warn(msg, {"block": block})
	return issues

func _check_optional_string(block: Dictionary, field: String, id: String = "") -> Array:
	var issues := []
	if block.has(field) and (typeof(block[field]) != TYPE_STRING or str(block[field]) == ""):
		var msg = "Optional field '%s' must be string when present" % field
		issues.append(msg)
		_warn(msg, {"block_id": id})
	return issues

func _validate_requires(requires: Variant, id: String, path: String) -> Array:
	var issues := []
	if typeof(requires) != TYPE_DICTIONARY:
		var msg = "Requires must be dictionary"
		issues.append(msg)
		_warn(msg, {"block_id": id, "path": path})
		return issues
		
	for key in requires.keys():
		if rule_validators.has(key):
			var validator_func = rule_validators[key]
			if validator_func is Callable:
				issues += validator_func.call(requires, id, path)
		else:
			var msg = "Unknown key in requires"
			issues.append(msg)
			_warn(msg, {"block_id": id, "path": path, "key": key})
			
	return issues

func _validate_rules_if_present(block: Dictionary, id: String, field: String) -> Array:
	var issues := []
	if block.has(field):
		issues += _validate_rules(block[field], id, field)
	return issues

func _validate_rules(rules: Variant, id: String, path: String) -> Array:
	var issues := []
	if typeof(rules) != TYPE_DICTIONARY:
		var msg = "Rules must be a Dictionary"
		issues.append(msg)
		_warn(msg, {"block_id": id, "path": path})
		return issues
		
	var seen := false
	for mode in ["any_of", "all_of", "none_of"]:
		if rules.has(mode):
			seen = true
			if typeof(rules[mode]) != TYPE_ARRAY:
				var msg = "Rules '%s' must be array" % mode
				issues.append(msg)
				_warn(msg, {"block_id": id})
			else:
				for i in range(rules[mode].size()):
					issues += _validate_condition(rules[mode][i], id, "%s.%s[%d]" % [path, mode, i])
					
	if not seen:
		var msg = "Rules missing any_of/all_of/none_of"
		issues.append(msg)
		_warn(msg, {"block_id": id, "path": path})
		
	return issues

func _validate_condition(cond: Variant, id: String, path: String) -> Array:
	var issues := []
	if typeof(cond) != TYPE_DICTIONARY:
		var msg = "Condition must be dictionary"
		issues.append(msg)
		_warn(msg, {"block_id": id, "path": path})
		return issues
		
	var has_key := false
	for k in rule_validators.keys():
		if cond.has(k): 
			has_key = true
			if rule_validators.has(k):
				var validator_func = rule_validators[k]
				if validator_func is Callable:
					issues += validator_func.call(cond, id, path)
			break
			
	if not has_key:
		var msg = "No known keys in condition"
		issues.append(msg)
		_warn(msg, {"block_id": id, "path": path})
		
	return issues

func _validate_effects_if_present(block: Dictionary, id: String, field: String) -> Array:
	var issues := []
	if not block.has(field): return issues
	
	if typeof(block[field]) != TYPE_DICTIONARY:
		var msg = "effects must be a Dictionary"
		issues.append(msg)
		_warn(msg, {"block_id": id})
		return issues
		
	for k in block[field].keys():
		var sec = block[field][k]
		if typeof(sec) == TYPE_DICTIONARY:
			if sec.has("consume_item") and typeof(sec.consume_item) != TYPE_STRING:
				var msg = "%s.consume_item must be string" % k
				issues.append(msg)
				_warn(msg, {"block_id": id})
			if sec.has("actions"):
				issues += _validate_actions_array(sec.actions, id, "effects.%s.actions" % k)
		elif typeof(sec) == TYPE_ARRAY and k == "actions":
			issues += _validate_actions_array(sec, id, "effects.actions")
			
	return issues

func _validate_actions_array(arr: Variant, id: String, path: String) -> Array:
	var issues := []
	if typeof(arr) != TYPE_ARRAY:
		var msg = "Actions must be array"
		issues.append(msg)
		_warn(msg, {"block_id": id, "path": path})
		return issues
		
	for i in range(arr.size()):
		var act = arr[i]
		if typeof(act) != TYPE_DICTIONARY:
			var msg = "Action must be dictionary"
			issues.append(msg)
			_warn(msg, {"block_id": id, "path": "%s[%d]" % [path, i]})
			continue
			
		var t = str(act.get("type", ""))
		if t == "":
			var msg = "Action missing 'type'"
			issues.append(msg)
			_warn(msg, {"block_id": id, "path": "%s[%d]" % [path, i]})
			continue
			
		if action_validators.has(t):
			var validator_func = action_validators[t]
			if validator_func is Callable:
				var t0 = Time.get_ticks_usec() if enable_profiling else 0
				issues += validator_func.call(act, id, "%s[%d]" % [path, i])
				if enable_profiling:
					var elapsed = Time.get_ticks_usec() - t0
					if elapsed > 200:  # microseconds
						print("Slow action validator for %s: %dμs" % [t, elapsed])
		else:
			_invalid_action(id, t)
			issues.append("Invalid action type: %s" % t)
			
	return issues

# --- Documentation Generation ---
func generate_documentation(format: String = "markdown") -> String:
	var output := []
	
	if format == "markdown":
		output.append("# ZWValidator Documentation")
		output.append("")
		output.append("## Block Types")
		output.append("")
		
		for block_type in block_validators.keys():
			output.append("### %s" % block_type)
			output.append("TODO: Add description for %s block type" % block_type)
			output.append("")
			
		output.append("## Action Types")
		output.append("")
		
		for action_type in action_validators.keys():
			output.append("### %s" % action_type)
			output.append("TODO: Add description for %s action type" % action_type)
			output.append("")
			
		output.append("## Rule Types")
		output.append("")
		
		for rule_type in rule_validators.keys():
			output.append("### %s" % rule_type)
			output.append("TODO: Add description for %s rule type" % rule_type)
			output.append("")
	
	return "\n".join(output)

# --- Export Functions ---
func export_issues(blocks: Array, format: String = "text") -> Variant:
	var issues = validate_all(blocks)
	
	match format:
		"json":
			var result = {
				"issue_count": issues.size(),
				"issues": issues
			}
			return JSON.stringify(result)
		"csv":
			var csv = "Type,Message,BlockID,Path\n"
			for issue in issues:
				# Simple parsing - in a real implementation, you'd want more structured issues
				csv += "error,%s,,\n" % issue
			return csv
		_:
			return issues

# --- Alert Routing ---
func _alerts() -> Node:
	return get_node("/root/ZWAlerts") if has_node("/root/ZWAlerts") else null

func _critical(msg: String, payload: Dictionary) -> void:
	var A := _alerts(); if A and A.has_method("critical"): A.critical(msg, payload)

func _warn(msg: String, payload: Dictionary) -> void:
	var A := _alerts()
	if A and A.has_method("warning"):
		A.warning(msg, payload)
	else:
		print("[WARN] %s: %s" % [msg, payload])

func _missing_ref(block_id: String, key: String, ref_id: String) -> void:
	var A := _alerts(); if A and A.has_method("alert_for_missing_reference"): A.alert_for_missing_reference(block_id, key, ref_id)

func _invalid_action(block_id: String, action_type: String) -> void:
	var A := _alerts(); if A and A.has_method("alert_for_invalid_action"): A.alert_for_invalid_action(block_id, action_type)

# --- Unit Test Helper ---
func test_validator(validator_func: Callable, test_data: Dictionary) -> Array:
	var issues := []
	
	if validator_func is Callable:
		issues = validator_func.call(test_data, "test_id", "test_path")
	
	return issues
