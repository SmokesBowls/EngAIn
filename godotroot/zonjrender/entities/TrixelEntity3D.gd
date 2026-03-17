extends Node3D
class_name TrixelEntity3D

signal entity_selected(entity_id: String, button_index: int)
signal asset_edit_requested(entity_id: String)
signal render_plan_applied(entity_id: String)

@export var use_unshaded_material: bool = true
@export var show_name_label: bool = true
@export var default_interaction_radius: float = 1.5
@export var default_collision_profile: String = "character_medium"

const RENDER_MODE_PLANAR_SPRITE: String = "planar_sprite"
const RENDER_MODE_MESH_FULL: String = "mesh_full"

const PLANE_MODE_VERTICAL: String = "vertical"
const PLANE_MODE_GROUND: String = "ground"
const PLANE_MODE_WALL: String = "wall"

const COLLISION_PROFILES := {
	"character_small": {
		"shape": "capsule",
		"radius": 0.22,
		"height": 1.20,
	},
	"character_medium": {
		"shape": "capsule",
		"radius": 0.32,
		"height": 1.80,
	},
	"character_large": {
		"shape": "capsule",
		"radius": 0.45,
		"height": 2.40,
	},
	"item_small": {
		"shape": "box",
		"size": Vector3(0.35, 0.20, 0.35),
	},
	"item_medium": {
		"shape": "box",
		"size": Vector3(0.60, 0.35, 0.60),
	},
	"building_small": {
		"shape": "box",
		"size": Vector3(2.0, 2.0, 2.0),
	},
	"building_medium": {
		"shape": "box",
		"size": Vector3(4.0, 3.0, 4.0),
	},
	"trigger": {
		"shape": "box",
		"size": Vector3(1.0, 1.0, 1.0),
	},
}

var entity_id: String = ""
var render_plan: Dictionary = {}

@onready var visual: MeshInstance3D = $Visual
@onready var body_collision: CollisionShape3D = $BodyCollision
@onready var interaction_area: Area3D = $InteractionArea
@onready var interaction_collision: CollisionShape3D = $InteractionArea/InteractionCollision
@onready var shadow_indicator: MeshInstance3D = $ShadowIndicator
@onready var name_label: Label3D = $NameLabel

var _base_material: StandardMaterial3D
var _shadow_material: StandardMaterial3D

func _ready() -> void:
	if not interaction_area.input_event.is_connected(_on_interaction_input_event):
		interaction_area.input_event.connect(_on_interaction_input_event)
	_ensure_runtime_resources()

func apply_render_plan(plan: Dictionary) -> void:
	render_plan = plan.duplicate(true)

	entity_id = String(plan.get("id", plan.get("entity_id", name)))
	name = "TrixelEntity3D_%s" % entity_id

	var pos_3d: Vector3 = _to_vector3(plan.get("pos_3d", Vector3.ZERO))
	position = pos_3d

	var yaw: float = float(plan.get("yaw", rotation.y))
	rotation = Vector3(0.0, yaw, 0.0)

	var render_mode: String = String(plan.get("render_mode", RENDER_MODE_PLANAR_SPRITE))
	var plane_mode: String = String(plan.get("plane_mode", PLANE_MODE_VERTICAL))
	var size_world: Vector2 = _to_size2(plan.get("size_world", Vector2(1.0, 1.8)))
	var asset_ref: String = String(plan.get("asset_ref", ""))
	var flip_x: bool = bool(plan.get("flip_x", false))
	var depth_bias: float = float(plan.get("depth_bias", 0.0))
	var shadow_mode: String = String(plan.get("shadow_mode", "off"))
	var collision_profile: String = String(plan.get("collision_profile", default_collision_profile))
	var interaction_radius: float = float(plan.get("interaction_radius", default_interaction_radius))

	_apply_visual_mode(render_mode, plane_mode, size_world, asset_ref, flip_x, depth_bias)
	_apply_collision_profile(collision_profile, size_world)
	_apply_interaction_radius(interaction_radius)
	_apply_shadow(shadow_mode, size_world)
	_apply_name_label(size_world, plan)

	render_plan_applied.emit(entity_id)

func set_visual_facing(yaw_radians: float) -> void:
	rotation.y = yaw_radians

func set_display_name(display_name: String) -> void:
	name_label.text = display_name
	name_label.visible = show_name_label and display_name != ""

func get_entity_id() -> String:
	return entity_id

func _ensure_runtime_resources() -> void:
	if visual.mesh == null:
		var quad: QuadMesh = QuadMesh.new()
		quad.size = Vector2(1.0, 1.0)
		visual.mesh = quad

	if _base_material == null:
		_base_material = StandardMaterial3D.new()
		_base_material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED if use_unshaded_material else BaseMaterial3D.SHADING_MODE_PER_PIXEL
		_base_material.cull_mode = BaseMaterial3D.CULL_DISABLED
		_base_material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		_base_material.albedo_color = _color_from_string(name)
		visual.material_override = _base_material

	if shadow_indicator.mesh == null:
		var shadow_quad: QuadMesh = QuadMesh.new()
		shadow_quad.size = Vector2(1.0, 1.0)
		shadow_indicator.mesh = shadow_quad

	if _shadow_material == null:
		_shadow_material = StandardMaterial3D.new()
		_shadow_material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		_shadow_material.cull_mode = BaseMaterial3D.CULL_DISABLED
		_shadow_material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		_shadow_material.albedo_color = Color(0.0, 0.0, 0.0, 0.28)
		shadow_indicator.material_override = _shadow_material

	if body_collision.shape == null:
		var capsule: CapsuleShape3D = CapsuleShape3D.new()
		capsule.radius = 0.32
		capsule.height = 1.80
		body_collision.shape = capsule

	if interaction_collision.shape == null:
		var sphere: SphereShape3D = SphereShape3D.new()
		sphere.radius = default_interaction_radius
		interaction_collision.shape = sphere

func _apply_visual_mode(
	render_mode: String,
	plane_mode: String,
	size_world: Vector2,
	asset_ref: String,
	flip_x: bool,
	depth_bias: float
) -> void:
	if render_mode != RENDER_MODE_PLANAR_SPRITE and render_mode != RENDER_MODE_MESH_FULL:
		push_warning("Unknown render_mode '%s' for %s. Falling back to planar_sprite." % [render_mode, entity_id])

	var quad: QuadMesh = visual.mesh as QuadMesh
	if quad == null:
		quad = QuadMesh.new()
		visual.mesh = quad

	quad.size = size_world
	visual.scale = Vector3(-1.0 if flip_x else 1.0, 1.0, 1.0)

	match plane_mode:
		PLANE_MODE_VERTICAL:
			visual.rotation = Vector3.ZERO
			visual.position = Vector3(0.0, size_world.y * 0.5, depth_bias)
		PLANE_MODE_GROUND:
			visual.rotation = Vector3(-PI * 0.5, 0.0, 0.0)
			visual.position = Vector3(0.0, 0.02, depth_bias)
		PLANE_MODE_WALL:
			visual.rotation = Vector3.ZERO
			visual.position = Vector3(0.0, size_world.y * 0.5, depth_bias)
		_:
			push_warning("Unknown plane_mode '%s' for %s. Falling back to vertical." % [plane_mode, entity_id])
			visual.rotation = Vector3.ZERO
			visual.position = Vector3(0.0, size_world.y * 0.5, depth_bias)

	var material: StandardMaterial3D = visual.material_override as StandardMaterial3D
	if material == null:
		material = _base_material
		visual.material_override = material

	if asset_ref != "" and ResourceLoader.exists(asset_ref):
		var tex: Texture2D = load(asset_ref) as Texture2D
		if tex != null:
			material.albedo_texture = tex
			material.albedo_color = Color.WHITE
		else:
			material.albedo_texture = null
			material.albedo_color = _color_from_string(entity_id)
	else:
		material.albedo_texture = null
		material.albedo_color = _color_from_string(entity_id)

func _apply_collision_profile(profile_name: String, size_world: Vector2) -> void:
	var profile: Dictionary = COLLISION_PROFILES.get(profile_name, COLLISION_PROFILES[default_collision_profile])
	var shape_type: String = String(profile.get("shape", "capsule"))

	match shape_type:
		"capsule":
			var capsule: CapsuleShape3D = body_collision.shape as CapsuleShape3D
			if capsule == null:
				capsule = CapsuleShape3D.new()
				body_collision.shape = capsule

			capsule.radius = float(profile.get("radius", max(size_world.x * 0.18, 0.15)))
			capsule.height = float(profile.get("height", max(size_world.y, 1.0)))
			body_collision.position = Vector3(0.0, capsule.height * 0.5, 0.0)

		"box":
			var box: BoxShape3D = body_collision.shape as BoxShape3D
			if box == null:
				box = BoxShape3D.new()
				body_collision.shape = box

			var box_size: Vector3 = profile.get("size", Vector3(size_world.x, size_world.y, max(size_world.x, 0.2)))
			box.size = box_size
			body_collision.position = Vector3(0.0, box_size.y * 0.5, 0.0)

		_:
			push_warning("Unknown collision profile shape '%s' for %s." % [shape_type, entity_id])

func _apply_interaction_radius(radius: float) -> void:
	var sphere: SphereShape3D = interaction_collision.shape as SphereShape3D
	if sphere == null:
		sphere = SphereShape3D.new()
		interaction_collision.shape = sphere

	sphere.radius = max(radius, 0.1)
	interaction_collision.position = Vector3(0.0, max(radius * 0.5, 0.5), 0.0)

func _apply_shadow(shadow_mode: String, size_world: Vector2) -> void:
	if shadow_mode == "off":
		shadow_indicator.visible = false
		return

	shadow_indicator.visible = true

	var shadow_quad: QuadMesh = shadow_indicator.mesh as QuadMesh
	if shadow_quad == null:
		shadow_quad = QuadMesh.new()
		shadow_indicator.mesh = shadow_quad

	var shadow_size: float = max(size_world.x * 0.72, 0.3)
	shadow_quad.size = Vector2(shadow_size, shadow_size)
	shadow_indicator.rotation = Vector3(-PI * 0.5, 0.0, 0.0)
	shadow_indicator.position = Vector3(0.0, 0.01, 0.0)

	match shadow_mode:
		"projected":
			_shadow_material.albedo_color = Color(0.0, 0.0, 0.0, 0.22)
		"full":
			_shadow_material.albedo_color = Color(0.0, 0.0, 0.0, 0.34)
		_:
			_shadow_material.albedo_color = Color(0.0, 0.0, 0.0, 0.22)

func _apply_name_label(size_world: Vector2, plan: Dictionary) -> void:
	var display_name: String = String(plan.get("display_name", plan.get("name", entity_id)))
	name_label.text = display_name
	name_label.visible = show_name_label and display_name != ""
	name_label.position = Vector3(0.0, size_world.y + 0.25, 0.0)

func _on_interaction_input_event(
	_camera: Node,
	event: InputEvent,
	_event_position: Vector3,
	_normal: Vector3,
	_shape_idx: int
) -> void:
	if event is InputEventMouseButton and event.pressed:
		var mouse_event: InputEventMouseButton = event as InputEventMouseButton
		entity_selected.emit(entity_id, mouse_event.button_index)
		if mouse_event.button_index == MOUSE_BUTTON_RIGHT:
			asset_edit_requested.emit(entity_id)

func _to_vector3(value: Variant) -> Vector3:
	if value is Vector3:
		return value as Vector3

	if value is Array:
		var arr: Array = value as Array
		if arr.size() >= 3:
			return Vector3(
				float(arr[0]),
				float(arr[1]),
				float(arr[2])
			)

	if value is Dictionary:
		var d: Dictionary = value as Dictionary
		return Vector3(
			float(d.get("x", 0.0)),
			float(d.get("y", 0.0)),
			float(d.get("z", 0.0))
		)

	return Vector3.ZERO

func _to_size2(value: Variant) -> Vector2:
	if value is Vector2:
		var v2: Vector2 = value as Vector2
		return Vector2(max(v2.x, 0.05), max(v2.y, 0.05))

	if value is Array:
		var arr: Array = value as Array
		if arr.size() >= 2:
			return Vector2(
				max(float(arr[0]), 0.05),
				max(float(arr[1]), 0.05)
			)

	if value is Dictionary:
		var d: Dictionary = value as Dictionary
		return Vector2(
			max(float(d.get("width", d.get("x", 1.0))), 0.05),
			max(float(d.get("height", d.get("y", 1.0))), 0.05)
		)

	return Vector2(1.0, 1.8)

func _color_from_string(seed_text: String) -> Color:
	var h: int = seed_text.hash()
	var r: float = float((h >> 16) & 0xFF) / 255.0
	var g: float = float((h >> 8) & 0xFF) / 255.0
	var b: float = float(h & 0xFF) / 255.0

	r = 0.35 + (r * 0.55)
	g = 0.35 + (g * 0.55)
	b = 0.35 + (b * 0.55)

	return Color(r, g, b, 1.0)
