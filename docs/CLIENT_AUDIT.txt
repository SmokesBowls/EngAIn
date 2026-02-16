# Client Authority Creep Audit Checklist

## The Litmus Test (Run This First!)

### Setup Test Scene

Add to TestZWScene.gd:
```gdscript
func _input(event):
    if event is InputEventKey and event.pressed:
        if event.keycode == KEY_L:  # L for Litmus
            run_litmus_test()

func run_litmus_test():
    """
    The ultimate client authority test:
    1. Pause Godot rendering
    2. Let Python advance 10 ticks
    3. Resume Godot
    4. Visuals should SNAP to latest truth instantly
    
    If they don't, client is holding forbidden state.
    """
    print("=== LITMUS TEST START ===")
    
    # Step 1: Note current state
    var snapshot_before = zw_runtime.last_snapshot
    if snapshot_before and snapshot_before.has("entities"):
        print("Before pause:")
        for eid in snapshot_before.entities:
            var e = snapshot_before.entities[eid]
            if e.has("position"):
                print("  ", eid, ": ", e.position)
    
    # Step 2: Pause rendering (stop polling)
    zw_runtime.pause_rendering()
    print("Rendering paused - Python still running")
    
    # Step 3: Wait for Python to advance
    await get_tree().create_timer(1.0).timeout
    
    # Step 4: Resume rendering (restart polling)
    zw_runtime.resume_rendering()
    
    # Step 5: Check if snap happened
    await get_tree().create_timer(0.1).timeout
    
    var snapshot_after = zw_runtime.last_snapshot
    if snapshot_after and snapshot_after.has("entities"):
        print("After resume:")
        for eid in snapshot_after.entities:
            var e = snapshot_after.entities[eid]
            if e.has("position"):
                print("  ", eid, ": ", e.position)
    
    print("=== LITMUS TEST END ===")
    print("PASS: Positions snapped instantly to new values")
    print("FAIL: Positions unchanged or smoothly transitioned")
```

Add to ZWRuntime.gd:
```gdscript
var rendering_paused = false
var last_snapshot = null

func pause_rendering():
    rendering_paused = true
    poll_timer.stop()

func resume_rendering():
    rendering_paused = false
    poll_timer.start()

func on_world_state_updated(snapshot):
    last_snapshot = snapshot  # Store for litmus test
    
    if rendering_paused:
        return  # Don't update visuals while paused
    
    # Normal rendering logic...
```

### Expected Results

**PASS:**
```
=== LITMUS TEST START ===
Before pause:
  greeter_main: [5, 0, 3]
Rendering paused - Python still running
After resume:
  greeter_main: [5, -8.2, 3]  ← SNAPPED to new position
=== LITMUS TEST END ===
PASS: Positions snapped instantly to new values
```

**FAIL (client holding state):**
```
After resume:
  greeter_main: [5, -1.2, 3]  ← Smoothly transitioned, not snapped
FAIL: Client is predicting/holding state
```

---

## Manual Audit Checklist

### ❌ FORBIDDEN (World State)

Search for these patterns in ZWRuntime.gd and all Godot scripts:

**1. Authoritative Position Storage**
```gdscript
# FORBIDDEN
var entity_positions = {}  # ← Mirrors server truth
var player_position = Vector3.ZERO  # ← Should come from snapshot only

# Check: grep -r "var.*position" *.gd
```

**2. Authoritative Movement Logic**
```gdscript
# FORBIDDEN
func _process(delta):
    player_position += velocity * delta  # ← Client-side physics
    entity.position = calculate_next_pos()  # ← Local simulation

# Check: grep -r "position.*+=" *.gd
# Check: grep -r "position.*\*.*delta" *.gd
```

**3. State Prediction**
```gdscript
# FORBIDDEN
func predict_position(entity_id):
    var last_pos = positions[entity_id]
    var last_vel = velocities[entity_id]
    return last_pos + last_vel * time_since_update  # ← Guessing future

# Check: grep -r "predict" *.gd
```

**4. Decision Making**
```gdscript
# FORBIDDEN
func should_attack():
    return distance_to_player < 5.0  # ← Logic decision in client

# Check: grep -r "should_" *.gd
# Check: grep -r "can_" *.gd
```

**5. Unbounded Tweens**
```gdscript
# FORBIDDEN
tween.tween_property(node, "position", target, 2.0)  # ← No snapshot override

# Check: Look for tweens without snapshot cancellation
```

---

### ✅ ALLOWED (Presentation State)

These are LEGAL in Godot:

**1. Node References**
```gdscript
# ALLOWED
var entity_nodes = {}  # Node references for rendering
var particle_systems = {}  # FX systems
```

**2. Visual Interpolation (with strict rules)**
```gdscript
# ALLOWED (if bounded)
func update_visual(eid, new_pos):
    var node = entity_nodes[eid]
    
    # Rule 1: Target MUST equal snapshot position
    var target = new_pos
    
    # Rule 2: Duration MUST be < snapshot interval
    var duration = 0.05  # 50ms, if snapshots come every 100ms
    
    # Rule 3: New snapshot MUST cancel tween
    if node.has_method("stop_tween"):
        node.stop_tween()
    
    tween.tween_property(node, "position", target, duration)
```

**3. Animation State**
```gdscript
# ALLOWED
var is_playing_attack_anim = false  # Visual only
var particle_cooldowns = {}  # FX timing
```

**4. Camera State**
```gdscript
# ALLOWED
var camera_offset = Vector3(0, 5, -10)
var camera_shake_intensity = 0.0
```

---

## Refactoring Guide

### Pattern: Strip Local State Dictionary

**BEFORE:**
```gdscript
var world_state = {
    "entities": {},
    "player_position": Vector3.ZERO,
    "npc_targets": {}
}

func on_world_state_updated(snapshot):
    # Update local mirror
    world_state.entities = snapshot.entities
    world_state.player_position = snapshot.entities.player.position
```

**AFTER:**
```gdscript
# NO local state dictionary!

func on_world_state_updated(snapshot):
    # Render directly from snapshot
    if snapshot.has("entities"):
        for eid in snapshot.entities:
            update_visual(eid, snapshot.entities[eid])
```

### Pattern: Snapshot-Driven Tweens

**BEFORE:**
```gdscript
# Tween runs forever, no snapshot override
tween.tween_property(node, "position", target, 5.0)
```

**AFTER:**
```gdscript
func update_visual(eid, entity_data):
    var node = entity_nodes.get(eid)
    if not node:
        return
    
    var new_pos = Vector3(
        entity_data.position[0],
        entity_data.position[1],
        entity_data.position[2]
    )
    
    # Cancel any existing tween - snapshot is authority
    if node.has_meta("active_tween"):
        var old_tween = node.get_meta("active_tween")
        old_tween.kill()
    
    # Create new bounded tween
    var tween = create_tween()
    tween.tween_property(node, "position", new_pos, 0.05)
    node.set_meta("active_tween", tween)
```

### Pattern: Commands, Not Mutations

**BEFORE:**
```gdscript
# Client directly mutates state
func on_player_move(direction):
    player_position += direction * speed
    world_state.entities.player.position = player_position
```

**AFTER:**
```gdscript
# Client sends command, waits for snapshot
func on_player_move(direction):
    var command = {
        "action": "move",
        "entity_id": "player",
        "direction": direction
    }
    zw_runtime.send_command(command)
    
    # Position update comes from snapshot, not here!
```

---

## Audit Summary Report Template

After running audit, fill this out:

```
=== CLIENT AUTHORITY AUDIT ===
Date: __________
Audited by: __________

LITMUS TEST: [ ] PASS  [ ] FAIL
If FAIL, describe behavior: _______________________

FORBIDDEN STATE FOUND:
[ ] Authoritative position storage
[ ] Client-side physics/movement
[ ] State prediction
[ ] Decision-making logic
[ ] Unbounded tweens

FILES REQUIRING REFACTOR:
- _______________________________
- _______________________________
- _______________________________

ESTIMATED CLEANUP TIME: ________ hours

NOTES:
_________________________________________
_________________________________________
```

---

## Enforcement Tools

### 1. Add Assertion in ZWRuntime

```gdscript
func _ready():
    # Self-audit on startup
    assert(not has_forbidden_state(), "Client holds forbidden world state!")

func has_forbidden_state() -> bool:
    """Check for common forbidden patterns"""
    # Add checks for your specific vars
    if has_node("LocalState"):
        return true
    return false
```

### 2. Add to Code Review Checklist

When reviewing Godot PRs, check:
- [ ] No world state mirrors
- [ ] No client-side physics
- [ ] All tweens have snapshot cancellation
- [ ] Commands used instead of mutations
- [ ] Litmus test passes

---

## Next Steps

1. Run litmus test NOW: `Press L in Godot`
2. If FAIL: Use audit checklist to find forbidden state
3. Refactor using patterns above
4. Re-run litmus test until PASS
5. Add enforcement assertions
6. Document in architecture notes
