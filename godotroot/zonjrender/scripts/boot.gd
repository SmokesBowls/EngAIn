extends Node

@export var headless_timeout_sec: float = 8.0

func _ready() -> void:
	if Engine.is_editor_hint():
		return

	SceneClient.request_failed.connect(_on_api_fail)
	SceneClient.search_results.connect(_on_search)
	SceneClient.scene_loaded.connect(_on_scene_loaded)

	SimClient.sim_failed.connect(_on_sim_fail)
	SimClient.sim_response.connect(_on_sim_response)

	print("[boot] Searching for 'nephilim'...")
	SceneClient.search("nephilim")

	if DisplayServer.get_name() == "headless":
		if headless_timeout_sec > 0.0:
			get_tree().create_timer(headless_timeout_sec).timeout.connect(func() -> void:
				push_warning("Headless safety timeout reached; quitting.")
				get_tree().quit()
			)

func _on_api_fail(kind: String, detail: String, status_code: int) -> void:
	push_error("scene_api fail [%s] (%d): %s" % [kind, status_code, detail])

func _on_sim_fail(kind: String, detail: String, status_code: int) -> void:
	push_error("sim_runtime fail [%s] (%d): %s" % [kind, status_code, detail])

func _on_search(q: String, hits: Array) -> void:
	print("[boot] Search: '%s' → %d hits" % [q, hits.size()])
	if hits.is_empty():
		push_warning("No hits for query: %s" % q)
		return
	var first: Dictionary = hits[0] as Dictionary
	var sid: String = String(first.get("scene_id", ""))
	print("[boot] Fetching full scene: %s" % sid)
	SceneClient.get_scene(sid)

func _on_scene_loaded(scene_id: String, scene: Dictionary) -> void:
	var segs_v: Variant = scene.get("=segments")
	if typeof(segs_v) != TYPE_ARRAY:
		print("[boot] ⚠ No =segments in scene payload; keys: ", scene.keys())
	else:
		print("[boot] Scene '%s' has %d segments" % [scene_id, (segs_v as Array).size()])

	print("[boot] Loading into sim_runtime...")
	SimClient.load_scene_doc(scene)

func _on_sim_response(kind: String, payload: Dictionary) -> void:
	if kind == "scene/load":
		var sid: String = String(payload.get("scene_id", "?"))
		var segs: int = int(payload.get("segments", 0))
		print("[boot] Scene loaded: %s (%d segments)" % [sid, segs])
		print("[boot] Issuing 'look' command...")
		SimClient.command("look")

	elif kind == "command":
		var cmd_type: String = String(payload.get("type", ""))

		if cmd_type == "result":
			# Real content came back
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

			var entities_v: Variant = payload.get("entities_present")
			if typeof(entities_v) == TYPE_ARRAY:
				var entities: Array = entities_v as Array
				if entities.size() > 0:
					print("  Entities: %s" % ", ".join(PackedStringArray(entities)))

			var total_v: Variant = payload.get("total_segments")
			if total_v != null:
				print("  Segments: %s" % str(total_v))

			print("═══════════════════════════════════════════")
			print("")
		else:
			# Bare ACK (action commands like spawn_entity)
			print("[boot] sim ack: %s" % str(payload).left(200))
