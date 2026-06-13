extends Node3D
class_name BlenderTerrainMount

@export var terrain_mesh_path: String = "res://assets/blender/engain_biome_terrain.glb"

var _terrain_mesh: MeshInstance3D = null

func _ready() -> void:
	_load_blender_terrain()

func _load_blender_terrain() -> void:
	if not ResourceLoader.exists(terrain_mesh_path):
		push_error("[BlenderTerrainMount] Terrain mesh not found: %s" % terrain_mesh_path)
		return

	var packed_scene: PackedScene = load(terrain_mesh_path) as PackedScene
	if packed_scene == null:
		push_error("[BlenderTerrainMount] Failed to load terrain as PackedScene: %s" % terrain_mesh_path)
		return

	var scene: Node = packed_scene.instantiate()
	add_child(scene)
	_terrain_mesh = _find_first_mesh_instance(scene)

	if _terrain_mesh != null:
		print("[BlenderTerrainMount] Terrain mesh loaded: %s" % terrain_mesh_path)
	else:
		push_warning("[BlenderTerrainMount] Could not find MeshInstance3D in loaded GLB.")

func _find_first_mesh_instance(node: Node) -> MeshInstance3D:
	if node is MeshInstance3D:
		return node as MeshInstance3D

	for child in node.get_children():
		var child_node: Node = child as Node
		var found: MeshInstance3D = _find_first_mesh_instance(child_node)
		if found != null:
			return found

	return null

# ===============================================================
# GEOMETRY AUTHORITY INTERFACE (Dumb Mesh Holder)
# ===============================================================

func apply_recipe_texture(texture: Texture2D, materialization: Dictionary) -> void:
	## Applies a Trixel recipe texture to the Blender terrain mesh.
	## Called only by SemanticRenderer via an embodiment contract.
	## This node holds geometry and applies textures as instructed; it does not decide materialization policy.
	if _terrain_mesh == null:
		push_warning("[BlenderTerrainMount] No terrain mesh available. Cannot apply texture.")
		return

	if texture == null:
		push_warning("[BlenderTerrainMount] Received null texture. Cannot apply.")
		return

	var mat: StandardMaterial3D = _terrain_mesh.get_active_material(0) as StandardMaterial3D
	if mat == null:
		mat = StandardMaterial3D.new()
		_terrain_mesh.set_surface_override_material(0, mat)

	var assignment_rule: String = String(materialization.get("assignment_rule", "surface_0_albedo_texture"))
	if assignment_rule == "surface_0_albedo_texture":
		mat.albedo_texture = texture
		mat.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
		print("[BlenderTerrainMount] Recipe texture applied to Blender mesh surface 0 (albedo).")
	else:
		push_warning("[BlenderTerrainMount] Unknown assignment rule: %s" % assignment_rule)

func get_terrain_mesh() -> MeshInstance3D:
	## Returns the terrain mesh instance for inspection/debugging.
	return _terrain_mesh
