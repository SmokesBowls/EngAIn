# MRLORE AUTHORITY CONTRACT v1

Status: Draft contract, preservation-first governance boundary
Scope: MrLore continuity authority, proposal/review artifacts, external ingest gates, promotion workflow, EngAIn integration boundaries
Repository root: `/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn`
MrLore audit target: `/home/mytruelove/Downloads/obsidianburdenNov25/_mrlore`
Normative upstream authority spec: `godotengain/engainos/docs/architecture/AUTHORITY_TIER_SPEC_v1.md`
Related embodiment contracts:
- `docs/trixel/contracts/TRIXEL_EMBODIMENT_CONTRACT_v1.md`
- `docs/trixel/contracts/TRIXEL_COMPOSER_ABI_v1.md`

---

## 1. Purpose

This contract defines what MrLore may own inside EngAIn and what it must never own.

MrLore is the continuity authority lane. It may inspect, classify, lint, audit, score, and propose. It may not silently promote proposal/review artifacts into approved canon or world state.

The core invariant is:

```text
proposal/review artifact != approved canon/world state
```

This contract exists to make MrLore a stable member of the Architecture Boundary Committee without letting continuity tooling become a hidden mutation path.

EngAIn is stabilizing around contracts and boundaries, not feature invention. This document therefore freezes authority edges before further MrLore, Trixel, Dragon, AP, ZON, runtime, or renderer integration.

---

## 2. Non-goals

This contract does not:

- make MrLore the canonical narrative author;
- make MrLore the runtime state authority;
- make MrLore the AP/governance authority;
- make MrLore the Trixel embodiment authority;
- make MrLore a renderer or output visualizer;
- make proposal files equivalent to accepted edits;
- make review artifacts equivalent to canon decisions;
- bypass `AUTHORITY_TIER_SPEC_v1.md`;
- bypass human approval for canon promotion;
- resolve the missing `authority_score_calculator.py` implementation issue;
- require immediate code mutation in the external MrLore vault;
- require cleanup, deletion, relocation, or quarantine of old MrLore files.

This is a doctrine and audit contract. It is intentionally documentation-first.

---

## 3. Authority hierarchy

MrLore must operate under the existing EngAIn authority model:

```text
Human Authority Root / AP governance / runtime authority
> canon promotion gates
> MrLore continuity validation
> proposal/review artifacts
> renderer/editor/embodiment candidates
```

MrLore can strengthen continuity confidence. It cannot grant itself mutation authority.

The binding upstream law remains `AUTHORITY_TIER_SPEC_v1.md`:

- a tier is necessary but not sufficient for mutation;
- `REPLAY` blocks all mutation;
- `FINALIZED` requires Tier 3;
- Tier escalation is impossible from inside the actor;
- rejected attempts go to Intent Shadow or equivalent review logs;
- governance must be deterministic for same inputs, tier, and reality mode;
- canon outranks convenience.

MrLore contracts must never conflict with those rules. If this contract and the frozen authority spec disagree, the frozen authority spec wins.

---

## 4. MrLore owns

MrLore may own these lanes:

### 4.1 Continuity audit authority

MrLore may inspect source material and known registry/wiki state for continuity conflicts.

Observed tool:

- `/home/mytruelove/Downloads/obsidianburdenNov25/_mrlore/tools/continuity_audit.py`

Observed contract from code comments:

- detects discontinuities deterministically;
- writes continuity findings and run reports;
- does not generate prose;
- does not edit canon;
- does not resolve conflicts.

Allowed outputs:

- `wiki/continuity/CONT-*.yaml`
- `logs/continuity_audit_*.md`
- structured conflict metadata
- human-review flags
- proposal-availability hints

These outputs are review artifacts, not canon.

### 4.2 Registry and lint support authority

MrLore may build, lint, and query registries that help humans and downstream tools understand continuity state.

Examples from observed tooling:

- registry building;
- wiki linting;
- entity contract linting;
- scene contract linting;
- relationship schema linting;
- query/report helpers.

Registry material is supporting evidence unless explicitly promoted through a canon gate.

### 4.3 External ingest gatekeeping

MrLore may define the safe boundary for external systems submitting changed files for ingest.

Observed tool:

- `/home/mytruelove/Downloads/obsidianburdenNov25/_mrlore/tools/write_changed_manifest.py`

Observed gatekeeping responsibilities:

- vault-relative paths only;
- no absolute paths;
- no `..` traversal;
- canonical forward-slash normalization;
- deduplication;
- existence checks;
- tier filtering;
- atomic manifest write;
- all external systems must use the script instead of directly writing `changed_files.txt`.

This script is an ingest gatekeeper, not canon authority. It decides what may enter the MrLore processing queue, not what becomes true.

### 4.4 Promotion eligibility scoring and reporting

MrLore may compute deterministic promotion eligibility and report whether candidates are ready for review.

Observed tools:

- `/home/mytruelove/Downloads/obsidianburdenNov25/_mrlore/tools/promotion_eligibility_gate.py`
- `/home/mytruelove/Downloads/obsidianburdenNov25/_mrlore/tools/promote_candidate.py`

Eligibility status may include concepts such as:

- authority score;
- source coverage;
- open conflict count;
- canon decision support;
- blocked by conflict;
- insufficient evidence;
- pending canon decision;
- eligible for review.

Eligibility is not approval. `eligible_for_review` means review may proceed; it does not mean canon mutation is already permitted.

### 4.5 Proposal generation authority

MrLore may generate bounded proposals from authorized continuity conflicts.

Observed tool:

- `/home/mytruelove/Downloads/obsidianburdenNov25/_mrlore/tools/propose_corrections.py`

Allowed outputs:

- proposal YAML files;
- Trae-executable task files;
- status updates on conflict records;
- logs or reports describing pending proposals.

Generated proposals are not applied patches. Trae task files are not proof of approval unless their approval path is explicit and auditable.

---

## 5. MrLore must not own

MrLore must not own:

- final canonical prose;
- direct narrative rewriting;
- silent source mutation;
- runtime simulation state;
- `EngAInRuntime.snapshot`;
- AP mutation permission;
- actor tier escalation;
- reality mode selection;
- Godot or UPBGE client state;
- renderer output;
- Trixel embodiment contracts;
- terrain grids;
- atlas policy;
- role policy;
- Dragon conversational policy;
- user approval semantics;
- final promotion from candidate/review artifact into canon without an explicit gate.

MrLore may advise and validate these lanes, but it must not seize them.

---

## 6. Artifact classes

Every MrLore artifact should be classifiable as one of the following.

| Class | Examples | Canonical? | May mutate source/world state? | Required next gate |
|---|---|---:|---:|---|
| `source_input` | Tier 0 chapter files, approved source documents | Contextual | No by MrLore alone | ingest gate + audit |
| `ingest_manifest` | `raw/changed_files.txt` | No | No | processing pipeline |
| `registry_support` | `wiki/registry.md`, entity state compilations | No unless separately promoted | No | lint + human review |
| `audit_finding` | `wiki/continuity/CONT-*.yaml` | No | No | human triage |
| `run_report` | `logs/*.md` | No | No | review |
| `proposal` | `wiki/proposals/*.yaml` | No | No | explicit approval |
| `agent_task` | `*_trae_task.txt` | No | Potentially, if separately executed | execution approval + patch review |
| `candidate_codex` | `wiki/codex_candidates/*.md` | No | No | eligibility + human approval |
| `canon_decision_support` | `wiki/canon_decisions/*.md` | Support only unless root-approved | No by MrLore alone | AP/human root gate |
| `promoted_codex` | `wiki/codex/*.md` | Canon-supporting after approved promotion | No by MrLore alone | explicit promotion record |

If an artifact cannot be classified, treat it as non-canonical review material until proven otherwise.

---

## 7. Proposal and approval semantics

### 7.1 Proposal states

MrLore proposal states should remain explicit:

```text
open
authorized_for_proposal_generation
pending_approval
approved_for_task_generation
approved_for_execution
applied
rejected
deferred
superseded
```

A proposal may only advance by an explicit actor/action that is logged.

### 7.2 Approval is not execution

Approval to write a proposal is not approval to apply it.

Approval to generate a task is not approval to mutate canon.

Approval to execute a mechanical patch is not proof that the result is canonically correct.

Each gate must preserve provenance.

### 7.3 Batch approval warning

Observed tool behavior:

- `propose_corrections.py --batch` auto-approves all safe `replace_token` proposals and writes proposal/task artifacts.

Contract rule:

`--batch` approval must be treated as mechanical batch approval, not human root approval, unless an external human approval record is attached.

Recommended future naming or metadata:

```yaml
approval_kind: mechanical_batch
human_approved: false
requires_human_review: true
```

or, if truly human-approved:

```yaml
approval_kind: human_explicit
human_approved: true
approved_by: <human-or-root-actor-id>
approval_record: <path-or-id>
```

---

## 8. Promotion contract

A candidate may not become promoted canon-supporting material unless all required gates are satisfied.

Minimum v1 promotion gates:

1. source path was admitted through the ingest manifest gate or another documented safe source;
2. registry/wiki structure passes lint;
3. continuity audit has no blocking open conflicts for the candidate;
4. authority score and evidence coverage meet the configured threshold;
5. candidate is reported as eligible for review, not auto-approved;
6. explicit approval is present;
7. promotion writes provenance metadata;
8. original candidate is preserved;
9. destination overwrite requires explicit force or equivalent review;
10. post-promotion state is auditable.

Observed `promote_candidate.py` already requires `--approve` for actual promotion and supports `--dry-run` for evaluation. This is the right shape.

However, `--approve` must mean explicit promotion approval, not merely "the script flag was supplied by an autonomous agent." Future integrations should record who or what supplied approval and under what authority.

---

## 9. External integration boundaries

### 9.1 Trixel boundary

Trixel embodies approved state. It does not own canon.

MrLore may say whether a scene, entity, identity, or relationship is continuity-safe enough to embody. Trixel may render or preview approved state. Neither MrLore nor Trixel may silently turn a preview into canonical world state.

Boundary rule:

```text
MrLore continuity validation -> approved semantic/runtime state -> Trixel embodiment
```

Not:

```text
Trixel output -> canon
```

### 9.2 Runtime boundary

The Python runtime / EngAInOS authority layers own simulation state and mutation application.

MrLore may provide continuity evidence to the runtime or AP layer, but runtime state must not be replaced by MrLore registry output.

Boundary rule:

```text
MrLore finding -> AP/runtime decision input
```

Not:

```text
MrLore finding -> runtime mutation
```

### 9.3 AP boundary

AP governs mutation legality. MrLore reports continuity legality.

Continuity legality is necessary context, not sufficient mutation permission.

Boundary rule:

```text
continuity safe != mutation authorized
```

### 9.4 Dragon boundary

Dragon may provide a friendly conversational interface over MrLore schemas, validators, proposals, and promotion gates.

Dragon must expose proposal/review/approval distinctions to the user. It must not hide a promotion behind conversational convenience.

Boundary rule:

```text
user-friendly != authority-blind
```

### 9.5 Agent boundary

AI agents may run read-only audits, generate proposals, draft contracts, and prepare review packets.

AI agents must not silently approve, promote, or mutate finalized canon. They may not self-escalate authority.

---

## 10. Determinism and provenance requirements

MrLore governance paths should be deterministic where possible.

For the same inputs, registry state, rule set, thresholds, and source files, MrLore should produce the same classifications and eligibility results.

Required provenance for mutation-adjacent artifacts:

- source path or source id;
- source tier or classification if known;
- tool name and version if available;
- timestamp;
- actor or runner identity when available;
- input artifact digest when practical;
- output artifact path;
- approval kind;
- approval actor if human/root-approved;
- whether the artifact is canonical, review-only, or candidate-only.

If provenance is missing, the artifact remains review-only.

---

## 11. Known current risk: missing authority score calculator

Observed issue from the audit handoff:

- `promotion_eligibility_gate.py` imports `tools/authority_score_calculator.py`.
- `promote_candidate.py` imports `tools/authority_score_calculator.py`.
- Active `tools/authority_score_calculator.py` appears missing.
- Archived copy appears at:
  `/home/mytruelove/Downloads/obsidianburdenNov25/_mrlore/tools/_archived/2026-05-17_layer_realignment/authority_score_calculator.py`

Contract impact:

- promotion eligibility and promotion workflows depend on a single source of truth for authority scoring;
- duplicated score logic was intentionally removed from active tools;
- restoring or re-anchoring the scorer is a follow-up task;
- until resolved, score-dependent promotion should be treated as blocked or mechanically incomplete.

Safe next step:

1. inspect the archived scorer read-only;
2. compare imports and expected function signature;
3. decide whether to restore, wrap, or reimplement as an active governed module;
4. add a minimal dry-run verification;
5. preserve archived provenance.

This contract does not perform that fix.

---

## 12. Minimum review checklist

Before any MrLore output is consumed by AP, runtime, Trixel, Dragon, or a human promotion lane, verify:

- What artifact class is this?
- Is it canonical, candidate, review-only, or generated support?
- Which tool produced it?
- Which source files were used?
- Was the ingest path gated?
- Were open continuity conflicts checked?
- Was authority scoring available and deterministic?
- Is human/root approval required?
- Is approval separate from execution?
- Is execution separate from canon acceptance?
- Is provenance preserved?
- Does this cross into runtime, AP, renderer, or embodiment authority?
- If so, which contract governs that boundary?

If any answer is unknown, do not promote automatically.

---

## 13. Red-line rules

1. MrLore must not silently mutate source prose.
2. MrLore must not silently mutate runtime/world state.
3. MrLore must not treat proposal artifacts as canon.
4. MrLore must not treat batch approval as human root approval without an attached approval record.
5. MrLore must not bypass AP or the frozen authority tier spec.
6. MrLore must not let renderer/editor output backflow into canon.
7. MrLore must not self-escalate actor authority.
8. MrLore must preserve candidates, reports, and provenance when promoting.
9. MrLore must classify unknown artifacts as review-only until proven otherwise.
10. MrLore must fail closed when score, approval, source, or provenance gates are missing.

---

## 14. Versioning

This is `mrlore_authority.v1`.

Backward-incompatible changes require:

- a v2 document;
- explicit migration notes;
- updated integration checklists;
- review against `AUTHORITY_TIER_SPEC_v1.md`;
- review against Trixel embodiment/editor contracts if renderer or embodiment lanes are affected.

---

## 15. Final invariant

MrLore is continuity authority, not canon owner.

Trixel embodies approved state, not truth.

Runtime owns simulation state, not provenance.

AP governs mutation, not aesthetics.

Dragon makes governance usable, not optional.

Canon outranks convenience.
