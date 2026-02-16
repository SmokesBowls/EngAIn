#!/usr/bin/env python3
"""
combat3d_integration.py - Combat3D Integration Patch for sim_runtime.py

Adds Combat3D subsystem to EngAIn production runtime following existing pattern.

Installation:
1. Copy to ~/godotsim/
2. Import Combat3DAdapter in sim_runtime.py
3. Initialize in _init_subsystems()
4. Add to _update_subsystems()
5. Add HTTP endpoint /combat/damage
"""

from typing import Dict, Any, List, Tuple
from combat3d_mr import step_combat, WOUND_STATE_DEAD

class Combat3DAdapter:
    """
    Adapter for Combat3D MR kernel.
    Matches pattern of Spatial3DStateViewAdapter, PerceptionStateView, BehaviorStateView.
    """
    
    def __init__(self):
        """Initialize combat state container"""
        self.state = {
            "entities": {}
        }
        self.delta_queue = []
    
    def register_entity(self, entity_id: str, health: int = 100, max_health: int = 100,
                       strength: int = 10, defense: int = 5):
        """
        Register entity for combat tracking.
        
        Args:
            entity_id: Unique entity identifier
            health: Current health
            max_health: Maximum health
            strength: Attack power
            defense: Damage reduction
        """
        self.state["entities"][entity_id] = {
            "health": health,
            "max_health": max_health,
            "strength": strength,
            "defense": defense,
            "alive": True,
            "state": "healthy",
            "attack_mode": False,
            "fight_bit": False
        }
        print(f"[COMBAT] Registered entity: {entity_id} ({health}/{max_health} HP)")
    
    def handle_delta(self, delta_type: str, payload: Dict[str, Any]):
        """
        Queue a combat delta for next tick.
        
        Args:
            delta_type: Type of combat action
            payload: Action parameters
        """
        self.delta_queue.append({
            "type": delta_type,
            "payload": payload
        })
    
    def tick(self, dt: float) -> Tuple[List[Dict], List[Dict]]:
        """
        Process queued combat deltas.
        
        Args:
            dt: Time delta
        
        Returns:
            (deltas_fired, alerts)
        """
        if not self.delta_queue:
            return ([], [])
        
        # Build snapshot for MR kernel
        snapshot_in = {"combat3d": self.state}
        
        # Run pure functional kernel
        snapshot_out, accepted, alerts = step_combat(
            snapshot_in,
            self.delta_queue,
            dt
        )
        
        # Update state from kernel output
        self.state = snapshot_out["combat3d"]
        
        # Clear queue
        processed_deltas = self.delta_queue.copy()
        self.delta_queue.clear()
        
        return (processed_deltas, alerts)
    
    def get_entity_state(self, entity_id: str) -> Dict[str, Any]:
        """Get current combat state for entity"""
        return self.state["entities"].get(entity_id, {})
    
    def get_all_state(self) -> Dict[str, Any]:
        """Get full combat state (for snapshot export)"""
        return self.state.copy()
    
    def is_alive(self, entity_id: str) -> bool:
        """Check if entity is alive"""
        entity = self.state["entities"].get(entity_id)
        if not entity:
            return False
        return entity.get("alive", False)
    
    def is_dead(self, entity_id: str) -> bool:
        """Check if entity is dead"""
        return not self.is_alive(entity_id)


# ============================================================
# INTEGRATION GUIDE FOR sim_runtime.py
# ============================================================

INTEGRATION_PATCH = """
# === ADD TO sim_runtime.py ===

# 1. Import at top
from combat3d_integration import Combat3DAdapter

# 2. In __init__ (after line 62):
self._init_combat()

# 3. Add method _init_combat() (after _init_subsystems):
def _init_combat(self):
    '''Initialize Combat3D subsystem'''
    try:
        self.combat = Combat3DAdapter()
        print("  ✓ Combat3D")
        
        # Register test entities (remove in production)
        self.combat.register_entity("player", health=100, strength=15, defense=5)
        self.combat.register_entity("guard", health=100, strength=12, defense=8)
        self.combat.register_entity("enemy", health=50, strength=10, defense=3)
    except Exception as e:
        print(f"  ✗ Combat3D failed: {e}")
        self.combat = None

# 4. In _update_subsystems() (after Behavior section, ~line 433):
# Combat3D
if self.combat:
    try:
        combat_deltas, combat_alerts = self.combat.tick(dt)
        
        if combat_alerts:
            print(f"[COMBAT] {len(combat_alerts)} alerts")
            for alert in combat_alerts:
                self._apply_combat_alert(alert)
    except Exception as e:
        print(f"[COMBAT ERROR] {e}")

# 5. Add method _apply_combat_alert() (after _apply_delta):
def _apply_combat_alert(self, alert: Dict[str, Any]):
    '''Process combat alerts'''
    alert_type = alert.get("type")
    
    if alert_type == "entity_died":
        entity_id = alert.get("entity_id")
        print(f"  💀 {entity_id} has died")
        
        # Update main snapshot
        if entity_id in self.snapshot["entities"]:
            self.snapshot["entities"][entity_id]["alive"] = False
            self.snapshot["entities"][entity_id]["state"] = "dead"
        
        # Disable navigation
        if self.behavior:
            self.behavior.set_behavior_state(entity_id, "dead")
    
    elif alert_type == "low_health_warning":
        entity_id = alert.get("entity_id")
        health = alert.get("health")
        print(f"  ⚠️  {entity_id} low health: {health}")
        
        # Set low_health flag for behavior
        if self.behavior:
            # Trigger flee behavior
            pass
    
    elif alert_type == "wound_state_change":
        entity_id = alert.get("entity_id")
        old_state = alert.get("old_state")
        new_state = alert.get("new_state")
        print(f"  🩹 {entity_id}: {old_state} → {new_state}")
    
    elif alert_type == "attack_hit":
        attacker = alert.get("attacker")
        target = alert.get("target")
        damage = alert.get("damage")
        print(f"  ⚔️  {attacker} hits {target} for {damage} damage")
    
    elif alert_type == "attack_miss":
        attacker = alert.get("attacker")
        target = alert.get("target")
        print(f"  ⭕ {attacker} misses {target}")

# 6. Add HTTP endpoint (in RuntimeHTTPHandler.do_POST, after /command):
elif self.path == "/combat/damage":
    content_length = int(self.headers['Content-Length'])
    body = self.rfile.read(content_length)
    
    try:
        data = json.loads(body.decode('utf-8'))
        source = data.get("source", "unknown")
        target = data.get("target")
        damage = data.get("damage", 25)
        
        if self.runtime.combat:
            self.runtime.combat.handle_delta("combat3d/apply_damage", {
                "source": source,
                "target": target,
                "amount": damage
            })
            response = {"type": "ack", "status": "damage_applied"}
        else:
            response = {"type": "error", "status": "combat_not_loaded"}
        
        self._send_json_response(response)
    except json.JSONDecodeError:
        self.send_error(400, "Invalid JSON")

# 7. Update get_snapshot() to include combat state (after line 488):
if self.combat:
    snapshot["combat"] = self.combat.get_all_state()
"""

if __name__ == "__main__":
    print(INTEGRATION_PATCH)
