"""Public facade. Do not place implementation here yet. Legacy source remains in terrain/world_field_nucleus.py.

Chunk/world coordinate helpers:
- local tile (x,z) within chunk
- chunk key (chunk_x, chunk_y)
- chunk_size
-> world position (world_x, world_z)

This module is intentionally Python-only and side-effect free.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


LocalXZ = Tuple[int, int]
ChunkKey = Tuple[int, int]
WorldXZ = Tuple[int, int]


@dataclass(frozen=True)
class ChunkCoordinate:
    """Canonical chunk coordinate conversion packet."""

    chunk_key: ChunkKey
    chunk_size: int
    local_xz: LocalXZ
    world_xz: WorldXZ


def local_to_world_xz(local_x: int, local_z: int, chunk_x: int, chunk_y: int, chunk_size: int) -> WorldXZ:
    """Convert local tile coords in a chunk to world-space XZ cell coords.

    Formula:
    world_x = chunk_x * chunk_size + local_x
    world_z = chunk_y * chunk_size + local_z
    """

    cs = int(chunk_size)
    if cs <= 0:
        raise ValueError("chunk_size must be > 0")

    wx = int(chunk_x) * cs + int(local_x)
    wz = int(chunk_y) * cs + int(local_z)
    return (wx, wz)


def world_to_chunk_local_xz(world_x: int, world_z: int, chunk_size: int) -> tuple[ChunkKey, LocalXZ]:
    """Inverse mapping from world-space XZ cell coords to chunk key + local XZ."""

    cs = int(chunk_size)
    if cs <= 0:
        raise ValueError("chunk_size must be > 0")

    wx = int(world_x)
    wz = int(world_z)

    chunk_x = wx // cs
    chunk_y = wz // cs
    local_x = wx - (chunk_x * cs)
    local_z = wz - (chunk_y * cs)

    return (chunk_x, chunk_y), (local_x, local_z)


def make_chunk_coordinate(local_x: int, local_z: int, chunk_x: int, chunk_y: int, chunk_size: int) -> ChunkCoordinate:
    """Build a stable ChunkCoordinate packet from local + chunk inputs."""

    world_xz = local_to_world_xz(local_x, local_z, chunk_x, chunk_y, chunk_size)
    return ChunkCoordinate(
        chunk_key=(int(chunk_x), int(chunk_y)),
        chunk_size=int(chunk_size),
        local_xz=(int(local_x), int(local_z)),
        world_xz=world_xz,
    )
