extends Node

@export var headless_timeout_sec: float = 8.0
@export var preferred_scene_id: String = "03_Fist_contact"
@export var auto_load_on_ready: bool = true
@export var auto_issue_look: bool = true
@export var auto_request_snapshot: bool = true
@onready var chapter_output: RichTextLabel = get_tree().current_scene.get_node("UI/ChapterOutput")

var _entity_nodes: Dictionary = {}
var _current_scene_id: String = ""
var _current_scene_doc: Dictionary = {}

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

func _ready() -> void:
	if Engine.is_editor_hint():
		return
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

	var chosen_scene_id: String = preferred_scene_id
	if chosen_scene_id == "" or not scenes.has(chosen_scene_id):
		chosen_scene_id = String(scenes[0])

	print("[boot] Fetching scene: %s" % chosen_scene_id)
	SceneClient.load_scene(chosen_scene_id)

func _on_scene_loaded(scene_id: String, scene: Dictionary) -> void:
	_current_scene_id = scene_id
	print("[boot] Scene payload received from scene server: %s" % scene_id)

	var runtime_scene_doc: Dictionary = _adapt_scene_server_payload_to_runtime_doc(scene_id, scene)
	_current_scene_doc = runtime_scene_doc

	var segs_v: Variant = runtime_scene_doc.get("segments", [])
	var seg_count: int = 0
	if typeof(segs_v) == TYPE_ARRAY:
		seg_count = (segs_v as Array).size()

	print("[boot] Adapted runtime scene doc: %s (%d segments)" % [scene_id, seg_count])
	SimClient.load_scene_doc(runtime_scene_doc)

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

			#if auto_request_snapshot:
				#SimClient.snapshot()

		"snapshot":
			var snapshot: Dictionary = _extract_snapshot_payload(payload)
			if snapshot.is_empty():
				snapshot = _extract_snapshot_payload(inner)

			if not snapshot.is_empty():
				_spawn_from_snapshot(snapshot)
			else:
				print("[boot] snapshot response did not include a usable snapshot payload.")

		"command":
			var cmd_type: String = String(inner.get("type", ""))

			if cmd_type == "result":
				_print_command_result(inner)
				if chapter_output:
					chapter_output.text += String(inner.get("text", "")) + "\n\n"

				var entities_v: Variant = inner.get("entities_present")
				if typeof(entities_v) == TYPE_ARRAY:
					_spawn_from_id_list(entities_v as Array)

				var snapshot2: Dictionary = _extract_snapshot_payload(payload)
				if snapshot2.is_empty():
					snapshot2 = _extract_snapshot_payload(inner)
					print("[boot] sim kind raw: ", kind)
					print("[boot] sim inner raw: ", JSON.stringify(inner))
				if not snapshot2.is_empty():
					_spawn_from_snapshot(snapshot2)
			else:
				print("[boot] sim ack: %s" % str(inner).left(200))

		_:
			print("[boot] Unhandled sim_response kind: %s" % kind)

func _adapt_scene_server_payload_to_runtime_doc(scene_id: String, scene: Dictionary) -> Dictionary:
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

	var segments: Array = []
	if typeof(events_v) == TYPE_ARRAY:
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

	return {
		"scene_id": scene_id,
		"@id": scene_id,
		"where": where_value,
		"when": when_value,
		"segments": segments,
		"entities": entities,
		"initial_state": initial_state,
	}

func _extract_snapshot_payload(payload: Dictionary) -> Dictionary:
	var snapshot_v: Variant = payload.get("snapshot", null)
	if typeof(snapshot_v) == TYPE_DICTIONARY:
		return snapshot_v as Dictionary

	if payload.has("entities") or payload.has("scene") or payload.has("world"):
		return payload

	return {}

func _spawn_from_id_list(entity_ids: Array) -> void:
	for raw_id in entity_ids:
		var eid: String = String(raw_id)
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

func _spawn_entity(eid: String, plan: Dictionary) -> void:
	var world_root: Node3D = get_node_or_null("World")
	if world_root == null:
		push_error("World node not found. Cannot spawn 3.2D entity.")
		return

	print("[boot] Spawned 3.2D entity: %s at %s" % [
		String(plan.get("display_name", eid)),
		String(plan.get("pos_3d", [])),
	])

func _despawn_entity(eid: String) -> void:
	if _entity_nodes.has(eid):
		var node: Node = _entity_nodes[eid] as Node
		if node != null:
			node.queue_free()
		_entity_nodes.erase(eid)
		print("[boot] Despawned: %s" % eid)

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
