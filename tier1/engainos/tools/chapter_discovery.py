#!/usr/bin/env python3
"""
chapter_discovery.py — EngAIn Chapter Discovery Tool

Scans the active vault for book folders and their chapter files.
A book folder is any directory whose name starts with "book".
A chapter is any .md or .txt file inside a book folder.

Writes a chapter index to vault/.engain/chapter_index.json.

Usage:
    python3 chapter_discovery.py
    python3 chapter_discovery.py --manifest /path/to/engain_manifest.json
    python3 chapter_discovery.py --list
    python3 chapter_discovery.py --vault /path/to/vault

Can also be imported:
    from tier1.engainos.tools.chapter_discovery import discover_chapters
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Optional


# ── Chapter index contract ───────────────────────────────────────────────────

CONTRACT = "engain.chapter_index.v1"


# ── Discovery ────────────────────────────────────────────────────────────────

def discover_chapters(vault_root: Path) -> dict:
    """
    Scan vault_root for book folders and their chapter files.

    Returns:
        {
            "contract":     str,
            "vault_root":   str,
            "book_count":   int,
            "chapter_count": int,
            "books": [
                {
                    "book_id":      str,   # e.g. "book_01_book_of_genesis"
                    "book_number":  int,   # e.g. 1
                    "book_name":    str,   # e.g. "book of genesis"
                    "path":         str,
                    "chapters": [
                        {
                            "chapter_id":     str,   # e.g. "001_the_ethereal_vigil"
                            "chapter_number": int,   # e.g. 1
                            "chapter_name":   str,   # e.g. "the ethereal vigil"
                            "path":           str,
                            "extension":      str,   # ".md" or ".txt"
                        }
                    ]
                }
            ]
        }
    """
    vault_root = vault_root.resolve()

    book_dirs = sorted(
        d for d in vault_root.iterdir()
        if d.is_dir() and d.name.lower().startswith("book")
    )

    books = []
    total_chapters = 0

    for book_dir in book_dirs:
        book_number = _extract_number(book_dir.name)
        book_name = _extract_name(book_dir.name, prefix_pattern=r"^book[\s_-]*\d+[\s_-]*")

        chapter_files = sorted(
            f for f in book_dir.iterdir()
            if f.is_file() and f.suffix.lower() in (".md", ".txt")
        )

        chapters = []
        for chapter_file in chapter_files:
            chapter_number = _extract_number(chapter_file.stem)
            chapter_name = _extract_name(
                chapter_file.stem,
                prefix_pattern=r"^\d+[\s_-]*",
            )
            chapters.append({
                "chapter_id":     chapter_file.stem,
                "chapter_number": chapter_number,
                "chapter_name":   chapter_name,
                "path":           str(chapter_file),
                "extension":      chapter_file.suffix.lower(),
            })

        books.append({
            "book_id":      book_dir.name,
            "book_number":  book_number,
            "book_name":    book_name,
            "path":         str(book_dir),
            "chapters":     chapters,
        })

        total_chapters += len(chapters)

    return {
        "contract":      CONTRACT,
        "vault_root":    str(vault_root),
        "book_count":    len(books),
        "chapter_count": total_chapters,
        "books":         books,
    }


def _extract_number(name: str) -> int:
    """Extract the first integer from a filename or folder name."""
    m = re.search(r"\d+", name)
    return int(m.group()) if m else 0


def _extract_name(name: str, prefix_pattern: str) -> str:
    """Strip leading number prefix and return a human-readable name."""
    cleaned = re.sub(prefix_pattern, "", name, flags=re.IGNORECASE)
    return cleaned.replace("_", " ").replace("-", " ").strip()


# ── Manifest I/O ─────────────────────────────────────────────────────────────

def _read_manifest(manifest_path: Path) -> dict:
    if not manifest_path.exists():
        return {}
    try:
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[chapter_discovery] Warning: could not read manifest: {e}")
        return {}


def _default_manifest_path() -> Path:
    here = Path(__file__).resolve().parent
    candidates = []
    if len(here.parents) > 1:
        candidates.append(here.parents[1] / "assets" / "engain_manifest.json")
    if len(here.parents) > 2:
        candidates.append(here.parents[2] / "tier1" / "engainos" / "assets" / "engain_manifest.json")
    candidates.append(here.parent / "engain_manifest.json")
    for c in candidates:
        if c.exists():
            return c
    if len(here.parents) > 1:
        return here.parents[1] / "assets" / "engain_manifest.json"
    return here / "engain_manifest.json"


def _vault_from_manifest(manifest_path: Path) -> Optional[Path]:
    manifest = _read_manifest(manifest_path)
    active_vault = manifest.get("active_vault")
    if active_vault:
        return Path(active_vault)
    return None


def write_chapter_index(index: dict, vault_root: Path) -> Path:
    """Write chapter index to vault/.engain/chapter_index.json."""
    output_dir = vault_root / ".engain"
    output_dir.mkdir(exist_ok=True)
    index_path = output_dir / "chapter_index.json"
    index_path.write_text(
        json.dumps(index, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return index_path


# ── Display ───────────────────────────────────────────────────────────────────

def _print_index(index: dict, verbose: bool = False) -> None:
    print(f"\n[EngAIn] Vault: {index['vault_root']}")
    print(f"         Books   : {index['book_count']}")
    print(f"         Chapters: {index['chapter_count']}\n")

    for book in index["books"]:
        print(f"  Book {book['book_number']:02d}: {book['book_name']}  ({len(book['chapters'])} chapters)")
        if verbose:
            for ch in book["chapters"]:
                print(f"           {ch['chapter_number']:03d}. {ch['chapter_name']}")
        print()


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="EngAIn Chapter Discovery — scan vault for book folders and chapters."
    )
    parser.add_argument(
        "--manifest",
        default=None,
        help="Path to engain_manifest.json (auto-detected if omitted).",
    )
    parser.add_argument(
        "--vault",
        default=None,
        help="Direct path to vault root (overrides manifest).",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List discovered books and chapters without writing index.",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show individual chapter names.",
    )
    args = parser.parse_args()

    # Resolve vault root
    if args.vault:
        vault_root = Path(args.vault).resolve()
    else:
        manifest_path = Path(args.manifest) if args.manifest else _default_manifest_path()
        vault_root = _vault_from_manifest(manifest_path)
        if vault_root is None:
            print("[chapter_discovery] No active_vault in manifest.")
            print("                    Run vault_discovery.py first, or pass --vault.")
            return 1

    if not vault_root.exists():
        print(f"[chapter_discovery] Vault not found: {vault_root}")
        return 1

    print(f"[EngAIn] Scanning for chapters in: {vault_root}")
    index = discover_chapters(vault_root)

    if index["book_count"] == 0:
        print("[chapter_discovery] No book folders found.")
        print("                    Book folders must start with 'book'.")
        return 1

    _print_index(index, verbose=args.verbose)

    if not args.list:
        index_path = write_chapter_index(index, vault_root)
        print(f"[chapter_discovery] CHAPTER_INDEX_WRITTEN = TRUE")
        print(f"[chapter_discovery] INDEX_PATH            = {index_path}")
        print(f"[chapter_discovery] BOOK_COUNT            = {index['book_count']}")
        print(f"[chapter_discovery] CHAPTER_COUNT         = {index['chapter_count']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
