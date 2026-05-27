extends Node
# ─────────────────────────────────────────────
#  SceneNetworkService.gd
#  Add as Autoload: Project > Autoload > SceneNetworkService
#  Owns ALL HTTP polling and JSON parsing.
#  Emits clean typed signals — renderer never touches network.
# ─────────────────────────────────────────────

signal fetch_succeeded(scene_id: String, data: Dictionary)
signal fetch_failed(scene_id: String, detail: String)

const HOST := "127.0.0.1"
const PORT := 8765

# ── Async runtime fetch (uses SceneClient if present) ──
func fetch_scene(scene_id: String) -> void:
	var sc = get_node_or_null("/root/SceneClient")
	if sc != null:
		if not sc.scene_loaded.is_connected(_on_client_loaded):
			sc.scene_loaded.connect(_on_client_loaded)
		if not sc.request_failed.is_connected(_on_client_failed):
			sc.request_failed.connect(_on_client_failed)
		sc.load_scene(scene_id)
	else:
		push_warning("[SceneNetworkService] SceneClient not found — falling back to direct HTTP")
		var data := await _direct_fetch(scene_id)
		if data.is_empty():
			fetch_failed.emit(scene_id, "Direct HTTP fetch returned empty data")
		else:
			fetch_succeeded.emit(scene_id, data)


# ── Synchronous editor fetch (blocks main thread briefly — localhost only) ──
func fetch_scene_sync(scene_id: String) -> Dictionary:
	return _sync_fetch(scene_id)


# ── SceneClient passthrough ────────────────────
func _on_client_loaded(scene_id: String, data: Dictionary) -> void:
	fetch_succeeded.emit(scene_id, data)

func _on_client_failed(kind: String, detail: String, code: int) -> void:
	fetch_failed.emit(kind, "[%d] %s" % [code, detail])


# ── Direct async HTTP (fallback) ───────────────
func _direct_fetch(scene_id: String) -> Dictionary:
	var http := HTTPRequest.new()
	add_child(http)
	var url := "http://%s:%d/load_scene?scene_id=%s" % [HOST, PORT, scene_id.uri_encode()]
	http.request(url)
	var result = await http.request_completed
	http.queue_free()
	return _parse_response(result[1], result[3])


# ── Synchronous HTTP (editor only) ────────────
func _sync_fetch(scene_id: String) -> Dictionary:
	var http := HTTPClient.new()
	if http.connect_to_host(HOST, PORT) != OK:
		push_error("[SceneNetworkService] Cannot connect to %s:%d" % [HOST, PORT])
		return {}
	var tries := 0
	while http.get_status() in [HTTPClient.STATUS_CONNECTING, HTTPClient.STATUS_RESOLVING]:
		http.poll()
		tries += 1
		if tries > 200:
			return {}
	if http.get_status() != HTTPClient.STATUS_CONNECTED:
		push_error("[SceneNetworkService] Connection failed — is scene server running?")
		return {}
	http.request(
		HTTPClient.METHOD_GET,
		"/load_scene?scene_id=%s" % scene_id.uri_encode(),
		["Accept: application/json"]
	)
	while http.get_status() == HTTPClient.STATUS_REQUESTING:
		http.poll()
	var body := PackedByteArray()
	while http.get_status() == HTTPClient.STATUS_BODY:
		http.poll()
		var chunk := http.read_response_body_chunk()
		if chunk.size() > 0:
			body.append_array(chunk)
	return _parse_body(body.get_string_from_utf8())

# ── Parsing ────────────────────────────────────
func _parse_response(code: int, body: PackedByteArray) -> Dictionary:
	if code < 200 or code >= 300:
		push_error("[SceneNetworkService] HTTP %d" % code)
		return {}
	return _parse_body(body.get_string_from_utf8())

func _parse_body(raw: String) -> Dictionary:
	var parsed = JSON.parse_string(raw)
	if typeof(parsed) != TYPE_DICTIONARY:
		push_error("[SceneNetworkService] Invalid JSON")
		return {}
	var wrapped := parsed as Dictionary
	if String(wrapped.get("status", "")) != "success":
		push_error("[SceneNetworkService] Server returned non-success")
		return {}
	var data = wrapped.get("data", wrapped)
	if typeof(data) != TYPE_DICTIONARY:
		push_error("[SceneNetworkService] No data dict in response")
		return {}
	return data as Dictionary
