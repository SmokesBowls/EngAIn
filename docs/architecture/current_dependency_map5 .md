# AP/Authority Layer & Narrative Ingestion Pipeline Dependency Map

This document establishes the structural roles, calling patterns, and paths for the authoritative server runtime under `godotengain/engainos/` and the narrative extraction pipeline under `mettaext/`.

---

## 1. AP/Authority Engine & Facade Layer (`godotengain/engainos`)

Enforces authority tiers, validates state mutability, runs determinism checks, and serves endpoints for Godot adapters.

### [launch_engine.py](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/godotengain/engainos/launch_engine.py)
* **File Path:** `godotengain/engainos/launch_engine.py`
* **Role:** Autoritative bootstrap entrypoint. Resolves core path authorities, verifies strict module/import boundaries, validates core logic files, starts the Scene HTTP server on port 8765, and binds stdin/stdout loops to the Godot adapters.
* **Imports/Calls:** `ap_engine.StateProvider`, `ap_engine.ZWAPEngine`, `ap_runtime.APRuntimeIntegration`, `scene_server.start_scene_server`, `godot_adapter`
* **Called By:** Started manually by operators/shell pipelines to initiate runtime AP environments.
* **Hardcoded Paths:** `/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn` (validated root directory), `/game_scenes`
* **Safe to Move:** **No** (The canonical bootstrap script relies heavily on localized expectations).
* **Notes:** Expected Python 3.10+. Enforces import boundaries: `core` must not import `godot` or `tools`, and `tools` must not import `godot`.

---

### [engainos_server.py](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/godotengain/engainos/engainos_server.py)
* **File Path:** `godotengain/engainos/engainos_server.py`
* **Role:** FastAPI supervisor and kernel proxy facade. Connects to the main simulation server, maps inventory, dialogue, and combat endpoints, and projects flat read-only summaries for the Godot HUD.
* **Imports/Calls:** `FastAPI`, `HTTPException`, `runtime_client.NGATRTClient`
* **Called By:** supervisor loops started on port 8090.
* **Hardcoded Paths:** None (Uses environment variable `NGAT_RT_BASE_URL` defaulting to `http://127.0.0.1:8080`).
* **Safe to Move:** **Yes** (FastAPI facade; decoupled from filesystem state).
* **Notes:** Returns deterministic `502 Bad Gateway` if backend snapshot channels fail.

---

### [runtime_client.py](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/godotengain/engainos/runtime_client.py)
* **File Path:** `godotengain/engainos/runtime_client.py`
* **Role:** Lightweight client proxy. Invokes HTTP requests via `urllib.request` to talk to the core gameplay simulation backend (port 8080).
* **Imports/Calls:** `urllib.request`, `urllib.error`, `json`
* **Called By:** `engainos_server.py`
* **Hardcoded Paths:** None (Defaults to environment variable `NGAT_RT_BASE_URL` or `http://127.0.0.1:8080`).
* **Safe to Move:** **Yes** (Standalone client model).
* **Notes:** Features automatic retries with exponential backoffs.

---

### [ap_engine.py](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/godotengain/engainos/core/ap_engine.py)
* **File Path:** `godotengain/engainos/core/ap_engine.py`
* **Role:** Deterministic AP rules processor (ZWAPEngine). Loads rules from metta outputs, evaluates state predicates, computes read/write resource sets, resolves conflict overlaps, and appends actions to the ZON timeline.
* **Imports/Calls:** `re`, `time`, `json`, `dataclass`
* **Called By:** `ap_runtime.py`, `launch_engine.py`
* **Hardcoded Paths:** `/zon/timeline.jsonl` (relative timeline ledger file)
* **Safe to Move:** **Yes** (Self-contained mathematical logic rules evaluator).
* **Notes:** Maintains strict conflict resolution checks based on write-sets.

---

### [ap_runtime.py](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/godotengain/engainos/core/ap_runtime.py)
* **File Path:** `godotengain/engainos/core/ap_runtime.py`
* **Role:** AP integration manager. Loads rules and maps runtime state Provider data between snapshot dictionaries and the rules evaluator.
* **Imports/Calls:** `ap_engine.ZWAPEngine`, `ap_engine.StateProvider`, `json`
* **Called By:** `launch_engine.py`
* **Hardcoded Paths:** `/rules.json` (load directories)
* **Safe to Move:** **Later** (Coordinates between game directories).
* **Notes:** Handles structural mappings.

---

### [authority_validator.py](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/godotengain/engainos/core/authority_validator.py)
* **File Path:** `godotengain/engainos/core/authority_validator.py`
* **Role:** Reality checker module. Determines if incoming actions comply with active mutability modes (DRAFT, IMBUED, FINALIZED, DREAM, REPLAY) and checks sender access tiers (Tier 0: System, Tier 1: AI Agent, Tier 2: Limited Operator, Tier 3: Root Operator).
* **Imports/Calls:** `reality_mode`
* **Called By:** Gateway middleware.
* **Hardcoded Paths:** None.
* **Safe to Move:** **Yes** (Deterministic rules validator).
* **Notes:** Refuses all mutations in REPLAY mode; blocks non-Tier-3 operators on FINALIZED canon.

---

### [agent_gateway.py](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/godotengain/engainos/core/agent_gateway.py)
* **File Path:** `godotengain/engainos/core/agent_gateway.py`
* **Role:** Gateway gateway checking incoming commands against authority validations before dispatching to the main dispatcher.
* **Imports/Calls:** `authority_validator.py`
* **Called By:** Command dispatcher processes.
* **Hardcoded Paths:** None.
* **Safe to Move:** **Yes**
* **Notes:** Direct gatekeeper for AI agents.

---

### [reality_mode.py](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/godotengain/engainos/core/reality_mode.py)
* **File Path:** `godotengain/engainos/core/reality_mode.py`
* **Role:** Constants declaring active modes of simulation state mutability.
* **Imports/Calls:** None.
* **Called By:** `authority_validator.py`
* **Hardcoded Paths:** None.
* **Safe to Move:** **Yes**
* **Notes:** Flat domain definitions.

---

### [intent_shadow.py](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/godotengain/engainos/core/intent_shadow.py)
* **File Path:** `godotengain/engainos/core/intent_shadow.py`
* **Role:** Audit ledger logger recording rejected or pending state changes that were blocked by validation checks.
* **Imports/Calls:** `json`, `os`
* **Called By:** Gateways.
* **Hardcoded Paths:** None.
* **Safe to Move:** **Yes**
* **Notes:** Non-mutating logs.

---

### [history_xeon.py](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/godotengain/engainos/core/history_xeon.py)
* **File Path:** `godotengain/engainos/core/history_xeon.py`
* **Role:** Flat chronometer module logging valid timeline steps with timestamps.
* **Imports/Calls:** `time`
* **Called By:** `ap_engine.py`
* **Hardcoded Paths:** None.
* **Safe to Move:** **Yes**
* **Notes:** Audit tool.

---

### [godot_adapter.py](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/godotengain/engainos/core/godot_adapter.py)
* **File Path:** `godotengain/engainos/core/godot_adapter.py`
* **Role:** Standard input/output pipe coordinator. Bridges terminal process stdout prints with Godot client command receivers.
* **Imports/Calls:** `sys`, `json`
* **Called By:** `launch_engine.py`
* **Hardcoded Paths:** None.
* **Safe to Move:** **No** (Directly bound to engine stdio streams).
* **Notes:** Core I/O link.

---
---

## 2. Narrative Ingestion & Semantic Pipeline (`mettaext`)

Chains compilation passes to turn raw textual lore into structured segment indexes, runs MeTTa semantic inferences, converts them to 4D declarative ZON memory fabrics, and builds game-ready cell grids.

### [pipeline_runner.py](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/mettaext/pipeline_runner.py)
* **File Path:** `mettaext/pipeline_runner.py`
* **Role:** Ingestion pipeline runner. Chains raw text segmentation (P1-P5) and compiler augmentations (ZW-C), then sends a scene load POST request to the simulation server on port 8080.
* **Imports/Calls:** `subprocess`, `json`, `urllib.request`, `urllib.error`
* **Called By:** Operators importing raw narrative drafts.
* **Hardcoded Paths:** `manifests/engain_manifest.json`, `http://127.0.0.1:8080/scene/load` (HTTP POST URL)
* **Safe to Move:** **No** (Relies on directory hierarchy relative to root manifests).
* **Notes:** Direct deployment runner.

---

### [master_pipeline.py](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/mettaext/master_pipeline.py)
* **File Path:** `mettaext/master_pipeline.py`
* **Role:** Orchestrator controller. Invokes passes 1 through 5 sequentially via subprocess loops and outputs structured `.zonj.json` files.
* **Imports/Calls:** `subprocess`, `argparse`, `json`, `pathlib`
* **Called By:** `pipeline_runner.py`
* **Hardcoded Paths:** None (Input/output paths parameterized).
* **Safe to Move:** **Yes** (Strictly orchestrates other pass scripts).
* **Notes:** Outputs full pipeline status reports.

---

### [pass1_explicit.py](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/mettaext/pass1_explicit.py)
* **File Path:** `mettaext/pass1_explicit.py`
* **Role:** Pass 1 text structuring segmenter. Reads raw textual stories and splits them into typed lines (e.g. dialogue, description, narration) with sequential line markers.
* **Imports/Calls:** `re`, `json`
* **Called By:** `master_pipeline.py`
* **Hardcoded Paths:** None.
* **Safe to Move:** **Yes** (Stateless text tokenizer).
* **Notes:** First parsing layer.

---

### [pass2_enhanced.py](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/mettaext/pass2_enhanced.py)
* **File Path:** `mettaext/pass2_enhanced.py`
* **Role:** Pass 2 semantic inference compiler. Evaluates structured segments to infer actor intentions, character emotions, action labels, and thoughts.
* **Imports/Calls:** `json`
* **Called By:** `master_pipeline.py`
* **Hardcoded Paths:** None.
* **Safe to Move:** **Yes** (MeTTa-compatible inference logic builder).
* **Notes:** Yields relational annotations.

---

### [pass3_merge.py](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/mettaext/pass3_merge.py)
* **File Path:** `mettaext/pass3_merge.py`
* **Role:** Pass 3 data merger. Merges textual segment blocks from Pass 1 with inferred semantic details from Pass 2 into unified ZONJ scene definitions.
* **Imports/Calls:** `json`
* **Called By:** `master_pipeline.py`
* **Hardcoded Paths:** None.
* **Safe to Move:** **Yes** (Stateless JSON merger).
* **Notes:** Consolidates raw segmentation and reasoning layers.

---

### [pass4_zon_bridge.py](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/mettaext/pass4_zon_bridge.py)
* **File Path:** `mettaext/pass4_zon_bridge.py`
* **Role:** Pass 4 memory conversion bridge. Assigns temporal (@when) and spatial (@where) metadata anchors to ZONJ maps to generate declarative 4D ZON memory fabrics (`.zon` and `.zonj.json`).
* **Imports/Calls:** `json`, `argparse`, `pathlib.Path`
* **Called By:** `master_pipeline.py`
* **Hardcoded Paths:** None.
* **Safe to Move:** **Yes** (Uses parameter inputs).
* **Notes:** Extracts region keywords to guess terrain categories (coastal, sand, grass, etc.) and environment bounds.

---

### [pass5_game_bridge.py](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/mettaext/pass5_game_bridge.py)
* **File Path:** `mettaext/pass5_game_bridge.py`
* **Role:** Pass 5 game world builder. Transmutes 4D memory fabrics into actual game-ready cell grids, spawns character entries, defines level boundaries and hazards, and builds the unified `scene_index.json`.
* **Imports/Calls:** `json`, `argparse`, `pathlib.Path`
* **Called By:** `master_pipeline.py`
* **Hardcoded Paths:** `scene_index.json` (writes scene index in outputs)
* **Safe to Move:** **Yes** (Stateless grid layout exporter).
* **Notes:** Automatically infers regional layout bounds and hazard density cues directly from descriptive prose contexts.
