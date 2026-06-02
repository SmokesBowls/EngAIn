# EngAIn Architecture Hardening Roadmap

**Current Status:** Phase 1 Complete - Working AI with Slice Protection
**Next Goal:** Production-Ready Protocol + Client Discipline

---

## ✅ COMPLETED (What You Have Now)

### Phase 0: Foundation (DONE)
- ✓ Pure MR kernels (spatial3d_mr, perception_mr, behavior3d_mr, navigation_mr)
- ✓ Slice builder protection layer (slice_builders.py)
- ✓ Canonical position/velocity keys
- ✓ Python authority maintained
- ✓ HTTP transport operational
- ✓ Behavior AI firing deltas
- ✓ Real physics simulation

**Evidence:** Working system, no KeyErrors, AI responds to perception, physics active

---

## 🎯 PHASE 1: Protocol Sovereignty (2-3 hours)

### Goal
Eliminate silent drift through versioned, hashed protocol envelopes.

### Tasks

**1.1 Install Protocol System (30 min)**
```bash
cd ~/godotsim
cp protocol_envelope.py .
```
- Add imports to sim_runtime.py
- Initialize envelope in __init__
- Update get_snapshot() to wrap

**1.2 Python Integration (1 hour)**
- Wrap snapshots with version/tick/epoch/hash
- Add hard rejection in HTTP handlers
- Test hash verification
- Add protocol logging

**1.3 Godot Integration (1 hour)**
- Add envelope validation in ZWRuntime.gd
- Implement hard rejection logic
- Test version mismatch handling
- Test epoch consistency

**1.4 Validation (30 min)**
- Run test suite (see PROTOCOL_INTEGRATION.md)
- Verify hash detection works
- Verify version rejection works
- Document in logs

### Success Criteria
- [ ] Every snapshot has version/tick/epoch/hash
- [ ] Version mismatch causes immediate rejection
- [ ] Hash corruption detected instantly
- [ ] Logs show protocol info on startup
- [ ] No silent failures

### Deliverables
- Modified sim_runtime.py with envelope
- Modified ZWRuntime.gd with validation
- Test results documented

---

## 🎯 PHASE 2: Client Discipline (1-2 hours)

### Goal
Eliminate client authority creep through stateless projection.

### Tasks

**2.1 Run Litmus Test (15 min)**
- Add litmus test to TestZWScene.gd
- Press L in Godot
- Document whether PASS or FAIL
- If FAIL, note what smooth-transitioned vs snapped

**2.2 Audit for Forbidden State (30 min)**
- Use CLIENT_AUDIT.md checklist
- Search for forbidden patterns:
  - `grep -r "var.*position" *.gd`
  - `grep -r "position.*+=" *.gd`
  - `grep -r "predict" *.gd`
- Document all findings

**2.3 Refactor Client (1 hour)**
- Strip local world_state dictionaries
- Add snapshot cancellation to all tweens
- Convert mutations to commands
- Remove any client-side physics

**2.4 Re-test (15 min)**
- Run litmus test again
- Should now PASS (instant snap)
- Verify no visual lag or prediction
- Document cleanup

### Success Criteria
- [ ] Litmus test PASSES
- [ ] No forbidden state variables found
- [ ] All tweens bounded by snapshots
- [ ] All mutations replaced with commands
- [ ] grep searches return clean

### Deliverables
- Refactored ZWRuntime.gd
- Litmus test results (PASS)
- Audit report filled out

---

## 🎯 PHASE 3: Enforcement Layers (1 hour)

### Goal
Make violations impossible through structural enforcement.

### Tasks

**3.1 Slice Builder Guards (30 min)**
- Add contamination detection in slice_builders.py
- Raise SliceError if kernel names leak into snapshot
- Add reverse contamination guards
- Test with intentional violations

**3.2 Client Assertions (15 min)**
- Add has_forbidden_state() check in ZWRuntime
- Assert on startup
- Document forbidden patterns

**3.3 Integration Test Suite (15 min)**
- Create test_protocol.py
- Test envelope wrap/unwrap
- Test hash verification
- Test version rejection
- Document results

### Success Criteria
- [ ] Contamination guards active
- [ ] Client self-checks on startup
- [ ] All tests passing
- [ ] Violations cause immediate errors

### Deliverables
- Enhanced slice_builders.py with guards
- ZWRuntime.gd with assertions
- test_protocol.py passing

---

## 📊 Progress Tracking

### Phase Completion Status
```
Phase 0: Foundation           [████████████████████] 100% DONE
Phase 1: Protocol Sovereignty [                    ]   0%
Phase 2: Client Discipline    [                    ]   0%
Phase 3: Enforcement          [                    ]   0%
```

### Time Estimates
- Phase 1: 2-3 hours
- Phase 2: 1-2 hours  
- Phase 3: 1 hour
- **Total: 4-6 hours to production-ready**

### Current Sprint Goals
**Next Session:**
1. Install protocol_envelope.py
2. Integrate into sim_runtime.py
3. Test hash verification

**Following Session:**
4. Run client litmus test
5. Audit and refactor Godot

---

## 🔧 Quick Reference

### Files Created This Session
- `protocol_envelope.py` - Complete envelope system
- `PROTOCOL_INTEGRATION.md` - Step-by-step guide
- `CLIENT_AUDIT.md` - Audit checklist + litmus test
- `sim_runtime_FIXED.py` - Working runtime with canonical keys
- `slice_builders.py` - Boundary protection
- `slice_types.py` - Canonical types

### Key Commands

**Run protocol tests:**
```bash
cd ~/godotsim
python3 protocol_envelope.py
```

**Run client audit:**
```bash
cd ~/godotsim
grep -r "var.*position" *.gd
grep -r "position.*+=" *.gd
```

**Start system:**
```bash
cd ~/godotsim
python3 sim_runtime.py
# In Godot: Press L for litmus test
```

---

## 🎯 Success Metrics

### Current State (Baseline)
- Working AI: ✓
- Physics active: ✓
- Slice protection: ✓
- Canonical keys: ✓

### After Phase 1 (Protocol)
- Version enforcement: ✓
- Hash verification: ✓
- Hard rejection: ✓
- No silent drift: ✓

### After Phase 2 (Client)
- Litmus test PASS: ✓
- No forbidden state: ✓
- Stateless projection: ✓
- Command-driven: ✓

### After Phase 3 (Enforcement)
- Contamination guards: ✓
- Startup assertions: ✓
- Test suite passing: ✓
- Architecture hardened: ✓

---

## 📝 Next Session Checklist

When you return:

1. **Quick Status**
   - [ ] Confirm system still works: `python3 sim_runtime.py`
   - [ ] Greeter AI still fires deltas
   - [ ] Physics still running

2. **Start Phase 1**
   - [ ] Copy protocol_envelope.py to ~/godotsim
   - [ ] Follow PROTOCOL_INTEGRATION.md steps 1-2
   - [ ] Test hash verification
   - [ ] Commit working state

3. **If Time Allows**
   - [ ] Start Phase 2: Run litmus test
   - [ ] Document results
   - [ ] Begin client refactor

4. **End Session**
   - [ ] Document progress
   - [ ] Note any blockers
   - [ ] Update phase completion %

---

## 🚨 Rollback Plans

If anything breaks:

**Protocol issues:**
```bash
cd ~/godotsim
cp sim_runtime_FIXED.py sim_runtime.py  # Last known good
```

**Client issues:**
```bash
cd ~/godotsim
git checkout ZWRuntime.gd  # If using git
# Or restore from backup
```

**Nuclear option:**
```bash
# You have working system NOW - snapshot it!
cd ~
tar -czf godotsim_working_$(date +%Y%m%d).tar.gz godotsim/
```

---

## 💡 Key Insights from Critique

**"Silent drift is a nightmare"**
→ Solution: Version checking with hard rejection

**"Dual truth is poison"**
→ Solution: Litmus test + stateless client

**"Ad-hoc carpentry breaks purity"**
→ Solution: Slice builders as mandatory membrane

**"The wire is a customs check"**
→ Solution: Protocol envelope with hash verification

---

## 🎉 Victory Conditions

**You'll know the architecture is hardened when:**
1. Version mismatch instantly rejects
2. Hash corruption instantly detected
3. Litmus test passes (instant snap)
4. No forbidden state in client
5. Slice contamination impossible
6. All tests passing

**Then you have:**
- Production-ready protocol
- Disciplined client
- Protected boundaries
- Survivable engine

**Ready for:**
- ZON4D temporal features
- Task system integration
- Combat + health system
- Voice/dialogue pipeline
- Multiplayer (future)

---

## End Goal

**From critique:**
> "This is the difference between a clean prototype and a survivable engine."

**You're building the survivable engine.**

Current: Working prototype with AI + physics
Target: Production-ready with hardened boundaries
Gap: 4-6 hours of focused work

**Let's close that gap.** 🚀
