extends Node

# GODOT_INPUT_LISTENER_BRIDGE_CONSUME_COMMAND_V1
#
# Godot-side input-listener bridge.
#
# This script MAY:
# - read the lawful player input listener command
# - validate command scope
# - attach a limited boot-shell input listener
# - write captured input as a packet
# - write a report proving listener state
#
# This script MAY NOT:
# - mutate EngAInOS runtime
# - spawn player
# - spawn entities
# - start gameplay
# - write canon
# - write quest/combat/inventory state


const COMMAND_PATH := "res://runtime/godot_commands/PLAYER_INPUT_LISTENER_COMMAND_V1.json"
const REPORT_PATH := "res://runtime/godot_reports/GODOT_INPUT_LISTENER_BRIDGE_CONSUME_COMMAND_V1.report.json"
const INPUT_PACKET_PATH := "res://runtime/input_packets/PLAYER_INPUT_PACKET_V1.json"

const EXPECTED_CONTRACT := "engainos.godot_player_input_listener_command.v1"
const EXPECTED_COMMAND_TYPE := "ATTACH_BOOT_SHELL_INPUT_LISTENER"
const EXPECTED_SCENE_ID := "engainos.boot.empty"
const EXPECTED_INPUT_MODE := "boot_shell_input_probe"
const EXPECTED_INPUT_PACKET_CONTRACT := "engainos.player_input_packet.v1"

var listener_attached: bool = false
var allowed_input_events: Array = []


func _ready() -> void:
	# Run on the next frame to avoid scene tree busy warning/errors
	call_deferred("deferred_setup")


func deferred_setup() -> void:
	var result := consume_listener_command()

	if not result.get("ok", false):
		var fail_report := {
			"contract": "godot.input_listener_bridge_consume_command_report.v1",
			"ok": false,
			"status": "GODOT_INPUT_LISTENER_BRIDGE_BLOCKED",
			"blocked_by": result.get("blocked_by", "UNKNOWN"),
			"reason": result.get("reason", "Input listener command failed validation."),
			"listener_attached": false,
			"input_packet_written": false,
			"runtime_mutation_allowed": false,
			"player_spawned": false,
			"entities_spawned": false,
			"gameplay_started": false,
			"next_action": "FIX_GODOT_INPUT_LISTENER_BRIDGE_CONSUME_COMMAND_V1"
		}
		write_json(REPORT_PATH, fail_report)
		push_error("[GODOT_INPUT_LISTENER_BRIDGE] BLOCKED: " + str(fail_report["blocked_by"]))
		return

	allowed_input_events = result.get("allowed_input_events", [])
	listener_attached = true

	var pass_report := {
		"contract": "godot.input_listener_bridge_consume_command_report.v1",
		"ok": true,
		"status": "GODOT_INPUT_LISTENER_BRIDGE_CONSUMED_COMMAND",
		"blocked_by": null,
		"reason": "Boot shell input listener attached. It may capture allowed input and write packet only.",
		"scene_id": EXPECTED_SCENE_ID,
		"input_mode": EXPECTED_INPUT_MODE,
		"allowed_input_events": allowed_input_events,
		"listener_attached": true,
		"input_packet_written": false,
		"input_packet_path": INPUT_PACKET_PATH,
		"runtime_mutation_allowed": false,
		"player_spawned": false,
		"entities_spawned": false,
		"gameplay_started": false,
		"next_action": "PLAYER_INPUT_PACKET_CAPTURE_READY_V1"
	}

	write_json(REPORT_PATH, pass_report)

	print("[GODOT_INPUT_LISTENER_BRIDGE][ALL_CHECKS] true")
	print("[GODOT_INPUT_LISTENER_BRIDGE][LISTENER_ATTACHED] true")
	print("[GODOT_INPUT_LISTENER_BRIDGE][INPUT_PACKET_WRITTEN] false")
	print("[GODOT_INPUT_LISTENER_BRIDGE][RUNTIME_MUTATION_ALLOWED] false")
	print("[GODOT_INPUT_LISTENER_BRIDGE][NEXT_ACTION] PLAYER_INPUT_PACKET_CAPTURE_READY_V1")


func _input(event: InputEvent) -> void:
	if not listener_attached:
		return

	var event_name := classify_allowed_event(event)

	if event_name == "":
		return

	var packet := build_input_packet(event_name, event)
	write_json(INPUT_PACKET_PATH, packet)

	var report := {
		"contract": "godot.input_listener_bridge_consume_command_report.v1",
		"ok": true,
		"status": "GODOT_INPUT_PACKET_WRITTEN",
		"blocked_by": null,
		"reason": "Allowed boot-shell input captured and packetized.",
		"scene_id": EXPECTED_SCENE_ID,
		"input_mode": EXPECTED_INPUT_MODE,
		"allowed_input_events": allowed_input_events,
		"listener_attached": true,
		"input_packet_written": true,
		"input_packet_path": INPUT_PACKET_PATH,
		"last_input_event": event_name,
		"runtime_mutation_allowed": false,
		"player_spawned": false,
		"entities_spawned": false,
		"gameplay_started": false,
		"next_action": "PLAYER_INPUT_PACKET_VALIDATION_REQUEST_V1"
	}

	write_json(REPORT_PATH, report)

	print("[GODOT_INPUT_LISTENER_BRIDGE][INPUT_PACKET_WRITTEN] true")
	print("[GODOT_INPUT_LISTENER_BRIDGE][LAST_INPUT_EVENT] " + event_name)
	print("[GODOT_INPUT_LISTENER_BRIDGE][NEXT_ACTION] PLAYER_INPUT_PACKET_VALIDATION_REQUEST_V1")


func consume_listener_command() -> Dictionary:
	if not FileAccess.file_exists(COMMAND_PATH):
		return {
			"ok": false,
			"blocked_by": "COMMAND_FILE_MISSING",
			"reason": "Input listener command file is missing.",
			"command_path": COMMAND_PATH
		}

	var raw := FileAccess.get_file_as_string(COMMAND_PATH)

	if raw.strip_edges() == "":
		return {
			"ok": false,
			"blocked_by": "COMMAND_FILE_EMPTY",
			"reason": "Input listener command file is empty.",
			"command_path": COMMAND_PATH
		}

	var parsed = JSON.parse_string(raw)

	if typeof(parsed) != TYPE_DICTIONARY:
		return {
			"ok": false,
			"blocked_by": "COMMAND_JSON_INVALID",
			"reason": "Input listener command JSON could not be parsed as dictionary.",
			"command_path": COMMAND_PATH
		}

	return validate_command(parsed)


func validate_command(command: Dictionary) -> Dictionary:
	var checks := {
		"contract_valid": command.get("contract") == EXPECTED_CONTRACT,
		"command_type_valid": command.get("command_type") == EXPECTED_COMMAND_TYPE,
		"scene_id_valid": command.get("scene_id") == EXPECTED_SCENE_ID,
		"input_mode_valid": command.get("input_mode") == EXPECTED_INPUT_MODE,
		"input_packet_contract_valid": command.get("input_packet_contract") == EXPECTED_INPUT_PACKET_CONTRACT,

		"permits_runtime_mutation_false": command.get("permits_runtime_mutation") == false,
		"permits_player_spawn_false": command.get("permits_player_spawn") == false,
		"permits_entity_spawn_false": command.get("permits_entity_spawn") == false,
		"permits_gameplay_start_false": command.get("permits_gameplay_start") == false,
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
				"reason": "Input listener command failed validation.",
				"checks": checks
			}

	var input_events = command.get("allowed_input_events", [])

	if typeof(input_events) != TYPE_ARRAY:
		return {
			"ok": false,
			"blocked_by": "allowed_input_events_invalid",
			"reason": "allowed_input_events must be an array."
		}

	return {
		"ok": true,
		"checks": checks,
		"allowed_input_events": input_events
	}


func classify_allowed_event(event: InputEvent) -> String:
	for event_name in allowed_input_events:
		if typeof(event_name) != TYPE_STRING:
			continue

		if event.is_action_pressed(event_name):
			return str(event_name)

	if event is InputEventKey and event.pressed and not event.echo:
		if allowed_input_events.has("text_submitted"):
			var key_event := event as InputEventKey
			var text := key_event.as_text_key_label()

			if text != "":
				return "text_submitted"

	return ""


func build_input_packet(event_name: String, event: InputEvent) -> Dictionary:
	var input_text := ""

	if event is InputEventKey:
		input_text = (event as InputEventKey).as_text_key_label()

	return {
		"contract": EXPECTED_INPUT_PACKET_CONTRACT,
		"source": "godot_input_listener_bridge",
		"authority_claimed": false,
		"scene_id": EXPECTED_SCENE_ID,
		"input_mode": EXPECTED_INPUT_MODE,
		"captured_at_unix_msec": Time.get_unix_time_from_system() * 1000.0,

		"input_event": {
			"event_name": event_name,
			"input_text": input_text,
			"device": event.device
		},

		"permissions": {
			"runtime_mutation_allowed": false,
			"player_spawn_allowed": false,
			"entity_spawn_allowed": false,
			"gameplay_start_allowed": false,
			"canon_write_allowed": false,
			"quest_state_write_allowed": false,
			"combat_state_write_allowed": false,
			"inventory_state_write_allowed": false
		},

		"next_action": "PLAYER_INPUT_PACKET_VALIDATION_REQUEST_V1"
	}


func write_json(path: String, data: Dictionary) -> void:
	var dir := path.get_base_dir()

	if not DirAccess.dir_exists_absolute(dir):
		DirAccess.make_dir_recursive_absolute(dir)

	var file := FileAccess.open(path, FileAccess.WRITE)

	if file == null:
		push_error("[GODOT_INPUT_LISTENER_BRIDGE] Could not write JSON: " + path)
		return

	file.store_string(JSON.stringify(data, "\t"))
	file.close()
