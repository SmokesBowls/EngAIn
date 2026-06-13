# sim_client.gd
# Godot Thin Client for EngAIn Simulation
# 
# This script connects to the Python sim_runtime.py and renders its state.
# Python owns all logic, Godot is just I/O + visualization.

extends Node3D

# Path to Python runtime
@export var python_runtime_path: String = "res://sim_runtime.py"
@export var python_executable: String = "python3"

# Entity rendering
var entity_nodes: Dictionary = {}  # entity_id -> Node3D
var entity_scene = preload("res://entity_cube.tscn") if ResourceLoader.exists("res://entity_cube.tscn") else null

# Python process
var python_process: Thread
var python_mutex: Mutex
var python_running: bool = false

# Snapshot buffer
var latest_snapshot: Dictionary = {}
var snapshot_mutex: Mutex

# Player control
@export var player_entity_id: String = "player"
@export var move_speed: float = 5.0

func _ready():
	print("=" * 60)
	print("ENGAIN THIN CLIENT")
	print("=" * 60)
	
	snapshot_mutex = Mutex.new()
	python_mutex = Mutex.new()
	
	# Start Python runtime
	start_python_runtime()
	
	print("\nControls:")
	print("  WASD - Move player")
	print("  SPACE - Attack enemy")
	print("  Q - Quit")

func start_python_runtime():
	"""Launch Python sim_runtime.py as subprocess"""
	print("\n[CLIENT] Starting Python runtime...")
	
	# For now, we'll use a simple approach with OS.execute
	# In production, you'd use a proper subprocess with pipes
	
	# Create thread to run Python and handle I/O
	python_process = Thread.new()
	python_running = true
	python_process.start(_python_thread_func)
	
	print("[CLIENT] Python runtime started")

func _python_thread_func():
	"""
	Thread function that manages Python process I/O
	
	Note: This is a simplified version. In production, you'd use:
	- OS.create_process() with pipes
	- Proper stdin/stdout communication
	- Error handling
	"""
	
	# For this demo, we'll simulate the connection
	# In real implementation, you'd spawn the process and pipe I/O
	print("[THREAD] Python I/O thread started")
	
	while python_running:
		# Simulate receiving snapshots
		OS.delay_msec(16)  # ~60 FPS
		
		# In real implementation:
		# 1. Read JSON line from python stdout
		# 2. Parse snapshot
		# 3. Lock mutex and update latest_snapshot
	
	print("[THREAD] Python I/O thread stopped")

func send_command(command: Dictionary):
	"""Send JSON command to Python runtime"""
	# Lock mutex
	python_mutex.lock()
	
	# In real implementation:
	# Write JSON line to python stdin
	var json_str = JSON.stringify(command)
	# python_stdin.write(json_str + "\n")
	
	print("[CLIENT] Sent command: %s" % json_str)
	
	python_mutex.unlock()

func send_tick():
	"""Tell Python to advance one tick"""
	send_command({"type": "tick"})

func send_move(entity_id: String, target_pos: Vector3):
	"""Send move command"""
	send_command({
		"type": "move",
		"entity_id": entity_id,
		"data": {
			"target_pos": [target_pos.x, target_pos.y, target_pos.z],
			"speed": move_speed
		}
	})

func send_attack(attacker_id: String, target_id: String, damage: float = 25.0):
	"""Send attack command"""
	send_command({
		"type": "attack",
		"entity_id": attacker_id,
		"data": {
			"target_id": target_id,
			"damage": damage
		}
	})

func _process(_delta):
	# Send tick command
	send_tick()
	
	# Get latest snapshot
	snapshot_mutex.lock()
	var snapshot = latest_snapshot.duplicate()
	snapshot_mutex.unlock()
	
	# Render entities
	if snapshot.has("entities"):
		render_entities(snapshot["entities"])

func render_entities(entities: Dictionary):
	"""
	Update Godot scene to match simulation state
	
	For each entity:
	- Create cube if doesn't exist
	- Update position
	- Update color based on health/state
	"""
	
	for entity_id in entities:
		var entity_data = entities[entity_id]
		
		# Get or create node
		var node = get_or_create_entity_node(entity_id, entity_data)
		
		# Update position
		var pos = entity_data.get("pos", [0, 0, 0])
		node.position = Vector3(pos[0], pos[1], pos[2])
		
		# Update visual based on state
		update_entity_visual(node, entity_data)
	
	# Remove entities that no longer exist
	for entity_id in entity_nodes:
		if not entities.has(entity_id):
			entity_nodes[entity_id].queue_free()
			entity_nodes.erase(entity_id)

func get_or_create_entity_node(entity_id: String, entity_data: Dictionary) -> Node3D:
	"""Get existing entity node or create new one"""
	
	if entity_nodes.has(entity_id):
		return entity_nodes[entity_id]
	
	# Create new entity node
	var node: Node3D
	
	if entity_scene:
		node = entity_scene.instantiate()
	else:
		# Fallback: create simple cube
		node = create_simple_cube(entity_id, entity_data)
	
	add_child(node)
	entity_nodes[entity_id] = node
	
	print("[CLIENT] Created entity node: %s" % entity_id)
	return node

func create_simple_cube(entity_id: String, entity_data: Dictionary) -> Node3D:
	"""Create a simple cube mesh for entity visualization"""
	
	var node = Node3D.new()
	node.name = entity_id
	
	# Add mesh
	var mesh_instance = MeshInstance3D.new()
	var box_mesh = BoxMesh.new()
	box_mesh.size = Vector3(1, 1, 1)
	mesh_instance.mesh = box_mesh
	
	# Add material
	var material = StandardMaterial3D.new()
	material.albedo_color = get_entity_color(entity_id, entity_data)
	mesh_instance.set_surface_override_material(0, material)
	
	node.add_child(mesh_instance)
	
	# Add label (entity ID)
	var label = Label3D.new()
	label.text = entity_id
	label.position = Vector3(0, 1.5, 0)
	label.font_size = 32
	node.add_child(label)
	
	return node

func get_entity_color(entity_id: String, entity_data: Dictionary) -> Color:
	"""Determine entity color based on state"""
	
	# Dead = black
	if not entity_data.get("alive", true):
		return Color.BLACK
	
	# Low health = red
	var health = entity_data.get("health", 100)
	var max_health = entity_data.get("max_health", 100)
	var health_percent = health / max_health if max_health > 0 else 1.0
	
	if health_percent < 0.25:
		return Color.RED
	elif health_percent < 0.5:
		return Color.YELLOW
	
	# Default colors by entity type
	if entity_id == "player":
		return Color.BLUE
	elif entity_id == "guard":
		return Color.GREEN
	elif entity_id == "enemy":
		return Color.DARK_RED
	else:
		return Color.GRAY

func update_entity_visual(node: Node3D, entity_data: Dictionary):
	"""Update entity appearance based on state"""
	
	# Find mesh instance
	var mesh_instance = node.get_node_or_null("MeshInstance3D")
	if not mesh_instance:
		for child in node.get_children():
			if child is MeshInstance3D:
				mesh_instance = child
				break
	
	if mesh_instance:
		# Update material color
		var material = mesh_instance.get_surface_override_material(0)
		if material is StandardMaterial3D:
			material.albedo_color = get_entity_color(node.name, entity_data)
	
	# Update label if exists
	var label = node.get_node_or_null("Label3D")
	if label:
		var health = entity_data.get("health", 100)
		var max_health = entity_data.get("max_health", 100)
		var state = entity_data.get("state", "idle")
		label.text = "%s\n%d/%d HP\n%s" % [node.name, health, max_health, state]

func _input(event):
	"""Handle player input"""
	
	if event is InputEventKey and event.pressed:
		# Movement (WASD)
		var move_dir = Vector3.ZERO
		
		if event.keycode == KEY_W:
			move_dir.z = -1
		elif event.keycode == KEY_S:
			move_dir.z = 1
		elif event.keycode == KEY_A:
			move_dir.x = -1
		elif event.keycode == KEY_D:
			move_dir.x = 1
		
		if move_dir != Vector3.ZERO:
			# Get current player position
			var player_node = entity_nodes.get(player_entity_id)
			if player_node:
				var target_pos = player_node.position + move_dir * 2.0
				send_move(player_entity_id, target_pos)
		
		# Attack
		if event.keycode == KEY_SPACE:
			print("[CLIENT] Player attacks enemy")
			send_attack(player_entity_id, "enemy", 25.0)
		
		# Quit
		if event.keycode == KEY_Q:
			print("[CLIENT] Quit requested")
			send_command({"type": "quit"})
			python_running = false
			get_tree().quit()

func _exit_tree():
	"""Cleanup on exit"""
	print("\n[CLIENT] Shutting down...")
	
	# Stop Python process
	python_running = false
	send_command({"type": "quit"})
	
	if python_process and python_process.is_alive():
		python_process.wait_to_finish()
	
	print("[CLIENT] Shutdown complete")
