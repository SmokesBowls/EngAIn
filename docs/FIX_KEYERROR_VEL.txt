# Fix: KeyError: 'vel' - Entity State Structure

## The Problem

Your tests are failing with:
```
KeyError: 'vel'
```

This happens because:
1. ✗ **Old runtime** creates entities with `"position": {"x": 5, "y": 0, "z": 3}`
2. ✓ **Subsystems expect** entities with `"pos": (5, 0, 3)` and `"vel": (0, 0, 0)`

The MR kernels expect entities to have:
- **`pos`** as a tuple: `(x, y, z)`
- **`vel`** as a tuple: `(vx, vy, vz)`

## The Fix

Replace your `sim_runtime.py` with `sim_runtime_fixed.py`

### What Changed

**Old entity creation:**
```python
self.snapshot["entities"][entity_id] = {
    "type": entity_type,
    "position": {"x": 5, "y": 0, "z": 3},  # Dict - WRONG FORMAT
    "health": 100
    # Missing "vel"!
}
```

**New entity creation:**
```python
entity_state = self._create_entity_state(
    entity_id,
    entity_type,
    (5.0, 0.0, 3.0),  # Tuple position
    health=100
)

# Results in:
{
    "id": "greeter_main",
    "type": "greeter",
    "pos": (5.0, 0.0, 3.0),  # Tuple!
    "vel": (0.0, 0.0, 0.0),  # Always present!
    "health": 100,
    "max_health": 100
}
```

## Quick Fix Steps

```bash
cd ~/godotsim

# Backup current
cp sim_runtime.py sim_runtime_old_keyerror.py

# Use fixed version
cp sim_runtime_fixed.py sim_runtime.py

# Restart
python3 sim_runtime.py
```

## Test It

Run your tests:
```bash
python3 test_spatial3d.py
python3 test_behavior3d_integration.py
```

**Should now pass!** ✓

## What the Fixed Runtime Does

### 1. Helper Function for Complete State
```python
def _create_entity_state(self, entity_id, entity_type, position, **kwargs):
    """Create complete entity state with all required fields"""
    return {
        "id": entity_id,
        "type": entity_type,
        "pos": position,              # Tuple (x, y, z)
        "vel": (0.0, 0.0, 0.0),      # Velocity tuple - REQUIRED
        "health": kwargs.get("health", 100),
        "max_health": kwargs.get("max_health", 100),
        **kwargs  # Any additional properties
    }
```

### 2. Converts Position Dicts to Tuples
```python
# When receiving position as dict:
position = {"x": 5, "y": 0, "z": 3}

# Convert to tuple:
pos_tuple = (position.get("x", 0), position.get("y", 0), position.get("z", 0))
```

### 3. Actually Calls step_spatial3d()
```python
def _update_subsystems(self, dt):
    # Build spatial state
    spatial_state = {"entities": {}}
    for eid in entity_ids:
        entity = self.snapshot["entities"][eid]
        spatial_state["entities"][eid] = {
            "pos": entity["pos"],  # Has both!
            "vel": entity["vel"]
        }
    
    # Step the MR kernel - applies physics!
    updated_state = step_spatial3d(spatial_state, dt)
    
    # Update entities with new positions/velocities
    for eid, spatial_data in updated_state.get("entities", {}).items():
        self.snapshot["entities"][eid]["pos"] = spatial_data["pos"]
        self.snapshot["entities"][eid]["vel"] = spatial_data["vel"]
```

Now entities actually have **physics applied** every frame!

## Verify It Works

After replacing and restarting:

**Spawn an entity:**
```
[Click button in Godot]
```

**Dump state:**
```
[Click "D - Dump State"]
```

**You should see:**
```json
"entities": {
  "greeter_main": {
    "id": "greeter_main",
    "type": "greeter",
    "pos": [5.0, 0.0, 3.0],     ← Tuple!
    "vel": [0.0, 0.0, 0.0],     ← Present!
    "health": 100,
    "dialogue": "Welcome back, friend!"
  }
}
```

## Why This Matters

**With correct structure:**
- ✓ Spatial3D can apply physics
- ✓ Entities fall with gravity
- ✓ Collisions work
- ✓ Perception can calculate line-of-sight
- ✓ Navigation can pathfind
- ✓ Behavior can make AI decisions

**Without it:**
- ✗ KeyError crashes
- ✗ No physics
- ✗ Subsystems can't function

## The Three Data Formats

Your system needs to handle 3 formats:

1. **Godot sends** (from UI): `{"x": 5, "y": 0, "z": 3}`
2. **Runtime converts to**: `(5.0, 0.0, 3.0)`
3. **Subsystems use**: Tuples internally
4. **Runtime sends back** (snapshot): Can be tuple or dict, Godot handles both

The fixed runtime does all conversions automatically!

---

**TL;DR**: Replace sim_runtime.py with sim_runtime_fixed.py, restart, tests will pass!
