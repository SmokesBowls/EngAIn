extends Node

signal ok(kind, payload)
signal fail(kind, status_code, detail)

@export var base_url: String = "http://127.0.0.1:8081"

var _http: HTTPRequest
var _kind: String = ""

func _ready() -> void:
	_http = HTTPRequest.new()
	add_child(_http)
	_http.request_completed.connect(_on_done)

func load_scene_doc(scene: Dictionary) -> void:
	_post("scene/load", "/scene/load", scene)

func _post(kind: String, path: String, payload: Dictionary) -> void:
	_kind = kind
	var url := base_url + path
	var body := JSON.stringify(payload)
	var headers := PackedStringArray(["Content-Type: application/json"])
	var err := _http.request(url, headers, HTTPClient.METHOD_POST, body)
	if err != OK:
		fail.emit(kind, -1, "HTTPRequest start failed: %s" % str(err))

func _on_done(_result: int, code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	if code < 200 or code >= 300:
		fail.emit(_kind, code, body.get_string_from_utf8().left(2000))
		return
	var parsed = JSON.parse_string(body.get_string_from_utf8())
	if parsed == null:
		fail.emit(_kind, code, "Invalid JSON response")
		return
	ok.emit(_kind, parsed)

# ---- sim_runtime endpoints ----

func load_scene(scene_id: String) -> void:
	# minimal guess: sim_runtime wants {"scene_id": "..."}.
	# If it wants "id" instead, we’ll adjust after first 400 response.
	_post("scene/load", "/scene/load", {"scene_id": scene_id})

func command(text: String) -> void:
	_post("command", "/command", {"text": text})

func snapshot() -> void:
	_post("snapshot", "/snapshot", {})

func dialogue_ask(prompt: String) -> void:
	_post("dialogue/ask", "/dialogue/ask", {"prompt": prompt})

func dialogue_say(who: String, text: String) -> void:
	_post("dialogue/say", "/dialogue/say", {"who": who, "text": text})

func inv_take(item: String) -> void:
	_post("inventory/take", "/inventory/take", {"item": item})

func inv_drop(item: String) -> void:
	_post("inventory/drop", "/inventory/drop", {"item": item})

func inv_wear(item: String) -> void:
	_post("inventory/wear", "/inventory/wear", {"item": item})

func combat_damage(target: String, amount: int) -> void:
	_post("combat/damage", "/combat/damage", {"target": target, "amount": amount})
