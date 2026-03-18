"""
surface_behavior_mr.py — Trixel Surface Behavior Definitions

The abstract parent layer. Describes *what kind of surface* is being painted —
not a specific object, not a specific brush. The behavior layer answers:
  - What is the edge character?       (hard, porous, organic, directional)
  - What is the fill character?       (flat, layered, clustered, flowing)
  - What adds variation?              (grain, jitter, scale shift, angle drift)
  - What gives age or motion?         (accumulation, erosion, drift, growth)
  - What controls color discipline?   (gradient, sequential, nearest, material)

These are frozen descriptors. They sit above brush recipes and below
world-object definitions. A TreeDef says "my canopy is a CLUSTERED_ORGANIC
surface." A HouseDef says "my wall is a FLAT_LAYERED surface." The surface
behavior translates that intent into recipe selection parameters.

Nothing here renders. Nothing here loads assets. It is the vocabulary layer.
"""

# ---------------------------------------------------------------------------
# DEPENDENCY TRACKING                                               v1
# ---------------------------------------------------------------------------
# This file calls:    Python standard library only
# This file is called by: world_tree_mr.py         (Same Folder)
#                          world_house_mr.py        (Same Folder — future)
#                          world_water_mr.py        (Same Folder — future)
# ---------------------------------------------------------------------------

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


# ---------------------------------------------------------------------------
# Edge character
# ---------------------------------------------------------------------------

class EdgeType:
    """How this surface meets other surfaces."""
    HARD        = "hard"        # crisp boundary, no feather — walls, beams, windows
    SOFT        = "soft"        # blended edge, high falloff — fog, shadow, glow
    POROUS      = "porous"      # broken edge, irregular — bark, old stone, moss
    DIRECTIONAL = "directional" # edge defined by a vector — grass, fur, thatch
    ORGANIC     = "organic"     # irregular silhouette — leaves, lichen, roots
    LAYERED     = "layered"     # multiple distinct bands — cliff strata, old paint


# ---------------------------------------------------------------------------
# Fill character
# ---------------------------------------------------------------------------

class FillType:
    """How this surface fills its area."""
    FLAT        = "flat"        # single tone, minimal variation — fresh plaster
    TONAL       = "tonal"       # smooth gradient — sky, water depth, bare wall
    GRAINY      = "grainy"      # fine scattered texture — sand, stone dust, old paper
    CLUSTERED   = "clustered"   # grouped stamps — leaf mass, foam, gravel
    DIRECTIONAL = "directional" # strokes follow a vector — bark, thatch, water flow
    TILED       = "tiled"       # repeating unit — brick, planking, scales
    LAYERED     = "layered"     # successive passes build up — charcoal, heavy paint


# ---------------------------------------------------------------------------
# Variation mode
# ---------------------------------------------------------------------------

class VariationMode:
    """What produces natural variation within the surface."""
    NONE        = "none"        # perfectly uniform — glass, polished metal
    GRAIN       = "grain"       # fine random scatter — stone, aged wood
    JITTER      = "jitter"      # position displacement — organic edges
    ANGLE_DRIFT = "angle_drift" # slight rotation per stamp — natural media feel
    SCALE_SHIFT = "scale_shift" # size varies — leaf clusters, rocky ground
    DENSITY     = "density"     # coverage varies by region — moss, wear
    HOSE        = "hose"        # variant cell selection — leaf types, bark sections


# ---------------------------------------------------------------------------
# Age/motion character
# ---------------------------------------------------------------------------

class AgeMode:
    """What signals time or movement in this surface."""
    FRESH       = "fresh"       # no aging — new paint, new stone
    WORN        = "worn"        # edge erosion, color lightening
    WEATHERED   = "weathered"   # staining, lichen, water marks
    MOSSY       = "mossy"       # organic growth accumulation
    FLOWING     = "flowing"     # ripple direction, current marks
    GROWING     = "growing"     # organic expansion from a center


# ---------------------------------------------------------------------------
# SurfaceBehavior — the composite descriptor
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SurfaceBehavior:
    """
    Abstract surface description. One per distinct surface type in a world object.

    A TreeDef.bark uses:
        edge=POROUS, fill=DIRECTIONAL, variation=GRAIN, age=WEATHERED

    A HouseDef.wall uses:
        edge=HARD, fill=FLAT, variation=GRAIN, age=WORN

    A WaterDef.surface uses:
        edge=SOFT, fill=DIRECTIONAL, variation=ANGLE_DRIFT, age=FLOWING

    Callers use these values to select recipe parameters, not specific brushes.
    The world recipe layer translates SurfaceBehavior → recipe choices.
    """
    name:           str           # e.g. "bark", "leaf_mass", "wall_plaster"
    edge:           str           # EdgeType constant
    fill:           str           # FillType constant
    variation:      str           # VariationMode constant
    age:            str           # AgeMode constant
    colour_mode:    str           # palette_mr ColourContext mode
    blend_mode:     str           # 'normal' | 'multiply' | 'additive' | 'screen'
    opacity_range:  tuple[float, float]  # (min, max) opacity for this layer
    density:        float         # 0.0 = sparse, 1.0 = full coverage
    direction_bias: Optional[float]  # radians, None = no directional preference

    def is_organic(self) -> bool:
        return self.edge in (EdgeType.ORGANIC, EdgeType.POROUS)

    def is_directional(self) -> bool:
        return (self.fill == FillType.DIRECTIONAL or
                self.direction_bias is not None)

    def wants_hose(self) -> bool:
        return self.variation == VariationMode.HOSE

    def wants_multiply(self) -> bool:
        return self.age in (AgeMode.WORN, AgeMode.WEATHERED, AgeMode.MOSSY)


# ---------------------------------------------------------------------------
# Pre-built canonical surface behaviors
# (named constants for use in world recipe definitions)
# ---------------------------------------------------------------------------

import math as _math

# Tree surfaces
TREE_BARK = SurfaceBehavior(
    name="bark",
    edge=EdgeType.POROUS,
    fill=FillType.DIRECTIONAL,
    variation=VariationMode.GRAIN,
    age=AgeMode.WEATHERED,
    colour_mode="gradient",
    blend_mode="normal",
    opacity_range=(0.6, 0.9),
    density=0.8,
    direction_bias=_math.pi / 2,    # upward (90°)
)

TREE_SHADOW_MASS = SurfaceBehavior(
    name="shadow_mass",
    edge=EdgeType.SOFT,
    fill=FillType.CLUSTERED,
    variation=VariationMode.DENSITY,
    age=AgeMode.FRESH,
    colour_mode="index",
    blend_mode="multiply",
    opacity_range=(0.3, 0.6),
    density=0.5,
    direction_bias=None,
)

TREE_LEAF_MASS = SurfaceBehavior(
    name="leaf_mass",
    edge=EdgeType.ORGANIC,
    fill=FillType.CLUSTERED,
    variation=VariationMode.HOSE,
    age=AgeMode.FRESH,
    colour_mode="sequential",
    blend_mode="normal",
    opacity_range=(0.7, 1.0),
    density=0.75,
    direction_bias=None,
)

TREE_CANOPY_EDGE = SurfaceBehavior(
    name="canopy_edge",
    edge=EdgeType.ORGANIC,
    fill=FillType.GRAINY,
    variation=VariationMode.JITTER,
    age=AgeMode.FRESH,
    colour_mode="gradient",
    blend_mode="normal",
    opacity_range=(0.5, 0.85),
    density=0.4,
    direction_bias=None,
)

# House surfaces (reserved for future HouseDef)
HOUSE_WALL_PLASTER = SurfaceBehavior(
    name="wall_plaster",
    edge=EdgeType.HARD,
    fill=FillType.FLAT,
    variation=VariationMode.GRAIN,
    age=AgeMode.WORN,
    colour_mode="index",
    blend_mode="normal",
    opacity_range=(0.8, 1.0),
    density=1.0,
    direction_bias=None,
)

HOUSE_TIMBER = SurfaceBehavior(
    name="timber",
    edge=EdgeType.HARD,
    fill=FillType.DIRECTIONAL,
    variation=VariationMode.GRAIN,
    age=AgeMode.WEATHERED,
    colour_mode="gradient",
    blend_mode="normal",
    opacity_range=(0.85, 1.0),
    density=0.9,
    direction_bias=0.0,             # horizontal
)

HOUSE_ROOF_SHINGLE = SurfaceBehavior(
    name="roof_shingle",
    edge=EdgeType.LAYERED,
    fill=FillType.TILED,
    variation=VariationMode.ANGLE_DRIFT,
    age=AgeMode.WORN,
    colour_mode="gradient",
    blend_mode="normal",
    opacity_range=(0.8, 1.0),
    density=0.95,
    direction_bias=_math.pi,        # horizontal bands
)

HOUSE_WEATHERING = SurfaceBehavior(
    name="weathering",
    edge=EdgeType.SOFT,
    fill=FillType.GRAINY,
    variation=VariationMode.DENSITY,
    age=AgeMode.WEATHERED,
    colour_mode="index",
    blend_mode="multiply",
    opacity_range=(0.1, 0.4),
    density=0.25,
    direction_bias=None,
)

# Water surfaces (reserved for future WaterDef)
WATER_DEPTH_BAND = SurfaceBehavior(
    name="depth_band",
    edge=EdgeType.SOFT,
    fill=FillType.TONAL,
    variation=VariationMode.NONE,
    age=AgeMode.FLOWING,
    colour_mode="elevation",
    blend_mode="normal",
    opacity_range=(0.9, 1.0),
    density=1.0,
    direction_bias=None,
)

WATER_SURFACE_RIPPLE = SurfaceBehavior(
    name="surface_ripple",
    edge=EdgeType.DIRECTIONAL,
    fill=FillType.DIRECTIONAL,
    variation=VariationMode.ANGLE_DRIFT,
    age=AgeMode.FLOWING,
    colour_mode="gradient",
    blend_mode="screen",
    opacity_range=(0.2, 0.5),
    density=0.3,
    direction_bias=0.0,             # horizontal flow
)


# ---------------------------------------------------------------------------
# Registry of all canonical behaviors
# ---------------------------------------------------------------------------

ALL_BEHAVIORS: dict[str, SurfaceBehavior] = {
    b.name: b for b in [
        TREE_BARK, TREE_SHADOW_MASS, TREE_LEAF_MASS, TREE_CANOPY_EDGE,
        HOUSE_WALL_PLASTER, HOUSE_TIMBER, HOUSE_ROOF_SHINGLE, HOUSE_WEATHERING,
        WATER_DEPTH_BAND, WATER_SURFACE_RIPPLE,
    ]
}


if __name__ == "__main__":
    print("=== Surface Behavior Registry ===\n")
    for name, b in ALL_BEHAVIORS.items():
        print(f"  {b.name:20s}  edge={b.edge:12s}  fill={b.fill:12s}"
              f"  var={b.variation:12s}  age={b.age}")
    print(f"\n{len(ALL_BEHAVIORS)} behaviors defined.")
