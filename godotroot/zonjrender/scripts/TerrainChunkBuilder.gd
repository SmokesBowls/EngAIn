class_name TerrainChunkBuilder
extends RefCounted
# ─────────────────────────────────────────────
#  TerrainChunkBuilder.gd
#  Pure factory — owns all SurfaceTool math,
#  UV atlas mapping, and autotile resolution.
#  Returns Array[MeshInstance3D] — one per terrain type.
#  No network, no add_child, no editor logic.
# ─────────────────────────────────────────────

const ASSET_ROOT       := "res://engain/tests/trixel/assets"
const TILE_SIZE        := 1.0
const TERRAIN_Y        := 0.0
const TILE_PX          := 16
const FALLBACK_TERRAIN := "grass"

const TERRAIN_DRAW_ORDER := [
	"deep_water","shallow_water","shoreline","sand",
	"grass","forest_edge","pier","rock","cliff",
]

var _atlases: Dictionary = {}
var _terrain_grid: Array = []
var _grid_w: int = 0
var _grid_h: int = 0


# ── Public API ─────────────────────────────────
func build(data: Dictionary) -> Array:
	_load_atlases()
	_build_grid(data)
	return _bake_meshes()


# ── Atlas loading ──────────────────────────────
func _load_atlases() -> void:
	if not _atlases.is_empty():
		return
	for terrain in TERRAIN_DRAW_ORDER:
		var dir := "%s/%s" % [ASSET_ROOT, terrain]
		var man_path  := "%s/manifest.json"   % dir
		var meta_path := "%s/atlas_meta.json" % dir
		var atl_path  := "%s/atlas.png"       % dir
		if not FileAccess.file_exists(man_path) or not FileAccess.file_exists(meta_path):
			continue
		var manifest   = JSON.parse_string(FileAccess.get_file_as_string(man_path))
		var atlas_meta = JSON.parse_string(FileAccess.get_file_as_string(meta_path))
		var tex: Texture2D = load(atl_path)
		if typeof(manifest) != TYPE_DICTIONARY or typeof(atlas_meta) != TYPE_DICTIONARY or tex == null:
			continue
		var tile_order: Array = atlas_meta.get("tile_order", [])
		var columns: int = int(atlas_meta.get("columns", 4))
		var tw: int = int(atlas_meta.get("tile_width",  TILE_PX))
		var th: int = int(atlas_meta.get("tile_height", TILE_PX))
		var rects: Dictionary = {}
		for i in tile_order.size():
			rects[str(tile_order[i])] = Rect2i((i % columns) * tw, (i / columns) * th, tw, th)
		_atlases[terrain] = {"texture": tex, "rects": rects}


# ── Grid builders ──────────────────────────────
func _build_grid(data: Dictionary) -> void:
	if data.has("terrain_chunks"):
		_from_commands(data["terrain_chunks"])
	elif data.has("terrain"):
		_from_raw(data["terrain"])
	else:
		_fallback(16, 16)

func _from_commands(chunks: Array) -> void:
	var max_x := 0; var max_z := 0
	for c in chunks:
		max_x = max(max_x, int(c.get("x", 0)))
		max_z = max(max_z, int(c.get("z", 0)))
	_init_grid(max_x + 1, max_z + 1, FALLBACK_TERRAIN)
	for c in chunks:
		_terrain_grid[int(c.get("z", 0))][int(c.get("x", 0))] = c.get("type", FALLBACK_TERRAIN)

func _from_raw(raw) -> void:
	if raw is Array and raw.size() > 0 and raw[0] is Array:
		_grid_h = raw.size(); _grid_w = raw[0].size()
		_terrain_grid = raw.duplicate(true)
	else:
		_fallback(16, 16)

func _fallback(w: int, h: int) -> void:
	_init_grid(w, h, FALLBACK_TERRAIN)

func _init_grid(w: int, h: int, fill: String) -> void:
	_grid_w = w; _grid_h = h; _terrain_grid.clear()
	for _z in range(h):
		var row := []; row.resize(w); row.fill(fill)
		_terrain_grid.append(row)


# ── Mesh baking ────────────────────────────────
func _bake_meshes() -> Array:
	var st_map: Dictionary = {}
	for z in _grid_h:
		for x in _grid_w:
			var terrain := str(_terrain_grid[z][x])
			if not _atlases.has(terrain): terrain = FALLBACK_TERRAIN
			if not _atlases.has(terrain): continue
			if not st_map.has(terrain):
				var st := SurfaceTool.new()
				st.begin(Mesh.PRIMITIVE_TRIANGLES)
				st_map[terrain] = st
			_add_tile(st_map[terrain], x, z, terrain, _resolve_role(x, z, terrain))

	var result: Array = []
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
		result.append(mi)
	return result


func _add_tile(st: SurfaceTool, tx: int, tz: int, terrain: String, role: String) -> void:
	var atlas: Dictionary = _atlases[terrain] as Dictionary
	var tex: Texture2D    = atlas["texture"] as Texture2D
	var rects: Dictionary = atlas["rects"] as Dictionary
	var tw := float(tex.get_width()); var th := float(tex.get_height())
	var region: Rect2i = rects.get(role, rects.get("center", Rect2i(0, 0, TILE_PX, TILE_PX)))
	var u0 := region.position.x / tw;  var v0 := region.position.y / th
	var u1 := (region.position.x + region.size.x) / tw
	var v1 := (region.position.y + region.size.y) / th
	var x0 := (tx - _grid_w * 0.5) * TILE_SIZE; var x1 := x0 + TILE_SIZE
	var z0 := (tz - _grid_h * 0.5) * TILE_SIZE; var z1 := z0 + TILE_SIZE
	var n := Vector3.UP
	st.set_uv(Vector2(u0,v0)); st.set_normal(n); st.add_vertex(Vector3(x0,TERRAIN_Y,z0))
	st.set_uv(Vector2(u1,v0)); st.set_normal(n); st.add_vertex(Vector3(x1,TERRAIN_Y,z0))
	st.set_uv(Vector2(u1,v1)); st.set_normal(n); st.add_vertex(Vector3(x1,TERRAIN_Y,z1))
	st.set_uv(Vector2(u0,v0)); st.set_normal(n); st.add_vertex(Vector3(x0,TERRAIN_Y,z0))
	st.set_uv(Vector2(u1,v1)); st.set_normal(n); st.add_vertex(Vector3(x1,TERRAIN_Y,z1))
	st.set_uv(Vector2(u0,v1)); st.set_normal(n); st.add_vertex(Vector3(x0,TERRAIN_Y,z1))


# ── Autotile ───────────────────────────────────
func _at(x: int, z: int) -> String:
	if z < 0 or z >= _terrain_grid.size(): return ""
	var row: Array = _terrain_grid[z]
	if x < 0 or x >= row.size(): return ""
	return str(row[x])

func _resolve_role(x: int, z: int, t: String) -> String:
	var n := _at(x,z-1)==t; var s := _at(x,z+1)==t
	var e := _at(x+1,z)==t; var w := _at(x-1,z)==t
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
