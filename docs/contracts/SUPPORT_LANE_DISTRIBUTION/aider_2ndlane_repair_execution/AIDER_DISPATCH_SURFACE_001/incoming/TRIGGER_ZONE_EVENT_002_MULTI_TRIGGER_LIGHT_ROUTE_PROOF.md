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

## 1. Gate Architecture Requirements

### Expected Visual Route:
The capsule starts at Position A.
The directional light starts ON.
The capsule walks forward.

Forward pass:
1. Capsule enters Trigger OFF zone.
   Expected: light turns OFF.
2. Capsule continues forward into Trigger ON zone.
   Expected: light turns ON.
3. Capsule continues forward into Trigger WHILE_INSIDE zone.
   Expected: light turns OFF.
4. Capsule pauses inside the WHILE_INSIDE zone.
   Expected: light stays OFF during hold.
5. Capsule exits the WHILE_INSIDE zone.
   Expected: light turns ON.

Return pass:
6. Capsule walks back toward Position A.
7. Capsule crosses the ON trigger again first.
   Expected: light remains ON because this trigger sets light ON and it is already ON.
8. Capsule crosses the OFF trigger again.
   Expected: light turns OFF.
9. Scene ends with light OFF.

### Required Godot Nodes in the Scene:
- Node3D root
- DirectionalLight3D named ProofLight
- Camera3D
- StaticBody3D or floor mesh
- CharacterBody3D or deterministic capsule body named ProofCapsule
- Area3D named TriggerOff
- Area3D named TriggerOn
- Area3D named TriggerWhileInside
- CollisionShape3D for each Area3D
- visible semi-transparent BoxMesh helper for each trigger zone

### Trigger Colors:
- OFF trigger: semi-transparent red (transparency = 1, Color(1, 0, 0, 0.3))
- ON trigger: semi-transparent green (transparency = 1, Color(0, 1, 0, 0.3))
- WHILE_INSIDE trigger: semi-transparent blue (transparency = 1, Color(0, 0, 1, 0.3))

### Movement Rule:
The capsule must be moved deterministically by script (do not require keyboard inputs).
The route must be reproducible in headless mode and visible mode.

### Layout Coordinates:
- Capsule start: Vector3(0, 1, 7)
- TriggerOff center: Vector3(0, 1, 4)
- TriggerOn center: Vector3(0, 1, 1)
- TriggerWhileInside center: Vector3(0, 1, -2)
- Forward endpoint beyond while-inside trigger: Vector3(0, 1, -4)
- Return endpoint / Position A: Vector3(0, 1, 7)

The capsule should move along the Z axis:
start at z = 7
walk forward toward z = -4
pause inside TriggerWhileInside
continue out of TriggerWhileInside
reverse direction
walk back toward z = 7
end after crossing TriggerOff on the return pass

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
- write temporary Godot scene file `tmp_multi_trigger_scene.tscn`
- write temporary GDScript controller file `tmp_multi_trigger_controller.gd`
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
