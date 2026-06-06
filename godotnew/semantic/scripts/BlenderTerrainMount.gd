extends Node3D
class_name BlenderTerrainMount

@export var terrain_scene_path: String = "res://assets/blender/engain_biome_terrain.glb"
@export var apply_latest_artwork_on_ready: bool = true
@export var terrain_scale: Vector3 = Vector3(1.0, 1.0, 1.0)
@export var terrain_position: Vector3 = Vector3(0.0, 0.0, 0.0)

var _terrain_instance: Node = null
var _latest_texture: Texture2D = null

func _ready() -> void:
	_load_blender_terrain()

	var artwork_client := get_node_or_null("/root/ArtworkClient")
	if artwork_client != null:
		artwork_client.artwork_loaded.connect(_on_artwork_loaded)
		artwork_client.artwork_failed.connect(_on_artwork_failed)

		if apply_latest_artwork_on_ready:
			print("[BlenderTerrainMount] requesting latest artwork")
			artwork_client.get_latest_artwork()
	else:
		push_warning("[BlenderTerrainMount] /root/ArtworkClient not found; terrain loaded without artwork texture")

func _load_blender_terrain() -> void:
	var packed: PackedScene = load(terrain_scene_path) as PackedScene
	if packed == null:
		push_error("[BlenderTerrainMount] failed to load terrain scene: %s" % terrain_scene_path)
		return

	_terrain_instance = packed.instantiate()
	if _terrain_instance == null:
		push_error("[BlenderTerrainMount] failed to instantiate terrain scene: %s" % terrain_scene_path)
		return

	add_child(_terrain_instance)

	if _terrain_instance is Node3D:
		var terrain_3d := _terrain_instance as Node3D
		terrain_3d.position = terrain_position
		terrain_3d.scale = terrain_scale

	print("[BlenderTerrainMount] loaded terrain: %s" % terrain_scene_path)

func _on_artwork_loaded(scene_id: String, texture: Texture2D) -> void:
	if texture == null:
		push_warning("[BlenderTerrainMount] artwork_loaded emitted null texture for %s" % scene_id)
		return

	_latest_texture = texture
	_apply_texture_to_meshes(texture)
	print("[BlenderTerrainMount] applied artwork texture scene_id=%s size=%dx%d" % [
		scene_id,
		texture.get_width(),
		texture.get_height()
	])

func _on_artwork_failed(scene_id: String, detail: String, status_code: int) -> void:
	push_warning("[BlenderTerrainMount] artwork failed scene_id=%s status=%d detail=%s" % [
		scene_id,
		status_code,
		detail
	])

func _apply_texture_to_meshes(texture: Texture2D) -> void:
	if _terrain_instance == null:
		push_warning("[BlenderTerrainMount] cannot apply texture; terrain not loaded")
		return

	var meshes: Array[MeshInstance3D] = []
	_collect_meshes(_terrain_instance, meshes)

	if meshes.is_empty():
		push_warning("[BlenderTerrainMount] no MeshInstance3D nodes found under terrain")
		return

	for mesh_instance in meshes:
		var mat := StandardMaterial3D.new()
		mat.albedo_texture = texture
		mat.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
		mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		mesh_instance.material_override = mat

	print("[BlenderTerrainMount] textured mesh_count=%d" % meshes.size())

func _collect_meshes(node: Node, out_meshes: Array[MeshInstance3D]) -> void:
	if node is MeshInstance3D:
		out_meshes.append(node as MeshInstance3D)

	for child in node.get_children():
		_collect_meshes(child, out_meshes)
