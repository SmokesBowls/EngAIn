extends Node3D
class_name PlacementPacketRenderer

@export var packet_json_path: String = ""


func load_packets_from_file(path: String) -> bool:
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		push_error("[PlacementPacketRenderer] Failed to open packet file: %s" % path)
		return false
	var raw := f.get_as_text()
	f.close()

	var parsed: Variant = JSON.parse_string(raw)
	if typeof(parsed) != TYPE_ARRAY:
		push_error("[PlacementPacketRenderer] Root JSON must be an Array")
		return false

	apply_packets(parsed as Array)
	return true


func apply_packets(packets: Array) -> void:
	# Clear previous render nodes
	for child in get_children():
		remove_child(child)
		child.queue_free()

	for i in range(packets.size()):
		var p: Variant = packets[i]
		if typeof(p) != TYPE_DICTIONARY:
			push_error("[PlacementPacketRenderer] Packet %d is not a Dictionary" % i)
			continue
		var pd := p as Dictionary

		if not pd.has("render") or typeof(pd["render"]) != TYPE_DICTIONARY:
			push_error("[PlacementPacketRenderer] Packet %d missing render Dictionary" % i)
			continue

		var rd := pd["render"] as Dictionary
		if not rd.has("position") or not rd.has("rotation") or not rd.has("scale"):
			push_error("[PlacementPacketRenderer] Packet %d missing render.position/rotation/scale" % i)
			continue

		var pos_v: Variant = rd["position"]
		var rot_v: Variant = rd["rotation"]
		var scl_v: Variant = rd["scale"]
		if typeof(pos_v) != TYPE_ARRAY or typeof(rot_v) != TYPE_ARRAY or typeof(scl_v) != TYPE_ARRAY:
			push_error("[PlacementPacketRenderer] Packet %d transform values must be Arrays" % i)
			continue

		var pos := pos_v as Array
		var rot := rot_v as Array
		var scl := scl_v as Array
		if pos.size() != 3 or rot.size() != 3 or scl.size() != 3:
			push_error("[PlacementPacketRenderer] Packet %d transform arrays must have length 3" % i)
			continue

		var node := MeshInstance3D.new()
		node.mesh = BoxMesh.new()
		var tile_id := String(pd.get("tile_id", "")).strip_edges()
		node.name = tile_id if not tile_id.is_empty() else "packet_%d" % i
		node.position = Vector3(float(pos[0]), float(pos[1]), float(pos[2]))
		node.rotation = Vector3(float(rot[0]), float(rot[1]), float(rot[2]))
		node.scale = Vector3(float(scl[0]), float(scl[1]), float(scl[2]))
		add_child(node)


func snapshot_state() -> Array:
	var names: Array[String] = []
	for child in get_children():
		names.append(child.name)
	names.sort()

	var out: Array = []
	for n in names:
		var child := get_node_or_null(NodePath(n))
		if child == null:
			continue
		if child is Node3D:
			var n3d := child as Node3D
			out.append({
				"name": n3d.name,
				"position": [n3d.position.x, n3d.position.y, n3d.position.z],
				"rotation": [n3d.rotation.x, n3d.rotation.y, n3d.rotation.z],
				"scale": [n3d.scale.x, n3d.scale.y, n3d.scale.z],
			})
	return out
