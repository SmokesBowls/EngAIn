# Quick Integration - Slice Protected Runtime

## What Changed

**Key additions:**
1. Imports slice_builders at top
2. Lines 295-318: Uses `build_entity_kview_v1()` to guarantee pos/vel exist
3. Falls back to old way if slices not available (safety)
4. Logs `[SLICE ERROR]` if entity data malformed

## Integration Steps

```bash
cd ~/godotsim

# Backup current runtime
cp sim_runtime.py sim_runtime.backup.py

# Install new runtime
cp sim_runtime_with_slices.py sim_runtime.py

# Verify slice files present
ls slice_*.py
# Should show: slice_builders.py  slice_types.py

# Test
python3 sim_runtime.py
```

## Expected Output

```
✓ Slice builders loaded
✓ MR kernels | spatial=True, perception=True, behavior=True
==================================================
EngAIn Runtime Server
==================================================
  ✓ Spatial3D
  ✓ Perception
  ✓ Behavior
  → Ladies and Gentalman and AI, This is your captain speaking...
```

## What to Watch For

**Good signs:**
- "✓ Slice builders loaded" appears
- No KeyError: 'vel' ever
- Behavior still fires deltas
- Everything works same as before

**If slice builders fail to load:**
- Falls back to old dict assembly (still works)
- Shows: "Slice builders missing: ..."
- No harm, just less protection

## Testing

```bash
# In Godot, press buttons:
1 - Spawn hostile greeter
D - Dump state

# Should see in Python:
[BEHAVIOR] 1 deltas fired
  🔥 [behavior3d/high_intent]
     greeter_main HIGH INTENT: 0.74
```

## Rollback if Needed

```bash
cd ~/godotsim
cp sim_runtime.backup.py sim_runtime.py
```

## What's Protected Now

**Before:** `if "pos" in entity and "vel" in entity:` ← guessing
**After:** `slice_view = build_entity_kview_v1(snapshot, eid)` ← guaranteed

**Before:** Missing vel → KeyError deep in kernel
**After:** Missing vel → SliceError at boundary with clear message

Ready to test! 🎯
