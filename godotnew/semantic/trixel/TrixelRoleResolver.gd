extends RefCounted
class_name TrixelRoleResolver

static func terrain_at(grid: Array, x: int, y: int) -> String:
	if y < 0 or y >= grid.size():
		return ""
	var row: Array = grid[y]
	if x < 0 or x >= row.size():
		return ""
	return str(row[x])

static func resolve_role(grid: Array, x: int, y: int, terrain: String) -> String:
	var has_n := terrain_at(grid, x, y - 1) == terrain
	var has_s := terrain_at(grid, x, y + 1) == terrain
	var has_e := terrain_at(grid, x + 1, y) == terrain
	var has_w := terrain_at(grid, x - 1, y) == terrain

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
