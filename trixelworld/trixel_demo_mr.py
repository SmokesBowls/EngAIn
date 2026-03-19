"""
trixel_demo_mr.py — Trixel Canonical Demo Output

Produces the official proof-of-capability output set.
Each output is deliberate, labelled, and tied to a named recipe.

This is not debug soup. It is the public proof sheet and regression witness.

Outputs (one PNG per recipe + one overview sheet):
    demo_hard_pixel.png       — crisp 1px marks at multiple pressures
    demo_hatch_texture.png    — hatch strokes building ink density
    demo_charcoal_grain.png   — grain strokes showing organic variation
    demo_bristle_rake.png     — dense bristle continuous coverage
    demo_oil_smear.png        — paint body strokes with transparency gradient
    demo_acrylic_variant.png  — acrylic hose cells with gradient colour
    demo_terrain_stroke.png   — elevation-coloured terrain strokes
    demo_overview.png         — all seven on one canonical sheet

Usage:
    python trixel_demo_mr.py [gimp_root] [output_dir]
    python trixel_demo_mr.py /usr/share/gimp/2.0 ./demo_output
"""

# ---------------------------------------------------------------------------
# DEPENDENCY TRACKING                                               v1
# ---------------------------------------------------------------------------
# This file calls:    trixel_recipes_mr.py        (Same Folder)
#                     trixel_brush_adapter.py     (Same Folder)
#                     engine_mr.py                (Same Folder)
#                     engine_debug_mr.py          (Same Folder)
#                     palette_mr.py               (Same Folder)
# This file is called by: None yet (leaf — direct execution or test runner)
# ---------------------------------------------------------------------------

from __future__ import annotations

import math
import struct
import zlib
from pathlib import Path
from typing import Optional

from engine_mr import (
    SurfaceBuffer,
    StrokeEvent,
    stamp_recipe,
    stamp_recipe_coloured,
    stroke_to_events,
)
from engine_debug_mr import (
    checkerboard,
    solid_bg,
    text,
    save_png,
    stamp_blended,
    wave,
)
from palette_mr import (
    ColourContext,
    palette_gradient,
    elevation_colour,
)
from trixel_recipes_mr import ALL_RECIPES, build, describe


# ---------------------------------------------------------------------------
# Demo rendering helpers
# ---------------------------------------------------------------------------

def _get_spacing(recipe, defn):
    """Extract base_radius and spacing from a built recipe + its definition."""
    if recipe.is_variant():
        cells  = recipe.variant_bundle.cells
        base_r = max(cells[0].width, cells[0].height) / 2.0
        spacing = recipe.variant_bundle.step
    elif recipe.shape:
        base_r  = recipe.shape.radius or (recipe.shape.width or 32) / 2.0
        spacing = recipe.shape.spacing_pct
    else:
        base_r, spacing = 10.0, 1.0
    return base_r, spacing


def _stroke_events(pts, base_r, spacing, pressure=0.85, velocity=0.7, seed=0):
    return stroke_to_events(
        pts, spacing_pct=spacing, base_radius=base_r,
        pressure=pressure, velocity=velocity, seed=seed,
    )


def _wave(W, cy, amp=30.0):
    return wave(W, cy, amp=amp)


def _render_stroke(buf, recipe, defn, pts, pressure, velocity, seed,
                   colour=(20, 20, 20), ctx=None):
    """Render a stroke with the recipe's blend mode applied."""
    if recipe is None:
        return 0
    base_r, spacing = _get_spacing(recipe, defn)
    events = _stroke_events(pts, base_r, spacing, pressure, velocity, seed)
    for idx, ev in enumerate(events):
        if ctx:
            c = ctx.next(stamp_index=idx, pressure=ev.pressure, velocity=ev.velocity,
                         elevation=max(0., min(1., (ev.position_x - 10) / (buf.width - 20))))
        else:
            c = colour
        stamp_blended(buf, recipe, ev, idx, c, defn.blend_mode)
    return len(events)


# ---------------------------------------------------------------------------
# Individual demo renderers
# ---------------------------------------------------------------------------

def demo_hard_pixel(recipe, defn, W=540, H=200) -> SurfaceBuffer:
    """
    Hard pixel: four strokes at different pressures.
    Shows that HARD_PIXEL really is crisp and pressure-invariant in shape.
    """
    buf = solid_bg(W, H, 245)
    text(buf, 8, 6, "HARD PIXEL  [no dynamics  no falloff]", colour=(40, 40, 40))

    labels = ["p=0.2", "p=0.5", "p=0.8", "p=1.0"]
    pressures = [0.2, 0.5, 0.8, 1.0]
    for i, (p, lbl) in enumerate(zip(pressures, labels)):
        cy = 50 + i * 35
        text(buf, 8, cy - 8, lbl, colour=(100, 100, 100))
        pts = [(60 + j * 6, cy) for j in range(76)]
        _render_stroke(buf, recipe, defn, pts, p, 0.5, i, colour=(20, 20, 20))
    return buf


def demo_hatch_texture(recipe, defn, W=540, H=200) -> SurfaceBuffer:
    """
    Hatch texture: three overlapping pass directions.
    Multiply blend means density builds up at intersections.
    """
    buf = solid_bg(W, H, 245)
    text(buf, 8, 6, "HATCH TEXTURE  [multiply blend  density build-up]", colour=(40, 40, 40))

    # Horizontal
    pts_h = [(30 + j * 4, 100) for j in range(116)]
    _render_stroke(buf, recipe, defn, pts_h, 0.7, 0.6, 1, colour=(30, 30, 30))
    # Diagonal up
    pts_d1 = [(30 + j * 4, 130 - j * 0.5) for j in range(116)]
    _render_stroke(buf, recipe, defn, pts_d1, 0.65, 0.6, 2, colour=(30, 30, 30))
    # Diagonal down
    pts_d2 = [(30 + j * 4, 70 + j * 0.5) for j in range(116)]
    _render_stroke(buf, recipe, defn, pts_d2, 0.6, 0.6, 3, colour=(30, 30, 30))
    return buf


def demo_charcoal_grain(recipe, defn, W=540, H=200) -> SurfaceBuffer:
    """
    Charcoal grain: pressure sweep from light to heavy.
    Shows organic grain variation driven by Pencil Generic dynamics.
    """
    buf = solid_bg(W, H, 248)
    text(buf, 8, 6, "CHARCOAL GRAIN  [pencil generic dynamics  organic variation]", colour=(40, 40, 40))

    for i in range(5):
        pressure = 0.2 + i * 0.18
        cy = 50 + i * 28
        pts = _wave(W, cy, amp=6.0)
        _render_stroke(buf, recipe, defn, pts, pressure, 0.5, i * 7, colour=(25, 20, 15))
    return buf


def demo_bristle_rake(recipe, defn, W=540, H=200) -> SurfaceBuffer:
    """
    Bristle rake: three strokes showing continuous coverage.
    Very tight native spacing (0.083) produces near-continuous texture.
    """
    buf = solid_bg(W, H, 245)
    text(buf, 8, 6, "BRISTLE RAKE  [dense overlap  continuous coverage]", colour=(40, 40, 40))

    cy_list = [70, 110, 150]
    pressures = [0.5, 0.75, 0.95]
    for i, (cy, p) in enumerate(zip(cy_list, pressures)):
        pts = _wave(W, cy, amp=8.0)
        _render_stroke(buf, recipe, defn, pts, p, 0.6, i * 13, colour=(30, 25, 20))
    return buf


def demo_oil_smear(recipe, defn, W=540, H=220) -> SurfaceBuffer:
    """
    Oil smear: wide slow strokes with a warm colour.
    Pressure gradient shows paint body building up.
    """
    buf = checkerboard(W, H, size=20, light=(230, 225, 220), dark=(210, 205, 200))
    text(buf, 8, 6, "OIL SMEAR  [pressure transparency  paint body]", colour=(50, 30, 10))

    warm = (120, 60, 20)
    for i in range(4):
        p = 0.3 + i * 0.22
        cy = 65 + i * 38
        pts = _wave(W, cy, amp=10.0)
        _render_stroke(buf, recipe, defn, pts, p, 0.4, i * 5, colour=warm)
    return buf


def demo_acrylic_variant(recipe, defn, palette, W=540, H=220) -> SurfaceBuffer:
    """
    Acrylic variant hose: gradient colour across stroke, random cell selection.
    Shows shape variation and colour discipline working together.
    """
    buf = solid_bg(W, H, 242)
    text(buf, 8, 6, "ACRYLIC VARIANT  [hose cells  gradient colour]", colour=(40, 40, 40))

    for i in range(3):
        cy = 80 + i * 45
        pts = _wave(W, cy, amp=15.0)

        if recipe is None:
            continue
        base_r, spacing = _get_spacing(recipe, defn)
        events = _stroke_events(pts, base_r, spacing, 0.8, 0.7, i * 11)
        for idx, ev in enumerate(events):
            t = max(0., min(1., (ev.position_x - 10) / (W - 20)))
            colour = palette_gradient(palette, t) if palette else (80, 80, 80)
            stamp_blended(buf, recipe, ev, idx, colour, defn.blend_mode)
    return buf


def demo_terrain_stroke(recipe, defn, palette, W=540, H=220) -> SurfaceBuffer:
    """
    Terrain colour stroke: elevation-mapped colour, parametric brush.
    Left = deep water (dark blue), right = highland (warm ochre).
    Shows palette-as-material with world-space semantics.
    """
    buf = solid_bg(W, H, 240)
    text(buf, 8, 6, "TERRAIN STROKE  [elevation colour  left=water  right=highland]",
         colour=(40, 40, 40))

    # Three passes at different elevations for variety
    configs = [
        (70,  0.1, 0.9, "shallow"),
        (120, 0.45, 0.85, "midland"),
        (165, 0.8, 0.75, "highland"),
    ]
    for cy, elev_bias, p, _ in configs:
        pts = _wave(W, cy, amp=12.0)
        if recipe is None:
            continue
        base_r, spacing = _get_spacing(recipe, defn)
        events = _stroke_events(pts, base_r, spacing, p, 0.6, hash(str(cy)) & 0xFFFF)
        for idx, ev in enumerate(events):
            # Blend x-position gradient with per-stroke elevation bias
            x_t  = max(0., min(1., (ev.position_x - 10) / (W - 20)))
            elev = elev_bias * 0.6 + x_t * 0.4    # bias + x drift
            colour = elevation_colour(palette, elev) if palette else (80, 80, 80)
            stamp_blended(buf, recipe, ev, idx, colour, defn.blend_mode)
    return buf


# ---------------------------------------------------------------------------
# Overview sheet
# ---------------------------------------------------------------------------

def make_overview(outputs: dict[str, SurfaceBuffer], output_path: Path) -> None:
    """
    Composite all individual demo outputs into one canonical overview sheet.
    Two columns, ordered by recipe type.
    """
    order = [
        "hard_pixel", "hatch_texture",
        "charcoal_grain", "bristle_rake",
        "oil_smear", "acrylic_variant",
        "terrain_stroke",
    ]
    present = [n for n in order if n in outputs]

    CELL_W = 540
    CELL_H = 220
    LABEL_H = 22
    PAD = 8
    COLS = 2
    rows = math.ceil(len(present) / COLS)

    SHEET_W = COLS * (CELL_W + PAD) + PAD
    SHEET_H = LABEL_H + rows * (CELL_H + PAD) + PAD + 16

    sheet = solid_bg(SHEET_W, SHEET_H, 230)
    text(sheet, PAD, 6, "TRIXEL CANONICAL DEMO  V1  STABLE FLOOR", colour=(40, 40, 40))

    for i, name in enumerate(present):
        col = i % COLS
        row = i // COLS
        ox  = PAD + col * (CELL_W + PAD)
        oy  = LABEL_H + row * (CELL_H + PAD) + PAD // 2

        buf = outputs[name]
        # Paste buf into sheet
        src_h = min(buf.height, CELL_H)
        src_w = min(buf.width,  CELL_W)
        for y in range(src_h):
            for x in range(src_w):
                s = (y * buf.width + x) * 4
                d = ((oy + y) * SHEET_W + (ox + x)) * 4
                if d + 3 < len(sheet.data):
                    sheet.data[d:d+4] = buf.data[s:s+4]

        # Recipe label
        defn = ALL_RECIPES.get(name)
        if defn:
            text(sheet, ox + 2, oy + src_h + 2, defn.label, colour=(60, 60, 60))

    text(sheet, PAD, SHEET_H - 10,
         "MARKS WITH JUDGMENT  TRIXEL ENGINE MR", colour=(100, 100, 100))

    save_png(sheet, output_path)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")
    from trixel_brush_adapter import AssetRegistry

    gimp_root  = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/usr/share/gimp/2.0")
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/tmp/trixel_demo")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading assets from {gimp_root}...")
    registry = AssetRegistry()
    for sub in ("brushes", "dynamics", "palettes", "patterns", "tool-presets", "gradients", "gflare"):
        p = gimp_root / sub
        if p.exists():
            registry.load_from_directory(p)

    s = registry.summary()
    print(f"  shapes={s['shapes']}  dynamics={s['dynamics']}"
          f"  palettes={s['palettes']}  bundles={s['variant_bundles']}")

    # Load palettes needed by specific demos
    topo_pal = registry.palettes.get("Topographic")

    print("\nBuilding named recipes...")
    recipes = {}
    for name in ALL_RECIPES:
        r = build(registry, name)
        recipes[name] = r
        status = "✓" if r else "✗"
        print(f"  [{status}] {name}")

    print("\nRendering demo outputs...")
    outputs: dict[str, SurfaceBuffer] = {}

    renders = [
        ("hard_pixel",       lambda: demo_hard_pixel(    recipes.get("hard_pixel"),    ALL_RECIPES["hard_pixel"])),
        ("hatch_texture",    lambda: demo_hatch_texture( recipes.get("hatch_texture"), ALL_RECIPES["hatch_texture"])),
        ("charcoal_grain",   lambda: demo_charcoal_grain(recipes.get("charcoal_grain"),ALL_RECIPES["charcoal_grain"])),
        ("bristle_rake",     lambda: demo_bristle_rake(  recipes.get("bristle_rake"),  ALL_RECIPES["bristle_rake"])),
        ("oil_smear",        lambda: demo_oil_smear(     recipes.get("oil_smear"),     ALL_RECIPES["oil_smear"])),
        ("acrylic_variant",  lambda: demo_acrylic_variant(recipes.get("acrylic_variant"), ALL_RECIPES["acrylic_variant"], topo_pal)),
        ("terrain_stroke",   lambda: demo_terrain_stroke( recipes.get("terrain_stroke"),  ALL_RECIPES["terrain_stroke"],  topo_pal)),
    ]

    for name, render_fn in renders:
        buf = render_fn()
        outputs[name] = buf
        out_path = output_dir / f"demo_{name}.png"
        save_png(buf, out_path)
        print(f"  demo_{name}.png  ({buf.width}x{buf.height})")

    print("\nRendering overview sheet...")
    overview_path = output_dir / "demo_overview.png"
    make_overview(outputs, overview_path)
    print(f"  demo_overview.png")

    # Render atmosphere flare specifically to prove Step 4.5
    print("\nRendering demonstration flare image...")
    Flare_Target = "Default"
    
    print(f"  Flared loaded: {list(registry.flares.keys())}")
    print(f"  Selected flare: {Flare_Target!r}")
    
    f = registry.flares.get(Flare_Target)
    if f:
        print(f"    Glow: radial={f.glow_radial}, angular={f.glow_angular}, size={f.glow_size}")
        print(f"    Rays: radial={f.rays_radial}, angular={f.rays_angular}, size={f.rays_size}")
        print(f"    Sec:  radial={f.sec_radial}, angular={f.sec_angular}, size={f.sec_size}")
    
    from atmosphere_mr import render_flare
    flare_buf = solid_bg(512, 512, 20)  # Deep dark blue/grey background
    render_flare(flare_buf, registry, Flare_Target, cx=256, cy=256, scale=1.5)
    flare_path = output_dir / "demo_atmosphere_flare.png"
    save_png(flare_buf, flare_path)
    print(f"  demo_atmosphere_flare.png saved to {flare_path}")

    print(f"\n✓  {len(outputs)} demos + overview + flare output written to {output_dir}")
