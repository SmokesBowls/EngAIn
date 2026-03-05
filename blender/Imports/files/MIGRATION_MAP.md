# EngAIn Component Migration Map

## UNCHANGED (zero modifications)

Python Core: sim_runtime.py, runtime_core.py, command_dispatcher.py, http_handlers.py, protocol_envelope.py, engain_hooks.py

MR Kernels: spatial3d_mr.py, perception_mr.py, behavior3d_mr.py, combat3d_mr.py

Adapters: spatial3d_adapter.py, perception_adapter.py, behavior_adapter.py, combat3d_adapter.py, inventory3d_integration.py, dialogue3d_integration.py

Data Pipeline: vault_linker.py, scene_extractor.py, slice_builders.py, all ZW/ZON4D/ZONB handlers

Supporting: vault_registry.json, all .zonj scene files

## NEW (UPBGE-specific, in this kit)

engain_controller.py -> replaces ZWRuntime.gd (Logic Brick entry point)
engain_bge_bridge.py -> replaces Godot HTTP polling (scene graph manager)

Two files. That is the entire UPBGE integration layer.

## NOT NEEDED IN UPBGE (Godot-only)

ZWRuntime.gd, AudioTimeline.gd, fix_3_protocol_envelope.gd, .tscn/.tres files, project.godot

## DUAL-CLIENT MODE (optional)

Run Godot AND UPBGE against same sim_runtime on :8080.
Godot = player view. UPBGE = creator view. Same world state.
sim_runtime is single source of truth. Both clients are consumers.
