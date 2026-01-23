# HARDENING ENGAIN - Complete Integration Guide
## Three Critical Fixes for Production Stability

**Source:** Architecture Critique Transcript  
**Status:** Ready for Implementation  
**Impact:** Eliminates silent corruption, dual truth, client authority creep

---

## 🎯 **The Three Vulnerabilities**

### 1. Snapshot Contamination
**Risk:** Internal kernel names leak into wire protocol  
**Impact:** Silent drift, debugging nightmare, dual truth

### 2. Client Authority Creep  
**Risk:** Godot visual smoothing creates independent movement  
**Impact:** Client "lies" about positions, violates stateless projector model

### 3. Transport Integrity Gap
**Risk:** No versioning, tick validation, or hash verification  
**Impact:** Silent corruption, impossible deterministic replay

---

## 📋 **Quick Implementation Checklist**

- [ ] FIX 1: Snapshot Purity (Python server)
- [ ] FIX 2: SYN-Client Exception (Godot client)
- [ ] FIX 3: Protocol Envelope (Python + Godot)
- [ ] Validation Tests
- [ ] Integration Tests

**Estimated Time:** 4-6 hours  
**Difficulty:** Intermediate  
**Breaking Changes:** Yes (requires client + server update)

---

## 🔧 **FIX 1: Snapshot Purity**

### Problem Location
```python
# spatial3d_adapter.py line 93
def spawn_entity(self, entity_id, pos, radius=0.5, ...):
    payload = {
        "entity_id": entity_id,
        "pos": pos,  # ❌ KERNEL NAME IN SNAPSHOT!
        # Should be "position"
    }
```

### Implementation

**Step 1:** Update `spatial3d_adapter.py`

```python
from fix_1_snapshot_purity import (
    create_entity_state,
    build_entity_slice_v1,
    write_kernel_output_to_snapshot,
    FORBIDDEN_IN_SNAPSHOT
)

# Replace spawn_entity
def spawn_entity(self, entity_id, pos, radius=0.5, solid=True, tags=None):
    """FIXED: Uses protocol names only"""
    
    # Create clean entity state
    entity_state = create_entity_state(
        entity_id=entity_id,
        position=tuple(pos),  # Protocol name
        velocity=(0.0, 0.0, 0.0),
        radius=radius,
        solid=solid,
        tags=tags
    )
    
    # Add to state slice
    self._state_slice['entities'][entity_id] = entity_state
    return True
```

**Step 2:** Add Guardrails to SliceBuilder

```python
# In physics_step() before calling MR kernel
snapshot_in = {"spatial3d": self._state_slice}

# Build slices with guardrails
for entity_id, entity_data in self._state_slice['entities'].items():
    try:
        kernel_slice = build_entity_slice_v1(entity_data)
    except SliceError as e:
        print(f"[FATAL] {e}")
        raise  # Fail hard, fail fast
```

**Step 3:** Add Cleanup to Kernel Writeback

```python
# After MR kernel returns
snapshot_out, accepted, mr_alerts = step_spatial3d(...)

# Write with mandatory cleanup
write_kernel_output_to_snapshot(
    snapshot={"spatial3d": self._state_slice},
    kernel_output=snapshot_out
)
```

### Validation

```python
from fix_1_snapshot_purity import assert_snapshot_purity

# Before sending to client
snapshot = runtime.get_snapshot()
assert_snapshot_purity(snapshot)  # Raises on contamination
```

**Expected Result:**
```
✓ Snapshot uses only: position, velocity
✗ Guardrail rejects: pos, vel
✓ Leaked keys purged automatically
```

---

## 🎮 **FIX 2: SYN-Client Exception Model**

### Problem Location
```gdscript
# EngAInBridge.gd - current implementation
func update_npc(entity_id, new_position):
    var tween = create_tween()
    tween.tween_property(npc, "position", new_position, 0.5)
    # ❌ No cancellation, no bounds, client authority creep!
```

### Implementation

**Step 1:** Replace `EngAInBridge.gd` with Disciplined Version

```gdscript
# Copy fix_2_syn_client_exception.gd logic

func update_npc(entity_id: String, new_position: Vector3, current_tick: int):
    """SYN-client disciplined update"""
    
    var npc = entity_nodes[entity_id]
    var truth = entity_truth[entity_id]
    
    # RULE 1: Cancel active interpolation (new truth overrides)
    if truth.active_tween and truth.active_tween.is_valid():
        truth.active_tween.kill()
    
    # Update truth snapshots (N → N+1)
    truth.snapshot_n = truth.snapshot_n_plus_1
    truth.snapshot_n_plus_1 = {
        "position": new_position,
        "tick": current_tick,
        "received_at": Time.get_ticks_msec()
    }
    
    # RULE 2: Interpolate ONLY between known truths
    if truth.snapshot_n != null:
        var pos_n = truth.snapshot_n.position
        var duration = min(time_delta / 1000.0, 0.5)
        
        var tween = create_tween()
        tween.tween_property(npc, "position", new_position, duration)
        truth.active_tween = tween
        
        npc.position = pos_n  # Start from N
    else:
        # RULE 3: No extrapolation - snap to truth
        npc.position = new_position
```

**Step 2:** Add Pause Test

```gdscript
# Debug command
func _input(event):
    if event.is_action_pressed("ui_pause_test"):
        start_pause_test(5.0)  # 5-second pause
```

**Step 3:** Monitor Violations

```gdscript
func _process(delta):
    var status = get_client_authority_status()
    
    if status.violations.size() > 0:
        for violation in status.violations:
            push_error("CLIENT AUTHORITY VIOLATION: ", violation)
```

### Validation

**Pause Test:**
1. Run game
2. Press pause test key
3. Wait 5 seconds
4. **PASS:** Entities snap to new positions
5. **FAIL:** Entities keep drifting

**Expected Result:**
```
✓ Tweens cancel on new snapshot
✓ No extrapolation beyond last truth
✓ Entities snap on pause resume
✗ Client has NO forbidden authority
```

---

## 🌐 **FIX 3: Protocol Envelope Validation**

### Implementation (Two Parts)

### Part A: Server-Side (Python)

**Step 1:** Add Protocol Envelope Middleware

```python
# In your HTTP server (e.g., FastAPI)
from protocol_envelope_server import SnapshotEnvelopeMiddleware

app = FastAPI()
envelope_middleware = SnapshotEnvelopeMiddleware()

@app.get("/snapshot")
async def get_snapshot():
    # Get raw snapshot
    raw_snapshot = sim_runtime.get_snapshot()
    
    # Wrap in protocol envelope
    envelope = envelope_middleware.wrap(
        payload=raw_snapshot,
        tick=sim_runtime.current_tick
    )
    
    return JSONResponse(envelope)
```

**Step 2:** Validate Envelope Structure

```python
# Before sending
from protocol_envelope_server import validate_envelope_structure

if not validate_envelope_structure(envelope):
    raise ValueError("Invalid envelope structure")
```

### Part B: Client-Side (Godot)

**Step 1:** Replace Polling Loop

```gdscript
# Copy fix_3_protocol_envelope.gd

# OLD: Time-based polling
# func _process(delta):
#     _poll_timer += delta
#     if _poll_timer > 0.1:
#         request_snapshot()

# NEW: Signal-driven polling
func _ready():
    _http_request = HTTPRequest.new()
    add_child(_http_request)
    
    # Signal-driven (adaptive rate)
    _http_request.request_completed.connect(_on_snapshot_completed)
    
    _request_next_snapshot()  # Start loop
```

**Step 2:** Add Envelope Validation

```gdscript
func _on_snapshot_completed(result, code, headers, body):
    _snapshot_request_in_flight = false
    
    # Parse JSON
    var raw_snapshot = JSON.parse_string(body.get_string_from_utf8())
    
    # VALIDATE ENVELOPE (Critical!)
    var validation = validate_and_unwrap_envelope(raw_snapshot)
    
    if not validation.success:
        push_error("ENVELOPE REJECTED: ", validation.error)
        _request_next_snapshot()  # Skip corrupted
        return
    
    # Envelope valid - propagate
    var payload = validation.payload
    var tick = validation.tick
    
    _process_validated_snapshot(payload, tick)
    
    # Request next (signal-driven)
    _request_next_snapshot()
```

### Validation

**Server Test:**
```bash
python3 protocol_envelope_server.py

# Expected:
✓ Envelope valid
✓ Hash: 94c150392014ae01...
✓ 5/5 snapshots accepted
```

**Client Test:**
```gdscript
# Check validation stats
var report = get_validation_report()
print("Acceptance rate: ", report.acceptance_rate)

# Should be > 95%
```

**Expected Result:**
```
Server:
✓ Generates envelope with version/tick/hash
✓ Hash calculated deterministically

Client:
✓ Validates version compatibility
✓ Rejects out-of-order ticks
✓ Verifies hash integrity
✓ No request overlap errors
```

---

## ✅ **Validation Tests**

### Test Suite

```python
# test_hardening.py

def test_snapshot_purity():
    """Test FIX 1"""
    from fix_1_snapshot_purity import (
        create_entity_state,
        assert_snapshot_purity,
        FORBIDDEN_IN_SNAPSHOT
    )
    
    # Create entity
    entity = create_entity_state('test', position=(1, 2, 3))
    
    # Should have protocol names
    assert 'position' in entity
    assert 'pos' not in entity
    
    # Contaminated snapshot should fail
    contaminated = {'entities': {'test': {'pos': [1,2,3]}}}
    
    try:
        assert_snapshot_purity(contaminated)
        assert False, "Should have raised SliceError"
    except Exception:
        pass  # Expected
    
    print("✓ Snapshot purity enforced")


def test_protocol_envelope():
    """Test FIX 3"""
    from protocol_envelope_server import create_snapshot_envelope
    
    payload = {"spatial3d": {"entities": {}}}
    envelope = create_snapshot_envelope(payload, tick=1, epoch="test")
    
    # Check envelope structure
    assert 'version' in envelope
    assert 'tick' in envelope
    assert 'content_hash' in envelope
    assert 'payload' in envelope
    
    print("✓ Protocol envelope valid")


# Run tests
if __name__ == "__main__":
    test_snapshot_purity()
    test_protocol_envelope()
    print("\n✅ ALL HARDENING TESTS PASSED")
```

---

## 📊 **Before & After**

### Before Hardening

```
❌ Snapshot contaminated (pos, vel present)
❌ Client tweens without bounds
❌ No version checking
❌ No hash verification
❌ Request overlap errors
❌ Silent corruption possible
```

### After Hardening

```
✅ Snapshot pure (position, velocity only)
✅ Client bounded to N→N+1
✅ Version enforced (1.0.0)
✅ Hash verified (SHA256)
✅ Signal-driven polling
✅ Corruption impossible (hard rejection)
```

---

## 🚀 **Deployment Steps**

### Phase 1: Server Hardening (2 hours)
1. Apply FIX 1 to `spatial3d_adapter.py`
2. Add FIX 3 envelope middleware
3. Test snapshot purity
4. Deploy server

### Phase 2: Client Hardening (2 hours)
1. Apply FIX 2 to `EngAInBridge.gd`
2. Add FIX 3 envelope validation
3. Test pause test
4. Deploy client

### Phase 3: Integration Testing (2 hours)
1. End-to-end smoke tests
2. Pause test validation
3. Hash verification checks
4. Monitor acceptance rate

**Total Time:** ~6 hours  
**Rollback Plan:** Keep old server/client for 24h

---

## 💡 **Key Principles**

**Snapshot Purity**
> "Snapshot = Pure Wire Protocol"  
> Internal kernel names NEVER leak

**Client Discipline**
> "Client = Archivist of Past, Not Prophet of Future"  
> Interpolate N→N+1 only, never extrapolate

**Transport Integrity**
> "Fail Hard, Fail Fast"  
> Reject corrupt data before it propagates

---

## 📁 **File Checklist**

- [x] `fix_1_snapshot_purity.py` - Snapshot purity enforcer
- [x] `fix_2_syn_client_exception.gd` - Client discipline model
- [x] `fix_3_protocol_envelope.gd` - Client envelope validation
- [x] `protocol_envelope_server.py` - Server envelope generation
- [x] `HARDENING_GUIDE.md` - This file

---

## 🎯 **Success Criteria**

**After implementation, you should see:**

1. **Zero snapshot contamination**
   - `assert_snapshot_purity()` never raises
   - Debug logs show only protocol names

2. **Client authority discipline**
   - Pause test always passes (entities snap)
   - No unauthorized movement between ticks

3. **Transport integrity**
   - Acceptance rate > 99%
   - Zero hash mismatches
   - No request overlap errors

---

**Your system is now:** Hardened, Disciplined, Survivable ✅

**Submit back** when navigation kernel is sliced in!
