extends CharacterBody3D

const SPEED = 5.0
const JUMP_VELOCITY = 4.5
var gravity = ProjectSettings.get_setting("physics/3d/default_gravity")

var max_speed = SPEED

# Track which directions were successfully tested
var forward_moved = false
var back_moved = false
var left_moved = false
var right_moved = false
var jump_applied = false

func _ready():
    # Programmatically set up input actions for WASD and Space
    _setup_input_action("move_left", KEY_A)
    _setup_input_action("move_right", KEY_D)
    _setup_input_action("move_forward", KEY_W)
    _setup_input_action("move_backward", KEY_S)
    _setup_input_action("jump", KEY_SPACE)
    
    # Check headless mode vs visual observer mode
    if DisplayServer.get_name() == "headless":
        run_test_sequence()
    else:
        run_visual_demo()

func _setup_input_action(action_name: String, keycode: int):
    if not InputMap.has_action(action_name):
        InputMap.add_action(action_name)
        var event = InputEventKey.new()
        event.physical_keycode = keycode
        InputMap.action_add_event(action_name, event)

func _physics_process(delta):
    # Apply gravity
    if not is_on_floor():
        velocity.y -= gravity * delta

    # Standard movement input handling (based on press state)
    var input_dir = Input.get_vector("move_left", "move_right", "move_forward", "move_backward")
    var direction = (transform.basis * Vector3(input_dir.x, 0, input_dir.y)).normalized()
    
    if direction:
        velocity.x = direction.x * max_speed
        velocity.z = direction.z * max_speed
    else:
        velocity.x = move_toward(velocity.x, 0, max_speed)
        velocity.z = move_toward(velocity.z, 0, max_speed)

    # Jump handling
    if Input.is_action_just_pressed("jump") and is_on_floor():
        velocity.y = JUMP_VELOCITY

    move_and_slide()

func run_visual_demo():
    print("MILESTONE_006_VISUAL_DEMO_STARTED")
    max_speed = 1.5 # Walk slowly for human visual observation
    
    while true:
        # 1. Hold still for 1 second
        await get_tree().create_timer(1.0).timeout
        
        # 2. Walk forward slowly for 3 seconds
        Input.action_press("move_forward")
        await get_tree().create_timer(3.0).timeout
        Input.action_release("move_forward")
        
        # 3. Hold still for 1 second
        await get_tree().create_timer(1.0).timeout
        
        # 4. Jump in place once
        Input.action_press("jump")
        await get_tree().physics_frame
        Input.action_release("jump")
        # Wait for jump completion
        await get_tree().create_timer(1.5).timeout
        
        # 5. Hold still for 1 second
        await get_tree().create_timer(1.0).timeout
        
        # 6. Walk backward slowly for 3 seconds
        Input.action_press("move_backward")
        await get_tree().create_timer(3.0).timeout
        Input.action_release("move_backward")

func run_test_sequence():
    print("MILESTONE_006_GODOT_RUNNER_STARTED")
    var start_pos = global_position
    print("MILESTONE_006_INITIAL_POSITION: ", start_pos)
    
    # Wait for things to settle on the floor
    for i in range(10):
        await get_tree().physics_frame
    
    # 1. Test FORWARD (W key -> moves in -Z)
    var before = global_position
    Input.action_press("move_forward")
    for i in range(15):
        await get_tree().physics_frame
    Input.action_release("move_forward")
    for i in range(5):
        await get_tree().physics_frame
    var after = global_position
    if after.z < before.z - 0.1:
        forward_moved = true
        print("MILESTONE_006_FORWARD_MOVED: TRUE")
    else:
        print("MILESTONE_006_FORWARD_MOVED: FALSE")

    # 2. Test BACK (S key -> moves in +Z)
    before = global_position
    Input.action_press("move_backward")
    for i in range(15):
        await get_tree().physics_frame
    Input.action_release("move_backward")
    for i in range(5):
        await get_tree().physics_frame
    after = global_position
    if after.z > before.z + 0.1:
        back_moved = true
        print("MILESTONE_006_BACK_MOVED: TRUE")
    else:
        print("MILESTONE_006_BACK_MOVED: FALSE")

    # 3. Test LEFT (A key -> moves in -X)
    before = global_position
    Input.action_press("move_left")
    for i in range(15):
        await get_tree().physics_frame
    Input.action_release("move_left")
    for i in range(5):
        await get_tree().physics_frame
    after = global_position
    if after.x < before.x - 0.1:
        left_moved = true
        print("MILESTONE_006_LEFT_MOVED: TRUE")
    else:
        print("MILESTONE_006_LEFT_MOVED: FALSE")

    # 4. Test RIGHT (D key -> moves in +X)
    before = global_position
    Input.action_press("move_right")
    for i in range(15):
        await get_tree().physics_frame
    Input.action_release("move_right")
    for i in range(5):
        await get_tree().physics_frame
    after = global_position
    if after.x > before.x + 0.1:
        right_moved = true
        print("MILESTONE_006_RIGHT_MOVED: TRUE")
    else:
        print("MILESTONE_006_RIGHT_MOVED: FALSE")

    # 5. Test JUMP (Space key -> moves in +Y)
    before = global_position
    Input.action_press("jump")
    # Action press triggers is_action_just_pressed next frame
    await get_tree().physics_frame
    Input.action_release("jump")
    for i in range(5):
        await get_tree().physics_frame
    after = global_position
    if after.y > before.y + 0.1:
        jump_applied = true
        print("MILESTONE_006_JUMP_APPLIED: TRUE")
    else:
        print("MILESTONE_006_JUMP_APPLIED: FALSE")

    # Final positions
    var end_pos = global_position
    print("MILESTONE_006_FINAL_POSITION: ", end_pos)
    print("MILESTONE_006_DELTA: ", end_pos - start_pos)

    # Output completed status
    if forward_moved and back_moved and left_moved and right_moved and jump_applied:
        print("MILESTONE_006_GODOT_RUNNER_DONE: TRUE")
        get_tree().quit(0)
    else:
        print("MILESTONE_006_GODOT_RUNNER_DONE: FALSE")
        get_tree().quit(1)
