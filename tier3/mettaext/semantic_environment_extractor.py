#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path
from typing import Any

PROFILES = [
    "coastal",
    "forest",
    "wasteland",
    "industrial",
    "volcanic",
    "underground",
    "cosmic",
    "urban",
    "default",
]

PROFILE_KEYWORDS = {
    "coastal": ["coast", "coastal", "shore", "shoreline", "beach", "ocean", "sea", "harbor", "bay", "tide", "wetland"],
    "forest": ["forest", "woods", "woodland", "grove", "jungle", "thicket", "canopy", "tree", "moss"],
    "wasteland": ["wasteland", "desert", "dune", "dust", "ash", "barren", "ruin", "ruins", "scrap", "badlands"],
    "industrial": ["factory", "industrial", "engine", "machine", "reactor", "facility", "plant", "pipeline", "forge", "assembly", "workshop"],
    "volcanic": ["volcano", "volcanic", "lava", "magma", "molten", "basalt", "caldera", "fissure", "ember"],
    "underground": ["underground", "subterranean", "cavern", "cave", "tunnel", "mine", "depth", "catacomb", "vault"],
    "cosmic": ["cosmic", "void", "stellar", "astral", "orbital", "space", "galactic", "nebula", "rift", "paradox"],
    "urban": ["city", "urban", "street", "district", "plaza", "tower", "market", "alley", "metro", "residential"],
}

SCALE_KEYWORDS = [
    ("massive", ["continent", "world", "planet", "vast", "mega", "megastructure", "endless"]),
    ("large", ["large", "city", "district", "sprawl", "expanse"]),
    ("medium", ["facility", "compound", "sector", "valley", "forest", "coast"]),
    ("small", ["room", "chamber", "hall", "camp", "site", "node"]),
    ("tiny", ["closet", "cell", "alcove", "pod", "booth"]),
]


def _as_text(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, str):
        return v
    if isinstance(v, (int, float, bool)):
        return str(v)
    return ""


def _flatten_text(v: Any) -> str:
    if isinstance(v, str):
        return v
    if isinstance(v, dict):
        parts = []
        for val in v.values():
            parts.append(_flatten_text(val))
        return " ".join(p for p in parts if p)
    if isinstance(v, list):
        parts = []
        for item in v:
            parts.append(_flatten_text(item))
        return " ".join(p for p in parts if p)
    return _as_text(v)


def _first_nonempty(*vals: Any) -> str:
    for val in vals:
        s = _as_text(val).strip()
        if s:
            return s
    return ""


def _extract_list(scene: dict, key: str, alt_key: str | None = None) -> list:
    raw = scene.get(key, scene.get(alt_key, [])) if alt_key else scene.get(key, [])
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        return list(raw.values())
    if isinstance(raw, str) and raw.strip():
        return [raw.strip()]
    return []


def _short_snippets(scene: dict) -> list[str]:
    snippets: list[str] = []
    fields = [
        "terrain_family", "@terrain_family", "environment", "@environment",
        "region", "@region", "where", "title",
    ]
    for f in fields:
        s = _as_text(scene.get(f, "")).strip()
        if s:
            snippets.append(f"{f}:{s[:80]}")

    for f in ["spatial_hints", "zon_blocks", "segments", "entities", "events", "locations"]:
        raw = scene.get(f, [])
        if isinstance(raw, list):
            for item in raw[:5]:
                text = _flatten_text(item)
                text = re.sub(r"\s+", " ", text).strip()
                if text:
                    snippets.append(f"{f}:{text[:80]}")
        elif isinstance(raw, dict):
            text = _flatten_text(raw)
            text = re.sub(r"\s+", " ", text).strip()
            if text:
                snippets.append(f"{f}:{text[:80]}")

    out: list[str] = []
    seen = set()
    for s in snippets:
        if s not in seen:
            seen.add(s)
            out.append(s)
        if len(out) >= 8:
            break
    return out


def _score_profile(scene: dict) -> tuple[str, float, list[str]]:
    explicit = _first_nonempty(
        scene.get("terrain_family"),
        scene.get("@terrain_family"),
        scene.get("environment"),
        scene.get("@environment"),
        scene.get("region"),
        scene.get("@region"),
    ).lower()

    if explicit in PROFILES and explicit != "default":
        return explicit, 1.0, [f"explicit:{explicit}"]

    corpus_parts = []
    for k in [
        "terrain_family", "@terrain_family", "environment", "@environment", "region", "@region",
        "where", "locations", "spatial_hints", "zon_blocks", "segments", "entities", "events",
    ]:
        corpus_parts.append(_flatten_text(scene.get(k, "")))
    corpus = re.sub(r"\s+", " ", " ".join(corpus_parts)).lower()

    token_scores = {p: 0 for p in PROFILES}
    evidence = {p: [] for p in PROFILES}

    for profile, keywords in PROFILE_KEYWORDS.items():
        for kw in keywords:
            if re.search(rf"\b{re.escape(kw)}\b", corpus):
                token_scores[profile] += 1
                if len(evidence[profile]) < 3:
                    evidence[profile].append(kw)

    best = "default"
    best_score = 0
    for p in PROFILES:
        if p == "default":
            continue
        if token_scores[p] > best_score:
            best_score = token_scores[p]
            best = p

    if best_score == 0:
        return "default", 0.0, []

    confidence = min(0.95, 0.25 + (best_score * 0.12))
    ev = [f"kw:{k}" for k in evidence[best]]
    return best, round(confidence, 2), ev


def _infer_scale(scene: dict) -> str:
    explicit = _first_nonempty(scene.get("spatial_scale_hint"), scene.get("@spatial_scale_hint")).lower()
    if explicit in {"tiny", "small", "medium", "large", "massive"}:
        return explicit

    corpus = _flatten_text({
        "spatial_hints": scene.get("spatial_hints", []),
        "locations": scene.get("locations", []),
        "segments": scene.get("segments", []),
        "zon_blocks": scene.get("zon_blocks", []),
    }).lower()
    for scale, kws in SCALE_KEYWORDS:
        for kw in kws:
            if re.search(rf"\b{re.escape(kw)}\b", corpus):
                return scale
    return "medium"


def extract(scene: dict) -> dict:
    profile, confidence, profile_evidence = _score_profile(scene)

    terrain_family = _first_nonempty(scene.get("terrain_family"), scene.get("@terrain_family"))
    environment = _first_nonempty(scene.get("environment"), scene.get("@environment"))
    region = _first_nonempty(scene.get("region"), scene.get("@region"))

    if not terrain_family:
        terrain_family = profile if profile != "default" else ""
    if not environment:
        environment = profile if profile != "default" else region.lower().strip()

    locations = _extract_list(scene, "locations")
    landmarks = _extract_list(scene, "landmarks")
    spatial_hints = _extract_list(scene, "spatial_hints", "spatialHints")

    source = "default"
    explicit_exists = any([
        _first_nonempty(scene.get("terrain_family")),
        _first_nonempty(scene.get("@terrain_family")),
        _first_nonempty(scene.get("environment")),
        _first_nonempty(scene.get("@environment")),
    ])
    if explicit_exists:
        source = "explicit"
    elif profile != "default" and confidence >= 0.45:
        source = "inferred"

    env_profile = profile if source != "default" else "default"
    evidence = profile_evidence + _short_snippets(scene)

    return {
        "terrain_family": terrain_family.lower().strip(),
        "environment": environment.lower().strip(),
        "locations": locations,
        "landmarks": landmarks,
        "spatial_hints": spatial_hints,
        "spatial_scale_hint": _infer_scale(scene),
        "environment_inference": {
            "source": source,
            "profile": env_profile,
            "confidence": float(confidence if source != "default" else 0.0),
            "evidence": evidence[:8],
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene-json", required=True)
    args = ap.parse_args()

    p = Path(args.scene_json)
    if not p.exists():
        print(json.dumps({
            "terrain_family": "",
            "environment": "",
            "locations": [],
            "landmarks": [],
            "spatial_hints": [],
            "spatial_scale_hint": "medium",
            "environment_inference": {
                "source": "default",
                "profile": "default",
                "confidence": 0.0,
                "evidence": ["scene_json_missing"],
            },
        }, ensure_ascii=False))
        return

    with p.open("r", encoding="utf-8") as f:
        scene = json.load(f)

    if not isinstance(scene, dict):
        scene = {}

    print(json.dumps(extract(scene), ensure_ascii=False))


if __name__ == "__main__":
    main()
