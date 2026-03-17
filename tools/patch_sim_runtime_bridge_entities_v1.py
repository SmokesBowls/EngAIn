#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from datetime import datetime
import os
import re
import sys
import tempfile


MARKER = "# [BRIDGE-ENTITIES-IN-SNAPSHOT V1]"


HELPER_BLOCK = r'''
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


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    target = repo_root / "godotsim" / "sim_runtime.py"
    if not target.exists():
        print(f"ERROR: target not found: {target}", file=sys.stderr)
        return 2

    s = target.read_text(encoding="utf-8")

    if MARKER in s:
        print(f"OK: already patched: {target}")
        return 0

    # Insert helper block before _install_live_edit_shims if possible.
    if "def _ensure_bridge_entities_in_snapshot(" not in s:
        m = re.search(r"^def _install_live_edit_shims\(", s, flags=re.M)
        if not m:
            print("ERROR: could not locate def _install_live_edit_shims(", file=sys.stderr)
            return 3
        insert_at = m.start()
        s = s[:insert_at] + HELPER_BLOCK.lstrip("\n") + "\n\n" + s[insert_at:]

    # Now patch the wrapper call site: ensure it runs before overrides.
    # Find: _apply_live_overrides_to_snapshot(data, ov_copy)
    m2 = re.search(r"^(?P<indent>\s*)_apply_live_overrides_to_snapshot\(data,\s*ov_copy\)\s*$", s, flags=re.M)
    if not m2:
        print("ERROR: could not find _apply_live_overrides_to_snapshot(data, ov_copy) call.", file=sys.stderr)
        return 4

    indent = m2.group("indent")
    inject = (
        f"{indent}{MARKER}\n"
        f"{indent}_ensure_bridge_entities_in_snapshot(data, runtime)\n"
        f"{indent}_apply_live_overrides_to_snapshot(data, ov_copy)"
    )
    s = s[:m2.start()] + inject + s[m2.end():]

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = target.with_suffix(target.suffix + f".bak.{ts}")
    backup.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")

    fd, tmp_path = tempfile.mkstemp(prefix=target.name + ".", suffix=".tmp", dir=str(target.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(s)
        os.replace(tmp_path, target)
    finally:
        try:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        except Exception:
            pass

    print(f"PATCHED: {target}")
    print(f"BACKUP : {backup}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
