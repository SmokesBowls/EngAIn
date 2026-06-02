#!/usr/bin/env python3
"""
trixelmap/spatial_pattern_matcher.py

Pure functional helper: Extracts spatial predicates from narrative text.
Converts book text → regions + edges with consistent directionality.

Usage:
    from spatial_pattern_matcher import extract_spatial_facts
    facts = extract_spatial_facts(narrative_snippet)
    # facts = {"regions": {id: {...}}, "edges": [{"from": ..., "to": ..., "relation": ...}]}

Direction Rule:
    Text: "Star Needle dominates the northern horizon from Sundrift."
    Edge: from: star_needle, to: sundrift, relation: north_of
    (Subject is always `from`, Reference is always `to`)
"""

import re
from typing import Dict, List, Tuple, Optional

# ─── Spatial Relation Maps ─────────────────────────────────────────────────────
# Maps linguistic cues to canonical edge relations.
# Direction is always normalized relative to the SUBJECT (`from`).

DIRECTIONAL_MAP = {
    "north": "north_of", "north of": "north_of", "northern": "north_of",
    "south": "south_of", "south of": "south_of", "southern": "south_of",
    "east": "east_of", "east of": "east_of", "eastern": "east_of",
    "west": "west_of", "west of": "west_of", "western": "west_of",
}

ELEVATION_MAP = {
    "above": "above", "overlooks": "overlooks", "dominates": "overlooks",
    "below": "below", "beneath": "below", "under": "below",
    "higher ground": "above", "lower ground": "below",
}

PROXIMITY_MAP = {
    "near": "adjacent_to", "close to": "adjacent_to", "adjacent to": "adjacent_to",
    "borders": "adjacent_to", "touching": "adjacent_to", "next to": "adjacent_to",
}

CONNECTIVITY_MAP = {
    "connected to": "connected_to", "leads to": "connected_to", "travels to": "connected_to",
    "journeyed from": "connected_to", "marched into": "connected_to",
}

CONTAINMENT_MAP = {
    "inside": "contained_by", "within": "contained_by", "surrounded by": "contained_by",
    "contains": "contains", "holds": "contains", "includes": "contains",
    "rose from": "contained_by", "sits in": "contained_by",
}

# ─── Regex Patterns ───────────────────────────────────────────────────────────
# Ordered by specificity. First match wins.
PATTERNS = [
    # 1. Horizon/Skyline references (e.g., "dominates the northern horizon")
    (
        r"(?P<subj>[A-Z][A-Za-z\s\-]{3,40})\s+(?:dominates|overlooks|commands|crowns|towers)\s+(?:the\s+)?(?P<dir>north|south|east|west|northern|southern|eastern|western)\s+(?:horizon|skyline|view|range)\s+(?:from|of|over)\s+(?:the\s+)?(?P<ref>[A-Z][A-Za-z\s\-]{3,40})",
        "horizon"
    ),
    # 2. Direct positional (e.g., "A lies north of B", "A is east of B")
    (
        r"(?P<subj>[A-Z][A-Za-z\s\-]{3,40})\s+(?:is|lies|sits|stands|rests|extends|stretches)\s+(?:the\s+)?(?P<dir>north|south|east|west|above|below|northern|southern|eastern|western)\s*(?:of|to)?\s+(?:the\s+)?(?P<ref>[A-Z][A-Za-z\s\-]{3,40})",
        "directional"
    ),
    # 3. Elevation (e.g., "A overlooks B", "A is higher ground than B")
    (
        r"(?P<subj>[A-Z][A-Za-z\s\-]{3,40})\s+(?:overlooks|dominates|is\s+higher\s+than|rises\s+above)\s+(?:the\s+)?(?P<ref>[A-Z][A-Za-z\s\-]{3,40})",
        "elevation"
    ),
    # 4. Containment (e.g., "A lies within B", "B contains A")
    (
        r"(?P<inner>[A-Z][A-Za-z\s\-]{3,40})\s+(?:lies\s+within|is\s+inside|rests\s+in|sits\s+within|rose\s+from|is\s+contained\s+by|surrounded\s+by)\s+(?:the\s+)?(?P<outer>[A-Z][A-Za-z\s\-]{3,40})",
        "containment"
    ),
    # 5. Proximity (e.g., "A is near B", "A borders B")
    (
        r"(?P<a>[A-Z][A-Za-z\s\-]{3,40})\s+(?:is\s+)?(?:near|close\s+to|adjacent\s+to|borders|touches|next\s+to)\s+(?:the\s+)?(?P<b>[A-Z][A-Za-z\s\-]{3,40})",
        "proximity"
    ),
    # 6. Travel/Chain (e.g., "Left A, entered B", "From A to B")
    (
        r"(?:left|leaves|departed\s+from|marched\s+from|journeyed\s+from)\s+(?P<start>[A-Z][A-Za-z\s\-]{3,40}).*?(?:to|toward|into|arrived\s+at|reached|entered)\s+(?P<end>[A-Z][A-Za-z\s\-]{3,40})",
        "travel"
    ),
]

# ─── Helper Functions ─────────────────────────────────────────────────────────

def normalize_id(name: str) -> str:
    """Convert entity name to canonical snake_case ID."""
    name = name.strip().lower()
    for prefix in ["the ", "a ", "an "]:
        if name.startswith(prefix):
            name = name[len(prefix):]
    name = name.strip()
    name = re.sub(r'[^\w\s]', '', name).replace(' ', '_')
    return name

def infer_region_type(entity_id: str, context: str) -> str:
    """Heuristic type inference based on entity name and context."""
    ctx = context.lower()
    eid = entity_id.lower()
    
    if any(k in eid or k in ctx for k in ["mountain", "peak", "spire", "range", "spine"]):
        return "mountain"
    if any(k in eid or k in ctx for k in ["valley", "dale", "basin"]):
        return "valley"
    if any(k in eid or k in ctx for k in ["marsh", "wetland", "bog", "swamp"]):
        return "wetlands"
    if any(k in eid or k in ctx for k in ["forest", "wood", "grove"]):
        return "forest"
    if any(k in eid or k in ctx for k in ["plain", "expanse", "waste", "flat"]):
        return "plains"
    if any(k in eid or k in ctx for k in ["ridge", "hill", "slope"]):
        return "hills"
    if any(k in eid or k in ctx for k in ["coast", "shore", "bay", "home", "settlement"]):
        return "coastal"
    if any(k in eid or k in ctx for k in ["caldera", "crater", "volcano"]):
        return "volcanic"
    return "unknown"

# ─── Core Extractor ───────────────────────────────────────────────────────────

def extract_spatial_facts(text: str) -> Dict:
    """
    Pure function: Narrative text → Spatial predicates.
    
    Returns:
        {
            "regions": {id: {"id": str, "type": str, "mentions": int}},
            "edges": [{"from": str, "to": str, "relation": str, "confidence": float, "source": str}]
        }
    """
    regions = {}
    edges = []

    # Split into sentences to isolate context
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if len(s.strip()) > 15]

    for sent in sentences:
        matched = False
        
        # Try patterns in order of specificity
        for pattern, category in PATTERNS:
            match = re.search(pattern, sent, re.IGNORECASE)
            if not match:
                continue

            if category == "horizon":
                subj = normalize_id(match.group("subj"))
                ref = normalize_id(match.group("ref"))
                direction = match.group("dir").lower()
                rel = DIRECTIONAL_MAP.get(direction, "adjacent_to")
                edges.append({"from": subj, "to": ref, "relation": rel, "confidence": 0.90, "source": sent})
                
            elif category == "directional":
                subj = normalize_id(match.group("subj"))
                ref = normalize_id(match.group("ref"))
                direction = match.group("dir").lower()
                rel = DIRECTIONAL_MAP.get(direction, "adjacent_to")
                # Handle vertical
                if direction in ["above", "below"]:
                    rel = ELEVATION_MAP[direction]
                edges.append({"from": subj, "to": ref, "relation": rel, "confidence": 0.85, "source": sent})
                
            elif category == "elevation":
                subj = normalize_id(match.group("subj"))
                ref = normalize_id(match.group("ref"))
                edges.append({"from": subj, "to": ref, "relation": "overlooks", "confidence": 0.85, "source": sent})
                
            elif category == "containment":
                inner = normalize_id(match.group("inner"))
                outer = normalize_id(match.group("outer"))
                # Normalize to inner -> outer contained_by
                edges.append({"from": inner, "to": outer, "relation": "contained_by", "confidence": 0.85, "source": sent})
                
            elif category == "proximity":
                a = normalize_id(match.group("a"))
                b = normalize_id(match.group("b"))
                edges.append({"from": a, "to": b, "relation": "adjacent_to", "confidence": 0.80, "source": sent})
                
            elif category == "travel":
                start = normalize_id(match.group("start"))
                end = normalize_id(match.group("end"))
                edges.append({"from": start, "to": end, "relation": "connected_to", "confidence": 0.75, "source": sent})
            
            matched = True
            break

        if matched:
            # Harvest regions from this sentence's edges
            for edge in edges:
                for node in [edge["from"], edge["to"]]:
                    if node not in regions:
                        regions[node] = {"id": node, "type": "unknown", "mentions": 0}
                    regions[node]["mentions"] += 1
                    # Update type based on sentence context
                    regions[node]["type"] = infer_region_type(node, sent)

    # Deduplicate edges
    unique_edges = []
    seen = set()
    for e in edges:
        key = (e["from"], e["to"], e["relation"])
        if key not in seen:
            seen.add(key)
            unique_edges.append(e)

    return {"regions": regions, "edges": unique_edges}

# ─── CLI Test Harness ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    test_text = """
    Star Needle dominated the northern horizon from Sundrift.
    The legion left Forest Needle and marched into the Plains of Sorrow.
    Falcon Ridge sits higher ground near Sundrift Valley.
    Plains Needle rose from the heart of a massive caldera.
    Nephoretti Marsh lies northeast of the Crescent Mountain Range.
    """
    
    facts = extract_spatial_facts(test_text)
    print("=== REGIONS ===")
    for rid, rdata in facts["regions"].items():
        print(f"  {rid}: type={rdata['type']}, mentions={rdata['mentions']}")
        
    print("\n=== EDGES (Direction Rule: from=subject, to=reference) ===")
    for e in facts["edges"]:
        print(f"  {e['from']} --[{e['relation']}]--> {e['to']} (conf: {e['confidence']})")
        print(f"    Source: '{e['source']}'")
