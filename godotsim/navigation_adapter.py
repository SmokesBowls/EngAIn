#!/usr/bin/env python3
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from slice_builders import build_nav_slice_v1, SliceError
from slice_types import Vec3

@dataclass
class Delta:
    id: str
    type: str
    payload: Dict[str, Any]
    tags: List[str]

@dataclass
class Alert:
    level: str
    message: str
    tick: float
    ts: float

class NavigationStateView:
    def __init__(self, initial_state: Dict[str, Any]):
        self._state_slice = {"entities": {}}
        self._spatial_snapshot = {}
    
    def set_spatial_state(self, snapshot: Dict[str, Any]):
        self._spatial_snapshot = snapshot
    
    def request_path(self, entity_id: str, goal: Vec3, current_tick: float) -> Tuple[List[Delta], List[Alert]]:
        deltas = []
        alerts = []
        try:
            nav_slice = build_nav_slice_v1(self._spatial_snapshot, tick=current_tick, eid=entity_id, goal=goal)
            delta = Delta(
                id=f"nav_{entity_id}_{int(current_tick)}",
                type="navigation3d/path_requested",
                payload={"entity_id": entity_id, "from": nav_slice.self.pos, "goal": goal},
                tags=["navigation"]
            )
            deltas.append(delta)
        except SliceError as e:
            alerts.append(Alert(level="ERROR", message=f"Nav error: {e}", tick=current_tick, ts=0.0))
        return deltas, alerts

if __name__ == "__main__":
    print("=== Navigation Adapter Test ===\n")
    nav = NavigationStateView({})
    snapshot = {"entities": {"npc": {"position": [5.0, 0.0, 3.0], "velocity": [0.0, 0.0, 0.0]}}, "world": {"time": 1.0}}
    nav.set_spatial_state(snapshot)
    deltas, alerts = nav.request_path("npc", goal=(10.0, 0.0, 5.0), current_tick=1.0)
    print(f"✓ Path request generated {len(deltas)} deltas")
    if deltas:
        print(f"  From: {deltas[0].payload['from']}")
        print(f"  Goal: {deltas[0].payload['goal']}")
    print(f"✓ {len(alerts)} alerts\n=== Test Complete ===")
