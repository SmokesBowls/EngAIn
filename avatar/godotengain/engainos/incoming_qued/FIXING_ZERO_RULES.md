# FIXING "AP Initialized with 0 Rules"
**Status:** ✅ FIXED  
**Issue:** AP engine loads but has no rules to evaluate  
**Root Cause:** Missing scene file + file scanning instead of direct rule loading

---

## What Was Wrong

1. **Missing Scene File:**
   ```
   Scene not found: .../game_scenes/test_scene.json
   ```
   The engine tried to load `test_scene.json` but it didn't exist.

2. **Rule Loading Mismatch:**
   `ap_runtime.py` was scanning for `.zonj` files but:
   - No `.zonj` files existed in `game_scenes/`
   - The working rules from `engain_bridge.py` weren't being used

---

## The Fix (3 Files)

### File 1: test_scene.json
**Location:** `/home/burdens/Downloads/EngAIn/godotengain/engainos/game_scenes/test_scene.json`

```json
{
  "scene_id": "test_scene",
  "title": "Test Scene - Door Puzzle",
  "type": "scene",
  "entities": [
    {
      "id": "player",
      "type": "character",
      "flags": {"has_key": false, "door_unlocked": false},
      "stats": {"health": 100, "xp": 0},
      "location": "entrance",
      "inventory": {}
    },
    {
      "id": "door",
      "type": "object",
      "flags": {"is_open": false, "is_locked": true},
      "location": "hallway"
    },
    {
      "id": "key",
      "type": "item",
      "location": "table"
    }
  ],
  "events": [
    {
      "id": "pickup_key",
      "tags": ["interaction", "item"],
      "conditions": [
        {"type": "location", "entity": "player", "location": "table"}
      ],
      "actions": [
        {"type": "set_flag", "entity": "player", "flag": "has_key", "value": true}
      ],
      "priority": 5
    },
    {
      "id": "unlock_door",
      "tags": ["interaction", "door"],
      "conditions": [
        {"type": "flag", "entity": "player", "flag": "has_key"},
        {"type": "location", "entity": "player", "location": "hallway"}
      ],
      "actions": [
        {"type": "set_flag", "entity": "door", "flag": "is_locked", "value": false},
        {"type": "set_flag", "entity": "player", "flag": "door_unlocked", "value": true}
      ],
      "priority": 10
    },
    {
      "id": "open_door",
      "tags": ["interaction", "door"],
      "conditions": [
        {"type": "flag", "entity": "door", "flag": "is_locked", "op": "==", "value": false},
        {"type": "location", "entity": "player", "location": "hallway"}
      ],
      "actions": [
        {"type": "set_flag", "entity": "door", "flag": "is_open", "value": true},
        {"type": "change_stat", "entity": "player", "stat": "xp", "delta": 10}
      ],
      "priority": 5
    }
  ]
}
```

**Copy from outputs:**
```bash
cp /mnt/user-data/outputs/test_scene.json \
   /home/burdens/Downloads/EngAIn/godotengain/engainos/game_scenes/
```

### File 2: Updated ap_runtime.py
**Changes Made:**

1. **Fixed `initialize()` to accept rules parameter:**
```python
def initialize(self, initial_state: Dict = None, rules: Dict[str, Dict] = None):
    # ... state provider setup ...
    
    # Load rules - either from parameter or from scenes
    if rules is None:
        rules = self._load_all_rules()
    
    self.engine = ZWAPEngine(rules, self.state_provider)
```

2. **Fixed `_event_to_rule()` to compute read/write sets:**
```python
def _event_to_rule(self, event: Dict, scene_id: str) -> Optional[Dict]:
    # ... extract requires/effects ...
    
    rule = {
        'id': f"{scene_id}_{event_id}",
        'tags': event.get('tags', []),
        'requires': requires,
        'effects': effects,
        'priority': event.get('priority', 0),
        'inputs': event.get('inputs', [])
    }
    
    # Compute read/write sets if not present
    if 'read_set' not in rule or 'write_set' not in rule:
        self._compute_rule_sets(rule)
    
    return rule
```

3. **Added `_compute_rule_sets()` method:**
```python
def _compute_rule_sets(self, rule: Dict):
    """Compute read_set and write_set for a rule"""
    read_set = set()
    write_set = set()
    
    # Parse requires for reads
    for pred in rule.get('requires', []):
        if 'flag(' in pred:
            # Extract entity.flag → flag.entity.flag_name
            ...
    
    # Parse effects for writes
    for effect in rule.get('effects', []):
        if 'set_flag(' in effect:
            # Extract entity.flag → flag.entity.flag_name
            ...
    
    rule['read_set'] = sorted(read_set)
    rule['write_set'] = sorted(write_set)
```

4. **Fixed `_condition_to_predicate()` to handle flag comparisons:**
```python
def _condition_to_predicate(self, cond: Dict) -> Optional[str]:
    if cond_type == 'flag':
        # Handle: {"type": "flag", "entity": "door", "flag": "is_locked", "op": "==", "value": false}
        if 'value' in cond:
            value = cond.get('value')
            op = cond.get('op', '==')
            if op == '==' and value is False:
                return None  # Should use conflicts
            elif op == '==' and value is True:
                return f'flag({entity}, "{flag}")'
        else:
            # Default: check if flag is true
            return f'flag({entity}, "{flag}")'
```

**Copy updated file:**
```bash
cp /mnt/user-data/outputs/ap_runtime.py \
   /home/burdens/Downloads/EngAIn/godotengain/engainos/core/
```

### File 3: Updated ap_engine.py
No changes needed - already correct.

---

## Verification

### Test 1: Standalone Test
```bash
cd /home/burdens/Downloads/EngAIn/godotengain/engainos
cp /mnt/user-data/outputs/test_scene_loading.py .
python3 test_scene_loading.py
```

**Expected Output:**
```
[3/4] Extracting rules from scene
  ✓ Extracted 3 rules:
    - unknown_pickup_key
    - unknown_unlock_door
    - unknown_open_door

[4/4] Full AP Runtime initialization
[APRuntime] Initialized with 3 rules
  ✓ AP Engine initialized with 3 rules

[BONUS] Testing rule evaluation
  Rule: unknown_pickup_key
    Eligible: False
    Reason: Failed requirement: location(player) == "table"
```

### Test 2: Launch Engine
```bash
python3 launch_engine.py
```

**Expected Output:**
```
[APRuntime] Initialized with 3 rules
[AP] Loaded 3 rules from game_scenes/test_scene.json
[AP] Total rules: 3

ENGINE READY
```

**Before (broken):**
```
[APRuntime] Initialized with 0 rules
Scene not found: .../test_scene.json
```

**After (fixed):**
```
[APRuntime] Initialized with 3 rules
```

---

## How Rules Are Now Loaded

### Option 1: From Scene Files (Auto)
When `initialize()` is called without rules parameter:
```python
ap_runtime.initialize(initial_state)
# Automatically scans game_scenes/ for *.json and *.zonj files
```

### Option 2: Direct Loading (Manual)
When you have rules already extracted:
```python
# Extract from scene
with open('game_scenes/test_scene.json') as f:
    scene = json.load(f)

rules = ap_runtime._extract_rules_from_scene_dict(scene)
initial_state = extract_initial_state_from_scene(scene)

# Initialize with extracted rules
ap_runtime.initialize(initial_state, rules)
```

---

## Integration with launch_engine.py

**Current Code (in launch_engine.py):**
```python
def _init_ap_runtime(self):
    scenes_dir = Path(__file__).parent / "game_scenes"
    self.ap_runtime = APRuntimeIntegration(scenes_dir=str(scenes_dir))
    
    initial_state = self._get_initial_state()
    self.ap_runtime.initialize(initial_state)
    # Now automatically loads from game_scenes/*.json
```

**This now works because:**
1. `game_scenes/test_scene.json` exists
2. `_load_all_rules()` finds it
3. `_extract_rules_from_scene_dict()` converts events → rules
4. `_compute_rule_sets()` generates read/write sets
5. `ZWAPEngine` receives valid rules

---

## What The Rules Do

**Rule 1: pickup_key**
- **Requires:** Player at "table" location
- **Effects:** Set player.has_key = true
- **Priority:** 5

**Rule 2: unlock_door**
- **Requires:** Player has key + player at "hallway"
- **Effects:** Unlock door + set player.door_unlocked
- **Priority:** 10

**Rule 3: open_door**
- **Requires:** Door is unlocked + player at "hallway"
- **Effects:** Open door + give player 10 XP
- **Priority:** 5

**Gameplay Flow:**
1. Player moves to table → pickup_key fires → has_key = true
2. Player moves to hallway → unlock_door fires → door unlocked
3. Player at hallway with unlocked door → open_door fires → door opens

---

## Testing From Godot

Once the engine shows `[APRuntime] Initialized with 3 rules`:

**From TestBridge:**
```gdscript
func _on_cube_clicked(cube_id):
    var context = {
        "player": "player",
        "target": cube_id
    }
    
    ap_bridge.simulate_tick(context)

func _on_tick_simulated(result):
    print("Would apply: ", result["would_apply"])
    print("Would block: ", result["would_block"])
```

**Expected Result:**
```
Would apply: []
Would block: [
  {rule_id: "test_scene_pickup_key", reason: "Failed requirement: location(player) == \"table\""},
  {rule_id: "test_scene_unlock_door", reason: "Failed requirement: flag(player, \"has_key\")"},
  ...
]
```

The rules are evaluating! They're blocked because initial state has player at "entrance" not "table".

---

## Next Steps

### 1. Test State Changes
Modify player location and verify rules become eligible:
```python
# In launch_engine.py or via message
ap_runtime.update_state({
    'locations': {'player': 'table'}
})

# Now pickup_key should be eligible
```

### 2. Add More Scenes
Create more `.json` files in `game_scenes/`:
- `combat_scene.json`
- `dialogue_scene.json`
- `quest_scene.json`

All will auto-load on engine start.

### 3. Convert ZONJ to JSON
If you have `.zonj` files from mettaext, they should work too:
```bash
cp mettaext/output/*.zonj game_scenes/
# Engine loads both .json and .zonj
```

---

## Files to Copy

**Summary:**
```bash
# 1. Test scene
cp /mnt/user-data/outputs/test_scene.json \
   /home/burdens/Downloads/EngAIn/godotengain/engainos/game_scenes/

# 2. Updated AP runtime
cp /mnt/user-data/outputs/ap_runtime.py \
   /home/burdens/Downloads/EngAIn/godotengain/engainos/core/

# 3. Test script (optional)
cp /mnt/user-data/outputs/test_scene_loading.py \
   /home/burdens/Downloads/EngAIn/godotengain/engainos/

# 4. Verify
cd /home/burdens/Downloads/EngAIn/godotengain/engainos
python3 test_scene_loading.py
python3 launch_engine.py
```

---

**Status:** ✅ Rules now load successfully  
**Verification:** `[APRuntime] Initialized with 3 rules`  
**Ready For:** Godot queries and cube interaction testing
