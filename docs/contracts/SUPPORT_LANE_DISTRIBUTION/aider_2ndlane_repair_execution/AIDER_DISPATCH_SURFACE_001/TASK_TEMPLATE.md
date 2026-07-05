# AIDER TASK PACKET TEMPLATE

SURFACE_ID: AIDER_DISPATCH_SURFACE_001
INTERACTION_MODEL: manual_only

## 1. Task Identity

TASK_ID:
TASK_TITLE:
TASK_STATUS: READY_FOR_AIDER
CREATED_BY: human
HUMAN_OWNER: mytruelove

## 2. Authority And Lane Boundary

TIER_AUTHORITY:
STACK:
EXECUTION_LANE: aider_2ndlane_repair_execution
TARGET_LANE:
REPO_PATH:

## 3. Aider Boundary Rules

1. The first meaningful file read must be this packet.
2. Before editing, Aider must echo:
   - TIER_AUTHORITY
   - STACK
   - EXECUTION_LANE
   - TARGET_LANE
   - REPO_PATH
   - FILES_IN_SCOPE
   - DONE_MEANS
3. Aider must not search for a different project root.
4. Aider may only edit files explicitly listed in FILES_IN_SCOPE.
5. If a listed file does not exist and is not listed under NEW_FILES_ALLOWED, Aider must stop and report:
   MISSING_SCOPE_FILE
6. If the gate cannot be reproduced before editing, Aider must stop and report:
   REPRO_FAILED_BEFORE_EDIT
7. If Aider needs another file, Aider must stop and report:
   BLOCKED_SCOPE_EXPANSION_REQUIRED

## 4. Files In Scope

FILES_IN_SCOPE:
-

NEW_FILES_ALLOWED:
-

DIRECTORIES_IN_SCOPE:
-

FILES_OUT_OF_SCOPE:
-

## 5. Problem Statement

EXPECTED_BEHAVIOR:

KNOWN_BAD_BEHAVIOR:

## 6. Required Reproduction

REPRODUCTION_COMMAND:

EXPECTED_PRE_EDIT_RESULT:

## 7. Post Edit Gates

POST_EDIT_GATE:

REGRESSION_GATES:
-

## 8. Done Means

DONE_MEANS:
-

DONE_DOES_NOT_MEAN:
-

## 9. Required Gate Table

Every listed gate must be reported as TRUE, FALSE, or BYPASS.

GATES_REQUIRED:
- GATE_PACKET_READ
- GATE_BOUNDARY_ECHOED
- GATE_REPRODUCTION_RAN
- GATE_PRE_EDIT_RESULT_RECORDED
- GATE_PATCH_WITHIN_SCOPE
- GATE_POST_EDIT_GATE_TRUE
- GATE_REGRESSIONS_TRUE
- GATE_RESULT_PACKET_WRITTEN

FALSE blocks acceptance.

## 10. Rollback Command

ROLLBACK_COMMAND:

## 11. Final Packet Verdict

AIDER_ALLOWED_TO_BEGIN: TRUE
FINAL_STAMP: AIDER_TASK_PACKET_READY
