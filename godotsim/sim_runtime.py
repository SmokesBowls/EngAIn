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
import threading
import time
import inspect
from http.server import ThreadingHTTPServer

from runtime_core import EngAInRuntime
from http_handlers import RuntimeHTTPHandler


def save_vault_config(config_path: str, vault_root: str, manifest_path: str):
    """Save vault config so next boot auto-relinks without manual curl."""
    try:
        data = {"vault_root": vault_root, "manifest_path": manifest_path}
        with open(config_path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"[VAULT] Config saved -> {config_path}")
    except Exception as e:
        print(f"[VAULT] Failed to save config: {e}")


def _auto_relink_vault(runtime, config_path: str):
    """
    Auto-relink vault on boot using the same pathway as POST /vault/link:

      runtime.vault_linker.link(manifest, vault_root)
      then populate runtime.vault_scenes from runtime.vault_linker.get_all_scenes()

    This avoids hardcoding runtime.link_vault(...) which your EngAInRuntime does not expose.
    """
    # [AUTO-RELINK-V3B vault_linker.link]
    if not os.path.exists(config_path):
        print("[VAULT] No saved config - link vault manually via POST /vault/link")
        return

    try:
        with open(config_path, "r") as f:
            cfg = json.load(f)
    except Exception as e:
        print(f"[VAULT] Saved config unreadable - skipping auto-relink: {e}")
        return

    vault_root = (cfg.get("vault_root") or "").strip()
    manifest_path = (cfg.get("manifest_path") or "").strip()

    if not vault_root:
        print("[VAULT] Saved config missing vault_root - skipping auto-relink")
        return

    if not os.path.isdir(vault_root):
        print(f"[VAULT] Vault root missing: {vault_root} - skipping")
        return

    # If manifest_path is missing/invalid, try vault_root/vault.manifest.json
    if not manifest_path or not os.path.isfile(manifest_path):
        candidate = os.path.join(vault_root, "vault.manifest.json")
        if os.path.isfile(candidate):
            manifest_path = candidate
        else:
            print(f"[VAULT] Manifest not found: {manifest_path or candidate} - skipping")
            return

    try:
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
    except Exception as e:
        print(f"[VAULT] Manifest unreadable: {manifest_path} - skipping: {e}")
        return

    vl = getattr(runtime, "vault_linker", None)
    link_fn = getattr(vl, "link", None) if vl is not None else None
    get_all_fn = getattr(vl, "get_all_scenes", None) if vl is not None else None

    if not callable(link_fn) or not callable(get_all_fn) or not hasattr(runtime, "vault_scenes"):
        print("[VAULT] Cannot auto-relink - runtime.vault_linker.link(...) not available")
        # Helpful hint list
        try:
            names = [n for n in dir(runtime) if "vault" in n.lower()]
            print("[VAULT] Runtime vault-related attrs (sample):", ", ".join(names[:30]))
        except Exception:
            pass
        return

    try:
        result = link_fn(manifest, vault_root)
    except Exception as e:
        print(f"[VAULT] Auto-relink via vault_linker.link failed: {e}")
        return

    if not isinstance(result, dict) or result.get("status") != "ok":
        if isinstance(result, dict):
            print(f"[VAULT] Auto-relink attempted via vault_linker.link but status={result.get('status')!r}")
        else:
            print("[VAULT] Auto-relink attempted via vault_linker.link but got non-dict result")
        return

    loaded = 0
    try:
        scenes = get_all_fn()
        if isinstance(scenes, dict):
            for sid, scene in scenes.items():
                runtime.vault_scenes[sid] = scene
                loaded += 1
    except Exception as e:
        print(f"[VAULT] Auto-relink succeeded but scene copy failed: {e}")
        return

    try:
        vault_id = (
            result.get("vault_id")
            or (manifest.get("vault_id") if isinstance(manifest, dict) else None)
            or (manifest.get("id") if isinstance(manifest, dict) else None)
            or os.path.basename(os.path.abspath(vault_root))
        )
        snapshot = getattr(runtime, "snapshot", None)
        if isinstance(snapshot, dict) and vault_id:
            vaults = snapshot.setdefault("vaults", {})
            if isinstance(vaults, dict):
                vaults[vault_id] = {
                    "vault_root": vault_root,
                    "manifest_path": manifest_path,
                }
            snapshot["active_vault_id"] = vault_id
    except Exception as e:
        print(f"[VAULT] Auto-relink state persistence warning: {e}")

    print(f"[VAULT] Auto-relinked: {loaded} scenes from {vault_root} via runtime.vault_linker.link(manifest, vault_root)")
def main():
    print("=" * 50)
    print("  EngAIn Runtime Server")
    print("=" * 50)

    runtime = EngAInRuntime()
    RuntimeHTTPHandler.runtime = runtime

    _install_live_edit_shims(RuntimeHTTPHandler, runtime)

    # EngAInRuntime already owns its simulation loop.
    # Do not start a second drain/tick pump here.

    # === VAULT AUTO-RELINK (persistent config survives restarts) ===
    _config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".engain_config.json")
    _auto_relink_vault(runtime, _config_path)

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
