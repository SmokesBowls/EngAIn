"""Public facade. Do not place implementation here yet. Legacy source remains in future runtime adapters.

Deterministic terrain-grid -> PlacementPacket emitter.
Pure Python only.
"""

from __future__ import annotations

from engain.world.coordinates import make_coordinate_abi
from engain.world.chunks import make_chunk_coordinate
from engain.render.transforms import build_placement_packet


def _validate_rectangular_grid(terrain_grid: list[list[str]]) -> tuple[int, int]:
    if not isinstance(terrain_grid, list) or not terrain_grid:
        raise ValueError("terrain_grid must be a non-empty list of rows")

    if not all(isinstance(row, list) for row in terrain_grid):
        raise ValueError("terrain_grid rows must all be lists")

    width = len(terrain_grid[0])
    if width == 0:
        raise ValueError("terrain_grid rows must be non-empty")

    for idx, row in enumerate(terrain_grid):
        if len(row) != width:
            raise ValueError(f"terrain_grid must be rectangular; row {idx} has width {len(row)} expected {width}")

    return len(terrain_grid), width


def _validate_elevations_shape(elevations: list[list[float]], height: int, width: int) -> None:
    if not isinstance(elevations, list) or len(elevations) != height:
        raise ValueError("elevations must be a list with same row count as terrain_grid")
    for y, row in enumerate(elevations):
        if not isinstance(row, list) or len(row) != width:
            raise ValueError(f"elevations shape mismatch at row {y}; expected width {width}")


def emit_placement_packets_from_grid(
    terrain_grid,
    elevations=None,
    chunk_x=0,
    chunk_y=0,
    chunk_size=48,
    tile_scale=1.0,
):
    """Convert terrain grid truth into deterministic PlacementPacket stream."""

    height, width = _validate_rectangular_grid(terrain_grid)

    if elevations is not None:
        _validate_elevations_shape(elevations, height, width)

    packets = []
    for grid_y in range(height):
        for grid_x in range(width):
            tile_id = str(terrain_grid[grid_y][grid_x])
            elev = float(elevations[grid_y][grid_x]) if elevations is not None else 0.0

            coordinate = make_coordinate_abi(
                grid_x=grid_x,
                grid_y=grid_y,
                elevation=int(elev),
                tile_address=f"d{grid_x}.u{elev}.f{grid_y}",
            )
            chunk = make_chunk_coordinate(
                local_x=grid_x,
                local_z=grid_y,
                chunk_x=chunk_x,
                chunk_y=chunk_y,
                chunk_size=chunk_size,
            )

            packet = build_placement_packet(
                tile_id=tile_id,
                coordinate_abi=coordinate,
                chunk_coordinate=chunk,
                visible_face="top",
                rotation=(0.0, 0.0, 0.0),
                scale=(float(tile_scale), float(tile_scale), float(tile_scale)),
            )
            packets.append(packet)

    # deterministic ordering contract
    packets.sort(
        key=lambda p: (
            int(p.chunk["y"]),
            int(p.chunk["x"]),
            int(p.grid["y"]),
            int(p.grid["x"]),
            str(p.tile_id),
        )
    )
    return packets
