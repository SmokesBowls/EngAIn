# File: autoload/ZWRuntime.gd
# ZWRuntime — Production Bridge to EngAInOS Runtime
#
# Authority model:
#   Python sim_runtime.py  →  all truth (combat, quest, AP, spatial, etc.)
#   This autoload           →  polls HTTP, emits typed signals
#   UI nodes                →  consume signals. Nothing else.
#
# Signals:
#   state_updated(snapshot)       — full /snapshot response (existing panels)
#   combat_updated(combat_data)   — /api/hud/combat?entity=player
#   quest_summaries_updated(list) — /api/hud/quest_summaries
#   engine_summary_updated(dict)  — /api/hud/engine_summary
#   connection_changed(connected) — true/false when runtime reachable
#
# No test harnesses. No fake data. No local logic.
# If the runtime isn't running, panels show "awaiting state."

extends Node
class_name autoZWRuntime

# ── Signals ──────────────────────────────────────────────────
signal state_updated(snapshot: Dictionary)
signal combat_updated(combat_data: Dictionary)
signal quest_summaries_updated(summaries: Array)
signal engine_summary_updated(summary: Dictionary)
signal connection_changed(connected: bool)

# ── Configuration ────────────────────────────────────────────
@export var server_url: String = "http://localhost:5000"
@export var poll_interval: float = 0.1      # 100ms for main snapshot
@export var hud_poll_interval: float = 0.25  # 250ms for HUD projections
@export var auto_connect: bool = true

# ── State ────────────────────────────────────────────────────
var current_snapshot: Dictionary = {}
var connected: bool = false
var pending_commands: Array = []

# ── HTTP channels (separate to avoid collision) ──────────────
var _http_snapshot: HTTPRequest
var _http_combat: HTTPRequest
var _http_quests: HTTPRequest
var _http_summary: HTTPRequest
var _http_command: HTTPRequest

# ── Timers ───────────────────────────────────────────────────
var _snapshot_timer: float = 0.0
var _hud_timer: float = 0.0
var _inflight_snapshot: bool = false
var _inflight_combat: bool = false
var _inflight_quests: bool = false
var _inflight_summary: bool = false
var _inflight_command: bool = false


func _ready() -> void:
	_http_snapshot = _create_http("snapshot")
	_http_combat = _create_http("combat")
	_http_quests = _create_http("quests")
	_http_summary = _create_http("summary")
	_http_command = _create_http("command")

	_http_snapshot.request_completed.connect(_on_snapshot_completed)
	_http_combat.request_completed.connect(_on_combat_completed)
	_http_quests.request_completed.connect(_on_quests_completed)
	_http_summary.request_completed.connect(_on_summary_completed)
	_http_command.request_completed.connect(_on_command_completed)

	print("ZWRuntime: Initialized → %s" % server_url)

	if auto_connect:
		# Fire first poll immediately
		_poll_snapshot()
		_poll_hud_endpoints()


func _process(delta: float) -> void:
	# ── Main snapshot poll ──
	_snapshot_timer += delta
	if _snapshot_timer >= poll_interval:
		_snapshot_timer = 0.0
		_poll_snapshot()
		_flush_commands()

	# ── HUD endpoint polls (staggered, lower frequency) ──
	_hud_timer += delta
	if _hud_timer >= hud_poll_interval:
		_hud_timer = 0.0
		_poll_hud_endpoints()


# ── Polling ──────────────────────────────────────────────────

func _poll_snapshot() -> void:
	if _inflight_snapshot:
		return
	_inflight_snapshot = true
	_http_snapshot.request(server_url + "/snapshot", [], HTTPClient.METHOD_GET)


func _poll_hud_endpoints() -> void:
	if not _inflight_combat:
		_inflight_combat = true
		_http_combat.request(server_url + "/api/hud/combat?entity=player", [], HTTPClient.METHOD_GET)

	if not _inflight_quests:
		_inflight_quests = true
		_http_quests.request(server_url + "/api/hud/quest_summaries", [], HTTPClient.METHOD_GET)

	if not _inflight_summary:
		_inflight_summary = true
		_http_summary.request(server_url + "/api/hud/engine_summary", [], HTTPClient.METHOD_GET)


# ── Response handlers ────────────────────────────────────────

func _on_snapshot_completed(result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	_inflight_snapshot = false
	if response_code != 200:
		_set_connected(false)
		return

	var data := _parse_json(body)
	if data.is_empty():
		return

	_set_connected(true)

	# NGAT-RT envelope: payload is under "payload" key
	var payload: Dictionary = data.get("payload", data.get("snapshot", data))
	current_snapshot = payload
	state_updated.emit(payload)


func _on_combat_completed(result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	_inflight_combat = false
	if response_code != 200:
		return

	var data := _parse_json(body)
	if data.is_empty() or data.has("error"):
		return

	combat_updated.emit(data)


func _on_quests_completed(result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	_inflight_quests = false
	if response_code != 200:
		return

	var data := _parse_json(body)
	if data.is_empty() or data.has("error"):
		return

	var summaries: Array = data.get("summaries", [])
	quest_summaries_updated.emit(summaries)


func _on_summary_completed(result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	_inflight_summary = false
	if response_code != 200:
		return

	var data := _parse_json(body)
	if data.is_empty() or data.has("error"):
		return

	engine_summary_updated.emit(data)


func _on_command_completed(result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	_inflight_command = false


# ── Command sending ──────────────────────────────────────────

func send_command(command: Dictionary) -> void:
	pending_commands.append(command)


func send_combat_damage(source: String, target: String, damage: float) -> void:
	_post("/combat/damage", {"source": source, "target": target, "damage": damage})


func send_quest_activate(quest_id: String) -> void:
	_post("/quest/activate", {"quest_id": quest_id})


func send_world_flag(key: String, value, entity: String = "player") -> void:
	_post("/world/set_flag", {"entity": entity, "key": key, "value": value})


func send_world_stat(key: String, value, entity: String = "player") -> void:
	_post("/world/set_stat", {"entity": entity, "key": key, "value": value})


func _flush_commands() -> void:
	if pending_commands.is_empty() or _inflight_command:
		return
	var cmd = pending_commands.pop_front()
	_inflight_command = true
	var json_str = JSON.stringify(cmd)
	var headers = ["Content-Type: application/json"]
	_http_command.request(server_url + "/command", headers, HTTPClient.METHOD_POST, json_str)


func _post(path: String, data: Dictionary) -> void:
	# Use command channel for simplicity; could add dedicated channels
	var http := HTTPRequest.new()
	add_child(http)
	http.request_completed.connect(func(_r, _c, _h, _b): http.queue_free())
	var json_str = JSON.stringify(data)
	var headers = ["Content-Type: application/json"]
	http.request(server_url + path, headers, HTTPClient.METHOD_POST, json_str)


# ── Helpers ──────────────────────────────────────────────────

func _create_http(channel_name: String) -> HTTPRequest:
	var http := HTTPRequest.new()
	http.name = "HTTP_" + channel_name
	http.timeout = 2.0
	add_child(http)
	return http


func _parse_json(body: PackedByteArray) -> Dictionary:
	var text := body.get_string_from_utf8()
	if text.is_empty():
		return {}
	var json := JSON.new()
	var err := json.parse(text)
	if err != OK:
		return {}
	if json.data is Dictionary:
		return json.data
	return {}


func _set_connected(value: bool) -> void:
	if connected != value:
		connected = value
		connection_changed.emit(value)
		if value:
			print("ZWRuntime: Connected to %s" % server_url)
		else:
			push_warning("ZWRuntime: Lost connection to %s" % server_url)

