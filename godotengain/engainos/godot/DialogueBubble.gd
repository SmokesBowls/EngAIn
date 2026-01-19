extends Node3D
## DialogueBubble - Shows character speech in 3D space

var label: Label3D
var timer: Timer

func _ready():
	# Create 3D label
	label = Label3D.new()
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	label.font_size = 48
	label.outline_size = 8
	label.position = Vector3(0, 3, 0)  # Above character
	add_child(label)
	
	# Auto-hide timer
	timer = Timer.new()
	timer.one_shot = true
	timer.timeout.connect(_on_timeout)
	add_child(timer)
	
	hide()

func show_dialogue(text: String, speaker: String, duration: float = 4.0):
	label.text = speaker + ": " + text
	show()
	timer.start(duration)

func _on_timeout():
	hide()
