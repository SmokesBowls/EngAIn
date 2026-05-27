"""tile_address.py — coordinate language for 3D trixel surface tiles.

A tile address encodes not just WHERE a cell is in the world, but WHICH
face is visible and from WHICH direction the camera sees it.  This lets
the renderer, recipe selector, and perception layer (dragon eyes) all
speak the same language without re-deriving orientation at each layer.

Address string format:  {h_prefix}{x}.{v_prefix}{y}.{d_prefix}{z}
Direction prefixes:
    d = down   (camera-relative)    u = up
    l = left                        r = right
    f = forward / into scene        b = back / toward camera

Example:
    world_cell (49, 19, 57), camera looking down-left-forward
    → tile_address "d49.l19.f57"

Visible face vocabulary:
    top       — horizontal surface facing camera upward
    bottom    — underside (floating island, overhang)
    wall      — vertical face, axis-aligned (cliff, building)
    slope     — angled surface between top and wall
    edge      — boundary tile between two terrain types
    side      — generic lateral face
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Direction vocabulary
# ---------------------------------------------------------------------------

DIRECTION_PREFIX: Dict[str, str] = {
    "down": "d",    "up": "u",
    "left": "l",    "right": "r",
    "forward": "f", "back": "b",
}

PREFIX_TO_DIRECTION: Dict[str, str] = {v: k for k, v in DIRECTION_PREFIX.items()}

VISIBLE_FACES = ("top", "bottom", "wall", "slope", "edge", "side")

# Standard outward normals for axis-aligned faces (Y-up world)
FACE_NORMALS: Dict[str, Tuple[float, float, float]] = {
    "top":    ( 0.0,  1.0,  0.0),
    "bottom": ( 0.0, -1.0,  0.0),
    "north":  ( 0.0,  0.0, -1.0),
    "south":  ( 0.0,  0.0,  1.0),
    "east":   ( 1.0,  0.0,  0.0),
    "west":   (-1.0,  0.0,  0.0),
}

_ADDR_RE = re.compile(r"([dulrfb])(-?\d+)")


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class CameraRelative:
    """Maps world axes to camera-relative directions for this view."""
    horizontal: str   # "left" | "right"
    vertical: str     # "up"   | "down"
    depth: str        # "forward" | "back"


@dataclass
class TileAddress:
    """Complete spatial descriptor for one visible trixel tile.

    Contains everything the renderer, recipe compiler, and dragon perception
    layer need to treat this tile correctly without re-deriving orientation.
    """
    world_cell:      Tuple[int, int, int]
    camera_relative: CameraRelative
    visible_face:    str                           # see VISIBLE_FACES
    view_vector:     Tuple[float, float, float]    # normalised camera→tile
    surface_normal:  Tuple[float, float, float]    # outward face normal
    recipe:          str                           # e.g. "volcano.branching_lava"
    tile_address:    str                    = ""   # compact string, auto-computed
    neighbor_cells:  List[Tuple[int,int,int]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.tile_address:
            self.tile_address = encode(self.world_cell, self.camera_relative)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["camera_relative"] = asdict(self.camera_relative)
        return d


# ---------------------------------------------------------------------------
# Encode / decode
# ---------------------------------------------------------------------------

def encode(
    world_cell: Tuple[int, int, int],
    camera_relative: CameraRelative,
) -> str:
    """Pack world_cell + camera orientation into a compact address string.

    Axis order in string: x (horizontal) · y (vertical) · z (depth).
    """
    px = DIRECTION_PREFIX[camera_relative.horizontal]
    py = DIRECTION_PREFIX[camera_relative.vertical]
    pz = DIRECTION_PREFIX[camera_relative.depth]
    x, y, z = world_cell
    return f"{px}{x}.{py}{y}.{pz}{z}"


def decode(tile_address: str) -> Dict[str, dict]:
    """Parse a tile_address string back into axis components.

    Returns {"x": {"direction": ..., "value": int}, "y": ..., "z": ...}
    """
    parts = tile_address.split(".")
    if len(parts) != 3:
        raise ValueError(
            f"Expected 3 dot-separated components, got {tile_address!r}"
        )
    result: Dict[str, dict] = {}
    for axis, part in zip(("x", "y", "z"), parts):
        m = _ADDR_RE.fullmatch(part)
        if not m:
            raise ValueError(f"Unrecognised address component: {part!r}")
        result[axis] = {
            "direction": PREFIX_TO_DIRECTION[m.group(1)],
            "value":     int(m.group(2)),
        }
    return result


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------

def build(
    world_cell: Tuple[int, int, int],
    camera_relative: CameraRelative,
    visible_face: str,
    surface_normal: Tuple[float, float, float],
    view_vector: Tuple[float, float, float],
    recipe: str,
    neighbor_cells: Optional[List[Tuple[int, int, int]]] = None,
) -> TileAddress:
    """Construct a fully-described TileAddress for one visible tile."""
    if visible_face not in VISIBLE_FACES and visible_face not in FACE_NORMALS:
        raise ValueError(
            f"Unknown visible_face {visible_face!r}. "
            f"Use one of: {VISIBLE_FACES + tuple(FACE_NORMALS)}"
        )
    return TileAddress(
        world_cell=tuple(world_cell),
        camera_relative=camera_relative,
        visible_face=visible_face,
        view_vector=tuple(view_vector),
        surface_normal=tuple(surface_normal),
        recipe=recipe,
        neighbor_cells=list(neighbor_cells or []),
    )


# ---------------------------------------------------------------------------
# Spatial helpers
# ---------------------------------------------------------------------------

def face_neighbors(cell: Tuple[int, int, int]) -> Dict[str, Tuple[int, int, int]]:
    """Return the 6 face-adjacent cells, keyed by face name."""
    x, y, z = cell
    return {
        "top":    (x,     y + 1, z    ),
        "bottom": (x,     y - 1, z    ),
        "north":  (x,     y,     z - 1),
        "south":  (x,     y,     z + 1),
        "east":   (x + 1, y,     z    ),
        "west":   (x - 1, y,     z    ),
    }


def visible_neighbors(
    cell: Tuple[int, int, int],
    camera_relative: CameraRelative,
) -> Dict[str, Tuple[int, int, int]]:
    """Return the subset of neighbors that share the camera-facing half-space.

    Useful for the dragon: 'what cells are adjacent in the direction I can see?'
    """
    all_n = face_neighbors(cell)
    cam_dirs = {
        camera_relative.horizontal,
        camera_relative.vertical,
        camera_relative.depth,
    }
    # Keep neighbors whose face name maps to a camera-forward direction
    direction_to_face = {
        "down":    "bottom", "up":      "top",
        "left":    "west",   "right":   "east",
        "forward": "south",  "back":    "north",
    }
    return {
        face: neighbor
        for face, neighbor in all_n.items()
        if face in {direction_to_face.get(d) for d in cam_dirs}
    }


def normal_for_face(visible_face: str) -> Tuple[float, float, float]:
    """Return the canonical outward normal for a face name.

    Falls back to (0, 1, 0) for semantic face types (slope, edge, etc.)
    that don't have a single canonical normal.
    """
    return FACE_NORMALS.get(visible_face, (0.0, 1.0, 0.0))
