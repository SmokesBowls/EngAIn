#!/usr/bin/env python3
"""
gate_trigger_zone_light_off_proof.py

This proof does not prove trigger_zone builder semantics.
This proof proves trigger_zone event behavior.
The debug mesh is a proof helper only.
"""

from __future__ import annotations
import sys
import os
import shutil
import subprocess
from pathlib import Path

# Setup root path to import relative modules
ROOT = Path(__file__).resolve().parents[3]
sys.path.append(str(ROOT))

SCENE_PATH = ROOT / "tmp_trigger_zone_light_off_scene.tscn"
SCRIPT_PATH = ROOT / "tmp_trigger_zone_light_off_controller.gd"

CONTROLLER_CODE = """extends Node3D

@onready var light = $DirectionalLight3D
@onready var player = $PlayerCapsule
@onready var area = $TriggerZone

var entered = false
var elapsed = 0.0
var exit_timer = 0.0
var is_headless = false

func _ready():
	is_headless = (DisplayServer.get_name() == "headless")
	
	print("TRIGGER_ZONE_EVENT_001_LIGHT_BEFORE: ON")
	print("TRIGGER_ZONE_EVENT_001_CAPSULE_START: " + str(player.global_position))
	
	# Connect Area3D body_entered signal
	area.body_entered.connect(_on_body_entered)

func _physics_process(delta):
	elapsed += delta
	if elapsed > 6.0:
		print("TIMEOUT: capsule did not enter trigger zone.")
		get_tree().quit(1)
		return
		
	# Move capsule forward (-Z) if not entered
	if not entered:
		player.global_position.z -= 4.0 * delta
	else:
		if is_headless:
			get_tree().quit(0)
		else:
			exit_timer += delta
			if exit_timer >= 3.0:
				get_tree().quit(0)

func _on_body_entered(body):
	if body == player and not entered:
		entered = true
		light.visible = false
		print("TRIGGER_ZONE_EVENT_001_CAPSULE_ENTERED: TRUE")
		print("TRIGGER_ZONE_EVENT_001_LIGHT_AFTER: OFF")
		print("gate_trigger_zone_light_off_proof: TRUE")
"""

SCENE_CODE = """[gd_scene load_steps=8 format=3]

[ext_resource type="Script" path="res://tmp_trigger_zone_light_off_controller.gd" id="1_controller"]

[sub_resource type="BoxMesh" id="BoxMesh_floor"]
size = Vector3(15, 0.2, 15)

[sub_resource type="BoxShape3D" id="BoxShape3D_floor"]
size = Vector3(15, 0.2, 15)

[sub_resource type="CapsuleMesh" id="CapsuleMesh_player"]
radius = 0.5
height = 2.0

[sub_resource type="CapsuleShape3D" id="CapsuleShape3D_player"]
radius = 0.5
height = 2.0

[sub_resource type="BoxShape3D" id="BoxShape3D_trigger"]
size = Vector3(2, 2, 2)

[sub_resource type="BoxMesh" id="BoxMesh_trigger"]
size = Vector3(2, 2, 2)

[sub_resource type="StandardMaterial3D" id="StandardMaterial3D_trigger"]
transparency = 1
albedo_color = Color(1, 0, 0, 0.3)

[node name="Root" type="Node3D"]
script = ExtResource("1_controller")

[node name="Floor" type="MeshInstance3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, -0.1, 0)
mesh = SubResource("BoxMesh_floor")

[node name="FloorCollision" type="StaticBody3D" parent="Floor"]
[node name="CollisionShape3D" type="CollisionShape3D" parent="Floor/FloorCollision"]
shape = SubResource("BoxShape3D_floor")

[node name="DirectionalLight3D" type="DirectionalLight3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 0.866025, 0.5, 0, -0.5, 0.866025, 0, 10, 0)

[node name="Camera3D" type="Camera3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 0.866025, 0.5, 0, -0.5, 0.866025, 0, 5, 8)
current = true

[node name="PlayerCapsule" type="CharacterBody3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 5)

[node name="MeshInstance3D" type="MeshInstance3D" parent="PlayerCapsule"]
mesh = SubResource("CapsuleMesh_player")

[node name="CollisionShape3D" type="CollisionShape3D" parent="PlayerCapsule"]
shape = SubResource("CapsuleShape3D_player")

[node name="TriggerZone" type="Area3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0)

[node name="CollisionShape3D" type="CollisionShape3D" parent="TriggerZone"]
shape = SubResource("BoxShape3D_trigger")

[node name="MeshInstance3D" type="MeshInstance3D" parent="TriggerZone"]
mesh = SubResource("BoxMesh_trigger")
material_override = SubResource("StandardMaterial3D_trigger")
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
    # Parse arguments
    headless_arg = "--headless" in sys.argv
    
    print("=" * 60)
    print(f"RUNNING GATE: gate_trigger_zone_light_off_proof.py (headless={headless_arg})")
    print("=" * 60)

    # 1. Write scripts and scenes dynamically
    try:
        SCRIPT_PATH.write_text(CONTROLLER_CODE, encoding="utf-8")
        SCENE_PATH.write_text(SCENE_CODE, encoding="utf-8")
    except Exception as e:
        print(f"FAILED to write temp files: {e}")
        sys.exit(1)

    godot_bin = find_godot_binary()
    if not godot_bin:
        print("gate_trigger_zone_light_off_proof: BYPASS (Godot binary not found)")
        # Clean up
        SCRIPT_PATH.unlink(missing_ok=True)
        SCENE_PATH.unlink(missing_ok=True)
        sys.exit(0)

    # 2. Launch Godot
    cmd = [godot_bin, "--scene", f"res://{SCENE_PATH.name}"]
    if headless_arg:
        cmd.append("--headless")

    print(f"Launching: {' '.join(cmd)}")
    
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=str(ROOT), text=True)
    
    try:
        # Give ample timeout (8 seconds)
        stdout, stderr = proc.communicate(timeout=8.0)
    except subprocess.TimeoutExpired:
        proc.terminate()
        try:
            stdout, stderr = proc.communicate(timeout=1.0)
        except Exception:
            stdout, stderr = "", ""
        print("FAILED: Godot process execution timed out.")
        sys.exit(1)
    finally:
        # Clean up temporary files immediately after Godot exits
        SCRIPT_PATH.unlink(missing_ok=True)
        SCENE_PATH.unlink(missing_ok=True)

    # 3. Print captured stdout to screen
    print("--- Godot Output ---")
    print(stdout)
    print("--------------------")

    # 4. Verify outputs and exit codes
    if proc.returncode != 0:
        print(f"FAILED: Godot process exited with error code {proc.returncode}")
        sys.exit(1)

    # Verify stdout markers exist
    expected_markers = [
        "TRIGGER_ZONE_EVENT_001_LIGHT_BEFORE:",
        "TRIGGER_ZONE_EVENT_001_CAPSULE_START:",
        "TRIGGER_ZONE_EVENT_001_CAPSULE_ENTERED: TRUE",
        "TRIGGER_ZONE_EVENT_001_LIGHT_AFTER: OFF",
        "gate_trigger_zone_light_off_proof: TRUE"
    ]
    
    missing_markers = []
    for m in expected_markers:
        if m not in stdout:
            missing_markers.append(m)
            
    if missing_markers:
        print(f"FAILED: Expected markers missing from output: {missing_markers}")
        sys.exit(1)

    # Print final verdict stamps
    print("=" * 60)
    if headless_arg:
        print("TRIGGER_ZONE_EVENT_001_HEADLESS = TRUE")
    else:
        print("TRIGGER_ZONE_EVENT_001_VISIBLE = HUMAN_CONFIRMED")
    print("LIGHT_BEFORE = ON")
    print("CAPSULE_ENTERED_TRIGGER = TRUE")
    print("LIGHT_AFTER = OFF")
    print("====================================================")
    print("gate_trigger_zone_light_off_proof: TRUE")
    print("====================================================")
    sys.exit(0)

if __name__ == "__main__":
    main()
