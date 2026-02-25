#!/usr/bin/env python3
"""behavior_adapter.py - Matches ACTUAL behavior3d_mr"""

import time
from typing import Dict, List, Tuple

# Stubs
class Alert:
    def __init__(self, level, message, tick, ts):
        self.level = level
        self.message = message
        self.tick = tick
        self.ts = ts

class Delta:
    def __init__(self, id, type, payload, tags=None):
        self.id = id
        self.type = type
        self.payload = payload
        self.tags = tags or []

# Import actual mr
from behavior3d_mr import BehaviorState, update_behavior_mr

class BehaviorStateView:
    def __init__(self, state_slice: dict = None):
        if state_slice is None:
            state_slice = {"entities": {}}
        self._state_slice = state_slice
        self._spatial_snapshot = {}
        self._perception_snapshot = {}
    
    def set_spatial_state(self, spatial_snapshot: dict):
        self._spatial_snapshot = spatial_snapshot
    
    def set_perception_state(self, perception_snapshot: dict):
        self._perception_snapshot = perception_snapshot
    
    def behavior_step(self, current_tick: float, delta_time: float) -> Tuple[List[Delta], List[Alert]]:
        deltas = []
        alerts = []
        
        spatial_entities = self._spatial_snapshot.get("entities", {})
        
        for entity_id, behavior_data in list(self._state_slice.get("entities", {}).items()):
            if entity_id not in spatial_entities:
                continue
            
            # Load state
            prev_state = BehaviorState(
                intent=behavior_data.get("intent", 0.0),
                alertness=behavior_data.get("alertness", 0.0),
                threat=behavior_data.get("threat", 0.0),
                aggression=behavior_data.get("aggression", 0.5),
                caution=behavior_data.get("caution", 0.5),
                persistence=behavior_data.get("persistence", 0.5)
            )
            
            # Track if was above threshold LAST tick
            was_high = behavior_data.get("was_high_intent", False)
            
            # Build slices
            spatial_slice = {"position": spatial_entities[entity_id].get("pos")}
            perception_slice = self._perception_snapshot.get(entity_id, {})
            nav_slice = {}
            
            try:
                # Call actual mr kernel
                new_state = update_behavior_mr(prev_state, spatial_slice, perception_slice, nav_slice)
                
                # Save state
                self._state_slice["entities"][entity_id] = {
                    "intent": new_state.intent,
                    "alertness": new_state.alertness,
                    "threat": new_state.threat,
                    "aggression": new_state.aggression,
                    "caution": new_state.caution,
                    "persistence": new_state.persistence,
                    "was_high_intent": new_state.intent > 0.7
                }
                
                # Emit delta only on THRESHOLD CROSS (not every tick)
                is_high_now = new_state.intent > 0.7
                if is_high_now and not was_high:
                    deltas.append(Delta(
                        id=f"behavior_{entity_id}_{int(current_tick)}",
                        type="behavior3d/high_intent",
                        payload={"entity_id": entity_id, "intent": new_state.intent},
                        tags=["behavior"]
                    ))
                
            except Exception as e:
                alerts.append(Alert(
                    level="ERROR",
                    message=f"Behavior error for {entity_id}: {e}",
                    tick=current_tick,
                    ts=time.time()
                ))
        
        return deltas, alerts
    
    def add_behavior_entity(self, entity_id: str, initial_state=None, **kwargs) -> Tuple[bool, List]:
        if entity_id in self._state_slice.get("entities", {}):
            return False, []
        
        self._state_slice["entities"][entity_id] = {
            "intent": 0.0,
            "alertness": 0.0,
            "threat": 0.0,
            "aggression": kwargs.get("aggression", 0.5),
            "caution": kwargs.get("caution", 0.5),
            "persistence": kwargs.get("persistence", 0.5)
        }
        return True, []
    
    def get_behavior_state(self, entity_id: str):
        return self._state_slice.get("entities", {}).get(entity_id)
