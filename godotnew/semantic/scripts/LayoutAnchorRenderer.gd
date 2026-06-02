extends Node3D
class_name LayoutAnchorRenderer

@export var layout_json_path: String = "/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/trixelmap/out_book/resolved_layout.json"
@export var cell_size: float = 1.5
@export var marker_height: float = 0.35
@export var y_offset: float = 0.35

var _materials: Dictionary = {}


func _ready() -> void:
	load_layout_from_file(layout_json_path)


func load_layout_from_file(path: String) -> bool:
	clear_markers()

	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		push_error("[LayoutAnchorRenderer] Failed to open layout file: %s" % path)
		return false

	var raw := file.get_as_text()
	file.close()

	var parsed: Variant = JSON.parse_string(raw)
	if typeof(parsed) != TYPE_DICTIONARY:
		push_error("[LayoutAnchorRenderer] Root JSON must be a Dictionary")
		return false

	var root := parsed as Dictionary
	if not root.has("regions") or typeof(root["regions"]) != TYPE_DICTIONARY:
		push_error("[LayoutAnchorRenderer] Missing regions Dictionary")
		return false

	_render_regions(root["regions"] as Dictionary)
	print("[LayoutAnchorRenderer] Rendered %d layout anchors from %s" % [(root["regions"] as Dictionary).size(), path])
	return true


func clear_markers() -> void:
	for child in get_children():
		remove_child(child)
		child.queue_free()


func _render_regions(regions: Dictionary) -> void:
	for region_id in regions.keys():
		var region_v: Variant = regions[region_id]
		if typeof(region_v) != TYPE_DICTIONARY:
			push_warning("[LayoutAnchorRenderer] Region %s is not a Dictionary" % String(region_id))
			continue

		var region := region_v as Dictionary
		if not region.has("bounds") or typeof(region["bounds"]) != TYPE_DICTIONARY:
			push_warning("[LayoutAnchorRenderer] Region %s missing bounds" % String(region_id))
			continue

		var bounds := region["bounds"] as Dictionary
		var x_min := float(bounds.get("x_min", 0.0))
		var x_max := float(bounds.get("x_max", x_min + 1.0))
		var y_min := float(bounds.get("y_min", 0.0))
		var y_max := float(bounds.get("y_max", y_min + 1.0))

		var width_cells: float = maxf(1.0, x_max - x_min)
		var depth_cells: float = maxf(1.0, y_max - y_min)

		var cx: float = x_min + width_cells * 0.5
		var cy: float = y_min + depth_cells * 0.5

		var marker := MeshInstance3D.new()
		marker.name = "%s_anchor" % String(region_id)
		marker.mesh = BoxMesh.new()
		marker.position = Vector3(cx * cell_size, y_offset, cy * cell_size)
		marker.scale = Vector3(width_cells * cell_size, marker_height, depth_cells * cell_size)
		marker.material_override = _material_for_region(region)
		marker.set_meta("region_id", String(region_id))
		marker.set_meta("type", String(region.get("type", "")))
		marker.set_meta("terrain_class", String(region.get("terrain_class", "")))
		add_child(marker)

		var label := Label3D.new()
		label.name = "%s_label" % String(region_id)
		label.text = _display_name(String(region_id))
		label.position = Vector3(cx * cell_size, y_offset + 0.8, cy * cell_size)
		label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		label.font_size = 32
		add_child(label)


func _material_for_region(region: Dictionary) -> StandardMaterial3D:
	var terrain_class := String(region.get("terrain_class", "unknown"))
	if _materials.has(terrain_class):
		return _materials[terrain_class]

	var mat := StandardMaterial3D.new()
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.albedo_color = _color_for_terrain_class(terrain_class)
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_materials[terrain_class] = mat
	return mat


func _color_for_terrain_class(terrain_class: String) -> Color:
	match terrain_class:
		"landmark":
			return Color(0.7, 0.45, 1.0, 0.45)
		"fertile_valley":
			return Color(0.25, 0.9, 0.35, 0.45)
		"rocky_hills":
			return Color(0.75, 0.65, 0.45, 0.45)
		_:
			return Color(1.0, 1.0, 1.0, 0.35)


func _display_name(region_id: String) -> String:
	var parts := region_id.split("_")
	for i in range(parts.size()):
		parts[i] = parts[i].capitalize()
	return " ".join(parts)
