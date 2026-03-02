extends Node3D
## SemanticRenderer.gd — Reads bridge_entities from EngAIn runtime snapshot
## and spawns colored placeholder meshes in the 3D scene.
##
## Attach to a Node3D in your scene. Set runtime_url to your sim_runtime address.
## On scene load, this spawns capsules/cubes/spheres for each resolved entity.

@export var runtime_url: String = "http://localhost:8080"
@export var auto_poll: bool = true
@export var poll_interval: float = 2.0

var _http: HTTPRequest
var _current_scene_id: String = ""
var _entity_nodes: Dictionary = {} # entity_id -> Node3D


func _ready() -> void:
	_http = HTTPRequest.new()
	_http.timeout = 5.0
	add_child(_http)
	_http.request_completed.connect(_on_snapshot_received)

	if auto_poll:
		var timer := Timer.new()
		timer.wait_time = poll_interval
		timer.autostart = true
		timer.timeout.connect(_poll_snapshot)
		add_child(timer)
		# Initial poll
		call_deferred("_poll_snapshot")

	print("[SemanticRenderer] Ready — polling %s" % runtime_url)


func _poll_snapshot() -> void:
	if _http.get_http_client_status() != HTTPClient.STATUS_DISCONNECTED:
		return # Previous request still in flight
	_http.request("%s/snapshot" % runtime_url)


func _on_snapshot_received(result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	if result != HTTPRequest.RESULT_SUCCESS or response_code != 200:
		return

	var json := JSON.new()
	if json.parse(body.get_string_from_utf8()) != OK:
		return

	var data: Dictionary = json.data
	if not data is Dictionary:
		return

	# Unwrap protocol envelope (supports 'payload', 'snapshot', or root)
	var payload: Dictionary = data.get("payload", data.get("snapshot", data))
	if payload.has("snapshot") and payload["snapshot"] is Dictionary:
		payload = payload["snapshot"]

	var scene_id: String = str(payload.get("scene_id", ""))
	var bridge_entities: Array = payload.get("bridge_entities", [])

	# Only rebuild if scene changed or we have no entities
	if scene_id == _current_scene_id and not _entity_nodes.is_empty():
		return

	if bridge_entities.is_empty():
		# Only print once per scene if empty
		if _current_scene_id != scene_id:
			print("[SemanticRenderer] Localizing scene '%s' — No bridge_entities found" % scene_id)
			_current_scene_id = scene_id
			_clear_entities()
		return

	print("[SemanticRenderer] New scene detected: '%s' (%d entities)" % [scene_id, bridge_entities.size()])
	_current_scene_id = scene_id
	_clear_entities()
	_spawn_entities(bridge_entities)


func _clear_entities() -> void:
	for eid in _entity_nodes:
		var node: Node3D = _entity_nodes[eid]
		if is_instance_valid(node):
			node.queue_free()
	_entity_nodes.clear()

func _spawn_entities(entities: Array) -> void:
	print("[SemanticRenderer] Starting spawn loop for %d entities" % entities.size())
	var spawn_count := 0
	for ent_data in entities:
		if not ent_data is Dictionary:
			printerr("[SemanticRenderer] ERROR: Entity data is not a dictionary: ", typeof(ent_data))
			continue

		var eid: String = str(ent_data.get("entity_id", "unknown"))
		var mesh_type: String = str(ent_data.get("placeholder_mesh", "cube"))
		var color_data: Dictionary = ent_data.get("color", {"r": 1.0, "g": 0.0, "b": 1.0})
		var transform_data: Dictionary = ent_data.get("transform", {})
		var entity_name: String = str(ent_data.get("name", eid))
		var concept: String = str(ent_data.get("zw_concept", "unknown"))
		
		# Build position/scale
		var pos_data: Dictionary = transform_data.get("position", {"x": 0, "y": 0, "z": 0})
		var scl_data: Dictionary = transform_data.get("scale", {"x": 1, "y": 1, "z": 1})

		var pos := Vector3(float(pos_data.get("x", 0)), float(pos_data.get("y", 0)), float(pos_data.get("z", 0)))
		var scl := Vector3(float(scl_data.get("x", 1)), float(scl_data.get("y", 1)), float(scl_data.get("z", 1)))
		var color := Color(float(color_data.get("r", 1.0)), float(color_data.get("g", 0.0)), float(color_data.get("b", 1.0)))

		# Create the entity node
		var entity_root := Node3D.new()
		entity_root.name = "Bridge_%s_%s" % [eid, str(spawn_count)]
		entity_root.position = pos
		entity_root.scale = Vector3.ONE # Scale is handled by mesh
		
		# Create mesh
		var mesh_instance := _create_mesh(mesh_type, scl, color)
		if mesh_instance:
			entity_root.add_child(mesh_instance)
		else:
			printerr("[SemanticRenderer] FAILED to create mesh for ", eid)

		# Create floating label
		var label := _create_label(entity_name, concept, color)
		if label:
			label.position.y = scl.y + 0.3
			entity_root.add_child(label)

		add_child(entity_root)
		_entity_nodes[eid] = entity_root
		spawn_count += 1
		
	print("[SemanticRenderer] Spawn loop finished. Successfully spawned %d/%d nodes. Total children: %d" % [spawn_count, entities.size(), get_child_count()])


func _create_mesh(mesh_type: String, scl: Vector3, color: Color) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	mi.name = "Mesh"

	match mesh_type:
		"capsule":
			var capsule := CapsuleMesh.new()
			capsule.radius = scl.x * 0.5
			capsule.height = scl.y
			mi.mesh = capsule

		"sphere":
			var sphere := SphereMesh.new()
			sphere.radius = scl.x * 0.5
			sphere.height = scl.y
			mi.mesh = sphere

		"cylinder":
			var cylinder := CylinderMesh.new()
			cylinder.top_radius = scl.x * 0.5
			cylinder.bottom_radius = scl.x * 0.5
			cylinder.height = scl.y
			mi.mesh = cylinder

		"plane":
			var plane := PlaneMesh.new()
			plane.size = Vector2(scl.x, scl.z)
			mi.mesh = plane

		_: # "cube" or fallback
			var box := BoxMesh.new()
			box.size = scl
			mi.mesh = box

	# Material
	var mat := StandardMaterial3D.new()
	mat.albedo_color = color
	mat.emission_enabled = true
	mat.emission = color * 0.3
	mat.emission_energy_multiplier = 0.5
	mi.material_override = mat

	# Center vertically so the base of the mesh is at Y=0
	mi.position.y = scl.y * 0.5
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON

	return mi


func _create_label(entity_name: String, concept: String, color: Color) -> Label3D:
	var label := Label3D.new()
	label.name = "Label"
	label.text = "%s\n[%s]" % [entity_name, concept]
	label.font_size = 24
	label.modulate = color
	label.outline_modulate = Color.BLACK
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	label.no_depth_test = false # Ensure it draws in 3D space
	label.outline_size = 4
	return label


## Manual trigger: call from GDScript or via signal
func force_refresh() -> void:
	_current_scene_id = ""
	_poll_snapshot()
