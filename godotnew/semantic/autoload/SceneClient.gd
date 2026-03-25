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

func load_scene(scene_id: String) -> void:
	var encoded_scene_id: String = scene_id.uri_encode()
	_do_get(
		"load_scene",
		"%s/load_scene?scene_id=%s" % [api_base, encoded_scene_id],
		{"scene_id": scene_id}
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
			var scene_v: Variant = data.get("data", {})
			if typeof(scene_v) != TYPE_DICTIONARY:
				request_failed.emit(kind, "Scene payload missing 'data' object", response_code)
				return
			scene_loaded.emit(scene_id, scene_v as Dictionary)

		_:
			request_failed.emit(kind, "Unknown response kind: %s" % kind, response_code)
