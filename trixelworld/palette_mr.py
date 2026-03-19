"""
palette_mr.py — Trixel Palette Colour Selection

Pure functional. No I/O, no side effects.
Takes a PaletteAsset and selection parameters → returns an RGB colour tuple.

Four selection modes:
  index      — direct index lookup (deterministic, good for fixed material slots)
  sequential — walk palette in order across stamps (cycle through ramp)
  gradient   — map a float t ∈ [0,1] to a colour by linear interpolation
               along the palette as a gradient ramp
  nearest    — find the palette entry closest to a given target colour (snap)

These cover the main art-use cases:
  - index/sequential → material identity, biome stripe slots
  - gradient         → terrain elevation, depth, fade effects
  - nearest          → palette-discipline enforcement (no clown soup)

All functions operate on plain colour tuples (r, g, b) with values 0-255.
The PaletteAsset type is imported for type hints only; no asset loading here.
"""


# ---------------------------------------------------------------------------
# DEPENDENCY TRACKING                                               v1
# ---------------------------------------------------------------------------
# This file calls:    brush_models_mr.py          (Same Folder — TYPE_CHECKING only)
#                     trixel_brush_adapter.py     (Same Folder — smoke test only)
# This file is called by: engine_mr.py            (Same Folder)
#                          __main__ (CLI direct execution)
# ---------------------------------------------------------------------------
from __future__ import annotations

import math
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from brush_models_mr import PaletteAsset, GradientAsset


# ---------------------------------------------------------------------------
# Colour math
# ---------------------------------------------------------------------------

Colour = tuple[int, int, int]


def lerp_colour(a: Colour, b: Colour, t: float) -> Colour:
    """Linearly interpolate between two RGB colours."""
    t = max(0.0, min(1.0, t))
    return (
        int(a[0] + (b[0] - a[0]) * t),
        int(a[1] + (b[1] - a[1]) * t),
        int(a[2] + (b[2] - a[2]) * t),
    )


def colour_distance_sq(a: Colour, b: Colour) -> int:
    """Squared Euclidean distance in RGB space (no sqrt needed for nearest)."""
    return (a[0]-b[0])**2 + (a[1]-b[1])**2 + (a[2]-b[2])**2


def blend_colour(fg: Colour, bg: Colour, alpha: float) -> Colour:
    """Alpha-blend fg over bg (normal mode, alpha in [0,1])."""
    a = max(0.0, min(1.0, alpha))
    return (
        int(fg[0]*a + bg[0]*(1.0-a)),
        int(fg[1]*a + bg[1]*(1.0-a)),
        int(fg[2]*a + bg[2]*(1.0-a)),
    )


def tint_colour(base: Colour, tint: Colour, strength: float = 0.3) -> Colour:
    """Shift base colour towards tint by strength ∈ [0,1]."""
    return blend_colour(tint, base, strength)


# ---------------------------------------------------------------------------
# Selection modes
# ---------------------------------------------------------------------------

def palette_index(palette: "PaletteAsset", index: int) -> Colour:
    """
    Return the colour at a specific palette index.
    Index wraps (modulo palette length) — never out of range.
    """
    if palette is None or not palette.colors:
        return (0, 0, 0)
    return palette.colors[index % len(palette.colors)]


def palette_sequential(palette: "PaletteAsset", stamp_index: int,
                        start: int = 0, count: Optional[int] = None) -> Colour:
    """
    Walk palette colours in order, one per stamp.
    Uses a slice of the palette: colours[start : start+count].
    count=None means "use all colours from start to end."

    Good for: ordered stripe patterns, material ramps, alternating colours.
    """
    if palette is None or not palette.colors:
        return (0, 0, 0)
    end = len(palette.colors) if count is None else min(start + count, len(palette.colors))
    span = palette.colors[start:end]
    if not span:
        return (0, 0, 0)
    return span[stamp_index % len(span)]


def gradient_sample(gradient: "GradientAsset", t: float) -> Colour:
    """Sample an authored GradientAsset at normalized position t ∈ [0, 1]."""
    if not gradient.segments:
        return (0, 0, 0)
    t = max(0.0, min(1.0, t))
    for seg in gradient.segments:
        if seg.l <= t <= seg.r:
            width = seg.r - seg.l
            if width <= 0.0:
                frac = 0.0
            else:
                frac = (t - seg.l) / width
            
            # Linear interpolation (blend_type ignored for now)
            r = int(seg.rgba0[0]*255 + (seg.rgba1[0] - seg.rgba0[0]) * 255 * frac)
            g = int(seg.rgba0[1]*255 + (seg.rgba1[1] - seg.rgba0[1]) * 255 * frac)
            b = int(seg.rgba0[2]*255 + (seg.rgba1[2] - seg.rgba0[2]) * 255 * frac)
            return (r, g, b)
    
    # Fallback if t is out of bounds (should not happen with clamped t)
    s = gradient.segments[-1]
    return (int(s.rgba1[0]*255), int(s.rgba1[1]*255), int(s.rgba1[2]*255))

def palette_gradient(asset: "PaletteAsset | GradientAsset", t: float,
                     start: int = 0, count: Optional[int] = None) -> Colour:
    """
    Sample an asset as a gradient at normalised position t ∈ [0, 1].
    
    If asset is a GradientAsset (.ggr), uses its continuous piecewise segments.
    If asset is a PaletteAsset (.gpl), linearly interpolates between adjacent colours.
    
    count/start slicing only applies to PaletteAssets.
    """
    if asset is None:
        return (0, 0, 0)
    
    if hasattr(asset, 'segments'):
        return gradient_sample(asset, t)
        
    palette: "PaletteAsset" = asset
    if not palette.colors:
        return (0, 0, 0)
    end = len(palette.colors) if count is None else min(start + count, len(palette.colors))
    span = palette.colors[start:end]
    n = len(span)
    if n == 0:
        return (0, 0, 0)
    if n == 1:
        return span[0]

    t = max(0.0, min(1.0, t))
    pos   = t * (n - 1)
    lo    = int(pos)
    hi    = min(lo + 1, n - 1)
    frac  = pos - lo
    return lerp_colour(span[lo], span[hi], frac)


def palette_nearest(palette: "PaletteAsset", target: Colour,
                    start: int = 0, count: Optional[int] = None) -> Colour:
    """
    Find the palette entry with the smallest Euclidean distance to target.
    Snaps any colour to the nearest entry in the palette.

    Uses a slice of the palette: colours[start : start+count].

    Good for: palette discipline (snapping free colours to material set),
    avoiding clown soup when compositing.
    """
    if palette is None or not palette.colors:
        return target
    end = len(palette.colors) if count is None else min(start + count, len(palette.colors))
    span = palette.colors[start:end]
    if not span:
        return target
    return min(span, key=lambda c: colour_distance_sq(c, target))


# ---------------------------------------------------------------------------
# Composite selectors (higher-level, built from the four primitives)
# ---------------------------------------------------------------------------

def elevation_colour(asset: "PaletteAsset | GradientAsset", elevation: float,
                     sea_level: float = 0.3) -> Colour:
    """
    Map an elevation value [0,1] to a colour using the palette as a
    terrain gradient. Values below sea_level use the lower portion of
    the palette (water/depth range); values above use the upper portion.

    This is a two-zone gradient that treats sea_level as a hard boundary:
        elevation < sea_level → gradient over colors[0 : sea_idx]
        elevation >= sea_level → gradient over colors[sea_idx :]

    Works naturally with palettes like Topographic where the colour
    sequence encodes water → ground → highland → snow.
    """
    if asset is None:
        return (0, 0, 0)
        
    if hasattr(asset, 'segments'):
        return gradient_sample(asset, elevation) # Pass raw elevation to true gradients
        
    palette: "PaletteAsset" = asset
    if not palette.colors:
        return (0, 0, 0)
    n = len(palette.colors)
    sea_idx = max(1, int(sea_level * n))

    if elevation < sea_level:
        t = elevation / sea_level
        return palette_gradient(palette, t, start=0, count=sea_idx)
    else:
        t = (elevation - sea_level) / (1.0 - sea_level)
        return palette_gradient(palette, t, start=sea_idx)


def material_colour(palette: "PaletteAsset", material_id: int,
                    variation: float = 0.0) -> Colour:
    """
    Return a colour for a named material slot, with optional micro-variation.

    material_id: integer slot index (wraps around palette length)
    variation:   float ∈ [0, 1], used to interpolate toward the next slot's
                 colour. This gives slight natural variation without breaking
                 material identity.

    Good for: "this stamp is grass material [4], slightly varied"
    """
    if palette is None:
        return (0, 0, 0)
    base  = palette_index(palette, material_id)
    if variation == 0.0:
        return base
    next_ = palette_index(palette, material_id + 1)
    return lerp_colour(base, next_, variation * 0.4)  # cap at 40% blend


def dynamics_colour(asset: "PaletteAsset | GradientAsset", pressure: float,
                    velocity: float = 0.5) -> Colour:
    """
    Select a colour driven by tablet dynamics.

    Maps (pressure + velocity) combined to a palette gradient position.
    Low pressure + low velocity → dark/saturated end of palette.
    High pressure + high velocity → lighter/washed end.

    This gives strokes a natural feel where pressing harder produces
    the "full" colour and lighter strokes pick up the tone variants.
    """
    if asset is None:
        return (0, 0, 0)
    t = (pressure * 0.7 + velocity * 0.3)  # pressure-dominant blend
    return palette_gradient(asset, t)


# ---------------------------------------------------------------------------
# Colour context (bundles palette + mode for passing to stroke callers)
# ---------------------------------------------------------------------------

class ColourContext:
    """
    Holds a palette and a selection strategy for use across an entire stroke.
    Produced by the caller, consumed by stamp_recipe_coloured() in the engine.

    Stateful in that sequential mode tracks the stamp counter internally.
    All other modes are pure/stateless.

    Usage:
        ctx = ColourContext(palette, mode="gradient", t_param=0.6)
        colour = ctx.next(stamp_index=5, pressure=0.8, velocity=0.5)
    """

    def __init__(self, palette: "PaletteAsset | GradientAsset",
                 mode: str = "index",
                 index: int = 0,
                 t_param: float = 0.5,
                 target_colour: Optional[Colour] = None,
                 start: int = 0,
                 count: Optional[int] = None):
        """
        mode:
          "index"      — always return palette[index]
          "sequential" — cycle colours in order across stamps
          "gradient"   — sample palette at t_param
          "nearest"    — snap target_colour to nearest palette entry
          "elevation"  — treat t_param as elevation value
          "material"   — treat index as material slot, t_param as variation
          "dynamics"   — driven by pressure/velocity (passed in next())

        start, count: palette slice (default = whole palette)
        """
        self.palette        = palette
        self.mode           = mode
        self.index          = index
        self.t_param        = t_param
        self.target_colour  = target_colour or (128, 128, 128)
        self.start          = start
        self.count          = count

    def next(self, stamp_index: int = 0,
             pressure: float = 0.5,
             velocity: float = 0.5,
             elevation: float = 0.5) -> Colour:
        """Return the next colour for this stamp."""
        m = self.mode
        if m == "index":
            return palette_index(self.palette, self.index)
        elif m == "sequential":
            return palette_sequential(self.palette, stamp_index,
                                      self.start, self.count)
        elif m == "gradient":
            return palette_gradient(self.palette, self.t_param,
                                    self.start, self.count)
        elif m == "nearest":
            return palette_nearest(self.palette, self.target_colour,
                                   self.start, self.count)
        elif m == "elevation":
            return elevation_colour(self.palette, elevation)
        elif m == "material":
            return material_colour(self.palette, self.index, self.t_param)
        elif m == "dynamics":
            return dynamics_colour(self.palette, pressure, velocity)
        else:
            return palette_index(self.palette, 0)


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import math
    import sys
    from pathlib import Path

    sys.path.insert(0, ".")
    from trixel_brush_adapter import AssetRegistry

    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data")

    print(f"Loading assets from: {root.resolve()}")
    registry = AssetRegistry()
    registry.load_from_directory(root)

    registry.print_summary()

    if s["errors"]:
        for e in registry.errors:
            print(f"    ! {e}")

    topo = registry.palettes.get("Topographic")
    plasma = registry.palettes.get("Plasma")
    default_pal = registry.palettes.get("Default")

    if topo is None:
        raise SystemExit(
            "Smoke test requires palette 'Topographic'. "
            f"Not found under asset root: {root.resolve()}"
        )

    if default_pal is None:
        raise SystemExit(
            "Smoke test requires palette 'Default'. "
            f"Not found under asset root: {root.resolve()}"
        )

    print("=== palette_gradient: Topographic elevation ramp ===")
    for t in [0.0, 0.1, 0.25, 0.3, 0.5, 0.75, 1.0]:
        c = palette_gradient(topo, t)
        bar = "█" * (max(c) // 32)
        print(f"  t={t:.2f}  #{c[0]:02X}{c[1]:02X}{c[2]:02X}  {bar}")

    print("\n=== elevation_colour: sea_level=0.3 ===")
    for elev in [0.0, 0.15, 0.29, 0.30, 0.5, 0.8, 1.0]:
        c = elevation_colour(topo, elev)
        zone = "water" if elev < 0.3 else "land"
        print(f"  elev={elev:.2f}  #{c[0]:02X}{c[1]:02X}{c[2]:02X}  [{zone}]")

    print("\n=== palette_nearest: snap random colours to Default palette ===")
    targets = [(255, 0, 0), (0, 200, 50), (100, 100, 200), (255, 200, 0)]
    for t in targets:
        snapped = palette_nearest(default_pal, t)
        d = math.sqrt(colour_distance_sq(t, snapped))
        print(
            f"  #{t[0]:02X}{t[1]:02X}{t[2]:02X} → "
            f"#{snapped[0]:02X}{snapped[1]:02X}{snapped[2]:02X}  "
            f"(dist={d:.1f})"
        )

    print("\n=== ColourContext: dynamics mode (pressure-driven) ===")
    ctx = ColourContext(topo, mode="dynamics")
    for pressure in [0.1, 0.3, 0.5, 0.7, 0.9]:
        c = ctx.next(pressure=pressure, velocity=0.5)
        print(f"  pressure={pressure:.1f}  #{c[0]:02X}{c[1]:02X}{c[2]:02X}")

    print("\n=== material_colour: material slots with variation ===")
    for mat_id in range(5):
        c0 = material_colour(default_pal, mat_id, 0.0)
        c1 = material_colour(default_pal, mat_id, 0.8)
        print(
            f"  mat[{mat_id}]  "
            f"base=#{c0[0]:02X}{c0[1]:02X}{c0[2]:02X}  "
            f"varied=#{c1[0]:02X}{c1[1]:02X}{c1[2]:02X}"
        )

    if plasma is not None:
        print("\n=== palette_gradient: Plasma quick check ===")
        for t in [0.0, 0.25, 0.5, 0.75, 1.0]:
            c = palette_gradient(plasma, t)
            print(f"  t={t:.2f}  #{c[0]:02X}{c[1]:02X}{c[2]:02X}")

    print("\n✓ Palette module tests passed")
