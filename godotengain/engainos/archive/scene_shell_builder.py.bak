#!/usr/bin/env python3
"""
scene_shell_builder.py — Narrative → World delta generator for EngAIn.

Responsibility:
  Take narrative text (chapter/scene chunk) plus light hints and
  produce a list of world deltas suitable for TrixelWorldAdapter /
  TrixelWorldZWRouter.

It does NOT:
  - mutate world state
  - talk to the adapter directly
  - generate tileset art

It ONLY:
  - inspects text + hints
  - classifies high-level scene type(s)
  - emits deltas like:
      - fill_region
      - add_feature
      - add_override

API:
  build_scene_shell(scene_id, chapter_text, config, corpus_hints=None, world_tags=None) -> List[dict]
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

try:
    from .trixel_world_mr import WorldGridConfig, TerrainType, make_cell_id
except ImportError:
    from trixel_world_mr import WorldGridConfig, TerrainType, make_cell_id


# ============================================================
# Simple classifiers / hints
# ============================================================

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
    """
    Very simple scene classifier.

    Returns flags:
      - is_beach
      - has_pier
      - has_secret
      - has_construction

    corpus_hints is currently mostly dormant; future versions can
    use it to override weak textual signals (e.g. scene_type="beach").
    """
    tl = hints.text_lower()
    tags = hints.tags_lower()
    ch = hints.corpus_hints or {}

    def t_or_tag(words: List[str]) -> bool:
        return any(w in tl for w in words) or any(w in tags for w in words)

    is_beach = t_or_tag(["beach", "shore", "coast", "sea", "ocean", "shoreline"])
    has_pier = t_or_tag(["pier", "dock", "harbor", "jetty", "wharf"])
    has_secret = t_or_tag([
        "secret path",
        "hidden path",
        "hidden passage",
        "secret passage",
        "hidden route",
        "concealed path",
        "concealed route",
        "hidden trail",
        "narrow opening",
        "path through the trees",
    ])
    has_construction = t_or_tag(["construction", "building pyramids", "pyramids", "worksite", "scaffolding"])

    # Simple override hooks for future refinement
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


# ============================================================
# Layout utilities
# ============================================================

def _make_region(
    x_min: int,
    y_min: int,
    x_max: int,
    y_max: int,
    terrain: TerrainType,
    skin_id: Optional[str] = None,
) -> Dict:
    payload: Dict[str, object] = {
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


def _make_feature(
    feature_id: str,
    feature_type: str,
    cell_ids: List[str],
    narrative_source: str,
    confidence: str,
) -> Dict:
    return {
        "id": f"feat_{feature_id}",
        "type": "add_feature",
        "payload": {
            "feature_id": feature_id,
            "feature_type": feature_type,
            "cell_ids": cell_ids,
            "narrative_source": narrative_source,
            "confidence": confidence,
            "activation_conditions": [],
        },
    }


def _make_secret_override(scene_id: str, cell_ids: List[str]) -> Dict:
    return {
        "id": f"override_secret_path_{scene_id}",
        "type": "add_override",
        "payload": {
            "cell_ids": cell_ids,
            "tag": "secret_path",
        },
    }


# ============================================================
# Pattern generators
# ============================================================

def _generate_beach_bands(config: WorldGridConfig) -> List[Dict]:
    """
    Default beach layout:

      rows 0-2 : deep water
      rows 3-4 : shallow water
      row 5    : shoreline
      rows 6-10: sand
      rows 11-13: grass
      rows 14-15: forest_edge (if grid tall enough)
    """
    h = config.grid_height
    w = config.grid_width

    deltas: List[Dict] = []

    # Clamp bands to actual grid height
    deep_max = min(2, h - 1)
    shallow_max = min(4, h - 1)
    shoreline_row = min(5, h - 1)
    sand_max = min(10, h - 1)
    grass_max = min(13, h - 1)
    forest_max = min(15, h - 1)

    if h > 0:
        # Deep water band: rows 0-2
        if deep_max >= 0:
            deltas.append(
                _make_region(0, 0, w - 1, deep_max, TerrainType.DEEP_WATER)
            )
        # Shallow water band: rows 3-4
        if shallow_max >= 3 and h > 3:
            deltas.append(
                _make_region(0, 3, w - 1, shallow_max, TerrainType.SHALLOW_WATER)
            )
        # Shoreline: row 5
        if shoreline_row < h:
            deltas.append(
                _make_region(0, shoreline_row, w - 1, shoreline_row, TerrainType.SHORELINE)
            )
        # Sand: rows 6-10
        if sand_max >= 6 and h > 6:
            deltas.append(
                _make_region(0, 6, w - 1, sand_max, TerrainType.SAND)
            )
        # Grass: rows 11-13
        if grass_max >= 11 and h > 11:
            deltas.append(
                _make_region(0, 11, w - 1, grass_max, TerrainType.GRASS)
            )
        # Forest edge: rows 14-15
        if forest_max >= 14 and h > 14:
            deltas.append(
                _make_region(0, 14, w - 1, forest_max, TerrainType.FOREST_EDGE)
            )

    return deltas


def _generate_pier_feature(config: WorldGridConfig) -> List[Dict]:
    """
    Simple pier_main feature:

      - vertical pier starting from shoreline (row 5) out into water
      - uses columns near center (w//2, w//2 + 1)
    """
    w = config.grid_width
    h = config.grid_height
    deltas: List[Dict] = []

    if h < 6:
        return deltas  # not enough vertical space

    col_a = max(0, w // 2)
    col_b = min(w - 1, col_a + 1)

    # Choose rows 3-8 for pier if available
    y_start = max(3, 0)
    y_end = min(h - 1, 8)

    pier_cells: List[str] = []
    for y in range(y_start, y_end + 1):
        for x in (col_a, col_b):
            cid = make_cell_id(x, y)
            pier_cells.append(cid)

    # Fill region as PIER terrain
    deltas.append(
        _make_region(col_a, y_start, col_b, y_end, TerrainType.PIER)
    )

    # Add feature (no immediate assign_feature; kernel tags cells)
    feat_id = "pier_main"
    feat = _make_feature(
        feature_id=feat_id,
        feature_type="pier",
        cell_ids=pier_cells,
        narrative_source="scene_shell_builder:auto_pier",
        confidence="inferred_high",
    )
    deltas.append(feat)

    return deltas


def _generate_construction_site(config: WorldGridConfig) -> List[Dict]:
    """
    Construction site / pyramid zone:

      - 3x3 block inland on sand band (rows ~7-9, cols near 1/3 width)
    """
    w = config.grid_width
    h = config.grid_height
    deltas: List[Dict] = []

    if h < 10 or w < 4:
        return deltas

    x_min = max(1, w // 3)
    x_max = min(w - 2, x_min + 2)
    y_min = min(7, h - 3)
    y_max = min(9, h - 1)

    # Region as CONSTRUCTION_SITE
    deltas.append(
        _make_region(x_min, y_min, x_max, y_max, TerrainType.CONSTRUCTION_SITE)
    )

    # Feature (no immediate assign_feature)
    cells: List[str] = []
    for y in range(y_min, y_max + 1):
        for x in range(x_min, x_max + 1):
            cells.append(make_cell_id(x, y))

    feat_id = "pyramid_site_01"
    feat = _make_feature(
        feature_id=feat_id,
        feature_type="construction_zone",
        cell_ids=cells,
        narrative_source="scene_shell_builder:auto_construction",
        confidence="inferred_high",
    )
    deltas.append(feat)

    return deltas


def _generate_secret_path(config: WorldGridConfig, scene_id: str) -> List[Dict]:
    """
    Secret path:

      - use forest edge band (rows 14-15) if present
      - run a 2-cell vertical corridor at col = grid_width // 2
      - apply secret_path override
    """
    h = config.grid_height
    w = config.grid_width
    deltas: List[Dict] = []

    if h < 15:
        return deltas

    col = max(0, min(w - 1, w // 2))
    y0 = 14
    y1 = min(h - 1, 15)

    cells: List[str] = []
    for y in range(y0, y1 + 1):
        cells.append(make_cell_id(col, y))

    # Feature (no immediate assign_feature)
    feat_id = "secret_path_01"
    feat = _make_feature(
        feature_id=feat_id,
        feature_type="hidden_path",
        cell_ids=cells,
        narrative_source="scene_shell_builder:auto_secret",
        confidence="inferred_medium",
    )
    override = _make_secret_override(scene_id, cells)

    deltas.append(feat)
    deltas.append(override)

    return deltas


# ============================================================
# Public entry point
# ============================================================

def build_scene_shell(
    scene_id: str,
    chapter_text: str,
    config: WorldGridConfig,
    corpus_hints: Optional[Dict[str, str]] = None,
    world_tags: Optional[List[str]] = None,
) -> List[Dict]:
    """
    Build a list of world deltas describing a scene "shell"
    inferred from narrative.

    Args:
        scene_id: stable ID for the scene.
        chapter_text: narrative text for this scene/chapter.
        config: WorldGridConfig used for layout decisions.
        corpus_hints: optional structured hints (e.g., {"scene_type": "beach"}).
        world_tags: optional high-level tags passed from upstream
                    (e.g., ["beach", "pier", "secret"]).

    Returns:
        List[delta dict], each shaped for step_trixel_world / adapter:
          {
            "id": str,
            "type": str,          # e.g., "fill_region", "add_feature"
            "payload": {...},
          }
    """
    hints = SceneHints(
        scene_id=scene_id,
        chapter_text=chapter_text,
        corpus_hints=corpus_hints,
        world_tags=world_tags,
    )

    flags = classify_scene(hints)

    deltas: List[Dict] = []

    # Base terrain: if it's a beach-y scene, lay down canonical bands.
    if flags["is_beach"]:
        deltas.extend(_generate_beach_bands(config))

    # Pier / dock feature
    if flags["has_pier"]:
        deltas.extend(_generate_pier_feature(config))

    # Construction / pyramid zone
    if flags["has_construction"]:
        deltas.extend(_generate_construction_site(config))

    # Secret path / hidden route
    if flags["has_secret"]:
        deltas.extend(_generate_secret_path(config, scene_id))

    # Tag deltas with scene_id for provenance
    for d in deltas:
        payload = d.setdefault("payload", {})
        if "scene_id" not in payload:
            payload["scene_id"] = scene_id

    return deltas


# ============================================================
# Minimal smoke test
# ============================================================

if __name__ == "__main__":
    """
    Quick local test (no adapter):

      - Build a beach+pier+secret scene
      - Print emitted deltas
    """
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

