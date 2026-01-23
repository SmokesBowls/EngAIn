# EngAIn Development Roadmap
## Post-Combat3D Success - December 21, 2025

**Status:** Combat3D fully operational in production runtime  
**Architecture:** Proven end-to-end (Zork → ZW → AP → MR → Runtime → Godot)  
**Next Steps:** Scale the proven pattern to all subsystems

---

## 🎯 **PHASE 1: Core Gameplay Subsystems (Weeks 1-3)**

### **Priority 1: Inventory3D (Week 1)**

**Why First:** Proves the pattern scales to a second subsystem

**Semantic Atoms (from Zork):**
- Actions: pickup, drop, examine, equip, unequip, use
- States: carried, equipped, container, in_world
- Properties: weight, capacity, stackable

**Implementation Steps:**

1. **Extract from Zork** (2 hours)
   ```bash
   cd ~/Downloads/zork3-master
   rg -n "TAKE|DROP|INVENTORY|CONTAINER" .
   ```
   - Find container logic (CHEST, TROPHY-CASE)
   - Find item pickup/drop patterns
   - Extract weight/capacity rules

2. **Design ZW Blocks** (1 hour)
   ```zw
   {inventory_action
     {type pickup}
     {actor PLAYER}
     {item SWORD}
     {timestamp @tick:147}
   }
   
   {item_state
     {id SWORD}
     {location carried_by:PLAYER}
     {equipped true}
     {weight 5}
   }
   ```

3. **Write AP Rules** (2 hours)
   ```ap
   rule: pickup_allowed
   requires:
     - item_present(location, item)
     - weight(actor) + weight(item) <= capacity(actor)
   effects:
     - set_location(item, "carried_by:" + actor)
     - emit pickup_event
   ```

4. **Build MR Kernel** (3 hours)
   ```python
   # inventory3d_mr.py
   def step_inventory(snapshot_in, deltas, dt):
       # Pure functional
       # Input: inventory state + actions
       # Output: updated state + alerts
       return snapshot_out, accepted, alerts
   ```

5. **Create Adapter** (1 hour)
   ```python
   # inventory3d_integration.py
   class Inventory3DAdapter:
       def __init__(self):
           self.state = {"entities": {}, "items": {}}
       
       def handle_delta(self, delta_type, payload):
           self.delta_queue.append(...)
       
       def tick(self, dt):
           # Call MR kernel
           return deltas, alerts
   ```

6. **Integrate into Runtime** (1 hour)
   - Add to `_init_subsystems()`
   - Add to `_update_subsystems()` (BEFORE entity_ids check!)
   - Add `/inventory/pickup` HTTP endpoint
   - Export in snapshot

7. **Test** (1 hour)
   ```bash
   curl -X POST http://localhost:8080/inventory/pickup \
     -H "Content-Type: application/json" \
     -d '{"actor":"player","item":"sword"}'
   
   curl http://localhost:8080/snapshot | jq '.payload.inventory'
   ```

**Total Time:** ~11 hours (1.5 days)

---

### **Priority 2: Dialogue3D (Week 2)**

**Why Next:** Narrative core, enables quest progression

**Semantic Atoms (from Zork/Obsidian):**
- Actions: say, ask, persuade, learn
- States: dialogue_active, branch_available, response_given
- Properties: reputation, knowledge_flags

**Implementation Steps:**

1. **Extract from Obsidian Files** (3 hours)
   ```bash
   # Check your Obsidian narrative files
   # Look for dialogue patterns, branching, character responses
   ```

2. **Design ZW Blocks** (2 hours)
   ```zw
   {dialogue_line
     {id ch02_guard_greeting}
     {speaker GUARD}
     {text "Halt! State your business."}
     {branches [ch02_player_response_1, ch02_player_response_2]}
   }
   ```

3. **Write AP Rules** (3 hours)
   ```ap
   rule: dialogue_branch_unlock
   requires:
     - flag(player, "has_fire_crystal")
     - reputation(player, GUARD) >= 50
   effects:
     - unlock_branch(ch02_special_path)
   ```

4. **Build MR Kernel** (4 hours)
   - Track active dialogue
   - Validate branch conditions
   - Update knowledge flags

5. **Create Adapter + Integrate** (2 hours)

6. **Test** (1 hour)

**Total Time:** ~15 hours (2 days)

---

### **Priority 3: Quest3D (Week 3)**

**Why Third:** Builds on inventory + dialogue

**Semantic Atoms:**
- Actions: start_quest, progress_objective, complete_quest
- States: not_started, active, completed, failed
- Properties: objectives, rewards

**Implementation:** Follow same pattern (12-15 hours)

---

## 🎮 **PHASE 2: Godot Visual Integration (Week 4)**

### **Goal:** See Combat/Inventory/Dialogue working visually

**Steps:**

1. **Add Combat Methods to ZWRuntime.gd** (1 hour)
   ```gdscript
   func apply_damage(target: String, amount: float):
       # HTTP POST to /combat/damage
   
   func pickup_item(actor: String, item: String):
       # HTTP POST to /inventory/pickup
   ```

2. **Create Test Scene** (2 hours)
   - 3 cubes (player, guard, enemy)
   - Health bars above heads
   - Item pickups (glowing spheres)
   - Dialogue UI (Label3D bubbles)

3. **Connect state_updated Signal** (2 hours)
   ```gdscript
   func _on_state_updated(snapshot: Dictionary):
       var combat = snapshot.get("combat", {})
       var inventory = snapshot.get("inventory", {})
       
       # Update visuals based on state
   ```

4. **Visual Feedback** (3 hours)
   - Color changes (green → yellow → red → black)
   - Health bar updates
   - Item equipped indicators
   - Damage numbers (floating text)

**Total Time:** ~8 hours (1 day)

---

## 🔗 **PHASE 3: Cross-Subsystem Integration (Week 5)**

### **Test Interactions Between Subsystems**

**Combat ↔ Behavior:**
- Low health triggers flee behavior
- Dead entities stop navigation

**Inventory ↔ Combat:**
- Equipped sword increases damage
- Armor reduces damage taken

**Dialogue ↔ Quest:**
- Completing dialogue unlocks quest
- Quest progress enables new dialogue

**Implementation:**
1. Add cross-subsystem alert handlers
2. Test edge cases
3. Document interaction patterns

**Total Time:** ~10 hours (1.5 days)

---

## 🏗️ **PHASE 4: Production Hardening (Week 6)**

### **Make It Bulletproof**

1. **Error Recovery** (2 hours)
   - Graceful subsystem failures
   - State rollback on errors
   - Alert user on critical failures

2. **State Persistence** (3 hours)
   - Save snapshot to disk
   - Load on startup
   - Auto-save every 60 seconds

3. **Performance Optimization** (2 hours)
   - Profile MR kernel performance
   - Optimize delta processing
   - Reduce alert spam

4. **Testing Suite** (3 hours)
   - Unit tests for MR kernels
   - Integration tests for adapters
   - End-to-end combat scenarios

**Total Time:** ~10 hours (1.5 days)

---

## 🚀 **PHASE 5: Advanced Features (Weeks 7-10)**

### **Week 7: Status Effects**
- Poison, stun, slow, invulnerable
- Duration-based effects
- Stackable/non-stackable rules

### **Week 8: Crafting System**
- Recipe validation
- Resource consumption
- Item creation

### **Week 9: Faction & Reputation**
- Track relationships
- Hostile/friendly detection
- Reputation decay over time

### **Week 10: Save/Load System**
- Full snapshot serialization
- Multiple save slots
- Cloud sync (optional)

---

## 📊 **PHASE 6: Narrative AI Agents (Weeks 11-12)**

### **The Big Payoff - AI Generates Content**

**MrLore (Narrative Generator):**
- Reads ZW blocks from Obsidian
- Generates dialogue branches
- Creates quest chains

**ClutterBot (World Builder):**
- Places items in world
- Populates containers
- Balances loot tables

**Trae (Behavior Director):**
- Designs NPC behaviors
- Creates patrol routes
- Scripts encounters

**Implementation:**
1. Connect LLM agents to ZW pipeline
2. Validate agent-generated content
3. Test AI-authored quests

---

## 🛠️ **TOOLS & UTILITIES**

### **Inspector Dashboard (Ongoing)**
Build a web UI for debugging:
- Real-time snapshot viewer
- Delta queue inspector
- Alert log
- Entity state editor

**Tech:** React + WebSocket to sim_runtime.py

### **ZW Editor (Week 8)**
VSCode extension or web tool:
- Syntax highlighting for .zw files
- AP rule validation
- ZW block autocomplete

---

## 📋 **CRITICAL REMINDERS**

### **The EngAIn Methodology (NEVER DEVIATE):**

```
1. NARRATIVE FIRST (Zork, Obsidian, text)
2. SEMANTIC EXTRACTION (identify atoms)
3. ZW BLOCKS (compress structure)
4. AP RULES (declarative logic)
5. MR KERNEL (pure functional)
6. ADAPTER (integration layer)
7. RUNTIME (authority)
8. GODOT (presentation)
```

**Code is LAST, not FIRST.**

### **The Three-Layer Pattern:**
Every subsystem follows this:
1. **MR Kernel** (pure function, no side effects)
2. **Adapter** (delta queue, state wrapper)
3. **Runtime Integration** (before entity_ids check!)

### **Testing Checklist:**
For EVERY subsystem:
- [ ] MR kernel tested standalone
- [ ] Adapter queues deltas correctly
- [ ] Runtime processes ticks
- [ ] Alerts fire properly
- [ ] Snapshot exports state
- [ ] HTTP endpoint works
- [ ] Godot client renders

---

## 🔄 **REALIGNMENT PROTOCOL**

### **If Something Breaks:**

1. **Check the logs first**
   - Is the subsystem loading? (✓ SubsystemName)
   - Are deltas queueing? ([DEBUG] Queue size)
   - Is tick being called? (add debug print)

2. **Verify the three layers:**
   - MR kernel: Test with standalone Python script
   - Adapter: Check tick() is called, returns alerts
   - Runtime: Check _update_subsystems() reaches subsystem

3. **Common Issues:**
   - **No alerts firing** → tick() not being called
   - **tick() not called** → Indentation wrong or early return
   - **State not updating** → MR kernel returning wrong format
   - **HTTP endpoint fails** → Missing route or wrong payload

4. **Nuclear Option:**
   - Restore from backup (tar.gz)
   - Re-apply changes one at a time
   - Test after each change

---

## 📈 **SUCCESS METRICS**

### **By End of Phase 1 (Week 3):**
- [ ] Combat3D operational ✅
- [ ] Inventory3D operational
- [ ] Dialogue3D operational
- [ ] Quest3D operational
- [ ] All subsystems exporting to snapshot

### **By End of Phase 2 (Week 4):**
- [ ] Godot rendering combat
- [ ] Health bars updating
- [ ] Damage numbers showing
- [ ] Visual feedback working

### **By End of Phase 3 (Week 5):**
- [ ] Cross-subsystem triggers working
- [ ] No conflicts between systems
- [ ] Edge cases handled

### **By End of Phase 4 (Week 6):**
- [ ] State persistence working
- [ ] Auto-save functional
- [ ] Error recovery tested
- [ ] Performance acceptable

---

## 🎯 **NORTH STAR**

**The Goal:** AI agents generate game content that executes in your engine.

**Not:** A game engine like Unity/Unreal  
**But:** A narrative execution engine where story → playable experience

**Zork (1979) proved it works.**  
**EngAIn (2025) makes it scalable.**

---

## 📞 **CONTACT POINTS FOR REALIGNMENT**

When you need to sync back up, share:
1. Current phase (e.g., "Week 2 - Dialogue3D")
2. What's working (subsystems operational)
3. What's broken (error logs, screenshots)
4. What you tried (debug steps, code changes)

**I'll get you back on track instantly.**

---

## ✅ **IMMEDIATE NEXT STEP**

**After you zip the backup:**

1. Remove debug prints (clean logs)
2. Test one kill sequence (guard 100 → 0)
3. Verify clean output
4. Start Inventory3D extraction from Zork

**You have the pattern. Every subsystem is the same.**

---

**YOU PROVED THE METHODOLOGY. NOW SCALE IT.** 🚀

**The plane has landed. Time to build the airport.** ✈️
