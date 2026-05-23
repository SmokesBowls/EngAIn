extends Node3D

@onready var world: Node3D = $World
@onready var camera_rig: Node3D = $World/CameraRig
@onready var camera_3d: Camera3D = $World/CameraRig/Camera3D
@onready var semantic_renderer: Node3D = $World/SemanticRenderer
@onready var actors: Node3D = $World/Actors
@onready var ui: Node = $UI

var scene_chosen := false
var dragon_spawned := false
var world_ready := false
var chooser_ui: CanvasLayer
var active_asset_manifest: Dictionary = {}

# Populated by _build_scene_chooser(); keyed by scene_id from scene_index.json.
# Each value is the full registry entry dict (scene_id, display_title, cache_file_path, …).
var _scene_registry: Dictionary = {}

# === SPATIAL CONTRACT ===
var playable_bounds: AABB = AABB()
var camera_bounds: AABB = AABB()
var _bounds_initialized: bool = false

func _clamp_to_aabb(pos: Vector3, bounds: AABB) -> Vector3:
	return Vector3(
		clamp(pos.x, bounds.position.x, bounds.position.x + bounds.size.x),
		clamp(pos.y, bounds.position.y, bounds.position.y + bounds.size.y),
		clamp(pos.z, bounds.position.z, bounds.position.z + bounds.size.z)
	)

func _generate_fallback_bounds_from_renderer() -> void:
	if semantic_renderer == null:
		push_warning("[Main] SemanticRenderer missing for bounds generation")
		return

	var grid: Array = semantic_renderer.terrain_grid
	if grid.is_empty():
		push_warning("[Main] terrain_grid empty")
		return

	var rows: int = grid.size()
	var cols: int = (grid[0] as Array).size()
	var tile_size: float = semantic_renderer.CELL_SIZE

	var width: float = float(cols) * tile_size
	var depth: float = float(rows) * tile_size

	playable_bounds = AABB(
		Vector3(-width * 0.5, -1.0, -depth * 0.5),
		Vector3(width, 8.0, depth)
	)

	camera_bounds = AABB(
		Vector3((-width * 0.5) - tile_size, -6.0, (-depth * 0.5) - tile_size),
		Vector3(width + tile_size * 2.0, 24.0, depth + tile_size * 2.0)
	)

	_bounds_initialized = true
	print("[Main] Renderer-derived centered bounds initialized")
	print("[Main] Playable bounds: ", playable_bounds)

var move_speed := 10.0
var vertical_speed := 8.0
var mouse_sensitivity := 0.0025
var yaw := 0.0
var pitch := 0.0

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
		push_error("[world_rules] parse failed")
		return

	var data = json.data
	if typeof(data) != TYPE_DICTIONARY:
		push_error("[world_rules] invalid root")
		return

	_world_rules_entities = data.get("entities", {})


func _is_spawnable_by_world_rules(entity_id: String) -> bool:
	if _world_rules_entities.has(entity_id):
		var entry = _world_rules_entities[entity_id]

		if not bool(entry.get("spawnable", false)):
			return false

		if String(entry.get("render_as", "none")) == "none":
			return false

		return true

	var lower_id := entity_id.to_lower()

	for key in _world_rules_entities.keys():
		if String(key).to_lower() == lower_id:
			var entry = _world_rules_entities[key]

			if not bool(entry.get("spawnable", false)):
				return false

			if String(entry.get("render_as", "none")) == "none":
				return false

			return true

	print("[world_rules] UNKNOWN blocked from spawn: ", entity_id)
	return false

func _ready() -> void:
	_load_world_rules()
	print("[Main] Loaded")
	print("[Main] World ok: ", world != null)
	print("[Main] Camera ok: ", camera_3d != null)
	print("[Main] SemanticRenderer ok: ", semantic_renderer != null)
	print("[Main] Actors ok: ", actors != null)
	print("[Main] UI ok: ", ui != null)
	if camera_3d != null:
		camera_3d.current = true
	Input.set_mouse_mode(Input.MOUSE_MODE_VISIBLE)
	_build_scene_chooser()

func _build_scene_chooser() -> void:
	chooser_ui = CanvasLayer.new()
	chooser_ui.name = "SceneChooserUI"
	add_child(chooser_ui)

	var panel := Panel.new()
	panel.position = Vector2(40, 80)
	panel.size = Vector2(420, 520)
	chooser_ui.add_child(panel)

	var scroll := ScrollContainer.new()
	scroll.set_anchors_preset(Control.PRESET_FULL_RECT)
	scroll.offset_left = 10
	scroll.offset_top = 10
	scroll.offset_right = -10
	scroll.offset_bottom = -10
	panel.add_child(scroll)

	var vbox := VBoxContainer.new()
	vbox.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(vbox)

	var scene_chooser_label := Label.new()
	scene_chooser_label.text = "EngAIn: Select a Scene"
	scene_chooser_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	vbox.add_child(scene_chooser_label)

	var manifest_path := "/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/manifests/engain_manifest.json"
	var mfile := FileAccess.open(manifest_path, FileAccess.READ)
	if not mfile:
		print("[Main] Failed to open engain_manifest.json")
		return

	var mjson := JSON.new()
	if mjson.parse(mfile.get_as_text()) != OK:
		print("[Main] Failed to parse engain_manifest.json")
		return
		
	var manifest = mjson.data
	
	# Load asset manifest
	var active_asset_pack = manifest.get("active", {}).get("asset_pack", "")
	var asset_manifest_path = manifest.get("asset_packs", {}).get(active_asset_pack, {}).get("manifest", "")
	if asset_manifest_path != "":
		var afile = FileAccess.open(asset_manifest_path, FileAccess.READ)
		if afile:
			var ajson = JSON.new()
			if ajson.parse(afile.get_as_text()) == OK:
				active_asset_manifest = ajson.data
				print("[Main] Loaded active asset manifest for: ", active_asset_pack)

	var active_lib = manifest.get("active", {}).get("scene_library", "")
	var index_path = manifest.get("scene_libraries", {}).get(active_lib, {}).get("index", "")
	
	var file := FileAccess.open(index_path, FileAccess.READ)
	if not file:
		print("[Main] Failed to open scene_index.json")
		return

	var json := JSON.new()
	var err := json.parse(file.get_as_text())
	if err != OK:
		print("[Main] Failed to parse scene_index.json")
		return

	var data = json.data
	if typeof(data) == TYPE_DICTIONARY and (data.has("scenes") or data.has("active_scenes")):
		_scene_registry.clear()
		var loaded_count := 0
		var scene_list: Array = data.get("scenes", data.get("active_scenes", []))
		for entry in scene_list:
			# Support both index schemas: new (id/file/name) and legacy (scene_id/cache_file_path/display_title)
			var sid  := String(entry.get("scene_id", entry.get("id", "")))
			var path := String(entry.get("cache_file_path", entry.get("file", "")))
			var display_title := String(entry.get("display_title", entry.get("name", sid)))
			if sid.is_empty() or path.is_empty():
				continue
			# Normalize to canonical field names so _on_scene_selected always finds them
			var normalized: Dictionary = entry.duplicate()
			normalized["scene_id"] = sid
			normalized["cache_file_path"] = path
			normalized["display_title"] = display_title
			_scene_registry[sid] = normalized
			var btn := Button.new()
			btn.text = display_title
			btn.pressed.connect(_on_scene_selected.bind(sid))
			vbox.add_child(btn)
			loaded_count += 1
		print("[Main] Scene registry loaded: %d scenes" % loaded_count)

func _on_scene_selected(scene_id: String) -> void:
	# --- Registry lookup: no filename guessing allowed ---
	if not _scene_registry.has(scene_id):
		push_error("[Main] FATAL: scene_id not found in registry: ", scene_id)
		return

	var entry: Dictionary = _scene_registry[scene_id]
	var scene_file := String(entry.get("cache_file_path", ""))

	print("[CHOOSER] clicked file=", scene_file)

	# --- Hard file-existence check: halt on missing, no silent fallback ---
	if not FileAccess.file_exists(scene_file):
		push_error("[Main] FATAL: Selected scene file missing: ", scene_file)
		return

	var file := FileAccess.open(scene_file, FileAccess.READ)
	if file == null:
		push_error("[Main] FATAL: Could not open scene file: ", scene_file)
		return

	var txt := file.get_as_text()
	var json := JSON.new()
	if json.parse(txt) != OK:
		push_error("[Main] FATAL: JSON parse failed for: ", scene_file)
		return

	# All checks passed — commit to loading this scene
	scene_chosen = true
	chooser_ui.visible = false

	var scene_data: Dictionary = json.data
	var payload := normalize_scene_payload(scene_data, scene_id)

	print("[Main] POSTing normalized scene to 8080/scene/load — id=", payload.get("scene_id", scene_id))
	SimClient._post_json("scene/load", "/scene/load", payload)

	SceneClient.scene_loaded.emit(payload.get("scene_id", scene_id), payload)

	Input.set_mouse_mode(Input.MOUSE_MODE_CAPTURED)

	get_tree().create_timer(1.0).timeout.connect(_fetch_snapshot)

func normalize_scene_payload(raw: Dictionary, fallback_id: String) -> Dictionary:
	var scene := raw.duplicate(true)

	if not scene.has("scene_id"):
		if scene.has("id"):
			scene["scene_id"] = str(scene["id"])
		elif scene.has("@id"):
			scene["scene_id"] = str(scene["@id"])
		else:
			scene["scene_id"] = fallback_id

	if not scene.has("title"):
		scene["title"] = str(scene["scene_id"]).replace("_", " ")

	if not scene.has("segments"):
		if scene.has("events"):
			scene["segments"] = scene["events"]
		else:
			scene["segments"] = []

	if not scene.has("entities"):
		scene["entities"] = []

	if not scene.has("events"):
		scene["events"] = scene["segments"]

	return scene

func _fetch_snapshot() -> void:
	var http = HTTPRequest.new()
	add_child(http)
	http.request_completed.connect(_on_snapshot_received)
	# ✅ FETCH FROM ENGAIn ENGINE (port 8090), NOT sim_runtime (8080)
	var error = http.request("http://127.0.0.1:8080/snapshot")
	if error != OK:
		print("[Main] HTTP request failed: ", error)

func _on_snapshot_received(result: int, code: int, headers: PackedStringArray, body: PackedByteArray) -> void:
	if code != 200:
		print("[Main] Snapshot fetch failed, code: ", code)
		return
	
	if not scene_chosen:
		print("[Main] Snapshot ignored until Scene Chooser selects a scene.")
		return
	
	var txt = body.get_string_from_utf8()
	var data = JSON.parse_string(txt)
	if typeof(data) != TYPE_DICTIONARY:
		print("[Main] Snapshot parse failed")
		return
	
	var payload = data.get("payload", {})
	var scene_id = payload.get("scene_id", "unknown")
	print("[Main] Scene: ", scene_id)
	
	# Prefer authoritative entities_present from look-command pipeline
	var entities_present = payload.get("entities_present", [])

	var bridge_entities: Array = []

	if typeof(entities_present) == TYPE_ARRAY and not entities_present.is_empty():
		print("[Main] Using authoritative entities_present: ", entities_present.size())

		var idx := 0

		for raw_id in entities_present:
			var eid := String(raw_id)

			if not _is_spawnable_by_world_rules(eid):
				print("[Main] Skipping non-spawnable:", eid)
				continue

			bridge_entities.append({
				"entity_id": eid,
				"type": "character",
				"position": {
					"x": float((idx % 4) * 3),
					"y": 0.0,
					"z": float(idx / 4) * 3
				},
				"transform": {
					"scale": {
						"x": 0.5,
						"y": 1.8,
						"z": 0.5
					}
				},
				"color": {
					"r": 0.2,
					"g": 0.6,
					"b": 1.0
				}
			})

			idx += 1

	else:
		bridge_entities = payload.get("bridge_entities", [])
		print("[Main] Fallback bridge entities count: ", bridge_entities.size())

	if bridge_entities.is_empty():
		print("[Main] WARNING: No renderable entities found!")
		print("[Main] Available keys: ", payload.keys())
		return
	
	# Clear existing actors
	for child in actors.get_children():
		child.queue_free()
	
	# Spawn each bridge entity with its ACTUAL position
	for entity_data in bridge_entities:
		var eid: String = String(entity_data.get("entity_id", ""))
		if not _is_spawnable_by_world_rules(eid):
			print("[Main] Skipping non-spawnable:", eid)
			continue

		_spawn_bridge_entity(entity_data)
		
	if not _bounds_initialized:
		_generate_fallback_bounds_from_renderer()

	_inject_entities_into_renderer(bridge_entities)
	_on_world_built()

func _on_world_built():
	world_ready = true

func _inject_entities_into_renderer(entities: Array) -> void:
	var rt := semantic_renderer.get_node_or_null("RuntimeEntities")
	if rt == null:
		push_warning("[Main] SemanticRenderer/RuntimeEntities not found — skipping entity injection")
		return

	for entity_data in entities:
		var eid: String = String(entity_data.get("entity_id", ""))
		if not _is_spawnable_by_world_rules(eid):
			continue

		# Skip if the asset-manifest path already placed this entity in actors
		if actors.get_node_or_null(eid) != null:
			continue

		# Skip if already injected (e.g. snapshot polled twice)
		if rt.get_node_or_null(eid) != null:
			continue

		var pd = entity_data.get("position", {})
		var pos := Vector3(float(pd.get("x", 0.0)), float(pd.get("y", 0.0)), float(pd.get("z", 0.0)))

		var sd = entity_data.get("transform", {}).get("scale", {"x": 0.25, "y": 0.9, "z": 0.25})
		var scale := Vector3(float(sd.get("x", 0.25)), float(sd.get("y", 0.9)), float(sd.get("z", 0.25)))

		var cd = entity_data.get("color", {"r": 0.2, "g": 0.6, "b": 1.0})
		var color := Color(float(cd.get("r", 0.2)), float(cd.get("g", 0.6)), float(cd.get("b", 1.0)))

		var marker := MeshInstance3D.new()
		marker.name = eid
		var cap := CapsuleMesh.new()
		cap.radius = scale.x
		cap.height = scale.y * 2.0
		marker.mesh = cap
		var mat := StandardMaterial3D.new()
		mat.albedo_color = color
		marker.material_override = mat

		var original_pos: Vector3 = pos

		if _bounds_initialized:
			pos = _clamp_to_aabb(pos, playable_bounds)
			if pos != original_pos:
				print("[Main] Clamped actor ", eid, " from ", original_pos, " to ", pos)

		marker.position = pos
		rt.add_child(marker)
		print("[Main] Injected into renderer: ", eid, " at ", pos)

func _spawn_bridge_entity(data: Dictionary) -> void:  # ✅ FIXED: Added 'data' parameter
	var entity_id = data.get("entity_id", "unknown")
	var entity_type = data.get("type", "unknown")
	var pos_data = data.get("position", {})
	var pos = Vector3(
		pos_data.get("x", 0.0),
		pos_data.get("y", 0.0), 
		pos_data.get("z", 0.0)
	)
	var color_data = data.get("color", {"r": 0.2, "g": 0.6, "b": 1.0})
	var scale_data = data.get("transform", {}).get("scale", {"x": 0.5, "y": 1.8, "z": 0.5})
	
	var mode = "procedural_capsule"
	var scene_path = ""
	
	# Check asset manifest for resolution
	if not active_asset_manifest.is_empty():
		var entity_cfg = active_asset_manifest.get("entities", {}).get(entity_id, {})
		var type_cfg = active_asset_manifest.get("types", {}).get(entity_type, {})
		var fallback_cfg = active_asset_manifest.get("fallback", {}).get("entity", {})
		
		var active_cfg = {}
		if not entity_cfg.is_empty():
			active_cfg = entity_cfg
		elif not type_cfg.is_empty():
			active_cfg = type_cfg
		elif not fallback_cfg.is_empty():
			active_cfg = fallback_cfg
			
		if not active_cfg.is_empty():
			mode = active_cfg.get("mode", mode)
			scene_path = active_cfg.get("path", "")
			if active_cfg.has("color"):
				var c = active_cfg["color"]
				color_data = {"r": c[0], "g": c[1], "b": c[2]}
			if active_cfg.has("scale"):
				var s = active_cfg["scale"]
				scale_data = {"x": s[0], "y": s[1], "z": s[2]}
			
	if mode == "scene" and scene_path != "":
		var packed_scene = load(scene_path)
		if packed_scene:
			var instance = packed_scene.instantiate()
			instance.name = entity_id
			instance.position = pos
			actors.add_child(instance)
			print("[Main] Spawned mapped scene: ", entity_id, " from ", scene_path)
			return
		else:
			print("[Main] Failed to load mapped scene: ", scene_path, " falling back to capsule.")
	
	# FALLBACK: Create capsule mesh
	# TODO: replace 'return' with: if not BootHasSpawned(entity_id):
	# Disabled until spawn-tracking system is in place — prevents double-spawns
	# with Boot.gd's _spawn_from_id_list / _spawn_from_bridge_entities paths.
	return

func _input(event):
	if event is InputEventMouseMotion:
		handle_mouse_look(event)
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_TAB:
			return_to_scene_chooser()
			return
	if event is InputEventKey and event.pressed:
		if event.keycode == KEY_ESCAPE:
			Input.set_mouse_mode(Input.MOUSE_MODE_VISIBLE)
		elif event.keycode == KEY_ENTER:
			Input.set_mouse_mode(Input.MOUSE_MODE_CAPTURED)

func return_to_scene_chooser():
	print("[Main] Returning to Scene Chooser.")

	scene_chosen = false
	world_ready = false
	dragon_spawned = false

	Input.set_mouse_mode(Input.MOUSE_MODE_VISIBLE)

	if chooser_ui:
		chooser_ui.visible = true

	if semantic_renderer and semantic_renderer.has_method("clear_scene"):
		semantic_renderer.clear_scene()

	if actors:
		for child in actors.get_children():
			child.queue_free()

	var dragon := get_node_or_null("EngAIn_Dragon_Placeholder")
	if dragon:
		dragon.queue_free()

	print("[Main] Scene hidden. Chooser active.")

func _process(delta: float) -> void:
	if world_ready and not dragon_spawned:
		spawn_dragon()

	handle_movement(delta)

func handle_movement(delta):
	var camera := get_viewport().get_camera_3d()
	if not camera:
		return

	# Vertical movement: Ctrl + Up / Ctrl + Down
	if Input.is_key_pressed(KEY_CTRL) and Input.is_action_pressed("ui_up"):
		var new_pos: Vector3 = camera.global_position
		new_pos.y += vertical_speed * delta
		if _bounds_initialized:
			new_pos = _clamp_to_aabb(new_pos, camera_bounds)
		camera.global_position = new_pos
		return

	if Input.is_key_pressed(KEY_CTRL) and Input.is_action_pressed("ui_down"):
		var new_pos: Vector3 = camera.global_position
		new_pos.y -= vertical_speed * delta
		if _bounds_initialized:
			new_pos = _clamp_to_aabb(new_pos, camera_bounds)
		camera.global_position = new_pos
		return

	var dir := Vector3.ZERO

	if Input.is_action_pressed("ui_up"):
		dir -= camera.global_transform.basis.z
	if Input.is_action_pressed("ui_down"):
		dir += camera.global_transform.basis.z
	if Input.is_action_pressed("ui_left"):
		dir -= camera.global_transform.basis.x
	if Input.is_action_pressed("ui_right"):
		dir += camera.global_transform.basis.x

	dir.y = 0

	if dir.length() > 0:
		dir = dir.normalized()
		var new_pos: Vector3 = camera.global_position + dir * move_speed * delta

		if _bounds_initialized:
			new_pos = _clamp_to_aabb(new_pos, camera_bounds)

		camera.global_position = new_pos

func handle_mouse_look(event):
	var camera := get_viewport().get_camera_3d()
	if not camera:
		return

	yaw -= event.relative.x * mouse_sensitivity
	pitch -= event.relative.y * mouse_sensitivity

	# Clamp vertical rotation so you don't flip
	pitch = clamp(pitch, -1.5, 1.5)

	var basis := Basis()
	basis = Basis(Vector3.UP, yaw) * Basis(Vector3.RIGHT, pitch)

	camera.global_transform.basis = basis

func spawn_dragon():
	dragon_spawned = true

	var dragon := Node3D.new()
	dragon.name = "EngAIn_Dragon_Placeholder"

	var dragon_mat := StandardMaterial3D.new()
	dragon_mat.albedo_color = Color(0.8, 0.1, 0.1)

	var body := MeshInstance3D.new()
	var mesh := SphereMesh.new()
	mesh.radius = 0.8
	mesh.height = 1.6
	body.mesh = mesh
	body.material_override = dragon_mat
	dragon.add_child(body)

	var wing_l := MeshInstance3D.new()
	var wing_l_mesh := BoxMesh.new()
	wing_l_mesh.size = Vector3(1.8, 0.12, 0.6)
	wing_l.mesh = wing_l_mesh
	wing_l.position = Vector3(-1.2, 0.15, 0)
	wing_l.material_override = dragon_mat
	dragon.add_child(wing_l)

	var wing_r := MeshInstance3D.new()
	var wing_r_mesh := BoxMesh.new()
	wing_r_mesh.size = Vector3(1.8, 0.12, 0.6)
	wing_r.mesh = wing_r_mesh
	wing_r.position = Vector3(1.2, 0.15, 0)
	wing_r.material_override = dragon_mat
	dragon.add_child(wing_r)

	add_child(dragon)

	var camera := get_viewport().get_camera_3d()
	if camera:
		var forward := -camera.global_transform.basis.z
		dragon.global_position = camera.global_position + forward * 6.0 + Vector3(0, 2, 0)
		dragon.look_at(camera.global_position, Vector3.UP)
	else:
		dragon.global_position = Vector3(0, 2, -6)
	show_dragon_prompt(dragon)

func show_dragon_prompt(dragon):
	print("\n=== EngAIn Assistant ===")
	print("Let's build this damn world together.\n")
	print("1. Use my own assets")
	print("2. Generate assets")
	print("3. Use Trixel system")
	print("4. Let the world run\n")
