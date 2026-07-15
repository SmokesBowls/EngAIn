"""Public facade. Do not place implementation here yet. Legacy source remains in terrain/*.py."""

from .coordinates import (
    CoordinateABI,
    grid_elevation_to_world_cell_3d,
    make_coordinate_abi,
)

__all__ = [
    "CoordinateABI",
    "grid_elevation_to_world_cell_3d",
    "make_coordinate_abi",
]
