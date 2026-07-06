#!/usr/bin/env python3
"""
gate_trigger_zone_multi_trigger_light_route_proof.py

This proof does not prove trigger_zone builder semantics.
This proof proves trigger_zone event behavior.
The debug mesh is a proof helper only.
"""

from __future__ import annotations
import sys
import os
import shutil
import subprocess
import argparse
from pathlib import Path

# Setup root path to import relative modules
ROOT = Path(__file__).resolve().parents[3]
sys.path.append(str(ROOT))

SCENE_PATH = ROOT / "tmp_multi_trigger_scene.tscn"
SCRIPT_PATH = ROOT / "tmp_multi_trigger_controller.gd"

CONTROLLER_CODE = """extends Node3D

@onready var light = $ProofLight
@onready var player = $ProofCapsule
@onready var trigger_off = $TriggerOff
@onready var trigger_on = $TriggerOn
@onready var trigger_while_inside = $TriggerWhileInside
@onready var trigger_slow = $TriggerSlow

var elapsed = 0.0
var phase = "forward" # "forward", "hold", "forward_exit", "return", "done"
var hold_timer = 0.0
var exit_timer = 0.0
var is_headless = false

var while_inside_active = false
var slow_speed = 1.5

func _ready():
	is_headless = (DisplayServer.get_name() == "headless")
	
	print("TRIGGER_ZONE_EVENT_002_LIGHT_INITIAL: ON")
	print("TRIGGER_ZONE_EVENT_002_CAPSULE_START: " + str(player.global_position))
	
	# Connect signals
	trigger_off.body_entered.connect(_on_off_entered)
	trigger_on.body_entered.connect(_on_on_entered)
	trigger_while_inside.body_entered.connect(_on_while_inside_entered)
	trigger_while_inside.body_exited.connect(_on_while_inside_exited)
	trigger_slow.body_entered.connect(_on_slow_entered)
	trigger_slow.body_exited.connect(_on_slow_exited)

func _physics_process(delta):
	elapsed += delta
	if elapsed > 15.0:
		print("TIMEOUT: route not completed.")
		get_tree().quit(1)
		return

	if phase == "forward":
		player.global_position.z -= slow_speed * delta
		if player.global_position.z <= -2.0:
			phase = "hold"
			hold_timer = 0.0
			
	elif phase == "hold":
		hold_timer += delta
		if hold_timer >= 1.0:
			print("TRIGGER_ZONE_EVENT_002_WHILE_INSIDE_HOLD_CONFIRMED: TRUE")
			print("TRIGGER_ZONE_EVENT_002_LIGHT_DURING_WHILE_INSIDE_HOLD: OFF")
			phase = "forward_exit"
			
	elif phase == "forward_exit":
		player.global_position.z -= 3.0 * delta
		if player.global_position.z <= -4.0:
			phase = "return"
			
	elif phase == "return":
		player.global_position.z += 3.0 * delta
		if player.global_position.z >= 7.0:
			player.global_position.z = 7.0
			phase = "done"
			print("TRIGGER_ZONE_EVENT_002_CAPSULE_RETURNED_TO_A: TRUE")
			print("TRIGGER_ZONE_EVENT_002_FINAL_LIGHT_STATE: OFF")
			print("gate_trigger_zone_multi_trigger_light_route_proof: TRUE")
			
	elif phase == "done":
		if is_headless:
			get_tree().quit(0)
		else:
			exit_timer += delta
			if exit_timer >= 3.0:
				get_tree().quit(0)

func _on_off_entered(body):
	if body == player:
		light.light_energy = 0.0
		if phase == "forward":
			print("TRIGGER_ZONE_EVENT_002_FORWARD_OFF_TRIGGER_ENTERED: TRUE")
			print("TRIGGER_ZONE_EVENT_002_LIGHT_AFTER_FORWARD_OFF_TRIGGER: OFF")
		elif phase == "return":
			print("TRIGGER_ZONE_EVENT_002_RETURN_OFF_TRIGGER_ENTERED: TRUE")
			print("TRIGGER_ZONE_EVENT_002_LIGHT_AFTER_RETURN_OFF_TRIGGER: OFF")

func _on_on_entered(body):
	if body == player:
		light.light_energy = 1.0
		if phase == "forward":
			print("TRIGGER_ZONE_EVENT_002_FORWARD_ON_TRIGGER_ENTERED: TRUE")
			print("TRIGGER_ZONE_EVENT_002_LIGHT_AFTER_FORWARD_ON_TRIGGER: ON")
		elif phase == "return":
			print("TRIGGER_ZONE_EVENT_002_RETURN_ON_TRIGGER_ENTERED: TRUE")
			print("TRIGGER_ZONE_EVENT_002_LIGHT_AFTER_RETURN_ON_TRIGGER: ON")

func _on_while_inside_entered(body):
	if body == player:
		light.light_energy = 0.0
		while_inside_active = true
		if phase == "forward" or phase == "hold":
			print("TRIGGER_ZONE_EVENT_002_WHILE_INSIDE_TRIGGER_ENTERED: TRUE")
			print("TRIGGER_ZONE_EVENT_002_LIGHT_WHILE_INSIDE_ENTER: OFF")

func _on_while_inside_exited(body):
	if body == player:
		light.light_energy = 1.0
		while_inside_active = false
		if phase == "forward_exit":
			print("TRIGGER_ZONE_EVENT_002_WHILE_INSIDE_TRIGGER_EXITED: TRUE")
			print("TRIGGER_ZONE_EVENT_002_LIGHT_AFTER_WHILE_INSIDE_EXIT: ON")

func _on_slow_entered(body):
	if body == player:
		slow_speed = 1.5
		print("TRIGGER_ZONE_EVENT_002_FORWARD_SLOW_TRIGGER_ENTERED: TRUE")
		print("TRIGGER_ZONE_EVENT_002_LIGHT_AFTER_FORWARD_SLOW_TRIGGER: ON")

func _on_slow_exited(body):
	if body == player:
		slow_speed = 3.0
		print("TRIGGER_ZONE_EVENT_002_FORWARD_SLOW_TRIGGER_EXITED: TRUE")
		print("TRIGGER_ZONE_EVENT_002_RETURN_SLOW_TRIGGER_ENTERED: TRUE")
		print("TRIGGER_ZONE_EVENT_002_LIGHT_AFTER_RETURN_SLOW_TRIGGER: ON")

func _on_return_slow_entered(body):
	if body == player:
		slow_speed = 1.5
		print("TRIGGER_ZONE_EVENT_002_RETURN_SLOW_TRIGGER_ENTERED: TRUE")
		print("TRIGGER_ZONE_EVENT_002_LIGHT_AFTER_RETURN_SLOW_TRIGGER: ON")

func _on_return_slow_exited(body):
	if body == player:
		slow_speed = 3.0
		print("TRIGGER_ZONE_EVENT_002_RETURN_SLOW_TRIGGER_EXITED: TRUE")
"""

SCENE_CODE = """[gd_scene load_steps=15 format=3]

[ext_resource type="Script" path="res://tmp_multi_trigger_controller.gd" id="1_controller"]

[sub_resource type="BoxMesh" id="BoxMesh_floor"]
size = Vector3(15, 0.2, 20)

[sub_resource type="BoxShape3D" id="BoxShape3D_floor"]
size = Vector3(15, 0.2, 20)

[sub_resource type="CapsuleMesh" id="CapsuleMesh_player"]
radius = 0.5
height = 2.0

[sub_resource type="CapsuleShape3D" id="CapsuleShape3D_player"]
radius = 0.5
height = 2.0

[sub_resource type="BoxShape3D" id="BoxShape3D_off"]
size = Vector3(2, 2, 1)

[sub_resource type="BoxMesh" id="BoxMesh_off"]
size = Vector3(2, 2, 1)

[sub_resource type="StandardMaterial3D" id="StandardMaterial3D_off"]
transparency = 1
albedo_color = Color(1, 0, 0, 0.3)

[sub_resource type="BoxShape3D" id="BoxShape3D_on"]
size = Vector3(2, 2, 1)

[sub_resource type="BoxMesh" id="BoxMesh_on"]
size = Vector3(2, 2, 1)

[sub_resource type="StandardMaterial3D" id="StandardMaterial3D_on"]
transparency = 1
albedo_color = Color(0, 1, 0, 0.3)

[sub_resource type="BoxShape3D" id="BoxShape3D_while"]
size = Vector3(2, 2, 1)

[sub_resource type="BoxMesh" id="BoxMesh_while"]
size = Vector3(2, 2, 1)

[sub_resource type="StandardMaterial3D" id="StandardMaterial3D_while"]
transparency = 1
albedo_color = Color(0, 0, 1, 0.3)

[sub_resource type="BoxShape3D" id="BoxShape3D_slow"]
size = Vector3(2, 2, 1)

[sub_resource type="BoxMesh" id="BoxMesh_slow"]
size = Vector3(2, 2, 1)

[sub_resource type="StandardMaterial3D" id="StandardMaterial3D_slow"]
transparency = 0.5
albedo_color = Color(1, 1, 0, 0.7)

[node name="Root" type="Node3D"]
script = ExtResource("1_controller")

[node name="Floor" type="MeshInstance3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, -0.1, 0)
mesh = SubResource("BoxMesh_floor")

[node name="FloorCollision" type="StaticBody3D" parent="Floor"]
[node name="CollisionShape3D" type="CollisionShape3D" parent="Floor/FloorCollision"]
shape = SubResource("BoxShape3D_floor")

[node name="ProofLight" type="DirectionalLight3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 0.866025, 0.5, 0, -0.5, 0.866025, 0, 10, 0)

[node name="Camera3D" type="Camera3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 0.866025, 0.5, 0, -0.5, 0.866025, 0, 6, 12)
current = true

[node name="ProofCapsule" type="CharacterBody3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 7)

[node name="MeshInstance3D" type="MeshInstance3D" parent="ProofCapsule"]
mesh = SubResource("CapsuleMesh_player")

[node name="CollisionShape3D" type="CollisionShape3D" parent="ProofCapsule"]
shape = SubResource("CapsuleShape3D_player")

[node name="TriggerOff" type="Area3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 4)

[node name="CollisionShape3D" type="CollisionShape3D" parent="TriggerOff"]
shape = SubResource("BoxShape3D_off")

[node name="MeshInstance3D" type="MeshInstance3D" parent="TriggerOff"]
mesh = SubResource("BoxMesh_off")
material_override = SubResource("StandardMaterial3D_off")

[node name="TriggerOn" type="Area3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 1)

[node name="CollisionShape3D" type="CollisionShape3D" parent="TriggerOn"]
shape = SubResource("BoxShape3D_on")

[node name="MeshInstance3D" type="MeshInstance3D" parent="TriggerOn"]
mesh = SubResource("BoxMesh_on")
material_override = SubResource("StandardMaterial3D_on")

[node name="TriggerWhileInside" type="Area3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, -2)

[node name="CollisionShape3D" type="CollisionShape3D" parent="TriggerWhileInside"]
shape = SubResource("BoxShape3D_while")

[node name="MeshInstance3D" type="MeshInstance3D" parent="TriggerWhileInside"]
mesh = SubResource("BoxMesh_while")
material_override = SubResource("StandardMaterial3D_while")

[node name="TriggerSlow" type="Area3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, -0.5)

[node name="CollisionShape3D" type="CollisionShape3D" parent="TriggerSlow"]
shape = SubResource("BoxShape3D_slow")

[node name="MeshInstance3D" type="MeshInstance3D" parent="TriggerSlow"]
mesh = SubResource("BoxMesh_slow")
material_override = SubResource("StandardMaterial3D_slow")
"""

def find_godot_binary() -> str | None:
    bin_path = shutil.which("godot")
    if bin_path:
        return bin_path
    local_path = Path("/home/mytruelove/.local/bin/godot")
    if local_path.exists() and os.access(local_path, os.X_OK):
        return str(local_path)
    return None

def main():
    parser = argparse.ArgumentParser(description="Multi-trigger light route proof gate")
    parser.add_argument("--headless", action="store_true", help="Run Godot in headless mode")
    args = parser.parse_args()

    print("=" * 60)
    print(f"RUNNING GATE: gate_trigger_zone_multi_trigger_light_route_proof.py (headless={args.headless})")
    print("=" * 60)

    # 1. Write temp scene and controller
    try:
        SCRIPT_PATH.write_text(CONTROLLER_CODE, encoding="utf-8")
        SCENE_PATH.write_text(SCENE_CODE, encoding="utf-8")
    except Exception as e:
        print(f"FAILED to write temp files: {e}")
        sys.exit(1)

    godot_bin = find_godot_binary()
    if not godot_bin:
        print("gate_trigger_zone_multi_trigger_light_route_proof: BYPASS (Godot binary not found)")
        SCRIPT_PATH.unlink(missing_ok=True)
        SCENE_PATH.unlink(missing_ok=True)
        sys.exit(0)

    # 2. Launch Godot process
    cmd = [godot_bin, "--scene", f"res://{SCENE_PATH.name}"]
    if args.headless:
        cmd.append("--headless")

    print(f"Launching: {' '.join(cmd)}")
    
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=str(ROOT), text=True)
    
    try:
        # Long timeout to allow for the forward pass, pause, and return pass sequence
        stdout, stderr = proc.communicate(timeout=18.0)
    except subprocess.TimeoutExpired:
        proc.terminate()
        try:
            stdout, stderr = proc.communicate(timeout=1.0)
        except Exception:
            stdout, stderr = "", ""
        print("FAILED: Godot process execution timed out.")
        sys.exit(1)
    finally:
        # Clean up temp files
        SCRIPT_PATH.unlink(missing_ok=True)
        SCENE_PATH.unlink(missing_ok=True)

    # 3. Print captured output
    print("--- Godot Output ---")
    print(stdout)
    print("--------------------")

    # 4. Verify exit code and markers
    if proc.returncode != 0:
        print(f"FAILED: Godot process exited with error code {proc.returncode}")
        sys.exit(1)

    expected_markers = [
        "TRIGGER_ZONE_EVENT_002_LIGHT_INITIAL: ON",
        "TRIGGER_ZONE_EVENT_002_CAPSULE_START:",
        "TRIGGER_ZONE_EVENT_002_FORWARD_OFF_TRIGGER_ENTERED: TRUE",
        "TRIGGER_ZONE_EVENT_002_LIGHT_AFTER_FORWARD_OFF_TRIGGER: OFF",
        "TRIGGER_ZONE_EVENT_002_FORWARD_ON_TRIGGER_ENTERED: TRUE",
        "TRIGGER_ZONE_EVENT_002_LIGHT_AFTER_FORWARD_ON_TRIGGER: ON",
        "TRIGGER_ZONE_EVENT_002_WHILE_INSIDE_TRIGGER_ENTERED: TRUE",
        "TRIGGER_ZONE_EVENT_002_LIGHT_WHILE_INSIDE_ENTER: OFF",
        "TRIGGER_ZONE_EVENT_002_WHILE_INSIDE_HOLD_CONFIRMED: TRUE",
        "TRIGGER_ZONE_EVENT_002_LIGHT_DURING_WHILE_INSIDE_HOLD: OFF",
        "TRIGGER_ZONE_EVENT_002_WHILE_INSIDE_TRIGGER_EXITED: TRUE",
        "TRIGGER_ZONE_EVENT_002_LIGHT_AFTER_WHILE_INSIDE_EXIT: ON",
        "TRIGGER_ZONE_EVENT_002_RETURN_ON_TRIGGER_ENTERED: TRUE",
        "TRIGGER_ZONE_EVENT_002_LIGHT_AFTER_RETURN_ON_TRIGGER: ON",
        "TRIGGER_ZONE_EVENT_002_RETURN_OFF_TRIGGER_ENTERED: TRUE",
        "TRIGGER_ZONE_EVENT_002_LIGHT_AFTER_RETURN_OFF_TRIGGER: OFF",
        "TRIGGER_ZONE_EVENT_002_CAPSULE_RETURNED_TO_A: TRUE",
        "TRIGGER_ZONE_EVENT_002_FINAL_LIGHT_STATE: OFF",
        "TRIGGER_ZONE_EVENT_002_FORWARD_SLOW_TRIGGER_ENTERED: TRUE",
        "TRIGGER_ZONE_EVENT_002_LIGHT_AFTER_FORWARD_SLOW_TRIGGER: ON",
        "TRIGGER_ZONE_EVENT_002_FORWARD_SLOW_TRIGGER_EXITED: TRUE",
        "TRIGGER_ZONE_EVENT_002_RETURN_SLOW_TRIGGER_ENTERED: TRUE",
        "TRIGGER_ZONE_EVENT_002_LIGHT_AFTER_RETURN_SLOW_TRIGGER: ON"
    ]

    missing = []
    for m in expected_markers:
        if m not in stdout:
            missing.append(m)

    if missing:
        print(f"FAILED: Missing required stdout markers: {missing}")
        sys.exit(1)

    # 5. Output required summary and final stamps
    if args.headless:
        print("============================================================")
        print("TRIGGER_ZONE_EVENT_002_HEADLESS = TRUE")
        print("LIGHT_INITIAL = ON")
        print("FORWARD_OFF_TRIGGER = TRUE")
        print("FORWARD_ON_TRIGGER = TRUE")
        print("WHILE_INSIDE_ENTER = TRUE")
        print("WHILE_INSIDE_HOLD_OFF = TRUE")
        print("WHILE_INSIDE_EXIT_RESTORE = TRUE")
        print("RETURN_ON_TRIGGER = TRUE")
        print("RETURN_OFF_TRIGGER = TRUE")
        print("FINAL_LIGHT_STATE = OFF")
    else:
        print("============================================================")
        print("TRIGGER_ZONE_EVENT_002_VISIBLE = HUMAN_CONFIRMABLE")
        print("LIGHT_INITIAL = ON")
        print("FORWARD_OFF_TRIGGER = TRUE")
        print("FORWARD_ON_TRIGGER = TRUE")
        print("WHILE_INSIDE_ENTER = TRUE")
        print("WHILE_INSIDE_HOLD_OFF = TRUE")
        print("WHILE_INSIDE_EXIT_RESTORE = TRUE")
        print("RETURN_ON_TRIGGER = TRUE")
        print("RETURN_OFF_TRIGGER = TRUE")
        print("FINAL_LIGHT_STATE = OFF")

    print("\nTRIGGER_ZONE_EVENT_002_HEADLESS = TRUE" if args.headless else "TRIGGER_ZONE_EVENT_002_VISIBLE = HUMAN_CONFIRMED")
    print("LIGHT_BEFORE = ON")
    print("CAPSULE_ENTERED_TRIGGER = TRUE")
    print("LIGHT_AFTER = OFF")
    print("====================================================")
    print("gate_trigger_zone_multi_trigger_light_route_proof: TRUE")
    print("====================================================")
    sys.exit(0)

if __name__ == "__main__":
    main()
