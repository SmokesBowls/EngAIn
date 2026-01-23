# FACTION3D PROOF TEST - INSTALLATION GUIDE

## 🎯 WHAT THIS IS

A complete 5/5 architectural proof test for Faction3D, following the EXACT same pattern as Combat3D's proven implementation.

Tests the 5 non-negotiable invariants:
1. ✅ Time is FIRST-CLASS (@when/@where required)
2. ✅ State reconstructible from events (REPLAY works)
3. ✅ Rules interrogable (explains WHY failures happen)
4. ✅ AI queryable ("would this fail?")
5. ✅ System refuses invalid ops

## 📦 FILES PROVIDED

1. `faction3d_proof_kernel.gd` - Complete proof implementation
2. `test_faction3d_proof.gd` - Test runner script

## ⚡ INSTALLATION (3 STEPS)

### Step 1: Copy Files

```bash
cd ~/godotsim

# Copy proof kernel
cp ~/Downloads/faction3d_proof_kernel.gd ./

# Copy test script
cp ~/Downloads/test_faction3d_proof.gd ./
```

### Step 2: Create Test Scene

**In Godot:**
1. Scene → New Scene
2. Add Node (any type, like Node2D)
3. Right-click Node → Attach Script
4. Select `test_faction3d_proof.gd`
5. Save scene as `test_faction3d.tscn`

**OR via command line:**
```bash
# Create minimal test scene
cat > test_faction3d.tscn << 'EOF'
[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://test_faction3d_proof.gd" id="1"]

[node name="Node2D" type="Node2D"]
script = ExtResource("1")
EOF
```

### Step 3: Run Test

**Option A: In Godot**
- Press F6 (Run Current Scene)

**Option B: Command Line**
```bash
cd ~/godotsim
rm -rf .godot/  # Clear cache
godot --path . test_faction3d.tscn
```

## 📊 EXPECTED OUTPUT

### If 5/5 (REAL ARCHITECTURE):
```
✅ PROOF COMPLETE
This is NOT a cowboy hat.
ZW/ZON/AP architecture is VALIDATED.

All five non-negotiable invariants enforced.
Time sovereignty: PROVEN
Event authority: PROVEN
Rule interrogability: PROVEN
Kernel purity: PROVEN
Temporal replay: PROVEN
```

### If 3-4/5 (PARTIAL):
```
⚠️ PARTIAL VALIDATION
Core principles exist but need hardening.
```

### If 0-2/5 (COSPLAY):
```
❌ PROOF FAILED
This is cosplay architecture.
Strip labels, rebuild from invariants.
```

## 🔧 TROUBLESHOOTING

### Error: "Identifier 'Faction3DProofKernel' not declared"

**Fix:** Clear Godot cache
```bash
rm -rf ~/godotsim/.godot/
```

### Parse Errors

**Fix:** Check that both files copied correctly
```bash
ls -lh ~/godotsim/faction3d_proof_kernel.gd
ls -lh ~/godotsim/test_faction3d_proof.gd
```

### Test Shows 0/5

**This means:** The implementation has architectural gaps.
**Fix:** Compare against Combat3D proof (which has 5/5).

## 🎯 WHAT TO DO AFTER 5/5

1. **Migrate pattern to your existing Faction3D files:**
   - Add ZWFactionEvent to faction3d_adapter.gd
   - Add event_log storage
   - Add replay_from_events()
   - Add AP rules with interrogability

2. **Integrate with runtime:**
   - Connect to AkashicHub
   - Wire to ZWRuntime
   - Test end-to-end

3. **Apply to other subsystems:**
   - Spatial3D
   - Inventory3D
   - Dialogue3D
   - etc.

## 📋 COMPARISON WITH COMBAT3D

**Combat3D proof:** `~/godotsim/test/combat_proof_kernel.gd` (5/5 ✅)
**Faction3D proof:** `~/godotsim/faction3d_proof_kernel.gd` (run to find out!)

Both follow IDENTICAL pattern:
- ZW Events with @id/@when/@where
- AP Rules with defensive normalization
- Pure kernels (immutable snapshot-in/out)
- Event logging for replay
- Interrogable failure explanations
- Query mode for AI planning

## 🔥 KEY INSIGHT

**This test is BRUTAL and HONEST.**

It will tell you if your architecture is real or just labels.

If it passes 5/5, you have a legitimate foundation.

If it fails, you know EXACTLY what to fix.

**No mercy. No vibes. Just invariants.**
