extends Node

@export var headless_timeout_sec: float = 8.0
@export var preferred_scene_id: String = ""
@export var auto_load_on_ready: bool = false
@export var auto_issue_look: bool = true
@export var auto_request_snapshot: bool = true
@onready var chapter_output: RichTextLabel = get_tree().current_scene.get_node_or_null("UI/ChapterOutput")

var _entity_nodes: Dictionary = {}
var _current_scene_id: String = ""
var _current_scene_doc: Dictionary = {}

const SemanticActorScene := preload("res://entities/SemanticActor.tscn")
const DEFAULT_RENDER_PLAN := {
	"render_mode": "planar_sprite",
	"plane_mode": "vertical",
	"size_world": [1.0, 1.8],
	"depth_bias": 0.0,
	"shadow_mode": "projected",
	"collision_profile": "character_medium",
	"interaction_radius": 1.5,
	"flip_x": false,
}

const TYPE_RENDER_PROFILES := {
	"character": {
		"size_world": [1.0, 1.8],
		"collision_profile": "character_medium",
		"shadow_mode": "projected",
	},
	"npc": {
		"size_world": [1.0, 1.8],
		"collision_profile": "character_medium",
		"shadow_mode": "projected",
	},
	"enemy": {
		"size_world": [1.2, 2.0],
		"collision_profile": "character_large",
		"shadow_mode": "projected",
	},
	"item": {
		"size_world": [0.5, 0.5],
		"collision_profile": "item_small",
		"shadow_mode": "off",
		"plane_mode": "ground",
	},
	"building": {
		"size_world": [4.0, 3.0],
		"collision_profile": "building_medium",
		"shadow_mode": "full",
	},
	"trigger": {
		"size_world": [1.0, 1.0],
		"collision_profile": "trigger",
		"shadow_mode": "off",
	},
}


const WORLD_RULES_PATH := "/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/manifests/world_rules.json"

var _world_rules_entities: Dictionary = {}


func _load_world_rules() -> void:
	_world_rules_entities.clear()

	var file := FileAccess.open(WORLD_RULES_PATH, FileAccess.READ)
	if file == null:
		push_error("[world_rules] missing file: %s" % WORLD_RULES_PATH)
		return

	var json := JSON.new()
	var err := json.parse(file.get_as_text())
	if err != OK:
		push_error("[world_rules] JSON parse failed at line %d: %s" % [json.get_error_line(), json.get_error_message()])
		return

	var data = json.data
	if typeof(data) != TYPE_DICTIONARY:
		push_error("[world_rules] root is not a Dictionary")
		return

	var entities = data.get("entities", {})
	if typeof(entities) != TYPE_DICTIONARY:
		push_error("[world_rules] missing entities dictionary")
		return

	_world_rules_entities = entities
	print("[world_rules] Godot loaded entities: ", _world_rules_entities.size())


func _world_rule_entry(entity_id: String) -> Dictionary:
	if _world_rules_entities.has(entity_id):
		return _world_rules_entities[entity_id]

	var lower_id := entity_id.to_lower()
	for key in _world_rules_entities.keys():
		if String(key).to_lower() == lower_id:
			return _world_rules_entities[key]

	return {}


func _is_spawnable_by_world_rules(entity_id: String) -> bool:
	var entry := _world_rule_entry(entity_id)
	if entry.is_empty():
		print("[world_rules] UNKNOWN blocked from spawn: ", entity_id)
		return false

	if not bool(entry.get("spawnable", false)):
		print("[world_rules] non-spawnable blocked: ", entity_id)
		return false

	if String(entry.get("render_as", "none")) == "none":
		print("[world_rules] render_as=none blocked: ", entity_id)
		return false

	return true



func _ready() -> void:
	if Engine.is_editor_hint():
		return
	_load_world_rules()
	await get_tree().process_frame
	if chapter_output:
		chapter_output.text = "UI OUTPUT READY\n"
	
	SceneClient.request_failed.connect(_on_api_fail)
	SceneClient.scenes_listed.connect(_on_scenes_listed)
	SceneClient.scene_loaded.connect(_on_scene_loaded)

	SimClient.sim_failed.connect(_on_sim_fail)
	SimClient.sim_response.connect(_on_sim_response)

	var query_node: LineEdit = get_node_or_null("UI/Control/SearchRow/Query")
	var go_node: Button = get_node_or_null("UI/Control/SearchRow/Go")
	if query_node != null:
		query_node.text_submitted.connect(_on_query_submitted)
		query_node.text = preferred_scene_id
	if go_node != null:
		go_node.pressed.connect(_on_go_pressed)

	if auto_load_on_ready:
		if preferred_scene_id != "":
			print("[boot] Loading preferred scene: %s" % preferred_scene_id)
			SceneClient.load_scene(preferred_scene_id)
		else:
			print("[boot] Listing available scenes...")
			SceneClient.list_scenes()

	if DisplayServer.get_name() == "headless" and headless_timeout_sec > 0.0:
		get_tree().create_timer(headless_timeout_sec).timeout.connect(func() -> void:
			push_warning("Headless safety timeout reached; quitting.")
			get_tree().quit()
		)

func _on_query_submitted(text: String) -> void:
	var scene_id: String = text.strip_edges()
	if scene_id == "":
		SceneClient.list_scenes()
		return

	preferred_scene_id = scene_id
	print("[boot] Manual load requested: %s" % scene_id)
	SceneClient.load_scene(scene_id)

func _on_go_pressed() -> void:
	var query_node: LineEdit = get_node_or_null("UI/Control/SearchRow/Query")
	if query_node == null:
		return
	_on_query_submitted(query_node.text)

func _on_scenes_listed(scenes: Array) -> void:
	print("[boot] list_scenes → %d scenes" % scenes.size())
	if scenes.is_empty():
		push_warning("No scenes available from SceneClient.")
		return

	print("[boot] Scene library available. Waiting for Scene Chooser UI to trigger load.")
	# DISABLED: We no longer auto-load the first scene.
	# var chosen_scene_id: String = preferred_scene_id
	# if chosen_scene_id == "" or not scenes.has(chosen_scene_id):
	# 	chosen_scene_id = String(scenes[0])
	# print("[boot] Fetching scene: %s" % chosen_scene_id)
	# SceneClient.load_scene(chosen_scene_id)

func _on_scene_loaded(scene_id: String, scene: Dictionary) -> void:
	_current_scene_id = scene_id
	print("[boot] Scene payload received from scene server: %s" % scene_id)
	print("[Boot] received payload scene_id: ", scene.get("scene_id", "NO_SCENE_ID"))
	print("[Boot] received payload title: ", scene.get("title", "NO_TITLE"))

	var runtime_scene_doc: Dictionary = _adapt_scene_server_payload_to_runtime_doc(scene_id, scene)
	_current_scene_doc = runtime_scene_doc

	var segs_v: Variant = runtime_scene_doc.get("segments", [])
	var seg_count: int = 0
	if typeof(segs_v) == TYPE_ARRAY:
		seg_count = (segs_v as Array).size()

	print("[boot] Adapted runtime scene doc: %s (%d segments)" % [scene_id, seg_count])

	_apply_environment_from_scene_doc(runtime_scene_doc)

	# DISABLED: Main.gd now directly posts the raw ZONJ object to the server
	# SimClient.load_scene_doc(runtime_scene_doc)

func _on_sim_response(kind: String, payload: Dictionary) -> void:
	var inner: Dictionary = payload

	if payload.has("payload"):
		var payload_v: Variant = payload.get("payload")
		if typeof(payload_v) == TYPE_DICTIONARY:
			inner = payload_v as Dictionary

	match kind:
		"scene/load":
			var sid: String = String(inner.get("scene_id", "?"))
			print("[boot] sim scene/load → %s" % sid)
			print("[boot] forcing look command now...")
			SimClient.command("look")

		"snapshot":
			print("[boot] snapshot received (ignored for actor spawn in this branch)")
		
		"command":
			var cmd_type: String = String(inner.get("type", ""))

			if cmd_type == "result":
				_print_command_result(inner)

				if chapter_output:
					chapter_output.text += String(inner.get("text", "")) + "\n\n"

				_clear_spawned_actors()
				print("[boot] inner keys: ", inner.keys())

				var bridge_v: Variant = inner.get("bridge_entities", null)
				if typeof(bridge_v) == TYPE_ARRAY:
					_spawn_from_bridge_entities(bridge_v as Array)
				else:
									var present_v: Variant = inner.get("entities_present", null)
									if typeof(present_v) == TYPE_ARRAY:
										_spawn_from_id_list(present_v as Array)
									else:
										print("[boot] command result did not include bridge_entities or entities")
			
func _adapt_scene_server_payload_to_runtime_doc(scene_id: String, scene: Dictionary) -> Dictionary:
	var payload = scene
	print("[BOOT_PAYLOAD_KEYS] ", payload.keys())
	print("[BOOT_PAYLOAD_segments] segments=", payload.get("segments", []).size(), " =segments=", payload.get("=segments", []).size())
	print("[BOOT_PAYLOAD_scene_id] ", payload.get("scene_id", payload.get("@id", "NO_ID")))
	print("[BOOT_PAYLOAD_terrain] ", payload.get("terrain_family", payload.get("@terrain_family", "NO_TERRAIN")))
	
	var metadata: Dictionary = scene.get("metadata", {})
	var spawn_commands_v: Variant = scene.get("spawn_commands", [])
	var events_v: Variant = scene.get("events", [])
	var initial_state: Dictionary = scene.get("initial_state", {})

	var entities: Array = []
	if typeof(spawn_commands_v) == TYPE_ARRAY:
		for item_v in spawn_commands_v:
			if typeof(item_v) != TYPE_DICTIONARY:
				continue

			var item: Dictionary = item_v as Dictionary
			var pos_v: Variant = item.get("position", [0.0, 0.0, 0.0])
			var pos_x: float = 0.0
			var pos_y: float = 0.0
			var pos_z: float = 0.0

			if typeof(pos_v) == TYPE_ARRAY:
				var pos_a: Array = pos_v as Array
				if pos_a.size() >= 3:
					pos_x = float(pos_a[0])
					pos_y = float(pos_a[1])
					pos_z = float(pos_a[2])
			elif typeof(pos_v) == TYPE_DICTIONARY:
				var pos_d: Dictionary = pos_v as Dictionary
				pos_x = float(pos_d.get("x", 0.0))
				pos_y = float(pos_d.get("y", 0.0))
				pos_z = float(pos_d.get("z", 0.0))

			entities.append({
				"id": String(item.get("id", "unknown")),
				"name": String(item.get("name", item.get("id", "unknown"))),
				"type": String(item.get("entity_type", "character")),
				"position": {
					"x": pos_x,
					"y": pos_y,
					"z": pos_z,
				},
				"health": float(item.get("health", 100.0)),
				"max_health": float(item.get("max_health", 100.0)),
			})

	var normalized_segments := []

	if payload.has("segments") and typeof(payload["segments"]) == TYPE_ARRAY:
		normalized_segments = payload["segments"]

	if normalized_segments.is_empty() \
	and payload.has("=segments") \
	and typeof(payload["=segments"]) == TYPE_ARRAY:
		normalized_segments = payload["=segments"]

	var segments: Array = normalized_segments.duplicate(true)
	if segments.is_empty() and typeof(events_v) == TYPE_ARRAY:
		for ev_v in events_v:
			if typeof(ev_v) != TYPE_DICTIONARY:
				continue

			var ev: Dictionary = ev_v as Dictionary
			var data_v: Variant = ev.get("data", {})
			var text: String = ""
			if typeof(data_v) == TYPE_DICTIONARY:
				var data_d: Dictionary = data_v as Dictionary
				text = String(data_d.get("text", ""))

			if text == "":
				continue

			segments.append({
				"type": String(ev.get("type", "narration")),
				"actor": String(ev.get("actor", "")),
				"timestamp": int(ev.get("timestamp", 0)),
				"text": text,
			})

	var when_value: String = String(
		scene.get("when",
		metadata.get("when",
		metadata.get("era", "unknown")))
	)

	var where_value: String = String(
		scene.get("where",
		metadata.get("where",
		metadata.get("location", "Realm/Unknown")))
	)

	# Pull region metadata from top-level fields first, then fall back to metadata dict
	var meta_dict: Dictionary = scene.get("metadata", {})
	var region_val:      String = String(scene.get("region",      meta_dict.get("region",      "")))
	var environment_val: String = String(scene.get("environment", meta_dict.get("environment", "")))
	var terrain_fam_val: String = String(scene.get("terrain_family", meta_dict.get("terrain_family", "")))
	var scale_hint_val:  String = String(scene.get("spatial_scale_hint", meta_dict.get("spatial_scale_hint", "")))

	# Extract level_design — top-level field first, metadata fallback
	var level_design_v: Variant = scene.get("level_design", null)
	if typeof(level_design_v) != TYPE_DICTIONARY:
		var meta_v: Variant = scene.get("metadata", null)
		if typeof(meta_v) == TYPE_DICTIONARY:
			level_design_v = (meta_v as Dictionary).get("level_design", null)
	var level_design: Dictionary = {}
	if typeof(level_design_v) == TYPE_DICTIONARY:
		level_design = level_design_v as Dictionary

	print("[BOOT_LEVEL_DESIGN] entry=%s | nav=%s | landmarks=%s" % [
		level_design.get("entry_point", "unknown"),
		level_design.get("navigation_style", "default"),
		level_design.get("landmarks", [])
	])

	return {
		"scene_id": scene_id,
		"@id": scene_id,
		"where": where_value,
		"when": when_value,
		"segments": segments,
		"entities": entities,
		"initial_state": initial_state,
		"region": region_val,
		"environment": environment_val,
		"terrain_family": terrain_fam_val,
		"spatial_scale_hint": scale_hint_val,
		"level_design": level_design,
	}

func _clear_spawned_actors() -> void:
	var actors_root: Node3D = get_tree().current_scene.get_node_or_null("Actors")
	if actors_root == null:
		return

	for child in actors_root.get_children():
		child.queue_free()


func _spawn_from_entity_dict(entities: Dictionary) -> void:
	for eid_v in entities.keys():
		var eid: String = String(eid_v)
		var data_v: Variant = entities.get(eid, {})
		if typeof(data_v) == TYPE_DICTIONARY:
			var data: Dictionary = data_v as Dictionary
			_spawn_entity(eid, data)

func _spawn_from_bridge_entities(items: Array) -> void:
	for item_v in items:
		if typeof(item_v) != TYPE_DICTIONARY:
			continue

		var item: Dictionary = item_v as Dictionary
		var eid: String = String(item.get("entity_id", item.get("name", "unknown")))
		_spawn_entity(eid, item)

func _extract_snapshot_payload(payload: Dictionary) -> Dictionary:
	var snapshot_v: Variant = payload.get("snapshot", null)
	if typeof(snapshot_v) == TYPE_DICTIONARY:
		return snapshot_v as Dictionary

	if payload.has("entities") or payload.has("scene") or payload.has("world"):
		return payload

	return {}

func _spawn_from_id_list(id_list: Array) -> void:
	var filtered: Array = []

	for raw_id in id_list:
		var eid: String = String(raw_id)
		if not _is_spawnable_by_world_rules(eid):
			print("[boot] Skipping non-spawnable: ", eid)
			continue

		filtered.append(eid)

	print("[boot] spawning filtered: ", filtered)

	for eid in filtered:
		if _entity_nodes.has(eid):
			continue

		var idx: int = _entity_nodes.size()
		var pos: Vector3 = Vector3(float(idx) * 2.0, 0.0, 0.0)

		var plan: Dictionary = _build_render_plan(
			eid,
			"character",
			eid,
			pos,
			0.0,
			""
		)
		_spawn_entity(eid, plan)

func _apply_environment_from_scene_doc(scene_doc: Dictionary) -> void:
	var renderer: Node = get_tree().current_scene.get_node_or_null("World/SemanticRenderer")
	if renderer == null:
		push_warning("[boot] SemanticRenderer not found; cannot apply environment")
		return

	if not renderer.has_method("set_environment_layout"):
		print("[boot] pushing env layout...")
		return

	var layout: Dictionary = _build_environment_layout(scene_doc)
	renderer.call("set_environment_layout", layout)
	print("[boot] Environment layout pushed to SemanticRenderer")


# === PROOF-SCALE REGION CONFIG (Valid tile strings only + generator keys) ===
const REGION_CONFIG = {
	"beach":     {"size": Vector2i(48, 48), "terrain": "beach"},      # Generator key
	"coastal":   {"size": Vector2i(48, 48), "terrain": "beach"},      # Generator key
	"mars":      {"size": Vector2i(64, 64), "terrain": "sand"},       # Valid renderer tile
	"forest":    {"size": Vector2i(64, 64), "terrain": "grass"},      # Valid renderer tile
	"valley":    {"size": Vector2i(64, 64), "terrain": "grass"},      # Valid renderer tile
	"default":   {"size": Vector2i(32, 32), "terrain": "grass"}       # Valid renderer tile
}

# === HELPER: Resolve region config from metadata/text ===
func _resolve_region_config(scene: Dictionary) -> Dictionary:
	# Priority 1: explicit terrain_family from game scene JSON (written by pass5)
	var explicit_tf: String = String(scene.get("terrain_family", "")).to_lower().strip_edges()
	if explicit_tf != "" and REGION_CONFIG.has(explicit_tf):
		print("[Boot] terrain_family resolved explicitly: ", explicit_tf)
		return REGION_CONFIG[explicit_tf]

	# Priority 2: explicit environment field mapped to terrain
	var env_to_terrain := {
		"coastal": "beach", "beach": "beach",
		"arid": "mars", "sand": "mars",
		"temperate": "forest", "grass": "forest",
	}
	var explicit_env: String = String(scene.get("environment", "")).to_lower().strip_edges()
	if explicit_env != "" and env_to_terrain.has(explicit_env):
		var tc: String = env_to_terrain[explicit_env]
		print("[Boot] terrain_family resolved from environment '", explicit_env, "': ", tc)
		return REGION_CONFIG.get(tc, REGION_CONFIG["default"])

	# Priority 3: keyword scan of free-text fields (legacy fallback)
	var search_text: String = ""
	for field in ["where", "region", "environment", "biome", "terrain", "location"]:
		var val = scene.get(field, "")
		if val != "": search_text += " " + str(val)

	var look_text = scene.get("text", "")
	if look_text != "":
		search_text += " " + str(look_text)

	var segments = scene.get("segments", scene.get("=segments", []))
	if typeof(segments) == TYPE_ARRAY:
		for seg in segments:
			for seg_field in ["text", "narrative", "content", "look_text", "where", "region"]:
				var seg_val = seg.get(seg_field, "")
				if seg_val != "": search_text += " " + str(seg_val)

	search_text = search_text.to_lower()
	print("[Boot] terrain fallback scan (first 300 chars): ", search_text.substr(0, 300))

	var keyword_map := {
		"coastal": "beach", "beach": "beach", "shore": "beach", "shoreline": "beach",
		"ocean": "beach", "water": "beach", "island": "beach",
		"mars": "mars", "red_dust": "mars", "battlefield": "mars",
		"forest": "forest", "woods": "forest", "valley": "valley",
		"jungle": "forest", "mountain": "forest", "alpine": "forest",
	}

	var matched_key: String = "default"
	for keyword in keyword_map:
		if search_text.contains(keyword):
			matched_key = keyword_map[keyword]
			break

	return REGION_CONFIG.get(matched_key, REGION_CONFIG["default"])

# === HELPER: Build uniform grid (sand, grass, etc.) ===
func _build_region_grid(terrain: String, width: int, height: int) -> Array:
	var grid: Array = []
	for y in range(height):
		var row: Array = []
		for x in range(width):
			row.append(terrain)
		grid.append(row)
	return grid

# === HELPER: Build beach band grid (deep_water → grass) ===
func _build_beach_grid(width: int, height: int) -> Array:
	var grid: Array = []
	for y in range(height):
		var row: Array = []
		for x in range(width):
			var t := "sand"
			var ratio := float(y) / float(max(height - 1, 1))

			if ratio < 0.22:
				t = "deep_water"
			elif ratio < 0.34:
				t = "shallow_water"
			elif ratio < 0.40:
				t = "shoreline"
			elif ratio < 0.72:
				t = "sand"
			else:
				t = "grass"

			row.append(t)
		grid.append(row)
	return grid

# === REPLACEMENT: Routes to correct generator based on terrain type ===
func _build_environment_layout(scene: Dictionary) -> Dictionary:
	var config: Dictionary = _resolve_region_config(scene)
	var dims: Vector2i = config["size"]
	var terrain_type: String = config["terrain"]

	var grid: Array = []
	if terrain_type == "beach":
		grid = _build_beach_grid(dims.x, dims.y)
	else:
		grid = _build_region_grid(terrain_type, dims.x, dims.y)

	print("[Boot] Terrain region resolved: %dx%d (%s) → %d tiles" % [dims.x, dims.y, terrain_type, dims.x * dims.y])
	return {"terrain_grid": grid}

func _spawn_from_snapshot(snapshot: Dictionary) -> void:
	var ents_v: Variant = snapshot.get("entities", {})
	if typeof(ents_v) != TYPE_DICTIONARY:
		return

	var ents: Dictionary = ents_v as Dictionary
	var behavior_snapshot: Dictionary = {}
	var beh_v: Variant = snapshot.get("behavior", {})
	if typeof(beh_v) == TYPE_DICTIONARY:
		behavior_snapshot = beh_v as Dictionary

	for eid_raw in ents.keys():
		var eid: String = String(eid_raw)
		var edata_v: Variant = ents[eid_raw]
		if typeof(edata_v) != TYPE_DICTIONARY:
			continue

		var edata: Dictionary = edata_v as Dictionary
		var pos: Vector3 = _extract_pos3(edata)
		var etype: String = String(edata.get("type", "character"))
		var ename: String = String(edata.get("name", eid))
		var yaw: float = _extract_yaw(eid, edata, behavior_snapshot)
		var asset_ref: String = String(edata.get("asset_ref", ""))

		var plan: Dictionary = _build_render_plan(eid, etype, ename, pos, yaw, asset_ref)

		if _entity_nodes.has(eid):
			var node_existing: Node = _entity_nodes[eid] as Node
			if node_existing != null and node_existing.has_method("apply_render_plan"):
				node_existing.call("apply_render_plan", plan)
		else:
			_spawn_entity(eid, plan)

func _build_render_plan(
	eid: String,
	etype: String,
	ename: String,
	pos: Vector3,
	yaw: float,
	asset_ref: String
) -> Dictionary:
	var plan: Dictionary = DEFAULT_RENDER_PLAN.duplicate(true)

	var profile: Dictionary = TYPE_RENDER_PROFILES.get(etype, {})
	for key in profile.keys():
		plan[key] = profile[key]

	plan["id"] = eid
	plan["display_name"] = ename
	plan["pos_3d"] = [pos.x, pos.y, pos.z]
	plan["yaw"] = yaw

	if asset_ref != "":
		plan["asset_ref"] = asset_ref

	return plan

func _spawn_entity(eid: String, data: Dictionary) -> void:
	var actors_root: Node3D = get_tree().current_scene.get_node_or_null("World/Actors")
	if actors_root == null:
		push_error("Actors node not found")
		return

	var actor: Node = SemanticActorScene.instantiate()
	actors_root.add_child(actor)

	if actor.has_method("apply_entity_data"):
		actor.call("apply_entity_data", eid, data)
	else:
		push_warning("[boot] SemanticActor missing apply_entity_data for %s" % eid)

	print("[boot] Spawned clean actor: %s data=%s" % [eid, JSON.stringify(data)])

func _on_entity_selected(entity_id: String, button_index: int) -> void:
	print("[boot] Entity selected: %s (button %d)" % [entity_id, button_index])

func _on_asset_edit_requested(entity_id: String) -> void:
	print("[boot] Asset edit requested: %s" % entity_id)

func _extract_pos3(edata: Dictionary) -> Vector3:
	var pos_v: Variant = edata.get("position", edata.get("pos", [0.0, 0.0, 0.0]))

	if typeof(pos_v) == TYPE_DICTIONARY:
		var pd: Dictionary = pos_v as Dictionary
		return Vector3(
			float(pd.get("x", 0.0)),
			float(pd.get("y", 0.0)),
			float(pd.get("z", 0.0))
		)

	if typeof(pos_v) == TYPE_ARRAY:
		var pa: Array = pos_v as Array
		if pa.size() >= 3:
			return Vector3(
				float(pa[0]),
				float(pa[1]),
				float(pa[2])
			)

	return Vector3.ZERO

func _extract_yaw(eid: String, edata: Dictionary, behavior_snapshot: Dictionary) -> float:
	if edata.has("yaw"):
		return float(edata["yaw"])

	if behavior_snapshot.has(eid):
		var beh_v: Variant = behavior_snapshot[eid]
		if typeof(beh_v) == TYPE_DICTIONARY:
			var beh: Dictionary = beh_v as Dictionary
			if beh.has("facing_yaw"):
				return float(beh["facing_yaw"])

	var vel_v: Variant = edata.get("velocity", edata.get("vel", [0.0, 0.0, 0.0]))
	if typeof(vel_v) == TYPE_DICTIONARY:
		var vd: Dictionary = vel_v as Dictionary
		var vx: float = float(vd.get("x", 0.0))
		var vz: float = float(vd.get("z", 0.0))
		if abs(vx) + abs(vz) > 0.05:
			return atan2(-vx, -vz)

	if typeof(vel_v) == TYPE_ARRAY:
		var va: Array = vel_v as Array
		if va.size() >= 3:
			var vx2: float = float(va[0])
			var vz2: float = float(va[2])
			if abs(vx2) + abs(vz2) > 0.05:
				return atan2(-vx2, -vz2)

	return 0.0

func _print_command_result(payload: Dictionary) -> void:
	var cmd: String = String(payload.get("command", ""))
	var text: String = String(payload.get("text", ""))
	var scene_id: String = String(payload.get("scene_id", ""))
	var where: String = String(payload.get("where", ""))
	var when_str: String = String(payload.get("when", ""))

	print("")
	print("═══════════════════════════════════════════")
	print("  Command: %s" % cmd)
	if scene_id != "":
		print("  Scene:   %s" % scene_id)
	if where != "":
		print("  Where:   %s" % where)
	if when_str != "":
		print("  When:    %s" % when_str)
	print("───────────────────────────────────────────")
	print("  %s" % text)
	print("═══════════════════════════════════════════")
	print("")

	var output_node: RichTextLabel = get_node_or_null("UI/Control/Body/Output")
	if output_node != null:
		output_node.text = (
			"Command: %s\nScene: %s\nWhere: %s\nWhen: %s\n\n%s"
			% [cmd, scene_id, where, when_str, text]
		)

func _on_api_fail(kind: String, detail: String, status_code: int) -> void:
	push_error("scene_api fail [%s] (%d): %s" % [kind, status_code, detail])

func _on_sim_fail(kind: String, detail: String, status_code: int) -> void:
	push_error("sim_runtime fail [%s] (%d): %s" % [kind, status_code, detail])
