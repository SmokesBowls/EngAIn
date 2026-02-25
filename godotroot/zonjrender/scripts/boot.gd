extends Node

func _ready() -> void:
	SceneClient.request_failed.connect(_on_api_fail)
	SceneClient.search_results.connect(_on_search)
	SceneClient.scene_loaded.connect(_on_scene_loaded)

	SimClient.sim_failed.connect(_on_sim_fail)
	SimClient.sim_response.connect(_on_sim_response)

	print("[boot] Searching for 'nephilim'...")
	SceneClient.search("nephilim")

	# headless safety: quit after 5s so the process doesn't hang
	get_tree().create_timer(5.0).timeout.connect(func() -> void: get_tree().quit())

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
	print("[boot] sim_response [%s]: %s" % [kind, str(payload).left(500)])
	if kind == "scene/load":
		print("[boot] Scene loaded — issuing 'look' command")
		SimClient.command("look")
