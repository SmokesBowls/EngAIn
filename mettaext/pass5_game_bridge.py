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
from typing import Dict, Any, List, Optional


def _slugify(name: str) -> str:
    """Convert a canonical name to a safe entity id slug."""
    import re
    s = name.lower().replace(".", "").replace(" ", "_")
    return re.sub(r"_+", "_", s).strip("_")


# ---------------------------------------------------------------------------
# Region metadata extraction (mirrors pass4; reads @ fields first)
# ---------------------------------------------------------------------------

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

# Same table mirrored in pass4 — keep in sync manually if adding entries.

_TERRAIN_TO_ENV: Dict[str, str] = {
    "beach":   "coastal",
    "sand":    "arid",
    "grass":   "temperate",
    "default": "unknown",
}

# === PROSE FALLBACK KEYWORD MAP ===
_PROSE_TERRAIN_MAP = {
    # Ash/Wasteland cluster
    "ash":        {"terrain_family": "ash",     "environment": "wasteland", "scale": "region"},
    "grey":       {"terrain_family": "stone",   "environment": "wasteland", "scale": "region"},
    "gray":       {"terrain_family": "stone",   "environment": "wasteland", "scale": "region"},
    "mist":       {"terrain_family": "shrouded","environment": "wasteland", "scale": "region"},
    "fog":        {"terrain_family": "shrouded","environment": "ambient",   "scale": "region"},
    "starless":   {"terrain_family": "void",    "environment": "wasteland", "scale": "region"},
    "twilight":   {"terrain_family": "shadow",  "environment": "ambient",   "scale": "region"},
    "dusk":       {"terrain_family": "shadow",  "environment": "ambient",   "scale": "region"},
    "wasteland":  {"terrain_family": "barren",  "environment": "wasteland", "scale": "region"},
    "barren":     {"terrain_family": "barren",  "environment": "wasteland", "scale": "region"},
    "desolate":   {"terrain_family": "barren",  "environment": "wasteland", "scale": "region"},
    "plain":      {"terrain_family": "flat",    "environment": "open",      "scale": "region"},
    "featureless":{"terrain_family": "flat",    "environment": "wasteland", "scale": "region"},
    "powder":     {"terrain_family": "dust",    "environment": "wasteland", "scale": "region"},
    "dust":       {"terrain_family": "dust",    "environment": "arid",      "scale": "region"},
    "cracks":     {"terrain_family": "fissure", "environment": "wasteland", "scale": "region"}
}

def _infer_terrain_from_prose(segments: list, max_segments: int = 30) -> dict | None:
    """
    Falls back to prose scanning when explicit REGION: metadata is absent.
    Scans first N narration segments for terrain descriptors.
    """
    if not segments:
        return None

    scores = {}
    context_words = []
    family_meta = {}

    for seg in segments[:max_segments]:
        text = seg.get("text", "").lower()
        if not text:
            continue
            
        # Keep first 12 descriptive words for region string construction
        words = [w.strip(".,;:!?\"'()[]{}") for w in text.split() if len(w) > 3]
        context_words.extend(words[:12])

        for word in words:
            if word in _PROSE_TERRAIN_MAP:
                entry = _PROSE_TERRAIN_MAP[word]
                family = entry["terrain_family"]

                scores[family] = scores.get(family, 0) + 1

                if family not in family_meta:
                    family_meta[family] = entry

    if not scores:
        return None

    # Pick highest-confidence family
    best_family = max(scores, key=scores.get)
    meta = family_meta[best_family]

    # Construct region string from captured prose context
    region_desc = " ".join(context_words[:10]).capitalize()
    if len(region_desc) < 4:
        region_desc = "Inferred terrain region"

    return {
        "region": region_desc,
        "terrain_family": best_family,
        "environment": meta["environment"],
        "spatial_scale_hint": meta["scale"],
        "confidence": "inferred_prose",
        "match_count": scores[best_family]
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
        terrain_family = "default"
        for keyword, tf in _TERRAIN_KEYWORD_MAP:
            if keyword in primary:
                terrain_family = tf
                break
        environment = _TERRAIN_TO_ENV.get(terrain_family, "unknown")
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
        for keyword, tf in _TERRAIN_KEYWORD_MAP:
            if keyword in where:
                return {
                    "region": where.split("/")[-1].capitalize(),
                    "environment": _TERRAIN_TO_ENV.get(tf, "unknown"),
                    "terrain_family": tf,
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

    def convert_zon_to_game(self, zon_data: Dict[str, Any]) -> Dict[str, Any]:
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
        characters = self._create_characters(entity_list)

        # Extract location from @where
        where = zon_data.get('@where', '')
        locations = self._create_locations(where)

        # Extract events from segments
        events = self._extract_events(segments)

        # Extract structured region metadata
        region_meta = _extract_region_metadata(zon_data)

        # 🔍 PROSE FALLBACK: Only when REGION: is absent
        if not region_meta or region_meta.get("terrain_family", "default") == "default":
            narration_segments = [s for s in segments if s.get("type", "").lower() in ("narration", "description", "action")]
            terrain_meta = _infer_terrain_from_prose(narration_segments, max_segments=30)
            if terrain_meta:
                region_meta = terrain_meta
                print(f"[pass5] Prose inference triggered for {scene_id} → terrain_family: {terrain_meta['terrain_family']}")

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
        metadata['level_design'] = level_design

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
        }

        return output
    
    def _get_description(self, segments: List[Dict]) -> str:
        """Get scene description from first narration"""
        for seg in segments[:10]:
            if seg.get('type') == 'narration':
                return seg.get('text', '')[:200]
        return ''
    
    def _create_characters(self, entity_list: List[str]) -> List[Dict]:
        """Create character entries, filtering non-spawnable and using canonical names."""
        characters = []
        position = 0
        for raw in entity_list:
            canonical = self._canonical_name(raw)
            if not self._is_spawnable(canonical):
                continue
            characters.append({
                'id': _slugify(canonical),
                'name': canonical,
                'health': 100.0,
                'max_health': 100.0,
                'position': {'x': position * 5, 'y': 0, 'z': 0},
                'type': 'character',
            })
            position += 1
        return characters
    
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
        
        # Convert
        game_scene = bridge.convert_zon_to_game(zon_data)
        
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


if __name__ == '__main__':
    main()
