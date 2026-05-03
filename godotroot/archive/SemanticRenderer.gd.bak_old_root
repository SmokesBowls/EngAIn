@tool
extends Node3D
# [PATCH transforms-inflight-guard V1]
# [PATCH variant-inference-fix V1]
## SemanticRenderer.gd v2 — Critique-driven rewrite
##
## FIX 1: @tool mode — entities spawn in EDITOR, not just runtime.
##        Inspector button triggers fetch without running game.
## FIX 2: Unshaded materials — semantic colors glow regardless of lighting.
##        No scene lights needed. Red=antagonist, blue=character, etc.
## FIX 3: Dynamic label scaling — readable at any zoom level.
## FIX 4: Dual-speed sync — slow poll for entity lifecycle,
##        fast poll for transforms (when running).

enum RenderMode {VOID, LABELS, PRIMITIVES, SKINS}
@export var render_mode: RenderMode = RenderMode.PRIMITIVES:
	set(v):
		render_mode = v
		_force_fetch() # Rebuild to apply visiblity changes

@export var runtime_url: String = "http://localhost:8080"

## Click this in Inspector to fetch entities WITHOUT running the game
@export var refresh_now: bool = false:
	set(value):
		if value:
			print("[SemanticRenderer] Manual refresh triggered from Inspector")
			_force_fetch()
		refresh_now = false

## Lifecycle poll (spawn/despawn) — slow is fine
@export var lifecycle_interval: float = 2.0

## Transform poll (position updates) — fast for real-time feel
@export var transform_interval: float = 0.1

## Enable transform interpolation during gameplay
@export var enable_fast_transforms: bool = true

# [PATCH auto-frame-camera V1]
@export var auto_frame_camera_on_spawn: bool = true
@export var camera_height: float = 10.0
@export var camera_distance: float = 18.0
@export var camera_look_at_y: float = 1.0

## Path to discover imported .glb or .tscn skins with 'vault_id' metadata
@export_dir var skin_library_path: String = "res://zonjrender/skins"

## Click to re-scan library for vault_id metadata
@export var rescan_library: bool = false:
	set(value):
		if value:
			_rebuild_skin_cache()
		rescan_library = false

var _http_lifecycle: HTTPRequest
var _http_transforms: HTTPRequest
var _current_scene_id: String = ""
var _entity_nodes: Dictionary = {} # entity_id -> Node3D
var _vault_skin_cache: Dictionary = {} # vault_id -> PackedScene
var _pending_fetch: bool = false
var _pending_transforms: bool = false

# Chapter Selector UI
var _http_vault: HTTPRequest
var _http_load: HTTPRequest
var _ui_layer: CanvasLayer
var _chapter_list_visible: bool = false

# Dedicated move HTTP node
var _http_move: HTTPRequest

#Tracking Dictionary
var _last_entity_positions: Dictionary = {} # entity_id -> Vector3
var _suppress_runtime_transform_once: Dictionary = {}


func _ready() -> void:
	_http_lifecycle = HTTPRequest.new()
	_http_lifecycle.timeout = 5.0
	add_child(_http_lifecycle)
	_http_lifecycle.request_completed.connect(_on_lifecycle_snapshot)

	_http_transforms = HTTPRequest.new()
	_http_transforms.timeout = 2.0
	add_child(_http_transforms)
	_http_transforms.request_completed.connect(_on_transform_update)

	_http_vault = HTTPRequest.new()
	add_child(_http_vault)
	_http_vault.request_completed.connect(_on_vault_list_received)

	_http_load = HTTPRequest.new()
	add_child(_http_load)
	_http_load.request_completed.connect(_on_chapter_loaded)

	_http_move = HTTPRequest.new()
	add_child(_http_move)

	# Lifecycle timer (slow — entity spawn/despawn)
	var lifecycle_timer := Timer.new()
	lifecycle_timer.wait_time = lifecycle_interval
	lifecycle_timer.autostart = not Engine.is_editor_hint() # Only auto-poll in game
	lifecycle_timer.timeout.connect(_poll_lifecycle)
	add_child(lifecycle_timer)

	# Transform timer (fast — position updates during gameplay only)
	if enable_fast_transforms:
		var transform_timer := Timer.new()
		transform_timer.wait_time = transform_interval
		transform_timer.autostart = not Engine.is_editor_hint()
		transform_timer.timeout.connect(_poll_transforms)
		add_child(transform_timer)

	# Initial skin scan
	_rebuild_skin_cache()

	# Initial fetch (works in both editor and runtime)
	call_deferred("_poll_lifecycle")
	print("[SemanticRenderer] Ready — %s mode" % ("EDITOR" if Engine.is_editor_hint() else "GAME"))


func _process(delta: float) -> void:
	_update_label_scales()
	_detect_editor_moves(delta)

func _input(event: InputEvent) -> void:
	if Engine.is_editor_hint():
		_update_label_scales()
		return

	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_TAB or event.keycode == KEY_F5:
			_toggle_chapter_selector()
			print("[SemanticRenderer] Chapter selector toggled")
		elif event.keycode == KEY_F1:
			render_mode = RenderMode.VOID
			print("[SemanticRenderer] Mode changed to: ", RenderMode.keys()[render_mode])
		elif event.keycode == KEY_F2:
			render_mode = RenderMode.LABELS
			print("[SemanticRenderer] Mode changed to: ", RenderMode.keys()[render_mode])
		elif event.keycode == KEY_F3:
			render_mode = RenderMode.PRIMITIVES
			print("[SemanticRenderer] Mode changed to: ", RenderMode.keys()[render_mode])
		elif event.keycode == KEY_F4:
			render_mode = RenderMode.SKINS
			print("[SemanticRenderer] Mode changed to: ", RenderMode.keys()[render_mode])


# ═══════════════════════════════════════════════════════════════
# FIX 1: EDITOR + RUNTIME FETCH
# ═══════════════════════════════════════════════════════════════

func _force_fetch() -> void:
	"""Triggered by Inspector button OR force_refresh() call."""
	_current_scene_id = "" # Force rebuild
	_poll_lifecycle()


func _poll_lifecycle() -> void:
	if _pending_fetch or not is_inside_tree():
		return
	_pending_fetch = true
	var err := _http_lifecycle.request("%s/snapshot" % runtime_url)
	if err != OK:
		_pending_fetch = false


func _on_lifecycle_snapshot(result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	_pending_fetch = false

	if result != HTTPRequest.RESULT_SUCCESS or response_code != 200:
		return

	var json := JSON.new()
	if json.parse(body.get_string_from_utf8()) != OK:
		return

	var data: Dictionary = json.data
	if not data is Dictionary:
		return

	# Unwrap protocol envelope (supports EngAIn payload envelope)
	# [PATCH payload-unpack V1]
	var snapshot: Dictionary = {}
	if data.has("payload") and data.get("payload") is Dictionary:
		snapshot = data.get("payload")
	elif data.has("snapshot") and data.get("snapshot") is Dictionary:
		snapshot = data.get("snapshot")
	else:
		snapshot = data
	var scene_id: String = str(snapshot.get("scene_id", ""))
	var bridge_entities: Array = snapshot.get("bridge_entities", [])

	# Also check top-level (bridge fix may put it there)
	if bridge_entities.is_empty() and data.has("bridge_entities"):
		bridge_entities = data.get("bridge_entities", [])

	if bridge_entities.is_empty():
		return

	# Only rebuild if scene changed
	if scene_id == _current_scene_id and not _entity_nodes.is_empty():
		return

	_current_scene_id = scene_id
	_clear_entities()
	_spawn_entities(bridge_entities)

	if auto_frame_camera_on_spawn:
		_frame_camera_to_entities(bridge_entities)

	# In editor, notify the scene tree changed so Inspector updates
	if Engine.is_editor_hint():
		notify_property_list_changed()

# ═══════════════════════════════════════════════════════════════
# FIX 4: FAST TRANSFORM POLLING (game mode only)
# ═══════════════════════════════════════════════════════════════

# AFTER (lightweight - 500 bytes payload)
func _poll_transforms() -> void:
	if Engine.is_editor_hint() or _entity_nodes.is_empty() or _pending_transforms or not is_inside_tree():
		return
	_pending_transforms = true
	var err = _http_transforms.request("%s/transforms" % runtime_url)
	if err != OK:
		_pending_transforms = false

func _on_transform_update(result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	_pending_transforms = false
	if result != HTTPRequest.RESULT_SUCCESS or response_code != 200:
		return

	var json: JSON = JSON.new()
	if json.parse(body.get_string_from_utf8()) != OK:
		return

	var data: Dictionary = json.data as Dictionary

	# Lightweight transforms-only format
	var transforms: Dictionary = data.get("transforms", {}) as Dictionary
	if transforms.is_empty():
		return

	# Update positions only — no spawn/despawn
	for eid in transforms:
		if not _entity_nodes.has(eid):
			continue

		var node: Node3D = _entity_nodes[eid] as Node3D
		var pos_data: Dictionary = transforms[eid] as Dictionary
		var target_pos: Vector3 = Vector3(
			float(pos_data.get("x", node.position.x)),
			float(pos_data.get("y", node.position.y)),
			float(pos_data.get("z", node.position.z))
		)

		# Apply with "runtime wins" rule
		_apply_runtime_transform(str(eid), target_pos)

# ═══════════════════════════════════════════════════════════════
# ENTITY SPAWNING
# ═══════════════════════════════════════════════════════════════

func _clear_entities() -> void:
	for eid in _entity_nodes:
		var node: Node3D = _entity_nodes[eid]
		if is_instance_valid(node):
			node.queue_free()
	_entity_nodes.clear()
	_last_entity_positions.clear()


# ═══════════════════════════════════════════════════════════════
# METADATA BRIDGE: Skin Resolution
# ═══════════════════════════════════════════════════════════════

func _rebuild_skin_cache() -> void:
	"""Scan skin_library_path for scenes with vault_id metadata."""
	_vault_skin_cache.clear()
	if skin_library_path.is_empty():
		return

	var dir := DirAccess.open(skin_library_path)
	if not dir:
		print("[SemanticRenderer] Library path not found: %s" % skin_library_path)
		return

	dir.list_dir_begin()
	var file_name = dir.get_next()
	while file_name != "":
		if not dir.current_is_dir() and (file_name.ends_with(".tscn") or file_name.ends_with(".glb")):
			var full_path = skin_library_path + "/" + file_name
			var scene := load(full_path) as PackedScene
			if scene:
				var vid = _find_vault_id_in_scene(scene)
				if not vid.is_empty():
					_vault_skin_cache[vid] = scene
					print("[SemanticRenderer] Linked vault_id '%s' -> %s" % [vid, file_name])
		file_name = dir.get_next()
	
	print("[SemanticRenderer] Skin cache rebuilt: %d matches" % _vault_skin_cache.size())


func _find_vault_id_in_scene(scene: PackedScene) -> String:
	"""Instantiate briefly to check metadata (glTF extras)."""
	var node = scene.instantiate()
	var vid = ""
	
	# Check root node
	if node.has_meta("vault_id"):
		vid = str(node.get_meta("vault_id"))
	elif node.has_meta("extras") and node.get_meta("extras") is Dictionary:
		# glTF importer often puts 'extras' as a dict
		var extras = node.get_meta("extras")
		vid = str(extras.get("vault_id", ""))
	
	node.free()
	return vid


func _spawn_entities(entities: Array) -> void:
	for ent_data in entities:
		if not ent_data is Dictionary:
			continue

		var presence: String = ent_data.get("presence", "visible")
		# Only render if visible/active
		if presence == "hidden" or presence == "planned":
			continue

		var eid: String = str(ent_data.get("entity_id", "unknown"))
		var vault_id: String = str(ent_data.get("vault_id", ""))
		var entity_type: String = str(ent_data.get("entity_type", "generic"))
		var mesh_type: String = str(ent_data.get("placeholder_mesh", "cube"))
		var color_data: Dictionary = ent_data.get("color", {"r": 1.0, "g": 0.0, "b": 1.0})
		var transform_data: Dictionary = ent_data.get("transform", {})
		var entity_name: String = str(ent_data.get("name", eid))
		var concept: String = str(ent_data.get("zw_concept", "unknown"))
		var ap_profile: String = str(ent_data.get("ap_profile", ""))
		var tags: Array = ent_data.get("semantic_tags", [])

		# Position + scale
		var pos_data: Dictionary = transform_data.get("position", {"x": 0, "y": 0, "z": 0})
		var scl_data: Dictionary = transform_data.get("scale", {"x": 1, "y": 1, "z": 1})

		var pos := Vector3(
			float(pos_data.get("x", 0)),
			float(pos_data.get("y", 0)),
			float(pos_data.get("z", 0))
		)
		var scl := Vector3(
			float(scl_data.get("x", 1)),
			float(scl_data.get("y", 1)),
			float(scl_data.get("z", 1))
		)

		var color := Color(
			float(color_data.get("r", 1.0)),
			float(color_data.get("g", 0.0)),
			float(color_data.get("b", 1.0))
		)

		# Root node
		var entity_root := Node3D.new()
		entity_root.name = "BridgeEntity_%s" % eid
		entity_root.position = pos

		# Store metadata as node meta (accessible in Inspector)
		entity_root.set_meta("entity_id", eid)
		entity_root.set_meta("vault_id", vault_id)
		entity_root.set_meta("entity_type", entity_type)
		entity_root.set_meta("zw_concept", concept)
		entity_root.set_meta("ap_profile", ap_profile)
		entity_root.set_meta("semantic_tags", ",".join(tags))

		# BRIDGE LOGIC: High-fidelity Skin vs. Placeholder
		var spawned_skin: Node3D = null
		if not vault_id.is_empty() and _vault_skin_cache.has(vault_id):
			var skin_scene: PackedScene = _vault_skin_cache[vault_id]
			spawned_skin = skin_scene.instantiate() as Node3D
			entity_root.add_child(spawned_skin)
			print("[SemanticRenderer] Resolved skin for vault_id: %s" % vault_id)
		else:
			# FIX 2: Unshaded mesh
			var mesh_instance := _create_unshaded_mesh(mesh_type, scl, color)
			entity_root.add_child(mesh_instance)
			if Engine.is_editor_hint():
				mesh_instance.owner = get_tree().edited_scene_root
			spawned_skin = mesh_instance

		# FIX 3: Dynamic label
		var label := _create_label(entity_name, concept, ap_profile, color)
		label.position.y = scl.y + 0.3
		entity_root.add_child(label)
		if Engine.is_editor_hint():
			label.owner = get_tree().edited_scene_root

		_apply_render_mode_to_entity(entity_root)

		add_child(entity_root)
		if Engine.is_editor_hint():
			entity_root.owner = get_tree().edited_scene_root

		_entity_nodes[eid] = entity_root
		_last_entity_positions[eid] = entity_root.global_position # ← NEW

	print("[SemanticRenderer] Spawned %d entities (%s mode)" % [
		_entity_nodes.size(),
		"EDITOR" if Engine.is_editor_hint() else "GAME"
	])

func _apply_render_mode_to_entity(node: Node3D) -> void:
	var label = node.get_node_or_null("Label")
	var mesh = node.get_node_or_null("Mesh")
	var skin: Node3D = null
	for child in node.get_children():
		if child != label and child != mesh:
			skin = child
			break
	
	match render_mode:
		RenderMode.VOID:
			if label: label.visible = false
			if mesh: mesh.visible = false
			if skin: skin.visible = false
		RenderMode.LABELS:
			if label: label.visible = true
			if mesh: mesh.visible = false
			if skin: skin.visible = false
		RenderMode.PRIMITIVES:
			if label: label.visible = true
			if mesh: mesh.visible = true
			if skin: skin.visible = false
		RenderMode.SKINS:
			if label: label.visible = true
			if skin:
				skin.visible = true
				if mesh: mesh.visible = false
			else:
				if mesh: mesh.visible = true


# ═══════════════════════════════════════════════════════════════
# FIX 2: UNSHADED MATERIALS
# ═══════════════════════════════════════════════════════════════

func _create_unshaded_mesh(mesh_type: String, scl: Vector3, color: Color) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	mi.name = "Mesh"

	match mesh_type:
		"capsule":
			var capsule := CapsuleMesh.new()
			capsule.radius = scl.x * 0.5
			capsule.height = scl.y
			mi.mesh = capsule
		"sphere":
			var sphere := SphereMesh.new()
			sphere.radius = scl.x * 0.5
			sphere.height = scl.y
			mi.mesh = sphere
		"cylinder":
			var cylinder := CylinderMesh.new()
			cylinder.top_radius = scl.x * 0.5
			cylinder.bottom_radius = scl.x * 0.5
			cylinder.height = scl.y
			mi.mesh = cylinder
		"plane":
			var plane := PlaneMesh.new()
			plane.size = Vector2(scl.x, scl.z)
			mi.mesh = plane
		_: # "cube"
			var box := BoxMesh.new()
			box.size = scl
			mi.mesh = box

	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.albedo_color = color
	mat.emission_enabled = true
	mat.emission = color
	mat.emission_energy_multiplier = 0.4
	mi.material_override = mat
	mi.position.y = scl.y * 0.5
	return mi


# ═══════════════════════════════════════════════════════════════
# FIX 3: DYNAMIC LABELS
# ═══════════════════════════════════════════════════════════════

func _create_label(entity_name: String, concept: String, ap_profile: String, color: Color) -> Label3D:
	var label := Label3D.new()
	label.name = "Label"
	var text_parts := [entity_name]
	if concept != "unknown" and concept != entity_name.to_lower():
		text_parts.append("[%s]" % concept)
	if ap_profile and ap_profile != "generic_static":
		text_parts.append("(%s)" % ap_profile)
	label.text = "\n".join(text_parts)
	label.font_size = 32
	label.modulate = Color(color.r * 0.8 + 0.2, color.g * 0.8 + 0.2, color.b * 0.8 + 0.2)
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	label.no_depth_test = true
	label.outline_size = 6
	label.outline_modulate = Color(0, 0, 0, 0.8)
	label.pixel_size = 0.005
	return label


func _update_label_scales() -> void:
	var camera := EditorInterface.get_editor_viewport_3d(0).get_camera_3d() if Engine.is_editor_hint() else get_viewport().get_camera_3d()
	if not camera: return
	var cam_pos := camera.global_position
	for eid in _entity_nodes:
		var node: Node3D = _entity_nodes[eid]
		if not is_instance_valid(node): continue
		var label := node.get_node_or_null("Label")
		if label and label is Label3D:
			var dist := cam_pos.distance_to(node.global_position)
			label.pixel_size = clampf(dist * 0.002, 0.003, 0.02)


func force_refresh() -> void:
	_force_fetch()

func _frame_camera_to_entities(ents: Array) -> void:
	if ents.is_empty(): return
	var pts: Array[Vector3] = []
	for e in ents:
		if not (e is Dictionary): continue
		var posd: Dictionary = {}
		if e.has("position") and e.get("position") is Dictionary:
			posd = e.get("position")
		elif e.has("transform") and e.get("transform") is Dictionary:
			var tr: Dictionary = e.get("transform")
			if tr.has("position") and tr.get("position") is Dictionary:
				posd = tr.get("position")
		if posd.is_empty(): continue
		pts.append(Vector3(float(posd.get("x", 0.0)), float(posd.get("y", 0.0)), float(posd.get("z", 0.0))))
	if pts.is_empty(): return
	var center := Vector3.ZERO
	for p in pts: center += p
	center /= float(pts.size())
	var radius := 1.0
	for p in pts: radius = max(radius, center.distance_to(p))
	var cam: Camera3D = _get_primary_camera()
	if cam == null: return
	var look := center + Vector3(0.0, camera_look_at_y, 0.0)
	var dist: float = max(camera_distance, radius * 1.6)
	var h: float = max(camera_height, radius * 0.6 + 2.0)
	cam.global_position = look + Vector3(0.0, h, dist)
	cam.look_at(look, Vector3.UP)


func _get_primary_camera() -> Camera3D:
	var cam: Camera3D = get_viewport().get_camera_3d()
	if cam: return cam
	var root := get_tree().current_scene
	if root:
		var cams := root.find_children("*", "Camera3D", true, false)
		if cams.size() > 0: return cams[0] as Camera3D
	return null

# ═══════════════════════════════════════════════════════════════
# CHAPTER SELECTOR UI
# ═══════════════════════════════════════════════════════════════

func _toggle_chapter_selector() -> void:
	_chapter_list_visible = !_chapter_list_visible
	if _chapter_list_visible:
		_show_chapter_ui()
		_fetch_vault_list()
	else:
		_hide_chapter_ui()

func _fetch_vault_list() -> void:
	if not is_inside_tree(): return
	var url := runtime_url + "/vault/search?q=&limit=200"
	_http_vault.request(url)

func _on_vault_list_received(result: int, response_code: int, headers: PackedStringArray, body: PackedByteArray) -> void:
	if response_code != 200: return
	var json = JSON.parse_string(body.get_string_from_utf8())
	if json and json.has("hits"):
		_populate_chapter_list(json["hits"])

func _show_chapter_ui() -> void:
	if _ui_layer == null:
		_ui_layer = CanvasLayer.new()
		_ui_layer.name = "ChapterSelector"
		add_child(_ui_layer)
		
	if not _ui_layer.has_node("ChapterPanel"):
		var panel = PanelContainer.new()
		panel.name = "ChapterPanel"
		panel.custom_minimum_size = Vector2(400, 600)
		panel.set_anchors_and_offsets_preset(Control.PRESET_TOP_RIGHT, Control.PRESET_MODE_MINSIZE, 20)
		panel.position.y += 50
		_ui_layer.add_child(panel)
		
		var vbox = VBoxContainer.new()
		vbox.name = "ChapterVBox"
		panel.add_child(vbox)
		
		var title = Label.new()
		title.text = "VAULT CHAPTER SELECTOR"
		title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		vbox.add_child(title)
		
		var scroll = ScrollContainer.new()
		scroll.name = "ScrollContainer"
		scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
		vbox.add_child(scroll)
		
		var list = VBoxContainer.new()
		list.name = "ChapterList"
		scroll.add_child(list)
		
		var close_btn = Button.new()
		close_btn.text = "CLOSE"
		close_btn.pressed.connect(_toggle_chapter_selector)
		vbox.add_child(close_btn)
	
	_ui_layer.visible = true
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE

func _hide_chapter_ui() -> void:
	if _ui_layer:
		_ui_layer.visible = false
	Input.mouse_mode = Input.MOUSE_MODE_CAPTURED

func _populate_chapter_list(hits: Array) -> void:
	if _ui_layer == null:
		return

	var list = _ui_layer.get_node("ChapterPanel/ChapterVBox/ScrollContainer/ChapterList")
	for child in list.get_children():
		child.queue_free()

	for hit in hits:
		var scene_id := str(hit.get("scene_id", ""))
		if scene_id == "":
			continue

		var hbox = HBoxContainer.new()
		list.add_child(hbox)

		var btn = Button.new()
		btn.text = scene_id
		btn.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		btn.alignment = HORIZONTAL_ALIGNMENT_LEFT
		btn.pressed.connect(_load_chapter.bind(scene_id))
		hbox.add_child(btn)

		var meta = Label.new()
		meta.text = "E:%d S:%d" % [int(hit.get("entity_count", 0)), int(hit.get("segment_count", 0))]
		meta.modulate = Color(0.7, 0.7, 0.7)
		hbox.add_child(meta)

func _load_chapter(scene_id: String) -> void:
	if not is_inside_tree(): return
	print("[UI] Loading chapter: ", scene_id)
	var url := runtime_url + "/scene/load"
	var headers := ["Content-Type: application/json"]
	var body := JSON.stringify({"scene_id": scene_id})
	_http_load.request(url, headers, HTTPClient.METHOD_POST, body)
	_toggle_chapter_selector()

func _on_chapter_loaded(result: int, response_code: int, headers: PackedStringArray, body: PackedByteArray) -> void:
	if response_code == 200:
		print("[UI] Chapter loaded successfully")
		_force_fetch()
	else:
		push_error("[UI] Failed to load chapter: %d" % response_code)


func _detect_editor_moves(delta: float) -> void:
	for eid in _entity_nodes.keys():
		var node := _entity_nodes[eid] as Node3D
		if node == null:
			continue

		var prev_pos: Vector3 = _last_entity_positions.get(eid, node.global_position)
		var curr_pos: Vector3 = node.global_position

		# If you moved its gizmo / transform locally
		if prev_pos.distance_to(curr_pos) > 0.01:
			_last_entity_positions[eid] = curr_pos
			_send_move_to_runtime(eid, curr_pos)


func _send_move_to_runtime(eid: String, pos: Vector3) -> void:
	if not is_inside_tree() or _http_move == null:
		return
	
	# If we are already busy, skip this frame to prevent congestion
	if _http_move.get_http_client_status() != HTTPClient.STATUS_DISCONNECTED:
		return

	var payload: Dictionary = {
		"command": "move_entity",
		"entity_id": eid,
		"pos": [pos.x, pos.y, pos.z]
	}
	var headers: PackedStringArray = PackedStringArray(["Content-Type: application/json"])
	var json: String = JSON.stringify(payload)

	var err := _http_move.request(runtime_url + "/command", headers, HTTPClient.METHOD_POST, json)
	if err != OK:
		push_warning("[SemanticRenderer] move request failed to start: %s" % err)
		return

	# Suppression: ignore the very next poll so the gizmo doesn't "snap back"
	_suppress_runtime_transform_once[eid] = true


func _apply_runtime_transform(eid: String, pos: Vector3) -> void:
	if _suppress_runtime_transform_once.get(eid, false):
		_suppress_runtime_transform_once[eid] = false
		return

	var node = _entity_nodes.get(eid, null)
	if node == null:
		return

	# Direct apply (or lerp if you prefer smoothness)
	node.position = node.position.lerp(pos, 0.3)
	_last_entity_positions[eid] = node.global_position
