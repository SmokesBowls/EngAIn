# TRIXEL COMPOSER ABI v1

Status: Draft contract, editor/composer convergence target
Scope: Trixel composer/editor cognition loop, AI bridge boundary, replay/session artifacts
Parent embodiment contract: `docs/trixel/contracts/TRIXEL_EMBODIMENT_CONTRACT_v1.md`
Related classification contract: `docs/TRIXEL_EDITOR_OUTPUT_CLASSIFICATION_v1.md` if present
Repository root: `/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn`

---

## 1. Purpose

This document freezes the shared operational interface for Trixel composer/editor systems before further editor, AI bridge, PixiEditor, or renderer integration.

The goal is one cognition loop across many hosts:

```text
perceive()
→ plan()
→ act(plan)
→ persist()
```

Instead of many incompatible editor brains:

```text
TerminalTrixelComposer semantics
EnhancedTrixelComposer semantics
EmpireBridge hidden assumptions
PixiEditor future semantics
Godot preview semantics
```

This ABI does not make editors authoritative. It standardizes how editor/composer systems expose their non-authoritative creative state, actions, persistence, and bridge boundaries.

## 2. Current motivating implementations

Observed current systems that this ABI is meant to normalize:

| Path | Current state | ABI issue |
|---|---|---|
| `trixelcomposer/terminal_trixel.py` | Has `TerminalTrixelComposer`, `perceive()`, `plan_action()`, `execute_action()`, `save_session()`, snapshots, replay, memory | Almost satisfies loop but method names and artifact envelopes are not contract-stable. |
| `trixelcomposer/enhanced_trixel_core.py` | Has `EnhancedTrixelComposer`, `perceive()`, internal `_autonomous_plan()`, `_execute_action()`, autonomous session save | Almost satisfies loop but uses private plan/act names and non-envelope sessions. |
| `trixelcomposer/empire_bridge.py` | Assumes composer exposes `perceive()`, `plan()`, `act(plan)`, `tool`, `canvas`, and memory | Uses hidden ABI, executes AI suggestions directly, and uses `action` where canonical editor actions use `tool`. |

This contract is documentation-first. It does not require immediate code mutation. Future code changes should converge on this ABI without deleting or renaming historical editor systems unless explicitly approved.

## 3. Non-goals

This ABI does not:

- define runtime world authority;
- define canonical narrative state;
- define AP governance;
- replace `TRIXEL_EMBODIMENT_CONTRACT_v1.md`;
- make editor canvas state equivalent to `EngAInRuntime.snapshot`;
- make AI suggestions accepted actions;
- make editor memory equivalent to ZON memory;
- define final art style;
- define terrain planner output;
- require immediate PixiEditor integration;
- require moving, deleting, or cleaning old composer/editor files.

## 4. Authority model

### 4.1 Composer/editor authority

A Trixel composer owns only its local editor surface:

- editor canvas;
- editor tool state;
- local creative memory;
- local replay log;
- local session files;
- preview/export artifacts;
- local non-authoritative plans and actions.

A composer must not own:

- runtime scene authority;
- Godot runtime state;
- AP approval or mutation authority;
- canonical ZON memory;
- canonical terrain grid;
- atlas policy;
- role policy;
- embodiment contract promotion.

### 4.2 Runtime/Godot/terrain authority remains external

Runtime, Godot, AP, terrain planner, atlas policy, and role policy may consume composer/editor artifacts only after explicit validation and promotion against the relevant contracts.

Composer/editor artifacts are always candidates until promoted.

```text
editor artifact ≠ runtime state
AI suggestion ≠ accepted edit
accepted editor edit ≠ runtime mutation
editor replay ≠ AP history
```

## 5. Required composer interface

Every ABI-compatible composer should expose these methods:

```python
perceive() -> dict
plan() -> dict
act(plan: dict) -> dict
persist() -> None
```

The methods may be synchronous or asynchronous only if the host declares that in its adapter metadata. The canonical ABI is synchronous at the method-shape level; async hosts must provide an adapter or document async use explicitly.

### 5.1 `perceive() -> dict`

`perceive()` returns a non-authoritative editor perception envelope.

Required top-level fields:

```json
{
  "schema_version": "trixel_composer_perception.v1",
  "authority_level": "editor_only",
  "authoritative": false,
  "artifact_kind": "editor_perception",
  "source": "terminal_trixel|enhanced_trixel_core|empire_bridge|pixieditor|unknown",
  "composer_id": "string",
  "session_id": "string",
  "base_contract_version": "trixel_embodiment.v1|null",
  "base_scene_id": "scene-id-or-null",
  "base_contract_digest": "sha256:...|null",
  "deterministic_seed": 12345,
  "status": "recorded|non_deterministic",
  "canvas_snapshot": {},
  "tool_state": {},
  "memory_context": {},
  "analysis": {}
}
```

Rules:

- `canvas_snapshot` must be an editor canvas snapshot, not `EngAInRuntime.snapshot`.
- `memory_context` must be editor memory only.
- `analysis` may contain creative/composition analysis but must not be terrain planner authority.
- If the perception is not reproducible because no seed exists, use `deterministic_seed: null` and `status: non_deterministic`.

### 5.2 `plan() -> dict`

`plan()` returns a proposed editor action envelope. It must not mutate canvas state.

Required shape:

```json
{
  "schema_version": "trixel_composer_plan.v1",
  "authority_level": "editor_only",
  "authoritative": false,
  "artifact_kind": "editor_action_plan",
  "source": "terminal_trixel|enhanced_trixel_core|empire_bridge|pixieditor|ollama|human|replay|unknown",
  "composer_id": "string",
  "session_id": "string",
  "base_contract_version": "trixel_embodiment.v1|null",
  "base_scene_id": "scene-id-or-null",
  "base_contract_digest": "sha256:...|null",
  "deterministic_seed": 12345,
  "status": "proposed",
  "action": {
    "schema_version": "trixel_editor_action.v1",
    "authority_level": "editor_only",
    "authoritative": false,
    "artifact_kind": "editor_action",
    "source": "terminal_trixel|enhanced_trixel_core|empire_bridge|pixieditor|ollama|human|replay|unknown",
    "status": "proposed",
    "tool": "brush",
    "x": 0,
    "y": 0,
    "color": [255, 255, 255],
    "pressure": 1.0,
    "reasoning": "why this action was proposed"
  }
}
```

Rules:

- Use `tool`, not bridge-local `action`, for tool identity.
- `plan()` returns `status: proposed`.
- `plan()` must not write session files, replay logs, runtime state, Godot state, or terrain state.
- `plan()` may consult editor memory if that memory is classified `editor_only`.
- AI-generated plans must remain proposals until validated/accepted by the host/editor policy.

### 5.3 `act(plan: dict) -> dict`

`act(plan)` applies a validated or accepted editor plan to the local editor canvas only.

Required input:

- a `trixel_composer_plan.v1` envelope; or
- a legacy plan normalized by an adapter into a `trixel_composer_plan.v1` envelope.

Required output:

```json
{
  "schema_version": "trixel_composer_act_result.v1",
  "authority_level": "editor_only",
  "authoritative": false,
  "artifact_kind": "editor_action_result",
  "source": "terminal_trixel|enhanced_trixel_core|empire_bridge|pixieditor|replay|unknown",
  "composer_id": "string",
  "session_id": "string",
  "base_contract_version": "trixel_embodiment.v1|null",
  "base_scene_id": "scene-id-or-null",
  "base_contract_digest": "sha256:...|null",
  "deterministic_seed": 12345,
  "status": "applied|rejected",
  "input_plan_digest": "sha256:...|null",
  "applied_action": {},
  "canvas_snapshot_after": {},
  "quality": null,
  "errors": []
}
```

Rules:

- `act()` may mutate only the composer/editor canvas and editor-local memory/replay artifacts.
- `act()` must not mutate runtime, Godot, AP, terrain planner, atlas policy, or role policy state.
- `act()` must return `rejected` if the plan cannot be normalized, validated, or applied safely.
- `act()` must record enough information for editor replay if the host supports replay.
- `act()` does not promote editor output into embodiment authority.

### 5.4 `persist() -> None`

`persist()` writes editor-owned artifacts only.

Allowed outputs:

- `.zw/memory.json` as classified editor memory;
- `.zw/snapshots.json` as classified editor canvas snapshots;
- `.zw/experience_log.jsonl` as classified editor replay events;
- `.zw/sessions/*.json` as classified editor sessions;
- preview images or draft exports marked non-authoritative.

Required behavior:

- preserve editor classification fields;
- preserve `authority_level: editor_only`;
- preserve `authoritative: false`;
- include `base_contract_version`, `base_scene_id`, and `base_contract_digest`, even when null;
- include `deterministic_seed`, or explicitly use `status: non_deterministic`;
- never write runtime/Godot/AP/terrain/atlas/role files directly.

`persist()` may call `save_session()` internally, but the public ABI uses `persist()` as the stable host-facing method.

## 6. Optional composer interface

These methods are optional but should use these names if present:

```python
load_session(path: str | None = None) -> dict
save_session(path: str | None = None) -> dict
attach_bridge(bridge: object) -> dict
attach_renderer(renderer: object) -> dict
```

### 6.1 `load_session()`

Loads editor session artifacts only.

Rules:

- Must reject sessions that do not declare `authority_level: editor_only` unless a legacy adapter explicitly wraps them.
- Must not load a session as runtime state.
- Must not infer terrain grid authority from editor canvas pixels.

### 6.2 `save_session()`

Saves a classified editor session and returns a result envelope.

Rules:

- Must include session classification fields.
- Must include references or digests for replay logs and AI suggestions where applicable.
- Must not overwrite canonical docs or generated runtime files.

### 6.3 `attach_bridge()`

Attaches an AI/human/tool bridge to the composer.

Rules:

- The bridge may request perception and propose plans.
- The bridge may not bypass `plan()`/proposal lifecycle by mutating canvas directly unless explicitly operating inside a legacy adapter.
- Bridge output must be normalized into `trixel_composer_plan.v1` before `act()`.

### 6.4 `attach_renderer()`

Attaches preview rendering only.

Rules:

- Renderer attachment is editor preview unless separately promoted through the embodiment contract.
- Preview renderers must not become Godot runtime authority.
- Preview exports must be classified as editor artifacts.

## 7. Editor artifact envelope

Every composer output that leaves process memory should include or be wrapped by:

```json
{
  "schema_version": "trixel_composer_artifact.v1",
  "authority_level": "editor_only",
  "authoritative": false,
  "artifact_kind": "editor_memory|editor_canvas_snapshot|editor_replay_event|editor_session|ai_bridge_payload|ai_suggestion|editor_action|editor_action_plan|editor_action_result|editor_perception",
  "source": "terminal_trixel|enhanced_trixel_core|empire_bridge|pixieditor|ollama|human|replay|unknown",
  "composer_id": "string",
  "session_id": "string",
  "base_contract_version": "trixel_embodiment.v1|null",
  "base_scene_id": "scene-id-or-null",
  "base_contract_digest": "sha256:...|null",
  "deterministic_seed": 12345,
  "status": "draft|proposed|validated|accepted|rejected|applied|recorded|non_deterministic"
}
```

Consumers connected to runtime embodiment must reject composer artifacts whose authority remains:

```json
{
  "authority_level": "editor_only",
  "authoritative": false
}
```

unless consuming them only as preview/debug/validation input.

## 8. Proposal lifecycle

The canonical lifecycle is:

```text
raw input
→ normalized proposal
→ validated proposal
→ accepted or rejected proposal
→ applied editor action
→ replay event
→ persisted editor session
→ optional promotion validation
→ contract-compatible embodiment input/output
```

Allowed status transitions:

```text
draft → proposed
proposed → validated
validated → accepted
validated → rejected
accepted → applied
applied → recorded
recorded → validated_for_promotion
```

Forbidden shortcuts:

```text
AI response → composer.act(...)
AI response → runtime mutation
editor canvas → terrain_grid authority
editor replay → AP history
editor session → Godot runtime state
```

Legacy systems may still contain shortcuts, but adapters must identify them as legacy behavior and prevent their outputs from being consumed as authority.

## 9. AI bridge boundary

AI bridges are proposal sources, not authorities.

An AI bridge may:

- request `perceive()`;
- send editor-only perception to an AI service;
- receive raw AI output;
- preserve raw AI output or digest;
- normalize output into `trixel_composer_plan.v1`;
- return a proposed plan;
- record accepted/rejected/applied status after the editor host decides.

An AI bridge must not:

- directly mutate runtime embodiment;
- directly mutate Godot state;
- directly mutate AP state;
- directly mutate terrain planner, atlas policy, or role policy;
- treat raw AI output as accepted;
- use `action` as the canonical tool identity field;
- bypass proposal validation before editor application.

Required AI suggestion shape:

```json
{
  "schema_version": "trixel_ai_suggestion.v1",
  "authority_level": "editor_only",
  "authoritative": false,
  "artifact_kind": "ai_suggestion",
  "source": "empire_bridge|ollama|human_proxy|unknown",
  "composer_id": "string",
  "session_id": "string",
  "base_contract_version": "trixel_embodiment.v1|null",
  "base_scene_id": "scene-id-or-null",
  "base_contract_digest": "sha256:...|null",
  "deterministic_seed": 12345,
  "status": "proposed",
  "raw_response_digest": "sha256:...|null",
  "plan": {
    "schema_version": "trixel_composer_plan.v1",
    "status": "proposed",
    "action": {
      "schema_version": "trixel_editor_action.v1",
      "tool": "brush",
      "x": 0,
      "y": 0,
      "color": [255, 255, 255],
      "pressure": 1.0,
      "reasoning": "AI suggestion"
    }
  }
}
```

## 10. Replay semantics

Editor replay is local editor replay only.

Replay may reconstruct:

- editor canvas state;
- action history;
- local creative memory effects if deterministic;
- preview artifacts.

Replay must not reconstruct or imply:

- runtime scene state;
- AP history;
- canonical terrain grid;
- Godot runtime state;
- atlas policy;
- role policy.

Required replay event shape:

```json
{
  "schema_version": "trixel_composer_replay_event.v1",
  "authority_level": "editor_only",
  "authoritative": false,
  "artifact_kind": "editor_replay_event",
  "source": "terminal_trixel|enhanced_trixel_core|empire_bridge|pixieditor|replay|unknown",
  "composer_id": "string",
  "session_id": "string",
  "event_index": 0,
  "base_contract_version": "trixel_embodiment.v1|null",
  "base_scene_id": "scene-id-or-null",
  "base_contract_digest": "sha256:...|null",
  "deterministic_seed": 12345,
  "status": "recorded|non_deterministic",
  "input_plan_digest": "sha256:...|null",
  "act_result_digest": "sha256:...|null",
  "event": {}
}
```

Replay logs must preserve order. Deterministic replay must not depend on wall-clock time, unrecorded randomness, hidden AI calls, or host UI timing.

## 11. Deterministic seed policy

Every composer session should declare one of:

```json
{
  "deterministic_seed": 12345,
  "status": "recorded"
}
```

or:

```json
{
  "deterministic_seed": null,
  "status": "non_deterministic"
}
```

Rules:

- Unseeded randomness is allowed only for editor-only creative exploration.
- Deterministic proof, replay, or promotion requires a seed or complete event record.
- Wall-clock timestamps may be metadata only.
- Session IDs may include time for legacy readability, but deterministic output must not depend on them.
- External AI calls make a session non-deterministic unless raw responses are recorded or digest-linked with exact replay substitutes.

## 12. Session persistence ownership

Composer sessions belong to the editor/composer surface.

Allowed path class:

```text
.zw/sessions/*.json
```

Required session envelope:

```json
{
  "schema_version": "trixel_composer_session.v1",
  "authority_level": "editor_only",
  "authoritative": false,
  "artifact_kind": "editor_session",
  "source": "terminal_trixel|enhanced_trixel_core|empire_bridge|pixieditor|unknown",
  "composer_id": "string",
  "session_id": "string",
  "base_contract_version": "trixel_embodiment.v1|null",
  "base_scene_id": "scene-id-or-null",
  "base_contract_digest": "sha256:...|null",
  "deterministic_seed": 12345,
  "status": "recorded|non_deterministic",
  "canvas_final": {},
  "memory_summary": {},
  "replay_log_ref": null,
  "ai_suggestions": [],
  "exports": []
}
```

Session files must not be imported by runtime/Godot/AP/terrain/atlas/role systems as authority. They may be used only as preview, debug, validation input, or candidate source material for explicit promotion.

## 13. Legacy adapter mapping

Current systems can be mapped without immediate code deletion.

### 13.1 `TerminalTrixelComposer`

Suggested adapter mapping:

| ABI method | Current equivalent |
|---|---|
| `perceive()` | `perceive()` |
| `plan()` | `plan_action(perception)` with perception supplied internally |
| `act(plan)` | `execute_action(CreativeAction(...))` |
| `persist()` | `save_session()` plus memory/snapshot/experience persistence |

Required future normalization:

- wrap `CreativeAction` as `trixel_editor_action.v1`;
- wrap snapshots as `editor_canvas_snapshot`;
- wrap experience log entries as replay events;
- declare deterministic seed or non-deterministic status;
- keep `.zw/memory.json` editor-only.

### 13.2 `EnhancedTrixelComposer`

Suggested adapter mapping:

| ABI method | Current equivalent |
|---|---|
| `perceive()` | `perceive()` |
| `plan()` | `_autonomous_plan(perception)` exposed through adapter |
| `act(plan)` | `_execute_action(CreativeAction(...))` exposed through adapter |
| `persist()` | `_save_autonomous_session()` exposed through adapter |

Required future normalization:

- convert private plan/act methods into public ABI or adapter methods;
- wrap autonomous session artifacts;
- declare seed/non-determinism;
- classify memory as editor-only;
- ensure GUI canvas state is never interpreted as embodiment authority.

### 13.3 `EmpireBridge`

Suggested adapter mapping:

| ABI role | Current equivalent |
|---|---|
| bridge perception source | `composer.perceive()` |
| AI request | `request_ai_guidance(canvas_state)` |
| AI normalization | `parse_ai_suggestion()` |
| local fallback plan | `composer.plan()` |
| application | currently `composer.act(...)`, but should be host-mediated |

Required future normalization:

- return `tool`, not `action`, inside editor actions;
- preserve raw AI output or digest;
- return proposed plans instead of executing suggestions directly;
- allow host/editor policy to validate, accept/reject, and then call `act()`;
- classify bridge memory as editor-only.

## 14. Promotion rule

Composer/editor artifacts must be explicitly validated against:

```text
docs/trixel/contracts/TRIXEL_COMPOSER_ABI_v1.md
docs/trixel/contracts/TRIXEL_EMBODIMENT_CONTRACT_v1.md
```

and, if present:

```text
docs/TRIXEL_EDITOR_OUTPUT_CLASSIFICATION_v1.md
```

before being consumed by:

- runtime;
- Godot;
- AP;
- terrain planner;
- atlas policy;
- role policy;
- canonical scene state;
- ZON memory;
- runtime snapshot systems;
- production embodiment pipelines.

Promotion must create a new validated artifact or contract-compatible input. It must not mutate the original editor artifact into authority.

## 15. Minimal conformance checklist

A composer is ABI-compatible when:

- [ ] it exposes `perceive() -> dict`;
- [ ] it exposes `plan() -> dict`;
- [ ] it exposes `act(plan: dict) -> dict`;
- [ ] it exposes `persist() -> None`;
- [ ] every output declares `authority_level: editor_only`;
- [ ] every output declares `authoritative: false`;
- [ ] every action uses `tool` for tool identity;
- [ ] plans are proposed before applied;
- [ ] AI suggestions are not directly accepted;
- [ ] editor memory is not runtime/ZON memory;
- [ ] editor snapshots are not `EngAInRuntime.snapshot`;
- [ ] replay is editor replay only;
- [ ] deterministic seed or non-deterministic status is explicit;
- [ ] session persistence stays in editor-owned paths;
- [ ] runtime/Godot/AP/terrain/atlas/role consumption requires explicit promotion validation.

## 16. Final boundary

This ABI creates a shared composer/editor interface. It does not grant authority.

The desired long-term shape is:

```text
many hosts
one composer ABI
many bridges/renderers
one proposal lifecycle
zero accidental runtime authority
```

Any editor, bridge, or renderer that bypasses this boundary must be classified as legacy/fallback until adapted.
