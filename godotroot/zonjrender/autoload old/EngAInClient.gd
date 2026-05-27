extends Node
## EngAInClient.gd — Command & scene management layer
## Add as Autoload: Project Settings → Autoload → Name: EngAInClient
##
## Sends commands, loads scenes, links vaults.
## SemanticRenderer handles visuals; this handles logic.

signal scene_loaded(scene_id: String, entity_count: int)
signal command_result(result: Dictionary)
signal vault_linked(scene_count: int)
signal connection_changed(connected: bool)

@export var engain_url: String = "http://localhost:8080"

var _http_cmd: HTTPRequest
var _http_scene: HTTPRequest
var _http_vault: HTTPRequest
var _http_health: HTTPRequest
var _health_timer: float = 0.0
var _connected: bool = false
var _pending_callback: Callable


func _ready() -> void:
	_http_cmd = _make_http("_on_command_done")
	_http_scene = _make_http("_on_scene_done")
	_http_vault = _make_http("_on_vault_done")
	_http_health = _make_http("_on_health_done")
	print("[EngAInClient] Ready -> %s" % engain_url)


func _process(delta: float) -> void:
	_health_timer -= delta
	if _health_timer <= 0.0:
		_health_timer = 5.0
		_check_health()


# --- Public API ---

func load_scene(scene_id: String) -> void:
	var body := JSON.stringify({"scene_id": scene_id})
	_post(_http_scene, "/scene/load", body)
	print("[EngAInClient] Loading scene: %s" % scene_id)


func send_command(command: String, args: Dictionary = {}) -> void:
	args["command"] = command
	_post(_http_cmd, "/command", JSON.stringify(args))


func link_vault(vault_root: String, manifest_path: String) -> void:
	## Call with paths on the SERVER machine (where sim_runtime runs)
	var manifest_json := FileAccess.get_file_as_string(manifest_path)
	if manifest_json.is_empty():
		push_error("[EngAInClient] Cannot read manifest: %s" % manifest_path)
		return
	var manifest = JSON.parse_string(manifest_json)
	if manifest == null:
		push_error("[EngAInClient] Invalid JSON in manifest")
		return
	var body := JSON.stringify({"vault_root": vault_root, "manifest": manifest})
	_post(_http_vault, "/vault/link", body)
	print("[EngAInClient] Linking vault: %s" % vault_root)


func search_vault(query: String, limit: int = 10) -> void:
	var url := "%s/vault/search?q=%s&limit=%d" % [engain_url, query.uri_encode(), limit]
	_http_cmd.request(url)


func runtime_is_connected() -> bool:
	return _connected


# --- HTTP helpers ---

func _make_http(callback: String) -> HTTPRequest:
	var h := HTTPRequest.new()
	h.timeout = 3.0
	h.request_completed.connect(Callable(self, callback))
	add_child(h)
	return h


func _post(http: HTTPRequest, path: String, body: String) -> void:
	if http.get_http_client_status() != HTTPClient.STATUS_DISCONNECTED:
		push_warning("[EngAInClient] Request in flight, skipping %s" % path)
		return
	http.request(
		engain_url + path,
		["Content-Type: application/json"],
		HTTPClient.METHOD_POST,
		body
	)


func _check_health() -> void:
	if _http_health.get_http_client_status() != HTTPClient.STATUS_DISCONNECTED:
		return
	_http_health.request(engain_url + "/health")


# --- Callbacks ---

func _on_command_done(result: int, code: int, _h: PackedStringArray, body: PackedByteArray) -> void:
	if result != HTTPRequest.RESULT_SUCCESS or code != 200:
		return
	var parsed = JSON.parse_string(body.get_string_from_utf8())
	if parsed:
		command_result.emit(parsed)


func _on_scene_done(result: int, code: int, _h: PackedStringArray, body: PackedByteArray) -> void:
	if result != HTTPRequest.RESULT_SUCCESS or code != 200:
		push_error("[EngAInClient] Scene load failed: %d / %d" % [result, code])
		return
	var parsed = JSON.parse_string(body.get_string_from_utf8())
	if parsed:
		var sid: String = parsed.get("scene_id", "unknown")
		print("[EngAInClient] Scene loaded: %s" % sid)
		scene_loaded.emit(sid, 0)


func _on_vault_done(result: int, code: int, _h: PackedStringArray, body: PackedByteArray) -> void:
	if result != HTTPRequest.RESULT_SUCCESS or code != 200:
		push_error("[EngAInClient] Vault link failed: %d / %d" % [result, code])
		return
	var parsed = JSON.parse_string(body.get_string_from_utf8())
	if parsed:
		var count: int = parsed.get("scenes_loaded", 0)
		print("[EngAInClient] Vault linked: %d scenes" % count)
		vault_linked.emit(count)


func _on_health_done(result: int, code: int, _h: PackedStringArray, _body: PackedByteArray) -> void:
	var was := _connected
	_connected = (result == HTTPRequest.RESULT_SUCCESS and code == 200)
	if _connected != was:
		connection_changed.emit(_connected)
		if _connected:
			print("[EngAInClient] sim_runtime connected")
		else:
			print("[EngAInClient] sim_runtime disconnected")
