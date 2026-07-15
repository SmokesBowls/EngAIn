"""Public facade. Do not place implementation here yet. Legacy source remains in future topology/world-field generators.

Deterministic topology birth stub:
profile -> terrain_grid + elevations + chunk metadata.
Pure Python only.
"""

from __future__ import annotations


def _build_coastal(width: int, height: int) -> tuple[list[list[str]], list[list[float]]]:
    terrain_grid: list[list[str]] = []
    elevations: list[list[float]] = []
    for y in range(height):
        t_row: list[str] = []
        e_row: list[float] = []
        for x in range(width):
            if y == 0:
                tile = "deep_water"
                elev = -1.0
            elif y == 1:
                tile = "shallow_water"
                elev = 0.0
            elif y == 2:
                tile = "shoreline"
                elev = 0.0
            elif y == 3:
                tile = "sand"
                elev = 1.0 if x in (2, 3) else 0.0
            else:
                tile = "grass"
                elev = 2.0 if (x + y) % 4 == 0 else 1.0
            t_row.append(tile)
            e_row.append(float(elev))
        terrain_grid.append(t_row)
        elevations.append(e_row)
    return terrain_grid, elevations


def _build_highland(width: int, height: int) -> tuple[list[list[str]], list[list[float]]]:
    terrain_grid: list[list[str]] = []
    elevations: list[list[float]] = []
    for y in range(height):
        t_row: list[str] = []
        e_row: list[float] = []
        for x in range(width):
            rim = x in (0, width - 1) or y in (0, height - 1)
            if rim:
                tile = "cliff"
                elev = 3.0
            elif x == width // 2 and y == height // 2:
                tile = "rock"
                elev = 4.0
            elif (x + y) % 2 == 0:
                tile = "forest_edge"
                elev = 2.0
            else:
                tile = "grass"
                elev = 1.0
            t_row.append(tile)
            e_row.append(float(elev))
        terrain_grid.append(t_row)
        elevations.append(e_row)
    return terrain_grid, elevations


def _build_cosmic(width: int, height: int) -> tuple[list[list[str]], list[list[float]]]:
    terrain_grid: list[list[str]] = []
    elevations: list[list[float]] = []
    for y in range(height):
        t_row: list[str] = []
        e_row: list[float] = []
        for x in range(width):
            if (x + y) % 5 == 0:
                tile = "deep_water"
                elev = -1.0
            elif (x * y) % 4 == 0:
                tile = "rock"
                elev = 1.0
            elif (x + y) % 3 == 0:
                tile = "cliff"
                elev = 2.0
            else:
                tile = "grass"
                elev = 0.0
            t_row.append(tile)
            e_row.append(float(elev))
        terrain_grid.append(t_row)
        elevations.append(e_row)
    return terrain_grid, elevations


def build_topology_stub(width: int = 6, height: int = 6, profile: str = "coastal") -> dict:
    if width <= 0 or height <= 0:
        raise ValueError("width and height must be > 0")

    p = str(profile).strip().lower()
    if p == "coastal":
        terrain_grid, elevations = _build_coastal(width, height)
    elif p == "highland":
        terrain_grid, elevations = _build_highland(width, height)
    elif p == "cosmic":
        terrain_grid, elevations = _build_cosmic(width, height)
    else:
        raise ValueError(f"unsupported profile: {profile}")

    return {
        "profile": p,
        "terrain_grid": terrain_grid,
        "elevations": elevations,
        "chunk_x": 0,
        "chunk_y": 0,
        "chunk_size": 48,
    }
