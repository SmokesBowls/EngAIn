#!/usr/bin/env python3
"""
pass5_game_bridge.py - ZON Memory Fabric → Game Scene

Takes Pass4 ZON output and generates game-ready scene JSON.

Usage:
    python3 pass5_game_bridge.py out_pass1_03_Fist_contact.zonj.json
    python3 pass5_game_bridge.py narrative_work/zon/*.zonj.json --output game_scenes/
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _slugify(name: str) -> str:
    """Convert a canonical name to a safe entity id slug."""
    import re
    s = name.lower().replace(".", "").replace(" ", "_")
    return re.sub(r"_+", "_", s).strip("_")


# ---------------------------------------------------------------------------
# Region metadata extraction (mirrors pass4; reads @ fields first)
# ---------------------------------------------------------------------------

_VOTING_KEYWORD_REGISTRY: Dict[str, Dict[str, Any]] = {
    # Prose descriptors
    "ash":         {"terrain_family": "ash",         "environment": "wasteland", "is_topology": True},
    "grey":        {"terrain_family": "stone",       "environment": "wasteland", "is_topology": True},
    "gray":        {"terrain_family": "stone",       "environment": "wasteland", "is_topology": True},
    "mist":        {"terrain_family": "shrouded",    "environment": "wasteland", "is_topology": False},
    "fog":         {"terrain_family": "shrouded",    "environment": "ambient",   "is_topology": False},
    "starless":    {"terrain_family": "void",        "environment": "wasteland", "is_topology": True},
    "twilight":    {"terrain_family": "shadow",      "environment": "ambient",   "is_topology": False},
    "dusk":        {"terrain_family": "shadow",      "environment": "ambient",   "is_topology": False},
    "wasteland":   {"terrain_family": "barren",      "environment": "wasteland", "is_topology": True},
    "barren":      {"terrain_family": "barren",      "environment": "wasteland", "is_topology": True},
    "desolate":    {"terrain_family": "barren",      "environment": "wasteland", "is_topology": True},
    "plain":       {"terrain_family": "flat",        "environment": "open",      "is_topology": True},
    "featureless": {"terrain_family": "flat",        "environment": "wasteland", "is_topology": True},
    "powder":      {"terrain_family": "dust",        "environment": "wasteland", "is_topology": True},
    "dust":        {"terrain_family": "dust",        "environment": "arid",      "is_topology": True},
    "cracks":      {"terrain_family": "fissure",     "environment": "wasteland", "is_topology": True},

    # Volcanic descriptors
    "volcano":     {"terrain_family": "ash",         "environment": "volcanic",  "is_topology": True},
    "volcanic":    {"terrain_family": "ash",         "environment": "volcanic",  "is_topology": True},
    "lava":        {"terrain_family": "ash",         "environment": "volcanic",  "is_topology": True},
    "magma":       {"terrain_family": "ash",         "environment": "volcanic",  "is_topology": True},
    "molten":      {"terrain_family": "ash",         "environment": "volcanic",  "is_topology": True},
    "basalt":      {"terrain_family": "stone",       "environment": "volcanic",  "is_topology": True},
    "caldera":     {"terrain_family": "ash",         "environment": "volcanic",  "is_topology": True},
    "fissure":     {"terrain_family": "fissure",     "environment": "volcanic",  "is_topology": True},
    "ember":       {"terrain_family": "ash",         "environment": "volcanic",  "is_topology": True},

    # Coastal/Beach cluster
    "coastal":     {"terrain_family": "beach",       "environment": "coastal",   "is_topology": True},
    "beach":       {"terrain_family": "beach",       "environment": "coastal",   "is_topology": True},
    "shore":       {"terrain_family": "beach",       "environment": "coastal",   "is_topology": True},
    "shoreline":   {"terrain_family": "beach",       "environment": "coastal",   "is_topology": True},
    "landing site":{"terrain_family": "beach",       "environment": "coastal",   "is_topology": True},
    "ocean":       {"terrain_family": "beach",       "environment": "coastal",   "is_topology": True},
    "island":      {"terrain_family": "beach",       "environment": "coastal",   "is_topology": True},
    "sea":         {"terrain_family": "beach",       "environment": "coastal",   "is_topology": True},
    "harbor":      {"terrain_family": "beach",       "environment": "coastal",   "is_topology": True},
    "bay":         {"terrain_family": "beach",       "environment": "coastal",   "is_topology": True},

    # Arid/Sand cluster
    "mars":        {"terrain_family": "sand",        "environment": "arid",      "is_topology": True},
    "desert":      {"terrain_family": "sand",        "environment": "arid",      "is_topology": True},
    "arid":        {"terrain_family": "sand",        "environment": "arid",      "is_topology": True},
    "dune":        {"terrain_family": "sand",        "environment": "arid",      "is_topology": True},

    # Temperate/Grass cluster
    "forest":      {"terrain_family": "grass",       "environment": "temperate", "is_topology": True},
    "valley":      {"terrain_family": "grass",       "environment": "temperate", "is_topology": True},
    "jungle":      {"terrain_family": "grass",       "environment": "temperate", "is_topology": True},
    "woods":       {"terrain_family": "grass",       "environment": "temperate", "is_topology": True},
    "mainland":    {"terrain_family": "grass",       "environment": "temperate", "is_topology": True},
    "plains":      {"terrain_family": "grass",       "environment": "temperate", "is_topology": True},
    "garden":      {"terrain_family": "grass",       "environment": "temperate", "is_topology": True},
    "mountain":    {"terrain_family": "grass",       "environment": "temperate", "is_topology": True},
}

_TERRAIN_KEYWORD_MAP: list = [
    ("coastal",      "beach"),
    ("beach",        "beach"),
    ("shore",        "beach"),
    ("landing site", "beach"),
    ("ocean",        "beach"),
    ("island",       "beach"),
    ("mars",         "sand"),
    ("desert",       "sand"),
    ("arid",         "sand"),
    ("wasteland",    "sand"),
    ("red dust",     "sand"),
    ("forest",       "grass"),
    ("valley",       "grass"),
    ("jungle",       "grass"),
    ("woods",        "grass"),
    ("mainland",     "grass"),
    ("plains",       "grass"),
    ("garden",       "grass"),
    ("mountain",     "grass"),
]

_TERRAIN_TO_ENV: Dict[str, str] = {
    "beach":   "coastal",
    "sand":    "arid",
    "grass":   "temperate",
    "default": "unknown",
}


def _resolve_votes_for_text(text: str) -> tuple[str, str, dict]:
    """Score text and return (terrain_family, environment, flat_votes) using weighted voting."""
    import re
    text_lower = text.lower()
    
    votes = {}       # Key: (tf, env) -> count
    tf_metadata = {}  # Key: tf -> is_topology (bool)
    
    # Perform exact matching against the voting registry
    for kw, meta in _VOTING_KEYWORD_REGISTRY.items():
        tf = meta["terrain_family"]
        env = meta["environment"]
        is_topo = meta["is_topology"]
        
        tf_metadata[tf] = is_topo
        
        # Match using word boundaries to avoid partial-word matches
        matches = len(re.findall(rf"\b{re.escape(kw)}\b", text_lower))
        if matches > 0:
            votes[(tf, env)] = votes.get((tf, env), 0) + matches

    if not votes:
        return "default", "unknown", {}

    # Deterministic Tie-breaking:
    # Sort candidates by:
    # 1. Total match count (descending)
    # 2. Topology preference (topology=True first, atmosphere=False second)
    # 3. Alphabetical order of terrain_family (guarantees absolute determinism)
    candidates = list(votes.items())
    candidates.sort(key=lambda x: (
        -x[1], 
        0 if tf_metadata.get(x[0][0], True) else 1, 
        x[0][0]
    ))
    
    winning_tf, winning_env = candidates[0][0]
    
    # Flatten votes for evidence logging
    flat_votes = {}
    for (tf, env), count in votes.items():
        flat_votes[tf] = flat_votes.get(tf, 0) + count
        
    return winning_tf, winning_env, flat_votes


def _resolve_terrain_votes(segments: list, max_segments: int = 30) -> dict | None:
    """
    Scans segments using weighted voting to determine terrain_family and environment.
    """
    if not segments:
        return None

    narration_texts = []
    context_words = []
    
    for seg in segments[:max_segments]:
        text = seg.get("text", "")
        if text:
            narration_texts.append(text)
            words = [w.strip(".,;:!?\"'()[]{}") for w in text.lower().split() if len(w) > 3]
            context_words.extend(words[:12])
            
    combined_text = " ".join(narration_texts)
    winning_tf, winning_env, votes_dict = _resolve_votes_for_text(combined_text)
    
    if not votes_dict:
        return None
        
    region_desc = " ".join(context_words[:10]).capitalize()
    if len(region_desc) < 4:
        region_desc = "Inferred terrain region"
        
    return {
        "region": region_desc,
        "terrain_family": winning_tf,
        "environment": winning_env,
        "spatial_scale_hint": "region",
        "confidence": "inferred_prose",
        "environment_inference": {
            "source": "inferred_votes",
            "profile": winning_tf,
            "confidence": 0.8,
            "evidence": [f"{tf}:{count}" for tf, count in votes_dict.items()]
        }
    }


def _extract_region_metadata(zon_data: Dict[str, Any]) -> Dict[str, str]:
    """Return region metadata dict.

    Priority:
      1. Explicit @region fields written by pass4.
      2. Scan =segments for a REGION: annotation line.
    """
    # Pass4 writes explicit @ fields
    region = zon_data.get("@region") or ""
    if region:
        return {
            "region": str(region),
            "environment": str(zon_data.get("@environment") or "unknown"),
            "terrain_family": str(zon_data.get("@terrain_family") or "default"),
            "spatial_scale_hint": str(zon_data.get("@spatial_scale_hint") or "location"),
        }

    # Fallback: scan segments
    segments = zon_data.get("=segments") or zon_data.get("segments") or []
    region_str = ""
    for seg in segments[:30]:
        if not isinstance(seg, dict):
            continue
        txt = (seg.get("text") or "").strip()
        if txt.startswith("REGION:"):
            region_str = txt[7:].strip()
            break

    if region_str:
        primary = region_str.split(",")[0].strip().lower()
        winning_tf, winning_env, votes_dict = _resolve_votes_for_text(primary)
        
        if votes_dict:
            terrain_family = winning_tf
            environment = winning_env
        else:
            terrain_family = "default"
            environment = "unknown"
            
        has_multiple = "," in region_str
        has_brief = "(brief)" in region_str.lower()
        spatial_scale_hint = "region" if (has_multiple or has_brief) else "location"
        return {
            "region": region_str,
            "environment": environment,
            "terrain_family": terrain_family,
            "spatial_scale_hint": spatial_scale_hint,
        }

    # Last resort: infer terrain from @where path (e.g. "Realm/Physical/Mars" → sand)
    where = (zon_data.get("@where") or "").lower()
    if where:
        winning_tf, winning_env, votes_dict = _resolve_votes_for_text(where)
        if votes_dict:
            return {
                "region": where.split("/")[-1].capitalize(),
                "environment": winning_env,
                "terrain_family": winning_tf,
                "spatial_scale_hint": "location",
            }

    return {}


# ---------------------------------------------------------------------------
# Level design extraction — deterministic keyword/rule only, no LLM
# ---------------------------------------------------------------------------

_LD_ENTRY_CUES = frozenset({
    "materialized", "arrived", "entered", "emerged", "stepped into",
    "landed", "appeared", "came to", "set foot", "touched down", "descended into",
})
_LD_LANDMARK_NOUNS = frozenset({
    "crown", "spire", "gate", "hall", "chamber", "city", "mountain", "spine",
    "tower", "citadel", "temple", "archive", "plain", "vale", "ruins", "sanctum",
    "throne", "bridge", "keep", "fortress", "amphitheater", "underchamber",
    "outcrop", "crater", "basin", "plateau", "cavern", "vault", "altar", "peak",
})
_LD_BOUNDARY_CUES = frozenset({
    "wall", "gate", "mountain", "cliff", "edge", "perimeter", "spine",
    "shore", "ridge", "barrier", "treeline", "canyon", "ravine",
})
_LD_HAZARD_CUES = frozenset({
    "attack", "threat", "alarm", "massing", "hostile", "ambush", "creature",
    "enemy", "danger", "trap", "predator", "stalking", "aggress", "charging",
    "ambush", "lethal", "toxic", "collapse", "unstable",
})
_LD_POI_CUES = frozenset({
    "chamber", "archive", "hall", "council", "amphitheater", "vault", "shrine",
    "crystal", "relic", "monument", "altar", "underchamber", "archive",
    "terminal", "console", "lever", "switch", "pedestal", "inscription",
})
_LD_VERTICAL_CUES = frozenset({
    "ramp", "spiral", "ascend", "descend", "underground", "below", "above",
    "cliff", "tower", "depth", "summit", "roots", "staircase", "cavern",
    "lower level", "upper level", "shaft", "chasm",
})
_LD_LOW_VIS_CUES = frozenset({
    "mist", "fog", "ash", "grey", "gray", "obscured", "dim", "shadow",
    "twilight", "dusk", "darkness", "haze", "dust", "starless", "dulling",
    "low visibility", "murky", "overcast", "shrouded",
})
_LD_GUIDED_CUES = frozenset({
    "destination", "led through", "led them", "guided", "escorted",
    "made their way", "heading toward", "walked toward", "moved toward",
    "following the path",
})
_LD_DENSITY_HIGH = frozenset({"hundreds", "massing", "horde", "swarm", "dozens", "swarming", "countless"})
_LD_DENSITY_MED  = frozenset({"group", "several", "trio", "pair", "flanked", "small band"})
_LD_DENSITY_LOW  = frozenset({"alone", "solitary", "empty", "deserted", "abandoned", "no one"})


def _extract_level_design(segments: List[Dict], max_segments: int = 40) -> Dict[str, Any]:
    """
    Deterministic extraction of level design metadata from narration/action segments.
    Scans first max_segments qualifying segments only.
    """
    narr = [
        s for s in segments
        if isinstance(s, dict) and s.get("type", "").lower()
        in ("narration", "description", "action", "dialogue")
    ][:max_segments]

    entry_point = ""
    primary_path = ""
    landmarks: List[str] = []
    boundaries: List[str] = []
    hazards: List[str] = []
    points_of_interest: List[str] = []
    verticality = "flat"
    low_vis_hits = 0
    guided_hits = 0
    density_score = 0

    seen_landmarks: set = set()
    seen_boundaries: set = set()
    seen_hazards: set = set()
    seen_pois: set = set()

    for seg in narr:
        text = seg.get("text", "") or ""
        lower = text.lower()

        # --- entry_point: first arrival cue ---
        if not entry_point:
            for cue in _LD_ENTRY_CUES:
                if cue in lower:
                    idx = lower.find(cue) + len(cue)
                    snippet = text[idx: idx + 70].strip().lstrip(" .,").split(".")[0].strip()
                    if len(snippet) > 3:
                        entry_point = snippet[:70]
                    break

        # --- primary_path: first explicit destination mention ---
        if not primary_path:
            for cue in ("destination was", "their way to", "heading toward", "headed toward", "path led"):
                if cue in lower:
                    idx = lower.find(cue)
                    snippet = text[idx: idx + 90].strip().split(".")[0].strip()
                    if snippet:
                        primary_path = snippet[:90]
                    break

        # --- landmarks: word before a structural noun (up to 3 preceding words) ---
        word_list = text.split()
        for i, w in enumerate(word_list):
            w_clean = w.strip(".,;:!?\"'()[]{}—-").lower()
            if w_clean in _LD_LANDMARK_NOUNS:
                start = max(0, i - 3)
                phrase = " ".join(
                    ww.strip(".,;:!?\"'()[]{}—-") for ww in word_list[start: i + 1]
                )
                phrase_key = phrase.lower()
                if phrase_key not in seen_landmarks and len(phrase) > 2:
                    seen_landmarks.add(phrase_key)
                    landmarks.append(phrase)

        # --- boundaries ---
        for cue in _LD_BOUNDARY_CUES:
            if cue in lower and cue not in seen_boundaries:
                seen_boundaries.add(cue)
                idx = lower.find(cue)
                snippet = text[max(0, idx - 20): idx + 35].strip()
                boundaries.append(snippet[:60])

        # --- hazards ---
        for cue in _LD_HAZARD_CUES:
            if cue in lower and cue not in seen_hazards:
                seen_hazards.add(cue)
                idx = lower.find(cue)
                snippet = text[max(0, idx - 15): idx + 50].strip()
                hazards.append(snippet[:70])

        # --- points of interest ---
        for cue in _LD_POI_CUES:
            if cue in lower and cue not in seen_pois:
                seen_pois.add(cue)
                idx = lower.find(cue)
                snippet = text[max(0, idx - 20): idx + 35].strip()
                points_of_interest.append(snippet[:60])

        # --- verticality ---
        if verticality == "flat":
            for cue in _LD_VERTICAL_CUES:
                if cue in lower:
                    verticality = "variable"
                    break

        # --- navigation style signals ---
        if any(c in lower for c in _LD_LOW_VIS_CUES):
            low_vis_hits += 1
        if any(c in lower for c in _LD_GUIDED_CUES):
            guided_hits += 1

        # --- encounter density ---
        for kw in _LD_DENSITY_HIGH:
            if kw in lower:
                density_score += 3
        for kw in _LD_DENSITY_MED:
            if kw in lower:
                density_score += 1
        for kw in _LD_DENSITY_LOW:
            if kw in lower:
                density_score -= 1

    # --- navigation_style: threshold decision ---
    if low_vis_hits >= 2 and guided_hits >= 1:
        navigation_style = "guided_low_visibility"
    elif low_vis_hits >= 2:
        navigation_style = "low_visibility"
    elif guided_hits >= 2:
        navigation_style = "guided_linear"
    elif low_vis_hits == 1:
        navigation_style = "low_visibility"
    else:
        navigation_style = "open"

    # --- encounter_density bucket ---
    if density_score >= 6:
        encounter_density = "high"
    elif density_score >= 2:
        encounter_density = "medium"
    elif density_score <= -2:
        encounter_density = "sparse"
    else:
        encounter_density = "low"

    return {
        "entry_point":        entry_point,
        "primary_path":       primary_path,
        "landmarks":          landmarks[:8],
        "boundaries":         boundaries[:6],
        "hazards":            hazards[:6],
        "points_of_interest": points_of_interest[:6],
        "verticality":        verticality,
        "navigation_style":   navigation_style,
        "encounter_density":  encounter_density,
    }


SPATIAL_LAYOUT_RELATIONS = {
    "beside",
    "near",
    "in_front_of",
    "behind",
    "above",
    "below",
    "within",
    "between",
    "through",
}


def _extract_spatial_relation_list(payload: Any) -> List[Dict[str, Any]]:
    """
    Pull pass1_spatial-style records out of any JSON shape.

    Expected pass1_spatial record shape:
      {
        "signal_id": "spatial_0001",
        "signal_type": "spatial_signal",
        "subject_hint": "...",
        "object_hint": "...",
        "relation": "in_front_of",
        "confidence": 0.85
      }

    This intentionally walks nested payloads because older pipeline files may
    store signals under different wrapper keys.
    """
    found: List[Dict[str, Any]] = []
    seen = set()

    def visit(obj: Any) -> None:
        if isinstance(obj, dict):
            relation = str(obj.get("relation", "")).strip().lower()
            signal_type = str(obj.get("signal_type", "")).strip().lower()

            looks_spatial = (
                signal_type == "spatial_signal"
                or relation in SPATIAL_LAYOUT_RELATIONS
            )

            if looks_spatial and relation:
                key = (
                    obj.get("signal_id"),
                    obj.get("subject_hint"),
                    obj.get("relation"),
                    obj.get("object_hint"),
                    obj.get("confidence"),
                )
                frozen = repr(key)
                if frozen not in seen:
                    seen.add(frozen)
                    found.append(dict(obj))

            for value in obj.values():
                visit(value)

        elif isinstance(obj, list):
            for item in obj:
                visit(item)

    visit(payload)
    return found


def _candidate_scene_stems(zon_path: Path, zon_data: Dict[str, Any]) -> List[str]:
    """
    Build likely scene stems for locating out_pass1_spatial_<scene_stem>.json.
    This avoids assuming one exact naming convention.
    """
    candidates: List[str] = []

    raw_name = zon_path.name
    candidates.append(raw_name)

    if raw_name.endswith(".zonj.json"):
        candidates.append(raw_name[:-len(".zonj.json")])
    if raw_name.endswith(".json"):
        candidates.append(raw_name[:-len(".json")])

    for key in ("scene_id", "@scene_id", "id", "@id", "source_scene_id"):
        value = zon_data.get(key)
        if value:
            candidates.append(str(value))

    expanded: List[str] = []
    for item in candidates:
        if not item:
            continue

        expanded.append(item)

        if item.startswith("scene."):
            expanded.append(item[len("scene."):])

        if item.startswith("scene_"):
            expanded.append(item[len("scene_"):])

        if item.startswith("zonj_"):
            expanded.append(item[len("zonj_"):])

        expanded.append(item.replace(".", "_"))
        expanded.append(item.replace("_", "."))

    deduped: List[str] = []
    seen = set()
    for item in expanded:
        item = item.strip()
        if item and item not in seen:
            seen.add(item)
            deduped.append(item)

    return deduped


def _load_spatial_relations_for_zon(
    zon_path: Path,
    zon_data: Dict[str, Any],
    spatial_dir: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """
    Load matching pass1_spatial output for a ZONJ scene, if it exists.

    This is read-only. Missing spatial files are not fatal; pass5 keeps its
    old linear fallback when no relation file is found.
    """
    roots: List[Path] = []

    if spatial_dir is not None:
        roots.append(spatial_dir.expanduser())

    roots.append(zon_path.parent)

    stems = _candidate_scene_stems(zon_path, zon_data)
    candidate_paths: List[Path] = []

    for root in roots:
        if not root.exists():
            continue

        for stem in stems:
            candidate_paths.append(root / f"out_pass1_spatial_{stem}.json")
            candidate_paths.append(root / f"{stem}_spatial.json")
            candidate_paths.append(root / f"spatial_{stem}.json")

        # Small recursive fallback, scoped only to the given root.
        for stem in stems:
            candidate_paths.extend(root.glob(f"**/*spatial*{stem}*.json"))
            candidate_paths.extend(root.glob(f"**/*{stem}*spatial*.json"))

    seen_paths = set()
    all_relations: List[Dict[str, Any]] = []

    for path in candidate_paths:
        if path in seen_paths or not path.exists() or not path.is_file():
            continue

        seen_paths.add(path)

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"  ! Spatial file unreadable: {path} ({exc})")
            continue

        relations = _extract_spatial_relation_list(payload)
        if relations:
            print(f"  + Spatial relations: {len(relations)} from {path}")
            all_relations.extend(relations)

    return all_relations


class GameBridge:
    """Convert ZON memory fabric to game scenes"""

    def __init__(self, world_rules_path: Optional[Path] = None):
        self.world_rules: Dict = {}
        if world_rules_path and Path(world_rules_path).exists():
            with open(world_rules_path, encoding="utf-8") as f:
                self.world_rules = json.load(f)

    def _is_spawnable(self, name: str) -> bool:
        """Return False for known non-spawnable entities."""
        if not self.world_rules:
            return True
        name_lower = name.lower()
        for key, entry in self.world_rules.get("entities", {}).items():
            cn = entry.get("canonical_name", key)
            if cn.lower() == name_lower or key.lower() == name_lower:
                if not entry.get("spawnable", True):
                    return False
                if entry.get("cardinality") in ("species", "collective", "abstract"):
                    return False
                return True
        return True

    def _canonical_name(self, raw: str) -> str:
        """Return the canonical display name from world_rules, or raw as fallback."""
        if not self.world_rules:
            return raw
        raw_lower = raw.lower()
        for key, entry in self.world_rules.get("entities", {}).items():
            cn = entry.get("canonical_name", key)
            if cn.lower() == raw_lower or key.lower() == raw_lower:
                return cn
        return raw

    def convert_zon_to_game(
        self,
        zon_data: Dict[str, Any],
        spatial_relations: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Convert ZON to game scene format"""

        # Extract scene ID — ensure "scene." prefix is present
        scene_id = zon_data.get('@id', 'unknown_scene')
        if scene_id.startswith('scene.'):
            pass
        else:
            scene_id = 'scene.' + scene_id

        # Get description from first narration segment
        segments = zon_data.get('=segments', zon_data.get('segments', []))
        description = self._get_description(segments)

        # Extract characters from @entities
        entity_list = zon_data.get('@entities', [])
        characters, layout_proof = self._create_characters(
            entity_list,
            spatial_relations=spatial_relations,
        )

        # Extract location from @where
        where = zon_data.get('@where', '')
        locations = self._create_locations(where)

        # Extract events from segments
        events = self._extract_events(segments)

        # Extract structured region metadata
        region_meta = _extract_region_metadata(zon_data)

        # 🔍 PROSE FALLBACK: Only when REGION: is absent
        if not region_meta or region_meta.get("terrain_family", "default") == "default":
            # 1. Primary: Semantic Environment Extractor
            try:
                import sys
                from pathlib import Path
                sys.path.insert(0, str(Path(__file__).parent))
                import semantic_environment_extractor
                
                extracted = semantic_environment_extractor.extract(zon_data)
                if extracted.get("environment_inference", {}).get("source") != "default":
                    region_meta = {
                        "region": extracted.get("region") or zon_data.get("@region") or "Inferred region",
                        "terrain_family": extracted.get("terrain_family"),
                        "environment": extracted.get("environment"),
                        "spatial_scale_hint": extracted.get("spatial_scale_hint", "location"),
                        "environment_inference": extracted.get("environment_inference")
                    }
                    print(f"[pass5] Semantic Extractor triggered for {scene_id} → terrain_family: {region_meta['terrain_family']}")
            except Exception as e:
                print(f"[pass5] Semantic Extractor failed: {e}")

        if not region_meta or region_meta.get("terrain_family", "default") == "default":
            # 2. Fallback: Prose weighted voting
            narration_segments = [s for s in segments if s.get("type", "").lower() in ("narration", "description", "action")]
            terrain_meta = _resolve_terrain_votes(narration_segments, max_segments=30)
            if terrain_meta:
                region_meta = terrain_meta
                print(f"[pass5] Prose weighted voting triggered for {scene_id} → terrain_family: {terrain_meta['terrain_family']}")

        if not region_meta:
            region_meta = {
                "region": "unspecified",
                "terrain_family": "default",
                "environment": "neutral",
                "spatial_scale_hint": "default",
                "confidence": "none"
            }

        # Extract level design metadata
        level_design = _extract_level_design(segments)

        # Build initial state
        initial_state = self._build_state(characters, locations)

        metadata = {
            'when': zon_data.get('@when', ''),
            'where': zon_data.get('@where', ''),
            'scope': zon_data.get('@scope', 'narrative'),
        }
        if region_meta:
            metadata['region'] = region_meta['region']
            metadata['environment'] = region_meta['environment']
            metadata['terrain_family'] = region_meta['terrain_family']
            metadata['spatial_scale_hint'] = region_meta['spatial_scale_hint']
            if 'environment_inference' in region_meta:
                metadata['environment_inference'] = region_meta['environment_inference']
        metadata['level_design'] = level_design
        metadata["layout_proof"] = layout_proof

        output: Dict[str, Any] = {
            'scene_id': scene_id,
            'description': description,
            'entities': characters,
            'locations': locations,
            'events': events,
            'initial_state': initial_state,
            'metadata': metadata,
            "region": region_meta.get("region", ""),
            "environment": region_meta.get("environment", "unknown"),
            "terrain_family": region_meta.get("terrain_family", "default"),
            "spatial_scale_hint": region_meta.get("spatial_scale_hint", "location"),
            "terrain_metadata": region_meta,
            "level_design": level_design,
            "layout_proof": layout_proof,
        }

        return output
    
    def _get_description(self, segments: List[Dict]) -> str:
        """Get scene description from first narration"""
        for seg in segments[:10]:
            if seg.get('type') == 'narration':
                return seg.get('text', '')[:200]
        return ''
    
    def _create_characters(
        self,
        entity_list: List[str],
        spatial_relations: Optional[List[Dict[str, Any]]] = None,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Create character entries, filtering non-spawnable and using canonical names.

        Positioning rule:
        - If pass1_spatial relations are available and resolvable, use them.
        - Otherwise keep the old honest fallback: x = index * 5, y = 0, z = 0.
        """
        characters: List[Dict[str, Any]] = []
        position = 0

        for raw in entity_list:
            canonical = self._canonical_name(raw)
            if not self._is_spawnable(canonical):
                continue

            char_id = _slugify(canonical)

            characters.append({
                "id": char_id,
                "name": canonical,
                "health": 100.0,
                "max_health": 100.0,
                "position": {"x": position * 5, "y": 0, "z": 0},
                "type": "character",
                "layout_source": "fallback_linear",
            })

            position += 1

        layout = self._resolve_spatial_positions(
            characters=characters,
            spatial_relations=spatial_relations or [],
        )

        for char in characters:
            char_id = char["id"]

            resolved_position = layout["positions"].get(char_id)
            if resolved_position:
                char["position"] = resolved_position

            source = layout["sources"].get(char_id)
            if source:
                char["layout_source"] = source

            evidence = layout["evidence"].get(char_id, [])
            if evidence:
                char["layout_evidence"] = evidence

        return characters, layout["proof"]

    def _resolve_spatial_positions(
        self,
        characters: List[Dict[str, Any]],
        spatial_relations: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Convert pass1_spatial relation records into simple engine-agnostic positions.

        Coordinate convention:
        - x = left/right spacing
        - y = vertical height
        - z = depth/front/back

        This does not pretend to solve full scene blocking yet. It only upgrades
        the flat row when pass1_spatial gives usable relational evidence.
        """
        fallback_positions: Dict[str, Dict[str, float]] = {
            char["id"]: {
                "x": float(char["position"]["x"]),
                "y": float(char["position"]["y"]),
                "z": float(char["position"]["z"]),
            }
            for char in characters
        }

        positions: Dict[str, Dict[str, float]] = dict(fallback_positions)
        sources: Dict[str, str] = {
            char["id"]: "fallback_linear"
            for char in characters
        }
        evidence: Dict[str, List[Dict[str, Any]]] = {
            char["id"]: []
            for char in characters
        }

        lookup = self._build_character_lookup(characters)

        suggestions: Dict[str, List[Dict[str, float]]] = {}
        unresolved: List[Dict[str, Any]] = []
        consumed = 0
        unanchored = 0

        for index, relation_record in enumerate(spatial_relations):
            relation = str(relation_record.get("relation", "")).strip().lower()

            subject_hint = (
                relation_record.get("subject_hint")
                or relation_record.get("subject")
                or relation_record.get("actor")
                or relation_record.get("source")
                or ""
            )

            object_hint = (
                relation_record.get("object_hint")
                or relation_record.get("object")
                or relation_record.get("target")
                or ""
            )

            subject_id = self._resolve_character_hint(subject_hint, lookup)
            object_id = self._resolve_character_hint(object_hint, lookup)

            if not subject_id:
                unresolved.append({
                    "reason": "subject_not_resolved",
                    "relation": relation,
                    "subject_hint": subject_hint,
                    "object_hint": object_hint,
                })
                continue

            # Some spatial relations point to locations or containers rather than
            # another spawnable character. Preserve evidence, but do not invent a
            # coordinate anchor.
            if not object_id:
                if relation in {"within", "through", "between"}:
                    evidence[subject_id].append(self._compact_spatial_evidence(relation_record))
                    sources[subject_id] = "spatial_relation_unanchored"
                    unanchored += 1
                else:
                    unresolved.append({
                        "reason": "object_not_resolved",
                        "relation": relation,
                        "subject_hint": subject_hint,
                        "object_hint": object_hint,
                    })
                continue

            offset = self._offset_for_spatial_relation(relation, index)
            if offset is None:
                unresolved.append({
                    "reason": "unsupported_relation_for_static_layout",
                    "relation": relation,
                    "subject_hint": subject_hint,
                    "object_hint": object_hint,
                })
                continue

            anchor = positions.get(object_id) or fallback_positions[object_id]

            suggested_position = {
                "x": anchor["x"] + offset["x"],
                "y": anchor["y"] + offset["y"],
                "z": anchor["z"] + offset["z"],
            }

            suggestions.setdefault(subject_id, []).append(suggested_position)
            evidence[subject_id].append(self._compact_spatial_evidence(relation_record))
            consumed += 1

        for char_id, proposed_positions in suggestions.items():
            if not proposed_positions:
                continue

            count = float(len(proposed_positions))
            positions[char_id] = {
                "x": round(sum(p["x"] for p in proposed_positions) / count, 3),
                "y": round(sum(p["y"] for p in proposed_positions) / count, 3),
                "z": round(sum(p["z"] for p in proposed_positions) / count, 3),
            }
            sources[char_id] = "spatial_relation"

        proof = {
            "mode": "spatial_relations" if consumed else "fallback_linear",
            "input_relation_count": len(spatial_relations),
            "consumed_relation_count": consumed,
            "unanchored_relation_count": unanchored,
            "unresolved_relation_count": len(unresolved),
            "unresolved_relations": unresolved[:25],
            "fallback_character_count": sum(
                1 for char_id in fallback_positions
                if sources.get(char_id) == "fallback_linear"
            ),
        }

        return {
            "positions": positions,
            "sources": sources,
            "evidence": evidence,
            "proof": proof,
        }

    def _build_character_lookup(self, characters: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Build loose lookup keys so pass1_spatial subject_hint/object_hint strings
        can resolve to canonical pass5 character ids.
        """
        lookup: Dict[str, str] = {}

        for char in characters:
            char_id = char["id"]
            name = str(char.get("name", "")).strip()
            slug = _slugify(name)

            keys = {
                char_id,
                slug,
                name.lower(),
                name.lower().replace("_", " "),
                name.lower().replace("-", " "),
            }

            for token in name.replace("-", " ").replace("_", " ").split():
                if len(token) >= 3:
                    keys.add(token.lower())

            for key in keys:
                if key:
                    lookup[key] = char_id

        return lookup

    def _resolve_character_hint(
        self,
        hint: Any,
        lookup: Dict[str, str],
    ) -> Optional[str]:
        """
        Resolve a pass1_spatial hint like 'the guard' or 'Darian' to a pass5
        character id. Returns None if resolution is ambiguous or impossible.
        """
        if hint is None:
            return None

        text = str(hint).strip().lower()
        if not text:
            return None

        direct_candidates = [
            text,
            _slugify(text),
            text.replace("_", " "),
            text.replace("-", " "),
        ]

        for candidate in direct_candidates:
            if candidate in lookup:
                return lookup[candidate]

        matches = set()
        for key, char_id in lookup.items():
            if len(key) < 3:
                continue
            if key in text or text in key:
                matches.add(char_id)

        if len(matches) == 1:
            return next(iter(matches))

        return None

    def _offset_for_spatial_relation(
        self,
        relation: str,
        index: int,
    ) -> Optional[Dict[str, float]]:
        """
        Translate one prose relation into a simple coordinate offset.

        This is intentionally modest. It creates usable blocking hints without
        pretending to be a full topological solver.
        """
        side = -1.0 if index % 2 else 1.0

        if relation == "beside":
            return {"x": 3.0 * side, "y": 0.0, "z": 0.0}

        if relation == "near":
            return {"x": 2.0 * side, "y": 0.0, "z": 1.0}

        if relation == "in_front_of":
            return {"x": 0.0, "y": 0.0, "z": -4.0}

        if relation == "behind":
            return {"x": 0.0, "y": 0.0, "z": 4.0}

        if relation == "above":
            return {"x": 0.0, "y": 3.0, "z": 0.0}

        if relation == "below":
            return {"x": 0.0, "y": -3.0, "z": 0.0}

        # These are real spatial relations, but not enough by themselves to
        # produce a static x/y/z offset unless the object resolves as an anchor.
        if relation in {"within", "between", "through"}:
            return None

        return None

    def _compact_spatial_evidence(self, relation_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Keep a small proof trail on the entity without copying the entire source file.
        """
        return {
            "signal_id": relation_record.get("signal_id"),
            "relation": relation_record.get("relation"),
            "subject_hint": relation_record.get("subject_hint"),
            "object_hint": relation_record.get("object_hint"),
            "confidence": relation_record.get("confidence"),
        }
    
    def _create_locations(self, where: str) -> List[Dict]:
        """Create location from @where path"""
        if not where:
            return []
        
        parts = where.split('/')
        location_name = parts[-1] if parts else 'Unknown'
        
        return [{
            'id': location_name.lower(),
            'name': location_name,
            'description': f"Location: {where}",
            'path': where,
            'type': 'area'
        }]
    
    def _extract_events(self, segments: List[Dict]) -> List[Dict]:
        """Extract events from segments"""
        events = []
        
        for i, seg in enumerate(segments):
            seg_type = seg.get('type', '')
            
            if seg_type == 'dialogue':
                events.append({
                    'type': 'dialogue',
                    'timestamp': i,
                    'actor': seg.get('speaker', 'unknown'),
                    'action': 'speak',
                    'data': {
                        'text': seg.get('text', ''),
                        'line': seg.get('line', 0)
                    }
                })
            
            elif seg_type in ('thought', 'internal_monologue'):
                events.append({
                    'type': 'thought',
                    'timestamp': i,
                    'actor': seg.get('subject', seg.get('thinker', seg.get('speaker', 'unknown'))),
                    'action': 'think',
                    'data': {
                        'text': seg.get('text', ''),
                        'line': seg.get('line', 0)
                    }
                })
        
        return events
    
    def _build_state(self, characters: List[Dict], locations: List[Dict]) -> Dict:
        """Build initial game state"""
        combat_entities = {}
        spatial_entities = {}
        
        for char in characters:
            combat_entities[char['id']] = {
                'health': char['health'],
                'max_health': char['max_health']
            }
            spatial_entities[char['id']] = char['position']
        
        return {
            'combat': {'entities': combat_entities},
            'spatial': {'entities': spatial_entities},
            'locations': locations
        }


def main():
    parser = argparse.ArgumentParser(description='Convert ZON to game scenes')
    parser.add_argument('zon_files', nargs='+', help='ZON files to convert')
    parser.add_argument('--output', default='./game_scenes', help='Output directory')
    parser.add_argument(
        '--world-rules',
        default=None,
        help='Path to world_rules.json for canonical names and spawnable filtering',
    )
    parser.add_argument(
        "--spatial-dir",
        default=None,
        help="Optional directory containing out_pass1_spatial_*.json files",
    )

    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    world_rules_path = Path(args.world_rules) if args.world_rules else None
    bridge = GameBridge(world_rules_path=world_rules_path)
    
    for zon_file in args.zon_files:
        zon_path = Path(zon_file)
        
        if not zon_path.exists():
            print(f"⚠ File not found: {zon_path}")
            continue
        
        print(f"Converting: {zon_path.name}")
        
        # Load ZON
        with zon_path.open('r') as f:
            zon_data = json.load(f)
        
        spatial_dir = Path(args.spatial_dir).expanduser() if args.spatial_dir else None
        spatial_relations = _load_spatial_relations_for_zon(
            zon_path=zon_path,
            zon_data=zon_data,
            spatial_dir=spatial_dir,
        )

        # Convert
        game_scene = bridge.convert_zon_to_game(
            zon_data,
            spatial_relations=spatial_relations,
        )
        
        # Save
        output_path = output_dir / f"{game_scene['scene_id']}.json"
        with output_path.open('w') as f:
            json.dump(game_scene, f, indent=2)
        
        print(f"  ✓ {game_scene['scene_id']}.json")
        print(f"    Characters: {len(game_scene['entities'])}")
        print(f"    Events: {len(game_scene['events'])}")
        print(f"    Location: {game_scene['metadata']['where']}")
        print()
    
    print(f"✓ Done! Game scenes in: {output_dir}")
    
    _build_scene_index(output_dir)

def _build_scene_index(output_dir: Path):
    scenes = []
    for f in output_dir.glob("*.json"):
        if f.name == "scene_index.json":
            continue
        try:
            with open(f, 'r') as fp:
                data = json.load(fp)
                
            scene_id = data.get("scene_id") or data.get("@id", f.stem)
            title = data.get("title") or data.get("@title", scene_id.replace("_", " "))
            
            meta = data.get("metadata", {})
            when = meta.get("when", data.get("@when", ""))
            where = meta.get("where", data.get("@where", ""))
            terrain_family = data.get("terrain_family", meta.get("terrain_family", ""))
            source_file = data.get("source_file", "")
            
            scenes.append({
                "scene_id": scene_id,
                "display_title": title,
                "cache_file": str(f.absolute()),
                "source_file": source_file,
                "where": where,
                "when": when,
                "terrain_family": terrain_family
            })
        except Exception as e:
            print(f"[pass5] Failed to index {f.name}: {e}")

    index_data = {"active_scenes": scenes}
    index_path = output_dir / "scene_index.json"
    with open(index_path, 'w') as fp:
        json.dump(index_data, fp, indent=2)
    print(f"Built scene_index.json with {len(scenes)} scenes at {index_path}")


if __name__ == '__main__':
    main()
