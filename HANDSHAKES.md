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
- **WIRED — PARTIAL GOVERNANCE** — code on both ends works today and the route
  performs some admission checks, but AP enforcement is incomplete (see §9).
  Acceptance on such a route means "not rejected". It permits candidate or
  non-canonical operations but does **not** establish authoritative world-state
  commitment, and it is **never** canon approval.
- **RESERVED** — named in architecture or doctrine as a future interface; no working
  implementation and no current contract. Systems may *design* for it and declare
  future compatibility; they must not *integrate against* it.
- **UNRESOLVED** — more than one implementation, or no owner, and the intended
  relationship has not been decided. Preserve every current implementation; do not
  treat any one as canonical; do not modify them on this file's authority.

This file has two parts:
- **Part I (§1–§10) — Verified handshakes:** what connects and works today, with
  code references.
- **Part II (§11) — Ecosystem integration rules:** what future systems must respect.

**Precedence.** There are two axes. Neither replaces the other.
- *What the code does now:* Part I is authoritative.
- *What a system is supposed to do:* existing architectural contracts
  (`docs/contracts/`, `ENGAINOS_AUTHORITY_MAP.md`, frozen authority doctrine) remain
  authoritative.
- When the two disagree, record the gap in §11.9 (Discrepancy register). A
  verified defect describes the code; it does not rewrite the intended design.
  A doc's intention does not make an unwired interface usable.

Evidence tags: `[verified <date>]` checked against code; `[rule: <source>]` existing
doctrine; `[proposed]` pending approval; `[rule: HANDSHAKES §11, approved <date>]`
approved Part II rule.

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

### 1b. runtime vault cache ← vault_linker — **WIRED, ungated**  [verified 2026-10-13]
- **Asks:** 8080 runtime — `runtime.vault_scenes`, filled at boot relink
  (`sim_runtime.py:153-154`, env-gated) and by `POST /vault/link` (§1c).
- **Gives:** `tier2/godotsim/vault_linker.py`. It converts Obsidian markdown to ZONJ
  with its own converter (`_md_to_zonj`, `vault_linker.py:167`) and writes
  `.vault_cache/<vault_id>/*.zonj.json` + `_index.json` (`_write_cache`, `:395-418`).
  Current cache: `.vault_cache/obsidianburdennov25/`, index generated 2026-06-21,
  2715 scenes.
- Mettaext output does not travel this seam. `run1time.py` is now a 34-line
  deprecated shim that delegates to `pipeline_runner`; the previously cited
  `run1time.py:9` and `:71` no longer exist.
- **Relationship to §1f: UNRESOLVED.** Two narrative→ZONJ extractors exist and serve
  different consumers (this one: 8080 runtime; §1f: 8765 SceneLoader). See §11.4.

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

### 1e. runtime `/scene/load` ← scene document — **WIRED — PARTIAL GOVERNANCE, path-read risk**
- **Asks:** any HTTP caller of `POST 8080/scene/load`
- **Gives:** caller supplies the scene inline, by id, or by file path
- **Handshake:** JSON body with one of: `scene_id` / `@id` / `id` (resolved against
  linked vault scenes), an embedded `scene` or `zonj` object (`entities` + `segments`/
  `events`), or `source_path` pointing at a scene JSON on disk. The `source_path` variant
  reads arbitrary caller-supplied filesystem paths (known governance gap).

### 1f. mettaext → stageroom → EngAInOS SceneLoader (8765) — **WIRED (file seam, no AP)**  [verified 2026-10-13]
- **Gives:** `tier3/mettaext/pipeline_runner.py` writes
  `tier3/mettaext/stageroom/output/passroom/<scene_id>/game_scenes/<scene_id>.json`,
  the chapterroom `scene_packets_index.json`, and `stageroom/mettaext_done_manifest.json`.
  It pushes nothing: `pipeline_runner.py:140` prints
  `METTAEXT_PUSHES_TO_STAGEROOM_ONLY=TRUE`.
- **Asks:** `tier1/engainos/bridgeroom/stageroom_scene_resolver.py` (fails closed on
  scene_id mismatch, `:159-163`) → `scene_loader.py:28` (default mode) →
  `scene_server.py:203-245` (`/load_scene`, `/load_chapter`, `/list_scenes`) on 8765,
  started by `launch_engine.py:237-242`.
- **Authority:** none. The resolver "neither dispatches nor grants AP/canon approval"
  (`stageroom_scene_resolver.py:3-4`).
- **Relationship to §1b: UNRESOLVED** (see §11.4).
- Known defect: `pass5_game_bridge.py:716-719` bare-imports
  `semantic_environment_extractor` from `passroom/`, but the module lives in
  `tier3/mettaext/`. The `except` at `:730` swallows the error, so pass5 always falls
  back to prose voting.

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
  Admission on `/command` is **WIRED — PARTIAL GOVERNANCE** (§9); ungoverned routes
  are listed in §11.3.
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

### 7a. trixel32d surface request/response — **IDENTITY-COMPLETE FIXTURE PATH PROVEN; TRANSPORT UNWIRED**

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
  3×2 built-response fixture is now vendored under EngAIn tests and pinned at
  SHA-256 `bc1951f55de00aa0114679fab1a46d80439d1b840309b0df4c9b835539dd2929`.
- **Consumes (presentation proof only):** `/mnt/data-drive/godotollama` commit
  `b05e704` validates the exact built-response bytes and passively materializes one
  in-memory `ArrayMesh`; 10/10 headless tests pass. Nothing in the EngAIn runtime
  consumes or applies the response yet.
- **Role of the in-EngAIn gate:**
  `tier1/engainos/gates/gate_trixel32d_handshake.py` validates outgoing requests
  and identity-complete built responses. Its byte-level API hashes and parses the
  same bytes, matches request identity, recomputes surface identity, and returns
  the exact response digest; its dict helper is semantic-only. The gate is not a
  dispatcher, transport, application authorizer, or runtime consumer.
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

## 9. AP rule engines (three distinct things — do not conflate)  [verified 2026-10-13]

- **8080 admission gateway — WIRED — PARTIAL GOVERNANCE.**
  `tier2/godotsim/runtime_gateway.py` (logic extracted from the off-repo
  `empire_agent_gateway.py`). Called from `http_handlers.py:293-295` (`/command` +
  legacy aliases) and inline at `:403-440` (`/scene/load`). Uses aproom
  `reality_mode`, `canon`, `core/intent_shadow`, `ap_complex_rules`, and
  `authority_gate.ACTION_CLASSIFICATION` (table only).
  Why it is partial: global mode defaults to DRAFT and nothing calls `set_mode` /
  `finalize_scene`; `canon.can_edit` is True for unregistered scenes; the 2 complex
  rules match `attacker`/`amount`, which no live caller sends; `/scene/load` skips
  complex rules entirely. Rejections are recorded in Intent Shadow (in memory only).
- **aproom ZW engine on 8765 — WIRED, 0 rules.** `launch_engine.py:179,193-194` builds
  `APRuntimeIntegration(scenes_dir=tier1/engainos/game_scenes)`; `scene_server`
  routes `/ap_*` to it. Those 111 scene JSONs are a legacy scene set, not stageroom
  output; none carry `rules` or event conditions/actions, so 0 rules load.
  `ap_engine.py` is imported but unused (a duplicate of `ap_zw_engine`).
- **ap/0.1 governance registry (8090 only) — BROKEN.** `authority_gate.evaluate()` →
  `ap_rule_loader.load("runtime_mutation")`. `tier1/engainos/rules/` does not exist,
  so non-read-only actions raise an uncaught `APRuleLoadError` (HTTP 500 — a crash,
  not a deliberate deny). The authority/reality checks inside `evaluate` are a TODO
  stub. Rule files survive only in the pre-move copy
  (`/mnt/data-drive/.../godotengain/engainos/rules/runtime_mutation/`).
- No unit test in `tier1/engainos/tests` imports any AP module; AP is exercised only by
  `tier1/engainos/gates/gate_ap_*.py`, several of which use stale `godotengain/` paths.

## 10. Shared manifest inputs

- **Gives:** `tier1/engainos/assets/world_rules.json` + `engain_manifest.json` (the
  live copies; `manifests/` at root and `out of root/manifests/` are historical).
- **Asks:** runtime boot, `tier3/mettaext/world_rules_loader.py` (repaired to point
  here — see `.bak_engainos_assets_rules` history), and `zw_world_rules_compiler.py`.

---

## Quick repair list (handshakes that fail today)

1. `/world/sync` → ingest paths (`http_handlers.py:~648`): `ROOT_DIR/engain_ingest.py`,
   `ROOT_DIR/mettaext` → `tier3/mettaext/…`
2. pass5 semantic-extractor import (§1f)
3. `scene_manager.py:32,41` bare imports → package-relative (SceneExtractor,
   SemanticBridge silently disabled)
4. Facade trixel artwork root → decide where rebuilt trixelcomposer output will live
5. ap/0.1 registry empty → author first `.zon` rules or make the gate fail-closed.
   8090 currently fails as a 500, not as a deliberate deny.

---

# Part II — Ecosystem integration rules

## 11. Rules for new and future systems

### 11.1 Independent development vs integration  [rule: HANDSHAKES §11, approved 2026-10-13]
A new system (Trixel 3.2D, Cartographer, Mechanimation, or anything unnamed) is built
and run **independently**. It need not import, run, or wait for any EngAIn component.
At its EngAIn boundary it must:
1. File an Integration Impact Statement (§11.8) before designing its EngAIn adapter.
2. **Integrate now** only through interfaces whose Part I status is WIRED or
   WIRED — PARTIAL GOVERNANCE, and treat the latter as admission of candidate or
   non-canonical operations, never as authoritative commitment or canon.
3. **Declare future compatibility** with RESERVED, DOC-ONLY or UNRESOLVED interfaces
   as stated requirements, isolated in its adapter, never as a runtime dependency.

A dormant EngAIn component is never a reason to block a new tool, and never a
thing to build against.

### 11.2 Interface status for integrators  [verified 2026-10-13]
| Concern | Status | Where |
|---|---|---|
| Scene artifacts out of Mettaext | WIRED (file, pull-only, no AP) | §1f |
| Scene artifacts out of vault_linker | WIRED, ungated | §1b |
| Which extractor is canonical | UNRESOLVED | §11.4 |
| Scene load into 8080 runtime | WIRED — PARTIAL GOVERNANCE | §1e, §9 |
| Commands into 8080 runtime | WIRED — PARTIAL GOVERNANCE | §2, §9 |
| Spatial truth packets (topologist→cartographer→mrlore) | WIRED code / hand-carried / partial | §5 |
| trixel32d surface request/response | fixture proven, transport unwired | §7a |
| trixel32d surface application | DOC-ONLY | §7a.1 |
| ap/0.1 rule registry (8090) | BROKEN | §9 |
| Authoritative ID minting | RESERVED | §11.4 |
| ZON4D temporal memory / history / replay | RESERVED | §11.5 |
| EngAInOS canonical promotion (candidate → canon) | RESERVED | §11.6 |

### 11.3 Authority admission
[rule: AGENTS.md "Client authority"; ENGAINOS_AUTHORITY_MAP.md] Clients and tools
never own state; shared world state changes only through governance.

[rule: HANDSHAKES §11, approved 2026-10-13] Integrators submit world-affecting
changes only through the verified admission routes, both
**WIRED — PARTIAL GOVERNANCE**  [verified 2026-10-13]:
- `POST 8080 /command` (and its legacy aliases)
- `POST 8080 /scene/load`

These check identity fields, REPLAY/FINALIZED and canon edit rights. With no AP rules
loaded and no scene finalized, acceptance means "not rejected". These routes permit
candidate or non-canonical operations; they do not establish authoritative
world-state commitment, they are not AP approval, and they are not canon.
[verified 2026-10-13]

Ungoverned mutation routes — **not valid integration paths**  [verified 2026-10-13]:
- `POST 8080 /world/sync` (also BROKEN, §1d), `/world/load_mirror` (bulk load)
- `POST 8080 /vault/link` (§1c)
- `POST 8080 /embodiment/apply`
- boot vault relink (`sim_runtime.py:177`, env-gated)
- the 8765 scene server (serves candidates; grants no approval)

### 11.4 Identity and semantics
- [verified 2026-10-13] No authoritative ID-minting service exists. Scene IDs are
  currently produced independently by chapterroom/pass3 (§1f) and by
  `vault_linker._stem_to_scene_id` (§1b).
- [rule: mettaextgen2 design; enforced by `tier3/mettaextgen2/lib/artifact_schema.py:101-102`]
  EngAInOS mints IDs; `runtime_stage_id` stays null until EngAInOS promotion.
- [rule: HANDSHAKES §11, approved 2026-10-13] Until minting exists (RESERVED), new
  systems use **namespaced provisional IDs** (`<system>:<local_id>`, e.g.
  `cartographer:layout_0042`) with recorded provenance. Provisional IDs carry no
  canonical authority and are never written into canon or FINALIZED state. How they
  map to minted IDs is part of the RESERVED promotion interface, not something a new
  system decides.
- [verified 2026-10-13] Two narrative→ZONJ extractors exist: Mettaext passroom
  (consumer: 8765 SceneLoader via stageroom) and vault_linker (consumer: 8080 runtime).
- **UNRESOLVED:** their long-term relationship. Both are preserved as-is. Neither is
  designated canonical, and neither is modified on this file's authority.
- [rule: HANDSHAKES §11, approved 2026-10-13] A new system that consumes scene
  semantics names which extractor's output it reads and records that dependency as
  non-canonical. Adding a further extractor requires an Impact Statement that
  addresses this section.

### 11.5 Time, history and ZON4D
- [verified 2026-10-13] ZON4D is **RESERVED**.
  `tier2/engionality/controlroom/zon4d_kernel.py` and `runtime_loop.py` are dormant:
  no live importer, and the AP step is stubbed (`runtime_loop.py:207-209`). The ZON4D
  spec files listed in LEGACY_TREE_OUTPUT.md are not in the repo. Pass 4's
  ".zon"/"ZON4D" output is flat per-scene ZON with a string `@when`.
- [rule: HANDSHAKES §11, approved 2026-10-13] A system's internal timeline is **not**
  world memory. Mechanimation frame timing, poses and interpolation, and
  Cartographer's local edit history, stay internal and need no ZON4D. ZON4D becomes
  relevant only when EngAIn must retain or reconstruct the **authoritative history**
  of a world-affecting action.
- [rule: HANDSHAKES §11, approved 2026-10-13] A system with that need declares it in
  its Impact Statement as a future compatibility requirement (status `unresolved`),
  emits plain timestamped events in its own format, and does not import the
  engionality kernel. Those timestamped events are a **temporary compatibility
  mechanism**, not a finalized ZON4D interchange standard.

### 11.6 Preserved isolations (intentional — do not "fix")
- [verified 2026-10-13] Mettaext writes to stageroom only and never pushes to the
  runtime (`METTAEXT_PUSHES_TO_STAGEROOM_ONLY`, `pipeline_runner.py:140`).
- [verified 2026-10-13] Stageroom artifacts are candidates, not canon (§1f).
  Promotion from candidate to canon is RESERVED.
- [verified 2026-10-13] mettaextgen2 is an isolated sidecar with no runtime coupling.
- [rule: §7, 2026-07-16] Trixel re-enters only through the single §7a handshake.
- [rule: AGENTS.md] Clients render and request; they never own state.

### 11.7 Referenced contracts (not duplicated here)
`docs/contracts/` (per-system authority folders, CARTOGRAPHER_METRIC_LAYOUT_v1,
MRLORE_NARRATIVE_CONCURRENCE_v1, TRIXEL32D_* ×3, SHARED_SESSION_CONTINUITY_v1,
PROVIDER_PRESENCE_REGISTRY_v1), `ENGAINOS_AUTHORITY_MAP.md`,
`docs/architecture/TIER2_PRODUCTION_MAP.md`, `stageroom/STAGEROOM_HANDOFF_RULE.md`.
These remain authoritative for intended responsibilities. Where they disagree with
Part I's verified behaviour, the gap is recorded in §11.9. Neither side is silently
rewritten.

### 11.8 Integration Impact Statement — template  [rule: HANDSHAKES §11, approved 2026-10-13]
Filed before a new system's EngAIn adapter is designed. Each category is
**required / optional / not applicable / unresolved**, with the Part I § it depends on.

| Category | Status | Depends on (§) | Integrate now or future? | Notes |
|---|---|---|---|---|
| Identity (IDs created/consumed; provisional namespace) | | | | |
| Semantics (ZW/ZON/ZONJ consumed/produced; which extractor) | | | | |
| Spatial (coordinate space, units, origin, placement) | | | | |
| Time / history (internal timeline vs authoritative history) | | | | |
| Authority (what becomes shared reality; which admission route) | | | | |
| Persistence (who saves what; conflict handling) | | | | |
| Runtime handoff (file seam / HTTP route / packet; push or pull) | | | | |

- Proposed system / outputs:
- Integrate now (WIRED / WIRED — PARTIAL GOVERNANCE dependencies only):
- Future compatibility declared (RESERVED / DOC-ONLY / UNRESOLVED):
- Explicitly excluded (EngAIn internals it will not import):
- Adapter location:
- Contract tests required:
- Open questions:

A `required` row that points at a non-WIRED interface must be restated as either
"future compatibility" or "request to build that interface". It is never a silent
dependency.

### 11.9 Discrepancy register (intended design vs verified behaviour)  [verified 2026-10-13]
Records gaps between the two precedence axes; it changes neither side.

| Intended (source) | Verified now | Status |
|---|---|---|
| EngAInOS mints IDs (mettaextgen2 design) | No minting service; two independent ID producers | open |
| Engionality ZON4D loop enforces AP accept/reject (`TIER2_PRODUCTION_MAP.md:129-141`, `handshakes/THE_SYSTEM_TO_ENGAINOS_COMPILATION_HANDSHAKE.md:49`) | Loop dormant; AP step stubbed | open |
| AP governs world mutation (AGENTS.md, ENGAINOS_AUTHORITY_MAP.md) | Partial on 2 routes; 5 ungoverned mutation paths (§11.3) | open |
| ap/0.1 runtime_mutation registry | Registry directory absent in repo | open |
| `AUTHORITY_TIER_SPEC_v1.md`, `empire_agent_gateway.py`, `runtime_api.py` listed in AGENTS.md | Not in repo | open |
| launch_engine core-law files under `godotengain/engainos/core/` (AGENTS.md) | Checks `tier1/engainos/bridgeroom/*`; `godotengain/` absent | open |
| Single narrative source for runtime scenes (implied by pipeline docs) | Two extractors, different consumers | UNRESOLVED (§11.4) |
