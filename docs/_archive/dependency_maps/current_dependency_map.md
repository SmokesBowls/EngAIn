# current_dependency_map

Scope: godotsim and godotnew/semantic (read-only)

## godotsim

### `godotsim/sim_runtime.py`
- file path: `godotsim/sim_runtime.py`
- role: Main HTTP simulation runtime (port 8080 API anchor)
- imports/calls: import json; import os; import argparse; import threading; import time; import inspect; import sys; from http.server import ThreadingHTTPServer; calls: get, isinstance, getattr, setdefault, update, abspath, callable, exit, open, _ensure_bridge_entities_in_snapshot
- called by: godotsim/runtime_core.py, godotsim/vault_linker.py, godotnew/semantic/scripts/Boot.gd
- hardcoded paths: /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn
- safe_to_move: no
- notes: hardcoded path literals present; referenced by other in-scope files; active contract/entrypoint or path-coupled

### `godotsim/runtime_core.py`
- file path: `godotsim/runtime_core.py`
- role: Runtime core state/orchestration
- imports/calls: import copy; import json; import math; import os; import random; import re; import subprocess; import sys; calls: get, isinstance, KernelContractError, append, abspath, join, deep_freeze, dirname, exists, extend
- called by: godotsim/sim_runtime.py, godotsim/command_dispatcher.py, godotsim/scene_manager.py
- hardcoded paths: none detected
- safe_to_move: no
- notes: referenced by other in-scope files; active contract/entrypoint or path-coupled

### `godotsim/command_dispatcher.py`
- file path: `godotsim/command_dispatcher.py`
- role: Gameplay command routing and action dispatch
- imports/calls: from typing import Dict, Any, TYPE_CHECKING; calls: get, in, handle_delta, handle_text_command, Commands, isinstance, lower, split, strip, type
- called by: godotsim/sim_runtime.py, godotsim/runtime_core.py, godotsim/scene_manager.py
- hardcoded paths: none detected
- safe_to_move: later
- notes: referenced by other in-scope files; move only with coordinated refactor + runtime verification

### `godotsim/protocol_envelope.py`
- file path: `godotsim/protocol_envelope.py`
- role: Transport envelope/parser helpers
- imports/calls: import hashlib; import json; from typing import Dict, Any, Optional; import time; calls: _make_serializable, isinstance, time, ProtocolEnvelope, ProtocolError, __hook__, __init__, append, create_envelope_for_runtime, dumps
- called by: godotsim/runtime_core.py
- hardcoded paths: none detected
- safe_to_move: later
- notes: referenced by other in-scope files; move only with coordinated refactor + runtime verification

### `godotsim/scene_manager.py`
- file path: `godotsim/scene_manager.py`
- role: Scene load/registry lifecycle
- imports/calls: from typing import Dict, Any, List, TYPE_CHECKING; calls: get, isinstance, join, append, lower, strip, _find_entity, to_dict, in, items
- called by: godotsim/sim_runtime.py, godotsim/runtime_core.py, godotsim/command_dispatcher.py, godotsim/vault_manager.py
- hardcoded paths: none detected
- safe_to_move: later
- notes: referenced by other in-scope files; move only with coordinated refactor + runtime verification

### `godotsim/scene_extractor.py`
- file path: `godotsim/scene_extractor.py`
- role: Scene extraction/normalization utilities
- imports/calls: import re; import os; import json; from typing import Dict, Any, List, Optional, Tuple; from collections import defaultdict; calls: get, items, lower, append, _get_context, search, _override_path, extract, open, SceneExtractor
- called by: godotsim/scene_manager.py
- hardcoded paths: none detected
- safe_to_move: later
- notes: referenced by other in-scope files; move only with coordinated refactor + runtime verification

### `godotsim/semantic_bridge.py`
- file path: `godotsim/semantic_bridge.py`
- role: Narrative/semantic bridge into runtime scene model
- imports/calls: from dataclasses import dataclass, field; from typing import Dict, Optional, List, Any; import json; import yaml; from pathlib import Path; from spatial_skin_system import Entity3D, Transform3D, ColorRGB; calls: get, _fallback, any, items, resolve_concept, ColorRGB, ConceptProfile, _semantic_fallback, get_skin_for_concept, load
- called by: none detected
- hardcoded paths: none detected
- safe_to_move: later
- notes: move only with coordinated refactor + runtime verification

### `godotsim/vault_manager.py`
- file path: `godotsim/vault_manager.py`
- role: Vault indexing/storage/search management
- imports/calls: import json; import os; import subprocess; import time; from dataclasses import dataclass; from typing import Any, Dict, List, Optional, Tuple; calls: get, isinstance, append, join, open, strip, _read_json, _safe_mkdir, exists, select_active_scene
- called by: godotsim/sim_runtime.py, godotsim/runtime_core.py
- hardcoded paths: none detected
- safe_to_move: later
- notes: referenced by other in-scope files; move only with coordinated refactor + runtime verification

### `godotsim/vault_linker.py`
- file path: `godotsim/vault_linker.py`
- role: Vault runtime link/search adapter
- imports/calls: import json; import os; import re; import hashlib; from pathlib import Path; from typing import Dict, List, Any, Optional, Union; from datetime import datetime; calls: get, strip, Path, sorted, split, startswith, replace, append, dumps, expanduser
- called by: godotsim/sim_runtime.py, godotsim/runtime_core.py
- hardcoded paths: none detected
- safe_to_move: later
- notes: referenced by other in-scope files; move only with coordinated refactor + runtime verification

## godotnew/semantic

### `godotnew/semantic/scripts/Boot.gd`
- file path: `godotnew/semantic/scripts/Boot.gd`
- role: Semantic boot pipeline; adapts scene payload then planner/renderer
- imports/calls: extends Node; const SemanticActorScene := preload("res://entities/SemanticActor.tscn"); const TrixelEnvironmentPlanner := preload("res://trixel/TrixelEnvironmentPlanner.gd"); calls: get, String, typeof, has, is_empty, size, strip_edges, to_lower, connect, get_node_or_null
- called by: none detected
- hardcoded paths: /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/.engain_cache/terrain_plans/scene.proof.001_worldfield_plan.json, /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/manifests/world_rules.json, /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/mettaext/semantic_environment_extractor.py, res://entities/SemanticActor.tscn, res://primitive_vocabulary_bindings.json, res://render_policy.json, res://trixel/TrixelEnvironmentPlanner.gd
- safe_to_move: no
- notes: hardcoded path literals present; active contract/entrypoint or path-coupled

### `godotnew/semantic/scripts/Main.gd`
- file path: `godotnew/semantic/scripts/Main.gd`
- role: Semantic scene controller entry script
- imports/calls: none detected; calls: none
- called by: godotsim/runtime_core.py, godotsim/vault_linker.py, godotnew/semantic/scripts/Boot.gd
- hardcoded paths: none detected
- safe_to_move: later
- notes: referenced by other in-scope files; move only with coordinated refactor + runtime verification

### `godotnew/semantic/scripts/SceneClient.gd`
- file path: `godotnew/semantic/scripts/SceneClient.gd`
- role: HTTP client for runtime scene/snapshot/commands
- imports/calls: none detected; calls: none
- called by: godotnew/semantic/scripts/Boot.gd
- hardcoded paths: none detected
- safe_to_move: later
- notes: referenced by other in-scope files; move only with coordinated refactor + runtime verification

### `godotnew/semantic/scripts/SemanticRenderer.gd`
- file path: `godotnew/semantic/scripts/SemanticRenderer.gd`
- role: Active semantic renderer used by runtime logs
- imports/calls: extends Node3D; calls: get, push_warning, is_empty, Vector3, size, get_tree, get_node_or_null, new, rebuild_scene, _atlas_static
- called by: godotnew/semantic/scripts/Boot.gd, godotnew/semantic/autoload/TrixelTileClient.gd
- hardcoded paths: res://trixel/trixelassets
- safe_to_move: no
- notes: hardcoded path literals present; referenced by other in-scope files; active contract/entrypoint or path-coupled

### `godotnew/semantic/trixel/TrixelEnvironmentPlanner.gd`
- file path: `godotnew/semantic/trixel/TrixelEnvironmentPlanner.gd`
- role: Terrain topology planner + Python world-field bridge
- imports/calls: extends RefCounted; class_name TrixelEnvironmentPlanner; calls: get, String, is_empty, strip_edges, size, typeof, has, Vector2i, append, to_lower
- called by: godotnew/semantic/scripts/Boot.gd, godotnew/semantic/scripts/SemanticRenderer.gd
- hardcoded paths: /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/terrain/trixel_world_adapter.py
- safe_to_move: no
- notes: hardcoded path literals present; referenced by other in-scope files; active contract/entrypoint or path-coupled

### `godotnew/semantic/trixel/TrixelAtlas.gd`
- file path: `godotnew/semantic/trixel/TrixelAtlas.gd`
- role: Atlas family/edge/corner/path topology resolver
- imports/calls: extends Node2D; calls: get, _terrain_at, push_warning, Rect2, Vector2, Rect2i, size, Vector2i, _build_sample_grid, _draw_legend
- called by: none detected
- hardcoded paths: res://trixel/trixelassets
- safe_to_move: no
- notes: hardcoded path literals present; active contract/entrypoint or path-coupled

### `godotnew/semantic/autoload/TrixelTileClient.gd`
- file path: `godotnew/semantic/autoload/TrixelTileClient.gd`
- role: Godot runtime bridge client to tile HTTP server
- imports/calls: extends Node; calls: emit, uri_encode, get, has, _load_texture_from_file, _update_connected, connect, fetch_atlas, push_warning, _load_atlas_for
- called by: godotnew/semantic/scripts/SemanticRenderer.gd
- hardcoded paths: none detected
- safe_to_move: no
- notes: referenced by other in-scope files; active contract/entrypoint or path-coupled
