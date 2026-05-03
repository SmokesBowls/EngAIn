class_name EntitySpawner
extends RefCounted
# ─────────────────────────────────────────────
#  EntitySpawner.gd
#  Pure factory — reads spawn_commands array,
#  returns Array[Node3D] of capsule placeholder nodes.
#  No network, no add_child, no editor logic.
# ─────────────────────────────────────────────

# ── Public API ─────────────────────────────────
func build(data: Dictionary) -> Array:
	var commands: Array = data.get("spawn_commands", [])
	var result: Array = []
	for cmd in commands:
		if cmd.get("type", "spawn_entity") == "spawn_entity":
			result.append(_build_node(cmd))
	return result


# ── Node builder ───────────────────────────────
func _build_node(cmd: Dictionary) -> Node3D:
	var id: String = cmd.get("id", "entity")
	var size: Vector2 = _parse_size(cmd.get("size_world", null))

	var anchor := Node3D.new()
	anchor.name = id
	anchor.position = _parse_position(cmd.get("position", null))

	# Body capsule
	var body := MeshInstance3D.new()
	body.name = "Body"
	var cap := CapsuleMesh.new()
	cap.radius = size.x * 0.25
	cap.height = size.y
	body.mesh = cap
	body.position = Vector3(0.0, size.y * 0.5, 0.0)

	var mat := StandardMaterial3D.new()
	mat.albedo_color = _color_from_string(id)
	body.material_override = mat
	anchor.add_child(body)

	# Name label
	var label := Label3D.new()
	label.name = "NameLabel"
	label.text = cmd.get("display_name", cmd.get("name", id))
	label.position = Vector3(0.0, size.y + 0.3, 0.0)
	label.pixel_size = 0.01
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	anchor.add_child(label)

	return anchor


# ── Helpers ────────────────────────────────────
func _parse_position(value) -> Vector3:
	if value is Vector3:
		return value
	if value is Array and value.size() >= 3:
		return Vector3(float(value[0]), float(value[1]), float(value[2]))
	if value is Dictionary:
		return Vector3(float(value.get("x", 0)), float(value.get("y", 0)), float(value.get("z", 0)))
	return Vector3.ZERO

func _parse_size(value) -> Vector2:
	if value is Vector2:
		return value
	if value is Array and value.size() >= 2:
		return Vector2(max(float(value[0]), 0.05), max(float(value[1]), 0.05))
	return Vector2(0.6, 1.8)

func _color_from_string(s: String) -> Color:
	var h: int = s.hash()
	var r := 0.35 + (float((h >> 16) & 0xFF) / 255.0) * 0.55
	var g := 0.35 + (float((h >> 8) & 0xFF) / 255.0) * 0.55
	var b := 0.35 + (float(h & 0xFF) / 255.0) * 0.55
	return Color(r, g, b, 1.0)
