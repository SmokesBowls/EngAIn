#!/usr/bin/env python3
"""
inventory3d_integration.py - Inventory3D Adapter for sim_runtime.py

Integrates Inventory3D MR kernel into EngAIn production runtime.
"""

from typing import Dict, Any, List, Tuple
from inventory3d_mr import step_inventory, LOAD_MAX, FUMBLE_NUMBER

class Inventory3DAdapter:
    """Adapter for Inventory3D MR kernel"""
    
    def __init__(self):
        """Initialize inventory state container"""
        self.state = {
            "entities": {},
            "items": {}
        }
        self.delta_queue = []
    
    def register_entity(self, entity_id: str, load_allowed: int = LOAD_MAX):
        """
        Register entity for inventory tracking.
        
        Args:
            entity_id: Unique entity identifier
            load_allowed: Maximum weight capacity
        """
        self.state["entities"][entity_id] = {
            "load_allowed": load_allowed,
            "load_max": LOAD_MAX,
            "current_weight": 0,
            "carry_count": 0
        }
        print(f"[INVENTORY] Registered entity: {entity_id} (capacity: {load_allowed})")
    
    def register_item(self, item_id: str, size: int = 5, takeable: bool = True,
                     wearable: bool = False, location: str = "world"):
        """
        Register item in the world.
        
        Args:
            item_id: Unique item identifier
            size: Item weight/size
            takeable: Can be picked up
            wearable: Can be worn
            location: Initial location
        """
        self.state["items"][item_id] = {
            "size": size,
            "takeable": takeable,
            "wearable": wearable,
            "held_by": None,
            "location": location,
            "worn": False,
            "invisible": False,
            "no_describe": False,
            "children": []
        }
        print(f"[INVENTORY] Registered item: {item_id} ({size} units, {location})")
    
    def handle_delta(self, delta_type: str, payload: Dict[str, Any]):
        """Queue an inventory delta for next tick"""
        self.delta_queue.append({
            "type": delta_type,
            "payload": payload
        })
    
    def tick(self, dt: float) -> Tuple[List[Dict], List[Dict]]:
        """Process queued inventory deltas"""
        if not self.delta_queue:
            return ([], [])
        
        # Build snapshot for MR kernel
        snapshot_in = {"inventory3d": self.state}
        
        # Run pure functional kernel
        snapshot_out, accepted, alerts = step_inventory(
            snapshot_in,
            self.delta_queue,
            dt
        )
        
        # Update state from kernel output
        self.state = snapshot_out["inventory3d"]
        
        # Clear queue
        processed_deltas = self.delta_queue.copy()
        self.delta_queue.clear()
        
        return (processed_deltas, alerts)
    
    def get_entity_inventory(self, entity_id: str) -> List[str]:
        """Get list of items held by entity"""
        inventory = []
        for item_id, item_data in self.state["items"].items():
            if item_data.get("held_by") == entity_id:
                inventory.append(item_id)
        return inventory
    
    def get_entity_state(self, entity_id: str) -> Dict[str, Any]:
        """Get current inventory state for entity"""
        return self.state["entities"].get(entity_id, {})
    
    def get_item_state(self, item_id: str) -> Dict[str, Any]:
        """Get current state for item"""
        return self.state["items"].get(item_id, {})
    
    def get_all_state(self) -> Dict[str, Any]:
        """Get full inventory state (for snapshot export)"""
        return self.state.copy()


# ============================================================
# INTEGRATION GUIDE FOR sim_runtime.py
# ============================================================

INTEGRATION_PATCH = """
# === ADD TO sim_runtime.py ===

# 1. Import at top
from inventory3d_integration import Inventory3DAdapter

# 2. In __init__ (after Combat init):
self._init_inventory()

# 3. Add method _init_inventory():
def _init_inventory(self):
    '''Initialize Inventory3D subsystem'''
    try:
        self.inventory = Inventory3DAdapter()
        print("  ✓ Inventory3D")
        
        # Register test entities
        self.inventory.register_entity("player", load_allowed=100)
        self.inventory.register_entity("guard", load_allowed=80)
        
        # Register test items
        self.inventory.register_item("sword", size=10, wearable=True, location="world")
        self.inventory.register_item("shield", size=15, wearable=True, location="world")
        self.inventory.register_item("potion", size=2, takeable=True, location="world")
        self.inventory.register_item("armor", size=20, wearable=True, location="world")
    except Exception as e:
        print(f"  ✗ Inventory3D failed: {e}")
        self.inventory = None

# 4. In _update_subsystems() (BEFORE entity_ids, after Combat):
# Inventory3D
if self.inventory:
    try:
        inv_deltas, inv_alerts = self.inventory.tick(dt)
        
        if inv_alerts:
            print(f"[INVENTORY] {len(inv_alerts)} alerts")
            for alert in inv_alerts:
                self._apply_inventory_alert(alert)
    except Exception as e:
        print(f"[INVENTORY ERROR] {e}")
        import traceback
        traceback.print_exc()

# 5. Add method _apply_inventory_alert():
def _apply_inventory_alert(self, alert: Dict[str, Any]):
    '''Process inventory alerts'''
    alert_type = alert.get("type")
    
    if alert_type == "item_taken":
        actor = alert.get("actor")
        item = alert.get("item")
        print(f"  📦 {actor} picked up {item}")
    
    elif alert_type == "item_dropped":
        actor = alert.get("actor")
        item = alert.get("item")
        location = alert.get("location")
        print(f"  📦 {actor} dropped {item} at {location}")
    
    elif alert_type == "item_worn":
        actor = alert.get("actor")
        item = alert.get("item")
        print(f"  👕 {actor} equipped {item}")
    
    elif alert_type == "item_removed":
        actor = alert.get("actor")
        item = alert.get("item")
        print(f"  👕 {actor} unequipped {item}")
    
    elif alert_type == "take_failed":
        reason = alert.get("reason")
        actor = alert.get("actor")
        item = alert.get("item")
        
        if reason == "too_heavy":
            current = alert.get("current_weight")
            item_weight = alert.get("item_weight")
            limit = alert.get("limit")
            print(f"  ⚠️  {actor} can't carry {item}: too heavy ({current}+{item_weight} > {limit})")
        elif reason == "too_many_items":
            count = alert.get("carry_count")
            limit = alert.get("limit")
            print(f"  ⚠️  {actor} fumbling: too many items ({count}/{limit})")
        else:
            print(f"  ⚠️  {actor} can't take {item}: {reason}")
    
    elif alert_type == "overloaded":
        entity = alert.get("entity")
        weight = alert.get("current_weight")
        limit = alert.get("limit")
        print(f"  ⚠️  {entity} overloaded: {weight}/{limit}")
    
    elif alert_type == "fumble_risk":
        entity = alert.get("entity")
        count = alert.get("carry_count")
        limit = alert.get("limit")
        print(f"  ⚠️  {entity} fumble risk: {count}/{limit} items")

# 6. Add HTTP endpoints (in RuntimeHTTPHandler.do_POST):

elif self.path == "/inventory/take":
    content_length = int(self.headers['Content-Length'])
    body = self.rfile.read(content_length)
    
    try:
        data = json.loads(body.decode('utf-8'))
        actor = data.get("actor")
        item = data.get("item")
        
        if self.runtime.inventory:
            self.runtime.inventory.handle_delta("inventory3d/take", {
                "actor": actor,
                "item": item
            })
            response = {"type": "ack", "status": "take_queued"}
        else:
            response = {"type": "error", "status": "inventory_not_loaded"}
        
        self._send_json_response(response)
    except json.JSONDecodeError:
        self.send_error(400, "Invalid JSON")

elif self.path == "/inventory/drop":
    content_length = int(self.headers['Content-Length'])
    body = self.rfile.read(content_length)
    
    try:
        data = json.loads(body.decode('utf-8'))
        actor = data.get("actor")
        item = data.get("item")
        location = data.get("location", "world")
        
        if self.runtime.inventory:
            self.runtime.inventory.handle_delta("inventory3d/drop", {
                "actor": actor,
                "item": item,
                "location": location
            })
            response = {"type": "ack", "status": "drop_queued"}
        else:
            response = {"type": "error", "status": "inventory_not_loaded"}
        
        self._send_json_response(response)
    except json.JSONDecodeError:
        self.send_error(400, "Invalid JSON")

elif self.path == "/inventory/wear":
    content_length = int(self.headers['Content-Length'])
    body = self.rfile.read(content_length)
    
    try:
        data = json.loads(body.decode('utf-8'))
        actor = data.get("actor")
        item = data.get("item")
        
        if self.runtime.inventory:
            self.runtime.inventory.handle_delta("inventory3d/wear", {
                "actor": actor,
                "item": item
            })
            response = {"type": "ack", "status": "wear_queued"}
        else:
            response = {"type": "error", "status": "inventory_not_loaded"}
        
        self._send_json_response(response)
    except json.JSONDecodeError:
        self.send_error(400, "Invalid JSON")

# 7. Update get_snapshot() to include inventory state:
if self.inventory:
    snapshot["inventory"] = self.inventory.get_all_state()
"""

if __name__ == "__main__":
    print(INTEGRATION_PATCH)
