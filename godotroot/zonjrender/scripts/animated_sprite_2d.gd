extends AnimatedSprite2D

@export var orbit_radius: float = 24.0
@export var orbit_speed: float = 1.2
@export var bob_height: float = 6.0
@export var bob_speed: float = 2.0
@export var auto_play_animation: bool = true
@export var default_animation: String = "idle_flap"

var _base_position: Vector2
var _t: float = 0.0

func _ready() -> void:
	_base_position = position

	if auto_play_animation:
		_play_default_animation()

func _process(delta: float) -> void:
	_t += delta

	var orbit_x := cos(_t * orbit_speed) * orbit_radius
	var orbit_y := sin(_t * orbit_speed) * orbit_radius * 0.35
	var bob := sin(_t * bob_speed) * bob_height

	position = _base_position + Vector2(orbit_x, orbit_y + bob)

func _play_default_animation() -> void:
	if sprite_frames == null:
		push_warning("EngAInDragon.gd: AnimatedSprite2D has no SpriteFrames")
		return

	if sprite_frames.has_animation(default_animation):
		play(default_animation)
		return

	if sprite_frames.has_animation("idle"):
		play("idle")
		return

	var names: PackedStringArray = sprite_frames.get_animation_names()
	if names.size() > 0:
		play(names[0])
	else:
		push_warning("EngAInDragon.gd: no animations found to play")
