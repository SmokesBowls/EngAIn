extends CharacterBody3D

@onready var sprite = $AnimatedSprite3D
@onready var speech_label = $Label
@onready var input_box = $"../LineEdit"
@onready var snapshot_manager = $"../SnapshotManager"

const SPEED = 100.0
var flight_time = 0.0
var center_position = Vector2()

var manual_responses = {
	"greeting": "Ancient draconic consciousness acknowledges your presence.",
	"location": "We exist within the Cosmic Command Center.",
	"dragons": "Nine aspects of cosmic control manifest here.",
	"help": "Ask about location, dragons, time, or weather.",
	"time": "Time flows differently here... but now is now.",
	"weather": "Energy streams are calm, with occasional rifts.",
	"default": "The dragon ponders your words."
}

func _ready():
	sprite.play("idle_flap")
	speech_label.text = "Dragon awaits your command..."
	center_position = global_position
	if snapshot_manager:
		snapshot_manager.capture_event("scene_loaded", {"scene": "ManualDragon"})

func _physics_process(delta):
	flight_time += delta
	var radius = 100.0
	var circle_speed = 1.0
	var target_x = center_position.x + cos(flight_time * circle_speed) * radius
	var target_y = center_position.y + sin(flight_time * circle_speed) * radius
	var target_position = Vector2(target_x, target_y)
	var direction = (target_position - global_position).normalized()
	velocity = direction * SPEED
	move_and_slide()

func _on_line_edit_text_submitted(text: String):
	if text.is_empty():
		return
	var original = text
	input_box.clear()
	if snapshot_manager:
		snapshot_manager.capture_event("message_received", {"command": original})
	var response = get_manual_response(original)
	dragon_speak(response)

func get_manual_response(input: String) -> String:
	var lower = input.to_lower()
	if "hello" in lower or "hi" in lower:
		return manual_responses["greeting"]
	elif "where" in lower:
		return manual_responses["location"]
	elif "dragon" in lower and ("many" in lower or "how" in lower):
		return manual_responses["dragons"]
	elif "help" in lower:
		return manual_responses["help"]
	elif "time" in lower:
		return manual_responses["time"]
	elif "weather" in lower or "energy" in lower:
		return manual_responses["weather"]
	else:
		return manual_responses["default"]

func dragon_speak(text: String):
	speech_label.text = text
	sprite.modulate = Color.YELLOW
	var tween = create_tween()
	tween.tween_property(sprite, "modulate", Color.WHITE, 0.5)
	var display_time = max(3.0, min(10.0, text.length() * 0.05))
	await get_tree().create_timer(display_time).timeout
	speech_label.text = "Dragon awaits your command..."
