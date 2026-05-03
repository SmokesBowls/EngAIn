@tool
extends Node3D
class_name DragonAvatar3D

# Dragon avatar controller
# - orbit/bob motion for display
# - pulse on AI/log response
# - safe bridge hookup (optional)

@export var bridge_path: NodePath = ^"EngAInBridge"
@export var sprite_path: NodePath = ^"AnimatedSprite3D"
@export var orbit_radius: float = 1.5
@export var orbit_speed: float = 0.6
@export var bob_height: float = 0.25
@export var bob_speed: float = 1.2
@export var pulse_duration: float = 0.18
@export var pulse_intensity: Color = Color(1.0, 1.0, 0.2, 1.0)

var _bridge: Node = null
var _sprite: AnimatedSprite3D = null
# CHANGED: Removed _base_pos. We use local position now so it follows parent automatically.
var _t: float = 0.0
var _pulse_tween: Tween = null

func _ready() -> void:
	# No longer caches global_position. Uses local position relative to parent.
	_bridge = get_node_or_null(bridge_path)
	_sprite = get_node_or_null(sprite_path) as AnimatedSprite3D

	# SAFE CONNECTION: Only connects if bridge exists
	if _bridge and _bridge.has_signal("ai_decision_received"):
		_bridge.connect("ai_decision_received", _on_ai_decision)

	if _sprite:
		_sprite.play("idle")

func _exit_tree() -> void:
	if _pulse_tween:
		_pulse_tween.kill()

func _process(delta: float) -> void:
	if Engine.is_editor_hint():
		return
	
	_t += delta

	var angle: float = _t * orbit_speed
	var x: float = cos(angle) * orbit_radius
	var z: float = sin(angle) * orbit_radius
	var y: float = sin(_t * bob_speed) * bob_height

	# CHANGED: Uses local 'position' instead of 'global_position'.
	# This ensures the dragon stays attached to its parent (Trixel) if the parent moves.
	position = Vector3(x, y, z)

	if _sprite:
		_sprite.rotation = Vector3(deg_to_rad(90.0), 0.0, 0.0)

func _on_ai_decision(decision_data: Dictionary) -> void:
	var action_type = decision_data.get("action_type", "")
	if action_type != "":
		_start_pulse()

func _start_pulse() -> void:
	if not _sprite:
		return
	if _pulse_tween:
		_pulse_tween.kill()

	var original_modulate: Color = _sprite.modulate

	var tween: Tween = create_tween()
	tween.tween_property(_sprite, "modulate", pulse_intensity, 0.0)
	tween.tween_interval(pulse_duration)
	tween.tween_callback(func() -> void:
		if is_instance_valid(_sprite):
			_sprite.modulate = original_modulate
	)

	_pulse_tween = tween

func set_pulse_color(col: Color) -> void:
	pulse_intensity = col

func set_orbit_parameters(
	radius: float = -1.0,
	speed: float = -1.0,
	new_bob_height: float = -1.0,
	new_bob_speed: float = -1.0
) -> void:
	if radius >= 0.0:
		orbit_radius = radius
	if speed >= 0.0:
		orbit_speed = speed
	if new_bob_height >= 0.0:
		bob_height = new_bob_height
	if new_bob_speed >= 0.0:
		bob_speed = new_bob_speed
