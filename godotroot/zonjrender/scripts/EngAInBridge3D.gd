extends CharacterBody3D

@onready var sprite: AnimatedSprite3D = $"../AnimatedSprite3D"

@export var move_speed: float = 2.5
@export var auto_play_animation: bool = true
@export var default_animation: String = "idle_flap"

func _ready() -> void:
	if sprite == null:
		push_error("EngAInBridge3D.gd: AnimatedSprite3D not found at ../AnimatedSprite3D")
		return

	if auto_play_animation:
		_play_default_animation()

func _physics_process(_delta: float) -> void:
	move_and_slide()

func _play_default_animation() -> void:
	if sprite == null:
		return

	if sprite.sprite_frames == null:
		push_warning("EngAInBridge3D.gd: AnimatedSprite3D has no SpriteFrames")
		return

	if sprite.sprite_frames.has_animation(default_animation):
		sprite.play(default_animation)
		return

	if sprite.sprite_frames.has_animation("idle"):
		sprite.play("idle")
		return

	var names: PackedStringArray = sprite.sprite_frames.get_animation_names()
	if names.size() > 0:
		sprite.play(names[0])
	else:
		push_warning("EngAInBridge3D.gd: no animations found to play")
