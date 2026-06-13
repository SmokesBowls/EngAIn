# sim_client_file_test.gd
# Simplified File-Based Godot Client for Testing
#
# This version reads snapshots from a file instead of managing subprocess.
# Use this to validate rendering logic before implementing full IPC.
#
# Setup:
# 1. Terminal: python3 sim_runtime_file_test.py
# 2. Godot: Run this scene
# 3. Watch entities update in real-time!

extends Node3D

# File paths
const SNAPSHOT_FILE = "/tmp/engain_snapshot.json"
const COMMAND_FILE = "/tmp/engain_command.json"

# Entity rendering
var entity_nodes: Dictionary = {}  # entity_id -> Node3D

# Update rate
@export var update_rate: float = 60.0  # Updates per second
var update_timer: float = 0.0

func _ready():
	print("============================================================")
	print("ENGAIN FILE-BASED TEST CLIENT")
	print("============================================================")
	print("\nMake sure Python runtime is running:")
	print("  cd ~/Downloads/EngAIn/zonengine4d/zon4d/sim")
	print("  python3 sim_runtime_file_test.py")
	print("\nControls:")
	print("  SPACE - Enemy attacks Guard (25 damage)")
	print("  ENTER - Guard attacks Enemy (15 damage)")
	print("  1 - Enemy heavy attack (80 damage)")
	print("  2 - Guard heavy attack (50 damage)")
	print("  Q - Quit")
	print("============================================================")

func _process(delta):
	# Update at fixed rate
	update_timer += delta
	var update_interval = 1.0 / update_rate
	
	if update_timer >= update_interval:
		update_timer = 0.0
		update_from_snapshot()

func update_from_snapshot():
	"""Read snapshot from file and update scene"""
	
	# Check if file exists
	if not FileAccess.file_exists(SNAPSHOT_FILE):
		return
	
	# Read snapshot
	var file = FileAccess.open(SNAPSHOT_FILE, FileAccess.READ)
	if not file:
		return
	
	var json_str = file.get_as_text()
	file.close()
	
	# Parse JSON
	var json = JSON.new()
	var error = json.parse(json_str)
	if error != OK:
		print("[ERROR] Failed to parse snapshot JSON")
		return
	
	var snapshot = json.get_data()
	
	# Render entities
	if snapshot.has("entities"):
		render_entities(snapshot["entities"])

func render_entities(entities: Dictionary):
	"""Update Godot scene to match simulation state"""
	
	for entity_id in entities:
		var entity_data = entities[entity_id]
		
		# Get or create node
		var node = get_or_create_entity_node(entity_id, entity_data)
		
		# Update position
		var pos = entity_data.get("pos", [0, 0, 0])
		node.position = Vector3(pos[0], pos[1], pos[2])
		
		# Update visual
		update_entity_visual(node, entity_data)
	
	# Remove entities that no longer exist
	for entity_id in entity_nodes.keys():
		if not entities.has(entity_id):
			print("[CLIENT] Removing entity: %s" % entity_id)
			entity_nodes[entity_id].queue_free()
			entity_nodes.erase(entity_id)

func get_or_create_entity_node(entity_id: String, entity_data: Dictionary) -> Node3D:
	"""Get existing entity node or create new one"""
	
	if entity_nodes.has(entity_id):
		return entity_nodes[entity_id]
	
	# Create new entity node
	var node = create_entity_cube(entity_id, entity_data)
	add_child(node)
	entity_nodes[entity_id] = node
	
	print("[CLIENT] Created entity: %s" % entity_id)
	return node

func create_entity_cube(entity_id: String, entity_data: Dictionary) -> Node3D:
	"""Create a visual representation of an entity"""
	
	var node = Node3D.new()
	node.name = entity_id
	
	# Add mesh
	var mesh_instance = MeshInstance3D.new()
	var box_mesh = BoxMesh.new()
	
	# Size based on radius
	var radius = entity_data.get("radius", 0.5)
	box_mesh.size = Vector3(radius * 2, radius * 2, radius * 2)
	mesh_instance.mesh = box_mesh
	
	# Material
	var material = StandardMaterial3D.new()
	material.albedo_color = get_entity_color(entity_id, entity_data)
	mesh_instance.set_surface_override_material(0, material)
	
	node.add_child(mesh_instance)
	
	# Add label showing entity info
	var label = Label3D.new()
	label.text = format_entity_label(entity_id, entity_data)
	label.position = Vector3(0, radius + 0.5, 0)
	label.font_size = 24
	label.outline_size = 4
	label.outline_modulate = Color.BLACK
	node.add_child(label)
	
	return node

func format_entity_label(entity_id: String, entity_data: Dictionary) -> String:
	"""Format entity label text"""
	var health = entity_data.get("health", 0)
	var max_health = entity_data.get("max_health", 100)
	var state = entity_data.get("state", "idle")
	
	return "%s\n%d/%d HP\n%s" % [entity_id, health, max_health, state]

func get_entity_color(entity_id: String, entity_data: Dictionary) -> Color:
	"""Determine entity color based on state"""
	
	# Dead = black
	if not entity_data.get("alive", true):
		return Color.BLACK
	
	# Health-based coloring
	var health = entity_data.get("health", 100)
	var max_health = entity_data.get("max_health", 100)
	var health_percent = health / max_health if max_health > 0 else 1.0
	
	if health_percent < 0.25:
		return Color.RED
	elif health_percent < 0.5:
		return Color.YELLOW
	
	# Entity type colors
	if entity_id == "player":
		return Color.BLUE
	elif entity_id == "guard":
		return Color.GREEN
	elif entity_id == "enemy":
		return Color.DARK_RED
	elif "wall" in entity_id:
		return Color.GRAY
	else:
		return Color.WHITE

func update_entity_visual(node: Node3D, entity_data: Dictionary):
	"""Update entity appearance based on state"""
	
	# Update mesh material
	for child in node.get_children():
		if child is MeshInstance3D:
			var material = child.get_surface_override_material(0)
			if material is StandardMaterial3D:
				material.albedo_color = get_entity_color(node.name, entity_data)
		
		# Update label
		if child is Label3D:
			child.text = format_entity_label(node.name, entity_data)

func send_command(command: Dictionary):
	"""Write command to file for Python to read"""
	var file = FileAccess.open(COMMAND_FILE, FileAccess.WRITE)
	if file:
		file.store_string(JSON.stringify(command))
		file.close()
		print("[CLIENT] Sent command: %s" % JSON.stringify(command))

func _input(event):
	"""Handle keyboard input"""
	
	if event is InputEventKey and event.pressed:
		
		# Enemy attacks Guard
		if event.keycode == KEY_SPACE:
			print("\n[INPUT] Enemy attacks Guard!")
			send_command({
				"type": "attack",
				"source": "enemy",
				"target": "guard",
				"damage": 25.0
			})
		
		# Guard attacks Enemy
		elif event.keycode == KEY_ENTER:
			print("\n[INPUT] Guard attacks Enemy!")
			send_command({
				"type": "attack",
				"source": "guard",
				"target": "enemy",
				"damage": 15.0
			})
		
		# Heavy attacks
		elif event.keycode == KEY_1:
			print("\n[INPUT] Enemy HEAVY attack!")
			send_command({
				"type": "attack",
				"source": "enemy",
				"target": "guard",
				"damage": 80.0
			})
		
		elif event.keycode == KEY_2:
			print("\n[INPUT] Guard HEAVY attack!")
			send_command({
				"type": "attack",
				"source": "guard",
				"target": "enemy",
				"damage": 50.0
			})
		
		# Quit
		elif event.keycode == KEY_Q:
			print("\n[CLIENT] Quitting...")
			get_tree().quit()

func _exit_tree():
	print("\n[CLIENT] Shutdown complete")
