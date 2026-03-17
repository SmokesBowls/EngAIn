# engain_upbge_bridge.py
from __future__ import annotations

import os
import sys
import time
from collections import OrderedDict
from typing import Any, Dict, Optional, Tuple, List

import bge
from bge import events

from engain_http_client import EngAInHttpClient


def _blend_dir() -> str:
    return bge.logic.expandPath("//")


def _ensure_local_imports() -> str:
    d = _blend_dir()
    if d and d not in sys.path:
        sys.path.insert(0, d)
    return d


def _now_ms() -> int:
    return int(time.time() * 1000)


def _key_input_obj(keycode: int):
    kb = bge.logic.keyboard
    if hasattr(kb, "inputs"):
        try:
            inputs = kb.inputs
            if hasattr(inputs, "get"):
                return inputs.get(keycode)
            return inputs[keycode]
        except Exception:
            return None
    return None


def _key_down(keycode: int) -> bool:
    inp = _key_input_obj(keycode)
    if inp is None:
        try:
            return bge.logic.keyboard.events[keycode] in (bge.logic.KX_INPUT_ACTIVE, bge.logic.KX_INPUT_JUST_ACTIVATED)
        except Exception:
            return False

    if hasattr(inp, "active"):
        return bool(getattr(inp, "active"))
    if hasattr(inp, "activated"):
        return bool(getattr(inp, "activated"))
    if hasattr(inp, "status"):
        return getattr(inp, "status") in (bge.logic.KX_INPUT_ACTIVE, bge.logic.KX_INPUT_JUST_ACTIVATED)
    return False


def _key_just_pressed(keycode: int) -> bool:
    inp = _key_input_obj(keycode)
    if inp is None:
        try:
            return bge.logic.keyboard.events[keycode] == bge.logic.KX_INPUT_JUST_ACTIVATED
        except Exception:
            return False

    if hasattr(inp, "justActivated"):
        return bool(getattr(inp, "justActivated"))
    if hasattr(inp, "status"):
        return getattr(inp, "status") == bge.logic.KX_INPUT_JUST_ACTIVATED
    return False


_KEY_MAP = {
    "W": events.WKEY,
    "A": events.AKEY,
    "S": events.SKEY,
    "D": events.DKEY,
    "Q": events.QKEY,
    "E": events.EKEY,
    "SPACE": events.SPACEKEY,
    "SHIFT": events.LEFTSHIFTKEY,
    "CTRL": events.LEFTCTRLKEY,
    "ALT": events.LEFTALTKEY,
    "UP": events.UPARROWKEY,
    "DOWN": events.DOWNARROWKEY,
    "LEFT": events.LEFTARROWKEY,
    "RIGHT": events.RIGHTARROWKEY,
}


def _parse_key_list(spec: str) -> List[Tuple[str, int]]:
    out: List[Tuple[str, int]] = []
    spec = (spec or "").strip()
    if not spec:
        spec = "W,A,S,D,SPACE"
    for raw in spec.split(","):
        name = raw.strip().upper()
        if not name:
            continue
        code = _KEY_MAP.get(name)
        if code is None:
            continue
        out.append((name, code))
    seen = set()
    uniq: List[Tuple[str, int]] = []
    for n, c in out:
        if n in seen:
            continue
        seen.add(n)
        uniq.append((n, c))
    return uniq


def _safe_get(d: Dict[str, Any], path: str, default=None):
    cur: Any = d
    for part in path.split("."):
        if not isinstance(cur, dict):
            return default
        cur = cur.get(part)
        if cur is None:
            return default
    return cur


def _clamp01(x: float) -> float:
    try:
        v = float(x)
    except Exception:
        return 1.0
    if v < 0.0:
        return 0.0
    if v > 1.0:
        return 1.0
    return v


class EngAInBridge(bge.types.KX_PythonComponent):
    args = OrderedDict([
        ("base_url", "http://127.0.0.1:8080"),

        ("health_path", "/health"),
        ("snapshot_path", "/snapshot"),
        ("scene_load_path", "/scene/load"),
        ("command_path", "/command"),

        ("timeout_s", 0.25),
        ("health_poll_interval_s", 1.0),
        ("status_text_object", "ENGAIN_STATUS_TEXT"),
        ("verbose_log", False),

        ("default_scene_id", "scene.04_the_convergence"),

        ("spawn_enabled", True),
        ("spawn_poll_interval_s", 0.5),
        ("template_box", "EntityTemplate"),
        ("template_capsule", "EntityTemplateCapsule"),

        ("input_send_enabled", False),
        ("input_send_interval_s", 0.10),
        ("input_keys", "W,A,S,D,SPACE,SHIFT,CTRL,E,Q"),
        ("input_command_prefix", "input"),
        ("default_command", "look"),
    ])

    def start(self, args: Dict[str, Any]) -> None:
        self._blend_dir = _ensure_local_imports()
        self._cwd = os.getcwd()

        self.base_url = str(args.get("base_url") or "http://127.0.0.1:8080").strip().rstrip("/")

        self.health_path = str(args.get("health_path") or "/health").strip()
        self.snapshot_path = str(args.get("snapshot_path") or "/snapshot").strip()
        self.scene_load_path = str(args.get("scene_load_path") or "/scene/load").strip()
        self.command_path = str(args.get("command_path") or "/command").strip()

        self.timeout_s = float(args.get("timeout_s") or 0.25)
        self.health_poll_interval_s = max(0.1, float(args.get("health_poll_interval_s") or 1.0))
        self.spawn_poll_interval_s = max(0.1, float(args.get("spawn_poll_interval_s") or 0.5))

        self.status_text_object = str(args.get("status_text_object") or "ENGAIN_STATUS_TEXT").strip()
        self.verbose_log = bool(args.get("verbose_log") or False)

        self.default_scene_id = str(args.get("default_scene_id") or "scene.04_the_convergence").strip()

        self.spawn_enabled = bool(args.get("spawn_enabled") if args.get("spawn_enabled") is not None else True)
        self.template_box = str(args.get("template_box") or "EntityTemplate").strip()
        self.template_capsule = str(args.get("template_capsule") or "EntityTemplateCapsule").strip()

        self.input_send_enabled = bool(args.get("input_send_enabled") or False)
        self.input_send_interval_s = max(0.05, float(args.get("input_send_interval_s") or 0.10))
        self.input_keys_spec = str(args.get("input_keys") or "W,A,S,D,SPACE,SHIFT,CTRL,E,Q")
        self.input_command_prefix = str(args.get("input_command_prefix") or "input").strip() or "input"
        self.default_command = str(args.get("default_command") or "look").strip() or "look"

        self._tracked_keys = _parse_key_list(self.input_keys_spec)
        self._last_down: Dict[str, bool] = {name: False for name, _ in self._tracked_keys}

        self.client = EngAInHttpClient(base_url=self.base_url, timeout_s=self.timeout_s)

        self._next_health_poll_t = 0.0
        self._next_spawn_poll_t = 0.0
        self._next_input_send_t = 0.0

        # Separate log de-dupe for each stream
        self._last_health_key: Optional[Tuple[Any, ...]] = None
        self._last_snapshot_key: Optional[Tuple[Any, ...]] = None
        self._last_spawn_key: Optional[Tuple[Any, ...]] = None
        self._last_cmd_key: Optional[Tuple[Any, ...]] = None

        self._spawned: Dict[str, bge.types.KX_GameObject] = {}
        self._spawn_failure_hard = False

        self._poll_health(force=True)

    def update(self) -> None:
        self._poll_health(force=False)

        if _key_just_pressed(events.F5KEY):
            self._send_command(self.default_command)

        if _key_just_pressed(events.F7KEY):
            self._load_scene(self.default_scene_id)

        if self.spawn_enabled and not self._spawn_failure_hard:
            self._poll_snapshot_and_spawn()

        if self.input_send_enabled:
            self._maybe_send_inputs()

    def dispose(self) -> None:
        return

    # -------------------------
    # Phase 1: health
    # -------------------------
    def _poll_health(self, force: bool) -> None:
        t = time.perf_counter()
        if not force and t < self._next_health_poll_t:
            return
        self._next_health_poll_t = t + self.health_poll_interval_s

        resp = self.client.get_json(self.health_path)

        if resp.ok and resp.data:
            ok_flag = bool(resp.data.get("ok", True))
            svc = str(resp.data.get("service", "engain"))
            pid = resp.data.get("pid", None)
            display = f"{svc} {'OK' if ok_flag else 'NOT_OK'}"
            if pid is not None:
                display += f" pid={pid}"
            display += f" {resp.elapsed_ms}ms"

            key = ("health", True, svc, ok_flag, pid)
            self._log_once(stream="health", key=key, ok=True, msg=display)
            self._set_text(ok=True, display_msg=display)
            return

        detail = resp.error or f"status={resp.status}"
        if resp.data and isinstance(resp.data, dict) and resp.data.get("raw"):
            detail = f"{detail} | {resp.data.get('raw')}"
        display = f"engain OFFLINE ({detail})"
        key = ("health", False, detail)
        self._log_once(stream="health", key=key, ok=False, msg=display)
        self._set_text(ok=False, display_msg=display)

    # -------------------------
    # Phase 2: command + scene/load
    # -------------------------
    def _post_json(self, path: str, payload: Dict[str, Any]):
        return self.client.post_json(path, payload)

    def _send_command(self, command: str, extra: Optional[Dict[str, Any]] = None) -> None:
        payload: Dict[str, Any] = {
            "command": command,
            "source": "upbge",
            "ts_ms": _now_ms(),
            "blend_dir": self._blend_dir,
            "cwd": self._cwd,
            "object": getattr(self.object, "name", "UNKNOWN"),
        }
        if extra:
            payload.update(extra)

        resp = self._post_json(self.command_path, payload)
        if resp.ok:
            display = f"/command {command} -> ok ({resp.elapsed_ms}ms)"
            print(f"[ENGAIN] {display}")
            if self.verbose_log and resp.data:
                print("[ENGAIN][CMD]", resp.data)
            self._set_text(ok=True, display_msg=display)
            return

        display = f"/command {command} failed ({resp.status}) ({resp.error})"
        print(f"[ENGAIN][ERR] {display}")
        self._set_text(ok=False, display_msg=display)

    def _load_scene(self, scene_id: str) -> None:
        payload = {"scene_id": scene_id}
        resp = self._post_json(self.scene_load_path, payload)
        if resp.ok:
            display = f"/scene/load {scene_id} -> ok ({resp.elapsed_ms}ms)"
            print(f"[ENGAIN] {display}")
            self._set_text(ok=True, display_msg=display)
            return

        display = f"/scene/load {scene_id} failed ({resp.status}) ({resp.error})"
        print(f"[ENGAIN][ERR] {display}")
        self._set_text(ok=False, display_msg=display)

    # -------------------------
    # Phase 3: snapshot-driven spawning
    # -------------------------
    def _inactive_template(self, name: str):
        scene = bge.logic.getCurrentScene()
        inactive = getattr(scene, "objectsInactive", None)
        if inactive is None:
            return None
        try:
            return inactive[name]
        except Exception:
            return None

    def _spawn_from_template(self, template_obj, at_obj) -> Optional[bge.types.KX_GameObject]:
        scene = bge.logic.getCurrentScene()
        try:
            return scene.addObject(template_obj, at_obj, 0)
        except Exception:
            try:
                return scene.addObject(getattr(template_obj, "name", str(template_obj)), at_obj, 0)
            except Exception:
                return None

    def _poll_snapshot_and_spawn(self) -> None:
        t = time.perf_counter()
        if t < self._next_spawn_poll_t:
            return
        self._next_spawn_poll_t = t + self.spawn_poll_interval_s

        resp = self.client.get_json(self.snapshot_path)
        if not resp.ok or not resp.data:
            detail = resp.error or f"status={resp.status}"
            key = ("snapshot", "fail", detail)
            self._log_once(stream="snapshot", key=key, ok=False, msg=f"/snapshot failed ({detail})")
            return

        root = resp.data
        payload = root.get("payload", root) if isinstance(root, dict) else {}
        bridge_entities = payload.get("bridge_entities", []) if isinstance(payload, dict) else []

        if not isinstance(bridge_entities, list):
            key = ("snapshot", "bad")
            self._log_once(stream="snapshot", key=key, ok=False, msg="/snapshot invalid bridge_entities")
            return

        if not bridge_entities:
            key = ("snapshot", "empty")
            self._log_once(stream="snapshot", key=key, ok=True, msg="snapshot ok (0 entities)")
            return

        t_box = self._inactive_template(self.template_box)
        t_cap = self._inactive_template(self.template_capsule) or t_box

        if t_box is None:
            self._spawn_failure_hard = True
            msg = (
                f"Template '{self.template_box}' not found in scene.objectsInactive. "
                "Create an object named EntityTemplate and move it to an INACTIVE layer/collection."
            )
            print(f"[ENGAIN][ERR] {msg}")
            return

        seen: Dict[str, bool] = {}

        for ent in bridge_entities:
            if not isinstance(ent, dict):
                continue

            eid = str(ent.get("entity_id") or ent.get("name") or "").strip()
            if not eid:
                continue
            seen[eid] = True

            placeholder_mesh = str(ent.get("placeholder_mesh") or "").strip().lower()
            template = t_cap if placeholder_mesh == "capsule" else t_box

            # === UPBGE-POS v1 (prefer converted position) ===
            pos = _safe_get(ent, "position", None)
            if not isinstance(pos, dict):
                pos = _safe_get(ent, "transform_upbge.position", None)
            if not isinstance(pos, dict):
                pos = _safe_get(ent, "transform.position", {}) or {}
            # === END UPBGE-POS v1 ===

            # === UPBGE-SCL v1 (prefer converted scale) ===
            scl = _safe_get(ent, "transform_upbge.scale", None)
            if not isinstance(scl, dict):
                scl = _safe_get(ent, "transform.scale", {}) or {}
            # === END UPBGE-SCL v1 ===

            col = ent.get("color", {}) or {}

            x = float(pos.get("x", 0.0) or 0.0)
            y = float(pos.get("y", 0.0) or 0.0)
            z = float(pos.get("z", 0.0) or 0.0)

            sx = float(scl.get("x", 1.0) or 1.0)
            sy = float(scl.get("y", 1.0) or 1.0)
            sz = float(scl.get("z", 1.0) or 1.0)

            r = _clamp01(col.get("r", 1.0))
            g = _clamp01(col.get("g", 1.0))
            b = _clamp01(col.get("b", 1.0))

            obj = self._spawned.get(eid)
            if obj is None or getattr(obj, "invalid", False):
                obj = self._spawn_from_template(template, self.object)
                if obj is None:
                    print("[ENGAIN][ERR] spawn failed (addObject)")
                    continue
                self._spawned[eid] = obj
                try:
                    obj["entity_id"] = eid
                    if "inferred_type" in ent:
                        obj["entity_type"] = str(ent.get("inferred_type"))
                    if "name" in ent:
                        obj["entity_name"] = str(ent.get("name"))
                except Exception:
                    pass

            try:
                obj.worldPosition = [x, y, z]
            except Exception:
                pass
            try:
                obj.localScale = [sx, sy, sz]
            except Exception:
                pass
            try:
                obj.color = [r, g, b, 1.0]
            except Exception:
                pass

        for eid, obj in list(self._spawned.items()):
            if eid in seen:
                continue
            try:
                obj.endObject()
            except Exception:
                pass
            self._spawned.pop(eid, None)

        key = ("spawn", len(seen))
        self._log_once(stream="spawn", key=key, ok=True, msg=f"spawned {len(seen)} entities")

    # -------------------------
    # Optional: input push as /command
    # -------------------------
    def _maybe_send_inputs(self) -> None:
        t = time.perf_counter()
        if t < self._next_input_send_t:
            return
        self._next_input_send_t = t + self.input_send_interval_s

        downs: Dict[str, bool] = {}
        just_pressed: List[str] = []
        just_released: List[str] = []

        for name, code in self._tracked_keys:
            d = _key_down(code)
            downs[name] = d
            last = self._last_down.get(name, False)
            if d and not last:
                just_pressed.append(name)
            if (not d) and last:
                just_released.append(name)

        if not just_pressed and not just_released:
            return

        self._last_down = downs

        extra = {
            "type": "input",
            "keys_down": [k for k, v in downs.items() if v],
            "just_pressed": just_pressed,
            "just_released": just_released,
        }
        self._send_command(self.input_command_prefix, extra=extra)

    # -------------------------
    # Logging + text
    # -------------------------
    def _log_once(self, stream: str, key: Tuple[Any, ...], ok: bool, msg: str) -> None:
        if self.verbose_log:
            if ok:
                print(f"[ENGAIN] {msg}")
            else:
                print(f"[ENGAIN][ERR] {msg}")
            return

        last_key_attr = {
            "health": "_last_health_key",
            "snapshot": "_last_snapshot_key",
            "spawn": "_last_spawn_key",
        }.get(stream)

        if not last_key_attr:
            # default: always print
            if ok:
                print(f"[ENGAIN] {msg}")
            else:
                print(f"[ENGAIN][ERR] {msg}")
            return

        last = getattr(self, last_key_attr, None)
        if last == key:
            return
        setattr(self, last_key_attr, key)

        if ok:
            print(f"[ENGAIN] {msg}")
        else:
            print(f"[ENGAIN][ERR] {msg}")

    def _set_text(self, ok: bool, display_msg: str) -> None:
        scene = bge.logic.getCurrentScene()
        txt = scene.objects.get(self.status_text_object) if self.status_text_object else None
        if txt is not None and hasattr(txt, "text"):
            prefix = "[ENGAIN] " if ok else "[ENGAIN][ERR] "
            txt.text = prefix + display_msg
