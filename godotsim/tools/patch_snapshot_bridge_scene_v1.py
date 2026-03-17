#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from datetime import datetime
import os
import re
import sys
import tempfile


MARKER_SIM = "# [SNAPSHOT-HYDRATE+BRIDGE V1]"
MARKER_HTTP = "# [SCENE-LOAD-PERSIST-ACTIVE V1]"


HELPERS_BLOCK = r'''
def _hydrate_snapshot_scene(snapshot_obj, runtime=None):
    """
    Ensure snapshot payload has:
      - payload.scene_id
      - payload.scene (scene doc with segments)
    using runtime._active_scene_id/_active_scene_doc populated by /scene/load.
    """
    if not isinstance(snapshot_obj, dict):
        return

    payload = snapshot_obj.get("payload")
    if not isinstance(payload, dict):
        payload = snapshot_obj

    # if already has a real scene id, keep it
    if payload.get("scene_id"):
        return

    if runtime is None:
        return

    sid = getattr(runtime, "_active_scene_id", None)
    sdoc = getattr(runtime, "_active_scene_doc", None)

    # If doc missing but we have an id, try vault_scenes lookup
    if not isinstance(sdoc, dict) and sid:
        vs = getattr(runtime, "vault_scenes", None)
        if isinstance(vs, dict) and sid in vs:
            sdoc = vs.get(sid)

    if sid:
        payload["scene_id"] = sid
    if isinstance(sdoc, dict):
        payload["scene"] = sdoc


def _ensure_bridge_entities_in_snapshot(snapshot_obj, runtime=None):
    """
    Ensure snapshot payload contains:
      - payload.bridge_entities: list[dict] (Entity3D-like dicts)
      - payload.entities: dict keyed by entity_id (best-effort)
      - payload.spatial.entities: dict keyed by entity_id -> transform (best-effort)
    Cached per scene_id on runtime to avoid recompute each poll.
    """
    if not isinstance(snapshot_obj, dict):
        return

    payload = snapshot_obj.get("payload")
    if not isinstance(payload, dict):
        payload = snapshot_obj

    scene = payload.get("scene")
    if not isinstance(scene, dict):
        return

    # Already present?
    be = payload.get("bridge_entities")
    if isinstance(be, list) and be:
        return

    scene_id = payload.get("scene_id") or scene.get("scene_id") or scene.get("id") or "unknown"

    cache = None
    if runtime is not None:
        cache = getattr(runtime, "_bridge_entities_cache", None)
        if not isinstance(cache, dict):
            try:
                runtime._bridge_entities_cache = {}
                cache = runtime._bridge_entities_cache
            except Exception:
                cache = None

    if cache is not None:
        cached = cache.get(scene_id)
        if isinstance(cached, list) and cached:
            payload["bridge_entities"] = cached
            _fill_entity_maps_from_bridge_entities(payload, cached)
            return

    try:
        import os as _os
        import sys as _sys
        base = _os.path.dirname(_os.path.abspath(__file__))
        if base not in _sys.path:
            _sys.path.insert(0, base)
        from bridge_integration import bridge_entities_for_scene
        ents = bridge_entities_for_scene(scene, None)
    except Exception as e:
        if not getattr(_ensure_bridge_entities_in_snapshot, "_warned", False):
            print(f"[BRIDGE][WARN] snapshot inject failed: {e}")
            _ensure_bridge_entities_in_snapshot._warned = True
        return

    if not isinstance(ents, list) or not ents:
        return

    payload["bridge_entities"] = ents
    _fill_entity_maps_from_bridge_entities(payload, ents)

    if cache is not None:
        try:
            cache[scene_id] = ents
        except Exception:
            pass


def _fill_entity_maps_from_bridge_entities(payload: dict, ents: list):
    cur_entities = payload.get("entities")
    if not isinstance(cur_entities, dict) or not cur_entities:
        ent_map = {}
        for e in ents:
            if not isinstance(e, dict):
                continue
            eid = e.get("entity_id") or e.get("id")
            if eid:
                ent_map[str(eid)] = e
        if ent_map:
            payload["entities"] = ent_map

    spatial = payload.get("spatial")
    if not isinstance(spatial, dict):
        spatial = {}
        payload["spatial"] = spatial

    cur_spatial_entities = spatial.get("entities")
    if not isinstance(cur_spatial_entities, dict) or not cur_spatial_entities:
        sp_map = {}
        for e in ents:
            if not isinstance(e, dict):
                continue
            eid = e.get("entity_id") or e.get("id")
            tr = e.get("transform") if isinstance(e.get("transform"), dict) else {}
            if eid:
                sp_map[str(eid)] = tr
        if sp_map:
            spatial["entities"] = sp_map
'''


def _atomic_write(path: Path, content: str) -> None:
    fd, tmp_path = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp_path, path)
    finally:
        try:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        except Exception:
            pass


def _backup(path: Path, original: str) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = path.with_suffix(path.suffix + f".bak.{ts}")
    backup.write_text(original, encoding="utf-8")
    return backup


def patch_http_handlers(http_path: Path) -> tuple[bool, str]:
    s = http_path.read_text(encoding="utf-8")

    if MARKER_HTTP in s:
        return False, "OK: http_handlers already patched"

    # Anchor: scene load returns scene_id, then returns JSON
    # We will insert persistence right after scene_id assignment.
    m = re.search(r"^\s*scene_id\s*=\s*doc\.get\(\"@id\"\)\s*or\s*doc\.get\(\"scene_id\"\)\s*or\s*\"unknown\"\s*$",
                  s, flags=re.M)
    if not m:
        return False, "ERROR: could not find scene_id assignment anchor in http_handlers.py"

    indent = re.match(r"^(\s*)", m.group(0)).group(1)
    insert = (
        f"{indent}{MARKER_HTTP}\n"
        f"{indent}try:\n"
        f"{indent}    self.runtime._active_scene_id = scene_id\n"
        f"{indent}    self.runtime._active_scene_doc = doc\n"
        f"{indent}except Exception:\n"
        f"{indent}    pass\n"
    )

    s2 = s[:m.end()] + "\n" + insert + s[m.end():]
    _backup(http_path, s)
    _atomic_write(http_path, s2)
    return True, f"PATCHED: {http_path}"


def patch_sim_runtime(sim_path: Path) -> tuple[bool, str]:
    s = sim_path.read_text(encoding="utf-8")

    if MARKER_SIM in s and "def _ensure_bridge_entities_in_snapshot(" in s and "def _hydrate_snapshot_scene(" in s:
        return False, "OK: sim_runtime already patched"

    # Insert helper block before _install_live_edit_shims
    if "def _ensure_bridge_entities_in_snapshot(" not in s or "def _hydrate_snapshot_scene(" not in s:
        m = re.search(r"^def _install_live_edit_shims\(", s, flags=re.M)
        if not m:
            return False, "ERROR: could not locate def _install_live_edit_shims( in sim_runtime.py"
        s = s[:m.start()] + HELPERS_BLOCK.lstrip("\n") + "\n\n" + s[m.start():]

    # Patch call site in get_snapshot wrapper: find _apply_live_overrides_to_snapshot(data, ov_copy)
    m2 = re.search(r"^(?P<indent>\s*)_apply_live_overrides_to_snapshot\(data,\s*ov_copy\)\s*$", s, flags=re.M)
    if not m2:
        return False, "ERROR: could not find _apply_live_overrides_to_snapshot(data, ov_copy) call in sim_runtime.py"

    indent = m2.group("indent")
    inject = (
        f"{indent}{MARKER_SIM}\n"
        f"{indent}_hydrate_snapshot_scene(data, runtime)\n"
        f"{indent}_ensure_bridge_entities_in_snapshot(data, runtime)\n"
        f"{indent}_apply_live_overrides_to_snapshot(data, ov_copy)"
    )
    s = s[:m2.start()] + inject + s[m2.end():]

    _backup(sim_path, sim_path.read_text(encoding="utf-8"))
    _atomic_write(sim_path, s)
    return True, f"PATCHED: {sim_path}"


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    sim_path = repo_root / "godotsim" / "sim_runtime.py"
    http_path = repo_root / "godotsim" / "http_handlers.py"

    if not sim_path.exists():
        print(f"ERROR: missing {sim_path}", file=sys.stderr)
        return 2
    if not http_path.exists():
        print(f"ERROR: missing {http_path}", file=sys.stderr)
        return 3

    changed_http, msg_http = patch_http_handlers(http_path)
    print(msg_http)

    changed_sim, msg_sim = patch_sim_runtime(sim_path)
    print(msg_sim)

    if (not changed_http and msg_http.startswith("ERROR")) or (not changed_sim and msg_sim.startswith("ERROR")):
        return 4

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
