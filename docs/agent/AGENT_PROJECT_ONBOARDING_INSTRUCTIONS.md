# EngAIn Agent Project Onboarding Instructions

Purpose: give every agent a repeatable way to understand EngAIn before writing code.

This file belongs at:

```text
/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/docs/agent/AGENT_PROJECT_ONBOARDING_INSTRUCTIONS.md
```

Use this file before making patches. The goal is to stop agents from guessing, editing stale files, touching the wrong authority lane, or confusing generated/cache files with active project code.

---

## 0.1 TIER / Lane Authority Rule

TIER means system-wide authority rank.

Lane means ordered work boundary.

Stack means implementation family.

TIER names must always be written in caps:

```text
TIER1
TIER2
TIER3
```

If an agent does not know what lane it is in, work must stop.

Unknown lane state is:

```text
BLOCKED_PENDING_TIER1_LANE_ASSIGNMENT
```

Authority routing:

```text
Inside EngAIn declared/runtime truth, ask EngAInOS TIER1.
Inside Trixel art/asset truth, ask Trixel TIER1.
```

Do not guess lane placement.
Do not self-assign authority.
Do not continue a refactor from an unknown lane.


## 0. Prime Rule

Do not write code before you identify:

```text
1. Which project/system owns the bug.
2. Which file owns the behavior.
3. Which contract controls the behavior.
4. Which files are runtime authority and which are client/view adapters.
5. Whether the apparent failure is sync/timing, schema/contract, render, actor-spawn, or tooling noise.
6. Which TIER authority owns the lane assignment.
```
Before any edit, paste these findings into your response:
1. Active repo root:
2. Dirty files:
3. Owning system:
4. Owning file:
5. Contract/doc consulted:
6. Exact proof line from log or code:
7. Planned files to edit:
8. Verification command:
A patch is not valid just because it parses. It must preserve the lane boundary.

---

## 1. Workspace Safety Start

Always begin from the EngAIn root:

```bash
cd /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn
```

Then run:

```bash
git status --short
```

Before editing, identify the changed files. If the workspace is already dirty, do not overwrite blindly. Inspect the relevant modified files first.

Recommended:

```bash
git diff --stat
git diff -- <path/to/file>
```

If the user says a file was changed by another agent, read the live file from disk, not a cached copy, not memory, not an old pasted version.

---

## 2. Files and Folders Agents Must Know

### Root project docs

Read these first when present:

```text
docs/REGISTRY_INSTRUCTIONS.md
docs/BOOLEAN_SWITCH_REGISTRY_RAW.md
docs/BOOLEAN_SWITCH_REGISTRY_CURATED.md
docs/agent/AGENT_PROJECT_ONBOARDING_INSTRUCTIONS.md
```

Read before editing code:

```text
docs/REGISTRY_INSTRUCTIONS.md
docs/BOOLEAN_SWITCH_REGISTRY_CURATED.md
docs/BOOLEAN_SWITCH_REGISTRY_RAW.md
```

Before changing behavior, agents must check whether the behavior is controlled by a documented switch, state flag, policy gate, operation result, or contract validation function.

Root docs are for cross-system contracts and shared governance.

### Godot semantic client

Primary path:

```text
godotnew/semantic/
```

Important files:

```text
godotnew/semantic/Main.gd
godotnew/semantic/Mainline.tscn
godotnew/semantic/project.godot

godotnew/semantic/scripts/Boot.gd
godotnew/semantic/scripts/SceneTransitionBouncer.gd
godotnew/semantic/scripts/SemanticRenderer.gd
godotnew/semantic/scripts/SemanticActor.gd
godotnew/semantic/scripts/PlacementPacketRenderer.gd
godotnew/semantic/scripts/LayoutAnchorRenderer.gd

godotnew/semantic/autoload/SimClient.gd
godotnew/semantic/autoload/SceneClient.gd
godotnew/semantic/autoload/VaultClient.gd
godotnew/semantic/autoload/TrixelTileClient.gd

godotnew/semantic/trixel/TrixelEnvironmentPlanner.gd
godotnew/semantic/trixel/RenderPolicy.gd
```

Current known authority boundary:

```text
Main.gd owns snapshot hydration.
Boot.gd may observe command/look but must not spawn or warn from look when Main owns hydration.
SceneTransitionBouncer.gd owns transition gate validation.
SemanticRenderer.gd owns visual terrain/marker rendering.
$World/Actors is the gameplay actor lane.
Runtime 8080 owns authoritative scene/snapshot data.
```

### GodotSim runtime

Primary path:

```text
godotsim/
```

Important files vary, but look for:

```text
godotsim/sim_runtime.py
godotsim/scene_manager.py
godotsim/bridge_integration.py
godotsim/http_handlers.py
godotsim/runtime_core.py
godotsim/data/beach_scene.json
```

Runtime lane rule:

```text
Do not patch runtime when the log proves runtime already publishes the correct snapshot/bridge_entities.
Do not patch Godot client when runtime schema is actually missing data.
First prove which side owns the failure.
```

### EngAInOS / other systems

If present:

```text
godotengain/engainos/
```

Read local docs before editing:

```text
godotengain/engainos/docs/
```

Root docs only define shared contracts. System docs explain local operation.

---

## 3. Files and Folders to Avoid Unless Explicitly Asked

Do not use these as source-of-truth code:

```text
_quarantine/
.engain_cache/
__pycache__/
node_modules/
venv/
vent/
lib/python*/site-packages/
lib64/python*/site-packages/
*.pyc
```

Do not use `Downloads` paths as active runtime paths unless the user explicitly says to inspect an archive.

Known bad/noisy patterns:

```text
/home/mytruelove/Downloads/...
/run/media/... old vault copies
_quarantine/generated/...
```

These can appear in grep results. They are not automatically active project files.

---

## 4. First Commands to Learn a System

From EngAIn root:

```bash
pwd
git status --short
find . -maxdepth 2 -type d | sort
```

For Godot semantic client:

```bash
find godotnew/semantic -maxdepth 3 -type f \
  \( -name '*.gd' -o -name '*.tscn' -o -name '*.godot' -o -name '*.json' -o -name '*.md' \) \
  | grep -vE '/(venv|vent|__pycache__|\.godot|\.import)/' \
  | sort
```

For runtime:

```bash
find godotsim -maxdepth 3 -type f \
  \( -name '*.py' -o -name '*.json' -o -name '*.md' -o -name '*.sh' \) \
  | grep -vE '/(__pycache__|_quarantine|node_modules|venv|vent)/' \
  | sort
```

Search for a symbol:

```bash
grep -RIn "main_owns_snapshot_hydration" godotnew/semantic --include='*.gd'
grep -RIn "bridge_entities_scene_id" godotnew/semantic godotsim --include='*.gd' --include='*.py'
grep -RIn "snapshot_synced" godotnew/semantic --include='*.gd'
```

Search but exclude noise:

```bash
grep -RInE "pattern_here" godotnew/semantic godotsim \
  --include='*.gd' --include='*.py' --include='*.json' --include='*.md' \
  --exclude-dir='__pycache__' \
  --exclude-dir='.git' \
  --exclude-dir='_quarantine' \
  --exclude-dir='node_modules' \
  --exclude-dir='.engain_cache' \
  --exclude-dir='venv' \
  --exclude-dir='vent'
```

If `rg` is installed, prefer:

```bash
rg -n "pattern_here" godotnew/semantic godotsim \
  -g '*.gd' -g '*.py' -g '*.json' -g '*.md' \
  -g '!**/venv/**' -g '!**/vent/**' -g '!**/_quarantine/**' \
  -g '!**/node_modules/**' -g '!**/__pycache__/**' -g '!**/.engain_cache/**'
```

---

## 5. How to Read Code Before Editing

When assigned a bug, do this order:

```text
1. Read the latest log.
2. Identify the strongest proof line.
3. Search the exact log string in code.
4. Read the function around that print.
5. Search who calls that function.
6. Search who owns the state variable or gate.
7. Read the registry docs for true/false controls.
8. Decide the lane: runtime, client, renderer, actor, UI, transition, docs, or tooling.
```

Useful commands:

```bash
grep -RIn "exact log text" godotnew/semantic godotsim --include='*.gd' --include='*.py'
```

Show context around a line:

```bash
nl -ba godotnew/semantic/Main.gd | sed -n '500,590p'
```

Find callers:

```bash
grep -RIn "_inject_synced_entities" godotnew/semantic --include='*.gd'
grep -RIn "_spawn_bridge_entity" godotnew/semantic --include='*.gd'
```

Read signal connections:

```bash
grep -RIn "connect\|emit\|signal" godotnew/semantic --include='*.gd'
```

Read autoloads:

```bash
grep -n "autoload" -A40 godotnew/semantic/project.godot
```

---

## 6. How to Use the Boolean Registry

Registry docs live at:

```text
docs/REGISTRY_INSTRUCTIONS.md
docs/BOOLEAN_SWITCH_REGISTRY_RAW.md
docs/BOOLEAN_SWITCH_REGISTRY_CURATED.md
```

Rule:

```text
RAW = machine harvest.
CURATED = contract for agents.
```

Do not treat every `true` or `false` as a switch.

Categories:

```text
1. Real Switches
2. Debug Flags
3. Internal State Flags
4. Policy Gates
5. Operation Result Booleans
6. Contract Validation Functions
```

Before changing a boolean, answer:

```text
Is it safe to change manually?
Is it a debug override or internal state?
Is it an authority contract?
Does changing it reopen a previous fixed bug?
```

Examples:

```text
main_owns_snapshot_hydration() -> true
Do not flip casually. This protects Boot/Main ownership.

_auto flags in Boot.gd
May be config switches, but changing them can affect startup behavior.

_is_spawnable_by_world_rules(...)
Policy gate. Do not bypass in production. Use a named debug flag if profiling.
```

Regenerate raw registry only with dependency exclusions.

---

## 7. Known Current Godot Semantic Contracts

### Scene load authority chain

```text
Chooser
→ SceneClient
→ Scene Server 8765
→ SimClient
→ Runtime 8080
→ SceneManager activation
→ BridgeIntegration
→ snapshot.bridge_entities
→ Main ownership gate
→ Renderer/Actor hydration
```

### Snapshot ownership gate

Main must not hydrate until:

```text
payload.scene_id == expected_scene_id
payload.bridge_entities_scene_id == expected_scene_id
```

### Boot/Main split

Boot may issue `look` and print text. Boot must not spawn or declare render failure when Main owns snapshot hydration.

Required behavior:

```text
[boot] look response observed; Main owns snapshot hydration, so Boot will not spawn or warn from look.
```

### Transition bouncer

Old async callbacks must be ignored by token.

Healthy log:

```text
[Main] Ignoring stale TERRAIN_LAYOUT_READY continuation. expected_token=3 got=1
[Main] Ignoring stale TERRAIN_LAYOUT_READY continuation. expected_token=3 got=2
[Main] Bouncer SNAPSHOT_SYNCED passed. Hydrating entities...
```

Hydration should happen once per selected scene.

### Actor and renderer lanes

```text
SemanticRenderer/RuntimeEntities = visual semantic markers
$World/Actors = interactive gameplay actors/capsules
```

Do not confuse marker injection with actor spawning.

### World rules

If bridge entities exist but fewer actors spawn, check:

```text
[Main][BRIDGE_SPAWN_SUMMARY]
```

If `skipped_non_spawnable` is nonzero, the world-rules policy is blocking the entity. That is not a runtime failure.

---

## 8. Verification Commands Before and After Patches

Godot parse/check:

```bash
cd /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn
godot --headless --path godotnew/semantic --quit --check-only
```

Godot normal run:

```bash
cd /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/godotnew/semantic
godot --path .
```

Runtime server check:

```bash
ss -ltnp | grep ':8080'
```

Runtime start, if using GodotSim:

```bash
cd /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/godotsim
python3 sim_runtime.py
```

Snapshot test:

```bash
curl -s http://127.0.0.1:8080/snapshot > /tmp/engain_snapshot.json
python3 - <<'PY'
import json
from pathlib import Path
p = json.loads(Path('/tmp/engain_snapshot.json').read_text())
payload = p.get('payload', p)
print('scene_id:', payload.get('scene_id'))
print('bridge_entities_scene_id:', payload.get('bridge_entities_scene_id'))
print('bridge_entities:', len(payload.get('bridge_entities', [])))
PY
```

Use `/tmp` only for throwaway command output. Do not store durable project docs in `/tmp`.

---

## 9. How to Patch Safely

Prefer targeted patches over wholesale replacement.

Before patching:

```bash
git status --short
cp path/to/file path/to/file.bak_agent_$(date +%Y%m%d_%H%M%S)
```

Patch only the owning file. Do not edit multiple lanes unless the contract requires it.

After patching:

```bash
git diff -- path/to/file
godot --headless --path godotnew/semantic --quit --check-only
```

For Python:

```bash
python3 -m py_compile path/to/file.py
```

Never claim a runtime behavior is fixed from parse-check alone. Parse-check means syntax survived. A live log proves behavior.

---

## 10. When to Stop and Ask for a Log

Stop patching and request/run a live log when:

```text
The code parses but behavior is unknown.
The bug is timing/synchronization related.
The failure depends on runtime server state.
The fix touches scene transition, snapshot polling, or actor hydration.
```

Look for proof lines, not vibes.

Examples of proof lines:

```text
payload.scene_id:
payload.bridge_entities_scene_id:
expected:
Bouncer SNAPSHOT_SYNCED passed
Ignoring stale TERRAIN_LAYOUT_READY continuation
Fallback bridge entities count
BRIDGE_SPAWN_SUMMARY
Spawned capsule actor
```

---

## 11. Agent Report Format

Every agent report should include:

```text
Changed files:
- path/to/file

What changed:
- precise bullet list

What was preserved:
- authority boundaries not touched
- files intentionally not touched

Verification command:
- exact command run

Verification result:
- exit code
- key log lines

Next recommended test:
- exact scene sequence or command
```

Do not say “fixed” unless a behavior log proves it. Say “patched” after code changes and “confirmed” after live verification.

---

## 12. Current Known Good Scene Test

Useful stress test for scene transition race protection:

```text
058 → 001 → 002
```

Healthy expected results:

```text
stale old token continuations ignored
snapshot ownership matches selected scene
SNAPSHOT_SYNCED hydration happens once
bridge_entities count appears
capsule actors spawn under $World/Actors
Boot does not spawn from look
```

---

## 13. Do Not Reopen Fixed Bugs

Do not undo these fixes:

```text
Main owns snapshot hydration.
Boot backs off from spawning/warning during Main-owned hydration.
Main checks payload.scene_id and payload.bridge_entities_scene_id before hydration.
HTTPRequest nodes are freed after snapshot polling.
Movement is blocked while chooser UI is visible.
Old transition coroutines re-check active token before continuing.
Actor spawning is separate from renderer marker injection.
```

Changing these without a new contract is regression risk.

---

## 14. Human Rule

The user may not code. Give exact commands, exact file paths, exact functions, exact snippets, and exact expected output. Do not provide vague instructions.

