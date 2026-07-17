# grid_facts_emitter.py
# Emits the worldfield_grid_facts packet — the "Grid facts" block of
# trixel32d_surface_request (see docs/contracts/TRIXEL32D_REQUEST_ASSEMBLY_AND_CONSUMER_v1.md).
#
# Joins the two truths this lane holds separately:
#   - WorldField chunks: per-cell elevation floats (0.0–1.0), the field authority
#   - TrixelWorldFieldAdapter grid: per-cell semantic terrain strings
# into one complete record per cell:
#   {"field_x": 12, "field_y": 7, "elevation": 0.5, "terrain": "tundra", "recipe": "tundra.frozen_plain"}
#
# Doctrine:
#   - DENSE coverage: exactly one record per grid coordinate, always.
#   - No silent defaults for semantics: a terrain name with no declared recipe
#     mapping emits recipe=null and is listed in "unmapped_terrains" so EngAInOS
#     request assembly can reject or decide — never guess.
#   - Unsculpted cells read elevation 0.0 (the field's genuine resting value,
#     not a fallback).
#
# WorldField is Trixel's input doorway without being part of Trixel:
#   tier2/worldfield → worldfield_grid_facts → EngAInOS request assembly
#     → trixel32d_surface_request → Trixel 3.2d

from __future__ import annotations

from typing import Any


PACKET_TYPE = "worldfield_grid_facts"
PACKET_VERSION = "worldfield_grid_facts.v1"


# ---------------------------------------------------------------------------
# Terrain-name → Trixel recipe identity reconciliation (v1 PROPOSAL)
#
# Right side must match trixel3.2d recipes/terrain/*.json identities.
# This table is EngAIn's proposal; trixel3.2d concurrence is pending — entries
# may be re-pointed, but the MECHANISM (explicit table, null for unmapped)
# is the contract. Deliberately unmapped names stay unmapped until a recipe
# exists for them; they are surfaced, not guessed.
# ---------------------------------------------------------------------------

TERRAIN_TO_RECIPE: dict[str, str] = {
    # coastal_beach profile
    "deep_water":    "ocean.deep_current",
    "shallow_water": "beach.tidal_flats",
    "shoreline":     "beach.tidal_flats",
    "sand":          "beach.tidal_flats",
    "grass":         "default.generic",
    "forest_edge":   "forest.dense_canopy",
    "rock":          "mountain.rocky_ridge",
    "cliff":         "mountain.rocky_ridge",
    # volcanic / wasteland profiles
    "ash_plain":             "volcano.branching_lava",
    "coarse_sediment_dark":  "volcano.branching_lava",
    "basalt":                "volcano.branching_lava",
    # classify_biome() vocabulary
    "snow":     "tundra.frozen_plain",
    "tundra":   "tundra.frozen_plain",
    "mountain": "mountain.rocky_ridge",
    "desert":   "desert.arid_flats",
    "forest":   "forest.dense_canopy",
    "marsh":    "swamp.murky_bog",
    # Deliberately unmapped (no honest recipe exists yet — will emit null):
    #   pier, fog_waste, ash_plain_dark, cracked_soil, scree
}


def elevation_at(world_field, field_x: int, field_y: int) -> float:
    """Read the raw elevation float for a world cell (0.0 if never sculpted)."""
    chunk = world_field.get_chunk_at(field_x, field_y)
    if chunk is None:
        return 0.0
    lx, ly = world_field.get_local_coords(field_x, field_y)
    if 0 <= lx < chunk.size and 0 <= ly < chunk.size:
        return float(chunk.get(lx, ly))
    return 0.0


def emit_grid_facts(world_field, adapter) -> dict[str, Any]:
    """
    Produce the complete worldfield_grid_facts packet from a wired
    (world_field, adapter) pair — see make_wired_field().

    Guarantees DENSE coverage: len(cells) == width × height, every
    coordinate exactly once, row-major (field_y outer, field_x inner —
    the same ordering contract trixel32d uses).
    """
    width = adapter.grid_width
    height = adapter.grid_height

    cells: list[dict[str, Any]] = []
    unmapped: set[str] = set()

    for field_y in range(height):
        for field_x in range(width):
            terrain = adapter.get_terrain_at(field_x, field_y)
            recipe = TERRAIN_TO_RECIPE.get(terrain)
            if recipe is None:
                unmapped.add(terrain)
            cells.append({
                "field_x": field_x,
                "field_y": field_y,
                "elevation": elevation_at(world_field, field_x, field_y),
                "terrain": terrain,
                "recipe": recipe,
            })

    return {
        "packet_type": PACKET_TYPE,
        "version": PACKET_VERSION,
        "width": width,
        "height": height,
        "field_coverage": "DENSE",
        "profile": adapter.profile_id,
        "cells": cells,
        "unmapped_terrains": sorted(unmapped),
        "fully_mapped": not unmapped,
    }


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json

    try:
        from .trixel_world_adapter import make_wired_field
    except ImportError:
        from trixel_world_adapter import make_wired_field

    field, bridge, adapter = make_wired_field(16, 16, profile_id="coastal_beach")
    dirty = bridge.handle_edit(8.0, 8.0, "add", radius=6, strength=0.6)
    adapter.apply_dirty_chunks(dirty)

    packet = emit_grid_facts(field, adapter)

    expected = packet["width"] * packet["height"]
    coords = {(c["field_x"], c["field_y"]) for c in packet["cells"]}
    checks = {
        "dense_complete": len(packet["cells"]) == expected and len(coords) == expected,
        "elevation_preserved": any(c["elevation"] > 0.0 for c in packet["cells"]),
        "elevation_in_range": all(0.0 <= c["elevation"] <= 1.0 for c in packet["cells"]),
        "terrain_present": all(c["terrain"] for c in packet["cells"]),
        "unmapped_surfaced": all(
            (c["recipe"] is None) == (c["terrain"] in packet["unmapped_terrains"])
            for c in packet["cells"]
        ),
    }

    center = next(c for c in packet["cells"] if c["field_x"] == 8 and c["field_y"] == 8)
    print("sample cell:", json.dumps(center))
    print("unmapped_terrains:", packet["unmapped_terrains"], "| fully_mapped:", packet["fully_mapped"])
    for name, ok in checks.items():
        print(f"  {name}: {ok}")
    print("grid_facts_emitter:", "TRUE" if all(checks.values()) else "FALSE")
