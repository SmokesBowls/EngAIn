extends Node2D

const ASSET_ROOT := "res://engain/tests/trixel/assets"
const TILE_SIZE := 16
const DISPLAY_SCALE := 3
const GRID_ORIGIN := Vector2i(24, 24)
const LEGEND_ORIGIN := Vector2i(24, 860)
const SAMPLE_WIDTH := 20
const SAMPLE_HEIGHT := 16

const TERRAIN_DRAW_ORDER := [
	"deep_water",
	"shallow_water",
	"shoreline",
	"sand",
	"grass",
	"forest_edge",
	"pier",
	"rock",
	"cliff",
]

var atlases: Dictionary = {}
var sample_grid: Array = []

func _ready() -> void:
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_load_all_assets()
	_build_sample_grid()
	queue_redraw()


func _load_all_assets() -> void:
	atlases.clear()
	for terrain in TERRAIN_DRAW_ORDER:
		var dir_path := "%s/%s" % [ASSET_ROOT, terrain]
		var manifest_path := "%s/manifest.json" % dir_path
		var atlas_meta_path := "%s/atlas_meta.json" % dir_path
		var atlas_path := "%s/atlas.png" % dir_path

		if not FileAccess.file_exists(manifest_path):
			push_warning("Missing manifest for terrain: %s" % terrain)
			continue
		if not FileAccess.file_exists(atlas_meta_path):
			push_warning("Missing atlas_meta for terrain: %s" % terrain)
			continue

		var manifest_raw := FileAccess.get_file_as_string(manifest_path)
		var meta_raw := FileAccess.get_file_as_string(atlas_meta_path)
		var manifest = JSON.parse_string(manifest_raw)
		var atlas_meta = JSON.parse_string(meta_raw)
		var atlas_tex: Texture2D = load(atlas_path)

		if typeof(manifest) != TYPE_DICTIONARY:
			push_warning("Invalid manifest JSON for terrain: %s" % terrain)
			continue
		if typeof(atlas_meta) != TYPE_DICTIONARY:
			push_warning("Invalid atlas_meta JSON for terrain: %s" % terrain)
			continue
		if atlas_tex == null:
			push_warning("Failed to load atlas texture for terrain: %s" % terrain)
			continue

		var tile_order: Array = atlas_meta.get("tile_order", [])
		var columns: int = int(atlas_meta.get("columns", 4))
		var tile_width: int = int(atlas_meta.get("tile_width", TILE_SIZE))
		var tile_height: int = int(atlas_meta.get("tile_height", TILE_SIZE))
		var rects: Dictionary = {}

		for i in range(tile_order.size()):
			var role: String = str(tile_order[i])
			var col: int = i % columns
			var row: int = i / columns
			rects[role] = Rect2i(col * tile_width, row * tile_height, tile_width, tile_height)

		atlases[terrain] = {
			"manifest": manifest,
			"atlas_meta": atlas_meta,
			"texture": atlas_tex,
			"rects": rects,
		}


func _build_sample_grid() -> void:
	sample_grid.clear()
	for y in range(SAMPLE_HEIGHT):
		var row: Array = []
		for x in range(SAMPLE_WIDTH):
			var terrain := "sand"
			if y <= 2:
				terrain = "deep_water"
			elif y <= 4:
				terrain = "shallow_water"
			elif y == 5:
				terrain = "shoreline"
			elif y <= 10:
				terrain = "sand"
			elif y <= 13:
				terrain = "grass"
			else:
				terrain = "forest_edge"
			row.append(terrain)
		sample_grid.append(row)

	# Pier running from shoreline into the water.
	for y in range(2, 11):
		sample_grid[y][9] = "pier"
		sample_grid[y][10] = "pier"

	# Rock outcrop and cliff patch on the right edge to verify more than one family loads.
	for y in range(11, 14):
		for x in range(15, 18):
			sample_grid[y][x] = "rock"
	for y in range(14, 16):
		for x in range(15, 19):
			sample_grid[y][x] = "cliff"


func _terrain_at(x: int, y: int) -> String:
	if y < 0 or y >= sample_grid.size():
		return ""
	var row: Array = sample_grid[y]
	if x < 0 or x >= row.size():
		return ""
	return str(row[x])


func _resolve_role(x: int, y: int, terrain: String) -> String:
	var has_n := _terrain_at(x, y - 1) == terrain
	var has_s := _terrain_at(x, y + 1) == terrain
	var has_e := _terrain_at(x + 1, y) == terrain
	var has_w := _terrain_at(x - 1, y) == terrain

	var count := 0
	if has_n:
		count += 1
	if has_s:
		count += 1
	if has_e:
		count += 1
	if has_w:
		count += 1

	if count == 0:
		return "single"
	if count == 4:
		return "center"
	if count == 3:
		if not has_n:
			return "edge_n"
		if not has_s:
			return "edge_s"
		if not has_e:
			return "edge_e"
		if not has_w:
			return "edge_w"
	if count == 2:
		if has_s and has_e:
			return "corner_nw"
		if has_s and has_w:
			return "corner_ne"
		if has_n and has_e:
			return "corner_sw"
		if has_n and has_w:
			return "corner_se"
		if has_n and has_s:
			return "path_straight_v"
		if has_e and has_w:
			return "path_straight_h"
	if count == 1:
		if has_n:
			return "path_end_s"
		if has_s:
			return "path_end_n"
		if has_e:
			return "path_end_w"
		if has_w:
			return "path_end_e"
	return "center"


func _draw() -> void:
	_draw_world_preview()
	_draw_legend()


func _draw_world_preview() -> void:
	if atlases.is_empty():
		return

	for y in range(SAMPLE_HEIGHT):
		for x in range(SAMPLE_WIDTH):
			var terrain := _terrain_at(x, y)
			if not atlases.has(terrain):
				continue
			var atlas: Dictionary = atlases[terrain]
			var rects: Dictionary = atlas.get("rects", {})
			var role := _resolve_role(x, y, terrain)
			var region: Rect2i = rects.get(role, rects.get("center", Rect2i(0, 0, TILE_SIZE, TILE_SIZE)))
			var texture: Texture2D = atlas.get("texture")

			var dest := Rect2(
				GRID_ORIGIN.x + x * TILE_SIZE * DISPLAY_SCALE,
				GRID_ORIGIN.y + y * TILE_SIZE * DISPLAY_SCALE,
				TILE_SIZE * DISPLAY_SCALE,
				TILE_SIZE * DISPLAY_SCALE
			)
			draw_texture_rect_region(texture, dest, Rect2(region.position, region.size))

	# Light grid overlay so bad seam logic stands out instead of hiding in pixel soup.
	var world_width := SAMPLE_WIDTH * TILE_SIZE * DISPLAY_SCALE
	var world_height := SAMPLE_HEIGHT * TILE_SIZE * DISPLAY_SCALE
	var grid_color := Color(0, 0, 0, 0.20)
	for x in range(SAMPLE_WIDTH + 1):
		var gx := GRID_ORIGIN.x + x * TILE_SIZE * DISPLAY_SCALE
		draw_line(Vector2(gx, GRID_ORIGIN.y), Vector2(gx, GRID_ORIGIN.y + world_height), grid_color, 1.0)
	for y in range(SAMPLE_HEIGHT + 1):
		var gy := GRID_ORIGIN.y + y * TILE_SIZE * DISPLAY_SCALE
		draw_line(Vector2(GRID_ORIGIN.x, gy), Vector2(GRID_ORIGIN.x + world_width, gy), grid_color, 1.0)


func _draw_legend() -> void:
	var index := 0
	for terrain in TERRAIN_DRAW_ORDER:
		if not atlases.has(terrain):
			continue
		var atlas: Dictionary = atlases[terrain]
		var rects: Dictionary = atlas.get("rects", {})
		var region: Rect2i = rects.get("center", Rect2i(0, 0, TILE_SIZE, TILE_SIZE))
		var texture: Texture2D = atlas.get("texture")

		var col := index % 3
		var row := index / 3
		var x := LEGEND_ORIGIN.x + col * 210
		var y := LEGEND_ORIGIN.y + row * 70
		var dest := Rect2(x, y, TILE_SIZE * DISPLAY_SCALE, TILE_SIZE * DISPLAY_SCALE)
		draw_texture_rect_region(texture, dest, Rect2(region.position, region.size))
		index += 1
