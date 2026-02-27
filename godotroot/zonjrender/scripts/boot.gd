extends Node

@export var do_startup_search: bool = false
@export var startup_term: String = "nephilim"

@export var headless_auto_quit: bool = false
@export var headless_quit_seconds: float = 8.0

# Correct defaults for YOUR tree:
# Main/SearchRow/Query, Main/SearchRow/Go, Main/Body/Results, Main/Body/Output
@export var query_path: NodePath = ^"SearchRow/Query"
@export var go_path: NodePath = ^"SearchRow/Go"
@export var results_path: NodePath = ^"Body/Results"
@export var output_path: NodePath = ^"Body/Output"

@onready var Query: LineEdit = get_node_or_null(query_path)
@onready var Go: Button = get_node_or_null(go_path)
@onready var Results: ItemList = get_node_or_null(results_path)
@onready var Output: RichTextLabel = get_node_or_null(output_path)

@onready var SceneClient = get_node_or_null("/root/SceneClient") # :8090
@onready var SimClient = get_node_or_null("/root/SimClient")     # :8080

var _last_results_payload: Dictionary = {}
var _library_ok: bool = false

func _ready() -> void:
	# Hard fail early with clear message if paths wrong
	if Query == null or Go == null or Results == null or Output == null:
		push_error(
			"[boot] UI nodes not found. Check NodePaths.\n" +
			" query_path=%s found=%s\n go_path=%s found=%s\n results_path=%s found=%s\n output_path=%s found=%s"
			% [
				str(query_path), str(Query != null),
				str(go_path), str(Go != null),
				str(results_path), str(Results != null),
				str(output_path), str(Output != null),
			]
		)
		return

	_wire_ui()
	_log_ui("[boot] UI wired. Checking services...")

	if headless_auto_quit and DisplayServer.get_name().to_lower() == "headless":
		_log_ui("[boot] Headless detected; quitting in %.1fs" % headless_quit_seconds)
		var t := get_tree().create_timer(headless_quit_seconds)
		t.timeout.connect(func(): get_tree().quit())

	# SceneClient signals (yours)
	if SceneClient:
		SceneClient.health_result.connect(_on_library_health)
		SceneClient.search_results.connect(_on_library_search_results)
		SceneClient.request_failed.connect(_on_library_failed)
	else:
		_log_ui("[boot] SceneClient autoload missing (library disabled).")

	# SimClient signals (yours)
	if SimClient:
		SimClient.api_ok.connect(_on_sim_ok)
		SimClient.api_fail.connect(_on_sim_fail)
	else:
		_log_ui("[boot] SimClient autoload missing (runtime disabled).")

	_attempt_library_health()
	_attempt_runtime_status()

	if do_startup_search:
		Query.text = startup_term
		_on_go_pressed()

func _wire_ui() -> void:
	Go.pressed.connect(_on_go_pressed)
	Query.text_submitted.connect(func(_t: String): _on_go_pressed())
	Results.item_selected.connect(_on_result_selected)

func _attempt_library_health() -> void:
	if not SceneClient:
		return
	_log_ui("[library] health :8090 ...")
	SceneClient.health()

func _attempt_runtime_status() -> void:
	if not SimClient:
		return
	_log_ui("[runtime] status :8080 ...")
	SimClient.command("status")

func _on_go_pressed() -> void:
	var term := Query.text.strip_edges()
	if term.is_empty():
		_log_ui("[ui] Enter a search term.")
		return

	Results.clear()
	_last_results_payload.clear()

	if SceneClient and _library_ok:
		_log_ui("[library] searching '%s' ..." % term)
		SceneClient.search(term)
	elif SimClient:
		_log_ui("[runtime] searching '%s' via snapshot ..." % term)
		SimClient.search(term)
	else:
		_log_ui("[error] No clients available to search.")

func _on_result_selected(index: int) -> void:
	if not _last_results_payload.has("items"):
		return
	var items: Array = _last_results_payload.get("items", [])
	if index < 0 or index >= items.size():
		return
	var item: Variant = items[index]
	_log_ui("[result] " + JSON.stringify(item).left(1200))

# ---- Library callbacks (8090) ----

func _on_library_health(payload: Dictionary) -> void:
	_library_ok = true
	_log_ui("[library] OK: " + JSON.stringify(payload).left(300))

func _on_library_search_results(query: String, hits: Array) -> void:
	_render_items("library", hits)

func _on_library_failed(kind: String, detail: String, status_code: int) -> void:
	_library_ok = false
	_log_ui("[library] FAIL(%s) code=%d: %s" % [kind, status_code, detail.left(600)])
	_log_ui("[library] Library is optional. Runtime on :8080 will still work.")

# ---- Runtime callbacks (8080) ----

func _on_sim_ok(action: String, data: Dictionary) -> void:
	if action == "command":
		var cmd := str(data.get("command", ""))
		if cmd == "status":
			_log_ui("[runtime] status scene=%s entities=%s t=%s weather=%s" % [
				str(data.get("scene_id", "none")),
				str(data.get("entities_active", 0)),
				str(data.get("world_time", 0.0)),
				str(data.get("weather", "unknown"))
			])
		elif cmd == "look":
			_log_ui("[runtime] " + str(data.get("text", "")))
		else:
			_log_ui("[runtime] " + JSON.stringify(data).left(800))
		return

	if action == "search":
		var items_v: Variant = data.get("items", [])
		var items: Array = items_v if typeof(items_v) == TYPE_ARRAY else []
		_render_items("runtime", items)
		return

	_log_ui("[runtime] ok(%s): %s" % [action, JSON.stringify(data).left(600)])

func _on_sim_fail(action: String, code: int, detail: String) -> void:
		_log_ui("[runtime] FAIL(%s) code=%d: %s" % [action, code, detail.left(600)])

# ---- Rendering ----

func _render_items(source: String, items: Array) -> void:
	_last_results_payload = {"items": items}

	Results.clear()
	if items.is_empty():
		_log_ui("[%s] No results." % source)
		return

	for it in items:
		Results.add_item(_label_for_item(it))

	_log_ui("[%s] %d result(s)." % [source, items.size()])

func _label_for_item(it: Variant) -> String:
	if typeof(it) == TYPE_DICTIONARY:
		var d := it as Dictionary
		if d.has("title"): return str(d["title"])
		if d.has("name"): return str(d["name"])
		if d.has("@id"): return str(d["@id"])
		if d.has("id"): return str(d["id"])
		if d.has("path"): return str(d["path"])
		if d.has("text"): return str(d["text"]).left(60)
		return JSON.stringify(d).left(60)
	return str(it).left(60)

func _log_ui(msg: String) -> void:
	print(msg)
	Output.append_text(msg + "\n")
	Output.scroll_to_line(Output.get_line_count())