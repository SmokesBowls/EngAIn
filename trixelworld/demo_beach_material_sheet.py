"""
demo_beach_material_sheet.py — Beach Material Vocabulary Sheet

One strip per material. One question per strip:
  does this recipe read as that material?

If a strip can only be identified by its label, the recipe needs tuning.
If a strip reads as the material without the label, it is ready.

Strips (top to bottom):
  1. sky_clear        — pale blue gradient, no texture
  2. sky_haze         — soft charcoal grain over sky, horizon glow
  3. water_deep       — dark blue, horizontal ripple charcoal
  4. water_shallow    — lighter blue-green, shorter ripple marks
  5. foam_edge        — broken white bristle on dark wet ground
  6. wet_sand         — dark warm tan, smooth bristle grain
  7. dry_sand         — light warm tan, loose bristle scatter
  8. grass_tufts      — dark green single stamps, irregular
  9. rock_face        — grey hatch, directional downward strokes

Each strip is STRIP_H pixels tall, full canvas width.
Labels printed left-aligned in each strip.

Run:
  python3 demo_beach_material_sheet.py [gimp_root] [out_path]
"""

# ---------------------------------------------------------------------------
# DEPENDENCY TRACKING                                               v1
# ---------------------------------------------------------------------------
# This file calls:    trixel_brush_adapter.py     (Same Folder)
#                     trixel_recipes_mr.py        (Same Folder)
#                     engine_mr.py                (Same Folder)
#                     engine_debug_mr.py          (Same Folder)
# This file is called by: __main__ (CLI direct execution)
# ---------------------------------------------------------------------------

from __future__ import annotations

import math
import sys
from pathlib import Path

_HERE = Path(__file__).parent
sys.path.insert(0, str(_HERE))

from engine_mr import (
    SurfaceBuffer, StrokeEvent, stroke_to_events,
    stamp_recipe, _render_bitmap, _load_bitmap, DynamicsModifiers,
)
from engine_debug_mr import solid_bg, text, save_png, stamp_blended
from trixel_recipes_mr import build
from trixel_brush_adapter import AssetRegistry
from world_tree_mr import _find_gimp_data


# ---------------------------------------------------------------------------
# LCG
# ---------------------------------------------------------------------------
def _lcg(s):  return (s * 1664525 + 1013904223) & 0xFFFFFFFF
def _lcg_f(s): return _lcg(s) / 0x100000000


# ---------------------------------------------------------------------------
# Sheet dimensions
# ---------------------------------------------------------------------------
W        = 640
STRIP_H  = 64
N_STRIPS = 9
H        = STRIP_H * N_STRIPS + 24   # 24px header


# ---------------------------------------------------------------------------
# Strip fill utilities
# ---------------------------------------------------------------------------

def _fill_strip(buf, y0, r, g, b):
    """Solid fill one strip."""
    for y in range(y0, y0 + STRIP_H):
        for x in range(W):
            base = (y * W + x) * 4
            buf.data[base]=r; buf.data[base+1]=g; buf.data[base+2]=b; buf.data[base+3]=255


def _gradient_strip(buf, y0, r0,g0,b0, r1,g1,b1):
    """Horizontal gradient fill."""
    for y in range(y0, y0 + STRIP_H):
        t = (y - y0) / max(STRIP_H - 1, 1)
        r = int(r0 + t*(r1-r0)); g = int(g0 + t*(g1-g0)); b = int(b0 + t*(b1-b0))
        for x in range(W):
            base = (y * W + x) * 4
            buf.data[base]=r; buf.data[base+1]=g; buf.data[base+2]=b; buf.data[base+3]=255


def _label(buf, y0, label, status=""):
    """Label a strip. status= '' | 'OK' | 'NEEDS TUNING'"""
    col = (240, 240, 240)
    text(buf, 6, y0 + 4, label, colour=col)
    if status:
        sc = (100, 220, 100) if status == "OK" else (220, 120, 100)
        text(buf, W - 130, y0 + 4, status, colour=sc)


def _divider(buf, y0):
    """1px dark divider between strips."""
    for x in range(W):
        base = (y0 * W + x) * 4
        buf.data[base]=30; buf.data[base+1]=30; buf.data[base+2]=30; buf.data[base+3]=255


# ---------------------------------------------------------------------------
# Individual strip renders
# ---------------------------------------------------------------------------

def strip_sky_clear(buf, registry, y0, seed=10):
    """
    Sky: vertical gradient light blue top to pale horizon.
    No texture. Answer: reads as sky by colour alone.
    """
    _gradient_strip(buf, y0, 100, 160, 220,  210, 225, 240)
    _label(buf, y0, "1. SKY CLEAR  gradient only, no marks")


def strip_sky_haze(buf, registry, y0, seed=20):
    """
    Sky with atmosphere: same gradient, then sparse horizontal charcoal
    at very low pressure and large radius. Reads as streaky high cloud.
    """
    _gradient_strip(buf, y0, 95, 152, 215,  200, 220, 238)
    charcoal = build(registry, "charcoal_grain")
    if charcoal:
        br = (charcoal.shape.width or 64) / 2.0
        sp = charcoal.shape.spacing_pct
        s = seed
        for row in range(3):
            s = _lcg(s + row * 97)
            y_pos = y0 + 12 + row * 18
            pts = [(x, y_pos + math.sin(x * 0.04) * 3) for x in range(0, W, 3)]
            evs = stroke_to_events(pts, spacing_pct=sp * 2.0, base_radius=br * 0.6,
                                    pressure=0.12, seed=s)
            for idx, ev in enumerate(evs):
                stamp_blended(buf, charcoal, ev, idx, (200, 215, 235), "screen")
    _label(buf, y0, "2. SKY HAZE  charcoal @ 0.12 pressure screen")


def strip_water_deep(buf, registry, y0, seed=30):
    """
    Deep water: dark blue-green fill, horizontal charcoal ripples in screen.
    Charcoal at low pressure = soft round ghosts = underwater shapes.
    """
    _gradient_strip(buf, y0, 18, 42, 88,  22, 55, 105)
    charcoal = build(registry, "charcoal_grain")
    if charcoal:
        br = (charcoal.shape.width or 64) / 2.0
        sp = charcoal.shape.spacing_pct
        s = seed
        for row in range(4):
            s = _lcg(s + row * 113)
            y_pos = y0 + 8 + row * 14
            x_off = int(_lcg_f(s) * 60)
            pts = [(x, y_pos + math.sin((x + x_off) * 0.06) * 4)
                   for x in range(0, W, 3)]
            evs = stroke_to_events(pts, spacing_pct=sp * 1.5, base_radius=br * 0.55,
                                    pressure=0.28, seed=s + row)
            # Ripple colour: slightly lighter blue
            ripple_col = (int(80 + row * 10), int(130 + row * 8), int(180 + row * 6))
            for idx, ev in enumerate(evs):
                stamp_blended(buf, charcoal, ev, idx, ripple_col, "screen")
    _label(buf, y0, "3. WATER DEEP  charcoal ripples @ 0.28p screen")


def strip_water_shallow(buf, registry, y0, seed=40):
    """
    Shallow water: lighter blue-green, bristle strokes for choppy surface.
    Shorter marks, higher pressure than deep = more visible texture.
    """
    _gradient_strip(buf, y0, 35, 95, 130,  55, 130, 160)
    bristle = build(registry, "bristle_rake")
    if bristle:
        br = bristle.shape.radius or 32 if bristle.shape else 32
        sp = bristle.shape.spacing_pct
        s = seed
        for row in range(5):
            s = _lcg(s + row * 79)
            y_pos = y0 + 6 + row * 11
            x_start = int(_lcg_f(s) * 80)
            pts = [(x_start + x, y_pos + math.sin(x * 0.08) * 2)
                   for x in range(0, W - x_start, 2)]
            evs = stroke_to_events(pts, spacing_pct=sp, base_radius=br * 0.4,
                                    pressure=0.35, seed=s + row)
            for idx, ev in enumerate(evs):
                stamp_blended(buf, bristle, ev, idx, (140, 190, 210), "screen")
    _label(buf, y0, "4. WATER SHALLOW  bristle @ 0.35p screen")


def strip_foam_edge(buf, registry, y0, seed=50):
    """
    Foam/surf: dark wet sand base, irregular white bristle broken line.
    Hard pixel for foam dots. Reads as broken surf edge.
    """
    _gradient_strip(buf, y0, 90, 82, 60,  110, 100, 72)
    bristle = build(registry, "bristle_rake")
    pixel_r = build(registry, "hard_pixel")
    if bristle:
        br = bristle.shape.radius or 32 if bristle.shape else 32
        sp = bristle.shape.spacing_pct
        s = seed
        # Main foam line — mid-strip, broken into segments
        foam_y = y0 + STRIP_H // 2
        seg_len = 80
        n_segs = 7
        for seg in range(n_segs):
            s = _lcg(s + seg * 83)
            if _lcg_f(s) > 0.75:   # 25% of segments missing = broken foam
                continue
            s = _lcg(s)
            x_start = int(_lcg_f(s) * (W - seg_len))
            pts = [(x_start + x, foam_y + math.sin(x * 0.12) * 3)
                   for x in range(0, seg_len, 2)]
            evs = stroke_to_events(pts, spacing_pct=sp * 0.5, base_radius=br * 0.3,
                                    pressure=0.65, seed=s + seg)
            for idx, ev in enumerate(evs):
                stamp_recipe(buf, bristle, ev, idx, (220, 222, 225))
    # Foam dots above/below line
    if pixel_r:
        s2 = seed + 300
        for _ in range(80):
            s2 = _lcg(s2)
            fx = int(_lcg_f(s2) * W)
            s2 = _lcg(s2)
            fy = y0 + STRIP_H//2 - 8 + int(_lcg_f(s2) * 16)
            s2 = _lcg(s2)
            if _lcg_f(s2) > 0.6:
                ev = StrokeEvent(float(fx), float(fy), 0.8, 0.5, random_seed=s2)
                stamp_recipe(buf, pixel_r, ev, 0, (210, 215, 218))
    _label(buf, y0, "5. FOAM EDGE  broken bristle + pixel dots")


def strip_wet_sand(buf, registry, y0, seed=60):
    """
    Wet sand: dark warm tan, fine bristle grain, slight sheen in screen.
    Should read as compressed damp sand.
    """
    _gradient_strip(buf, y0, 130, 108, 68,  115, 95, 58)
    bristle = build(registry, "bristle_rake")
    if bristle:
        br = bristle.shape.radius or 32 if bristle.shape else 32
        sp = bristle.shape.spacing_pct
        s = seed
        # Horizontal grain passes — fine, low pressure
        for row in range(6):
            y_pos = y0 + 5 + row * 9
            pts = [(x, y_pos + math.sin(x * 0.015) * 1.5) for x in range(0, W, 2)]
            evs = stroke_to_events(pts, spacing_pct=sp, base_radius=br * 0.25,
                                    pressure=0.22, seed=s + row * 17)
            for idx, ev in enumerate(evs):
                stamp_recipe(buf, bristle, ev, idx, (100, 84, 50))
        # Sheen pass — screen blend, lighter
        for row in range(2):
            y_pos = y0 + 20 + row * 22
            pts = [(x, y_pos + math.sin(x * 0.025) * 2) for x in range(0, W, 3)]
            evs = stroke_to_events(pts, spacing_pct=sp * 2.0, base_radius=br * 0.3,
                                    pressure=0.18, seed=s + 500 + row)
            for idx, ev in enumerate(evs):
                stamp_blended(buf, bristle, ev, idx, (175, 160, 110), "screen")
    _label(buf, y0, "6. WET SAND  bristle grain + screen sheen")


def strip_dry_sand(buf, registry, y0, seed=70):
    """
    Dry sand: warm light tan, loose scattered bristle, occasional pixel.
    Should feel airy and granular vs wet sand's compressed look.
    """
    _gradient_strip(buf, y0, 195, 170, 98,  210, 185, 112)
    bristle = build(registry, "bristle_rake")
    pixel_r = build(registry, "hard_pixel")
    if bristle:
        br = bristle.shape.radius or 32 if bristle.shape else 32
        sp = bristle.shape.spacing_pct
        s = seed
        # Loose scattered strokes — short segments, gaps between
        n_segs = 14
        for seg in range(n_segs):
            s = _lcg(s + seg * 61)
            seg_len = int(30 + _lcg_f(s) * 80)
            s = _lcg(s)
            x_s = int(_lcg_f(s) * (W - seg_len))
            s = _lcg(s)
            y_pos = y0 + 8 + int(_lcg_f(s) * (STRIP_H - 16))
            pts = [(x_s + x, y_pos + math.sin(x * 0.04) * 2) for x in range(0, seg_len, 2)]
            evs = stroke_to_events(pts, spacing_pct=sp, base_radius=br * 0.22,
                                    pressure=0.20, seed=s + seg)
            for idx, ev in enumerate(evs):
                stamp_recipe(buf, bristle, ev, idx, (168, 145, 82))
    if pixel_r:
        s2 = seed + 600
        for _ in range(120):
            s2 = _lcg(s2)
            fx = int(_lcg_f(s2) * W)
            s2 = _lcg(s2)
            fy = y0 + 4 + int(_lcg_f(s2) * (STRIP_H - 8))
            s2 = _lcg(s2)
            bright = int(155 + _lcg_f(s2) * 40)
            ev = StrokeEvent(float(fx), float(fy), 0.7, 0.5, random_seed=s2)
            stamp_recipe(buf, pixel_r, ev, 0, (bright, int(bright*0.88), int(bright*0.55)))
    _label(buf, y0, "7. DRY SAND  loose bristle + pixel grain")


def strip_grass_tufts(buf, registry, y0, seed=80):
    """
    Coastal grass: dark green single stamps using foliage bundles
    at SMALL scale (max 30% cell), sparse, in lower half of strip.
    No strokes — single stamp placement only.
    """
    _fill_strip(buf, y0, 48, 58, 30)
    bundles_to_try = ["Grass", "Vegetation 02", "Chalk 01"]
    s = seed
    for bi, name in enumerate(bundles_to_try):
        b = registry.variant_bundles.get(name)
        if not b: continue
        from brush_models_mr import BrushShapeAsset
        n_stamps = 12
        for si in range(n_stamps):
            s = _lcg(s + si * 71 + bi * 211)
            fx = int(_lcg_f(s) * W)
            s = _lcg(s)
            fy = y0 + STRIP_H // 2 + int(_lcg_f(s) * (STRIP_H // 2 - 4))
            s = _lcg(s)
            # KEY: cap at 25-30% to keep stamps brush-like not block-like
            scale = 0.18 + _lcg_f(s) * 0.12
            cell_idx = si % len(b.cells)
            cell = b.cells[cell_idx]
            shape = BrushShapeAsset(
                name=cell.name, source_format="gih", shape_kind="bitmap",
                radius=None, aspect=None, hardness=None, shape_type=None,
                spikes=None, angle=None,
                width=cell.width, height=cell.height, depth=cell.depth,
                bitmap_path=cell.bitmap_path, spacing_pct=1.0,
            )
            pixels = _load_bitmap(shape)
            mods = DynamicsModifiers(opacity=0.80, size_scale=scale)
            _render_bitmap(buf, float(fx), float(fy), shape, mods,
                           28 + bi*6, 62 + bi*4, 18 + bi*3, pixels)
    _label(buf, y0, "8. GRASS TUFTS  single stamps 18-30% scale")


def strip_rock_face(buf, registry, y0, seed=90):
    """
    Rock/driftwood: grey base, vertical hatch strokes SHORT and clipped,
    charcoal grain for surface texture. Reads as rough stone or weathered wood.
    Hatch strokes are SHORT SEGMENTS (80px max) — not full-width bleeds.
    """
    _gradient_strip(buf, y0, 78, 75, 72,  62, 60, 58)
    charcoal = build(registry, "charcoal_grain")
    hatch    = build(registry, "hatch_texture")
    if hatch:
        # Hatch: short vertical segments clustered in patches
        br = (hatch.shape.width or 128) / 2.0
        sp = hatch.shape.spacing_pct
        s = seed
        # Rock patches — 3 clusters, not full-width
        for patch in range(4):
            s = _lcg(s + patch * 131)
            patch_cx = int(_lcg_f(s) * (W - 120)) + 60
            s = _lcg(s)
            n_strokes = int(3 + _lcg_f(s) * 4)
            for st in range(n_strokes):
                s = _lcg(s + st * 43)
                sx = patch_cx + int((_lcg_f(s) - 0.5) * 80)
                # Vertical strokes — NOT horizontal spans
                pts = [(sx + math.sin(j * 0.3) * 4,
                        y0 + 4 + j * (STRIP_H - 8) // 8)
                       for j in range(9)]
                evs = stroke_to_events(pts, spacing_pct=sp * 0.7,
                                        base_radius=max(br * 0.18, 4),
                                        pressure=0.55, seed=s + st)
                for idx, ev in enumerate(evs):
                    stamp_recipe(buf, hatch, ev, idx, (50, 48, 45))
    if charcoal:
        br2 = (charcoal.shape.width or 64) / 2.0
        sp2 = charcoal.shape.spacing_pct
        s2 = seed + 700
        for row in range(4):
            y_pos = y0 + 8 + row * 14
            pts = [(x, y_pos + math.sin(x * 0.03) * 2) for x in range(0, W, 4)]
            evs = stroke_to_events(pts, spacing_pct=sp2 * 1.2, base_radius=br2 * 0.4,
                                    pressure=0.30, seed=s2 + row)
            for idx, ev in enumerate(evs):
                stamp_recipe(buf, charcoal, ev, idx, (55, 52, 50))
    _label(buf, y0, "9. ROCK/DRIFTWOOD  short vertical hatch + charcoal")


# ---------------------------------------------------------------------------
# Assemble sheet
# ---------------------------------------------------------------------------

def build_sheet(registry: AssetRegistry) -> SurfaceBuffer:
    buf = SurfaceBuffer.blank(W, H)

    # Header
    for y in range(24):
        for x in range(W):
            base = (y * W + x) * 4
            buf.data[base]=18; buf.data[base+1]=18; buf.data[base+2]=22; buf.data[base+3]=255
    text(buf, 6, 6, "TRIXEL BEACH MATERIAL VOCABULARY  640x64 per strip", colour=(180,180,200))

    strips = [
        strip_sky_clear,
        strip_sky_haze,
        strip_water_deep,
        strip_water_shallow,
        strip_foam_edge,
        strip_wet_sand,
        strip_dry_sand,
        strip_grass_tufts,
        strip_rock_face,
    ]

    for i, fn in enumerate(strips):
        y0 = 24 + i * STRIP_H
        fn(buf, registry, y0, seed=10 * (i + 1))
        _divider(buf, y0 + STRIP_H - 1)

    return buf


# ---------------------------------------------------------------------------
# Entry
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import time

    gimp_root = Path(sys.argv[1]) if len(sys.argv) > 1 else _find_gimp_data()
    out_path  = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/tmp/beach_material_sheet.png")

    if gimp_root is None:
        print("Could not find GIMP data. Pass path as argument.")
        sys.exit(1)

    print(f"GIMP root: {gimp_root}")
    print(f"Output:    {out_path}")

    t0 = time.time()
    print("Loading assets...", end=" ", flush=True)
    registry = AssetRegistry()
    for sub in ("brushes", "dynamics", "palettes"):
        p = gimp_root / sub
        if p.exists():
            registry.load_from_directory(p)
    s = registry.summary()
    print(f"shapes={s['shapes']} errors={s['errors']}")

    print("Building material sheet...")
    buf = build_sheet(registry)

    print("Saving...", end=" ", flush=True)
    save_png(buf, out_path)
    print(f"done  ({time.time()-t0:.1f}s)")
    print(f"\n✓  {out_path}  ({W}x{H})")
    print()
    print("Read each strip:")
    print("  PASS = strip reads as its material without reading the label")
    print("  FAIL = strip reads as 'debug marks' or 'brush test'")
    print("  Fix failing strips before building the beach scene.")
