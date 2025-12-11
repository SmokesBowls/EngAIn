#!/usr/bin/env python3
import os
import re
import sys
from dataclasses import dataclass
from typing import List, Tuple, Optional

# ============================================================
# CONFIG / FLAGS
# ============================================================

# When you’re ready to experiment with heavier reasoning,
# flip this to True and implement the FULL_* functions.
ENABLE_FULL = False

# Known character names for this universe (extend as needed)
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

# Emotion keywords → canonical label
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

# Action keywords → canonical label
ACTION_KEYWORDS = {
    "retreated": "retreat",
    "retreat": "retreat",
    "withdrew": "retreat",
    "kneel": "submission",
    "kneeling": "submission",
    "knelt": "submission",
    "submission": "submission",
    "attack": "attack",
    "attacked": "attack",
    "struck": "attack",
    "vrill-manipulation": "vrill_manipulation",
    "vrill manipulation": "vrill_manipulation",
    "manipulating vrill": "vrill_manipulation",
    "manipulated vrill": "vrill_manipulation",
    "vrill energy": "vrill_energy",
    "vrill-energy": "vrill_energy",
    "chemical fear": "chemical_fear",
    "shaping": "shaping",
    "shape the boundary": "shaping",
    "sand-shaping": "shaping",
    "sand shaping": "shaping",
    "create": "creation",
    "created": "creation",
    "creating": "creation",
}

# Regex to parse the Pass1 inline tag format:
#   {type:narration} text...
#   {type:dialogue, speaker:Vairis} "We should..."
TYPE_RE = re.compile(
    r'^\{type:(?P<type>[a-z_]+)'
    r'(?:,\s*speaker:(?P<speaker>[A-Za-z_]+))?'
    r'\}\s*(?P<text>.*)$'
)

# Asterisk / italic thought pattern: *Why are they afraid of us?*
ASTERISK_THOUGHT_RE = re.compile(
    r"[*_](?P<thought>[A-Za-z0-9 ,.\"'?;:!\-]{2,})[*_]"
)

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
    """
    Load Pass1 output file where each logical segment is a single line:
      {type:narration} The sun had set...
      {type:dialogue, speaker:Vairis} "We should establish shelter,"
    """
    segments: List[Segment] = []
    with open(path, "r", encoding="utf-8") as f:
        lines = [line.rstrip("\n") for line in f]

    for idx, line in enumerate(lines, start=1):
        m = TYPE_RE.match(line.strip())
        if not m:
            continue
        seg_type = m.group("type")
        speaker = m.group("speaker")
        text = m.group("text") or ""
        segments.append(
            Segment(
                tag_line_no=idx,
                text_line_no=idx,
                type=seg_type,
                speaker=speaker,
                text=text,
            )
        )
    return segments

# ============================================================
# SPEAKER INFERENCE
# ============================================================

def infer_speakers(segments: List[Segment]) -> List[Tuple[int, str, float]]:
    """
    For now: only emit speakers that are already explicit in Pass1.
    (CORE++: no guessing here.)
    """
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
    """
    Track last seen explicit actor and map pronouns to that actor.
    Very local, very dumb, but high precision in these scenes.
    """
    atoms: List[Tuple[int, str, float]] = []
    last_actor: Optional[str] = None

    for seg in segments:
        text = seg.text
        if not text:
            continue

        words = text.split()

        # Update last_actor if first token is a known name (cleaned)
        if words:
            token_clean = words[0].strip(",.;!?")
            if token_clean in KNOWN_NAMES:
                last_actor = token_clean

        lower = text.lower()
        if last_actor is None:
            continue

        for pron in PRONOUNS:
            if re.search(rf"\b{re.escape(pron)}\b", lower):
                atoms.append((seg.text_line_no, last_actor, 0.8))
                break  # one actor per line is enough for CORE
    return atoms

# ============================================================
# EMOTION INFERENCE
# ============================================================

def _find_subject_backwards(segments: List[Segment], idx: int) -> Optional[str]:
    """
    Scan backwards from index idx to find the nearest explicit name.
    """
    for j in range(idx, -1, -1):
        txt = segments[j].text
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
        text = seg.text
        if not text:
            continue
        lower = text.lower()

        # SPECIAL CASE: multi-emotion list "Wonder. Triumph. Relief. Hope."
        # We treat each word as a full-strength emotion if present.
        tokens = [t.strip().lower() for t in text.split(".") if t.strip()]
        multi_candidates = [t for t in tokens if t in EMOTION_KEYWORDS]
        if multi_candidates:
            subject = _find_subject_backwards(segments, idx)
            if subject is not None:
                for emo_word in multi_candidates:
                    atoms.append(
                        (seg.text_line_no, subject, EMOTION_KEYWORDS[emo_word], 1.0)
                    )
            # Skip generic pass for this segment to avoid duplicates
            continue

        # PASS 1: simple emotion word detection with backward subject search
        for emo_word, canonical in EMOTION_KEYWORDS.items():
            if re.search(rf"\b{re.escape(emo_word)}\b", lower):
                subject = _find_subject_backwards(segments, idx)
                if subject is not None:
                    atoms.append((seg.text_line_no, subject, canonical, 0.9))

    # Deduplicate: keep highest confidence per (line, subject, emotion)
    dedup: dict[Tuple[int, str, str], float] = {}
    for line, subj, emo, conf in atoms:
        key = (line, subj, emo)
        if key not in dedup or conf > dedup[key]:
            dedup[key] = conf

    result: List[Tuple[int, str, str, float]] = []
    for (line, subj, emo), conf in sorted(dedup.items()):
        result.append((line, subj, emo, conf))
    return result

# ============================================================
# ACTION INFERENCE
# ============================================================

def infer_actions(segments: List[Segment]) -> List[Tuple[int, str, float]]:
    atoms: List[Tuple[int, str, float]] = []
    seen: set[Tuple[int, str]] = set()

    for seg in segments:
        text = seg.text
        if not text:
            continue
        lower = text.lower()

        for phrase, canonical in ACTION_KEYWORDS.items():
            if phrase in lower:
                key = (seg.text_line_no, canonical)
                if key in seen:
                    continue
                seen.add(key)
                atoms.append((seg.text_line_no, canonical, 0.9))
    return atoms

# ============================================================
# THOUGHT / INTERNAL MONOLOGUE INFERENCE
# ============================================================

def infer_thoughts(segments: List[Segment]) -> List[Tuple[int, str, float]]:
    atoms: List[Tuple[int, str, float]] = []

    for idx, seg in enumerate(segments):
        # 1) Internal monologue type
        if seg.type == "internal_monologue":
            text = seg.text
            lower = text.lower()

            # Try to find explicit thinker
            thinker: Optional[str] = None
            # "... Senareth thought ..."
            m = re.search(r"\b([A-Z][a-zA-Z]+)\b\s+thought", text)
            if m and m.group(1) in KNOWN_NAMES:
                thinker = m.group(1)
                conf = 1.0
            else:
                # Fallback: backward scan
                thinker = _find_subject_backwards(segments, idx)
                conf = 0.9 if thinker else 0.6

            if thinker is None:
                thinker = "unknown"
            atoms.append((seg.text_line_no, thinker, conf))

        # 2) Asterisk thoughts inside narration/dialogue: *Patience,* etc.
        #    Very light handling: just mark as "unknown" unless we can
        #    confidently find a nearby subject.
        matches = list(ASTERISK_THOUGHT_RE.finditer(seg.text))
        if matches:
            thinker = _find_subject_backwards(segments, idx)
            if thinker is None:
                thinker = "unknown"
                conf = 0.6
            else:
                conf = 0.9
            atoms.append((seg.text_line_no, thinker, conf))

    # Deduplicate on (line, thinker) keeping highest conf
    dedup: dict[Tuple[int, str], float] = {}
    for line, who, conf in atoms:
        key = (line, who)
        if key not in dedup or conf > dedup[key]:
            dedup[key] = conf

    result: List[Tuple[int, str, float]] = []
    for (line, who), conf in sorted(dedup.items()):
        result.append((line, who, conf))
    return result

# ============================================================
# FULL MODE PLACEHOLDERS (DISABLED)
# ============================================================

def full_causal_links(segments: List[Segment]):
    """
    Placeholder for future FULL reasoning:
    e.g. (causes line:46 line:48 retreat :confidence 0.7)
    Currently disabled via ENABLE_FULL.
    """
    if not ENABLE_FULL:
        return []
    # TODO: implement later
    return []

def full_relationships(segments: List[Segment]):
    """
    Placeholder for inferred relationships:
    e.g. (trusts Kyreth Torhh :confidence 0.6)
    """
    if not ENABLE_FULL:
        return []
    # TODO: implement later
    return []

# ============================================================
# METTA OUTPUT
# ============================================================

def write_metta(
    path: str,
    speakers: List[Tuple[int, str, float]],
    pronouns: List[Tuple[int, str, float]],
    emotions: List[Tuple[int, str, str, float]],
    actions: List[Tuple[int, str, float]],
    thoughts: List[Tuple[int, str, float]],
) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write("; PASS2 CORE++ INFERENCES\n\n")

        # Speakers
        f.write("; ---- Speaker Inference ----\n")
        for line, name, conf in speakers:
            f.write(f"(speaker line:{line} {name} :confidence {conf:.2f})\n")
        f.write("\n")

        # Pronouns
        f.write("; ---- Pronoun \u2192 Actor ----\n")
        for line, name, conf in pronouns:
            f.write(f"(actor line:{line} {name} :confidence {conf:.2f})\n")
        f.write("\n")

        # Emotions
        f.write("; ---- Emotions ----\n")
        for line, subj, emo, conf in emotions:
            f.write(
                f"(emotion line:{line} {subj} {emo} :confidence {conf:.2f})\n"
            )
        f.write("\n")

        # Actions
        f.write("; ---- Actions ----\n")
        for line, act, conf in actions:
            f.write(f"(action line:{line} {act} :confidence {conf:.2f})\n")
        f.write("\n")

        # Thoughts
        f.write("; ---- Thoughts ----\n")
        for line, who, conf in thoughts:
            f.write(f"(thought line:{line} {who} :confidence {conf:.2f})\n")
        f.write("\n")

# ============================================================
# MAIN
# ============================================================

def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: pass2_core.py <pass1_output.txt>")
        sys.exit(1)

    infile = sys.argv[1]
    segments = load_segments(infile)

    speakers = infer_speakers(segments)
    pronouns = infer_pronouns(segments)
    emotions = infer_emotions(segments)
    actions = infer_actions(segments)
    thoughts = infer_thoughts(segments)

    base = os.path.basename(infile)
    # Strip common bits like .txt and optional out_pass1_ prefix
    base_noext = base
    if base_noext.endswith(".txt"):
        base_noext = base_noext[:-4]
    base_noext = base_noext.replace("out_pass1_", "")

    outfile = f"out_pass2_{base_noext}.metta"
    write_metta(outfile, speakers, pronouns, emotions, actions, thoughts)
    print(f"[PASS2] Wrote \u2192 {outfile}")

if __name__ == "__main__":
    main()
