#!/usr/bin/env python3
"""
pass2_event_builder.py

Builds structured runtime-ready events from:
1. Pass1 segmented text
2. Pass2 enhanced .metta inference output

Purpose:
- Convert clean semantic atoms into structured events
- Keep physical, cognitive, emotional, and observation events separate
- Avoid spawning junk abstract entities
- Avoid treating pronouns as actors
"""

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Any


TYPE_RE = re.compile(
    r'^\{type:(?P<type>[a-z_]+)'
    r'(?:,\s*speaker:(?P<speaker>[A-Za-z_]+))?\}\s*(?P<text>.*)$'
)

CHAR_RE = re.compile(r"^; (?P<name>[A-Za-z][A-Za-z0-9_-]*): (?P<count>\d+) mentions")
SPEAKER_RE = re.compile(r"^\(speaker line:(?P<line>\d+) (?P<actor>[A-Za-z0-9_-]+) :confidence (?P<conf>[0-9.]+)\)")
EMOTION_RE = re.compile(r"^\(emotion line:(?P<line>\d+) (?P<actor>[A-Za-z0-9_-]+) (?P<emotion>[A-Za-z0-9_-]+) :confidence (?P<conf>[0-9.]+)\)")
ACTION_RE = re.compile(r"^\(action line:(?P<line>\d+) (?P<action>[A-Za-z0-9_-]+) :confidence (?P<conf>[0-9.]+)\)")
THOUGHT_RE = re.compile(r"^\(thought line:(?P<line>\d+) (?P<actor>[A-Za-z0-9_-]+) :confidence (?P<conf>[0-9.]+)\)")


PRONOUNS = {
    "he", "she", "they", "him", "her", "them", "his", "hers", "their", "theirs", "it", "its"
}

ALIAS_MAP = {
    "Sage": "Zephyr",
    "the Sage": "Zephyr",
    "the Giant": "Torrhen",
}

# Mirrors pass2_entity_filter WHITELIST — proper lore names never plural-classified
ACTOR_WHITELIST = {
    "Nephoretti", "Pelagor", "Lyaris", "Theron",
    "Vaelith", "Korath", "Mordain", "Syreth", "Marduk",
}


def resolve_alias(name: Optional[str]) -> Optional[str]:
    if not name:
        return name
    return ALIAS_MAP.get(name, name)


def classify_actor_type(name: Optional[str]) -> str:
    """Return 'group' if the name looks plural, 'individual' otherwise."""
    if not name:
        return "individual"
    if name in ACTOR_WHITELIST:
        return "individual"
    if name.endswith("s"):
        return "group"
    return "individual"


PHYSICAL_ACTIONS = {
    "attack",
    "retreat",
    "approach",
    "advance",
    "flee",
    "gather",
    "huddle",
    "submission",
    "kneel",
}

COGNITIVE_ACTIONS = {
    "observe",
    "question",
    "respond",
    "speak",
}

MAGIC_ACTIONS = {
    "shaping",
    "vrill_manipulation",
    "vrill_energy",
    "vrel_flow",
    "vrel_potential",
    "vrel_interference",
    "vrel_vibration",
    "vrel_resonance",
    "creation",
    "manipulation",
}


@dataclass
class Segment:
    line: int
    type: str
    speaker: Optional[str]
    text: str


def load_segments(path: str) -> Dict[int, Segment]:
    segments: Dict[int, Segment] = {}

    with open(path, "r", encoding="utf-8") as f:
        for idx, raw in enumerate(f, start=1):
            line = raw.rstrip("\n")
            match = TYPE_RE.match(line.strip())
            if not match:
                continue

            speaker = match.group("speaker")
            if speaker and speaker.lower() in PRONOUNS:
                speaker = None

            segments[idx] = Segment(
                line=idx,
                type=match.group("type"),
                speaker=speaker,
                text=match.group("text") or "",
            )

    return segments


def load_metta(path: str) -> Dict[str, Any]:
    data: Dict[str, Any] = {
        "characters": {},
        "speakers": [],
        "emotions": [],
        "actions": [],
        "thoughts": [],
    }

    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()

            m = CHAR_RE.match(line)
            if m:
                data["characters"][m.group("name")] = int(m.group("count"))
                continue

            m = SPEAKER_RE.match(line)
            if m:
                actor = m.group("actor")
                if actor.lower() not in PRONOUNS:
                    data["speakers"].append({
                        "line": int(m.group("line")),
                        "actor": actor,
                        "confidence": float(m.group("conf")),
                    })
                continue

            m = EMOTION_RE.match(line)
            if m:
                actor = m.group("actor")
                if actor.lower() not in PRONOUNS:
                    data["emotions"].append({
                        "line": int(m.group("line")),
                        "actor": actor,
                        "emotion": m.group("emotion"),
                        "confidence": float(m.group("conf")),
                    })
                continue

            m = ACTION_RE.match(line)
            if m:
                data["actions"].append({
                    "line": int(m.group("line")),
                    "action": m.group("action"),
                    "confidence": float(m.group("conf")),
                })
                continue

            m = THOUGHT_RE.match(line)
            if m:
                actor = m.group("actor")
                if actor.lower() not in PRONOUNS:
                    data["thoughts"].append({
                        "line": int(m.group("line")),
                        "actor": actor,
                        "confidence": float(m.group("conf")),
                    })
                continue

    return data


def nearest_actor(
    line_no: int,
    segments: Dict[int, Segment],
    characters: Dict[str, int],
    speaker_map: Dict[int, str],
    window: int = 8,
) -> Optional[str]:
    if line_no in speaker_map:
        resolved = speaker_map[line_no]
        return ALIAS_MAP.get(resolved, resolved)

    for line in range(line_no, max(0, line_no - window), -1):
        seg = segments.get(line)
        if not seg:
            continue

        if seg.speaker and seg.speaker in characters:
            resolved = seg.speaker
            return ALIAS_MAP.get(resolved, resolved)

        text = (seg.text or "").lower()

        # --- anonymous actor detection (HIGH PRIORITY) ---
        ANON_PATTERNS = [
            (r"\b(pelagor)\b", "Pelagor"),  # allow species-level actor
            (r"\b(creature|being|figure)\b", "entity_unknown"),
            (r"\b(group|others|many|several)\b", "group_unknown"),
            (r"\b(they|them)\b", "group_unknown"),
        ]

        for pattern, label in ANON_PATTERNS:
            if re.search(pattern, text):
                return label

        # --- fallback to named characters ---
        for name in characters:
            if re.search(rf"\b{re.escape(name.lower())}\b", text):
                resolved = name
                return ALIAS_MAP.get(resolved, resolved)

    return None


def classify_action(action: str) -> str:
    if action in PHYSICAL_ACTIONS:
        return "physical_event"
    if action in MAGIC_ACTIONS:
        return "system_event"
    if action in COGNITIVE_ACTIONS:
        return "cognitive_event"
    return "semantic_event"


def context_excerpt(line_no: int, segments: Dict[int, Segment], radius: int = 1) -> str:
    parts: List[str] = []

    for line in range(max(1, line_no - radius), line_no + radius + 1):
        seg = segments.get(line)
        if seg and seg.text:
            parts.append(seg.text.strip())

    return " ".join(parts).strip()


def extract_target(text: str) -> Optional[str]:
    text = (text or "").lower()

    target_patterns = [
        (r"\b(stone|stones|rock|rocks|boulder|boulders|cliff|cliffs)\b", "stone"),
        (r"\b(water|waters|pool|pools|ocean|oceans|sea|seas)\b", "water"),
        (r"\b(ground|earth|soil|land)\b", "earth"),
        (r"\b(vrill|current|currents|flow|flows)\b", "vrill"),
        (r"\b(body|form|physical form|flesh)\b", "body"),
    ]

    for pattern, label in target_patterns:
        if re.search(pattern, text):
            return label

    return None


def build_events(pass1_path: str, metta_path: str) -> Dict[str, Any]:
    segments = load_segments(pass1_path)
    metta = load_metta(metta_path)

    characters: Dict[str, int] = metta["characters"]
    speaker_map = {
        item["line"]: item["actor"]
        for item in metta["speakers"]
        if item["actor"] in characters
    }

    events: List[Dict[str, Any]] = []
    event_id = 1

    for item in metta["actions"]:
        line_no = item["line"]
        actor = nearest_actor(line_no, segments, characters, speaker_map)

        if not actor:
            continue

        action = item["action"]
        event_type = classify_action(action)
        excerpt = context_excerpt(line_no, segments)
        if event_type == "system_event":
            target = extract_target(excerpt)
        elif event_type == "physical_event" and action not in {"retreat", "flee", "approach", "advance", "gather", "huddle"}:
            target = extract_target(excerpt)
        else:
            target = None

        events.append({
            "event_id": f"evt_{event_id:04d}",
            "source": "pass2_event_builder",
            "line": line_no,
            "type": event_type,
            "actor": actor,
            "actor_type": classify_actor_type(actor),
            "action": action,
            "target": target,
            "confidence": item["confidence"],
            "renderable": event_type in {"physical_event", "system_event"},
            "excerpt": excerpt,
        })
        event_id += 1

    for item in metta["emotions"]:
        actor = resolve_alias(item["actor"])
        if actor not in characters:
            continue

        events.append({
            "event_id": f"evt_{event_id:04d}",
            "source": "pass2_event_builder",
            "line": item["line"],
            "type": "state_change",
            "actor": actor,
            "actor_type": classify_actor_type(actor),
            "action": "enter_emotional_state",
            "state": item["emotion"],
            "target": None,
            "confidence": item["confidence"],
            "renderable": False,
            "excerpt": context_excerpt(item["line"], segments),
        })
        event_id += 1

    for item in metta["thoughts"]:
        actor = resolve_alias(item["actor"])
        if actor not in characters:
            continue

        events.append({
            "event_id": f"evt_{event_id:04d}",
            "source": "pass2_event_builder",
            "line": item["line"],
            "type": "thought_event",
            "actor": actor,
            "actor_type": classify_actor_type(actor),
            "action": "think",
            "target": None,
            "confidence": item["confidence"],
            "renderable": False,
            "excerpt": context_excerpt(item["line"], segments),
        })
        event_id += 1

    events.sort(key=lambda e: (e["line"], e["event_id"]))

    return {
        "source_pass1": pass1_path,
        "source_metta": metta_path,
        "character_count": len(characters),
        "event_count": len(events),
        "renderable_event_count": sum(1 for e in events if e.get("renderable")),
        "nonrenderable_event_count": sum(1 for e in events if not e.get("renderable")),
        "characters": sorted(characters.keys()),
        "events": events,
    }


def default_output_path(metta_path: str) -> str:
    base = os.path.basename(metta_path)

    if base.startswith("out_pass2_"):
        base = base[len("out_pass2_"):]

    if base.endswith(".metta"):
        base = base[:-len(".metta")]

    return os.path.join(os.path.dirname(metta_path), f"out_events_{base}.json")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build structured events from Pass1 text and Pass2 enhanced .metta output."
    )
    parser.add_argument("pass1", help="Path to matching out_pass1_*.txt file")
    parser.add_argument("metta", help="Path to matching out_pass2_*.metta file")
    parser.add_argument("outfile", nargs="?", help="Optional output JSON file")

    args = parser.parse_args()

    if not os.path.exists(args.pass1):
        print(f"ERROR: Pass1 file not found: {args.pass1}")
        sys.exit(1)

    if not os.path.exists(args.metta):
        print(f"ERROR: Pass2 metta file not found: {args.metta}")
        sys.exit(1)

    outfile = args.outfile or default_output_path(args.metta)
    os.makedirs(os.path.dirname(outfile) or ".", exist_ok=True)

    result = build_events(args.pass1, args.metta)

    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"[EVENT BUILDER] Characters: {result['character_count']}")
    print(f"[EVENT BUILDER] Events: {result['event_count']}")
    print(f"[EVENT BUILDER] Renderable: {result['renderable_event_count']}")
    print(f"[EVENT BUILDER] Non-renderable: {result['nonrenderable_event_count']}")
    print(f"[EVENT BUILDER] Wrote → {outfile}")


if __name__ == "__main__":
    main()
