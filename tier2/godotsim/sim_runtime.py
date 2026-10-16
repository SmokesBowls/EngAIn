#!/usr/bin/env python3
"""
sim_runtime.py — SLIM entrypoint for EngAIn Runtime.

This file does exactly three things:
    1. Instantiates EngAInRuntime
    2. Injects it into RuntimeHTTPHandler
    3. Starts the HTTP server

All engine logic lives in runtime_core.py.
All HTTP routing lives in http_handlers.py.
All scene logic lives in scene_manager.py.
All command routing lives in command_dispatcher.py.
All vault utilities live in vault_manager.py.
"""

import json
import os
import argparse
import threading
import time
import inspect
import sys
from http.server import ThreadingHTTPServer

from .runtime_core import EngAInRuntime
from .http_handlers import RuntimeHTTPHandler
from .environment_manager import EnvironmentManager

try:
    _ROOT_FOR_SCENE_ID = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _ROOT_FOR_SCENE_ID not in sys.path:
        sys.path.insert(0, _ROOT_FOR_SCENE_ID)
    from tier3.mettaext.scene_identity import canonical_scene_id, scene_id_aliases
except Exception:
    def canonical_scene_id(raw):
        return str(raw or "unknown")

    def scene_id_aliases(raw):
        v = str(raw or "unknown")
        return {v}

def _resolve_expected_root(manifest_path: str = None) -> str:
    if not manifest_path:
        return "/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn"
    mp = os.path.realpath(manifest_path)
    if not os.path.isfile(mp):
        print(f"[STOP] Missing manifest: {mp}")
        sys.exit(1)
    try:
        data = json.loads(open(mp, "r", encoding="utf-8").read())
    except Exception as e:
        print(f"[STOP] Invalid manifest JSON: {e}")
        sys.exit(1)
    root = (data.get("paths", {}) or {}).get("root")
    if not root:
        print("[STOP] Manifest missing required field: paths.root")
        sys.exit(1)
    return os.path.realpath(root)
    
def save_vault_config(config_path: str, vault_root: str, manifest_path: str, last_scene_id: str = None):
    """Save vault config so next boot auto-relinks without manual curl."""
    try:
        data = {
            "vault_root": vault_root,
            "manifest_path": manifest_path,
            "last_scene_id": canonical_scene_id(last_scene_id)
        }
        with open(config_path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"[VAULT] Config saved -> {config_path} (last_scene_id: {last_scene_id})")
    except Exception as e:
        print(f"[VAULT] Failed to save config: {e}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default=None, help="Path to engain_manifest.json")
    args = ap.parse_args()
    expected = _resolve_expected_root(args.manifest)
    here = os.path.realpath(os.getcwd())
    if not here.startswith(expected):
        print("[STOP] launch_engine started outside configured root")
        print(" HERE:   ", here)
        print(" EXPECT: ", expected)
        sys.exit(1)
    print("=" * 50)
    print("  EngAIn Runtime Server")
    print("=" * 50)

    runtime = EngAInRuntime()
    runtime.env_manager = EnvironmentManager(mcp_url="http://127.0.0.1:8000")
    RuntimeHTTPHandler.runtime = runtime

    _install_live_edit_shims(RuntimeHTTPHandler, runtime)

    # EngAInRuntime already owns its simulation loop.
    # Do not start a second drain/tick pump here.

    _config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".engain_config.json")

    ThreadingHTTPServer.allow_reuse_address = True
    ThreadingHTTPServer.daemon_threads = True
    server = ThreadingHTTPServer(("127.0.0.1", 8080), RuntimeHTTPHandler)  # prevent port zombie on fast restart

    # Stash config path on runtime so http_handlers can save on /vault/link
    runtime._config_path = _config_path

    print(f"\nServer running on http://localhost:8080 THIS IS THE SIM_RUNTIME 1025PM WED. MARCH 4TH(Multi-threaded) ")
    print("Press Ctrl+C to stop\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"\n[FATAL] {e}")
    finally:
        server.server_close()      # <-- releases port 8080 immediately
        runtime.shutdown()
        print("Port 8080 released. Goodbye!")




def _find_zeroarg_method(obj, preferred_names, fallback_contains=None):
    """Return (name, bound_method) where method takes 0 params (after binding), else (None, None)."""
    names = list(preferred_names)
    if fallback_contains:
        # add any matching names as fallback candidates (stable order)
        for n in dir(obj):
            if fallback_contains in n.lower() and n not in names:
                names.append(n)

    for name in names:
        fn = getattr(obj, name, None)
        if not callable(fn):
            continue
        try:
            sig = inspect.signature(fn)
            # bound method -> params is 0 for no-arg methods
            if len(sig.parameters) == 0:
                return name, fn
        except Exception:
            # If signature can't be inspected (C-impl), assume it's okay and try.
            return name, fn
    return None, None


def _apply_live_overrides_to_snapshot(snapshot_obj, overrides_by_scene):
    """Mutate snapshot_obj in-place, overlaying per-entity transform deltas."""
    if not isinstance(snapshot_obj, dict):
        return
    payload = snapshot_obj.get("payload", snapshot_obj)
    if not isinstance(payload, dict):
        return

    scene_id = payload.get("scene_id") or ""
    overrides = {}
    if isinstance(overrides_by_scene, dict):
        # merge global + scene-specific
        global_ov = overrides_by_scene.get("_global", {})
        scene_ov = overrides_by_scene.get(scene_id, {})
        if isinstance(global_ov, dict):
            overrides.update(global_ov)
        if isinstance(scene_ov, dict):
            overrides.update(scene_ov)

    if not overrides:
        return

    ents = payload.get("bridge_entities")
    if not isinstance(ents, list):
        return

    idx = {}
    for e in ents:
        if isinstance(e, dict) and e.get("entity_id"):
            idx[e["entity_id"]] = e

    for eid, patch in overrides.items():
        e = idx.get(eid)
        if not e or not isinstance(patch, dict):
            continue

        # patch can be {"transform": {...}} or directly {"position":{...},...}
        patch_tr = patch.get("transform") if "transform" in patch else patch
        if not isinstance(patch_tr, dict):
            continue

        tr = e.setdefault("transform", {})
        if not isinstance(tr, dict):
            tr = {}
            e["transform"] = tr

        # position/rotation/scale
        for k in ("position", "rotation", "scale"):
            if k in patch_tr and isinstance(patch_tr[k], dict):
                cur = tr.setdefault(k, {})
                if not isinstance(cur, dict):
                    cur = {}
                    tr[k] = cur
                cur.update(patch_tr[k])
                # some snapshots mirror position at top-level
                if k == "position" and isinstance(e.get("position"), dict):
                    e["position"].update(patch_tr[k])

        # optional color overlay
        if "color" in patch_tr and isinstance(patch_tr["color"], dict):
            col = e.setdefault("color", {})
            if isinstance(col, dict):
                col.update(patch_tr["color"])


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


def _hydrate_snapshot_scene(envelope, runtime=None):
    """
    Ensure envelope.payload scene identity tracks the active runtime scene.

    Governance rule:
      - active scene pointer owns /snapshot scene identity
      - do not keep stale scene_id/scene when runtime active pointer changed
    """
    if not isinstance(envelope, dict):
        return

    payload = envelope.get("payload")
    if not isinstance(payload, dict):
        # some engines return the payload as the top-level dict
        payload = envelope.setdefault("payload", {})

    if runtime is None:
        return

    sid = getattr(runtime, "_active_scene_id", None)
    sdoc = getattr(runtime, "_active_scene_doc", None)

    # As fallback, try vault_scenes lookup if we only have an id.
    if sid and not isinstance(sdoc, dict):
        vs = getattr(runtime, "vault_scenes", None)
        if isinstance(vs, dict) and sid in vs:
            sdoc = vs.get(sid)

    # Bind payload scene identity to active pointer.
    if sid:
        payload["scene_id"] = sid
    if isinstance(sdoc, dict):
        payload["scene"] = sdoc


_PLACEHOLDER_SCENE_IDS = {"", "unknown", "scene.unknown", "scene.000_unknown"}


def _bridge_owner_scene_id(scene_id, scene, active_scene_id):
    """
    Scene id allowed to own bridge entities in this snapshot, or None.

    Ownership needs a real scene id (not a placeholder such as the
    "scene.unknown" given to docs without an id) that is the runtime's active
    scene and is also the id declared by the scene doc the entities come from.
    """
    sid = str(scene_id or "").strip()
    if sid.lower() in _PLACEHOLDER_SCENE_IDS:
        return None
    if not active_scene_id or sid != active_scene_id:
        return None
    if (scene.get("scene_id") or scene.get("@id")) != sid:
        return None
    return sid


def _ensure_bridge_entities_in_snapshot(envelope, runtime=None):
    """
    Ensure envelope.payload has bridge_entities (list of Entity3D dicts).
    Also fills payload.entities and payload.spatial.entities maps (best-effort).

    Scene-ownership rule:
      - preserve existing non-empty bridge_entities ONLY when they belong to
        runtime._active_scene_id
      - otherwise rebuild from active scene doc
      - bridge_entities_scene_id is set only for an owner from
        _bridge_owner_scene_id, including scenes with zero entities, and is
        removed when there is no owner
    """
    if not isinstance(envelope, dict):
        return

    payload = envelope.get("payload")
    if not isinstance(payload, dict):
        payload = envelope.setdefault("payload", {})

    scene = payload.get("scene")
    if not isinstance(scene, dict):
        payload.pop("bridge_entities_scene_id", None)
        return

    scene_id = payload.get("scene_id") or scene.get("scene_id") or scene.get("@id") or "unknown"
    active_scene_id = getattr(runtime, "_active_scene_id", None) if runtime is not None else None
    owner = _bridge_owner_scene_id(scene_id, scene, active_scene_id)

    be = payload.get("bridge_entities")
    be_owner = payload.get("bridge_entities_scene_id")
    if not owner:
        payload.pop("bridge_entities_scene_id", None)

    # Preserve only when ownership matches active scene pointer.
    if isinstance(be, list) and be:
        if owner and be_owner == owner:
            _fill_maps(payload, be)
            return

    cache = None
    if runtime is not None:
        cache = getattr(runtime, "_bridge_entities_cache", None)
        if not isinstance(cache, dict):
            try:
                runtime._bridge_entities_cache = {}
                cache = runtime._bridge_entities_cache
            except Exception:
                cache = None

    if cache is not None and owner:
        cached = cache.get(owner)
        if isinstance(cached, list) and cached:
            payload["bridge_entities"] = cached
            payload["bridge_entities_scene_id"] = owner
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

    if not isinstance(ents, list):
        return

    # A resolved empty list is still an answer for this scene: mark ownership
    # so clients can tell "zero entities" apart from "not resolved".
    payload["bridge_entities"] = ents
    if owner:
        payload["bridge_entities_scene_id"] = owner
    _fill_maps(payload, ents)

    if cache is not None and owner and ents:
        try:
            cache[owner] = ents
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


def _install_live_edit_shims(handler_cls, runtime):
    """
    Install snapshot hydration/overlay only.

    This keeps /snapshot rich enough for render clients without hijacking
    HTTP routes that belong to http_handlers.py.
    """
    if not hasattr(runtime, "_live_overrides_lock"):
        runtime._live_overrides_lock = threading.Lock()
    if not hasattr(runtime, "_live_overrides"):
        runtime._live_overrides = {"_global": {}}

    snap_name, snap_fn = _find_zeroarg_method(
        runtime,
        preferred_names=("snapshot", "get_snapshot", "build_snapshot", "export_snapshot", "dump_snapshot"),
        fallback_contains="snapshot",
    )
    if snap_name and callable(snap_fn):
        orig_snap = snap_fn

        def _snap_wrapper():
            data = orig_snap()
            try:
                if isinstance(data, dict):
                    with runtime._live_overrides_lock:
                        ov = runtime._live_overrides
                        ov_copy = {k: dict(v) if isinstance(v, dict) else v for k, v in ov.items()}
                    _hydrate_snapshot_scene(data, runtime)
                    _ensure_bridge_entities_in_snapshot(data, runtime)
                    _apply_live_overrides_to_snapshot(data, ov_copy)
            except Exception as e:
                print("[LIVEEDIT][ERR] snapshot overlay failed:", e)
            return data

        setattr(runtime, snap_name, _snap_wrapper)
        print(f"[LIVEEDIT] Snapshot overlay installed: runtime.{snap_name}()")
    else:
        print("[LIVEEDIT][WARN] No snapshot method found to overlay (live edits may not render).")

if __name__ == "__main__":
    main()
