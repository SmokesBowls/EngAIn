# terrain_thresholds.py
# Converts WorldField float values (0.0–1.0) to terrain type strings.
# These are the only strings the SemanticRenderer and TrixelRoleResolver know.
# Adjust band boundaries here to reshape how terrain distributes across the field.

TERRAIN_BANDS = [
    (0.00, 0.10, "deep_water"),
    (0.10, 0.22, "shallow_water"),
    (0.22, 0.30, "shoreline"),
    (0.30, 0.42, "sand"),
    (0.42, 0.62, "grass"),
    (0.62, 0.78, "forest_edge"),
    (0.78, 0.90, "rock"),
    (0.90, 1.01, "cliff"),
]

# Canonical set — must match what SemanticRenderer/TrixelAtlas know.
VALID_TERRAIN_TYPES = frozenset(
    t for _, _, t in TERRAIN_BANDS
) | {"pier"}


def value_to_terrain(value: float) -> str:
    """Map a single float (0.0–1.0) to a terrain type string."""
    v = max(0.0, min(1.0, value))
    for lo, hi, terrain in TERRAIN_BANDS:
        if lo <= v < hi:
            return terrain
    return "cliff"


def field_chunk_to_terrain_row(chunk_data: list[float], chunk_size: int) -> list[list[str]]:
    """Convert a flat chunk data list to a 2D terrain string grid."""
    grid = []
    for y in range(chunk_size):
        row = []
        for x in range(chunk_size):
            idx = y * chunk_size + x
            row.append(value_to_terrain(chunk_data[idx]))
        grid.append(row)
    return grid


def dirty_chunks_to_terrain_grid(
    dirty_chunks: list[dict],
    world_width_cells: int,
    world_height_cells: int,
    default_terrain: str = "grass",
) -> list[list[str]]:
    """
    Assemble a full terrain_grid from a list of dirty chunk dicts.
    Each dict has keys: chunk_key (tuple), data (list[float]), size (int).

    Only cells covered by dirty chunks are updated.
    Everything else stays as default_terrain.

    Returns a 2D Array[Array[String]] matching what SemanticRenderer expects.
    """
    # Initialise with default
    grid = [[default_terrain] * world_width_cells for _ in range(world_height_cells)]

    for chunk in dirty_chunks:
        cx, cy = chunk["chunk_key"]
        size: int = chunk["size"]
        data: list[float] = chunk["data"]

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
                grid[world_y][world_x] = value_to_terrain(data[idx])

    return grid


if __name__ == "__main__":
    # Sanity check
    test_values = [0.0, 0.05, 0.15, 0.25, 0.35, 0.50, 0.70, 0.85, 0.95, 1.0]
    print("Threshold smoke test:")
    for v in test_values:
        print(f"  {v:.2f} → {value_to_terrain(v)}")
