"""
engain_bge_bridge.py - EngAIn <-> UPBGE Scene Graph Bridge
===========================================================
Thick creative client. Polls sim_runtime HTTP API, diffs the snapshot
against current BGE scene, spawns/updates/removes Blender objects.

Objects spawned here are REAL Blender objects. Press ESC to stop,
they persist in the .blend file for editing.

Architecture:
    sim_runtime.py :8080  -->  HTTP JSON  -->  this bridge  -->  BGE scene graph
"""

import json
import threading
import time

try:
    from bge import logic
    IN_BGE = True
except ImportError:
    IN_BGE = False
    print("[EngAIn Bridge] Not in BGE - dry run mode")

from urllib.request import urlopen, Request
from urllib.error import URLError


class EngAInBridge:
    """
    Manages connection between sim_runtime and UPBGE scene graph.

    Created once on first Logic Brick tick, stored on bge.logic.
    tick() called every logic frame. Polls at configurable interval.
    """

    def __init__(self, base_url="http://localhost:8080", poll_interval=0.5):
        self.base_url = base_url.rstrip("/")
        self.poll_interval = poll_interval
        self.last_poll = 0.0
        self.last_snapshot = None
        self.managed_objects = {}   # vault_id -> bge object name
        self.connected = False
        self.error_count = 0
        self.template_name = "EntityTemplate"

        # Async HTTP state
        self._pending_response = None
        self._fetch_thread = None

        # World sync interval (sync positions back to Python)
        self.sync_interval = 2.0
        self.last_sync = 0.0

        print(f"[EngAIn Bridge] Init -> {self.base_url}")
        print(f"[EngAIn Bridge] Poll: {self.poll_interval}s  Template: '{self.template_name}'")

    # =================================================================
    #  Main tick - called every BGE logic frame
    # =================================================================

    def tick(self):
        """Called every logic tick from engain_controller.py."""
        now = time.time()

        # Check if async fetch completed
        if self._pending_response is not None:
            snapshot = self._pending_response
            self._pending_response = None
            self._apply_snapshot(snapshot)

        # Time to poll?
        if now - self.last_poll >= self.poll_interval:
            self.last_poll = now
            self._start_async_poll()

        # Time to sync back?
        if now - self.last_sync >= self.sync_interval:
            self.last_sync = now
            self.sync_world_back()

    # =================================================================
    #  HTTP Communication (non-blocking via threads)
    # =================================================================

    def _start_async_poll(self):
        if self._fetch_thread and self._fetch_thread.is_alive():
            return
        self._fetch_thread = threading.Thread(target=self._fetch_snapshot, daemon=True)
        self._fetch_thread.start()

    def _fetch_snapshot(self):
        try:
            req = Request(f"{self.base_url}/snapshot", method="GET")
            req.add_header("Accept", "application/json")
            with urlopen(req, timeout=2) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                self._pending_response = data
                if not self.connected:
                    self.connected = True
                    self.error_count = 0
                    print("[EngAIn Bridge] Connected to sim_runtime!")
        except URLError as e:
            self.error_count += 1
            if self.error_count <= 3 or self.error_count % 30 == 0:
                print(f"[EngAIn Bridge] Connection failed ({self.error_count}x): {e.reason}")
            self.connected = False
        except Exception as e:
            self.error_count += 1
            if self.error_count <= 3:
                print(f"[EngAIn Bridge] Fetch error: {e}")

    def send_command(self, command_dict):
        """POST /command to sim_runtime (fire-and-forget)."""
        def _post():
            try:
                payload = json.dumps(command_dict).encode("utf-8")
                req = Request(f"{self.base_url}/command", data=payload, method="POST")
                req.add_header("Content-Type", "application/json")
                with urlopen(req, timeout=2) as resp:
                    result = json.loads(resp.read().decode("utf-8"))
                    print(f"[EngAIn CMD] {command_dict.get('command', '?')} -> {result.get('status', result.get('type', '?'))}")
            except Exception as e:
                print(f"[EngAIn CMD] Failed: {e}")
        threading.Thread(target=_post, daemon=True).start()

    def sync_world_back(self):
        """POST /world/sync - push BGE positions back to sim_runtime."""
        if not IN_BGE or not self.managed_objects:
            return

        scene = logic.getCurrentScene()
        entities = {}
        for vault_id, obj_name in self.managed_objects.items():
            if obj_name in scene.objects:
                obj = scene.objects[obj_name]
                pos = obj.worldPosition
                entities[vault_id] = {
                    "position": {"x": round(pos.x, 3), "y": round(pos.y, 3), "z": round(pos.z, 3)},
                    "visible": obj.visible,
                }

        if entities:
            def _sync():
                try:
                    payload = json.dumps({"entities": entities}).encode("utf-8")
                    req = Request(f"{self.base_url}/world/sync", data=payload, method="POST")
                    req.add_header("Content-Type", "application/json")
                    urlopen(req, timeout=2)
                except Exception:
                    pass  # silent fail for sync
            threading.Thread(target=_sync, daemon=True).start()

    def load_scene(self, scene_id):
        """POST /scene/load to switch scenes."""
        def _load():
            try:
                payload = json.dumps({"scene_id": scene_id}).encode("utf-8")
                req = Request(f"{self.base_url}/scene/load", data=payload, method="POST")
                req.add_header("Content-Type", "application/json")
                with urlopen(req, timeout=5) as resp:
                    result = json.loads(resp.read().decode("utf-8"))
                    print(f"[EngAIn SCENE] Loaded: {result.get('scene_id', '?')} -> {result.get('status', '?')}")
            except Exception as e:
                print(f"[EngAIn SCENE] Load failed: {e}")
        threading.Thread(target=_load, daemon=True).start()

    # =================================================================
    #  Snapshot -> Scene Graph
    # =================================================================

    def _apply_snapshot(self, snapshot):
        """Diff snapshot against BGE scene. Spawn/update/remove."""
        if not IN_BGE:
            ents = snapshot.get("entities", {})
            print(f"[EngAIn Bridge] Dry run: {len(ents)} entities")
            return

        self.last_snapshot = snapshot
        scene = logic.getCurrentScene()
        entities = snapshot.get("entities", {})
        seen_ids = set()

        for entity_id, entity_data in entities.items():
            seen_ids.add(entity_id)
            if entity_id in self.managed_objects:
                self._update_object(scene, entity_id, entity_data)
            else:
                self._spawn_object(scene, entity_id, entity_data)

        # Remove dead entities
        dead_ids = set(self.managed_objects.keys()) - seen_ids
        for dead_id in dead_ids:
            self._remove_object(scene, dead_id)

    def _spawn_object(self, scene, entity_id, entity_data):
        """Spawn a new BGE object from EntityTemplate."""
        try:
            # Reference point for spawning
            if "EngAInController" in scene.objects:
                reference = scene.objects["EngAInController"]
            elif "spawnpoint" in scene.objects:
                reference = scene.objects["spawnpoint"]
            else:
                reference = list(scene.objects)[0]

            # Spawn (time=0 = persist forever)
            obj = scene.addObject(self.template_name, reference, 0)

            # Position
            pos = entity_data.get("position", {})
            if isinstance(pos, dict):
                obj.worldPosition.x = float(pos.get("x", 0))
                obj.worldPosition.y = float(pos.get("y", 0))
                obj.worldPosition.z = float(pos.get("z", 0))
            elif isinstance(pos, (list, tuple)) and len(pos) >= 3:
                obj.worldPosition = [float(pos[0]), float(pos[1]), float(pos[2])]

            # Metadata as custom properties
            obj["vault_id"] = entity_id
            obj["entity_type"] = entity_data.get("type", "unknown")
            obj["entity_name"] = entity_data.get("name", entity_id)

            # Color by type
            etype = entity_data.get("type", "").lower()
            colors = {
                "player":  [0.2, 0.6, 1.0, 1.0],
                "npc":     [0.2, 0.8, 0.2, 1.0],
                "hostile": [0.9, 0.1, 0.1, 1.0],
                "item":    [1.0, 0.8, 0.0, 1.0],
            }
            obj.color = colors.get(etype, [0.7, 0.7, 0.7, 1.0])
            obj.visible = True

            # Scale items smaller
            if etype == "item":
                obj.localScale = [0.5, 0.5, 0.5]

            self.managed_objects[entity_id] = obj.name
            print(f"[EngAIn SPAWN] {entity_id} ({etype}) -> {obj.name}")

        except Exception as e:
            print(f"[EngAIn SPAWN] FAILED '{entity_id}': {e}")
            if "did not match" in str(e):
                print(f"  FIX: '{self.template_name}' must be in main Scene Collection")
                print(f"       Move it back from any excluded/hidden collection")

    def _update_object(self, scene, entity_id, entity_data):
        """Update existing BGE object position and properties."""
        obj_name = self.managed_objects.get(entity_id)
        if not obj_name or obj_name not in scene.objects:
            del self.managed_objects[entity_id]
            self._spawn_object(scene, entity_id, entity_data)
            return

        obj = scene.objects[obj_name]
        pos = entity_data.get("position", {})
        if isinstance(pos, dict):
            obj.worldPosition.x = float(pos.get("x", obj.worldPosition.x))
            obj.worldPosition.y = float(pos.get("y", obj.worldPosition.y))
            obj.worldPosition.z = float(pos.get("z", obj.worldPosition.z))

        # Sync gameplay properties
        for key in ("health", "mood", "intent", "state"):
            val = entity_data.get(key)
            if val is not None:
                obj[key] = str(val) if isinstance(val, dict) else val

    def _remove_object(self, scene, entity_id):
        """Remove BGE object no longer in snapshot."""
        obj_name = self.managed_objects.pop(entity_id, None)
        if obj_name and obj_name in scene.objects:
            scene.objects[obj_name].endObject()
            print(f"[EngAIn REMOVE] {entity_id}")

    # =================================================================
    #  Debug
    # =================================================================

    def get_status(self):
        return {
            "connected": self.connected,
            "managed": len(self.managed_objects),
            "errors": self.error_count,
            "objects": list(self.managed_objects.keys()),
        }

    def debug_print(self):
        s = self.get_status()
        print(f"\n=== EngAIn Bridge ===")
        print(f"  Connected: {s['connected']}")
        print(f"  Managed:   {s['managed']} objects")
        print(f"  Errors:    {s['errors']}")
        if s['objects']:
            for oid in s['objects']:
                print(f"    - {oid} -> {self.managed_objects[oid]}")
        print(f"=====================\n")
