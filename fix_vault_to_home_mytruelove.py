#!/usr/bin/env python3
from pathlib import Path
import json
import re

ENGAIN = Path("/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn")
GOOD_ROOT = "/home/mytruelove/obsidian/obsidianburdenNov25"
GOOD_MANIFEST = f"{GOOD_ROOT}/vault.manifest.json"
BAD_ROOT = "/home/burdens/obsidian/obsidianburdenNov25"
BAD_MANIFEST = f"{BAD_ROOT}/vault.manifest.json"

targets = [
    ENGAIN / "godotroot" / "zonjrender" / "autoload" / "VaultClient.gd",
    ENGAIN / "godotroot" / "zonjrender" / "scenes" / "EngAInTestScene.gd",
]

def backup(path: Path) -> None:
    bak = path.with_name(path.name + ".bak_homefix")
    if not bak.exists():
        bak.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

def patch_text(path: Path) -> bool:
    if not path.exists():
        print(f"[MISS] {path}")
        return False
    original = path.read_text(encoding="utf-8")
    updated = original.replace(BAD_MANIFEST, GOOD_MANIFEST).replace(BAD_ROOT, GOOD_ROOT)
    if updated != original:
        backup(path)
        path.write_text(updated, encoding="utf-8")
        print(f"[PATCHED] {path}")
        return True
    print(f"[OK] {path}")
    return False

def write_runtime_config() -> None:
    cfg_path = ENGAIN / "godotsim" / ".engain_config.json"
    if cfg_path.exists():
        backup(cfg_path)
    cfg = {
        "vault_root": GOOD_ROOT,
        "manifest_path": GOOD_MANIFEST
    }
    cfg_path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    print(f"[WROTE] {cfg_path}")

def sweep_project() -> None:
    root = ENGAIN / "godotroot" / "zonjrender"
    exts = {".gd", ".tscn", ".godot", ".json", ".cfg", ".txt"}
    changed = 0
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in exts:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue
        new_text = text.replace(BAD_MANIFEST, GOOD_MANIFEST).replace(BAD_ROOT, GOOD_ROOT)
        if new_text != text:
            backup(path)
            path.write_text(new_text, encoding="utf-8")
            print(f"[SWEEP] {path}")
            changed += 1
    print(f"[SWEEP] changed files: {changed}")

def main() -> None:
    if not Path(GOOD_ROOT).is_dir():
        raise SystemExit(f"Vault root missing: {GOOD_ROOT}")
    if not Path(GOOD_MANIFEST).is_file():
        raise SystemExit(f"Manifest missing: {GOOD_MANIFEST}")

    write_runtime_config()
    for t in targets:
        patch_text(t)
    sweep_project()

    print("\nDone.")
    print("Next: restart godotsim and reopen Godot.")

if __name__ == "__main__":
    main()
