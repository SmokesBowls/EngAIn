# RUNTIME STATE AUTHORITY CONTRACT v1

Status: DRAFT CONTRACT
Scope: EngAIn live simulation runtime state, source preservation, normalized scene state, client projections, mutation requests, AP/governance interaction, and runtime-load boundaries
Repository root: `/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn`

---

## 1. Purpose

This contract freezes the runtime as EngAIn's live simulation Single Source of Truth before generated files, Godot output, Trae edits, Dragon orchestration, AP mutation paths, or other automation scale further.

Runtime authority must be explicit because many EngAIn subsystems can now produce convincing artifacts:

- MrLore can produce continuity reports and proposals;
- Trixel can produce embodiment/editor candidates;
- Trae can generate and edit files;
- Godot can render loaded projections;
- Dragon can orchestrate conversational workflows;
- AP can govern mutation legality;
- scene pipelines can produce generated ZONJ/game artifacts.

None of those artifacts become live simulation truth merely by existing.

Core runtime law:

```text
EngAInRuntime.snapshot is the live simulation Single Source of Truth.
```

---

## 2. Upstream authority

This contract is subordinate to:

- `AGENTS.md` repository preservation rules;
- `godotengain/engainos/docs/architecture/AUTHORITY_TIER_SPEC_v1.md`;
- `docs/trae/contracts/TRAE_OPERATOR_AUTHORITY_CONTRACT_v1.md`;
- `docs/trixel/contracts/TRIXEL_EMBODIMENT_CONTRACT_v1.md`;
- `docs/trixel/contracts/TRIXEL_COMPOSER_ABI_v1.md`;
- `docs/mrlore/contracts/MRLORE_AUTHORITY_CONTRACT_v1.md`;
- `system.manifest.md` runtime SSOT doctrine;
- runtime implementation surfaces under `godotsim/`.

If this contract conflicts with the frozen AP authority tier spec, the AP authority tier spec wins.

---

## 3. Architectural classification

Runtime is:

```text
Runtime = live simulation authority
```

Runtime owns accepted live state for the running simulation.

Runtime is not:

- the sole canon authority;
- a replacement for AP mutation governance;
- a replacement for human/root promotion approval;
- a renderer;
- an editor canvas;
- a continuity-audit system;
- a generated-artifact validator by itself;
- a replay/provenance archive by itself.

Runtime load and runtime state are powerful, but they do not automatically equal canon promotion.

---

## 4. Non-negotiable boundary law

Required distinctions:

```text
client request != runtime truth
runtime load != canon
snapshot != replay
scene_raw != normalized scene
rendered output != truth
accepted delta != promoted canon
Godot node state != authoritative world state
```

Additional distinctions:

```text
MrLore proposal != runtime state
Trixel embodiment != runtime truth
Trae generated file != loaded runtime state
Dragon orchestration != approval
AP permission != renderer proof
runtime snapshot != canonical history
```

Runtime may accept and expose live simulation state. It must not silently convert live state into canon history without the appropriate AP/human/root promotion path.

---

## 5. Runtime-owned state

Runtime-owned live state includes the accepted state currently held by `EngAInRuntime.snapshot`.

Known runtime-owned fields include, where present:

| Field | Authority meaning |
|---|---|
| `snapshot` | Live simulation SSOT for the running runtime process. |
| `snapshot["entities"]` | Runtime entity dictionary keyed by entity ID. |
| `snapshot["scene"]` | Normalized runtime scene view. |
| `snapshot["scene_raw"]` | Preserved original source payload. |
| runtime combat state | Accepted live combat state and deltas. |
| runtime inventory state | Accepted live inventory state and deltas. |
| runtime dialogue state | Accepted live dialogue state and deltas. |
| runtime spatial/perception/behavior state | Accepted live MR-kernel/adapted simulation state. |
| active scene ID / registry references | Runtime selection and lookup state, not by itself canon promotion. |

Rules:

1. `EngAInRuntime.snapshot` is the live simulation SSOT.
2. Runtime/adapters apply accepted deltas to runtime-owned state.
3. Clients may observe or request changes; they do not own runtime state.
4. Generated files may be loaded into runtime only through declared runtime load paths.
5. Runtime state may be canonical input/evidence, but is not automatically canonical history.

---

## 6. Source-preservation state

`snapshot["scene_raw"]` preserves the original source payload used to load or construct the active scene.

Rules:

1. `scene_raw` is source-preservation state.
2. `scene_raw` must not be confused with the normalized runtime view.
3. `scene_raw` should preserve the original ZONJ/source structure as faithfully as the loader permits.
4. Runtime may retain `scene_raw` for audit, reload, comparison, and provenance.
5. Mutation of normalized runtime state must not silently rewrite preserved source payload.

Core law:

```text
scene_raw != normalized scene
```

---

## 7. Normalized runtime state

`snapshot["scene"]` is the normalized runtime view used by look/examine/status pipelines and runtime scene interaction.

Rules:

1. `scene` is optimized for runtime use, not source preservation.
2. `scene` may be derived from `scene_raw` or another accepted load input.
3. `scene` may normalize, index, simplify, or adapt source payload into runtime shape.
4. Consumers must not assume `scene` is byte-for-byte source truth.
5. Consumers must not assume `scene_raw` is directly runtime-ready.

Runtime should preserve the distinction:

```text
source payload -> scene_raw
runtime-normalized view -> scene
```

---

## 8. Render and client projections

Render/client projections are not runtime authority.

Projection examples include:

- Godot nodes;
- Godot scenes/resources generated from runtime data;
- Trixel terrain/embodiment outputs;
- bridge entities prepared for Godot;
- editor canvases;
- previews/screenshots;
- Trixel/PixiEditor-style visual artifacts;
- Dragon UI summaries of runtime state.

Rules:

1. Godot renders projections; Godot node state is not canon.
2. Godot node state is not authoritative world state.
3. Trixel outputs embodiment/projection candidates, not runtime truth.
4. Rendered output is visual/load evidence, not truth.
5. A client may request mutation through runtime/AP paths; it must not directly own accepted state.
6. Client-side divergence must be reconciled against runtime snapshot, not the other way around.

Core law:

```text
rendered output != truth
Godot node state != authoritative world state
```

---

## 9. External subsystem boundaries

### 9.1 MrLore boundary

MrLore proposals, continuity reports, promotion eligibility reports, and review artifacts are continuity evidence.

They are not runtime state.

```text
MrLore proposal != runtime state
continuity-safe != mutation-authorized
```

### 9.2 Trixel boundary

Trixel embodies approved semantic/runtime state and may produce editor/embodiment candidates.

Trixel output is not runtime truth until accepted by runtime through a declared load/mutation path.

```text
Trixel embodiment != runtime truth
```

### 9.3 Trae boundary

Trae generated files are candidates until validated, loaded, and promoted where promotion is required.

Trae may generate runtime-loadable files only from approved task specs.

```text
Trae generated file != loaded runtime state
```

### 9.4 Godot boundary

Godot is a client/renderer.

Godot may render snapshots and submit requests. Godot must not become authoritative state owner.

```text
Godot node state != authoritative world state
```

### 9.5 Dragon boundary

Dragon is an orchestration interface.

Dragon may help route requests, explain state, draft task specs, and present approval choices. Dragon must not hide mutation, promotion, or runtime-load transitions behind conversational convenience.

```text
Dragon orchestration != approval
```

---

## 10. Mutation request boundaries

Clients submit requests, not truth.

Mutation requests may originate from:

- HTTP clients;
- Godot;
- Dragon;
- Trae-generated task execution;
- internal systems;
- CLI/debug tools;
- AP runtime integration;
- test harnesses.

Rules:

1. A request is not accepted state.
2. A request must be normalized through the runtime command/load boundary.
3. A request that implies mutation must be eligible under AP/governance rules where applicable.
4. Runtime may reject malformed, unauthorized, unsafe, or governance-invalid requests.
5. Rejected requests must not mutate runtime state.
6. Accepted requests may still produce queued deltas rather than immediate state mutation.
7. URL paths are transport metadata; gameplay meaning must come from normalized command/action/text/payload fields.

Core law:

```text
client request != runtime truth
```

---

## 11. Delta acceptance rules

A delta is not live state until accepted and applied by runtime or a runtime-authorized adapter.

Rules:

1. MR kernels should operate on slices/snapshots and return deltas/outputs.
2. Kernels should not directly mutate global runtime state in place.
3. Runtime/adapters decide whether and how accepted deltas apply to `EngAInRuntime.snapshot`.
4. AP/governance may veto mutation before application.
5. Accepted deltas update live runtime state, not necessarily canon history.
6. Accepted deltas must preserve source/runtime distinctions where relevant.
7. Failed or rejected deltas must not be silently applied.

Core law:

```text
accepted delta != promoted canon
```

---

## 12. Endpoint classification expectations

Runtime endpoints must be classifiable by authority effect.

Expected endpoint classes:

| Class | Meaning | Examples |
|---|---|---|
| read/query | Observes runtime state without mutation. | `GET /health`, `GET /snapshot`, text `status`, text `look` when read-only. |
| load | Loads source/generated artifacts into runtime state. | `POST /scene/load`, `POST /world/load_mirror`. |
| sync/link | Connects or synchronizes external source/vault state. | `POST /world/sync`, `POST /vault/link`. |
| mutation/action | Changes simulation state or queues changes. | `POST /command`, combat/inventory/dialogue mutation endpoints. |
| projection | Builds or exposes render/client projections. | bridge/Godot-facing snapshot data, render plans. |

Expectations:

1. Read/query endpoints must not mutate live state except for harmless diagnostics/caches explicitly documented.
2. Load endpoints must distinguish loading into runtime from canon promotion.
3. Sync/link endpoints must record provenance and avoid silent canon mutation.
4. Mutation/action endpoints must pass through runtime normalization and AP/governance when applicable.
5. Projection endpoints must not become state owners.
6. Endpoint behavior must be testable against these classes.

---

## 13. AP and governance interaction

AP/governance may veto mutations.

Rules:

1. A tier is necessary but not sufficient for mutation.
2. `REPLAY` blocks mutation.
3. `FINALIZED` requires Tier 3/root authority.
4. AI/operator requests must not self-escalate.
5. Runtime must not treat client intent as authority.
6. Runtime should fail closed when governance context is missing for a mutation that requires it.
7. Rejected mutation attempts should be routed to the appropriate rejection/Intent Shadow path where that subsystem is active.
8. AP permission allows a mutation path to proceed; it does not by itself prove renderer output, continuity approval, or canon promotion.

Core law:

```text
AP/governance may veto runtime mutation.
```

---

## 14. Reality mode behavior

Runtime behavior must respect reality modes defined by the frozen authority tier spec.

### 14.1 DRAFT

DRAFT runtime state may be mutable and non-canonical.

Rules:

- mutation may proceed subject to runtime safety and applicable AP checks;
- outputs remain non-canonical unless promoted;
- generated/load artifacts should remain candidate or draft unless explicitly approved.

### 14.2 IMBUED

IMBUED runtime state is mutable but AP-enforced.

Rules:

- AP/governance applies;
- accepted runtime state is not automatically canonical history;
- continuity/render/provenance artifacts remain evidence unless promoted.

### 14.3 FINALIZED

FINALIZED state is restricted and canonical.

Rules:

- Tier 3/root authority is required for mutation;
- AI/operator/client mutation attempts must fail closed;
- Trae, Dragon, Godot, Trixel, and MrLore must not mutate FINALIZED state on their own.

### 14.4 DREAM

DREAM state is sandbox/non-canonical.

Rules:

- DREAM mutations must remain discardable and non-canonical;
- DREAM outputs may inform proposals, tests, previews, or learning;
- DREAM output must not silently enter live canonical/runtime state.

### 14.5 REPLAY

REPLAY is read-only.

Rules:

- no mutation;
- no shadow-to-canon leakage;
- no generated artifact promotion;
- no runtime state mutation;
- replay evidence may be inspected but not applied without a separate non-replay mutation request.

Core law:

```text
snapshot != replay
```

---

## 15. Runtime load and canon promotion

Runtime load means an artifact has been accepted into live runtime state.

Runtime load does not mean the artifact is canon.

Rules:

1. Loading a scene into runtime may populate `snapshot`.
2. Loading a generated artifact may prove runtime compatibility.
3. Loading may be a validation step in a promotion pipeline.
4. Loading must not silently promote source/canon/world history.
5. Canon promotion requires explicit promotion authority outside ordinary runtime load.
6. Runtime state may diverge from canonical history in DRAFT, IMBUED, DREAM, debug, or test contexts.

Core law:

```text
runtime load != canon
```

---

## 16. Runtime snapshot and canonical history

`EngAInRuntime.snapshot` is live state.

It is not necessarily canonical history.

Rules:

1. Snapshot is authoritative for the running simulation's current accepted live state.
2. Snapshot may include draft/test/generated/loaded/sandbox state depending on reality mode and runtime context.
3. Snapshot may be used as evidence for promotion, debugging, rendering, or replay creation.
4. Snapshot must not be mistaken for an immutable canon ledger.
5. Canonical history requires explicit AP/human/root promotion or history rules.

Core law:

```text
runtime snapshot is live state, not necessarily canonical history
```

---

## 17. Provenance requirements

Runtime-affecting loads and mutations should record enough provenance to answer:

1. What request caused this?
2. Who or what requested it?
3. What authority tier/mode applied?
4. What source artifact was loaded or mutated?
5. What source hash or payload identity was used?
6. What normalized runtime state was produced?
7. What AP/governance decision applied?
8. What deltas were accepted or rejected?
9. What runtime endpoints were used?
10. What remains candidate vs canonical?
11. What validation/load checks passed?
12. What rejection path was used if blocked?

Minimum provenance for runtime-loadable artifacts:

- source path or payload ID;
- source hash when available;
- loader/generator identity;
- runtime endpoint/action used;
- timestamp or run ID;
- actor/requester identity when available;
- authority tier/mode when mutation-related;
- AP decision when applicable;
- loaded scene/entity IDs;
- validation result;
- canonicality status.

---

## 18. Failure and rejection behavior

Runtime authority must fail closed when state ownership is ambiguous.

Reject or block when:

- request payload is invalid;
- runtime cannot classify the endpoint/action;
- source artifact is malformed;
- mutation lacks required AP/governance context;
- actor tier/mode forbids mutation;
- generated artifact is not validated;
- client attempts to assert truth directly;
- Godot/client state conflicts with runtime snapshot;
- replay attempts mutation;
- FINALIZED mutation lacks Tier 3/root authority.

Rejected requests must not mutate runtime state.

---

## 19. Minimum audit checklist before trusting runtime state transitions

Before accepting a runtime-affecting transition as valid, verify:

1. Is this read/query, load, sync/link, mutation/action, or projection?
2. What exact endpoint/action/path was used?
3. What payload was provided?
4. Was the payload normalized by runtime/dispatcher logic?
5. Was AP/governance required?
6. If required, did AP/governance allow it?
7. What snapshot fields changed?
8. Did `scene_raw` preserve original payload?
9. Did `scene` contain normalized runtime view?
10. Were client/render projections kept non-authoritative?
11. Was runtime load separated from canon promotion?
12. Was provenance recorded?
13. Was rejection/failure non-mutating?

---

## 20. Red-line rules

1. Clients submit requests, not truth.
2. Godot node state must not become authoritative world state.
3. Rendered output must not become truth.
4. Trixel embodiment must not become runtime truth by rendering alone.
5. MrLore proposals must not become runtime state by review alone.
6. Trae generated files must not become runtime state without validation/load.
7. Runtime load must not become canon promotion.
8. Runtime snapshot must not be mistaken for replay.
9. Runtime snapshot must not be mistaken for canonical history.
10. `scene_raw` must not be confused with normalized `scene`.
11. Accepted deltas must not be treated as promoted canon.
12. AP/governance veto must be respected.

---

## 21. Versioning

This is `RUNTIME_STATE_AUTHORITY_CONTRACT_v1`.

Backward-incompatible changes require a v2 contract or explicit amendment section.

Implementation may add schemas, endpoint audits, validators, AP envelopes, CI smoke tests, or runtime wrappers under this contract, but must not weaken runtime SSOT or AP veto semantics without explicit review.

---

## 22. Final invariant

Runtime is the live simulation authority, not the whole canon system.

```text
EngAInRuntime.snapshot is live simulation SSOT.
snapshot["scene_raw"] preserves source payload.
snapshot["scene"] is normalized runtime view.
Clients request; runtime accepts or rejects.
AP/governance may veto mutation.
Rendered output is not truth.
Runtime load is not canon promotion.
Canon outranks convenience.
```
