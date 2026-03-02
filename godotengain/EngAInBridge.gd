# EngAInBridge.gd - Godot Bridge for EngAIn
# 
# This is THE BRIDGE between Python EngAIn and Godot rendering.
#
# Flow:
# 1. Python: Story → ZON → Entity3D → RenderPlan (JSON)
# 2. Godot: JSON → spawn_entity() → 3D scene nodes
#
# Philosophy:
# - Placeholder mesh = game object (collision, logic)
# - Art skin = optional visual overlay
# - Python never imports Godot; Godot consumes Python output

extends Node3D

# ================================================================
# CONFIGURATION
# ================================================================

# Python bridge configuration
@export var python_executable: String = "python3"
@export var engain_core_path: String = "" # Auto-detect from project
@export var auto_load_on_ready: bool = false
@export var test_scene_id: String = "chapter1_opening"

# Placeholder materials (fallback colors)
var placeholder_materials := {}

# Scene container
@onready var entity_container: Node3D = self


# ================================================================
# INITIALIZATION
# ================================================================

func _ready():
	print("=== EngAIn Bridge Initialized ===")
	
	# Auto-detect engain_core_path if not set
	if engain_core_path.is_empty():
		var project_dir = ProjectSettings.globalize_path("res://")
		engain_core_path = project_dir.path_join("../engainos/core")
	
	print("EngAIn core path: ", engain_core_path)
	
	# Initialize placeholder materials
	_initialize_materials()
	
	if auto_load_on_ready:
		load_test_scene()


func _initialize_materials():
	"""Create colored materials for placeholder meshes"""
	placeholder_materials = {
		"red": _create_material(Color(0.8, 0.2, 0.2)),
		"green": _create_material(Color(0.2, 0.8, 0.2)),
		"blue": _create_material(Color(0.2, 0.2, 0.8)),
		"brown": _create_material(Color(0.6, 0.4, 0.2)),
		"gray": _create_material(Color(0.6, 0.6, 0.6)),
		"magenta": _create_material(Color(1.0, 0.0, 1.0)) # Error color
	}


func _create_material(color: Color) -> StandardMaterial3D:
	"""Create a simple colored material"""
	var mat = StandardMaterial3D.new()
	mat.albedo_color = color
	mat.metallic = 0.0
	mat.roughness = 0.8
	return mat


# ================================================================
# PYTHON BRIDGE
# ================================================================

func call_python_bridge(script_args: Array) -> Dictionary:
	"""
	Call Python EngAIn bridge script.
	
	Args:
		script_args: Arguments to pass to Python script
	
	Returns:
		Parsed JSON result from Python
	"""
	var python_script = engain_core_path.path_join("../tests/godot_bridge_test.py")
	
	var args = [python_script] + script_args
	
	var output = []
	var exit_code = OS.execute(python_executable, args, output, true, false)
	
	if exit_code != 0:
		push_error("Python bridge failed with code: " + str(exit_code))
		return {}
	
	# Parse JSON output
	var json_text = output[0] if output.size() > 0 else "{}"
	var json = JSON.new()
	var parse_result = json.parse(json_text)
	
	if parse_result != OK:
		push_error("Failed to parse JSON from Python: " + json_text)
		return {}
	
	return json.data


func load_zon_scene(scene_id: String) -> Array:
	"""
	Load ZON scene from Python and convert to Entity3D list.
	
	Args:
		scene_id: Scene identifier (e.g., "chapter1_opening")
	
	Returns:
		Array of entity dictionaries with RenderPlan data
	"""
	var result = call_python_bridge(["--scene", scene_id])
	
	if result.has("entities"):
		return result["entities"]
	
	return []


# ================================================================
# ENTITY SPAWNING
# ================================================================

func spawn_entity(entity_data: Dictionary) -> Node3D:
	"""
	Spawn a single entity from RenderPlan data.
	
	Args:
		entity_data: Dictionary with keys:
			- placeholder_mesh: "cube", "capsule", "cylinder", etc.
			- transform: {position, rotation, scale}
			- color: {r, g, b}
			- zw_concept: Semantic identity
			- entity_id: Unique identifier
	
	Returns:
		The spawned Node3D
	"""
	# Extract data
	var mesh_type = entity_data.get("placeholder_mesh", "cube")
	var transform_data = entity_data.get("transform", {})
	var color_data = entity_data.get("color", {"r": 1.0, "g": 0.0, "b": 1.0})
	var zw_concept = entity_data.get("zw_concept", "unknown")
	var entity_id = entity_data.get("entity_id", "entity_" + str(randi()))
	
	# Create placeholder mesh
	var mesh_node = _create_placeholder_mesh(mesh_type)
	mesh_node.name = entity_id
	
	# Set transform
	_apply_transform(mesh_node, transform_data)
	
	# Apply color
	var color = Color(color_data.r, color_data.g, color_data.b)
	_apply_color(mesh_node, color)
	
	# Add metadata
	mesh_node.set_meta("zw_concept", zw_concept)
	mesh_node.set_meta("entity_id", entity_id)
	
	# Apply semantic visual effects (Chaos integration)
	var semantic_data = entity_data.get("semantic_data", {})
	_apply_semantic_effects(mesh_node, semantic_data)
	
	# Add collision (all entities are solid by default)
	_add_collision(mesh_node, mesh_type)
	
	# Add to scene
	entity_container.add_child(mesh_node)
	
	print("Spawned: ", zw_concept, " (", mesh_type, ") at ", mesh_node.position)
	
	return mesh_node


func _apply_semantic_effects(mesh_instance: MeshInstance3D, semantic_data: Dictionary):
	"""
	Apply visual effects based on narrative semantics (emotions, ambiguity, Vrel).
	Implements the 'Living Aurora' effect and emotional shifts.
	"""
	if semantic_data.is_empty():
		return
	
	var mat = mesh_instance.material_override
	if not mat is StandardMaterial3D:
		return
	
	# 1. Enable Emission for bioluminescence
	mat.emission_enabled = true
	var base_emission = mat.albedo_color * 0.5
	mat.emission = base_emission
	
	# 2. Extract Emotions
	var emotions = semantic_data.get("emotion", [])
	for emo in emotions:
		var label = emo.get("label", "")
		var conf = emo.get("confidence", 0.0)
		
		if conf > 0.6:
			match label:
				"fear":
					# Pulse sickly yellow/green
					mat.emission = Color(0.8, 0.8, 0.2) * conf
					_add_pulse_effect(mesh_instance, 0.5, 2.0)
				"triumph":
					# Maximize intense blue/white
					mat.emission = Color(0.2, 0.6, 1.0) * (1.0 + conf)
					mat.emission_energy_multiplier = 2.0
				"wonder":
					# Purple aurora shift
					mat.albedo_color = mat.albedo_color.lerp(Color(0.5, 0.0, 0.8), conf)
					mat.emission = Color(0.6, 0.2, 0.9)
	
	# 3. Handle Visual Hints
	var visuals = semantic_data.get("visuals", [])
	for vis in visuals:
		var effect = vis.get("effect", "")
		var conf = vis.get("confidence", 0.0)
		
		match effect:
			"aurora_shimmer":
				# Purple/Teal aurora effect
				mat.albedo_color = mat.albedo_color.lerp(Color(0.4, 0.1, 0.9), conf)
				mat.emission = Color(0.2, 0.8, 1.0) * conf
				mat.emission_energy_multiplier = 1.5
				_add_shimmer_effect(mesh_instance, conf)
			"glow":
				mat.emission = mat.albedo_color * 2.0 * conf
				mat.emission_energy_multiplier = 2.0
			"pulse":
				_add_pulse_effect(mesh_instance, 0.8, 3.0)

	# 4. Handle Ambiguity
	var ambiguity = semantic_data.get("ambiguity", 0.0)
	if ambiguity > 0.5:
		# Use transparency/shimmer for ambiguous entities
		mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		mat.albedo_color.a = 1.0 - (ambiguity * 0.5)
		_add_shimmer_effect(mesh_instance, ambiguity)


func _add_pulse_effect(node: Node, intensity: float, speed: float):
	# Minimal implementation: could use a Tween or a script
	var script = GDScript.new()
	script.source_code = "extends Node\nvar time = 0.0\nvar parent_mat\nfunc _process(delta):\n\ttime += delta * " + str(speed) + "\n\tvar emission = parent_mat.emission\n\tparent_mat.emission_energy_multiplier = 1.0 + sin(time) * " + str(intensity)
	var pulse_node = Node.new()
	pulse_node.set_script(script)
	pulse_node.name = \"PulseEffect\"
	node.add_child(pulse_node)
	pulse_node.parent_mat = node.material_override


func _add_shimmer_effect(node: Node, ambiguity: float):
	var script = GDScript.new()
	script.source_code = "extends Node\nvar time = 0.0\nvar parent_mat\nfunc _process(delta):\n\ttime += delta * 5.0\n\tparent_mat.albedo_color.a = 0.5 + sin(time) * 0.2"
	var shimmer_node = Node.new()
	shimmer_node.set_script(script)
	shimmer_node.name = \"ShimmerEffect\"
	node.add_child(shimmer_node)
	shimmer_node.parent_mat = node.material_override


func _create_placeholder_mesh(mesh_type: String) -> MeshInstance3D:
	"""Create a placeholder mesh of the specified type"""
	var mesh_instance = MeshInstance3D.new()
	
	match mesh_type:
		"cube":
			mesh_instance.mesh = BoxMesh.new()
		"capsule":
			mesh_instance.mesh = CapsuleMesh.new()
			mesh_instance.mesh.height = 1.8 # Human height
			mesh_instance.mesh.radius = 0.3
		"cylinder":
			mesh_instance.mesh = CylinderMesh.new()
		"sphere":
			mesh_instance.mesh = SphereMesh.new()
		"plane":
			mesh_instance.mesh = PlaneMesh.new()
		_:
			mesh_instance.mesh = BoxMesh.new() # Fallback
	
	return mesh_instance


func _apply_transform(node: Node3D, transform_data: Dictionary):
	"""Apply position, rotation, and scale to node"""
	var pos = transform_data.get("position", {"x": 0, "y": 0, "z": 0})
	var rot = transform_data.get("rotation", {"x": 0, "y": 0, "z": 0})
	var scl = transform_data.get("scale", {"x": 1, "y": 1, "z": 1})
	
	node.position = Vector3(pos.x, pos.y, pos.z)
	node.rotation = Vector3(rot.x, rot.y, rot.z)
	node.scale = Vector3(scl.x, scl.y, scl.z)


func _apply_color(mesh_instance: MeshInstance3D, color: Color):
	"""Apply colored material to mesh"""
	var mat = StandardMaterial3D.new()
	mat.albedo_color = color
	mat.metallic = 0.0
	mat.roughness = 0.8
	mesh_instance.material_override = mat


func _add_collision(mesh_node: MeshInstance3D, mesh_type: String):
	"""Add collision shape to mesh"""
	var static_body = StaticBody3D.new()
	var collision_shape = CollisionShape3D.new()
	
	match mesh_type:
		"cube":
			var shape = BoxShape3D.new()
			shape.size = Vector3(1, 1, 1)
			collision_shape.shape = shape
		"capsule":
			var shape = CapsuleShape3D.new()
			shape.height = 1.8
			shape.radius = 0.3
			collision_shape.shape = shape
		"cylinder":
			var shape = CylinderShape3D.new()
			shape.height = 2.0
			shape.radius = 0.5
			collision_shape.shape = shape
		"sphere":
			var shape = SphereShape3D.new()
			shape.radius = 0.5
			collision_shape.shape = shape
		_:
			var shape = BoxShape3D.new()
			collision_shape.shape = shape
	
	static_body.add_child(collision_shape)
	mesh_node.add_child(static_body)


# ================================================================
# SCENE LOADING
# ================================================================

func load_scene(scene_id: String) -> int:
	"""
	Load a complete scene from ZON.
	
	Args:
		scene_id: Scene identifier
	
	Returns:
		Number of entities spawned
	"""
	print("=== Loading scene: ", scene_id, " ===")
	
	# Clear existing entities
	clear_scene()
	
	# Load from Python
	var entities = load_zon_scene(scene_id)
	
	if entities.is_empty():
		push_warning("No entities loaded for scene: " + scene_id)
		return 0
	
	# Spawn each entity
	var count = 0
	for entity_data in entities:
		spawn_entity(entity_data)
		count += 1
	
	print("=== Scene loaded: ", count, " entities ===")
	return count


func clear_scene():
	"""Remove all spawned entities"""
	for child in entity_container.get_children():
		child.queue_free()


func load_test_scene():
	"""Load the configured test scene"""
	load_scene(test_scene_id)


# ================================================================
# UTILITY
# ================================================================

func get_entity_by_id(entity_id: String) -> Node3D:
	"""Find entity by ID"""
	for child in entity_container.get_children():
		if child.get_meta("entity_id", "") == entity_id:
			return child
	return null


func get_entities_by_concept(zw_concept: String) -> Array:
	"""Find all entities of a given concept"""
	var results = []
	for child in entity_container.get_children():
		if child.get_meta("zw_concept", "") == zw_concept:
			results.append(child)
	return results


func get_scene_statistics() -> Dictionary:
	"""Get statistics about current scene"""
	var stats = {
		"total_entities": 0,
		"by_concept": {},
		"by_mesh_type": {}
	}
	
	for child in entity_container.get_children():
		stats.total_entities += 1
		
		var concept = child.get_meta("zw_concept", "unknown")
		if not stats.by_concept.has(concept):
			stats.by_concept[concept] = 0
		stats.by_concept[concept] += 1
		
		if child is MeshInstance3D:
			var mesh_type = _get_mesh_type_name(child.mesh)
			if not stats.by_mesh_type.has(mesh_type):
				stats.by_mesh_type[mesh_type] = 0
			stats.by_mesh_type[mesh_type] += 1
	
	return stats


func _get_mesh_type_name(mesh: Mesh) -> String:
	"""Get human-readable mesh type name"""
	if mesh is BoxMesh:
		return "cube"
	elif mesh is CapsuleMesh:
		return "capsule"
	elif mesh is CylinderMesh:
		return "cylinder"
	elif mesh is SphereMesh:
		return "sphere"
	elif mesh is PlaneMesh:
		return "plane"
	else:
		return "unknown"
