#!/usr/bin/env python3
"""
pass1_spatial.py — EngAIn Passroom · Pass 1 Spatial

ROLE: Spatial Signal Extractor

CONSUMES:
  pass1_explicit output: tagged lines
    {type:narration} The guard stood before the closed stone gate.

PRODUCES:
  out_pass1_spatial_<scene_stem>.json
  {
    "source_pass1": "...",
    "signal_count": N,
    "signals": [
      {
        "signal_id": "spatial_0001",
        "line": 1,
        "signal_type": "spatial_signal",
        "relation": "in_front_of",
        "source_text": "The guard stood before the closed stone gate.",
        "subject_hint": "guard",
        "object_hint": "stone gate",
        "confidence": 0.70,
        "topology_link_hint": "OLINK"
      }
    ]
  }

SIGNAL FAMILIES:
  spatial_signal     — positional relations (before, behind, near, within, …)
  movement_signal    — entity motion (approached, stood, entered, raised, …)
  obstruction_signal — barrier/blocking events (blocked, closed, barred, sealed, …)

DOES NOT:
  - Call the topologist bridge
  - Call Trixel, Blender, Mechanimation, or Godot
  - Mutate runtime
  - Depend on the Chronicles ontology gate
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Pass 1 tagged-line parser — TYPE_RE is the same shape as pass2_enhanced
# ---------------------------------------------------------------------------

TYPE_RE = re.compile(
    r'^\{type:(?P<type>[a-z_]+)'
    r'(?:,\s*speaker:(?P<speaker>[A-Za-z_]+))?'
    r'\}\s*(?P<text>.*)$'
)


def _load_pass1_units(path: Path) -> list[dict[str, Any]]:
    units: list[dict[str, Any]] = []
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        m = TYPE_RE.match(raw.strip())
        if not m:
            continue
        units.append({
            "line": line_no,
            "type": m.group("type"),
            "speaker": m.group("speaker"),
            "text": m.group("text") or "",
        })
    return units


# ---------------------------------------------------------------------------
# Sentence splitting
# ---------------------------------------------------------------------------

_SENT_SPLIT_RE = re.compile(r'(?<=[.!?])\s+')


def _split_sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENT_SPLIT_RE.split(text.strip()) if s.strip()]


# ---------------------------------------------------------------------------
# Subject / object hint extraction
# ---------------------------------------------------------------------------

_STOP_WORDS = frozenset({
    "the", "a", "an", "is", "was", "were", "are", "be", "been", "being",
    "to", "of", "in", "and", "but", "or", "so", "at", "on", "for", "with",
    "by", "from", "that", "this", "which", "who", "whom", "whose",
    "he", "she", "it", "they", "we", "i", "you", "his", "her", "its",
    "their", "our", "my", "your", "not", "no", "nor", "yet", "then",
    "had", "has", "have", "did", "do", "does", "one",
})

# Verbs to skip when scanning left for the subject noun.
# Without POS tagging these would otherwise surface as subject hints.
_VERB_SKIP = frozenset({
    "stood", "waited", "approached", "moved", "entered", "crossed",
    "retreated", "withdrew", "raised", "blocked", "closed", "barred",
    "sealed", "walked", "ran", "sat", "knelt", "turned", "came",
    "went", "held", "kept", "left", "found", "saw", "seemed",
    "said", "asked", "replied", "called", "told",
})


def _clean_word(word: str) -> str:
    return re.sub(r"[^a-zA-Z]", "", word).lower()


def _subject_hint(sentence: str, trigger_start: int) -> str | None:
    """Last meaningful word to the left of the trigger — skips stop words and verbs."""
    for word in reversed(sentence[:trigger_start].split()):
        clean = _clean_word(word)
        if clean and clean not in _STOP_WORDS and clean not in _VERB_SKIP:
            return clean
    return None


def _object_hint(sentence: str, trigger_end: int) -> str | None:
    """First NP to the right of the trigger.

    Collects content words until hitting a stop word after content has started,
    then returns the last two to capture compound nouns like 'stone gate'.
    """
    content: list[str] = []
    for word in sentence[trigger_end:].split():
        clean = _clean_word(word)
        if not clean:
            break
        if clean in _STOP_WORDS:
            if content:
                break
            continue
        content.append(clean)
    if not content:
        return None
    return " ".join(content[-2:])


# ---------------------------------------------------------------------------
# Trigger definitions
#
# Multi-word phrases are listed before their component words so the overlap
# guard can suppress the shorter sub-match (e.g. "raised one hand" beats
# "raised"; "blocked the path" beats "blocked").
# ---------------------------------------------------------------------------

# (phrase, signal_type, relation, topology_link_hint, base_confidence)
_TRIGGERS: list[tuple[str, str, str, str, float]] = [
    # --- obstruction multi-word (most specific) ---
    ("raised one hand",   "obstruction_signal", "blocks_path",      "OLINK",    0.90),
    ("blocked the path",  "obstruction_signal", "blocks_path",      "OLINK",    0.90),
    # --- spatial multi-word ---
    ("in front of",       "spatial_signal",     "in_front_of",      "OLINK",    0.85),
    # --- spatial single-word ---
    ("before",            "spatial_signal",     "in_front_of",      "OLINK",    0.70),
    ("behind",            "spatial_signal",     "behind",           "OLINK",    0.80),
    ("beside",            "spatial_signal",     "beside",           "QSLINK",   0.80),
    ("near",              "spatial_signal",     "near",             "QSLINK",   0.75),
    ("above",             "spatial_signal",     "above",            "QSLINK",   0.80),
    ("below",             "spatial_signal",     "below",            "QSLINK",   0.80),
    ("within",            "spatial_signal",     "within",           "QSLINK",   0.80),
    ("between",           "spatial_signal",     "between",          "QSLINK",   0.80),
    ("through",           "spatial_signal",     "through",          "QSLINK",   0.75),
    # --- movement ---
    ("approached",        "movement_signal",    "approach",         "MOVELINK", 0.90),
    ("moved",             "movement_signal",    "movement",         "MOVELINK", 0.80),
    ("entered",           "movement_signal",    "enter",            "MOVELINK", 0.90),
    ("crossed",           "movement_signal",    "cross",            "MOVELINK", 0.85),
    ("retreated",         "movement_signal",    "retreat",          "MOVELINK", 0.85),
    ("withdrew",          "movement_signal",    "withdraw",         "MOVELINK", 0.85),
    ("stood",             "movement_signal",    "stand",            "MOVELINK", 0.75),
    ("waited",            "movement_signal",    "wait",             "MOVELINK", 0.70),
    ("raised",            "movement_signal",    "raise",            "MOVELINK", 0.70),
    # --- obstruction single-word ---
    ("blocked",           "obstruction_signal", "blocks_path",      "OLINK",    0.85),
    ("closed",            "obstruction_signal", "closed_boundary",  "OLINK",    0.80),
    ("barred",            "obstruction_signal", "closed_boundary",  "OLINK",    0.85),
    ("sealed",            "obstruction_signal", "closed_boundary",  "OLINK",    0.85),
]

_TRIGGER_PATTERNS = [
    (re.compile(r"\b" + re.escape(phrase) + r"\b"), phrase, sig, rel, topo, conf)
    for phrase, sig, rel, topo, conf in _TRIGGERS
]


# ---------------------------------------------------------------------------
# Sentence-level scan
# ---------------------------------------------------------------------------

def _scan_sentence(
    sentence: str,
    line_no: int,
    counter: list[int],
) -> list[dict[str, Any]]:
    """
    Scan one sentence for topology signals.

    Matched character spans are recorded so a longer multi-word match
    suppresses any shorter sub-phrase that overlaps it.
    """
    signals: list[dict[str, Any]] = []
    lower = sentence.lower()
    matched_spans: list[tuple[int, int]] = []

    for pattern, _phrase, signal_type, relation, topology_link, confidence in _TRIGGER_PATTERNS:
        for m in pattern.finditer(lower):
            mstart, mend = m.start(), m.end()

            if any(s < mend and mstart < e for s, e in matched_spans):
                continue

            matched_spans.append((mstart, mend))
            counter[0] += 1

            signals.append({
                "signal_id": f"spatial_{counter[0]:04d}",
                "line": line_no,
                "signal_type": signal_type,
                "relation": relation,
                "source_text": sentence,
                "subject_hint": _subject_hint(sentence, mstart),
                "object_hint": _object_hint(sentence, mend),
                "confidence": confidence,
                "topology_link_hint": topology_link,
            })

    return signals


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def process_file(pass1_path: Path, output_path: Path) -> dict[str, Any]:
    """
    Read a pass1_explicit output file and write out_pass1_spatial_<stem>.json.

    Inspects narration and dialogue units only.
    Emits JSON structured signal records for the topologist bridge.
    """
    units = _load_pass1_units(pass1_path)
    counter = [0]
    all_signals: list[dict[str, Any]] = []

    for unit in units:
        if unit["type"] not in ("narration", "dialogue"):
            continue
        for sentence in _split_sentences(unit["text"]):
            all_signals.extend(_scan_sentence(sentence, unit["line"], counter))

    result: dict[str, Any] = {
        "source_pass1": str(pass1_path),
        "signal_count": len(all_signals),
        "signals": all_signals,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return result


# ---------------------------------------------------------------------------
# CLI — operator convenience, not the system API
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="EngAIn Passroom · Pass 1 Spatial — extract topology signals"
    )
    parser.add_argument("pass1_file", help="Pass 1 explicit output file (tagged lines).")
    parser.add_argument(
        "--output", "-o", default=None,
        help="Output JSON path (default: out_pass1_spatial_<scene_stem>.json beside input).",
    )
    args = parser.parse_args()

    pass1_path = Path(args.pass1_file).resolve()
    if not pass1_path.exists():
        print(f"[PASS1_SPATIAL] ERROR: file not found: {pass1_path}", file=sys.stderr)
        return 1

    scene_stem = pass1_path.stem.removesuffix(".pass1_explicit")
    out_path = (
        Path(args.output).resolve()
        if args.output
        else pass1_path.parent / f"out_pass1_spatial_{scene_stem}.json"
    )

    result = process_file(pass1_path, out_path)

    type_counts: dict[str, int] = {}
    for sig in result["signals"]:
        type_counts[sig["signal_type"]] = type_counts.get(sig["signal_type"], 0) + 1

    print(f"[PASS1_SPATIAL] signal_count   : {result['signal_count']}")
    for stype, count in sorted(type_counts.items()):
        print(f"[PASS1_SPATIAL]   {stype}: {count}")
    print(f"[PASS1_SPATIAL] → {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
