extends Node

## EngAInBridge.gd - The Godot End of the Governed Reality Bridge
## Manages the Python subprocess and Duplex JSON-RPC communication.

signal state_updated(snapshot: Dictionary)
signal command_result(result: Dictionary)
signal bridge_error(message: String)
signal scene_loaded(scene_id: String, entity_count: int)

@export_group("Bridge Settings")
@export var python_executable: String = "python3"
@export var engain_core_path: String = "" # Auto-detects if empty
@export var auto_load_on_ready: bool = false
@export var test_scene_id: String = "chapter1_opening"

var process_id: int = -1
var pipes: Dictionary = {}
var current_scene_entities: Array = []
var bridge_started := false

func _ready() -> void:
	if engain_core_path == "":
		engain_core_path = ProjectSettings.globalize_path("res://")
	
	if auto_load_on_ready:
		load_scene(test_scene_id)

func load_scene(scene_id: String) -> void:
	print("[EngAInBridge] Requesting scene: ", scene_id)
	
	# 1. Resolve paths
	var adapter_path = engain_core_path.path_join("tests/godot_bridge_test.py")
	
	# 2. Launch subprocess to get JSON
	var args = ["--scene", scene_id]
	var output = []
	var exit_code = OS.execute(python_executable, [adapter_path] + args, output, true)
	
	if exit_code != 0:
		var err = "[EngAInBridge] Python bridge failed with exit code: " + str(exit_code)
		printerr(err)
		bridge_error.emit(err)
		return
	
	# 3. Parse JSON output
	var full_output = "".join(output)
	var json = JSON.new()
	var error = json.parse(full_output)
	if error != OK:
		printerr("[EngAInBridge] Failed to parse JSON: ", full_output)
		bridge_error.emit("JSON Parse Error")
		return
		
	var data = json.get_data()
	if data.has("error"):
		printerr("[EngAInBridge] Bridge Error: ", data.get("error"))
		bridge_error.emit(data.get("error"))
		return
		
	# 4. Spawn entities
	current_scene_entities = data.get("entities", [])
	_clear_scene()
	
	for entity_data in current_scene_entities:
		spawn_entity(entity_data)
		
	scene_loaded.emit(scene_id, current_scene_entities.size())
	print("[EngAInBridge] Scene loaded successfully with ", current_scene_entities.size(), " entities.")

func spawn_entity(entity_data: Dictionary) -> Node3D:
	var mesh_instance := MeshInstance3D.new()

	# 1. Mesh type
	match entity_data.get("placeholder_mesh", "cube"):
		"capsule":
			mesh_instance.mesh = CapsuleMesh.new()
		"cylinder":
			mesh_instance.mesh = CylinderMesh.new()
		"sphere":
			mesh_instance.mesh = SphereMesh.new()
		"plane":
			mesh_instance.mesh = PlaneMesh.new()
		_:
			mesh_instance.mesh = BoxMesh.new()

	# 2. Position from flat transform dict
	var t: Dictionary = entity_data.get("transform", {})
	var x := float(t.get("x", 0.0))
	var y := float(t.get("y", 0.0))
	var z := float(t.get("z", 0.0))
	mesh_instance.position = Vector3(x, y, z)
	
	# Rotation and Scale also use dict access
	mesh_instance.rotation = Vector3(
		float(t.get("rx", 0.0)),
		float(t.get("ry", 0.0)),
		float(t.get("rz", 0.0))
	)
	mesh_instance.scale = Vector3(
		float(t.get("sx", 1.0)),
		float(t.get("sy", 1.0)),
		float(t.get("sz", 1.0))
	)

	# 3. Color from color dict
	var col: Dictionary = entity_data.get("color", {})
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(
		float(col.get("r", 1.0)),
		float(col.get("g", 1.0)),
		float(col.get("b", 1.0))
	)
	mesh_instance.material_override = mat

	# 4. Name and Metadata
	mesh_instance.name = entity_data.get("entity_id", entity_data.get("zw_concept", "entity"))
	mesh_instance.set_meta("zw_concept", entity_data.get("zw_concept", "unknown"))
	mesh_instance.set_meta("entity_id", entity_data.get("entity_id", ""))
	
	add_child(mesh_instance)
	print("Spawned: ", entity_data.get("zw_concept", "unknown"), " at ", mesh_instance.position)
	return mesh_instance

func submit_command(command: Dictionary) -> void:
	"""Placeholder for future live command support"""
	print("[EngAInBridge] submit_command called: ", command)
	# command_result.emit({"accepted": false, "reason": "Live bridge not active"})

func send_command(command_input: Variant) -> void:
	"""Alias for submit_command to match user interaction patterns"""
	if command_input is Dictionary:
		submit_command(command_input)
	else:
		# Handle string commands by wrapping them
		submit_command({"type": "raw_command", "command": str(command_input)})

func get_entities_by_concept(concept: String) -> Array:
	var results = []
	for child in get_children():
		if child.has_meta("zw_concept") and child.get_meta("zw_concept") == concept:
			results.append(child)
	return results

func get_scene_statistics() -> Dictionary:
	return {
		"total_entities": get_child_count(),
		"data_count": current_scene_entities.size()
	}

func _clear_scene() -> void:
	for child in get_children():
		child.queue_free()
