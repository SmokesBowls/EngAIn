# EngAIn Handshake Inventory

Last updated: 2026-07-16. A **handshake** (a.k.a. payload, contract) is the accumulated
information a script needs from elsewhere to not fail. Every entry answers three questions:
**who asks** (consumer), **who gives** (provider), and **what the handshake consists of**.

Status legend:
- **WIRED** — code on both ends exists and the paths/ports line up today.
- **BROKEN** — code on both ends exists but a path, port, or import is stale.
- **HALF** — one side is real code, the other side is missing or external.
- **DOC-ONLY** — a contract document exists in `docs/contracts/` but no code enforces
  or produces it yet.

The 5-day gate process left real artifacts: `docs/contracts/` holds per-system authority
contracts (some now enforced by gates in code, some aspirational). This file is the
*as-wired* truth; `docs/contracts/` is the *as-intended* doctrine. Where they disagree,
this file says so.

See also `docs/architecture/TIER2_PRODUCTION_MAP.md` — per-system inventory of exactly
what each tier2 system (topologist, cartographer, godotsim, engionality, worldfield)
produces for EngAInOS, including the finding that godotsim's `runtime_gateway` is
EngAInOS admission logic resident in tier2. The formerly missing "Grid facts" crew
member was rehoused 2026-07-17 as `tier2/worldfield/` (WorldField float authority +
threshold classification + terrain plan packets; smoke-tested as package and CLI).

---

## 1. The vault chain (narrative source → runtime scenes)

### 1a. mettaext ingest ← Obsidian vault — **WIRED (manual CLI)**
- **Asks:** `tier3/mettaext/engain_ingest.py` (also `master_pipeline.py` / `pipeline_runner.py`)
- **Gives:** `/home/mytruelove/Downloads/obsidianburdenNov25` (the vault)
- **Handshake:** a directory of chapter `.md` files, passed as `--vault <dir>` (or `--file`
  / `--scan`); plus `--out <dir>` for output. No hardcoded vault path in live code —
  the path is supplied per-invocation. (Archived tools under `tier1/mrlore/archive/old_tools/`
  hardcode `~/Downloads/obsidianburdenNov25/_mrlore`; archive only.)
- Note: `vault.manifest.json` is NOT needed here — it belongs to handshake 1c.

### 1b. mettaext pass5 → runtime vault cache — **WIRED**
- **Asks:** `tier2/godotsim/vault_manager.py` (runtime scene lookup)
- **Gives:** `tier3/mettaext/passroom/pass5_game_bridge.py` via `run1time.py`
- **Handshake:** game-ready scene JSON files `scene.<chapter>.json` (entities + events)
  written to `EngAIn/.vault_cache/obsidianburdennov25/` (path hardcoded in
  `run1time.py:71`). `vault_manager` reads `ROOT/.vault_cache/<vault_id>/`.
- Caveat: `run1time.py:9` reads `tier3/manifests/world_rules.json`, which does not exist
  (world rules actually live at `tier1/engainos/assets/world_rules.json`) — so the
  one-shot runner is **BROKEN at its input** even though its output seam is correct.

### 1c. runtime `/vault/link` ← vault manifest — **WIRED, ungated**
- **Asks:** any HTTP caller of `POST 127.0.0.1:8080/vault/link` (this is how a session
  attaches a vault to the live runtime)
- **Gives:** the vault itself — `vault.manifest.json` at the vault root
- **Handshake:** JSON body `{ "manifest": <dict or path>, "vault_root": <abs path>,
  "manifest_path"?: <path>, "vault_id"?: <str> }`. `vault_linker.link()` discovers `.md`
  files per the manifest's `content.source_markdown.dir`, registers scenes into
  `runtime.vault_scenes`, records the vault in the snapshot, and persists via
  `save_vault_config` so the runtime re-links on next boot.
- Governance note: endpoint is ungated (TODO.md governance gap).

### 1d. runtime `/world/sync` → mettaext ingest — **BROKEN**
- **Asks:** `tier2/godotsim/http_handlers.py:~648` (vault rebuild trigger)
- **Gives:** should be `tier3/mettaext/engain_ingest.py`
- **Handshake:** subprocess call `python engain_ingest.py --vault <root> --out <build dir>
  --pipeline-dir <mettaext>` — but it resolves `ROOT_DIR/engain_ingest.py` and
  `ROOT_DIR/mettaext`, both pre-rehousing paths. Fix = point at `tier3/mettaext/`.

### 1e. runtime `/scene/load` ← scene document — **WIRED, path-read risk**
- **Asks:** any HTTP caller of `POST 8080/scene/load`
- **Gives:** caller supplies the scene inline, by id, or by file path
- **Handshake:** JSON body with one of: `scene_id` / `@id` / `id` (resolved against
  linked vault scenes), an embedded `scene` or `zonj` object (`entities` + `segments`/
  `events`), or `source_path` pointing at a scene JSON on disk. The `source_path` variant
  reads arbitrary caller-supplied filesystem paths (known governance gap).

---

## 2. Sim runtime HTTP surface (port 8080) — the hub

- **Gives:** `tier2/godotsim/sim_runtime.py` (multi-threaded HTTP server, port 8080).
- **Asks:** the tier1 facade (`runtime_client.py`), tools, and the Godot semantic POC
  client — located at `godotnew/semantic/autoload/SimClient.gd` in the pre-move copy
  (`/mnt/data-drive/burdens_of_a_forgotten_past/EngAIn`), with uncommitted local edits.
- **Handshake surface:**
  - GET: `/health`, `/status`, `/snapshot`, `/transforms`, `/embodiment/pending`,
    `/environment/terrain/<scene_id>`, `/vault/status`, `/vault/search`
  - POST: `/command`, `/scene/load`, `/vault/link`, `/world/sync`, `/world/load_mirror`,
    `/transforms`, `/embodiment/apply`, plus legacy `/combat/damage`, `/inventory/take`,
    `/inventory/drop`, `/inventory/wear`, `/dialogue/ask` (rewritten into `/command`)
- `/command` governance is `runtime_gateway.py` (RuntimeGateway), NOT
  `authority_gate.evaluate()` — that only runs behind the 8090 facade.
- Inside 8080, `scene_manager.py:32,41` tries bare imports of `scene_extractor` /
  `bridge_integration` (the semantic-POC entity + placeholder-visual systems) and
  silently disables them on failure — **BROKEN import seam**, fix pending (TODO.md).

## 3. Facade HTTP surface (port 8090) → runtime 8080

- **Gives:** `tier1/engainos/engainos_server.py` (FastAPI facade). **Asks onward:**
  `tier1/engainos/runtime_client.py` → `http://127.0.0.1:8080` (override with env
  `NGAT_RT_BASE_URL`). This is the tier boundary: facade = witness/authority layer,
  runtime = execution layer.
- **Handshake surface (asker side, what a caller must send):**
  - `POST /api/command` — `{command dict}` (forwarded to 8080 `/command`)
  - `POST /api/combat/damage` — `{source, target, damage}`
  - `POST /api/inventory/take|drop|wear` — `{actor, item[, location]}`
  - `POST /api/dialogue/say|ask` — dialogue dict
  - GET `/api/health`, `/api/snapshot`, `/api/hud/engine`, `/api/hud/combat`,
    `/api/hud/inventory`, `/api/hud/engine_summary` (read-only projections)
- `GET /api/trixel/artwork/{scene_id}` serves newest PNG from
  `EngAIn/trixelcomposer/.zw/artwork/` — **BROKEN/HALF**: `trixelcomposer/` is
  externalized (trixel suite under reconstruction), so this always 404s.
- Live combat payload mismatch: complex AP rules match `attacker`/`amount` keys but this
  path sends `source`/`damage` — rules can never fire (TODO.md governance gap).

## 4. Boot handshake: kernel ↔ Godot (file-drop protocol) — **WIRED & proven**

The only fully proven bidirectional handshake in the repo. Transport is JSON files, not HTTP.

### 4a. Boot scene command
- **Asks (consumer):** `godot/boot/GodotBootBridgeConsumeCommand.gd`
- **Gives (producer):** `executors/boot_scene_load_executor_v1.py`, orchestrated by
  root `engainos_boot_kernel.py` after `gates/` preflight
- **Handshake:** `runtime/godot_commands/BOOT_SCENE_LOAD_COMMAND_V1.json` with exactly:
  `contract = "engainos.godot_boot_shell_command.v1"`,
  `command_type = "LOAD_BOOT_SHELL_SCENE"`, `scene_id = "engainos.boot.empty"`,
  `scene_resource_path = "res://scenes/EngAInOSBootShell.tscn"`. Godot validates every
  field and refuses to act on mismatch.

### 4b. Boot report (return handshake)
- **Asks:** `engainos_boot_kernel.py` (reads it back to declare boot complete)
- **Gives:** the Godot boot bridge
- **Handshake:** `runtime/godot_reports/GODOT_BOOT_BRIDGE_CONSUME_COMMAND_V1.report.json`
  (`contract = "godot.boot_bridge_consume_command_report.v1"`, `ok`, `status`,
  `blocked_by`, mutation-denial flags). Kernel also writes
  `runtime/logs/BOOT_SCENE_AUTHORIZATION_DECISION_V1.json`,
  `BOOT_SCENE_LOAD_EXECUTOR_DECISION_V1.json`, and
  `ENGAINOS_BOOT_KERNEL_LAST_RUN.json`.

### 4c. Player input listener command + input packet
- **Gives:** `executors/player_input_listener_executor_v1.py` →
  `runtime/godot_commands/PLAYER_INPUT_LISTENER_COMMAND_V1.json`
  (`contract = "engainos.godot_player_input_listener_command.v1"`,
  `command_type = "ATTACH_BOOT_SHELL_INPUT_LISTENER"`, `input_mode =
  "boot_shell_input_probe"`).
- **Asks/consumes:** `godot/input/GodotInputListenerBridgeConsumeCommand.gd`, which then
  **gives back** `runtime/input_packets/PLAYER_INPUT_PACKET_V1.json`
  (`contract = "engainos.player_input_packet.v1"`) plus its own report.
- **Asks (final):** `gates/gate_boot_shell_presentation_ready_v1.py` verifies the packet
  and report exist and conform.

## 5. Spatial-truth packet chain (the new doctrine pipeline)

Prose → topology → metric layout → narrative concurrence → authority verification.
Each stage is a packet handshake; producers and consumers are library seams (no HTTP),
currently orchestrated by hand.

### 5a. mettaext passroom → topologist — **WIRED (file seam)**
- **Gives:** `tier3/mettaext/passroom/pass1_spatial.py` →
  `out_pass1_spatial_<stem>.json`: `{ source_pass1, signal_count, signals[] }`
- **Asks:** `tier2/topologist/artifactroom/passroom_signal_converter.py` — converts
  signals into a `ProseTopologyArtifact`. Doctrine: "producer describes, consumer
  interprets"; passroom never imports topologist.

### 5b. topologist → cartographer — **WIRED code, hand-carried packet**
- **Gives:** topologist `reckoningroom/topology_validator.py` →
  `accepted_spatial_truth` packet: `{ packet_type=accepted_spatial_truth,
  source_artifact_id, entities, qslinks, olinks, movelinks }`
- **Asks:** `tier2/cartographer/layoutroom/topology_metric_layout_solver.py`
- Contract doc: `docs/contracts/CARTOGRAPHER_METRIC_LAYOUT_CONTRACT_v1.md`

### 5c. cartographer → mrlore — **contract + partial code**
- **Gives:** cartographer → `engain.cartographer_metric_layout.v1` proposal:
  `{ artifact_id, source_artifact_id, source_packet_hash, lifecycle=PROPOSED,
  coordinate_space=world_cell_y_up, unit=meter, axis_contract, anchor_entity_id,
  entities (x/y/z), applied_constraints, unresolved_constraints }`
- **Asks:** MrLore narrative concurrence, which also needs the original
  `accepted_spatial_truth` **and** `source_prose` (three inputs). Output:
  `narratively_concurred_metric_layout` (`lifecycle=CONCURRED`, `contradictions`,
  `unresolved_findings`, unaltered coordinate map).
- Contract doc: `docs/contracts/MRLORE_NARRATIVE_CONCURRENCE_CONTRACT_v1.md`
- Final step (EngAInOS contract/authority verification → canonical) is **DOC-ONLY**.

## 6. Control-center gate packets (engain_control framework)

- **Gives (framework):** root `engain_control/` — `gate_print.run_script_gates` +
  `GateResult`. Imported by every control center; this was the output of the gate
  process and it IS live code.
- **Asks/validates:**
  - `tier1/mrlore/mrlore_control_center.py` — claim packets: required fields, enum
    values, claims structure, contradictions-if-present, no lane theft, no auto-resolve,
    no vault-path dependency, contradiction-stop proof.
  - `tier2/engionality/engionality_control_center.py` — `engionality.affect_packet.v1`:
    affect state valid, intensity bounds, relationship deltas if present, scene mood if
    present, no lane theft. **HALF**: gate rails exist; no live producer feeds affect
    packets into the runtime yet (engainos control center references the contract).
  - `tier1/engainos/engainos_control_center.py` — board-level checks.
  - Root `engain_master_control_center.py` — master board across systems.
- **Handshake shape:** plain Python dicts ("packets") with `packet_type`/`contract`
  fields; each system's `gates/` directory is the authoritative field list.

## 7. Trixel seams (2D → 3.2D, under reconstruction)

**Standing decision (2026-07-16):** ALL trixel lives outside EngAIn until trixel3.2d is
finished (`~/Desktop/burdens_of_a_forgotten_past/trixel3.2d`, its own git repo). The 2D
trixel remnants were evicted to `~/Desktop/burdens_of_a_forgotten_past/trixel_legacy_2d/`
(see its EVICTION_MANIFEST.md). When trixel returns, it returns as ONE system with ONE
handshake — the trixel32d surface request below — never as four suites with private seams.

### 7a. trixel32d surface request/response — **FIXTURE PATH PROVEN; TRANSPORT UNWIRED**

This is a two-direction handshake and the direction matters (corrected 2026-07-16 —
an earlier revision of this file wrongly said trixel "emits" the request):

- **Asks (requester — assembled, not dispatched):** EngAInOS authors
  `trixel32d_surface_request` through
  `tier1/engainos/bridgeroom/trixel32d_request_assembler.py`. The 3×2 canonical
  fixture is gate-verified. No transport caller or live dispatcher exists.
- **Gives (builder — canonical fixture proven):** trixel3.2d consumes the request
  and returns `trixel32d_surface_built`: status `BUILT` (full `geometry` plus
  row-major `cell_geometry_ranges` and provenance in `TRIXEL_LOCAL_Y_UP`) or
  `REJECTED` (`geometry = null`, first validation failure in `errors`). The exact
  3×2 built-response fixture is persisted and passes EngAIn's response validator.
- **Consumes (presentation proof only):** `/mnt/data-drive/godotollama` commit
  `b05e704` validates the exact built-response bytes and passively materializes one
  in-memory `ArrayMesh`; 10/10 headless tests pass. Nothing in the EngAIn runtime
  consumes or applies the response yet.
- **Role of the in-EngAIn gate:**
  `tier1/engainos/gates/gate_trixel32d_handshake.py` validates outgoing requests
  and returned built responses. It is not a dispatcher, transport, application
  authorizer, or runtime consumer.
- **Still unwired:** request/response transport, runtime application validation,
  runtime execution, scene attachment, and consume-report return.
- Full request/response spec:
  `docs/contracts/TRIXEL32D_SURFACE_REQUEST_CONTRACT_v1.md`.
- Assembly + passive-consumer requirements:
  `docs/contracts/TRIXEL32D_REQUEST_ASSEMBLY_AND_CONSUMER_v1.md`.

### 7a.1. trixel32d surface application — **CONTRACT ONLY; NO EXECUTOR**

After a built response is identity-completely validated, EngAInOS may issue an
immutable `trixel32d_surface_apply.v1` authorization for a future executor. It
names the exact built-response hash, target scene revision, declared parent and
slot, local-to-scene transform, visibility, exact replacement target, lifetime,
and classification. This is not a new EngAInOS-to-GodotSim transport.

- **Application authority:** EngAInOS alone issues and accepts the packet under AP,
  actor-tier, reality-mode, and runtime-session governance.
- **Physical execution:** collision `GRANTED` is an explicit EngAInOS decision
  bound to the same scene, surface, transform, classification, layer, and mask.
  GodotSim may later admit or refuse exact execution through its governed
  simulation lane, but it cannot grant AP or rewrite the declaration.
- **Presentation:** Godot remains passive and may not infer any missing placement,
  replacement, persistence, or collision field.
- **Current stop:** doctrine only. No validator, transport, runtime attachment,
  collision allocation, state mutation, or execution receipt exists.
- Full application authority contract:
  `docs/contracts/TRIXEL32D_SURFACE_APPLY_CONTRACT_v1.md`.

### 7b. facade artwork bridge — **REMOVED 2026-07-16**. The `/api/trixel/artwork/`
  endpoint was deleted from `engainos_server.py` (it pointed at the externalized 2D
  `trixelcomposer/.zw/artwork`). The old PNGs survive in the pre-move copy at
  `/mnt/data-drive/burdens_of_a_forgotten_past/EngAIn/trixelcomposer/.zw/artwork/`.
  Artwork re-entry must come through the 7a handshake.

### 7c. 2D remnants evicted — `tier2/godotsim/trixel_composer.py`,
  `mechanimation/trixel_bridge.py` + `trixel_composer/`, `out of root/engain/render/
  trixel.py`, and the old-doctrine `docs/contracts/TRIXEL_TIER1_AUTHORITY/` now live at
  `~/Desktop/burdens_of_a_forgotten_past/trixel_legacy_2d/from_engain/`. Nothing in the
  repo imported them (verified before the move).

### 7d. `.trixel` skin-manifest format — **STAYED (consumer side)**. The runtime still
  understands `.trixel` skin manifests: `semantic_bridge.py` scans them,
  `bridgeroom/zon_to_entities.py` binds `assets/trixels/{concept}.trixel` skins,
  `embodiment_contract_builder.py` emits `trixel_embodiment.v1`. `assets/trixels/` is
  currently empty; `launch_engine.py:137` soft-asserts a `tools/trixel/` that no longer
  exists (non-critical warning). This machinery is the in-EngAIn socket the finished
  3.2d producer will feed — or replace when the 7a contract settles.

## 8. External services

- **Blender MCP** — **Asks:** `tier2/godotsim/environment_manager.py` /
  `blender_mcp_bridge.py`; **Gives:** MCP server at `http://127.0.0.1:8000`;
  **Handshake:** terrain-generation commands; results exposed at
  `GET 8080/environment/terrain/<scene_id>`. HALF — works only when Blender MCP is up.
- **Ollama** — **Asks:** `tools/ollama_diff_patcher.py` (and archived mrlore tools);
  **Gives:** `http://127.0.0.1:11434/api/generate`; **Handshake:** `{model, prompt}`.
  Tooling-only, not runtime.

## 9. AP rule engines (two distinct systems — do not conflate)

- **aproom ZW engine** (`tier1/engainos/aproom/ap_engine.py`, doctrine in `APZWV.1/`):
  in-process rule engine + `contract_validator.py` used by `command_dispatcher` /
  facade. No live 8765 listener found in current tree.
- **ap/0.1 governance registry** (`ap_rule_loader.py` / `ap_rule_evaluator.py` behind
  `authority_gate.evaluate()`): loader/evaluator implemented, **zero rule files** at
  `tier1/engainos/rules/runtime_mutation/` — any mutating/unknown action raises
  `APRuleLoadError` (TODO.md known bug). The *handshake it wants* is `.zon` rule files
  in that directory.

## 10. Shared manifest inputs

- **Gives:** `tier1/engainos/assets/world_rules.json` + `engain_manifest.json` (the
  live copies; `manifests/` at root and `out of root/manifests/` are historical).
- **Asks:** runtime boot, `tier3/mettaext/world_rules_loader.py` (repaired to point
  here — see `.bak_engainos_assets_rules` history), and `zw_world_rules_compiler.py`.
- Broken asker: `run1time.py` (see §1b caveat).

---

## Quick repair list (handshakes that fail today)

1. `/world/sync` → ingest paths (`http_handlers.py:~648`): `ROOT_DIR/engain_ingest.py`,
   `ROOT_DIR/mettaext` → `tier3/mettaext/…`
2. `run1time.py:9` world-rules path → `tier1/engainos/assets/world_rules.json`
3. `scene_manager.py:32,41` bare imports → package-relative (SceneExtractor,
   SemanticBridge silently disabled)
4. Facade trixel artwork root → decide where rebuilt trixelcomposer output will live
5. ap/0.1 registry empty → author first `.zon` rules or make the gate fail-closed
