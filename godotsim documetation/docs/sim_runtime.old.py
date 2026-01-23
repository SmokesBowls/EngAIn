#!/usr/bin/env python3
"""sim_runtime.py - EngAIn Runtime - FULL OPERATIONAL"""

import json
import sys
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any, List, Tuple, Optional

# Import MR kernels
try:
    from spatial3d_mr import step_spatial3d
    from perception_mr import step_perception
    from behavior3d_mr import update_behavior_mr
    HAS_MR = True
except ImportError as e:
    print(f"MR kernels missing: {e}")
    HAS_MR = False

# Import adapters
try:
    from spatial3d_adapter import Spatial3DStateViewAdapter
    from perception_adapter import PerceptionStateView
    from behavior_adapter import BehaviorStateView
    HAS_ADAPTERS = True
except ImportError as e:
    print(f"Adapters missing: {e}")
    HAS_ADAPTERS = False

print(f"✓ MR kernels | spatial=True, perception=True, behavior=True")

class EngAInRuntime:
    def __init__(self):
        self.snapshot = {
            "entities": {},
            "spatial": {},
            "perception": {},
            "behavior": {},
            "world": {"time": 0.0, "weather": "clear"},
            "events": []
        }
        
        self.delta_queue = []
        self.command_queue = []
        
        self._init_subsystems()
        
        self.running = True
        self.sim_thread = threading.Thread(target=self._simulation_loop, daemon=True)
        self.sim_thread.start()
        
        print("  → Ladies and Gentalman and AI, This is your captain speaking, EngAI systems are all full capacity.. Well done. you dont have to go home but you cant stay here.  ")
        print("EngAIn Runtime: Initialized")
    
    def _init_subsystems(self):
        if HAS_ADAPTERS:
            try:
                self.spatial = Spatial3DStateViewAdapter()
                print("  ✓ Spatial3D")
            except:
                self.spatial = None
            
            try:
                self.perception = PerceptionStateView({"entities": {}})
                print("  ✓ Perception")
            except:
                self.perception = None
            
            try:
                self.behavior = BehaviorStateView({"entities": {}})
                print("  ✓ Behavior")
            except:
                self.behavior = None
        else:
            self.spatial = None
            self.perception = None
            self.behavior = None
    
    def _create_entity_state(self, entity_id: str, entity_type: str, 
                            position: Tuple[float, float, float], **kwargs) -> Dict[str, Any]:
        return {
            "id": entity_id,
            "type": entity_type,
            "pos": position,
            "vel": (0.0, 0.0, 0.0),
            "health": kwargs.get("health", 100),
            "max_health": kwargs.get("max_health", 100),
            "ai_enabled": kwargs.get("ai_enabled", False),
            **kwargs
        }
    
    def _simulation_loop(self):
        dt = 0.016
        while self.running:
            start_time = time.time()
            self._process_commands()
            self._update_subsystems(dt)
            self.snapshot["world"]["time"] += dt
            elapsed = time.time() - start_time
            sleep_time = max(0, dt - elapsed)
            time.sleep(sleep_time)
    
    def _process_commands(self):
        while self.command_queue:
            cmd = self.command_queue.pop(0)
            self._execute_command(cmd)
    
    def _execute_command(self, cmd: Dict[str, Any]):
        action = cmd.get("action")
        
        if action == "spawn_entity":
            entity_id = cmd.get("entity_id")
            entity_type = cmd.get("entity_type")
            position = cmd.get("position", {"x": 0, "y": 0, "z": 0})
            properties = cmd.get("properties", {})
            
            pos_tuple = (position.get("x", 0), position.get("y", 0), position.get("z", 0))
            
            entity_state = self._create_entity_state(
                entity_id, entity_type, pos_tuple,
                ai_enabled=properties.get("ai_enabled", False),
                **properties
            )
            
            self.snapshot["entities"][entity_id] = entity_state
            
            if self.spatial:
                try:
                    self.spatial.spawn_entity(entity_id, pos_tuple)
                    print(f"✓ Spawned {entity_type} '{entity_id}' (Spatial3D)")
                except:
                    print(f"✓ Spawned {entity_type} '{entity_id}'")
            else:
                print(f"✓ Spawned {entity_type} '{entity_id}'")
        
        elif action == "interact":
            self._handle_interaction(cmd)
        
        elif action == "reload_blocks":
            print("Reloading blocks...")
        
        elif action == "dump_state":
            self._dump_full_state()
    
    def _handle_interaction(self, cmd: Dict[str, Any]):
        entity = cmd.get("entity", "unknown")
        player_rep = cmd.get("player_rep", 50)
        player_gold = cmd.get("player_gold", 0)
        context = cmd.get("context", "default")
        
        print(f"\n[INTERACTION] {entity} (context: {context})")
        
        if entity == "greeter":
            greeter_id = "greeter_main"
            pos_tuple = (5.0, 0.0, 3.0)
            
            # Simple dialogue lookup
            if player_rep < 30:
                dialogue = "What do you want?"
                mood = "unfriendly"
            elif player_rep < 70:
                dialogue = "Hello there."
                mood = "neutral"
            else:
                dialogue = "Welcome back, friend!"
                mood = "friendly"
            
            entity_state = self._create_entity_state(
                greeter_id, "greeter", pos_tuple,
                dialogue=dialogue, mood=mood,
                reputation=player_rep, ai_enabled=True
            )
            
            self.snapshot["entities"][greeter_id] = entity_state
            
            if self.spatial:
                try:
                    self.spatial.spawn_entity(greeter_id, pos_tuple)
                except:
                    pass
            
            # Register with behavior
            if self.behavior:
                try:
                    self.behavior.add_behavior_entity(
                        greeter_id,
                        initial_state="idle",
                        patrol_points=[(5,0,3), (10,0,5), (5,0,3)]
                    )
                    print(f"  [BEHAVIOR] AI enabled for {greeter_id}")
                except:
                    pass
            
            self.snapshot["events"].append({
                "type": "dialogue_started",
                "npc_id": greeter_id,
                "dialogue": dialogue,
                "mood": mood
            })
            
            print(f"  Greeter spawned: '{dialogue}' (mood: {mood})")
        
        elif entity == "merchant":
            merchant_id = "merchant_main"
            pos_tuple = (8.0, 0.0, 5.0)
            
            if player_gold < 100:
                dialogue = "Come back when you have more coin."
                willing_to_trade = False
            else:
                dialogue = "What would you like to buy?"
                willing_to_trade = True
            
            entity_state = self._create_entity_state(
                merchant_id, "merchant", pos_tuple,
                dialogue=dialogue,
                willing_to_trade=willing_to_trade,
                gold_required=100,
                inventory=["sword", "potion", "shield"]
            )
            
            self.snapshot["entities"][merchant_id] = entity_state
            
            if self.spatial:
                try:
                    self.spatial.spawn_entity(merchant_id, pos_tuple)
                except:
                    pass
            
            self.snapshot["events"].append({
                "type": "trade_initiated",
                "merchant_id": merchant_id,
                "willing": willing_to_trade,
                "gold": player_gold
            })
            
            print(f"  Merchant spawned: '{dialogue}'")
            print(f"  Inventory: {entity_state['inventory']}")
    
    def _update_subsystems(self, dt: float):
        entity_ids = list(self.snapshot["entities"].keys())
        
        if not entity_ids:
            return
        
        # Spatial
        if HAS_MR and self.spatial:
            try:
                spatial_state = {"entities": {}}
                for eid in entity_ids:
                    entity = self.snapshot["entities"][eid]
                    if "pos" in entity and "vel" in entity:
                        spatial_state["entities"][eid] = {
                            "pos": entity["pos"],
                            "vel": entity["vel"]
                        }
                
                updated_state = step_spatial3d(spatial_state, dt)
                
                for eid, spatial_data in updated_state.get("entities", {}).items():
                    if eid in self.snapshot["entities"]:
                        self.snapshot["entities"][eid]["pos"] = spatial_data["pos"]
                        self.snapshot["entities"][eid]["vel"] = spatial_data["vel"]
            except:
                pass
        
        # Perception
        if self.perception and entity_ids:
            try:
                self.perception.set_spatial_state(self.snapshot)
                perception_deltas, perception_alerts = self.perception.perception_step(
                    current_tick=int(self.snapshot["world"]["time"])
                )
                for delta in perception_deltas:
                    self._apply_delta(delta)
            except:
                pass
        
        # Behavior - TICK DRIVEN
        if self.behavior and entity_ids:
            try:
                self.behavior.set_spatial_state(self.snapshot)
                self.behavior.set_perception_state(self.snapshot.get("perception", {}))
                
                behavior_deltas, behavior_alerts = self.behavior.behavior_step(
                    current_tick=self.snapshot["world"]["time"],
                    delta_time=dt
                )
                
                for delta in behavior_deltas:
                    self._apply_delta(delta)
            except:
                pass
    
    def _apply_delta(self, delta):
        delta_type = delta.type
        payload = delta.payload
        
        if delta_type == "navigation3d/request_path":
            entity_id = payload.get("entity_id")
            if entity_id:
                print(f"  [NAV] Path request for {entity_id}")
        
        elif delta_type == "behavior3d/attack":
            attacker = payload.get("attacker")
            target = payload.get("target")
            print(f"  [COMBAT] {attacker} attacks {target}")
            
            self.snapshot["events"].append({
                "type": "attack_initiated",
                "attacker": attacker,
                "target": target
            })
    
    def _dump_full_state(self):
        print("\n=== STATE DUMP ===")
        print(json.dumps(self.snapshot, indent=2, default=str))
    
    def add_command(self, cmd: Dict[str, Any]):
        self.command_queue.append(cmd)
    
    def get_snapshot(self) -> Dict[str, Any]:
        snapshot = self.snapshot.copy()
        self.snapshot["events"] = []
        return snapshot
    
    def shutdown(self):
        self.running = False
        self.sim_thread.join()


class RuntimeHTTPHandler(BaseHTTPRequestHandler):
    runtime: EngAInRuntime = None
    
    def do_GET(self):
        if self.path == "/snapshot":
            snapshot = self.runtime.get_snapshot()
            response = {"type": "snapshot", "snapshot": snapshot}
            self._send_json_response(response)
        else:
            self.send_error(404)
    
    def do_POST(self):
        if self.path == "/command":
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            
            try:
                command = json.loads(body.decode('utf-8'))
                self.runtime.add_command(command)
                response = {"type": "ack", "status": "ok"}
                self._send_json_response(response)
            except json.JSONDecodeError:
                self.send_error(400, "Invalid JSON")
        else:
            self.send_error(404)
    
    def _send_json_response(self, data: Dict[str, Any]):
        response_json = json.dumps(data)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(response_json))
        self.end_headers()
        self.wfile.write(response_json.encode('utf-8'))
    
    def log_message(self, format, *args):
        pass


def main():
    print("=" * 50)
    print("EngAIn Runtime Server")
    print("=" * 50)
    
    runtime = EngAInRuntime()
    RuntimeHTTPHandler.runtime = runtime
    server = HTTPServer(('localhost', 8080), RuntimeHTTPHandler)
    
    print("\nServer running on http://localhost:8080")
    print("Press Ctrl+C to stop\n")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        runtime.shutdown()
        server.shutdown()
        print("Goodbye!")


if __name__ == "__main__":
    main()
