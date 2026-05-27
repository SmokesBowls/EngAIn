"""Public facade. Do not place implementation here yet. Legacy source remains in godotnew/semantic/scripts/SemanticRenderer.gd.

Render Transform ABI contract:
CoordinateABI + ChunkCoordinate -> renderer-ready transform packet.

This module does not call Godot. It only defines a stable packet shape.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


Vec3 = tuple[float, float, float]


@dataclass(frozen=True)
class RenderTransformABI:
    """Renderer-ready transform contract (engine-agnostic)."""

    position: Vec3 = (0.0, 0.0, 0.0)
    rotation: Vec3 = (0.0, 0.0, 0.0)
    scale: Vec3 = (1.0, 1.0, 1.0)
    visible_face: str = "top"


@dataclass(frozen=True)
class PlacementPacket:
    """Complete placement packet from world truth to render instruction."""

    tile_id: str
    grid: dict[str, int]
    chunk: dict[str, int]
    world: dict[str, float]
    render: RenderTransformABI

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        # Keep render.position/rotation/scale as list-like arrays for JSON wire use.
        d["render"]["position"] = list(self.render.position)
        d["render"]["rotation"] = list(self.render.rotation)
        d["render"]["scale"] = list(self.render.scale)
        return d


def build_render_transform_abi(
    world_x: float,
    world_y: float,
    world_z: float,
    visible_face: str = "top",
    rotation: Vec3 = (0.0, 0.0, 0.0),
    scale: Vec3 = (1.0, 1.0, 1.0),
) -> RenderTransformABI:
    """Build an engine-agnostic render transform contract."""

    return RenderTransformABI(
        position=(float(world_x), float(world_y), float(world_z)),
        rotation=(float(rotation[0]), float(rotation[1]), float(rotation[2])),
        scale=(float(scale[0]), float(scale[1]), float(scale[2])),
        visible_face=str(visible_face),
    )


def build_placement_packet(
    tile_id: str,
    coordinate_abi: Any,
    chunk_coordinate: Any,
    visible_face: str = "top",
    rotation: Vec3 = (0.0, 0.0, 0.0),
    scale: Vec3 = (1.0, 1.0, 1.0),
) -> PlacementPacket:
    """Create the full placement packet.

    Expected minimal attributes:
    - coordinate_abi.grid_xy -> (grid_x, grid_y)
    - coordinate_abi.elevation -> y
    - chunk_coordinate.chunk_key -> (chunk_x, chunk_y)
    - chunk_coordinate.world_xz -> (world_x, world_z)
    """

    grid_x, grid_y = coordinate_abi.grid_xy
    chunk_x, chunk_y = chunk_coordinate.chunk_key
    world_x, world_z = chunk_coordinate.world_xz
    world_y = coordinate_abi.elevation

    render = build_render_transform_abi(
        world_x=float(world_x),
        world_y=float(world_y),
        world_z=float(world_z),
        visible_face=visible_face,
        rotation=rotation,
        scale=scale,
    )

    return PlacementPacket(
        tile_id=str(tile_id),
        grid={"x": int(grid_x), "y": int(grid_y)},
        chunk={"x": int(chunk_x), "y": int(chunk_y)},
        world={"x": float(world_x), "y": float(world_y), "z": float(world_z)},
        render=render,
    )
