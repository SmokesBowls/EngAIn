#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from datetime import datetime
import os
import sys
import tempfile


MARKER = "# [AUTO-RELINK-V3 vault_linker.link]"


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

    if MARKER in original:
        print(f"OK: already patched: {target}")
        return 0

    new_fn = f'''def _auto_relink_vault(runtime, config_path: str):
    """
    Auto-relink vault on boot using the same engine pathway as POST /vault/link:

      runtime.vault_linker.link(manifest, vault_root)
      then populate runtime.vault_scenes from runtime.vault_linker.get_all_scenes()

    Falls back to a tiny method scan if vault_linker isn't present.
    """
    {MARKER}
    if not os.path.exists(config_path):
        print("[VAULT] No saved config — link vault manually via POST /vault/link")
        return

    try:
        with open(config_path, "r") as f:
            cfg = json.load(f)
    except Exception as e:
        print(f"[VAULT] Saved config unreadable — skipping auto-relink: {e}")
        return

    vault_root = (cfg.get("vault_root") or "").strip()
    manifest_path = (cfg.get("manifest_path") or "").strip()

    if not vault_root or not manifest_path:
        print("[VAULT] Saved config incomplete — skipping auto-relink")
        return

    if not os.path.isdir(vault_root):
        print(f"[VAULT] Vault root missing: {vault_root} — skipping")
        return

    if not os.path.isfile(manifest_path):
        # Common fallback: vault_root/vault.manifest.json
        candidate = os.path.join(vault_root, "vault.manifest.json")
        if os.path.isfile(candidate):
            manifest_path = candidate
        else:
            print(f"[VAULT] Manifest not found: {manifest_path} — skipping")
            return

    try:
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
    except Exception as e:
        print(f"[VAULT] Manifest unreadable: {manifest_path} — skipping: {e}")
        return

    # Preferred: mirror the HTTP handler’s implementation.
    try:
        vl = getattr(runtime, "vault_linker", None)
        link_fn = getattr(vl, "link", None) if vl is not None else None
        get_all = getattr(vl, "get_all_scenes", None) if vl is not None else None

        if callable(link_fn):
            result = link_fn(manifest, vault_root)

            ok = isinstance(result, dict) and result.get("status") == "ok"
            if ok and callable(get_all) and hasattr(runtime, "vault_scenes"):
                loaded = 0
                scenes = get_all()
                if isinstance(scenes, dict):
                    for sid, scene in scenes.items():
                        runtime.vault_scenes[sid] = scene
                        loaded += 1
                # Keep a helpful summary line
                print(f"[VAULT] Auto-relinked: {loaded} scenes from {vault_root} via runtime.vault_linker.link(manifest, vault_root)")
                return

            # If result isn't dict/ok, still print something actionable.
            if isinstance(result, dict):
                print(f"[VAULT] Auto-relink attempted via vault_linker.link but status={result.get('status')!r}")
            else:
                print("[VAULT] Auto-relink attempted via vault_linker.link but got non-dict result")
            # Fall through to discovery hints.
    except Exception as e:
        print(f"[VAULT] Auto-relink via vault_linker.link failed: {e}")

    # Fallback: small scan for any obvious vault link callables (no guessing beyond 2 args).
    import inspect

    def _sig(fn):
        try:
            return str(inspect.signature(fn))
        except Exception:
            return "(?)"

    candidates = []
    for obj, prefix in (
        (runtime, "runtime"),
        (getattr(runtime, "vault_manager", None), "runtime.vault_manager"),
        (getattr(runtime, "vault_client", None), "runtime.vault_client"),
        (getattr(runtime, "vault", None), "runtime.vault"),
    ):
        if obj is None:
            continue
        for name in ("link_vault","vault_link","relink_vault","vault_relink","link","relink","attach_vault","connect_vault"):
            fn = getattr(obj, name, None)
            if callable(fn):
                candidates.append((f"{prefix}.{name}", fn))

    last_err = None
    for label, fn in candidates:
        try:
            sig = inspect.signature(fn)
            req = [p for p in sig.parameters.values()
                   if p.default is p.empty and p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)]
            if len(req) == 2:
                fn(vault_root, manifest)
                print(f"[VAULT] Auto-relinked via {label}{_sig(fn)}")
                return
            elif len(req) == 1:
                fn(vault_root)
                print(f"[VAULT] Auto-relinked via {label}{_sig(fn)}")
                return
            elif len(req) == 0:
                fn()
                print(f"[VAULT] Auto-relinked via {label}{_sig(fn)}")
                return
        except Exception as e:
            last_err = f"{label}{_sig(fn)}: {e}"

    print("[VAULT] Cannot auto-relink — no compatible vault link method found.")
    if last_err:
        print(f"[VAULT] Last error: {last_err}")
'''

    patched, ok = _rewrite_function(original, "_auto_relink_vault", new_fn)
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

