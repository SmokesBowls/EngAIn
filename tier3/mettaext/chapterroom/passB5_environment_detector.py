#!/usr/bin/env python3
"""
passB5_environment_detector.py — EngAIn Chapterroom · Pass B5

ROLE: Environment Detector
  Reads a Pass B scene boundary proposal and adds an environment block
  to each scene. Does not write scene packets — that is Pass C's job.

WHAT IT DOES:
  - Detects terrain_family from scene text keywords
  - Detects region hints
  - Collects raw environment sentences (sky, ground, water, weather, sound, light)
  - Collects boundary hints (walls, gates, cliffs, edges, barriers)
  - Collects hazard hints (poison, fire, collapse, flood, darkness)
  - Collects path hints (roads, bridges, tunnels, rivers, trails)
  - Collects atmospheric hints (hum, pulse, silence, color, wind)
  - Writes: out_passB5_<chapter_id>.json

DOES NOT:
  - Extract MrLore claims
  - Decide canon status
  - Write scene packets
  - Touch Godot or runtime

CONTRACT IN:
  engain.scene_boundary_proposal.v1  (Pass B output)

CONTRACT OUT:
  engain.scene_environment_proposal.v1
  Extends each scene with an "environment" block.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


CONTRACT_IN  = "engain.scene_boundary_proposal.v1"
CONTRACT_OUT = "engain.scene_environment_proposal.v1"


# ── Terrain family keywords ──────────────────────────────────────────────────

_TERRAIN_PROFILES: list[tuple[str, list[str]]] = [
    ("cosmic",   ["void", "star", "stellar", "nebula", "orbit", "cosmos", "space",
                  "dimension", "celestial", "astral", "ethereal realm", "akashic",
                  "dimensional", "frequency", "vrill", "thought-seed", "consciousness"]),
    ("coastal",  ["ocean", "sea", "shore", "beach", "wave", "tide", "coast",
                  "salt", "sand", "surf", "bay", "cove", "lagoon", "shallows"]),
    ("forest",   ["forest", "tree", "jungle", "canopy", "undergrowth", "fern",
                  "woodland", "grove", "thicket", "branches", "roots", "bark"]),
    ("mountain", ["mountain", "peak", "cliff", "ridge", "summit", "glacier",
                  "highland", "canyon", "ravine", "gorge", "plateau", "alpine"]),
    ("desert",   ["desert", "dune", "sand", "arid", "drought", "wasteland",
                  "scrub", "parched", "dust", "scorched", "basin"]),
    ("swamp",    ["swamp", "marsh", "bog", "wetland", "mire", "reed", "mud",
                  "murky", "stagnant", "mangrove", "fen"]),
    ("cave",     ["cave", "cavern", "tunnel", "underground", "stalactite",
                  "stalagmite", "dark passage", "grotto", "subterranean"]),
    ("ruins",    ["ruin", "rubble", "collapsed", "ancient structure", "crumbled",
                  "overgrown", "abandoned", "derelict", "remnant", "debris"]),
    ("urban",    ["city", "town", "street", "building", "wall", "gate", "tower",
                  "market", "district", "plaza", "courtyard", "alley"]),
    ("cosmic",   ["dying star", "solar", "fusion", "supernova", "pulsar",
                  "gravity", "gravitational"]),
]

# ── Environment sentence patterns ────────────────────────────────────────────

_ENV_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("sky",        re.compile(r"\b(sky|cloud|sun|moon|star|horizon|dawn|dusk|night|day|light|dark|eclipse)\b", re.I)),
    ("ground",     re.compile(r"\b(ground|earth|soil|floor|surface|stone|rock|grass|sand|mud|dirt)\b", re.I)),
    ("water",      re.compile(r"\b(water|river|lake|ocean|sea|rain|flood|stream|pool|puddle|mist|fog)\b", re.I)),
    ("weather",    re.compile(r"\b(wind|storm|rain|snow|hail|thunder|lightning|heat|cold|frost|blizzard)\b", re.I)),
    ("sound",      re.compile(r"\b(sound|noise|silence|hum|vibrat|echo|reverberat|quiet|loud|rumble|pulse)\b", re.I)),
    ("light",      re.compile(r"\b(light|dark|shadow|glow|shimmer|flash|bright|dim|illuminate|luminous)\b", re.I)),
    ("atmosphere", re.compile(r"\b(air|smell|scent|odor|breath|pressure|temperature|humid|dry|damp|thick)\b", re.I)),
]

_BOUNDARY_PATTERNS = re.compile(
    r"\b(wall|gate|door|fence|barrier|cliff|edge|border|boundary|threshold|"
    r"limit|end|blocked|sealed|closed|locked|barred|fortif)\w*\b", re.I
)

_HAZARD_PATTERNS = re.compile(
    r"\b(poison|toxic|danger|hazard|trap|collapse|flood|fire|burning|acid|"
    r"shadow shape|patrol|ambush|infect|plague|radiation|null zone)\w*\b", re.I
)

_PATH_PATTERNS = re.compile(
    r"\b(road|path|trail|bridge|tunnel|passage|corridor|route|ford|crossing|"
    r"river crossing|gate|doorway|entrance|exit|stairway|ramp)\w*\b", re.I
)

_ATMOSPHERIC_PATTERNS = re.compile(
    r"\b(hum|pulse|vibrat|resonate|frequency|Hz|silence|dampened|echo|color|"
    r"white sky|red sky|black sky|painted sky|tinted)\w*\b", re.I
)


# ── Core detection ────────────────────────────────────────────────────────────

def detect_terrain_family(text: str) -> str:
    """Score each terrain profile and return the best match."""
    text_lower = text.lower()
    scores: dict[str, int] = {}

    for profile, keywords in _TERRAIN_PROFILES:
        count = sum(1 for kw in keywords if kw in text_lower)
        if count > 0:
            scores[profile] = scores.get(profile, 0) + count

    if not scores:
        return "default"

    return max(scores, key=lambda p: scores[p])


def detect_region(text: str) -> str:
    """Very rough region hint from scene text."""
    text_lower = text.lower()

    if any(w in text_lower for w in ["north", "northern"]):
        return "north"
    if any(w in text_lower for w in ["south", "southern"]):
        return "south"
    if any(w in text_lower for w in ["east", "eastern"]):
        return "east"
    if any(w in text_lower for w in ["west", "western"]):
        return "west"
    if any(w in text_lower for w in ["ethereal", "dimension", "void", "akashic"]):
        return "ethereal"
    return "unknown"


def collect_environment_sentences(text: str) -> list[str]:
    """Return sentences that contain environment keywords."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    result = []
    for sentence in sentences:
        s = sentence.strip()
        if not s:
            continue
        for _label, pattern in _ENV_PATTERNS:
            if pattern.search(s):
                result.append(s)
                break
    return result[:20]  # cap at 20 to keep packets lean


def collect_hints(text: str, pattern: re.Pattern) -> list[str]:
    """Return unique matched hint strings from text."""
    matches = pattern.findall(text)
    seen = set()
    result = []
    for m in matches:
        m_lower = m.lower()
        if m_lower not in seen:
            seen.add(m_lower)
            result.append(m_lower)
    return result


def detect_environment(text: str) -> dict[str, Any]:
    """
    Detect environment signals from scene text.

    Returns a structured environment block ready for the scene packet.
    All fields are PROPOSED — MrLore decides canon status later.
    """
    return {
        "status": "PROPOSED",
        "terrain_family": detect_terrain_family(text),
        "region": detect_region(text),
        "raw_environment_sentences": collect_environment_sentences(text),
        "boundary_hints": collect_hints(text, _BOUNDARY_PATTERNS),
        "hazard_hints": collect_hints(text, _HAZARD_PATTERNS),
        "path_hints": collect_hints(text, _PATH_PATTERNS),
        "atmospheric_hints": collect_hints(text, _ATMOSPHERIC_PATTERNS),
    }


# ── Pass B5 main function ─────────────────────────────────────────────────────

def detect_environments(proposal: dict[str, Any]) -> dict[str, Any]:
    """
    Add an environment block to every scene in a Pass B proposal.

    Returns the extended proposal (does not mutate in place).
    """
    scenes = proposal.get("scenes", [])
    extended_scenes = []

    for scene in scenes:
        extended = dict(scene)
        extended["environment"] = detect_environment(scene.get("text", ""))
        extended_scenes.append(extended)

    result = dict(proposal)
    result["contract"] = CONTRACT_OUT
    result["scenes"] = extended_scenes
    result["passB5_complete"] = True
    return result


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="EngAIn Chapterroom · Pass B5 — Environment Detector"
    )
    parser.add_argument("passB_proposal", help="Pass B JSON proposal file.")
    parser.add_argument(
        "--output", "-o", default=None,
        help="Output path (default: out_passB5_<chapter_id>.json beside input)."
    )
    args = parser.parse_args()

    input_path = Path(args.passB_proposal).resolve()
    if not input_path.exists():
        print(f"[PASS B5] ERROR: file not found: {input_path}", file=sys.stderr)
        return 1

    proposal = json.loads(input_path.read_text(encoding="utf-8"))
    result = detect_environments(proposal)

    safe_chapter = result["chapter_id"].replace("/", "_")
    out_path = Path(args.output) if args.output else (
        input_path.parent / f"out_passB5_{safe_chapter}.json"
    )
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    scene_count = len(result["scenes"])
    terrain_counts: dict[str, int] = {}
    for scene in result["scenes"]:
        tf = scene["environment"]["terrain_family"]
        terrain_counts[tf] = terrain_counts.get(tf, 0) + 1

    print("[PASS B5] ENVIRONMENT_DETECTOR_COMPLETE = TRUE")
    print(f"[PASS B5] CHAPTER_ID   = {result['chapter_id']}")
    print(f"[PASS B5] SCENE_COUNT  = {scene_count}")
    print(f"[PASS B5] TERRAIN_MIX  = {terrain_counts}")
    print(f"[PASS B5] WROTE        = {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
