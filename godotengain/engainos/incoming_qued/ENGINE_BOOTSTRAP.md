# ENGINE_BOOTSTRAP.md

**Authority:** `core/launch_engine.py`  
**Status:** CANONICAL ENTRYPOINT  
**Rule:** Engine must be launched through this file

---

## The Bootstrap Rule

**If this fails, fix the engine - do not bypass.**

```
Tests may mock runtime.
Runtime may not mock tests.
Engine must be launched through launch_engine.py.
```

This is not a guideline. This is **law**.

---

## What launch_engine.py Does

### Phase 1: Path Authority (No CWD Assumptions)

**Locks to file location:**
```python
SCRIPT_PATH = Path(__file__).resolve()
CORE = SCRIPT_PATH.parent
ROOT = CORE.parent
```

**Why this matters:**
- No `cd` dependency
- Works from any directory
- Explicit path resolution
- No environment pollution

### Phase 2: Engine Invariants (Learning Gate)

**Checks 7 critical invariants:**

1. **Core law files exist**
   - `mesh_intake.py` (HARD GATE)
   - `mesh_manifest.py` (manifest system)
   - `scene_server.py` (HTTP server)
   - `godot_adapter.py` (Godot bridge)

2. **Directory structure**
   - `tools/` exists
   - `tools/trixel/` exists
   - `godot/` exists

3. **Boundary enforcement (CRITICAL)**
   - core/ does NOT import godot
   - core/ does NOT import tools/
   - tools/ does NOT import godot

4. **Python version**
   - Python 3.10+ required

5. **Core modules importable**
   - scene_server imports cleanly
   - godot_adapter imports cleanly

6. **Asset structure**
   - assets/ exists or created
   - assets/trixels/ exists or created

7. **Test isolation**
   - core/ does NOT import tests/

**If any invariant fails → EXIT HARD**

### Phase 3: Subsystem Startup (Explicit)

**Starts in order:**
1. Scene HTTP server (port 8765, background thread)
2. Godot adapter (stdin/stdout bridge, foreground)
3. Optional scene load (from CLI arg or default)

**Each step validated before proceeding.**

### Phase 4: Runtime Loop

**Godot adapter runs in main thread:**
- Handles stdin/stdout with Godot
- Scene server handles HTTP requests
- Both coordinate via shared state

---

## Why This Replaces "Todays Lunch"

### The Original Test

**Setup (pre-20-day absence):**
- Rename `launch_bridge.py` → `todays lunch`
- Leave in `core/` with no extension
- Test: Does AI inspect or assume?

**Result:**
- ✅ AI inspected contents first
- ✅ AI didn't delete based on name
- ✅ AI flagged for review
- ✅ Test PASSED

### The Evolution

**"Todays lunch" was:**
- A disguised test
- A learning trap
- Intentionally confusing

**`launch_engine.py` is:**
- The final form
- Authoritative
- Explicit and boring

**Why the transition:**
- Test phase complete
- Authority needs to be obvious
- New agents need clear entrypoint
- No more disguises

---

## The Learning Gate (Critical Feature)

### What It Enforces

**A new chat/agent MUST:**
1. Understand directory structure
2. Respect import boundaries
3. Know what files are critical
4. Run validation before extending

**Cannot:**
- Bypass bootstrap
- Run subsystems independently
- Violate boundaries
- Mock runtime from tests

### Why This Matters

**Without this gate:**
- Tests can run without runtime
- Godot can start without Python
- Scripts run with wrong assumptions
- Nothing forces learning

**With this gate:**
- Engine must be understood before extending
- Violations fail immediately
- Learning is enforced, not optional
- Reality-driven development mandated

---

## Usage

### Normal Usage
```bash
# From anywhere
python3 path/to/engainos/core/launch_engine.py

# With specific scene
python3 core/launch_engine.py game_scenes/my_scene.json

# Default scene (test_scene.json)
python3 core/launch_engine.py
```

### What You'll See
```
======================================================================
ENGAIN ENGINE BOOTSTRAP
======================================================================
Authority: /path/to/core/launch_engine.py
Root:      /path/to/engainos
Core:      /path/to/engainos/core
Tools:     /path/to/engainos/tools
Godot:     /path/to/engainos/godot
======================================================================

[PHASE 2] Checking engine invariants...

  [1/7] Core law files...
  ✓ All core law files present
  [2/7] Directory structure...
  ✓ Required directories present
  [3/7] Import boundaries (CRITICAL)...
  ✓ Boundaries clean: core ← tools ← godot
  [4/7] Python version...
  ✓ Python 3.10.12
  [5/7] Core module imports...
  ✓ Core modules importable
  [6/7] Asset structure...
  ✓ Asset structure ready
  [7/7] Test isolation...
  ✓ Tests isolated from runtime

✓ All engine invariants verified

[PHASE 3] Starting subsystems...

  [1/2] Scene HTTP server (port 8765)...
  ✓ Scene server running on port 8765

  [2/2] Godot adapter (stdin/stdout bridge)...
  ✓ Loading default scene: test_scene.json
  ✓ Scene initialized

======================================================================
ENGINE READY
======================================================================

Subsystems:
  • Scene server:   http://localhost:8765/
  • Godot adapter:  stdin/stdout bridge active
  • Scene loaded:   test_scene.json

To stop: Ctrl+C
======================================================================
```

### If Something Fails
```
❌ ENGINE INVARIANT VIOLATION:
   mesh_intake.py missing - this is the HARD GATE
   Fix the engine before proceeding.
```

**Do not bypass. Fix the actual problem.**

---

## Relationship to Other Files

### vs launch_bridge.py (Historical)

**`launch_bridge.py`:**
- Original working version
- Lives in core/
- Still functional
- Historical reference

**`launch_engine.py`:**
- Canonical authority
- Adds invariant checking
- Explicit path locking
- Learning gate enforcement

**Keep both:**
- `launch_bridge.py` = proof of concept
- `launch_engine.py` = production entrypoint

### vs Tests

**Tests are separate:**
- Tests can run without runtime
- Tests can mock subsystems
- Tests validate components

**Runtime is authoritative:**
- Runtime cannot run without validation
- Runtime cannot mock tests
- Runtime validates system

**The rule:**
```
Tests may mock runtime.
Runtime may not mock tests.
```

### vs Godot

**Godot is downstream:**
- Godot receives from Python
- Godot never starts Python
- Godot is render + input only

**launch_engine.py starts:**
- Python runtime
- Godot bridge
- HTTP server

**Godot opens project:**
- Connects to existing Python
- Never launches Python
- Overlay only

---

## Maintenance

### When to Update This File

**DO update when:**
- Adding new critical subsystem
- Adding new invariant check
- Changing startup order
- Adding new boundary rule

**DON'T update for:**
- Feature additions to subsystems
- Test additions
- Documentation changes
- Non-critical utilities

### How to Add Invariants

```python
# Add to PHASE 2, numbered sequence
print("  [N/7] New invariant description...")
assert_invariant(
    your_condition_here,
    "Failure message explaining what's wrong"
)
print("  ✓ New invariant verified")
```

### Invariant Design Rules

**Good invariants:**
- Fast to check (< 1 second)
- Fail with clear message
- Structural, not behavioral
- Required for engine to work

**Bad invariants:**
- Slow validation
- Vague error messages
- Style preferences
- Optional features

---

## The 20-Day Gap Closure

### What Was Missing

**Before 20-day absence:**
- Critical file disguised as "todays lunch"
- Test: Would AI inspect or assume?
- No canonical entrypoint
- No invariant enforcement

**During 20-day absence:**
- System could be extended without understanding
- No learning gate
- Authority unclear

**After return (now):**
- Test validated (AI inspected correctly)
- Authority restored
- Learning gate implemented
- Bootstrap canonical

### What This Completes

**The original lesson:**
> "If you don't understand how the engine starts, you don't get to extend it."

**Now enforced by:**
- Explicit invariant checks
- Hard failures on violations
- Clear authority hierarchy
- Cannot bypass validation

---

## For Future AI Agents

### If You're Reading This

You are probably a new AI agent asked to work on EngAIn.

**Before you do ANYTHING:**

1. **Read this file completely**
2. **Run:** `python3 core/launch_engine.py`
3. **If it fails:** Fix what it tells you to fix
4. **If it succeeds:** You now understand the engine structure

**Do not:**
- Skip the bootstrap
- Bypass invariants
- Run subsystems independently
- Assume you understand without running

**The test:**
If you can't make `launch_engine.py` succeed, you don't understand the engine yet. That's okay. Fix the problems it identifies, then proceed.

---

## Status

**Current:** CANONICAL ENTRYPOINT  
**Historical:** Evolved from "todays lunch" test  
**Authority:** This is the only blessed way to start EngAIn  
**Enforcement:** Invariants + documentation  
**Evolution:** Update when adding critical subsystems only

---

## Final Note

**This file is boring on purpose.**

No tricks. No disguises. No clever names.

Just:
1. Lock paths
2. Check invariants
3. Start subsystems
4. Run loop

**If this is boring, you're doing it right.**

The cleverness was in the test phase.  
The authority is in the execution.

---

**Date:** 2026-01-18  
**Replaces:** "todays lunch" test (completed)  
**Authority:** CANONICAL  
**Status:** LOCKED
