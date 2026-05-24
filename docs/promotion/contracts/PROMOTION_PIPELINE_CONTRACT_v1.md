# PROMOTION PIPELINE CONTRACT v1

Status: DRAFT CONTRACT
Scope: Cross-system artifact transition stages for EngAIn — from proposal through candidate, validation, load, promotion, and canonical acceptance
Repository root: `/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn`

---

## 1. Purpose

This contract freezes the promotion pipeline: the ordered sequence of explicit stages through which any EngAIn artifact must pass before being treated as canonical.

The problem this contract addresses: systems at any layer — Trae, Dragon, MrLore, Trixel, Godot, runtime, AP — can produce artifacts that look canonical without being canonical. Without a frozen pipeline, stages collapse silently:

- a proposal gets treated as an accepted candidate;
- a validated file gets treated as runtime-loaded state;
- loaded state gets treated as promoted world truth;
- promoted truth gets treated as final canon without a canon gate.

Each of those collapses is a silent authority emergence event.

This contract prevents them by freezing six non-negotiable pipeline stages, the transitions between them, and the authority required for each transition.

Core law:

```text
proposal → candidate → validated → loaded → promoted → canonical

No stage skips. No silent transitions. Each step requires explicit authority and evidence.
```

---

## 2. Upstream authority

This contract is subordinate to:

- `AGENTS.md` repository preservation rules;
- `godotengain/engainos/docs/architecture/AUTHORITY_TIER_SPEC_v1.md`;
- `docs/ap/contracts/AP_MUTATION_GOVERNANCE_CONTRACT_v1.md`;
- `docs/runtime/contracts/RUNTIME_STATE_AUTHORITY_CONTRACT_v1.md`;
- `docs/runtime/contracts/SNAPSHOT_REPLAY_TRUTH_CONTRACT_v1.md`;
- `docs/trae/contracts/TRAE_OPERATOR_AUTHORITY_CONTRACT_v1.md`;
- `docs/mrlore/contracts/MRLORE_AUTHORITY_CONTRACT_v1.md`;
- `docs/trixel/contracts/TRIXEL_EMBODIMENT_CONTRACT_v1.md`;
- `docs/trixel/contracts/TRIXEL_COMPOSER_ABI_v1.md`;
- `system.manifest.md` runtime SSOT doctrine.

If this contract conflicts with the frozen AP authority tier spec, the AP authority tier spec wins.

---

## 3. Architectural classification

The promotion pipeline is:

```text
promotion pipeline = the gated sequence of explicit stages required for any artifact to reach canonical status
```

The promotion pipeline is not:

- a runtime operation;
- a generation operation;
- an automatic consequence of load, review, or AP allowance;
- a conversational approval;
- a rendering step;
- an observation or replay step.

The pipeline is a governed sequence of explicit transitions. Transitions do not happen automatically.

---

## 4. The six pipeline stages

### Stage 0 — Proposal

A proposal is an intent to create, change, or promote an artifact.

```text
proposal = intent artifact; not yet a nominated candidate
```

A proposal:

- originates from Dragon, Trae, MrLore, a human operator, CLI, or external request;
- expresses a desired change or creation;
- has no claim over runtime state, canon, or history;
- may be rejected, deferred, or forwarded;
- does not become a candidate by existing.

Required to advance to Candidate:
- proposal must be explicitly nominated and accepted as a candidate by an authorized system or operator;
- nomination must record: actor, authority tier, source system, target artifact, reason.

Core law:

```text
proposal != candidate
```

### Stage 1 — Candidate

A candidate is a nominated artifact that is eligible for validation.

```text
candidate = nominated artifact; eligible for validation checks, not yet validated
```

A candidate:

- has been accepted as a nomination by an authorized actor;
- has a declared target artifact, actor, authority tier, and source provenance;
- has not yet passed validation;
- may be rejected, deferred, or returned to proposal;
- does not become validated by existing as a candidate.

Required to advance to Validated:
- candidate must pass all required validators for its artifact type, target system, and reality mode;
- validator results must be recorded in the promotion record;
- each validator must be typed (schema, continuity, file parse, runtime-load check, AP rule, etc.);
- no validator can be skipped for artifact types that require it;
- validating system must record: validator identity, artifact version, results, timestamp.

Core law:

```text
candidate != validated
```

### Stage 2 — Validated

A validated artifact has passed all required checks for its type, target, and reality mode.

```text
validated = artifact that passed required validation checks; not yet loaded or applied
```

A validated artifact:

- has a complete validator record;
- is confirmed structurally and semantically acceptable for its target system;
- has not yet been applied to runtime or any live target;
- may be rejected post-validation if governance or authority context changes;
- does not become loaded or applied by passing validation.

Required to advance to Loaded:
- validated artifact must be explicitly loaded/applied to its target system through a declared load path;
- load must use the appropriate runtime/target endpoint and mutation envelope;
- AP/governance review must be complete before load for mutation-capable artifacts;
- load must record: artifact identity, target system, load endpoint, actor, authority tier, reality mode, AP decision, timestamp.

Core law:

```text
validated != loaded
```

### Stage 3 — Loaded

A loaded artifact has been accepted into live runtime or target system state.

```text
loaded = artifact accepted into live runtime or target system state; not yet promoted
```

A loaded artifact:

- has been applied to `EngAInRuntime.snapshot` or an equivalent target system live state;
- may be operational within runtime, Godot, Trixel, or another target;
- is live state, not promoted or canonical state;
- may diverge from canonical history in DRAFT, DREAM, IMBUED, or debug contexts;
- does not become promoted by being loaded.

Required to advance to Promoted:
- loaded artifact must pass a promotion gate;
- promotion gate must verify: source provenance chain, validation record, load record, AP decision record, continuity review (if required), authority tier sufficient for the target reality mode;
- promotion gate must record: gate identity, artifact identity, promotion actor, authority tier, reality mode, promotion timestamp, promotion reason, and any outstanding conditions.

Core law:

```text
loaded != promoted
runtime load != canon promotion
```

### Stage 4 — Promoted

A promoted artifact has passed a promotion gate and is eligible for canonical acceptance.

```text
promoted = artifact that passed a promotion gate; eligible for canon gate, not yet canonical
```

A promoted artifact:

- has a complete promotion gate record;
- may be treated as promoted world state in IMBUED or eligible DRAFT contexts;
- is not yet canonical unless the canon gate accepts it;
- may still be rejected by the canon gate;
- does not become canonical by being promoted.

Required to advance to Canonical:
- promoted artifact must be presented to and accepted by the canon gate;
- canon gate requires: Tier 3/root authority for FINALIZED canon entries; explicit mode = FINALIZED or equivalent for immutable canon; complete provenance chain from proposal through promotion; continuity evidence where required; human/root acknowledgment for canonical-history entries;
- canon gate must record: gate identity, artifact identity, canon actor identity, authority tier, canon mode, canon timestamp, provenance chain reference, any conditions or restrictions.

Core law:

```text
promoted != canonical unless canon gate approves
```

### Stage 5 — Canonical

A canonical artifact has been accepted by the canon gate under required authority.

```text
canonical = canon-gate-accepted artifact under required authority; authoritative world/simulation truth
```

A canonical artifact:

- is authoritative for its declared scope;
- requires Tier 3/root authority to mutate if in FINALIZED reality mode;
- may not be retroactively demoted by runtime load, replay, generation, or render alone;
- must have a complete provenance chain traceable from proposal through canon gate;
- is the end point of the pipeline — not a starting point for undocumented mutation.

Canon modification rules:

1. Canonical artifacts may only be modified through a new promotion pipeline run.
2. FINALIZED canonical artifacts require Tier 3/root authority for modification.
3. No subsystem may directly overwrite canonical artifacts without a canon gate record.
4. Canon modification attempts that lack required authority must produce Intent Shadow evidence.

---

## 5. Stage transition requirements summary

| Transition | Gate | Required evidence | Authority |
|---|---|---|---|
| Proposal → Candidate | Nomination gate | Actor, tier, source, target, reason | Declared actor authority tier |
| Candidate → Validated | Validation gate | All required validator results, typed | Validator identity, artifact version |
| Validated → Loaded | Load gate | AP decision, load endpoint, mutation envelope | Authority tier for target mode |
| Loaded → Promoted | Promotion gate | Provenance chain, validation + load records, AP decision, continuity review if required | Authority tier sufficient for reality mode |
| Promoted → Canonical | Canon gate | Complete provenance chain, Tier 3/root for FINALIZED, human/root acknowledgment | Tier 3/root for FINALIZED; declared authority for others |

---

## 6. Non-negotiable boundary law

Required distinctions:

```text
proposal != candidate
candidate != validated
validated != loaded
loaded != promoted
promoted != canonical unless canon gate approves
trajectory != canon
generation != promotion
review != approval
AP allowed != promoted
runtime load != promotion
render != canon
REPLAY output != canon advancement
DREAM output != promotion
```

Additional distinctions:

```text
Dragon proposal != candidate nomination
Trae file generation != validation pass
MrLore continuity review != promotion gate
Godot load check != runtime load record
Trixel embodiment candidate != promoted artifact
snapshot evidence != canon history entry
intent shadow != accepted stage
```

---

## 7. Non-skippable stage rules

Stages must not be silently skipped.

Rules:

1. An artifact may not be treated as validated without a validator record.
2. An artifact may not be treated as loaded without a load record.
3. An artifact may not be treated as promoted without a promotion gate record.
4. An artifact may not be treated as canonical without a canon gate record.
5. A validated artifact that has not been loaded must not be applied to live state.
6. A loaded artifact that has not been promoted must not be treated as promoted world truth.
7. A promoted artifact that has not cleared the canon gate must not be treated as canonical.
8. Stage claims in metadata or labels must be backed by records, not asserted by generating systems.

Core law:

```text
no stage may be self-asserted without a gate record
```

---

## 8. Subsystem roles in the pipeline

Each subsystem participates in the pipeline at specific stages. No subsystem may unilaterally advance an artifact beyond its authorized stage.

### 8.1 Dragon

Dragon may:
- originate proposals;
- present candidates for nomination;
- explain pipeline stage and requirements;
- route mutation envelopes to appropriate gates.

Dragon must not:
- nominate candidates without a declared actor, tier, and target;
- assert validation by conversational narrative;
- self-approve promotion or canon gates;
- hide pipeline stage transitions behind conversational convenience.

```text
Dragon proposal != candidate
Dragon routing != approval
```

### 8.2 Trae

Trae may:
- generate file artifacts from approved task specs;
- produce candidates for validation;
- apply validated task specs to produce validated artifacts.

Trae must not:
- treat generated files as validated without a validation gate record;
- treat task completion as promotion;
- assert runtime load authority.

```text
Trae generation = candidate material
generation != promotion
trajectory != canon
```

### 8.3 MrLore

MrLore may:
- produce continuity review evidence for the validated → loaded and loaded → promoted transitions;
- provide promotion eligibility assessments.

MrLore must not:
- treat continuity review as a promotion gate;
- write history entries;
- assert canonical status.

```text
MrLore continuity review = validator evidence
continuity review != promotion gate
```

### 8.4 AP

AP may:
- provide the AP rule evaluation gate required for validated → loaded;
- veto mutation that would advance pipeline stages illegally.

AP must not:
- be treated as the promotion gate or canon gate;
- be used to self-authorize canon advancement;
- skip AP rule evaluation for mutation-capable transitions.

```text
AP allowed != promoted
AP veto blocks all illegal stage advancement
```

### 8.5 Runtime

Runtime may:
- accept validated artifacts through declared load paths (validated → loaded);
- record load provenance in the promotion record.

Runtime must not:
- treat runtime load as promotion;
- treat runtime state as canonical history;
- accept artifacts that have not passed validation.

```text
runtime load = loaded stage; not promoted, not canonical
```

### 8.6 Godot and Trixel

Godot and Trixel may:
- render projections of loaded or promoted state;
- provide load-check evidence for validation.

Godot and Trixel must not:
- treat render as validation;
- treat display as promotion or canon;
- self-advance pipeline stages.

```text
rendered output != validated
Godot/Trixel render != canon
```

### 8.7 Human/root operators

Human/root operators are required for:
- canon gate approval in FINALIZED contexts (Tier 3/root);
- promotion gate review where human sign-off is required;
- overriding deferral or rejection at gates with appropriate authority.

Human/root operators must:
- record their stage-transition authority explicitly in gate records;
- not use conversational approval as a substitute for gate records.

---

## 9. Promotion record structure

Each stage transition must produce a promotion record entry.

Required fields per entry:

| Field | Meaning |
|---|---|
| `artifact_id` | Stable identity of the artifact being tracked. |
| `artifact_type` | Type: scene, entity, world, file, generated, embodiment, history entry, etc. |
| `pipeline_stage` | Current stage after this transition: candidate, validated, loaded, promoted, canonical. |
| `transition_from` | Stage before this transition. |
| `transition_gate` | Gate responsible for the transition: nomination, validation, load, promotion, canon. |
| `gate_actor` | Actor identity for the gate. |
| `gate_actor_tier` | Authority tier of the gate actor. |
| `reality_mode` | Reality mode at transition time. |
| `transition_timestamp` | When the transition was recorded. |
| `source_provenance` | Source system, generator, or task spec reference. |
| `validator_results` | Validator records for this stage (type, result, timestamp). |
| `ap_decision` | AP mutation envelope decision for this stage where applicable. |
| `load_endpoint` | Runtime/target load endpoint used, if applicable. |
| `promotion_gate_ref` | Promotion gate record reference, if applicable. |
| `canon_gate_ref` | Canon gate record reference, if applicable. |
| `promotion_conditions` | Outstanding conditions or restrictions, if any. |
| `rejection_reason` | If rejected at gate, the reason. |
| `intent_shadow_ref` | Intent Shadow reference if rejected. |
| `provenance_chain` | Ordered list of prior promotion record entries for this artifact. |

Minimum valid promotion record entry:

```json
{
  "artifact_id": "...",
  "artifact_type": "...",
  "pipeline_stage": "candidate|validated|loaded|promoted|canonical|rejected",
  "transition_from": "proposal|candidate|validated|loaded|promoted",
  "transition_gate": "nomination|validation|load|promotion|canon",
  "gate_actor": "...",
  "gate_actor_tier": 1,
  "reality_mode": "DRAFT|IMBUED|FINALIZED|DREAM|REPLAY",
  "transition_timestamp": "...",
  "source_provenance": "...",
  "validator_results": [],
  "ap_decision": null,
  "load_endpoint": null,
  "promotion_gate_ref": null,
  "canon_gate_ref": null,
  "promotion_conditions": [],
  "rejection_reason": null,
  "intent_shadow_ref": null,
  "provenance_chain": []
}
```

---

## 10. Rejection at any stage

An artifact may be rejected at any gate.

Rules:

1. Rejection must produce an Intent Shadow or equivalent rejection record.
2. Rejected artifacts must not advance the pipeline.
3. Rejected artifacts must not be applied to live state or canon.
4. Rejection records are evidence — they are not accepted state.
5. Rejection may be appealed through a new promotion pipeline run with corrected artifacts.
6. Rejection of a FINALIZED mutation attempt by a non-Tier-3 actor must be recorded and blocked.

```text
rejected artifact != accepted state
intent shadow != accepted stage
```

---

## 11. Reality mode and pipeline interaction

Reality mode constrains which stages an artifact may occupy and what authority is required.

| Reality mode | Pipeline constraints |
|---|---|
| `DRAFT` | All stages allowed; canon requires explicit gate; FINALIZED canon blocked. |
| `IMBUED` | All stages allowed; AP/governance required for mutation; Tier 3 for FINALIZED canon. |
| `FINALIZED` | Canonical stage only with Tier 3/root authority; all other mutation attempts rejected. |
| `DREAM` | Candidate, validated, and sandboxed loaded allowed; promoted and canonical require exit from DREAM + new pipeline run. |
| `REPLAY` | Read-only; no stage advances; no mutations; no promotion. |

Core laws:

```text
REPLAY cannot advance pipeline stages
DREAM cannot reach canonical without exiting DREAM and a new pipeline run
FINALIZED canonical requires Tier 3/root authority
```

---

## 12. Failure behavior

Fail closed when:

- a gate record is missing for a claimed stage;
- `artifact_id` is missing or ambiguous;
- `gate_actor_tier` is missing for a mutation-capable transition;
- `reality_mode` is missing;
- a required validator result is absent;
- AP decision is required but not recorded;
- FINALIZED transition lacks Tier 3/root authority;
- REPLAY output is presented as a pipeline stage advance;
- DREAM output claims canonical status without a new pipeline run;
- a source system self-asserts a stage without a gate record.

Failure must produce a rejection record.

---

## 13. Minimum audit checklist

Before accepting an artifact as being at a declared pipeline stage, verify:

1. Is there a promotion record entry for each stage it claims to have passed?
2. Is each gate record signed by an authorized gate actor with a declared tier?
3. Is the provenance chain complete from proposal through the current stage?
4. Is AP decision recorded for mutation-capable transitions?
5. Are validator results complete and typed?
6. Is the load record present if claiming `loaded`?
7. Is the promotion gate record present if claiming `promoted`?
8. Is the canon gate record present if claiming `canonical`?
9. Is the reality mode declared and consistent through the chain?
10. If FINALIZED canonical, is there a Tier 3/root gate record?
11. If REPLAY, did the pipeline remain read-only?
12. If DREAM, is the artifact labeled sandboxed and not claiming canonical?
13. Are any rejection records present that would block the current claimed stage?

---

## 14. Red-line rules

1. Proposal != candidate. No nomination without a gate record.
2. Candidate != validated. No validation without a typed validator record.
3. Validated != loaded. No runtime load without AP decision and load record.
4. Loaded != promoted. No promotion without a promotion gate record.
5. Promoted != canonical without a canon gate record.
6. No stage self-assertion. Stages must be backed by gate records, not labels.
7. No stage skipping. Each transition must be sequential and recorded.
8. REPLAY is read-only. No pipeline advancement in REPLAY mode.
9. DREAM is sandboxed. Cannot reach canonical without exiting DREAM and a new pipeline run.
10. FINALIZED canonical requires Tier 3/root authority.
11. Rejected artifacts must not advance the pipeline.
12. Dragon/Trae/MrLore/Godot/Trixel may not unilaterally advance artifacts past their authorized stage.
13. AP allowed != promoted. Promotion requires a promotion gate record.
14. Runtime load != promoted. Load record and promotion gate are distinct.

---

## 15. Versioning

This is `PROMOTION_PIPELINE_CONTRACT_v1`.

Backward-incompatible changes require a v2 contract or explicit amendment section.

Implementation may add promotion record schemas, gate validators, CI pipeline checkers, canon gate integrations, and Intent Shadow writers under this contract, but must not collapse pipeline stages or weaken gate authority requirements.

---

## 16. Final invariant

An artifact's claimed stage is only as trustworthy as its gate records.

```text
proposal → candidate: requires nomination gate record
candidate → validated: requires typed validator results
validated → loaded: requires AP decision + load record
loaded → promoted: requires promotion gate record with sufficient authority
promoted → canonical: requires canon gate record with Tier 3/root for FINALIZED

No stage self-asserts.
No stage skips.
REPLAY is read-only — no stage advancement.
DREAM cannot reach canonical without a new pipeline run.
FINALIZED canonical requires Tier 3/root.
Canon outranks convenience.
```
