#!/usr/bin/env python3
"""
scene_shell_builder.py — Narrative → World delta generator for EngAIn.

Responsibility:
  Take narrative text + hints → produce list of world deltas.

DOES NOT:
  - mutate world state
  - talk to adapter
  - generate art

API:
  build_scene_shell(...) → List[dict]
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .trixel_world_mr import (
    WorldGridConfig,
    TerrainType,
    make_cell_id,
    create_empty_grid,
    step_trixel_world,   # ← USED for snapshot application
)
from .scene_feature_registry import ensure_default_features_registered, get_feature_generator

# -----------------------------------------------------------
# Classification (UNCHANGED)
# -----------------------------------------------------------

@dataclass
class SceneHints:
    scene_id: str
    chapter_text: str
    corpus_hints: Optional[Dict[str, str]] = None
    world_tags: Optional[List[str]] = None

    def text_lower(self) -> str:
        return self.chapter_text.lower()

    def tags_lower(self) -> List[str]:
        return [t.lower() for t in (self.world_tags or [])]

    def has_any(self, words: List[str]) -> bool:
        tl = self.text_lower()
        return any(w in tl for w in words)

    def tag_any(self, words: List[str]) -> bool:
        tl = self.tags_lower()
        return any(w in tl for w in words)


def classify_scene(hints: SceneHints) -> Dict[str, bool]:
    tl = hints.text_lower()
    tags = hints.tags_lower()
    ch = hints.corpus_hints or {}

    def t_or_tag(words: List[str]) -> bool:
        return any(w in tl for w in words) or any(w in tags for w in words)

    is_beach = t_or_tag(["beach", "shore", "coast", "sea", "ocean", "shoreline"])
    has_pier = t_or_tag(["pier", "dock", "harbor", "jetty", "wharf"])
    has_secret = t_or_tag([
        "secret path", "hidden path", "hidden passage",
        "secret passage", "hidden route", "concealed path",
        "concealed route", "hidden trail", "narrow opening",
        "path through the trees",
    ])
    has_construction = t_or_tag([
        "construction", "building pyramids", "pyramids", "worksite", "scaffolding"
    ])

    scene_type = ch.get("scene_type", "").lower()
    if scene_type == "beach":
        is_beach = True
    if ch.get("has_pier", "").lower() in ("true", "yes", "1"):
        has_pier = True

    return {
        "is_beach": is_beach,
        "has_pier": has_pier,
        "has_secret": has_secret,
        "has_construction": has_construction,
    }

# -----------------------------------------------------------
# Base Terrain (UNCHANGED – only beach bands for now)
# -----------------------------------------------------------

def _make_region(
    x_min: int,
    y_min: int,
    x_max: int,
    y_max: int,
    terrain: TerrainType,
    skin_id: Optional[str] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "x_min": x_min,
        "y_min": y_min,
        "x_max": x_max,
        "y_max": y_max,
        "terrain_type": terrain.value,
    }
    if skin_id is not None:
        payload["skin_id"] = skin_id
    return {
        "id": f"fill_{terrain.value}_{x_min}_{y_min}_{x_max}_{y_max}",
        "type": "fill_region",
        "payload": payload,
    }

def _generate_beach_bands(config: WorldGridConfig) -> List[Dict[str, Any]]:
    h, w = config.grid_height, config.grid_width
    deltas: List[Dict[str, Any]] = []

    deep_max    = min(2,  h-1)
    shallow_max = min(4,  h-1)
    shoreline   = min(5,  h-1)
    sand_max    = min(10, h-1)
    grass_max   = min(13, h-1)
    forest_max  = min(15, h-1)

    if deep_max >= 0:
        deltas.append(_make_region(0, 0, w-1, deep_max, TerrainType.DEEP_WATER))
    if shallow_max >= 3 and h > 3:
        deltas.append(_make_region(0, 3, w-1, shallow_max, TerrainType.SHALLOW_WATER))
    if shoreline < h:
        deltas.append(_make_region(0, shoreline, w-1, shoreline, TerrainType.SHORELINE))
    if sand_max >= 6 and h > 6:
        deltas.append(_make_region(0, 6, w-1, sand_max, TerrainType.SAND))
    if grass_max >= 11 and h > 11:
        deltas.append(_make_region(0, 11, w-1, grass_max, TerrainType.GRASS))
    if forest_max >= 14 and h > 14:
        deltas.append(_make_region(0, 14, w-1, forest_max, TerrainType.FOREST_EDGE))

    return deltas

# -----------------------------------------------------------
# Snapshot Handling (Simplified – no feature helpers here!)
# -----------------------------------------------------------

def _make_planning_snapshot(
    config: WorldGridConfig,
    snapshot: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Build a **mutable** planning snapshot.
    Re-uses existing snapshot if provided.
    """
    cells = create_empty_grid(config)
    features: Dict[str, Dict[str, Any]] = {}
    skin_table: Dict[str, Any] = {}
    tick = 0.0

    if snapshot:
        # Merge existing cells into empty grid
        world = snapshot.get("trixel_world", snapshot)
        if isinstance(world, dict):
            existing_cells = world.get("cells", {})
            for cid, cell in existing_cells.items():
                if cid in cells and isinstance(cell, dict):
                    cells[cid].update(cell)   # shallow merge

            features = world.get("features", {}).copy()
            skin_table = world.get("skin_table", {}).copy()
            tick = float(world.get("tick", 0.0))

    return {
        "trixel_world": {
            "cells": cells,
            "features": features,
            "skin_table": skin_table,
            "tick": tick,
        }
    }

def _apply_deltas_to_snapshot(
    snapshot: Dict[str, Any],
    deltas: List[Dict[str, Any]],
    config: WorldGridConfig,
) -> Dict[str, Any]:
    """
    Apply deltas to snapshot using `step_trixel_world`.
    Returns **new** snapshot (immutable operation).
    """
    out, _, _ = step_trixel_world(
        snapshot_in=snapshot,
        deltas=deltas,
        config=config,
        delta_time=0.0,   # planning phase – no time advance
    )
    return out

# -----------------------------------------------------------
# PUBLIC ENTRY POINT
# -----------------------------------------------------------

def build_scene_shell(
    scene_id: str,
    chapter_text: str,
    config: WorldGridConfig,
    corpus_hints: Optional[Dict[str, str]] = None,
    world_tags: Optional[List[str]] = None,
    snapshot: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Generates world deltas for a scene.

    Order of operations (critical for correctness):
      1. Base terrain
      2. Pier   → (snapshot now contains pier)
      3. Secret → (snapshot now contains secret)
      4. Construction (pyramid) → sees pier + secret

    All placement is **relative** and deterministic per `scene_id`.
    """
    ensure_default_features_registered()  # ← Loads beach features lazily

    hints = SceneHints(
        scene_id=scene_id,
        chapter_text=chapter_text,
        corpus_hints=corpus_hints,
        world_tags=world_tags,
    )
    flags = classify_scene(hints)

    deltas: List[Dict[str, Any]] = []
    planning_snapshot = _make_planning_snapshot(config, snapshot)

    # ---- 1) Base terrain (beach bands if applicable) ----
    if flags["is_beach"]:
        base_deltas = _generate_beach_bands(config)
        deltas.extend(base_deltas)
        planning_snapshot = _apply_deltas_to_snapshot(planning_snapshot, base_deltas, config)

    # ---- 2) Pier ----
    if flags["has_pier"]:
        gen = get_feature_generator("pier_main")
        if gen:
            pier_deltas = gen(scene_id=scene_id, config=config, snapshot=planning_snapshot)
            deltas.extend(pier_deltas)
            planning_snapshot = _apply_deltas_to_snapshot(planning_snapshot, pier_deltas, config)

    # ---- 3) Secret Path ----
    if flags["has_secret"]:
        gen = get_feature_generator("secret_path_01")
        if gen:
            secret_deltas = gen(scene_id=scene_id, config=config, snapshot=planning_snapshot)
            deltas.extend(secret_deltas)
            planning_snapshot = _apply_deltas_to_snapshot(planning_snapshot, secret_deltas, config)

    # ---- 4) Pyramid Construction Site ----
    if flags["has_construction"]:
        gen = get_feature_generator("pyramid_site_01")
        if gen:
            cons_deltas = gen(scene_id=scene_id, config=config, snapshot=planning_snapshot)
            deltas.extend(cons_deltas)
            planning_snapshot = _apply_deltas_to_snapshot(planning_snapshot, cons_deltas, config)

    # Tag every delta with scene_id for auditability
    for d in deltas:
        d.setdefault("payload", {})["scene_id"] = scene_id

    return deltas

# -----------------------------------------------------------
# Smoke Test (works exactly as before)
# -----------------------------------------------------------

if __name__ == "__main__":
    from .trixel_world_mr import WorldGridConfig

    cfg = WorldGridConfig(grid_width=16, grid_height=16, tile_size=16)
    text = (
        "They were building pyramids on the sand near a tree ridge. "
        "To the north, the sea lapped at a long wooden pier. "
        "Locals whispered of a secret path through the forest edge."
    )
    deltas = build_scene_shell(
        scene_id="scene_beach_001",
        chapter_text=text,
        config=cfg,
        corpus_hints={"scene_type": "beach"},
        world_tags=["beach", "pier", "secret"],
    )
    import json
    print(json.dumps(deltas, indent=2))
