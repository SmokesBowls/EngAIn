#!/usr/bin/env python3
"""
trixelmap/spatial_pattern_matcher.py

Pure functional helper: Extracts spatial predicates from narrative text.
Architecture: Regex over-collect → Filter Pipeline → Canonical IDs.

Filter Pipeline:
1. Canon Allowlist Bypass (always accept known locations)
2. Bad Determiner/Adjective Prefix Reject
3. Generic Singleton Reject
4. Common English Word Reject
5. Weak Suffix Compound Reject
"""

import re
from typing import Dict, List, Optional

# ─── Location Suffixes (Canonical List) ─────────────────────────────────────
LOCATION_SUFFIXES = {
    "valley", "needle", "ridge", "mountain", "range", "marsh", "forest",
    "plains", "expanse", "spire", "caldera", "basin", "shelf", "home", 
    "water", "village", "settlement", "camp", "tower", "keep", "island"
}

# ─── Spatial Descriptors → (relation, confidence) ────────────────────────────
SPATIAL_KEYWORDS = {
    "dominated the northern horizon": ("north_of", 0.95),
    "dominated the southern horizon": ("south_of", 0.95),
    "dominated the eastern horizon": ("east_of", 0.95),
    "dominated the western horizon": ("west_of", 0.95),
    "northern horizon": ("north_of", 0.90),
    "southern horizon": ("south_of", 0.90),
    "eastern horizon": ("east_of", 0.90),
    "western horizon": ("west_of", 0.90),
    "higher ground": ("above", 0.85),
    "lower ground": ("below", 0.85),
    "overlooked": ("above", 0.80),
    "towered above": ("above", 0.85),
    "rose from": ("contained_by", 0.80),
    "miles from": ("adjacent_to", 0.75),
    "miles away": ("adjacent_to", 0.75),
    "beyond the": ("adjacent_to", 0.70),
    "across from": ("adjacent_to", 0.75),
    "led to": ("connected_to", 0.70),
    "marched into": ("connected_to", 0.75),
    "journeyed to": ("connected_to", 0.70),
}

# ─── Canon Allowlist (Bypasses all filters) ─────────────────────────────────
CANON_LOCATION_ALLOWLIST = frozenset({
    "ashfall_plains", "asteroid_spire", "earth_giant_settlement",
    "earth_prime_spire", "earth_spire", "earth_void_spire",
    "echo_tower", "falcon_ridge", "ironspire", "sundrift_valley",
    "star_needle", "tidecaller_mountain", "nephoretti_marsh",
    "crescent_mountain_range"
})

# ─── Hygiene Filters ──────────────────────────────────────────────────────────
BAD_LOCATION_PREFIX_WORDS = frozenset({
    "a", "an", "and", "another", "any", "as", "at", "but", "by",
    "each", "every", "for", "from", "in", "into", "it", "its",
    "of", "on", "or", "some", "that", "the", "then", "this",
    "to", "toward", "towards", "through", "with"
})

GENERIC_SINGLETONS = frozenset({
    "water", "home", "range", "village", "tower", "marsh", "ridge",
    "valley", "plains", "forest", "mountain", "island", "expanse",
    "caldera", "shelf", "basin", "camp", "keep", "settlement"
})

WEAK_SUFFIXES = frozenset({"range", "water", "home", "village"})

COMMON_ENGLISH_WORDS = frozenset({
    "adequate", "arrange", "cold", "deep", "great", "high", "left", "many",
    "more", "much", "new", "old", "other", "own", "right", "same", "some",
    "such", "than", "there", "these", "they", "very", "well", "what",
    "where", "which", "while", "white", "who", "why", "will", "yet",
    "you", "your", "create", "build", "make", "take", "give", "have",
    "do", "say", "get", "go", "come", "know", "think", "see", "look",
    "want", "use", "find", "tell", "ask", "work", "seem", "feel", "try",
    "leave", "call", "good", "bad", "long", "little", "big", "small",
    "large", "early", "late", "far", "near", "open", "close", "hard",
    "easy", "low", "young", "hot", "prepare", "organize", "start", "end",
    "age", "area", "point", "time", "way", "place", "part", "case",
    # NEW: Abstract/Event Nouns
    "convergence", "press", "response", "arrival", "departure", "incident",
    "event", "ritual", "ceremony", "battle", "war", "skirmish", "fight",
    "conflict", "journey", "voyage", "travel", "passage", "crossing",
    "view", "sight", "scene", "vision", "dream", "memory", "thought",
    "action", "reaction", "impact", "force", "energy", "power", "magic",
    "spell", "curse", "blessing", "gift", "burden", "legacy", "heritage",
    "truth", "lie", "secret", "mystery", "riddle", "puzzle", "enigma"
})

# ─── Alias Resolver (STRICT) ──────────────────────────────────────────────────
ALIAS_OVERRIDES = {
    "sundrift": "sundrift_valley",
    "star": "star_needle",
    "falcon": "falcon_ridge",
    "ironspire": "ironspire",
    "tidecaller": "tidecaller_mountain",
    "echo": "echo_tower",
    "nephoretti": "nephoretti_marsh",
    "crescent": "crescent_mountain_range",
}

def normalize_id(name: str) -> str:
    """Convert entity name to canonical snake_case ID."""
    # Collapse all whitespace/newlines to a single space first
    name = re.sub(r'\s+', ' ', name.strip()).lower()
    for prefix in ["the ", "a ", "an "]:
        if name.startswith(prefix):
            name = name[len(prefix):]
    return re.sub(r'[^\w\s]', '', name.strip()).replace(' ', '_')

def resolve_canonical_id(raw_id: str) -> str:
    """Resolves aliases to canonical location IDs."""
    normalized = normalize_id(raw_id)
    if normalized in ALIAS_OVERRIDES:
        return ALIAS_OVERRIDES[normalized]
    for key, val in ALIAS_OVERRIDES.items():
        if key in normalized and len(key) > 3:
            return val
    return normalized

def _is_hygienic_id(nid: str) -> bool:
    """
    Filter Pipeline:
    0. Canon Allowlist → Always accept
    1. Bad Prefix → Reject determiners/adjectives
    2. Generic Singleton → Reject bare terrain words
    3. Common English → Reject non-location vocabulary
    4. Weak Suffix → Reject compounds like 'another_village'
    """
    # 0. Canon bypass
    if nid in CANON_LOCATION_ALLOWLIST:
        return True

    # 1. Bad prefix check (first word)
    first_word = nid.split("_", 1)[0]
    if first_word in BAD_LOCATION_PREFIX_WORDS:
        return False

    # 2. Generic singleton check
    if nid in GENERIC_SINGLETONS:
        return False

    # 3. Common English word check
    if nid in COMMON_ENGLISH_WORDS:
        return False

    # 4. Weak suffix compound check
    if "_" in nid:
        suffix = nid.rsplit("_", 1)[-1]
        if suffix in WEAK_SUFFIXES:
            prefix = nid.rsplit("_", 1)[0]
            # FIX: Split prefix parts and check each one
            prefix_parts = prefix.split("_")
            if any(part in BAD_LOCATION_PREFIX_WORDS or part in COMMON_ENGLISH_WORDS for part in prefix_parts):
                return False

    return True

def extract_location_mentions(text: str) -> List[str]:
    """
    Pass B: Extracts ALL location mentions.
    Enforces Title Case for names and applies Candidate Hygiene filters.
    """
    found = []
    
    # 1. Standard Pattern: "Name Suffix" (Space separated, Title Case)
    standard_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+([A-Za-z]+)\b'
    for m in re.finditer(standard_pattern, text):
        name_part = m.group(1)
        suffix_part = m.group(2)
        
        if suffix_part.lower() in LOCATION_SUFFIXES:
            if name_part.lower() not in ["the", "a", "an", "his", "her", "its"]:
                raw_name = m.group(0)
                nid = resolve_canonical_id(raw_name)
                if _is_hygienic_id(nid):
                    found.append(nid)
        
    # 2. Compound Pattern: "NameSuffix" (e.g., Ironspire)
    word_pattern = r'\b([A-Z][a-zA-Z]+)\b'
    for m in re.finditer(word_pattern, text):
        word = m.group(0)
        for suffix in LOCATION_SUFFIXES:
            if word.lower().endswith(suffix.lower()) and len(word) > len(suffix):
                nid = resolve_canonical_id(word)
                if _is_hygienic_id(nid):
                    found.append(nid)
                break
                
    return list(set(found))

def extract_spatial_facts(text: str) -> Dict:
    """
    Pure function: Narrative text → Spatial predicates.
    Two-pass architecture: Entity harvest → Context window binding.
    Applies Candidate Hygiene filters to all extracted entities.
    """
    regions = {}
    edges = []

    # ── PHASE 1: Named Place Extraction ──────────────────────────────────────
    entity_pattern = r'(?:the\s+)?\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\s+(' + '|'.join([s.capitalize() for s in LOCATION_SUFFIXES]) + r')\b'
    candidates = []
    for m in re.finditer(entity_pattern, text):
        full_name = m.group(0)
        nid = resolve_canonical_id(full_name)
        
        if _is_hygienic_id(nid):
            candidates.append({
                "id": nid,
                "name": full_name,
                "start": m.start(),
                "end": m.end()
            })

    # ── PHASE 2: Spatial Descriptor Scanning & Context Binding ───────────────
    for keyword, (relation, confidence) in SPATIAL_KEYWORDS.items():
        kw_lower = keyword.lower()
        for m in re.finditer(re.escape(kw_lower), text.lower()):
            pos = m.start()
            window_start = max(0, pos - 250)
            window_end = min(len(text), pos + 250)
            window_text = text[window_start:window_end]

            window_entities = [
                e for e in candidates
                if e["start"] >= window_start and e["end"] <= window_end
            ]

            if len(window_entities) < 2:
                continue

            sorted_by_proximity = sorted(window_entities, key=lambda e: abs(e["start"] - pos))
            subject = sorted_by_proximity[0]
            anchor = next((e for e in sorted_by_proximity if e["id"] != subject["id"]), None)

            if not anchor:
                continue

            edges.append({
                "from": subject["id"],
                "to": anchor["id"],
                "relation": relation,
                "confidence": confidence,
                "source": window_text.replace("\n", " ").strip()[:140] + "..."
            })

            for ent in [subject, anchor]:
                if ent["id"] not in regions:
                    regions[ent["id"]] = {"id": ent["id"], "type": "unknown", "mentions": 0}
                regions[ent["id"]]["mentions"] += 1

    unique_edges, seen = [], set()
    for e in edges:
        key = (e["from"], e["to"], e["relation"])
        if key not in seen:
            seen.add(key)
            unique_edges.append(e)

    return {"regions": regions, "edges": unique_edges}

if __name__ == "__main__":
    test_text = """
    Sundrift Valley lay quiet. In the distance, the Star Needle 
    dominated the northern horizon. To the west, higher ground rose sharply—Falcon Ridge.
    The legion left Forest Needle and marched into the Plains of Sorrow.
    Adequate water was scarce. But home was far. Arrange the troops.
    Each spire watched. Another village burned. Age range shifted.
    """
    
    facts = extract_spatial_facts(test_text)
    mentions = extract_location_mentions(test_text)
    print("=== MENTIONS (Filtered) ===")
    print(sorted(mentions))
    print("\n=== EDGES ===")
    for e in facts["edges"]:
        print(f"  {e['from']} --[{e['relation']}]--> {e['to']}")