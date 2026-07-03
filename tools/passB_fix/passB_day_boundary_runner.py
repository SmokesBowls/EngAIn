#!/usr/bin/env python3
from __future__ import annotations

"""
Pass B scene-boundary repair runner.

Purpose:
    Read existing out_passA_*.json files and produce corrected Pass B scene splits.

Fix:
    Detect italic/bold Day subheadings such as:
        *Day 46 - The Final Breath*
        **Day 47 – The Hidden Resonance**
        _Day 3: The Road Through Discord_
    after explicit @scene tags and markdown ## headings, but before mechanical word chunks.

Safety:
    This script does not modify existing Pass A or Pass B files.
    It writes new files into a proof/output directory.

Default repo:
    /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn
"""

import argparse
import csv
import datetime as dt
import hashlib
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Iterable


SCRIPT_NAME = "passB_day_boundary_runner"
DEFAULT_REPO = Path("/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn")
DEFAULT_OUTDIR = Path("scratch/passB_day_boundary_fix")

# Explicit scene tags should win when already authored.
SCENE_TAG_RE = re.compile(
    r"^\s*@scene(?:\s*[:\-]\s*|\s+)(?P<title>.+?)\s*$",
    re.IGNORECASE,
)

# Normal markdown scene headings. We intentionally use ## and deeper, not #, because # is often chapter title.
MARKDOWN_SCENE_HEADING_RE = re.compile(
    r"^\s{0,3}#{2,6}\s+(?P<title>\S.+?)\s*$",
    re.IGNORECASE,
)

# The verified missing convention: italic/bold Day subheadings.
# Supports: *Day 46 - Title*, **Day 46 – Title**, _Day 46: Title_, ***Day 46 — Title***.
DAY_SUBHEADING_RE = re.compile(
    r"^\s{0,3}"
    r"(?P<open>[_*]{1,3})?"
    r"\s*"
    r"(?P<title>Day\s+\d+(?:\s*(?:-|–|—|:)\s*[^*_#\n]+)?)"
    r"\s*"
    r"(?P<close>[_*]{1,3})?"
    r"\s*$",
    re.IGNORECASE,
)

# Last-resort fallback, intentionally obvious in audit output.
DEFAULT_CHUNK_WORDS = 1800
MIN_PREFACE_WORDS = 80

PREFERRED_TEXT_KEYS = (
    "chapter_text",
    "full_text",
    "source_text",
    "raw_text",
    "markdown",
    "content",
    "body",
    "text",
)


@dataclass
class Boundary:
    line_index: int
    char_offset: int
    title: str
    detector: str
    raw_line: str


@dataclass
class Scene:
    scene_index: int
    scene_id: str
    title: str
    boundary_type: str
    start_line: int
    end_line: int
    start_char: int
    end_char: int
    word_count: int
    text: str


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def word_count(text: str) -> int:
    return len(re.findall(r"\b\S+\b", text))


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "scene"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8", errors="replace") as f:
        return json.load(f)


def iter_string_fields(obj: Any, path: tuple[str, ...] = ()) -> Iterable[tuple[tuple[str, ...], str]]:
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield from iter_string_fields(value, path + (str(key),))
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            yield from iter_string_fields(value, path + (str(index),))
    elif isinstance(obj, str):
        yield path, obj


def extract_text_from_passA(obj: Any) -> tuple[str, str]:
    """
    Extract chapter text from unknown Pass A JSON shape.

    Returns:
        (text, source_path_inside_json)

    Strategy:
        1. Prefer known text-bearing keys.
        2. Fall back to the longest multiline string.
        3. Fail closed if no plausible text exists.
    """
    candidates: list[tuple[int, int, tuple[str, ...], str]] = []

    for path, value in iter_string_fields(obj):
        if not value.strip():
            continue
        line_count = value.count("\n") + 1
        wc = word_count(value)
        key = path[-1].lower() if path else ""
        key_score = 100000 if key in PREFERRED_TEXT_KEYS else 0
        multiline_score = 10000 if line_count >= 5 else 0
        # Favor word count, but allow preferred keys to dominate similarly sized metadata strings.
        score = key_score + multiline_score + wc
        candidates.append((score, wc, path, value))

    if not candidates:
        raise ValueError("No string fields found in Pass A JSON.")

    candidates.sort(key=lambda row: row[0], reverse=True)
    _score, wc, path, text = candidates[0]

    if wc < 50:
        raise ValueError(
            f"No plausible chapter text found. Best string field was {'.'.join(path)} with only {wc} words."
        )

    return text, ".".join(path)


def line_start_offsets(text: str) -> list[int]:
    offsets = []
    cursor = 0
    for line in text.splitlines(keepends=True):
        offsets.append(cursor)
        cursor += len(line)
    if not offsets:
        offsets.append(0)
    return offsets


def strip_markdown_wrapping(title: str) -> str:
    title = title.strip()
    # Remove symmetrical emphasis wrappers without destroying inner punctuation.
    for wrapper in ("***", "**", "*", "___", "__", "_"):
        if title.startswith(wrapper) and title.endswith(wrapper) and len(title) > 2 * len(wrapper):
            title = title[len(wrapper) : -len(wrapper)].strip()
    return title


def find_boundaries(text: str, detector_name: str, regex: re.Pattern[str]) -> list[Boundary]:
    offsets = line_start_offsets(text)
    lines = text.splitlines()
    boundaries: list[Boundary] = []

    for i, line in enumerate(lines):
        m = regex.match(line)
        if not m:
            continue
        title = strip_markdown_wrapping(m.group("title"))
        if not title:
            continue
        boundaries.append(
            Boundary(
                line_index=i,
                char_offset=offsets[i] if i < len(offsets) else 0,
                title=title,
                detector=detector_name,
                raw_line=line,
            )
        )

    return boundaries


def choose_boundaries(text: str) -> tuple[str, list[Boundary]]:
    """
    Boundary precedence:
        1. @scene explicit tags
        2. Markdown ##+ headings
        3. Day N subheadings, including italic/bold markdown wrappers
        4. Mechanical chunk fallback
    """
    explicit = find_boundaries(text, "scene_tag", SCENE_TAG_RE)
    if explicit:
        return "scene_tag", explicit

    headings = find_boundaries(text, "markdown_heading", MARKDOWN_SCENE_HEADING_RE)
    if headings:
        return "markdown_heading", headings

    day_headings = find_boundaries(text, "day_subheading", DAY_SUBHEADING_RE)
    if day_headings:
        return "day_subheading", day_headings

    return "mechanical_word_chunk", []


def split_by_boundaries(text: str, boundaries: list[Boundary], source_stem: str) -> list[Scene]:
    offsets = line_start_offsets(text)
    lines = text.splitlines()
    scenes: list[Scene] = []

    # If there is substantial prose before the first boundary, preserve it as a preface scene.
    first = boundaries[0]
    preface = text[: first.char_offset].strip()
    starts_with_preface = word_count(preface) >= MIN_PREFACE_WORDS

    scene_ranges: list[tuple[str, str, int, int, int, int]] = []

    if starts_with_preface:
        scene_ranges.append(
            (
                "preface",
                "preface_before_first_boundary",
                0,
                max(0, first.line_index - 1),
                0,
                first.char_offset,
            )
        )

    for index, boundary in enumerate(boundaries):
        next_boundary = boundaries[index + 1] if index + 1 < len(boundaries) else None
        start_char = boundary.char_offset
        end_char = next_boundary.char_offset if next_boundary else len(text)
        start_line = boundary.line_index
        end_line = (next_boundary.line_index - 1) if next_boundary else max(0, len(lines) - 1)
        scene_ranges.append(
            (
                boundary.title,
                boundary.detector,
                start_line,
                end_line,
                start_char,
                end_char,
            )
        )

    for idx, (title, detector, start_line, end_line, start_char, end_char) in enumerate(scene_ranges, start=1):
        scene_text = text[start_char:end_char].strip()
        if not scene_text:
            continue
        scene_id = f"{source_stem}.scene_{idx:03d}.{slugify(title)[:60]}"
        scenes.append(
            Scene(
                scene_index=len(scenes) + 1,
                scene_id=scene_id,
                title=title,
                boundary_type=detector,
                start_line=start_line + 1,
                end_line=end_line + 1,
                start_char=start_char,
                end_char=end_char,
                word_count=word_count(scene_text),
                text=scene_text,
            )
        )

    return scenes


def split_mechanically(text: str, source_stem: str, chunk_words: int = DEFAULT_CHUNK_WORDS) -> list[Scene]:
    words = list(re.finditer(r"\S+", text))
    if not words:
        return []

    scenes: list[Scene] = []
    line_offsets = line_start_offsets(text)

    def line_for_char(char_offset: int) -> int:
        # Small file counts here; simple scan is readable and fine.
        line_no = 1
        for i, start in enumerate(line_offsets):
            if start <= char_offset:
                line_no = i + 1
            else:
                break
        return line_no

    for chunk_index, start_word in enumerate(range(0, len(words), chunk_words), start=1):
        end_word = min(start_word + chunk_words, len(words))
        start_char = words[start_word].start()
        end_char = words[end_word - 1].end()
        scene_text = text[start_char:end_char].strip()
        title = f"mechanical_word_chunk_{chunk_index:03d}"
        scenes.append(
            Scene(
                scene_index=chunk_index,
                scene_id=f"{source_stem}.scene_{chunk_index:03d}.{title}",
                title=title,
                boundary_type="mechanical_word_chunk",
                start_line=line_for_char(start_char),
                end_line=line_for_char(end_char),
                start_char=start_char,
                end_char=end_char,
                word_count=word_count(scene_text),
                text=scene_text,
            )
        )

    return scenes


def split_scenes_from_passA(passA_path: Path, output_dir: Path, chunk_words: int) -> dict[str, Any]:
    obj = load_json(passA_path)
    text, text_json_path = extract_text_from_passA(obj)
    mode, boundaries = choose_boundaries(text)
    source_stem = passA_path.stem.replace("out_passA_", "")

    if boundaries:
        scenes = split_by_boundaries(text, boundaries, source_stem)
    else:
        scenes = split_mechanically(text, source_stem, chunk_words=chunk_words)

    out = {
        "contract": "passB.scene_split.v2.day_boundary_fix",
        "source": SCRIPT_NAME,
        "created_at": dt.datetime.now().isoformat(timespec="seconds"),
        "input_passA_path": str(passA_path),
        "input_passA_sha256": sha256_file(passA_path),
        "input_text_json_path": text_json_path,
        "input_text_sha256": sha256_text(text),
        "split_mode": mode,
        "boundary_count": len(boundaries),
        "scene_count": len(scenes),
        "boundaries": [asdict(b) for b in boundaries],
        "scenes": [asdict(s) for s in scenes],
        "gates": {
            "passA_read": True,
            "text_extracted": True,
            "scene_count_gt_zero": len(scenes) > 0,
            "mechanical_fallback_used": mode == "mechanical_word_chunk",
            "day_boundary_fix_used": mode == "day_subheading",
        },
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"out_passB_dayfix_{source_stem}.json"
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

    return {
        "passA_path": str(passA_path),
        "out_path": str(out_path),
        "split_mode": mode,
        "boundary_count": len(boundaries),
        "scene_count": len(scenes),
        "word_count": word_count(text),
        "text_json_path": text_json_path,
        "status": "TRUE" if scenes else "FALSE",
    }


def find_passA_files(repo: Path, glob_pattern: str) -> list[Path]:
    return sorted(p for p in repo.rglob(glob_pattern) if p.is_file())


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Pass B day-boundary fix over existing out_passA_*.json files.")
    parser.add_argument("--repo", default=str(DEFAULT_REPO), help="Repo root path.")
    parser.add_argument("--glob", default="out_passA_*.json", help="Pass A filename glob to search recursively.")
    parser.add_argument("--outdir", default=str(DEFAULT_OUTDIR), help="Output dir, relative to repo unless absolute.")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of files for smoke test. 0 means all.")
    parser.add_argument("--chunk-words", type=int, default=DEFAULT_CHUNK_WORDS, help="Mechanical fallback chunk size.")
    parser.add_argument("--fail-on-fallback", action="store_true", help="Return nonzero if any file still needs mechanical fallback.")
    args = parser.parse_args()

    repo = Path(args.repo).expanduser().resolve()
    if not repo.exists():
        print(f"[{SCRIPT_NAME}][GATE_REPO_EXISTS] FALSE: {repo}")
        return 2
    print(f"[{SCRIPT_NAME}][GATE_REPO_EXISTS] TRUE: {repo}")

    outdir = Path(args.outdir).expanduser()
    if not outdir.is_absolute():
        outdir = repo / outdir
    outdir.mkdir(parents=True, exist_ok=True)

    passA_files = find_passA_files(repo, args.glob)
    if args.limit and args.limit > 0:
        passA_files = passA_files[: args.limit]

    if not passA_files:
        print(f"[{SCRIPT_NAME}][GATE_PASSA_FILES_FOUND] FALSE: no files matched {args.glob}")
        return 2
    print(f"[{SCRIPT_NAME}][GATE_PASSA_FILES_FOUND] TRUE: {len(passA_files)} files")

    rows: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []

    for path in passA_files:
        try:
            row = split_scenes_from_passA(path, outdir / "passB_outputs", chunk_words=args.chunk_words)
            rows.append(row)
            print(
                f"[{SCRIPT_NAME}][SPLIT] {row['status']}: {path.name} "
                f"mode={row['split_mode']} scenes={row['scene_count']} boundaries={row['boundary_count']}"
            )
        except Exception as e:
            fail = {
                "passA_path": str(path),
                "status": "FALSE",
                "error": f"{type(e).__name__}: {e}",
            }
            failures.append(fail)
            rows.append(fail)
            print(f"[{SCRIPT_NAME}][SPLIT] FALSE: {path.name} error={type(e).__name__}: {e}")

    summary: dict[str, Any] = {
        "contract": "passB.day_boundary_fix.audit.v1",
        "source": SCRIPT_NAME,
        "created_at": dt.datetime.now().isoformat(timespec="seconds"),
        "repo": str(repo),
        "glob": args.glob,
        "file_count": len(passA_files),
        "failure_count": len(failures),
        "mode_counts": {},
        "rows": rows,
        "failures": failures,
    }

    for row in rows:
        mode = row.get("split_mode", "ERROR")
        summary["mode_counts"][mode] = summary["mode_counts"].get(mode, 0) + 1

    audit_json = outdir / "PASSB_DAY_BOUNDARY_FIX_AUDIT.json"
    audit_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    audit_csv = outdir / "PASSB_DAY_BOUNDARY_FIX_AUDIT.csv"
    with audit_csv.open("w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "status",
            "split_mode",
            "scene_count",
            "boundary_count",
            "word_count",
            "passA_path",
            "out_path",
            "text_json_path",
            "error",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})

    fallback_count = summary["mode_counts"].get("mechanical_word_chunk", 0)
    day_count = summary["mode_counts"].get("day_subheading", 0)
    heading_count = summary["mode_counts"].get("markdown_heading", 0)
    scene_tag_count = summary["mode_counts"].get("scene_tag", 0)

    print(f"[{SCRIPT_NAME}][SUMMARY] files={len(passA_files)} failures={len(failures)}")
    print(
        f"[{SCRIPT_NAME}][SUMMARY] scene_tag={scene_tag_count} "
        f"markdown_heading={heading_count} day_subheading={day_count} mechanical_fallback={fallback_count}"
    )
    print(f"[{SCRIPT_NAME}][AUDIT_JSON] {audit_json}")
    print(f"[{SCRIPT_NAME}][AUDIT_CSV] {audit_csv}")

    all_ok = len(failures) == 0 and (fallback_count == 0 or not args.fail_on_fallback)
    print(f"[{SCRIPT_NAME}][ALL_GATES] {str(all_ok).lower()}")

    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
