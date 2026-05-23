# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/terrain/terrain_thresholds.py
# Converts WorldField float values (0.0–1.0) to terrain type strings.
# Supports biome/context-specific threshold profiles while keeping the old API stable.

from __future__ import annotations

from typing import Final


TERRAIN_PROFILES: Final[dict[str, list[tuple[float, float, str]]]] = {
    "coastal_beach": [
        (0.00, 0.10, "deep_water"),
        (0.10, 0.22, "shallow_water"),
        (0.22, 0.30, "shoreline"),
        (0.30, 0.42, "sand"),
        (0.42, 0.62, "grass"),
        (0.62, 0.78, "forest_edge"),
        (0.78, 0.90, "rock"),
        (0.90, 1.01, "cliff"),
    ],
    "default_wasteland": [
        (0.00, 0.18, "ash_plain"),
        (0.18, 0.38, "coarse_sediment_dark"),
        (0.38, 0.68, "fog_waste"),
        (0.68, 0.86, "rock"),
        (0.86, 1.01, "cliff"),
    ],
}

DEFAULT_PROFILE_ID: Final[str] = "coastal_beach"

VALID_TERRAIN_TYPES: Final[frozenset[str]] = frozenset(
    terrain
    for bands in TERRAIN_PROFILES.values()
    for _, _, terrain in bands
) | {"pier"}


def value_to_terrain(value: float, profile_id: str = DEFAULT_PROFILE_ID) -> str:
    """Map a single float value from 0.0–1.0 to a terrain type string."""
    v = max(0.0, min(1.0, float(value)))
    bands = TERRAIN_PROFILES.get(profile_id, TERRAIN_PROFILES[DEFAULT_PROFILE_ID])

    for lo, hi, terrain in bands:
        if lo <= v < hi:
            return terrain

    return bands[-1][2]


def field_chunk_to_terrain_row(
    chunk_data: list[float],
    chunk_size: int,
    profile_id: str = DEFAULT_PROFILE_ID,
) -> list[list[str]]:
    """Convert a flat chunk data list to a 2D terrain string grid."""
    expected_len = chunk_size * chunk_size
    if len(chunk_data) < expected_len:
        raise ValueError(
            f"chunk_data too short: expected {expected_len}, got {len(chunk_data)}"
        )

    grid: list[list[str]] = []
    for y in range(chunk_size):
        row: list[str] = []
        for x in range(chunk_size):
            idx = y * chunk_size + x
            row.append(value_to_terrain(chunk_data[idx], profile_id))
        grid.append(row)

    return grid


def dirty_chunks_to_terrain_grid(
    dirty_chunks: list[dict],
    world_width_cells: int,
    world_height_cells: int,
    default_terrain: str = "grass",
    profile_id: str = DEFAULT_PROFILE_ID,
) -> list[list[str]]:
    """
    Assemble a full terrain_grid from dirty chunks.

    Each chunk dict must contain:
    - chunk_key: tuple[int, int]
    - data: list[float]
    - size: int
    """
    if default_terrain not in VALID_TERRAIN_TYPES:
        raise ValueError(f"Invalid default terrain: {default_terrain}")

    grid = [[default_terrain] * world_width_cells for _ in range(world_height_cells)]

    for chunk in dirty_chunks:
        cx, cy = chunk["chunk_key"]
        size: int = int(chunk["size"])
        data: list[float] = chunk["data"]

        expected_len = size * size
        if len(data) < expected_len:
            raise ValueError(
                f"Chunk {chunk['chunk_key']} data too short: "
                f"expected {expected_len}, got {len(data)}"
            )

        world_origin_x = cx * size
        world_origin_y = cy * size

        for local_y in range(size):
            world_y = world_origin_y + local_y
            if world_y < 0 or world_y >= world_height_cells:
                continue

            for local_x in range(size):
                world_x = world_origin_x + local_x
                if world_x < 0 or world_x >= world_width_cells:
                    continue

                idx = local_y * size + local_x
                grid[world_y][world_x] = value_to_terrain(data[idx], profile_id)

    return grid


if __name__ == "__main__":
    test_values = [0.0, 0.05, 0.15, 0.25, 0.35, 0.50, 0.70, 0.85, 0.95, 1.0]

    for profile in TERRAIN_PROFILES:
        print(f"Threshold smoke test: {profile}")
        for v in test_values:
            print(f"  {v:.2f} → {value_to_terrain(v, profile)}")
