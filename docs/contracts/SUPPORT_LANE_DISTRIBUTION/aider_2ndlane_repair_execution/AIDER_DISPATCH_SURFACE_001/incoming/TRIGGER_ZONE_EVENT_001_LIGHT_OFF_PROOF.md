# TASK: TRIGGER_ZONE_EVENT_001_LIGHT_OFF_PROOF

GOAL:
Create a standalone proof gate showing that a trigger_zone can cause an event:
capsule enters visible trigger bounds → light turns off.

FILE IN SCOPE:
tier2/godotsim/gates/gate_trigger_zone_light_off_proof.py

NEW TEMP FILES ALLOWED:
tmp_trigger_zone_light_off_scene.tscn
tmp_trigger_zone_light_off_controller.gd

DO NOT TOUCH:
- docs/contracts/ENGAINOS_TIER1_AUTHORITY/engainos_1stlane_governance_authority/piece_baseline_manifest.json
- tier2/godotsim/kernels/piece3d_mr.py
- tier2/godotsim/builders/godot_scene_piece_builder.py
- tier2/godotsim/gates/gate_piece_recipe_pack_001.py
- tier2/godotsim/gates/gate_piece_recipe_pack_002_door_proof.py
- support runner doctrine
- MCP files
