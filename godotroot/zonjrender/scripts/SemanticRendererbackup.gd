@tool
extends Node3D

# ─────────────────────────────────────────────
#  SemanticRenderer.gd
#  Dual-mode: editor preview (Local) + runtime.
#  Editor:  sync HTTP fetch → undo/redo nodes → visible in Local
#  Runtime: SceneClient signal → RuntimeRoot
# ─────────────────────────────────────────────

const ASSET_ROOT       := "res://engain/tests/trixel/assets"
const SCENE_ID         := "03_Fist_contact"
const TILE_SIZE        := 1.0
const TERRAIN_Y        := 0.0
const TILE_PX          := 16
const FALLBACK_TERRAIN := "grass"

const TERRAIN_DRAW_ORDER := [
	"deep_water","shallow_water","shoreline","sand",
	"grass","forest_edge","pier","rock","cliff",
]

# ── Inspector controls ─────────────────────────
@export_file("*.json") var preview_json_path: String = ""

@export var refresh_preview: bool = false:
	set(v):
		refresh_preview = false
		if Engine.is_editor_hint():
			_editor_fetch_and_build()

@export var clear_preview: bool = false:
	set(v):
		clear_preview = false
		if Engine.is_editor_hint():
			_editor_clear_preview()

@export var entity_scene: PackedScene

# ── State ──────────────────────────────────────
var _atlases: Dictionary = {}
var _terrain_grid: Array = []
var _grid_w: int = 0
var _grid_h: int = 0
var _runtime_root: Node3D
var _preview_root: Node3D

# Editor-only — not declared as typed to avoid parse errors at runtime
var _editor_plugin = null
var _undo_redo = null


# ── Boot ──────────────────────────────────────
func _ready() -> void:
	_load_all_atlases()

	if Engine.is_editor_hint():
		_editor_plugin = EditorPlugin.new()
		_undo_redo = _editor_plugin.get_undo_redo()
		if preview_json_path != "":
			_editor_build()
		return

	# Runtime path
	if entity_scene == null:
		entity_scene = load("res://entities/TrixelEntity3D.tscn")
	_runtime_root = _get_or_create_root("RuntimeRoot")

	var sc = get_node_or_null("/root/SceneClient")
	if sc == null:
		push_error("[SemanticRenderer] SceneClient autoload not found")
		return
	sc.scene_loaded.connect(_on_scene_loaded)
	sc.request_failed.connect(_on_scene_error)
	sc.load_scene(SCENE_ID)


# ── Editor: live fetch ─────────────────────────
func _editor_fetch_and_build() -> void:
	var http := HTTPClient.new()
	var err := http.connect_to_host("127.0.0.1", 8765)
	if err != OK:
		push_error("[SemanticRenderer][editor] Cannot connect to 127.0.0.1:8765")
		return
	var tries := 0
	while http.get_status() in [HTTPClient.STATUS_CONNECTING, HTTPClient.STATUS_RESOLVING]:
		http.poll()
		tries += 1
		if tries > 100:
			push_error("[SemanticRenderer][editor] Connection timeout")
			return
	if http.get_status() != HTTPClient.STATUS_CONNECTED:
		push_error("[SemanticRenderer][editor] Not connected — is scene server on port 8765?")
		return
	err = http.request(HTTPClient.METHOD_GET,
		"/load_scene?scene_id=%s" % SCENE_ID.uri_encode(),
		["Accept: application/json"])
	if err != OK:
		push_error("[SemanticRenderer][editor] Request error: %d" % err)
		return
	while http.get_status() == HTTPClient.STATUS_REQUESTING:
		http.poll()
	var body := PackedByteArray()
	while http.get_status() == HTTPClient.STATUS_BODY:
		http.poll()
		var chunk := http.read_response_body_chunk()
		if chunk.size() > 0:
			body.append_array(chunk)
	var parsed = JSON.parse_string(body.get_string_from_utf8())
	if typeof(parsed) != TYPE_DICTIONARY:
		push_error("[SemanticRenderer][editor] Invalid JSON from server")
		return
	var data: Dictionary = (parsed as Dictionary).get("data", parsed)
	print("[SemanticRenderer][editor] Live fetch OK")
	_build_scene(data, _get_or_create_root("PreviewRoot"))


# ── Editor: file fallback ──────────────────────
func _editor_build() -> void:
	if not FileAccess.file_exists(preview_json_path):
		push_warning("[SemanticRenderer] File not found: " + preview_json_path)
		return
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(preview_json_path))
	if typeof(parsed) != TYPE_DICTIONARY:
		push_error("[SemanticRenderer] Bad JSON: " + preview_json_path)
		return
	var data: Dictionary = (parsed as Dictionary).get("data", parsed)
	_build_scene(data, _get_or_create_root("PreviewRoot"))


# ── Editor: clear preview ──────────────────────
func _editor_clear_preview() -> void:
	var pr = get_node_or_null("PreviewRoot")
	if pr == null:
		return
	if _undo_redo != null:
		_undo_redo.create_action("Clear SemanticRenderer Preview")
		_undo_redo.add_do_method(self, "remove_child", pr)
		_undo_redo.add_undo_method(self, "add_child", pr)
		_undo_redo.commit_action()
		_editor_plugin.get_editor_interface().mark_scene_as_unsaved()
	else:
		pr.queue_free()


# ── Runtime scene response ─────────────────────
func _on_scene_loaded(scene_id: String, data: Dictionary) -> void:
	print("[SemanticRenderer] scene_id: ", scene_id)
	print("[SemanticRenderer] spawn_commands: ", data.get("spawn_commands", []).size())
	_build_scene(data, _runtime_root)


func _on_scene_error(kind: String, detail: String, status_code: int) -> void:
	push_error("[SemanticRenderer] request_failed [%s] (%d): %s" % [kind, status_code, detail])


# ── Shared build ──────────────────────────────
func _build_scene(data: Dictionary, root: Node3D) -> void:
	_clear_root(root)

	if data.has("terrain_chunks"):
		_build_grid_from_commands(data["terrain_chunks"])
	elif data.has("terrain"):
		_build_grid_from_raw(data["terrain"])
	else:
		_build_fallback_grid(16, 16)

	_render_terrain(root)

	for cmd in data.get("spawn_commands", []):
		if cmd.get("type", "spawn_entity") == "spawn_entity":
			_spawn_entity(cmd, root)

	if not Engine.is_editor_hint():
		_frame_camera(root)


# ── Terrain grid builders ──────────────────────
func _build_grid_from_commands(chunks: Array) -> void:
	var max_x := 0; var max_z := 0
	for c in chunks:
		max_x = max(max_x, int(c.get("x", 0)))
		max_z = max(max_z, int(c.get("z", 0)))
	_init_grid(max_x + 1, max_z + 1, FALLBACK_TERRAIN)
	for c in chunks:
		_terrain_grid[int(c.get("z", 0))][int(c.get("x", 0))] = c.get("type", FALLBACK_TERRAIN)

func _build_grid_from_raw(raw) -> void:
	if raw is Array and raw.size() > 0 and raw[0] is Array:
		_grid_h = raw.size(); _grid_w = raw[0].size()
		_terrain_grid = raw.duplicate(true)
	else:
		_build_fallback_grid(16, 16)

func _build_fallback_grid(w: int, h: int) -> void:
	print("[SemanticRenderer] fallback terrain %dx%d" % [w, h])
	_init_grid(w, h, FALLBACK_TERRAIN)

func _init_grid(w: int, h: int, fill: String) -> void:
	_grid_w = w; _grid_h = h
	_terrain_grid.clear()
	for _z in range(h):
		var row := []; row.resize(w); row.fill(fill)
		_terrain_grid.append(row)


# ── Terrain renderer ───────────────────────────
func _render_terrain(root: Node3D) -> void:
	if _terrain_grid.is_empty(): return
	var st_map: Dictionary = {}
	for z in _grid_h:
		for x in _grid_w:
			var terrain := str(_terrain_grid[z][x])
			if not _atlases.has(terrain): terrain = FALLBACK_TERRAIN
			if not _atlases.has(terrain): continue
			var role := _resolve_role(x, z, terrain)
			if not st_map.has(terrain):
				var st := SurfaceTool.new()
				st.begin(Mesh.PRIMITIVE_TRIANGLES)
				st_map[terrain] = st
			_add_tile_to_surface(st_map[terrain], x, z, terrain, role)

	for terrain in st_map:
		var st: SurfaceTool = st_map[terrain]
		st.generate_normals()
		var mi := MeshInstance3D.new()
		mi.name = "Terrain_" + terrain
		mi.mesh = st.commit()
		var mat := StandardMaterial3D.new()
		mat.albedo_texture = _atlases[terrain]["texture"] as Texture2D
		mat.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
		mi.material_override = mat
		_add_node_to(mi, root)

	print("[SemanticRenderer] Terrain baked — %d mesh(es)" % st_map.size())


func _add_tile_to_surface(st: SurfaceTool, tx: int, tz: int,
		terrain: String, role: String) -> void:
	var atlas: Dictionary = _atlases[terrain] as Dictionary
	var tex: Texture2D = atlas["texture"] as Texture2D
	var tw := float(tex.get_width()); var th := float(tex.get_height())
	var rects: Dictionary = atlas["rects"] as Dictionary
	var region: Rect2i = rects.get(role, rects.get("center", Rect2i(0,0,TILE_PX,TILE_PX)))
	var u0 := region.position.x/tw; var v0 := region.position.y/th
	var u1 := (region.position.x+region.size.x)/tw
	var v1 := (region.position.y+region.size.y)/th
	# centered on origin
	var x0 := (tx - _grid_w * 0.5) * TILE_SIZE
	var x1 := x0 + TILE_SIZE
	var z0 := (tz - _grid_h * 0.5) * TILE_SIZE
	var z1 := z0 + TILE_SIZE
	var n := Vector3.UP
	st.set_uv(Vector2(u0,v0)); st.set_normal(n); st.add_vertex(Vector3(x0,TERRAIN_Y,z0))
	st.set_uv(Vector2(u1,v0)); st.set_normal(n); st.add_vertex(Vector3(x1,TERRAIN_Y,z0))
	st.set_uv(Vector2(u1,v1)); st.set_normal(n); st.add_vertex(Vector3(x1,TERRAIN_Y,z1))
	st.set_uv(Vector2(u0,v0)); st.set_normal(n); st.add_vertex(Vector3(x0,TERRAIN_Y,z0))
	st.set_uv(Vector2(u1,v1)); st.set_normal(n); st.add_vertex(Vector3(x1,TERRAIN_Y,z1))
	st.set_uv(Vector2(u0,v1)); st.set_normal(n); st.add_vertex(Vector3(x0,TERRAIN_Y,z1))


# ── Entity spawn ───────────────────────────────
func _spawn_entity(cmd: Dictionary, root: Node3D) -> void:
	if Engine.is_editor_hint():
		_spawn_editor_placeholder(cmd, root)
	else:
		_spawn_runtime_entity(cmd, root)


func _spawn_editor_placeholder(cmd: Dictionary, root: Node3D) -> void:
	# Editor preview: a real MeshInstance3D so it appears in Local tree
	var id: String = cmd.get("id", "entity")
	var size: Vector2 = _cmd_size(cmd)

	# Anchor node (Node3D) — holds position, named after entity
	var anchor := Node3D.new()
	anchor.name = id
	if cmd.has("position"):
		var p = cmd["position"]
		anchor.position = Vector3(float(p[0]), float(p[1]), float(p[2]))

	# Body mesh — capsule sized to render plan
	var body := MeshInstance3D.new()
	body.name = "Body"
	var capsule := CapsuleMesh.new()
	capsule.radius = size.x * 0.25
	capsule.height = size.y
	body.mesh = capsule
	body.position = Vector3(0.0, size.y * 0.5, 0.0)

	# Unique color per entity so they're visually distinct
	var mat := StandardMaterial3D.new()
	mat.albedo_color = _color_from_string(id)
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	body.material_override = mat

	# Label above
	var label := Label3D.new()
	label.name = "NameLabel"
	label.text = cmd.get("display_name", cmd.get("name", id))
	label.position = Vector3(0.0, size.y + 0.3, 0.0)
	label.pixel_size = 0.01
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED

	anchor.add_child(body)
	anchor.add_child(label)
	_add_node_to(anchor, root)
	# children need owner set too
	if Engine.is_editor_hint():
		var scene_root = _editor_plugin.get_editor_interface().get_edited_scene_root()
		body.owner = scene_root
		label.owner = scene_root

	print("[SemanticRenderer][editor] Placeholder: ", id, " @ ", anchor.position)


func _spawn_runtime_entity(cmd: Dictionary, root: Node3D) -> void:
	# Placeholder: same capsule mesh as editor preview until real visuals are ready.
	# TrixelEntity3D.tscn needs its own mesh nodes before it's useful here.
	var id: String = cmd.get("id", "entity")
	var size: Vector2 = _cmd_size(cmd)

	var anchor := Node3D.new()
	anchor.name = id
	if cmd.has("position"):
		var p = cmd["position"]
		anchor.position = Vector3(float(p[0]), float(p[1]), float(p[2]))

	var body := MeshInstance3D.new()
	body.name = "Body"
	var capsule := CapsuleMesh.new()
	capsule.radius = size.x * 0.25
	capsule.height = size.y
	body.mesh = capsule
	body.position = Vector3(0.0, size.y * 0.5, 0.0)

	var mat := StandardMaterial3D.new()
	mat.albedo_color = _color_from_string(id)
	body.material_override = mat

	var label := Label3D.new()
	label.name = "NameLabel"
	label.text = cmd.get("display_name", cmd.get("name", id))
	label.position = Vector3(0.0, size.y + 0.3, 0.0)
	label.pixel_size = 0.01
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED

	anchor.add_child(body)
	anchor.add_child(label)
	root.add_child(anchor)
	print("[SemanticRenderer] Spawned: ", id, " @ ", anchor.position)


func _cmd_size(cmd: Dictionary) -> Vector2:
	var s = cmd.get("size_world", null)
	if s is Array and s.size() >= 2:
		return Vector2(float(s[0]), float(s[1]))
	if s is Vector2:
		return s
	return Vector2(0.6, 1.8)  # character default


# ── Node addition (editor vs runtime) ─────────
func _add_node_to(node: Node, parent: Node) -> void:
	if Engine.is_editor_hint() and _undo_redo != null:
		var scene_root = _editor_plugin.get_editor_interface().get_edited_scene_root()
		_undo_redo.create_action("SemanticRenderer: add " + node.name)
		_undo_redo.add_do_method(parent, "add_child", node)
		_undo_redo.add_do_method(node, "set_owner", scene_root)
		_undo_redo.add_undo_method(parent, "remove_child", node)
		_undo_redo.commit_action()
		_editor_plugin.get_editor_interface().mark_scene_as_unsaved()
	else:
		parent.add_child(node)


# ── Camera framing (runtime only) ─────────────
func _frame_camera(root: Node3D) -> void:
	var cam := get_viewport().get_camera_3d()
	if cam == null: return
	var pts: Array[Vector3] = []
	for c in root.get_children():
		if c is Node3D:
			pts.append((c as Node3D).global_position)
	if pts.is_empty(): return
	var center := Vector3.ZERO
	for p in pts: center += p
	center /= float(pts.size())
	var radius := 8.0
	for p in pts: radius = max(radius, center.distance_to(p) + 3.0)
	cam.global_position = center + Vector3(0.0, radius * 0.9, radius * 1.4)
	cam.look_at(center, Vector3.UP)


# ── Atlas loader ───────────────────────────────
func _load_all_atlases() -> void:
	_atlases.clear()
	for terrain in TERRAIN_DRAW_ORDER:
		var dir := "%s/%s" % [ASSET_ROOT, terrain]
		if not FileAccess.file_exists("%s/manifest.json" % dir) \
		or not FileAccess.file_exists("%s/atlas_meta.json" % dir):
			continue
		var manifest = JSON.parse_string(FileAccess.get_file_as_string("%s/manifest.json" % dir))
		var atlas_meta = JSON.parse_string(FileAccess.get_file_as_string("%s/atlas_meta.json" % dir))
		var tex: Texture2D = load("%s/atlas.png" % dir)
		if typeof(manifest) != TYPE_DICTIONARY or typeof(atlas_meta) != TYPE_DICTIONARY or tex == null:
			continue
		var tile_order: Array = atlas_meta.get("tile_order", [])
		var columns: int = int(atlas_meta.get("columns", 4))
		var tw: int = int(atlas_meta.get("tile_width", TILE_PX))
		var th: int = int(atlas_meta.get("tile_height", TILE_PX))
		var rects: Dictionary = {}
		for i in tile_order.size():
			rects[str(tile_order[i])] = Rect2i((i % columns)*tw, (i / columns)*th, tw, th)
		_atlases[terrain] = {"texture": tex, "rects": rects}
	print("[SemanticRenderer] Loaded %d terrain atlases" % _atlases.size())


func _color_from_string(seed_text: String) -> Color:
	var h: int = seed_text.hash()
	var r := 0.35 + (float((h >> 16) & 0xFF) / 255.0) * 0.55
	var g := 0.35 + (float((h >> 8)  & 0xFF) / 255.0) * 0.55
	var b := 0.35 + (float(h         & 0xFF) / 255.0) * 0.55
	return Color(r, g, b, 1.0)


# ── Autotile ───────────────────────────────────
func _terrain_at(x: int, z: int) -> String:
	if z < 0 or z >= _terrain_grid.size(): return ""
	var row: Array = _terrain_grid[z]
	if x < 0 or x >= row.size(): return ""
	return str(row[x])

func _resolve_role(x: int, z: int, terrain: String) -> String:
	var n := _terrain_at(x,z-1)==terrain; var s := _terrain_at(x,z+1)==terrain
	var e := _terrain_at(x+1,z)==terrain; var w := _terrain_at(x-1,z)==terrain
	var c := int(n)+int(s)+int(e)+int(w)
	match c:
		0: return "single"
		4: return "center"
		3:
			if not n: return "edge_n"
			if not s: return "edge_s"
			if not e: return "edge_e"
			return "edge_w"
		2:
			if s and e: return "corner_nw"
			if s and w: return "corner_ne"
			if n and e: return "corner_sw"
			if n and w: return "corner_se"
			if n and s: return "path_straight_v"
			return "path_straight_h"
		1:
			if n: return "path_end_s"
			if s: return "path_end_n"
			if e: return "path_end_w"
			return "path_end_e"
	return "center"


# ── Root helpers ───────────────────────────────
func _get_or_create_root(root_name: String) -> Node3D:
	var existing = get_node_or_null(root_name)
	if existing is Node3D:
		return existing as Node3D
	var root := Node3D.new()
	root.name = root_name
	add_child(root)
	if Engine.is_editor_hint():
		root.owner = get_tree().edited_scene_root
	return root

func _clear_root(root: Node3D) -> void:
	_terrain_grid.clear(); _grid_w = 0; _grid_h = 0
	for c in root.get_children():
		c.queue_free()
