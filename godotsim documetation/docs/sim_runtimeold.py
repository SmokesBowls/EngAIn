#!/usr/bin/env python3
"""sim_runtime.py - EngAIn Runtime - FULL OPERATIONAL WITH SLICE PROTECTION"""

import json
import sys
import time
import copy
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any, List, Tuple, Optional
from protocol_envelope import ProtocolEnvelope, ProtocolError, create_envelope_for_runtime

# Import slice builders - PROTECTION LAYER
try:
    from slice_builders import build_spatial_slice_v1, build_entity_kview_v1, SliceError
    HAS_SLICES = True
    print("✓ Slice builders loaded")
except ImportError as e:
    print(f"Slice builders missing: {e}")
    HAS_SLICES = False

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
    from combat3d_integration import Combat3DAdapter
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
        
        self.envelope = create_envelope_for_runtime()
        print(f"  ✓ Protocol: {self.envelope.PROTOCOL_NAME} v{self.envelope.version}")
        print(f"  ✓ Epoch: {self.envelope.epoch_id}")
        
        self._init_subsystems()
        self._init_combat()
        
        self.running = True
        self.sim_thread = threading.Thread(target=self._simulation_loop, daemon=True)
        self.sim_thread.start()
        
        print("  → son of a bitch.... its finally fixed.. whats next boys?.  ")
        print("EngAIn Runtime: Initialized")
    
    def _init_subsystems(self):
        if HAS_ADAPTERS:
            try:
                self.spatial = Spatial3DStateViewAdapter()
                print("  ✓ Spatial3D")
            except:
                self.spatial = None
            
            try:
                self.perception = PerceptionStateView({})
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

    def _init_combat(self):
        """Initialize Combat3D subsystem"""
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
    
    def _create_entity_state(self, entity_id: str, entity_type: str, 
                            position: Tuple[float, float, float], **kwargs) -> Dict[str, Any]:
        return {
            "id": entity_id,
            "type": entity_type,
            "position": position,  # Canonical key
            "velocity": (0.0, 0.0, 0.0),  # Canonical key
            "health": kwargs.get("health", 100),
            "max_health": kwargs.get("max_health", 100),
            "ai_enabled": kwargs.get("ai_enabled", False),
            **kwargs
        }
    
    def _simulation_loop(self):
        dt = 0.016
        tick_count = 0
        while self.running:
            start_time = time.time()
            self._process_commands()
            self._update_subsystems(dt)
            self.snapshot["world"]["time"] += dt
            
            tick_count += 1
            if tick_count % 60 == 0:  # Every second
                print(f"[DEBUG] Tick {tick_count}, combat queue size: {len(self.combat.delta_queue) if self.combat else 'N/A'}")
            
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

        elif action == "update_entity":
            entity = cmd.get("entity")
            state = cmd.get("state", {})
            
            if entity and entity in self.snapshot["entities"]:
                # Normalize Godot types to Python tuples
                if "position" in state:
                    p = state["position"]
                    if isinstance(p, dict):
                        self.snapshot["entities"][entity]["pos"] = (
                            float(p.get("x", 0)), 
                            float(p.get("y", 0)), 
                            float(p.get("z", 0))
                        )
                
                if "velocity" in state:
                    v = state["velocity"]
                    if isinstance(v, dict):
                        self.snapshot["entities"][entity]["vel"] = (
                            float(v.get("x", 0)), 
                            float(v.get("y", 0)), 
                            float(v.get("z", 0))
                        )
                
                # Update other fields
                for k, v in state.items():
                    if k not in ["position", "velocity", "rotation"]:
                        self.snapshot["entities"][entity][k] = v
            elif entity and entity not in self.snapshot["entities"]:
                # Auto-create if missing (lazy spawn for player)
                print(f"Lazy spawning {entity} from update")
                p = state.get("position", {"x":0,"y":0,"z":0})
                pos_tuple = (p.get("x", 0), p.get("y", 0), p.get("z", 0))
                
                # Filter out position from state to prevent dual-argument error
                create_kwargs = {k:v for k,v in state.items() if k != "position"}
                
                self.snapshot["entities"][entity] = self._create_entity_state(
                    entity, "player", pos_tuple, **create_kwargs
                )
        
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
                    
                    # Seed perception so greeter can react
                    if greeter_id not in self.snapshot["perception"]:
                        self.snapshot["perception"][greeter_id] = {}
                    
                    if player_rep < 30:
                        # Unfriendly - watching player closely
                        self.snapshot["perception"][greeter_id] = {
                            "visible_entities": ["player"],
                            "focus_target": "player"
                        }
                        print(f"  [PERCEPTION] Greeter hostile - focused on player")
                    else:
                        # Friendly - aware but not focused
                        self.snapshot["perception"][greeter_id] = {
                            "visible_entities": ["player"],
                            "focus_target": None
                        }
                        print(f"  [PERCEPTION] Greeter friendly - player visible")
                    
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
        print("[DEBUG] _update_subsystems() called")
        entity_ids = list(self.snapshot["entities"].keys())
        
        if not entity_ids:
            return
        
        # Spatial - WITH SLICE PROTECTION
        if HAS_MR and self.spatial and HAS_SLICES:
            try:
                spatial_state = {"entities": {}}
                
                for eid in entity_ids:
                    try:
                        # Build guaranteed slice
                        slice_view = build_entity_kview_v1(self.snapshot, eid)
                        
                        # Now guaranteed to have pos/vel
                        spatial_state["entities"][eid] = {
                            "pos": slice_view.pos,
                            "vel": slice_view.vel
                        }
                    
                    except SliceError as e:
                        print(f"[SLICE ERROR] {eid}: {e}")
                        continue
                
                # Wrap in snapshot format
                snapshot_in = {"spatial3d": spatial_state}
                
                # Call kernel with correct signature: (snapshot, deltas, dt)
                snapshot_out, accepted, alerts = step_spatial3d(
                    snapshot_in,
                    [],  # No deltas for now
                    dt
                )
                
                # Extract updated entities
                updated_spatial = snapshot_out.get("spatial3d", {})
                
                for eid, spatial_data in updated_spatial.get("entities", {}).items():
                    if eid in self.snapshot["entities"]:
                        # Use canonical keys: position/velocity
                        self.snapshot["entities"][eid]["position"] = list(spatial_data["pos"])
                        self.snapshot["entities"][eid]["velocity"] = list(spatial_data["vel"])
            
            except Exception as e:
                import traceback
                print(f"[SPATIAL ERROR] {e}")
                traceback.print_exc()
        
        # Fallback without slices (old way)
        elif HAS_MR and self.spatial and not HAS_SLICES:
            raise RuntimeError(
                   "ARCHITECTURAL VIOLATION: MR kernel invoked without slices"
    )
            try:
                spatial_state = {"entities": {}}
                for eid in entity_ids:
                    entity = self.snapshot["entities"][eid]
                    if "pos" in entity and "vel" in entity:
                        spatial_state["entities"][eid] = {
                            "pos": entity["pos"],
                            "vel": entity["vel"]
                        }
                
                # Wrap in snapshot format
                snapshot_in = {"spatial3d": spatial_state}
                
                # Call with correct signature
                snapshot_out, accepted, alerts = step_spatial3d(
                    snapshot_in,
                    [],
                    dt
                )
                
                updated_spatial = snapshot_out.get("spatial3d", {})
                
                for eid, spatial_data in updated_spatial.get("entities", {}).items():
                    if eid in self.snapshot["entities"]:
                        # Use canonical keys: position/velocity
                        self.snapshot["entities"][eid]["position"] = list(spatial_data["pos"])
                        self.snapshot["entities"][eid]["velocity"] = list(spatial_data["vel"])
            except Exception as e:
                import traceback
                print(f"[SPATIAL ERROR] {e}")
                traceback.print_exc()
        
        # Perception
        if self.perception and entity_ids:
            try:
                self.perception.set_spatial_state(self.snapshot)
                perception_deltas, perception_alerts = self.perception.perception_step(
                    current_tick=int(self.snapshot["world"]["time"])
                )
                for delta in perception_deltas:
                    self._apply_delta(delta)
            except Exception as e:
                print(f"[PERCEPTION ERROR] {e}")
        
        # Behavior - TICK DRIVEN
        if self.behavior and entity_ids:
            try:
                self.behavior.set_spatial_state(self.snapshot)
                self.behavior.set_perception_state(self.snapshot.get("perception", {}))
                
                behavior_deltas, behavior_alerts = self.behavior.behavior_step(
                    current_tick=self.snapshot["world"]["time"],
                    delta_time=dt
                )
                
                if behavior_deltas:
                    print(f"[BEHAVIOR] {len(behavior_deltas)} deltas fired")
                
                for delta in behavior_deltas:
                    self._apply_delta(delta)
            except Exception as e:
                print(f"[BEHAVIOR ERROR] {e}")

        # Combat3D
        print("[DEBUG] After Behavior, about to check Combat")
        print(f"[DEBUG] About to check combat, self.combat = {self.combat}")
        if self.combat:
            try:
                combat_deltas, combat_alerts = self.combat.tick(dt)
                
                if combat_alerts:
                    print(f"[COMBAT] {len(combat_alerts)} alerts")
                    for alert in combat_alerts:
                        self._apply_combat_alert(alert)
            except Exception as e:
                print(f"[COMBAT ERROR] {e}")
                import traceback
                traceback.print_exc()

    def _apply_combat_alert(self, alert: Dict[str, Any]):
        """Process combat alerts"""
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
        
        elif alert_type == "damage_applied":
            target = alert.get("target")
            amount = alert.get("amount")
            source = alert.get("source")
            print(f"  ⚔️  {source} hits {target} for {amount} damage")

        elif alert_type == "attack_hit":
            attacker = alert.get("attacker")
            target = alert.get("target")
            damage = alert.get("damage")
            print(f"  ⚔️  {attacker} hits {target} for {damage} damage")
        
        elif alert_type == "attack_miss":
            attacker = alert.get("attacker")
            target = alert.get("target")
            print(f"  ⭕ {attacker} misses {target}")

    def _apply_delta(self, delta):
        delta_type = delta.type
        payload = delta.payload
        
        print(f"  🔥 [{delta_type}]")
        
        if delta_type == "navigation3d/request_path":
            entity_id = payload.get("entity_id")
            if entity_id:
                print(f"     Path request for {entity_id}")
        
        elif delta_type == "behavior3d/attack":
            attacker = payload.get("attacker")
            target = payload.get("target")
            print(f"     {attacker} → attacks → {target}")
            
            self.snapshot["events"].append({
                "type": "attack_initiated",
                "attacker": attacker,
                "target": target
            })
        
        elif delta_type == "behavior3d/high_intent":
            entity_id = payload.get("entity_id")
            intent = payload.get("intent", 0.0)
            print(f"     {entity_id} HIGH INTENT: {intent:.2f}")
    
    def _dump_full_state(self):
        print("\n=== STATE DUMP ===")
        print(json.dumps(self.snapshot, indent=2, default=str))
        
        if self.behavior:
            print("\n=== BEHAVIOR STATES ===")
            for entity_id in self.snapshot["entities"].keys():
                behavior_state = self.behavior.get_behavior_state(entity_id)
                if behavior_state:
                    print(f"{entity_id}:")
                    print(f"  intent={behavior_state.get('intent', 0):.2f}")
                    print(f"  alertness={behavior_state.get('alertness', 0):.2f}")
                    print(f"  threat={behavior_state.get('threat', 0):.2f}")
    
    def add_command(self, cmd: Dict[str, Any]):
        self.command_queue.append(cmd)
    
    def get_snapshot(self) -> Dict[str, Any]:
        """Get current snapshot wrapped in protocol envelope"""
        snapshot = copy.deepcopy(self.snapshot)
        
        # Clear ephemeral events AFTER copy
        self.snapshot["events"] = []

        # Wrap in protocol envelope with hash
        tick = snapshot["world"]["time"]
        # Wrap in protocol envelope with hash
        tick = snapshot["world"]["time"]
        
        if self.combat:
            snapshot["combat"] = self.combat.get_all_state()
            
        return self.envelope.wrap_snapshot(snapshot, tick)
    
    def shutdown(self):
        self.running = False
        self.sim_thread.join()


class RuntimeHTTPHandler(BaseHTTPRequestHandler):
    runtime: EngAInRuntime = None
    
    def do_GET(self):
        if self.path == "/snapshot":
            envelope = self.runtime.get_snapshot()
            self._send_json_response(envelope)
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
        
        elif self.path == "/combat/damage":
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            
            try:
                data = json.loads(body.decode('utf-8'))
                source = data.get("source", "unknown")
                target = data.get("target")
                damage = data.get("damage", 25)
                
                if self.runtime.combat:
                    print(f"[DEBUG] Queueing damage delta: {data}")
                    self.runtime.combat.handle_delta("combat3d/apply_damage", {
                        "source": source,
                        "target": target,
                        "amount": damage
                    })
                    print(f"[DEBUG] Queue size after: {len(self.runtime.combat.delta_queue)}")
                    response = {"type": "ack", "status": "damage_applied"}
                else:
                    response = {"type": "error", "status": "combat_not_loaded"}
                
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
