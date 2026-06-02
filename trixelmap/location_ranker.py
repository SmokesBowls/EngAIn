#!/usr/bin/env python3
"""
trixelmap/location_ranker.py
Consumes vault spatial evidence and produces a ranked Location Authority Registry.
Architecture: Evidence → Scoring → Tiered Registry → JSON/MD Report.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple

# ─── Authority Signals (Weights) ───────────────────────────────────────────────
WEIGHT_MULTI_FILE = 5.0
WEIGHT_SPATIAL_EVIDENCE = 5.0
WEIGHT_PROPER_NOUN = 3.0
WEIGHT_TERRAIN_SUFFIX = 3.0
WEIGHT_CANON_ALIAS = 4.0

PENALTY_COMMON_WORD = 10.0
PENALTY_PRONOUN_PHRASE = 10.0
PENALTY_DIALOGUE_FRAGMENT = 10.0
PENALTY_SINGLE_CHAR = 5.0

# ─── Dictionaries ───────────────────────────────────────────────────────────────
COMMON_ENGLISH_WORDS = frozenset({
    "orange", "strange", "return", "split", "threshold", "presence_begins",
    "isfet", "garden", "grove", "keep", "camp", "home", "water",
    "just", "my", "our", "welcome", "we", "you", "the", "a", "an", "and", "but"
})

PRONOUN_PHRASES = frozenset({
    "my_home", "our_home", "your_home", "their_home", "we_camp", "you_keep",
    "my_place", "our_place", "your_place", "their_place"
})

DIALOGUE_FRAGMENTS = frozenset({
    "just_water", "some_water", "the_water", "a_home", "the_home", "our_home",
    "welcome_home", "we_camp", "you_keep", "my_home", "just_home"
})

TERRAIN_SUFFIXES = frozenset({
    "valley", "needle", "ridge", "mountain", "range", "marsh", "forest",
    "plains", "expanse", "spire", "caldera", "basin", "shelf", "home",
    "water", "village", "settlement", "camp", "tower", "keep", "island",
    "void", "earth", "mars"
})

CANON_LOCATIONS = frozenset({
    "star_needle", "falcon_ridge", "sundrift_valley", "echo_tower",
    "ironspire", "tidecaller_mountain", "nephoretti_marsh",
    "crescent_mountain_range", "void_spire", "earth_void_spire", "mars_void_spire"
})

def score_location(lid: str, data: Dict) -> Tuple[float, str]:
    """
    Scores a location based on authority signals.
    Returns (score, tier) where tier is "CONFIRMED", "CANDIDATE", or "LOW_CONFIDENCE".
    """
    score = 0.0
    reasons = []

    # 1. Multi-file appearance
    files = data.get("files_mentioned", [])
    if len(files) > 1:
        score += WEIGHT_MULTI_FILE * len(files)
        reasons.append(f"Multi-file ({len(files)})")

    # 2. Spatial evidence
    evidence = data.get("evidence", [])
    if len(evidence) > 0:
        score += WEIGHT_SPATIAL_EVIDENCE * len(evidence)
        reasons.append(f"Spatial evidence ({len(evidence)})")

    # 3. Proper noun (TitleCase in aliases)
    aliases = data.get("aliases", [])
    has_proper_noun = any(a[0].isupper() for a in aliases if a)
    if has_proper_noun:
        score += WEIGHT_PROPER_NOUN
        reasons.append("Proper noun")

    # 4. Terrain suffix
    suffix = lid.rsplit("_", 1)[-1]
    if suffix in TERRAIN_SUFFIXES:
        score += WEIGHT_TERRAIN_SUFFIX
        reasons.append(f"Terrain suffix ({suffix})")

    # 5. Canon alias
    if lid in CANON_LOCATIONS:
        score += WEIGHT_CANON_ALIAS
        reasons.append("Canon location")

    # Penalties
    if lid in COMMON_ENGLISH_WORDS:
        score -= PENALTY_COMMON_WORD
        reasons.append("Common word (-10)")

    if lid in PRONOUN_PHRASES:
        score -= PENALTY_PRONOUN_PHRASE
        reasons.append("Pronoun phrase (-10)")

    if lid in DIALOGUE_FRAGMENTS:
        score -= PENALTY_DIALOGUE_FRAGMENT
        reasons.append("Dialogue fragment (-10)")

    if len(lid) <= 3:
        score -= PENALTY_SINGLE_CHAR
        reasons.append("Too short (-5)")

    # Tier assignment
    if score >= 10.0:
        tier = "CONFIRMED"
    elif score >= 3.0:
        tier = "CANDIDATE"
    else:
        tier = "LOW_CONFIDENCE"

    return round(score, 2), tier

def generate_registry(evidence_path: str, output_dir: str):
    """Generates ranked registry from vault spatial evidence."""
    evidence = json.loads(Path(evidence_path).read_text())
    registry = {"CONFIRMED": [], "CANDIDATE": [], "LOW_CONFIDENCE": []}

    for lid, data in evidence.items():
        score, tier = score_location(lid, data)
        entry = {
            "id": lid,
            "score": score,
            "tier": tier,
            "files": data.get("files_mentioned", []),
            "evidence_count": len(data.get("evidence", [])),
            "aliases": data.get("aliases", []),
            "conflicts": data.get("conflicts", [])
        }
        registry[tier].append(entry)

    # Sort by score descending
    for tier in registry:
        registry[tier].sort(key=lambda x: x["score"], reverse=True)

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # JSON Registry
    (out / "location_authority_registry.json").write_text(
        json.dumps(registry, indent=2, ensure_ascii=False)
    )

    # MD Report
    lines = ["# Location Authority Registry\n"]
    for tier in ["CONFIRMED", "CANDIDATE", "LOW_CONFIDENCE"]:
        lines.append(f"## {tier}\n")
        for entry in registry[tier]:
            lines.append(f"### `{entry['id']}` (score: {entry['score']})")
            lines.append(f"- **Files:** {', '.join(entry['files'])}")
            lines.append(f"- **Evidence:** {entry['evidence_count']} spatial claims")
            if entry['conflicts']:
                lines.append(f"- **⚠️ Conflicts:** {'; '.join(entry['conflicts'])}")
            lines.append("")
    (out / "location_authority_report.md").write_text("\n".join(lines))

    print(f"[ranker] Registry written: {out / 'location_authority_registry.json'}")
    print(f"[ranker] Report written: {out / 'location_authority_report.md'}")
    print(f"[ranker] Summary: {len(registry['CONFIRMED'])} confirmed, {len(registry['CANDIDATE'])} candidates, {len(registry['LOW_CONFIDENCE'])} low confidence")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Location Authority Ranker")
    parser.add_argument("--evidence", required=True, help="Path to location_spatial_evidence.json")
    parser.add_argument("--output-dir", default="trixelmap/out/registry", help="Output directory")
    args = parser.parse_args()
    generate_registry(args.evidence, args.output_dir)
