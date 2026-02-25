extends Node
## CourierScene - Bob delivers package from Tom to Ted

# Character references
var bob: Node3D
var tom: Node3D
var ted: Node3D

# Courier state
enum State { WAITING, WALKING_TO_TOM, AT_TOM, WALKING_TO_TED, AT_TED, COMPLETE }
var current_state: State = State.WAITING

# Movement
var move_speed: float = 2.5
var target_position: Vector3
var dialogue_box: Control

func _ready():
	print("[CourierScene] Waiting for characters to spawn...")

func start_courier_sequence():
	"""Begin the courier sequence once characters are spawned"""
	
	# Find our three characters (using narrative names)
	tom = find_character("Elyraen")   # Tom = Elyraen (sender)
	bob = find_character("Senareth")   # Bob = Senareth (courier)
	ted = find_character("Vairis")     # Ted = Vairis (receiver)
	
	if not bob or not tom or not ted:
		push_error("[CourierScene] Missing characters!")
		push_error("  Tom (Elyraen): " + str(tom != null))
		push_error("  Bob (Senareth): " + str(bob != null))
		push_error("  Ted (Vairis): " + str(ted != null))
		return
	
	print("[CourierScene] Found all characters!")
	print("  Tom at: ", tom.global_position)
	print("  Ted at: ", ted.global_position)
	print("  Bob at: ", bob.global_position)
	
	# Disable wandering for Tom and Ted (they stand still)
	disable_wandering(tom)
	disable_wandering(ted)
	
	# Disable wandering for Bob (we'll control him)
	disable_wandering(bob)
	
	# Create dialogue box
	create_dialogue_box()
	
	# Update Bob's intent
	var bob_intent = bob.get_node_or_null("Wanderer/IntentMarker")
	if bob_intent:
		bob_intent.set_intent("→ TOM (SENDER)", Color.ORANGE)
	
	# Start sequence
	current_state = State.WALKING_TO_TOM
	target_position = tom.global_position
	print("[CourierScene] Bob walking to Tom...")

func _process(delta: float):
	match current_state:
		State.WALKING_TO_TOM:
			if move_towards(bob, tom.global_position, delta):
				arrive_at_tom()
		
		State.WALKING_TO_TED:
			if move_towards(bob, ted.global_position, delta):
				arrive_at_ted()

func move_towards(character: Node3D, target: Vector3, delta: float) -> bool:
	"""Move character toward target, return true when arrived"""
	var direction = (target - character.global_position).normalized()
	var distance = character.global_position.distance_to(target)
	
	if distance < 1.0:
		return true  # Arrived
	
	# Move
	character.global_position += direction * move_speed * delta
	
	# Face direction
	if direction.length() > 0.01:
		var target_rotation = atan2(direction.x, direction.z)
		character.rotation.y = lerp_angle(character.rotation.y, target_rotation, delta * 5.0)
	
	return false

func arrive_at_tom():
	"""Bob arrived at Tom"""
	current_state = State.AT_TOM
	print("[CourierScene] Bob arrived at Tom")
	
	# Update Bob's intent
	var intent = bob.get_node_or_null("Wanderer/IntentMarker")
	if intent:
		intent.set_intent("PICKUP FROM TOM", Color.GREEN)
	
	# Show dialogue
	show_dialogue("Elyraen (Tom): Here's the package for Vairis.")
	
	# Wait 2 seconds, then walk to Ted
	await get_tree().create_timer(2.0).timeout
	
	current_state = State.WALKING_TO_TED
	
	var bob_intent = bob.get_node_or_null("Wanderer/IntentMarker")
	if bob_intent:
		bob_intent.set_intent("→ TED (DELIVER)", Color.YELLOW)
	
	print("[CourierScene] Bob walking to Ted...")

func arrive_at_ted():
	"""Bob arrived at Ted"""
	current_state = State.AT_TED
	print("[CourierScene] Bob arrived at Ted")
	
	# Show dialogue
	show_dialogue("Vairis (Ted): Thanks for the delivery!")
	
	# Wait 2 seconds, then complete
	await get_tree().create_timer(2.0).timeout
	
	current_state = State.COMPLETE
	print("[CourierScene] Delivery complete!")
	
	var bob_intent = bob.get_node_or_null("Wanderer/IntentMarker")
	if bob_intent:
		bob_intent.set_intent("TASK COMPLETE", Color.GOLD)
	
	hide_dialogue()

func find_character(char_name: String) -> Node3D:
	"""Find character by name (case-insensitive)"""
	var scene_root = get_tree().current_scene
	for child in scene_root.get_children():
		if child is Node3D and child.name.to_lower() == char_name.to_lower():
			return child
	return null

func disable_wandering(character: Node3D):
	"""Stop wandering behavior for a character"""
	var wanderer = character.get_node_or_null("Wanderer")
	if wanderer:
		wanderer.queue_free()
		print("[CourierScene] Disabled wandering for ", character.name)

func create_dialogue_box():
	"""Create UI dialogue box"""
	dialogue_box = Panel.new()
	dialogue_box.custom_minimum_size = Vector2(400, 80)
	dialogue_box.position = Vector2(20, 500)
	dialogue_box.visible = false
	
	var label = Label.new()
	label.name = "DialogueLabel"
	label.add_theme_font_size_override("font_size", 20)
	label.position = Vector2(10, 10)
	label.size = Vector2(380, 60)
	dialogue_box.add_child(label)
	
	get_tree().current_scene.get_node("UI").add_child(dialogue_box)

func show_dialogue(text: String):
	"""Display dialogue text"""
	if dialogue_box:
		dialogue_box.visible = true
		dialogue_box.get_node("DialogueLabel").text = text
		print("[CourierScene] Dialogue: ", text)

func hide_dialogue():
	"""Hide dialogue box"""
	if dialogue_box:
		dialogue_box.visible = false
