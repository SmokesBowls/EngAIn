# AIDER ENTRY STAMP

STATUS: ACTIVE

Aider enters EngAIn as the active bounded support execution runner.

## Entry Basis

Aider is admitted because the support-runner workflow now has:
- explicit task packet requirement
- explicit file-scope requirement
- no-stdin invocation rule
- declared gate requirement
- human final acceptance requirement

## Authority Boundary

Aider is a runner, not authority.

AIDER_ACTIVE_EXECUTION: TRUE
AIDER_CAN_RECEIVE_DISPATCH: TRUE
AIDER_CAN_RUN_DECLARED_GATES: TRUE
AIDER_CAN_PATCH_SCOPE_FILES: TRUE

AIDER_CAN_OWN_AUTHORITY: FALSE
AIDER_CAN_MUTATE_CANON: FALSE
AIDER_CAN_MUTATE_AP: FALSE
AIDER_CAN_MUTATE_ENGAINOS_AUTHORITY: FALSE
AIDER_CAN_SELF_ASSIGN_TASKS: FALSE

FINAL_STAMP: AIDER_INSTALLED_AS_ACTIVE_SUPPORT_RUNNER
