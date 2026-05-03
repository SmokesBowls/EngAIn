extends Node3D
# ─────────────────────────────────────────────
#  SemanticRenderer.gd  —  RUNTIME ONLY
#  No @tool. No editor vars. No HTTP. No variants.
#  Orchestrates TerrainChunkBuilder + EntitySpawner.
#  Feed it data via render_from_data(dict).
# ─────────────────────────────────────────────

const SCENE_ID := "03_Fist_contact"

var _runtime_root: Node3D
var _terrain_builder := TerrainChunkBuilder.new()
var _entity_spawner := EntitySpawner.new()


# ── Boot ──────────────────────────────────────
func _ready() -> void:
	_runtime_root = _ensure_root("RuntimeEntities")

	var svc = get_node_or_null("/root/SceneNetworkService")
	if svc == null:
		push_error("[SemanticRenderer] SceneNetworkService autoload not found")
		return

	if not svc.fetch_succeeded.is_connected(_on_fetch_succeeded):
		svc.fetch_succeeded.connect(_on_fetch_succeeded)

	if not svc.fetch_failed.is_connected(_on_fetch_failed):
		svc.fetch_failed.connect(_on_fetch_failed)

	svc.fetch_scene(SCENE_ID)


# ── Signal handlers ────────────────────────────
func _on_fetch_succeeded(scene_id: String, data: Dictionary) -> void:
	print("[SemanticRenderer] scene loaded: ", scene_id)
	render_from_data(data)

func _on_fetch_failed(scene_id: String, detail: String) -> void:
	push_error("[SemanticRenderer] fetch failed [%s]: %s" % [scene_id, detail])


# ── Public entry point ─────────────────────────
func render_from_data(data: Dictionary) -> void:
	_clear(_runtime_root)

	# Terrain
	var terrain_meshes: Array = _terrain_builder.build(data)
	for mi in terrain_meshes:
		_runtime_root.add_child(mi)
	print("[SemanticRenderer] terrain meshes: ", terrain_meshes.size())

	# Entities
	var entities: Array = _entity_spawner.build(data)
	for ent in entities:
		_runtime_root.add_child(ent)
	print("[SemanticRenderer] entities: ", entities.size())
	
	#this is flying in circles we dont need it
	#_frame_camera()


# ── Camera ─────────────────────────────────────
func _frame_camera() -> void:
	var cam := get_viewport().get_camera_3d()
	if cam == null:
		return

	var pts: Array[Vector3] = []
	for c in _runtime_root.get_children():
		if c is Node3D:
			pts.append((c as Node3D).global_position)

	if pts.is_empty():
		return

	var center := Vector3.ZERO
	for p in pts:
		center += p
	center /= float(pts.size())

	var radius := 8.0
	for p in pts:
		radius = max(radius, center.distance_to(p) + 3.0)

	cam.global_position = center + Vector3(0.0, radius * 0.9, radius * 1.4)
	cam.look_at(center, Vector3.UP)


# ── Helpers ────────────────────────────────────
func _ensure_root(root_name: String) -> Node3D:
	var n = get_node_or_null(root_name)
	if n is Node3D:
		return n as Node3D

	var root := Node3D.new()
	root.name = root_name
	add_child(root)
	return root

func _clear(root: Node3D) -> void:
	for c in root.get_children():
		c.queue_free()
