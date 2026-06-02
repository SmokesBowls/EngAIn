# OKArchitect Project Brief: EngAIn

**Last Updated:** December 2025  
**Status:** 4-subsystem integration validated, Godot integration next

---

## Core Mission

**EngAIn = AI Game Engine**  
Build games from text descriptions. AI understands intent, generates logic, validates constraints. Art is optional (placeholders work). The engine that thinks like a dungeon master.

---

## Architecture (The Unified Stack)

### The 3-Layer Pattern (Used Everywhere)
```
Layer 1: MR Kernel (Pure Functional)
├── Immutable data structures (frozen dataclasses)
├── snapshot-in → snapshot-out
├── No side effects, deterministic
└── Portable to C++/Rust/GDExtension

Layer 2: Deep Contract / Adapter
├── State persistence (_state_slice)
├── Two-phase execution (queue → execute)
├── AP pre/post validation with rollback
└── Delta queuing and routing

Layer 3: Integration
├── Subsystems communicate via deltas
├── ZON4D manages canonical state
└── Godot renders visual representation
```

**EVERY subsystem follows this pattern. No exceptions.**

---

## The 4 Core Subsystems (Validated & Working)

### 1. Spatial3D
**Purpose:** Physics, movement, collision  
**Files:** `spatial3d_mr.py` (kernel), `spatial3d_adapter.py` (adapter)  
**Status:** ✅ Validated with full test suite

**Key Features:**
- Gravity, velocity, bounds checking
- Collision detection (sphere-based)
- Entity spawning/despawning
- AP constraint: No entity overlap (currently disabled for testing)

---

### 2. Perception3D
**Purpose:** Vision, hearing, memory  
**Files:** `perception_mr.py` (kernel), `perception_adapter.py` (adapter)  
**Status:** ✅ Validated with full test suite

**Key Features:**
- Line-of-sight calculations
- Field-of-view constraints
- Memory decay (certainty degrades over time)
- Tracks "last seen" positions

---

### 3. Navigation3D
**Purpose:** Pathfinding, obstacle avoidance  
**Files:** `navigation_mr.py` (kernel), `navigation_adapter.py` (adapter)  
**Status:** ✅ Validated with full test suite

**Key Features:**
- A* pathfinding algorithm
- Grid-based navigation (NavGrid)
- Obstacle detection from Spatial3D
- Path request/response deltas

---

### 4. Behavior3D
**Purpose:** AI decision-making (FSM)  
**Files:** `behavior_mr.py` (kernel), `behavior_adapter.py` (adapter)  
**Status:** ✅ Validated with integration test

**Key Features:**
- FSM states: IDLE, PATROL, CHASE, ATTACK, FLEE, SEARCH
- Observes world via Perception3D
- Requests paths via Navigation3D
- Emits action deltas

---

## The 4-Subsystem Integration Loop (PROVEN)

```python
for tick in range(simulation_ticks):
    # 1. Update perception from spatial state
    perception.set_spatial_state(spatial_snapshot)
    perception_deltas = perception.perception_step(tick)
    
    # 2. Update behavior from all subsystems
    behavior.set_spatial_state(spatial_snapshot)
    behavior.set_perception_state(perception_snapshot)
    behavior.set_navigation_state(navigation_snapshot)
    behavior_deltas = behavior.behavior_step(tick, delta_time)
    
    # 3. Route behavior deltas to navigation
    for delta in behavior_deltas:
        if delta.type.startswith("navigation3d/"):
            navigation.request_path(...)
    
    # 4. Process navigation requests
    nav_deltas = navigation.navigation_step(tick)
    
    # 5. Apply physics
    spatial.physics_step(delta_time)
```

**Status:** Runs cleanly for 10+ ticks, all subsystems communicating via deltas, no exceptions.

---

## Key Protocols & Technologies

### ZW (Ziegel Wagga) - The Anti-JSON Protocol
**Purpose:** Semantic data compression that preserves meaning

**Philosophy:**
- Structure-over-labels (meaning from consistency, not field names)
- Schema-agnostic (self-negotiating)
- Profile-aware (content shifts based on context)
- 3x character compression, 1.7x token compression vs JSON

**Example:**
```
{perception.guard
    vision_range: 20
    fov: 140deg
    height_offset: 1.6
    tags.ignore: [decor]
}
```

**Never use JSON as authority. ZW → ZON → ZONB is the pipeline.**

---

### ZON (Canonical Object Notation)
**Purpose:** Temporal snapshots with metadata

**Structure:**
```
#ZON domain/subsystem version
@id: canonical_name
@scope: domain

=section_name
key: value
nested.key: value
=end
```

**ZON4D = ZON + 4th dimension (time)**  
Enables temporal queries, rollback, time travel.

---

### AP (Anti-Python) - Declarative Constraints
**Purpose:** Rules that CANNOT be violated

**Philosophy:**
- Declarative, not procedural (what, not how)
- Pre/post validation (check before queue, check after kernel)
- Rollback on violation (restore old state)
- Canonical validation layer

**Example:**
```python
# AP constraint in adapter
valid, msg = validate_ap_constraint(snapshot_out)
if not valid:
    self._state_slice = old_state  # ROLLBACK
    raise APViolation(msg)
```

**AP is law. Never bypass it.**

---

### ZONB (ZON Binary)
**Purpose:** Compressed binary format for ZON snapshots

**Benefits:**
- ~3x compression vs JSON
- Preserves semantic relationships
- Fast load/save
- Network-efficient

---

## Non-Negotiable Laws

### 1. Pure Functional Kernels
```python
# ALWAYS:
@dataclass(frozen=True)  # Immutable
class State:
    ...

def step_kernel(snapshot_in, deltas, config):
    # No side effects
    # No mutations
    # Deterministic
    return snapshot_out, accepted_ids, alerts
```

**Never mutate inputs. Always return new state.**

---

### 2. Two-Phase Execution
```python
# Phase 1: Queue (handle_delta)
def handle_delta(self, delta_type: str, payload: dict):
    # AP pre-validation
    # Queue for processing
    # Does NOT mutate _state_slice yet
    
# Phase 2: Execute (step function)  
def step(self, delta_time: float):
    # Call mr kernel
    # AP post-validation
    # Update _state_slice
    # Clear queue
```

**Never skip phases. Never mutate in Phase 1.**

---

### 3. No JSON as Authority
```python
# WRONG:
config = json.load("config.json")

# RIGHT:
config = ZWParser.load("config.zw")
config = ZONLoader.load("config.zon")
```

**JSON is transport format ONLY. ZW/ZON are semantic formats.**

---

### 4. AP is Canonical
```python
# ALWAYS validate AP constraints
# ALWAYS rollback on violation
# NEVER bypass AP layer

valid, msg = validate_constraint(state)
if not valid:
    restore_previous_state()
    raise APViolation(msg)
```

**AP violations are non-negotiable. Rollback, don't patch.**

---

### 5. MR vs Adapter Separation
```
MR Kernel:
- Pure functions
- No state ownership
- Portable across languages

Adapter:
- Owns state (_state_slice)
- Handles AP validation
- Manages delta queuing
```

**Never mix concerns. Keep layers separate.**

---

## Current State (What Works)

### ✅ Validated & Operational
- **4-subsystem integration test** (`test_behavior3d_integration.py`)
- **Spatial3D:** Entity spawning, physics, collision
- **Perception3D:** LOS, FOV, memory decay
- **Navigation3D:** A* pathfinding, obstacle avoidance
- **Behavior3D:** FSM with patrol/chase/attack states
- **Delta routing:** All subsystems communicating
- **AP validation:** Rollback on constraint violation (tested)

### 🔄 In Progress
- **Scene loading:** Narrative → entity spawns → behavior configs
- **ZW/ZON config system:** Replace JSON thinking
- **Godot integration:** Render simulation as placeholders

### 📋 Next Steps
- **Combat3D subsystem:** Damage, hitboxes, cooldowns
- **ZON4D temporal binding:** Make subsystems time-aware
- **Task system integration:** Connect to TaskRouter
- **Godot visualization:** Cubes moving based on simulation

---

## File Locations

### Validated Code
```
~/Downloads/EngAIn/zonengine4d/zon4d/sim/
├── spatial3d_mr.py ✅
├── spatial3d_adapter.py ✅
├── perception_mr.py ✅
├── perception_adapter.py ✅
├── navigation_mr.py ✅
├── navigation_adapter.py ✅
├── behavior_mr.py ✅
├── behavior_adapter.py ✅
├── test_spatial3d.py ✅
├── test_perception.py ✅
├── test_behavior3d_integration.py ✅
└── sim_imports.py ✅
```

### Specs & Documentation
```
/mnt/project/
├── deep_obsidian.txt (ZW philosophy)
├── obsidian_to_godot.txt (Pipeline overview)
├── build-the-game.txt (7700-line blueprint)
├── ZW_white_paper.txt (ZW spec)
├── ZON4D_Temporal_Law_v1_0_zwdoc.txt (ZON4D spec)
└── zw_framework.txt (Core architecture)
```

---

## When Answering Questions

### Always Consider:
1. **Does this follow the 3-layer pattern?**
2. **Is the kernel pure functional?**
3. **Does the adapter validate AP constraints?**
4. **Would this work with ZW/ZON or does it assume JSON?**
5. **Is state immutable in the kernel?**

### Red Flags:
- ❌ Mutable state in kernels
- ❌ Side effects in step functions
- ❌ JSON as canonical format
- ❌ Bypassing AP validation
- ❌ Mixing kernel and adapter concerns

### Green Flags:
- ✅ Immutable dataclasses with frozen=True
- ✅ snapshot-in → snapshot-out pattern
- ✅ Two-phase execution (queue → execute)
- ✅ AP pre/post validation
- ✅ ZW/ZON for configuration

---

## Success Criteria

**An EngAIn subsystem is complete when:**
1. MR kernel has pure functional tests (determinism verified)
2. Adapter has AP validation with rollback
3. Integration test shows delta communication working
4. Code follows proven patterns from existing subsystems
5. No JSON anywhere in the pipeline

**The engine succeeds when:**
- Text description → playable scene (even with cubes)
- AI agents make decisions based on world state
- All logic is deterministic and replayable
- Art is optional (placeholders prove logic works)

---

## Philosophy (The Core Belief)

> "EngAIn is an engine that understands what you mean."

Not "what you code." Not "what you model."  
**What you mean.**

Every other engine requires translation.  
EngAIn just listens.

**This is the first engine built for AI authorship, not human authorship.**

---

**When in doubt, check existing subsystems. The pattern is proven. Follow it.**
