extends Node
## CharacterWanderer - Makes NPCs wander around naturally

# Movement settings
var speed: float = 2.0
var wander_radius: float = 8.0
var idle_time_min: float = 2.0
var idle_time_max: float = 5.0
var walk_time_min: float = 3.0
var walk_time_max: float = 8.0

# State
enum State { IDLE, WALKING }
var current_state: State = State.IDLE
var target_position: Vector3
var state_timer: float = 0.0
var home_position: Vector3
var entity: Node3D  # Reference to parent entity
var intent_marker: Node3D  # Shows current intent

func _ready():
	# Get reference to parent entity (the MeshInstance3D)
	entity = get_parent()
	
	if not entity:
		push_error("[Wanderer] No parent entity!")
		return
	
	# Remember spawn position as "home"
	home_position = entity.global_position
	
	print("[Wanderer] Initialized for ", entity.name, " at ", home_position)
	
	# Create intent marker
	intent_marker = Node3D.new()
	intent_marker.set_script(load("res://godot/IntentMarker.gd"))
	entity.add_child(intent_marker)
	
	# Start with random idle time
	start_idle()

func _process(delta: float):
	if not entity:
		return
	
	state_timer -= delta
	
	if state_timer <= 0:
		# Time to change state
		match current_state:
			State.IDLE:
				start_walking()
			State.WALKING:
				start_idle()
	
	# Execute current state
	match current_state:
		State.WALKING:
			walk_towards_target(delta)

func start_idle():
	"""Begin idle state - standing still"""
	current_state = State.IDLE
	state_timer = randf_range(idle_time_min, idle_time_max)
	
	if intent_marker:
		intent_marker.set_intent("IDLE", Color.GRAY)
	
	if entity:
		print("[Wanderer] ", entity.name, " idling for ", state_timer, "s")

func start_walking():
	"""Begin walking state - pick new destination"""
	current_state = State.WALKING
	state_timer = randf_range(walk_time_min, walk_time_max)
	
	# Pick random point within radius of home
	var random_angle = randf() * TAU
	var random_distance = randf() * wander_radius
	
	target_position = home_position + Vector3(
		cos(random_angle) * random_distance,
		0.0,  # Stay on ground
		sin(random_angle) * random_distance
	)
	
	if intent_marker:
		intent_marker.set_intent("WANDER", Color.LIGHT_BLUE)
	
	if entity:
		print("[Wanderer] ", entity.name, " walking to ", target_position)

func walk_towards_target(delta: float):
	"""Move towards target position"""
	if not entity:
		return
	
	var direction = (target_position - entity.global_position).normalized()
	var distance = entity.global_position.distance_to(target_position)
	
	# Stop if close enough
	if distance < 0.5:
		start_idle()
		return
	
	# Move entity (parent)
	var move_amount = speed * delta
	entity.global_position += direction * move_amount
	
	# Face movement direction (rotate around Y axis)
	if direction.length() > 0.01:
		var target_rotation = atan2(direction.x, direction.z)
		entity.rotation.y = lerp_angle(entity.rotation.y, target_rotation, delta * 5.0)
