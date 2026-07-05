# SUPPORT EXECUTION DOCTRINE v1

This document defines the stable execution lane and replaceable runners for automated and assisted code repair in the EngAIn project.

## Stable Lane & Replaceable Runner

The support execution lane represents a stable boundary for bounded code modification tasks. The agent/runner executing the tasks is a replaceable component, not a permanent authority.

```text
SUPPORT_EXECUTION_LANE = stable
ACTIVE_RUNNER = replaceable
CURRENT_ACTIVE_RUNNER = Aider
RUNNER_IDENTITY_IS_NOT_AUTHORITY = TRUE
TASK_PACKET_DEFAULT = atomic microtask
ONE_TARGET_FILE_PER_PATCH = preferred default
PATCHER_ACCEPTANCE_RULE = mandatory
AUTO_ACCEPT_STATUS = FORBIDDEN_UNTIL_PROVEN
SUPPORT_RUNNER_CONFIG_RESOLUTION = FUTURE_ENGINEERING_TASK
```

---

## Auto-Accept Reconsideration Threshold

Automatic diff acceptance is strictly forbidden under the baseline doctrine. Human diff acceptance remains mandatory. Any future transition to an automated or semi-automated validation model requires meeting the following measurable, proven threshold:

```text
AUTO_ACCEPT_STATUS = FORBIDDEN_UNTIL_PROVEN

AUTO_ACCEPT_RECONSIDERATION_THRESHOLD:
- 25 consecutive clean ollama_diff_patcher runs
- 0 destructive diffs
- 0 rollback-required writes
- 0 deleted existing ptype branches unless explicitly requested
- at least 5 builder-logic edits
- at least 5 gate/test-file edits
- at least 5 kernel/validation edits
- every run must show diff, pass py_compile where applicable, pass target gate, and pass declared regression gate
- human diff acceptance remains mandatory during the entire proof window
```
