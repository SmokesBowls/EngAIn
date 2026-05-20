@tool
extends Node3D

@export var preview_in_editor: bool = true
@export var rebuild_now: bool = false:
	set(value):
		rebuild_now = false
		if value:
			rebuild_scene()
@export var enable_tile_clicks: bool = true
@export var click_ray_length: float = 1000.0
@export var runtime_rebuild_key: Key = KEY_R

const CELL_SIZE: float = 1.5
const ATLAS_ROOT := "res://trixel/trixelassets"

@onready var runtime_entities: Node3D = get_node_or_null("RuntimeEntities")

var atlas_cache: Dictionary = {}
var tile_index: Dictionary = {}

var terrain_grid: Array = [
	["deep_water", "deep_water", "deep_water", "deep_water", "deep_water"],
	["shallow_water", "shallow_water", "shallow_water", "shallow_water", "shallow_water"],
	["shoreline", "shoreline", "shoreline", "shoreline", "shoreline"],
	["sand", "sand", "sand", "sand", "sand"],
	["grass", "grass", "grass", "grass", "grass"]
]

func _load_atlas_for(terrain: String) -> Dictionary:
	if atlas_cache.has(terrain):
		return atlas_cache[terrain]

	var dir_path := "%s/%s" % [ATLAS_ROOT, terrain]
	var meta_path := "%s/atlas_meta.json" % dir_path
	var tex_path := "%s/atlas.png" % dir_path

	if not FileAccess.file_exists(meta_path):
		push_warning("Missing atlas_meta for %s" % terrain)
		return {}
	if not FileAccess.file_exists(tex_path):
		push_warning("Missing atlas texture for %s" % terrain)
		return {}

	var meta_raw := FileAccess.get_file_as_string(meta_path)
	var atlas_meta: Variant = JSON.parse_string(meta_raw)
	if typeof(atlas_meta) != TYPE_DICTIONARY:
		push_warning("Invalid atlas_meta for %s" % terrain)
		return {}

	var texture: Texture2D = load(tex_path) as Texture2D
	if texture == null:
		push_warning("Failed to load texture for %s" % terrain)
		return {}

	var tile_order: Array = (atlas_meta as Dictionary).get("tile_order", [])
	var columns: int = int((atlas_meta as Dictionary).get("columns", 4))
	var tile_w: int = int((atlas_meta as Dictionary).get("tile_width", 16))
	var tile_h: int = int((atlas_meta as Dictionary).get("tile_height", 16))

	var rects: Dictionary = {}
	for i in range(tile_order.size()):
		var role: String = str(tile_order[i])
		var col := i % columns
		var row := i / columns
		rects[role] = Rect2i(col * tile_w, row * tile_h, tile_w, tile_h)

	var data := {
		"texture": texture,
		"rects": rects,
		"tile_w": tile_w,
		"tile_h": tile_h
	}

	atlas_cache[terrain] = data
	return data

func _ready() -> void:
	if runtime_entities == null:
		runtime_entities = get_node_or_null("RuntimeEntities")

	if runtime_entities == null:
		push_warning("[SemanticRenderer] Missing RuntimeEntities child")
		return

	if Engine.is_editor_hint():
		rebuild_scene()

func _unhandled_key_input(event: InputEvent) -> void:
	if Engine.is_editor_hint():
		return

	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == runtime_rebuild_key:
			print("[SemanticRenderer] Runtime rebuild requested")
			rebuild_scene()

func rebuild_scene() -> void:
	if runtime_entities == null:
		runtime_entities = get_node_or_null("RuntimeEntities")
	if runtime_entities == null:
		push_warning("[SemanticRenderer] Missing RuntimeEntities child")
		return

	tile_index.clear()

	await _clear_runtime_entities()
	_spawn_terrain_grid()

	if Engine.is_editor_hint():
		print("[SemanticRenderer] Editor scene rebuilt")
	else:
		print("[SemanticRenderer] Runtime scene rebuilt")

func _clear_runtime_entities() -> void:
	for child in runtime_entities.get_children():
		child.queue_free()

	if Engine.is_editor_hint():
		await get_tree().process_frame

func clear_scene() -> void:
	_clear_runtime_entities()
	tile_index.clear()

func _spawn_terrain_grid() -> void:
	for y in range(terrain_grid.size()):
		var row: Array = terrain_grid[y]
		for x in range(row.size()):
			var terrain: String = str(row[x])
			var role: String = TrixelRoleResolver.resolve_role(terrain_grid, x, y, terrain)
			var grid_width := float(row.size()) * CELL_SIZE
			var grid_depth := float(terrain_grid.size()) * CELL_SIZE

			var origin_x := -grid_width * 0.5
			var origin_z := -grid_depth * 0.5

			var pos := Vector3(
				origin_x + (x * CELL_SIZE),
				0.0,
				origin_z + (y * CELL_SIZE)
			)
			_spawn_terrain_cell(terrain, role, pos, x, y)

func _terrain_height(terrain: String) -> float:
	match terrain:
		"deep_water":
			return -0.4
		"shallow_water":
			return -0.2
		"shoreline":
			return 0.0
		"sand":
			return 0.05
		"grass":
			return 0.15
		_:
			return 0.0

func _spawn_terrain_cell(terrain: String, role: String, pos: Vector3, gx: int, gy: int) -> void:
	var atlas := _load_atlas_for(terrain)
	if atlas.is_empty():
		return

	var texture: Texture2D = atlas["texture"]
	var rects: Dictionary = atlas["rects"]

	var region: Rect2i = rects.get(role, rects.get("center", Rect2i(0, 0, 16, 16)))

	var mesh := QuadMesh.new()
	mesh.size = Vector2(CELL_SIZE - 0.08, CELL_SIZE - 0.08)

	var node := StaticBody3D.new()
	node.name = "%s_%s" % [terrain, role]

	var visual := MeshInstance3D.new()
	visual.mesh = mesh
	visual.rotation_degrees = Vector3(-90, 0, 0)

	var gap := 0.08
	var h := _terrain_height(terrain)

	node.position = Vector3(
		pos.x + float(gx) * gap,
		h,
		pos.z + float(gy) * gap
	)

	var tile_id := "%d_%d" % [gx, gy]

	node.name = "%s_%d_%d_%s" % [terrain, gx, gy, role]
	node.set_meta("tile_id", tile_id)
	node.set_meta("gx", gx)
	node.set_meta("gy", gy)
	node.set_meta("terrain", terrain)
	node.set_meta("role", role)

	var mat := StandardMaterial3D.new()
	mat.albedo_texture = texture
	mat.uv1_scale = Vector3(
		float(region.size.x) / texture.get_width(),
		float(region.size.y) / texture.get_height(),
		1.0
	)

	mat.uv1_offset = Vector3(
		float(region.position.x) / texture.get_width(),
		float(region.position.y) / texture.get_height(),
		0.0
	)

	mat.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED

	visual.material_override = mat
	node.add_child(visual)

	var collision := CollisionShape3D.new()
	var shape := BoxShape3D.new()
	shape.size = Vector3(CELL_SIZE - 0.08, 0.05, CELL_SIZE - 0.08)
	collision.shape = shape
	collision.position = Vector3(0.0, 0.0, 0.0)
	node.add_child(collision)

	runtime_entities.add_child(node)
	tile_index[tile_id] = node

	if Engine.is_editor_hint():
		node.owner = get_tree().edited_scene_root
		node.set_owner(get_tree().edited_scene_root)
		visual.owner = get_tree().edited_scene_root
		visual.set_owner(get_tree().edited_scene_root)
		collision.owner = get_tree().edited_scene_root
		collision.set_owner(get_tree().edited_scene_root)

func set_environment_layout(layout: Dictionary) -> void:
	var grid_v: Variant = layout.get("terrain_grid", [])
	if typeof(grid_v) != TYPE_ARRAY:
		push_warning("[SemanticRenderer] set_environment_layout missing terrain_grid Array")
		return

	terrain_grid = grid_v as Array
	print("[SemanticRenderer] Environment layout received (%d rows)" % terrain_grid.size())
	rebuild_scene()

func update_tile_from_event(tile_id: String, new_terrain: String) -> void:
	if not tile_index.has(tile_id):
		push_warning("[SemanticRenderer] Tile not found: %s" % tile_id)
		return

	var old_node_variant: Variant = tile_index[tile_id]
	if not (old_node_variant is StaticBody3D):
		push_warning("[SemanticRenderer] Indexed tile is not StaticBody3D: %s" % tile_id)
		return

	var old_node: StaticBody3D = old_node_variant as StaticBody3D
	var gx: int = int(old_node.get_meta("gx"))
	var gy: int = int(old_node.get_meta("gy"))

	terrain_grid[gy][gx] = new_terrain

	old_node.queue_free()
	tile_index.erase(tile_id)

	var role: String = TrixelRoleResolver.resolve_role(terrain_grid, gx, gy, new_terrain)
	var grid_width := float((terrain_grid[0] as Array).size()) * CELL_SIZE
	var grid_depth := float(terrain_grid.size()) * CELL_SIZE

	var origin_x := -grid_width * 0.5
	var origin_z := -grid_depth * 0.5

	var pos := Vector3(
		origin_x + (gx * CELL_SIZE),
		0.0,
		origin_z + (gy * CELL_SIZE)
	)
	_spawn_terrain_cell(new_terrain, role, pos, gx, gy)

	print("[SemanticRenderer] Updated tile %s -> %s" % [tile_id, new_terrain])

func _unhandled_input(event: InputEvent) -> void:
	if not enable_tile_clicks:
		return

	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		_handle_tile_click(event.position)

func _handle_tile_click(screen_pos: Vector2) -> void:
	var camera := get_viewport().get_camera_3d()
	if camera == null:
		push_warning("[SemanticRenderer] No Camera3D available for tile click")
		return

	var from := camera.project_ray_origin(screen_pos)
	var to := from + camera.project_ray_normal(screen_pos) * click_ray_length

	var query := PhysicsRayQueryParameters3D.create(from, to)
	query.collide_with_areas = false
	query.collide_with_bodies = true

	var space_state := get_world_3d().direct_space_state
	var result := space_state.intersect_ray(query)

	if result.is_empty():
		return

	var collider = result.get("collider", null)
	if collider == null:
		return

	var node := _resolve_clicked_tile_node(collider)
	if node == null:
		return

	if not node.has_meta("tile_id"):
		return

	var tile_id: String = str(node.get_meta("tile_id"))
	update_tile_from_event(tile_id, "sand")

func _resolve_clicked_tile_node(collider: Object) -> Node:
	if collider is Node:
		var node := collider as Node
		if node.has_meta("tile_id"):
			return node
		if node.get_parent() != null and node.get_parent().has_meta("tile_id"):
			return node.get_parent()
	return null
