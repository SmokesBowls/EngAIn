#!/usr/bin/env python3
"""
pass3_merge.py (Pass 3.1 – future-proof edition)

Pass 3 of the EngAIn / ZW narrative pipeline.

Takes:
  - Pass 1 explicit structure output (out_pass1_*.txt)
  - Pass 2 CORE++ metta inferences (out_pass2_*.metta)

Produces:
  - A single ZONJ (JSON) scene file with merged explicit + inferred data:
    {
      "type": "scene",
      "id": "03_Fist_contact",
      "source_files": {...},
      "segments": [
        {
          "line": 12,
          "type": "narration",
          "text": "...",
          "speaker": "Vairis",        # when explicit in Pass1
          "header_attrs": {...},      # all non-core header fields from Pass1
          "inferred": {
            "speaker_inferred": [
              {"value": "Senareth", "confidence": 0.9}
            ],
            "thought": [
              {"subject": "Senareth", "confidence": 0.9}
            ]
          }
        },
        ...
      ]
    }

Key upgrades vs v1:
  - Header parsing is attribute-based, not regex-locked.
  - Pass2 metta parsing is tolerant:
      * ignores unknown atom types
      * tolerates extra attributes and reordering
      * doesn't explode on format drift
  - Extra header fields from Pass1 are preserved in `header_attrs`.
"""

import json
import os
import re
import sys
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict

# ---------------------------------------------------------------------------
# Data model for Pass 1 segments
# ---------------------------------------------------------------------------

@dataclass
class Segment:
    line: int                      # 1-based physical line number in pass1 file
    type: str                      # "blank", "narration", "dialogue", etc.
    text: str = ""                 # content after header
    speaker: Optional[str] = None  # explicit speaker if present
    header_attrs: Dict[str, Any] = field(default_factory=dict)
    # header_attrs holds ALL parsed header fields from Pass1, including type/speaker.


# ---------------------------------------------------------------------------
# Pass 1 parsing
# ---------------------------------------------------------------------------

HEADER_RE = re.compile(r'^\{([^}]*)\}\s*(.*)$')


def _parse_header_attrs(header_str: str) -> Dict[str, str]:
    """
    Parse a header string like:
      "type:dialogue, speaker:Vairis, mood:angry"
    into:
      {"type": "dialogue", "speaker": "Vairis", "mood": "angry"}

    - Whitespace is trimmed.
    - Unknown keys are kept; values remain strings.
    """
    attrs: Dict[str, str] = {}
    if not header_str:
        return attrs

    parts = [p.strip() for p in header_str.split(",") if p.strip()]
    for part in parts:
        if ":" not in part:
            # malformed chunk; keep as-is under a generic key to avoid data loss
            # but don't crash the pipeline.
            key = f"_raw_{len(attrs)}"
            attrs[key] = part
            continue

        key, value = part.split(":", 1)
        key = key.strip()
        value = value.strip()
        if key:
            attrs[key] = value
    return attrs


def parse_pass1(path: str) -> List[Segment]:
    """
    Parse out_pass1_*.txt into a list of Segments.

    Lines normally look like:
      {type:blank}
      {type:narration} Some prose...
      {type:dialogue, speaker:Vairis} "We should establish shelter,"
      {type:scene_header} # Part 3: First Contact

    But this parser is tolerant:
      - Extra / unknown header fields are preserved in header_attrs.
      - If header parsing fails, the whole line becomes narration text.
    """
    segments: List[Segment] = []

    with open(path, "r", encoding="utf-8") as f:
        for idx, raw in enumerate(f, start=1):
            line = raw.rstrip("\n")

            if not line:
                # True blank – treat as structural blank segment.
                segments.append(Segment(line=idx, type="blank", text=""))
                continue

            m = HEADER_RE.match(line)
            if not m:
                # No header present – fallback to pure narration.
                segments.append(Segment(line=idx, type="narration", text=line))
                continue

            header_str = m.group(1).strip()
            text = m.group(2) or ""

            attrs = _parse_header_attrs(header_str)
            type_str = attrs.get("type", "narration")
            speaker = attrs.get("speaker")

            segments.append(
                Segment(
                    line=idx,
                    type=type_str,
                    text=text,
                    speaker=speaker,
                    header_attrs=attrs,
                )
            )

    return segments


# ---------------------------------------------------------------------------
# Pass 2 parsing (metta)
# ---------------------------------------------------------------------------

# Example atoms (existing format):
# (speaker line:28 Vairis :confidence 0.95)
# (actor   line:20 Senareth :confidence 0.8)
# (emotion line:39 Senareth fear :confidence 0.9)
# (action  line:20 vrill_energy :confidence 0.9)
# (thought line:69 Senareth :confidence 1.0)
#
# Design goal: tolerate:
#   - additional attributes
#   - reordering
#   - unknown atom types
#   - colon forms like "line:28" and separate ":confidence 0.95"


@dataclass
class Pass2Data:
    speakers: Dict[int, List[Tuple[str, float]]]
    actors: Dict[int, List[Tuple[str, float]]]
    emotions: Dict[int, List[Tuple[str, str, float]]]
    actions: Dict[int, List[Tuple[str, float]]]
    thoughts: Dict[int, List[Tuple[str, float]]]


def _tokenize_metta(line: str) -> List[str]:
    """
    Very simple metta tokenizer:
      "(speaker line:28 Vairis :confidence 0.95)"
    -> ["speaker", "line:28", "Vairis", ":confidence", "0.95"]

    - Strips surrounding parens if present.
    - Splits on whitespace.
    """
    line = line.strip()
    if line.startswith("(") and line.endswith(")"):
        line = line[1:-1].strip()
    if not line:
        return []
    return line.split()


def _parse_conf_from_tokens(tokens: List[str], i: int) -> Tuple[Optional[float], int]:
    """
    Parse confidence from tokens starting at index i, handling:
      - ":confidence 0.95"
      - ":confidence=0.95"
    Returns (confidence, new_index).
    """
    tok = tokens[i]

    # Case 1: ":confidence=0.95"
    if tok.startswith(":confidence="):
        try:
            return float(tok.split("=", 1)[1]), i
        except ValueError:
            return None, i

    # Case 2: ":confidence 0.95"
    if tok == ":confidence" and i + 1 < len(tokens):
        try:
            return float(tokens[i + 1]), i + 1
        except ValueError:
            return None, i + 1

    # Unknown pattern – ignore
    return None, i


def _handle_speaker(tokens: List[str], speakers: Dict[int, List[Tuple[str, float]]]) -> None:
    line_num: Optional[int] = None
    name: Optional[str] = None
    conf: Optional[float] = None

    i = 1  # tokens[0] == "speaker"
    while i < len(tokens):
        tok = tokens[i]

        if tok.startswith("line:"):
            try:
                line_num = int(tok.split(":", 1)[1])
            except ValueError:
                pass

        elif tok.startswith(":confidence"):
            conf, i = _parse_conf_from_tokens(tokens, i)

        elif not tok.startswith(":") and not tok.startswith("line:") and name is None:
            # first plain symbol after line is treated as speaker name
            name = tok

        i += 1

    if line_num is not None and name is not None and conf is not None:
        speakers[line_num].append((name, conf))


def _handle_actor(tokens: List[str], actors: Dict[int, List[Tuple[str, float]]]) -> None:
    line_num: Optional[int] = None
    name: Optional[str] = None
    conf: Optional[float] = None

    i = 1  # tokens[0] == "actor"
    while i < len(tokens):
        tok = tokens[i]

        if tok.startswith("line:"):
            try:
                line_num = int(tok.split(":", 1)[1])
            except ValueError:
                pass

        elif tok.startswith(":confidence"):
            conf, i = _parse_conf_from_tokens(tokens, i)

        elif not tok.startswith(":") and not tok.startswith("line:") and name is None:
            name = tok

        i += 1

    if line_num is not None and name is not None and conf is not None:
        actors[line_num].append((name, conf))


def _handle_emotion(tokens: List[str], emotions: Dict[int, List[Tuple[str, str, float]]]) -> None:
    line_num: Optional[int] = None
    subject: Optional[str] = None
    label: Optional[str] = None
    conf: Optional[float] = None

    i = 1  # tokens[0] == "emotion"
    while i < len(tokens):
        tok = tokens[i]

        if tok.startswith("line:"):
            try:
                line_num = int(tok.split(":", 1)[1])
            except ValueError:
                pass

        elif tok.startswith(":confidence"):
            conf, i = _parse_conf_from_tokens(tokens, i)

        elif not tok.startswith(":") and not tok.startswith("line:"):
            # first plain symbol → subject, second → label
            if subject is None:
                subject = tok
            elif label is None:
                label = tok

        i += 1

    if line_num is not None and subject is not None and label is not None and conf is not None:
        emotions[line_num].append((subject, label, conf))


def _handle_action(tokens: List[str], actions: Dict[int, List[Tuple[str, float]]]) -> None:
    line_num: Optional[int] = None
    label: Optional[str] = None
    conf: Optional[float] = None

    i = 1  # tokens[0] == "action"
    while i < len(tokens):
        tok = tokens[i]

        if tok.startswith("line:"):
            try:
                line_num = int(tok.split(":", 1)[1])
            except ValueError:
                pass

        elif tok.startswith(":confidence"):
            conf, i = _parse_conf_from_tokens(tokens, i)

        elif not tok.startswith(":") and not tok.startswith("line:") and label is None:
            label = tok

        i += 1

    if line_num is not None and label is not None and conf is not None:
        actions[line_num].append((label, conf))


def _handle_thought(tokens: List[str], thoughts: Dict[int, List[Tuple[str, float]]]) -> None:
    line_num: Optional[int] = None
    subject: Optional[str] = None
    conf: Optional[float] = None

    i = 1  # tokens[0] == "thought"
    while i < len(tokens):
        tok = tokens[i]

        if tok.startswith("line:"):
            try:
                line_num = int(tok.split(":", 1)[1])
            except ValueError:
                pass

        elif tok.startswith(":confidence"):
            conf, i = _parse_conf_from_tokens(tokens, i)

        elif not tok.startswith(":") and not tok.startswith("line:") and subject is None:
            # subject can be "unknown" or a name
            subject = tok

        i += 1

    if line_num is not None and subject is not None and conf is not None:
        thoughts[line_num].append((subject, conf))


def parse_pass2(path: str) -> Pass2Data:
    """
    Parse out_pass2_*.metta into Pass2Data.

    Tolerant by design:
      - Ignores unknown atom types instead of failing.
      - Ignores malformed lines.
      - Allows attribute reordering and extras.
    """
    speakers_dd: Dict[int, List[Tuple[str, float]]] = defaultdict(list)
    actors_dd: Dict[int, List[Tuple[str, float]]] = defaultdict(list)
    emotions_dd: Dict[int, List[Tuple[str, str, float]]] = defaultdict(list)
    actions_dd: Dict[int, List[Tuple[str, float]]] = defaultdict(list)
    thoughts_dd: Dict[int, List[Tuple[str, float]]] = defaultdict(list)

    # Atom type registry for easy future extension.
    # Add new atom types here without touching the main loop.
    handlers = {
        "speaker": lambda t: _handle_speaker(t, speakers_dd),
        "actor":   lambda t: _handle_actor(t, actors_dd),
        "emotion": lambda t: _handle_emotion(t, emotions_dd),
        "action":  lambda t: _handle_action(t, actions_dd),
        "thought": lambda t: _handle_thought(t, thoughts_dd),
    }

    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith(";"):
                continue

            tokens = _tokenize_metta(line)
            if not tokens:
                continue

            head = tokens[0]
            handler = handlers.get(head)
            if handler is None:
                # Unknown / future atom type – ignore safely.
                continue

            try:
                handler(tokens)
            except Exception:
                # Malformed atom should NOT kill the pipeline; skip it.
                continue

    return Pass2Data(
        speakers=dict(speakers_dd),
        actors=dict(actors_dd),
        emotions=dict(emotions_dd),
        actions=dict(actions_dd),
        thoughts=dict(thoughts_dd),
    )


# ---------------------------------------------------------------------------
# Merge logic → ZONJ
# ---------------------------------------------------------------------------

def merge_to_zonj(
    pass1_segments: List[Segment],
    p2: Pass2Data,
    pass1_path: str,
    pass2_path: str,
) -> Dict[str, Any]:
    """
    Merge Pass1 + Pass2 into final ZONJ scene dict, following the frozen spec
    while being tolerant to future expansions.
    """
    # Scene id: prefer stripping "out_pass1_" from the basename.
    base = os.path.splitext(os.path.basename(pass1_path))[0]
    if base.startswith("out_pass1_"):
        scene_id = base[len("out_pass1_"):]
    else:
        scene_id = base

    scene: Dict[str, Any] = {
        "type": "scene",
        "id": scene_id,
        "source_files": {
            "pass1": os.path.basename(pass1_path),
            "pass2": os.path.basename(pass2_path),
        },
        "segments": [],
    }

    for seg in pass1_segments:
        seg_obj: Dict[str, Any] = {
            "line": seg.line,
            "type": seg.type,
        }

        if seg.type != "blank":
            seg_obj["text"] = seg.text

        if seg.speaker is not None and seg.type == "dialogue":
            seg_obj["speaker"] = seg.speaker

        # Preserve *all* header attrs for future engines, excluding core fields
        # already lifted to the top-level.
        if seg.header_attrs:
            extra = {
                k: v
                for (k, v) in seg.header_attrs.items()
                if k not in ("type", "speaker")
            }
            if extra:
                seg_obj["header_attrs"] = extra

        inferred: Dict[str, Any] = {}

        if seg.line in p2.speakers:
            inferred["speaker_inferred"] = [
                {"value": name, "confidence": conf}
                for (name, conf) in p2.speakers[seg.line]
            ]

        if seg.line in p2.actors:
            inferred["actor"] = [
                {"value": name, "confidence": conf}
                for (name, conf) in p2.actors[seg.line]
            ]

        if seg.line in p2.emotions:
            inferred["emotion"] = [
                {"subject": subj, "label": label, "confidence": conf}
                for (subj, label, conf) in p2.emotions[seg.line]
            ]

        if seg.line in p2.actions:
            inferred["action"] = [
                {"label": label, "confidence": conf}
                for (label, conf) in p2.actions[seg.line]
            ]

        if seg.line in p2.thoughts:
            inferred["thought"] = [
                {"subject": subj, "confidence": conf}
                for (subj, conf) in p2.thoughts[seg.line]
            ]

        if inferred:
            seg_obj["inferred"] = inferred

        scene["segments"].append(seg_obj)

    return scene


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    if len(sys.argv) != 3:
        print("Usage: pass3_merge.py <pass1_output.txt> <pass2_output.metta>")
        sys.exit(1)

    pass1_path = sys.argv[1]
    pass2_path = sys.argv[2]

    if not os.path.exists(pass1_path):
        print(f"[ERROR] Pass1 file not found: {pass1_path}")
        sys.exit(1)
    if not os.path.exists(pass2_path):
        print(f"[ERROR] Pass2 file not found: {pass2_path}")
        sys.exit(1)

    segments = parse_pass1(pass1_path)
    p2 = parse_pass2(pass2_path)
    scene = merge_to_zonj(segments, p2, pass1_path, pass2_path)

    base = os.path.splitext(os.path.basename(pass1_path))[0]
    out_name = f"zonj_{base}.txt" 
    with open(out_name, "w", encoding="utf-8") as f:
        json.dump(scene, f, ensure_ascii=False, indent=2)

    print(f"[PASS3] ZONJ written → {out_name}")


if __name__ == "__main__":
    main()
