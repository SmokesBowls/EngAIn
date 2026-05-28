@tool
extends Node3D

signal propose_tile_mutation(tile_id: String, new_terrain: String)

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
var render_policy: RenderPolicy = null
var _applied_texture_log: Dictionary = {}

var terrain_grid: Array = [
	["rock", "cliff", "sand", "shallow_water", "forest_edge"],
	["sand", "rock", "grass", "sand", "forest_edge"]
]

func set_render_policy(policy: RenderPolicy) -> void:
	## Set (or replace) the asset-source policy. Clears the atlas cache so the
	## next rebuild picks up the new source decisions.
	render_policy = policy
	atlas_cache.clear()
	print("[SemanticRenderer] Render policy set: default=%s" % policy.default_render_mode)


func _load_atlas_for(terrain: String) -> Dictionary:
	# 🛡️ UNIFIED TREATY VOCABULARY GATEWAY
	terrain = TrixelEnvironmentPlanner.resolve_tile_alias(terrain)
	if atlas_cache.has(terrain):
		return atlas_cache[terrain]

	var policy := render_policy if render_policy != null else RenderPolicy.default_policy()
	var resolved  := policy.resolve(terrain)
	var mode: String = resolved["render_mode"]
	print("[RenderPolicy] %s -> %s" % [terrain, mode])

	var data: Dictionary = {}
	match mode:
		RenderPolicy.MODE_ATLAS_2D:
			data = _atlas_static(terrain)
		RenderPolicy.MODE_RECIPE_3D:
			data = _atlas_recipe(terrain)
		RenderPolicy.MODE_CUSTOM_UPLOAD:
			data = _atlas_custom(terrain, resolved["asset_path"])
		_:  # composer_2_3d
			data = _atlas_composer(terrain)

	if not data.is_empty():
		atlas_cache[terrain] = data
	return data


# ── Atlas source helpers ──────────────────────────────────────────────────────

func _build_rects(meta: Dictionary) -> Dictionary:
	var tile_order: Array = meta.get("tile_order", [])
	var columns: int = int(meta.get("columns", 4))
	var tile_w: int  = int(meta.get("tile_width", 16))
	var tile_h: int  = int(meta.get("tile_height", 16))
	var rects: Dictionary = {}
	for i in range(tile_order.size()):
		rects[str(tile_order[i])] = Rect2i(
			(i % columns) * tile_w, (i / columns) * tile_h, tile_w, tile_h
		)
	return rects


func _read_atlas_meta(terrain: String) -> Dictionary:
	var meta_path := "%s/%s/atlas_meta.json" % [ATLAS_ROOT, terrain]
	if not FileAccess.file_exists(meta_path):
		push_warning("[SemanticRenderer] Missing atlas_meta for %s" % terrain)
		return {}
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(meta_path))
	if typeof(parsed) != TYPE_DICTIONARY:
		push_warning("[SemanticRenderer] Invalid atlas_meta JSON for %s" % terrain)
		return {}
	return parsed as Dictionary


func _atlas_static(terrain: String) -> Dictionary:
	var meta := _read_atlas_meta(terrain)
	if meta.is_empty():
		return {}
	var tex_path := "%s/%s/atlas.png" % [ATLAS_ROOT, terrain]
	if not FileAccess.file_exists(tex_path):
		push_warning("[SemanticRenderer] Missing atlas.png for %s" % terrain)
		return {}
	var texture: Texture2D = load(tex_path) as Texture2D
	if texture == null:
		return {}
	return {
		"texture": texture, "rects": _build_rects(meta),
		"tile_w": int(meta.get("tile_width", 16)), "tile_h": int(meta.get("tile_height", 16)),
	}


func _atlas_recipe(terrain: String) -> Dictionary:
	# Trixelcomposer output only.  Serve static atlas while async generation runs.
	var meta := _read_atlas_meta(terrain)
	if meta.is_empty():
		return {}

	var tc := get_node_or_null("/root/TrixelTileClient")
	if tc != null:
		var cached: ImageTexture = tc.get_cached_atlas(terrain)
		if cached != null:
			return {
				"texture": cached, "rects": _build_rects(meta),
				"tile_w": int(meta.get("tile_width", 16)), "tile_h": int(meta.get("tile_height", 16)),
			}
		tc.fetch_atlas(terrain)

	# Pending — return static so the cell still renders this frame
	return _atlas_static(terrain)


func _atlas_custom(terrain: String, asset_path: String) -> Dictionary:
	if asset_path.is_empty():
		push_warning("[SemanticRenderer] custom_upload for '%s' has no asset_path — falling back to atlas_2d" % terrain)
		return _atlas_static(terrain)

	var meta := _read_atlas_meta(terrain)
	if meta.is_empty():
		return {}

	var texture: Texture2D = null
	if asset_path.begins_with("res://"):
		texture = load(asset_path) as Texture2D
	else:
		var img := Image.load_from_file(asset_path)
		if img != null:
			texture = ImageTexture.create_from_image(img)

	if texture == null:
		push_warning("[SemanticRenderer] custom_upload failed to load '%s' — falling back to atlas_2d" % asset_path)
		return _atlas_static(terrain)

	return {
		"texture": texture, "rects": _build_rects(meta),
		"tile_w": int(meta.get("tile_width", 16)), "tile_h": int(meta.get("tile_height", 16)),
	}


func _atlas_composer(terrain: String) -> Dictionary:
	# composer_2_3d: static atlas as fallback; trixelcomposer overlaid async.
	var meta := _read_atlas_meta(terrain)
	if meta.is_empty():
		return {}

	var texture: Texture2D = null
	var tc := get_node_or_null("/root/TrixelTileClient")
	if tc != null:
		var cached: ImageTexture = tc.get_cached_atlas(terrain)
		if cached != null:
			texture = cached
			print("[RenderPolicy] composer_2_3d cache hit for '%s'" % terrain)
	else:
		push_warning("[RenderPolicy] composer_2_3d requested for '%s' but /root/TrixelTileClient is missing" % terrain)

	if texture == null:
		var tex_path := "%s/%s/atlas.png" % [ATLAS_ROOT, terrain]
		if not FileAccess.file_exists(tex_path):
			push_warning("[SemanticRenderer] Missing atlas.png for %s" % terrain)
			return {}
		texture = load(tex_path) as Texture2D
		if tc != null:
			print("[RenderPolicy] composer_2_3d -> TrixelTileClient.fetch_atlas('%s')" % terrain)
			tc.fetch_atlas(terrain)  # non-blocking; hot-swap on atlas_ready

	return {
		"texture": texture, "rects": _build_rects(meta),
		"tile_w": int(meta.get("tile_width", 16)), "tile_h": int(meta.get("tile_height", 16)),
	}


func _on_trixel_atlas_ready(terrain: String, _texture: ImageTexture) -> void:
	## TrixelTileClient emits this when a semantic atlas finishes generating.
	## Only matters for composer_2_3d and recipe_3d modes.
	if not atlas_cache.has(terrain):
		return
	var policy := render_policy if render_policy != null else RenderPolicy.default_policy()
	var mode: String = policy.resolve(terrain)["render_mode"]
	if mode in [RenderPolicy.MODE_RECIPE_3D, RenderPolicy.MODE_COMPOSER_2_3D]:
		atlas_cache.erase(terrain)
		print("[SemanticRenderer] Semantic atlas ready for '%s' (%s) — rebuilding" % [terrain, mode])
		rebuild_scene()

func _ready() -> void:
	if runtime_entities == null:
		runtime_entities = get_node_or_null("RuntimeEntities")

	if runtime_entities == null:
		push_warning("[SemanticRenderer] Missing RuntimeEntities child")
		return

	var tc := get_node_or_null("/root/TrixelTileClient")
	if tc != null:
		tc.atlas_ready.connect(_on_trixel_atlas_ready)

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
	_applied_texture_log.clear()

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
	# Perceptual visual approximation, not an authoritative elevation source.
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
	var applied_path := ""
	if texture != null and texture.has_meta("source_path"):
		applied_path = String(texture.get_meta("source_path"))
	elif texture != null:
		applied_path = String(texture.resource_path)
	var tex_path := applied_path if not applied_path.is_empty() else "<runtime_or_embedded>"
	var applied_key := "%s|%s" % [terrain, tex_path]
	if not _applied_texture_log.has(applied_key):
		print("[SemanticRenderer] APPLIED atlas terrain='%s' texture=%s" % [terrain, tex_path])
		_applied_texture_log[applied_key] = true
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
	var new_terrain := "sand"
	# Renderer only proposes. Authority layer (runtime/AP) commits per §11.3 envelope.
	emit_signal("propose_tile_mutation", tile_id, new_terrain)

func _resolve_clicked_tile_node(collider: Object) -> Node:
	if collider is Node:
		var node := collider as Node
		if node.has_meta("tile_id"):
			return node
		if node.get_parent() != null and node.get_parent().has_meta("tile_id"):
			return node.get_parent()
	return null
