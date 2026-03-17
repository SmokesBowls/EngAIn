#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from datetime import datetime
import os
import sys
import tempfile


MARKER = "# [AUTO-RELINK-V3B vault_linker.link]"


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


NEW_FN = '''def _auto_relink_vault(runtime, config_path: str):
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

    print(f"[VAULT] Auto-relinked: {loaded} scenes from {vault_root} via runtime.vault_linker.link(manifest, vault_root)")
'''


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    target = repo_root / "godotsim" / "sim_runtime.py"
    if not target.exists():
        print(f"ERROR: target not found: {target}", file=sys.stderr)
        return 2

    original = target.read_text(encoding="utf-8")

    if MARKER in original:
        print(f"OK: already patched: {target}")
        return 0

    patched, ok = _rewrite_function(original, "_auto_relink_vault", NEW_FN)
    if not ok:
        print("ERROR: could not locate def _auto_relink_vault(...)", file=sys.stderr)
        return 3

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
