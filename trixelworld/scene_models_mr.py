"""
scene_models_mr.py — Trixel Environment Descriptor Layer

Abstracts spatial composition entirely away from rendering harnesses.
A SceneDef describes 'where' and 'what' without executing drawing loops.
"""

from dataclasses import dataclass, field
from typing import Optional
import math

# ---------------------------------------------------------------------------
# Descriptor Models
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BandDef:
    """A horizontal region (zone) filled with strokes, optionally wavy over X."""
    label: str
    recipe_name: str
    y_start: float
    y_end: float
    steps_y: int = 1
    wave_amp: float = 0.0
    x_step: int = 20

@dataclass(frozen=True)
class PathDef:
    """A specific vector path with a single brush applied."""
    label: str
    recipe_name: str
    points: tuple[tuple[float, float], ...]

@dataclass(frozen=True)
class AtmosphereDef:
    """A localized atmospheric phenomenon (flare, fog node)."""
    flare_name: str
    position_x_pct: float  # Percentage of width, so it scales with resolution
    position_y: float
    scale: float = 1.0

@dataclass(frozen=True)
class SceneDef:
    """A complete environment layout descriptor."""
    name: str
    width: int
    height: int
    bg_colour: tuple[int, int, int]
    bands: tuple[BandDef, ...] = field(default_factory=tuple)
    paths: tuple[PathDef, ...] = field(default_factory=tuple)
    atmosphere: tuple[AtmosphereDef, ...] = field(default_factory=tuple)


# ---------------------------------------------------------------------------
# Canonical Scenes
# ---------------------------------------------------------------------------

BEACH_SCENE = SceneDef(
    name="Canonical Beach",
    width=640,
    height=360,
    bg_colour=(230, 230, 230),
    bands=(
        BandDef("Sky",         "beach_sky",      30,  150, steps_y=30, wave_amp=2.0),
        BandDef("Sun Core",    "beach_sun",      145, 155, steps_y=2,  wave_amp=0.0),
        BandDef("Water",       "beach_water",    155, 230, steps_y=15, wave_amp=4.0),
        BandDef("Foam Edge",   "beach_foam",     225, 235, steps_y=2,  wave_amp=6.0),
        BandDef("Wet Sand",    "beach_wet_sand", 235, 270, steps_y=6,  wave_amp=2.0),
        BandDef("Dry Sand",    "beach_dry_sand", 270, 360, steps_y=12, wave_amp=2.0),
    ),
    paths=(
        PathDef("Foreground Rock", "beach_rock",
            tuple((50 + math.cos(i*0.5)*30, 320 + math.sin(i*0.5)*30) for i in range(15))
        ),
        PathDef("Driftwood", "beach_driftwood", ((400, 340), (520, 310))),
        PathDef("Grass", "beach_grass", ((400, 335), (420, 300), (450, 300), (500, 330))),
    ),
    atmosphere=(
        AtmosphereDef("Default", position_x_pct=0.75, position_y=150.0, scale=1.0),
    )
)

ALL_SCENES = {
    "beach": BEACH_SCENE,
}
