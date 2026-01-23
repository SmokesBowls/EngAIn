extends Node
class_name ZWR

# FIX #1 APPLIED: Centralized Transport Validation
# All protocol validation delegated to fix_3_protocol_envelope.gd

signal state_updated(snapshot: Dictionary)
signal delta_received(delta: Dictionary)

const SERVER_URL = "http://localhost:8080"
var server_url = SERVER_URL

# SINGLE SOURCE OF TRUTH for validation
var envelope_validator: Node

var current_epoch: String = ""
var epoch_changes: int = 0

# Dedicated transport nodes
var snapshot_request: HTTPRequest
var command_request: HTTPRequest

var rendering_paused = false
var last_snapshot = null
var _snapshot_request_in_flight = false
var current_snapshot: Dictionary = {}

func _ready():
	# FIX #1: Load envelope validator (SINGLE SOURCE OF TRUTH)
	envelope_validator = preload("res://fix_3_protocol_envelope.gd").new()
	add_child(envelope_validator)
	
	# Create HTTP nodes
	snapshot_request = HTTPRequest.new()
	add_child(snapshot_request)
	snapshot_request.request_completed.connect(_on_snapshot_completed)
	
	command_request = HTTPRequest.new()
	add_child(command_request)
	command_request.request_completed.connect(_on_command_completed)
	
	print("ZWRuntime: Initialized with centralized validation")
	
	await get_tree().create_timer(0.5).timeout
	_request_next_snapshot()

func _request_next_snapshot():
	if _snapshot_request_in_flight:
		return
	
	_snapshot_request_in_flight = true
	var url = server_url + "/snapshot"
	var error = snapshot_request.request(url)
	
	if error != OK:
		print("ZWRuntime: Request failed: ", error)
		_snapshot_request_in_flight = false
		await get_tree().create_timer(1.0).timeout
		_request_next_snapshot()

func _on_snapshot_completed(_result, response_code, _headers, body):
	_snapshot_request_in_flight = false
	
	if response_code != 200:
		if response_code != 0:
			print("ZWRuntime: Server error ", response_code)
		await get_tree().create_timer(0.5).timeout
		_request_next_snapshot()
		return
	
	var json = JSON.new()
	var parse_result = json.parse(body.get_string_from_utf8())
	
	if parse_result != OK:
		print("ZWRuntime: JSON parse failed")
		_request_next_snapshot()
		return
	
	var data = json.data
	
	if rendering_paused:
		print("ZWRuntime: Paused")
		_request_next_snapshot()
		return
	
	# ============================================================
	# FIX #1: CENTRALIZED VALIDATION
	# ============================================================
	
	var validation_result = envelope_validator.validate_and_unwrap_envelope(data)
	
	if not validation_result.success:
		push_error("ZWRuntime: Validation failed - " + validation_result.error)
		_request_next_snapshot()
		return
	
	# Extract validated payload
	var snapshot = validation_result.payload
	
	last_snapshot = snapshot
	current_snapshot = snapshot
	
	# Sync epoch tracking
	if envelope_validator.current_epoch != current_epoch:
		if current_epoch != "":
			epoch_changes += 1
		current_epoch = envelope_validator.current_epoch
	
	state_updated.emit(current_snapshot)
	_request_next_snapshot()

# --- COMMAND CHANNEL ---

func send_command(command: Dictionary):
	var url = server_url + "/command"
	var json_string = JSON.stringify(command)
	var headers = ["Content-Type: application/json"]
	
	var error = command_request.request(url, headers, HTTPClient.METHOD_POST, json_string)
	
	if error != OK:
		print("ZWRuntime: Command failed: ", error)

func _on_command_completed(_result, response_code, _headers, _body):
	if response_code == 200:
		print("ZWRuntime: Command acknowledged")
	else:
		print("ZWRuntime: Command failed: ", response_code)

# --- PUBLIC API ---

func get_snapshot() -> Dictionary:
	return current_snapshot.duplicate(true)

func reload_blocks():
	send_command({"action": "reload_blocks"})

func dump_state():
	send_command({"action": "dump_state"})

func pause_rendering():
	rendering_paused = true
	print("ZWRuntime: PAUSED")

func resume_rendering():
	rendering_paused = false
	print("ZWRuntime: RESUMED")
	if not _snapshot_request_in_flight:
		_request_next_snapshot()

func get_validation_stats() -> Dictionary:
	if envelope_validator:
		return envelope_validator.get_validation_report()
	return {}

func print_validation_stats():
	if envelope_validator:
		envelope_validator.print_validation_stats()
