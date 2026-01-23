# FIXED: Canonical Keys - position/velocity vs pos/vel

## The Problem

**Runtime was using inconsistent keys:**
- Creating entities with: `"pos"` and `"vel"`
- Writing back with: `"pos"` and `"vel"`  
- But canonical format should be: `"position"` and `"velocity"`

**This caused:**
- Snapshot had mixed keys
- Godot expecting "position"/"velocity" 
- Silent errors being swallowed by except blocks

## What Was Fixed

### 1. Entity Creation (line 94-95)
```python
# BEFORE
"pos": position,
"vel": (0.0, 0.0, 0.0),

# AFTER  
"position": position,  # Canonical
"velocity": (0.0, 0.0, 0.0),  # Canonical
```

### 2. Spatial Update Writeback (lines 352-353, 384-385)
```python
# BEFORE
self.snapshot["entities"][eid]["pos"] = list(spatial_data["pos"])
self.snapshot["entities"][eid]["vel"] = list(spatial_data["vel"])

# AFTER
self.snapshot["entities"][eid]["position"] = list(spatial_data["pos"])
self.snapshot["entities"][eid]["velocity"] = list(spatial_data["vel"])
```

### 3. Error Visibility (added traceback)
```python
# BEFORE
except Exception as e:
    print(f"[SPATIAL ERROR] {e}")

# AFTER
except Exception as e:
    import traceback
    print(f"[SPATIAL ERROR] {e}")
    traceback.print_exc()  # See full error!
```

## Why Slice Builders Still Work

**slice_builders.py already handles both formats:**
```python
pos_raw = e.get("pos") or e.get("position")  # Checks both!
vel_raw = e.get("vel") or e.get("velocity")  # Checks both!
```

So it can READ from either format, but we WRITE in canonical format.

## Install

```bash
cd ~/godotsim

# Backup
cp sim_runtime.py sim_runtime.before_canonical.py

# Install
cp sim_runtime_FIXED.py sim_runtime.py

# Test
python3 sim_runtime.py
```

## Expected Result

**Snapshots now look like:**
```json
{
  "entities": {
    "greeter_main": {
      "position": [5.0, 0.0, 3.0],  ✅ Canonical
      "velocity": [0.0, 0.0, 0.0]   ✅ Canonical
    }
  }
}
```

**No more [SPATIAL ERROR] silently hiding issues!**

If there IS an error now, you'll see the full traceback to debug it.
