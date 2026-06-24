#!/usr/bin/env python3
import re
import sys
from pathlib import Path

# --- Speech verbs --------------------------------------------------------

SPEECH_VERBS = (
    "said", "asked", "whispered", "murmured", "replied", "shouted",
    "called", "answered", "observed", "confirmed", "added", "reported",
    "noted", "admitted", "agreed", "continued", "began", "interrupted",
    "conceded", "declared", "acknowledged", "responded", "concluded",
    "insisted", "corrected", "explained", "suggested", "proposed",
    "commanded", "instructed", "requested", "urged", "warned", "promised",
    "announced", "stated", "offered", "protested", "objected", "clarified",
    "reminded", "assured", "argued", "breathed", "muttered", "summarized",
    "decided", "finished", "repeated", "cautioned", "countered", "pointed",
    "pressed", "projected", "extended", "realized", "thought",
)
_VERB_ALT = "|".join(re.escape(v) for v in SPEECH_VERBS)

# --- Regexes -------------------------------------------------------------

HEADER_RE = re.compile(r'^\s*(#|=+|-{3,})')
THOUGHT_LINE_RE = re.compile(r'^\s*\*(?P<thought>.+?)\*\s*$')

INLINE_THOUGHT_RE = re.compile(
    r'\*(?P<thought>[^*]+)\*\s*(?P<rest>.*?(?P<speaker>[A-Z][a-zA-Z]+)\s+'
    r'(?P<verb>thought|wondered|realized|considered|mused)\b.*)',
    re.IGNORECASE,
)

DIALOGUE_SPEAKER_RE = re.compile(
    r'^(?P<quote>[""].+?[""])'
    r'(?:\s*,?\s*(?P<speaker>[A-Z][a-zA-Z]+)\s+'
    r'(?P<verb>' + _VERB_ALT + r')\b.*)?',
    re.IGNORECASE,
)

# Next-line attribution: "said Mordain," or "added Syreth,"
CONTINUATION_VERB_NAME_RE = re.compile(
    r'^(?P<verb>' + _VERB_ALT + r')\s+(?P<speaker>[A-Z][a-zA-Z]{2,})\s*[,\.]',
    re.IGNORECASE,
)

# Next-line attribution: "Mordain said," or "Senareth commanded,"
CONTINUATION_NAME_VERB_RE = re.compile(
    r'^(?P<speaker>[A-Z][a-zA-Z]{2,})\s+(?P<verb>' + _VERB_ALT + r')\b',
    re.IGNORECASE,
)

DIALOGUE_START_RE = re.compile(r'^[""].+')
SENTENCE_SPLIT_RE = re.compile(r'(?<=[.!?])\s+(?=[A-Z""])')


# --- Core helpers --------------------------------------------------------


def split_sentences(text: str):
    """
    Very simple sentence splitter: splits on . ? ! followed by space + capital/".
    """
    text = text.strip()
    if not text:
        return []
    parts = SENTENCE_SPLIT_RE.split(text)
    return [p.strip() for p in parts if p.strip()]


def emit_line(type_, text, speaker=None):
    """
    Build a single semantic-unit output line.
    """
    meta_parts = [f"type:{type_}"]
    if speaker is not None:
        meta_parts.append(f"speaker:{speaker}")
    meta = "{" + ", ".join(meta_parts) + "}"
    return f"{meta} {text}".rstrip() + "\n"


# --- Processing of a single raw line ------------------------------------


def process_raw_line(line: str):
    """
    Takes a raw line of text and yields zero or more semantic-unit lines.
    """
    stripped = line.rstrip("\n")

    # Blank line
    if stripped.strip() == "":
        yield emit_line("blank", "")
        return

    # Scene/header line
    if HEADER_RE.match(stripped):
        yield emit_line("scene_header", stripped)
        return

    # Full-line internal monologue: *thought*
    m = THOUGHT_LINE_RE.match(stripped)
    if m:
        thought = m.group("thought").strip()
        yield emit_line("internal_monologue", f'"{thought}"', speaker="unknown")
        return

    # Inline thought pattern: *thought* Senareth thought...
    m = INLINE_THOUGHT_RE.search(stripped)
    if m:
        thought = m.group("thought").strip()
        rest = m.group("rest").strip()
        speaker = m.group("speaker")
        # 1) internal monologue unit
        yield emit_line("internal_monologue", f'"{thought}"', speaker=speaker)
        # 2) remaining narration part (if any meaningful text)
        if rest:
            yield emit_line("narration", rest)
        return

    # Dialogue with optional explicit speaker
    m = DIALOGUE_SPEAKER_RE.match(stripped)
    if m:
        quote = m.group("quote").strip()
        speaker = m.group("speaker")
        # Dialogue line (keep full quote text)
        if speaker:
            yield emit_line("dialogue", quote, speaker=speaker)
        else:
            yield emit_line("dialogue", quote, speaker="unknown")

        # Anything after the quote (narration tail)
        tail = stripped[len(m.group(0)) :].strip()
        if tail:
            # If tail starts with punctuation/comma, strip it
            tail = tail.lstrip(",;: ")
            if tail:
                yield emit_line("narration", tail)
        return

    # Dialogue without speaker (line starts with quote)
    if DIALOGUE_START_RE.match(stripped):
        # We still treat the whole line as a dialogue unit
        yield emit_line("dialogue", stripped, speaker="unknown")
        return

    # Default: narration, possibly multi-sentence
    for sent in split_sentences(stripped):
        yield emit_line("narration", sent)


# --- File-level driver ---------------------------------------------------


def process_file(in_path: Path, out_path: Path):
    with in_path.open("r", encoding="utf-8") as fin:
        raw_lines = fin.readlines()

    lines = [l.rstrip("\n") for l in raw_lines]

    with out_path.open("w", encoding="utf-8") as fout:
        i = 0
        while i < len(lines):
            stripped = lines[i]
            sstripped = stripped.strip()

            diag_m = DIALOGUE_SPEAKER_RE.match(sstripped)
            # A line is "bare dialogue" if it starts with a quote, the
            # DIALOGUE_SPEAKER_RE matched but found no inline speaker, and
            # there is no leftover tail on the same line (attribution is split
            # onto the next line by the author's prose style).
            if (
                diag_m is not None
                and DIALOGUE_START_RE.match(sstripped)
                and not diag_m.group("speaker")
                and not sstripped[diag_m.end():].strip()
                and i + 1 < len(lines)
            ):
                next_s = lines[i + 1].strip()
                speaker = None
                attr_end = 0

                cm = CONTINUATION_VERB_NAME_RE.match(next_s)
                if cm and cm.group("speaker")[0].isupper():
                    speaker = cm.group("speaker")
                    attr_end = cm.end()

                if not speaker:
                    cm = CONTINUATION_NAME_VERB_RE.match(next_s)
                    if cm and cm.group("speaker")[0].isupper():
                        speaker = cm.group("speaker")
                        attr_end = cm.end()

                if speaker:
                    fout.write(emit_line("dialogue", diag_m.group("quote"), speaker=speaker))
                    remainder = next_s[attr_end:].lstrip(" ,.")
                    if remainder.strip():
                        for out_line in process_raw_line(remainder):
                            fout.write(out_line)
                    i += 2
                    continue

            for out_line in process_raw_line(stripped):
                fout.write(out_line)
            i += 1


# --- CLI -----------------------------------------------------------------


# -------------------------------------------------------
# MAIN ENTRYPOINT
# -------------------------------------------------------

def main():
    # Usage:
    #   python3 pass1_explicit.py input.txt
    #   python3 pass1_explicit.py input.txt custom_output.txt

    if len(sys.argv) < 2:
        print("Usage: python3 pass1_explicit.py <input.txt> [output.txt]")
        sys.exit(1)

    input_path = Path(sys.argv[1])

    if not input_path.exists():
        print(f"ERROR: Input file does not exist: {input_path}")
        sys.exit(1)

    # Optional explicit output override
    if len(sys.argv) >= 3:
        output_path = Path(sys.argv[2])
    else:
        # AUTOGENERATE the output file name
        base = input_path.stem
        output_path = Path(f"out_pass1_{base}.txt")

    process_file(input_path, output_path)

    print(f"[PASS1] Done. Output → {output_path}")


# Run main() if executed directly
if __name__ == "__main__":
    main()
