# scene_features_beach.py

from typing import Dict, Any, List, Tuple
import hashlib

from .trixel_world_mr import (
    WorldGridConfig,
    TerrainType,
    make_cell_id,
)
from .scene_feature_registry import register_feature

# ------------------------------------------------------------------
# Shared Helpers (used ONLY by generators in this file)
# ------------------------------------------------------------------

def _world_view(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """Normalise snapshot to always contain 'trixel_world' key."""
    return snapshot.get("trixel_world", snapshot)

def _stable_index(key: str, count: int) -> int:
    """Deterministic index derived from `key`. Guarantees same result for same scene_id."""
    if count <= 0:
        raise ValueError("count must be > 0")
    digest = hashlib.sha256(key.encode("utf-8")).digest()
    value = int.from_bytes(digest[:8], "big")
    return value % count

def _extract_cells(snapshot: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    w = _world_view(snapshot)
    return w.get("cells", {})

def _synthetic_terrain(config: WorldGridConfig, assume_beach: bool) -> Dict[str, str]:
    """Build a fallback terrain map when no snapshot exists."""
    terrain_map: Dict[str, str] = {}
    for y in range(config.grid_height):
        for x in range(config.grid_width):
            cid = make_cell_id(x, y)
            if not assume_beach:
                terrain_map[cid] = config.default_terrain
                continue
            # Standard beach bands
            if y <= 2:
                t = TerrainType.DEEP_WATER.value
            elif y <= 4:
                t = TerrainType.SHALLOW_WATER.value
            elif y == 5:
                t = TerrainType.SHORELINE.value
            elif y <= 10:
                t = TerrainType.SAND.value
            elif y <= 13:
                t = TerrainType.GRASS.value
            elif y <= 15:
                t = TerrainType.FOREST_EDGE.value
            else:
                t = config.default_terrain
            terrain_map[cid] = t
    return terrain_map

def _cell_terrain(
    x: int, y: int,
    config: WorldGridConfig,
    cells: Dict[str, Dict[str, Any]],
    synthetic: Dict[str, str]
) -> str:
    if not (0 <= x < config.grid_width and 0 <= y < config.grid_height):
        return config.default_terrain
    cid = make_cell_id(x, y)
    cell = cells.get(cid, {})
    if isinstance(cell, dict) and "terrain_type" in cell:
        return str(cell["terrain_type"])
    return synthetic.get(cid, config.default_terrain)

def _cell_is_protected(
    x: int,
    y: int,
    config: WorldGridConfig,
    cells: Dict[str, Dict[str, Any]],
) -> bool:
    """True if cell already carries meaningful protected state."""
    if not (0 <= x < config.grid_width and 0 <= y < config.grid_height):
        return True

    cid = make_cell_id(x, y)
    cell = cells.get(cid, {})

    return bool(
        cell.get("feature_ids")
        or cell.get("override_tags")
        or cell.get("socket_ids")
        or cell.get("state_flags")
    )
# ------------------------------------------------------------------
# FEATURE GENERATORS
# ------------------------------------------------------------------

def pier_main_generator(
    *,
    scene_id: str,
    config: WorldGridConfig,
    snapshot: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Places a deterministic 2×6 pier touching shoreline.
    Uses `snapshot` to avoid protected cells.
    """
    cells = _extract_cells(snapshot)
    synthetic = _synthetic_terrain(config, assume_beach=True)

    if config.grid_width < 2 or config.grid_height < 6:
        return []

    candidates: List[Tuple[float, List[str]]] = []

    for shoreline_y in range(config.grid_height):
        for col_a in range(config.grid_width - 1):
            cols = (col_a, col_a + 1)
            y_start = shoreline_y - 5
            if y_start < 0:
                continue

            footprint = [(x, y) for y in range(y_start, shoreline_y + 1) for x in cols]
            # Skip if any cell protected/blocked
            if any(_cell_is_protected(x, y, config, cells) for x, y in footprint):
                continue

            # Southern edge MUST be shoreline
            shore_ok = all(
                _cell_terrain(x, shoreline_y, config, cells, synthetic) == TerrainType.SHORELINE.value
                for x in cols
            )
            if not shore_ok:
                continue

            # Northern part must be water
            water_ok = all(
                _cell_terrain(x, y, config, cells, synthetic) in
                (TerrainType.SHALLOW_WATER.value, TerrainType.DEEP_WATER.value)
                for x, y in [(x, y) for y in range(y_start, shoreline_y) for x in cols]
            )
            if not water_ok:
                continue

            # Score (deterministic jitter via scene_id)
            interior_bonus = 1.0 if 0 < col_a < (config.grid_width - 2) else 0.0
            shallow_count = sum(
                1 for y in range(y_start, shoreline_y)
                for x in cols
                if _cell_terrain(x, y, config, cells, synthetic) == TerrainType.SHALLOW_WATER.value
            )
            score = (shallow_count * 20.0) + interior_bonus
            jitter = (_stable_index(f"{scene_id}_pier_{col_a}_{shoreline_y}", 10000)) / 10000.0
            score += jitter

            cell_ids = [make_cell_id(x, y) for x, y in footprint]
            candidates.append((score, cell_ids))

    if not candidates:
        # Fallback: centre‑aligned pier
        col_a = max(0, (config.grid_width // 2) - 1)
        col_b = min(config.grid_width - 1, col_a + 1)
        shoreline_y = min(config.grid_height - 1, 5)
        y_start = max(0, shoreline_y - 5)
        fallback_cells = [
            make_cell_id(x, y)
            for y in range(y_start, shoreline_y + 1)
            for x in (col_a, col_b)
        ]
        candidates.append((0.0, fallback_cells))

    candidates.sort(key=lambda item: (-item[0], item[1]))
    pier_cells = candidates[0][1]

    # Build deltas
    xs = [int(cid.split('_')[1]) for cid in pier_cells]
    ys = [int(cid.split('_')[3]) for cid in pier_cells]
    deltas: List[Dict[str, Any]] = [{
        "id": f"fill_pier_{scene_id}",
        "type": "fill_region",
        "payload": {
            "x_min": min(xs),
            "y_min": min(ys),
            "x_max": max(xs),
            "y_max": max(ys),
            "terrain_type": TerrainType.PIER.value,
        }
    }, {
        "id": f"feat_pier_main_{scene_id}",
        "type": "add_feature",
        "payload": {
            "feature_id": "pier_main",
            "feature_type": "pier",
            "cell_ids": pier_cells,
            "narrative_source": "scene_features_beach:pier_main_generator",
            "confidence": "inferred_high",
            "activation_conditions": [],
        }
    }]
    return deltas


def secret_path_01_generator(
    *,
    scene_id: str,
    config: WorldGridConfig,
    snapshot: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Places a 2‑cell secret path on forest_edge.
    Deterministic per `scene_id`.
    """
    cells = _extract_cells(snapshot)
    synthetic = _synthetic_terrain(config, assume_beach=True)

    if config.grid_height < 15:
        return []

    y_start, y_end = 14, min(config.grid_height - 1, 15)
    candidates: List[Tuple[float, List[str]]] = []

    for col in range(config.grid_width):
        coords = [(col, y) for y in range(y_start, y_end + 1)]
        # Skip protected cells
        if any(_cell_is_protected(x, y, config, cells) for x, y in coords):
            continue
        # Must be FOREST_EDGE terrain
        if not all(
            _cell_terrain(x, y, config, cells, synthetic) == TerrainType.FOREST_EDGE.value
            for x, y in coords
        ):
            continue

        # Score: prefer interior + contact with grass
        grass_contacts = 0
        open_neighbors = 0
        for x, y in coords:
            for nx, ny in ((x-1, y), (x+1, y), (x, y-1), (x, y+1)):
                if 0 <= nx < config.grid_width and 0 <= ny < config.grid_height:
                    if not _cell_is_protected(nx, ny, config, cells):
                        open_neighbors += 1
                    if _cell_terrain(nx, ny, config, cells, synthetic) == TerrainType.GRASS.value:
                        grass_contacts += 1

        if open_neighbors == 0:
            continue

        interior_bonus = 1.0 if 0 < col < (config.grid_width - 1) else 0.0
        jitter = (_stable_index(f"{scene_id}_secret_{col}", 10000)) / 10000.0
        score = (grass_contacts * 100.0) + (open_neighbors * 5.0) + interior_bonus + jitter
        cell_ids = [make_cell_id(col, y) for y in range(y_start, y_end + 1)]
        candidates.append((score, cell_ids))

    if not candidates:
        # Fallback: centre column
        col = max(0, min(config.grid_width - 1, config.grid_width // 2))
        fallback_cells = [make_cell_id(col, y) for y in range(y_start, y_end + 1)]
        candidates.append((0.0, fallback_cells))

    candidates.sort(key=lambda item: (-item[0], item[1]))
    secret_cells = candidates[0][1]

    deltas: List[Dict[str, Any]] = [{
        "id": f"feat_secret_path_01_{scene_id}",
        "type": "add_feature",
        "payload": {
            "feature_id": "secret_path_01",
            "feature_type": "hidden_path",
            "cell_ids": secret_cells,
            "narrative_source": "scene_features_beach:secret_path_01_generator",
            "confidence": "inferred_medium",
            "activation_conditions": [],
        }
    }, {
        "id": f"override_secret_{scene_id}",
        "type": "add_override",
        "payload": {
            "cell_ids": secret_cells,
            "tag": "secret_path",
        }
    }]
    return deltas


def pyramid_site_01_generator(
    *,
    scene_id: str,
    config: WorldGridConfig,
    snapshot: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Places a deterministic 3×3 pyramid construction site on inland sand.
    """
    cells = _extract_cells(snapshot)
    synthetic = _synthetic_terrain(config, assume_beach=True)

    if config.grid_width < 3 or config.grid_height < 3:
        return []

    # Find shoreline row
    shoreline_rows = set()
    for y in range(config.grid_height):
        for x in range(config.grid_width):
            if _cell_terrain(x, y, config, cells, synthetic) == TerrainType.SHORELINE.value:
                shoreline_rows.add(y)
    if not shoreline_rows:
        return []
    shore_max = max(shoreline_rows)

    # Inland sand rows = sand rows > shore_max + 1
    inland_rows = [
        r for r in range(config.grid_height)
        if _cell_terrain(0, r, config, cells, synthetic) == TerrainType.SAND.value
        and r > (shore_max + 1)
    ]
    if not inland_rows:
        return []

    candidates: List[Tuple[float, List[str]]] = []

    for y0 in inland_rows:
        y2 = y0 + 2
        if y2 >= config.grid_height:
            continue
        for x0 in range(0, config.grid_width - 2):
            x2 = x0 + 2
            footprint = [(x, y) for y in range(y0, y2 + 1) for x in range(x0, x2 + 1)]

            # Skip protected cells
            if any(_cell_is_protected(x, y, config, cells) for x, y in footprint):
                continue
            # Must be pure SAND
            if not all(
                _cell_terrain(x, y, config, cells, synthetic) == TerrainType.SAND.value
                for x, y in footprint
            ):
                continue

            shore_dist = y0 - shore_max
            interior_margin = min(x0, config.grid_width - 1 - x2)
            center_bias = -abs((x0 + 1) - (config.grid_width / 2.0))
            jitter = (_stable_index(f"{scene_id}_pyramid_{x0}_{y0}", 10000)) / 10000.0
            score = (shore_dist * 100.0) + (interior_margin * 10.0) + center_bias + jitter
            cell_ids = [make_cell_id(x, y) for x, y in footprint]
            candidates.append((score, cell_ids))

    if not candidates:
        return []

    candidates.sort(key=lambda item: (-item[0], item[1]))
    site_cells = candidates[0][1]

    xs = [int(cid.split('_')[1]) for cid in site_cells]
    ys = [int(cid.split('_')[3]) for cid in site_cells]
    deltas: List[Dict[str, Any]] = [{
        "id": f"fill_construction_{scene_id}",
        "type": "fill_region",
        "payload": {
            "x_min": min(xs),
            "y_min": min(ys),
            "x_max": max(xs),
            "y_max": max(ys),
            "terrain_type": TerrainType.CONSTRUCTION_SITE.value,
        }
    }, {
        "id": f"feat_pyramid_site_01_{scene_id}",
        "type": "add_feature",
        "payload": {
            "feature_id": "pyramid_site_01",
            "feature_type": "construction_zone",
            "cell_ids": site_cells,
            "narrative_source": "scene_features_beach:pyramid_site_01_generator",
            "confidence": "inferred_high",
            "activation_conditions": [],
        }
    }]
    return deltas


def register_beach_features() -> None:
    """Register all beach‑related feature generators."""
    register_feature("pier_main", pier_main_generator)
    register_feature("secret_path_01", secret_path_01_generator)
    register_feature("pyramid_site_01", pyramid_site_01_generator)
