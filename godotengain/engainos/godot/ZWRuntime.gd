extends Node

## ZWRuntime.gd - High-level API for the EngAIn Governed Reality OS.
## Acts as a facade over EngAInBridge for easy game integration.

var bridge: Node = null
var current_state: Dictionary = {}

signal state_changed(new_state: Dictionary)

func _ready() -> void:
	# Add to "zw_runtime" group for easy discovery
	add_to_group("zw_runtime")
	
	# Use the global EngAInBridge singleton
	bridge = get_node_or_null("/root/EngAInBridge")
	if not bridge:
		printerr("[ZWRuntime] Error: EngAInBridge singleton not found!")
		return
	
	# Connect signals
	bridge.state_updated.connect(_on_state_updated)
	bridge.command_result.connect(_on_command_result)
	bridge.bridge_error.connect(_on_bridge_error)
	
	# Initial scene load from contract
	# Note: Path should ideally be shared with EngAInBridge or passed in
	load_scene_from_json("res://game_scenes/test_scene.json")

func load_scene_from_json(path: String) -> void:
	var file = FileAccess.open(path, FileAccess.READ)
	if not file: return
	var json = JSON.new()
	json.parse(file.get_as_text())
	var data = json.get_data()
	
	# Spawn entities from contract
	for entity in data.get("entities", []):
		spawn_character(entity)

func spawn_character(entity: Dictionary):
	var mesh := MeshInstance3D.new()
	var box := BoxMesh.new()
	mesh.mesh = box

	# 1. Debug Material
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(0.7, 0.7, 0.9) # Neutral blue-grey
	mesh.material_override = mat

	# 2. Position
	var pos = entity.get("position", entity.get("transform", {"x": 0.0, "y": 0.0, "z": 0.0}))
	mesh.position = Vector3(float(pos.get("x", 0.0)), float(pos.get("y", 0.0)), float(pos.get("z", 0.0)))

	# 3. Name Label (Debug Only)
	var label := Label3D.new()
	label.text = entity.get("name", "Unknown")
	label.position = Vector3(0, 1.2, 0)
	mesh.add_child(label)

	# 4. Attach Sync Adapter
	var adapter = load("res://godot/Spatial3DAdapter.gd").new()
	adapter.entity_id = entity.get("id", "")
	mesh.add_child(adapter)

	get_tree().current_scene.call_deferred("add_child", mesh)

func _input(event: InputEvent) -> void:
	if event.is_action_pressed("reload_scene"):
		print("[DEBUG] Reloading scene from authoritative data")
		get_tree().reload_current_scene()
	
	# Press 'L' to load First Contact scene
	if event is InputEventKey and event.pressed and event.keycode == KEY_L:
		load_narrative_scene("03_Fist_contact")
	
	# Press 'C' to start Courier sequence
	if event is InputEventKey and event.pressed and event.keycode == KEY_C:
		start_courier_scene()

func send_command(command: Dictionary) -> void:
	bridge.submit_command(command)

func submit_attack(attacker_id: String, target_id: String, amount: float, authority_level: int = 1) -> void:
	var command = {
		"system": "combat",
		"issuer": "godot_player",
		"authority_level": authority_level,
		"events": [ {
			"source_id": attacker_id,
			"target_id": target_id,
			"amount": amount
		}]
	}
	send_command(command)

func get_entity_state(entity_id: String) -> Dictionary:
	# Check combat system
	var combat = current_state.get("combat", {})
	var entities = combat.get("entities", {})
	return entities.get(entity_id, {})

func _on_state_updated(snapshot: Dictionary) -> void:
	current_state = snapshot
	state_changed.emit(current_state)

func _on_command_result(result: Dictionary) -> void:
	if result.get("accepted"):
		print("[ZWRuntime] Command accepted: ", result.get("authority_reason"))
		# Snapshot is included in command result for responsiveness
		_on_state_updated(result.get("state"))
	else:
		print("[ZWRuntime] Command REJECTED: ", result.get("reason"))

func _on_bridge_error(message: String) -> void:
	printerr("[ZWRuntime] Bridge Error: ", message)


# ================================================================
func load_narrative_scene(scene_id: String) -> void:
	"""Load a narrative scene"""
	if not has_node("SceneSpawner"):
		var scene_spawner = Node.new()
		scene_spawner.name = "SceneSpawner"
		scene_spawner.set_script(load("res://godot/SceneSpawner.gd"))
		add_child(scene_spawner)
	
	var spawner = get_node("SceneSpawner")
	spawner.load_scene(scene_id)
	
	print("[ZWRuntime] Loading scene: ", scene_id)


# ================================================================


func start_courier_scene():
	"""Start the courier delivery sequence"""
	print("[ZWRuntime] Starting courier scene...")
	
	var courier: Node = get_node_or_null("CourierScene")
	
	# Create courier controller if not exists
	if not courier:
		courier = Node.new()
		courier.name = "CourierScene"
		courier.set_script(load("res://godot/CourierScene.gd"))
		add_child(courier)
	
	# Trigger the sequence
	courier.start_courier_sequence()
