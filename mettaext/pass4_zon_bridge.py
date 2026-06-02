#!/usr/bin/env python3
"""
pass4_zon_bridge.py - Convert ZONJ narrative scenes to ZON memory fabric

Takes Pass3 ZONJ output and converts to ZON4D format with:
- Temporal anchoring (@when)
- Spatial anchoring (@where)
- Scope and entity tracking
- Proper semantic sections

Usage:
    python3 pass4_zon_bridge.py zonj_scene.json
    python3 pass4_zon_bridge.py zonj_scene.json --era FirstAge --location Beach
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class ZONMetadata:
    """Metadata for ZON temporal/spatial anchoring"""
    era: str = "Unknown"
    location: str = "Unknown"
    scope: str = "narrative"
    start_time: Optional[str] = None
    end_time: Optional[str] = None


_SPEAKER_STOPWORDS = frozenset({
    "unknown", "she", "he", "they", "someone", "narrator", "voice",
    "everyone", "all", "none", "it",
})

# ---------------------------------------------------------------------------
# Region metadata extraction
# ---------------------------------------------------------------------------

# Unified map for Prose and Legacy keywords
# Structure: {keyword: {"terrain_family": ..., "environment": ..., "is_topology": ...}}
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

# Legacy references preserved for backwards-compatibility checks
_TERRAIN_KEYWORD_MAP = [
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
    ("forest",       "grass"),
    ("valley",       "grass"),
    ("jungle",       "grass"),
    ("woods",        "grass"),
    ("mainland",     "grass"),
    ("plains",       "grass"),
    ("garden",       "grass"),
    ("mountain",     "grass"),
]

_TERRAIN_TO_ENV = {
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


def _derive_terrain_from_location(location: str) -> Dict[str, str]:
    """Derive terrain metadata from a --location arg (e.g. 'Beach')."""
    winning_tf, winning_env, votes_dict = _resolve_votes_for_text(location)
    return {
        "region": location,
        "environment": winning_env,
        "terrain_family": winning_tf,
        "spatial_scale_hint": "location",
        "environment_inference": {
            "source": "location_votes",
            "profile": winning_tf,
            "confidence": 0.9 if votes_dict else 0.5,
            "evidence": [f"{tf}:{count}" for tf, count in votes_dict.items()] if votes_dict else ["default_fallback"]
        }
    }


def _inject_terrain_meta(out: Dict, region_meta: Dict) -> None:
    """Write terrain fields in all three forms expected by the runtime."""
    for k, v in region_meta.items():
        if k == "environment_inference":
            out[k] = v
            continue
        out[f"@{k}"] = v  # @region, @environment, @terrain_family, @spatial_scale_hint
        out[k] = v         # region, environment, terrain_family, spatial_scale_hint
    if region_meta:
        md = out.setdefault("metadata", {})
        if not isinstance(md, dict):
            md = {}
            out["metadata"] = md
        for k, v in region_meta.items():
            md[k] = v  # metadata.region, metadata.environment, …


def _resolve_scene_terrain_meta(scene: Dict[str, Any], location: str) -> Dict[str, Any]:
    """
    Authoritative upstream semantic arbitration layer.
    Executes primary semantic extractor, fallback weighted voting, and legacy location overrides.
    """
    # 1. Start with any REGION: annotation explicit check
    segments = scene.get("segments") or scene.get("=segments") or []
    region_meta = extract_region_metadata(segments)
    
    # If REGION: was explicitly annotated and resolved a non-default family, use it
    if region_meta and region_meta.get("terrain_family", "default") != "default":
        region_meta["environment_inference"] = {
            "source": "explicit_annotation",
            "profile": region_meta["terrain_family"],
            "confidence": 1.0,
            "evidence": ["explicit:REGION_annotation"]
        }
        return region_meta

    # 2. Try the primary semantic environment extractor
    try:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent))
        import semantic_environment_extractor
        
        extracted = semantic_environment_extractor.extract(scene)
        # If the extractor resolved a non-default profile with positive confidence
        if extracted.get("environment_inference", {}).get("source") != "default":
            return {
                "region": extracted.get("region") or scene.get("@region") or location or "Inferred region",
                "terrain_family": extracted.get("terrain_family"),
                "environment": extracted.get("environment"),
                "spatial_scale_hint": extracted.get("spatial_scale_hint", "location"),
                "environment_inference": extracted.get("environment_inference")
            }
    except Exception as e:
        print(f"[pass4] Semantic Extractor failed: {e}")

    # 3. Fall back to weighted voting on narration prose
    narration_texts = []
    for seg in segments[:30]:
        if isinstance(seg, dict) and seg.get("type", "").lower() in ("narration", "description", "action"):
            text = seg.get("text", "")
            if text:
                narration_texts.append(text)
    combined_text = " ".join(narration_texts)
    
    winning_tf, winning_env, votes_dict = _resolve_votes_for_text(combined_text)
    if votes_dict and winning_tf != "default":
        return {
            "region": location if location.lower() not in ("", "unknown") else "Inferred terrain",
            "terrain_family": winning_tf,
            "environment": winning_env,
            "spatial_scale_hint": "location",
            "environment_inference": {
                "source": "inferred_votes",
                "profile": winning_tf,
                "confidence": 0.85,
                "evidence": [f"{tf}:{count}" for tf, count in votes_dict.items()]
            }
        }

    # 4. Fall back to location string weighted voting
    if location.lower() not in ("", "unknown"):
        return _derive_terrain_from_location(location)

    # 5. Default Grass fallback
    return {
        "region": "Unknown Region",
        "environment": "unknown",
        "terrain_family": "default",
        "spatial_scale_hint": "location",
        "environment_inference": {
            "source": "default_fallback",
            "profile": "default",
            "confidence": 0.0,
            "evidence": ["no_terrain_cues_found"]
        }
    }


def extract_region_metadata(segments: List[Dict]) -> Dict[str, str]:
    """Parse REGION: annotation from early narration segments into structured fields.

    Returns dict with keys: region, environment, terrain_family, spatial_scale_hint.
    Returns empty dict if no REGION: line found.
    """
    region_str = ""
    for seg in segments[:30]:
        if not isinstance(seg, dict):
            continue
        txt = (seg.get("text") or "").strip()
        if txt.startswith("REGION:"):
            region_str = txt[7:].strip()
            break

    if not region_str:
        return {}

    # Derive terrain from the primary (first) region area only
    primary = region_str.split(",")[0].strip().lower()

    winning_tf, winning_env, votes_dict = _resolve_votes_for_text(primary)

    if votes_dict:
        terrain_family = winning_tf
        environment = winning_env
    else:
        terrain_family = "default"
        environment = "unknown"

    # Multiple comma-separated areas or a "(brief)" qualifier → regional scale
    has_multiple = "," in region_str
    has_brief = "(brief)" in region_str.lower()
    spatial_scale_hint = "region" if (has_multiple or has_brief) else "location"

    return {
        "region": region_str,
        "environment": environment,
        "terrain_family": terrain_family,
        "spatial_scale_hint": spatial_scale_hint,
    }


class ZONBridge:
    """Convert ZONJ scenes to ZON memory fabric format"""

    def __init__(
        self,
        world_rules_path: Optional[Path] = None,
        scene_tags: Optional[List[str]] = None,
        scene_id_override: Optional[str] = None,
    ):
        self.known_entities = set()
        self.world_rules: Dict = {}
        self.scene_tags: List[str] = scene_tags or []
        self.scene_id_override: Optional[str] = scene_id_override
        if world_rules_path and Path(world_rules_path).exists():
            with open(world_rules_path, encoding="utf-8") as f:
                self.world_rules = json.load(f)

    # ------------------------------------------------------------------
    # World-rules helpers
    # ------------------------------------------------------------------

    def _wr_entities(self) -> Dict[str, Dict]:
        return self.world_rules.get("entities", {})

    def _resolve_to_canonical(self, name: str) -> Optional[str]:
        """Resolve a raw name to its canonical world_rules form.

        Tries (in order):
          1. Exact match of name vs key or canonical_name (case-insensitive)
          2. Exact match of name vs the *last word* of canonical_name
             (handles "GPT" → "Mr. GPT")
        """
        name_lower = name.lower()
        for key, entry in self._wr_entities().items():
            cn = entry.get("canonical_name", key)
            if cn.lower() == name_lower or key.lower() == name_lower:
                return cn
            last_word = cn.lower().split()[-1] if cn else ""
            if name_lower == last_word:
                return cn
        return None

    def _is_spawnable(self, canonical: str) -> bool:
        """Return True if the entity is individually spawnable."""
        for key, entry in self._wr_entities().items():
            cn = entry.get("canonical_name", key)
            if cn == canonical or key == canonical:
                if not entry.get("spawnable", True):
                    return False
                if entry.get("cardinality") in ("species", "collective", "abstract"):
                    return False
                return True
        return True  # unknown entity: don't filter

    # ------------------------------------------------------------------
    # Entity extraction
    # ------------------------------------------------------------------

    def extract_entities(self, obj: Dict[str, Any]) -> List[str]:
        """Extract canonical entity names from a scene or ZONJ object.

        Priority:
          1. If @entities already populated: normalise + filter spawnable.
          2. Otherwise: collect from segment speakers/inferred, then enrich
             via narration text scan and scene_tags injection.
        """
        existing = obj.get("@entities")
        if isinstance(existing, list) and existing:
            return self._normalise_and_filter(existing)

        segments = obj.get("segments", [])
        if not isinstance(segments, list):
            segments = []

        raw_names: List[str] = []

        for seg in segments:
            if not isinstance(seg, dict):
                continue
            sp = seg.get("speaker")
            if isinstance(sp, str) and sp.strip():
                raw_names.append(sp.strip())

            inferred = seg.get("inferred", {}) or {}
            for item in inferred.get("speaker_inferred", []):
                v = item.get("value") if isinstance(item, dict) else None
                if v:
                    raw_names.append(str(v).strip())
            for item in inferred.get("actor", []):
                v = item.get("value") if isinstance(item, dict) else None
                if v:
                    raw_names.append(str(v).strip())

        canonical: set = set()

        # Resolve segment names → canonical
        for name in raw_names:
            if name.lower() in _SPEAKER_STOPWORDS:
                continue
            resolved = self._resolve_to_canonical(name)
            canonical.add(resolved if resolved else name)

        # Narration scan: find canonical names that appear verbatim in text
        if self.world_rules:
            all_text = " ".join(
                (s.get("text", "") or "") for s in segments
            ).lower()
            for key, entry in self._wr_entities().items():
                if not entry.get("spawnable", True):
                    continue
                if entry.get("cardinality") in ("species", "collective", "abstract"):
                    continue
                cn = entry.get("canonical_name", key)
                if cn.lower() in all_text:
                    canonical.add(cn)

        # Scene-tags injection: add entities whose zw_tags overlap scene_tags
        if self.scene_tags and self.world_rules:
            for key, entry in self._wr_entities().items():
                if not entry.get("spawnable", True):
                    continue
                if entry.get("cardinality") in ("species", "collective", "abstract"):
                    continue
                entity_tags = entry.get("zw_tags", [])
                if any(t in entity_tags for t in self.scene_tags):
                    canonical.add(entry.get("canonical_name", key))

        # Final spawnable filter (removes non-physical entities found above)
        if self.world_rules:
            canonical = {c for c in canonical if self._is_spawnable(c)}

        return sorted(canonical)

    def _normalise_and_filter(self, names: List) -> List[str]:
        """Resolve a pre-existing entity list to canonical names and filter."""
        result: set = set()
        for raw in names:
            name = str(raw).strip()
            if not name or name.lower() in _SPEAKER_STOPWORDS:
                continue
            resolved = self._resolve_to_canonical(name)
            candidate = resolved if resolved else name
            if self.world_rules and not self._is_spawnable(candidate):
                continue
            result.add(candidate)
        return sorted(result)

    def build_zon_header(self, scene: Dict[str, Any], metadata: ZONMetadata) -> str:
        """Build ZON header section"""
        scene_id = self.scene_id_override or scene.get("id", "unknown_scene")
        entities = self.extract_entities(scene)

        region_meta = _resolve_scene_terrain_meta(scene, metadata.location)

        lines = []
        lines.append(f"@id: scene.{scene_id}")

        # Temporal anchor
        if metadata.start_time and metadata.end_time:
            lines.append(f"@when: {metadata.start_time}~{metadata.end_time}")
        else:
            lines.append(f"@when: {metadata.era}.scene_{scene_id}")

        # Spatial anchor
        lines.append(f"@where: Realm/Physical/{metadata.location}")

        # Scope
        lines.append(f"@scope: {metadata.scope}")

        # Entities
        if entities:
            entities_str = ", ".join(entities)
            lines.append(f"@entities: [{entities_str}]")

        # Region metadata (structured, not free-text)
        if region_meta:
            lines.append(f"@region: {region_meta['region']}")
            lines.append(f"@environment: {region_meta['environment']}")
            lines.append(f"@terrain_family: {region_meta['terrain_family']}")
            lines.append(f"@spatial_scale_hint: {region_meta['spatial_scale_hint']}")

        return "\n".join(lines)

    def build_segments_section(self, scene: Dict[str, Any]) -> str:
        """Build =segments section"""
        lines = ["=segments:"]

        for seg in scene.get("segments", []):
            if seg.get("type") == "blank":
                continue

            line_no = seg.get("line")
            seg_type = seg.get("type", "narration")
            text = seg.get("text", "")

            lines.append(f"  - line: {line_no}")
            lines.append(f"    type: {seg_type}")

            if "speaker" in seg:
                lines.append(f"    speaker: {seg['speaker']}")

            if text:
                text_escaped = str(text).replace('"', '\\"')
                lines.append(f'    text: "{text_escaped}"')

        return "\n".join(lines)

    def build_inferred_section(self, scene: Dict[str, Any]) -> str:
        """Build =inferred section"""
        lines = ["=inferred:"]

        emotions = []
        actions = []
        thoughts = []
        actors = []

        for seg in scene.get("segments", []):
            if seg.get("type") == "blank":
                continue

            line_no = seg.get("line")
            inferred = seg.get("inferred", {})

            for emo in inferred.get("emotion", []):
                emotions.append({
                    "line": line_no,
                    "subject": emo.get("subject"),
                    "emotion": emo.get("label"),
                    "confidence": float(emo.get("confidence", 0.0)),
                })

            for act in inferred.get("action", []):
                actions.append({
                    "line": line_no,
                    "action": act.get("label"),
                    "confidence": float(act.get("confidence", 0.0)),
                })

            for th in inferred.get("thought", []):
                thoughts.append({
                    "line": line_no,
                    "subject": th.get("subject"),
                    "confidence": float(th.get("confidence", 0.0)),
                })

            for ac in inferred.get("actor", []):
                actors.append({
                    "line": line_no,
                    "actor": ac.get("value"),
                    "confidence": float(ac.get("confidence", 0.0)),
                })

        if emotions:
            lines.append("  emotions:")
            for emo in emotions:
                lines.append(
                    f"    - {{line: {emo['line']}, subject: {emo['subject']}, "
                    f"emotion: {emo['emotion']}, confidence: {emo['confidence']:.2f}}}"
                )

        if actions:
            lines.append("  actions:")
            for act in actions:
                lines.append(
                    f"    - {{line: {act['line']}, action: {act['action']}, "
                    f"confidence: {act['confidence']:.2f}}}"
                )

        if thoughts:
            lines.append("  thoughts:")
            for th in thoughts:
                lines.append(
                    f"    - {{line: {th['line']}, subject: {th['subject']}, "
                    f"confidence: {th['confidence']:.2f}}}"
                )

        if actors:
            lines.append("  actors:")
            for ac in actors:
                lines.append(
                    f"    - {{line: {ac['line']}, actor: {ac['actor']}, "
                    f"confidence: {ac['confidence']:.2f}}}"
                )

        return "\n".join(lines)

    def build_narrative_section(self, scene: Dict[str, Any]) -> str:
        """Build =narrative summary section"""
        lines = ["=narrative:"]
        segment_types: Dict[str, int] = {}

        for seg in scene.get("segments", []):
            t = seg.get("type", "narration")
            segment_types[t] = segment_types.get(t, 0) + 1

        total_segments = sum(segment_types.values())
        lines.append(f'  "{scene.get("id", "unknown")} - {total_segments} segments"')

        for seg_type, count in sorted(segment_types.items()):
            lines.append(f"  {seg_type}: {count}")

        return "\n".join(lines)

    def convert_to_zon(self, zonj_path: Path, metadata: ZONMetadata) -> str:
        with zonj_path.open("r", encoding="utf-8") as f:
            scene = json.load(f)

        sections = [
            self.build_zon_header(scene, metadata),
            "",
            self.build_segments_section(scene),
            "",
            self.build_inferred_section(scene),
            "",
            self.build_narrative_section(scene),
        ]
        return "\n".join(sections)

    def convert_to_zonj(self, zonj_path: Path, metadata: ZONMetadata) -> Dict[str, Any]:
        with zonj_path.open("r", encoding="utf-8") as f:
            scene = json.load(f)

        # If the input already is a canonical ZONJ (has @id and =segments),
        # preserve it wholesale and only inject terrain metadata on top.
        existing_id = scene.get("@id")
        existing_segments = scene.get("=segments")
        if existing_id and isinstance(existing_segments, list) and existing_segments:
            out = dict(scene)
            region_meta = _resolve_scene_terrain_meta(scene, metadata.location)
            _inject_terrain_meta(out, region_meta)
            return out

        # --- Legacy path: rebuild from a raw ZONJ narrative object ---
        raw_id = self.scene_id_override or scene.get("@id", scene.get("id", "unknown_scene"))
        scene_id = raw_id[len("scene."):] if raw_id.startswith("scene.") else raw_id
        entities = self.extract_entities(scene)

        when_val = (
            f"{metadata.start_time}~{metadata.end_time}"
            if (metadata.start_time and metadata.end_time)
            else f"{metadata.era}.scene_{scene_id}"
        )

        all_segments = scene.get("=segments") or scene.get("segments") or []
        region_meta = _resolve_scene_terrain_meta(scene, metadata.location)

        zon_canonical: Dict[str, Any] = {
            "@id": f"scene.{scene_id}",
            "@when": when_val,
            "@where": f"Realm/Physical/{metadata.location}",
            "@scope": metadata.scope,
            "@entities": entities,
            "=segments": [],
            "=inferred": {
                "emotions": [],
                "actions": [],
                "thoughts": [],
                "actors": [],
            },
            "=metadata": {
                "source_format": "zonj_narrative",
                "source_files": scene.get("source_files", {}),
            },
        }

        _inject_terrain_meta(zon_canonical, region_meta)

        # Segments
        for seg in (scene.get("=segments") or scene.get("segments") or []):
            if seg.get("type") == "blank":
                continue
            entry = {"line": seg.get("line"), "type": seg.get("type")}
            if "speaker" in seg:
                entry["speaker"] = seg.get("speaker")
            if "text" in seg:
                entry["text"] = seg.get("text")
            zon_canonical["=segments"].append(entry)

        # Inferred
        for seg in (scene.get("=segments") or scene.get("segments") or []):
            inferred = seg.get("inferred", {})
            line_no = seg.get("line")

            for emo in inferred.get("emotion", []):
                zon_canonical["=inferred"]["emotions"].append({
                    "line": line_no,
                    "subject": emo.get("subject"),
                    "emotion": emo.get("label"),
                    "confidence": emo.get("confidence"),
                })
            for act in inferred.get("action", []):
                zon_canonical["=inferred"]["actions"].append({
                    "line": line_no,
                    "action": act.get("label"),
                    "confidence": act.get("confidence"),
                })
            for th in inferred.get("thought", []):
                zon_canonical["=inferred"]["thoughts"].append({
                    "line": line_no,
                    "subject": th.get("subject"),
                    "confidence": th.get("confidence"),
                })
            for ac in inferred.get("actor", []):
                zon_canonical["=inferred"]["actors"].append({
                    "line": line_no,
                    "actor": ac.get("value"),
                    "confidence": ac.get("confidence"),
                })

        return zon_canonical


def main():
    parser = argparse.ArgumentParser(
        description="Convert ZONJ narrative scenes to ZON memory fabric format"
    )
    parser.add_argument("input", help="Input ZONJ scene file")
    parser.add_argument("--era", default="Unknown", help="Temporal era (e.g. FirstAge)")
    parser.add_argument("--location", default="Unknown", help="Spatial location (e.g. Beach)")
    parser.add_argument("--scope", default="narrative", help="Scope (narrative/canon/log)")
    parser.add_argument("--start", help="Start time (ISO or relative)")
    parser.add_argument("--end", help="End time (ISO or relative)")
    parser.add_argument("--output-dir", default=".", help="Output directory")
    parser.add_argument(
        "--world-rules",
        default=None,
        help="Path to world_rules.json for canonical entity resolution and filtering",
    )
    parser.add_argument(
        "--scene-tags",
        default=None,
        help="Comma-separated zw_tags to inject cast from world_rules (e.g. chapter_102)",
    )
    parser.add_argument(
        "--scene-id",
        default=None,
        help="Override the scene id written into @id (e.g. 102_convergence_on_mars)",
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}")
        sys.exit(1)

    world_rules_path = Path(args.world_rules) if args.world_rules else None
    scene_tags = [t.strip() for t in args.scene_tags.split(",")] if args.scene_tags else []

    metadata = ZONMetadata(
        era=args.era,
        location=args.location,
        scope=args.scope,
        start_time=args.start,
        end_time=args.end,
    )

    bridge = ZONBridge(
        world_rules_path=world_rules_path,
        scene_tags=scene_tags,
        scene_id_override=args.scene_id,
    )

    zon_text = bridge.convert_to_zon(input_path, metadata)
    zon_json = bridge.convert_to_zonj(input_path, metadata)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    scene_id = args.scene_id or input_path.stem.replace("zonj_", "")
    zon_path = output_dir / f"{scene_id}.zon"
    zonj_path = output_dir / f"{scene_id}.zonj.json"

    with zon_path.open("w", encoding="utf-8") as f:
        f.write(zon_text)

    with zonj_path.open("w", encoding="utf-8") as f:
        json.dump(zon_json, f, ensure_ascii=False, indent=2)

    print(f"[PASS4] Converted to ZON format:")
    print(f"  Human-readable: {zon_path}")
    print(f"  Canonical JSON: {zonj_path}")
    print(f"  Era: {metadata.era}")
    print(f"  Location: {metadata.location}")

    entities = zon_json.get("@entities") or bridge.extract_entities(zon_json)
    if entities:
        print(f"  Entities ({len(entities)}): {', '.join(entities)}")


if __name__ == "__main__":
    main()
