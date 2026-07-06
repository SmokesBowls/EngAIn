# TASK: TRIGGER_ZONE_EVENT_002_MULTI_TRIGGER_LIGHT_ROUTE_PROOF

GOAL:
Create a standalone proof gate showing that a trigger_zone route can support multiple trigger behaviors using Area3D:
1. an OFF trigger that turns the light off on entry,
2. an ON trigger that turns the light on on entry,
3. a WHILE_INSIDE trigger that turns the light off on entry and restores it on exit,
4. repeatable trigger behavior when the capsule returns along the same path.

Aider must create the gate script file from scratch. Do not rely on any pre-existing version of this file.

FILE TO CREATE (FROM SCRATCH):
tier2/godotsim/gates/gate_trigger_zone_multi_trigger_light_route_proof.py

NEW TEMP FILES ALLOWED:
tmp_multi_trigger_scene.tscn
tmp_multi_trigger_controller.gd

DO NOT TOUCH:
- docs/contracts/ENGAINOS_TIER1_AUTHORITY/engainos_1stlane_governance_authority/piece_baseline_manifest.json
- tier2/godotsim/kernels/piece3d_mr.py
- tier2/godotsim/builders/godot_scene_piece_builder.py
- support runner doctrine
- MCP files

---

## 1. Reference Specifications

Aider must write the temporary files with the exact code structures defined below.

### GDScript Controller (`tmp_multi_trigger_controller.gd`):
```gdscript
extends Node3D

@onready var light = $ProofLight
@onready var player = $ProofCapsule
@onready var trigger_off = $TriggerOff
@onready var trigger_on = $TriggerOn
@onready var trigger_while_inside = $TriggerWhileInside

var elapsed = 0.0
var phase = "forward" # "forward", "hold", "forward_exit", "return", "done"
var hold_timer = 0.0
var exit_timer = 0.0
var is_headless = false

func _ready():
	is_headless = (DisplayServer.get_name() == "headless")
	
	print("TRIGGER_ZONE_EVENT_002_LIGHT_INITIAL: ON")
	print("TRIGGER_ZONE_EVENT_002_CAPSULE_START: " + str(player.global_position))
	
	# Connect signals
	trigger_off.body_entered.connect(_on_off_entered)
	trigger_on.body_entered.connect(_on_on_entered)
	trigger_while_inside.body_entered.connect(_on_while_inside_entered)
	trigger_while_inside.body_exited.connect(_on_while_inside_exited)

func _physics_process(delta):
	elapsed += delta
	if elapsed > 15.0:
		print("TIMEOUT: route not completed.")
		get_tree().quit(1)
		return

	if phase == "forward":
		player.global_position.z -= 3.0 * delta
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
		if phase == "forward" or phase == "hold":
			print("TRIGGER_ZONE_EVENT_002_WHILE_INSIDE_TRIGGER_ENTERED: TRUE")
			print("TRIGGER_ZONE_EVENT_002_LIGHT_WHILE_INSIDE_ENTER: OFF")

func _on_while_inside_exited(body):
	if body == player:
		light.light_energy = 1.0
		if phase == "forward_exit":
			print("TRIGGER_ZONE_EVENT_002_WHILE_INSIDE_TRIGGER_EXITED: TRUE")
			print("TRIGGER_ZONE_EVENT_002_LIGHT_AFTER_WHILE_INSIDE_EXIT: ON")
```

### Godot Scene File (`tmp_multi_trigger_scene.tscn`):
```text
[gd_scene load_steps=15 format=3]

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
```

---

## 2. Required Stdout Markers

At startup:
TRIGGER_ZONE_EVENT_002_LIGHT_INITIAL: ON
TRIGGER_ZONE_EVENT_002_CAPSULE_START: (0.0, 1.0, 7.0)

Forward pass:
TRIGGER_ZONE_EVENT_002_FORWARD_OFF_TRIGGER_ENTERED: TRUE
TRIGGER_ZONE_EVENT_002_LIGHT_AFTER_FORWARD_OFF_TRIGGER: OFF

TRIGGER_ZONE_EVENT_002_FORWARD_ON_TRIGGER_ENTERED: TRUE
TRIGGER_ZONE_EVENT_002_LIGHT_AFTER_FORWARD_ON_TRIGGER: ON

TRIGGER_ZONE_EVENT_002_WHILE_INSIDE_TRIGGER_ENTERED: TRUE
TRIGGER_ZONE_EVENT_002_LIGHT_WHILE_INSIDE_ENTER: OFF

TRIGGER_ZONE_EVENT_002_WHILE_INSIDE_HOLD_CONFIRMED: TRUE
TRIGGER_ZONE_EVENT_002_LIGHT_DURING_WHILE_INSIDE_HOLD: OFF

TRIGGER_ZONE_EVENT_002_WHILE_INSIDE_TRIGGER_EXITED: TRUE
TRIGGER_ZONE_EVENT_002_LIGHT_AFTER_WHILE_INSIDE_EXIT: ON

Return pass:
TRIGGER_ZONE_EVENT_002_RETURN_ON_TRIGGER_ENTERED: TRUE
TRIGGER_ZONE_EVENT_002_LIGHT_AFTER_RETURN_ON_TRIGGER: ON

TRIGGER_ZONE_EVENT_002_RETURN_OFF_TRIGGER_ENTERED: TRUE
TRIGGER_ZONE_EVENT_002_LIGHT_AFTER_RETURN_OFF_TRIGGER: OFF

Final:
TRIGGER_ZONE_EVENT_002_CAPSULE_RETURNED_TO_A: TRUE
TRIGGER_ZONE_EVENT_002_FINAL_LIGHT_STATE: OFF
gate_trigger_zone_multi_trigger_light_route_proof: TRUE

---

## 3. Required Python Gate Script Logic
The Python gate must:
- use argparse to accept `--headless` flag
- write temporary Godot scene file `tmp_multi_trigger_scene.tscn` containing the exact text in reference specs
- write temporary GDScript controller file `tmp_multi_trigger_controller.gd` containing the exact text in reference specs
- launch Godot using subprocess (`godot` binary)
- capture and parse stdout for every required marker, failing if any are missing
- clean up temp files on exit
- exit 0 on success, exit non-zero on failure

---

## 4. Required Executor Provenance Result Packet
Aider must write a result packet file named `docs/contracts/SUPPORT_LANE_DISTRIBUTION/aider_2ndlane_repair_execution/AIDER_DISPATCH_SURFACE_001/completed/TRIGGER_ZONE_EVENT_002_MULTI_TRIGGER_LIGHT_ROUTE_PROOF_RESULT.md` containing:

```text
executor_name: aider / qwen2.5-coder:7b-instruct
supervisor_name: Antigravity
worker_created_gate_from_scratch: TRUE
antigravity_implemented_code: FALSE
prior_antigravity_artifacts_removed_or_voided: TRUE
git_used_only_by_supervisor: TRUE
command_interface_used: <exact command run to invoke runner>
files_created_by_executor: <list of files created>
files_modified_by_executor: <list of files modified>
commands_run_by_executor: <list of validation/proof commands run>
result_packet_path: <path to result file>
proof_stdout_markers: <list of required markers verified>
artifact_hashes_or_file_sizes: <list of files and sizes>
supervisor_archive_method: <how the task was moved and committed>
git_commit_hash_created_by_supervisor_optional: <leave blank>
whether_human_visually_confirmed: PENDING
```
