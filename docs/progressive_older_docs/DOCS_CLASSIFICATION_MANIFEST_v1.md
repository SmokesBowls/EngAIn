# DOCS CLASSIFICATION MANIFEST v1

Status: read-only classification manifest; no files moved
Scope: current `docs/` tree plus `/tmp/docs_classification_dry_run.txt` output
Source organizer: `organize_docs.py` dry-run only

---

## 1. Purpose

This manifest records a preservation-first classification map for `docs/`. It is an x-ray for review, not permission to move files.

No file should be moved from this manifest alone. Any future move must update references, preserve history anchors, and respect canonical/foundational documents.

## 2. Dry-run source summary

The dry-run at `/tmp/docs_classification_dry_run.txt` reported:

| Category | Count | Dry-run examples |
|---|---:|---|
| `runtime` | 35 | 21 COMPLETED — The Time Axis is fully defined.txt; Building_the_Self-Writing_AI_Game_Engine (transcribed on 01-Dec-2025 05-21-58).txt; ENHANCED_RUNTIME_GUIDE.txt |
| `subsystems` | 31 | DIALOGUE3D_COMPLETE.txt; ENGAIN_COMBAT3D_COMPLETE.txt; ENGAIN_ROADMAP.txt |
| `trixel` | 8 | TRIXEL_GUIDE.txt; trixelV4.zip; trixel_color_TODO.md |
| `pipeline` | 11 | The birth of soft coding.txt; ZON_FORMAT.txt; door_rule.zonj.txt |
| `godot` | 21 | ADD_BUTTONS_GUIDE.txt; CLIENT_AUDIT.txt; CLIENT_AUDIT_SUMMARY.txt |
| `terrain` | 1 | roundtrip_diff.txt |
| `gui_tools` | 10 | LITMUS_TEST_INSTALL.txt; cleanup_heavy_hitter.sh; litmus_test_patch.txt |
| `architecture` | 10 | CANONICAL_KEYS_FIX.txt; Enginality_A_Unified_Performance_Engine_Not_TTS (transcribed on 03-Dec-2025 00-05-09).txt; OKARCHITECT_PROJECT_BRIEF.txt |
| `archive` | 10 | CRITIQUE_RESPONSE.txt; ChatGPT-AI architecture summary.txt; Converting_Narrative_Prose_to_Game_Logic (transcribed on 01-Dec-2025 05-58-02).txt |
| `unclassified` | 2 | unpack_example_output.txt; unpack_out.txt |

Current scan note: this manifest was generated from the current `docs/` tree. Nested files already present under subdirectories are documented separately from the organizer dry-run, which only scans top-level `docs/` files.

## 3. Global DO-NOT-MOVE-YET set

These files/patterns are pinned until a reviewed migration plan updates references and confirms authority classification:

- `docs/TRIXEL_EMBODIMENT_CONTRACT_v1.md` if present at root
- `docs/trixel/contracts/TRIXEL_EMBODIMENT_CONTRACT_v1.md` if present in the current tree
- `docs/TRIXEL_EDITOR_OUTPUT_CLASSIFICATION_v1.md` if present
- all `README*` files
- all `*manifest*` / `*MANIFEST*` files
- all `*canon*` / `*CANON*` files
- all `*spec*` / `*SPEC*` files
- all `*contract*` / `*CONTRACT*` files
- all architecture anchors: `*architecture*`, `*architectual*`, `*architect*`, `OKARCHITECT*`, `STRUCTURE*`, `START_HERE*`, `PROTOCOL*`
- any guide or integration doc referenced by code, manifests, AGENTS.md, or another doc

Explicit current matches:

- `docs/CANONICAL_KEYS_FIX.txt`
- `docs/ChatGPT-AI architecture summary.txt`
- `docs/okarchitect_brief.txt`
- `docs/OKARCHITECT_PROJECT_BRIEF.txt`
- `docs/project.manifest.md`
- `docs/PROJECT_MANIFEST.txt`
- `docs/PROTOCOL_INTEGRATION.txt`
- `docs/README.txt`
- `docs/README_ENGAIN_GODOT.txt`
- `docs/START_HERE.txt`
- `docs/STRUCTURE.txt`
- `docs/system.manifest.md`
- `docs/test_protocol.txt`
- `docs/trixel/contracts/TRIXEL_EMBODIMENT_CONTRACT_v1.md`
- `docs/zon4dspec.txt`
- `docs/zork/compiled/README.txt`
- `docs/zork/README.md`

## 4. Category manifests

### 4.1 `runtime`

Proposed top-level files: 37

Belongs here if reviewed:
- `docs/21 COMPLETED — The Time Axis is fully defined.txt` — score 3; content:delta, content:state, content:physics
- `docs/alphascript.sh` — score 2; content:sim_runtime, content:runtime
- `docs/brokenloop_cli.md` — score 1; content:enforce
- `docs/Building_the_Self-Writing_AI_Game_Engine (transcribed on 01-Dec-2025 05-21-58).txt` — score 4; content:zw, content:state, content:physics, content:runtime
- `docs/CLIENT_AUDIT.txt` — score 8; content:zw, content:ZWR, content:tick, content:delta, content:state, content:physics, content:pause, content:runtime
- `docs/cmline.md` — score 2; content:sim_runtime, content:runtime
- `docs/coherant_runtime.md` — score 9; content:enforce, content:state, filename:coherant, filename:runtime, content:runtime
- `docs/deep zon4d freeze.txt` — score 5; content:zw, content:tick, content:state, content:physics, content:runtime
- `docs/engine_target.yml` — score 1; content:runtime
- `docs/ENHANCED_RUNTIME_GUIDE.txt` — score 6; content:sim_runtime, content:state, filename:runtime, content:runtime
- `docs/HARDENING_ROADMAP.txt` — score 9; content:sim_runtime, content:zw, content:ZWR, content:enforce, content:tick, content:delta, content:state, content:physics
- `docs/IMPLEMENTATION_SUCCESS.txt` — score 3; content:zw, content:enforce, content:state
- `docs/Init.md` — score 4; content:sim_runtime, content:zw, content:state, content:runtime
- `docs/Mistral frozen.txt` — score 2; content:zw, content:enforce
- `docs/oooZWRuntime.gd.txt` — score 9; filename:zw, filename:ZWR, filename:runtime
- `docs/oooZWRuntime.txt` — score 15; filename:zw, content:zw, filename:ZWR, content:ZWR, content:delta, content:state, content:pause, filename:runtime
- `docs/PARSE_ERROR_FIX.txt` — score 3; content:zw, content:ZWR, content:runtime
- `docs/PHASE_6_ENFORCEMENT (copy).txt` — score 10; content:sim_runtime, content:zw, content:ZWR, filename:enforce, content:enforce, content:tick, content:physics, content:runtime
- `docs/PHASE_6_ENFORCEMENT.txt` — score 10; content:sim_runtime, content:zw, content:ZWR, filename:enforce, content:enforce, content:tick, content:physics, content:runtime
- `docs/PROTOCOL_INTEGRATION.txt` — score 6; content:sim_runtime, content:zw, content:ZWR, content:tick, content:state, content:runtime
- `docs/remembertrixel.md` — score 5; content:zw, content:enforce, content:delta, content:state, content:runtime
- `docs/ROADMAP.txt` — score 5; content:zw, content:ZWR, content:enforce, content:state, content:runtime
- `docs/seeking feedbach.txt` — score 7; content:sim_runtime, content:zw, content:tick, content:delta, content:state, content:physics, content:runtime
- `docs/sim_runtime.old.txt` — score 10; filename:sim_runtime, content:sim_runtime, content:delta, content:state, filename:runtime, content:runtime
- `docs/sim_runtimeold.txt` — score 10; filename:sim_runtime, content:sim_runtime, content:delta, content:state, filename:runtime, content:runtime
- `docs/soft code to.txt` — score 3; content:zw, content:state, content:runtime
- `docs/son of a bith its fixed gpt.txt` — score 4; content:tick, content:delta, content:state, content:runtime
- `docs/START_HERE.txt` — score 7; content:sim_runtime, content:zw, content:enforce, content:delta, content:state, content:physics, content:runtime
- `docs/SUBSYSTEM_TEMPLATE.txt` — score 6; content:sim_runtime, content:zw, content:tick, content:delta, content:state, content:runtime
- `docs/zon4d freeze.txt` — score 5; content:zw, content:tick, content:state, content:physics, content:runtime
- `docs/zon4d tts.txt` — score 2; content:zw, content:state
- `docs/ZWRuntime.gd.txt` — score 17; content:sim_runtime, filename:zw, content:zw, filename:ZWR, content:ZWR, content:enforce, content:delta, content:state
- `docs/zwruntime_enforcement_patch (copy).txt` — score 16; filename:zw, content:zw, filename:ZWR, content:ZWR, filename:enforce, content:enforce, filename:runtime, content:runtime
- `docs/zwruntime_enforcement_patch.gd (copy).txt` — score 12; filename:zw, filename:ZWR, filename:enforce, filename:runtime
- `docs/zwruntime_enforcement_patch.gd.txt` — score 12; filename:zw, filename:ZWR, filename:enforce, filename:runtime
- `docs/zwruntime_enforcement_patch.txt` — score 16; filename:zw, content:zw, filename:ZWR, content:ZWR, filename:enforce, content:enforce, filename:runtime, content:runtime
- `docs/zwruntime_pause_patch.txt` — score 17; filename:zw, content:zw, filename:ZWR, content:ZWR, content:state, filename:pause, content:pause, filename:runtime

Pinned / do-not-move-yet within this category:
- `docs/PROTOCOL_INTEGRATION.txt`
- `docs/START_HERE.txt`

Canonical/foundational candidates:
- `docs/PROTOCOL_INTEGRATION.txt`
- `docs/START_HERE.txt`

Historical/archive candidates:
- `docs/Building_the_Self-Writing_AI_Game_Engine (transcribed on 01-Dec-2025 05-21-58).txt`
- `docs/deep zon4d freeze.txt`
- `docs/PARSE_ERROR_FIX.txt`
- `docs/PHASE_6_ENFORCEMENT (copy).txt`
- `docs/sim_runtime.old.txt`
- `docs/sim_runtimeold.txt`
- `docs/son of a bith its fixed gpt.txt`
- `docs/zon4d freeze.txt`
- `docs/zwruntime_enforcement_patch (copy).txt`
- `docs/zwruntime_enforcement_patch.gd (copy).txt`

Needs reference update before any move:
- `docs/21 COMPLETED — The Time Axis is fully defined.txt`
- `docs/brokenloop_cli.md`
- `docs/Building_the_Self-Writing_AI_Game_Engine (transcribed on 01-Dec-2025 05-21-58).txt`
- `docs/CLIENT_AUDIT.txt`
- `docs/cmline.md`
- `docs/coherant_runtime.md`
- `docs/deep zon4d freeze.txt`
- `docs/engine_target.yml`
- `docs/ENHANCED_RUNTIME_GUIDE.txt`
- `docs/HARDENING_ROADMAP.txt`
- `docs/IMPLEMENTATION_SUCCESS.txt`
- `docs/Init.md`
- `docs/Mistral frozen.txt`
- `docs/oooZWRuntime.gd.txt`
- `docs/oooZWRuntime.txt`
- `docs/PARSE_ERROR_FIX.txt`
- `docs/PHASE_6_ENFORCEMENT (copy).txt`
- `docs/PHASE_6_ENFORCEMENT.txt`
- `docs/PROTOCOL_INTEGRATION.txt`
- `docs/remembertrixel.md`
- `docs/ROADMAP.txt`
- `docs/seeking feedbach.txt`
- `docs/sim_runtime.old.txt`
- `docs/sim_runtimeold.txt`
- `docs/soft code to.txt`
- `docs/son of a bith its fixed gpt.txt`
- `docs/START_HERE.txt`
- `docs/SUBSYSTEM_TEMPLATE.txt`
- `docs/zon4d freeze.txt`
- `docs/zon4d tts.txt`
- `docs/ZWRuntime.gd.txt`
- `docs/zwruntime_enforcement_patch (copy).txt`
- `docs/zwruntime_enforcement_patch.gd (copy).txt`
- `docs/zwruntime_enforcement_patch.gd.txt`
- `docs/zwruntime_enforcement_patch.txt`
- `docs/zwruntime_pause_patch.txt`

### 4.2 `subsystems`

Proposed top-level files: 31

Belongs here if reviewed:
- `docs/alignment comparionb.txt` — score 8; content:combat, content:inventory, content:dialogue, content:behavior, content:adapter, content:3d, content:kernel, content:spatial
- `docs/behavior_adapter.old.txt` — score 12; filename:behavior, content:behavior, filename:adapter, content:adapter, content:3d, content:kernel, content:slice, content:spatial
- `docs/DIALOGUE3D_COMPLETE.txt` — score 12; content:combat, content:inventory, filename:dialogue, content:dialogue, content:adapter, filename:3d, content:3d, content:kernel
- `docs/engain_code_reference.txt` — score 6; content:behavior, content:adapter, content:3d, content:kernel, content:slice, content:spatial
- `docs/ENGAIN_COMBAT3D_COMPLETE.txt` — score 11; filename:combat, content:combat, content:behavior, content:adapter, filename:3d, content:3d, content:kernel
- `docs/ENGAIN_ROADMAP.txt` — score 6; content:combat, content:inventory, content:dialogue, content:adapter, content:3d, content:kernel
- `docs/engine project arch.txt` — score 9; content:combat, content:inventory, content:dialogue, content:behavior, content:adapter, content:3d, content:kernel, content:slice
- `docs/faction3d_adapter.txt` — score 13; filename:faction, content:faction, filename:adapter, content:adapter, filename:3d, content:3d, content:kernel
- `docs/FACTION3D_COMPLETE.txt` — score 12; filename:faction, content:faction, content:combat, content:dialogue, content:adapter, filename:3d, content:3d, content:kernel
- `docs/FACTION3D_GAP_ANALYSIS.txt` — score 10; filename:faction, content:faction, content:adapter, filename:3d, content:3d, content:kernel
- `docs/faction3d_kernel.txt` — score 13; filename:faction, content:faction, content:dialogue, filename:3d, content:3d, filename:kernel, content:kernel
- `docs/faction3d_proof.txt` — score 8; filename:faction, content:faction, filename:3d, content:3d
- `docs/FACTION3D_PROOF_INSTALL.txt` — score 14; filename:faction, content:faction, content:combat, content:inventory, content:dialogue, content:adapter, filename:3d, content:3d
- `docs/faction3d_proof_kernel.txt` — score 13; filename:faction, content:faction, filename:3d, content:3d, filename:kernel, content:kernel, content:spatial
- `docs/faction3d_validator.txt` — score 10; filename:faction, content:faction, content:adapter, filename:3d, content:3d, content:kernel
- `docs/FIX_KEYERROR_VEL.txt` — score 5; content:dialogue, content:behavior, content:3d, content:kernel, content:spatial
- `docs/HARDENING_GUIDE.txt` — score 5; content:adapter, content:3d, content:kernel, content:slice, content:spatial
- `docs/holly_mesh.txt` — score 8; content:combat, content:inventory, content:dialogue, content:behavior, content:adapter, content:3d, content:vault, content:spatial
- `docs/import_fix.txt` — score 5; content:behavior, content:adapter, content:3d, content:kernel, content:spatial
- `docs/INDENTATION_FIX.txt` — score 5; content:behavior, content:3d, content:kernel, content:slice, content:spatial
- `docs/init_fix.txt` — score 5; content:behavior, content:adapter, content:3d, content:kernel, content:spatial
- `docs/INVENTORY3D_COMPLETE.txt` — score 11; content:combat, filename:inventory, content:inventory, content:adapter, filename:3d, content:3d, content:kernel
- `docs/newruntime.md` — score 8; content:combat, content:inventory, content:dialogue, content:behavior, content:adapter, content:3d, content:vault, content:spatial
- `docs/phase 6 inforcemen.txt` — score 6; content:combat, content:behavior, content:adapter, content:3d, content:kernel, content:spatial
- `docs/QUICK_INTEGRATION.txt` — score 5; content:behavior, content:3d, content:kernel, content:slice, content:spatial
- `docs/QUICK_REFERENCE.txt` — score 8; content:combat, content:inventory, content:dialogue, content:behavior, content:adapter, content:3d, content:kernel, content:spatial
- `docs/round trip conversion.txt` — score 4; content:combat, content:adapter, content:kernel, content:spatial
- `docs/SLICE_INTEGRATION.txt` — score 9; content:behavior, content:adapter, content:3d, content:kernel, filename:slice, content:slice, content:spatial
- `docs/system.manifest.md` — score 9; content:combat, content:inventory, content:dialogue, content:behavior, content:adapter, content:3d, content:kernel, content:vault
- `docs/test_faction3d_proof.txt` — score 9; filename:faction, content:faction, filename:3d, content:3d, content:kernel
- `docs/THE GOVERNED REALITY MACHINE.txt` — score 8; content:combat, content:inventory, content:dialogue, content:behavior, content:3d, content:kernel, content:slice, content:spatial

Pinned / do-not-move-yet within this category:
- `docs/system.manifest.md`

Canonical/foundational candidates:
- `docs/system.manifest.md`

Historical/archive candidates:
- `docs/behavior_adapter.old.txt`
- `docs/DIALOGUE3D_COMPLETE.txt`
- `docs/FIX_KEYERROR_VEL.txt`
- `docs/import_fix.txt`
- `docs/INDENTATION_FIX.txt`
- `docs/init_fix.txt`

Needs reference update before any move:
- `docs/alignment comparionb.txt`
- `docs/behavior_adapter.old.txt`
- `docs/DIALOGUE3D_COMPLETE.txt`
- `docs/engain_code_reference.txt`
- `docs/ENGAIN_COMBAT3D_COMPLETE.txt`
- `docs/ENGAIN_ROADMAP.txt`
- `docs/engine project arch.txt`
- `docs/faction3d_adapter.txt`
- `docs/FACTION3D_COMPLETE.txt`
- `docs/FACTION3D_GAP_ANALYSIS.txt`
- `docs/faction3d_kernel.txt`
- `docs/faction3d_proof.txt`
- `docs/FACTION3D_PROOF_INSTALL.txt`
- `docs/faction3d_proof_kernel.txt`
- `docs/faction3d_validator.txt`
- `docs/FIX_KEYERROR_VEL.txt`
- `docs/HARDENING_GUIDE.txt`
- `docs/holly_mesh.txt`
- `docs/import_fix.txt`
- `docs/INDENTATION_FIX.txt`
- `docs/init_fix.txt`
- `docs/INVENTORY3D_COMPLETE.txt`
- `docs/newruntime.md`
- `docs/phase 6 inforcemen.txt`
- `docs/QUICK_INTEGRATION.txt`
- `docs/QUICK_REFERENCE.txt`
- `docs/round trip conversion.txt`
- `docs/SLICE_INTEGRATION.txt`
- `docs/system.manifest.md`
- `docs/test_faction3d_proof.txt`
- `docs/THE GOVERNED REALITY MACHINE.txt`

### 4.3 `trixel`

Proposed top-level files: 8

Belongs here if reviewed:
- `docs/trixel_color_TODO.md` — score 5; filename:trixel, content:trixel, content:palette
- `docs/TRIXEL_GUIDE.txt` — score 6; filename:trixel, content:trixel, content:palette, content:pixel
- `docs/trixel_tree_demoV1.zip` — score 3; filename:trixel
- `docs/trixel_work.md` — score 8; filename:trixel, content:trixel, content:brush, content:palette, content:pixel, content:stroke
- `docs/trixelV4.zip` — score 3; filename:trixel
- `docs/trixelworld_data.zip` — score 5; filename:trixel, content:brush, content:gbr
- `docs/trixelworld_data_tree_demoV2.zip` — score 5; filename:trixel, content:brush, content:gbr
- `docs/trixelworld_dataV3.zip` — score 5; filename:trixel, content:brush, content:gbr

Pinned / do-not-move-yet within this category:
- None detected by filename heuristic.

Canonical/foundational candidates:
- None detected by filename heuristic.

Historical/archive candidates:
- `docs/trixel_color_TODO.md`

Needs reference update before any move:
- `docs/trixel_color_TODO.md`
- `docs/TRIXEL_GUIDE.txt`
- `docs/trixel_tree_demoV1.zip`
- `docs/trixel_work.md`
- `docs/trixelV4.zip`
- `docs/trixelworld_data.zip`
- `docs/trixelworld_data_tree_demoV2.zip`
- `docs/trixelworld_dataV3.zip`

### 4.4 `pipeline`

Proposed top-level files: 11

Belongs here if reviewed:
- `docs/door_rule.zonj.txt` — score 3; filename:zonj
- `docs/engain_ingest.py` — score 9; content:pass1, content:pass2, content:pass3, content:zonj, content:narrative, filename:ingest, content:ingest
- `docs/narrative pipeline.txt` — score 7; content:pass1, content:zonj, filename:narrative, content:narrative, content:lore
- `docs/pack_example_output.txt` — score 1; content:zonj
- `docs/roadmap.txt` — score 6; content:metta, content:pass1, content:pass2, content:pass3, content:zonj, content:segment
- `docs/smoke_runtime_repo.sh` — score 5; content:metta, content:zonj, content:narrative, content:ingest, content:segment
- `docs/The birth of soft coding.txt` — score 5; content:zonj, content:narrative, content:compiler, content:lore, content:segment
- `docs/the_win_anti.txt` — score 4; content:metta, content:zonj, content:ingest, content:segment
- `docs/vault_registry.json` — score 5; content:metta, content:zonj, content:ingest, content:lore, content:segment
- `docs/zon4dspec.txt` — score 4; content:pass1, content:pass2, content:zonj, content:compiler
- `docs/ZON_FORMAT.txt` — score 2; content:narrative, content:entity

Pinned / do-not-move-yet within this category:
- `docs/zon4dspec.txt`

Canonical/foundational candidates:
- `docs/zon4dspec.txt`

Historical/archive candidates:
- None detected by filename heuristic.

Needs reference update before any move:
- `docs/door_rule.zonj.txt`
- `docs/engain_ingest.py`
- `docs/narrative pipeline.txt`
- `docs/pack_example_output.txt`
- `docs/roadmap.txt`
- `docs/smoke_runtime_repo.sh`
- `docs/The birth of soft coding.txt`
- `docs/the_win_anti.txt`
- `docs/vault_registry.json`
- `docs/zon4dspec.txt`
- `docs/ZON_FORMAT.txt`

### 4.5 `godot`

Proposed top-level files: 19

Belongs here if reviewed:
- `docs/ADD_BUTTONS_GUIDE.txt` — score 3; content:godot, content:scene, content:.gd
- `docs/capsulated.md` — score 3; content:godot, content:bridge, content:viewport
- `docs/CLIENT_AUDIT_SUMMARY.txt` — score 9; content:godot, content:scene, content:.gd, content:bridge, content:spawn, filename:client, content:client
- `docs/creation_pipeline.md` — score 7; content:godot, content:scene, content:tscn, content:spawn, content:client, content:render, content:viewport
- `docs/FIX_PRELOAD_ERROR.txt` — score 4; content:godot, content:scene, content:.gd, content:bridge
- `docs/fixed.md` — score 6; content:godot, content:scene, content:.gd, content:client, content:render, content:autoload
- `docs/godot_pathway.txt` — score 7; filename:godot, content:godot, content:scene, content:.gd, content:bridge
- `docs/holly_hell.txt` — score 4; content:godot, content:scene, content:.gd, content:bridge
- `docs/its_a_heavy_system.md` — score 3; content:godot, content:scene, content:render
- `docs/my_code_blurbs.md` — score 3; content:godot, content:scene, content:spawn
- `docs/perplexpoking.md` — score 7; content:godot, content:scene, content:.gd, content:bridge, content:client, content:render, content:autoload
- `docs/pipeline_test_complete_3-1-26.txt` — score 6; content:godot, content:scene, content:.gd, content:bridge, content:client, content:render
- `docs/proposal_pipeline.md` — score 5; content:godot, content:scene, content:spawn, content:client, content:render
- `docs/QUICKSTART.txt` — score 4; content:godot, content:scene, content:.gd, content:bridge
- `docs/README_ENGAIN_GODOT.txt` — score 11; filename:godot, content:godot, content:scene, content:.gd, content:bridge, content:spawn, content:client, content:render
- `docs/son of a bitch its fixed.txt` — score 7; content:godot, content:scene, content:.gd, content:bridge, content:spawn, content:client, content:render
- `docs/untitledgptbridge.md` — score 10; content:godot, content:scene, filename:bridge, content:bridge, content:spawn, content:client, content:render, content:viewport
- `docs/VAULT_INTEGRATION_GUIDE.gd` — score 9; content:godot, content:scene, filename:.gd, content:.gd, content:client, content:render, content:autoload
- `docs/yay_another_server.md` — score 3; content:godot, content:scene, content:bridge

Pinned / do-not-move-yet within this category:
- `docs/QUICKSTART.txt`
- `docs/README_ENGAIN_GODOT.txt`

Canonical/foundational candidates:
- None detected by filename heuristic.

Historical/archive candidates:
- `docs/CLIENT_AUDIT_SUMMARY.txt`
- `docs/FIX_PRELOAD_ERROR.txt`
- `docs/fixed.md`
- `docs/son of a bitch its fixed.txt`

Needs reference update before any move:
- `docs/ADD_BUTTONS_GUIDE.txt`
- `docs/capsulated.md`
- `docs/CLIENT_AUDIT_SUMMARY.txt`
- `docs/creation_pipeline.md`
- `docs/FIX_PRELOAD_ERROR.txt`
- `docs/fixed.md`
- `docs/godot_pathway.txt`
- `docs/holly_hell.txt`
- `docs/its_a_heavy_system.md`
- `docs/my_code_blurbs.md`
- `docs/perplexpoking.md`
- `docs/pipeline_test_complete_3-1-26.txt`
- `docs/proposal_pipeline.md`
- `docs/QUICKSTART.txt`
- `docs/README_ENGAIN_GODOT.txt`
- `docs/son of a bitch its fixed.txt`
- `docs/untitledgptbridge.md`
- `docs/VAULT_INTEGRATION_GUIDE.gd`
- `docs/yay_another_server.md`

### 4.8 `terrain`

Proposed top-level files: 1

Belongs here if reviewed:
- `docs/roundtrip_diff.txt` — score 1; content:field

Pinned / do-not-move-yet within this category:
- None detected by filename heuristic.

Canonical/foundational candidates:
- None detected by filename heuristic.

Historical/archive candidates:
- None detected by filename heuristic.

Needs reference update before any move:
- `docs/roundtrip_diff.txt`

### 4.10 `gui_tools`

Proposed top-level files: 10

Belongs here if reviewed:
- `docs/cleanup_heavy_hitter.sh` — score 6; filename:cleanup, content:cleanup, content:test_, content:pytest
- `docs/LITMUS_TEST_INSTALL.txt` — score 10; content:gui, content:patch, filename:test_, content:test_, filename:litmus, content:litmus
- `docs/litmus_test_patch.txt` — score 11; filename:patch, filename:test_, content:test_, filename:litmus, content:litmus
- `docs/pytest_all_output.txt` — score 8; filename:test_, content:test_, filename:pytest, content:pytest
- `docs/pytest_fixed.txt` — score 9; content:patch, filename:test_, content:test_, filename:pytest, content:pytest
- `docs/pytest_unit_combined_output.txt` — score 6; filename:test_, filename:pytest
- `docs/pytest_unit_output.txt` — score 6; filename:test_, filename:pytest
- `docs/pytest_unit_verbose.txt` — score 7; filename:test_, filename:pytest, content:pytest
- `docs/requirements.txt` — score 4; content:pytest, filename:requirements
- `docs/test_comprehensive.txt` — score 4; filename:test_, content:test_

Pinned / do-not-move-yet within this category:
- None detected by filename heuristic.

Canonical/foundational candidates:
- None detected by filename heuristic.

Historical/archive candidates:
- `docs/pytest_fixed.txt`

Needs reference update before any move:
- `docs/LITMUS_TEST_INSTALL.txt`
- `docs/litmus_test_patch.txt`
- `docs/pytest_all_output.txt`
- `docs/pytest_fixed.txt`
- `docs/pytest_unit_combined_output.txt`
- `docs/pytest_unit_output.txt`
- `docs/pytest_unit_verbose.txt`
- `docs/requirements.txt`
- `docs/test_comprehensive.txt`

### 4.11 `architecture`

Proposed top-level files: 10

Belongs here if reviewed:
- `docs/CANONICAL_KEYS_FIX.txt` — score 4; filename:canon, content:canon
- `docs/Enginality_A_Unified_Performance_Engine_Not_TTS (transcribed on 03-Dec-2025 00-05-09).txt` — score 4; content:roadmap, content:structure, content:design, content:architect
- `docs/frozen (1).txt` — score 3; content:structure, content:canon, content:architect
- `docs/okarchitect_brief.txt` — score 13; filename:okarchitect, filename:brief, content:brief, content:protocol, content:canon, filename:architect, content:architect
- `docs/OKARCHITECT_PROJECT_BRIEF.txt` — score 15; filename:okarchitect, content:okarchitect, content:structure, filename:brief, content:brief, content:protocol, content:canon, filename:architect
- `docs/project.manifest.md` — score 7; filename:manifest, content:manifest, content:protocol, content:canon, content:architect
- `docs/PROJECT_MANIFEST.txt` — score 7; filename:manifest, content:manifest, content:structure, content:protocol, content:canon
- `docs/README.txt` — score 5; content:structure, content:design, content:protocol, content:canon, content:architect
- `docs/STRUCTURE.txt` — score 7; content:roadmap, content:manifest, filename:structure, content:structure, content:protocol
- `docs/test_protocol.txt` — score 5; content:structure, filename:protocol, content:protocol

Pinned / do-not-move-yet within this category:
- `docs/CANONICAL_KEYS_FIX.txt`
- `docs/project.manifest.md`
- `docs/PROJECT_MANIFEST.txt`
- `docs/README.txt`
- `docs/STRUCTURE.txt`
- `docs/test_protocol.txt`

Canonical/foundational candidates:
- `docs/CANONICAL_KEYS_FIX.txt`
- `docs/project.manifest.md`
- `docs/PROJECT_MANIFEST.txt`
- `docs/STRUCTURE.txt`
- `docs/test_protocol.txt`

Historical/archive candidates:
- `docs/CANONICAL_KEYS_FIX.txt`
- `docs/Enginality_A_Unified_Performance_Engine_Not_TTS (transcribed on 03-Dec-2025 00-05-09).txt`

Needs reference update before any move:
- `docs/CANONICAL_KEYS_FIX.txt`
- `docs/Enginality_A_Unified_Performance_Engine_Not_TTS (transcribed on 03-Dec-2025 00-05-09).txt`
- `docs/frozen (1).txt`
- `docs/okarchitect_brief.txt`
- `docs/OKARCHITECT_PROJECT_BRIEF.txt`
- `docs/project.manifest.md`
- `docs/PROJECT_MANIFEST.txt`
- `docs/README.txt`
- `docs/STRUCTURE.txt`
- `docs/test_protocol.txt`

### 4.12 `archive`

Proposed top-level files: 10

Belongs here if reviewed:
- `docs/ChatGPT-AI architecture summary.txt` — score 7; content:old, content:log, filename:summary, content:summary, content:feedback
- `docs/Converting_Narrative_Prose_to_Game_Logic (transcribed on 01-Dec-2025 05-58-02).txt` — score 8; content:old, filename:log, content:log, filename:transcribed
- `docs/CRITIQUE_RESPONSE.txt` — score 3; content:log, content:summary, content:feedback
- `docs/FINAL_SESSION_SUMMARY.txt` — score 9; content:log, filename:summary, content:summary, filename:session, content:session
- `docs/FIX_1_SUMMARY.txt` — score 5; content:backup, content:log, filename:summary
- `docs/FIX_2_SUMMARY.txt` — score 6; content:old, content:backup, content:log, filename:summary
- `docs/generate_summary.py` — score 4; filename:summary, content:summary
- `docs/Letting_Chaos_Into_EngAIn’s_Rigid_Engine (transcribed on 26-Feb-2026 15-48-49).txt` — score 5; content:old, content:log, filename:transcribed
- `docs/SESSION_SUMMARY.txt` — score 9; content:log, filename:summary, content:summary, filename:session, content:session
- `docs/The_EngAIn_Core_Language_Stack_Decoded (transcribed on 02-Dec-2025 19-08-27).txt` — score 4; content:old, filename:transcribed

Pinned / do-not-move-yet within this category:
- `docs/ChatGPT-AI architecture summary.txt`

Canonical/foundational candidates:
- `docs/ChatGPT-AI architecture summary.txt`

Historical/archive candidates:
- `docs/ChatGPT-AI architecture summary.txt`
- `docs/Converting_Narrative_Prose_to_Game_Logic (transcribed on 01-Dec-2025 05-58-02).txt`
- `docs/CRITIQUE_RESPONSE.txt`
- `docs/FINAL_SESSION_SUMMARY.txt`
- `docs/FIX_1_SUMMARY.txt`
- `docs/FIX_2_SUMMARY.txt`
- `docs/generate_summary.py`
- `docs/Letting_Chaos_Into_EngAIn’s_Rigid_Engine (transcribed on 26-Feb-2026 15-48-49).txt`
- `docs/SESSION_SUMMARY.txt`
- `docs/The_EngAIn_Core_Language_Stack_Decoded (transcribed on 02-Dec-2025 19-08-27).txt`

Needs reference update before any move:
- `docs/ChatGPT-AI architecture summary.txt`
- `docs/Converting_Narrative_Prose_to_Game_Logic (transcribed on 01-Dec-2025 05-58-02).txt`
- `docs/CRITIQUE_RESPONSE.txt`
- `docs/FINAL_SESSION_SUMMARY.txt`
- `docs/FIX_1_SUMMARY.txt`
- `docs/FIX_2_SUMMARY.txt`
- `docs/generate_summary.py`
- `docs/Letting_Chaos_Into_EngAIn’s_Rigid_Engine (transcribed on 26-Feb-2026 15-48-49).txt`
- `docs/SESSION_SUMMARY.txt`
- `docs/The_EngAIn_Core_Language_Stack_Decoded (transcribed on 02-Dec-2025 19-08-27).txt`

### 4.13 `unclassified`

Proposed top-level files: 2

Belongs here if reviewed:
- `docs/unpack_example_output.txt` — score 0; no keyword reason
- `docs/unpack_out.txt` — score 0; no keyword reason

Pinned / do-not-move-yet within this category:
- None detected by filename heuristic.

Canonical/foundational candidates:
- None detected by filename heuristic.

Historical/archive candidates:
- None detected by filename heuristic.

Needs reference update before any move:
- `docs/unpack_example_output.txt`
- `docs/unpack_out.txt`

## 5. Already nested docs observed

These files are already under subdirectories and were not part of the top-level dry-run move list. Preserve their current paths unless separately reviewed.

- `docs/trixel parser pack/mnt/user-data/outputs/trixelworld/module_gbr/gbr_parser_mr.py`
- `docs/trixel parser pack/mnt/user-data/outputs/trixelworld/module_gdyn/gdyn_parser_mr.py`
- `docs/trixel parser pack/mnt/user-data/outputs/trixelworld/module_gpl/gpl_parser_mr.py`
- `docs/trixel parser pack/mnt/user-data/outputs/trixelworld/module_gtp/gpt_parser_mr.py`
- `docs/trixel parser pack/parser.py`
- `docs/trixel/contracts/TRIXEL_EMBODIMENT_CONTRACT_v1.md`
- `docs/trixel/reviews/TRIXEL_EDITOR_OUTPUT_REVIEW_NOTES.md`
- `docs/zork/compiled/door_rule.zonb`
- `docs/zork/compiled/README.txt`
- `docs/zork/QUICK_START.md`
- `docs/zork/README.md`
- `docs/zork/test_unpack_fixed.zonj.json`
- `docs/zork/test_unpack_fixed_rt.json`
- `docs/zork/test_unpack_fixed_test.zonb`

## 6. Reference update requirements before any move

Before moving any file listed in this manifest:

1. Search the repository for references to the exact filename and relative path.
2. Update markdown links, script paths, AGENTS.md references, manifest references, and docs cross-links in the same change as the move.
3. For canonical/foundational docs, prefer adding an index/redirect note over moving the file.
4. For archives and transcribed memory anchors, preserve original names unless the user explicitly approves renaming.
5. For generated artifacts, identify the generator before moving or regenerating.
6. For `.zip`, `.zonb`, `.zonj`, `.json`, `.gd`, `.py`, `.sh`, `.yml`, and patch/output files, confirm whether code or scripts consume the path.
7. After a proposed move plan, run a dry-run diff and do not execute mass moves without explicit approval.

## 7. Safe next step

Treat this file as the reviewed classification ledger. The next safe operation is not `python3 organize_docs.py --execute`; it is a smaller migration plan that selects one low-risk category, pins constitutional docs, updates references, and provides rollback instructions.
