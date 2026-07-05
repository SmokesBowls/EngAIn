# player_movement.gd
extends Node3D

var initial_position = Vector3.ZERO
var final_position = Vector3.ZERO
var delta = Vector3.ZERO
var forward_moved = false
var back_moved = false
var left_moved = false
var right_moved = false
var jump_applied = false

func _ready():
    initial_position = transform.origin
    add_child(MovementRunner.new())

func _exit_tree():
    var output = f"""
MILESTONE_006_GODOT_RUNNER_STARTED
MILESTONE_006_INITIAL_POSITION: {initial_position}
MILESTONE_006_FINAL_POSITION: {final_position}
MILESTONE_006_DELTA: {delta}
MILESTONE_006_FORWARD_MOVED: {forward_moved}
MILESTONE_006_BACK_MOVED: {back_moved}
MILESTONE_006_LEFT_MOVED: {left_moved}
MILESTONE_006_RIGHT_MOVED: {right_moved}
MILESTONE_006_JUMP_APPLIED: {jump_applied}
MILESTONE_006_GODOT_RUNNER_DONE: TRUE
"""
    File.open("player_movement_output.txt", "w").store_string(output)
    get_tree().quit(0)

func _input(event):
    if event is InputEventKey:
        if event.pressed:
            match event.scancode:
                KEY_W: move_forward()
                KEY_A: move_left()
                KEY_S: move_backward()
                KEY_D: move_right()
                KEY_SPACE: jump()
        else:
            match event.scancode:
                KEY_W: release_forward()
                KEY_A: release_left()
                KEY_S: release_backward()
                KEY_D: release_right()

func move_forward():
    global_transform.origin += Vector3.UP * 0.1
    forward_moved = true

func move_backward():
    global_transform.origin -= Vector3.UP * 0.1
    back_moved = true

func move_left():
    global_transform.origin -= Vector3.RIGHT * 0.1
    left_moved = true

func move_right():
    global_transform.origin += Vector3.RIGHT * 0.1
    right_moved = true

func jump():
    if is_on_floor():
        global_transform.origin += Vector3.UP * 2.0
        jump_applied = true

func release_forward():
    pass

func release_backward():
    pass

func release_left():
    pass

func release_right():
    pass
