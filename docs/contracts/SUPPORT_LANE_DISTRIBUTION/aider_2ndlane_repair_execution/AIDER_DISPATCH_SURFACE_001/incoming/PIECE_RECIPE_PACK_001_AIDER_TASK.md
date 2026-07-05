# AIDER TASK PACKET

SURFACE_ID: AIDER_DISPATCH_SURFACE_001
INTERACTION_MODEL: manual_only

## 1. Task Identity

TASK_ID: PIECE_RECIPE_PACK_001_AIDER_TASK
TASK_TITLE: Add GodotSim Piece Recipe Pack 001
TASK_STATUS: READY_FOR_AIDER
CREATED_BY: human
HUMAN_OWNER: mytruelove

## 2. Authority And Lane Boundary

TIER_AUTHORITY: ENGAINOS_TIER1
STACK: EngAIn / GodotSim / Godot / GDScript / Python
EXECUTION_LANE: aider_2ndlane_repair_execution
TARGET_LANE: tier2/godotsim
REPO_PATH: /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn

## 3. Aider Boundary Rules

1. The first meaningful file read must be this packet.
2. Before editing, Aider must echo:
   - TIER_AUTHORITY
   - STACK
   - EXECUTION_LANE
   - TARGET_LANE
   - REPO_PATH
   - FILES_IN_SCOPE
   - DONE_MEANS
3. Aider must not search for a different project root.
4. Aider may only edit files explicitly listed in FILES_IN_SCOPE.
5. If Aider needs another file, Aider must stop and report:
   BLOCKED_SCOPE_EXPANSION_REQUIRED
6. Aider must not modify canon, AP, Trixel, Retrographer, retired Trae, or EngAInOS authority maps.
7. Aider must not replace existing MILESTONE_004, MILESTONE_005, or MILESTONE_006 gates.

## 4. Files In Scope

FILES_IN_SCOPE:
- docs/contracts/ENGAINOS_TIER1_AUTHORITY/engainos_1stlane_governance_authority/piece_baseline_manifest.json
- tier2/godotsim/kernels/piece3d_mr.py
- tier2/godotsim/builders/godot_scene_piece_builder.py
- tier2/godotsim/gates/gate_piece3d_baseline.py

NEW_FILES_ALLOWED:
- tier2/godotsim/gates/gate_piece_recipe_pack_001.py
- tier2/godotsim/gates/gate_piece_recipe_pack_001_visible_proof.py
- docs/contracts/SUPPORT_LANE_DISTRIBUTION/aider_2ndlane_repair_execution/AIDER_DISPATCH_SURFACE_001/working/PIECE_RECIPE_PACK_001_AIDER_TASK.md
- docs/contracts/SUPPORT_LANE_DISTRIBUTION/aider_2ndlane_repair_execution/AIDER_DISPATCH_SURFACE_001/completed/PIECE_RECIPE_PACK_001_RESULT.md
- docs/contracts/SUPPORT_LANE_DISTRIBUTION/aider_2ndlane_repair_execution/AIDER_DISPATCH_SURFACE_001/failed/PIECE_RECIPE_PACK_001_RESULT.md

DIRECTORIES_IN_SCOPE:
- tier2/godotsim/
- docs/contracts/ENGAINOS_TIER1_AUTHORITY/engainos_1stlane_governance_authority/
- docs/contracts/SUPPORT_LANE_DISTRIBUTION/aider_2ndlane_repair_execution/AIDER_DISPATCH_SURFACE_001/

FILES_OUT_OF_SCOPE:
- docs/canon/**
- tier1/engainos/aproom/**
- docs/contracts/TRIXEL_TIER1_AUTHORITY/**
- docs/contracts/MRLORE_TIER1_AUTHORITY/**
- docs/contracts/SUPPORT_LANE_DISTRIBUTION/retired_agents/**
- /mnt/data-drive/retrographer/**
- conductor/**
- trixel/**
- retrographer/**

## 5. Problem Statement

GodotSim currently supports only a small piece vocabulary: floor, wall, camera, light, and player.

Add Piece Recipe Pack 001:

- marker
- box
- ramp
- platform
- trigger_zone

EXPECTED_BEHAVIOR:

Each new piece type must:
- validate through piece3d_mr.py
- reject missing required fields
- reject invalid discriminator mismatch
- build into a Godot .tscn scene when valid
- produce no partial scene on rejection
- preserve existing floor/wall/camera/light/player behavior

## 6. Required Reproduction

REPRODUCTION_COMMAND:

cd /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn
PYTHONPATH=. python3 tier2/godotsim/gates/gate_piece3d_baseline.py
PYTHONPATH=. python3 tier2/godotsim/gates/gate_player_movement_proof.py
PYTHONPATH=. python3 tier2/godotsim/gates/gate_player_body_visible_proof.py
PYTHONPATH=. python3 tier2/godotsim/gates/gate_static_room_visible_proof.py

EXPECTED_PRE_EDIT_RESULT:

Existing gates TRUE.

## 7. Required Recipe Definitions

Add these piece types to the manifest:

marker:
- required_fields: mesh, position, scale, color, collision
- mesh allowed: cube, cylinder, sphere
- collision allowed: true, false

box:
- required_fields: mesh, position, scale, collision
- mesh allowed: cube
- collision allowed: true, false

ramp:
- required_fields: mesh, position, rotation, scale, collision
- mesh allowed: wedge
- collision allowed: true

platform:
- required_fields: mesh, position, scale, collision
- mesh allowed: cube
- collision allowed: true

trigger_zone:
- required_fields: shape, position, scale, monitoring
- shape allowed: box
- monitoring allowed: true, false

## 8. Builder Requirements

The builder must convert:

marker:
- cube -> BoxMesh
- cylinder -> CylinderMesh
- sphere -> SphereMesh
- color should produce a visible material if builder supports material resources
- collision true should add a matching StaticBody3D / CollisionShape3D or equivalent
- collision false should be visual only

box:
- BoxMesh visual
- optional collision

platform:
- BoxMesh visual
- collision required

ramp:
- simplest acceptable implementation:
  - build as a rotated/scaled box if wedge mesh is not yet available
  - must still be visibly sloped
  - must include collision
  - if true wedge mesh is too large for this task, report RAMP_WEDGE_APPROXIMATION_USED

trigger_zone:
- Area3D
- CollisionShape3D using BoxShape3D
- visible debug mesh is allowed but not required
- no gameplay behavior required yet

## 9. Post Edit Gates

POST_EDIT_GATE:

cd /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn
PYTHONPATH=. python3 tier2/godotsim/gates/gate_piece_recipe_pack_001.py

REGRESSION_GATES:
- PYTHONPATH=. python3 tier2/godotsim/gates/gate_piece3d_baseline.py
- PYTHONPATH=. python3 tier2/godotsim/gates/gate_player_movement_proof.py
- PYTHONPATH=. python3 tier2/godotsim/gates/gate_player_body_visible_proof.py
- PYTHONPATH=. python3 tier2/godotsim/gates/gate_static_room_visible_proof.py

VISIBLE_OBSERVER_GATE:
- PYTHONPATH=. python3 tier2/godotsim/gates/gate_piece_recipe_pack_001_visible_proof.py

## 10. Done Means

DONE_MEANS:
- New piece recipes exist in manifest.
- New piece recipes validate.
- Missing-field tests reject invalid pieces.
- Discriminator mismatch still rejects invalid pieces.
- Builder can build a scene containing marker, box, ramp, platform, and trigger_zone.
- gate_piece_recipe_pack_001.py prints TRUE.
- Existing MILESTONE_004, MILESTONE_005, and MILESTONE_006 gates still pass.
- Visible observer gate opens a room showing the new pieces.
- Result packet is written.

DONE_DOES_NOT_MEAN:
- combat
- doors
- NPCs
- inventory
- terrain
- shader system
- procedural world generation
- replacing GodotSim builder
- replacing gates with MCP

## 11. Required Gate Table

GATES_REQUIRED:
- GATE_PACKET_READ
- GATE_BOUNDARY_ECHOED
- GATE_REPRODUCTION_RAN
- GATE_MANIFEST_UPDATED
- GATE_MARKER_VALIDATES
- GATE_BOX_VALIDATES
- GATE_RAMP_VALIDATES
- GATE_PLATFORM_VALIDATES
- GATE_TRIGGER_ZONE_VALIDATES
- GATE_MISSING_FIELDS_REJECTED
- GATE_DISCRIMINATOR_MISMATCH_REJECTED
- GATE_SCENE_BUILDS
- GATE_VISIBLE_OBSERVER_RAN
- GATE_MILESTONE_004_STILL_TRUE
- GATE_MILESTONE_005_STILL_TRUE
- GATE_MILESTONE_006_STILL_TRUE
- GATE_RESULT_PACKET_WRITTEN

FALSE blocks acceptance.

## 12. Rollback Command

ROLLBACK_COMMAND:

cd /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn
git restore docs/contracts/ENGAINOS_TIER1_AUTHORITY/engainos_1stlane_governance_authority/piece_baseline_manifest.json
git restore tier2/godotsim/kernels/piece3d_mr.py
git restore tier2/godotsim/builders/godot_scene_piece_builder.py
git restore tier2/godotsim/gates/gate_piece3d_baseline.py
rm -f tier2/godotsim/gates/gate_piece_recipe_pack_001.py
rm -f tier2/godotsim/gates/gate_piece_recipe_pack_001_visible_proof.py

## 13. Final Packet Verdict

AIDER_ALLOWED_TO_BEGIN: TRUE
FINAL_STAMP: PIECE_RECIPE_PACK_001_READY_FOR_AIDER
