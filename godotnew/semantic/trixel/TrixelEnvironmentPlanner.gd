extends RefCounted
class_name TrixelEnvironmentPlanner

const DEFAULT_TILE := "grass"

# Absolute path to the Python terrain adapter CLI.
const WORLD_FIELD_SCRIPT := "/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/terrain/trixel_world_adapter.py"

const TERRAIN_MAP := {
	"beach":     "sand",
	"coastal":   "shoreline",
	"shore":     "shoreline",
	"shoreline": "shoreline",
	"ocean":     "deep_water",
	"water":     "shallow_water",
	"forest":    "forest_edge",
	"woods":     "forest_edge",
	"grass":     "grass",
	"plains":    "grass",
	"rock":      "rock",
	"cliff":     "cliff",
	"sand":      "sand",
	"desert":    "sand",
}

const SIZE_MAP := {
	"tiny":    Vector2i(24, 24),
	"small":   Vector2i(32, 32),
	"medium":  Vector2i(48, 48),
	"large":   Vector2i(64, 64),
	"massive": Vector2i(96, 96),
}

static func plan(runtime_scene_doc: Dictionary) -> Dictionary:
	var terrain_family: String = String(
		runtime_scene_doc.get("terrain_family", "grass")
	).to_lower().strip_edges()

	var environment: String = String(
		runtime_scene_doc.get("environment", "")
	).to_lower().strip_edges()

	var region: String = String(
		runtime_scene_doc.get("region", "")
	).to_lower().strip_edges()

	var scale_hint: String = String(
		runtime_scene_doc.get("spatial_scale_hint", "medium")
	).to_lower().strip_edges()

	var level_design: Dictionary = runtime_scene_doc.get("level_design", {})
	var terrain_metadata: Dictionary = runtime_scene_doc.get("terrain_metadata", {})

	# REQUIREMENT 1 & 2: Determine source scene JSON path if available from payload dict
	var source_path := ""
	if runtime_scene_doc.has("file") and typeof(runtime_scene_doc["file"]) == TYPE_DICTIONARY:
		var file_dict = runtime_scene_doc["file"] as Dictionary
		if file_dict.has("path") and typeof(file_dict["path"]) == TYPE_DICTIONARY:
			var path_dict = file_dict["path"] as Dictionary
			source_path = String(path_dict.get("source_path", ""))
	
	# REQUIREMENT 3: If not available, apply the specific temporary fallback path
	if source_path.is_empty():
		source_path = "/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/.engain_cache/parsed/scenes/002_molten_descent_with_semantics.zonj.json"
		
	var scene_id := String(runtime_scene_doc.get("scene_id", runtime_scene_doc.get("id", runtime_scene_doc.get("@id", "unknown"))))

	# Extract runtime string fragments to serve as primary dynamic context
	var context_fragments := [terrain_family, environment, region, scene_id]
	var context_string := " ".join(context_fragments).to_lower()

	# --- Try Python WorldField pipeline ---
	var wf_plan := _fetch_world_field_plan(scale_hint, scene_id, source_path, context_string)
	if not wf_plan.is_empty():
		var prop_placements := _build_prop_plan(level_design)
		var landmark_nodes  := _build_landmark_nodes(level_design)
		wf_plan["prop_placements"] = prop_placements
		wf_plan["landmark_nodes"]  = landmark_nodes
		wf_plan["terrain_family"]  = terrain_family
		wf_plan["environment"]     = environment
		return wf_plan

	# --- REQUIREMENT 5: Static fallback behavior if Python fails ---
	print("[TRIXEL_PLAN] source=static (world_field unavailable)")
	var resolved_tile := _resolve_tile(terrain_family, environment, region)
	var map_size := _resolve_size(scale_hint)
	var terrain_grid := _generate_base_grid(map_size, resolved_tile)

	_apply_environment_rules(terrain_grid, resolved_tile, environment, terrain_metadata)

	var prop_placements := _build_prop_plan(level_design)
	var landmark_nodes := _build_landmark_nodes(level_design)

	return {
		"terrain_grid":    terrain_grid,
		"prop_placements": prop_placements,
		"landmark_nodes":  landmark_nodes,
		"terrain_family":  terrain_family,
		"environment":     environment,
		"map_size": {
			"x": map_size.x,
			"y": map_size.y,
		},
	}


static func _fetch_world_field_plan(scale_hint: String, scene_id: String, source_path: String, context_string: String) -> Dictionary:
	"""
	Call the Python terrain CLI and return its plan dict.
	Returns empty Dictionary on any failure — caller falls back to static generation.
	"""
	if not FileAccess.file_exists(WORLD_FIELD_SCRIPT):
		return {}

	var size := _resolve_size(scale_hint)
	
	# REQUIREMENT 4: Pass explicitly via --scene-json, --scene-id, and --context parameters
	var args := PackedStringArray([
		WORLD_FIELD_SCRIPT,
		"--demo",
		"--width",  str(size.x),
		"--height", str(size.y),
		"--context", context_string,
		"--scene-json", source_path,
		"--scene-id", scene_id
	])

	var output: Array = []
	var exit_code := OS.execute("python3", args, output, false, false)

	if exit_code != 0 or output.is_empty():
		push_warning("[TRIXEL_PLAN] Python CLI failed (exit %d)" % exit_code)
		return {}

	var raw: String = String(output[0]).strip_edges()
	var parsed = JSON.parse_string(raw)
	if typeof(parsed) != TYPE_DICTIONARY:
		push_warning("[TRIXEL_PLAN] Python CLI returned invalid JSON")
		return {}

	var data: Dictionary = parsed as Dictionary
	if not data.has("terrain_grid"):
		push_warning("[TRIXEL_PLAN] Python CLI JSON missing terrain_grid key")
		return {}

	var source: String = String(data.get("source", "unknown"))
	var profile: String = String(data.get("profile", "default"))
	
	# REQUIREMENT 6: Explicit log matching expected formatting
	print("[TRIXEL_PLAN] source=%s profile=%s grid=%dx%d" % [
		source,
		profile,
		size.x,
		size.y,
	])

	return {
		"terrain_grid": data["terrain_grid"],
		"map_size": {"x": size.x, "y": size.y},
	}

static func _resolve_tile(
	terrain_family: String,
	environment: String,
	region: String
) -> String:
	for key in [terrain_family, environment, region]:
		if key != "" and TERRAIN_MAP.has(key):
			return TERRAIN_MAP[key]
	return DEFAULT_TILE

static func _resolve_size(scale_hint: String) -> Vector2i:
	if SIZE_MAP.has(scale_hint):
		return SIZE_MAP[scale_hint]
	if scale_hint.contains("massive"):
		return SIZE_MAP["massive"]
	if scale_hint.contains("large"):
		return SIZE_MAP["large"]
	if scale_hint.contains("small"):
		return SIZE_MAP["small"]
	return SIZE_MAP["medium"]

static func _generate_base_grid(size: Vector2i, fill_tile: String) -> Array:
	var grid: Array = []
	for y in range(size.y):
		var row: Array = []
		for x in range(size.x):
			row.append(fill_tile)
		grid.append(row)
	return grid

static func _apply_environment_rules(
	grid: Array,
	base_tile: String,
	environment: String,
	terrain_metadata: Dictionary
) -> void:
	if grid.is_empty():
		return

	var height := grid.size()
	var width := (grid[0] as Array).size()

	match base_tile:
		"shoreline":
			var water_band := int(height * 0.25)
			for y in range(water_band):
				for x in range(width):
					grid[y][x] = "deep_water"
			var shallow_band := int(height * 0.40)
			for y in range(water_band, shallow_band):
				for x in range(width):
					grid[y][x] = "shallow_water"

		"forest_edge":
			for y in range(height):
				for x in range(width):
					if x == 0 or y == 0 or x == width - 1 or y == height - 1:
						grid[y][x] = "forest_edge"

		"sand":
			for y in range(height):
				for x in range(width):
					if y < int(height * 0.10):
						grid[y][x] = "rock"

	if bool(terrain_metadata.get("contains_pier", false)):
		var pier_x := width / 2
		for y in range(0, min(10, height)):
			grid[y][pier_x] = "pier"

static func _build_prop_plan(level_design: Dictionary) -> Array:
	var props: Array = []
	var landmarks_v: Variant = level_design.get("landmarks", [])
	if typeof(landmarks_v) == TYPE_ARRAY:
		var idx := 0
		for item in landmarks_v:
			props.append({
				"id":   "landmark_%d" % idx,
				"type": "landmark",
				"name": String(item),
				"position": {
					"x": 8 + (idx * 4),
					"y": 0,
					"z": 8 + (idx * 3),
				},
			})
			idx += 1
	return props

static func _build_landmark_nodes(level_design: Dictionary) -> Array:
	var nodes: Array = []
	var entry_point := String(level_design.get("entry_point", "south"))
	nodes.append({
		"id":        "entry_point",
		"kind":      "spawn",
		"direction": entry_point,
	})
	return nodes