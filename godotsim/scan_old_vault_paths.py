#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path

VAULT_ROOT = Path("/run/media/mytruelove/storage1/pop/obsidian/obsidianburdenNov25")
ENGAIN_ROOT = Path("/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn")
NEEDLE = "/home/burdens"

TEXT_EXTS = {
    ".json", ".txt", ".md", ".py", ".yaml", ".yml", ".toml",
    ".cfg", ".ini", ".csv", ".zon", ".zonj", ".zw"
}


def safe_read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None


def print_header(title: str) -> None:
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


def scan_text_files(root: Path, label: str) -> None:
    print_header(f"TEXT MATCHES in {label}: {root}")
    found = 0

    if not root.exists():
        print(f"[MISSING] {root}")
        return

    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in TEXT_EXTS:
            continue

        text = safe_read_text(path)
        if not text or NEEDLE not in text:
            continue

        print(f"\n[FILE] {path}")
        for lineno, line in enumerate(text.splitlines(), start=1):
            if NEEDLE in line:
                print(f"  L{lineno}: {line.strip()}")
        found += 1

    if found == 0:
        print("No text matches found.")


def scan_symlinks(root: Path, label: str) -> None:
    print_header(f"SYMLINKS in {label}: {root}")
    found = 0

    if not root.exists():
        print(f"[MISSING] {root}")
        return

    for path in root.rglob("*"):
        if not path.is_symlink():
            continue
        try:
            target = os.readlink(path)
        except OSError as e:
            print(f"[BROKEN-READ] {path}: {e}")
            continue

        if NEEDLE in target:
            print(f"[SYMLINK] {path} -> {target}")
            found += 1

    if found == 0:
        print("No symlink matches found.")


def scan_manifest() -> None:
    manifest = VAULT_ROOT / "vault.manifest.json"
    print_header(f"MANIFEST CHECK: {manifest}")

    if not manifest.is_file():
        print("[MISSING] vault.manifest.json")
        return

    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[FAIL] Could not parse manifest: {e}")
        return

    blob = json.dumps(data, indent=2)
    if NEEDLE in blob:
        print("[HIT] /home/burdens appears inside vault.manifest.json")
        for lineno, line in enumerate(blob.splitlines(), start=1):
            if NEEDLE in line:
                print(f"  L{lineno}: {line.strip()}")
    else:
        print("No direct /home/burdens match in parsed manifest JSON.")


def main() -> None:
    print(f"Searching for old absolute path: {NEEDLE}")
    scan_manifest()
    scan_text_files(VAULT_ROOT, "VAULT")
    scan_symlinks(VAULT_ROOT, "VAULT")
    scan_text_files(ENGAIN_ROOT / "godotsim", "GODOTSIM")
    scan_text_files(ENGAIN_ROOT / "godotengain", "GODOTENGAIN")
    scan_symlinks(ENGAIN_ROOT / "godotsim", "GODOTSIM")
    scan_symlinks(ENGAIN_ROOT / "godotengain", "GODOTENGAIN")


if __name__ == "__main__":
    main()
