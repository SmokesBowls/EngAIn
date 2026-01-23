# THIN CLIENT QUICK START GUIDE

## Two Testing Approaches

### Approach 1: File-Based (START HERE) ✓
**Easiest to test, validates rendering immediately**
- Python writes snapshots to `/tmp/engain_snapshot.json`
- Godot reads file every frame
- No subprocess complexity

### Approach 2: Subprocess-Based (LATER)
**Production-ready, real-time IPC**
- Godot spawns Python process
- Communicates via stdin/stdout
- More complex setup

---

## Quick Test (File-Based)

### Step 1: Start Python Runtime

```bash
cd ~/Downloads/EngAIn/zonengine4d/zon4d/sim

# Copy test file to sim directory
cp ~/Downloads/sim_runtime_file_test.py .

# Run Python runtime
python3 sim_runtime_file_test.py
```

**Expected Output:**
```
=== Spawning Test Scene ===
[SPAWN] guard at [-3, 0, 0] with 100.0/100.0 HP
[SPAWN] enemy at [3, 0, 0] with 50.0/50.0 HP
[SPAWN] wall at [0, 0, 0] with 100.0/100.0 HP

[FILE TEST] Writing snapshots to: /tmp/engain_snapshot.json
[FILE TEST] Reading commands from: /tmp/engain_command.json

Press Ctrl+C to stop

[TICK 60] Snapshot written
[TICK 120] Snapshot written
...
```

**Leave this running!**

---

### Step 2: Create Godot Scene

**In your clean Godot project:**

1. **Create scripts folder:**
   - FileSystem → Create Folder → `scripts`

2. **Add test client script:**
   - Copy `sim_client_file_test.gd` to `res://scripts/`

3. **Create new 3D scene:**
   - Scene → New Scene → 3D Scene
   - Rename root to "ThinClientTest"
   - Attach script: `res://scripts/sim_client_file_test.gd`

4. **Add Camera:**
   - Add Child → Camera3D
   - Position: (0, 10, 15)
   - Rotation: (-30, 0, 0)

5. **Add Light:**
   - Add Child → DirectionalLight3D
   - Rotation: (-45, -45, 0)

6. **Save scene:**
   - `res://thin_client_test.tscn`

---

### Step 3: Run Godot Scene

1. Press **F5** (or click Play)
2. Set as main scene if asked

**What You Should See:**

```
════════════════════════════════════════════════════════
ENGAIN FILE-BASED TEST CLIENT
════════════════════════════════════════════════════════

Make sure Python runtime is running:
  cd ~/Downloads/EngAIn/zonengine4d/zon4d/sim
  python3 sim_runtime_file_test.py

Controls:
  SPACE - Enemy attacks Guard (25 damage)
  ENTER - Guard attacks Enemy (15 damage)
  1 - Enemy heavy attack (80 damage)
  2 - Guard heavy attack (50 damage)
  Q - Quit
════════════════════════════════════════════════════════

[CLIENT] Created entity: guard
[CLIENT] Created entity: enemy
[CLIENT] Created entity: wall
```

**In the 3D viewport:**
- Green cube (Guard) at left
- Dark red cube (Enemy) at right
- Gray cube (Wall) at center
- Labels showing: "guard\n100/100 HP\nidle"

---

### Step 4: Test Combat

**Press SPACE repeatedly:**

1. Guard takes 25 damage
2. Health bar label updates: "75/100 HP"
3. After 4 hits → "25/100 HP" → Cube turns RED
4. Python console shows: `[BEHAVIOR] guard → fleeing`
5. Label shows: "guard\n25/100 HP\nfleeing"
6. One more hit → Guard dies, cube turns BLACK

**Press ENTER:**
- Enemy takes 15 damage
- Similar visual feedback

**Python Console Shows:**
```
[COMMAND] enemy attacks guard for 25.0 damage
[COMBAT] 1 alert deltas
  → Behavior flag: guard now has 'low_health'
[BEHAVIOR] guard → fleeing

[COMMAND] enemy attacks guard for 25.0 damage
[COMBAT] 2 alert deltas
  → Behavior flag: guard now has 'dead'
  → Navigation disabled for guard
[BEHAVIOR] guard → dead
```

---

## What This Proves

✅ **Python sim is authority** - All logic runs in Python  
✅ **Godot is renderer** - Just displays Python's state  
✅ **Combat3D works visually** - Health, damage, death all visible  
✅ **Real-time sync** - 60 updates per second  
✅ **Commands work** - Godot → Python communication validated  

---

## Manual Testing (Terminal)

You can also test Python directly:

```bash
# In another terminal, while Python is running:
echo '{"type":"attack","source":"enemy","target":"guard","damage":80}' > /tmp/engain_command.json

# Watch Python console:
[COMMAND] enemy attacks guard for 80.0 damage
[COMBAT] 1 alert deltas
  → Behavior flag: guard now has 'low_health'
[BEHAVIOR] guard → fleeing
```

Then watch Godot update automatically!

---

## Troubleshooting

### Python not writing file
```bash
# Check if file exists:
cat /tmp/engain_snapshot.json

# Should show JSON with entities
```

### Godot not rendering
- Check Godot output tab for errors
- Verify Camera3D can see origin (0,0,0)
- Check file permissions on `/tmp/engain_snapshot.json`

### Commands not working
```bash
# Test manually:
echo '{"type":"attack","source":"test","target":"guard","damage":10}' > /tmp/engain_command.json

# Watch Python console for [COMMAND] line
```

---

## Next Steps

### Phase 1: Visual Tuning ✓
You're here! Use this to tune:
- Health bar colors
- Entity sizes
- Damage numbers
- Death effects

### Phase 2: Add Features
**In Python only** (no Godot changes needed):
- Flee behavior (guard moves when low health)
- Hit detection
- Projectiles
- Status effects

Godot just renders the new states automatically!

### Phase 3: Production IPC
Once happy with visuals, upgrade to subprocess-based:
- Use `sim_runtime.py` (full version)
- Godot spawns Python process
- Real stdin/stdout pipes
- Remove file-based polling

### Phase 4: Rich Graphics
- Replace cubes with 3D models
- Add animations (idle, attack, death)
- Particle effects
- Sound effects
- Health bars as UI

---

## File Locations

**Python Side:**
```
~/Downloads/EngAIn/zonengine4d/zon4d/sim/
├── sim_runtime_file_test.py  (file-based test)
├── sim_runtime.py             (full subprocess version)
├── combat3d_adapter.py        (existing)
├── spatial3d_adapter.py       (existing)
└── ... (all other adapters)
```

**Godot Side:**
```
~/Downloads/EngAIn/godot/
├── scripts/
│   └── sim_client_file_test.gd
└── thin_client_test.tscn
```

**Shared Files:**
```
/tmp/engain_snapshot.json  (Python writes, Godot reads)
/tmp/engain_command.json   (Godot writes, Python reads)
```

---

## Success Criteria

✅ Python runtime runs without errors  
✅ Godot scene loads with 3 entities visible  
✅ Pressing SPACE damages guard (visible health change)  
✅ Guard turns RED at low health  
✅ Guard turns BLACK on death  
✅ Python console shows combat/behavior events  

If all these work, **you have a functional thin client!**

---

**Status:** Ready to test! Start Python, then Godot. 🚀
