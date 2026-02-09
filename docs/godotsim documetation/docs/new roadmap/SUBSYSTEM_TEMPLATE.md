# EngAIn Subsystem Template
## Copy-Paste Pattern for Building Any New Subsystem

**Proven with Combat3D - Replicate for Inventory, Dialogue, Quest, etc.**

---

## 📋 **CHECKLIST (Use This Every Time)**

```
[ ] 1. Extract semantic atoms from Zork/Obsidian
[ ] 2. Design ZW block format
[ ] 3. Write AP rules
[ ] 4. Build MR kernel (pure functional)
[ ] 5. Create adapter class
[ ] 6. Integrate into sim_runtime.py
[ ] 7. Add HTTP endpoint
[ ] 8. Test with curl
[ ] 9. Add Godot client support
[ ] 10. Visual test
```

---

## 🔧 **STEP-BY-STEP IMPLEMENTATION**

### **Step 1: Extract Semantic Atoms (2-3 hours)**

**Zork extraction:**
```bash
cd ~/Downloads/zork3-master
rg -n "KEYWORD1|KEYWORD2|KEYWORD3" .
```

**Identify:**
- **Verbs** (actions): pickup, drop, attack, talk
- **States** (conditions): carried, equipped, wounded, hostile
- **Properties** (attributes): weight, damage, health

**Document in a .txt file:**
```
SUBSYSTEM: Inventory3D

VERBS: pickup, drop, examine, equip, unequip, use
STATES: carried, equipped, in_world, in_container
PROPERTIES: weight, capacity, stackable, equippable
FLAGS: is_key, is_weapon, is_consumable

ZORK PATTERNS:
- Weight limit check before pickup
- Container capacity rules
- Equip slots (weapon, armor, accessory)
```

---

### **Step 2: Design ZW Blocks (1-2 hours)**

**Create:** `subsystem_zw_blocks.txt`

```zw
# Action block
{subsystem_action
  {id action_147}
  {type verb_name}
  {actor ENTITY_ID}
  {target ENTITY_ID or ITEM_ID}
  {timestamp @tick:147}
}

# State block
{subsystem_state
  {id ENTITY_ID}
  {property_1 value}
  {property_2 value}
  {state state_name}
  {@tick 147}
}
```

**Example (Inventory):**
```zw
{inventory_action
  {id pickup_147}
  {type pickup}
  {actor PLAYER}
  {item SWORD}
  {@tick 147}
}

{item_state
  {id SWORD}
  {location carried_by:PLAYER}
  {equipped true}
  {weight 5}
}
```

---

### **Step 3: Write AP Rules (2-3 hours)**

**Create:** `subsystem_ap_rules.zw`

```zw
# Rule template
{ap_rule
  {id rule_name}
  {priority 100}
  
  {requires [
    {condition_1}
    {condition_2}
  ]}
  
  {conflicts [
    {conflict_check}
  ]}
  
  {effects [
    {effect_1}
    {effect_2}
    {emit_event event_name}
  ]}
}
```

**Example (Inventory pickup):**
```zw
{ap_rule
  {id pickup_allowed}
  {priority 100}
  
  {requires [
    {item_present location item}
    {weight actor + item <= capacity actor}
    {alive actor}
  ]}
  
  {effects [
    {set_location item "carried_by:actor"}
    {increase_weight actor weight_of_item}
    {emit_event item_picked_up}
  ]}
}
```

---

### **Step 4: Build MR Kernel (3-4 hours)**

**Create:** `subsystem_mr.py`

```python
#!/usr/bin/env python3
"""
subsystem_mr.py - Pure Functional Subsystem Kernel

NO SIDE EFFECTS.
Input: snapshot_in (immutable)
Output: snapshot_out, accepted_deltas, alerts
"""

from typing import Dict, Any, List, Tuple

# ============================================================
# CONSTANTS
# ============================================================

STATE_EXAMPLE = "example_state"

# ============================================================
# PURE HELPER FUNCTIONS
# ============================================================

def validate_action(entity_data: Dict, action: Dict) -> bool:
    """
    Check if action is valid.
    Pure function - no state mutation.
    """
    # Validation logic
    return True

def apply_effect(entity_data: Dict, effect: Dict) -> Dict:
    """
    Apply effect to entity.
    Returns NEW dict, does not mutate input.
    """
    new_data = entity_data.copy()
    # Apply changes to new_data
    return new_data

# ============================================================
# MR KERNEL ENTRY POINT
# ============================================================

def step_subsystem(
    snapshot_in: Dict[str, Any],
    deltas: List[Dict[str, Any]],
    dt: float
) -> Tuple[Dict[str, Any], List[Dict], List[Dict]]:
    """
    Pure functional subsystem resolution.
    
    Args:
        snapshot_in: Immutable world state
        deltas: Actions to process
        dt: Time delta
    
    Returns:
        (snapshot_out, accepted_deltas, alerts)
    """
    # Deep copy to ensure immutability
    snapshot_out = {
        "subsystem": {
            "entities": {}
        }
    }
    
    # Extract subsystem state from input
    subsystem_in = snapshot_in.get("subsystem", {})
    entities_in = subsystem_in.get("entities", {})
    
    # Copy existing entities
    for eid, edata in entities_in.items():
        snapshot_out["subsystem"]["entities"][eid] = edata.copy()
    
    accepted = []
    alerts = []
    
    # Process each delta
    for delta in deltas:
        delta_type = delta.get("type")
        payload = delta.get("payload", {})
        
        if delta_type == "subsystem/action":
            result = _handle_action(
                snapshot_out["subsystem"]["entities"],
                payload,
                alerts
            )
            if result:
                accepted.append(delta)
    
    return snapshot_out, accepted, alerts

# ============================================================
# DELTA HANDLERS (Internal)
# ============================================================

def _handle_action(
    entities: Dict[str, Dict],
    payload: Dict[str, Any],
    alerts: List[Dict]
) -> bool:
    """Handle specific action"""
    # Implementation
    return True

# ============================================================
# TESTING
# ============================================================

if __name__ == "__main__":
    test_snapshot = {
        "subsystem": {
            "entities": {
                "test_entity": {
                    "property": "value"
                }
            }
        }
    }
    
    deltas = [
        {
            "type": "subsystem/action",
            "payload": {"test": "data"}
        }
    ]
    
    snapshot_out, accepted, alerts = step_subsystem(test_snapshot, deltas, 0.016)
    
    print("=== Subsystem Test ===")
    print(f"Alerts: {len(alerts)}")
    for alert in alerts:
        print(f"  - {alert}")
```

**Test standalone:**
```bash
cd ~/godotsim
python3 subsystem_mr.py
```

---

### **Step 5: Create Adapter (1-2 hours)**

**Create:** `subsystem_integration.py`

```python
#!/usr/bin/env python3
"""
subsystem_integration.py - Adapter for sim_runtime.py
"""

from typing import Dict, Any, List, Tuple
from subsystem_mr import step_subsystem

class SubsystemAdapter:
    """Adapter for Subsystem MR kernel"""
    
    def __init__(self):
        """Initialize state container"""
        self.state = {
            "entities": {}
        }
        self.delta_queue = []
    
    def register_entity(self, entity_id: str, **properties):
        """Register entity for subsystem tracking"""
        self.state["entities"][entity_id] = properties
        print(f"[SUBSYSTEM] Registered entity: {entity_id}")
    
    def handle_delta(self, delta_type: str, payload: Dict[str, Any]):
        """Queue a delta for next tick"""
        self.delta_queue.append({
            "type": delta_type,
            "payload": payload
        })
    
    def tick(self, dt: float) -> Tuple[List[Dict], List[Dict]]:
        """Process queued deltas"""
        if not self.delta_queue:
            return ([], [])
        
        # Build snapshot for MR kernel
        snapshot_in = {"subsystem": self.state}
        
        # Run pure functional kernel
        snapshot_out, accepted, alerts = step_subsystem(
            snapshot_in,
            self.delta_queue,
            dt
        )
        
        # Update state from kernel output
        self.state = snapshot_out["subsystem"]
        
        # Clear queue
        processed_deltas = self.delta_queue.copy()
        self.delta_queue.clear()
        
        return (processed_deltas, alerts)
    
    def get_entity_state(self, entity_id: str) -> Dict[str, Any]:
        """Get current state for entity"""
        return self.state["entities"].get(entity_id, {})
    
    def get_all_state(self) -> Dict[str, Any]:
        """Get full state (for snapshot export)"""
        return self.state.copy()
```

---

### **Step 6: Integrate into sim_runtime.py (1-2 hours)**

**Add to sim_runtime.py:**

```python
# 1. Import at top
from subsystem_integration import SubsystemAdapter

# 2. In __init__ (after line 62):
self._init_subsystem()

# 3. Add init method:
def _init_subsystem(self):
    '''Initialize Subsystem subsystem'''
    try:
        self.subsystem = SubsystemAdapter()
        print("  ✓ Subsystem")
        
        # Register test entities
        self.subsystem.register_entity("player", property1="value1")
    except Exception as e:
        print(f"  ✗ Subsystem failed: {e}")
        self.subsystem = None

# 4. In _update_subsystems() (BEFORE entity_ids line!):
# Subsystem
if self.subsystem:
    try:
        subsystem_deltas, subsystem_alerts = self.subsystem.tick(dt)
        
        if subsystem_alerts:
            print(f"[SUBSYSTEM] {len(subsystem_alerts)} alerts")
            for alert in subsystem_alerts:
                self._apply_subsystem_alert(alert)
    except Exception as e:
        print(f"[SUBSYSTEM ERROR] {e}")
        import traceback
        traceback.print_exc()

# 5. Add alert handler:
def _apply_subsystem_alert(self, alert: Dict[str, Any]):
    '''Process subsystem alerts'''
    alert_type = alert.get("type")
    
    if alert_type == "example_alert":
        print(f"  🎯 Example alert fired")
    # Add more alert handlers

# 6. Add HTTP endpoint (in RuntimeHTTPHandler.do_POST):
elif self.path == "/subsystem/action":
    content_length = int(self.headers['Content-Length'])
    body = self.rfile.read(content_length)
    
    try:
        data = json.loads(body.decode('utf-8'))
        actor = data.get("actor")
        target = data.get("target")
        
        if self.runtime.subsystem:
            self.runtime.subsystem.handle_delta("subsystem/action", {
                "actor": actor,
                "target": target
            })
            response = {"type": "ack", "status": "action_queued"}
        else:
            response = {"type": "error", "status": "subsystem_not_loaded"}
        
        self._send_json_response(response)
    except json.JSONDecodeError:
        self.send_error(400, "Invalid JSON")

# 7. Export in get_snapshot() (after line 488):
if self.subsystem:
    snapshot["subsystem"] = self.subsystem.get_all_state()
```

---

### **Step 7: Test with Curl (30 min)**

```bash
# Start runtime
python3 sim_runtime.py

# Test action
curl -X POST http://localhost:8080/subsystem/action \
  -H "Content-Type: application/json" \
  -d '{"actor":"player","target":"item"}'

# Check snapshot
curl http://localhost:8080/snapshot | jq '.payload.subsystem'
```

**Expected:**
```
[SUBSYSTEM] 1 alerts
  🎯 Example alert fired
```

---

### **Step 8: Add Godot Support (1-2 hours)**

**Add to ZWRuntime.gd:**

```gdscript
func subsystem_action(actor: String, target: String):
    var url = server_url + "/subsystem/action"
    var payload = {
        "actor": actor,
        "target": target
    }
    var json_string = JSON.stringify(payload)
    var headers = ["Content-Type: application/json"]
    
    command_request.request(url, headers, HTTPClient.METHOD_POST, json_string)
    print("ZWRuntime: Subsystem action - ", actor, " → ", target)
```

---

## ⏱️ **TIME ESTIMATES**

```
Extract Atoms:     2-3 hours
Design ZW:         1-2 hours
Write AP:          2-3 hours
Build MR:          3-4 hours
Create Adapter:    1-2 hours
Integrate Runtime: 1-2 hours
Test with Curl:    0.5 hours
Godot Support:     1-2 hours
------------------------
TOTAL:            12-19 hours (~2-3 days)
```

---

## 🎯 **SUCCESS CRITERIA**

**Before moving to next subsystem:**

- [ ] MR kernel tests pass standalone
- [ ] Adapter queues deltas
- [ ] Runtime shows "✓ Subsystem" on startup
- [ ] HTTP endpoint responds with ack
- [ ] Snapshot includes subsystem state
- [ ] Alerts fire correctly
- [ ] No exceptions in logs

---

**USE THIS TEMPLATE FOR EVERY NEW SUBSYSTEM.**

**The pattern is proven. Just copy-paste and adapt.** 🚀
