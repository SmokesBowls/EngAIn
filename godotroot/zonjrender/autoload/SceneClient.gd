extends Node

signal health_result(payload: Dictionary)
signal chapters_result(chapter: int, matches: Array)
signal search_results(query: String, hits: Array)
signal scene_loaded(scene_id: String, scene: Dictionary)
signal request_failed(kind: String, detail: String, status_code: int)

@export var api_base: String = "http://127.0.0.1:8090"

var _http: HTTPRequest
var _kind: String = ""
var _meta: Dictionary = {}

func _ready() -> void:
	_http = HTTPRequest.new()
	add_child(_http)
	_http.request_completed.connect(_on_request_completed)

func _do_get(kind: String, url: String, meta: Dictionary) -> void:
	_kind = kind
	_meta = meta
	var err: int = _http.request(url)
	if err != OK:
		request_failed.emit(kind, "HTTPRequest start failed: err=%s url=%s" % [str(err), url], -1)

func _on_request_completed(result: int, response_code: int, headers: PackedStringArray, body: PackedByteArray) -> void:
	var kind: String = _kind
	var meta: Dictionary = _meta
	_kind = ""
	_meta = {}

	var raw: String = body.get_string_from_utf8()

	# ✅ Critical fix: transport-layer failure (connection refused, DNS, etc.)
	if result != OK:
		request_failed.emit(
			kind,
			"Transport failure: result=%d response_code=%d api_base=%s raw=%s" % [
				result, response_code, api_base, raw.left(400)
			],
			response_code
		)
		return

	# HTTP failure
	if response_code < 200 or response_code >= 300:
		request_failed.emit(kind, raw.left(4000), response_code)
		return

	var parsed: Variant = JSON.parse_string(raw)
	if typeof(parsed) != TYPE_DICTIONARY:
		request_failed.emit(kind, "Invalid JSON response: raw=%s" % raw.left(800), response_code)
		return

	var data: Dictionary = parsed as Dictionary

	if kind == "health":
		health_result.emit(data)
	elif kind == "chapters":
		var chap: int = int(meta.get("chapter", -1))
		var matches_v: Variant = data.get("matches")
		var matches: Array = matches_v if typeof(matches_v) == TYPE_ARRAY else []
		chapters_result.emit(chap, matches)
	elif kind == "search":
		var q: String = String(meta.get("q", ""))
		var hits_v: Variant = data.get("hits")
		var hits: Array = hits_v if typeof(hits_v) == TYPE_ARRAY else []
		search_results.emit(q, hits)
	elif kind == "scene":
		var sid: String = String(meta.get("scene_id", ""))
		scene_loaded.emit(sid, data)

func health() -> void:
	_do_get("health", "%s/health" % api_base, {})

func chapters(chapter_num: int) -> void:
	_do_get("chapters", "%s/chapters/%d" % [api_base, chapter_num], {"chapter": chapter_num})

func search(q: String) -> void:
	var encoded: String = q.uri_encode()
	_do_get("search", "%s/search?q=%s" % [api_base, encoded], {"q": q})

func get_scene(scene_id: String) -> void:
	var encoded: String = scene_id.uri_encode()
	_do_get("scene", "%s/scenes/%s" % [api_base, encoded], {"scene_id": scene_id})