# TASK: AIDER_INDEPENDENCE_PROOF_001_TRIGGER_ROUTE_EXTENSION

GOAL:
Extend the multi-trigger route proof to include a fourth trigger, proving Aider's ability to receive a dispatch task packet and perform the code updates independently.

FILE IN SCOPE:
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

## 1. Extension Requirements
Aider must edit `gate_trigger_zone_multi_trigger_light_route_proof.py` to:
1. Add a fourth trigger zone Area3D named `TriggerSlow` with a yellow semi-transparent helper BoxMesh at `Vector3(0, 1, -0.5)` with size `Vector3(2, 2, 1)`.
2. Connect `body_entered` and `body_exited` signals for `TriggerSlow`.
3. When the capsule enters `TriggerSlow`, its Z-axis movement speed must be reduced to half (from `3.0` to `1.5`). When it exits `TriggerSlow`, its Z-axis speed must be restored back to `3.0`.
4. Emit these stdout markers during the runs:
   - On forward pass enter: `TRIGGER_ZONE_EVENT_002_FORWARD_SLOW_TRIGGER_ENTERED: TRUE`
   - On forward pass enter: `TRIGGER_ZONE_EVENT_002_LIGHT_AFTER_FORWARD_SLOW_TRIGGER: ON`
   - On forward pass exit: `TRIGGER_ZONE_EVENT_002_FORWARD_SLOW_TRIGGER_EXITED: TRUE`
   - On return pass enter: `TRIGGER_ZONE_EVENT_002_RETURN_SLOW_TRIGGER_ENTERED: TRUE`
   - On return pass exit: `TRIGGER_ZONE_EVENT_002_RETURN_SLOW_TRIGGER_EXITED: TRUE`
5. Verify both headless and visible runs complete successfully and all markers (including the new ones) are present.

## 2. Patcher Acceptance Rule
The patcher runs under mandatory acceptance rules. Aider must not bypass human Acceptance.

## 3. Required Executor Provenance
Aider must write a result packet file named `docs/contracts/SUPPORT_LANE_DISTRIBUTION/aider_2ndlane_repair_execution/AIDER_DISPATCH_SURFACE_001/completed/AIDER_INDEPENDENCE_PROOF_001_TRIGGER_ROUTE_EXTENSION_RESULT.md` containing:
- `executor_name`: (e.g. aider / qwen2.5-coder:7b-instruct)
- `command_interface_used`: (the exact command line run to invoke Aider)
- `files_created_by_executor`: (list of new files created)
- `files_modified_by_executor`: (list of files modified)
- `commands_run_by_executor`: (list of validation commands run)
- `commit_hash_created_by_executor`: (leave blank or fill with latest git commit hash)
- `whether_human_visually_confirmed`: (set to PENDING)

## 4. Antigravity Boundary Rule
Antigravity must not implement the gate changes, edit the files, run Aider's commands, or write the result packet itself. Antigravity's role is to invoke Aider, monitor the output, check the result, and report back.
