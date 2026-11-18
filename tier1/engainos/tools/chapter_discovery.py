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
import hashlib
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


# ── Catalog (read-only, live rescan) ─────────────────────────────────────────

CATALOG_CONTRACT = "engain.chapter_catalog.v1"

_LEADING_NUMBER_RE = re.compile(r"^(\d+)")
_BOOK_LEADING_NUMBER_RE = re.compile(r"^book[\s_-]*(\d+)", re.IGNORECASE)
# A leading number joined to a second number ("22 and 23", "22-23", "22 to 23").
_AMBIGUOUS_NUMBER_RE = re.compile(r"^\d+\s*(?:and|&|to|-|–|,|\+)\s*\d+", re.IGNORECASE)


def _leading_number(stem: str, pattern: re.Pattern = _LEADING_NUMBER_RE) -> Optional[int]:
    m = pattern.match(stem)
    return int(m.group(1)) if m else None


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _manifest_discrepancies(vault_root: Path, vault_manifest_path: Path, catalog_ids: set) -> dict:
    out = {"vault_manifest": str(vault_manifest_path), "status": "ok",
           "listed_but_missing": [], "on_disk_but_unlisted": []}
    try:
        data = json.loads(vault_manifest_path.read_text(encoding="utf-8"))
        listed = data.get("source_files") if isinstance(data, dict) else None
        if not isinstance(listed, list):
            raise ValueError("source_files is not a list")
    except Exception as e:
        out["status"] = f"unreadable: {e}"
        return out
    listed = [str(p) for p in listed]
    out["listed_but_missing"] = sorted(p for p in listed if not (vault_root / p).is_file())
    out["on_disk_but_unlisted"] = sorted(catalog_ids - set(listed))
    return out


def build_chapter_catalog(vault_root: Path, vault_manifest_path: Optional[Path] = None) -> dict:
    """
    Read-only chapter catalog for the given vault. Rescans the filesystem on
    every call and never reads or writes .engain/chapter_index.json.

    Discovery is discover_chapters()'s rule. Each entry keeps its legacy fields
    (chapter_id, chapter_number, ...) and adds:
        catalog_id      "<book folder>/<file name with extension>" — file identity
        source_sha256   hash of the file's bytes — content version, not identity
        leading_number  number at the start of the file name, or None
        anomalies       flags; flagged files are still listed

    An entry is a source file, not an approved canonical chapter.
    """
    index = discover_chapters(Path(vault_root))
    root = Path(index["vault_root"])
    anomaly_counts: dict = {}
    chapter_id_owners: dict = {}
    books = []

    for book in index["books"]:
        chapters = []
        for ch in book["chapters"]:
            path = Path(ch["path"])
            stem = path.stem
            entry = dict(ch)
            entry["file_name"] = path.name
            entry["catalog_id"] = f"{book['book_id']}/{path.name}"
            entry["source_sha256"] = _sha256_file(path)
            entry["leading_number"] = _leading_number(stem)
            entry["anomalies"] = []
            if entry["leading_number"] is None:
                entry["anomalies"].append("unusual_filename")
            elif _AMBIGUOUS_NUMBER_RE.match(stem):
                entry["anomalies"].append("ambiguous_chapter_number")
            chapter_id_owners.setdefault(ch["chapter_id"], []).append(entry["catalog_id"])
            chapters.append(entry)

        by_number: dict = {}
        for entry in chapters:
            if entry["leading_number"] is not None:
                by_number.setdefault(entry["leading_number"], []).append(entry)
        for group in by_number.values():
            if len(group) > 1:
                for entry in group:
                    entry["anomalies"].append("duplicate_chapter_number")

        # Numbered files in numeric order, then unnumbered; file name breaks ties.
        chapters.sort(key=lambda e: (e["leading_number"] is None, e["leading_number"] or 0, e["file_name"]))
        for entry in chapters:
            for flag in entry["anomalies"]:
                anomaly_counts[flag] = anomaly_counts.get(flag, 0) + 1

        book_entry = dict(book)
        book_entry["leading_number"] = _leading_number(book["book_id"], _BOOK_LEADING_NUMBER_RE)
        book_entry["chapters"] = chapters
        books.append(book_entry)

    books.sort(key=lambda b: (b["leading_number"] is None, b["leading_number"] or 0, b["book_id"]))

    catalog_ids = {e["catalog_id"] for b in books for e in b["chapters"]}
    vmp = Path(vault_manifest_path) if vault_manifest_path else root / "vault.manifest.json"
    return {
        "contract": CATALOG_CONTRACT,
        "vault_root": str(root),
        "book_count": len(books),
        "chapter_count": sum(len(b["chapters"]) for b in books),
        "anomaly_counts": dict(sorted(anomaly_counts.items())),
        # Legacy chapter_id is the bare stem, so it can collide where catalog_id cannot.
        "chapter_id_collisions": {cid: owners for cid, owners in sorted(chapter_id_owners.items()) if len(owners) > 1},
        "manifest_discrepancies": _manifest_discrepancies(root, vmp, catalog_ids),
        "books": books,
    }


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
    # Vault identity comes from Tier 1's resolver, not a local manifest read.
    try:
        from .vault_discovery import resolve_active_vault
    except ImportError:  # run as a script from tools/
        from vault_discovery import resolve_active_vault
    resolved = resolve_active_vault(manifest_path)
    if resolved["status"] != "ok":
        for problem in resolved["problems"]:
            print(f"[chapter_discovery] Vault resolution: {problem}")
        return None
    return Path(resolved["root"])


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
