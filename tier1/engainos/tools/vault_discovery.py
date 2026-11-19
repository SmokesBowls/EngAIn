#!/usr/bin/env python3
"""
vault_discovery.py — EngAIn Vault Discovery Tool

Scans common filesystem locations for Obsidian vaults (folders containing
a .obsidian/ subfolder). Presents candidates to the user, writes the chosen
vault into engain_manifest.json.

Usage:
    python3 vault_discovery.py
    python3 vault_discovery.py --manifest /path/to/engain_manifest.json
    python3 vault_discovery.py --scan /custom/search/root
    python3 vault_discovery.py --non-interactive  # auto-selects if only one found

Can also be imported:
    from tier1.engainos.tools.vault_discovery import discover_vaults, write_vault_to_manifest
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional


# ── Default scan roots ───────────────────────────────────────────────────────

def _default_scan_roots() -> list[Path]:
    home = Path.home()
    candidates = [
        home,
        home / "Downloads",
        home / "Documents",
        home / "Desktop",
        home / "Dropbox",
        home / "OneDrive",
        home / "iCloud",
        Path("/mnt"),
        Path("/run/media") / os.environ.get("USER", ""),
    ]
    return [p for p in candidates if p.exists() and p.is_dir()]


# ── Discovery ────────────────────────────────────────────────────────────────

def discover_vaults(
    scan_roots: Optional[list[Path]] = None,
    max_depth: int = 4,
) -> list[dict]:
    """
    Scan filesystem for Obsidian vaults.

    A vault is any directory that contains a .obsidian/ subdirectory.

    Returns a list of dicts sorted by score descending:
        {
            "path":       Path,
            "name":       str,
            "md_count":   int,
            "has_manifest": bool,
            "score":      int,
        }
    """
    if scan_roots is None:
        scan_roots = _default_scan_roots()

    found: dict[Path, dict] = {}

    for root in scan_roots:
        _scan_dir(root, found, current_depth=0, max_depth=max_depth)

    results = sorted(found.values(), key=lambda v: v["score"], reverse=True)
    return results


def _scan_dir(
    path: Path,
    found: dict,
    current_depth: int,
    max_depth: int,
) -> None:
    if current_depth > max_depth:
        return

    try:
        entries = list(path.iterdir())
    except PermissionError:
        return
    except OSError:
        return

    entry_names = {e.name for e in entries}

    if ".obsidian" in entry_names:
        obsidian_dir = path / ".obsidian"
        if obsidian_dir.is_dir() and path not in found:
            found[path] = _describe_vault(path)
        return  # don't recurse into a vault

    # Recurse into subdirectories (skip hidden dirs and common noise)
    skip = {".git", "__pycache__", "node_modules", ".cache", ".local", ".config"}
    for entry in entries:
        if entry.is_dir() and entry.name not in skip and not entry.name.startswith("."):
            _scan_dir(entry, found, current_depth + 1, max_depth)


def _describe_vault(path: Path) -> dict:
    """Build a description and score for a discovered vault."""
    md_files = list(path.rglob("*.md"))
    md_count = len(md_files)
    has_manifest = (path / "vault.manifest.json").exists()

    score = 0
    score += min(md_count, 200)          # up to 200 points for md files
    score += 50 if has_manifest else 0   # bonus for existing EngAIn manifest
    score += 20 if md_count > 50 else 0  # bonus for large vaults
    score += 10 if md_count > 10 else 0  # bonus for non-trivial vaults

    return {
        "path": path,
        "name": path.name,
        "md_count": md_count,
        "has_manifest": has_manifest,
        "score": score,
    }


# ── Manifest I/O ─────────────────────────────────────────────────────────────

def _default_manifest_path() -> Path:
    """Find engain_manifest.json relative to this script's location."""
    # Try: script is at tier1/engainos/tools/vault_discovery.py
    here = Path(__file__).resolve().parent
    candidates = []
    if len(here.parents) > 1:
        candidates.append(here.parents[1] / "assets" / "engain_manifest.json")
    if len(here.parents) > 2:
        candidates.append(here.parents[2] / "tier1" / "engainos" / "assets" / "engain_manifest.json")
    candidates.append(here.parent / "engain_manifest.json")
    candidates.append(here / "engain_manifest.json")
    for c in candidates:
        if c.exists():
            return c
    # Return the most likely install location even if it doesn't exist yet
    if len(here.parents) > 1:
        return here.parents[1] / "assets" / "engain_manifest.json"
    return here / "engain_manifest.json"


def read_manifest(manifest_path: Path) -> dict:
    if not manifest_path.exists():
        return {"spec_version": "engain.manifest.v2"}
    try:
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[vault_discovery] Warning: could not read manifest: {e}")
        return {"spec_version": "engain.manifest.v2"}


def resolve_active_vault(manifest_path: Optional[Path] = None) -> dict:
    """
    Tier 1's single, read-only answer to "which vault is active?".

    Authority: active.vault names an entry in vaults{}; that entry's root wins.
    The legacy top-level active_vault is only cross-checked (still read by
    tier3 chapterroom_index_runner); a mismatch is reported, never guessed past.

    Returns {status: "ok"|"error", vault_id, root, manifest_path, source,
    authority_fields, problems[]}. source is the engain_manifest.json read;
    authority_fields names the keys in it that decided vault_id and root.
    Never writes.
    """
    mp = Path(manifest_path) if manifest_path else _default_manifest_path()
    result = {"status": "error", "vault_id": None, "root": None,
              "manifest_path": None, "source": str(mp),
              "authority_fields": {"vault_id": "active.vault", "root": None},
              "problems": []}
    problems = result["problems"]

    if not mp.is_file():
        problems.append(f"engain_manifest.json not found: {mp}")
        return result
    try:
        manifest = json.loads(mp.read_text(encoding="utf-8"))
    except Exception as e:
        problems.append(f"engain_manifest.json unreadable: {e}")
        return result
    if not isinstance(manifest, dict):
        problems.append("engain_manifest.json is not a JSON object")
        return result

    active = manifest.get("active")
    vault_id = active.get("vault") if isinstance(active, dict) else None
    vaults = manifest.get("vaults")
    entry = vaults.get(vault_id) if isinstance(vaults, dict) and vault_id else None
    root = entry.get("root") if isinstance(entry, dict) else None
    result["vault_id"] = vault_id
    if vault_id:
        result["authority_fields"]["root"] = f"vaults[{vault_id!r}].root"

    if not vault_id:
        problems.append("active.vault is missing")
    elif not root:
        problems.append(f"vaults[{vault_id!r}] is missing or has no root")
    else:
        result["root"] = root
        if not os.path.isdir(root):
            problems.append(f"vault root does not exist: {root}")
        vmanifest = entry.get("manifest") or os.path.join(root, "vault.manifest.json")
        result["manifest_path"] = vmanifest
        if not os.path.isfile(vmanifest):
            problems.append(f"vault manifest does not exist: {vmanifest}")

    legacy = manifest.get("active_vault")
    if legacy and root and os.path.realpath(legacy) != os.path.realpath(root):
        problems.append(f"legacy active_vault {legacy!r} disagrees with vaults[{vault_id!r}].root {root!r}")

    if not problems:
        result["status"] = "ok"
    return result


ASSETS_MANIFEST_SPEC = "engain.assets_manifest.v1"


def resolve_active_asset_pack(manifest_path: Optional[Path] = None) -> dict:
    """
    Tier 1's read-only answer to "which asset pack is active, and what does it say?".

    Authority: active.asset_pack names an entry in asset_packs{}; that entry's
    manifest is read and returned as-is. A missing or invalid pack is reported,
    never replaced. Returns {status, asset_pack_id, root, manifest_path, source,
    authority_fields, problems[], manifest}. Never writes.
    """
    mp = Path(manifest_path) if manifest_path else _default_manifest_path()
    result = {"status": "error", "asset_pack_id": None, "root": None,
              "manifest_path": None, "source": str(mp),
              "authority_fields": {"asset_pack_id": "active.asset_pack", "manifest_path": None},
              "problems": [], "manifest": None}
    problems = result["problems"]

    try:
        manifest = json.loads(mp.read_text(encoding="utf-8"))
    except FileNotFoundError:
        problems.append(f"engain_manifest.json not found: {mp}")
        return result
    except Exception as e:
        problems.append(f"engain_manifest.json unreadable: {e}")
        return result
    if not isinstance(manifest, dict):
        problems.append("engain_manifest.json is not a JSON object")
        return result

    active = manifest.get("active")
    pack_id = active.get("asset_pack") if isinstance(active, dict) else None
    packs = manifest.get("asset_packs")
    entry = packs.get(pack_id) if isinstance(packs, dict) and pack_id else None
    result["asset_pack_id"] = pack_id
    if not pack_id:
        problems.append("active.asset_pack is missing")
        return result
    if not isinstance(entry, dict) or not entry.get("manifest"):
        problems.append(f"asset_packs[{pack_id!r}] is missing or has no manifest")
        return result

    result["root"] = entry.get("root")
    result["manifest_path"] = entry["manifest"]
    result["authority_fields"]["manifest_path"] = f"asset_packs[{pack_id!r}].manifest"
    try:
        pack = json.loads(Path(entry["manifest"]).read_text(encoding="utf-8"))
    except FileNotFoundError:
        problems.append(f"asset pack manifest does not exist: {entry['manifest']}")
        return result
    except Exception as e:
        problems.append(f"asset pack manifest unreadable: {e}")
        return result
    if not isinstance(pack, dict):
        problems.append("asset pack manifest is not a JSON object")
        return result
    if pack.get("spec_version") != ASSETS_MANIFEST_SPEC:
        problems.append(f"asset pack spec_version {pack.get('spec_version')!r} is not {ASSETS_MANIFEST_SPEC!r}")
    if pack.get("asset_pack_id") != pack_id:
        problems.append(f"asset pack declares asset_pack_id {pack.get('asset_pack_id')!r}, expected {pack_id!r}")
    if not problems:
        result["status"] = "ok"
        result["manifest"] = pack
    return result


def write_vault_to_manifest(vault_path: Path, manifest_path: Path) -> None:
    """
    Write the chosen vault into engain_manifest.json.

    Sets:
        active_vault   — absolute path to vault root
        output_dir     — vault_root/.engain  (EngAIn's output home)

    Preserves all other existing manifest fields.
    """
    manifest = read_manifest(manifest_path)

    vault_abs = vault_path.resolve()
    output_dir = vault_abs / ".engain"

    manifest["active_vault"] = str(vault_abs)
    manifest["output_dir"] = str(output_dir)

    # Keep legacy vaults block updated too
    vaults = manifest.setdefault("vaults", {})
    vaults[vault_abs.name] = {
        "root": str(vault_abs),
        "manifest": str(vault_abs / "vault.manifest.json"),
    }
    manifest["active"] = manifest.get("active", {})
    manifest["active"]["vault"] = vault_abs.name

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # Create .engain output dir
    output_dir.mkdir(exist_ok=True)
    print(f"[vault_discovery] Output directory: {output_dir}")


# ── Interactive UI ────────────────────────────────────────────────────────────

def _print_vault(idx: int, vault: dict) -> None:
    marker = " [has EngAIn manifest]" if vault["has_manifest"] else ""
    print(f"  {idx}. {vault['name']}{marker}")
    print(f"     Path     : {vault['path']}")
    print(f"     Chapters : {vault['md_count']} .md files")


def run_interactive(
    scan_roots: Optional[list[Path]],
    manifest_path: Path,
    non_interactive: bool = False,
) -> Optional[Path]:
    print("\n[EngAIn] Scanning for Obsidian vaults...")
    vaults = discover_vaults(scan_roots)

    if not vaults:
        print("[EngAIn] No Obsidian vaults found.")
        print("         Make sure your vault folder contains a .obsidian/ subfolder.")
        return None

    print(f"\n[EngAIn] Found {len(vaults)} vault(s):\n")
    for i, v in enumerate(vaults, start=1):
        _print_vault(i, v)
        print()

    if non_interactive:
        if len(vaults) == 1:
            chosen = vaults[0]
            print(f"[vault_discovery] Auto-selected: {chosen['path']}")
        else:
            print("[vault_discovery] --non-interactive requires exactly one vault. Found multiple.")
            return None
    else:
        if len(vaults) == 1:
            answer = input(f"Use '{vaults[0]['name']}'? [Y/n]: ").strip().lower()
            if answer in ("", "y", "yes"):
                chosen = vaults[0]
            else:
                print("[vault_discovery] Cancelled.")
                return None
        else:
            while True:
                raw = input(f"Select vault [1-{len(vaults)}] or 'q' to quit: ").strip()
                if raw.lower() == "q":
                    print("[vault_discovery] Cancelled.")
                    return None
                try:
                    idx = int(raw)
                    if 1 <= idx <= len(vaults):
                        chosen = vaults[idx - 1]
                        break
                    else:
                        print(f"  Please enter a number between 1 and {len(vaults)}.")
                except ValueError:
                    print("  Please enter a number.")

    write_vault_to_manifest(chosen["path"], manifest_path)

    print(f"\n[vault_discovery] VAULT_SELECTED = TRUE")
    print(f"[vault_discovery] VAULT_PATH     = {chosen['path']}")
    print(f"[vault_discovery] MANIFEST       = {manifest_path}")
    print(f"[vault_discovery] OUTPUT_DIR     = {chosen['path']}/.engain")

    return chosen["path"]


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="EngAIn Vault Discovery — find and register an Obsidian vault."
    )
    parser.add_argument(
        "--manifest",
        default=None,
        help="Path to engain_manifest.json (auto-detected if omitted).",
    )
    parser.add_argument(
        "--scan",
        action="append",
        dest="scan_roots",
        metavar="DIR",
        help="Additional directory to scan (can be repeated).",
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Auto-select if exactly one vault is found.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List discovered vaults and exit without writing.",
    )
    args = parser.parse_args()

    manifest_path = Path(args.manifest) if args.manifest else _default_manifest_path()

    scan_roots = None
    if args.scan_roots:
        scan_roots = _default_scan_roots() + [Path(p) for p in args.scan_roots]

    if args.list:
        print("\n[EngAIn] Scanning for Obsidian vaults...\n")
        vaults = discover_vaults(scan_roots)
        if not vaults:
            print("No vaults found.")
        for i, v in enumerate(vaults, start=1):
            _print_vault(i, v)
            print()
        return 0

    result = run_interactive(scan_roots, manifest_path, args.non_interactive)
    return 0 if result else 1


if __name__ == "__main__":
    raise SystemExit(main())
