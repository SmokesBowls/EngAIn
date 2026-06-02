#!/usr/bin/env python3
import json
import re
from typing import Any, Dict, List

from spatial_pattern_matcher import extract_spatial_facts

def extract_from_zonj(zonj_data: Dict[str, Any]) -> Dict[str, Any]:
    regions = {}
    for seg_id, seg in zonj_data.get("=segments", {}).items():
        if seg.get("type") in ("location", "landmark", "terrain"):
            rid = seg.get("id", seg_id)
            regions[rid] = {
                "id": rid,
                "terrain_class": seg.get("terrain_class", "default"),
                "quadrant_hint": _infer_quadrant(seg.get("description", "")),
                "adjacency_hints": _extract_adjacency(seg.get("description", "")),
                "landmarks": seg.get("contains", []),
            }
    return {"version": "1.0", "source": "zonj", "regions": regions, "edges": _build_edges_from_adjacency(regions)}

def extract_from_vault_md(md_text: str) -> Dict[str, Any]:
    facts = extract_spatial_facts(md_text)

    regions = {}
    for rid, rdata in facts.get("regions", {}).items():
        regions[rid] = {
            "id": rid,
            "terrain_class": _region_type_to_terrain(rdata.get("type", "unknown")),
            "quadrant_hint": "center",
            "adjacency_hints": [],
            "landmarks": [],
            "type": rdata.get("type", "unknown"),
            "mentions": rdata.get("mentions", 0),
        }

    edges = []
    for e in facts.get("edges", []):
        edges.append({
            "from": e["from"],
            "to": e["to"],
            "relation": e["relation"],
            "strength": e.get("strength", e.get("confidence", 0.75)),
            "source": e.get("source", ""),
        })

    return {"version": "1.0", "source": "vault_md", "regions": regions, "edges": edges}

def extract_from_scene_json(scene_data: Dict[str, Any]) -> Dict[str, Any]:
    regions = {}
    for loc in scene_data.get("locations", []):
        regions[loc["id"]] = {
            "id": loc["id"],
            "terrain_class": loc.get("terrain", "default"),
            "quadrant_hint": loc.get("position_hint", "center"),
            "adjacency_hints": loc.get("borders", []),
            "landmarks": loc.get("landmarks", []),
        }
    return {"version": "1.0", "source": "scene_json", "regions": regions, "edges": _build_edges_from_adjacency(regions)}

def _infer_quadrant(text: str) -> str:
    text = text.lower()
    if "northwest" in text or "north-west" in text: return "northwest"
    if "northeast" in text or "north-east" in text: return "northeast"
    if "southwest" in text or "south-west" in text: return "southwest"
    if "southeast" in text or "south-east" in text: return "southeast"
    if "north" in text or "northern" in text: return "north"
    if "south" in text or "southern" in text: return "south"
    if "east" in text or "eastern" in text: return "east"
    if "west" in text or "western" in text: return "west"
    return "center"

def _region_type_to_terrain(region_type: str) -> str:
    return {
        "landmark": "landmark",
        "valley": "fertile_valley",
        "hills": "rocky_hills",
        "wetlands": "wetlands",
        "plains": "arid_plains",
        "volcanic": "volcanic_caldera",
        "mountain": "alpine_spine",
        "coastal": "coastal_settlement",
    }.get(region_type, "default")

def _extract_adjacency(text: str) -> List[str]:
    return re.findall(r"(?:borders|touches|adjacent to|near)\s+([\w\s]+)", text.lower())

def _build_edges_from_adjacency(regions: Dict[str, Any]) -> List[Dict[str, Any]]:
    edges = []
    for rid, rdata in regions.items():
        for adj in rdata.get("adjacency_hints", []):
            adj_id = adj.strip().replace(" ", "_")
            if adj_id in regions:
                edges.append({"from": rid, "to": adj_id, "relation": "adjacent_to", "strength": 0.6})
    return edges
