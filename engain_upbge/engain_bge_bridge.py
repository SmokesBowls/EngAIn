"""
engain_bge_bridge.py - EngAIn <-> UPBGE Scene Graph Bridge
===========================================================
Polls sim_runtime HTTP API, diffs snapshot vs current BGE scene,
spawns/updates/removes objects.

Note:
- scene.addObject(..., time=0.0) means "exists forever during gameplay",
  not "saved into the .blend file". (Persistence requires a save/export step.)
"""

import json
import threading
import time
from queue import SimpleQueue, Empty
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

try:
    from bge import logic
    IN_BGE = True
except ImportError:
    IN_BGE = False
    print("[EngAIn Bridge] Not in BGE - dry run mode")


class EngAInBridge:
    def __init__(self, base_url: str = "http://localhost:8080", poll_interval: float = 0.5):
        self.base_url = base_url.rstrip("/")
        self.poll_interval = float(poll_interval)
        self.last_poll = 0.0

        self.last_snapshot = None
        self.managed_objects = {}  # entity_id -> bge object name
        self.connected = False
        self.error_count = 0

        self.template_name = "EntityTemplate"
        self.sync_interval = 2.0
        self.last_sync = 0.0

        self._fetch_thread = None
        self._snapshots = SimpleQueue()  # thread-safe handoff to main tick

        self._post_jobs = SimpleQueue()
        self._post_thread = threading.Thread(target=self._post_worker, daemon=True)
        self._post_thread.start()

        self._scene_name = None

        print(f"[EngAIn Bridge] Init -> {self.base_url}")
        print(f"[EngAIn Bridge] Poll: {self.poll_interval}s  Template: '{self.template_name}'")

    # ============================================================
    # Main tick (called every BGE logic frame)
    # ============================================================

    def tick(self):
        now = time.time()

        # Apply only the latest snapshot available (drop stale ones)
        latest = None
        while True:
            try:
                latest = self._snapshots.get_nowait()
            except Empty:
                break
        if latest is not None:
            self._apply_snapshot(latest)

        # Poll snapshot
        if now - self.last_poll >= self.poll_interval:
            self.last_poll = now
            self._start_async_poll()

        # Sync back
        if now - self.last_sync >= self.sync_interval:
            self.last_sync = now
            self.sync_world_back()

    # ============================================================
    # HTTP (snapshot polling in background thread)
    # ============================================================

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
                self._snapshots.put(data)

            if not self.connected:
                self.connected = True
                self.error_count = 0
                print("[EngAIn Bridge] Connected to sim_runtime!")

        except HTTPError as e:
            self.error_count += 1
            self.connected = False
            if e.code == 404:
                # Very common during integration: endpoint mismatch
                if self.error_count <= 3 or self.error_count % 30 == 0:
                    print(f"[EngAIn Bridge] /snapshot not found (HTTP 404). Your sim_runtime must expose GET /snapshot.")
            else:
                if self.error_count <= 3 or self.error_count % 30 == 0:
                    print(f"[EngAIn Bridge] HTTP error ({e.code}): {e.reason}")

        except URLError as e:
            self.error_count += 1
            self.connected = False
            if self.error_count <= 3 or self.error_count % 30 == 0:
                print(f"[EngAIn Bridge] Connection failed ({self.error_count}x): {getattr(e, 'reason', e)}")

        except Exception as e:
            self.error_count += 1
            self.connected = False
            if self.error_count <= 3 or self.error_count % 30 == 0:
                print(f"[EngAIn Bridge] Fetch error ({self.error_count}x): {e}")

    def _post_worker(self):
        while True:
            job = self._post_jobs.get()
            try:
                job()
            except Exception:
                pass

    def _enqueue_post_json(self, path: str, payload_obj: dict, timeout: float = 2.0, log_label: str | None = None):
        payload = json.dumps(payload_obj).encode("utf-8")

        def _job():
            req = Request(f"{self.base_url}{path}", data=payload, method="POST")
            req.add_header("Content-Type", "application/json")
            req.add_header("Accept", "application/json")
            with urlopen(req, timeout=timeout) as resp:
                if log_label:
                    try:
                        data = json.loads(resp.read().decode("utf-8"))
                        print(f"[{log_label}] -> {data.get('status', data.get('type', 'ok'))}")
                    except Exception:
                        print(f"[{log_label}] -> ok")

        self._post_jobs.put(_job)

    def send_command(self, command_dict: dict):
        cmd = command_dict.get("command", "?")
        self._enqueue_post_json("/command", command_dict, timeout=2.0, log_label=f"EngAIn CMD {cmd}")

    def sync_world_back(self):
        if not IN_BGE or not self.managed_objects:
            return

        scene = logic.getCurrentScene()
        entities = {}

        for entity_id, obj_name in self.managed_objects.items():
            if obj_name in scene.objects:
                obj = scene.objects[obj_name]
                pos = obj.worldPosition
                entities[entity_id] = {
                    "position": {"x": round(pos.x, 3), "y": round(pos.y, 3), "z": round(pos.z, 3)},
                    "visible": bool(getattr(obj, "visible", True)),
                }

        if entities:
            self._enqueue_post_json("/world/sync", {"entities": entities}, timeout=2.0, log_label=None)

    def load_scene(self, scene_id: str):
        # Keep your original endpoint; if you later decide to use a different one,
        # change it here without touching the rest of the bridge.
        self._enqueue_post_json("/scene/load", {"scene_id": scene_id}, timeout=5.0, log_label=f"EngAIn SCENE {scene_id}")

    # ============================================================
    # Snapshot -> Scene Graph
    # ============================================================

    def _apply_snapshot(self, snapshot: dict):
        if not IN_BGE:
            ents = snapshot.get("entities", {})
            print(f"[EngAIn Bridge] Dry run: {len(ents)} entities")
            return

        self.last_snapshot = snapshot
        scene = logic.getCurrentScene()

        # If scene changes, reset mapping (prevents “ghost map” bugs)
        if self._scene_name != scene.name:
            self._scene_name = scene.name
            self.managed_objects.clear()

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

    def _spawn_object(self, scene, entity_id: str, entity_data: dict):
        try:
            if "EngAInController" in scene.objects:
                reference = scene.objects["EngAInController"]
            elif "spawnpoint" in scene.objects:
                reference = scene.objects["spawnpoint"]
            elif getattr(scene, "active_camera", None) is not None:
                reference = scene.active_camera
            elif len(scene.objects) > 0:
                reference = scene.objects[0]
            else:
                raise RuntimeError("Scene has no objects. Add an EngAInController empty (recommended).")

            # time=0.0 -> lives forever during gameplay :contentReference[oaicite:4]{index=4}
            obj = scene.addObject(self.template_name, reference, 0.0)

            pos = entity_data.get("position", {})
            if isinstance(pos, dict):
                obj.worldPosition.x = float(pos.get("x", 0.0))
                obj.worldPosition.y = float(pos.get("y", 0.0))
                obj.worldPosition.z = float(pos.get("z", 0.0))
            elif isinstance(pos, (list, tuple)) and len(pos) >= 3:
                obj.worldPosition = [float(pos[0]), float(pos[1]), float(pos[2])]

            obj["vault_id"] = entity_id
            obj["entity_type"] = entity_data.get("type", "unknown")
            obj["entity_name"] = entity_data.get("name", entity_id)

            etype = str(entity_data.get("type", "")).lower()
            colors = {
                "player":  [0.2, 0.6, 1.0, 1.0],
                "npc":     [0.2, 0.8, 0.2, 1.0],
                "hostile": [0.9, 0.1, 0.1, 1.0],
                "item":    [1.0, 0.8, 0.0, 1.0],
            }
            try:
                obj.color = colors.get(etype, [0.7, 0.7, 0.7, 1.0])
            except Exception:
                pass

            try:
                obj.visible = True
            except Exception:
                pass

            if etype == "item":
                obj.localScale = [0.5, 0.5, 0.5]

            self.managed_objects[entity_id] = obj.name
            print(f"[EngAIn SPAWN] {entity_id} ({etype}) -> {obj.name}")

        except Exception as e:
            print(f"[EngAIn SPAWN] FAILED '{entity_id}': {e}")
            if "did not match" in str(e):
                print(f"  FIX: '{self.template_name}' must be in the main Scene Collection (not excluded/hidden).")

    def _update_object(self, scene, entity_id: str, entity_data: dict):
        obj_name = self.managed_objects.get(entity_id)
        if not obj_name or obj_name not in scene.objects:
            self.managed_objects.pop(entity_id, None)
            self._spawn_object(scene, entity_id, entity_data)
            return

        obj = scene.objects[obj_name]
        pos = entity_data.get("position", {})

        if isinstance(pos, dict):
            obj.worldPosition.x = float(pos.get("x", obj.worldPosition.x))
            obj.worldPosition.y = float(pos.get("y", obj.worldPosition.y))
            obj.worldPosition.z = float(pos.get("z", obj.worldPosition.z))
        elif isinstance(pos, (list, tuple)) and len(pos) >= 3:
            obj.worldPosition = [float(pos[0]), float(pos[1]), float(pos[2])]

        for key in ("health", "mood", "intent", "state"):
            val = entity_data.get(key)
            if val is not None:
                obj[key] = str(val) if isinstance(val, dict) else val

    def _remove_object(self, scene, entity_id: str):
        obj_name = self.managed_objects.pop(entity_id, None)
        if obj_name and obj_name in scene.objects:
            try:
                scene.objects[obj_name].endObject()
            except Exception:
                pass
            print(f"[EngAIn REMOVE] {entity_id}")

    # ============================================================
    # Debug
    # ============================================================

    def get_status(self):
        return {
            "connected": self.connected,
            "managed": len(self.managed_objects),
            "errors": self.error_count,
            "objects": list(self.managed_objects.keys()),
        }

    def debug_print(self):
        s = self.get_status()
        print("\n=== EngAIn Bridge ===")
        print(f"  Connected: {s['connected']}")
        print(f"  Managed:   {s['managed']} objects")
        print(f"  Errors:    {s['errors']}")
        if s["objects"]:
            for oid in s["objects"]:
                print(f"    - {oid} -> {self.managed_objects[oid]}")
        print("=====================\n")
