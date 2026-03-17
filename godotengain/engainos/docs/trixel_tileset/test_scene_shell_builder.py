#!/usr/bin/env python3
"""
test_scene_shell_builder.py — integration test for scene_shell_builder.

Scenario:
  One narrative that implies:
    - beach terrain bands
    - a pier
    - a construction/pyramid site
    - a secret path through the forest edge

We verify, after applying the builder's deltas via the pure kernel:

  - deep/shallow/shore/sand/grass/forest bands exist as expected
  - pier_main feature exists
  - pyramid_site_01 feature exists
  - secret_path_01 feature exists
  - secret-path forest cells are effectively walkable
  - a normal forest-edge cell remains blocked
"""

import json
from typing import Dict, List

from scene_shell_builder import build_scene_shell
from trixel_world_mr import (
    WorldGridConfig,
    step_trixel_world,
    make_cell_id,
    resolve_cell_walkability,
    create_empty_grid,
)


def _index_world(world: Dict) -> Dict:
    """Convenience accessors for the world snapshot."""
    tw = world["trixel_world"]
    return {
        "cells": tw["cells"],
        "features": tw["features"],
        "skin_table": tw["skin_table"],
        "tick": tw["tick"],
    }


def _terrain_at(cells: Dict[str, Dict], x: int, y: int) -> str:
    cid = make_cell_id(x, y)
    return cells[cid]["terrain_type"]


def test_scene_shell_beach_pier_construction_secret() -> None:
    # --- Arrange: config + narrative ---
    config = WorldGridConfig(grid_width=16, grid_height=16, tile_size=16)
    scene_id = "scene_beach_001"
    text = (
        "They were building pyramids on the sand near a tree ridge. "
        "To the north, the sea lapped at a long wooden pier. "
        "Locals whispered of a secret path through the forest edge."
    )

    deltas = build_scene_shell(
        scene_id=scene_id,
        chapter_text=text,
        config=config,
        corpus_hints={"scene_type": "beach"},
        world_tags=["beach", "pier", "secret"],
    )

    # Initial empty world snapshot in kernel format
    empty_world = {
        "trixel_world": {
            "cells": create_empty_grid(config),
            "features": {},
            "skin_table": {},
            "tick": 0.0,
        }
    }

    # --- Act: apply builder deltas via pure kernel ---
    snapshot_out, accepted_ids, alerts = step_trixel_world(
        snapshot_in=empty_world,
        deltas=deltas,
        config=config,
        delta_time=0.0,
    )

    idx = _index_world(snapshot_out)
    cells = idx["cells"]
    features = idx["features"]

    # Optional debug dump if you want to inspect:
    # print(json.dumps(snapshot_out, indent=2))

    # --- Assert: terrain bands ---

    # Check at least one cell in each band row has the expected terrain.
    # We sample column 0 for simplicity.
    assert _terrain_at(cells, 0, 0) == "deep_water"
    assert _terrain_at(cells, 0, 3) == "shallow_water"
    assert _terrain_at(cells, 0, 5) == "shoreline"
    assert _terrain_at(cells, 0, 7) == "sand"
    assert _terrain_at(cells, 0, 12) == "grass"
    assert _terrain_at(cells, 0, 14) == "forest_edge"

    # --- Assert: feature existence ---

    assert "pier_main" in features, "pier_main feature should exist"
    assert "pyramid_site_01" in features, "pyramid_site_01 feature should exist"
    assert "secret_path_01" in features, "secret_path_01 feature should exist"

    # --- Assert: secret-path walkability semantics ---

    # Secret path cells: col = grid_width // 2, rows 14–15
    col_secret = config.grid_width // 2
    secret_ids: List[str] = []
    for y in (14, 15):
        cid = make_cell_id(col_secret, y)
        secret_ids.append(cid)

    # All secret cells should resolve as walkable
    for cid in secret_ids:
        cell = cells[cid]
        effective = resolve_cell_walkability(cell)
        assert effective is True, f"Secret path cell {cid} should be walkable"

    # A normal forest-edge cell away from the secret should be blocked.
    # Choose col=1, row=14 which is in the forest_edge band but not the secret column.
    normal_forest_id = make_cell_id(1, 14)
    normal_cell = cells[normal_forest_id]
    effective_normal = resolve_cell_walkability(normal_cell)
    assert effective_normal is False, "Normal forest-edge cell should be blocked"

    # --- Assert: no kernel errors ---
    error_alerts = [a for a in alerts if a.get("level") == "ERROR"]
    assert not error_alerts, f"Kernel reported errors: {error_alerts}"


if __name__ == "__main__":
    # Run the test directly for quick manual verification.
    test_scene_shell_beach_pier_construction_secret()
    print("test_scene_shell_beach_pier_construction_secret: OK")

