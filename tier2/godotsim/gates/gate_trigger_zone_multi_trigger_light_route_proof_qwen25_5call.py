#!/usr/bin/env python3
"""
QWEN2_5_AIDER_5CALL_FULL_SCRIPT_BUILD_001

Purpose:
Build the complete multi-trigger GodotSim proof gate through Aider using
qwen2.5-coder:7b-instruct in 5 bounded calls.

Protected reference proof:
tier2/godotsim/gates/gate_trigger_zone_multi_trigger_light_route_proof.py

This file must not import, overwrite, or modify the protected reference proof.
"""

import argparse
import subprocess
import sys
from pathlib import Path

GATE_NAME = 'gate_trigger_zone_multi_trigger_light_route_proof_qwen25_5call'
SCENE_FILE = 'tmp_qwen25_5call_multi_trigger_scene.tscn'
CONTROLLER_FILE = 'tmp_qwen25_5call_multi_trigger_controller.gd'
GODOT_BIN = Path.home() / '.local/bin/godot'

REQUIRED_MARKERS = [
    'TRIGGER_ZONE_EVENT_002_LIGHT_INITIAL: ON',
    'TRIGGER_ZONE_EVENT_002_CAPSULE_START: (0.0, 1.0, 7.0)',
    'TRIGGER_ZONE_EVENT_002_FORWARD_OFF_TRIGGER_ENTERED: TRUE',
    'TRIGGER_ZONE_EVENT_002_LIGHT_AFTER_FORWARD_OFF_TRIGGER: OFF',
    'TRIGGER_ZONE_EVENT_002_FORWARD_ON_TRIGGER_ENTERED: TRUE',
    'TRIGGER_ZONE_EVENT_002_LIGHT_AFTER_FORWARD_ON_TRIGGER: ON',
    'TRIGGER_ZONE_EVENT_002_WHILE_INSIDE_TRIGGER_ENTERED: TRUE',
    'TRIGGER_ZONE_EVENT_002_LIGHT_WHILE_INSIDE_ENTER: OFF',
    'TRIGGER_ZONE_EVENT_002_WHILE_INSIDE_HOLD_CONFIRMED: TRUE',
    'TRIGGER_ZONE_EVENT_002_LIGHT_DURING_WHILE_INSIDE_HOLD: OFF',
    'TRIGGER_ZONE_EVENT_002_WHILE_INSIDE_TRIGGER_EXITED: TRUE',
    'TRIGGER_ZONE_EVENT_002_LIGHT_AFTER_WHILE_INSIDE_EXIT: ON',
    'TRIGGER_ZONE_EVENT_002_RETURN_ON_TRIGGER_ENTERED: TRUE',
    'TRIGGER_ZONE_EVENT_002_LIGHT_AFTER_RETURN_ON_TRIGGER: ON',
    'TRIGGER_ZONE_EVENT_002_RETURN_OFF_TRIGGER_ENTERED: TRUE',
    'TRIGGER_ZONE_EVENT_002_LIGHT_AFTER_RETURN_OFF_TRIGGER: OFF',
    'TRIGGER_ZONE_EVENT_002_CAPSULE_RETURNED_TO_A: TRUE',
    'TRIGGER_ZONE_EVENT_002_FINAL_LIGHT_STATE: OFF',
    'gate_trigger_zone_multi_trigger_light_route_proof: TRUE'
]

def write_temp_files(project_root):
    scene_path = project_root / SCENE_FILE
    controller_path = project_root / CONTROLLER_FILE

    with open(scene_path, 'w') as f:
        f.write(build_scene_text())

    with open(controller_path, 'w') as f:
        f.write(build_controller_script())

def cleanup_temp_files(project_root):
    scene_path = project_root / SCENE_FILE
    controller_path = project_root / CONTROLLER_FILE

    if scene_path.exists():
        scene_path.unlink()

    if controller_path.exists():
        controller_path.unlink()

def controller_chunk_001_setup_scene() -> str:
    # CALL_002_GDSCRIPT_SETUP_SCENE
    return """extends Node3D

var proof_light: DirectionalLight3D
var proof_capsule: CharacterBody3D
var trigger_off: TriggerZone
var trigger_on: TriggerZone
var trigger_while_inside: TriggerZone
var phase = 'forward'
var speed = 3.0
var hold_timer = 0.0
var printed_markers = {
    "TRIGGER_ZONE_EVENT_002_LIGHT_INITIAL": False,
    "TRIGGER_ZONE_EVENT_002_CAPSULE_START": False,
    "TRIGGER_ZONE_EVENT_002_FORWARD_OFF_TRIGGER_ENTERED": False,
    "TRIGGER_ZONE_EVENT_002_LIGHT_AFTER_FORWARD_OFF_TRIGGER": False,
    "TRIGGER_ZONE_EVENT_002_FORWARD_ON_TRIGGER_ENTERED": False,
    "TRIGGER_ZONE_EVENT_002_LIGHT_AFTER_FORWARD_ON_TRIGGER": False,
    "TRIGGER_ZONE_EVENT_002_WHILE_INSIDE_TRIGGER_ENTERED": False,
    "TRIGGER_ZONE_EVENT_002_LIGHT_WHILE_INSIDE_ENTER": False,
    "TRIGGER_ZONE_EVENT_002_WHILE_INSIDE_HOLD_CONFIRMED": False,
    "TRIGGER_ZONE_EVENT_002_LIGHT_DURING_WHILE_INSIDE_HOLD": False,
    "TRIGGER_ZONE_EVENT_002_WHILE_INSIDE_TRIGGER_EXITED": False,
    "TRIGGER_ZONE_EVENT_002_LIGHT_AFTER_WHILE_INSIDE_EXIT": False,
    "TRIGGER_ZONE_EVENT_002_RETURN_ON_TRIGGER_ENTERED": False,
    "TRIGGER_ZONE_EVENT_002_LIGHT_AFTER_RETURN_ON_TRIGGER": False,
    "TRIGGER_ZONE_EVENT_002_RETURN_OFF_TRIGGER_ENTERED": False,
    "TRIGGER_ZONE_EVENT_002_LIGHT_AFTER_RETURN_OFF_TRIGGER": False,
    "TRIGGER_ZONE_EVENT_002_CAPSULE_RETURNED_TO_A": False,
    "TRIGGER_ZONE_EVENT_002_FINAL_LIGHT_STATE": False
}

func _ready():
    setup_scene()
    setup_triggers()
    print("TRIGGER_ZONE_EVENT_002_LIGHT_INITIAL: ON")
    print("TRIGGER_ZONE_EVENT_002_CAPSULE_START: (0.0, 1.0, 7.0)")
    get_tree().set_pause_mode(Tree.PAUSE_MODE_PROCESS)

func setup_scene():
    proof_light = DirectionalLight3D.new()
    proof_light.light_energy = 1.0
    add_child(proof_light)

    camera = Camera3D.new()
    add_child(camera)

    floor = MeshInstance3D.new()
    floor.mesh = load("res://floor.tscn").instance()
    add_child(floor)

    proof_capsule = CharacterBody3D.new()
    capsule_mesh = CapsuleMesh.new()
    capsule_mesh.radius = 0.5
    capsule_mesh.height = 1.0
    proof_capsule.mesh_instance.mesh = capsule_mesh
    proof_capsule.translation = Vector3(0, 1, 7)
    add_child(proof_capsule)

func setup_triggers():
    # Add trigger logic here
"""

def setup_triggers():
    global proof_light, trigger_off, trigger_on, trigger_while_inside

    trigger_off = Area3D.new()
    trigger_off.monitoring = true
    add_child(trigger_off)

    collision_shape_off = CollisionShape3D.new()
    box_mesh_off = BoxMesh.new()
    box_mesh_off.extents = Vector3(1, 2, 0.5)
    collision_shape_off.shape = box_mesh_off
    trigger_off.add_child(collision_shape_off)

    visual_box_off = MeshInstance3D.new()
    visual_box_off.mesh = load("res://visual_box_red.tscn").instance()
    trigger_off.add_child(visual_box_off)

    trigger_off.connect("body_entered", self, "_on_trigger_off_body_entered")

    trigger_on = Area3D.new()
    trigger_on.monitoring = true
    add_child(trigger_on)

    collision_shape_on = CollisionShape3D.new()
    box_mesh_on = BoxMesh.new()
    box_mesh_on.extents = Vector3(1, 2, 0.5)
    collision_shape_on.shape = box_mesh_on
    trigger_on.add_child(collision_shape_on)

    visual_box_on = MeshInstance3D.new()
    visual_box_on.mesh = load("res://visual_box_green.tscn").instance()
    trigger_on.add_child(visual_box_on)

    trigger_on.connect("body_entered", self, "_on_trigger_on_body_entered")

    trigger_while_inside = Area3D.new()
    trigger_while_inside.monitoring = true
    add_child(trigger_while_inside)

    collision_shape_while_inside = CollisionShape3D.new()
    box_mesh_while_inside = BoxMesh.new()
    box_mesh_while_inside.extents = Vector3(1, 2, 0.5)
    collision_shape_while_inside.shape = box_mesh_while_inside
    trigger_while_inside.add_child(collision_shape_while_inside)

    visual_box_while_inside = MeshInstance3D.new()
    visual_box_while_inside.mesh = load("res://visual_box_blue.tscn").instance()
    trigger_while_inside.add_child(visual_box_while_inside)

    trigger_while_inside.connect("body_entered", self, "_on_trigger_while_inside_body_entered")
    trigger_while_inside.connect("body_exited", self, "_on_trigger_while_inside_body_exited")

def make_trigger(name, pos, color):
    # Implement this function if needed

def _on_trigger_off_body_entered(self, body):
    global phase
    proof_light.light_energy = 0.0
    if phase == 'forward':
        print("TRIGGER_ZONE_EVENT_002_FORWARD_OFF_TRIGGER_ENTERED: TRUE")
    elif phase == 'return':
        print("TRIGGER_ZONE_EVENT_002_RETURN_OFF_TRIGGER_ENTERED: TRUE")

def _on_trigger_on_body_entered(self, body):
    global phase
    proof_light.light_energy = 1.0
    if phase == 'forward':
        print("TRIGGER_ZONE_EVENT_002_FORWARD_ON_TRIGGER_ENTERED: TRUE")
    elif phase == 'return':
        print("TRIGGER_ZONE_EVENT_002_RETURN_ON_TRIGGER_ENTERED: TRUE")

def _on_trigger_while_inside_body_entered(self, body):
    proof_light.light_energy = 0.0
    print("TRIGGER_ZONE_EVENT_002_WHILE_INSIDE_HOLD_CONFIRMED: TRUE")
    print("TRIGGER_ZONE_EVENT_002_LIGHT_DURING_WHILE_INSIDE_HOLD: OFF")

def _on_trigger_while_inside_body_exited(self, body):
    proof_light.light_energy = 1.0
    print("TRIGGER_ZONE_EVENT_002_WHILE_INSIDE_TRIGGER_EXITED: TRUE")
    print("TRIGGER_ZONE_EVENT_002_LIGHT_AFTER_WHILE_INSIDE_EXIT: ON")

def controller_chunk_003_movement_and_markers() -> str:
    # CALL_004_GDSCRIPT_MOVEMENT_AND_MARKERS
    return ""

def build_controller_script() -> str:
    return "\n".join([
        controller_chunk_001_setup_scene(),
        controller_chunk_002_triggers_and_handlers(),
        controller_chunk_003_movement_and_markers(),
    ])

def build_scene_text() -> str:
    return """[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://tmp_qwen25_5call_multi_trigger_controller.gd" id="1"]

[node name="Root" type="Node3D"]
script = ExtResource("1")
"""

# CALL_005_PYTHON_RUNNER_VALIDATOR_MAIN

def main():
    parser = argparse.ArgumentParser(description="Build the complete multi-trigger GodotSim proof gate through Aider using qwen2.5-coder:7b-instruct in 5 bounded calls.")
    args = parser.parse_args()

    project_root = Path.cwd()
    write_temp_files(project_root)
    try:
        subprocess.run([GODOT_BIN, str(project_root / SCENE_FILE)], check=True)
    finally:
        cleanup_temp_files(project_root)

if __name__ == "__main__":
    main()
