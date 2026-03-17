@tool
extends Node3D
## SemanticRenderer.gd — EngAIn Godot Thin Client (v3)
## Polls sim_runtime /snapshot, spawns/updates entities from bridge_entities.
##
## Snapshot shape (confirmed):
##   { "protocol":..., "payload": {
##       "scene_id": "scene.04_the_convergence",
##       "bridge_entities": [
##         { "entity_id":"Senareth", "transform":{"position":{"x":17.5,"y":0,"z":0},
##           "scale":{"x":0.5,"y":1.8,"z":0.5}}, "color":{"r":0.2,"g":0.6,"b":1.0},
##           "inferred_type":"character", "name":"Senareth", "semantic_tags":[...] }, ...
##       ]
##   }}

@export var engain_url: String = "http://localhost:8080"
@export var poll_interval: float = 0.5
@export var label_scale: float = 0.01

var _poll_timer: float = 0.0
var _http: HTTPRequest
var _managed: Dictionary = {}  # entity_id -> Node3D
var _connected: bool = false
var _error_count: int = 0
var _current_scene_id: String = ""

# Materials cache (one per color to avoid duplicates)
var _material_cache: Dictionary = {}


func _ready() -> void:
	_http = HTTPRequest.new()
	_http.timeout = 2.0
	_http.request_completed.connect(_on_snapshot_received)
	add_child(_http)
	print("[SemanticRenderer] Ready -> %s  poll=%.1fs" % [engain_url, poll_interval])


func _process(delta: float) -> void:
	_poll_timer -= delta
	if _poll_timer <= 0.0:
		_poll_timer = poll_interval
		_poll_snapshot()


func _poll_snapshot() -> void:
	if _http.get_http_client_status() != HTTPClient.STATUS_DISCONNECTED:
		return  # previous request still in flight
	var err = _http.request(engain_url + "/snapshot")
	if err != OK and _error_count < 3:
		_error_count += 1
		print("[SemanticRenderer] HTTP error: %d" % err)


func _on_snapshot_received(result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	if result != HTTPRequest.RESULT_SUCCESS or response_code != 200:
		_error_count += 1
		if _error_count <= 3 or _error_count % 30 == 0:
			print("[SemanticRenderer] Connection failed (%dx)" % _error_count)
		_connected = false
		return

	if not _connected:
		_connected = true
		_error_count = 0
		print("[SemanticRenderer] Connected to sim_runtime!")

	var json = JSON.new()
	if json.parse(body.get_string_from_utf8()) != OK:
		return

	var data: Dictionary = json.data
	var payload: Dictionary = data.get("payload", data)
	_apply_snapshot(payload)


func _apply_snapshot(payload: Dictionary) -> void:
	var bridge_entities: Array = payload.get("bridge_entities", [])
	var scene_id: String = payload.get("scene_id", "")

	if scene_id != "" and scene_id != _current_scene_id:
		_current_scene_id = scene_id
		print("[SemanticRenderer] Scene: %s (%d entities)" % [scene_id, bridge_entities.size()])

	if bridge_entities.is_empty():
		return

	var seen_ids: Dictionary = {}

	for entity_data in bridge_entities:
		var eid: String = entity_data.get("entity_id", entity_data.get("name", "unknown"))
		seen_ids[eid] = true

		if _managed.has(eid):
			_update_entity(_managed[eid], entity_data)
		else:
			_spawn_entity(eid, entity_data)

	# Remove dead entities
	var dead: Array = []
	for eid in _managed.keys():
		if not seen_ids.has(eid):
			dead.append(eid)
	for eid in dead:
		_remove_entity(eid)


func _spawn_entity(eid: String, data: Dictionary) -> void:
	var node := MeshInstance3D.new()
	node.name = "entity_%s" % eid

	# Mesh: capsule for characters, box for others
	var etype: String = data.get("inferred_type", "unknown")
	var mesh_type: String = data.get("placeholder_mesh", "box")
	if mesh_type == "capsule" or etype == "character":
		var capsule := CapsuleMesh.new()
		capsule.radius = 0.25
		capsule.height = 1.0
		node.mesh = capsule
	else:
		node.mesh = BoxMesh.new()

	# Position
	var transform_data: Dictionary = data.get("transform", {})
	var pos: Dictionary = transform_data.get("position", {})
	node.position = Vector3(
		pos.get("x", 0.0),
		pos.get("y", 0.0),
		pos.get("z", 0.0)
	)

	# Scale
	var scl: Dictionary = transform_data.get("scale", {"x": 1, "y": 1, "z": 1})
	node.scale = Vector3(
		scl.get("x", 1.0),
		scl.get("y", 1.0),
		scl.get("z", 1.0)
	)

	# Color material (unshaded for visibility)
	var color_data: Dictionary = data.get("color", {"r": 0.7, "g": 0.7, "b": 0.7})
	var color := Color(
		color_data.get("r", 0.7),
		color_data.get("g", 0.7),
		color_data.get("b", 0.7),
		1.0
	)
	node.material_override = _get_material(color)

	# Metadata
	node.set_meta("entity_id", eid)
	node.set_meta("entity_type", etype)
	node.set_meta("entity_name", data.get("name", eid))
	node.set_meta("zw_concept", data.get("zw_concept", ""))
	node.set_meta("ap_profile", data.get("ap_profile", ""))

	var tags: Array = data.get("semantic_tags", [])
	node.set_meta("semantic_tags", ",".join(PackedStringArray(tags)))

	# Label
	var label := Label3D.new()
	label.text = data.get("name", eid)
	label.pixel_size = label_scale
	label.position.y = scl.get("y", 1.0) * 0.6
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	label.no_depth_test = true
	label.font_size = 32
	node.add_child(label)

	add_child(node)
	_managed[eid] = node


func _update_entity(node: Node3D, data: Dictionary) -> void:
	var transform_data: Dictionary = data.get("transform", {})
	var pos: Dictionary = transform_data.get("position", {})
	if not pos.is_empty():
		node.position = Vector3(
			pos.get("x", node.position.x),
			pos.get("y", node.position.y),
			pos.get("z", node.position.z)
		)

	var scl: Dictionary = transform_data.get("scale", {})
	if not scl.is_empty():
		node.scale = Vector3(
			scl.get("x", node.scale.x),
			scl.get("y", node.scale.y),
			scl.get("z", node.scale.z)
		)

	var color_data: Dictionary = data.get("color", {})
	if not color_data.is_empty():
		var color := Color(
			color_data.get("r", 0.7),
			color_data.get("g", 0.7),
			color_data.get("b", 0.7),
			1.0
		)
		if node is MeshInstance3D:
			node.material_override = _get_material(color)


func _remove_entity(eid: String) -> void:
	if _managed.has(eid):
		var node = _managed[eid]
		node.queue_free()
		_managed.erase(eid)
		print("[SemanticRenderer] Removed: %s" % eid)


func _get_material(color: Color) -> StandardMaterial3D:
	var key: String = color.to_html(false)
	if _material_cache.has(key):
		return _material_cache[key]

	var mat := StandardMaterial3D.new()
	mat.albedo_color = color
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_material_cache[key] = mat
	return mat


# --- Public API ---

func get_status() -> Dictionary:
	return {
		"connected": _connected,
		"managed": _managed.size(),
		"errors": _error_count,
		"scene": _current_scene_id,
	}

func get_entity(eid: String) -> Node3D:
	return _managed.get(eid)

func get_all_entities() -> Dictionary:
	return _managed.duplicate()

func clear_all() -> void:
	for eid in _managed.keys():
		_remove_entity(eid)
	_managed.clear()
