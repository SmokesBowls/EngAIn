# TRAE OPERATOR AUTHORITY CONTRACT v1

Status: DRAFT CONTRACT
Scope: Trae as supervised file-generation operator for EngAIn, Godot, runtime-adjacent tooling, and generated-file jobs
Repository root: `/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn`

---

## 1. Purpose

This contract freezes Trae's authority boundary before deeper use as a dynamic file-generation and editing mechanism inside EngAIn.

Trae is powerful because it can inspect files, run shell commands, create/edit source artifacts, edit JSON, operate in Docker, and record trajectories. That makes it useful for Godot/runtime tooling, but also makes it the first audited EngAIn subsystem where authority mistakes can become physical mutations on disk.

This document therefore classifies Trae as a supervised operator, not a decision authority.

Core law:

```text
Trae writes files.
Contracts decide whether those files are valid.
Runtime decides whether those files load.
Human/EngAIn approves promotion.
```

---

## 2. Upstream authority

This contract is subordinate to:

- `AGENTS.md` repository preservation rules;
- `godotengain/engainos/docs/architecture/AUTHORITY_TIER_SPEC_v1.md`;
- `docs/trixel/contracts/TRIXEL_EMBODIMENT_CONTRACT_v1.md`;
- `docs/trixel/contracts/TRIXEL_COMPOSER_ABI_v1.md`;
- `docs/mrlore/contracts/MRLORE_AUTHORITY_CONTRACT_v1.md`;
- runtime SSOT doctrine in `system.manifest.md` and `godotsim/` architecture notes.

If this contract conflicts with the frozen AP authority tier spec, the AP authority tier spec wins.

---

## 3. Architectural classification

Trae is:

```text
Trae = supervised file-generation operator
```

Trae may perform mechanical work inside an approved task scope:

- inspect files;
- run declared shell commands;
- create files;
- edit files;
- edit JSON;
- generate candidate Godot/runtime/tooling artifacts;
- run validators and load checks;
- record provenance/trajectory;
- report completion evidence.

Trae is not:

- canon authority;
- runtime authority;
- AP authority;
- promotion authority;
- continuity authority;
- renderer truth authority;
- human approval authority;
- source-of-truth owner for world state.

---

## 4. Non-negotiable boundary law

Trae may create or edit files only from approved task specs.

Trae may not decide:

- what is canon;
- what is `FINALIZED`;
- what narrative or world state is true;
- what should be promoted;
- whether generated files are authoritative;
- whether Godot output is canonical;
- whether AP rules may be bypassed;
- whether runtime truth should be mutated;
- whether review/proposal artifacts count as approved state.

Required distinction:

```text
proposal != approval
approval != execution
execution != runtime load
runtime load != promotion
rendered output != truth
trajectory != canon
```

---

## 5. Correct generation lane

Every Trae file-generation job must follow this lane:

```text
approved input / task spec
→ generated or edited candidate file
→ validation
→ Godot/runtime load check where applicable
→ review
→ commit/promote or reject
```

Forbidden lane:

```text
agent decides
→ writes files
→ Godot/runtime trusts them
```

A Trae-created artifact remains a candidate until an independent validation/promotion path accepts it.

---

## 6. Required generated-file job contract

Every Trae generated-file job must have a declared job spec before mutation.

Required fields:

| Field | Requirement |
|---|---|
| `job_id` | Stable identifier for the generation/edit job. |
| `requested_by` | Actor or process requesting the work. |
| `approved_by` | Actor or authority approving the task spec. |
| `approval_tier` | AP/human tier or explicit non-canonical draft authority. |
| `approval_timestamp` | Time approval was granted. |
| `task_spec_path` | Path to approved task spec. |
| `task_spec_hash` | Hash of approved task spec. |
| `source_inputs` | Files/data allowed as input. |
| `source_input_hashes` | Hashes of declared source inputs. |
| `target_paths` | Exact files/directories Trae may create/edit. |
| `forbidden_paths` | Files/directories Trae must not mutate. |
| `allowed_operations` | Read/create/edit/json_edit/bash list. |
| `workspace_root` | Root of authorized workspace. |
| `staging_root` | Candidate output area if generation is staged. |
| `sandbox_mode` | `none`, `docker`, or another declared sandbox. |
| `provider` | LLM/tool provider used. |
| `model` | Model used. |
| `local_or_cloud` | Local/Ollama or cloud/proprietary adapter. |
| `max_steps` | Execution step limit. |
| `trajectory_path` | Provenance output path. |
| `generated_files` | Files created by the job. |
| `modified_files` | Files changed by the job. |
| `deleted_files_allowed` | Default `false`; must be explicit if true. |
| `validators_required` | Validation commands that must pass. |
| `validation_commands` | Exact commands to run. |
| `godot_load_check` | Required when Godot files/scenes/scripts are touched. |
| `runtime_load_check` | Required when runtime-loadable artifacts are touched. |
| `ap_governance_check` | Required when mutation/canon/finality is implicated. |
| `expected_outputs` | Expected artifacts and behavior. |
| `rejection_policy` | What to do if validation fails. |
| `promotion_policy` | How candidate artifacts can be accepted. |
| `promotion_approver` | Who/what may approve promotion. |
| `commit_policy` | Whether and how outputs can be committed. |
| `rollback_plan` | How to undo or discard outputs. |
| `artifact_classification` | source/generated/candidate/runtime/canon/archive/vendor. |
| `canonicality` | Default `non_canonical_candidate`. |
| `notes_on_skipped_checks` | Explicitly record skipped checks and why. |
| `final_status` | One of the states below. |

Allowed final statuses:

- `generated_pending_validation`
- `validation_failed`
- `validation_passed_pending_review`
- `rejected`
- `approved_for_promotion`
- `promoted`

`promoted` must not be emitted by Trae alone unless an explicit promotion authority has already approved and recorded the promotion.

---

## 7. File path authority

Trae may mutate only explicitly allowed paths.

Default forbidden paths unless explicitly approved by the task spec and the relevant authority contract:

- canonical narrative/codex/world state;
- `FINALIZED` or canon files;
- runtime snapshots or live state dumps;
- generated caches unless the task is artifact regeneration;
- archive/quarantine/recovered directories;
- vendored dependency trees;
- build outputs;
- AP authority specs;
- promotion manifests;
- files outside the declared workspace;
- files not listed in `target_paths`.

For EngAIn, repository preservation rules apply:

- do not rename, move, delete, quarantine, or clean up files unless explicitly asked;
- do not assume generated files are disposable;
- do not treat archives or duplicate-looking files as obsolete;
- classify before mutating.

---

## 8. Bash authority and risk

Trae's bash capability is mechanical execution only.

Risks:

- shell state can persist;
- commands can mutate many files;
- commands can start long-lived processes;
- commands can read environment/config output;
- commands can bypass source-level edit restrictions if not governed externally.

Rules:

1. Bash commands must be declared or derivable from the approved task spec.
2. Destructive shell commands require explicit approval.
3. Cleanup/purge/reconcile scripts must not be run casually.
4. Commands that write outside `target_paths` are prohibited unless explicitly approved.
5. Validation commands must be recorded in the job result.
6. Background/long-lived processes must have explicit purpose, stop condition, and port/process notes.

---

## 9. Edit and JSON-edit authority

Text and JSON edit tools are mutation tools.

Rules:

1. Edits require target path authorization.
2. Created files are candidates until validated.
3. JSON parse validity is not semantic validity.
4. A successful text replace is not approval.
5. Trae must not hand-edit generated/runtime artifacts unless the task spec explicitly allows artifact surgery.
6. Trae must not mutate canonical/finalized narrative or world state unless the AP/human authority model permits it.

---

## 10. Docker and sandbox boundary

Docker is an execution boundary, not an authority boundary.

Core law:

```text
Docker is not authority.
```

A Docker container may reduce host-system blast radius, but a read-write mounted workspace remains writable. A containerized Trae can still damage the mounted repository if given broad access.

Required Docker/sandbox metadata:

- `sandbox_mode`;
- `container_image` if applicable;
- `workspace_mount.host_path`;
- `workspace_mount.container_path`;
- `workspace_mount.access` as `read_only` or `read_write`;
- `docker_keep` behavior;
- cleanup policy.

Default for generation should be staged output, not direct mutation of canonical/runtime files.

---

## 11. Trajectory and provenance boundary

Trae's trajectory recorder is valuable evidence.

It may record:

- task prompt;
- provider/model;
- messages;
- tool calls;
- tool results;
- final result;
- success flag;
- execution timing.

But:

```text
Trajectory is evidence, not approval.
```

A trajectory must not be treated as:

- human approval;
- AP approval;
- promotion;
- canonization;
- runtime truth;
- proof that validators passed unless the validator output is present and checked.

Trajectory files may contain prompts, file contents, tool outputs, and accidental secrets. They must be handled as provenance artifacts with possible sensitive content.

---

## 12. task_done and completion boundary

`task_done` or an agent-declared success state is not sufficient proof.

A Trae job is not complete until the result includes:

- changed file list;
- validation command output;
- Godot/runtime load-check output where applicable;
- skipped checks and reasons;
- final candidate/promotion status;
- trajectory/provenance path;
- rejection/rollback note if validation failed.

Completion evidence does not imply promotion.

---

## 13. Local/cloud provider boundary

EngAIn is local-first and provider-optional.

Trae may use local/Ollama or cloud/proprietary adapters if configured, but provider choice changes capability and privacy posture, not authority.

Rules:

1. Ollama/local execution must remain a supported lane.
2. Cloud providers are optional adapters, not required authority.
3. Provider and model must be recorded per job.
4. Cloud-generated output is not more authoritative than local-generated output.
5. Local-generated output is not automatically valid just because it stayed local.
6. No provider may bypass validation, AP, runtime load checks, or human/EngAIn promotion.

---

## 14. Godot dynamic generation boundary

For Godot dynamic file generation, Trae may create candidate files only from an approved task spec.

Required lane:

```text
approved task spec
→ generated Godot candidate file
→ syntax/import validation
→ Godot load/open check where available
→ runtime snapshot/API compatibility check if runtime-coupled
→ review
→ commit/promote or reject
```

Godot must not trust generated files merely because Trae wrote them.

Generated Godot scenes/scripts/resources must not:

- own canonical world state;
- bypass runtime/API authority;
- persist hidden runtime truth in client nodes;
- replace AP mutation rules;
- make renderer output canonical.

Godot output is load/render evidence, not canon proof.

---

## 15. Runtime boundary

Runtime owns live simulation truth.

Trae may generate candidate runtime files or candidate data artifacts only through approved jobs. Trae must not directly mutate live runtime truth or treat generated files as loaded runtime state.

Runtime law:

```text
Generated file != loaded runtime state.
Loaded runtime state != promoted canon.
```

Runtime acceptance requires the runtime/load contract and AP/governance checks where mutation is implicated.

---

## 16. AP and mutation governance boundary

AP governs mutation legality. Trae executes file operations.

Trae must not:

- self-assign Tier 3 authority;
- escalate actor tier;
- bypass `REPLAY` no-write rules;
- mutate `FINALIZED` state as an AI/operator;
- convert successful generation into AP-approved mutation;
- treat a task spec as sufficient for canonical mutation unless the task spec carries explicit authority metadata.

If a job touches mutation-adjacent state, it must include an `ap_governance_check` or explicitly state that it is non-canonical candidate work only.

---

## 17. Interaction with MrLore, Trixel, Runtime, AP, and Dragon

### 17.1 MrLore

MrLore may provide continuity findings, candidate review evidence, and promotion eligibility reports.

Trae may consume MrLore evidence only as input to an approved task spec.

MrLore finding != Trae approval to mutate.

### 17.2 Trixel

Trixel may provide embodiment/editor candidate artifacts and deterministic rendering lanes.

Trae may generate or edit Trixel/Godot embodiment files only as candidates unless promotion is explicitly approved.

Rendered output != truth.

### 17.3 Runtime

Runtime decides whether runtime-loadable artifacts actually load into live state.

Runtime load != canon promotion.

### 17.4 AP

AP governs mutation and reality-mode/tier legality.

Continuity-safe or validation-passing output is not automatically mutation-authorized.

### 17.5 Dragon

Dragon may orchestrate conversational task specs and present review/approval choices.

Dragon must not hide candidate/review/approval distinctions behind conversational convenience.

Dragon saying “done” or “approved” must map to a recorded authority event, not an implicit UI convenience.

---

## 18. Required validation evidence

Every mutation-capable Trae job must report:

- exact files created;
- exact files modified;
- exact files deleted, if any;
- commands run;
- validation results;
- load-check results where applicable;
- skipped checks and why;
- known risks;
- whether outputs remain candidates;
- whether anything was promoted;
- provenance/trajectory location.

If validation is unavailable, the artifact remains `generated_pending_validation` or `validation_failed`, not approved.

---

## 19. Rejection and rollback

Failed validation must fail closed.

Reject or quarantine-by-policy only; do not silently promote partial outputs.

Rejection rules:

- failed validation blocks promotion;
- missing validation blocks promotion;
- missing trajectory/provenance blocks promotion for mutation-capable jobs;
- unexpected file changes block promotion until explained;
- edits outside `target_paths` block promotion;
- AP/mode/tier mismatch blocks mutation.

Rollback policy must be declared before broad mutation jobs.

---

## 20. Minimum audit checklist before trusting Trae output

Before any Trae output is consumed by Godot, runtime, AP, Trixel, MrLore, Dragon, or human promotion lanes, verify:

1. Was there an approved task spec?
2. Who requested the job?
3. Who approved the job?
4. What authority tier/mode applies?
5. What exact files changed?
6. Were all changed paths authorized?
7. Were forbidden paths untouched?
8. Were validators run?
9. Did Godot/runtime load checks pass where required?
10. Is the artifact still candidate or promoted?
11. Where is the trajectory/provenance?
12. Were skipped checks documented?
13. Is there a rollback/rejection path?
14. Did any output claim canon/runtime truth without approval?

---

## 21. Red-line rules

1. Trae must not decide canon.
2. Trae must not decide runtime truth.
3. Trae must not decide promotion.
4. Trae must not silently mutate finalized/canonical state.
5. Trae must not treat Docker as authority.
6. Trae must not treat trajectory as approval.
7. Trae must not treat `task_done` as validation.
8. Trae must not let generated Godot output become trusted merely because it rendered.
9. Trae must not bypass AP or the frozen authority tier spec.
10. Trae must not widen a task beyond declared target paths without renewed approval.

---

## 22. Versioning

This is `TRAE_OPERATOR_AUTHORITY_CONTRACT_v1`.

Backward-incompatible changes require a v2 contract or explicit amendment section.

Implementation may add validators, job-spec schemas, wrappers, or CI checks under this contract, but must not weaken the core authority law without explicit review.

---

## 23. Final invariant

Trae is an operator, not an authority.

```text
Trae writes candidate files under approved scope.
Contracts validate them.
Runtime may load them.
AP governs mutation.
Human/EngAIn approves promotion.
Canon outranks convenience.
```
