#!/usr/bin/env python3
"""
pass3_merge.py

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
          "inferred": {
            "thought": [
              {"subject": "Senareth", "confidence": 0.9}
            ]
          }
        },
        ...
      ]
    }
"""

import json
import os
import re
import sys
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict

# ---------------------------------------------------------------------------
# Data model for Pass 1 segments
# ---------------------------------------------------------------------------

@dataclass
class Segment:
    line: int                  # 1-based physical line number in pass1 file
    type: str                  # "blank", "narration", "dialogue", etc.
    text: str = ""             # content after header
    speaker: Optional[str] = None  # explicit speaker if present


TYPE_HEADER_RE = re.compile(
    r'^\{type:([^,}]+)(?:,\s*speaker:([^}]+))?\}\s*(.*)$'
)

# ---------------------------------------------------------------------------
# Pass 1 parsing
# ---------------------------------------------------------------------------

def parse_pass1(path: str) -> List[Segment]:
    """
    Parse out_pass1_*.txt into a list of Segments.

    Lines look like:
      {type:blank}
      {type:narration} Some prose...
      {type:dialogue, speaker:Vairis} "We should establish shelter,"
      {type:scene_header} # Part 3: First Contact
    """
    segments: List[Segment] = []
    with open(path, "r", encoding="utf-8") as f:
        for idx, raw in enumerate(f, start=1):
            line = raw.rstrip("\n")
            if not line:
                # Should not normally happen because pass1 always wraps with {type:...},
                # but we handle defensively.
                segments.append(Segment(line=idx, type="blank", text=""))
                continue

            m = TYPE_HEADER_RE.match(line)
            if not m:
                # Fallback: treat as narration-only
                segments.append(Segment(line=idx, type="narration", text=line))
                continue

            type_str = m.group(1).strip()
            speaker = m.group(2).strip() if m.group(2) else None
            text = m.group(3) or ""
            segments.append(
                Segment(line=idx, type=type_str, text=text, speaker=speaker)
            )
    return segments

# ---------------------------------------------------------------------------
# Pass 2 parsing (metta)
# ---------------------------------------------------------------------------

# Example atoms:
# (speaker line:28 Vairis :confidence 0.95)
# (actor line:20 Senareth :confidence 0.8)
# (emotion line:39 Senareth fear :confidence 0.9)
# (action line:20 vrill_energy :confidence 0.9)
# (thought line:69 Senareth :confidence 1.0)

SPEAKER_RE = re.compile(
    r'^\(speaker\s+line:(\d+)\s+([A-Za-z_][A-Za-z0-9_]*)\s+:confidence\s+([0-9.]+)\)'
)
ACTOR_RE = re.compile(
    r'^\(actor\s+line:(\d+)\s+([A-Za-z_][A-Za-z0-9_]*)\s+:confidence\s+([0-9.]+)\)'
)
EMOTION_RE = re.compile(
    r'^\(emotion\s+line:(\d+)\s+([A-Za-z_][A-Za-z0-9_]*)\s+([a-z_]+)\s+:confidence\s+([0-9.]+)\)'
)
ACTION_RE = re.compile(
    r'^\(action\s+line:(\d+)\s+([a-z_]+)\s+:confidence\s+([0-9.]+)\)'
)
THOUGHT_RE = re.compile(
    r'^\(thought\s+line:(\d+)\s+([A-Za-z_][A-Za-z0-9_]*|unknown)\s+:confidence\s+([0-9.]+)\)'
)


@dataclass
class Pass2Data:
    speakers: Dict[int, List[Tuple[str, float]]]
    actors: Dict[int, List[Tuple[str, float]]]
    emotions: Dict[int, List[Tuple[str, str, float]]]
    actions: Dict[int, List[Tuple[str, float]]]
    thoughts: Dict[int, List[Tuple[str, float]]]


def parse_pass2(path: str) -> Pass2Data:
    speakers = defaultdict(list)   # line -> [(name, conf)]
    actors = defaultdict(list)     # line -> [(name, conf)]
    emotions = defaultdict(list)   # line -> [(subject, label, conf)]
    actions = defaultdict(list)    # line -> [(label, conf)]
    thoughts = defaultdict(list)   # line -> [(subject, conf)]

    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith(";"):
                continue

            m = SPEAKER_RE.match(line)
            if m:
                ln = int(m.group(1))
                name = m.group(2)
                conf = float(m.group(3))
                speakers[ln].append((name, conf))
                continue

            m = ACTOR_RE.match(line)
            if m:
                ln = int(m.group(1))
                name = m.group(2)
                conf = float(m.group(3))
                actors[ln].append((name, conf))
                continue

            m = EMOTION_RE.match(line)
            if m:
                ln = int(m.group(1))
                subj = m.group(2)
                label = m.group(3)
                conf = float(m.group(4))
                emotions[ln].append((subj, label, conf))
                continue

            m = ACTION_RE.match(line)
            if m:
                ln = int(m.group(1))
                label = m.group(2)
                conf = float(m.group(3))
                actions[ln].append((label, conf))
                continue

            m = THOUGHT_RE.match(line)
            if m:
                ln = int(m.group(1))
                subj = m.group(2)
                conf = float(m.group(3))
                # We keep "unknown" subject; AP/APSimKernel can decide later.
                thoughts[ln].append((subj, conf))
                continue

            # Anything else is ignored; metta is append-only and may gain new atom types later.

    return Pass2Data(
        speakers=dict(speakers),
        actors=dict(actors),
        emotions=dict(emotions),
        actions=dict(actions),
        thoughts=dict(thoughts),
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
    Merge Pass1 + Pass2 into final ZONJ scene dict, following the frozen spec.
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
            # preserve text for all non-blank segments (blank segments have no payload)
            seg_obj["text"] = seg.text
        if seg.speaker is not None and seg.type == "dialogue":
            seg_obj["speaker"] = seg.speaker

        # Attach inferred block if any atoms exist for this line.
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

def main():
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
    out_name = f"zonj_{base}.json"
    with open(out_name, "w", encoding="utf-8") as f:
        json.dump(scene, f, ensure_ascii=False, indent=2)

    print(f"[PASS3] ZONJ written → {out_name}")


if __name__ == "__main__":
    main()
