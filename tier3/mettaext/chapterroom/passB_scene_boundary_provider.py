#!/usr/bin/env python3
"""
Pass B — Scene Boundary Provider

Reads a Pass A chapter manifest and proposes scene boundaries.
Does not prove authored canon boundaries by itself.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple


def clean_scene_text(lines: List[str]) -> str:
    text = "\n".join(lines).strip()
    return text + "\n" if text else ""


def build_scene_id(chapter_id: str, index: int) -> str:
    base = chapter_id.replace("chapter.", "", 1)
    return f"scene.{base}.scene{index:03d}"


_SCENE_MARKER_RE = re.compile(
    r'^scene\s+(?P<num>\d+)\.(?P<sub>\d+)\s+[—-]\s+(?P<title>.+)$',
    re.IGNORECASE,
)
_SCENE_META_HEADER_RE = re.compile(r'^scene meta:\s*$', re.IGNORECASE)
_SCENE_META_FIELD_RE = re.compile(r'^([A-Za-z][A-Za-z _]*):\s*(.*)$')


def _parse_scene_meta(lines: List[str], meta_header_idx: int, limit: int) -> Dict[str, str]:
    """Parse a generic key:value scene meta: block.

    meta_header_idx must be the index of the 'scene meta:' line itself.
    Consumes consecutive non-blank 'key: value' lines after it, stopping
    at the first blank line, the first non-matching line, or `limit`
    (this scene's own end boundary) -- whichever comes first. No
    specific keys are assumed; unrecognized/future keys (e.g.
    'presentation', 'cutscene purpose') are preserved exactly as
    written. `time:` and every other value are stored as opaque
    strings -- no calendar/date interpretation happens here.
    """
    meta: Dict[str, str] = {}
    i = meta_header_idx + 1
    while i < limit:
        line = lines[i]
        if not line.strip():
            break
        m = _SCENE_META_FIELD_RE.match(line.strip())
        if not m:
            break
        key, value = m.group(1).strip(), m.group(2).strip()
        if key:
            meta[key] = value
        i += 1
    return meta


def split_by_authored_scene_markers(
    lines: List[str],
) -> List[Tuple[int, int, str, Dict[str, str]]]:
    """Split on explicit authored 'scene NNN.x — <title>' markers.

    This is the authoritative boundary source when present -- checked
    before every heuristic/mechanical method. Each marker starts
    exactly one scene; its immediately following 'scene meta:' block
    (if any) is parsed generically into a dict and returned alongside
    the scene's boundaries.

    The raw scene meta: lines (and everything else) are NOT stripped
    out of the scene's text -- Pass 2's manifestation inference
    (infer_presence_enhanced) depends on finding 'participants:' by
    scanning segment text directly, so the text a caller gets here
    must keep carrying it verbatim, in addition to the structured dict.

    Legacy 'day N' lines get no special handling -- they are not
    recognized as scene boundaries or folded into either neighboring
    scene specially. They simply fall wherever they land relative to
    the markers (trailing into the preceding scene's text, or excluded
    as chapter-level material if before the first marker) -- tolerated
    as harmless legacy noise, not formalized. See engain-avatar-audit's
    09-19-2026-scene-boundary-splitter-design-corrected-no-day-rule.md.
    """
    marker_indices = [
        i for i, line in enumerate(lines) if _SCENE_MARKER_RE.match(line.strip())
    ]
    if not marker_indices:
        return []

    chunks: List[Tuple[int, int, str, Dict[str, str]]] = []
    for pos, marker_idx in enumerate(marker_indices):
        start = marker_idx
        end = marker_indices[pos + 1] if pos + 1 < len(marker_indices) else len(lines)

        scene_meta: Dict[str, str] = {}
        probe = marker_idx + 1
        while probe < end and not lines[probe].strip():
            probe += 1
        if probe < end and _SCENE_META_HEADER_RE.match(lines[probe].strip()):
            scene_meta = _parse_scene_meta(lines, probe, end)

        text = clean_scene_text(lines[start:end])
        if text:
            chunks.append((start + 1, end, text, scene_meta))

    return chunks


def split_by_scene_tags(lines: List[str]) -> List[Tuple[int, int, str]]:
    tag_lines = [i for i, line in enumerate(lines) if line.strip() == "@scene"]
    if not tag_lines:
        return []

    chunks: List[Tuple[int, int, str]] = []
    for pos, tag_idx in enumerate(tag_lines):
        start = tag_idx + 1
        end = tag_lines[pos + 1] if pos + 1 < len(tag_lines) else len(lines)
        text = clean_scene_text(lines[start:end])
        if text:
            chunks.append((start + 1, end, text))
    return chunks


def split_by_markdown_headings(lines: List[str]) -> List[Tuple[int, int, str]]:
    heading_lines = [
        i for i, line in enumerate(lines)
        if line.strip().startswith("##") and not line.strip().startswith("###")
    ]
    if not heading_lines:
        return []

    chunks: List[Tuple[int, int, str]] = []
    for pos, heading_idx in enumerate(heading_lines):
        start = heading_idx
        end = heading_lines[pos + 1] if pos + 1 < len(heading_lines) else len(lines)
        text = clean_scene_text(lines[start:end])
        if text:
            chunks.append((start + 1, end, text))
    return chunks


def split_by_double_blank(lines: List[str]) -> List[Tuple[int, int, str]]:
    chunks: List[Tuple[int, int, str]] = []
    current: List[str] = []
    start_line = 1
    blank_count = 0

    for idx, line in enumerate(lines, start=1):
        if not line.strip():
            blank_count += 1
        else:
            blank_count = 0

        if blank_count >= 2:
            text = clean_scene_text(current)
            if text:
                chunks.append((start_line, idx, text))
            current = []
            start_line = idx + 1
            blank_count = 0
            continue

        current.append(line)

    text = clean_scene_text(current)
    if text:
        chunks.append((start_line, len(lines), text))

    return chunks if len(chunks) > 1 else []


def split_mechanical_words(lines: List[str], target_words: int) -> List[Tuple[int, int, str]]:
    text_lines = [(i, line) for i, line in enumerate(lines, start=1)]
    chunks: List[Tuple[int, int, str]] = []
    current: List[str] = []
    current_start = 1
    word_count = 0

    for line_no, line in text_lines:
        if not current:
            current_start = line_no
        current.append(line)
        word_count += len(re.findall(r"\S+", line))

        if word_count >= target_words:
            chunks.append((current_start, line_no, clean_scene_text(current)))
            current = []
            word_count = 0

    if current:
        chunks.append((current_start, text_lines[-1][0] if text_lines else 1, clean_scene_text(current)))

    return chunks


def choose_boundaries(manifest: Dict[str, Any], target_words: int) -> Dict[str, Any]:
    raw_text = manifest.get("raw_text", "")
    lines = raw_text.splitlines()
    chapter_id = manifest["chapter_id"]

    method = "authored_scene_marker"
    authored_chunks = split_by_authored_scene_markers(lines)
    scene_metas: List[Dict[str, str]] = []

    if authored_chunks:
        chunks = [(s, e, t) for (s, e, t, _m) in authored_chunks]
        scene_metas = [m for (_s, _e, _t, m) in authored_chunks]
    else:
        method = "scene_tag"
        chunks = split_by_scene_tags(lines)

        if not chunks:
            method = "markdown_heading"
            chunks = split_by_markdown_headings(lines)

        if not chunks:
            method = "double_blank_cluster"
            chunks = split_by_double_blank(lines)

        if not chunks:
            method = "mechanical_word_chunk"
            chunks = split_mechanical_words(lines, target_words)

    authored = method == "authored_scene_marker"
    mechanical = method == "mechanical_word_chunk"

    if authored:
        overall_authority_state = "SCENE_BOUNDARY_AUTHORED"
    elif mechanical:
        overall_authority_state = "SCENE_BOUNDARY_MECHANICAL"
    else:
        overall_authority_state = "SCENE_BOUNDARY_PROPOSED"

    scenes = []
    for idx, (start_line, end_line, text) in enumerate(chunks, start=1):
        scene_entry = {
            "scene_index": idx,
            "scene_id": build_scene_id(chapter_id, idx),
            "chapter_id": chapter_id,
            "boundary_start_line": start_line,
            "boundary_end_line": end_line,
            "text": text,
            "boundary_method": method,
            "authority_state": overall_authority_state,
            "authored_scene_boundaries_proven": authored,
        }
        if scene_metas and scene_metas[idx - 1]:
            scene_entry["scene_meta"] = scene_metas[idx - 1]
        scenes.append(scene_entry)

    return {
        "contract": "engain.scene_boundary_proposal.v1",
        "authority_state": overall_authority_state,
        "chapter_id": chapter_id,
        "source_passA_contract": manifest.get("contract"),
        "boundary_method": method,
        "authored_scene_boundaries_proven": authored,
        "scene_count": len(scenes),
        "scenes": scenes,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Pass B: scene boundary provider.")
    parser.add_argument("passA_manifest", help="Pass A JSON manifest.")
    parser.add_argument("--output-dir", default=".", help="Directory for Pass B output.")
    parser.add_argument("--target-words", type=int, default=900, help="Mechanical fallback target words per scene.")
    args = parser.parse_args()

    input_path = Path(args.passA_manifest).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest = json.loads(input_path.read_text(encoding="utf-8"))
    proposal = choose_boundaries(manifest, args.target_words)

    safe_chapter = proposal["chapter_id"].replace("/", "_")
    out_path = output_dir / f"out_passB_{safe_chapter}.json"
    out_path.write_text(json.dumps(proposal, indent=2, ensure_ascii=False), encoding="utf-8")

    print("[PASS B] SCENE_BOUNDARY_PROVIDER_COMPLETE = TRUE")
    print(f"[PASS B] CHAPTER_ID = {proposal['chapter_id']}")
    print(f"[PASS B] BOUNDARY_METHOD = {proposal['boundary_method']}")
    print(f"[PASS B] SCENE_COUNT = {proposal['scene_count']}")
    print(f"[PASS B] WROTE = {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
