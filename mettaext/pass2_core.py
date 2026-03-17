#!/usr/bin/env python3
# pass2_core.py (fixed)

import os
import re
import sys
import argparse
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict

# ============================================================
# CONFIG / FLAGS
# ============================================================

ENABLE_FULL = False

KNOWN_NAMES = {
    "Senareth",
    "Vairis",
    "Elyraen",
    "Olythae",
    "Torhh",
    "Kyreth",
    "Heminra",
    "Malthish",
}

EMOTION_KEYWORDS = {
    "fear": "fear",
    "terror": "fear",
    "anger": "anger",
    "hope": "hope",
    "gratitude": "gratitude",
    "wonder": "wonder",
    "triumph": "triumph",
    "relief": "relief",
    "anticipation": "anticipation",
    "anxiety": "anxiety",
}

ACTION_KEYWORDS = {
    "retreated": ["retreat"],
    "retreat": ["retreat"],
    "withdrew": ["retreat"],
    "kneel": ["submission", "prayer", "observation"],
    "kneeling": ["submission", "prayer", "observation"],
    "knelt": ["submission", "prayer", "observation"],
    "submission": ["submission"],
    "attack": ["attack"],
    "attacked": ["attack"],
    "struck": ["attack"],
    "vrill-manipulation": ["vrill_manipulation"],
    "vrill manipulation": ["vrill_manipulation"],
    "manipulating vrill": ["vrill_manipulation"],
    "manipulated vrill": ["vrill_manipulation"],
    "vrill energy": ["vrill_energy"],
    "vrill-energy": ["vrill_energy"],
    "chemical fear": ["chemical_fear"],
    "shaping": ["shaping"],
    "shape the boundary": ["shaping"],
    "sand-shaping": ["shaping"],
    "sand shaping": ["shaping"],
    "create": ["creation"],
    "created": ["creation"],
    "creating": ["creation"],
    "currents": ["vrel_flow"],
    "flows": ["vrel_flow"],
    "quantum potential": ["vrel_potential"],
    "interference": ["vrel_interference"],
    "vibration": ["vrel_vibration"],
    "resonate": ["vrel_resonance"],
}

VISUAL_KEYWORDS = {
    "aurora": "aurora_shimmer",
    "bioluminescent": "aurora_shimmer",
    "glowing": "glow",
    "glimmer": "glow",
    "shimmer": "shimmer",
    "pulse": "pulse",
    "flicker": "flicker",
    "shadow": "shadow_dim",
    "darkness": "shadow_dim",
}

TYPE_RE = re.compile(
    r'^\{type:(?P<type>[a-z_]+)'
    r'(?:,\s*speaker:(?P<speaker>[A-Za-z_]+))?\}\s*(?P<text>.*)$'
)

ASTERISK_THOUGHT_RE = re.compile(r"[*_](?P<thought>[^*_]{2,})[*_]")

# ============================================================
# SEGMENT CLASS
# ============================================================

@dataclass
class Segment:
    tag_line_no: int
    text_line_no: int
    type: str
    speaker: Optional[str]
    text: str

# ============================================================
# LOADING PASS1 SEGMENTS
# ============================================================

def load_segments(path: str) -> List[Segment]:
    segments: List[Segment] = []
    with open(path, "r", encoding="utf-8") as f:
        for idx, raw in enumerate(f, start=1):
            line = raw.rstrip("\n")
            m = TYPE_RE.match(line.strip())
            if not m:
                continue
            segments.append(
                Segment(
                    tag_line_no=idx,
                    text_line_no=idx,
                    type=m.group("type"),
                    speaker=m.group("speaker"),
                    text=m.group("text") or "",
                )
            )
    return segments

# ============================================================
# SPEAKER INFERENCE
# ============================================================

def infer_speakers(segments: List[Segment]) -> List[Tuple[int, str, float]]:
    atoms: List[Tuple[int, str, float]] = []
    for seg in segments:
        if seg.type == "dialogue" and seg.speaker and seg.speaker != "unknown":
            atoms.append((seg.text_line_no, seg.speaker, 0.95))
    return atoms

# ============================================================
# PRONOUN → ACTOR INFERENCE
# ============================================================

PRONOUNS = {"he", "she", "they", "him", "her", "them", "his", "their"}

def infer_pronouns(segments: List[Segment]) -> List[Tuple[int, str, float]]:
    atoms: List[Tuple[int, str, float]] = []
    last_actor: Optional[str] = None

    for seg in segments:
        text = seg.text or ""
        if not text:
            continue

        words = text.split()
        if words:
            token_clean = words[0].strip(",.;!?")
            if token_clean in KNOWN_NAMES:
                last_actor = token_clean

        if last_actor is None:
            continue

        lower = text.lower()
        if any(re.search(rf"\b{re.escape(p)}\b", lower) for p in PRONOUNS):
            atoms.append((seg.text_line_no, last_actor, 0.80))

    return atoms

# ============================================================
# EMOTION INFERENCE
# ============================================================

def _find_subject_backwards(segments: List[Segment], idx: int) -> Optional[str]:
    for j in range(idx, -1, -1):
        txt = segments[j].text or ""
        if not txt:
            continue
        for w in txt.split():
            w_clean = w.strip(",.;!?")
            if w_clean in KNOWN_NAMES:
                return w_clean
    return None

def infer_emotions(segments: List[Segment]) -> List[Tuple[int, str, str, float]]:
    atoms: List[Tuple[int, str, str, float]] = []

    for idx, seg in enumerate(segments):
        text = seg.text or ""
        if not text:
            continue
        lower = text.lower()

        # Special case: "Wonder. Triumph. Relief. Hope."
        tokens = [t.strip().lower() for t in text.split(".") if t.strip()]
        multi = [t for t in tokens if t in EMOTION_KEYWORDS]
        if multi:
            subject = _find_subject_backwards(segments, idx)
            if subject:
                for emo_word in multi:
                    atoms.append((seg.text_line_no, subject, EMOTION_KEYWORDS[emo_word], 1.0))
            continue

        for emo_word, canonical in EMOTION_KEYWORDS.items():
            if re.search(rf"\b{re.escape(emo_word)}\b", lower):
                subject = _find_subject_backwards(segments, idx)
                if subject:
                    atoms.append((seg.text_line_no, subject, canonical, 0.90))

    # Dedup: keep highest confidence per (line, subject, emotion)
    dedup: Dict[Tuple[int, str, str], float] = {}
    for line, subj, emo, conf in atoms:
        key = (line, subj, emo)
        if key not in dedup or conf > dedup[key]:
            dedup[key] = conf

    return [(line, subj, emo, conf) for (line, subj, emo), conf in sorted(dedup.items())]

# ============================================================
# ACTION INFERENCE
# ============================================================

def infer_actions(segments: List[Segment]) -> List[Tuple[int, str, float, float]]:
    """
    Returns List of (line, canonical_action, confidence, ambiguity)
    """
    atoms: List[Tuple[int, str, float, float]] = []
    
    # Track per line
    line_candidates = {} # line -> {canonical -> max_conf}

    for seg in segments:
        text = seg.text or ""
        if not text:
            continue
        lower = text.lower()

        for phrase, canonicals in ACTION_KEYWORDS.items():
            if phrase in lower:
                if seg.text_line_no not in line_candidates:
                    line_candidates[seg.text_line_no] = {}
                
                for canonical in canonicals:
                    # If multiple hypotheses for same phrase, split confidence
                    base_conf = 0.90 / len(canonicals)
                    if canonical not in line_candidates[seg.text_line_no] or base_conf > line_candidates[seg.text_line_no][canonical]:
                        line_candidates[seg.text_line_no][canonical] = base_conf

    for line, candidates in line_candidates.items():
        # Ambiguity score: 1.0 if many hypotheses, 0.0 if one
        ambiguity = 0.0
        if len(candidates) > 1:
            ambiguity = 0.5 + (0.1 * min(len(candidates), 5))
            # If "kneel" was the phrase, it matches 3 canonicals, so ambiguity is roughly 0.8
        
        for canonical, conf in candidates.items():
            atoms.append((line, canonical, conf, ambiguity))

    return atoms


def infer_visuals(segments: List[Segment]) -> List[Tuple[int, str, float]]:
    """
    Returns List of (line, visual_effect, confidence)
    """
    atoms: List[Tuple[int, str, float]] = []

    for seg in segments:
        text = seg.text or ""
        if not text:
            continue
        lower = text.lower()

        for phrase, effect in VISUAL_KEYWORDS.items():
            if phrase in lower:
                # Direct narrative hint
                atoms.append((seg.text_line_no, effect, 0.95))

    return atoms

# ============================================================
# THOUGHT / INTERNAL MONOLOGUE INFERENCE
# ============================================================

def infer_thoughts(segments: List[Segment]) -> List[Tuple[int, str, float]]:
    atoms: List[Tuple[int, str, float]] = []

    for idx, seg in enumerate(segments):
        text = seg.text or ""

        if seg.type == "internal_monologue":
            thinker = _find_subject_backwards(segments, idx) or "unknown"
            conf = 0.90 if thinker != "unknown" else 0.60
            atoms.append((seg.text_line_no, thinker, conf))

        if ASTERISK_THOUGHT_RE.search(text):
            thinker = _find_subject_backwards(segments, idx) or "unknown"
            conf = 0.90 if thinker != "unknown" else 0.60
            atoms.append((seg.text_line_no, thinker, conf))

    # Dedup
    dedup: Dict[Tuple[int, str], float] = {}
    for line, who, conf in atoms:
        key = (line, who)
        if key not in dedup or conf > dedup[key]:
            dedup[key] = conf

    return [(line, who, conf) for (line, who), conf in sorted(dedup.items())]

# ============================================================
# METTA OUTPUT
# ============================================================

def write_metta(
    path: str,
    speakers: List[Tuple[int, str, float]],
    pronouns: List[Tuple[int, str, float]],
    emotions: List[Tuple[int, str, str, float]],
    actions: List[Tuple[int, str, float, float]],
    thoughts: List[Tuple[int, str, float]],
    visuals: List[Tuple[int, str, float]],
) -> None:
    out_dir = os.path.dirname(path)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        f.write("; PASS2 CORE++ INFERENCES\n\n")

        f.write("; ---- Speaker Inference ----\n")
        for line, name, conf in speakers:
            f.write(f"(speaker line:{line} {name} :confidence {conf:.2f})\n")
        f.write("\n")

        f.write("; ---- Pronoun → Actor ----\n")
        for line, name, conf in pronouns:
            f.write(f"(actor line:{line} {name} :confidence {conf:.2f})\n")
        f.write("\n")

        f.write("; ---- Emotions ----\n")
        for line, subj, emo, conf in emotions:
            f.write(f"(emotion line:{line} {subj} {emo} :confidence {conf:.2f})\n")
        f.write("\n")

        f.write("; ---- Actions & Ambiguity ----\n")
        seen_ambiguity = set()
        for line, act, conf, amb in actions:
            f.write(f"(action line:{line} {act} :confidence {conf:.2f})\n")
            if amb > 0 and line not in seen_ambiguity:
                f.write(f"(ambiguity line:{line} value:{amb:.2f})\n")
                seen_ambiguity.add(line)
        f.write("\n")

        f.write("; ---- Visual Hints ----\n")
        for line, effect, conf in visuals:
            f.write(f"(visual line:{line} {effect} :confidence {conf:.2f})\n")
        f.write("\n")

        f.write("; ---- Thoughts ----\n")
        for line, who, conf in thoughts:
            f.write(f"(thought line:{line} {who} :confidence {conf:.2f})\n")
        f.write("\n")

# ============================================================
# MAIN
# ============================================================

def main() -> None:
    parser = argparse.ArgumentParser(description="Pass2 core inference on pass1 output.")
    parser.add_argument("infile", help="Path to pass1_output.txt")
    parser.add_argument("outfile", nargs="?", help="Optional output .metta file")
    args = parser.parse_args()

    infile = args.infile
    if not os.path.exists(infile):
        print(f"ERROR: Input file not found: {infile}")
        sys.exit(1)

    segments = load_segments(infile)

    speakers = infer_speakers(segments)
    pronouns = infer_pronouns(segments)
    emotions = infer_emotions(segments)
    actions = infer_actions(segments)
    thoughts = infer_thoughts(segments)
    visuals = infer_visuals(segments)

    if args.outfile:
        outfile = args.outfile
    else:
        base = os.path.basename(infile)
        base_noext = base[:-4] if base.endswith(".txt") else base
        base_noext = base_noext.replace("out_pass1_", "")
        outfile = f"out_pass2_{base_noext}.metta"

    write_metta(outfile, speakers, pronouns, emotions, actions, thoughts, visuals)
    print(f"[PASS2] Wrote → {outfile}")

if __name__ == "__main__":
    main()
