extends Node3D

@onready var label: Label3D = $Name

func apply_entity_data(eid: String, data: Dictionary) -> void:
	label.text = String(data.get("name", eid))

	var pos_v: Variant = data.get("position_godot", null)
	if typeof(pos_v) != TYPE_DICTIONARY:
		pos_v = data.get("position", {})

	if typeof(pos_v) == TYPE_DICTIONARY:
		var pos: Dictionary = pos_v as Dictionary

		var x: float = float(pos.get("x", 0.0))
		var y: float = float(pos.get("y", 0.0))
		var z: float = float(pos.get("z", 0.0))

		# TEMP DEBUG REMAP INTO THE 5x5 TEST WORLD
		global_position = Vector3(
			clamp(x + 3.5, 0.5, 5.8),
			y + 1.0,
			clamp(abs(z) + 0.5, 0.5, 5.8)
		)

		print("[SemanticActor] ", eid, " raw=", Vector3(x, y, z), " final=", global_position)
	else:
		global_position = Vector3(3.0, 1.0, 3.0)
		print("[SemanticActor] ", eid, " no usable position, using fallback ", global_position)
