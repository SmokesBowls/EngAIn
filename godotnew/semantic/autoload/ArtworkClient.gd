extends Node

signal artwork_loaded(scene_id: String, texture: Texture2D)
signal artwork_failed(scene_id: String, detail: String, status_code: int)

@export var api_base: String = "http://127.0.0.1:8090"

var _http: HTTPRequest
var _current_scene_id: String = ""

func _ready() -> void:
	_http = HTTPRequest.new()
	add_child(_http)
	_http.request_completed.connect(_on_request_completed)

func get_artwork(scene_id: String) -> void:
	if scene_id.strip_edges().is_empty():
		artwork_failed.emit(scene_id, "scene_id is empty", -1)
		return

	if not _current_scene_id.is_empty():
		artwork_failed.emit(scene_id, "Artwork request already in progress for: %s" % _current_scene_id, -1)
		return

	_current_scene_id = scene_id
	var url: String = "%s/api/trixel/artwork/%s" % [api_base, scene_id.uri_encode()]
	var err: int = _http.request(url)
	if err != OK:
		_current_scene_id = ""
		artwork_failed.emit(scene_id, "HTTPRequest start failed: %s" % str(err), -1)

func get_latest_artwork() -> void:
	"""Fetch the most recent Trixel artwork regardless of scene_id."""
	get_artwork("latest")

func _on_request_completed(
	result: int,
	response_code: int,
	headers: PackedStringArray,
	body: PackedByteArray
) -> void:
	var scene_id: String = _current_scene_id
	_current_scene_id = ""

	if result != HTTPRequest.RESULT_SUCCESS:
		artwork_failed.emit(scene_id, "HTTPRequest failed: %s" % str(result), response_code)
		return

	if response_code < 200 or response_code >= 300:
		var error_text: String = body.get_string_from_utf8()
		artwork_failed.emit(scene_id, error_text.left(4000), response_code)
		return

	var img: Image = Image.new()
	var err: Error = img.load_png_from_buffer(body)
	if err != OK:
		artwork_failed.emit(scene_id, "PNG decode failed: %s" % str(err), response_code)
		return

	var tex: ImageTexture = ImageTexture.create_from_image(img)
	artwork_loaded.emit(scene_id, tex)
