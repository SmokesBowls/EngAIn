#!/usr/bin/env python3
"""dialogue3d_integration.py - Dialogue3D Adapter"""

from typing import Dict, Any, List, Tuple
from dialogue3d_mr import step_dialogue, DEFAULT_REPUTATION

class Dialogue3DAdapter:
    """Adapter for Dialogue3D MR kernel"""
    
    def __init__(self):
        self.state = {"entities": {}, "conversations": {}}
        self.delta_queue = []
    
    def register_entity(self, entity_id: str, knowledge_flags: List[str] = None):
        """Register entity for dialogue tracking"""
        self.state["entities"][entity_id] = {
            "reputation": {},
            "knowledge_flags": set(knowledge_flags or []),
            "responses_given": set(),
            "active_conversation": None
        }
        print(f"[DIALOGUE] Registered entity: {entity_id}")
    
    def handle_delta(self, delta_type: str, payload: Dict[str, Any]):
        """Queue dialogue delta"""
        self.delta_queue.append({"type": delta_type, "payload": payload})
    
    def tick(self, dt: float) -> Tuple[List[Dict], List[Dict]]:
        """Process queued dialogue deltas"""
        if not self.delta_queue:
            return ([], [])
        
        snapshot_in = {"dialogue3d": self.state}
        snapshot_out, accepted, alerts = step_dialogue(snapshot_in, self.delta_queue, dt)
        self.state = snapshot_out["dialogue3d"]
        
        processed = self.delta_queue.copy()
        self.delta_queue.clear()
        return (processed, alerts)
    
    def get_entity_state(self, entity_id: str) -> Dict[str, Any]:
        """Get dialogue state for entity"""
        return self.state["entities"].get(entity_id, {})
    
    def get_all_state(self) -> Dict[str, Any]:
        """Get full dialogue state"""
        return self.state.copy()

# INTEGRATION PATCH FOR sim_runtime.py
INTEGRATION_PATCH = """
# 1. Import
from dialogue3d_integration import Dialogue3DAdapter

# 2. In __init__:
self._init_dialogue()

# 3. Add init method:
def _init_dialogue(self):
    try:
        self.dialogue = Dialogue3DAdapter()
        print("  ✓ Dialogue3D")
        
        self.dialogue.register_entity("player", knowledge_flags=[])
        self.dialogue.register_entity("guard", knowledge_flags=["fire_crystal_location"])
        self.dialogue.register_entity("merchant", knowledge_flags=["sword_upgrade"])
    except Exception as e:
        print(f"  ✗ Dialogue3D failed: {e}")
        self.dialogue = None

# 4. In _update_subsystems() (BEFORE entity_ids):
if self.dialogue:
    try:
        dlg_deltas, dlg_alerts = self.dialogue.tick(dt)
        if dlg_alerts:
            print(f"[DIALOGUE] {len(dlg_alerts)} alerts")
            for alert in dlg_alerts:
                self._apply_dialogue_alert(alert)
    except Exception as e:
        print(f"[DIALOGUE ERROR] {e}")
        import traceback
        traceback.print_exc()

# 5. Add alert handler:
def _apply_dialogue_alert(self, alert: Dict[str, Any]):
    alert_type = alert.get("type")
    
    if alert_type == "dialogue_started":
        speaker = alert.get("speaker")
        listener = alert.get("listener")
        print(f"  💬 {speaker} speaks to {listener}")
    
    elif alert_type == "knowledge_shared":
        asker = alert.get("asker")
        topic = alert.get("topic")
        print(f"  📚 {asker} learned: {topic}")
    
    elif alert_type == "knowledge_unknown":
        topic = alert.get("topic")
        print(f"  ❓ Topic unknown: {topic}")
    
    elif alert_type == "branch_selected":
        speaker = alert.get("speaker")
        branch_id = alert.get("branch_id")
        print(f"  🔀 {speaker} chose: {branch_id}")

# 6. Add HTTP endpoints:
elif self.path == "/dialogue/say":
    data = json.loads(body.decode('utf-8'))
    if self.runtime.dialogue:
        self.runtime.dialogue.handle_delta("dialogue3d/say", data)
        response = {"type": "ack", "status": "say_queued"}
    self._send_json_response(response)

elif self.path == "/dialogue/ask":
    data = json.loads(body.decode('utf-8'))
    if self.runtime.dialogue:
        self.runtime.dialogue.handle_delta("dialogue3d/ask", data)
        response = {"type": "ack", "status": "ask_queued"}
    self._send_json_response(response)

# 7. Snapshot export:
if self.dialogue:
    snapshot["dialogue"] = self.dialogue.get_all_state()
"""

if __name__ == "__main__":
    print(INTEGRATION_PATCH)
