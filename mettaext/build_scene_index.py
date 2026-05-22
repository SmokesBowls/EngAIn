#!/usr/bin/env python3
"""
build_scene_index.py — Filename-Agnostic Scene Index Builder

Scans mettaext/loaded/ for all JSON scene files, reads internal metadata
from each file's own structure (not its filename), and writes a unified
scene_index.json routing table for Godot's UI Chooser.

Two schemas are handled:
  - Old format:  {scene_id, description, locations, metadata, ...}
  - Zonj format: {id, type, segments, source_files}
"""

import json
import os
import re
import glob
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
LOADED_DIR = SCRIPT_DIR / "loaded"
OUTPUT_PATH = LOADED_DIR / "scene_index.json"

# ---------------------------------------------------------------------------
# Terrain keyword scoring — applied to the first 40 narration/dialogue lines
# ---------------------------------------------------------------------------
TERRAIN_KEYWORDS: dict[str, list[str]] = {
    "beach":    ["beach", "shore", "sand", "ocean", "sea", "wave", "coast", "tide", "dune"],
    "shadow":   ["shadow", "twilight", "dark", "night", "void", "abyss", "umbra", "gloom", "dusk"],
    "grass":    ["grass", "meadow", "plain", "field", "pasture", "prairie", "steppe", "savanna"],
    "volcanic": ["molten", "lava", "volcanic", "magma", "crater", "eruption", "pyroclast", "flame", "smelt"],
    "ethereal": ["ethereal", "cosmic", "astral", "dimensional", "spirit", "consciousness", "vrill", "probability"],
    "forest":   ["forest", "jungle", "tree", "grove", "canopy", "vine", "fern", "undergrowth", "foliage"],
    "mountain": ["mountain", "peak", "cliff", "glacier", "ice", "snow", "highland", "summit", "ridge"],
    "desert":   ["desert", "arid", "wasteland", "badland", "dust", "parched", "baked", "mirage"],
    "city":     ["city", "urban", "street", "building", "tower", "spire", "district", "metropolis"],
    "ocean":    ["ocean", "deep", "abyss", "current", "tidal", "submerged", "aquatic", "pressure"],
}

# Minimum keyword hit count before we trust the inferred terrain
TERRAIN_MIN_SCORE = 2


def infer_terrain_from_text(text_blob: str) -> str:
    text = text_blob.lower()
    scores = {t: sum(text.count(k) for k in kws) for t, kws in TERRAIN_KEYWORDS.items()}
    best_terrain = max(scores, key=scores.get)
    return best_terrain if scores[best_terrain] >= TERRAIN_MIN_SCORE else "unknown"


def terrain_from_path(path_str: str) -> str:
    """Extract terrain from a 'Realm/Physical/Beach' style path."""
    if not path_str or path_str.lower().endswith("unknown"):
        return "unknown"
    family = path_str.split("/")[-1].lower()
    return family if family else "unknown"


# ---------------------------------------------------------------------------
# Title helpers
# ---------------------------------------------------------------------------
CHAPTER_HEADING_RE = re.compile(
    r"(?:book\s*[\w\-]+\s*[-—]?\s*)?"   # optional book prefix
    r"(?:chapter|ch\.?)\s*(\d+)"         # "Chapter N" or "Ch. N"
    r"(?:\s*[:\-—.]?\s*(.+))?",          # optional title (separator optional)
    re.IGNORECASE,
)

# Detects terminal/shell garbage accidentally compiled as scenes
SHELL_GARBAGE_RE = re.compile(r"@[\w\-]+:.*\$\s|python3\s+\w+\.py\b|Scenes:\s*\d+|Segments:\s*\d+")


def title_from_narration(segments: list[dict]) -> str | None:
    """
    Walk the first narration segments looking for a 'Chapter N: Title' heading.
    Returns None when no chapter heading is found (caller uses id-based fallback).
    """
    for seg in segments[:60]:
        if seg.get("type") != "narration":
            continue
        text = seg.get("text", "").strip()
        if not text or SHELL_GARBAGE_RE.search(text):
            continue
        m = CHAPTER_HEADING_RE.search(text)
        if m:
            ch_num = int(m.group(1))
            raw_title = (m.group(2) or "").strip()
            # strip trailing punctuation artifacts
            raw_title = raw_title.strip(".-—").strip()
            ch_title = raw_title.title() if raw_title else ""
            if ch_title:
                return f"Chapter {ch_num}: {ch_title}"
            return f"Chapter {ch_num}"
    return None


def title_from_id(raw_id: str) -> str:
    """
    Derive a human-readable title from an internal id string.
    'act_01ch_08_the_shattered_mind' → 'Chapter 8: The Shattered Mind'
    '03_Fist_contact'               → 'Chapter 3: First Contact'
    """
    # Try to extract chapter number
    ch_match = re.search(r"(?:ch[_.]?|chapter[_.]?)0*(\d+)", raw_id, re.IGNORECASE)
    if not ch_match:
        ch_match = re.match(r"^0*(\d+)", raw_id)

    title_slug = raw_id
    # Remove known prefixes/suffixes to isolate the title words
    title_slug = re.sub(
        r"^(act_\d+ch_?\d+|fact_\d+ch_?\d+|b\d+act\d+ch\d+|chapter_?\d+|ch_?\d+|\d+)_?",
        "", title_slug, flags=re.IGNORECASE,
    )
    title_slug = title_slug.strip("_- ").replace("_", " ").title()

    if ch_match:
        ch_num = int(ch_match.group(1))
        if title_slug:
            return f"Chapter {ch_num}: {title_slug}"
        return f"Chapter {ch_num}"
    return title_slug or raw_id.replace("_", " ").title()


# ---------------------------------------------------------------------------
# Per-file extraction
# ---------------------------------------------------------------------------

def extract_old_format(data: dict, file_path: str) -> dict | None:
    """Schema: {scene_id, description, entities, locations, metadata, ...}"""
    raw_id = data.get("scene_id", "").strip()
    if not raw_id:
        return None

    description = data.get("description", "").strip()
    meta = data.get("metadata", {})
    locations = data.get("locations", [])

    # Title: description often contains "Chapter N: Title"
    display_title = ""
    if description:
        m = CHAPTER_HEADING_RE.search(description)
        if m:
            ch_num = int(m.group(1))
            ch_title = (m.group(2) or "").strip().title() if m.group(2) else ""
            display_title = f"Chapter {ch_num}: {ch_title}" if ch_title else f"Chapter {ch_num}"
    if not display_title:
        display_title = title_from_id(raw_id)

    # Terrain
    terrain = "unknown"
    if locations:
        loc_id = locations[0].get("id", "")
        loc_path = locations[0].get("path", "")
        terrain = terrain_from_path(loc_path) if loc_id in ("", "unknown") else loc_id.lower()

    where = meta.get("where", "Realm/Physical/Unknown")
    when = meta.get("when", f"Unknown.{raw_id}")

    return {
        "internal_id": raw_id,
        "display_title": display_title,
        "cache_file_path": file_path,
        "terrain_family": terrain,
        "where": where,
        "when": when,
    }


def extract_zonj_format(data: dict, file_path: str) -> dict | None:
    """Schema: {id, type, segments, source_files}"""
    raw_id = data.get("id", "").strip()
    if not raw_id:
        return None

    segments = data.get("segments", [])

    # Skip files whose content is shell/terminal output rather than story text
    first_texts = [s.get("text", "") for s in segments[:4] if s.get("type") == "narration"]
    if any(SHELL_GARBAGE_RE.search(t) for t in first_texts):
        print(f"  SKIP (shell garbage content) {os.path.basename(file_path)}", file=sys.stderr)
        return None

    display_title = title_from_narration(segments) or title_from_id(raw_id)

    # Collect text from first 40 non-blank content segments for terrain inference
    text_blob = " ".join(
        seg.get("text", "")
        for seg in segments[:40]
        if seg.get("type") in ("narration", "dialogue") and seg.get("text", "").strip()
    )
    terrain = infer_terrain_from_text(text_blob)

    where = f"Realm/Physical/{terrain.title()}" if terrain != "unknown" else "Realm/Physical/Unknown"
    when = f"Unknown.{raw_id}"

    return {
        "internal_id": raw_id,
        "display_title": display_title,
        "cache_file_path": file_path,
        "terrain_family": terrain,
        "where": where,
        "when": when,
    }


# ---------------------------------------------------------------------------
# Schema detection
# ---------------------------------------------------------------------------

def extract_entry(data: dict, file_path: str) -> dict | None:
    top_keys = set(data.keys())
    if "scene_id" in top_keys and "segments" not in top_keys:
        return extract_old_format(data, file_path)
    if "id" in top_keys and "segments" in top_keys:
        return extract_zonj_format(data, file_path)
    # Unknown schema — try both
    result = extract_old_format(data, file_path)
    return result or extract_zonj_format(data, file_path)


# ---------------------------------------------------------------------------
# scene_id formatter
# ---------------------------------------------------------------------------

def make_scene_id(internal_id: str) -> str:
    """
    Produce a stable, storage-agnostic scene_id string.
    Try to embed the padded chapter number for easy sorting.
    'act_01ch_08_the_shattered_mind' → 'scene.008_the_shattered_mind'
    '01_the_ethereal_vigil'          → 'scene.001_the_ethereal_vigil'
    'chapter_54'                     → 'scene.054'
    """
    raw = internal_id.lower()

    # Extract chapter number
    ch_match = re.search(r"(?:ch[_.]?|chapter[_.]?)0*(\d+)", raw)
    if not ch_match:
        ch_match = re.match(r"^0*(\d+)", raw)

    # Extract title slug (everything after chapter number)
    title_slug = raw
    title_slug = re.sub(
        r"^(act_\d+ch_?\d+_?|fact_\d+ch_?\d+_?|b\d+act\d+ch\d+_?|chapter_?\d+_?|ch_?\d+_?|\d+_?)",
        "", title_slug,
    )
    title_slug = title_slug.strip("_- ")

    if ch_match:
        ch_num = int(ch_match.group(1))
        if title_slug:
            # Normalize spaces and non-word chars to underscores
            slug = re.sub(r"[^a-z0-9]+", "_", title_slug).strip("_")
            return f"scene.{ch_num:03d}_{slug}"
        return f"scene.{ch_num:03d}"

    # Fallback: just normalize the raw id
    normalized = re.sub(r"[^a-z0-9_]", "_", raw).strip("_")
    return f"scene.{normalized}"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def build_index() -> int:
    if not LOADED_DIR.exists():
        print(f"ERROR: loaded/ directory not found: {LOADED_DIR}", file=sys.stderr)
        return 1

    json_files = sorted(LOADED_DIR.glob("*.json"))
    # Exclude the output file itself
    json_files = [f for f in json_files if f.name != "scene_index.json"]

    print(f"Scanning {len(json_files)} JSON files in {LOADED_DIR}")

    # Map: scene_id → (entry, mtime)  — deduplication keeps newest mtime
    seen: dict[str, tuple[dict, float]] = {}
    parse_errors = 0

    for json_path in json_files:
        try:
            with open(json_path, encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"  SKIP (parse error) {json_path.name}: {e}", file=sys.stderr)
            parse_errors += 1
            continue

        entry = extract_entry(data, str(json_path))
        if entry is None:
            print(f"  SKIP (unrecognized schema) {json_path.name}", file=sys.stderr)
            continue

        scene_id = make_scene_id(entry["internal_id"])
        mtime = json_path.stat().st_mtime

        if scene_id in seen:
            _, existing_mtime = seen[scene_id]
            if mtime <= existing_mtime:
                print(f"  DUP  (older) {json_path.name} → {scene_id}")
                continue
            print(f"  DUP  (newer replaces older) {json_path.name} → {scene_id}")

        seen[scene_id] = (entry, mtime)

    # Build output sorted by scene_id
    active_scenes = []
    for scene_id, (entry, _) in sorted(seen.items()):
        active_scenes.append({
            "scene_id": scene_id,
            "display_title": entry["display_title"],
            "cache_file_path": entry["cache_file_path"],
            "terrain_family": entry["terrain_family"],
            "where": entry["where"],
            "when": entry["when"],
        })

    output = {"active_scenes": active_scenes}

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nWrote {len(active_scenes)} scenes → {OUTPUT_PATH}")
    if parse_errors:
        print(f"  ({parse_errors} files skipped due to parse errors)")

    # Quick summary
    terrain_counts: dict[str, int] = {}
    for sc in active_scenes:
        t = sc["terrain_family"]
        terrain_counts[t] = terrain_counts.get(t, 0) + 1

    print("\nTerrain breakdown:")
    for t, count in sorted(terrain_counts.items(), key=lambda x: -x[1]):
        print(f"  {t:15s} {count}")

    return 0


if __name__ == "__main__":
    sys.exit(build_index())
