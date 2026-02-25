extends Label3D
## IntentMarker - Shows what an AI agent thinks it's doing

var intent_text: String = "IDLE"
var intent_color: Color = Color.GRAY

func _ready():
	billboard = BaseMaterial3D.BILLBOARD_ENABLED
	position = Vector3(0, 4.5, 0)  # High above head
	font_size = 64
	outline_size = 12
	outline_modulate = Color.BLACK
	update_display()

func set_intent(new_intent: String, color: Color = Color.WHITE):
	"""Update what this agent is doing"""
	intent_text = new_intent
	intent_color = color
	update_display()

func update_display():
	"""Refresh the label"""
	text = intent_text
	modulate = intent_color
