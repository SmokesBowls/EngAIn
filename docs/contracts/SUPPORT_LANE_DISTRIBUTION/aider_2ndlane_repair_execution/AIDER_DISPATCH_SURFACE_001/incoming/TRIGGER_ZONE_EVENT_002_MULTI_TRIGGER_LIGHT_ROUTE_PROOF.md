# TASK: TRIGGER_ZONE_EVENT_002_MULTI_TRIGGER_LIGHT_ROUTE_PROOF

GOAL:
Create a standalone proof gate showing that a trigger_zone route can support multiple trigger behaviors using Area3D:
1. an OFF trigger that turns the light off on entry,
2. an ON trigger that turns the light on on entry,
3. a WHILE_INSIDE trigger that turns the light off on entry and restores it on exit,
4. repeatable trigger behavior when the capsule returns along the same path.

FILE IN SCOPE:
tier2/godotsim/gates/gate_trigger_zone_multi_trigger_light_route_proof.py

NEW TEMP FILES ALLOWED:
tmp_multi_trigger_scene.tscn
tmp_multi_trigger_controller.gd

DO NOT TOUCH:
- docs/contracts/ENGAINOS_TIER1_AUTHORITY/engainos_1stlane_governance_authority/piece_baseline_manifest.json
- tier2/godotsim/kernels/piece3d_mr.py
- tier2/godotsim/builders/godot_scene_piece_builder.py
- tier2/godotsim/gates/gate_piece_recipe_pack_001.py
- tier2/godotsim/gates/gate_piece_recipe_pack_002_door_proof.py
- support runner doctrine
- MCP files
