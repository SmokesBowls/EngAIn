#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from datetime import datetime
import os
import re
import sys
import tempfile


MARKER = "# [AUTO-RELINK-METHOD-DISCOVERY V1]"


def build_replacement(indent: str) -> str:
    def L(t: str) -> str:
        return indent + t

    lines = [
        L(MARKER),
        L("import inspect"),
        "",
        L('cfg_obj = {"vault_root": vault_root, "manifest_path": manifest_path, "manifest": manifest}'),
        "",
        L("def _sig(fn):"),
        L("    try:"),
        L("        return str(inspect.signature(fn))"),
        L("    except Exception:"),
        L('        return "(?)"'),
        "",
        L("def _try_calls(label, fn):"),
        L("    # returns (ok: bool, err: str|None)"),
        L("    tries = []"),
        L("    try:"),
        L("        sig = inspect.signature(fn)"),
        L("        pnames = set(sig.parameters.keys())"),
        L("    except Exception:"),
        L("        sig = None"),
        L("        pnames = set()"),
        "",
        L("    # Prefer explicit config kw if supported"),
        L('    for k in ("cfg", "config", "vault_cfg", "vault_config"):'),
        L("        if k in pnames:"),
        L('            tries.append(("kw:"+k, lambda k=k: fn(**{k: cfg_obj})))'),
        L("            break"),
        "",
        L("    # Common kw shapes"),
        L("    if pnames:"),
        L("        kw = {}"),
        L('        for rk in ("vault_root","root","vault","vault_dir","vault_path"):'),
        L("            if rk in pnames:"),
        L("                kw[rk] = vault_root"),
        L("                break"),
        L('        for mk in ("manifest","mfst","manifest_dict","manifest_json","manifest_data"):'),
        L("            if mk in pnames:"),
        L("                kw[mk] = manifest"),
        L("                break"),
        L("        if kw:"),
        L('            tries.append(("kw:root+manifest", lambda kw=kw: fn(**kw)))'),
        "",
        L("        kw = {}"),
        L('        for rk in ("vault_root","root","vault","vault_dir","vault_path"):'),
        L("            if rk in pnames:"),
        L("                kw[rk] = vault_root"),
        L("                break"),
        L('        for pk in ("manifest_path","manifest_file","manifest_filename","manifest_json_path","manifest_fp"):'),
        L("            if pk in pnames:"),
        L("                kw[pk] = manifest_path"),
        L("                break"),
        L("        if kw:"),
        L('            tries.append(("kw:root+manifest_path", lambda kw=kw: fn(**kw)))'),
        "",
        L("    # Positional fallbacks (safe: only 0..2 args)"),
        L("    tries.append(('pos:2(root,manifest)', lambda: fn(vault_root, manifest)))"),
        L("    if manifest_path:"),
        L("        tries.append(('pos:2(root,manifest_path)', lambda: fn(vault_root, manifest_path)))"),
        L("    tries.append(('pos:1(cfg)', lambda: fn(cfg_obj)))"),
        L("    tries.append(('pos:1(root)', lambda: fn(vault_root)))"),
        L("    tries.append(('pos:0()', lambda: fn()))"),
        "",
        L("    last = None"),
        L("    for mode, thunk in tries:"),
        L("        try:"),
        L("            thunk()"),
        L("            return True, None"),
        L("        except TypeError as e:"),
        L('            last = f\"{label}{_sig(fn)} via {mode}: {e}\"'),
        L("        except Exception as e:"),
        L('            last = f\"{label}{_sig(fn)} via {mode}: {e}\"'),
        L("    return False, last"),
        "",
        L("def _collect(obj, prefix, out):"),
        L("    if obj is None:"),
        L("        return"),
        L("    for name in whitelist:"),
        L("        try:"),
        L("            fn = getattr(obj, name, None)"),
        L("        except Exception:"),
        L("            fn = None"),
        L("        if callable(fn):"),
        L("            out.append((f\"{prefix}.{name}\", fn))"),
        "",
        L("whitelist = ("),
        L('    "link_vault","vault_link","relink_vault","vault_relink",'),
        L('    "attach_vault","connect_vault","link","relink","attach","connect",'),
        L(")"),
        L("candidates = []"),
        L("_collect(runtime, 'runtime', candidates)"),
        L("_collect(getattr(runtime, 'vault_manager', None), 'runtime.vault_manager', candidates)"),
        L("_collect(getattr(runtime, 'vault_client', None), 'runtime.vault_client', candidates)"),
        L("_collect(getattr(runtime, 'vault', None), 'runtime.vault', candidates)"),
        "",
        L("last_err = None"),
        L("for label, fn in candidates:"),
        L("    ok, err = _try_calls(label, fn)"),
        L("    if ok:"),
        L("        count = 0"),
        L("        vs = getattr(runtime, 'vault_scenes', None)"),
        L("        if isinstance(vs, dict):"),
        L("            count = len(vs)"),
        L('        print(f\"[VAULT] Auto-relinked: {count} scenes from {vault_root} via {label}{_sig(fn)}\")'),
        L("        break"),
        L("    last_err = err or last_err"),
        L("else:"),
        L('    print("[VAULT] Cannot auto-relink — no compatible vault link method found.")'),
        L("    if last_err:"),
        L('        print(f"[VAULT] Last error: {last_err}")'),
        L("    # Print discovery hints"),
        L("    def _hint(obj, prefix):"),
        L("        if obj is None:"),
        L("            return"),
        L("        shown = 0"),
        L("        for name in sorted(dir(obj)):"),
        L("            ln = name.lower()"),
        L("            if 'vault' not in ln:"),
        L("                continue"),
        L("            if not any(k in ln for k in ('link','relink','attach','connect')):"),
        L("                continue"),
        L("            try:"),
        L("                fn = getattr(obj, name, None)"),
        L("            except Exception:"),
        L("                continue"),
        L("            if callable(fn):"),
        L('                print(f"[VAULT]  - {prefix}.{name}{_sig(fn)}")'),
        L("                shown += 1"),
        L("                if shown >= 25:"),
        L("                    break"),
        L("    _hint(runtime, 'runtime')"),
        L("    _hint(getattr(runtime,'vault_manager',None), 'runtime.vault_manager')"),
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    target = repo_root / "godotsim" / "sim_runtime.py"
    if not target.exists():
        print(f"ERROR: target not found: {target}", file=sys.stderr)
        return 2

    s = target.read_text(encoding="utf-8", errors="strict")

    if MARKER in s:
        print(f"OK: already patched: {target}")
        return 0

    anchor_comment = "# Call the same vault link method that /vault/link uses"
    anchor_print = 'print("[VAULT] Cannot auto-relink — no link_vault method found on runtime")'

    if anchor_comment not in s:
        print("ERROR: anchor comment not found; refusing to patch.", file=sys.stderr)
        print(f"  missing: {anchor_comment}", file=sys.stderr)
        return 3
    if anchor_print not in s:
        print("ERROR: anchor print not found; refusing to patch.", file=sys.stderr)
        print(f"  missing: {anchor_print}", file=sys.stderr)
        return 4

    # Determine indentation based on the anchor line
    m = re.search(r"^(?P<indent>\s*)# Call the same vault link method that /vault/link uses\s*$", s, flags=re.M)
    if not m:
        print("ERROR: could not determine indentation.", file=sys.stderr)
        return 5
    indent = m.group("indent")

    start = s.index(anchor_comment)
    end = s.index(anchor_print)
    end_line = s.find("\n", end)
    end_line_end = end_line + 1 if end_line != -1 else len(s)

    replacement = build_replacement(indent)
    patched = s[:start] + replacement + s[end_line_end:]

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = target.with_suffix(target.suffix + f".bak.{ts}")
    backup.write_text(s, encoding="utf-8")

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
