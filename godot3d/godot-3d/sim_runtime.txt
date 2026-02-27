#!/usr/bin/env python3
"""
sim_runtime.py - EngAIn Simulation Runtime Server

This is the **authority** - the single source of truth for the game world.
Godot is just a renderer that displays this simulation's state.

Architecture:
  Python (this file) → owns all game logic
  Godot → renders entities, sends input

Communication:
  Input: JSON commands from Godot via stdin
  Output: JSON world snapshots to stdout

Usage:
  python3 sim_runtime.py
"""

import sys
import json
import time
from spatial3d_adapter import Spatial3DStateViewAdapter
from perception_adapter import PerceptionStateView
from navigation_adapter import NavigationStateView
from combat3d_adapter import Combat3DAdapter


class EngAInRuntime:
    """
    Complete EngAIn simulation runtime.
    Wraps all subsystems and provides JSON interface for Godot.
    """
    
    def __init__(self):
        # Initialize all subsystems
        self.setup_spatial()
        self.setup_perception()
        self.setup_navigation()
        self.setup_combat()
        
        # Entity behavior tracking
        self.behavior_states = {}
        self.behavior_flags = {}
        
        self.tick_count = 0
        self.running = True
        
        self.log("[RUNTIME] EngAIn simulation initialized")
    
    def setup_spatial(self):
        """Initialize Spatial3D with zero gravity"""
        spatial_state = {
            "entities": {},
            "gravity": [0.0, 0.0, 0.0],
            "drag": 0.0,
            "static_entities": [],
            "perceivers": []
        }
        self.spatial = Spatial3DStateViewAdapter(state_slice=spatial_state)
        self.log("[SPATIAL] Initialized")
    
    def setup_perception(self):
        """Initialize Perception3D"""
        self.perception = PerceptionStateView(state_slice={})
        self.log("[PERCEPTION] Initialized")
    
    def setup_navigation(self):
        """Initialize Navigation3D"""
        self.navigation = NavigationStateView()
        self.log("[NAVIGATION] Initialized")
    
    def setup_combat(self):
        """Initialize Combat3D"""
        self.combat = Combat3DAdapter()
        self.log("[COMBAT] Initialized")
    
    def spawn_entity(self, entity_id, pos, radius=0.5, solid=True, tags=None,
                     perceiver=False, health=100.0, max_health=100.0):
        """
        Spawn entity in all subsystems
        
        Returns: success (bool)
        """
        if tags is None:
            tags = []
        
        # Spawn in Spatial3D
        spawn_data = {
            "entity_id": entity_id,
            "pos": pos,
            "radius": radius,
            "solid": solid,
            "tags": tags,
            "components": ["perceiver"] if perceiver else [],
        }
        
        if perceiver:
            spawn_data["perceiver"] = {
                "vision_range": 50.0,
                "fov": 180.0,
                "height": 1.8
            }
            spatial_state = self.spatial.save_to_state()
            if "perceivers" not in spatial_state:
                spatial_state["perceivers"] = []
            spatial_state["perceivers"].append(entity_id)
        
        success, alerts = self.spatial.handle_delta("spatial3d/spawn", spawn_data)
        
        if not success:
            self.log(f"[SPAWN] Failed: {entity_id}")
            return False
        
        # Register in Combat3D
        self.combat.register_entity(entity_id, health=health, max_health=max_health)
        
        # Initialize behavior
        self.behavior_states[entity_id] = "idle"
        self.behavior_flags[entity_id] = set()
        
        self.log(f"[SPAWN] {entity_id} at {pos} with {health}/{max_health} HP")
        return True
    
    def handle_input_command(self, command):
        """
        Process input command from Godot
        
        Command format:
        {
            "type": "move" | "attack" | "spawn" | "damage",
            "entity_id": "player",
            "data": {...}
        }
        """
        cmd_type = command.get("type")
        entity_id = command.get("entity_id")
        data = command.get("data", {})
        
        if cmd_type == "move":
            # Move entity to target position
            target_pos = data.get("target_pos")
            speed = data.get("speed", 5.0)
            self.spatial.handle_delta("spatial3d/move", {
                "entity_id": entity_id,
                "target_pos": target_pos,
                "speed": speed
            })
            
        elif cmd_type == "attack":
            # Apply damage
            target_id = data.get("target_id")
            damage = data.get("damage", 25.0)
            self.combat.handle_delta("combat3d/apply_damage", {
                "source": entity_id,
                "target": target_id,
                "amount": damage
            })
            self.log(f"[INPUT] {entity_id} attacks {target_id} for {damage} damage")
            
        elif cmd_type == "spawn":
            # Spawn new entity
            pos = data.get("pos", [0, 0, 0])
            health = data.get("health", 100.0)
            self.spawn_entity(entity_id, pos=pos, health=health, max_health=health)
            
        elif cmd_type == "damage":
            # Direct damage application (for testing)
            target_id = data.get("target_id")
            damage = data.get("damage", 10.0)
            self.combat.handle_delta("combat3d/apply_damage", {
                "source": entity_id,
                "target": target_id,
                "amount": damage
            })
    
    def tick(self, delta_time=0.016):
        """Run one simulation tick"""
        self.tick_count += 1
        
        # 1. Physics
        self.spatial.physics_step(delta_time=delta_time)
        
        # 2. Perception
        spatial_state = self.spatial.save_to_state()
        self.perception.set_spatial_state({"spatial3d": spatial_state})
        try:
            self.perception.perception_step(current_tick=self.tick_count)
        except Exception as e:
            pass  # Perception may fail if no perceivers
        
        # 3. Navigation
        self.navigation.update_obstacles_from_spatial({"spatial3d": spatial_state})
        self.navigation.navigation_step(current_tick=self.tick_count)
        
        # 4. Combat
        combat_deltas = self.combat.tick()
        for delta_type, payload in combat_deltas:
            self.route_delta(delta_type, payload)
        
        # 5. Behavior (simple for now)
        self.behavior_step()
    
    def route_delta(self, delta_type, payload):
        """Route subsystem deltas"""
        if delta_type == "behavior3d/set_flag":
            entity_id = payload["entity"]
            flag = payload["flag"]
            if entity_id not in self.behavior_flags:
                self.behavior_flags[entity_id] = set()
            self.behavior_flags[entity_id].add(flag)
            
        elif delta_type == "navigation3d/disable":
            entity_id = payload["entity"]
            nav_state = self.navigation.save_to_state()
            if "active_paths" in nav_state and entity_id in nav_state["active_paths"]:
                del nav_state["active_paths"][entity_id]
    
    def behavior_step(self):
        """Simple behavior processing"""
        for entity_id, state in list(self.behavior_states.items()):
            flags = self.behavior_flags.get(entity_id, set())
            
            if "dead" in flags:
                if state != "dead":
                    self.behavior_states[entity_id] = "dead"
                continue
            
            if "low_health" in flags and state != "fleeing":
                self.behavior_states[entity_id] = "fleeing"
                continue
    
    def get_world_snapshot(self):
        """
        Generate complete world snapshot for Godot
        
        Returns: dict with all entity states
        """
        snapshot = {
            "tick": self.tick_count,
            "entities": {}
        }
        
        # Get spatial state
        spatial_state = self.spatial.save_to_state()
        entities = spatial_state.get("entities", {})
        
        for entity_id, entity_data in entities.items():
            # Combine data from all subsystems
            snapshot["entities"][entity_id] = {
                # Spatial
                "pos": entity_data.get("pos", [0, 0, 0]),
                "vel": entity_data.get("vel", [0, 0, 0]),
                "radius": entity_data.get("radius", 0.5),
                "tags": entity_data.get("tags", []),
                
                # Combat
                "health": self.combat.get_entity_health(entity_id)[0],
                "max_health": self.combat.get_entity_health(entity_id)[1],
                "alive": self.combat.is_alive(entity_id),
                
                # Behavior
                "state": self.behavior_states.get(entity_id, "idle"),
                "flags": list(self.behavior_flags.get(entity_id, set()))
            }
        
        return snapshot
    
    def log(self, message):
        """Log to stderr (stdout is for JSON communication)"""
        print(message, file=sys.stderr, flush=True)
    
    def run_loop(self):
        """
        Main runtime loop
        
        Reads commands from stdin, processes tick, writes snapshot to stdout
        """
        self.log("[RUNTIME] Starting main loop")
        self.log("[RUNTIME] Waiting for commands on stdin...")
        
        while self.running:
            try:
                # Read command from stdin (blocking)
                line = sys.stdin.readline()
                if not line:
                    break
                
                line = line.strip()
                if not line:
                    continue
                
                # Parse command
                command = json.loads(line)
                
                # Handle special commands
                if command.get("type") == "quit":
                    self.log("[RUNTIME] Quit command received")
                    break
                
                elif command.get("type") == "tick":
                    # Just tick, no other command
                    pass
                
                else:
                    # Process input command
                    self.handle_input_command(command)
                
                # Advance simulation
                self.tick()
                
                # Send snapshot back to Godot
                snapshot = self.get_world_snapshot()
                print(json.dumps(snapshot), flush=True)
                
            except json.JSONDecodeError as e:
                self.log(f"[ERROR] Invalid JSON: {e}")
            except KeyboardInterrupt:
                self.log("[RUNTIME] Interrupted")
                break
            except Exception as e:
                self.log(f"[ERROR] {e}")
                import traceback
                traceback.print_exc(file=sys.stderr)
        
        self.log("[RUNTIME] Shutting down")


def main():
    """Entry point"""
    # Create runtime
    runtime = EngAInRuntime()
    
    # Spawn initial scene
    runtime.spawn_entity("guard", pos=[-3, 0, 0], perceiver=True, 
                        health=100.0, max_health=100.0)
    runtime.spawn_entity("enemy", pos=[3, 0, 0], 
                        health=50.0, max_health=50.0)
    runtime.spawn_entity("wall", pos=[0, 0, 0], radius=2.0)
    
    # Run main loop
    runtime.run_loop()


if __name__ == "__main__":
    main()
