# AP MUTATION GOVERNANCE CONTRACT v1

Status: DRAFT CONTRACT
Scope: Operational mutation envelope for EngAIn systems that request, apply, reject, record, or promote state changes
Repository root: `/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn`

---

## 1. Purpose

This contract defines the operational mutation envelope that all mutation-capable EngAIn systems must use when requesting, applying, rejecting, recording, or promoting state changes.

AP governs mutation permission. It does not author canon, render truth, write files, or replace runtime state ownership.

This contract exists because EngAIn now has multiple systems that can affect or appear to affect world state:

- Runtime owns accepted live simulation state.
- Trae can generate and edit files.
- Dragon can route and propose conversational actions.
- MrLore can provide continuity review and promotion evidence.
- Godot and Trixel can display, embody, and preview state.
- Generated pipelines can create scene/world artifacts.

Those systems must not blur mutation permission, runtime application, promotion, and canon acceptance.

Core AP law:

```text
AP governs mutation permission, not canon authorship.
```

---

## 2. Upstream authority

This contract is subordinate to:

- `AGENTS.md` repository preservation rules;
- `godotengain/engainos/docs/architecture/AUTHORITY_TIER_SPEC_v1.md`;
- `docs/runtime/contracts/RUNTIME_STATE_AUTHORITY_CONTRACT_v1.md`;
- `docs/trae/contracts/TRAE_OPERATOR_AUTHORITY_CONTRACT_v1.md`;
- `docs/mrlore/contracts/MRLORE_AUTHORITY_CONTRACT_v1.md`;
- `docs/trixel/contracts/TRIXEL_EMBODIMENT_CONTRACT_v1.md`;
- `docs/trixel/contracts/TRIXEL_COMPOSER_ABI_v1.md`.

The frozen authority tier spec is normative. If this document conflicts with it, the frozen authority tier spec wins.

---

## 3. Architectural classification

AP is:

```text
AP = mutation governance
```

AP decides whether a mutation is permitted under authority tier, reality mode, and applicable rules.

AP is not:

- canon author;
- runtime state owner;
- renderer;
- file-generation operator;
- continuity authority;
- conversational approval authority;
- promotion authority by itself.

AP permission allows a mutation path to proceed. It does not prove that the mutation was applied, promoted, rendered correctly, or canonized.

---

## 4. Non-negotiable boundary law

Required distinctions:

```text
allowed != applied
applied != promoted
promoted != canon unless canon gate approves
Tier 3 required for FINALIZED
REPLAY is read-only
DREAM is sandbox-first
AP veto blocks mutation
continuity review != mutation permission
generation != authority
```

Additional distinctions:

```text
request != permission
permission != runtime state
runtime load != canon promotion
Dragon routing != approval
Trae output != mutation authority
Godot/Trixel display != mutation authority
Intent Shadow != accepted state
```

---

## 5. Mutation governance doctrine

### 5.1 AP governs permission, not authorship

AP answers:

```text
May this mutation proceed under this actor, tier, mode, target, and rule context?
```

AP does not answer by itself:

```text
Is this canon?
Was this applied?
Was this promoted?
Is this rendered truth?
Is this continuity-approved?
```

### 5.2 Authority tier is necessary but not sufficient

Authority tier must be present on mutation requests, but tier alone does not authorize mutation.

A valid mutation decision may also require:

- reality mode;
- target artifact classification;
- AP rules;
- continuity review;
- runtime validation;
- source/generator provenance;
- human/root approval for promotion or finalized state.

### 5.3 Reality mode must be explicit

Every mutation request must declare `reality_mode`.

A mutation request without a reality mode must fail closed unless the caller is explicitly operating in a documented non-mutating read/query lane.

### 5.4 FINALIZED requires Tier 3/root approval

FINALIZED state is restricted and canonical.

Rules:

1. FINALIZED mutation requires `actor_authority_tier = 3` or explicit root authority.
2. Tier 1 AI/operator attempts must be rejected.
3. Tier 2 limited human/operator attempts must be rejected.
4. Rejections must be recorded as Intent Shadow or equivalent rejection evidence.
5. No subsystem may self-escalate to Tier 3.

Core law:

```text
Tier 3 required for FINALIZED
```

### 5.5 REPLAY blocks mutation

REPLAY is read-only.

Rules:

1. REPLAY mutation attempts must be rejected.
2. REPLAY must not write runtime state.
3. REPLAY must not write canon.
4. REPLAY must not promote generated artifacts.
5. REPLAY must not leak shadow/proposal/replay artifacts into accepted state.

Core law:

```text
REPLAY is read-only
```

### 5.6 DREAM is sandbox-first

DREAM mutations are symbolic, sandboxed, discardable, and non-canonical by default.

Rules:

1. DREAM output may inform proposals, tests, previews, or learning.
2. DREAM output must not silently enter live runtime state.
3. DREAM output must not silently enter canon.
4. DREAM output requires a separate promotion/mutation request to leave the sandbox.
5. DREAM promotion must cite provenance from the DREAM run.

Core law:

```text
DREAM is sandbox-first
```

---

## 6. Required mutation envelope

Every mutation-capable system must use or produce an equivalent mutation envelope before mutation is applied.

Required fields:

| Field | Required meaning |
|---|---|
| `request_id` | Stable unique ID for the mutation request. |
| `actor_id` | Actor, process, user, agent, or system requesting mutation. |
| `actor_authority_tier` | Immutable authority tier injected externally; must not be self-assigned. |
| `reality_mode` | Explicit mode: `DRAFT`, `IMBUED`, `FINALIZED`, `DREAM`, or `REPLAY`. |
| `source_system` | System originating the request: Dragon, Trae, Godot, Trixel, MrLore, runtime, CLI, test, etc. |
| `target_system` | System expected to evaluate/apply the mutation: runtime, AP, file system, canon store, Godot, etc. |
| `target_artifact` | Exact state/file/entity/scene/world artifact targeted. |
| `mutation_type` | Declared type: create, edit, delete, load, sync, spawn, move, damage, inventory, dialogue, promote, etc. |
| `requested_delta` | Structured proposed change. |
| `base_state_hash` | Hash/fingerprint of state the request was based on, if available. |
| `ap_rules_evaluated` | AP rules/specs/gates considered for the decision. |
| `decision` | `allowed`, `rejected`, `deferred`, `sandboxed`, or `requires_review`. |
| `decision_reason` | Human/audit-readable explanation of the decision. |
| `validator_results` | Validation outputs relevant to the request. |
| `applied_by` | Runtime/adapter/system that actually applied the accepted mutation, or `null`. |
| `promotion_status` | Candidate/review/applied/promoted/canon/rejected status. |
| `intent_shadow_ref` | Link/reference to rejection evidence when rejected. |
| `provenance_ref` | Link/reference to logs, trajectory, source, task spec, or audit record. |

Minimum valid mutation envelope shape:

```json
{
  "request_id": "...",
  "actor_id": "...",
  "actor_authority_tier": 1,
  "reality_mode": "DRAFT",
  "source_system": "Dragon|Trae|Godot|Trixel|MrLore|Runtime|CLI|Test|Other",
  "target_system": "Runtime|AP|Filesystem|CanonStore|Godot|Other",
  "target_artifact": "...",
  "mutation_type": "...",
  "requested_delta": {},
  "base_state_hash": "...",
  "ap_rules_evaluated": [],
  "decision": "allowed|rejected|deferred|sandboxed|requires_review",
  "decision_reason": "...",
  "validator_results": [],
  "applied_by": null,
  "promotion_status": "candidate|review|applied|promoted|canon|rejected|sandboxed",
  "intent_shadow_ref": null,
  "provenance_ref": "..."
}
```

---

## 7. Decision states

Allowed decision values:

| Decision | Meaning | Mutation effect |
|---|---|---|
| `allowed` | AP/governance permits the mutation path to proceed. | Not yet applied unless runtime/target applies it. |
| `rejected` | AP/governance blocks the mutation. | Must not mutate; record rejection evidence. |
| `deferred` | More information/review is required. | Must not mutate until resolved. |
| `sandboxed` | Allowed only in non-canonical sandbox context. | Must not become canon/live state without another gate. |
| `requires_review` | Mechanically plausible but requires human/root or domain authority review. | Must not mutate promoted/canon state. |

Core law:

```text
allowed != applied
```

---

## 8. Promotion states

Allowed `promotion_status` values:

| Status | Meaning |
|---|---|
| `candidate` | Proposed artifact/change; not accepted live state. |
| `review` | Under human/domain review; not canon. |
| `applied` | Applied to target live/draft/sandbox state; not necessarily promoted. |
| `promoted` | Promoted by a defined promotion gate; not necessarily canon unless canon gate says so. |
| `canon` | Accepted by canon/finality gate under required authority. |
| `rejected` | Blocked or discarded; must not mutate accepted state. |
| `sandboxed` | DREAM/test/sandbox state only. |

Core laws:

```text
applied != promoted
promoted != canon unless canon gate approves
```

---

## 9. Rejection and Intent Shadow

Rejected mutation attempts must be recorded.

Required rejection evidence:

- `request_id`;
- `actor_id`;
- `actor_authority_tier`;
- `reality_mode`;
- `source_system`;
- `target_system`;
- `target_artifact`;
- `mutation_type`;
- `requested_delta` summary;
- `decision = rejected`;
- `decision_reason`;
- AP rule/tier/mode that blocked the request;
- `intent_shadow_ref` or equivalent rejection record;
- `provenance_ref`.

Intent Shadow or equivalent evidence is required for:

- FINALIZED attempts by non-Tier-3 actors;
- REPLAY mutation attempts;
- AP rule vetoes;
- missing/invalid authority context;
- unauthorized direct client truth assertions;
- unauthorized promotion attempts.

A rejection record is evidence, not accepted state.

```text
Intent Shadow != accepted state
```

---

## 10. AP veto

AP veto blocks mutation.

Rules:

1. A vetoed mutation must not be applied.
2. A vetoed mutation must not be promoted.
3. A vetoed mutation must not be rendered as accepted truth.
4. A vetoed mutation may be recorded as rejected intent.
5. A vetoed mutation may be used as review evidence only if clearly labeled rejected.
6. No subsystem may bypass AP veto by writing directly to runtime state, generated files, Godot nodes, or canon stores.

Core law:

```text
AP veto blocks mutation
```

---

## 11. Runtime interaction

Runtime applies accepted live-state deltas.

Rules:

1. Runtime owns accepted live state through `EngAInRuntime.snapshot`.
2. AP may allow or veto mutation before runtime application.
3. `allowed` does not mean runtime already applied the delta.
4. Runtime/adapter application must populate `applied_by` or equivalent provenance.
5. Runtime application updates live state, not necessarily canon.
6. Runtime load is a live-state/load event, not canon promotion by itself.

```text
allowed != applied
applied != promoted
runtime load != canon promotion
```

---

## 12. Trae interaction

Trae may generate files but does not grant mutation authority.

Rules:

1. Trae output is candidate material unless validated and accepted.
2. Trae task approval is not AP mutation approval unless the task spec carries explicit authority context and AP accepts it.
3. Trae trajectory is evidence, not approval.
4. Trae `task_done` is completion evidence, not validation or promotion.
5. File generation does not authorize runtime mutation.

Core law:

```text
generation != authority
```

---

## 13. Dragon interaction

Dragon may route, propose, explain, and orchestrate mutation requests.

Dragon must not silently approve mutations.

Rules:

1. Dragon must preserve candidate/review/approval distinctions.
2. Dragon must surface authority tier and reality mode requirements for mutation.
3. Dragon must not convert conversational convenience into root approval.
4. Dragon must not hide AP veto, rejection, or sandbox status.
5. Dragon-originated mutation requests must carry a mutation envelope.

```text
Dragon routing != approval
```

---

## 14. MrLore interaction

MrLore may provide continuity review but cannot authorize runtime mutation.

Rules:

1. Continuity review may be validator evidence.
2. Continuity legality is not AP permission.
3. MrLore proposals are review artifacts, not runtime state.
4. MrLore promotion eligibility is not root/canon approval.
5. MrLore findings may be referenced in `validator_results` or `provenance_ref`.

Core law:

```text
continuity review != mutation permission
```

---

## 15. Godot and Trixel interaction

Godot and Trixel may display or embody accepted state but cannot authorize mutation.

Rules:

1. Godot is a client/renderer, not state authority.
2. Trixel is embodiment/editor candidate lane, not runtime authority.
3. Godot node state is not authoritative world state.
4. Trixel output is not runtime truth by rendering alone.
5. Rendered output may validate display/load behavior, but not mutation authority.
6. Godot/Trixel mutation requests must go through AP/runtime envelopes.

```text
rendered output != truth
Godot/Trixel display != mutation authority
```

---

## 16. Source system and target system expectations

Every mutation envelope must identify where the request came from and where it is meant to apply.

Common `source_system` values:

- `Dragon`
- `Trae`
- `MrLore`
- `Trixel`
- `Godot`
- `Runtime`
- `AP`
- `CLI`
- `Test`
- `Pipeline`
- `HumanOperator`

Common `target_system` values:

- `Runtime`
- `AP`
- `Filesystem`
- `CanonStore`
- `Godot`
- `Trixel`
- `MrLoreVault`
- `GeneratedArtifactStore`
- `IntentShadow`
- `History`

A source system must not claim the authority of the target system. The target system must still validate and apply according to its own contract.

---

## 17. Validator results

`validator_results` must distinguish evidence type.

Examples:

| Validator type | Evidence meaning | Not sufficient for |
|---|---|---|
| schema validation | Payload shape is acceptable. | Runtime application or canon. |
| continuity review | MrLore found no blocking contradiction. | Mutation permission. |
| file validation | Generated file parses/compiles. | Runtime load or promotion. |
| Godot load check | Godot can load/render artifact. | Runtime truth or canon. |
| runtime load check | Runtime accepted/load-compatible. | Canon promotion. |
| AP rule evaluation | Mutation is permitted or vetoed. | Authorship/canon by itself. |
| human review | Human reviewed artifact. | Tier 3/root unless explicitly recorded. |

Validator evidence must be recorded, but validators do not collapse the promotion ladder.

---

## 18. Base state hash and concurrency

`base_state_hash` records what state the mutation request assumed.

Rules:

1. If `base_state_hash` is present and does not match current target state, mutation should defer or require conflict handling.
2. Missing `base_state_hash` must be explicit in `decision_reason` for stateful mutation.
3. Runtime live state, canon history, generated artifact state, and client render state must not be assumed equivalent.
4. Concurrent generated or runtime mutation paths must not silently overwrite each other.

---

## 19. Promotion and canon gates

AP allows or vetoes mutation. Promotion and canon gates decide whether accepted/applied artifacts become promoted or canonical.

Rules:

1. AP `allowed` does not equal promotion.
2. Runtime `applied` does not equal promotion.
3. `promoted` does not equal canon unless a canon gate approves.
4. FINALIZED/canon mutation requires Tier 3/root authority.
5. Candidate artifacts remain candidates until a promotion gate records approval.
6. Canon transitions must record approver, authority tier, mode, provenance, and target artifact.

---

## 20. Failure behavior

Mutation governance must fail closed when required context is missing.

Fail closed when:

- `actor_authority_tier` is missing for mutation;
- `reality_mode` is missing for mutation;
- `target_artifact` is ambiguous;
- `requested_delta` is malformed;
- AP rules cannot be evaluated but are required;
- validator results are missing for required validators;
- FINALIZED mutation lacks Tier 3/root authority;
- REPLAY attempts mutation;
- DREAM output attempts unsandboxed promotion;
- source system tries to claim target-system authority;
- `base_state_hash` conflict is unresolved.

Failure must produce rejection evidence.

---

## 21. Minimum audit checklist

Before applying or trusting any mutation-capable transition, verify:

1. Is there a `request_id`?
2. Is `actor_id` identified?
3. Is `actor_authority_tier` externally supplied?
4. Is `reality_mode` explicit?
5. Is `source_system` declared?
6. Is `target_system` declared?
7. Is `target_artifact` exact?
8. Is `mutation_type` declared?
9. Is `requested_delta` structured?
10. Is `base_state_hash` present or explicitly omitted?
11. Were AP rules evaluated?
12. Is `decision` recorded?
13. Is `decision_reason` audit-readable?
14. Are validator results recorded?
15. If applied, who/what set `applied_by`?
16. Is promotion status distinct from application?
17. If rejected, is there `intent_shadow_ref` or equivalent evidence?
18. Is there `provenance_ref`?
19. Does FINALIZED have Tier 3/root authority?
20. Does REPLAY remain no-write?
21. Does DREAM remain sandbox-first?

---

## 22. Red-line rules

1. AP veto must block mutation.
2. Authority tier must not be self-assigned.
3. Reality mode must be explicit on mutation requests.
4. FINALIZED requires Tier 3/root approval.
5. REPLAY is read-only.
6. DREAM is sandbox-first.
7. Rejected mutation attempts must have rejection evidence.
8. Accepted mutation does not equal canon promotion.
9. Runtime applies accepted live-state deltas; AP does not replace runtime ownership.
10. Trae generation does not grant mutation authority.
11. Dragon routing does not grant approval.
12. MrLore continuity review does not grant mutation permission.
13. Godot/Trixel display does not authorize mutation.
14. Promotion does not equal canon unless a canon gate approves.

---

## 23. Versioning

This is `AP_MUTATION_GOVERNANCE_CONTRACT_v1`.

Backward-incompatible changes require a v2 contract or explicit amendment section.

Implementation may add schemas, validators, request wrappers, endpoint gates, Intent Shadow writers, or CI checks under this contract, but must not weaken the frozen authority tier spec.

---

## 24. Final invariant

AP is the mutation permission layer, not the entire truth system.

```text
Authority tier is necessary but not sufficient.
Reality mode outranks intent.
Tier 3 required for FINALIZED.
REPLAY is read-only.
DREAM is sandbox-first.
AP veto blocks mutation.
Allowed does not mean applied.
Applied does not mean promoted.
Promoted does not mean canon unless canon gate approves.
Continuity review is not mutation permission.
Generation is not authority.
Canon outranks convenience.
```
