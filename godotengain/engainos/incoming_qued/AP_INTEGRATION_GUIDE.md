# AP Engine Integration Guide
## Connecting Narrative → AP Rules → Godot Visualization

**Status:** Ready for integration  
**Estimated Time:** 30 minutes  
**Files Created:** ap_engine.py, ap_runtime.py, APBridge.gd

---

## What You're Integrating

This connects the complete pipeline:

```
Story Text (Obsidian)
  ↓
Pass1-3 Extraction (mettaext/)
  ↓
ZONJ Output (scenes/)
  ↓
AP Engine (ap_engine.py) ← YOU ARE HERE
  ↓
sim_runtime.py (HTTP bridge)
  ↓
Godot (APBridge.gd)
  ↓
Visual Feedback (cube tinting)
```

The AP engine is **operational** and spec-compliant. You just need to wire it in.

---

## Step 1: Place AP Engine Files

### 1.1 Copy ap_engine.py
```bash
cp ap_engine.py /home/burdens/Downloads/EngAIn/godotengain/engainos/core/
```

This is the core AP v1 implementation following your specs.

### 1.2 Copy ap_runtime.py
```bash
cp ap_runtime.py /home/burdens/Downloads/EngAIn/godotengain/engainos/core/
```

This integrates AP into your existing sim_runtime.py.

---

## Step 2: Integrate into sim_runtime.py

Open `/home/burdens/Downloads/EngAIn/godotengain/engainos/core/sim_runtime.py`

### 2.1 Add Import (top of file)
```python
from ap_runtime import APRuntimeIntegration
```

### 2.2 Initialize AP Runtime (in __init__ or startup)
```python
class YourRuntimeClass:
    def __init__(self):
        # ... existing initialization ...
        
        # Initialize AP Runtime
        self.ap_runtime = APRuntimeIntegration(scenes_dir="path/to/scenes")
        
        # Get initial state from ZON4D or use defaults
        initial_state = self._get_initial_state()
        self.ap_runtime.initialize(initial_state)
```

### 2.3 Handle AP Messages (in your message handler)
```python
def handle_message(self, msg: Dict) -> Dict:
    # ... existing message handling ...
    
    # Route AP messages to AP runtime
    if msg.get('type', '').startswith('ap_'):
        return self.ap_runtime.handle_message(msg)
    
    # ... rest of message handling ...
```

### 2.4 Sync State Updates (when ZON4D updates)
```python
def on_state_update(self, state_delta: Dict):
    # ... existing state sync ...
    
    # Sync to AP runtime
    self.ap_runtime.update_state(state_delta)
```

**That's it for Python side!** The AP engine is now operational.

---

## Step 3: Add Godot APBridge

### 3.1 Copy APBridge.gd to Godot project
```bash
cp APBridge.gd /path/to/godot/project/addons/zw/runtime/
# Or wherever your Godot scripts live
```

### 3.2 Modify TestBridge (or your cube click handler)

Open `TestBridge.gd` or `test_bridge.gd`:

```gdscript
extends Node3D

var ap_bridge: APBridge

func _ready():
    # Create AP bridge
    ap_bridge = APBridge.new()
    add_child(ap_bridge)
    
    # Connect to results
    ap_bridge.rule_evaluated.connect(_on_rule_evaluated)
    ap_bridge.tick_simulated.connect(_on_tick_simulated)

func _on_cube_clicked(cube_id: String):
    print("Cube clicked: ", cube_id)
    
    # Build context for this interaction
    var context = {
        "player": "player",
        "target": cube_id
    }
    
    # Ask AP: "What can fire right now?"
    ap_bridge.simulate_tick(context)

func _on_tick_simulated(result: Dictionary):
    print("\n=== AP Tick Simulation ===")
    print("Would apply: ", result.get("would_apply", []))
    print("Would block: ", result.get("would_block", []))
    
    # Use results to tint cubes
    if result.get("would_apply", []).size() > 0:
        _tint_clicked_cube(Color.GREEN)  # Rules can fire
    else:
        _tint_clicked_cube(Color.RED)    # Nothing can fire
        _show_blocked_reasons(result.get("would_block", []))

func _on_rule_evaluated(result: Dictionary):
    print("\n=== AP Rule Evaluation ===")
    print("Eligible: ", result.get("eligible", false))
    
    for req in result.get("requires", []):
        var status = "✓" if req.get("satisfied") else "✗"
        print("  ", status, " ", req.get("predicate"))

func _tint_clicked_cube(color: Color):
    # Your existing cube tinting logic
    pass

func _show_blocked_reasons(blocked: Array):
    for entry in blocked:
        print("  ✗ ", entry.get("rule_id"), ": ", entry.get("reason"))
```

---

## Step 4: Test the Integration

### 4.1 Start Engine
```bash
cd /home/burdens/Downloads/EngAIn/godotengain/engainos
python3 launch_engine.py --scene test_scene
```

You should see:
```
[APRuntime] Initialized with N rules
[APRuntime] Loaded X rules from scene_01.zonj
```

### 4.2 Launch Godot
Open your Godot project and run the test scene with TestBridge.

### 4.3 Click a Cube
You should see in console:
```
Cube clicked: cube_01

=== AP Tick Simulation ===
Would apply: []
Would block: [{"rule_id": "...", "reason": "..."}]
  ✗ interact_cube: Failed requirement: location(player) == "near_cube"
```

### 4.4 Observe Cube Behavior
- Cube should tint RED (rules blocked)
- Console shows why rules didn't fire
- This proves AP engine is evaluating rules from narrative

---

## Step 5: Wire to Real Rules

### 5.1 Check Extracted Rules
```bash
# Look at what rules were extracted from your narrative
python3 -c "
from ap_runtime import APRuntimeIntegration
ap = APRuntimeIntegration()
ap.initialize()
print('Rules:', list(ap.engine._rules.keys()))
"
```

### 5.2 Modify Context for Real Game State
Update your cube click handler to use actual game state:

```gdscript
func _on_cube_clicked(cube_id: String):
    var context = {
        "player": get_player_id(),
        "target": cube_id,
        # Add other relevant entities
    }
    
    # Check if player can interact
    ap_bridge.evaluate_rule("interact_object", context)
```

### 5.3 Add State Updates
When game state changes (player moves, picks up item), notify AP:

```python
# In sim_runtime.py
def on_player_move(self, new_location: str):
    state_delta = {
        'locations': {
            'player': new_location
        }
    }
    self.ap_runtime.update_state(state_delta)
```

---

## Troubleshooting

### "AP not initialized" error
- Check that `ap_runtime.initialize()` was called
- Check that scenes directory path is correct
- Verify ZONJ files exist and are valid JSON

### "No rules loaded"
- Check scenes directory contains .zonj files
- Verify ZONJ files have 'events' or 'rules' sections
- Check console for load errors

### "Rule not found" error
- Use `ap_bridge.list_rules()` to see available rules
- Check that rule_id matches extracted rules
- Verify rule extraction from ZONJ worked

### HTTP connection failed
- Check sim_runtime.py is running
- Verify port 8765 (or your configured port)
- Check APBridge runtime_url matches server

### Predicates always return false
- Check state_provider has correct state
- Verify context entities exist in state
- Use `evaluate_rule_explain` to see predicate results

---

## What This Proves

Once working, you have:

✅ **Narrative → Rules Extraction** (Pass1-3 → ZONJ → AP rules)  
✅ **AP Engine Evaluation** (rules check state, resolve conflicts)  
✅ **Runtime Integration** (Python engine processes AP queries)  
✅ **Godot Visualization** (cubes tint based on rule eligibility)  
✅ **Complete Pipeline** (story text → playable behavior)

This is **not theory** - it's executable code following your AP v1 specs.

---

## Next Steps (Optional)

After basic integration works:

1. **Add More Rule Types**
   - Combat rules from narrative
   - Dialogue triggers
   - Quest progression

2. **Enhanced Visualization**
   - Show requirement checklist in UI
   - Display conflicting rules
   - Highlight which predicates failed

3. **State Inspection**
   - Add debug UI showing current state
   - Display active flags/stats
   - Show rule fire history

4. **Predictive Preview**
   - Show what *would* happen before player acts
   - Display consequences of actions
   - Preview state changes

5. **Multi-Rule Orchestration**
   - Chain rule fires
   - Event sequences
   - Complex narrativ workflows

---

## File Checklist

✅ `ap_engine.py` - Core AP v1 implementation  
✅ `ap_runtime.py` - sim_runtime integration  
✅ `APBridge.gd` - Godot communication  
✅ `engain_bridge.py` - Standalone testing  
✅ This guide

**Everything needed is provided. Time to wire it together!**
