extends Node
## SceneSpawner - Loads narrative scenes and spawns entities

signal scene_loaded(scene_id: String)
signal entity_spawned(entity_id: String)

func load_scene(scene_id: String) -> void:
	"""Load a narrative scene from Python bridge"""
	print("[SceneSpawner] Loading scene: ", scene_id)
	
	var http = HTTPRequest.new()
	add_child(http)
	http.request_completed.connect(_on_scene_loaded)
	
	var url = "http://127.0.0.1:8765/load_scene?scene_id=" + scene_id
	print("[SceneSpawner] Requesting URL: ", url)
	
	var error = http.request(url)
	
	if error != OK:
		push_error("[SceneSpawner] HTTP request failed with error: " + str(error))
		http.queue_free()
		return
	
	print("[SceneSpawner] HTTP request sent successfully")

func _on_scene_loaded(_result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	"""Handle HTTP response"""
	print("[SceneSpawner] Callback triggered")
	print("[SceneSpawner] Response code: ", response_code)
	print("[SceneSpawner] Body size: ", body.size(), " bytes")
	
	if response_code != 200:
		push_error("[SceneSpawner] HTTP error: " + str(response_code))
		return
	
	if body.size() == 0:
		push_error("[SceneSpawner] Empty response body")
		return
	
	var json_text = body.get_string_from_utf8()
	print("[SceneSpawner] JSON text length: ", json_text.length())
	
	var json = JSON.new()
	var parse_error = json.parse(json_text)
	
	if parse_error != OK:
		push_error("[SceneSpawner] JSON parse error")
		return
	
	var scene_data = json.get_data()
	
	if scene_data.get("status") != "success":
		push_error("[SceneSpawner] Server error: " + str(scene_data.get("message", "Unknown")))
		return
	
	clear_scene()
	
	var data = scene_data.get("data", {})
	var spawn_commands = data.get("spawn_commands", [])
	print("[SceneSpawner] About to spawn ", spawn_commands.size(), " entities")
	
	for spawn_cmd in spawn_commands:
		spawn_entity(spawn_cmd)
	
	var metadata = data.get("metadata", {})
	print("[SceneSpawner] Scene loaded: ", metadata.get("scene_id", "unknown"))
	scene_loaded.emit(metadata.get("scene_id", "unknown"))

func spawn_entity(spawn_data: Dictionary) -> Node3D:
	"""Spawn a single entity as a simple cube"""
	
	var entity_name = spawn_data.get("name", spawn_data.get("entity_id", "Unknown"))
	print("[SceneSpawner] Creating entity: ", entity_name)
	
	var entity = MeshInstance3D.new()
	var mesh = BoxMesh.new()
	mesh.size = Vector3(1, 2, 1)
	entity.mesh = mesh
	
	var material = StandardMaterial3D.new()
	material.albedo_color = Color(0.3, 0.5, 0.8)
	entity.set_surface_override_material(0, material)
	
	entity.name = entity_name # Use NAME not ID for visibility
	
	# Robust Position Handling
	var transform_data = spawn_data.get("transform", spawn_data.get("position", {"x": 0.0, "y": 0.0, "z": 0.0}))
	if transform_data is Array:
		entity.position = Vector3(
			float(transform_data[0]),
			float(transform_data[1]) + 1.0,
			float(transform_data[2])
		)
	else:
		entity.position = Vector3(
			float(transform_data.get("x", 0.0)),
			float(transform_data.get("y", 0.0)) + 1.0,
			float(transform_data.get("z", 0.0))
		)
	
	var label = Label3D.new()
	label.text = entity_name
	label.position = Vector3(0, 2.5, 0)
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	label.font_size = 32
	entity.add_child(label)
	
	# Add wandering behavior
	var wanderer = Node.new()
	wanderer.name = "Wanderer"
	wanderer.set_script(load("res://godot/CharacterWanderer.gd"))
	# Vary personality per character
	wanderer.set("speed", randf_range(1.5, 3.0))
	wanderer.set("wander_radius", randf_range(6.0, 12.0))
	wanderer.set("idle_time_min", randf_range(1.0, 3.0))
	wanderer.set("idle_time_max", randf_range(3.0, 6.0))
	entity.add_child(wanderer)
	
	# FIX: Add to current scene's root, not by hardcoded name
	var scene_root = get_tree().current_scene
	if scene_root:
		scene_root.add_child(entity)
		print("[SceneSpawner] ✓ Spawned: ", entity_name, " at ", entity.position)
		entity_spawned.emit(spawn_data.get("entity_id", spawn_data.get("id", "")))
	else:
		push_error("[SceneSpawner] ✗ Could not find scene root!")
		entity.queue_free()
		return null
	
	return entity

func clear_scene() -> void:
	"""Remove all spawned entities"""
	var scene_root = get_tree().current_scene
	if not scene_root:
		return
	
	var removed = 0
	for child in scene_root.get_children():
		if child is MeshInstance3D:
			child.queue_free()
			removed += 1
	
	print("[SceneSpawner] Cleared ", removed, " entities")
