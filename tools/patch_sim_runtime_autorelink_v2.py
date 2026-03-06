#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from datetime import datetime
import os
import re
import sys
import tempfile


def _rewrite_function(src: str, fn_name: str, new_block: str) -> tuple[str, bool]:
    lines = src.splitlines(True)
    start = None
    for i, ln in enumerate(lines):
        if ln.startswith(f"def {fn_name}("):
            start = i
            break
    if start is None:
        return src, False

    end = len(lines)
    for j in range(start + 1, len(lines)):
        if lines[j].startswith("def ") or lines[j].startswith("class "):
            end = j
            break

    replaced = "".join(lines[:start]) + new_block + "".join(lines[end:])
    return replaced, True


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    target = repo_root / "godotsim" / "sim_runtime.py"
    if not target.exists():
        print(f"ERROR: target not found: {target}", file=sys.stderr)
        return 2

    original = target.read_text(encoding="utf-8")

    new_fn = r'''def _auto_relink_vault(runtime, config_path: str):
    """
    On boot, check for saved vault config and auto-relink if found.

    Method-discovery order:
      1) runtime / runtime.vault_manager / runtime.vault_client / runtime.vault callables
      2) http_handlers module route tables or helper callables for POST /vault/link
    """
    if not os.path.exists(config_path):
        print("[VAULT] No saved config — link vault manually via POST /vault/link")
        return

    try:
        with open(config_path, "r") as f:
            cfg = json.load(f)
    except Exception as e:
        print(f"[VAULT] Saved config unreadable — skipping auto-relink: {e}")
        return

    vault_root = cfg.get("vault_root", "") or ""
    manifest_path = cfg.get("manifest_path", "") or ""

    if not vault_root or not manifest_path:
        print("[VAULT] Saved config incomplete — skipping auto-relink")
        return

    if not os.path.isfile(manifest_path):
        print(f"[VAULT] Manifest not found: {manifest_path} — skipping")
        return

    try:
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
    except Exception as e:
        print(f"[VAULT] Manifest unreadable: {manifest_path} — skipping: {e}")
        return

    cfg_obj = {"vault_root": vault_root, "manifest_path": manifest_path, "manifest": manifest}

    import inspect
    import importlib

    def _sig(fn):
        try:
            return str(inspect.signature(fn))
        except Exception:
            return "(?)"

    def _count_scenes() -> int:
        # best-effort scene count across likely containers
        for obj in (runtime, getattr(runtime, "vault_manager", None), getattr(runtime, "scene_manager", None)):
            if obj is None:
                continue
            for attr in ("vault_scenes", "scenes", "scene_index", "index", "scene_cache"):
                d = getattr(obj, attr, None)
                if isinstance(d, dict) and d:
                    return len(d)
        return 0

    config_names = ("cfg", "config", "vault_cfg", "vault_config")
    root_names = ("vault_root", "root", "vault", "vault_dir", "vault_path", "vault_root_dir")
    manifest_names = ("manifest", "mfst", "manifest_dict", "manifest_json", "manifest_data")
    manifest_path_names = ("manifest_path", "manifest_file", "manifest_filename", "manifest_json_path", "manifest_fp")

    def _try_call(label: str, fn):
        # returns (ok: bool, err: str|None)
        tries = []

        try:
            sig = inspect.signature(fn)
            params = list(sig.parameters.values())
            pnames = set(sig.parameters.keys())
        except Exception:
            sig = None
            params = []
            pnames = set()

        # Prefer config kwargs if supported
        for k in config_names:
            if k in pnames:
                tries.append((f"kw:{k}", lambda k=k: fn(**{k: cfg_obj})))
                break

        # root+manifest kwargs (dict)
        if pnames:
            kw = {}
            for rk in root_names:
                if rk in pnames:
                    kw[rk] = vault_root
                    break
            for mk in manifest_names:
                if mk in pnames:
                    kw[mk] = manifest
                    break
            if kw:
                tries.append(("kw:root+manifest", lambda kw=kw: fn(**kw)))

            kw = {}
            for rk in root_names:
                if rk in pnames:
                    kw[rk] = vault_root
                    break
            for pk in manifest_path_names:
                if pk in pnames:
                    kw[pk] = manifest_path
                    break
            if kw:
                tries.append(("kw:root+manifest_path", lambda kw=kw: fn(**kw)))

        # Positional heuristics (only up to 3 args, no guessing beyond that)
        if sig is not None:
            pos = [p for p in params if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)]
            required = [p for p in pos if p.default is p.empty]

            if len(required) == 0:
                tries.append(("pos:0", lambda: fn()))
            elif len(required) == 1:
                n0 = (required[0].name or "").lower()
                if n0 in config_names:
                    tries.append(("pos:1(cfg)", lambda: fn(cfg_obj)))
                elif n0 in manifest_names:
                    tries.append(("pos:1(manifest)", lambda: fn(manifest)))
                else:
                    tries.append(("pos:1(root)", lambda: fn(vault_root)))
            elif len(required) == 2:
                tries.append(("pos:2(root,manifest)", lambda: fn(vault_root, manifest)))
                tries.append(("pos:2(root,manifest_path)", lambda: fn(vault_root, manifest_path)))
                tries.append(("pos:2(cfg,root)", lambda: fn(cfg_obj, vault_root)))
            elif len(required) == 3:
                # common shapes for helpers that take (runtime, root, manifest)
                tries.append(("pos:3(runtime,root,manifest)", lambda: fn(runtime, vault_root, manifest)))
                tries.append(("pos:3(runtime,root,manifest_path)", lambda: fn(runtime, vault_root, manifest_path)))
                tries.append(("pos:3(runtime,cfg,_)",
                              lambda: fn(runtime, cfg_obj, None)))
        else:
            # No signature info: try common shapes
            tries.append(("fallback(root,manifest)", lambda: fn(vault_root, manifest)))
            tries.append(("fallback(root,manifest_path)", lambda: fn(vault_root, manifest_path)))
            tries.append(("fallback(cfg)", lambda: fn(cfg_obj)))
            tries.append(("fallback(root)", lambda: fn(vault_root)))
            tries.append(("fallback()", lambda: fn()))

        last = None
        for mode, thunk in tries:
            try:
                thunk()
                return True, None
            except TypeError as e:
                last = f"{label}{_sig(fn)} via {mode}: {e}"
            except Exception as e:
                last = f"{label}{_sig(fn)} via {mode}: {e}"
        return False, last

    def _add_callable(cands, label: str, fn):
        if callable(fn):
            cands.append((label, fn))

    def _collect_from_obj(cands, obj, prefix: str):
        if obj is None:
            return
        # Prefer stable ordering: whitelist first, then name-scan
        whitelist = (
            "link_vault","vault_link","relink_vault","vault_relink",
            "attach_vault","connect_vault","link","relink","attach","connect",
        )
        for name in whitelist:
            fn = getattr(obj, name, None)
            _add_callable(cands, f"{prefix}.{name}", fn)

        # broader scan: anything with vault/link in the name
        for name in sorted(dir(obj)):
            ln = name.lower()
            if "vault" not in ln and "link" not in ln and "relink" not in ln and "attach" not in ln and "connect" not in ln:
                continue
            fn = getattr(obj, name, None)
            if callable(fn):
                _add_callable(cands, f"{prefix}.{name}", fn)

    def _collect_http_handlers(cands):
        try:
            hh = importlib.import_module("http_handlers")
        except Exception as e:
            return [f"import http_handlers failed: {e}"]

        notes = []
        # 1) Look for route tables that mention /vault/link
        for k, v in hh.__dict__.items():
            if not isinstance(v, dict):
                continue
            try:
                items = list(v.items())
            except Exception:
                continue
            for rk, rv in items:
                path_hit = False
                post_hit = False

                if isinstance(rk, str) and "/vault/link" in rk:
                    path_hit = True
                if isinstance(rk, tuple) and any(isinstance(x, str) and "/vault/link" in x for x in rk):
                    path_hit = True
                if isinstance(rk, tuple) and any(isinstance(x, str) and x.upper() == "POST" for x in rk):
                    post_hit = True
                if isinstance(rk, str) and "POST" in rk.upper():
                    post_hit = True

                if path_hit:
                    _add_callable(cands, f"http_handlers.{k}[{rk!r}]", rv)

        # 2) Also collect any helper-like callables with vault/link in the name
        for name in sorted(dir(hh)):
            ln = name.lower()
            if "vault" in ln and ("link" in ln or "relink" in ln or "attach" in ln or "connect" in ln):
                fn = getattr(hh, name, None)
                if callable(fn):
                    _add_callable(cands, f"http_handlers.{name}", fn)

        if not cands:
            notes.append("http_handlers loaded, but no vault-link callables discovered")
        return notes

    candidates = []
    _collect_from_obj(candidates, runtime, "runtime")
    _collect_from_obj(candidates, getattr(runtime, "vault_manager", None), "runtime.vault_manager")
    _collect_from_obj(candidates, getattr(runtime, "vault_client", None), "runtime.vault_client")
    _collect_from_obj(candidates, getattr(runtime, "vault", None), "runtime.vault")

    hh_notes = _collect_http_handlers(candidates)

    # Deduplicate while preserving order
    seen = set()
    uniq = []
    for label, fn in candidates:
        key = (label, id(fn))
        if key in seen:
            continue
        seen.add(key)
        uniq.append((label, fn))

    last_err = None
    for label, fn in uniq:
        ok, err = _try_call(label, fn)
        if ok:
            count = _count_scenes()
            print(f"[VAULT] Auto-relinked: {count} scenes from {vault_root} via {label}{_sig(fn)}")
            return
        last_err = err or last_err

    print("[VAULT] Cannot auto-relink — no compatible vault link method found.")
    if last_err:
        print(f"[VAULT] Last error: {last_err}")
    for n in hh_notes:
        print(f"[VAULT] Note: {n}")

    # Show a short hint list of what we *did* discover, for wiring
    shown = 0
    for label, fn in uniq:
        if shown >= 25:
            break
        print(f"[VAULT]  - candidate: {label}{_sig(fn)}")
        shown += 1
'''

    patched, ok = _rewrite_function(original, "_auto_relink_vault", new_fn)
    if not ok:
        print("ERROR: could not locate def _auto_relink_vault(...)", file=sys.stderr)
        return 3

    if "AUTO-RELINK-METHOD-DISCOVERY V2" in patched:
        print(f"OK: already patched: {target}")
        return 0

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = target.with_suffix(target.suffix + f".bak.{ts}")
    backup.write_text(original, encoding="utf-8")

    fd, tmp_path = tempfile.mkstemp(prefix=target.name + ".", suffix=".tmp", dir=str(target.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(patched)
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

