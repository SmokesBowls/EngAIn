#!/usr/bin/env python3
"""
quest3d_integration.py — Quest3D Adapter + Integration

Wraps quest3d_mr.py pure kernel with:
  - Delta queuing (batch quest changes per tick)
  - Snapshot management (extract/inject quest state)
  - sim_runtime.py integration hooks
  - AP-ready validation boundary (placeholder for AP rules)

Follows combat3d_integration.py pattern exactly.
"""

from typing import Dict, List, Tuple, Optional
from quest3d_mr import step_quest3d, QuestConfig


class Quest3DIntegration:
    """
    Adapter between sim_runtime.py and quest3d_mr.py kernel.
    
    Responsibilities:
      - Queue deltas between ticks
      - Call pure kernel each tick
      - Merge quest state back into world snapshot
      - Provide API for HTTP bridge (quest commands from Godot)
    
    Does NOT own state — delegates to kernel snapshot model.
    """

    def __init__(self, config: Optional[QuestConfig] = None):
        self.config = config or QuestConfig()
        self._delta_queue: List[Dict] = []
        self._delta_counter: int = 0
        self._last_alerts: List[Dict] = []

    # ── Delta API (called by HTTP handlers or sim_runtime) ─────

    def register_quest(self, quest_def: Dict) -> str:
        """Queue a quest registration. Returns delta ID."""
        delta_id = self._next_id("reg")
        self._delta_queue.append({
            "type": "quest/register",
            "id": delta_id,
            "quest": quest_def
        })
        return delta_id

    def activate_quest(self, quest_id: str) -> str:
        """Queue a quest activation. Returns delta ID."""
        delta_id = self._next_id("act")
        self._delta_queue.append({
            "type": "quest/activate",
            "id": delta_id,
            "quest_id": quest_id
        })
        return delta_id

    def abandon_quest(self, quest_id: str) -> str:
        """Queue a quest abandonment. Returns delta ID."""
        delta_id = self._next_id("abn")
        self._delta_queue.append({
            "type": "quest/abandon",
            "id": delta_id,
            "quest_id": quest_id
        })
        return delta_id

    # ── Tick (called by sim_runtime each frame) ────────────────

    def tick(self, world_snapshot: Dict, delta_time: float) -> Dict:
        """
        Run one quest tick. Consumes queued deltas, returns updated snapshot.
        
        Args:
            world_snapshot: Full world state (entities + quest + combat etc.)
            delta_time: Frame time
        
        Returns:
            Updated world snapshot with quest state merged in
        """
        # Ensure quest state exists in snapshot
        if "quest" not in world_snapshot:
            world_snapshot["quest"] = {"quests": {}, "tick": 0.0}

        # Run pure kernel
        snapshot_out, accepted, alerts = step_quest3d(
            world_snapshot,
            self._delta_queue,
            self.config,
            delta_time
        )

        # Store alerts for inspection
        self._last_alerts = alerts

        # Clear processed deltas
        self._delta_queue.clear()

        return snapshot_out

    # ── Query API ──────────────────────────────────────────────

    def get_last_alerts(self) -> List[Dict]:
        """Return alerts from last tick (for Godot bridge / logging)."""
        return self._last_alerts

    def get_quest_status(self, world_snapshot: Dict, quest_id: str) -> Optional[str]:
        """Read quest status from snapshot."""
        return (world_snapshot
                .get("quest", {})
                .get("quests", {})
                .get(quest_id, {})
                .get("status"))

    def get_active_quests(self, world_snapshot: Dict) -> List[str]:
        """Return IDs of all active quests."""
        quests = world_snapshot.get("quest", {}).get("quests", {})
        return [qid for qid, q in quests.items() if q.get("status") == "active"]

    def get_completed_quests(self, world_snapshot: Dict) -> List[str]:
        """Return IDs of all completed quests."""
        quests = world_snapshot.get("quest", {}).get("quests", {})
        return [qid for qid, q in quests.items() if q.get("status") == "completed"]

    def get_quest_summary(self, world_snapshot: Dict) -> Dict:
        """Return summary of all quests grouped by status."""
        quests = world_snapshot.get("quest", {}).get("quests", {})
        summary = {"inactive": [], "active": [], "completed": [], "failed": []}
        for qid, q in quests.items():
            status = q.get("status", "inactive")
            summary.setdefault(status, []).append({
                "id": qid,
                "title": q.get("title", ""),
                "objectives_done": sum(1 for o in q.get("objectives", []) if o.get("status") == "satisfied"),
                "objectives_total": len(q.get("objectives", []))
            })
        return summary

    # ── Internal ───────────────────────────────────────────────

    def _next_id(self, prefix: str) -> str:
        self._delta_counter += 1
        return f"quest_{prefix}_{self._delta_counter}"


# ============================================================
# HTTP BRIDGE HELPERS (for sim_runtime.py integration)
# ============================================================

def handle_quest_http_request(integration: Quest3DIntegration, request: Dict) -> Dict:
    """
    Handle an HTTP request from Godot for quest operations.
    
    Expected request shapes:
        {"action": "register", "quest": {...}}
        {"action": "activate", "quest_id": "q_find_sword"}
        {"action": "abandon", "quest_id": "q_find_sword"}
        {"action": "status", "quest_id": "q_find_sword"}
        {"action": "summary"}
    """
    action = request.get("action", "")

    if action == "register":
        delta_id = integration.register_quest(request.get("quest", {}))
        return {"ok": True, "delta_id": delta_id}

    elif action == "activate":
        delta_id = integration.activate_quest(request.get("quest_id", ""))
        return {"ok": True, "delta_id": delta_id}

    elif action == "abandon":
        delta_id = integration.abandon_quest(request.get("quest_id", ""))
        return {"ok": True, "delta_id": delta_id}

    elif action == "status":
        # This needs the current snapshot — caller must provide
        return {"ok": True, "note": "status requires snapshot context"}

    elif action == "summary":
        return {"ok": True, "note": "summary requires snapshot context"}

    return {"ok": False, "error": f"Unknown action: {action}"}


# ============================================================
# TESTING
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Testing Quest3D Integration Layer...")
    print("=" * 60)

    passed = 0

    # ── Test 1: Integration lifecycle ──
    print("\n[Test 1] Full lifecycle through integration layer")
    integration = Quest3DIntegration()

    world = {
        "entities": {
            "player": {
                "flags": {}, "items": {},
                "location": "village",
                "combat": {"health": 100}
            }
        }
    }

    # Register
    integration.register_quest({
        "id": "q_test",
        "title": "Test Quest",
        "objectives": [
            {"id": "obj_1", "description": "Go to cave", "conditions": [
                {"type": "at_location", "target_entity": "player", "key": "location", "value": "cave"}
            ]}
        ],
        "rewards": [
            {"type": "set_flag", "target_entity": "player", "key": "quest_done", "value": True}
        ]
    })

    # Tick 1: registers
    world = integration.tick(world, 0.016)
    assert integration.get_quest_status(world, "q_test") == "inactive"
    print("  ✅ Registered via integration")
    passed += 1

    # Activate
    integration.activate_quest("q_test")
    world = integration.tick(world, 0.016)
    assert integration.get_quest_status(world, "q_test") == "active"
    assert "q_test" in integration.get_active_quests(world)
    print("  ✅ Activated via integration")
    passed += 1

    # Complete objective
    world["entities"]["player"]["location"] = "cave"
    world = integration.tick(world, 0.016)
    assert integration.get_quest_status(world, "q_test") == "completed"
    assert world["entities"]["player"]["flags"].get("quest_done") == True
    alerts = integration.get_last_alerts()
    assert any(a["type"] == "quest_completed" for a in alerts)
    print("  ✅ Completed + rewards applied via integration")
    passed += 1

    # Summary
    summary = integration.get_quest_summary(world)
    assert len(summary["completed"]) == 1
    assert summary["completed"][0]["id"] == "q_test"
    print("  ✅ Summary correct")
    passed += 1

    # ── Test 2: HTTP bridge ──
    print("\n[Test 2] HTTP bridge helpers")
    integration2 = Quest3DIntegration()
    resp = handle_quest_http_request(integration2, {"action": "register", "quest": {"id": "q_http", "title": "HTTP Test"}})
    assert resp["ok"] == True
    resp2 = handle_quest_http_request(integration2, {"action": "activate", "quest_id": "q_http"})
    assert resp2["ok"] == True
    resp3 = handle_quest_http_request(integration2, {"action": "bogus"})
    assert resp3["ok"] == False
    print("  ✅ HTTP bridge dispatches correctly")
    passed += 1

    print("\n" + "=" * 60)
    print(f"Quest3D Integration: {passed} passed, 0 failed")
    print("=" * 60)
