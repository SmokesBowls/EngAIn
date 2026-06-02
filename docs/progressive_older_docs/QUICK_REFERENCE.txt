# EngAIn Subsystem Quick Reference
## 2-Day Pattern (Combat3D + Inventory3D Proven)

---

## 📋 **THE PATTERN (Copy Every Time)**

```
1. Zork Extraction     → 2-3 hours
2. ZW Block Design     → 1-2 hours
3. AP Rules            → 2-3 hours
4. MR Kernel           → 3-4 hours  ← Pure functional, test standalone
5. Adapter             → 1-2 hours
6. Runtime Integration → 1-2 hours  ← BEFORE entity_ids check!
7. HTTP Endpoints      → 30 min
8. Test with Curl      → 30 min
9. Godot Client        → 1-2 hours
10. Visual Test        → 1 hour
----------------------------
TOTAL: 12-19 hours (1.5-2.5 days)
```

---

## ✅ **PROVEN SUBSYSTEMS**

### **Combat3D**
- Semantic: attack, damage, death, wound_states
- Constraints: alive check, health bounds
- Time: 1 day (with debugging)

### **Inventory3D**
- Semantic: take, drop, wear, weight, count
- Constraints: LOAD_ALLOWED, FUMBLE_NUMBER
- Time: 4 hours (pattern proven)

---

## 🔧 **CRITICAL INTEGRATION POINTS**

### **1. MR Kernel Signature (ALWAYS)**
```python
def step_subsystem(
    snapshot_in: Dict[str, Any],
    deltas: List[Dict[str, Any]],
    dt: float
) -> Tuple[Dict[str, Any], List[Dict], List[Dict]]:
    # Pure functional
    # NO side effects
    # Deep copy input
    # Return new state + alerts
```

### **2. Runtime Integration (CRITICAL ORDER)**
```python
def _update_subsystems(self, dt: float):
    # Combat FIRST (before entity_ids!)
    if self.combat:
        combat_deltas, combat_alerts = self.combat.tick(dt)
    
    # Inventory SECOND (before entity_ids!)
    if self.inventory:
        inv_deltas, inv_alerts = self.inventory.tick(dt)
    
    # THEN get entity_ids
    entity_ids = list(self.snapshot["entities"].keys())
    
    if not entity_ids:
        return  # Early return OK now
    
    # Spatial, Perception, Behavior, etc.
```

**WHY:** Some subsystems don't need entities in main snapshot!

### **3. Adapter Pattern (ALWAYS)**
```python
class SubsystemAdapter:
    def __init__(self):
        self.state = {"entities": {}, "items": {}}
        self.delta_queue = []
    
    def handle_delta(self, delta_type, payload):
        self.delta_queue.append(...)
    
    def tick(self, dt):
        snapshot_in = {"subsystem": self.state}
        snapshot_out, accepted, alerts = step_subsystem(...)
        self.state = snapshot_out["subsystem"]
        self.delta_queue.clear()
        return (processed, alerts)
```

### **4. HTTP Endpoint Pattern (ALWAYS)**
```python
elif self.path == "/subsystem/action":
    data = json.loads(body.decode('utf-8'))
    if self.runtime.subsystem:
        self.runtime.subsystem.handle_delta("subsystem/action", data)
        response = {"type": "ack", "status": "action_queued"}
    self._send_json_response(response)
```

---

## 🧪 **TESTING CHECKLIST**

```bash
# 1. Test MR kernel standalone
cd ~/godotsim
python3 subsystem_mr.py
# → Should print test results, no errors

# 2. Start runtime
python3 sim_runtime.py
# → Should see "✓ Subsystem" in startup

# 3. Test HTTP endpoint
curl -X POST http://localhost:8080/subsystem/action \
  -H "Content-Type: application/json" \
  -d '{"actor":"player","target":"item"}'
# → Should get {"type": "ack", ...}

# 4. Check alerts in runtime console
# → Should see "[SUBSYSTEM] N alerts"

# 5. Verify snapshot
curl http://localhost:8080/snapshot | jq '.payload.subsystem'
# → Should show updated state
```

---

## 🎯 **SEMANTIC DOMAIN MAPPING**

### **Combat → harm_domain**
- Verbs: attack, defend, dodge
- States: wounded, badly_wounded, dead
- Properties: health, damage, armor

### **Inventory → possession_domain**
- Verbs: take, drop, wear, use
- States: held, worn, equipped
- Properties: weight, size, capacity

### **Dialogue → communication_domain**
- Verbs: say, ask, persuade, learn
- States: dialogue_active, branch_unlocked
- Properties: reputation, knowledge_flags

### **Quest → goal_domain**
- Verbs: start, progress, complete, fail
- States: not_started, active, completed
- Properties: objectives, rewards

---

## ⚠️ **COMMON MISTAKES**

### **Mistake 1: Indentation**
```python
# WRONG - Combat inside behavior if-block
if self.behavior and entity_ids:
    # behavior code
    if self.combat:  # ← NEVER RUNS!

# RIGHT - Combat at same level
if self.behavior:
    # behavior code

if self.combat:  # ← RUNS EVERY FRAME
```

### **Mistake 2: Early Return**
```python
# WRONG - Combat after early return
if not entity_ids:
    return

if self.combat:  # ← NEVER RUNS if no entities!

# RIGHT - Combat BEFORE entity_ids check
if self.combat:
    # runs first

if not entity_ids:
    return
```

### **Mistake 3: Side Effects in MR Kernel**
```python
# WRONG - Mutates input
def step_subsystem(snapshot_in, deltas, dt):
    snapshot_in["combat"]["health"] -= 10  # ← MUTATES INPUT!

# RIGHT - Deep copy, return new
def step_subsystem(snapshot_in, deltas, dt):
    snapshot_out = {"combat": {}}
    snapshot_out["combat"]["health"] = snapshot_in["combat"]["health"] - 10
    return snapshot_out, [], []
```

---

## 📊 **CURRENT STACK STATUS**

```
RUNTIME: ~/godotsim/sim_runtime.py
├── ✅ Combat3D
│   ├── combat3d_mr.py (kernel)
│   └── combat3d_integration.py (adapter)
├── ✅ Inventory3D
│   ├── inventory3d_mr.py (kernel)
│   └── inventory3d_integration.py (adapter)
├── ⬜ Dialogue3D (next)
├── ⬜ Quest3D
└── ⬜ Crafting3D

CLIENT: ~/Downloads/EngAIn/godot/
└── scripts/ZWRuntime.gd
    ├── apply_damage()
    ├── inventory_take()
    ├── inventory_drop()
    └── state_updated signal
```

---

## 🚀 **NEXT SUBSYSTEM: DIALOGUE3D**

### **Zork/Obsidian Extraction:**
```bash
cd ~/Downloads/zork3-master
rg -n "TELL|ASK|ANSWER|TALK" .
# Look for dialogue patterns
```

### **Semantic Atoms:**
- Verbs: SAY, ASK, TELL, PERSUADE
- States: dialogue_active, branch_available
- Properties: reputation, knowledge_flags

### **Time Estimate:** 12-15 hours

---

## 💾 **BACKUP COMMAND**

```bash
cd ~
tar -czf engain_backup_$(date +%Y%m%d_%H%M%S).tar.gz godotsim/
```

**Run after EVERY working subsystem!**

---

## 🎯 **SUCCESS = PATTERN REPETITION**

```
Day 1: Combat3D    → 15 hours (learning pattern)
Day 2: Inventory3D → 12 hours (pattern proven)
Day 3: Dialogue3D  → 12 hours (copy-paste)
Day 4: Quest3D     → 12 hours (copy-paste)
Day 5: Crafting3D  → 12 hours (copy-paste)
```

**The pattern scales. The methodology works. Zork proves it.**

---

**KEEP THIS FILE OPEN WHILE BUILDING SUBSYSTEMS** 📌
