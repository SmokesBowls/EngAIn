#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from datetime import datetime
import os
import re
import sys
import tempfile


TARGET = Path("/home/burdens/burdens_of_a_forgotten_past/EngAIn/godotsim/sim_runtime.py")

OLD_COMMENT = "        # Call the same vault link method that /vault/link uses"
OLD_PRINT = '            print("[VAULT] Cannot auto-relink — no link_vault method found on runtime")'
MARKER = "# [AUTO-RELINK] method-discovery v1"


def _build_new_block() -> str:
    indent = "        "  # 8 spaces

    def L(txt: str) -> str:
        return f"{indent}{txt}"

    lines = [
        L(MARKER),
        L('cfg_obj = {"vault_root": vault_root, "manifest_path": manifest_path, "manifest": manifest}'),
        "",
        L("def _sig(fn):"),
        L("    try:"),
        L("        return str(inspect.signature(fn))"),
        L("    except Exception:"),
        L('        return "(?)"'),
        "",
        L("def _pick_arg(param_name: str):"),
        L('    pn = (param_name or "").lower()'),
        L('    if pn in ("cfg", "config", "vault_cfg", "vault_config"):'),
        L("        return cfg_obj"),
        L('    if pn in ("manifest_path", "manifest_file", "manifest_filename", "manifest_json_path", "manifest_fp"):'),
        L("        return manifest_path"),
        L('    if pn in ("manifest", "mfst", "manifest_dict", "manifest_json", "manifest_data"):'),
        L("        return manifest"),
        L('    if pn in ("vault_root", "root", "vault", "vault_dir", "vault_path", "vault_root_dir"):'),
        L("        return vault_root"),
        L("    return vault_root"),
        "",
        L("def _call_candidate(fn, label: str):"),
        L("    # Returns (ok: bool, err: str|None)"),
        L("    try:"),
        L("        sig = inspect.signature(fn)"),
        L("        params = list(sig.parameters.values())"),
        L("    except Exception:"),
        L("        sig = None"),
        L("        params = []"),
        "",
        L("    attempts = []"),
        L('    config_names = ("cfg", "config", "vault_cfg", "vault_config")'),
        L('    root_names = ("vault_root", "root", "vault", "vault_dir", "vault_path", "vault_root_dir")'),
        L('    manifest_names = ("manifest", "mfst", "manifest_dict", "manifest_json", "manifest_data")'),
        L('    manifest_path_names = ("manifest_path", "manifest_file", "manifest_filename", "manifest_json_path", "manifest_fp")'),
        "",
        L("    if sig is not None:"),
        L("        pnames = set(sig.parameters.keys())"),
        L("        # 1) config kw call"),
        L("        for k in config_names:"),
        L("            if k in pnames:"),
        L('                attempts.append(("kwargs:" + k, lambda k=k: fn(**{k: cfg_obj})))'),
        L("                break"),
        L("        # 2) root+manifest kw call (manifest as dict)"),
        L("        kwargs = {}"),
        L("        for k in root_names:"),
        L("            if k in pnames:"),
        L("                kwargs[k] = vault_root"),
        L("                break"),
        L("        for k in manifest_names:"),
        L("            if k in pnames:"),
        L("                kwargs[k] = manifest"),
        L("                break"),
        L("        if kwargs:"),
        L('            attempts.append(("kwargs:root+manifest", lambda kwargs=kwargs: fn(**kwargs)))'),
        L("        # 3) root+manifest_path kw call"),
        L("        kwargs = {}"),
        L("        for k in root_names:"),
        L("            if k in pnames:"),
        L("                kwargs[k] = vault_root"),
        L("                break"),
        L("        for k in manifest_path_names:"),
        L("            if k in pnames:"),
        L("                kwargs[k] = manifest_path"),
        L("                break"),
        L("        if kwargs:"),
        L('            attempts.append(("kwargs:root+manifest_path", lambda kwargs=kwargs: fn(**kwargs)))'),
        "",
        L("        # Positional heuristics (0..2 required positional params)"),
        L("        pk = [p for p in params if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)]"),
        L("        required = [p for p in pk if p.default is p.empty]"),
        L("        if len(required) == 0:"),
        L('            attempts.append(("pos:0", lambda: fn()))'),
        L("        elif len(required) == 1:"),
        L("            a0 = _pick_arg(required[0].name)"),
        L('            attempts.append(("pos:1:" + required[0].name, lambda a0=a0: fn(a0)))'),
        L("        elif len(required) == 2:"),
        L("            a0 = _pick_arg(required[0].name)"),
        L("            a1 = _pick_arg(required[1].name)"),
        L('            attempts.append(("pos:2:" + required[0].name + "," + required[1].name, lambda a0=a0, a1=a1: fn(a0, a1)))'),
        L("            if a1 is manifest and manifest_path:"),
        L('                attempts.append(("pos:2:" + required[0].name + "," + required[1].name + ":path", lambda a0=a0: fn(a0, manifest_path)))'),
        L("    else:"),
        L("        # No signature available; try the common shapes"),
        L('        attempts.append(("fallback:root+manifest", lambda: fn(vault_root, manifest)))'),
        L("        if manifest_path:"),
        L('            attempts.append(("fallback:root+manifest_path", lambda: fn(vault_root, manifest_path)))'),
        L('        attempts.append(("fallback:root", lambda: fn(vault_root)))'),
        "",
        L("    last_err = None"),
        L("    for mode, thunk in attempts:"),
        L("        try:"),
        L("            thunk()"),
        L("            return True, None"),
        L("        except TypeError as e:"),
        L('            last_err = f"{label}{_sig(fn)} via {mode}: {e}"'),
        L("        except Exception as e:"),
        L('            last_err = f"{label}{_sig(fn)} via {mode}: {e}"'),
        L("    return False, last_err"),
        "",
        L("def _add_candidates(obj, prefix: str, names, out, seen):"),
        L("    if obj is None:"),
        L("        return"),
        L("    for n in names:"),
        L("        try:"),
        L("            fn = getattr(obj, n, None)"),
        L("        except Exception:"),
        L("            fn = None"),
        L("        if not callable(fn):"),
        L("            continue"),
        L("        key = id(fn)"),
        L("        if key in seen:"),
        L("            continue"),
        L("        seen.add(key)"),
        L('        out.append((prefix + "." + n, fn))'),
        "",
        L("whitelist = ("),
        L('    "link_vault", "vault_link", "relink_vault", "vault_relink",'),
        L('    "attach_vault", "connect_vault", "attach", "connect",'),
        L('    "link", "relink",'),
        L(")"),
        L("candidates = []"),
        L("seen = set()"),
        L('_add_candidates(runtime, "runtime", whitelist, candidates, seen)'),
        L('vm = getattr(runtime, "vault_manager", None)'),
        L('_add_candidates(vm, "runtime.vault_manager", whitelist, candidates, seen)'),
        L('vc = getattr(runtime, "vault_client", None)'),
        L('_add_candidates(vc, "runtime.vault_client", whitelist, candidates, seen)'),
        L('v = getattr(runtime, "vault", None)'),
        L('_add_candidates(v, "runtime.vault", whitelist, candidates, seen)'),
        "",
        L("last_err = None"),
        L("for label, fn in candidates:"),
        L("    ok, err = _call_candidate(fn, label)"),
        L("    if ok:"),
        L("        count = 0"),
        L('        vs = getattr(runtime, "vault_scenes", None)'),
        L("        if isinstance(vs, dict):"),
        L("            count = len(vs)"),
        L("        if not count and vm is not None:"),
        L('            for attr in ("scenes", "vault_scenes", "scene_index"):'),
        L("                d = getattr(vm, attr, None)"),
        L("                if isinstance(d, dict) and d:"),
        L("                    count = len(d)"),
        L("                    break"),
        L('        print(f"[VAULT] Auto-relinked: {count} scenes from {vault_root} via {label}{_sig(fn)}")'),
        L("        return"),
        L("    last_err = err or last_err"),
        "",
        L('print("[VAULT] Cannot auto-relink — no compatible vault link method found.")'),
        L("if last_err:"),
        L('    print(f"[VAULT] Last error: {last_err}")'),
        "",
        L("def _print_suggestions(obj, prefix: str):"),
        L("    if obj is None:"),
        L("        return"),
        L("    printed = 0"),
        L("    for name in sorted(dir(obj)):"),
        L("        ln = name.lower()"),
        L('        if "vault" not in ln:'),
        L("            continue"),
        L('        if not any(k in ln for k in ("link", "relink", "attach", "connect")):'),
        L("            continue"),
        L("        try:"),
        L("            fn = getattr(obj, name, None)"),
        L("        except Exception:"),
        L("            continue"),
        L("        if callable(fn):"),
        L('            print(f"[VAULT]  - {prefix}.{name}{_sig(fn)}")'),
        L("            printed += 1"),
        L("            if printed >= 25:"),
        L("                break"),
        "",
        L('_print_suggestions(runtime, "runtime")'),
        L('_print_suggestions(vm, "runtime.vault_manager")'),
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    if not TARGET.exists():
        print(f"ERROR: target not found: {TARGET}", file=sys.stderr)
        return 2

    s = TARGET.read_text(encoding="utf-8")

    if MARKER in s:
        print(f"OK: already patched: {TARGET}")
        return 0

    if OLD_COMMENT not in s:
        print("ERROR: could not find expected anchor comment in _auto_relink_vault().", file=sys.stderr)
        print(f"  missing: {OLD_COMMENT}", file=sys.stderr)
        return 3

    if OLD_PRINT not in s:
        print("ERROR: could not find expected anchor print line in _auto_relink_vault().", file=sys.stderr)
        print(f"  missing: {OLD_PRINT}", file=sys.stderr)
        return 4

    start = s.index(OLD_COMMENT)
    end = s.index(OLD_PRINT)
    end_line = s.find("\n", end)
    end_line_end = end_line + 1 if end_line != -1 else len(s)

    new_block = _build_new_block()
    patched = s[:start] + new_block + s[end_line_end:]

    # Backup then atomic replace
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = TARGET.with_suffix(TARGET.suffix + f".bak.{ts}")
    backup.write_text(s, encoding="utf-8")

    tmp_dir = str(TARGET.parent)
    fd, tmp_path = tempfile.mkstemp(prefix=TARGET.name + ".", suffix=".tmp", dir=tmp_dir)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(patched)
        os.replace(tmp_path, TARGET)
    finally:
        try:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        except Exception:
            pass

    print(f"PATCHED: {TARGET}")
    print(f"BACKUP : {backup}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
