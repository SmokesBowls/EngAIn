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

---

## Role Distribution & Storage Boundaries

To ensure that the repair lane is completely storage-agnostic, Git operations are decoupled from worker capabilities:

### Aider/Runner Role (Storage-Agnostic Worker)
* Read and interpret the incoming task packet.
* Modify or create the required target files.
* Run the required validation/proof commands.
* Write the result packet.
* Report stdout/stderr evidence.
* **Never require Git as part of execution success.**

### Antigravity/Agent Role (Supervisor & Archiver)
* Launch the runner/Aider.
* Observe what the runner did.
* Verify outputs if needed.
* Archive/move packets.
* Commit and push changes only as supervisor bookkeeping when the repository uses Git.
* Clearly state that any Git commit was created by the supervisor (Antigravity), not by the runner (Aider).

---

## Required Provenance Fields

All execution result packets must use this schema to trace task execution details:

```text
execution_id: <unique id>
executor_name: <name and version of model/runner>
command_interface_used: <exact command run to invoke runner>
files_created_by_executor: <list of files created>
files_modified_by_executor: <list of files modified>
commands_run_by_executor: <list of validation/proof commands run>
result_packet_path: <path to result file>
proof_stdout_markers: <list of required markers verified>
artifact_hashes_or_file_sizes: <list of files and sizes>
supervisor_archive_method: <how the task was moved and committed>
git_commit_hash_created_by_supervisor_optional: <commit hash created by supervisor>
```

