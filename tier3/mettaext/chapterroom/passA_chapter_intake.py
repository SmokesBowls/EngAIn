#!/usr/bin/env python3
"""
passA_chapter_intake.py  –  EngAIn Chapterroom · Pass A

ROLE: Chapter Intake
  Reads a raw chapter text file and produces a chapter identity manifest.

WHAT IT DOES:
  - Assigns a canonical chapter_id from filename or @chapter tag
  - Detects chapter-level metadata (title, book, era hints)
  - Counts rough line/word metrics
  - Sets authority_state: CHAPTER_RECEIVED
  - Writes:  out_passA_<stem>.json

DOES NOT:
  - Split scenes (that is Pass B's job)
  - Infer character details (that is the passroom's job)

CONTRACT OUT:
  engain.chapter_intake_manifest.v1
  {
    "contract":    "engain.chapter_intake_manifest.v1",
    "authority_state": "CHAPTER_RECEIVED",
    "chapter_id":  "chapter.058_paradox_engine",
    "source_file": "/abs/path/to/file.txt",
    "title":       "The Paradox Engine",
    "book_hint":   "book010",
    "era_hint":    "",
    "line_count":  342,
    "word_count":  4821,
    "raw_text":    "..."        # full chapter text
  }
"""

import argparse
import json
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Metadata extraction helpers
# ---------------------------------------------------------------------------

_TAG_RE    = re.compile(r"^@(\w[\w_-]*)\s*[:\s]\s*(.*)$", re.MULTILINE)
_HEADING_RE = re.compile(
    r"^(?:#{1,6}\s*)?(?:chapter|ch\.?)\s*[\d]+[:\.\s–\-]*(.+)$",
    re.IGNORECASE | re.MULTILINE,
)
_BOOK_RE   = re.compile(r"book\s*0*(\d+)", re.IGNORECASE)
_CHNUM_RE  = re.compile(r"(?:chapter|ch)[\s._-]*0*(\d+)", re.IGNORECASE)


def _slug(text: str) -> str:
    """Lowercase, replace non-alnum with underscores, collapse runs."""
    s = re.sub(r"[^a-z0-9]+", "_", text.lower().strip())
    return s.strip("_")


def _detect_tags(raw: str) -> dict:
    """Pull @key value pairs from the raw text."""
    tags = {}
    for m in _TAG_RE.finditer(raw):
        tags[m.group(1).lower()] = m.group(2).strip()
    return tags


def _detect_title(raw: str, tags: dict, stem: str) -> str:
    """Best-effort chapter title."""
    if "title" in tags:
        return tags["title"]
    if "chapter" in tags:
        return tags["chapter"]
    m = _HEADING_RE.search(raw[:2000])
    if m:
        return m.group(1).strip().rstrip(".")
    # Fall back to stem humanisation
    return stem.replace("_", " ").title()


def _detect_chapter_id(raw: str, tags: dict, stem: str) -> str:
    """Produce chapter.<book_hint><chapter_num>_<slug> or chapter.<stem>."""
    # Explicit tag wins
    if "chapter_id" in tags:
        cid = tags["chapter_id"]
        return cid if cid.startswith("chapter.") else f"chapter.{cid}"

    book_part = ""
    bm = _BOOK_RE.search(raw[:1000]) or _BOOK_RE.search(stem)
    if bm:
        book_part = f"book{int(bm.group(1)):03d}."

    ch_part = ""
    cm = _CHNUM_RE.search(raw[:1000]) or _CHNUM_RE.search(stem)
    if cm:
        ch_part = f"{int(cm.group(1)):03d}_"

    # Slug priority:
    # 1. Chapter heading title, e.g. "# Chapter 999: ABC Smoke" -> abc_smoke
    # 2. Filename stem cleaned of chapter prefix
    heading = _HEADING_RE.search(raw[:2000])
    if heading:
        slug_source = heading.group(1).strip().rstrip(".")
    else:
        slug_source = re.sub(
            r"^(?:b\d+_?)?(?:ch(?:apter)?_?)?0*\d+[_\-\.\s]*",
            "",
            stem,
            flags=re.IGNORECASE,
        )

    slug_part = _slug(slug_source) if slug_source.strip() else _slug(stem)

    return f"chapter.{book_part}{ch_part}{slug_part}" if slug_part else f"chapter.{book_part}{ch_part[:-1]}"


def _detect_era(tags: dict, raw: str) -> str:
    if "era" in tags:
        return tags["era"]
    if "age" in tags:
        return tags["age"]
    # Common era keywords in the first 500 chars
    era_hints = re.findall(
        r"\b(FirstAge|ModernEra|AncientEra|FinalAge|DarkAge|GoldenAge)\b",
        raw[:500],
        re.IGNORECASE,
    )
    return era_hints[0] if era_hints else ""


def _detect_book_hint(raw: str, stem: str) -> str:
    bm = _BOOK_RE.search(raw[:1000]) or _BOOK_RE.search(stem)
    if bm:
        return f"book{int(bm.group(1)):03d}"
    return ""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def intake(input_path: Path, output_path: Path | None) -> dict:
    raw = input_path.read_text(encoding="utf-8")
    stem = input_path.stem

    tags        = _detect_tags(raw)
    title       = _detect_title(raw, tags, stem)
    chapter_id  = _detect_chapter_id(raw, tags, stem)
    era_hint    = _detect_era(tags, raw)
    book_hint   = _detect_book_hint(raw, stem)
    lines       = raw.splitlines()
    word_count  = len(raw.split())

    manifest = {
        "contract":        "engain.chapter_intake_manifest.v1",
        "authority_state": "CHAPTER_RECEIVED",
        "chapter_id":      chapter_id,
        "source_file":     str(input_path.resolve()),
        "title":           title,
        "book_hint":       book_hint,
        "era_hint":        era_hint,
        "line_count":      len(lines),
        "word_count":      word_count,
        "raw_text":        raw,
    }

    if output_path is None:
        output_path = input_path.parent / f"out_passA_{stem}.json"

    output_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest


def main():
    parser = argparse.ArgumentParser(
        description="EngAIn Chapterroom · Pass A – Chapter Intake"
    )
    parser.add_argument("input", help="Raw chapter .txt or .md file")
    parser.add_argument("--output", "-o", default=None,
                        help="Destination JSON manifest (default: out_passA_<stem>.json)")
    args = parser.parse_args()

    in_path  = Path(args.input)
    out_path = Path(args.output) if args.output else None

    if not in_path.exists():
        print(f"❌ File not found: {in_path}", file=sys.stderr)
        sys.exit(1)

    m = intake(in_path, out_path)

    out_actual = out_path or (in_path.parent / f"out_passA_{in_path.stem}.json")
    print(f"✅ Pass A complete")
    print(f"   chapter_id  : {m['chapter_id']}")
    print(f"   title       : {m['title']}")
    print(f"   book_hint   : {m['book_hint'] or '(none detected)'}")
    print(f"   era_hint    : {m['era_hint'] or '(none detected)'}")
    print(f"   lines/words : {m['line_count']} / {m['word_count']}")
    print(f"   → {out_actual}")


if __name__ == "__main__":
    main()
