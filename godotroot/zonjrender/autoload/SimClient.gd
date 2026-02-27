extends Node

signal api_ok(action: String, data: Dictionary)
signal api_fail(action: String, code: int, detail: String)

@export var base_url: String = "http://127.0.0.1:8080"

var _http: HTTPRequest
var _pending_action: String = ""
var _pending_meta: Dictionary = {}

func _ready() -> void:
	_http = HTTPRequest.new()
	add_child(_http)
	_http.request_completed.connect(_on_request_completed)
	print("[SimClient] base_url=", base_url)

func command(text: String) -> void:
	_pending_action = "command"
	_pending_meta = {"text": text}
	_request_json_post(base_url + "/command", {"text": text})

func scene_load(zonj: Dictionary) -> void:
	_pending_action = "scene/load"
	_pending_meta = {"@id": zonj.get("@id", "unknown")}
	_request_json_post(base_url + "/scene/load", {"zonj": zonj})

func snapshot() -> void:
	_pending_action = "snapshot"
	_pending_meta = {}
	_request_get(base_url + "/snapshot")

# Runtime has no /search; implement via snapshot search.
func search(term: String) -> void:
	_pending_action = "search"
	_pending_meta = {"term": term}
	_request_get(base_url + "/snapshot")

func _request_get(url: String) -> void:
	var headers := PackedStringArray(["Accept: application/json"])
	var err := _http.request(url, headers, HTTPClient.METHOD_GET)
	if err != OK:
		_emit_fail(_pending_action, err, "GET request() failed url=" + url)

func _request_json_post(url: String, payload: Dictionary) -> void:
	var headers := PackedStringArray([
		"Content-Type: application/json",
		"Accept: application/json"
	])
	var body := JSON.stringify(payload)
	var err := _http.request(url, headers, HTTPClient.METHOD_POST, body)
	if err != OK:
		_emit_fail(_pending_action, err, "POST request() failed url=" + url + " body=" + body.left(200))

func _on_request_completed(result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	var action := _pending_action
	var meta := _pending_meta
	_pending_action = ""
	_pending_meta = {}

	var text := body.get_string_from_utf8()

	if result != OK:
		_emit_fail(action, result, "transport fail http=%d body=%s" % [response_code, text.left(400)])
		return

	if response_code < 200 or response_code >= 300:
		_emit_fail(action, response_code, "http fail body=%s" % text.left(400))
		return

	var j := JSON.new()
	var perr := j.parse(text)
	if perr != OK:
		_emit_fail(action, perr, "json parse fail body=%s" % text.left(400))
		return

	if typeof(j.data) != TYPE_DICTIONARY:
		_emit_fail(action, -2, "json not dict type=%d" % typeof(j.data))
		return

	var data := j.data as Dictionary

	if action == "search":
		var term := str(meta.get("term", "")).strip_edges()
		var results := _search_snapshot(data, term)
		api_ok.emit("search", results)
		return

	api_ok.emit(action, data)

func _emit_fail(action: String, code: int, detail: String) -> void:
	push_error("sim_api fail [%s] (%d): %s" % [action, code, detail])
	api_fail.emit(action, code, detail)

func _search_snapshot(envelope_or_snap: Dictionary, term: String) -> Dictionary:
	var out := {"items": [], "count": 0, "term": term}
	if term.is_empty():
		return out

	# Try common envelope keys
	var snap := envelope_or_snap
	if envelope_or_snap.has("snapshot") and typeof(envelope_or_snap["snapshot"]) == TYPE_DICTIONARY:
		snap = envelope_or_snap["snapshot"]
	elif envelope_or_snap.has("data") and typeof(envelope_or_snap["data"]) == TYPE_DICTIONARY:
		snap = envelope_or_snap["data"]

	var matches: Array = []
	_collect_matches(matches, snap, term, "")
	out["items"] = matches
	out["count"] = matches.size()
	return out

func _collect_matches(out_matches: Array, node: Variant, term: String, path: String) -> void:
	var t := term.to_lower()

	match typeof(node):
		TYPE_STRING:
			var s: String = node
			if s.to_lower().find(t) != -1:
				out_matches.append({"path": path, "text": s.left(240)})
		TYPE_DICTIONARY:
			var d := node as Dictionary
			for k in d.keys():
				var nk := str(k)
				var np: String = nk if path == "" else (path + "." + nk)
				_collect_matches(out_matches, d[k], term, np)
		TYPE_ARRAY:
			var a := node as Array
			for i in range(a.size()):
				var np := "%s[%d]" % [path, i]
				_collect_matches(out_matches, a[i], term, np)
		_:
			pass