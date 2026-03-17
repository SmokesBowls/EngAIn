#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import sys


DEFAULT_TARGET = Path("/home/burdens/burdens_of_a_forgotten_past/EngAIn/godotsim/sim_runtime.py")


HELPER_BLOCK = r'''
def _ensure_bridge_entities_in_snapshot(snapshot_obj, runtime=None):
    """
    Ensure snapshot payload contains:
      - payload.bridge_entities: list[dict] (Entity3D-like dicts)
      - payload.entities: dict keyed by entity_id (best-effort)
      - payload.spatial.entities: dict keyed by entity_id -> transform (best-effort)

    This is intentionally defensive: if bridge_integration isn't available, we do nothing.
    We also cache per scene_id on the runtime to avoid recomputing every snapshot poll.
    """
    if not isinstance(snapshot_obj, dict):
        return

    payload = snapshot_obj.get("payload")
    if not isinstance(payload, dict):
        payload = snapshot_obj

    # If already present and non-empty, nothing to do.
    be = payload.get("bridge_entities")
    if isinstance(be, list) and be:
        return

    scene = payload.get("scene")
    if not isinstance(scene, dict):
        return

    scene_id = payload.get("scene_id") or scene.get("scene_id") or scene.get("id") or "unknown"

    cache = None
    if runtime is not None:
        cache = getattr(runtime, "_bridge_entities_cache", None)
        if not isinstance(cache, dict):
            cache = {}
            try:
                setattr(runtime, "_bridge_entities_cache", cache)
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

        from bridge_integration import bridge_entities_for_scene  # local file in godotsim/

        ents = bridge_entities_for_scene(scene, None)
    except Exception as e:
        # Warn only once to avoid log spam.
        if not getattr(_ensure_bridge_entities_in_snapshot, "_warned", False):
            print(f"[BRIDGE][WARN] Could not inject bridge_entities into snapshot: {e}")
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
    # payload.entities (only if empty/missing)
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

    # payload.spatial.entities (only if empty/missing)
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


def die(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(2)


def main() -> None:
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_TARGET
    if not target.exists():
        die(f"Target not found: {target}")

    s = target.read_text(encoding="utf-8")

    if "def _install_live_edit_shims" not in s:
        die("This does not look like the expected sim_runtime.py (missing _install_live_edit_shims).")

    changed = False

    # 1) Insert helper functions (idempotent)
    if "def _ensure_bridge_entities_in_snapshot(" not in s:
        m = re.search(r"^def _install_live_edit_shims\(", s, flags=re.M)
        if not m:
            die("Could not locate insertion point before _install_live_edit_shims().")
        insert_at = m.start()
        s = s[:insert_at] + HELPER_BLOCK.lstrip("\n") + "\n\n" + s[insert_at:]
        changed = True

    # 2) In the snapshot wrapper, ensure bridge_entities exists BEFORE applying overrides
    #    Replace:
    #      _apply_live_overrides_to_snapshot(data, ov_copy)
    #    With:
    #      _ensure_bridge_entities_in_snapshot(data, runtime)
    #      _apply_live_overrides_to_snapshot(data, ov_copy)
    if "_ensure_bridge_entities_in_snapshot(data, runtime)" not in s:
        pat = re.compile(
            r"^(?P<indent>\s*)_apply_live_overrides_to_snapshot\(data,\s*ov_copy\)\s*$",
            flags=re.M,
        )
        m = pat.search(s)
        if not m:
            die("Could not find _apply_live_overrides_to_snapshot(data, ov_copy) call to patch.")
        indent = m.group("indent")
        repl = (
            f"{indent}_ensure_bridge_entities_in_snapshot(data, runtime)\n"
            f"{indent}_apply_live_overrides_to_snapshot(data, ov_copy)"
        )
        s = s[: m.start()] + repl + s[m.end() :]
        changed = True

    if not changed:
        print(f"OK: already patched: {target}")
        return

    target.write_text(s, encoding="utf-8")
    print(f"PATCHED: {target}")


if __name__ == "__main__":
    main()
