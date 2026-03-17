# Fix #3 — Combat Health Bar Smoothing
## Drop-In Integration Guide

### What This Is

Pure Godot visual layer. The Python kernel (`combat3d_mr.py`) sets `actual_health` in snapshots.
This node lerps `displayed_health` toward that value each frame. No kernel changes. No new HTTP events.

### Authority Model

```
Python combat3d_mr.py     →  actual_health   (TRUTH — never touch from Godot)
CombatHealthBar.gd        →  displayed_health (VISUAL — lerps toward truth)
                           →  ghost_health     (VISUAL — damage/heal trail)
```

---

### Step 1: Copy Files

```bash
cp CombatHealthBar.gd    ~/Downloads/EngAIn/godot/scripts/
cp test_combat_healthbar.gd ~/Downloads/EngAIn/godot/scripts/
```

### Step 2: Test Standalone (No Python Needed)

1. Open your Godot project
2. Create a new scene (Node2D root)
3. Attach `test_combat_healthbar.gd` to the root node
4. Run the scene

**You should see:**
- Health bar with smooth lerp on damage
- Red ghost trail that fades after hits
- Green ghost on heals
- Low-health red pulse below 25%
- White flash on damage events
- Auto-demo cycles through damage/heal patterns

**Keyboard controls:**
- `1` — Small hit (15 damage)
- `2` — Big hit (40 damage)
- `3` — Heal (+20)
- `4` — Full heal
- `5` — Kill (set to 0)
- `R` — Reset to full

### Step 3: Wire to ZWRuntime (Production)

Once the visual looks right, remove the test harness. The health bar auto-connects
to `ZWRuntime.state_updated` signal. Your Python snapshots just need this shape:

```json
{
  "entities": {
    "player": {
      "combat": {
        "health": 75.0,
        "max_health": 100.0
      }
    }
  }
}
```

That's already what `combat3d_integration.py` produces. No adapter changes needed.

In your game scene, just add the health bar node:

```gdscript
# In your HUD or game scene
var hbar = CombatHealthBar.new()
hbar.entity_id = "player"  # Must match entity key in snapshot
hbar.position = Vector2(20, 20)
add_child(hbar)
```

Or create it in the editor and set `entity_id` in the inspector.

### What You're Proving

This completes the thin slice: **tested kernel → existing adapter → visible Godot endpoint**.
Combat3D already had the kernel and adapter. This is the missing visual tip.

### Next Slice Options

After this works:
- **MV-CAR wiring** — AudioTimeline.gd → ZWRuntime (same pattern, different data)
- **Pass2 CORE+ hardening** — back to core, pronoun chains + emotion keywords
- **Quest3D kernel** — new subsystem following Combat3D pattern
