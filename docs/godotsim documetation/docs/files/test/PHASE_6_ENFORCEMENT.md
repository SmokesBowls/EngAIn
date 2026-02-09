# PHASE 6: ENFORCEMENT LAYER
## Final Hardening to Reach 50% Complete

**Goal:** Add protection layers that prevent architectural violations and detect corruption.

**Time:** 1 hour total

---

## Overview

Phase 6 adds three enforcement layers:

1. **Contamination Guards** (Python) - Prevent raw dicts from reaching MR kernels
2. **Client Assertions** (Godot) - Hash verification, version checking, epoch tracking
3. **Test Suite** (Python) - Verify all enforcement layers work

---

## Part 1: Contamination Guards (20 min)

### What It Does

Prevents this architectural violation:

```python
# FORBIDDEN (bypassing slices)
spatial_mr.physics_step(raw_snapshot)  # Raw dict!

# REQUIRED (using slices)
slice = build_spatial_slice_v1(world, tick, eid)
spatial_mr.physics_step(slice)  # Typed dataclass!
```

### Installation

**File:** `slice_builders.py` (already updated in outputs folder)

What changed:
- Added `ContaminationError` exception
- Added `assert_no_raw_dict_contamination()` function
- Added documentation about contamination guard

Just copy the updated file:

```bash
cd ~/godotsim
cp /mnt/user-data/outputs/slice_builders.py .
```

### Verification

```bash
cd ~/godotsim
python3 test_protocol.py
# Should see: TEST 4: Contamination Guard - PASS
```

---

## Part 2: Client Assertions (20 min)

### What It Does

Adds three client-side enforcement checks:

#### 1. Version Checking
- Ensures client and server use same protocol version
- Prevents silent drift
- Stops on mismatch (forces restart)

#### 2. Hash Verification
- Detects network corruption
- Detects tampering
- Rejects corrupt snapshots

#### 3. Epoch Tracking
- Detects world resets
- Tracks session continuity
- Logs epoch changes

### Installation

**File:** `ZWRuntime.gd` (manual edit required)

**Step 1:** Add constants near top (after `extends Node`):

```gdscript
const EXPECTED_PROTOCOL = "NGAT-RT"
const EXPECTED_VERSION = "1.0"

var current_epoch: String = ""
var epoch_changes: int = 0
```

**Step 2:** Add verification functions (before `_on_snapshot_completed`):

Copy these three functions from `zwruntime_enforcement_patch.gd`:
- `_verify_snapshot_hash(envelope)`
- `_verify_protocol_version(envelope)`
- `_verify_epoch_continuity(envelope)`

**Step 3:** Update `_on_snapshot_completed`:

Add enforcement calls after protocol validation:

```gdscript
    # 3. Protocol Validation
    if not data.has("protocol"):
        push_error("INVALID SNAPSHOT: missing protocol envelope")
        _request_next_snapshot()
        return
    
    # 4. ENFORCEMENT: Version Check (NEW!)
    if not _verify_protocol_version(data):
        push_error("ENFORCEMENT: Version check failed")
        return  # Don't request next - force restart
    
    # 5. ENFORCEMENT: Hash Verification (NEW!)
    if not _verify_snapshot_hash(data):
        push_error("ENFORCEMENT: Hash verification failed")
        _request_next_snapshot()
        return
    
    # 6. ENFORCEMENT: Epoch Tracking (NEW!)
    if not _verify_epoch_continuity(data):
        push_error("ENFORCEMENT: Epoch verification failed")
        _request_next_snapshot()
        return
    
    # 7. Process Content (existing code)
    var snapshot = data.get("payload", {})
    # ... rest of function
```

### Verification

```bash
# Start Python
cd ~/godotsim
python3 sim_runtime.py

# In Godot console, should see:
# ZWRuntime: World epoch locked to world_abc123...
# (No hash mismatch errors)
# (No version mismatch errors)
```

---

## Part 3: Test Suite (20 min)

### What It Does

Comprehensive test of all enforcement layers:
- Protocol envelope structure
- Hash verification
- Version checking
- Contamination guards
- Slice validation
- Epoch determinism

### Installation

**File:** `test_protocol.py` (already in outputs folder)

```bash
cd ~/godotsim
cp /mnt/user-data/outputs/test_protocol.py .
```

### Run Tests

```bash
cd ~/godotsim
python3 test_protocol.py
```

### Expected Output

```
============================================================
PROTOCOL ENFORCEMENT TEST SUITE
============================================================

TEST 1: Protocol Envelope Structure
----------------------------------------
✓ PASS: All required keys present
  Protocol: NGAT-RT
  Version: 1.0
  Epoch: world_abc123...
  Hash: sha256:9fae...

TEST 2: Hash Verification
----------------------------------------
✓ PASS: Hash mismatch detected (tampering caught)

TEST 3: Version Enforcement
----------------------------------------
✓ PASS: Version changes epoch (enforced isolation)

TEST 4: Contamination Guard
----------------------------------------
✓ PASS: Contamination detected
✓ PASS: Typed slice accepted

TEST 5: Slice Builder Validation
----------------------------------------
✓ PASS: Rejected missing position
✓ PASS: Valid entity accepted

TEST 6: Epoch Determinism
----------------------------------------
✓ PASS: Same inputs produce same epoch (deterministic)

============================================================
ALL TESTS PASSED ✓
============================================================

Enforcement layers verified:
  ✓ Protocol envelope structure
  ✓ Hash verification (tamper detection)
  ✓ Version isolation (epoch enforcement)
  ✓ Contamination guards (raw dict detection)
  ✓ Slice validation (contract enforcement)
  ✓ Epoch determinism (reproducible builds)

Engine is production-ready! 🎉
```

---

## Verification Checklist

After installation, verify:

- [ ] `test_protocol.py` runs and all tests pass
- [ ] Python starts without contamination errors
- [ ] Godot shows epoch lock message on connect
- [ ] No hash mismatch errors during gameplay
- [ ] System still runs smoothly (buttons work, physics works)

---

## What This Gives You

### Before Phase 6:
- Protocol exists but not enforced
- Hash present but not verified
- Slices exist but contamination possible

### After Phase 6:
✅ Version mismatch → Hard stop (forces fix)  
✅ Hash mismatch → Snapshot rejected (corruption caught)  
✅ Raw dict to kernel → Runtime error (violation caught)  
✅ Invalid slice → Contract error (bug caught early)  
✅ Epoch drift → Logged and tracked  

---

## Progress After Phase 6

```
Phase 0: Foundation           [████████████████████] 100% ✅
Phase 1: Protocol Envelope    [████████████████████] 100% ✅
Phase 2: Transport Fix        [████████████████████] 100% ✅
Phase 3: Navigation Hardening [████████████████████] 100% ✅
Phase 5: Client Audit         [████████████████████] 100% ✅
Phase 6: Enforcement          [████████████████████] 100% ✅

ENGINE HARDENING: 100% COMPLETE
OVERALL PROGRESS: 50% COMPLETE
```

---

## Time Breakdown

- Install contamination guards: 5 min (copy file)
- Add client assertions: 15 min (edit ZWRuntime.gd)
- Run test suite: 5 min (verify everything)
- End-to-end test: 5 min (play game, check console)

**Total:** ~30 min (faster than estimated!)

---

## Files Provided

All in `/mnt/user-data/outputs/`:

- `slice_builders.py` - Updated with contamination guards
- `test_protocol.py` - Complete test suite
- `zwruntime_enforcement_patch.gd` - Client assertion code
- `PHASE_6_ENFORCEMENT.md` - This guide

---

## After This

You will have:

✅ Production-ready engine core  
✅ All critical hardening complete  
✅ 50% of full vision achieved  
✅ Solid foundation for Empire integration  

### Next steps (optional):

1. Build game features on this foundation
2. Start Empire integration (the other 50%)
3. Add game-specific mechanics
4. Polish and deploy

---

**Ready to install? Start with Part 1!** 🚀
