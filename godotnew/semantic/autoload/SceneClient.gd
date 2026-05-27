extends Node

signal scenes_listed(scenes: Array)
signal scene_loaded(scene_id: String, scene: Dictionary)
signal request_failed(kind: String, detail: String, status_code: int)

@export var api_base: String = "http://127.0.0.1:8765"

var _http: HTTPRequest
var _kind: String = ""
var _meta: Dictionary = {}

func _ready() -> void:
	_http = HTTPRequest.new()
	add_child(_http)
	_http.request_completed.connect(_on_request_completed)

func list_scenes() -> void:
	_do_get("list_scenes", "%s/list_scenes" % api_base, {})

func load_scene(scene_id: String, source_path: String = "") -> void:
	print("[SceneClient] load_scene called with: ", scene_id)
	var encoded_scene_id: String = scene_id.uri_encode()
	_do_get(
		"load_scene",
		"%s/load_scene?scene_id=%s" % [api_base, encoded_scene_id],
		{"scene_id": scene_id, "source_path": source_path}
	)

func _do_get(kind: String, url: String, meta: Dictionary) -> void:
	_kind = kind
	_meta = meta
	var err: int = _http.request(url)
	if err != OK:
		request_failed.emit(kind, "HTTPRequest start failed: %s" % str(err), -1)

func _on_request_completed(
	_result: int,
	response_code: int,
	_headers: PackedStringArray,
	body: PackedByteArray
) -> void:
	var kind: String = _kind
	var meta: Dictionary = _meta
	_kind = ""
	_meta = {}

	var raw: String = body.get_string_from_utf8()

	if response_code < 200 or response_code >= 300:
		request_failed.emit(kind, raw.left(4000), response_code)
		return

	var parsed: Variant = JSON.parse_string(raw)
	if typeof(parsed) != TYPE_DICTIONARY:
		request_failed.emit(kind, "Invalid JSON response", response_code)
		return

	var data: Dictionary = parsed as Dictionary

	if String(data.get("status", "")) != "success":
		request_failed.emit(kind, raw.left(4000), response_code)
		return

	match kind:
		"list_scenes":
			var scenes_v: Variant = data.get("scenes", [])
			var scenes: Array = []
			if typeof(scenes_v) == TYPE_ARRAY:
				scenes = scenes_v as Array
			scenes_listed.emit(scenes)

		"load_scene":
			var scene_id: String = String(meta.get("scene_id", ""))
			var source_path: String = String(meta.get("source_path", ""))
			var scene_v: Variant = data.get("data", {})
			if typeof(scene_v) != TYPE_DICTIONARY:
				request_failed.emit(kind, "Scene payload missing 'data' object", response_code)
				return
			var scene_payload: Dictionary = (scene_v as Dictionary).duplicate(true)
			if not source_path.is_empty():
				if not scene_payload.has("source_path") or String(scene_payload.get("source_path", "")).is_empty():
					scene_payload["source_path"] = source_path
				var file_meta: Dictionary = {}
				if scene_payload.has("file") and typeof(scene_payload["file"]) == TYPE_DICTIONARY:
					file_meta = (scene_payload["file"] as Dictionary).duplicate(true)
				if not file_meta.has("source_path") or String(file_meta.get("source_path", "")).is_empty():
					file_meta["source_path"] = source_path
				scene_payload["file"] = file_meta
			scene_loaded.emit(canonical_scene_id(scene_id), scene_payload)

		_:
			request_failed.emit(kind, "Unknown response kind: %s" % kind, response_code)

func canonical_scene_id(raw: String) -> String:
	if raw.is_empty():
		return "scene.000_unknown"

	var s: String = raw.strip_edges()
	var regex := RegEx.new()
	
	regex.compile("(?i)(\\.zonj\\.json|\\.json|\\.zonj)$")
	s = regex.sub(s, "", true)
	
	regex.compile("(?i)_with_semantics$")
	s = regex.sub(s, "", true)
	
	s = s.strip_edges().to_lower()
	if s.begins_with("scene."):
		s = s.substr(6)
	
	regex.compile("[^a-z0-9_]+")
	s = regex.sub(s, "_", true)
	
	regex.compile("_+")
	s = regex.sub(s, "_", true)
	
	s = s.strip_edges()
	if s.is_empty():
		return "scene.000_unknown"
		
	regex.compile("^(\\d+)[_\\.-]?(.*)$")
	var m := regex.search(s)
	if m:
		var num_str := m.get_string(1)
		var tail_str := m.get_string(2)
		
		regex.compile("[^a-z0-9_]+")
		tail_str = regex.sub(tail_str, "_", true)
		regex.compile("_+")
		tail_str = regex.sub(tail_str, "_", true)
		tail_str = tail_str.strip_edges()
		tail_str = tail_str.trim_prefix("_")
		tail_str = tail_str.trim_suffix("_")		
		
		
		var num := num_str.to_int()
		if not tail_str.is_empty():
			return "scene.%03d_%s" % [num, tail_str]
		else:
			return "scene.%03d" % num
			
	return "scene.%s" % s
