#!/usr/bin/env python3
"""runtime_core.py — EngAIn Runtime core (simulation state, subsystems, kernel loop).

This is the engine. Contains:
    - EngAInRuntime: central state machine, subsystem init, simulation loop
    - Kernel contract enforcement
    - Snapshot management with protocol envelope

Delegates to:
    - scene_manager.SceneManager for scene/entity operations
    - command_dispatcher.CommandDispatcher for command routing
    - http_handlers.RuntimeHTTPHandler for HTTP transport (imported at server level)

All 2000+ lines of battle-tested logic live here. sim_runtime.py is just the entry point.
"""

import copy
import json
import os
import re
import subprocess
import sys
import threading
import time
import traceback
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

# ── Critical EngAIn imports ──────────────────────────────────────
try:
    from protocol_envelope import ProtocolEnvelope, ProtocolError, create_envelope_for_runtime
    import engain_hooks
    from vault_linker import VaultLinker
except ImportError as e:
    print(f"Critical EngAIn modules missing: {e}")
    sys.exit(1)

# ── Modular components ───────────────────────────────────────────
from scene_manager import SceneManager
from command_dispatcher import CommandDispatcher
from vault_manager import VaultRegistry, bulk_load_scenes


# ── Locate project root ─────────────────────────────────────────

def _find_root_dir(start_dir: str) -> str:
    """Walk upward to find repo root (has engain_ingest.py or mettaext/)."""
    cur = os.path.abspath(start_dir)
    for _ in range(8):
        if os.path.exists(os.path.join(cur, "engain_ingest.py")) or os.path.isdir(os.path.join(cur, "mettaext")):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    return os.path.dirname(os.path.abspath(start_dir))


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = _find_root_dir(THIS_DIR)

print(f"Current working directory: {os.getcwd()}")
print(f"Script location: {os.path.abspath(__file__)}")
print(f"ROOT_DIR: {ROOT_DIR}")


# ── Instrumentation hook ─────────────────────────────────────────

def __hook__(chain, event, module=None, file=None, func=None, **kw):
    """Runtime instrumentation hook for engain_hooks."""
    pass


# ── Optional subsystem imports ───────────────────────────────────

try:
    from slice_builders import build_spatial_slice_v1, build_entity_kview_v1, SliceError
    HAS_SLICES = True
except ImportError:
    HAS_SLICES = False

try:
    from spatial3d_mr import step_spatial3d
    from perception_mr import step_perception
    from behavior3d_mr import update_behavior_mr
    HAS_MR = True
except ImportError:
    HAS_MR = False
    print("[BOOT] MR kernels not found — running without spatial/perception/behavior kernels")

try:
    from spatial3d_adapter import Spatial3DStateViewAdapter
    from perception_adapter import PerceptionStateView
    from behavior_adapter import BehaviorStateView
    HAS_ADAPTERS = True
except ImportError:
    HAS_ADAPTERS = False
    print("[BOOT] State view adapters not found — subsystems will be None")

try:
    from combat3d_adapter import Combat3DAdapter
    HAS_COMBAT = True
except ImportError:
    HAS_COMBAT = False

try:
    from inventory3d_integration import Inventory3DAdapter
    HAS_INVENTORY = True
except ImportError:
    HAS_INVENTORY = False

try:
    from dialogue3d_integration import Dialogue3DAdapter
    HAS_DIALOGUE = True
except ImportError:
    HAS_DIALOGUE = False


# ── Kernel contract enforcement ──────────────────────────────────

VALID_KERNEL_RETURN_KEYS = {"deltas", "alerts"}
VALID_OPS = {"set", "add", "remove", "merge", "push", "increment", "decrement"}


class KernelContractError(Exception):
    pass


def deep_freeze(obj):
    """Recursively freeze dicts/lists for immutability checks in debug mode."""
    if isinstance(obj, dict):
        return {k: deep_freeze(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return tuple(deep_freeze(v) for v in obj)
    return obj


# ═════════════════════════════════════════════════════════════════
# EngAInRuntime — The Central State Machine
# ═════════════════════════════════════════════════════════════════

class EngAInRuntime:
    """
    EngAIn Runtime: simulation state, subsystem orchestration, kernel loop.

    Initialization order:
        1. Snapshot (state)
        2. SceneManager (scenes, entities, vault linking)
        3. Protocol envelope
        4. Subsystems (spatial, perception, behavior, combat, inventory, dialogue)
        5. CommandDispatcher (routes commands to SceneManager / subsystems)
        6. Simulation thread
    """

    def __init__(self):
        print("\n[BOOT] Initializing EngAIn Runtime...")

        # ── 1. Core state ────────────────────────────────────────
        self.snapshot: Dict[str, Any] = {
            "scene_id": None,
            "entities": {},
            "spatial": {},
            "perception": {},
            "behavior": {},
            "world": {"time": 0.0, "weather": "clear"},
            "events": [],
            "scene": None,
            "scene_raw": None,
        }

        # ── 2. Scene & Vault management ──────────────────────────
        self.scene_manager = SceneManager(self)

        # VaultLinker (existing module)
        self.vault_linker = VaultLinker()
        self.vault_scenes: Dict[str, Any] = {}     # All scenes from linked vaults
        self.vault_registry = VaultRegistry(os.path.join(ROOT_DIR, "vault_registry.json"))

        # After vault_linker init
        if os.path.exists("/path/to/vault/vault.manifest.json"):
            self.vault_linker.link("/path/to/vault/vault.manifest.json", "/path/to/vault")
            for sid, scene in self.vault_linker.get_all_scenes().items():
                self.vault_scenes[sid] = scene
            print(f"[BOOT] Auto-linked vault: {len(self.vault_scenes)} scenes")

        # ── 3. Protocol envelope ─────────────────────────────────
        self.envelope = create_envelope_for_runtime()
        print(f"  ✓ Protocol: {self.envelope.PROTOCOL_NAME} v{self.envelope.version}")
        print(f"  ✓ Epoch: {self.envelope.epoch_id}")

        # ── 4. Internal queues ───────────────────────────────────
        self._last_result = None
        self.delta_queue: List[Dict[str, Any]] = []
        self.command_queue: List[Dict[str, Any]] = []

        # ── 5. Subsystems ────────────────────────────────────────
        self._init_subsystems()
        self._init_combat()
        self._init_inventory()
        self._init_dialogue()

        # ── 6. Command dispatcher ────────────────────────────────
        self.command_dispatcher = CommandDispatcher(self, self.scene_manager)

        # ── 7. Simulation loop ───────────────────────────────────
        self.rng = 42
        self.debug = False
        self.running = True
        self._tick_counter = 0
        self.sim_thread = threading.Thread(target=self._simulation_loop, daemon=True)
        self.sim_thread.start()
        
        print("  → EngAIn Runtime: Initialized")

    # ── Property accessors for backward compatibility ────────────

    @property
    def scenes(self) -> Dict[str, Any]:
        return self.scene_manager.scenes

    @property
    def entity_cards(self) -> Dict[str, Any]:
        return self.scene_manager.entity_cards

    # ── Delegation methods (so bulk_load_scenes etc. can call runtime.load_scene) ──

    def load_scene(self, scene_doc: Dict[str, Any], activate: bool = False) -> str:
        """Delegate to SceneManager."""
        return self.scene_manager.load_scene(scene_doc, activate=activate)

    def select_active_scene(self, scene_id: str) -> bool:
        """Delegate to SceneManager."""
        return self.scene_manager.select_active_scene(scene_id)

    # ── Subsystem initialization ─────────────────────────────────

    def _init_subsystems(self):
        """Initialize state view adapters for spatial, perception, behavior."""
        if HAS_ADAPTERS:
            try:
                self.spatial = Spatial3DStateViewAdapter()
                print("  ✓ Spatial3D adapter loaded")
            except Exception as e:
                self.spatial = None
                print(f"  ✗ Spatial3D adapter failed: {e}")

            try:
                self.perception = PerceptionStateView({})
                print("  ✓ Perception adapter loaded")
            except Exception as e:
                self.perception = None
                print(f"  ✗ Perception adapter failed: {e}")

            try:
                self.behavior = BehaviorStateView({"entities": {}})
                print("  ✓ Behavior adapter loaded")
            except Exception as e:
                self.behavior = None
                print(f"  ✗ Behavior adapter failed: {e}")
        else:
            self.spatial = None
            self.perception = None
            self.behavior = None

    def _init_combat(self):
        if HAS_COMBAT:
            try:
                self.combat = Combat3DAdapter()
                print("  ✓ Combat3D adapter loaded")
            except Exception as e:
                self.combat = None
                print(f"  ✗ Combat3D adapter failed: {e}")
        else:
            self.combat = None

    def _init_inventory(self):
        if HAS_INVENTORY:
            try:
                self.inventory = Inventory3DAdapter()
                print("  ✓ Inventory3D adapter loaded")
            except Exception as e:
                self.inventory = None
                print(f"  ✗ Inventory3D adapter failed: {e}")
        else:
            self.inventory = None

    def _init_dialogue(self):
        if HAS_DIALOGUE:
            try:
                self.dialogue = Dialogue3DAdapter()
                print("  ✓ Dialogue3D adapter loaded")
            except Exception as e:
                self.dialogue = None
                print(f"  ✗ Dialogue3D adapter failed: {e}")
        else:
            self.dialogue = None

    # ── Command queue ────────────────────────────────────────────

    def add_command(self, cmd: Dict[str, Any]):
        """Queue a command for processing on next simulation tick."""
        self.command_queue.append(cmd)

    def drain_commands(self, dt=None):
        """Public method to process queued simulation commands."""
        while self.command_queue:
            cmd = self.command_queue.pop(0)
            self._execute_command(cmd)

    def tick(self, dt=0.016):
        """Public simulation step."""
        self._process_tick(self._tick_counter)
        self._tick_counter += 1

    # ── Simulation loop ──────────────────────────────────────────

    # runtime_core.py

    def _simulation_loop(self):
        """Main simulation tick loop (16ms target = ~60 fps)."""
        target_dt = 1.0 / 60.0
        next_frame = time.perf_counter()

        while self.running:
            try:
                self.drain_commands()
                self.tick()
            except Exception as e:
                print(f"[SIM] Simulation error: {e}")
                traceback.print_exc()

            # Frame pacing (monotonic) with drift control
            next_frame += target_dt
            now = time.perf_counter()
            sleep_time = next_frame - now

            if sleep_time > 0.0:
                time.sleep(sleep_time)
            else:
                # If we fell behind, resync so we don't spiral.
                next_frame = now

    def _process_tick(self, tick: int):
        """Process one simulation tick: run kernels, apply deltas."""
        self.snapshot["world"]["time"] = tick * (1.0 / 60.0)

        # Do NOT do command draining here if the loop (or pump) already calls drain_commands().
        # Keep draining in exactly one place to avoid double-processing.
        # (Remove the old "if not self.command_queue: pass" block entirely.)

        # Run kernels if available
        if HAS_MR and HAS_SLICES:
            snapshot_pack = self.build_snapshot_pack()
            all_deltas = []
            all_alerts = []

            # Spatial kernel
            if self.spatial:
                try:
                    snapshot_in = {"spatial3d": self.snapshot.get("spatial", {})}
                    # step_spatial3d(snapshot_in, deltas, dt)
                    snapshot_out, accepted, alerts = step_spatial3d(snapshot_in, [], 1.0/60.0)
                    
                    if isinstance(snapshot_out, dict) and "spatial3d" in snapshot_out:
                        self.snapshot["spatial"] = snapshot_out["spatial3d"]
                    
                    # Mirror to entities for compatibility
                    updated_entities = snapshot_out.get("spatial3d", {}).get("entities", {})
                    for eid, s_data in updated_entities.items():
                        if eid in self.snapshot["entities"]:
                            self.snapshot["entities"][eid]["pos"] = s_data["pos"]
                            self.snapshot["entities"][eid]["vel"] = s_data["vel"]

                    all_alerts.extend(alerts)
                except Exception as e:
                    print(f"[KERNEL] spatial3d error: {e}")

            # Perception kernel
            if self.perception:
                try:
                    # step_perception(spatial, perception, tick)
                    new_p_state, p_deltas, p_alerts = step_perception(
                        self.snapshot,
                        self.snapshot.get("perception", {}),
                        tick
                    )
                    self.snapshot["perception"] = new_p_state
                    all_deltas.extend(p_deltas)
                    all_alerts.extend(p_alerts)
                except Exception as e:
                    print(f"[KERNEL] perception3d error: {e}")

            # Behavior kernel
            if self.behavior:
                try:
                    # Update adapter with latest snapshots
                    self.behavior.set_spatial_state(self.snapshot.get("spatial", {}))
                    self.behavior.set_perception_state(self.snapshot.get("perception", {}))
                    
                    b_deltas, b_alerts = self.behavior.behavior_step(current_tick=tick, delta_time=1.0/60.0)
                    
                    # behavior_adapter returns Delta objects, convert to dicts
                    for d in b_deltas:
                        all_deltas.append({
                            "domain": d.tags[0] if d.tags else "behavior3d",
                            "op": "set",
                            "path": f"behavior/{d.payload['entity_id']}",
                            "value": d.payload
                        })
                    all_alerts.extend(b_alerts)
                except Exception as e:
                    print(f"[KERNEL] behavior3d error: {e}")

            # Apply deltas
            for delta in all_deltas:
                self._apply_delta(delta)

            # Record alerts as events
            for alert in all_alerts:
                if hasattr(alert, "message"):
                    self.snapshot["events"].append({"type": "alert", "tick": tick, "message": alert.message, "level": alert.level})
                elif isinstance(alert, dict):
                    self.snapshot["events"].append({"type": "alert", "tick": tick, **alert})
                else:
                    self.snapshot["events"].append({"type": "alert", "tick": tick, "data": str(alert)})

    def _execute_command(self, cmd: Dict[str, Any]):
        """Execute a queued simulation command (spawn, update, interact, etc.)."""
        action = cmd.get("command") or cmd.get("action") or ""

        if action == "spawn_entity":
            eid = cmd.get("entity_id") or cmd.get("id")
            if eid:
                self.snapshot["entities"][eid] = cmd.get("data", {"id": eid})
                self.snapshot["events"].append({"type": "entity_spawned", "entity_id": eid})

        elif action == "update_entity":
            eid = cmd.get("entity_id") or cmd.get("id")
            if eid and eid in self.snapshot["entities"]:
                updates = cmd.get("data", {})
                self.snapshot["entities"][eid].update(updates)

        elif action == "interact":
            source = cmd.get("source")
            target = cmd.get("target")
            self.snapshot["events"].append({
                "type": "interaction", "source": source, "target": target,
                "interaction_type": cmd.get("interaction_type", "generic"),
            })

        elif action == "reload_blocks":
            print("[SIM] Reload blocks requested (not yet implemented)")

        elif action == "dump_state":
            print(f"[SIM] State dump:\n{json.dumps(self.snapshot, indent=2, default=str)[:2000]}")

    # ── Kernel runner with contract enforcement ──────────────────

    def build_snapshot_pack(self) -> Dict[str, Any]:
        """Build immutable snapshot pack for kernel consumption."""
        state_copy = copy.deepcopy(self.snapshot)
        pack = {
            "snapshot": state_copy,
            "inventory3d": getattr(self.inventory, 'get_all_state', lambda: {})() if self.inventory else {},
            "combat3d": getattr(self.combat, 'get_all_state', lambda: {})() if self.combat else {},
            "dialogue3d": getattr(self.dialogue, 'get_all_state', lambda: {})() if self.dialogue else {},
        }
        if self.debug:
            pack = deep_freeze(pack)
        return pack

    def _run_kernel(self, domain: str, kernel_fn, intent: str, snapshot_pack: Dict, rng, tick: int):
        """
        Run a single MR kernel with strict contract enforcement.
        Returns (deltas, alerts).
        """
        result = kernel_fn(
            snapshot=snapshot_pack,
            intent=intent,
            rng=rng,
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

    def _apply_delta(self, delta: Dict[str, Any]):
        """Apply a kernel delta to the runtime snapshot."""
        domain = delta.get("domain", "")
        op = delta.get("op", "")
        path = delta.get("path", "")
        value = delta.get("value")

        # Navigate to parent
        parts = path.strip("/").split("/")
        target = self.snapshot
        for part in parts[:-1]:
            if isinstance(target, dict):
                target = target.setdefault(part, {})
            else:
                return  # Can't navigate further

        key = parts[-1] if parts else ""

        if op == "set":
            if isinstance(target, dict):
                target[key] = value
        elif op == "merge" and isinstance(target, dict) and isinstance(value, dict):
            target.setdefault(key, {})
            if isinstance(target[key], dict):
                target[key].update(value)
        elif op == "push":
            if isinstance(target, dict):
                target.setdefault(key, [])
                if isinstance(target[key], list):
                    target[key].append(value)
        elif op == "increment":
            if isinstance(target, dict) and isinstance(target.get(key), (int, float)):
                target[key] += value if isinstance(value, (int, float)) else 1
        elif op == "decrement":
            if isinstance(target, dict) and isinstance(target.get(key), (int, float)):
                target[key] -= value if isinstance(value, (int, float)) else 1

    # ── Snapshot export ──────────────────────────────────────────

    def get_snapshot(self) -> Dict[str, Any]:
        """Get current snapshot wrapped in protocol envelope."""
        snapshot = copy.deepcopy(self.snapshot)

        # Clear ephemeral events AFTER copy
        self.snapshot["events"] = []

        tick = snapshot["world"]["time"]

        # Include subsystem states
        if self.combat:
            try:
                snapshot["combat"] = self.combat.get_all_state()
            except AttributeError:
                snapshot["combat"] = {}

        if self.inventory:
            try:
                snapshot["inventory"] = self.inventory.get_all_state()
            except AttributeError:
                snapshot["inventory"] = {}

        if self.dialogue:
            try:
                snapshot["dialogue"] = self.dialogue.get_all_state()
            except AttributeError:
                snapshot["dialogue"] = {}

        return self.envelope.wrap_snapshot(snapshot, tick)

    # ── Shutdown ─────────────────────────────────────────────────

    def shutdown(self):
        """Signal simulation thread to stop and wait for it."""
        self.running = False
        if self.sim_thread.is_alive():
            self.sim_thread.join(timeout=3.0)
        print("[RUNTIME] Shutdown complete.")

