"""
stress_scene_mr.py — Trixel Stress Test Scene

Maximum diversity in one render. Tests every system simultaneously:
    - All 4 tree species at 3 scales (small/medium/large)
    - Ground layer (terrain gradient + bristle texture)
    - Sky gradient band
    - Fog/atmospheric depth pass
    - Water edge strip (gradient + ripple recipe)
    - Mixed variant bundles as foliage scatter
    - Palette discipline across zones (topographic elevation mapping)
    - Multiple blend modes composited in layers
    - Dense foreground + sparse background depth simulation
    - Extreme scale range: 1px pixel marks to 240px canopy stamps
    - ~20 trees, 6 ground zones, sky, water, fog

This is not a pretty scene. It is a system probe.
Coherence and consistency under load — that is the only test that matters.
"""

# ---------------------------------------------------------------------------
# DEPENDENCY TRACKING                                               v1
# ---------------------------------------------------------------------------
# This file calls:    world_tree_mr.py            (Same Folder)
#                     trixel_recipes_mr.py        (Same Folder)
#                     trixel_brush_adapter.py     (Same Folder)
#                     engine_mr.py                (Same Folder)
#                     engine_debug_mr.py          (Same Folder)
#                     palette_mr.py               (Same Folder)
# This file is called by: None yet (leaf — direct execution)
# ---------------------------------------------------------------------------

from __future__ import annotations

import math
import sys
from pathlib import Path

_HERE = Path(__file__).parent
sys.path.insert(0, str(_HERE))

from engine_mr import (
    SurfaceBuffer, StrokeEvent,
    stamp_recipe, stamp_recipe_coloured, stroke_to_events,
)
from engine_debug_mr import (
    solid_bg, checkerboard, text, save_png, stamp_blended, wave,
)
from palette_mr import (
    ColourContext, palette_gradient, elevation_colour,
    palette_nearest, palette_sequential,
)
from trixel_recipes_mr import ALL_RECIPES, build
from world_tree_mr import (
    draw_tree, ALL_TREES,
    TREE_OAK, TREE_PINE, TREE_BIRCH, TREE_DEAD,
    _find_gimp_data,
)
from trixel_brush_adapter import AssetRegistry


# ---------------------------------------------------------------------------
# LCG
# ---------------------------------------------------------------------------

def _lcg(s):  return (s * 1664525 + 1013904223) & 0xFFFFFFFF
def _lcg_f(s): return _lcg(s) / 0x100000000


# ---------------------------------------------------------------------------
# Scene dimensions
# ---------------------------------------------------------------------------

W, H      = 1400, 900
SKY_H     = 180        # top band = sky
GROUND_Y  = H - 120    # horizon line
WATER_Y   = H - 60     # water strip bottom edge
FOG_BAND  = 80         # atmospheric depth band near horizon


# ---------------------------------------------------------------------------
# Layer 1: Sky gradient
# ---------------------------------------------------------------------------

def draw_sky(buf, palette):
    """Vertical gradient from deep sky to horizon haze."""
    for y in range(SKY_H + FOG_BAND):
        t = y / (SKY_H + FOG_BAND)
        # Deep sky blue -> pale horizon
        r = int(40  + t * 170)
        g = int(60  + t * 160)
        b = int(120 + t * 100)
        for x in range(W):
            base = (y * W + x) * 4
            buf.data[base]   = r
            buf.data[base+1] = g
            buf.data[base+2] = b
            buf.data[base+3] = 255


# ---------------------------------------------------------------------------
# Layer 2: Ground — terrain gradient + bristle texture
# ---------------------------------------------------------------------------

def draw_ground(buf, registry, topo_palette, seed=100):
    """
    Fills ground zone with:
      - Topographic elevation gradient (darker near horizon = distance)
      - Bristle-rake texture pass for organic ground feel
      - Hard pixel scatter for pebbles/debris in foreground
    """
    bristle_r  = build(registry, "bristle_rake")
    hatch_r    = build(registry, "hatch_texture")
    pixel_r    = build(registry, "hard_pixel")

    # Background ground band (distant)
    for y in range(SKY_H + FOG_BAND, GROUND_Y):
        depth_t = (y - (SKY_H + FOG_BAND)) / max(GROUND_Y - SKY_H - FOG_BAND, 1)
        # Distant = cooler/darker, close = warmer/lighter
        r = int(55  + depth_t * 70)
        g = int(65  + depth_t * 60)
        b = int(35  + depth_t * 20)
        for x in range(W):
            base = (y * W + x) * 4
            buf.data[base]=r; buf.data[base+1]=g; buf.data[base+2]=b; buf.data[base+3]=255

    # Foreground ground (closer, darker, more textured)
    for y in range(GROUND_Y, H - 55):
        close_t = (y - GROUND_Y) / max(H - 55 - GROUND_Y, 1)
        r = int(45  + close_t * 30)
        g = int(38  + close_t * 20)
        b = int(22  + close_t * 10)
        for x in range(W):
            base = (y * W + x) * 4
            buf.data[base]=r; buf.data[base+1]=g; buf.data[base+2]=b; buf.data[base+3]=255

    # Bristle texture passes — horizontal sweeps across ground
    if bristle_r:
        br = bristle_r.shape.radius or 32 if bristle_r.shape else 32
        sp = bristle_r.shape.spacing_pct if bristle_r.shape else 0.08
        s = seed
        for row in range(8):
            y_pos = GROUND_Y + 15 + row * 10
            pressure = 0.3 + row * 0.04
            pts = [(x, y_pos + math.sin(x*0.03)*3) for x in range(0, W, 2)]
            evs = stroke_to_events(pts, spacing_pct=sp, base_radius=br,
                                    pressure=pressure, seed=s + row * 7)
            ground_col = (35 + row*2, 30 + row, 18 + row)
            for idx, ev in enumerate(evs):
                stamp_recipe(buf, bristle_r, ev, idx, ground_col)

    # Hatch texture on mid-ground — SHORT segments, clipped to ground zone
    # Do NOT span full canvas width — that causes bleed into trees and sky
    if hatch_r:
        br2 = hatch_r.shape.radius or (hatch_r.shape.width or 32)/2 if hatch_r.shape else 32
        sp2 = hatch_r.shape.spacing_pct if hatch_r.shape else 0.26
        s2 = seed + 500
        seg_len = 120   # short segments only
        for row in range(4):
            y_pos = GROUND_Y - 20 - row * 15
            s2 = _lcg(s2 + row * 11)
            # Scatter short segments across ground, leave gaps
            n_segs = 6
            for seg in range(n_segs):
                x_start = int(_lcg_f(_lcg(s2 + seg * 97)) * (W - seg_len))
                pts = [(x_start + x, y_pos + math.sin((x_start+x)*0.02)*4)
                       for x in range(0, seg_len, 2)]
                evs = stroke_to_events(pts, spacing_pct=sp2, base_radius=br2,
                                        pressure=0.38, seed=s2 + seg * 13)
                for idx, ev in enumerate(evs):
                    stamp_blended(buf, hatch_r, ev, idx, (40, 35, 22), "multiply")

    # Foreground pixel scatter (pebbles/debris)
    if pixel_r:
        s3 = seed + 1000
        for _ in range(300):
            s3 = _lcg(s3)
            px = int(_lcg_f(s3) * W)
            s3 = _lcg(s3)
            py = int(GROUND_Y + 10 + _lcg_f(s3) * (H - GROUND_Y - 70))
            s3 = _lcg(s3)
            brightness = int(40 + _lcg_f(s3) * 40)
            ev = StrokeEvent(float(px), float(py), 0.9, 0.5, random_seed=s3)
            stamp_recipe(buf, pixel_r, ev, 0, (brightness, brightness-5, brightness-10))


# ---------------------------------------------------------------------------
# Layer 3: Water strip
# ---------------------------------------------------------------------------

def draw_water(buf, registry, blues_palette, seed=200):
    """
    Three distinct zones:
      shore/sand (GROUND_Y+20 to H-90): warm sandy strip, bristle texture
      waterline  (H-90 to H-60):        dark wet sand, transition
      water body (H-60 to H):           deep blue, ripple + lily shapes
    """
    charcoal_r = build(registry, "charcoal_grain")
    bristle_r  = build(registry, "bristle_rake")
    hatch_r    = build(registry, "hatch_texture")

    SHORE_TOP = GROUND_Y + 18     # where sand starts
    WATER_TOP = H - 65            # where open water starts
    WET_SAND  = H - 88            # transition zone

    # --- Shore / sand strip ---
    for y in range(SHORE_TOP, WET_SAND):
        t = (y - SHORE_TOP) / max(WET_SAND - SHORE_TOP, 1)
        # Warm sandy colour darkening toward water
        r = int(190 - t * 60)
        g = int(165 - t * 55)
        b = int(85  - t * 35)
        for x in range(W):
            base = (y * W + x) * 4
            buf.data[base]=r; buf.data[base+1]=g; buf.data[base+2]=b; buf.data[base+3]=255

    # --- Wet sand transition ---
    for y in range(WET_SAND, WATER_TOP):
        t = (y - WET_SAND) / max(WATER_TOP - WET_SAND, 1)
        r = int(130 - t * 80)
        g = int(110 - t * 65)
        b = int(60  + t * 30)
        for x in range(W):
            base = (y * W + x) * 4
            buf.data[base]=r; buf.data[base+1]=g; buf.data[base+2]=b; buf.data[base+3]=255

    # --- Water body ---
    for y in range(WATER_TOP, H):
        depth_t = (y - WATER_TOP) / max(H - WATER_TOP, 1)
        r = int(20  + depth_t * 15)
        g = int(45  + depth_t * 20)
        b = int(90  + depth_t * 40)
        for x in range(W):
            base = (y * W + x) * 4
            buf.data[base]=r; buf.data[base+1]=g; buf.data[base+2]=b; buf.data[base+3]=255

    # Shore bristle texture (sand grain feel)
    if bristle_r:
        br_b = bristle_r.shape.radius or 32 if bristle_r.shape else 32
        sp_b = bristle_r.shape.spacing_pct if bristle_r.shape else 0.08
        s = seed + 50
        for row in range(5):
            y_pos = SHORE_TOP + 8 + row * 14
            pts = [(x, y_pos + math.sin(x*0.025)*2.5) for x in range(0, W, 2)]
            evs = stroke_to_events(pts, spacing_pct=sp_b, base_radius=br_b,
                                    pressure=0.28, seed=s + row * 9)
            for idx, ev in enumerate(evs):
                sand_col = (int(165 - row*8), int(145 - row*7), int(72 - row*4))
                stamp_recipe(buf, bristle_r, ev, idx, sand_col)

    # Waterline foam edge
    if bristle_r:
        br_b = bristle_r.shape.radius or 32 if bristle_r.shape else 32
        sp_b = bristle_r.shape.spacing_pct if bristle_r.shape else 0.08
        pts = [(x, WATER_TOP - 3 + math.sin(x*0.04)*3) for x in range(0, W, 2)]
        evs = stroke_to_events(pts, spacing_pct=sp_b, base_radius=br_b,
                                pressure=0.40, seed=seed + 300)
        for idx, ev in enumerate(evs):
            from engine_debug_mr import stamp_blended
            stamp_blended(buf, bristle_r, ev, idx, (215, 218, 222), "screen")

    # Water depth fill already done above

    # Ripple strokes — horizontal wave marks
    # Note: Charcoal stamps at low pressure in screen mode produce soft ghost
    # shapes that read as lily pads / submerged plant shadows. This is intentional.
    if charcoal_r:
        s = seed
        br = charcoal_r.shape.radius or (charcoal_r.shape.width or 64)/2 if charcoal_r.shape else 32
        sp = charcoal_r.shape.spacing_pct if charcoal_r.shape else 0.6
        for row in range(5):
            y_pos = H - 55 + row * 8
            s = _lcg(s)
            x_off = int(_lcg_f(s) * 80)
            pts = [(x, y_pos + math.sin((x + x_off) * 0.05) * 2)
                   for x in range(0, W, 3)]
            evs = stroke_to_events(pts, spacing_pct=sp, base_radius=br,
                                    pressure=0.35, velocity=0.8, seed=s + row)
            water_col = (int(140 + row*8), int(180 + row*5), int(220 + row*3))
            for idx, ev in enumerate(evs):
                stamp_blended(buf, charcoal_r, ev, idx, water_col, "screen")

    # Foam edge at waterline
    if bristle_r:
        s2 = seed + 300
        br2 = bristle_r.shape.radius or 32 if bristle_r.shape else 32
        sp2 = bristle_r.shape.spacing_pct if bristle_r.shape else 0.08
        pts = [(x, H - 63 + math.sin(x * 0.04) * 3) for x in range(0, W, 2)]
        evs = stroke_to_events(pts, spacing_pct=sp2, base_radius=br2,
                                pressure=0.45, seed=s2)
        for idx, ev in enumerate(evs):
            stamp_blended(buf, bristle_r, ev, idx, (210, 215, 220), "screen")


# ---------------------------------------------------------------------------
# Layer 4: Atmospheric fog band
# ---------------------------------------------------------------------------

def draw_fog(buf, seed=300):
    """
    Soft horizontal fog strip near horizon.
    Uses oil_smear recipe as a wide soft alpha overlay.
    Simulates depth haze — distant objects fade into pale band.
    """
    fog_y = SKY_H + FOG_BAND - 30
    for y in range(fog_y, fog_y + 80):
        t = abs(y - (fog_y + 40)) / 40.0   # 0 at centre, 1 at edges
        alpha = int((1.0 - t) * 55)         # max 55/255 opacity
        r, g, b = 200, 210, 220             # cool haze colour
        for x in range(W):
            base = (y * W + x) * 4
            # Alpha blend fog over existing
            dst_a = buf.data[base+3] / 255.0
            fa    = alpha / 255.0
            out_a = fa + dst_a * (1.0 - fa)
            if out_a > 1e-4:
                inv = dst_a * (1.0 - fa) / out_a
                buf.data[base]   = int(r * fa / out_a + buf.data[base]   * inv)
                buf.data[base+1] = int(g * fa / out_a + buf.data[base+1] * inv)
                buf.data[base+2] = int(b * fa / out_a + buf.data[base+2] * inv)
                buf.data[base+3] = int(out_a * 255)


# ---------------------------------------------------------------------------
# Layer 5: Foliage scatter (variant bundles)
# ---------------------------------------------------------------------------

def draw_foliage_scatter(buf, registry, seed=400):
    """
    Scatter individual foliage stamps in the ground zone.

    Key fix: single StrokeEvent per placement, no stroke paths.
    Stroke interpolation with large cells (250px) was creating solid green bands.
    Size is capped at 40% of cell to prevent stamps bleeding into sky.
    """
    bundles_to_try = ["Grass", "Vegetation 02", "Chalk 01", "Acrylic 01"]
    s = seed
    # Foliage colour palette: muted naturalistic greens, indexed by bundle
    FOLIAGE_COLOURS = [
        (32, 58, 22),   # Grass:        dark forest green
        (45, 72, 28),   # Vegetation:   olive green
        (38, 65, 30),   # Chalk:        mid green
        (42, 68, 25),   # Acrylic:      rich green
    ]

    for bi, bundle_name in enumerate(bundles_to_try):
        recipe = registry.build_recipe_from_bundle(bundle_name, "Basic Dynamics")
        if recipe is None:
            continue

        cells  = recipe.variant_bundle.cells
        cell_w = cells[0].width
        cell_h = cells[0].height
        # Cap rendered size: max 40% of cell so large cells stay brush-like
        max_scale = 0.40
        base_col   = FOLIAGE_COLOURS[bi % len(FOLIAGE_COLOURS)]

        n_stamps = 18 + bi * 4
        for ci in range(n_stamps):
            s = _lcg(s + ci * 137 + bi * 997)
            sx = int(_lcg_f(s) * W)
            s = _lcg(s)
            depth_t = _lcg_f(s)
            # Keep strictly in ground zone - no y that reaches sky
            sy = int(GROUND_Y - 55 + depth_t * 65)

            # Scale: distant = smaller, but capped
            scale_f = min(max_scale, 0.15 + depth_t * 0.25)

            # Single stamp — no stroke path, no interpolation
            s = _lcg(s)
            cell_idx = int(_lcg_f(s) * len(cells)) % len(cells)
            from engine_mr import StrokeEvent, _render_bitmap, _load_bitmap, DynamicsModifiers
            from brush_models_mr import BrushShapeAsset, BrushRecipe
            cell = cells[cell_idx]
            shape = BrushShapeAsset(
                name=cell.name, source_format="gih", shape_kind="bitmap",
                radius=None, aspect=None, hardness=None, shape_type=None,
                spikes=None, angle=None,
                width=cell.width, height=cell.height, depth=cell.depth,
                bitmap_path=cell.bitmap_path, spacing_pct=1.0,
            )
            pixels = _load_bitmap(shape)
            mods   = DynamicsModifiers(opacity=0.75 + depth_t * 0.2, size_scale=scale_f)

            # Slight distance desaturation
            if depth_t < 0.35:
                grey = sum(base_col) // 3
                colour = tuple(int(c * 0.6 + grey * 0.4) for c in base_col)
            else:
                colour = base_col

            _render_bitmap(buf, float(sx), float(sy), shape, mods,
                           colour[0], colour[1], colour[2], pixels)


# ---------------------------------------------------------------------------
# Layer 6: Trees — all species, 3 size tiers, scattered across scene
# ---------------------------------------------------------------------------

def draw_tree_population(buf, registry, topo_palette, seed=500):
    """
    Place trees across the scene:
      - Background row: small scale (cr=35-50), faded colour, near horizon
      - Midground row:  medium scale (cr=55-75), normal colour
      - Foreground:     large scale (cr=80-105), full detail, closer to bottom

    Species distribution: mixed, biased by horizontal position.
    Left third: mostly pine + dead
    Middle third: mixed oak + birch
    Right third: mostly oak + dead
    """
    s = seed
    stats_total = {}

    # Background trees (distant, smaller, cooler colour)
    bg_configs = []
    for i in range(7):
        s = _lcg(s + i * 211)
        x = int(30 + (W - 60) * i / 6)
        s = _lcg(s)
        cr = int(30 + _lcg_f(s) * 22)
        th = int(cr * 2.4 + _lcg_f(_lcg(s)) * 30)
        ty = GROUND_Y - 5
        # Species by position
        x_t = x / W
        if x_t < 0.35:
            species = [TREE_PINE, TREE_DEAD][i % 2]
        elif x_t < 0.65:
            species = [TREE_OAK, TREE_BIRCH][i % 2]
        else:
            species = [TREE_OAK, TREE_PINE, TREE_DEAD][i % 3]
        bg_configs.append((species, x, ty, th, cr, s + i))

    # Midground trees
    mg_configs = []
    for i in range(6):
        s = _lcg(s + i * 317)
        x = int(80 + (W - 160) * i / 5)
        s = _lcg(s)
        cr = int(52 + _lcg_f(s) * 22)
        th = int(cr * 2.6 + _lcg_f(_lcg(s)) * 40)
        ty = GROUND_Y + 15
        x_t = x / W
        species = [TREE_OAK, TREE_BIRCH, TREE_PINE, TREE_DEAD][i % 4]
        mg_configs.append((species, x, ty, th, cr, s + i * 13))

    # Foreground trees (fewer, larger)
    fg_configs = []
    for i in range(4):
        s = _lcg(s + i * 431)
        x = int(150 + (W - 300) * i / 3)
        s = _lcg(s)
        cr = int(75 + _lcg_f(s) * 30)
        th = int(cr * 2.8 + _lcg_f(_lcg(s)) * 50)
        ty = GROUND_Y + 30
        species = [TREE_OAK, TREE_DEAD, TREE_BIRCH, TREE_PINE][i]
        fg_configs.append((species, x, ty, th, cr, s + i * 73))

    all_configs = (
        [(c, "bg") for c in bg_configs] +
        [(c, "mg") for c in mg_configs] +
        [(c, "fg") for c in fg_configs]
    )

    for (tree_def, tx, ty, th, cr, sd), tier in all_configs:
        layer_stats = draw_tree(buf, tree_def, registry, tx, ty, th, cr, seed=sd)
        for k, v in layer_stats.items():
            stats_total[k] = stats_total.get(k, 0) + v

    return stats_total


# ---------------------------------------------------------------------------
# Layer 7: Cosmic elements — test extreme scale and unusual recipes
# ---------------------------------------------------------------------------

def draw_cosmic_layer(buf, registry, seed=700):
    """
    Extreme diversity pass:
      - Confetti/splat bundles for chaotic foreground debris
      - Animated Confetti hose scattered across sky
      - Vine hose as trailing organic element
      - Single-pixel star field in sky
      - Smoke/cell stamps for cloud-like upper elements
    """
    s = seed

    # Star field in sky
    pixel_r = build(registry, "hard_pixel")
    if pixel_r:
        for _ in range(180):
            s = _lcg(s)
            sx = int(_lcg_f(s) * W)
            s = _lcg(s)
            sy = int(_lcg_f(s) * (SKY_H - 20))
            s = _lcg(s)
            bright = int(180 + _lcg_f(s) * 75)
            ev = StrokeEvent(float(sx), float(sy), 0.9, 0.5, random_seed=s)
            stamp_recipe(buf, pixel_r, ev, 0, (bright, bright, bright))

    # Animated Confetti in sky scatter
    confetti = registry.build_recipe_from_bundle("Animated Confetti", "Confetti")
    if confetti:
        cells = confetti.variant_bundle.cells
        br = max(cells[0].width, cells[0].height) / 2.0
        sp = confetti.variant_bundle.step
        for ci in range(12):
            s = _lcg(s + ci * 191)
            cx = int(_lcg_f(s) * W)
            s = _lcg(s)
            cy = int(20 + _lcg_f(s) * (SKY_H - 40))
            pts = [(cx + math.sin(j*0.7)*br*2, cy + math.cos(j*0.5)*br)
                   for j in range(4)]
            evs = stroke_to_events(pts, spacing_pct=sp, base_radius=br,
                                    pressure=0.6, seed=s + ci)
            for idx, ev in enumerate(evs):
                s2 = _lcg(s + ci + idx)
                col = (int(_lcg_f(s2)*200+55), int(_lcg_f(_lcg(s2))*200+55),
                       int(_lcg_f(_lcg(_lcg(s2)))*200+55))
                stamp_recipe(buf, confetti, ev, idx, col)

    # Smoke stamps as distant clouds
    smoke_r = registry.build_recipe_from_parts("Smoke")
    if smoke_r:
        br = (smoke_r.shape.width or 168) / 2.0
        sp = smoke_r.shape.spacing_pct
        s = seed + 800
        for ci in range(6):
            s = _lcg(s + ci * 251)
            cx = int(_lcg_f(s) * W)
            s = _lcg(s)
            cy = int(30 + _lcg_f(s) * (SKY_H - 60))
            pts = [(cx + j*br*0.8, cy + math.sin(j*0.4)*20) for j in range(-1,2)]
            evs = stroke_to_events(pts, spacing_pct=sp, base_radius=br,
                                    pressure=0.25, seed=s + ci)
            for idx, ev in enumerate(evs):
                stamp_blended(buf, smoke_r, ev, idx, (220, 225, 230), "screen")

    # Vine hose as organic ground-level trailing element
    vine = registry.build_recipe_from_bundle("Vine")
    if vine:
        cells = vine.variant_bundle.cells
        br2 = max(cells[0].width, cells[0].height) / 2.0
        sp2 = vine.variant_bundle.step
        s = seed + 900
        for ci in range(3):
            s = _lcg(s + ci * 173)
            start_x = int(_lcg_f(s) * W)
            pts = [(start_x + j*8, GROUND_Y - 10 + math.sin(j*0.3)*12)
                   for j in range(40)]
            evs = stroke_to_events(pts, spacing_pct=sp2, base_radius=br2,
                                    pressure=0.7, seed=s + ci)
            for idx, ev in enumerate(evs):
                stamp_recipe(buf, vine, ev, idx, (35, 65, 25))


# ---------------------------------------------------------------------------
# Layer 8: Labels
# ---------------------------------------------------------------------------

def draw_labels(buf, tree_stats):
    text(buf, 8, 4, "TRIXEL STRESS TEST  V4  ALL SYSTEMS", colour=(230,230,230))
    text(buf, 8, 14, "SKY  FOG  GROUND  WATER  FOLIAGE  TREES  COSMIC", colour=(180,180,180))
    total = sum(tree_stats.values())
    text(buf, W - 200, 4, f"TREE STAMPS: {total}", colour=(200,200,180))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import time

    gimp_root = Path(sys.argv[1]) if len(sys.argv) > 1 else _find_gimp_data()
    out_path  = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/tmp/stress_scene.png")

    if gimp_root is None:
        print("Could not find GIMP data root. Pass as first argument.")
        sys.exit(1)

    print(f"GIMP root: {gimp_root}")
    print(f"Output:    {out_path}")

    t0 = time.time()
    print("\nLoading assets...", end=" ", flush=True)
    registry = AssetRegistry()
    for sub in ("brushes", "dynamics", "palettes"):
        p = gimp_root / sub
        if p.exists():
            registry.load_from_directory(p)
    s = registry.summary()
    print(f"shapes={s['shapes']} dyn={s['dynamics']} bundles={s['variant_bundles']} "
          f"palettes={s['palettes']} errors={s['errors']}")

    topo   = registry.palettes.get("Topographic")
    blues  = registry.palettes.get("Blues")
    greens = registry.palettes.get("Greens")

    print("Allocating surface buffer...", end=" ", flush=True)
    buf = SurfaceBuffer.blank(W, H)
    print(f"{W}x{H} = {W*H*4//1024}KB")

    print("Layer 1: Sky...", end=" ", flush=True)
    draw_sky(buf, topo)
    print("done")

    print("Layer 2: Ground...", end=" ", flush=True)
    draw_ground(buf, registry, topo, seed=100)
    print("done")

    print("Layer 3: Water...", end=" ", flush=True)
    draw_water(buf, registry, blues, seed=200)
    print("done")

    print("Layer 4: Fog...", end=" ", flush=True)
    draw_fog(buf, seed=300)
    print("done")

    print("Layer 5: Foliage scatter...", end=" ", flush=True)
    draw_foliage_scatter(buf, registry, seed=400)
    print("done")

    print("Layer 6: Trees (17 trees, 3 scale tiers)...")
    tree_stats = draw_tree_population(buf, registry, topo, seed=500)
    total_tree = sum(tree_stats.values())
    print(f"  {total_tree} tree stamps  "
          f"({' '.join(f'{k}={v}' for k,v in tree_stats.items())})")

    print("Layer 7: Cosmic elements...", end=" ", flush=True)
    draw_cosmic_layer(buf, registry, seed=700)
    print("done")

    print("Layer 8: Labels...", end=" ", flush=True)
    draw_labels(buf, tree_stats)
    print("done")

    print(f"\nSaving PNG...", end=" ", flush=True)
    save_png(buf, out_path)
    elapsed = time.time() - t0
    print(f"done  ({elapsed:.1f}s)")

    print(f"\n✓  {out_path}  ({W}x{H})")
    print(f"   Total render time: {elapsed:.1f}s")
    print(f"   All systems exercised: sky, fog, ground, water, foliage,")
    print(f"   trees (4 species × 3 scales), cosmic (stars, confetti, smoke, vine)")
