# Fix EngAInBridge Preload Error

## What Happened

EngAInBridge.gd has this line (around line 27):
```gdscript
zw_runtime = preload("res://addons/zw/runtime/ZWRuntime.gd").new()
```

This tries to load ZWRuntime from a folder structure that doesn't exist in your project.

## Quick Fix

Replace your `EngAInBridge.gd` with `EngAInBridge_fixed.gd`

The fixed version:
- ✅ Finds existing ZWRuntime using `get_tree().get_first_node_in_group()`
- ✅ Creates one dynamically if needed using `load()` not `preload()`
- ✅ No hard-coded addon paths
- ✅ Works with your project structure

## Why This Happened

The original EngAInBridge assumed you'd organize files like:
```
res://
  addons/
    zw/
      runtime/
        ZWRuntime.gd  ← Looking here
```

But your project has:
```
res://
  ZWRuntime.gd  ← Actually here
```

## If You Get This Error Again

Any script that tries to `preload("res://addons/...")` needs to be updated to either:

1. **Find existing nodes:**
   ```gdscript
   var zw = get_tree().get_first_node_in_group("zw_runtime")
   ```

2. **Load dynamically:**
   ```gdscript
   var script = load("res://ZWRuntime.gd")
   var zw = Node.new()
   zw.set_script(script)
   ```

3. **Remove preload entirely** if ZWRuntime already exists in the scene

## For Your Current Scene

Since you're working with the test scene, you don't need EngAInBridge right now anyway! 

**Just focus on TestZWScene** - that's all you need for testing. The EngAInBridge script is for the more complex isometric scene later.

The error probably appeared because Godot scanned all scripts in your project folder. It won't affect your current test scene.

---

**TL;DR**: Replace EngAInBridge.gd with the fixed version, or just ignore it for now since you're testing with TestZWScene.
