extends RefCounted
class_name TrixelEnvironmentPlanner

# =============================================================================
# 🏛️ CONSTITUTIONAL SEMANTIC CONFIGURATION STORAGE (IN-MEMORY CACHE)
# =============================================================================

static var _vocabulary_cache: Dictionary = {}
static var _cache_loaded: bool = false

const DEFAULT_TILE := "grass"
const WORLD_FIELD_SCRIPT := "/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/terrain/trixel_world_adapter.py"

const SIZE_MAP := {
	"tiny":    Vector2i(24, 24),
	"small":   Vector2i(32, 32),
	"medium":  Vector2i(48, 48),
	"large":   Vector2i(64, 64),
	"massive": Vector2i(96, 96),
}

static func initialize_vocabulary_bindings(bindings_path: String) -> void:
	if _cache_loaded:
		return
		
	print("[GOVERNANCE] [BINDINGS] Hydrating semantic ABI layer into memory...")
	if not FileAccess.file_exists(bindings_path):
		print("[GOVERNANCE] [BINDINGS] [WARN] Bindings file missing. Defaulting to empty literal map.")
		_cache_loaded = true
		return

	var file := FileAccess.open(bindings_path, FileAccess.READ)
	var json_string := file.get_as_text()
	file.close()

	var json := JSON.new()
	if json.parse(json_string) != OK:
		print("[GOVERNANCE] [BINDINGS] [ERROR] Structural invalidity in bindings file: ", json.get_error_message())
		_cache_loaded = true
		return

	var payload: Dictionary = json.get_data() as Dictionary
	_vocabulary_cache = payload.get("terrain_mappings", {})
	_cache_loaded = true
	print("[GOVERNANCE] [BINDINGS] Successfully cached %d primitive aliases in-memory." % _vocabulary_cache.size())


static func resolve_tile_alias(local_token: String) -> String:
	if _vocabulary_cache.has(local_token):
		return String(_vocabulary_cache[local_token])
	return local_token

# =============================================================================
# 🛡️ THE PARALLEL TREATY INGESTION LANE (PROSE-BLIND EXECUTION BOUNDARY)
# =============================================================================

static func load_treaty_terrain_plan(plan_path: String) -> Dictionary:
	if not FileAccess.file_exists(plan_path):
		print("[TRIXEL_TREATY] [ERROR] Treaty plan missing from absolute disk location: ", plan_path)
		return {}

	var file := FileAccess.open(plan_path, FileAccess.READ)
	var json_string := file.get_as_text()
	file.close()

	var json := JSON.new()
	var error := json.parse(json_string)
	if error != OK:
		print("[TRIXEL_TREATY] [ERROR] JSON serialization format invalid at line %d: %s" % [json.get_error_line(), json.get_error_message()])
		return {}

	var payload: Dictionary = json.get_data() as Dictionary

	if not _validate_treaty_contract_keys(payload):
		print("[TRIXEL_TREATY] [REJECT] Ingestion blocked: Payload violates structural schema constraints.")
		return {}

	var scene_id: String = payload.get("scene_id", "unknown_node")
	var grid: Array = payload.get("terrain_grid", [])
	var render_manifest: Dictionary = payload.get("render_manifest", {})
	
	var height: int = grid.size()
	var width: int = 0
	if height > 0 and typeof(grid[0]) == TYPE_ARRAY:
		width = (grid[0] as Array).size()

	print("[TRIXEL_TREATY] Loaded treaty terrain plan: ", scene_id)
	print("[TRIXEL_TREATY] Grid size: %dx%d" % [width, height])

	return {
		"scene_id": scene_id,
		"terrain_grid": grid,
		"render_manifest": render_manifest
	}


static func _validate_treaty_contract_keys(payload: Dictionary) -> bool:
	var mandatory_keys := ["scene_id", "terrain_grid", "render_manifest"]
	for key in mandatory_keys:
		if not payload.has(key):
			print("[TRIXEL_TREATY] [REJECT] Missing mandatory structural key: '", key, "'")
			return false
	return true

# =============================================================================
# 🔄 TRANSITIONAL FALLBACK PIPELINE (STRUCTURED RUNTIME CONTEXT PHASE B)
# =============================================================================

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

	var source_path := ""
	if runtime_scene_doc.has("file") and typeof(runtime_scene_doc["file"]) == TYPE_DICTIONARY:
		var file_dict = runtime_scene_doc["file"] as Dictionary
		if file_dict.has("path") and typeof(file_dict["path"]) == TYPE_DICTIONARY:
			var path_dict = file_dict["path"] as Dictionary
			source_path = String(path_dict.get("source_path", ""))
	
	if source_path.is_empty():
		source_path = "/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/.engain_cache/parsed/scenes/002_molten_descent_with_semantics.zonj.json"
		
	var scene_id := String(runtime_scene_doc.get("scene_id", runtime_scene_doc.get("id", runtime_scene_doc.get("@id", "unknown"))))

	# 🛡️ PHASE B: COMPILING STRUCTURED CONTEXT MATRIX
	# Banish unstructured text blending. Properties are strongly compartmentalized.
	var structured_context := {
		"terrain_profile": terrain_family,
		"environment_type": environment,
		"region_type": region,
		"atmospheric_profile": String(terrain_metadata.get("atmosphere", "default")),
		"world_state_id": scene_id
	}
	var context_payload_string := JSON.stringify(structured_context)

	# Pass the explicit payload string rather than raw space-separated text tokens
	var wf_plan := _fetch_world_field_plan(scale_hint, scene_id, source_path, context_payload_string)
	if not wf_plan.is_empty():
		var prop_placements := _build_prop_plan(level_design)
		var landmark_nodes  := _build_landmark_nodes(level_design)
		wf_plan["prop_placements"] = prop_placements
		wf_plan["landmark_nodes"]  = landmark_nodes
		wf_plan["terrain_family"]  = terrain_family
		wf_plan["environment"]     = environment
		return wf_plan

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


static func _fetch_world_field_plan(scale_hint: String, scene_id: String, source_path: String, context_json_string: String) -> Dictionary:
	if not FileAccess.file_exists(WORLD_FIELD_SCRIPT):
		return {}

	var size := _resolve_size(scale_hint)
	
	# The context argument now carries a clean serialized structural block
	var args := PackedStringArray([
		WORLD_FIELD_SCRIPT,
		"--demo",
		"--width",  str(size.x),
		"--height", str(size.y),
		"--context", context_json_string,
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
		push_warning("[TRIXEL_PLAN_ERR] Python CLI JSON missing terrain_grid key")
		return {}

	var source: String = String(data.get("source", "unknown"))
	var profile: String = String(data.get("profile", "default"))
	
	print("[TRIXEL_PLAN] source=%s profile=%s grid=%dx%d" % [source, profile, size.x, size.y])

	return {
		"terrain_grid": data["terrain_grid"],
		"map_size": {"x": size.x, "y": size.y},
	}

# --- Existing Helper Layout Functions Remain Perfectly Intact Underneath ---
static func _resolve_tile(terrain_family: String, environment: String, region: String) -> String:
	for key in [terrain_family, environment, region]:
		if key != "":
			var cached_alias := resolve_tile_alias(key)
			if cached_alias != key:
				return cached_alias
	return DEFAULT_TILE

static func _resolve_size(scale_hint: String) -> Vector2i:
	if SIZE_MAP.has(scale_hint): return SIZE_MAP[scale_hint]
	if scale_hint.contains("massive"): return SIZE_MAP["massive"]
	if scale_hint.contains("large"): return SIZE_MAP["large"]
	if scale_hint.contains("small"): return SIZE_MAP["small"]
	return SIZE_MAP["medium"]

static func _generate_base_grid(size: Vector2i, fill_tile: String) -> Array:
	var grid: Array = []
	for y in range(size.y):
		var row: Array = []
		for x in range(size.x): row.append(fill_tile)
		grid.append(row)
	return grid

static func _apply_environment_rules(grid: Array, base_tile: String, environment: String, terrain_metadata: Dictionary) -> void:
	if grid.is_empty(): return
	var height := grid.size()
	var width := (grid[0] as Array).size()
	match base_tile:
		"shoreline":
			var water_band := int(height * 0.25)
			for y in range(water_band):
				for x in range(width): grid[y][x] = "deep_water"
			var shallow_band := int(height * 0.40)
			for y in range(water_band, shallow_band):
				for x in range(width): grid[y][x] = "shallow_water"
		"forest_edge":
			for y in range(height):
				for x in range(width):
					if x == 0 or y == 0 or x == width - 1 or y == height - 1: grid[y][x] = "forest_edge"
		"sand":
			for y in range(height):
				for x in range(width):
					if y < int(height * 0.10): grid[y][x] = "rock"
	if bool(terrain_metadata.get("contains_pier", false)):
		var pier_x := width / 2
		for y in range(0, min(10, height)): grid[y][pier_x] = "pier"

static func _build_prop_plan(level_design: Dictionary) -> Array:
	var props: Array = []
	var landmarks_v: Variant = level_design.get("landmarks", [])
	if typeof(landmarks_v) == TYPE_ARRAY:
		var idx := 0
		for item in landmarks_v:
			props.append({
				"id": "landmark_%d" % idx, "type": "landmark", "name": String(item),
				"position": {"x": 8 + (idx * 4), "y": 0, "z": 8 + (idx * 3)}
			})
			idx += 1
	return props

static func _build_landmark_nodes(level_design: Dictionary) -> Array:
	var nodes: Array = []
	nodes.append({"id": "entry_point", "kind": "spawn", "direction": String(level_design.get("entry_point", "south"))})
	return nodes
