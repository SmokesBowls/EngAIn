# FACTION3D ARCHITECTURAL GAP ANALYSIS

## 🎯 WHAT YOU ALREADY HAVE (Good Foundation!)

### ✅ faction3d_kernel.gd (Pure MR Kernels)
- Canonical faction definitions (20 factions, 6 layers)
- Phase system (DORMANT/ACTIVE/ENFORCING)
- Pure functions (mr_create_snapshot, mr_set_faction_influence, etc.)
- Immutability enforced (_deep_copy)
- Bounds checking (influence -1.0 to 1.0)
- Constraint validation (non_recruitable, etc.)

**Status:** EXCELLENT - This is solid foundation

### ✅ faction3d_adapter.gd (Contract Layer)
- AP contract validation
- Delta queuing
- Contract violation logging
- Phase visibility checks

**Status:** GOOD - But missing ZW/ZON pattern

### ✅ faction3d_validator.gd (Testing)
- Immutability tests
- Determinism tests
- Contract compliance tests
- Bounds enforcement tests
- Phase coherence tests

**Status:** GOOD - But tests DIFFERENT invariants than proof

---

## ❌ WHAT'S MISSING (For 5/5 Proof)

### Missing: ZW Events (@id/@when/@where)

**Current:** Actions execute directly without temporal identity
**Needed:** Every faction operation must be a timestamped event

```gdscript
// Current (NO temporal identity):
modify_faction_influence(faction_id, delta, reason)

// Needed (WITH temporal identity):
{
    "@id": "faction/evt_12345",
    "@when": "epoch_faction:T+42.5",
    "@where": "realm/faction_hall/dragons",
    "rule_id": "influence_boost",
    "payload": {"faction": 0, "delta": 0.1}
}
```

### Missing: Event Logging

**Current:** No event log exists
**Needed:** Every operation must be logged for replay

```gdscript
// Needed in adapter:
var event_log: Array = []
var initial_snapshot: Dictionary = {}

func execute_action(...):
    # ... validate, check rules ...
    
    # LOG EVENT (missing!)
    event_log.append({
        "@id": event.id,
        "@when": event.when,
        "@where": event.where,
        "rule_id": event.rule_id,
        "payload": event.payload
    })
```

### Missing: Replay Function

**Current:** No way to rebuild state from events
**Needed:** replay_from_events() that proves kernels are pure

```gdscript
// Needed (CRITICAL for INVARIANT 2):
static func replay_from_events(initial: Dictionary, events: Array) -> Dictionary:
    var snapshot = _deep_copy(initial)
    for event_data in events:
        var event = ZWFactionEvent.new(event_data)
        var rule = rules[event.rule_id]
        snapshot = faction_influence_kernel(snapshot, event, rule)
    return snapshot
```

### Missing: AP Rules with Interrogability

**Current:** Adapter checks contracts, but doesn't explain WHY
**Needed:** Rules that return structured failure reasons

```gdscript
// Current (binary pass/fail):
if not _validate_faction_id(faction_id):
    return false

// Needed (structured explanation):
var req_check = rule.check_requires(snapshot)
if not req_check["success"]:
    return {
        "success": false,
        "reason": "requires.faction.influence >= -0.5 failed",
        "actual_value": -0.6,  // ← AI can learn from this!
        "needed": ">= -0.5"
    }
```

### Missing: Query Mode ("Would This Fail?")

**Current:** Can only discover failures by executing
**Needed:** Predict failures without executing

```gdscript
// Needed (INVARIANT 4):
func query_why_failed(rule_id: String) -> String:
    var rule = rules[rule_id]
    var check = rule.check_requires(current_snapshot)
    if not check["success"]:
        return "Would fail because: %s (actual: %s)" % [
            check["reason"], 
            check["actual_value"]
        ]
    return "Would succeed"
```

---

## 🔥 THE ARCHITECTURAL PATTERN (5/5)

### Layer 1: ZW Events (Temporal Identity)
```gdscript
class ZWFactionEvent:
    var id: String      # "@id"
    var when: String    # "@when" (epoch:T+offset)
    var where: String   # "@where" (realm/zone/location)
    var rule_id: String
    var payload: Dictionary
    
    func _init(event_data):
        assert(event_data.has("@when"))  # ← Refuses if missing!
```

### Layer 2: AP Rules (Interrogable)
```gdscript
class APRule:
    var requires: Array[Dictionary]
    var effects: Array[Dictionary]
    
    func check_requires(snapshot) -> Dictionary:
        # Returns {"success": bool, "reason": str, "actual_value": float}
```

### Layer 3: Pure Kernel
```gdscript
static func faction_influence_kernel(snapshot_in, event, rule) -> Dictionary:
    var snapshot_out = _deep_copy(snapshot_in)
    # Apply rule effects
    return snapshot_out  # Pure - no mutation!
```

### Layer 4: Adapter (Event Log + Replay)
```gdscript
class Faction3DProofAdapter:
    var event_log: Array = []
    var initial_snapshot: Dictionary = {}
    
    func execute_action(...):
        # Validate → Apply → Log → Commit
        
    func test_replay():
        var replayed = replay_from_events(initial_snapshot, event_log)
        return replayed == current_snapshot  # Must be true!
```

---

## 📊 COMPARISON: YOUR FILES vs PROOF PATTERN

| Component | Your faction3d_*.gd | Proof Pattern | Gap |
|-----------|-------------------|---------------|-----|
| **Pure Kernels** | ✅ Excellent | ✅ | None |
| **Temporal Events** | ❌ None | ✅ Required | **MISSING** |
| **Event Logging** | ❌ None | ✅ Required | **MISSING** |
| **Replay Function** | ❌ None | ✅ Required | **MISSING** |
| **AP Rules** | ⚠️ Partial | ✅ Full | **NEEDS UPGRADE** |
| **Interrogability** | ❌ None | ✅ Required | **MISSING** |
| **Query Mode** | ❌ None | ✅ Required | **MISSING** |
| **Immutability** | ✅ Good | ✅ | None |
| **Bounds Checking** | ✅ Good | ✅ | None |

---

## 🎯 WHAT TO DO

### Option A: Run Proof Test First (Recommended)

1. Install faction3d_proof_kernel.gd
2. Run test → Get actual score (0/5, 3/5, or 5/5)
3. See EXACTLY what's missing
4. Fix one invariant at a time

### Option B: Migrate Your Files Now

1. Add ZWFactionEvent to faction3d_adapter.gd
2. Add event_log storage
3. Add replay_from_events()
4. Add AP rules with interrogability
5. Then run proof test

---

## 💡 KEY INSIGHT

**Your existing code is GOOD.**

**It just doesn't follow the ZW/ZON/AP pattern yet.**

**The proof test will show you the exact gap.**

**Then you copy the pattern from Combat3D (5/5) to Faction3D.**

---

## 🔥 BOTTOM LINE

**Combat3D:** 5/5 (PROVEN)
**Faction3D:** ??? (Run test to find out!)

**Both should have 5/5 before you integrate with runtime.**

**Otherwise you're building on sand.**
