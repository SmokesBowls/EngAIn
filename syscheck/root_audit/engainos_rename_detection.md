# EngAInOS rename detection

## Summary
 delete mode 100644 godotengain/EngAInBridge.gd
 delete mode 100644 godotengain/TestScene.tscn
 delete mode 100644 godotengain/architectural_map_launch_engine (copy).md
 delete mode 100644 godotengain/architectural_map_launch_engine.md
 delete mode 100644 godotengain/engainos 1-18-26.tar.gz
 delete mode 100644 godotengain/engainos/APSimulationDebugger.gd
 delete mode 100644 godotengain/engainos/APSimulationDebugger.gd.uid
 delete mode 100644 godotengain/engainos/ClickablePlaceholder.gd
 delete mode 100644 godotengain/engainos/ClickablePlaceholder.gd.uid
 delete mode 100644 godotengain/engainos/autoload/ZWRuntime.gd
 delete mode 100644 godotengain/engainos/autoload/ZWRuntime.gd.uid
 delete mode 100644 godotengain/engainos/cleanup_engain_tree.sh
 delete mode 100644 godotengain/engainos/core/agent_gateway.py.broken
 delete mode 100644 godotengain/engainos/core/ap_complex_rules.py.old
 delete mode 100644 godotengain/engainos/core/combat3d_mr.py.txt
 delete mode 100644 godotengain/engainos/core/empire.py
 delete mode 100644 godotengain/engainos/core/empire_agent_gateway.py
 delete mode 100644 godotengain/engainos/core/empire_mr.py
 delete mode 100755 godotengain/engainos/core/launch_bridge.py
 delete mode 100644 godotengain/engainos/core/quest3d_integration
 delete mode 100644 godotengain/engainos/core/quest3d_mr.v1
 delete mode 100755 godotengain/engainos/core/run_all_quest_tests.sh
 delete mode 100644 godotengain/engainos/core/scene_feature_registry.py
 delete mode 100644 godotengain/engainos/core/scene_features_beach.py
 delete mode 100755 godotengain/engainos/core/scene_loader.py.bak
 delete mode 100644 godotengain/engainos/core/scene_shell_builder.py
 delete mode 100644 godotengain/engainos/core/scene_shell_builder.py.bak
 delete mode 100644 godotengain/engainos/core/scene_shell_builder.py.before_sync_fix
 delete mode 100644 godotengain/engainos/core/scene_shell_builder.py.pre_construction_relative
 delete mode 100644 godotengain/engainos/core/scene_shell_builder.py.pre_pier_relative
 delete mode 100644 godotengain/engainos/core/scene_shell_builder.py.pre_relative_fix
 delete mode 100644 godotengain/engainos/core/test_quest3d_comprehensive.py
 delete mode 100644 godotengain/engainos/core/test_quest3d_correct.py
 delete mode 100644 godotengain/engainos/core/test_quest3d_proper.py
 delete mode 100644 godotengain/engainos/core/test_quest_http.py
 delete mode 100644 godotengain/engainos/core/test_quest_lifecycle.py
 delete mode 100644 godotengain/engainos/core/test_sample_quests.py
 delete mode 100644 godotengain/engainos/core/test_scene_shell_builder.py
 delete mode 100644 godotengain/engainos/core/test_trixel_world_stack.py
 delete mode 100644 godotengain/engainos/core/test_trixel_world_stack.py.bak
 delete mode 100644 godotengain/engainos/core/test_trixel_world_stack.py.orig
 delete mode 100644 godotengain/engainos/core/test_trixel_world_stack.py.pre_construction_relative
 delete mode 100644 godotengain/engainos/core/test_trixel_world_stack.py.pre_pier_relative
 delete mode 100644 godotengain/engainos/core/test_trixel_world_stack.py.pre_relative_fix
 delete mode 100644 godotengain/engainos/core/test_trixel_world_stack.py.rej
 delete mode 100644 godotengain/engainos/core/test_with_game_data.py
 delete mode 100644 godotengain/engainos/core/trixel_world_adapter.py
 delete mode 100644 godotengain/engainos/core/trixel_world_mr.py
 delete mode 100644 godotengain/engainos/core/trixel_world_zw.py
 delete mode 100644 godotengain/engainos/core/world_builder.py
 delete mode 100644 godotengain/engainos/fix_godot_dependencies.sh
 delete mode 100644 godotengain/engainos/game_scenes/test_scene.json
 delete mode 100644 godotengain/engainos/game_scenes/unknown_scene.json
 delete mode 100644 godotengain/engainos/godot/CharacterWanderer.gd
 delete mode 100644 godotengain/engainos/godot/CharacterWanderer.gd.uid
 delete mode 100644 godotengain/engainos/godot/CourierScene.gd
 delete mode 100644 godotengain/engainos/godot/CourierScene.gd.uid
 delete mode 100644 godotengain/engainos/godot/DialogueBubble.gd
 delete mode 100644 godotengain/engainos/godot/DialogueBubble.gd.uid
 delete mode 100644 godotengain/engainos/godot/EngAInBridge.gd
 delete mode 100644 godotengain/engainos/godot/EngAInBridge.gd.uid
 delete mode 100644 godotengain/engainos/godot/EngAinBridge.gd
 delete mode 100644 godotengain/engainos/godot/EngAinBridge.gd.uid
 delete mode 100644 godotengain/engainos/godot/GovernedHUD.gd
 delete mode 100644 godotengain/engainos/godot/GovernedHUD.gd.uid
 delete mode 100644 godotengain/engainos/godot/IntentMarker.gd
 delete mode 100644 godotengain/engainos/godot/IntentMarker.gd.uid
 delete mode 100644 godotengain/engainos/godot/SceneSpawner.gd
 delete mode 100644 godotengain/engainos/godot/SceneSpawner.gd.backup
 delete mode 100644 godotengain/engainos/godot/SceneSpawner.gd.uid
 delete mode 100644 godotengain/engainos/godot/Spatial3DAdapter.gd
 delete mode 100644 godotengain/engainos/godot/Spatial3DAdapter.gd.uid
 delete mode 100644 godotengain/engainos/godot/TestZWScene.tscn
 delete mode 100644 godotengain/engainos/godot/scenes/ap_clickable_cube.gd
 delete mode 100644 godotengain/engainos/godot/scenes/ap_clickable_cube.gd.uid
 delete mode 100644 godotengain/engainos/godot/scenes/ap_test_direct.gd
 delete mode 100644 godotengain/engainos/godot/scenes/ap_test_direct.gd.uid
 delete mode 100644 godotengain/engainos/godot/scenes/ap_test_simple.gd
 delete mode 100644 godotengain/engainos/godot/scenes/ap_test_simple.gd.uid
 delete mode 100644 godotengain/engainos/godot/scenes/heartbeat.gd
 delete mode 100644 godotengain/engainos/godot/scenes/heartbeat.gd.uid
 delete mode 100644 godotengain/engainos/godot/scenes/mesh_instance_3d_2.tscn
 delete mode 100644 godotengain/engainos/godot/scenes/node_3d.tscn
 delete mode 100644 godotengain/engainos/godot/scripts/ClickablePlaceholder.gd
 delete mode 100644 godotengain/engainos/godot/scripts/ClickablePlaceholder.gd.uid
 delete mode 100644 godotengain/engainos/godot/scripts/test_bridge.gd
 delete mode 100644 godotengain/engainos/godot/scripts/test_bridge.gd.uid
 delete mode 100644 godotengain/engainos/godotsim.gd
 delete mode 100644 godotengain/engainos/godotsim.gd.uid
 delete mode 100644 godotengain/engainos/healthtest.tscn
 delete mode 100644 godotengain/engainos/icon.svg
 delete mode 100644 godotengain/engainos/icon.svg.import
 delete mode 100644 godotengain/engainos/incoming_qued/AP_INTEGRATION_GUIDE.md
 delete mode 100644 godotengain/engainos/incoming_qued/AP_INTEGRATION_SNIPPET.py
 delete mode 100644 godotengain/engainos/incoming_qued/ENGINE_BOOTSTRAP.md
 delete mode 100644 godotengain/engainos/incoming_qued/FIXING_ZERO_RULES.md
 delete mode 100644 godotengain/engainos/incoming_qued/fix_scene_file.py
 delete mode 100644 godotengain/engainos/incoming_qued/test_ap_connection.gd
 delete mode 100644 godotengain/engainos/incoming_qued/test_ap_connection.gd.uid
 delete mode 100644 godotengain/engainos/incoming_qued/test_scene_loading.py
 delete mode 100644 godotengain/engainos/inspect_godot_adapter.py
 delete mode 100644 godotengain/engainos/node_3d.tscn
 delete mode 100644 godotengain/engainos/project.godot
 delete mode 100644 godotengain/engainos/renders/tts/test_timeline.json
 delete mode 100644 godotengain/engainos/runtime_api.py
 delete mode 100644 godotengain/engainos/scripts/AudioTimeline.gd
 delete mode 100644 godotengain/engainos/scripts/AudioTimeline.gd.uid
 delete mode 100644 godotengain/engainos/scripts/CombatHealthBar.gd
 delete mode 100644 godotengain/engainos/scripts/CombatHealthBar.gd.uid
 delete mode 100644 godotengain/engainos/scripts/EngineSummaryHUD.gd
 delete mode 100644 godotengain/engainos/scripts/EngineSummaryHUD.gd.uid
 delete mode 100644 godotengain/engainos/scripts/EngineSummaryHUD.v1
 delete mode 100644 godotengain/engainos/scripts/QuestTracker.gd
 delete mode 100644 godotengain/engainos/scripts/QuestTracker.gd.uid
 delete mode 100644 godotengain/engainos/scripts/QuestTracker.v1
 delete mode 100644 godotengain/engainos/scripts/QuestTracker.v2
 delete mode 100644 godotengain/engainos/scripts/fix_trixel_init.sh
 delete mode 100644 godotengain/engainos/scripts/test_audio_timeline.gd
 delete mode 100644 godotengain/engainos/scripts/test_audio_timeline.gd.uid
 delete mode 100644 godotengain/engainos/scripts/test_combat_healthbar.gd.uid
 delete mode 100644 godotengain/engainos/scripts/test_engine_summary.gd.uid
 delete mode 100644 godotengain/engainos/scripts/test_quest_tracker.gd.uid
 delete mode 100644 godotengain/engainos/scripts/verify_trixel_integration.sh
 delete mode 100644 godotengain/engainos/sim_test.json
 delete mode 100644 godotengain/engainos/start_stack.fish
 delete mode 100644 godotengain/engainos/test_ap_debug.py
 delete mode 100644 godotengain/engainos/test_bridge.gd
 delete mode 100644 godotengain/engainos/test_bridge.gd.uid
 delete mode 100644 godotengain/engainos/tests/test_empire_pure.py.bak
 delete mode 100644 godotengain/engainos/zon/timeline.jsonl

## Name status
D	godotengain/EngAInBridge.gd
D	godotengain/TestScene.tscn
D	godotengain/architectural_map_launch_engine (copy).md
D	godotengain/architectural_map_launch_engine.md
D	godotengain/engainos 1-18-26.tar.gz
D	godotengain/engainos/APSimulationDebugger.gd
D	godotengain/engainos/APSimulationDebugger.gd.uid
D	godotengain/engainos/ClickablePlaceholder.gd
D	godotengain/engainos/ClickablePlaceholder.gd.uid
D	godotengain/engainos/autoload/ZWRuntime.gd
D	godotengain/engainos/autoload/ZWRuntime.gd.uid
D	godotengain/engainos/cleanup_engain_tree.sh
M	godotengain/engainos/core/agent_gateway.py
D	godotengain/engainos/core/agent_gateway.py.broken
M	godotengain/engainos/core/ap_complex_rules.py
D	godotengain/engainos/core/ap_complex_rules.py.old
M	godotengain/engainos/core/ap_runtime.py
M	godotengain/engainos/core/authority_validator.py
D	godotengain/engainos/core/combat3d_mr.py.txt
D	godotengain/engainos/core/empire.py
D	godotengain/engainos/core/empire_agent_gateway.py
D	godotengain/engainos/core/empire_mr.py
D	godotengain/engainos/core/launch_bridge.py
D	godotengain/engainos/core/quest3d_integration
D	godotengain/engainos/core/quest3d_mr.v1
D	godotengain/engainos/core/run_all_quest_tests.sh
D	godotengain/engainos/core/scene_feature_registry.py
D	godotengain/engainos/core/scene_features_beach.py
M	godotengain/engainos/core/scene_loader.py
D	godotengain/engainos/core/scene_loader.py.bak
M	godotengain/engainos/core/scene_server.py
D	godotengain/engainos/core/scene_shell_builder.py
D	godotengain/engainos/core/scene_shell_builder.py.bak
D	godotengain/engainos/core/scene_shell_builder.py.before_sync_fix
D	godotengain/engainos/core/scene_shell_builder.py.pre_construction_relative
D	godotengain/engainos/core/scene_shell_builder.py.pre_pier_relative
D	godotengain/engainos/core/scene_shell_builder.py.pre_relative_fix
D	godotengain/engainos/core/test_quest3d_comprehensive.py
D	godotengain/engainos/core/test_quest3d_correct.py
D	godotengain/engainos/core/test_quest3d_proper.py
D	godotengain/engainos/core/test_quest_http.py
D	godotengain/engainos/core/test_quest_lifecycle.py
D	godotengain/engainos/core/test_sample_quests.py
D	godotengain/engainos/core/test_scene_shell_builder.py
D	godotengain/engainos/core/test_trixel_world_stack.py
D	godotengain/engainos/core/test_trixel_world_stack.py.bak
D	godotengain/engainos/core/test_trixel_world_stack.py.orig
D	godotengain/engainos/core/test_trixel_world_stack.py.pre_construction_relative
D	godotengain/engainos/core/test_trixel_world_stack.py.pre_pier_relative
D	godotengain/engainos/core/test_trixel_world_stack.py.pre_relative_fix
D	godotengain/engainos/core/test_trixel_world_stack.py.rej
D	godotengain/engainos/core/test_with_game_data.py
D	godotengain/engainos/core/trixel_world_adapter.py
D	godotengain/engainos/core/trixel_world_mr.py
D	godotengain/engainos/core/trixel_world_zw.py
D	godotengain/engainos/core/world_builder.py
D	godotengain/engainos/fix_godot_dependencies.sh
D	godotengain/engainos/game_scenes/test_scene.json
D	godotengain/engainos/game_scenes/unknown_scene.json
D	godotengain/engainos/godot/CharacterWanderer.gd
D	godotengain/engainos/godot/CharacterWanderer.gd.uid
D	godotengain/engainos/godot/CourierScene.gd
D	godotengain/engainos/godot/CourierScene.gd.uid
D	godotengain/engainos/godot/DialogueBubble.gd
D	godotengain/engainos/godot/DialogueBubble.gd.uid
D	godotengain/engainos/godot/EngAInBridge.gd
D	godotengain/engainos/godot/EngAInBridge.gd.uid
D	godotengain/engainos/godot/EngAinBridge.gd
D	godotengain/engainos/godot/EngAinBridge.gd.uid
D	godotengain/engainos/godot/GovernedHUD.gd
D	godotengain/engainos/godot/GovernedHUD.gd.uid
D	godotengain/engainos/godot/IntentMarker.gd
D	godotengain/engainos/godot/IntentMarker.gd.uid
D	godotengain/engainos/godot/SceneSpawner.gd
D	godotengain/engainos/godot/SceneSpawner.gd.backup
D	godotengain/engainos/godot/SceneSpawner.gd.uid
D	godotengain/engainos/godot/Spatial3DAdapter.gd
D	godotengain/engainos/godot/Spatial3DAdapter.gd.uid
D	godotengain/engainos/godot/TestZWScene.tscn
D	godotengain/engainos/godot/scenes/ap_clickable_cube.gd
D	godotengain/engainos/godot/scenes/ap_clickable_cube.gd.uid
D	godotengain/engainos/godot/scenes/ap_test_direct.gd
D	godotengain/engainos/godot/scenes/ap_test_direct.gd.uid
D	godotengain/engainos/godot/scenes/ap_test_simple.gd
D	godotengain/engainos/godot/scenes/ap_test_simple.gd.uid
D	godotengain/engainos/godot/scenes/heartbeat.gd
D	godotengain/engainos/godot/scenes/heartbeat.gd.uid
D	godotengain/engainos/godot/scenes/mesh_instance_3d_2.tscn
D	godotengain/engainos/godot/scenes/node_3d.tscn
D	godotengain/engainos/godot/scripts/ClickablePlaceholder.gd
D	godotengain/engainos/godot/scripts/ClickablePlaceholder.gd.uid
D	godotengain/engainos/godot/scripts/test_bridge.gd
D	godotengain/engainos/godot/scripts/test_bridge.gd.uid
D	godotengain/engainos/godotsim.gd
D	godotengain/engainos/godotsim.gd.uid
D	godotengain/engainos/healthtest.tscn
D	godotengain/engainos/icon.svg
D	godotengain/engainos/icon.svg.import
D	godotengain/engainos/incoming_qued/AP_INTEGRATION_GUIDE.md
D	godotengain/engainos/incoming_qued/AP_INTEGRATION_SNIPPET.py
D	godotengain/engainos/incoming_qued/ENGINE_BOOTSTRAP.md
D	godotengain/engainos/incoming_qued/FIXING_ZERO_RULES.md
D	godotengain/engainos/incoming_qued/fix_scene_file.py
D	godotengain/engainos/incoming_qued/test_ap_connection.gd
D	godotengain/engainos/incoming_qued/test_ap_connection.gd.uid
D	godotengain/engainos/incoming_qued/test_scene_loading.py
D	godotengain/engainos/inspect_godot_adapter.py
M	godotengain/engainos/launch_engine.py
D	godotengain/engainos/node_3d.tscn
D	godotengain/engainos/project.godot
D	godotengain/engainos/renders/tts/test_timeline.json
D	godotengain/engainos/runtime_api.py
D	godotengain/engainos/scripts/AudioTimeline.gd
D	godotengain/engainos/scripts/AudioTimeline.gd.uid
D	godotengain/engainos/scripts/CombatHealthBar.gd
D	godotengain/engainos/scripts/CombatHealthBar.gd.uid
D	godotengain/engainos/scripts/EngineSummaryHUD.gd
D	godotengain/engainos/scripts/EngineSummaryHUD.gd.uid
D	godotengain/engainos/scripts/EngineSummaryHUD.v1
D	godotengain/engainos/scripts/QuestTracker.gd
D	godotengain/engainos/scripts/QuestTracker.gd.uid
D	godotengain/engainos/scripts/QuestTracker.v1
D	godotengain/engainos/scripts/QuestTracker.v2
D	godotengain/engainos/scripts/fix_trixel_init.sh
D	godotengain/engainos/scripts/test_audio_timeline.gd
D	godotengain/engainos/scripts/test_audio_timeline.gd.uid
D	godotengain/engainos/scripts/test_combat_healthbar.gd.uid
D	godotengain/engainos/scripts/test_engine_summary.gd.uid
D	godotengain/engainos/scripts/test_quest_tracker.gd.uid
D	godotengain/engainos/scripts/verify_trixel_integration.sh
D	godotengain/engainos/sim_test.json
D	godotengain/engainos/start_stack.fish
D	godotengain/engainos/test_ap_debug.py
D	godotengain/engainos/test_bridge.gd
D	godotengain/engainos/test_bridge.gd.uid
D	godotengain/engainos/tests/test_empire_pure.py.bak
D	godotengain/engainos/zon/timeline.jsonl
