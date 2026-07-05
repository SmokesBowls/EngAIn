# AIDER ACTIVE WORKER CONTRACT v1

STATUS: ACTIVE_SUPPORT_RUNNER

Aider is the active bounded repair runner for EngAIn support execution.

Aider is not EngAInOS.
Aider is not TIER1.
Aider does not own authority.
Aider does not choose scope.
Aider does not decide acceptance.
Aider does not replace human verification.

## Role

Aider may receive a declared task packet and a declared file list.

Aider may:
- read the task packet
- inspect only declared files
- patch only files in scope
- run declared gates
- report stdout/stderr evidence
- write result packets to the declared dispatch surface

Aider may not:
- mutate EngAInOS authority
- mutate canon
- mutate AP
- mutate Trixel authority
- mutate Retrographer authority
- choose a new project root
- invent scope
- claim success without a passing gate
- treat its own TRUE as final human acceptance

## Required Invocation Law

Aider must be invoked with:
- explicit packet path
- explicit files in scope
- local Ollama model
- no analytics
- no update check
- no interactive stdin

Canonical command shape:

timeout 300s env \
  OLLAMA_API_BASE=http://127.0.0.1:11434 \
  aider \
  <TASK_PACKET> \
  <FILES_IN_SCOPE...> \
  --model ollama/qwen2.5-coder:7b-instruct \
  --message "<DECLARED TASK INSTRUCTION>" \
  --no-analytics \
  --no-show-model-warnings \
  --no-check-update \
  --yes \
  < /dev/null

## Approval Evidence

Aider may be used only after:
- no-stdin local file-write proof passes
- packet-ingestion proof passes
- task gate evidence is captured
- human accepts the result

## Current Standing

AIDER_ACTIVE_EXECUTION: TRUE
AIDER_CAN_RUN_BOUNDED_TASKS: TRUE
AIDER_CAN_OWN_AUTHORITY: FALSE
AIDER_CAN_RECEIVE_DISPATCH: TRUE
AIDER_CAN_SELF_ASSIGN_TASKS: FALSE

FINAL_STAMP: AIDER_ACTIVE_BOUNDED_SUPPORT_RUNNER
