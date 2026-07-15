# EngAInOS reorg review

## Modified tracked EngAInOS files
 M godotengain/engainos/core/agent_gateway.py
 M godotengain/engainos/core/ap_complex_rules.py
 M godotengain/engainos/core/ap_runtime.py
 M godotengain/engainos/core/authority_validator.py
 M godotengain/engainos/core/scene_loader.py
 M godotengain/engainos/core/scene_server.py
 M godotengain/engainos/launch_engine.py

## Deleted tracked EngAInOS files
 D godotengain/EngAInBridge.gd
 D godotengain/TestScene.tscn
 D godotengain/architectural_map_launch_engine.md
 D godotengain/engainos/APSimulationDebugger.gd
 D godotengain/engainos/APSimulationDebugger.gd.uid
 D godotengain/engainos/ClickablePlaceholder.gd
 D godotengain/engainos/ClickablePlaceholder.gd.uid
 D godotengain/engainos/autoload/ZWRuntime.gd
 D godotengain/engainos/autoload/ZWRuntime.gd.uid
 D godotengain/engainos/cleanup_engain_tree.sh
 D godotengain/engainos/core/agent_gateway.py.broken
 D godotengain/engainos/core/ap_complex_rules.py.old
 D godotengain/engainos/core/combat3d_mr.py.txt
 D godotengain/engainos/core/empire.py
 D godotengain/engainos/core/empire_agent_gateway.py
 D godotengain/engainos/core/empire_mr.py
 D godotengain/engainos/core/launch_bridge.py
 D godotengain/engainos/core/quest3d_integration
 D godotengain/engainos/core/quest3d_mr.v1
 D godotengain/engainos/core/run_all_quest_tests.sh
 D godotengain/engainos/core/scene_feature_registry.py
 D godotengain/engainos/core/scene_features_beach.py
 D godotengain/engainos/core/scene_loader.py.bak
 D godotengain/engainos/core/scene_shell_builder.py
 D godotengain/engainos/core/scene_shell_builder.py.bak
 D godotengain/engainos/core/scene_shell_builder.py.before_sync_fix
 D godotengain/engainos/core/scene_shell_builder.py.pre_construction_relative
 D godotengain/engainos/core/scene_shell_builder.py.pre_pier_relative
 D godotengain/engainos/core/scene_shell_builder.py.pre_relative_fix
 D godotengain/engainos/core/test_quest3d_comprehensive.py
 D godotengain/engainos/core/test_quest3d_correct.py
 D godotengain/engainos/core/test_quest3d_proper.py
 D godotengain/engainos/core/test_quest_http.py
 D godotengain/engainos/core/test_quest_lifecycle.py
 D godotengain/engainos/core/test_sample_quests.py
 D godotengain/engainos/core/test_scene_shell_builder.py
 D godotengain/engainos/core/test_trixel_world_stack.py
 D godotengain/engainos/core/test_trixel_world_stack.py.bak
 D godotengain/engainos/core/test_trixel_world_stack.py.orig
 D godotengain/engainos/core/test_trixel_world_stack.py.pre_construction_relative
 D godotengain/engainos/core/test_trixel_world_stack.py.pre_pier_relative
 D godotengain/engainos/core/test_trixel_world_stack.py.pre_relative_fix
 D godotengain/engainos/core/test_trixel_world_stack.py.rej
 D godotengain/engainos/core/test_with_game_data.py
 D godotengain/engainos/core/trixel_world_adapter.py
 D godotengain/engainos/core/trixel_world_mr.py
 D godotengain/engainos/core/trixel_world_zw.py
 D godotengain/engainos/core/world_builder.py
 D godotengain/engainos/fix_godot_dependencies.sh
 D godotengain/engainos/game_scenes/test_scene.json
 D godotengain/engainos/game_scenes/unknown_scene.json
 D godotengain/engainos/godot/CharacterWanderer.gd
 D godotengain/engainos/godot/CharacterWanderer.gd.uid
 D godotengain/engainos/godot/CourierScene.gd
 D godotengain/engainos/godot/CourierScene.gd.uid
 D godotengain/engainos/godot/DialogueBubble.gd
 D godotengain/engainos/godot/DialogueBubble.gd.uid
 D godotengain/engainos/godot/EngAInBridge.gd
 D godotengain/engainos/godot/EngAInBridge.gd.uid
 D godotengain/engainos/godot/EngAinBridge.gd
 D godotengain/engainos/godot/EngAinBridge.gd.uid
 D godotengain/engainos/godot/GovernedHUD.gd
 D godotengain/engainos/godot/GovernedHUD.gd.uid
 D godotengain/engainos/godot/IntentMarker.gd
 D godotengain/engainos/godot/IntentMarker.gd.uid
 D godotengain/engainos/godot/SceneSpawner.gd
 D godotengain/engainos/godot/SceneSpawner.gd.backup
 D godotengain/engainos/godot/SceneSpawner.gd.uid
 D godotengain/engainos/godot/Spatial3DAdapter.gd
 D godotengain/engainos/godot/Spatial3DAdapter.gd.uid
 D godotengain/engainos/godot/TestZWScene.tscn
 D godotengain/engainos/godot/scenes/ap_clickable_cube.gd
 D godotengain/engainos/godot/scenes/ap_clickable_cube.gd.uid
 D godotengain/engainos/godot/scenes/ap_test_direct.gd
 D godotengain/engainos/godot/scenes/ap_test_direct.gd.uid
 D godotengain/engainos/godot/scenes/ap_test_simple.gd
 D godotengain/engainos/godot/scenes/ap_test_simple.gd.uid
 D godotengain/engainos/godot/scenes/heartbeat.gd
 D godotengain/engainos/godot/scenes/heartbeat.gd.uid
 D godotengain/engainos/godot/scenes/mesh_instance_3d_2.tscn
 D godotengain/engainos/godot/scenes/node_3d.tscn
 D godotengain/engainos/godot/scripts/ClickablePlaceholder.gd
 D godotengain/engainos/godot/scripts/ClickablePlaceholder.gd.uid
 D godotengain/engainos/godot/scripts/test_bridge.gd
 D godotengain/engainos/godot/scripts/test_bridge.gd.uid
 D godotengain/engainos/godotsim.gd
 D godotengain/engainos/godotsim.gd.uid
 D godotengain/engainos/healthtest.tscn
 D godotengain/engainos/icon.svg
 D godotengain/engainos/icon.svg.import
 D godotengain/engainos/incoming_qued/AP_INTEGRATION_GUIDE.md
 D godotengain/engainos/incoming_qued/AP_INTEGRATION_SNIPPET.py
 D godotengain/engainos/incoming_qued/ENGINE_BOOTSTRAP.md
 D godotengain/engainos/incoming_qued/FIXING_ZERO_RULES.md
 D godotengain/engainos/incoming_qued/fix_scene_file.py
 D godotengain/engainos/incoming_qued/test_ap_connection.gd
 D godotengain/engainos/incoming_qued/test_ap_connection.gd.uid
 D godotengain/engainos/incoming_qued/test_scene_loading.py
 D godotengain/engainos/inspect_godot_adapter.py
 D godotengain/engainos/node_3d.tscn
 D godotengain/engainos/project.godot
 D godotengain/engainos/renders/tts/test_timeline.json
 D godotengain/engainos/runtime_api.py
 D godotengain/engainos/scripts/AudioTimeline.gd
 D godotengain/engainos/scripts/AudioTimeline.gd.uid
 D godotengain/engainos/scripts/CombatHealthBar.gd
 D godotengain/engainos/scripts/CombatHealthBar.gd.uid
 D godotengain/engainos/scripts/EngineSummaryHUD.gd
 D godotengain/engainos/scripts/EngineSummaryHUD.gd.uid
 D godotengain/engainos/scripts/EngineSummaryHUD.v1
 D godotengain/engainos/scripts/QuestTracker.gd
 D godotengain/engainos/scripts/QuestTracker.gd.uid
 D godotengain/engainos/scripts/QuestTracker.v1
 D godotengain/engainos/scripts/QuestTracker.v2
 D godotengain/engainos/scripts/fix_trixel_init.sh
 D godotengain/engainos/scripts/test_audio_timeline.gd
 D godotengain/engainos/scripts/test_audio_timeline.gd.uid
 D godotengain/engainos/scripts/test_combat_healthbar.gd.uid
 D godotengain/engainos/scripts/test_engine_summary.gd.uid
 D godotengain/engainos/scripts/test_quest_tracker.gd.uid
 D godotengain/engainos/scripts/verify_trixel_integration.sh
 D godotengain/engainos/sim_test.json
 D godotengain/engainos/start_stack.fish
 D godotengain/engainos/test_ap_debug.py
 D godotengain/engainos/test_bridge.gd
 D godotengain/engainos/test_bridge.gd.uid
 D godotengain/engainos/tests/test_empire_pure.py.bak
 D godotengain/engainos/zon/timeline.jsonl

## New untracked EngAInOS files

## Current EngAInOS tree, depth 3
godotengain/engainos/archive/agent_gateway.py.broken
godotengain/engainos/archive/ap_complex_rules.py.old
godotengain/engainos/archive/scene_loader.py.bak
godotengain/engainos/archive/scene_shell_builder.py.bak
godotengain/engainos/archive/scene_shell_builder.py.before_sync_fix
godotengain/engainos/archive/scene_shell_builder.py.pre_construction_relative
godotengain/engainos/archive/scene_shell_builder.py.pre_pier_relative
godotengain/engainos/archive/scene_shell_builder.py.pre_relative_fix
godotengain/engainos/archive/test_trixel_world_stack.py.bak
godotengain/engainos/archive/test_trixel_world_stack.py.orig
godotengain/engainos/archive/test_trixel_world_stack.py.pre_construction_relative
godotengain/engainos/archive/test_trixel_world_stack.py.pre_pier_relative
godotengain/engainos/archive/test_trixel_world_stack.py.pre_relative_fix
godotengain/engainos/archive/test_trixel_world_stack.py.rej
godotengain/engainos/check_boundaries_precise.py
godotengain/ENGAINOS_CLEANUP_STATUS.md
godotengain/engainos/configs/concepts.yaml
godotengain/engainos/core/agent_gateway.py
godotengain/engainos/core/ap_complex_rules.py
godotengain/engainos/core/ap_core.py
godotengain/engainos/core/ap_engine.py
godotengain/engainos/core/ap_quest_rules.py
godotengain/engainos/core/ap_runtime.py
godotengain/engainos/core/ap_world_rules.py
godotengain/engainos/core/authority_validator.py
godotengain/engainos/core/canon.py
godotengain/engainos/core/combat3d_mr.py
godotengain/engainos/core/contract_validator.py
godotengain/engainos/core/engine_summary.py
godotengain/engainos/core/godot_adapter.py
godotengain/engainos/core/history_xeon.py
godotengain/engainos/core/__init__.py
godotengain/engainos/core/intent_shadow.py
godotengain/engainos/core/mesh_intake.py
godotengain/engainos/core/mesh_manifest.py
godotengain/engainos/core/protocol_envelope.py
godotengain/engainos/core/quest3d_integration.py
godotengain/engainos/core/quest3d_mr.py
godotengain/engainos/core/reality_mode.py
godotengain/engainos/core/replay.py
godotengain/engainos/core/scene_loader.py
godotengain/engainos/core/scene_server.py
godotengain/engainos/core/semantic_bridge.py
godotengain/engainos/core/spatial_reasoner.py
godotengain/engainos/core/spatial_skin_system.py
godotengain/engainos/core/trae_observer.py
godotengain/engainos/core/zon_bridge.py
godotengain/engainos/core/zon_to_entities.py
godotengain/engainos/core/zon_to_game.py
godotengain/engainos/core/zw_core.py
godotengain/engainos/docs/AP_INTEGRATION_GUIDE.md
godotengain/engainos/docs/ENGINE_BOOTSTRAP.md
godotengain/engainos/docs/FIX3_INTEGRATION_GUIDE.md
godotengain/engainos/docs/FIXING_ZERO_RULES.md
godotengain/engainos/docs/hud_contract_spec.md
godotengain/engainos/docs/MVCAR_INTEGRATION_GUIDE.md
godotengain/engainos/docs/Walking.fbx
godotengain/engainos/.editorconfig
godotengain/engainos/engainos_server.py
godotengain/engainos/find_boundary_violations.sh
godotengain/engainos/.gitattributes
godotengain/engainos/.gitignore
godotengain/engainos/launch_engine.py
godotengain/engainos/__pycache__/engainos_server.cpython-314.pyc
godotengain/engainos/__pycache__/launch_engine.cpython-314.pyc
godotengain/engainos/__pycache__/runtime_client.cpython-314.pyc
godotengain/engainos/.pytest_cache/CACHEDIR.TAG
godotengain/engainos/.pytest_cache/.gitignore
godotengain/engainos/.pytest_cache/README.md
godotengain/engainos/runtime_client.py
godotengain/engainos/tests/ap_complex_rules.py
godotengain/engainos/tests/godot_bridge_test.py
godotengain/engainos/tests/run_all_quest_tests.sh
godotengain/engainos/tests/test_agent_gateway.py
godotengain/engainos/tests/test_ap_complex_rules.py
godotengain/engainos/tests/test_ap_core.py
godotengain/engainos/tests/test_authority_spec_v1.py
godotengain/engainos/tests/test_canon.py
godotengain/engainos/tests/test_full_pipeline_integration.py
godotengain/engainos/tests/test_full_stack.py
godotengain/engainos/tests/test_history_xeon.py
godotengain/engainos/tests/test_intent_shadow.py
godotengain/engainos/tests/test_memory_integration.py
godotengain/engainos/tests/test_mesh_intake.py
godotengain/engainos/tests/test_mesh_manifest.py
godotengain/engainos/tests/test_quest3d_comprehensive.py
godotengain/engainos/tests/test_quest3d_correct.py
godotengain/engainos/tests/test_quest3d_proper.py
godotengain/engainos/tests/test_quest_http.py
godotengain/engainos/tests/test_quest_lifecycle.py
godotengain/engainos/tests/test_reality_mode.py
godotengain/engainos/tests/test_sample_quests.py
godotengain/engainos/tests/test_scene_shell_builder.py
godotengain/engainos/tests/test_semantic_bridge.py
godotengain/engainos/tests/test_spatial_skin_system.py
godotengain/engainos/tests/test_trae_observer.py
godotengain/engainos/tests/test_trixel_world_stack.py
godotengain/engainos/tests/test_with_game_data.py
godotengain/engainos/tests/test_zon_bridge.py
godotengain/engainos/tests/test_zon_to_entities.py
godotengain/engainos/tests/test_zon_to_game.py
godotengain/engainos/tests/test_zw_core.py
godotengain/engainos/tools/ap_timeline_viewer.py
godotengain/engainos/tools/fetch_scene_once.py
godotengain/syscheck/reports/cleanup_diffstat_after_intentional_delete.txt
godotengain/syscheck/reports/cleanup_status_after_intentional_delete.txt
