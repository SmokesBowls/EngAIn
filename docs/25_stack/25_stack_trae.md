Trae profile as code-worker agent and repo-edit executor.

## 1. PROJECT ROLE

Trae owns code-worker execution for software engineering tasks. Its declared project identity is an “LLM-based agent for general purpose software engineering tasks,” packaged as `trae-agent`, with a CLI entrypoint `trae-cli = "trae_agent.cli:main"` and Python requirement `>=3.12`. 

It owns task execution through CLI commands, repository navigation, bash execution, file editing, JSON editing, sequential thinking, MCP tool discovery, trajectory recording, Docker-backed execution, and final task completion signaling. The README explicitly lists file editing, bash execution, sequential thinking, multi-LLM support, YAML configuration, and trajectory recording as core features. 

It does not own project authority, canon authority, lore truth, AP governance, Godot scene authority, runtime world-state authority, or MrLore safety judgment. It can execute edits only inside a provided working directory and only according to the task, allowed file list, project authority stack, and test command it receives.

Neighboring projects that depend on Trae are any repo that wants automated patch execution: MrLore, EngAIn runtime, docs, Godot projects, trixel tools, MCP bridges, and any authority-stack project that needs a mechanical code-worker. But those projects must provide authority constraints; Trae should not infer them.

## 2. CURRENT WORKING STATUS

Confirmed working from the stack:

Trae has a CLI with `run`, `interactive`, `show-config`, and `tools` commands. The `run` command accepts task text or a task file, provider/model overrides, max steps, working directory, must-patch mode, config file, trajectory file, patch path, and Docker options. 

The agent wrapper creates a `TrajectoryRecorder`, auto-generates a trajectory path when one is not supplied, instantiates `TraeAgent`, attaches the CLI console, and initializes MCP tools when allowed. 

The base execution loop is present: it starts Docker if configured, loops until `max_steps`, calls the LLM, executes tools, records steps, closes tools, stops Docker if requested, and cleans MCP clients. 

The default Trae tool set is present: `str_replace_based_edit_tool`, `sequentialthinking`, `json_edit_tool`, `task_done`, and `bash`. 

Partially working:

Docker mode exists, but depends on Docker being installed, daemon-accessible, and packaged tools existing under `trae_agent/dist`. The CLI may build those tools with PyInstaller on first use.  The Docker manager mounts the workspace into `/workspace`, copies tools into `/agent_tools`, and uses a persistent shell through `pexpect`. 

MCP exists, but only stdio transport is implemented. HTTP, WebSocket, streamable HTTP, and TCP fields exist in config shape, but the MCP client raises `NotImplementedError` for HTTP and URL modes. 

Trajectory recording is healthy at code level: it records task metadata, LLM interactions, agent steps, tool calls/results, success, final result, and execution time to JSON.  The separate trajectory document confirms intended audit/debug use and the file format. 

Untested from the 25-stack alone:

There is no provided passing test log. The `pyproject.toml` defines pytest settings and dev/test dependencies, but the uploaded stack does not prove the suite was run. 

Abandoned, legacy, or proof-only:

Legacy JSON config support remains. The README recommends YAML and points legacy JSON users to legacy docs.  The CLI also falls back from YAML to JSON when YAML is missing.  This is compatibility, not current authority.

## 3. ERROR PROFILE

Import/path errors:

Likely if invoked outside an installed package or without `PYTHONPATH=.`. The README troubleshooting section explicitly suggests `PYTHONPATH=. trae-cli run "your task"` for import errors. 

Likely if the package path and uploaded flat files are not restored into the expected `trae_agent/...` package layout. The code imports modules like `trae_agent.agent`, `trae_agent.utils.config`, and `trae_agent.tools...`; flat placement alone is not a runnable installed tree. 

Missing files:

`trae_config.yaml` is expected by default. The CLI resolves YAML first and errors if neither YAML nor JSON exists. 

Docker mode expects `trae_agent/dist` and `trae_agent/dist/_internal`; if missing, it tries to build packaged edit/json tools. 

Duplicate files:

No direct duplicate source evidence in the 25-stack. However, both `README.md` and CLI support YAML plus legacy JSON config, so duplicate config formats may confuse operators.

Stale backups:

No explicit backup files shown in this stack. Legacy config support is the main stale lane.

Schema mismatch:

OpenAI tool schemas are altered: optional parameters become required but nullable, and `additionalProperties: false` is added for strict schema compliance.  This can behave differently across providers.

The Ollama client builds tool schemas as function tools and parses Ollama tool calls into Trae `ToolCall` objects, but usage and finish reason are not available.  That means trajectory and completion logic may be thinner under Ollama.

Runtime bridge mismatch:

Trae is not an EngAIn runtime bridge. It has no `/snapshot`, `/world/sync`, Godot, ZONJ, AP mutation, or lore governance endpoint. Its runtime bridge is only tool execution plus optional MCP.

Godot scene/autoload mismatch:

Not applicable. No Godot files in this 25-stack. Any Godot authority must belong to another project.

Generated-output drift:

Patch output can drift from actual desired scope if Trae is not given an allowed file list. `get_git_diff()` writes all git diff output, or diff from `base_commit` to `HEAD`, and `must_patch` only checks whether a non-test patch exists. 

Trajectory output may include sensitive task/code context. The trajectory documentation warns that trajectory files may contain sensitive information and should be stored securely. 

Old architecture still present:

Legacy JSON config remains. Programmatic usage in the trajectory documentation appears older than current class signatures, referring to older imports/parameters such as `ModelParameters`; treat that doc section as conceptual, not exact current code authority.

## 4. CONTRADICTION PROFILE

Own role contradiction:

The README says Trae is a general software engineering agent. Its system prompt says the primary goal is to resolve a GitHub issue, reproduce the bug, patch, test, and summarize.  So Trae is broad, but its prompt is bug-fix shaped. For EngAIn use, task prompts must make its lane explicit: code-worker, not autonomous architect.

Neighboring project contradiction:

Trae can edit files and run bash, but it has no native concept of AP authority, canon tiers, MrLore stop codes, or EngAIn world-state authority. Therefore, without an inbound authority stack, it may treat all repo files as equal.

Current home/project decision contradiction:

The CLI creates the working directory if it does not exist.  That is dangerous for authority stacks because a typo in `--working-dir` may create an empty directory instead of failing. For EngAIn, wrappers should pre-validate project roots before invoking Trae.

File naming contradiction:

Tool names mix `str_replace_based_edit_tool`, `json_edit_tool`, `sequentialthinking`, and `task_done`.  The “sequentialthinking” name lacks the underscore style of the others. Not fatal, but wrappers must use exact names.

Schema names contradiction:

Config supports `mcp_servers` entries with `url`, `http_url`, `tcp`, and `headers`, but the MCP client only implements stdio `command`.  That is a schema-future mismatch.

Old vs new pipeline behavior:

YAML is recommended, but JSON fallback remains.  For EngAIn, YAML should be treated as current; JSON as legacy import only.

## 5. PROPOSED ARCHITECTURE WAITING TO BE BUILT

System name: Full MCP Transport Layer.

Files implying it: `config.py`, `mcp_client.py`, `mcp_tool.py`, `trae_agent.py`.

What exists: config schemas include stdio command, URL, HTTP URL, headers, TCP, timeout, trust, and description.  MCP tool wrapping exists.  Trae discovers MCP tools only from allowed MCP servers. 

What is missing: HTTP, WebSocket, and TCP transport implementation. Current code raises `NotImplementedError` for HTTP and URL transports. 

System name: Authority-aware EngAIn Code Worker Wrapper.

Files implying it: `cli.py`, `trae_agent.py`, `agent_prompt.py`, edit/bash/json tools.

What exists: Trae accepts task instruction, working directory, must-patch flag, patch path, and trajectory file.  It can edit text, edit JSON, run bash, and mark task done.

What is missing: built-in allowed-file enforcement, authority-stack parser, forbidden-path guard, MrLore exit-code policy, and “stop on EXIT 2” behavior.

System name: Safer Patch Gate.

Files implying it: `trae_agent.py`, `agent_prompt.py`, `task_done_tool.py`.

What exists: `must_patch=true` prevents completion when the patch is empty after removing test-only changes.  `task_done` says it should not be called before verification. 

What is missing: enforcement that tests actually ran, enforcement that changed files are allowed, enforcement that command output is attached, and enforcement that a human-review stop is honored.

## 6. INBOUND SCHEMA

Inbound item: task instruction.

Source project: human/operator or orchestrator.

Expected filename/schema name: free-text issue/task, or file passed through `--file`.

Required fields: project root path, task description, expected behavior, allowed edits, verification command.

Optional fields: base commit, patch path, trajectory path, provider/model overrides, max steps.

Failure behavior if missing: CLI exits if neither task nor `--file` is supplied. TraeAgent raises an agent error if `project_path` or issue information is missing.

Inbound item: project authority stack.

Source project: EngAIn authority docs, MrLore governance, project-specific stack profile.

Expected filename/schema name: `PROJECT_AUTHORITY_STACK.md`, `system.manifest.md`, `allowed_files.json`, or equivalent wrapper-provided text.

Required fields: owning project, forbidden files, allowed file list, human-review stops, test commands, expected outputs.

Optional fields: severity tiers, rollback instructions, patch destination, log destination.

Failure behavior if missing: Trae will behave like a normal software engineering agent and may edit any file reachable in the working directory through bash/edit tools. That is unacceptable for authority-sensitive projects.

Inbound item: allowed file list.

Source project: owning repo or orchestrator.

Expected filename/schema name: `allowed_files.json` or task prompt section.

Required fields: absolute or repo-relative paths, allowed operations per path.

Optional fields: read-only paths, create-only paths, generated-output directories.

Failure behavior if missing: edits must be limited by wrapper policy, not by Trae itself. The edit tool only validates absolute path and existence/create behavior; it does not enforce project ownership. 

Inbound item: run/test command.

Source project: owning repo.

Expected filename/schema name: task prompt field, `project_manifest`, or `Makefile` target.

Required fields: exact command, expected exit code, working directory, timeout expectation.

Optional fields: smoke command, regression command, lint command.

Failure behavior if missing: Trae’s prompt still tells the model to reproduce and test, but no concrete command is enforced. 

Inbound item: model/config routing.

Source project: `trae_config.yaml`, environment, or CLI.

Expected filename/schema name: `trae_config.yaml`.

Required fields: `model_providers`, `models`, `agents.trae_agent.model`, `max_steps`, tools.

Optional fields: lakeview, MCP servers, allow MCP servers, base URL, provider override.

Failure behavior if missing: config creation fails when providers, models, or agent configs are absent. 

## 7. OUTBOUND SCHEMA

Outbound item: changed files.

Destination project: owning repo / human reviewer.

Expected filename/schema name: git working tree diff, optional patch file from `--patch-path`.

Required fields: changed file paths, diff hunks.

Optional fields: base commit diff.

Stability level: candidate.

Evidence: `get_git_diff()` returns git diff, and `execute_task()` writes it to `patch_path` if provided. 

Outbound item: trajectory log.

Destination project: audit/debug/human review.

Expected filename/schema name: `trajectories/trajectory_YYYYMMDD_HHMMSS.json` or custom `--trajectory-file`.

Required fields: task, start/end time, provider, model, max steps, LLM interactions, agent steps, success, final result, execution time.

Optional fields: token usage, cache tokens, reasoning tokens, lakeview summary.

Stability level: stable candidate.

Evidence: trajectory recorder creates and continuously saves the JSON shape. 

Outbound item: command output.

Destination project: human reviewer / trajectory log.

Expected filename/schema name: `tool_results[]` inside trajectory.

Required fields: call id, success, result, error.

Optional fields: command-specific output, stderr, truncation notice.

Stability level: stable candidate.

Evidence: tool results serialize call id, success, result, error, and id.  Bash output may truncate through tool helpers. 

Outbound item: patch result.

Destination project: owning repo / CI / reviewer.

Expected filename/schema name: patch file via `--patch-path`.

Required fields: git diff text.

Optional fields: base commit range.

Stability level: candidate.

Evidence: patch file writing is present but only writes git diff; it does not include authority metadata or test proof by itself. 

Outbound item: task done signal.

Destination project: Trae execution loop / human CLI.

Expected filename/schema name: `task_done` tool call.

Required fields: no parameters.

Optional fields: none.

Stability level: stable.

Evidence: completion is detected by tool call name `task_done`, and the tool returns “Task done.”

## 8. AUTHORITY BOUNDARIES

Trae must stop and ask another project when:

It is asked to modify canon/lore truth, AP governance, world-state rules, project authority stacks, Tier 0 prose, generated mirrors, vault manifests, schema contracts, or runtime authority files without explicit permission.

It sees a MrLore command return `EXIT 2`. Based on your project rule, that is a successful safety stop requiring human review. Trae does not know that natively; the wrapper/task must tell it.

It finds contradictions between old and new architecture. Trae may report contradictions, but it must not resolve ownership or canon by itself.

It needs to edit outside the allowed file list.

It needs to run networked MCP, HTTP MCP, or external services not explicitly allowed.

Another project must stop and ask Trae when:

It wants Trae’s exact changed file list, command output, trajectory path, patch file, or whether `task_done` was actually called.

It wants to know whether Trae ran inside host mode or Docker mode.

It wants to replay/inspect a code-worker session.

## 9. TOP 10 QUESTIONS FOR HUMAN REVIEW

1. What exact repo root is Trae allowed to operate inside for this task?

2. What exact files may Trae edit, create, or delete?

3. Is bash allowed, and are destructive commands forbidden explicitly?

4. Is Docker mode allowed, or must execution happen on the host?

5. Are MCP servers allowed? If yes, which stdio MCP server names are allowed?

6. Which model provider should Trae use: local Ollama, Anthropic, OpenAI, OpenRouter, Google, Azure, or Doubao?

7. Is internet/network access forbidden for this project run?

8. What is the required run/test command, and what exit code means pass?

9. For MrLore: should Trae run only the approved sequence `write_changed_manifest.py → mrlore_run_changed.py → read exit code → stop on EXIT 2`?

10. What files are authority sources versus generated outputs that must never be hand-edited?

## 10. STACK VERDICT

AUTHORITY_WITH_FIX_FLAGS.

Trae is not proof-only. It has a real CLI, real tool registry, bash/edit/json tools, MCP stdio discovery, Docker execution, trajectory recording, multi-provider LLM routing, patch output, and task completion signaling.

But it is not authority-ready by itself. It lacks native project authority enforcement, allowed-file guards, MrLore exit-code semantics, AP/canon awareness, Godot awareness, and full MCP transport implementation. MCP config implies more transports than are implemented.

Clean operating verdict:

Trae is a strong repo-edit executor when wrapped by an authority stack. It should receive four things every time: task instruction, project authority stack, allowed file list, and run/test command. Its safe outbound packet should be: changed files, trajectory log, command output, patch result, and task-done signal.
