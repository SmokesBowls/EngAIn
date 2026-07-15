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
    """Canonical coordinate packet for terrain->world conversion.

    Attributes:
        grid_xy: 2D terrain grid coordinate tuple.
        elevation: Terrain elevation.
        view_address_hint: Observer-relative view address hint (non-authoritative).
        world_cell_3d: Derived 3D world cell coordinates.
    """

    grid_xy: Grid2D
    elevation: int
    view_address_hint: str  # Non-authoritative. Derived from ViewAddressABI (§10.5).
    world_cell_3d: WorldCell3D

    @property
    def tile_address(self) -> str:
        """Deprecated: Use view_address_hint instead."""
        return self.view_address_hint


def grid_elevation_to_world_cell_3d(grid_x: int, grid_y: int, elevation: int) -> WorldCell3D:
    """Convert 2D terrain grid coordinates plus elevation to a world 3D cell.

    ABI mapping (current):
    - x <- grid_x
    - y <- elevation
    - z <- grid_y

    # debug_trace.coordinate_derivation: "grid_y_to_world_z"
    """

    return (int(grid_x), int(elevation), int(grid_y))


def make_coordinate_abi(
    grid_x: int,
    grid_y: int,
    elevation: int,
    tile_address: str = "",
    view_address_hint: str = "",
) -> CoordinateABI:
    """Build a stable CoordinateABI packet."""

    addr = view_address_hint if view_address_hint else tile_address
    world_cell = grid_elevation_to_world_cell_3d(grid_x, grid_y, elevation)
    return CoordinateABI(
        grid_xy=(int(grid_x), int(grid_y)),
        elevation=int(elevation),
        view_address_hint=str(addr),
        world_cell_3d=world_cell,
    )


def validate_coordinate_record(obj: dict) -> list[str]:
    """Validate a CoordinateRecord envelope against COORDINATE_ABI_v1.md specifications.

    Returns a list of validation failure descriptions, or an empty list if compliant.
    """
    errors = []
    if not isinstance(obj, dict):
        return ["Input must be a dictionary"]

    # 1. Required top-level keys and exact value matches
    required_top_level = {
        "schema_version": "trixel_coordinate_abi.v1",
        "authority_level": "coordinate_truth",
        "authoritative": True,
        "artifact_kind": "coordinate_record",
    }
    for key, expected in required_top_level.items():
        if key not in obj:
            errors.append(f"Missing required top-level key: '{key}'")
        elif obj[key] != expected:
            errors.append(f"Invalid value for '{key}': expected {expected!r}, got {obj[key]!r}")

    # 2. Position keys validation
    if "position" not in obj:
        errors.append("Missing required 'position' payload dict")
    elif not isinstance(obj["position"], dict):
        errors.append("'position' must be a dictionary")
    else:
        required_pos = {"world_x", "world_y", "world_z"}
        missing_pos = required_pos - obj["position"].keys()
        if missing_pos:
            errors.append(f"Missing position fields: {sorted(list(missing_pos))}")

    # 3. Chunk keys validation
    if "chunk" not in obj:
        errors.append("Missing required 'chunk' payload dict")
    elif not isinstance(obj["chunk"], dict):
        errors.append("'chunk' must be a dictionary")
    else:
        required_chunk = {"chunk_x", "chunk_y", "chunk_z", "chunk_size", "local_x", "local_y", "local_z"}
        missing_chunk = required_chunk - obj["chunk"].keys()
        if missing_chunk:
            errors.append(f"Missing chunk fields: {sorted(list(missing_chunk))}")

    return errors

