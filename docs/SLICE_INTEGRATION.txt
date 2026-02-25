# Slice Builder Integration Guide

## What This Fixes

**Old way (causes bugs):**
```python
for eid in entity_ids:
    entity = self.snapshot["entities"][eid]
    if "pos" in entity and "vel" in entity:  # ← GUESSING
        spatial_state["entities"][eid] = {
            "pos": entity["pos"],
            "vel": entity["vel"]
        }
```

**New way (guarantees shape):**
```python
from slice_builders import build_spatial_slice_v1, SliceError

for eid in entity_ids:
    try:
        slice = build_spatial_slice_v1(self.snapshot, tick, eid)
        # slice.self.pos and slice.self.vel GUARANTEED to exist
    except SliceError as e:
        # Fails fast with clear message
        print(f"[SLICE ERROR] {e}")
        continue
```

## Step 1: Add to ~/godotsim/

```bash
cd ~/godotsim
cp slice_types.py .
cp slice_builders.py .
```

## Step 2: Update _update_subsystems in sim_runtime.py

**Find this section (around line 260):**
```python
# Update spatial positions using MR kernel
if HAS_SPATIAL_MR and self.spatial:
    try:
        spatial_state = {"entities": {}}
        
        for eid in entity_ids:
            entity = self.snapshot["entities"][eid]
            if "pos" in entity and "vel" in entity:  # ← OLD
                spatial_state["entities"][eid] = {
                    "pos": entity["pos"],
                    "vel": entity["vel"]
                }
```

**Replace with:**
```python
# Update spatial positions using MR kernel
if HAS_SPATIAL_MR and self.spatial:
    from slice_builders import build_spatial_slice_v1, SliceError
    
    try:
        spatial_state = {"entities": {}}
        
        for eid in entity_ids:
            try:
                # Build guaranteed slice
                slice = build_spatial_slice_v1(
                    self.snapshot, 
                    self.snapshot["world"]["time"], 
                    eid
                )
                
                # Now guaranteed to have pos/vel
                spatial_state["entities"][eid] = {
                    "pos": slice.self.pos,
                    "vel": slice.self.vel
                }
                
            except SliceError as e:
                print(f"[SLICE ERROR] {eid}: {e}")
                continue
```

## Step 3: Update behavior section (around line 293)

**Replace behavior slice building:**
```python
# Old way
spatial_slice = {"position": spatial_entities[entity_id].get("pos")}
perception_slice = self._perception_snapshot.get(entity_id, {})

# New way
from slice_builders import build_behavior_slice_v1, SliceError

try:
    behavior_slice = build_behavior_slice_v1(
        self.snapshot,
        self.snapshot["world"]["time"],
        entity_id
    )
    
    # Pass to adapter
    self.behavior.set_spatial_state(self.snapshot)
    self.behavior.set_perception_state(self.snapshot.get("perception", {}))
    
except SliceError as e:
    print(f"[BEHAVIOR SLICE ERROR] {entity_id}: {e}")
    continue
```

## Step 4: Test

```bash
python3 sim_runtime.py
```

**Should see:**
- No more KeyError: 'vel'
- Clear SliceError messages if data missing
- Same behavior as before (but safer)

## What Changed

**Before:** Runtime guessed entity shape
**After:** Builders validate and normalize

**Before:** Missing vel → KeyError in kernel
**After:** Missing vel → SliceError at boundary

**Before:** Multiple places reading snapshot
**After:** ONE place (builders.py)

## Next: Update Kernels

Once runtime uses slices, update kernel signatures:

```python
# spatial3d_mr.py
def step_spatial3d(slice: SpatialSliceV1, dt: float):
    # Use slice.self.pos, slice.self.vel
    # Never access raw dict
```

This is optional but recommended.
