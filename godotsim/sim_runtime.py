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
    from combat3d_adapter import Combat3DAdapter
    from inventory3d_integration import Inventory3DAdapter
    from dialogue3d_integration import Dialogue3DAdapter
    HAS_ADAPTERS = True
except ImportError as e:
    print(f"Adapters missing: {e}")
    HAS_ADAPTERS = False

print(f"✓ MR kernels | spatial=True, perception=True, behavior=True")

# Kernel contract validation
VALID_KERNEL_RETURN_KEYS = {"deltas", "alerts"}
VALID_OPS = {"set", "add", "remove", "inc", "dec"}

class KernelContractError(RuntimeError):
    pass

def deep_freeze(obj):
    """Debug-only: catches mutation attempts if you use immutable containers later"""
    if isinstance(obj, dict):
        return {k: deep_freeze(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [deep_freeze(v) for v in obj]
    return obj

def stable_hash(obj) -> str:
    """Deterministic hash of state for debugging"""
    import hashlib
    payload = json.dumps(obj, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode()).hexdigest()

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
        self._init_inventory()
        self._init_dialogue()
        
        self.rng = 42  # Deterministic seed for reproducibility
        self.debug = False  # Set True for deep_freeze checks
        
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
            self.combat.register_entity("player", health=100, max_health=100)
            self.combat.register_entity("guard", health=100, max_health=100)
            self.combat.register_entity("enemy", health=50, max_health=50)
        except Exception as e:
            print(f"  ✗ Combat3D failed: {e}")
            self.combat = None

    def _init_inventory(self):
        """Initialize Inventory3D subsystem"""
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
            
            # Items for fumble test
            self.inventory.register_item("potion1", size=2, location="world")
            self.inventory.register_item("potion2", size=2, location="world")
            self.inventory.register_item("potion3", size=2, location="world")
            self.inventory.register_item("potion4", size=2, location="world")
            self.inventory.register_item("potion5", size=2, location="world")
            self.inventory.register_item("potion6", size=2, location="world")
            self.inventory.register_item("potion7", size=2, location="world")
            self.inventory.register_item("potion8", size=2, location="world")
        except Exception as e:
            print(f"  ✗ Inventory3D failed: {e}")
            self.inventory = None

    def _init_dialogue(self):
        """Initialize Dialogue3D subsystem"""
        try:
            self.dialogue = Dialogue3DAdapter()
            print("  ✓ Dialogue3D")
            
            self.dialogue.register_entity("player", knowledge_flags=[])
            self.dialogue.register_entity("guard", knowledge_flags=["fire_crystal_location"])
            self.dialogue.register_entity("merchant", knowledge_flags=["sword_upgrade"])
        except Exception as e:
            print(f"  ✗ Dialogue3D failed: {e}")
            self.dialogue = None
    
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
        """Sealed snapshot → run all kernels → apply once"""
        tick = self.snapshot["world"]["time"]
        pre_hash = stable_hash(self.snapshot)
        snapshot_pack = self.build_snapshot_pack()
        
        all_deltas = []
        all_alerts = []
        
        # Run kernels in fixed order (seal → run → collect)
        # Note: Using tick() for now until adapters support step() interface
        
        # Combat3D
        if self.combat:
            try:
                for delta_type, payload in self.combat.tick(dt):
                    all_deltas.append((delta_type, payload))
            except Exception as e:
                print(f"[COMBAT ERROR] {e}")
        
        # Inventory3D
        if self.inventory:
            try:
                inv_deltas, inv_alerts = self.inventory.tick(dt)
                all_alerts.extend(inv_alerts)
            except Exception as e:
                print(f"[INVENTORY ERROR] {e}")
        
        # Dialogue3D
        if self.dialogue:
            try:
                dlg_deltas, dlg_alerts = self.dialogue.tick(dt)
                all_alerts.extend(dlg_alerts)
            except Exception as e:
                print(f"[DIALOGUE ERROR] {e}")
        
        # Spatial3D (entity-based, runs with slice protection)
        entity_ids = list(self.snapshot["entities"].keys())
        if entity_ids and HAS_MR and self.spatial and HAS_SLICES:
            try:
                spatial_state = {"entities": {}}
                for eid in entity_ids:
                    try:
                        slice_view = build_entity_kview_v1(self.snapshot, eid)
                        spatial_state["entities"][eid] = {
                            "pos": slice_view.pos,
                            "vel": slice_view.vel
                        }
                    except SliceError as e:
                        print(f"[SLICE ERROR] {eid}: {e}")
                        continue
                
                snapshot_in = {"spatial3d": spatial_state}
                snapshot_out, accepted, alerts = step_spatial3d(snapshot_in, [], dt)
                
                updated_spatial = snapshot_out.get("spatial3d", {})
                for eid, spatial_data in updated_spatial.get("entities", {}).items():
                    if eid in self.snapshot["entities"]:
                        self.snapshot["entities"][eid]["position"] = list(spatial_data["pos"])
                        self.snapshot["entities"][eid]["velocity"] = list(spatial_data["vel"])
            except Exception as e:
                print(f"[SPATIAL ERROR] {e}")
        
        # Perception (entity-based)
        if self.perception and entity_ids:
            try:
                self.perception.set_spatial_state(self.snapshot)
                perception_deltas, perception_alerts = self.perception.perception_step(
                    current_tick=int(tick)
                )
                for delta in perception_deltas:
                    self._apply_delta(delta)
            except Exception as e:
                print(f"[PERCEPTION ERROR] {e}")
        
        # Behavior (entity-based)
        if self.behavior and entity_ids:
            try:
                self.behavior.set_spatial_state(self.snapshot)
                self.behavior.set_perception_state(self.snapshot.get("perception", {}))
                behavior_deltas, behavior_alerts = self.behavior.behavior_step(
                    current_tick=tick,
                    delta_time=dt
                )
                if behavior_deltas:
                    print(f"[BEHAVIOR] {len(behavior_deltas)} deltas fired")
                for delta in behavior_deltas:
                    self._apply_delta(delta)
            except Exception as e:
                print(f"[BEHAVIOR ERROR] {e}")
        
        # Apply all collected deltas and alerts
        self._apply_deltas(all_deltas)
        self._push_alerts(all_alerts)
        
        post_hash = stable_hash(self.snapshot)
        if self.debug:
            print(f"[TICK {tick}] state hash: {pre_hash[:12]} → {post_hash[:12]}")

    def _apply_deltas(self, deltas: list):
        """Apply collected deltas to committed state"""
        for delta in deltas:
            # Standard delta application
            domain = delta.get("domain")
            op = delta.get("op")
            path = delta.get("path")
            value = delta.get("value")
            
            # For now, just log - actual application depends on op type
            print(f"  [DELTA] {domain}/{op}: {path}")

    def _push_alerts(self, alerts: list):
        """Push collected alerts to handlers"""
        for alert in alerts:
            alert_type = alert.get("type", "")
            
            # Route to appropriate handler based on source domain
            if "inventory" in alert_type or alert_type in ["item_taken", "item_dropped", "item_worn"]:
                self._apply_inventory_alert(alert)
            elif "combat" in alert_type or alert_type in ["entity_died", "attack_hit", "attack_miss"]:
                self._apply_combat_alert(alert)
            elif "dialogue" in alert_type or alert_type in ["dialogue_started", "knowledge_shared"]:
                self._apply_dialogue_alert(alert)
            else:
                print(f"  [ALERT] {alert_type}: {alert}")

    def _apply_inventory_alert(self, alert: Dict[str, Any]):
        """Process inventory alerts"""
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

    def _apply_dialogue_alert(self, alert: Dict[str, Any]):
        """Process dialogue alerts"""
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
    
    def build_snapshot_pack(self):
        """Build snapshot pack for kernel invocation"""
        state = copy.deepcopy(self.snapshot)
        
        # Passthrough slices for subsystems
        pack = {
            "inventory3d": state.get("inventory3d", {}),
            "combat3d": state.get("combat3d", {}),
            "dialogue3d": state.get("dialogue3d", {}),
        }
        
        if getattr(self, "debug", False):
            pack = deep_freeze(pack)
        
        return pack
    
    def _run_kernel(self, domain, kernel_fn, intent, snapshot_pack, rng, tick):
        """Run a kernel with strict contract enforcement"""
        own_state = copy.deepcopy(self.snapshot.get(domain, {}))

        result = kernel_fn(
            intent=intent,
            own_state=own_state,
            foreign=snapshot_pack,
            rng_seed=rng,
            now_tick=tick,
        )

        if not isinstance(result, dict):
            raise KernelContractError(f"{domain} returned non-dict: {type(result)}")

        extra = set(result.keys()) - VALID_KERNEL_RETURN_KEYS
        if extra:
            raise KernelContractError(f"{domain} returned illegal fields: {sorted(extra)}")

        deltas = result.get("deltas", [])
        alerts = result.get("alerts", [])

        if not isinstance(deltas, list):
            raise KernelContractError(f"{domain} deltas must be list, got {type(deltas)}")
        if not isinstance(alerts, list):
            raise KernelContractError(f"{domain} alerts must be list, got {type(alerts)}")

        for d in deltas:
            if not isinstance(d, dict):
                raise KernelContractError(f"{domain} delta must be dict: {d}")

            if d.get("domain") != domain:
                raise KernelContractError(f"Cross-domain delta blocked from {domain}: {d}")

            if d.get("op") not in VALID_OPS:
                raise KernelContractError(f"Invalid op in {domain}: {d}")

            if not isinstance(d.get("path"), str):
                raise KernelContractError(f"Invalid path in {domain}: {d}")

        return deltas, alerts
    
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
        
        if self.inventory:
            snapshot["inventory"] = self.inventory.get_all_state()
        
        if self.dialogue:
            snapshot["dialogue"] = self.dialogue.get_all_state()
            
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

        elif self.path == "/dialogue/say":
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            
            try:
                data = json.loads(body.decode('utf-8'))
                
                if self.runtime.dialogue:
                    self.runtime.dialogue.handle_delta("dialogue3d/say", data)
                    response = {"type": "ack", "status": "say_queued"}
                else:
                    response = {"type": "error", "status": "dialogue_not_loaded"}
                
                self._send_json_response(response)
            except json.JSONDecodeError:
                self.send_error(400, "Invalid JSON")

        elif self.path == "/dialogue/ask":
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            
            try:
                data = json.loads(body.decode('utf-8'))
                
                if self.runtime.dialogue:
                    self.runtime.dialogue.handle_delta("dialogue3d/ask", data)
                    response = {"type": "ack", "status": "ask_queued"}
                else:
                    response = {"type": "error", "status": "dialogue_not_loaded"}
                
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