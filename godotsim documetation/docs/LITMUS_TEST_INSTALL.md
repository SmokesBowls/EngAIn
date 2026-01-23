# LITMUS TEST INSTALLATION GUIDE

## Quick Install (Manual Editing)

### File 1: ZWRuntime.gd

**Add these variables after line 17:**
```gdscript
var rendering_paused = false
var last_snapshot = null  # Store for litmus test
```

**Add these functions at the END of ZWRuntime.gd:**
```gdscript
func pause_rendering():
	rendering_paused = true
	print("ZWRuntime: Rendering PAUSED")

func resume_rendering():
	rendering_paused = false
	print("ZWRuntime: Rendering RESUMED")
	_request_next_snapshot()
```

**Modify _on_snapshot_completed function:**

Find this section (around line 50-60):
```gdscript
	var data = json.data
	on_world_state_updated(data)
	_request_next_snapshot()
```

Replace with:
```gdscript
	var data = json.data
	
	# Store snapshot for litmus test
	last_snapshot = data
	
	# Skip rendering if paused (but keep polling)
	if rendering_paused:
		print("ZWRuntime: Snapshot received but rendering paused")
		_request_next_snapshot()
		return
	
	on_world_state_updated(data)
	_request_next_snapshot()
```

---

### File 2: TestZWScene.gd

**Modify _input function to add KEY_L:**

Find the _input function (around line 66):
```gdscript
func _input(event):
	if event is InputEventKey and event.pressed:
		match event.keycode:
			KEY_1:
				_test_greeter_low_rep()
			KEY_2:
				_test_greeter_high_rep()
			KEY_3:
				_test_merchant()
			KEY_L:  # ← ADD THIS LINE
				_run_litmus_test()  # ← ADD THIS LINE
```

**Add this function at the END of TestZWScene.gd:**
```gdscript
func _run_litmus_test():
	"""Litmus test: Does client snap to authority or hold state?"""
	print("\n" + "="*50)
	print("LITMUS TEST START")
	print("="*50)
	
	# Note current state
	if zw_runtime.last_snapshot and zw_runtime.last_snapshot.has("entities"):
		print("\nBefore pause:")
		for eid in zw_runtime.last_snapshot.entities:
			var entity = zw_runtime.last_snapshot.entities[eid]
			if entity.has("position"):
				print("  %s: %s" % [eid, entity.position])
	else:
		print("\nNo snapshot available yet")
		return
	
	# Pause rendering
	zw_runtime.pause_rendering()
	print("\nRendering PAUSED - Python still running...")
	
	# Wait for Python to advance
	await get_tree().create_timer(1.0).timeout
	
	# Resume rendering
	zw_runtime.resume_rendering()
	
	# Check results
	await get_tree().create_timer(0.2).timeout
	
	print("\nAfter resume:")
	if zw_runtime.last_snapshot and zw_runtime.last_snapshot.has("entities"):
		for eid in zw_runtime.last_snapshot.entities:
			var entity = zw_runtime.last_snapshot.entities[eid]
			if entity.has("position"):
				print("  %s: %s" % [eid, entity.position])
	
	print("\n" + "="*50)
	print("LITMUS TEST COMPLETE")
	print("="*50)
	print("\nInterpretation:")
	print("  PASS: Positions changed significantly")
	print("  FAIL: Positions unchanged/barely changed")
	print("\nPress L to re-run")
	print("="*50 + "\n")
```

---

## Testing

1. **Apply patches above to ZWRuntime.gd and TestZWScene.gd**
2. **Python already running on port 8080** ✓
3. **Run Godot test scene**
4. **Press button 1 or 2** (spawn greeter - creates entity with physics)
5. **Wait 2 seconds** (let entity fall a bit)
6. **Press L key** (run litmus test)
7. **Watch console output**

---

## Expected Results

### PASS (Good - Client is Stateless)
```
Before pause:
  greeter_main: [5, 0, 3]

After resume:
  greeter_main: [5, -8.2, 3]  ← Big position change!
```
**Entities fell significantly during pause, snapped instantly when resumed.**

### FAIL (Bad - Client Holds State)
```
Before pause:
  greeter_main: [5, 0, 3]

After resume:
  greeter_main: [5, -0.5, 3]  ← Small change or smooth transition
```
**Positions barely changed or smoothly transitioned = client is predicting/holding.**

---

## Next Steps

**If PASS:**
- Client is already stateless! ✅
- Move to refactoring EngAInBridge.gd for cleanliness
- Then Phase 6: Enforcement

**If FAIL:**
- Identify which file holds state
- Refactor to remove forbidden patterns
- Re-test until PASS

---

Save this file as reference during testing!
