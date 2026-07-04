# TRAE TASK PACKET TEMPLATE

TASK_PACKET_VERSION: 1
SURFACE_ID: TRAE_DISPATCH_SURFACE_001
INTERACTION_MODEL: manual_only

## 1. Task Identity

TASK_ID:
TASK_TITLE:
TASK_STATUS: READY_FOR_TRAE
CREATED_BY: human
CREATED_AT:
HUMAN_OWNER:

## 2. Authority Declaration

TIER_AUTHORITY:
LANE:
STACK:
PROJECT:

Valid example:

TIER_AUTHORITY: EngAInOS TIER1
LANE: trae_2ndlane_repair_execution
STACK: retrographer
PROJECT: MILESTONE_006

If TIER_AUTHORITY or LANE is blank, Trae must stop.

## 3. Target Repo Boundary

REPO_PATH:

Example:

REPO_PATH: /mnt/data-drive/retrographer

Trae may not choose a repo path.
Trae may not operate outside REPO_PATH.
Trae must verify REPO_PATH exists before doing anything else.

## 4. Allowed Scope

FILES_IN_SCOPE:
- path/from/repo/root/example.py

DIRECTORIES_IN_SCOPE:
- path/from/repo/root/

FILES_FORBIDDEN:
- docs/canon/
- docs/contracts/engainos_1stlane_governance_authority/
- any file not listed in FILES_IN_SCOPE unless explicitly allowed by human

SCOPE_EXPANSION_ALLOWED: no

If Trae believes another file must be changed, Trae must stop and report:

BLOCKED_SCOPE_EXPANSION_REQUIRED

## 5. Problem Statement

HUMAN_OBSERVED_FAILURE:

Write the actual failure here.

Example:

The parity gate rejects the piece even though required baseline fields appear present.

EXPECTED_BEHAVIOR:

Write what should happen.

Example:

The gate should return TRUE only when every manifest-declared baseline requirement is satisfied.

KNOWN_BAD_BEHAVIOR:

Write what currently happens.

Example:

The gate returns TRUE even when a required field is missing.

## 6. Done Definition

DONE_MEANS:

Write the exact human definition of done.

Required form:

- Failure is reproduced before patch.
- Pre-patch gate result is recorded.
- Minimal patch is applied only to files in scope.
- Post-patch gate returns TRUE.
- No authority, lane, schema, or runtime meaning changes unless explicitly declared.
- Result packet is written.
- Human verification remains pending.

DONE_DOES_NOT_MEAN:

- Trae's own TRUE is final acceptance.
- Patch is automatically merged.
- Scope may expand silently.
- Trae may invent a fallback.
- Trae may update canon/AP/runtime law.

## 7. Required Step 0 Snapshot

SNAPSHOT_REQUIRED: yes

SNAPSHOT_METHOD_ALLOWED:
- git stash
- git tag
- temporary safety commit
- patch files under .engain/snapshots/

SNAPSHOT_COMMAND:

Paste exact command here or write:

HUMAN_ALREADY_CREATED_SNAPSHOT: yes
SNAPSHOT_ID:

ROLLBACK_COMMAND:

If SNAPSHOT_REQUIRED is yes and no snapshot exists, Trae must stop unless this task explicitly allows Trae to create the snapshot.

TRAE_MAY_CREATE_SNAPSHOT: no

## 8. Required Reproduction

REPRODUCE_COMMAND:

Example:

python gates/gate_milestone_006_parity.py

EXPECTED_PRE_PATCH_RESULT:

Example:

FALSE

REPRODUCTION_LOG_REQUIRED: yes

Trae must run REPRODUCE_COMMAND before patching.

If reproduction cannot be run, Trae must stop and write result:

REJECTED_REPRODUCTION_NOT_AVAILABLE

## 9. Required Gate Commands

PRE_PATCH_GATE_COMMAND:

POST_PATCH_GATE_COMMAND:

EXPECTED_POST_PATCH_RESULT:

Example:

TRUE

GATE_OUTPUT_REQUIRED: yes

Gate output must be copied or summarized into RESULT_TEMPLATE.md.

## 10. Allowed Commands

ALLOWED_COMMANDS:
- git status
- git diff
- grep
- sed
- cat
- python <declared gate>
- pytest <declared test>
- apply_patch or equivalent patch operation on FILES_IN_SCOPE only

FORBIDDEN_COMMANDS:
- rm -rf
- git push
- git clean -fdx
- editing files outside FILES_IN_SCOPE
- modifying canon/source story files
- modifying AP authority files
- modifying runtime law files
- starting daemon/watch/poll loops
- network installs
- package upgrades
- Docker cleanup unless explicitly listed

## 11. Patch Rules

PATCH_ALLOWED: yes

PATCH_STYLE:
minimal

PATCH_MAY_CHANGE_BEHAVIOR: no

PATCH_MAY_CHANGE_SCHEMA: no

PATCH_MAY_CHANGE_AUTHORITY: no

PATCH_MAY_CHANGE_LANE: no

PATCH_MAY_ADD_FALLBACK: no

PATCH_MAY_INFER_TRUTH: no

PATCH_MAY_CREATE_NEW_FILES: no

NEW_FILES_ALLOWED:
- none

If any answer above needs to become yes, this task packet must be rewritten by the human before Trae begins.

## 12. Required TRUE/FALSE/BYPASS Gates

GATES_REQUIRED:
- [ ] GATE_REPO_PATH_EXISTS
- [ ] GATE_LANE_DECLARED
- [ ] GATE_SCOPE_DECLARED
- [ ] GATE_SNAPSHOT_EXISTS
- [ ] GATE_REPRODUCTION_RAN
- [ ] GATE_PRE_PATCH_RESULT_RECORDED
- [ ] GATE_PATCH_WITHIN_SCOPE
- [ ] GATE_POST_PATCH_RESULT_RECORDED
- [ ] GATE_NO_AUTHORITY_CHANGE
- [ ] GATE_NO_LANE_CHANGE
- [ ] GATE_NO_SCHEMA_CHANGE
- [ ] GATE_NO_RUNTIME_MEANING_CHANGE
- [ ] GATE_RESULT_PACKET_WRITTEN

Every gate must be reported as exactly one of:

TRUE
FALSE
BYPASS

FALSE blocks acceptance.

Unknown lane blocks acceptance.

## 13. Human Verification

HUMAN_VERIFICATION_REQUIRED: yes

HUMAN_VERIFICATION_COMMAND_OR_CHECK:

Example:

Manually inspect diff and run the same gate from a clean shell.

MERGE_ALLOWED_BEFORE_HUMAN_VERIFICATION: no

## 14. Dispatch Instruction

Trae may begin only if:

- TASK_STATUS is READY_FOR_TRAE
- REPO_PATH is present
- TIER_AUTHORITY is present
- LANE is present
- FILES_IN_SCOPE is present
- REPRODUCE_COMMAND is present
- PRE_PATCH_GATE_COMMAND is present
- POST_PATCH_GATE_COMMAND is present
- SNAPSHOT_REQUIRED is satisfied
- This task does not ask Trae to run as daemon, watcher, or polling loop

If any required field is missing:

ACCEPTANCE: BLOCKED_PENDING_TIER1_LANE_ASSIGNMENT
or
ACCEPTANCE: REJECTED_MALFORMED_TASK_PACKET
