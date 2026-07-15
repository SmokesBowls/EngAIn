"""Public facade. Do not place implementation here yet. Legacy source remains in terrain/* runtime adapters.

Isolated world-field-style payload normalization for PlacementPacket pipeline.
Pure Python only.
"""

from __future__ import annotations


def _validate_rectangular_grid(terrain_grid: list[list[str]]) -> tuple[int, int]:
    if not isinstance(terrain_grid, list) or not terrain_grid:
        raise ValueError("terrain_grid must be a non-empty list of rows")
    if not all(isinstance(row, list) for row in terrain_grid):
        raise ValueError("terrain_grid rows must be lists")

    width = len(terrain_grid[0])
    if width == 0:
        raise ValueError("terrain_grid rows must be non-empty")

    for i, row in enumerate(terrain_grid):
        if len(row) != width:
            raise ValueError(f"terrain_grid must be rectangular; row {i} width mismatch")

    return len(terrain_grid), width


def _validate_elevations(elevations: list[list[float]], height: int, width: int) -> None:
    if not isinstance(elevations, list) or len(elevations) != height:
        raise ValueError("elevations must have same row count as terrain_grid")
    for y, row in enumerate(elevations):
        if not isinstance(row, list) or len(row) != width:
            raise ValueError(f"elevations shape mismatch at row {y}")


def _normalize_direct(payload: dict) -> dict:
    terrain_grid = payload.get("terrain_grid")
    elevations = payload.get("elevations")
    if not isinstance(terrain_grid, list):
        raise ValueError("direct payload requires terrain_grid list")
    if elevations is None:
        raise ValueError("direct payload requires elevations")

    height, width = _validate_rectangular_grid(terrain_grid)
    _validate_elevations(elevations, height, width)

    return {
        "terrain_grid": terrain_grid,
        "elevations": elevations,
        "chunk_x": int(payload.get("chunk_x", 0)),
        "chunk_y": int(payload.get("chunk_y", 0)),
        "chunk_size": int(payload.get("chunk_size", 48)),
    }


def _normalize_single_chunk(payload: dict) -> dict:
    chunks = payload.get("chunks")
    if not isinstance(chunks, list) or not chunks:
        raise ValueError("chunk payload requires non-empty chunks list")
    if len(chunks) != 1:
        raise ValueError("multiple chunks not supported in isolated adapter")

    c = chunks[0]
    if not isinstance(c, dict):
        raise ValueError("chunk entry must be an object")

    terrain_grid = c.get("terrain_grid")
    elevations = c.get("elevations")
    if not isinstance(terrain_grid, list):
        raise ValueError("chunk payload requires terrain_grid list")
    if elevations is None:
        raise ValueError("chunk payload requires elevations")

    height, width = _validate_rectangular_grid(terrain_grid)
    _validate_elevations(elevations, height, width)

    key = c.get("chunk_key", [payload.get("chunk_x", 0), payload.get("chunk_y", 0)])
    if not isinstance(key, (list, tuple)) or len(key) != 2:
        raise ValueError("chunk_key must be [x, y]")

    return {
        "terrain_grid": terrain_grid,
        "elevations": elevations,
        "chunk_x": int(key[0]),
        "chunk_y": int(key[1]),
        "chunk_size": int(c.get("chunk_size", payload.get("chunk_size", 48))),
    }


def normalize_world_field_payload(payload: dict) -> dict:
    """Normalize world-field-style payload to placement-emitter input contract."""
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")

    if "terrain_grid" in payload:
        return _normalize_direct(payload)
    if "chunks" in payload:
        return _normalize_single_chunk(payload)

    raise ValueError("payload must contain either terrain_grid or chunks")
