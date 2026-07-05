# TRAE TASK PACKET

TASK_PACKET_VERSION: 1
SURFACE_ID: TRAE_DISPATCH_SURFACE_001
INTERACTION_MODEL: manual_only

## 1. Task Identity

TASK_ID: MILESTONE_006_TRAE_TASK_001
TASK_TITLE: MILESTONE_006_PLAYER_MOVEMENT_PROOF
TASK_STATUS: READY_FOR_AGENT_RUN_AFTER_SCOPE_CONFIRMATION
CREATED_BY: human
HUMAN_OWNER: mytruelove

## 2. Authority And Lane Boundary

TIER_AUTHORITY: ENGAINOS_TIER1
STACK: EngAIn / GodotSim / Godot / GDScript
EXECUTION_LANE: trae_2ndlane_repair_execution
TARGET_LANE: tier2/godotsim
RUN_MODE: FULL_PIPELINE_FIRST_LOAD

REPO_PATH: /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn

This packet supersedes any stale Retrographer, Trixel, Conductor, or art-lane draft for MILESTONE_006.

This is not Retrographer.
This is not Trixel.
This is not Conductor.
This is not an art rendering lane.
This is a GodotSim player movement proof inside EngAIn.

## 3. Agent Boundary Rules

1. The first meaningful file read must be this packet.
2. Before editing, Trae must echo:
   - TIER_AUTHORITY
   - STACK
   - EXECUTION_LANE
   - TARGET_LANE
   - REPO_PATH
   - FILES_IN_SCOPE
   - DONE_MEANS
3. Trae must not search for a different project root.
4. Trae must not enter /mnt/data-drive/retrographer.
5. Trae must not edit retrographer, trixel, conductor, art-lane, canon, AP, or EngAInOS authority files.
6. Trae may only edit files explicitly listed in FILES_IN_SCOPE.
7. If a listed file does not exist and is not listed under NEW_FILES_ALLOWED, Trae must stop and report:
   MISSING_SCOPE_FILE
8. If the gate cannot be reproduced before editing, Trae must stop and report:
   REPRO_FAILED_BEFORE_EDIT
9. If Trae needs another file, Trae must stop and report:
   BLOCKED_SCOPE_EXPANSION_REQUIRED

## 4. Files In Scope

FILES_IN_SCOPE:
- tier2/godotsim/gates/gate_player_movement_proof.py
- tier2/godotsim/scripts/player_movement.gd
- tier2/godotsim/builders/godot_scene_piece_builder.py

NEW_FILES_ALLOWED:
- tier2/godotsim/gates/gate_player_movement_proof.py
- tier2/godotsim/scripts/player_movement.gd

DIRECTORIES_IN_SCOPE:
- tier2/godotsim/gates/
- tier2/godotsim/scripts/
- tier2/godotsim/builders/

FILES_OUT_OF_SCOPE:
- /mnt/data-drive/retrographer
- retrographer/**
- trixel/**
- conductor/**
- docs/canon/**
- docs/contracts/ENGAINOS_TIER1_AUTHORITY/**
- docs/contracts/engainos_1stlane_governance_authority/**
- tier2/trae-agent-main/tasks/mrlore_test_task.txt
- any MrLore canon file
- any AP authority file
- any file outside REPO_PATH

## 5. Prior Proof Dependency

MILESTONE_005_PLAYER_BODY_VISIBLE_PROOF: TRUE

Committed prior proof:

- player capsule renders visibly
- floor renders visibly
- wall renders visibly
- camera sees scene
- Godot window opens and stays open
- gate_player_body_visible_proof.py returns TRUE
- gate_static_room_visible_proof.py returns TRUE

MILESTONE_006 must preserve MILESTONE_005.

## 6. Problem Statement

MILESTONE_006 must prove minimum player movement.

EXPECTED_BEHAVIOR:

- W moves player forward.
- A moves player left.
- S moves player backward.
- D moves player right.
- Space jumps.
- Input map actions match the movement script.
- The movement proof runs through a Godot first-load scene.
- The movement proof is not just a parser check.

## 7. Required Godot Movement Proof Law

This proof must run inside an active, ticking Godot scene tree.

Do not implement MILESTONE_006 as a bare one-shot parse script.

Required movement proof pattern:

1. Build or load the test scene.
2. Attach a test runner script to a live node in the scene.
3. In the active scene tree, capture the player's initial position.
4. Use Input.action_press("move_forward").
5. Await multiple physics frames:
   await get_tree().physics_frame
6. Release input with:
   Input.action_release("move_forward")
7. Capture final position.
8. Compare initial and final position with epsilon.
9. Repeat enough checks to prove move_back, move_left, move_right, and jump bindings.
10. Print stdout proof lines.
11. Quit cleanly with success or failure code.

Required GDScript primitives:

- Input.action_press()
- Input.action_release()
- await get_tree().physics_frame
- get_tree().quit()

Movement script requirement:

- Use Input.get_vector("move_left", "move_right", "move_forward", "move_back")
- Held movement must be based on pressed input state, not only one-frame is_action_just_pressed.
- Jump may use Input.is_action_just_pressed("jump")
- Jump must only apply when grounded.

## 8. Required Stdout Return Path

The Python gate must launch Godot as a subprocess and capture stdout/stderr.

The GDScript runner must print machine-readable proof lines.

Required stdout lines:

MILESTONE_006_GODOT_RUNNER_STARTED
MILESTONE_006_INITIAL_POSITION:
MILESTONE_006_FINAL_POSITION:
MILESTONE_006_DELTA:
MILESTONE_006_FORWARD_MOVED: TRUE
MILESTONE_006_BACK_MOVED: TRUE
MILESTONE_006_LEFT_MOVED: TRUE
MILESTONE_006_RIGHT_MOVED: TRUE
MILESTONE_006_JUMP_APPLIED: TRUE
MILESTONE_006_GODOT_RUNNER_DONE: TRUE

The Python gate may only print:

gate_player_movement_proof: TRUE

if:

- Godot exits with code 0
- stdout contains required proof lines
- movement delta is proven
- no timeout occurs

On failure, Python must print a specific FALSE reason and exit nonzero.

## 9. Required Godot Exit Rule

Unlike visible render gates, this deterministic movement proof must exit cleanly.

The GDScript runner must call:

get_tree().quit(0)

after successful proof.

On failure, it must call:

get_tree().quit(1)

The Python gate must enforce a timeout.

## 10. Reproduction Command

REPRODUCTION_COMMAND:

cd /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn
PYTHONPATH=. python3 tier2/godotsim/gates/gate_player_movement_proof.py

EXPECTED_PRE_EDIT_RESULT:

FALSE

Trae must run this before edits.

If the file does not exist yet, record:

gate_player_movement_proof: FALSE

That is acceptable as reproduction for a missing milestone gate.

## 11. Post Edit Gates

POST_EDIT_GATE:

cd /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn
PYTHONPATH=. python3 tier2/godotsim/gates/gate_player_movement_proof.py

REGRESSION_GATE_PLAYER_BODY:

cd /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn
PYTHONPATH=. python3 tier2/godotsim/gates/gate_player_body_visible_proof.py

REGRESSION_GATE_STATIC_ROOM:

cd /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn
PYTHONPATH=. python3 tier2/godotsim/gates/gate_static_room_visible_proof.py

## 12. Dispatch Mailbox Lifecycle

DISPATCH_ROOT:

docs/contracts/SUPPORT_LANE_DISTRIBUTION/trae_2ndlane_repair_execution/TRAE_DISPATCH_SURFACE_001

Before patching, copy this packet into:

docs/contracts/SUPPORT_LANE_DISTRIBUTION/trae_2ndlane_repair_execution/TRAE_DISPATCH_SURFACE_001/working/MILESTONE_006_TRAE_TASK_001.md

Do not delete the incoming packet.

On success, write:

docs/contracts/SUPPORT_LANE_DISTRIBUTION/trae_2ndlane_repair_execution/TRAE_DISPATCH_SURFACE_001/completed/MILESTONE_006_PLAYER_MOVEMENT_PROOF_RESULT.md

On failure or block, write:

docs/contracts/SUPPORT_LANE_DISTRIBUTION/trae_2ndlane_repair_execution/TRAE_DISPATCH_SURFACE_001/failed/MILESTONE_006_PLAYER_MOVEMENT_PROOF_RESULT.md

Result packet must include:

- TASK_ID
- RUN_MODE
- RESULT_STATUS
- files changed
- reproduction output
- post-edit movement gate output
- player-body regression output
- static-room regression output
- stdout evidence from Godot runner
- final stamp

## 13. Done Means

DONE_MEANS:

- The player movement proof gate passes.
- The fix remains inside tier2/godotsim.
- MILESTONE_005 player body proof still passes.
- Static room proof still passes.
- No retrographer, trixel, conductor, art-lane, canon, AP, or unrelated files are changed.
- Final response includes:
  - files changed
  - commands run
  - gate result
  - rollback command

DONE_DOES_NOT_MEAN:

- production runtime complete
- camera follow complete
- animation complete
- combat complete
- network bridge complete
- canon/AP changed

## 14. Required Gate Table

Every listed gate must be reported as TRUE, FALSE, or BYPASS.

GATES_REQUIRED:
- GATE_PACKET_READ
- GATE_BOUNDARY_ECHOED
- GATE_REPO_PATH_CONFIRMED
- GATE_RETROGRAPHER_NOT_ENTERED
- GATE_SCOPE_CONFIRMED
- GATE_REPRODUCTION_RAN
- GATE_PRE_EDIT_RESULT_RECORDED
- GATE_PLAYER_MOVEMENT_SCRIPT_EXISTS
- GATE_INPUT_ACTION_NAMES_MATCH_SCRIPT
- GATE_WASD_SPACE_BINDINGS_EXIST
- GATE_ACTIVE_SCENE_TREE_USED
- GATE_PHYSICS_FRAMES_ADVANCED
- GATE_INPUT_ACTION_PRESS_RELEASE_USED
- GATE_GODOT_STDOUT_CAPTURED
- GATE_GODOT_QUIT_CODE_ENFORCED
- GATE_PLAYER_POSITION_CHANGED
- GATE_MOVEMENT_GATE_TRUE
- GATE_PLAYER_BODY_STILL_TRUE
- GATE_STATIC_ROOM_STILL_TRUE
- GATE_PATCH_WITHIN_SCOPE
- GATE_RESULT_PACKET_WRITTEN

FALSE blocks acceptance.

## 15. Rollback Command

ROLLBACK_COMMAND:

cd /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn
git restore tier2/godotsim/builders/godot_scene_piece_builder.py
rm -f tier2/godotsim/gates/gate_player_movement_proof.py
rm -f tier2/godotsim/scripts/player_movement.gd

## 16. Final Packet Verdict

TRAE_ALLOWED_TO_BEGIN: TRUE
FINAL_STAMP: MILESTONE_006_GODOTSIM_BOUNDARY_CORRECTED
