#!/usr/bin/env python3
"""
trixelmap/vault_spatial_parser.py

Whole-vault location evidence extractor.
Scans all chapters, aggregates spatial clues, resolves aliases, detects conflicts,
and outputs structured evidence + human-readable report.

Usage:
  python trixelmap/vault_spatial_parser.py --vault-dir /path/to/obsidian/vault --output-dir trixelmap/out/vault
"""

import argparse
import json
import math
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

# Reuse existing pattern matcher for relationship extraction
from spatial_pattern_matcher import extract_spatial_facts, normalize_id, extract_location_mentions

# ─── Data Structures ──────────────────────────────────────────────────────────
@dataclass
class SpatialEvidence:
    file: str
    sentence: str
    relation: str
    anchor: str
    confidence: float
    terrain_hint: Optional[str] = None
    distance_hint: Optional[str] = None

@dataclass
class LocationRecord:
    canonical_id: str
    aliases: List[str] = field(default_factory=list)
    evidence: List[SpatialEvidence] = field(default_factory=list)
    files_mentioned: List[str] = field(default_factory=list)  # NEW
    terrain_hints: List[str] = field(default_factory=list)
    placement_status: str = "draft"
    authority_tier: int = 1
    confidence: float = 0.0
    score: float = 0.0
    conflicts: List[str] = field(default_factory=list)

# ─── Alias Resolver (Heuristic + Override) ────────────────────────────────────
ALIAS_OVERRIDES = {
    "sundrift": "sundrift_valley",
    "the valley": "sundrift_valley",
    "needle": "star_needle",
    "star": "star_needle",
    "ridge": "falcon_ridge",
    "falcon": "falcon_ridge",
    # Add more as vault grows
}

def resolve_canonical_id(raw_id: str) -> str:
    """Resolves aliases to canonical location IDs."""
    normalized = normalize_id(raw_id)
    if normalized in ALIAS_OVERRIDES:
        return ALIAS_OVERRIDES[normalized]
    # Fallback: substring match against known keys
    for key, val in ALIAS_OVERRIDES.items():
        if key in normalized or normalized in key:
            return val
    return normalized

# ─── Conflict Detector ────────────────────────────────────────────────────────
OPPOSITE_RELATIONS = {
    "north_of": "south_of",
    "south_of": "north_of",
    "east_of": "west_of",
    "west_of": "east_of",
    "above": "below",
    "below": "above",
}

def detect_conflicts(locations: Dict[str, LocationRecord]) -> Dict[str, List[str]]:
    """Finds contradictory spatial claims across the vault."""
    conflicts = {lid: [] for lid in locations}
    
    # Group evidence by (location, relation_type)
    relation_map = {}
    for lid, loc in locations.items():
        for ev in loc.evidence:
            key = (lid, ev.relation)
            relation_map.setdefault(key, []).append(ev.anchor)
            
    # Check for direct opposites
    for lid, loc in locations.items():
        for rel, anchors in relation_map.items():
            if rel[0] != lid: continue
            opp_rel = OPPOSITE_RELATIONS.get(rel[1])
            if opp_rel and (lid, opp_rel) in relation_map:
                opp_anchors = relation_map[(lid, opp_rel)]
                for a1 in anchors:
                    for a2 in opp_anchors:
                        if a1 == a2:  # Same anchor, opposite direction
                            msg = f"CONFLICT: {lid} claimed {rel[1]} {a1} and {opp_rel} {a2} across chapters"
                            if msg not in conflicts[lid]:
                                conflicts[lid].append(msg)
                                
    return conflicts


def score_location(loc: LocationRecord) -> float:
    """Calculates an authority score for a location based on signals and penalties."""
    score = 0.0
    lid = loc.canonical_id

    # 1. Multi-file appearance
    files = loc.files_mentioned
    if len(files) > 1:
        score += 5.0 * len(files)

    # 2. Spatial evidence
    evidence = loc.evidence
    if len(evidence) > 0:
        score += 5.0 * len(evidence)

    # 3. Proper noun (TitleCase in aliases)
    aliases = loc.aliases
    has_proper_noun = any(a[0].isupper() for a in aliases if a)
    if has_proper_noun:
        score += 3.0

    # 4. Terrain suffix
    suffix = lid.rsplit("_", 1)[-1]
    terrain_suffixes = {
        "valley", "needle", "ridge", "mountain", "range", "marsh", "forest",
        "plains", "expanse", "spire", "caldera", "basin", "shelf", "home",
        "water", "village", "settlement", "camp", "tower", "keep", "island",
        "void", "earth", "mars"
    }
    if suffix in terrain_suffixes:
        score += 3.0

    # 5. Canon alias
    canon_locations = {
        "star_needle", "falcon_ridge", "sundrift_valley", "echo_tower",
        "ironspire", "tidecaller_mountain", "nephoretti_marsh",
        "crescent_mountain_range", "void_spire", "earth_void_spire", "mars_void_spire"
    }
    if lid in canon_locations:
        score += 4.0

    # Penalties
    common_english_words = {
        "orange", "strange", "return", "split", "threshold", "presence_begins",
        "isfet", "garden", "grove", "keep", "camp", "home", "water",
        "just", "my", "our", "welcome", "we", "you", "the", "a", "an", "and", "but"
    }
    if lid in common_english_words or "water" in lid:
        score -= 10.0

    pronoun_phrases = {
        "my_home", "our_home", "your_home", "their_home", "we_camp", "you_keep",
        "my_place", "our_place", "your_place", "their_place"
    }
    if lid in pronoun_phrases:
        score -= 10.0

    dialogue_fragments = {
        "just_water", "some_water", "the_water", "a_home", "the_home", "our_home",
        "welcome_home", "we_camp", "you_keep", "my_home", "just_home"
    }
    if lid in dialogue_fragments or any(frag in lid for frag in dialogue_fragments):
        score -= 10.0

    if len(lid) <= 3:
        score -= 5.0

    return round(score, 2)


# ─── Vault Parser Core ────────────────────────────────────────────────────────
class VaultSpatialParser:
    def __init__(self, vault_dir: str):
        self.vault_dir = Path(vault_dir)
        self.locations: Dict[str, LocationRecord] = {}

    def parse_vault(self) -> Dict[str, LocationRecord]:
        source_files = []
        
        # Strictly match directories starting with "book_"
        book_dirs = sorted(self.vault_dir.glob("book_*"))
        
        for book_dir in book_dirs:
            if book_dir.is_dir():
                # Only match .md and .txt files directly inside (non-recursive)
                chapter_files = []
                chapter_files.extend(sorted(book_dir.glob("*.md")))
                chapter_files.extend(sorted(book_dir.glob("*.txt")))
                source_files.extend(chapter_files)
                
        if not source_files:
            raise FileNotFoundError(
                f"No .md or .txt files found in book_* directories within {self.vault_dir}"
            )
            
        print(f"[vault] Found {len(source_files)} candidate files across {len(book_dirs)} book directories.")
            
        for source_file in source_files:
            try:
                text = source_file.read_text(encoding="utf-8")
                facts = extract_spatial_facts(text)
                
                for rid, rdata in facts["regions"].items():
                    canon_id = resolve_canonical_id(rid)
                    if canon_id not in self.locations:
                        self.locations[canon_id] = LocationRecord(canonical_id=canon_id)
                        
                    loc = self.locations[canon_id]
                    loc.aliases.append(rid) if rid not in loc.aliases else None
                    
                    if source_file.name not in loc.files_mentioned:
                        loc.files_mentioned.append(source_file.name)
                    
                    for edge in facts["edges"]:
                        if edge["from"] == rid:
                            loc.evidence.append(SpatialEvidence(
                                file=source_file.name,
                                sentence=edge["source"][:120] + "..." if len(edge["source"]) > 120 else edge["source"],
                                relation=edge["relation"],
                                anchor=edge["to"],
                                confidence=edge["confidence"],
                                terrain_hint=rdata.get("terrain_class"),
                            ))
                        if edge["to"] == rid:
                            loc.evidence.append(SpatialEvidence(
                                file=source_file.name,
                                sentence=edge["source"][:120] + "..." if len(edge["source"]) > 120 else edge["source"],
                                relation=_invert_relation(edge["relation"]),
                                anchor=edge["from"],
                                confidence=edge["confidence"],
                            ))
                            
                # PASS B: Extract all location mentions (even without relations)
                mentions = extract_location_mentions(text)
                for raw_mention in mentions:
                    canon_id = resolve_canonical_id(raw_mention)
                    if canon_id not in self.locations:
                        self.locations[canon_id] = LocationRecord(canonical_id=canon_id)
                    
                    loc = self.locations[canon_id]
                    # Track file presence
                    if source_file.name not in loc.files_mentioned:
                        loc.files_mentioned.append(source_file.name)
                    
                    # Track alias
                    if raw_mention not in loc.aliases:
                        loc.aliases.append(raw_mention)
                            
                for loc in self.locations.values():
                    if loc.evidence:
                        loc.confidence = sum(e.confidence for e in loc.evidence) / len(loc.evidence)
            except Exception as e:
                print(f"[vault] Warning: Failed to parse {source_file.name}: {e}")
                
        # Detect conflicts
        conflict_map = detect_conflicts(self.locations)
        for lid, conflicts in conflict_map.items():
            self.locations[lid].conflicts.extend(conflicts)
            
        for loc in self.locations.values():
            loc.score = score_location(loc)
            
        return self.locations
        
def _invert_relation(rel: str) -> str:
    opp = {
        "north_of": "south_of", "south_of": "north_of",
        "east_of": "west_of", "west_of": "east_of",
        "above": "below", "below": "above",
        "adjacent_to": "adjacent_to", "connected_to": "connected_to",
        "contained_by": "contains", "contains": "contained_by",
        "overlooks": "below"
    }
    return opp.get(rel, "unknown")

# ─── Output Generators ────────────────────────────────────────────────────────
def generate_evidence_json(locations: Dict[str, LocationRecord], output_path: str):
    data = {}
    for lid, loc in locations.items():
        data[lid] = {
            "canonical_id": loc.canonical_id,
            "aliases": sorted(list(set(loc.aliases))),
            "placement_status": loc.placement_status,
            "authority_tier": loc.authority_tier,
            "confidence": round(loc.confidence, 3),
            "conflicts": loc.conflicts,
            "files_mentioned": loc.files_mentioned,
            "evidence": [
                {
                    "file": e.file,
                    "sentence": e.sentence,
                    "relation": e.relation,
                    "anchor": e.anchor,
                    "confidence": e.confidence,
                    "terrain_hint": e.terrain_hint
                } for e in loc.evidence
            ]
        }
    Path(output_path).write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"[vault] Evidence JSON written: {output_path}")

def generate_report_md(locations: Dict[str, LocationRecord], output_path: str):
    lines = ["# Vault Spatial Evidence Report\n"]
    lines.append(f"Total locations detected: {len(locations)}\n")
    lines.append("## Location Index\n")
    
    for lid in sorted(locations.keys()):
        loc = locations[lid]
        score = getattr(loc, "score", 0.0)
        status = "⚠️ CONFLICT" if loc.conflicts else "✅ CLEAN"
        lines.append(f"### `{lid}` {status} (score: {score:.1f}, confidence: {loc.confidence:.2f})")
        lines.append(f"- **Aliases:** {', '.join(loc.aliases)}")
        lines.append(f"- **Score:** {score:.1f}")
        lines.append(f"- **Evidence count:** {len(loc.evidence)}")
        if loc.conflicts:
            lines.append("- **Conflicts:**")
            for c in loc.conflicts:
                lines.append(f"  - {c}")
        lines.append("- **Spatial Claims:**")
        for e in loc.evidence[:5]:  # Top 5
            lines.append(f"  - `{e.relation}` → `{e.anchor}` (from `{e.file}`, conf: {e.confidence})")
        if len(loc.evidence) > 5:
            lines.append(f"  - *...{len(loc.evidence)-5} more claims*")
        lines.append("")
        
    lines.append("## Resolution Guide\n")
    lines.append("1. Review locations marked ️ CONFLICT manually.")
    lines.append("2. Promote clean locations to `placement_status: locked` after verification.")
    lines.append("3. Feed resolved layout into `trixelmap_build.py` for coordinate solving.")
    
    Path(output_path).write_text("\n".join(lines))
    print(f"[vault] Report MD written: {output_path}")

# ─── CLI Entry Point ─────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="EngAIn Vault Spatial Evidence Parser")
    parser.add_argument("--vault-dir", required=True, help="Path to Obsidian/vault directory")
    parser.add_argument("--output-dir", default="trixelmap/out/vault", help="Output directory")
    args = parser.parse_args()
    
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    
    print(f"[vault] Scanning vault: {args.vault_dir}")
    parser_obj = VaultSpatialParser(args.vault_dir)
    locations = parser_obj.parse_vault()
    
    generate_evidence_json(locations, str(out / "location_spatial_evidence.json"))
    generate_report_md(locations, str(out / "location_spatial_report.md"))
    
    print("[vault] ✅ Vault parsing complete.")

if __name__ == "__main__":
    main()
