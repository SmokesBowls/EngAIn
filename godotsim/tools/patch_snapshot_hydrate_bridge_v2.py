#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from datetime import datetime
import os
import re
import sys
import tempfile


MARK_HTTP = "# [SCENE-LOAD-PERSIST-ACTIVE V2]"
MARK_SIM  = "# [SNAPSHOT-HYDRATE+BRIDGE V2]"


HELPERS = r'''
def _hydrate_snapshot_scene(envelope, runtime=None):
    """
    Ensure envelope.payload has:
      - scene_id
      - scene (scene doc)
    using runtime._active_scene_id/_active_scene_doc set by /scene/load.
    """
    if not isinstance(envelope, dict):
        return

    payload = envelope.get("payload")
    if not isinstance(payload, dict):
        # some engines return the payload as the top-level dict
        payload = envelope.setdefault("payload", {})

    # If already set, do nothing.
    if payload.get("scene_id") and isinstance(payload.get("scene"), dict):
        return

    if runtime is None:
        return

    sid = getattr(runtime, "_active_scene_id", None)
    sdoc = getattr(runtime, "_active_scene_doc", None)

    # As fallback, try vault_scenes lookup if we only have an id.
    if sid and not isinstance(sdoc, dict):
        vs = getattr(runtime, "vault_scenes", None)
        if isinstance(vs, dict) and sid in vs:
            sdoc = vs.get(sid)

    if sid and not payload.get("scene_id"):
        payload["scene_id"] = sid
    if isinstance(sdoc, dict) and not isinstance(payload.get("scene"), dict):
        payload["scene"] = sdoc


def _ensure_bridge_entities_in_snapshot(envelope, runtime=None):
    """
    Ensure envelope.payload has bridge_entities (list of Entity3D dicts).
    Also fills payload.entities and payload.spatial.entities maps (best-effort).
    """
    if not isinstance(envelope, dict):
        return

    payload = envelope.get("payload")
    if not isinstance(payload, dict):
        payload = envelope.setdefault("payload", {})

    scene = payload.get("scene")
    if not isinstance(scene, dict):
        return

    be = payload.get("bridge_entities")
    if isinstance(be, list) and be:
        return

    scene_id = payload.get("scene_id") or scene.get("scene_id") or scene.get("@id") or "unknown"

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
            _fill_maps(payload, cached)
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
    _fill_maps(payload, ents)

    if cache is not None:
        try:
            cache[scene_id] = ents
        except Exception:
            pass


def _fill_maps(payload: dict, ents: list):
    cur_ent = payload.get("entities")
    if not isinstance(cur_ent, dict) or not cur_ent:
        m = {}
        for e in ents:
            if not isinstance(e, dict):
                continue
            eid = e.get("entity_id") or e.get("id")
            if eid:
                m[str(eid)] = e
        if m:
            payload["entities"] = m

    spatial = payload.get("spatial")
    if not isinstance(spatial, dict):
        spatial = {}
        payload["spatial"] = spatial

    cur_sp = spatial.get("entities")
    if not isinstance(cur_sp, dict) or not cur_sp:
        m = {}
        for e in ents:
            if not isinstance(e, dict):
                continue
            eid = e.get("entity_id") or e.get("id")
            tr = e.get("transform") if isinstance(e.get("transform"), dict) else {}
            if eid:
                m[str(eid)] = tr
        if m:
            spatial["entities"] = m
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
    b = path.with_suffix(path.suffix + f".bak.{ts}")
    b.write_text(original, encoding="utf-8")
    return b


def _find_repo_root(start: Path) -> Path | None:
    for p in [start] + list(start.parents):
        if (p / "godotsim" / "sim_runtime.py").exists() and (p / "godotsim" / "http_handlers.py").exists():
            return p
    # last resort: known canonical path
    guess = Path("/home/burdens/burdens_of_a_forgotten_past/EngAIn")
    if (guess / "godotsim" / "sim_runtime.py").exists() and (guess / "godotsim" / "http_handlers.py").exists():
        return guess
    return None


def patch_http(http_path: Path) -> str:
    s = http_path.read_text(encoding="utf-8")
    if MARK_HTTP in s:
        return f"OK: already patched {http_path}"

    # Anchor inside _handle_scene_load: after scene_id is computed.
    anchor = r'^\s*scene_id\s*=\s*doc\.get\("@id"\)\s*or\s*doc\.get\("scene_id"\)\s*or\s*"unknown"\s*$'
    m = re.search(anchor, s, flags=re.M)
    if not m:
        return f"ERROR: could not find scene_id assignment anchor in {http_path}"

    indent = re.match(r"^(\s*)", m.group(0)).group(1)
    insert = (
        f"{indent}{MARK_HTTP}\n"
        f"{indent}try:\n"
        f"{indent}    # Persist active scene so /snapshot can hydrate reliably\n"
        f"{indent}    self.runtime._active_scene_id = scene_id\n"
        f"{indent}    self.runtime._active_scene_doc = doc\n"
        f"{indent}except Exception:\n"
        f"{indent}    pass\n"
    )
    s2 = s[:m.end()] + "\n" + insert + s[m.end():]
    _backup(http_path, s)
    _atomic_write(http_path, s2)
    return f"PATCHED: {http_path}"


def patch_sim(sim_path: Path) -> str:
    s = sim_path.read_text(encoding="utf-8")
    if MARK_SIM in s:
        return f"OK: already patched {sim_path}"

    # Insert helpers before _install_live_edit_shims if missing.
    if "def _hydrate_snapshot_scene(" not in s or "def _ensure_bridge_entities_in_snapshot(" not in s:
        m = re.search(r"^def _install_live_edit_shims\(", s, flags=re.M)
        if not m:
            return f"ERROR: could not locate def _install_live_edit_shims( in {sim_path}"
        s = s[:m.start()] + HELPERS.lstrip("\n") + "\n\n" + s[m.start():]

    # Patch the snapshot wrapper call site.
    # Find the apply line and replace with hydrate+ensure+apply.
    pat = r"^(?P<indent>\s*)_apply_live_overrides_to_snapshot\(data,\s*ov_copy\)\s*$"
    m2 = re.search(pat, s, flags=re.M)
    if not m2:
        return f"ERROR: could not find _apply_live_overrides_to_snapshot(data, ov_copy) call in {sim_path}"

    indent = m2.group("indent")
    repl = (
        f"{indent}{MARK_SIM}\n"
        f"{indent}_hydrate_snapshot_scene(data, runtime)\n"
        f"{indent}_ensure_bridge_entities_in_snapshot(data, runtime)\n"
        f"{indent}_apply_live_overrides_to_snapshot(data, ov_copy)"
    )
    s2 = s[:m2.start()] + repl + s[m2.end():]
    _backup(sim_path, sim_path.read_text(encoding="utf-8"))
    _atomic_write(sim_path, s2)
    return f"PATCHED: {sim_path}"


def main() -> int:
    here = Path(__file__).resolve()
    repo = _find_repo_root(here.parent)
    if repo is None:
        print("ERROR: could not find repo root containing godotsim/sim_runtime.py + godotsim/http_handlers.py", file=sys.stderr)
        return 2

    sim_path = repo / "godotsim" / "sim_runtime.py"
    http_path = repo / "godotsim" / "http_handlers.py"

    print(patch_http(http_path))
    print(patch_sim(sim_path))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

