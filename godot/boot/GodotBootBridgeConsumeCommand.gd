extends Node

# GODOT_BOOT_BRIDGE_CONSUME_COMMAND_V1
#
# This is Godot-side presentation consumption only.
# It reads the EngAInOS command packet and loads the empty boot shell scene.
#
# It does NOT:
# - decide authority
# - spawn player
# - spawn entities
# - mutate runtime
# - write canon
# - write quest/combat/inventory state
# - generate assets
# - accept player input


const COMMAND_PATH := "res://runtime/godot_commands/BOOT_SCENE_LOAD_COMMAND_V1.json"
const REPORT_PATH := "res://runtime/godot_reports/GODOT_BOOT_BRIDGE_CONSUME_COMMAND_V1.report.json"

const EXPECTED_CONTRACT := "engainos.godot_boot_shell_command.v1"
const EXPECTED_COMMAND_TYPE := "LOAD_BOOT_SHELL_SCENE"
const EXPECTED_SCENE_ID := "engainos.boot.empty"
const EXPECTED_SCENE_RESOURCE_PATH := "res://scenes/EngAInOSBootShell.tscn"


func _ready() -> void:
	call_deferred("deferred_setup")


func deferred_setup() -> void:
	var result := consume_boot_command()
	print("[GODOT_BOOT_BRIDGE][ALL_CHECKS] ", str(result.get("ok", false)).to_lower())

	if not result.get("ok", false):
		push_error("[GODOT_BOOT_BRIDGE] BOOT_BLOCKED: " + str(result.get("reason", "unknown failure")))
		return

	var scene_path := str(result["scene_resource_path"])
	var err := get_tree().change_scene_to_file(scene_path)

	if err != OK:
		var fail_report := {
			"contract": "godot.boot_bridge_consume_command_report.v1",
			"ok": false,
			"status": "GODOT_BOOT_BRIDGE_BLOCKED",
			"blocked_by": "CHANGE_SCENE_FAILED",
			"reason": "Godot failed to load declared boot shell scene.",
			"scene_resource_path": scene_path,
			"godot_error_code": err,
			"runtime_mutation_allowed": false,
			"player_spawned": false,
			"entities_spawned": false,
			"next_action": "FIX_BOOT_SHELL_SCENE_PATH"
		}
		write_report(fail_report)
		push_error("[GODOT_BOOT_BRIDGE] CHANGE_SCENE_FAILED: " + str(err))
		return

	var pass_report := {
		"contract": "godot.boot_bridge_consume_command_report.v1",
		"ok": true,
		"status": "GODOT_BOOT_BRIDGE_CONSUMED_COMMAND",
		"blocked_by": null,
		"reason": "Loaded declared empty boot shell scene only.",
		"scene_id": EXPECTED_SCENE_ID,
		"scene_resource_path": scene_path,
		"runtime_mutation_allowed": false,
		"player_spawned": false,
		"entities_spawned": false,
		"player_input_allowed": false,
		"next_action": "BOOT_SHELL_PRESENTATION_READY_V1"
	}
	write_report(pass_report)

	print("[GODOT_BOOT_BRIDGE][COMMAND_CONSUMED] true")
	print("[GODOT_BOOT_BRIDGE][BOOT_SHELL_LOADED] true")
	print("[GODOT_BOOT_BRIDGE][RUNTIME_MUTATION_ALLOWED] false")
	print("[GODOT_BOOT_BRIDGE][NEXT_ACTION] BOOT_SHELL_PRESENTATION_READY_V1")


func consume_boot_command() -> Dictionary:
	if not FileAccess.file_exists(COMMAND_PATH):
		return {
			"ok": false,
			"blocked_by": "COMMAND_FILE_MISSING",
			"reason": "Command file missing.",
			"command_path": COMMAND_PATH
		}

	var raw := FileAccess.get_file_as_string(COMMAND_PATH)
	if raw.strip_edges() == "":
		return {
			"ok": false,
			"blocked_by": "COMMAND_FILE_EMPTY",
			"reason": "Command file is empty.",
			"command_path": COMMAND_PATH
		}

	var parsed = JSON.parse_string(raw)
	if typeof(parsed) != TYPE_DICTIONARY:
		return {
			"ok": false,
			"blocked_by": "COMMAND_JSON_INVALID",
			"reason": "Command JSON could not be parsed as a dictionary.",
			"command_path": COMMAND_PATH
		}

	var command: Dictionary = parsed
	var checks := validate_command(command)

	if not checks.get("ok", false):
		return checks

	return {
		"ok": true,
		"scene_id": command.get("scene_id"),
		"scene_resource_path": command.get("scene_resource_path")
	}


func validate_command(command: Dictionary) -> Dictionary:
	var checks := {
		"contract_valid": command.get("contract") == EXPECTED_CONTRACT,
		"command_type_valid": command.get("command_type") == EXPECTED_COMMAND_TYPE,
		"scene_id_valid": command.get("scene_id") == EXPECTED_SCENE_ID,
		"scene_resource_path_valid": command.get("scene_resource_path") == EXPECTED_SCENE_RESOURCE_PATH,

		"permits_runtime_mutation_false": command.get("permits_runtime_mutation") == false,
		"permits_entity_spawn_false": command.get("permits_entity_spawn") == false,
		"permits_player_spawn_false": command.get("permits_player_spawn") == false,
		"permits_player_input_false": command.get("permits_player_input") == false,
		"permits_canon_write_false": command.get("permits_canon_write") == false,
		"permits_quest_state_write_false": command.get("permits_quest_state_write") == false,
		"permits_combat_state_write_false": command.get("permits_combat_state_write") == false,
		"permits_inventory_state_write_false": command.get("permits_inventory_state_write") == false
	}

	for key in checks.keys():
		if checks[key] != true:
			return {
				"ok": false,
				"blocked_by": key,
				"reason": "Boot command failed validation.",
				"checks": checks
			}

	return {
		"ok": true,
		"checks": checks
	}


func write_report(report: Dictionary) -> void:
	var dir := REPORT_PATH.get_base_dir()

	if not DirAccess.dir_exists_absolute(dir):
		DirAccess.make_dir_recursive_absolute(dir)

	var file := FileAccess.open(REPORT_PATH, FileAccess.WRITE)
	if file == null:
		push_error("[GODOT_BOOT_BRIDGE] Could not write report: " + REPORT_PATH)
		return

	file.store_string(JSON.stringify(report, "\t"))
	file.close()
