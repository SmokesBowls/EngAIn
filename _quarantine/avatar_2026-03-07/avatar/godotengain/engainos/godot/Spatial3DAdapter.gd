extends Node3D

## Spatial3DAdapter.gd - Synchronizes Godot entities with the Governed Reality state.

@export var entity_id: String = ""
@export var update_health: bool = true
@export var update_transform: bool = true

var health_bar: ProgressBar = null

func _ready() -> void:
	# Connect to ZWRuntime if available
	var zw = get_tree().get_first_node_in_group("zw_runtime")
	if zw:
		zw.state_updated.connect(_on_state_changed)
	else:
		printerr("[Spatial3DAdapter] Error: ZWRuntime not found in tree.")

func _on_state_changed(state: Dictionary) -> void:
	if entity_id == "":
		return
		
	# 1. Update Transform (Spatial system)
	if update_transform:
		var spatial = state.get("spatial", {})
		var entities = spatial.get("entities", {})
		if entities.has(entity_id):
			var pos = entities[entity_id]
			# Map Python [x,y,z] to Godot Vector3
			# Note: Godot is Y-up, Python might be Z-up or Y-up depending on kernel.
			# For now assume direct mapping.
			global_position = Vector3(float(pos.get("x", 0.0)), float(pos.get("y", 0.0)), float(pos.get("z", 0.0)))
			
	# 2. Update Health (Combat system)
	if update_health:
		var combat = state.get("combat", {})
		var entities = combat.get("entities", {})
		if entities.has(entity_id):
			var data = entities[entity_id]
			var health = data.get("health", 0.0)
			var max_health = data.get("max_health", 100.0)
			
			# If we have a health bar, update it
			if health_bar:
				health_bar.max_value = max_health
				health_bar.value = health
				
			# Visual feedback on death
			if health <= 0:
				_on_death()

func _on_death() -> void:
	# Handle visual death sequence
	pass
