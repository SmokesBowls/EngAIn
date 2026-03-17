extends Node

signal sim_response(kind: String, payload: Dictionary)
signal sim_failed(kind: String, detail: String, status_code: int)

@export var sim_base: String = "http://127.0.0.1:8080"

var _http: HTTPRequest
var _kind: String = ""

func _ready() -> void:
	_http = HTTPRequest.new()
	add_child(_http)
	_http.request_completed.connect(_on_done)

func load_scene_doc(scene_doc: Dictionary) -> void:
	_post("scene/load", "/scene/load", scene_doc)

func command(text: String) -> void:
	_post("command", "/command", {"text": text})

func snapshot() -> void:
	_do_get_request("snapshot", "/snapshot")

func _post(kind: String, path: String, payload: Dictionary) -> void:
	_kind = kind
	var url: String = "%s%s" % [sim_base, path]
	var body: String = JSON.stringify(payload)
	var headers: PackedStringArray = PackedStringArray(["Content-Type: application/json"])
	var err: int = _http.request(url, headers, HTTPClient.METHOD_POST, body)
	if err != OK:
		sim_failed.emit(kind, "HTTPRequest start failed: %s" % str(err), -1)

func _do_get_request(kind: String, path: String) -> void:
	_kind = kind
	var url: String = "%s%s" % [sim_base, path]
	var err: int = _http.request(url)
	if err != OK:
		sim_failed.emit(kind, "HTTPRequest start failed: %s" % str(err), -1)

func _on_done(
	_result: int,
	response_code: int,
	_headers: PackedStringArray,
	body: PackedByteArray
) -> void:
	var kind: String = _kind
	_kind = ""

	var raw: String = body.get_string_from_utf8()
	if response_code < 200 or response_code >= 300:
		sim_failed.emit(kind, raw.left(4000), response_code)
		return

	var parsed: Variant = JSON.parse_string(raw)
	if typeof(parsed) != TYPE_DICTIONARY:
		sim_failed.emit(kind, "Invalid JSON response", response_code)
		return

	sim_response.emit(kind, parsed as Dictionary)
