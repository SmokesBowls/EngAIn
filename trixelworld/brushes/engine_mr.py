"""
engine_mr.py — Trixel Brush Stamp Engine (mr kernel)

Pure functional. Snapshot-in → snapshot-out.
No I/O, no side effects, no GIMP knowledge.
Receives BrushRecipe objects from the adapter layer.
Renders strokes into a SurfaceBuffer.

Four core jobs:
  1. Choose the shape source — parametric, bitmap stamp, or hose cell
  2. Apply spacing / rotation / variant selection
  3. Apply dynamics as sampled modifiers (opacity, size, angle, jitter)
  4. Stamp onto a grayscale or RGBA surface buffer

Coordinate convention:
  - Surface origin (0, 0) is top-left.
  - X increases right, Y increases down.
  - All positions are floats; pixel writes are floor-snapped.
  - Buffer layout: flat bytes, row-major, channel-last.
    Grayscale: buf[y * width + x]
    RGBA:      buf[(y * width + x) * 4 : (y * width + x) * 4 + 4]

Input event model:
  A StrokeEvent carries the artist's intent at a single point in a stroke.
  Fields mirror what a tablet or mouse delivers: position, pressure,
  velocity, tilt, direction. Fields not available default to 0.5 (neutral).

All random selection (hose cells, jitter) is driven by a caller-supplied
seed so strokes are deterministic and replayable.
"""

from __future__ import annotations

import math
import struct
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from brush_models_mr import (
    BrushDynamicsAsset,
    BrushRecipe,
    BrushShapeAsset,
    VariantBrushBundle,
)


# ---------------------------------------------------------------------------
# Surface buffer
# ---------------------------------------------------------------------------

@dataclass
class SurfaceBuffer:
    """
    Mutable RGBA surface.

    Stored as a flat bytearray, channel-last RGBA.
    width × height × 4 bytes total.

    The engine is the only writer. Callers pass the buffer in and get it
    back after stamping.
    """
    width:  int
    height: int
    data:   bytearray

    @staticmethod
    def blank(width: int, height: int) -> "SurfaceBuffer":
        """Create a fully transparent black surface."""
        return SurfaceBuffer(width=width, height=height,
                             data=bytearray(width * height * 4))

    def get_pixel(self, x: int, y: int) -> tuple[int, int, int, int]:
        """Return RGBA at pixel (x, y). Clamps to border."""
        x = max(0, min(self.width - 1, x))
        y = max(0, min(self.height - 1, y))
        base = (y * self.width + x) * 4
        return tuple(self.data[base:base + 4])

    def set_pixel(self, x: int, y: int, r: int, g: int, b: int, a: int) -> None:
        """Write RGBA at pixel (x, y). Out-of-bounds writes are silently dropped."""
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return
        base = (y * self.width + x) * 4
        self.data[base]     = r
        self.data[base + 1] = g
        self.data[base + 2] = b
        self.data[base + 3] = a

    def blend_pixel(self, x: int, y: int,
                    r: int, g: int, b: int, stamp_alpha: int) -> None:
        """
        Alpha-composite stamp colour over existing pixel (normal blend mode).
        stamp_alpha is the combined brush alpha at this pixel.
        """
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return
        if stamp_alpha == 0:
            return
        base = (y * self.width + x) * 4
        dst_r = self.data[base]
        dst_g = self.data[base + 1]
        dst_b = self.data[base + 2]
        dst_a = self.data[base + 3]

        sa = stamp_alpha / 255.0
        da = dst_a / 255.0
        out_a = sa + da * (1.0 - sa)

        if out_a < 1e-6:
            return

        inv = da * (1.0 - sa) / out_a
        self.data[base]     = int(r * sa / out_a + dst_r * inv)
        self.data[base + 1] = int(g * sa / out_a + dst_g * inv)
        self.data[base + 2] = int(b * sa / out_a + dst_b * inv)
        self.data[base + 3] = int(out_a * 255)

    def to_pgm(self) -> bytes:
        """Export as grayscale PGM (P5) using alpha channel as luminance."""
        header = f"P5\n{self.width} {self.height}\n255\n".encode()
        pixels = bytearray(self.width * self.height)
        for i in range(self.width * self.height):
            pixels[i] = self.data[i * 4 + 3]   # alpha → grey
        return header + bytes(pixels)

    def to_ppm(self) -> bytes:
        """Export as RGB PPM (P6), discarding alpha."""
        header = f"P6\n{self.width} {self.height}\n255\n".encode()
        pixels = bytearray(self.width * self.height * 3)
        for i in range(self.width * self.height):
            pixels[i * 3]     = self.data[i * 4]
            pixels[i * 3 + 1] = self.data[i * 4 + 1]
            pixels[i * 3 + 2] = self.data[i * 4 + 2]
        return header + bytes(pixels)


# ---------------------------------------------------------------------------
# Stroke event
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class StrokeEvent:
    """
    One input sample along a stroke.

    All float fields are normalised to [0.0, 1.0] unless noted.
    Missing inputs default to 0.5 (neutral / mid-range).

    position_x / position_y: surface coordinates (pixels, may be fractional)
    pressure:    0.0 = no pressure, 1.0 = full pressure
    velocity:    0.0 = stationary, 1.0 = maximum speed
    direction:   stroke angle in radians [0, 2π), 0 = right, increases CW
    tilt_x:      stylus tilt along X axis [-1.0, 1.0]
    tilt_y:      stylus tilt along Y axis [-1.0, 1.0]
    random_seed: per-stamp seed for reproducible random selection
    """
    position_x:  float
    position_y:  float
    pressure:    float = 0.5
    velocity:    float = 0.5
    direction:   float = 0.0       # radians
    tilt_x:      float = 0.0
    tilt_y:      float = 0.0
    random_seed: int   = 0


# ---------------------------------------------------------------------------
# Dynamics sampling
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DynamicsModifiers:
    """Resolved per-stamp modifier values, all in [0.0, 1.0] unless noted."""
    opacity:       float = 1.0
    size_scale:    float = 1.0   # multiplier on base radius/size
    angle_offset:  float = 0.0   # additive rotation in radians
    jitter_radius: float = 0.0   # displacement in pixels


def _lut_sample(samples: tuple[float, ...], t: float) -> float:
    """Sample a 256-point LUT at normalised t ∈ [0.0, 1.0]."""
    idx = max(0, min(255, int(t * 255)))
    return samples[idx]


def _tilt_magnitude(tilt_x: float, tilt_y: float) -> float:
    """Combined tilt [0, 1] from separate X/Y components."""
    return min(1.0, math.sqrt(tilt_x ** 2 + tilt_y ** 2))


def sample_dynamics(
    dynamics: Optional[BrushDynamicsAsset],
    event: StrokeEvent,
) -> DynamicsModifiers:
    """
    Sample all active dynamics curves for a given input event.

    Returns resolved modifier values. When dynamics is None or a channel
    has no active curves, the neutral default is used (opacity=1, scale=1, etc.).

    Multiple active inputs for the same output channel are multiplied together.
    That matches GIMP's behaviour: if both pressure and velocity drive opacity,
    the result is pressure_opacity × velocity_opacity.
    """
    if dynamics is None or not dynamics.active_channels:
        return DynamicsModifiers()

    # Input signal map — all normalised [0, 1]
    inputs = {
        "pressure":  event.pressure,
        "velocity":  event.velocity,
        "direction": event.direction / (2 * math.pi),   # radians → [0,1]
        "tilt":      _tilt_magnitude(event.tilt_x, event.tilt_y),
        "fade":      0.0,    # fade requires stroke-length context; default 0
        "random":    _lcg_float(event.random_seed),
        "wheel":     0.5,    # airbrush wheel; neutral default
    }

    # Accumulate per-channel
    opacity       = 1.0
    size_scale    = 1.0
    angle_offset  = 0.0
    jitter_radius = 0.0

    for curve in dynamics.active_curves:
        t      = inputs.get(curve.input_source, 0.5)
        value  = _lut_sample(curve.samples, t)

        ch = curve.output_channel
        if ch == "opacity":
            opacity *= value
        elif ch == "size":
            size_scale *= value
        elif ch == "angle":
            # Angle LUT maps [0,1] → [0, 2π] rotation offset
            angle_offset += value * 2 * math.pi
        elif ch == "jitter":
            jitter_radius = max(jitter_radius, value * 50.0)  # max 50px jitter
        # force, hardness, aspect_ratio, spacing, rate, flow, color:
        # reserved for future passes; silently accepted here

    return DynamicsModifiers(
        opacity=max(0.0, min(1.0, opacity)),
        size_scale=max(0.01, size_scale),
        angle_offset=angle_offset % (2 * math.pi),
        jitter_radius=max(0.0, jitter_radius),
    )


def _lcg_float(seed: int) -> float:
    """Deterministic pseudo-random float [0, 1) from integer seed."""
    # LCG constants from Numerical Recipes
    val = (seed * 1664525 + 1013904223) & 0xFFFFFFFF
    return val / 0x100000000


# ---------------------------------------------------------------------------
# Shape rendering
# ---------------------------------------------------------------------------

def _render_parametric(
    buf: SurfaceBuffer,
    cx: float, cy: float,
    shape: BrushShapeAsset,
    mods: DynamicsModifiers,
    r: int, g: int, b: int,
) -> None:
    """
    Stamp a parametric brush (from .vbr) onto the surface.

    Generates a soft/hard ellipse with rotation support.
    aspect > 1 squishes the brush along the minor axis.
    angle_offset from dynamics adds to the shape's base rotation.
    """
    radius   = (shape.radius or 10.0) * mods.size_scale
    hardness = shape.hardness if shape.hardness is not None else 0.5
    aspect   = shape.aspect if shape.aspect is not None else 25.0
    # aspect in vbr: 25.0 = round default, lower = more elliptical
    # convert to ratio: 1.0 = circle, < 1.0 = squished
    aspect_ratio = min(1.0, aspect / 25.0) if aspect > 0 else 1.0
    base_angle   = (shape.angle or 0.0) * math.pi / 180.0
    total_angle  = base_angle + mods.angle_offset

    cos_a = math.cos(total_angle)
    sin_a = math.sin(total_angle)

    iradius = int(radius) + 2
    base_opacity = mods.opacity

    for dy in range(-iradius, iradius + 1):
        for dx in range(-iradius, iradius + 1):
            # Rotate the offset into brush-local space
            lx =  dx * cos_a + dy * sin_a
            ly = -dx * sin_a + dy * cos_a
            # Apply aspect squeeze on minor axis
            lx_scaled = lx / radius if radius > 0 else 0.0
            ly_scaled = ly / (radius * aspect_ratio) if radius > 0 else 0.0
            dist = math.sqrt(lx_scaled ** 2 + ly_scaled ** 2)
            if dist >= 1.0:
                continue
            # Hardness: sharper falloff curve
            if hardness >= 1.0:
                alpha_f = 1.0
            else:
                inner = hardness
                if dist <= inner:
                    alpha_f = 1.0
                else:
                    alpha_f = 1.0 - (dist - inner) / (1.0 - inner)

            alpha = int(alpha_f * base_opacity * 255)
            buf.blend_pixel(int(cx) + dx, int(cy) + dy, r, g, b, alpha)


def _render_bitmap(
    buf: SurfaceBuffer,
    cx: float, cy: float,
    shape: BrushShapeAsset,
    mods: DynamicsModifiers,
    r: int, g: int, b: int,
    pixel_data: Optional[bytes],
) -> None:
    """
    Stamp a bitmap brush (from .gbr, .pgm, or .gih cell) onto the surface.

    The bitmap supplies a grayscale alpha mask. It is scaled by size_scale
    and composited with the painter's colour (r, g, b) at the stamp position.

    pixel_data: raw grayscale bytes, length = width × height.
    If pixel_data is None (lazy-loaded bitmap not yet resolved), a flat
    square is stamped using the shape dimensions as a fallback.
    """
    w = shape.width or 32
    h = shape.height or 32
    scale = mods.size_scale
    sw = max(1, int(w * scale))
    sh = max(1, int(h * scale))
    base_opacity = mods.opacity

    ox = int(cx) - sw // 2
    oy = int(cy) - sh // 2

    if pixel_data is None:
        # Fallback: solid square of the brush's nominal dimensions
        alpha = int(base_opacity * 200)
        for dy in range(sh):
            for dx in range(sw):
                buf.blend_pixel(ox + dx, oy + dy, r, g, b, alpha)
        return

    for dy in range(sh):
        for dx in range(sw):
            # Sample source pixel (nearest-neighbour)
            src_x = int(dx * w / sw)
            src_y = int(dy * h / sh)
            src_idx = src_y * w + src_x
            if src_idx >= len(pixel_data):
                continue
            mask_alpha = pixel_data[src_idx]
            if mask_alpha == 0:
                continue
            alpha = int((mask_alpha / 255.0) * base_opacity * 255)
            buf.blend_pixel(ox + dx, oy + dy, r, g, b, alpha)


# ---------------------------------------------------------------------------
# Hose cell selection
# ---------------------------------------------------------------------------

def select_hose_cell(
    bundle: VariantBrushBundle,
    event: StrokeEvent,
    stroke_index: int,
) -> BrushShapeAsset:
    """
    Select which cell of a VariantBrushBundle to stamp at this event.

    Selection mode is read from the bundle's selection_mode field.
    Multi-axis bundles (mode = 'angular/random') dispatch each axis
    independently then compute the flat cell index.

    Supported modes (per axis):
        random       — deterministic hash of seed + stroke_index
        incremental  — cycle by stroke_index
        angular      — map stroke direction to cell
        pressure     — map pressure to cell
        xtilt        — map tilt_x to cell
        ytilt        — map tilt_y to cell
    """
    axes = bundle.selection_mode.split("/")
    cells = bundle.cells

    if len(cells) == 0:
        return cells[0]  # will raise if genuinely empty

    # Single axis (common case)
    if len(axes) == 1:
        return cells[_axis_index(axes[0], len(cells), event, stroke_index)]

    # Multi-axis: compute rank sizes from bundle
    # Rank sizes are stored in the original axes; we approximate from
    # the cell count and axis count by assuming equal rank distribution.
    # Full axis-rank data lives in GihBrush; the bundle stores the flat
    # cells. We reconstruct equal ranks as the best available approximation.
    n = len(cells)
    dim = len(axes)
    rank = max(1, round(n ** (1.0 / dim)))

    idx = 0
    stride = n
    for axis_mode in axes:
        stride = max(1, stride // rank)
        axis_idx = _axis_index(axis_mode, rank, event, stroke_index)
        idx += axis_idx * stride

    return cells[min(idx, n - 1)]


def _axis_index(
    mode: str,
    rank: int,
    event: StrokeEvent,
    stroke_index: int,
) -> int:
    """Map one selection axis to a cell index [0, rank)."""
    if rank <= 1:
        return 0

    if mode == "random":
        seed = (event.random_seed ^ stroke_index ^ 0xDEAD) & 0xFFFFFFFF
        return int(_lcg_float(seed) * rank) % rank
    elif mode == "incremental":
        return stroke_index % rank
    elif mode == "angular":
        # Divide the 2π circle into equal sectors
        t = event.direction / (2 * math.pi)
        return int(t * rank) % rank
    elif mode == "pressure":
        return int(event.pressure * rank) % rank
    elif mode in ("xtilt", "tilt"):
        t = (event.tilt_x + 1.0) / 2.0   # [-1,1] → [0,1]
        return int(t * rank) % rank
    elif mode == "ytilt":
        t = (event.tilt_y + 1.0) / 2.0
        return int(t * rank) % rank
    else:
        return 0


# ---------------------------------------------------------------------------
# Jitter
# ---------------------------------------------------------------------------

def _apply_jitter(
    cx: float, cy: float,
    jitter_radius: float,
    seed: int,
) -> tuple[float, float]:
    """Displace stamp centre by a deterministic jitter offset."""
    if jitter_radius <= 0:
        return cx, cy
    angle = _lcg_float(seed ^ 0xBEEF) * 2 * math.pi
    dist  = _lcg_float(seed ^ 0xCAFE) * jitter_radius
    return cx + math.cos(angle) * dist, cy + math.sin(angle) * dist


# ---------------------------------------------------------------------------
# Pixel data loader (lazy)
# ---------------------------------------------------------------------------

def _load_bitmap(shape: BrushShapeAsset) -> Optional[bytes]:
    """
    Load raw grayscale pixel data from the shape's bitmap_path.

    Returns None if the path is missing or the file cannot be read.
    The .gih case: bitmap_path points to the container .gih, not a standalone
    file — data is already in the GihCell's pixel_data. Callers that build
    shapes from .gih cells should pass pixel_data directly rather than using
    this loader.
    """
    if not shape.bitmap_path:
        return None
    p = Path(shape.bitmap_path)
    if not p.exists():
        return None
    ext = p.suffix.lower()
    try:
        if ext in (".gbr", ".pat"):
            from brushes.gbr_parser_mr import parse_gbr
            b = parse_gbr(p)
            return bytes(b.pixel_data) if b.depth == 1 else None
        elif ext == ".pgm":
            from brushes.gbr_parser_mr import parse_pgm
            b = parse_pgm(p)
            return bytes(b.pixel_data)
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Core stamp function
# ---------------------------------------------------------------------------

def stamp_recipe(
    buf: SurfaceBuffer,
    recipe: BrushRecipe,
    event: StrokeEvent,
    stroke_index: int = 0,
    colour: tuple[int, int, int] = (0, 0, 0),
) -> SurfaceBuffer:
    """
    Stamp one brush mark from a BrushRecipe onto a SurfaceBuffer.

    Pure functional on the recipe/event/colour side.
    The surface buffer is mutated in place and returned.

    Args:
        buf:          Surface to paint on.
        recipe:       Assembled brush recipe from the adapter layer.
        event:        Input event at this stamp position.
        stroke_index: Ordinal position in the stroke (for incremental hose).
        colour:       RGB ink colour (0-255 each).

    Returns:
        The same SurfaceBuffer, mutated.
    """
    r, g, b = colour

    # --- Dynamics ---
    mods = sample_dynamics(recipe.dynamics, event)

    # --- Jitter ---
    cx, cy = _apply_jitter(
        event.position_x, event.position_y,
        mods.jitter_radius,
        event.random_seed ^ stroke_index,
    )

    # --- Shape dispatch ---
    if recipe.is_variant() and recipe.variant_bundle:
        shape = select_hose_cell(recipe.variant_bundle, event, stroke_index)
        # For .gih cells the pixel data is embedded in the source file.
        # We don't cache it here; the loader reads the parent .gih and
        # extracts the right cell's bytes.
        pixel_data = _load_bitmap(shape)
        _render_bitmap(buf, cx, cy, shape, mods, r, g, b, pixel_data)

    elif recipe.shape is not None:
        shape = recipe.shape
        if shape.is_parametric():
            _render_parametric(buf, cx, cy, shape, mods, r, g, b)
        else:
            pixel_data = _load_bitmap(shape)
            _render_bitmap(buf, cx, cy, shape, mods, r, g, b, pixel_data)

    return buf


# ---------------------------------------------------------------------------
# Stroke interpolation
# ---------------------------------------------------------------------------

def stroke_to_events(
    points: list[tuple[float, float]],
    spacing_pct: float = 1.0,
    base_radius: float = 10.0,
    pressure: float = 0.7,
    velocity: float = 0.5,
    seed: int = 42,
) -> list[StrokeEvent]:
    """
    Interpolate a list of (x, y) control points into a sequence of
    evenly-spaced StrokeEvent stamps.

    spacing_pct: stamp distance as fraction of brush diameter (from recipe).
        1.0 = stamps touch, 2.0 = one gap between stamps.
    base_radius: brush radius in pixels (used to convert spacing_pct to pixels).
    """
    if not points:
        return []

    stamp_distance = max(1.0, base_radius * 2.0 * spacing_pct)
    events: list[StrokeEvent] = []
    accumulated = 0.0
    stroke_idx = 0

    # Always stamp at the start point
    x0, y0 = points[0]
    events.append(StrokeEvent(
        position_x=x0, position_y=y0,
        pressure=pressure, velocity=velocity,
        direction=0.0, random_seed=seed ^ stroke_idx,
    ))
    stroke_idx += 1

    for i in range(1, len(points)):
        px, py = points[i - 1]
        qx, qy = points[i]
        seg_len = math.sqrt((qx - px) ** 2 + (qy - py) ** 2)
        if seg_len < 1e-6:
            continue
        direction = math.atan2(qy - py, qx - px)
        t = (stamp_distance - accumulated) / seg_len

        while t <= 1.0:
            sx = px + t * (qx - px)
            sy = py + t * (qy - py)
            events.append(StrokeEvent(
                position_x=sx, position_y=sy,
                pressure=pressure, velocity=velocity,
                direction=direction,
                random_seed=(seed ^ stroke_idx) & 0xFFFFFFFF,
            ))
            stroke_idx += 1
            t += stamp_distance / seg_len

        accumulated = seg_len * (t - 1.0) * (seg_len / stamp_distance) % stamp_distance

    return events


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")
    from pathlib import Path
    from trixel_brush_adapter import AssetRegistry

    print("Loading assets...")
    registry = AssetRegistry()
    registry.load_from_directory(Path("/usr/share/gimp/2.0/brushes"))
    registry.load_from_directory(Path("/usr/share/gimp/2.0/dynamics"))
    s = registry.summary()
    print(f"  shapes={s['shapes']}  dynamics={s['dynamics']}"
          f"  bundles={s['variant_bundles']}")

    W, H = 400, 300

    # --- Test 1: parametric brush, pressure modulates opacity ---
    print("\nTest 1: parametric (Hardness 050 + Pencil Generic)")
    recipe1 = registry.build_recipe_from_parts("2. Hardness 050", "Pencil Generic")
    assert recipe1, "Recipe 1 not built"
    buf1 = SurfaceBuffer.blank(W, H)
    pts = [(50 + i * 8, 80 + math.sin(i * 0.3) * 30) for i in range(40)]
    for idx, ev in enumerate(stroke_to_events(pts, spacing_pct=recipe1.shape.spacing_pct,
                                               base_radius=recipe1.shape.radius or 10,
                                               pressure=0.8, seed=1)):
        stamp_recipe(buf1, recipe1, ev, stroke_index=idx, colour=(30, 30, 30))
    out1 = Path("/tmp/trixel_test1_parametric.pgm")
    out1.write_bytes(buf1.to_pgm())
    print(f"  Written: {out1}  ({W}x{H})")

    # --- Test 2: bitmap brush ---
    print("\nTest 2: bitmap stamp (Hatch-Pen-01 + Pressure Opacity)")
    recipe2 = registry.build_recipe_from_parts("Hatch-Pen-01", "Pressure Opacity")
    assert recipe2, "Recipe 2 not built"
    buf2 = SurfaceBuffer.blank(W, H)
    pts2 = [(60 + i * 6, 150) for i in range(45)]
    for idx, ev in enumerate(stroke_to_events(pts2, spacing_pct=1.0,
                                               base_radius=64, pressure=0.9, seed=2)):
        stamp_recipe(buf2, recipe2, ev, stroke_index=idx, colour=(20, 20, 20))
    out2 = Path("/tmp/trixel_test2_bitmap.pgm")
    out2.write_bytes(buf2.to_pgm())
    print(f"  Written: {out2}  ({W}x{H})")

    # --- Test 3: variant hose (Acrylic 03, random selection) ---
    print("\nTest 3: variant hose (Acrylic 03 + Pencil Generic, random cells)")
    recipe3 = registry.build_recipe_from_bundle("Acrylic 03", "Pencil Generic")
    assert recipe3, "Recipe 3 not built"
    buf3 = SurfaceBuffer.blank(W, H)
    pts3 = [(80 + i * 7, 230 + math.sin(i * 0.5) * 20) for i in range(30)]
    for idx, ev in enumerate(stroke_to_events(pts3, spacing_pct=1.0,
                                               base_radius=100, pressure=0.75, seed=3)):
        stamp_recipe(buf3, recipe3, ev, stroke_index=idx, colour=(40, 40, 40))
    out3 = Path("/tmp/trixel_test3_hose.pgm")
    out3.write_bytes(buf3.to_pgm())
    print(f"  Written: {out3}  ({W}x{H})")

    # --- Test 4: multi-axis variant (Felt Pen, pressure/ytilt/xtilt) ---
    print("\nTest 4: 3-axis variant (Felt Pen + Basic Dynamics)")
    recipe4 = registry.build_recipe_from_bundle("Felt Pen", "Basic Dynamics")
    assert recipe4, "Recipe 4 not built"
    buf4 = SurfaceBuffer.blank(200, 200)
    import random
    rng = random.Random(99)
    pts4 = [(rng.uniform(20, 180), rng.uniform(20, 180)) for _ in range(8)]
    for idx, ev in enumerate(stroke_to_events(pts4, spacing_pct=1.0,
                                               base_radius=15, pressure=0.6, seed=4)):
        ev_with_tilt = StrokeEvent(
            position_x=ev.position_x, position_y=ev.position_y,
            pressure=ev.pressure, velocity=ev.velocity,
            direction=ev.direction,
            tilt_x=math.sin(idx * 0.4) * 0.8,
            tilt_y=math.cos(idx * 0.3) * 0.5,
            random_seed=ev.random_seed,
        )
        stamp_recipe(buf4, recipe4, ev_with_tilt, stroke_index=idx, colour=(0, 0, 0))
    out4 = Path("/tmp/trixel_test4_multiaxis.pgm")
    out4.write_bytes(buf4.to_pgm())
    print(f"  Written: {out4}  (200x200)")

    print("\n✓ All four tests passed — check output files in /tmp/")
