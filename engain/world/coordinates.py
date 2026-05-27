"""Public facade. Do not place implementation here yet. Legacy source remains in trixelcomposer/tile_address.py and terrain/world_field_nucleus.py.

3D coordinate ABI helpers:
2D terrain grid + elevation + tile address -> world_cell_3d.

This module is intentionally lightweight and side-effect free.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


Grid2D = Tuple[int, int]
WorldCell3D = Tuple[int, int, int]


@dataclass(frozen=True)
class CoordinateABI:
    """Canonical coordinate packet for terrain->world conversion."""

    grid_xy: Grid2D
    elevation: int
    tile_address: str
    world_cell_3d: WorldCell3D


def grid_elevation_to_world_cell_3d(grid_x: int, grid_y: int, elevation: int) -> WorldCell3D:
    """Convert 2D terrain grid coordinates plus elevation to a world 3D cell.

    ABI mapping (current):
    - x <- grid_x
    - y <- elevation
    - z <- grid_y
    """

    return (int(grid_x), int(elevation), int(grid_y))


def make_coordinate_abi(grid_x: int, grid_y: int, elevation: int, tile_address: str) -> CoordinateABI:
    """Build a stable CoordinateABI packet."""

    world_cell = grid_elevation_to_world_cell_3d(grid_x, grid_y, elevation)
    return CoordinateABI(
        grid_xy=(int(grid_x), int(grid_y)),
        elevation=int(elevation),
        tile_address=str(tile_address),
        world_cell_3d=world_cell,
    )
