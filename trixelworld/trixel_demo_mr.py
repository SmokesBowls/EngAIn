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
# Dragonwayne — a gate-shrine in the Dragon Nebula
# ---------------------------------------------------------------------------

def demo_dragonwayne(registry, recipes) -> "SurfaceBuffer":
    """
    Dragonwayne: an ancient gate-shrine built into a cliff face inside
    the Dragon Nebula. Half fortress, half observatory. The structure
    reads from silhouette first: a wide arch cut into dark stone,
    flanked by two tower stubs, dragon-scale roofing on the gatehouse,
    void-lit windows, and brass trim catching nebula light.

    Layer order (back to front):
      1. Nebula background — deep void + gas wash
      2. Cliff face — sandstone-toned stone mass
      3. Gate arch — dark stone block surround
      4. Tower stubs left and right
      5. Dragon scale roofing on gatehouse
      6. Void windows (screen glow)
      7. Brass trim along arch edge and parapet
      8. Star scatter (sparse, warm brass)
      9. Foreground ground line
    """
    import math

    W, H = 720, 480
    buf = solid_bg(W, H, 8)

    # ── helpers ──────────────────────────────────────────────────────────
    def _lcg(s):  return (s * 1664525 + 1013904223) & 0xFFFFFFFF
    def _lcg_f(s): return _lcg(s) / 0x100000000

    def _fill(x0, y0, x1, y1, r, g, b):
        for y in range(max(0,y0), min(H,y1)):
            for x in range(max(0,x0), min(W,x1)):
                base = (y*W+x)*4
                buf.data[base]=r; buf.data[base+1]=g; buf.data[base+2]=b; buf.data[base+3]=255

    def _grad_v(x0,y0,x1,y1, r0,g0,b0, r1,g1,b1):
        for y in range(max(0,y0), min(H,y1)):
            t = (y-y0)/max(y1-y0,1)
            r=int(r0+t*(r1-r0)); g=int(g0+t*(g1-g0)); b=int(b0+t*(b1-b0))
            for x in range(max(0,x0), min(W,x1)):
                base=(y*W+x)*4
                buf.data[base]=r; buf.data[base+1]=g; buf.data[base+2]=b; buf.data[base+3]=255

    def _hline(y, x0, x1, r,g,b, thickness=1):
        for t in range(thickness):
            yy = y+t
            if 0<=yy<H:
                for x in range(max(0,x0), min(W,x1)):
                    base=(yy*W+x)*4
                    buf.data[base]=r; buf.data[base+1]=g; buf.data[base+2]=b

    def _vline(x, y0, y1, r,g,b, thickness=1):
        for t in range(thickness):
            xx=x+t
            if 0<=xx<W:
                for y in range(max(0,y0), min(H,y1)):
                    base=(y*W+xx)*4
                    buf.data[base]=r; buf.data[base+1]=g; buf.data[base+2]=b

    def _pixel(x,y,r,g,b):
        if 0<=x<W and 0<=y<H:
            base=(y*W+x)*4
            buf.data[base]=r; buf.data[base+1]=g; buf.data[base+2]=b

    def _strokes_clipped(recipe, x0,x1, y_start, n_rows=4, row_gap=14,
                         pressure=0.5, r_scale=0.4, seg_len=None,
                         col=(80,80,80), wave=2.0, seed=0):
        """Place strokes strictly within [x0,x1]."""
        if not recipe: return
        from engine_mr import _render_bitmap, _load_bitmap, DynamicsModifiers
        shape = recipe.shape
        if not shape: return
        pixels = _load_bitmap(shape)
        if not pixels: return
        br = (shape.radius or (shape.width or 32)/2.0) * r_scale
        sp = shape.spacing_pct
        mods = DynamicsModifiers(opacity=pressure, size_scale=r_scale)
        s = seed
        span = x1 - x0
        for row in range(n_rows):
            s = _lcg(s + row*97)
            y_pos = y_start + row*row_gap
            if seg_len:
                n_seg = max(1, span//(seg_len+8))
                for seg in range(n_seg):
                    s = _lcg(s+seg*61)
                    xs = x0 + int(_lcg_f(s)*(span-seg_len))
                    xe = min(xs+seg_len, x1)
                    pts = [(xs+x, y_pos+math.sin((xs+x)*0.05)*wave)
                           for x in range(0, xe-xs, 2)]
                    evs = stroke_to_events(pts, spacing_pct=sp, base_radius=br,
                                            pressure=pressure, seed=s+seg)
                    for idx,ev in enumerate(evs):
                        if x0<=ev.position_x<x1:
                            from engine_mr import _render_bitmap
                            _render_bitmap(buf, ev.position_x, ev.position_y,
                                           shape, mods, col[0],col[1],col[2], pixels)
            else:
                pts = [(x0+x, y_pos+math.sin((x0+x)*0.04)*wave)
                       for x in range(0, span, 2)]
                evs = stroke_to_events(pts, spacing_pct=sp, base_radius=br,
                                        pressure=pressure, seed=s)
                for idx,ev in enumerate(evs):
                    if x0<=ev.position_x<x1:
                        from engine_mr import _render_bitmap
                        _render_bitmap(buf, ev.position_x, ev.position_y,
                                       shape, mods, col[0],col[1],col[2], pixels)

    def _single_stamps(shape, x0,x1, y_min,y_max, n, scale, col, seed=0):
        if not shape: return
        from engine_mr import _render_bitmap, _load_bitmap, DynamicsModifiers
        pixels = _load_bitmap(shape)
        if not pixels: return
        mods = DynamicsModifiers(opacity=0.80, size_scale=scale)
        s = seed
        for i in range(n):
            s=_lcg(s+i*71); fx=x0+int(_lcg_f(s)*(x1-x0))
            s=_lcg(s);       fy=y_min+int(_lcg_f(s)*(y_max-y_min))
            if x0<=fx<x1:
                _render_bitmap(buf,float(fx),float(fy),shape,mods,col[0],col[1],col[2],pixels)

    nebula   = recipes.get("nebula_wash")
    brass    = recipes.get("brass_grain")
    scale_r  = recipes.get("scale_panel")
    void_r   = recipes.get("void_accent")
    stone_r  = recipes.get("charcoal_grain")
    bristle_r= recipes.get("bristle_rake")

    from engine_mr import _render_bitmap, _load_bitmap, DynamicsModifiers
    smoke_shape   = nebula.shape   if nebula  else None
    brass_shape   = brass.shape    if brass   else None
    scale_shape   = scale_r.shape  if scale_r else None
    void_shape    = void_r.shape   if void_r  else None
    stone_shape   = stone_r.shape  if stone_r else None
    bristle_shape = bristle_r.shape if bristle_r else None

    # ── 1. NEBULA BACKGROUND ─────────────────────────────────────────────
    # Deep void: near-black warm base
    _grad_v(0,0,W,H, 8,5,12, 18,10,6)

    # Gas wash — smoke stamps, screen blend, three colour layers
    if smoke_shape:
        smoke_pixels = _load_bitmap(smoke_shape)
        if smoke_pixels:
            # Layer A: deep purple-magenta nebula arm
            s=1000
            for i in range(14):
                s=_lcg(s+i*113)
                fx=int(_lcg_f(s)*W)
                s=_lcg(s); fy=int(_lcg_f(s)*(H*0.65))
                mods=DynamicsModifiers(opacity=0.22, size_scale=0.45)
                _render_bitmap(buf,float(fx),float(fy),smoke_shape,mods,
                                38,15,52,smoke_pixels)
            # Layer B: amber/orange nebula core
            s=2000
            for i in range(10):
                s=_lcg(s+i*97)
                fx=int(W*0.35+_lcg_f(s)*W*0.45)
                s=_lcg(s); fy=int(_lcg_f(s)*H*0.55)
                mods=DynamicsModifiers(opacity=0.28, size_scale=0.38)
                _render_bitmap(buf,float(fx),float(fy),smoke_shape,mods,
                                80,38,8,smoke_pixels)
            # Layer C: pale copper sheen at crown
            s=3000
            for i in range(6):
                s=_lcg(s+i*83)
                fx=int(W*0.25+_lcg_f(s)*W*0.5)
                s=_lcg(s); fy=int(_lcg_f(s)*H*0.35)
                mods=DynamicsModifiers(opacity=0.18, size_scale=0.30)
                _render_bitmap(buf,float(fx),float(fy),smoke_shape,mods,
                                120,72,28,smoke_pixels)

    # ── 2. CLIFF FACE — mass behind structure ────────────────────────────
    # Cliff body: sandstone-toned dark mass
    CLIFF_TOP = 85
    CLIFF_BTM = H
    CLIFF_L   = 45
    CLIFF_R   = W - 45
    _grad_v(CLIFF_L,CLIFF_TOP,CLIFF_R,CLIFF_BTM, 42,36,28, 28,24,18)

    # Cliff surface grain
    if stone_shape:
        stone_pixels = _load_bitmap(stone_shape)
        if stone_pixels:
            s=4000
            for row in range(12):
                s=_lcg(s+row*71)
                y_pos=CLIFF_TOP+10+row*30
                seg_len=90
                n_seg=5
                for seg in range(n_seg):
                    s=_lcg(s+seg*53)
                    xs=CLIFF_L+int(_lcg_f(s)*(CLIFF_R-CLIFF_L-seg_len))
                    pts=[(xs+x,y_pos+math.sin((xs+x)*0.04)*3)
                         for x in range(0,seg_len,2)]
                    evs=stroke_to_events(pts,spacing_pct=0.6,base_radius=28,
                                          pressure=0.30,seed=s+seg)
                    mods=DynamicsModifiers(opacity=0.30,size_scale=0.42)
                    for ev in evs:
                        if CLIFF_L<=ev.position_x<CLIFF_R:
                            _render_bitmap(buf,ev.position_x,ev.position_y,
                                           stone_shape,mods,25,20,14,stone_pixels)

    # ── 3. GATE STRUCTURE silhouette ─────────────────────────────────────
    # Geometry constants
    GATE_L  = 222
    GATE_R  = 498
    GATE_W  = GATE_R - GATE_L
    ARCH_Y  = 195          # arch crown y
    ARCH_BTM= 390          # arch base y (ground line)
    ARCH_CX = (GATE_L+GATE_R)//2   # 360
    ARCH_RX = (GATE_R-GATE_L)//2 - 12   # horizontal radius of arch opening
    ARCH_RY = 110          # vertical radius

    # Gate surround stone — dark block mass
    # Left jamb
    _grad_v(GATE_L,ARCH_Y-10,GATE_L+52,ARCH_BTM, 35,30,22, 22,19,14)
    # Right jamb
    _grad_v(GATE_R-52,ARCH_Y-10,GATE_R,ARCH_BTM, 35,30,22, 22,19,14)
    # Lintel / arch band
    _grad_v(GATE_L,ARCH_Y-18,GATE_R,ARCH_Y+22, 38,33,25, 30,26,18)

    # Arch opening — cut dark void into the gate mass
    # Elliptical arch opening, filled with deep void colour
    for y in range(ARCH_Y, ARCH_BTM+1):
        dy = (y - ARCH_Y) / max(ARCH_RY, 1)
        half_w = int(ARCH_RX * math.sqrt(max(0, 1 - dy*dy)))
        x_l = ARCH_CX - half_w
        x_r = ARCH_CX + half_w
        void_r_val = 6 + int((y-ARCH_Y)/(ARCH_BTM-ARCH_Y)*8)
        void_g_val = 4
        void_b_val = 2
        for x in range(max(0,x_l), min(W,x_r)):
            base=(y*W+x)*4
            buf.data[base]=void_r_val; buf.data[base+1]=void_g_val
            buf.data[base+2]=void_b_val; buf.data[base+3]=255

    # Stone texture on jambs
    if stone_shape:
        stone_pixels = _load_bitmap(stone_shape)
        if stone_pixels:
            for jamb_x0, jamb_x1 in [(GATE_L, GATE_L+52), (GATE_R-52, GATE_R)]:
                _strokes_clipped(stone_r, jamb_x0,jamb_x1, ARCH_Y, n_rows=8,
                                 row_gap=24, pressure=0.45, r_scale=0.32,
                                 seg_len=45, col=(28,24,16), seed=jamb_x0)

    # ── 4. TOWER STUBS ───────────────────────────────────────────────────
    TOW_W = 65
    TOW_H = 185
    TOW_L_X = GATE_L - TOW_W + 10
    TOW_R_X = GATE_R - 10
    TOW_TOP = ARCH_Y - TOW_H

    for tx in [TOW_L_X, TOW_R_X]:
        # Tower body
        _grad_v(tx,TOW_TOP,tx+TOW_W,ARCH_BTM, 45,38,28, 30,25,18)
        # Crenellations — 4 merlons
        merlon_w = 10; gap_w = 8
        mx = tx + 4
        while mx + merlon_w < tx + TOW_W - 4:
            _fill(mx, TOW_TOP-16, mx+merlon_w, TOW_TOP, 40,34,24)
            mx += merlon_w + gap_w
        # Tower surface grain
        if stone_shape:
            _strokes_clipped(stone_r, tx,tx+TOW_W, TOW_TOP, n_rows=6,
                             row_gap=26, pressure=0.38, r_scale=0.30,
                             seg_len=55, col=(22,18,12), seed=tx*7)
        # Brass corner trim
        _vline(tx+2, TOW_TOP, ARCH_BTM, 105,70,22, thickness=2)
        _vline(tx+TOW_W-4, TOW_TOP, ARCH_BTM, 105,70,22, thickness=2)
        _hline(TOW_TOP, tx,tx+TOW_W, 105,70,22, thickness=2)

    # ── 5. DRAGON SCALE ROOFING on gatehouse lintel ──────────────────────
    # Scale panel covers the lintel band
    SCALE_Y0 = ARCH_Y - 55
    SCALE_Y1 = ARCH_Y - 12
    SCALE_X0 = GATE_L + 52
    SCALE_X1 = GATE_R - 52
    _grad_v(SCALE_X0,SCALE_Y0,SCALE_X1,SCALE_Y1, 18,40,24, 10,28,16)

    # Scale tessellation — offset rows of arc-topped marks
    scale_w = 14; scale_h = 9
    if scale_shape:
        scale_pixels = _load_bitmap(scale_shape)
        if scale_pixels:
            for row in range((SCALE_Y1-SCALE_Y0)//scale_h+1):
                ry = SCALE_Y0 + row*scale_h
                x_shift = (scale_w//2) if row%2 else 0
                sx_ = SCALE_X0 + x_shift
                while sx_ < SCALE_X1:
                    for step in range(scale_w):
                        arc_y = ry + int((1-math.sin(step/scale_w*math.pi))*scale_h//2)
                        fx = sx_+step; fy = arc_y
                        if SCALE_X0<=fx<SCALE_X1 and SCALE_Y0<=fy<SCALE_Y1:
                            base=(fy*W+fx)*4
                            buf.data[base]=8; buf.data[base+1]=22; buf.data[base+2]=12
                    sx_ += scale_w
    # Scale surface grain via hatch
    if scale_shape:
        from engine_mr import _render_bitmap
        mods=DynamicsModifiers(opacity=0.55,size_scale=0.18)
        spx=_load_bitmap(scale_shape)
        if spx:
            s=9000
            for si in range(18):
                s=_lcg(s+si*83)
                fx=SCALE_X0+int(_lcg_f(s)*(SCALE_X1-SCALE_X0))
                s=_lcg(s); fy=SCALE_Y0+int(_lcg_f(s)*(SCALE_Y1-SCALE_Y0))
                if SCALE_X0<=fx<SCALE_X1:
                    _render_bitmap(buf,float(fx),float(fy),scale_shape,mods,
                                   6,18,10,spx)

    # ── 6. VOID WINDOWS — two per tower, one above arch ──────────────────
    windows = [
        (TOW_L_X+18, TOW_TOP+35, 26, 38),
        (TOW_L_X+18, TOW_TOP+90, 26, 38),
        (TOW_R_X+20, TOW_TOP+35, 26, 38),
        (TOW_R_X+20, TOW_TOP+90, 26, 38),
        (ARCH_CX-16, ARCH_Y-90, 32, 22),   # oculus above arch
    ]
    if void_shape:
        void_pixels = _load_bitmap(void_shape)
        for wx,wy,ww,wh in windows:
            # Window recess — dark bronze fill
            _fill(wx,wy,wx+ww,wy+wh, 5,3,1)
            # Void glow — warm amber absorption rings
            cx_=wx+ww//2; cy_=wy+wh//2
            for ring in range(1,5):
                falloff=1.0-ring/5.0
                for ang_i in range(20):
                    ang=ang_i*math.pi/10
                    rx_=int(cx_+math.cos(ang)*ring*(ww//3))
                    ry_=int(cy_+math.sin(ang)*ring*(wh//3))
                    if wx<=rx_<wx+ww and wy<=ry_<wy+wh:
                        base=(ry_*W+rx_)*4
                        buf.data[base]  =min(255,buf.data[base]  +int(55*falloff))
                        buf.data[base+1]=min(255,buf.data[base+1]+int(30*falloff))
                        buf.data[base+2]=min(255,buf.data[base+2]+int( 5*falloff))
            # Frame
            for fy in range(wy,wy+wh):
                for bx in [wx,wx+ww-1]:
                    if 0<=bx<W and 0<=fy<H:
                        base=(fy*W+bx)*4
                        buf.data[base]=88; buf.data[base+1]=58; buf.data[base+2]=18
            for fy in [wy,wy+wh-1]:
                for bx in range(wx,wx+ww):
                    if 0<=bx<W and 0<=fy<H:
                        base=(fy*W+bx)*4
                        buf.data[base]=88; buf.data[base+1]=58; buf.data[base+2]=18

    # ── 7. BRASS TRIM — arch edge, parapet lines ─────────────────────────
    # Arch keystone highlight
    BRASS = (108,72,24)
    BRASS_HI = (145,98,35)

    # Arch edge trim — trace the ellipse top
    for angle_deg in range(181):
        ang = math.radians(angle_deg)
        ex = int(ARCH_CX + ARCH_RX * math.cos(ang))
        ey = int(ARCH_Y  + ARCH_RY * math.sin(ang) * 0.3)  # flatter top
        if 0<=ex<W and 0<=ey<H:
            _pixel(ex, ey, BRASS_HI[0], BRASS_HI[1], BRASS_HI[2])
            _pixel(ex, ey-1, BRASS[0], BRASS[1], BRASS[2])

    # Parapet line across gatehouse top
    _hline(SCALE_Y0-1, GATE_L+52, GATE_R-52, BRASS[0],BRASS[1],BRASS[2], thickness=3)

    # Brass trim if shape available
    if brass_shape:
        brass_pixels=_load_bitmap(brass_shape)
        if brass_pixels:
            mods=DynamicsModifiers(opacity=0.60,size_scale=0.22)
            s=8000
            for i in range(20):
                s=_lcg(s+i*61)
                fx=GATE_L+52+int(_lcg_f(s)*(GATE_R-GATE_L-104))
                s=_lcg(s); fy=SCALE_Y0-2+int(_lcg_f(s)*4)
                if GATE_L+52<=fx<GATE_R-52:
                    _render_bitmap(buf,float(fx),float(fy),brass_shape,mods,
                                   105,68,20,brass_pixels)

    # ── 8. STAR SCATTER — warm brass, sparse ─────────────────────────────
    s=7000
    for i in range(55):
        s=_lcg(s+i*97)
        sx_=int(_lcg_f(s)*W)
        s=_lcg(s); sy_=int(_lcg_f(s)*(ARCH_Y-10))
        # Skip if inside structure silhouette
        if GATE_L<=sx_<GATE_R and sy_>=TOW_TOP: continue
        s=_lcg(s); mag=_lcg_f(s)
        core_r=min(255,int(185+mag*55)); core_g=min(255,int(118+mag*35)); core_b=int(25+mag*12)
        _pixel(sx_,sy_,core_r,core_g,core_b)
        if mag>0.5:
            for dy in [-1,0,1]:
                for dx in [-1,0,1]:
                    if abs(dx)+abs(dy)==1:
                        _pixel(sx_+dx,sy_+dy,
                               min(255,core_r-40),min(255,core_g-30),core_b)

    # ── 9. GROUND LINE + FOREGROUND ──────────────────────────────────────
    GND_Y = ARCH_BTM
    _grad_v(0,GND_Y,W,H, 22,18,12, 12,10,7)
    # Ground shadow under arch
    for x in range(ARCH_CX-ARCH_RX, ARCH_CX+ARCH_RX):
        for y in range(GND_Y, min(GND_Y+20,H)):
            t=(y-GND_Y)/19.0
            base=(y*W+x)*4
            buf.data[base]=max(0,buf.data[base]-int(12*t))
    # Parapet highlight
    _hline(GND_Y-1, GATE_L,GATE_R, 55,45,30, thickness=2)

    # Label
    text(buf, 8, 6, "DRAGONWAYNE  GATE-SHRINE  DRAGON NEBULA", colour=(108,72,24))

    return buf



# ---------------------------------------------------------------------------
# Dragonwayne top-down — playable overhead layout mockup
# ---------------------------------------------------------------------------

def demo_dragonwayne_topdown(registry, recipes) -> "SurfaceBuffer":
    """
    Dragonwayne viewed from directly above.
    A fortress compound: south gate -> entrance passage -> main courtyard ->
    inner wall + gate -> dragon-skin sanctum with raised dais.
    Left/right alcoves off the courtyard, void pits flanking them,
    brass trim marking the dais edge and gate thresholds.

    Top-down legibility rules:
      Wall tops:  dark filled rectangles, bright north/west edge (top-lit)
      Floors:     lighter textured fill
      Raised:     even lighter floor + bright perimeter line
      Pits:       dark fill + warm amber glow ring inset from edge
      Shadows:    2px dark offset south/east of every wall for thickness read
      Doors:      floor colour floods through wall gap = readable opening
    """
    import math

    W, H = 720, 680

    # ── palette ──────────────────────────────────────────────────────────
    C_VOID       = (5,   3,   8)     # background void
    C_WALL       = (32,  28,  22)    # wall top surface
    C_WALL_LIT   = (55,  48,  36)    # wall north/west highlight
    C_WALL_SHD   = (12,  10,   7)    # wall south/east shadow
    C_FLOOR      = (52,  46,  36)    # plain stone floor
    C_FLOOR_SANC = (28,  42,  26)    # sanctum dragon-skin floor base
    C_FLOOR_PASS = (46,  40,  30)    # passage floor (slightly darker)
    C_DAIS       = (68,  60,  44)    # raised dais surface
    C_DAIS_EDGE  = (105, 88,  52)    # dais perimeter highlight
    C_PIT        = (4,   2,   1)     # void pit fill
    C_PIT_GLOW   = (88,  52,  12)    # pit warm amber glow
    C_BRASS      = (108, 72,  24)    # brass trim
    C_BRASS_HI   = (148, 98,  35)    # brass highlight
    C_SCALE_RDG  = (8,   22,  12)    # dragon scale ridge line
    C_STAR_CORE  = (188, 122, 28)    # star brass core
    C_THRESHOLD  = (85,  70,  48)    # door threshold line

    # ── layout ───────────────────────────────────────────────────────────
    WALL_O = 20; WALL_I = 14
    OB_L,OB_R,OB_T,OB_B = 40,680,40,640
    GATE_S_X0,GATE_S_X1  = 315, 405
    PASS_L,PASS_R,PASS_T = 255, 465, 480
    COURT_L,COURT_R      = OB_L+WALL_O, OB_R-WALL_O
    COURT_T,COURT_B      = OB_T+WALL_O, PASS_T
    IW_Y                 = 210
    IW_L,IW_R            = COURT_L+60, COURT_R-60
    GATE_N_X0,GATE_N_X1  = 330, 390
    SANC_L,SANC_R        = IW_L, IW_R
    SANC_T,SANC_B        = OB_T+WALL_O, IW_Y
    DAIS_L,DAIS_R        = SANC_L+35, SANC_R-35
    DAIS_T,DAIS_B        = SANC_T+18, IW_Y-18
    LAL_L,LAL_R          = COURT_L, COURT_L+95
    LAL_T,LAL_B          = IW_Y+WALL_I, COURT_B-85
    LDOOR_Y0,LDOOR_Y1    = LAL_T+40, LAL_T+75
    RAL_L,RAL_R          = COURT_R-95, COURT_R
    RAL_T,RAL_B          = LAL_T, LAL_B
    RDOOR_Y0,RDOOR_Y1    = RAL_T+40, RAL_T+75
    PIT_L = (215, 307, 32)
    PIT_R = (505, 307, 32)

    buf = SurfaceBuffer.blank(W, H)

    # ── primitive helpers ────────────────────────────────────────────────
    def _fill(x0,y0,x1,y1,r,g,b):
        for y in range(max(0,y0),min(H,y1)):
            for x in range(max(0,x0),min(W,x1)):
                base=(y*W+x)*4
                buf.data[base]=r; buf.data[base+1]=g; buf.data[base+2]=b; buf.data[base+3]=255

    def _px(x,y,r,g,b):
        if 0<=x<W and 0<=y<H:
            base=(y*W+x)*4
            buf.data[base]=r; buf.data[base+1]=g; buf.data[base+2]=b

    def _hline(y,x0,x1,r,g,b,t=1):
        for tt in range(t):
            if 0<=y+tt<H:
                for x in range(max(0,x0),min(W,x1)):
                    base=((y+tt)*W+x)*4
                    buf.data[base]=r; buf.data[base+1]=g; buf.data[base+2]=b

    def _vline(x,y0,y1,r,g,b,t=1):
        for tt in range(t):
            if 0<=x+tt<W:
                for y in range(max(0,y0),min(H,y1)):
                    base=(y*W+x+tt)*4
                    buf.data[base]=r; buf.data[base+1]=g; buf.data[base+2]=b

    def _lcg(s): return (s*1664525+1013904223)&0xFFFFFFFF
    def _lcgf(s): return _lcg(s)/0x100000000

    def _wall_block(x0,y0,x1,y1):
        """Draw a wall top with lit NW edge and shadow SE."""
        _fill(x0,y0,x1,y1, C_WALL[0],C_WALL[1],C_WALL[2])
        _hline(y0, x0,x1, C_WALL_LIT[0],C_WALL_LIT[1],C_WALL_LIT[2], t=2)
        _vline(x0, y0,y1, C_WALL_LIT[0],C_WALL_LIT[1],C_WALL_LIT[2], t=2)
        _hline(y1-2, x0,x1, C_WALL_SHD[0],C_WALL_SHD[1],C_WALL_SHD[2], t=2)
        _vline(x1-2, y0,y1, C_WALL_SHD[0],C_WALL_SHD[1],C_WALL_SHD[2], t=2)

    def _floor_texture(x0,y0,x1,y1, col, shape, pixels, r_scale=0.28, pressure=0.22, seed=0):
        """Scatter stamp grain on a floor region."""
        if not shape or not pixels: return
        from engine_mr import _render_bitmap, DynamicsModifiers
        mods=DynamicsModifiers(opacity=pressure, size_scale=r_scale)
        br=(shape.radius or (shape.width or 32)/2.0)*r_scale
        sp=shape.spacing_pct
        s=seed; span_x=x1-x0; span_y=y1-y0
        n_rows=max(1,span_y//18)
        for row in range(n_rows):
            s=_lcg(s+row*97)
            y_pos=y0+8+row*18
            seg_len=min(span_x, 110)
            n_seg=max(1,span_x//(seg_len+12))
            for seg in range(n_seg):
                s=_lcg(s+seg*61)
                xs=x0+int(_lcgf(s)*(span_x-seg_len))
                xe=min(xs+seg_len,x1)
                pts=[(xs+x, y_pos+math.sin((xs+x)*0.05)*2)
                     for x in range(0,xe-xs,2)]
                evs=stroke_to_events(pts, spacing_pct=sp, base_radius=br,
                                       pressure=pressure, seed=s+seg)
                for ev in evs:
                    if x0<=ev.position_x<x1 and y0<=ev.position_y<y1:
                        _render_bitmap(buf, ev.position_x, ev.position_y,
                                       shape, mods, col[0],col[1],col[2], pixels)

    def _scale_floor(x0,y0,x1,y1):
        """Dragon-scale tessellation on floor."""
        sw=16; sh=10
        for row in range((y1-y0)//sh+1):
            ry=y0+row*sh
            xs=x0+((sw//2) if row%2 else 0)
            while xs<x1:
                for step in range(sw):
                    arc_y=ry+int((1-math.sin(step/sw*math.pi))*sh//2)
                    fx=xs+step; fy=arc_y
                    if x0<=fx<x1 and y0<=fy<y1:
                        _px(fx,fy, C_SCALE_RDG[0],C_SCALE_RDG[1],C_SCALE_RDG[2])
                xs+=sw

    def _void_pit(cx,cy,radius):
        """Circular pit with warm amber glow ring."""
        for y in range(cy-radius-4, cy+radius+5):
            for x in range(cx-radius-4, cx+radius+5):
                dist=math.sqrt((x-cx)**2+(y-cy)**2)
                if dist<=radius:
                    _px(x,y, C_PIT[0],C_PIT[1],C_PIT[2])
                elif dist<=radius+5:
                    t=1-(dist-radius)/5
                    r=int(C_PIT_GLOW[0]*t); g=int(C_PIT_GLOW[1]*t); b=int(C_PIT_GLOW[2]*t)
                    if 0<=x<W and 0<=y<H:
                        base=(y*W+x)*4
                        buf.data[base]=min(255,buf.data[base]+r)
                        buf.data[base+1]=min(255,buf.data[base+1]+g)
                        buf.data[base+2]=min(255,buf.data[base+2]+b)

    def _star_scatter(x0,y0,x1,y1, n=20, seed=0):
        """Warm brass star points."""
        s=seed
        for i in range(n):
            s=_lcg(s+i*97); fx=x0+int(_lcgf(s)*(x1-x0))
            s=_lcg(s);       fy=y0+int(_lcgf(s)*(y1-y0))
            s=_lcg(s); mag=0.4+_lcgf(s)*0.6
            cr=min(255,int(188+mag*50)); cg=min(255,int(118+mag*32)); cb=int(24+mag*10)
            _px(fx,fy,cr,cg,cb)
            if mag>0.6:
                for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                    _px(fx+dx,fy+dy,cr-45,cg-30,cb)

    # get shapes
    from engine_mr import _load_bitmap
    stone_shape  = recipes.get("charcoal_grain")
    stone_shape  = stone_shape.shape if stone_shape else None
    brist_recipe = recipes.get("bristle_rake")
    brist_shape  = brist_recipe.shape if brist_recipe else None
    stone_pixels = _load_bitmap(stone_shape) if stone_shape else None
    brist_pixels = _load_bitmap(brist_shape) if brist_shape else None

    # ── PAINT ORDER ───────────────────────────────────────────────────────
    # 1. Void background
    _fill(0,0,W,H, C_VOID[0],C_VOID[1],C_VOID[2])

    # Subtle nebula glow in background corners
    smoke_shape = recipes.get("nebula_wash")
    smoke_shape = smoke_shape.shape if smoke_shape else None
    smoke_pixels= _load_bitmap(smoke_shape) if smoke_shape else None
    if smoke_shape and smoke_pixels:
        from engine_mr import _render_bitmap, DynamicsModifiers
        mods=DynamicsModifiers(opacity=0.18, size_scale=0.55)
        for fx,fy in [(80,80),(640,80),(80,580),(640,580),(360,340)]:
            _render_bitmap(buf,float(fx),float(fy),smoke_shape,mods,42,18,55,smoke_pixels)

    # 2. Outer walls (four sides, gap at south gate)
    # North wall
    _wall_block(OB_L, OB_T, OB_R, OB_T+WALL_O)
    # South wall — left of gate
    _wall_block(OB_L, OB_B-WALL_O, GATE_S_X0, OB_B)
    # South wall — right of gate
    _wall_block(GATE_S_X1, OB_B-WALL_O, OB_R, OB_B)
    # West wall
    _wall_block(OB_L, OB_T, OB_L+WALL_O, OB_B)
    # East wall
    _wall_block(OB_R-WALL_O, OB_T, OB_R, OB_B)

    # 3. Inner wall (separating courtyard from sanctum)
    # Left section
    _wall_block(IW_L, IW_Y, GATE_N_X0, IW_Y+WALL_I)
    # Right section
    _wall_block(GATE_N_X1, IW_Y, IW_R, IW_Y+WALL_I)

    # 4. Alcove walls (east wall of left alcove, west of right)
    # Left alcove east wall (with door gap)
    _wall_block(LAL_R, LAL_T, LAL_R+WALL_I, LDOOR_Y0)
    _wall_block(LAL_R, LDOOR_Y1, LAL_R+WALL_I, LAL_B)
    _wall_block(LAL_R, LAL_B, LAL_R+WALL_I, LAL_B+WALL_I)
    _wall_block(LAL_L, LAL_T, LAL_L+WALL_I, LAL_T+WALL_I)  # alcove NW corner
    # Right alcove west wall
    _wall_block(RAL_L-WALL_I, RAL_T, RAL_L, RDOOR_Y0)
    _wall_block(RAL_L-WALL_I, RDOOR_Y1, RAL_L, RAL_B)
    _wall_block(RAL_L-WALL_I, RAL_B, RAL_L, RAL_B+WALL_I)

    # Alcove divider from inner wall top
    _wall_block(IW_L, OB_T+WALL_O, IW_L+WALL_I, IW_Y)   # left sanc wall
    _wall_block(IW_R-WALL_I, OB_T+WALL_O, IW_R, IW_Y)   # right sanc wall

    # 5. Main courtyard floor
    _fill(COURT_L,COURT_T,COURT_R,COURT_B, C_FLOOR[0],C_FLOOR[1],C_FLOOR[2])
    _floor_texture(COURT_L,COURT_T,COURT_R,COURT_B,
                   (38,32,24), stone_shape, stone_pixels, r_scale=0.32, seed=100)

    # 6. Entrance passage floor
    _fill(PASS_L,PASS_T,PASS_R,OB_B-WALL_O, C_FLOOR_PASS[0],C_FLOOR_PASS[1],C_FLOOR_PASS[2])
    _floor_texture(PASS_L,PASS_T,PASS_R,OB_B-WALL_O,
                   (35,30,20), stone_shape, stone_pixels, r_scale=0.28, seed=200)

    # 7. Sanctum floor (dragon skin)
    _fill(SANC_L,SANC_T,SANC_R,SANC_B, C_FLOOR_SANC[0],C_FLOOR_SANC[1],C_FLOOR_SANC[2])
    _scale_floor(SANC_L+WALL_I, SANC_T, SANC_R-WALL_I, SANC_B)

    # 8. Alcove floors
    _fill(OB_L+WALL_O, LAL_T, LAL_R, LAL_B, C_FLOOR[0],C_FLOOR[1],C_FLOOR[2])
    _floor_texture(OB_L+WALL_O, LAL_T, LAL_R, LAL_B,
                   (38,32,24), brist_shape, brist_pixels, r_scale=0.20, seed=300)
    _fill(RAL_L, RAL_T, OB_R-WALL_O, RAL_B, C_FLOOR[0],C_FLOOR[1],C_FLOOR[2])
    _floor_texture(RAL_L, RAL_T, OB_R-WALL_O, RAL_B,
                   (38,32,24), brist_shape, brist_pixels, r_scale=0.20, seed=400)

    # 9. Raised dais
    _fill(DAIS_L,DAIS_T,DAIS_R,DAIS_B, C_DAIS[0],C_DAIS[1],C_DAIS[2])
    # Dais edge highlight (top-lit)
    _hline(DAIS_T, DAIS_L,DAIS_R, C_DAIS_EDGE[0],C_DAIS_EDGE[1],C_DAIS_EDGE[2], t=2)
    _vline(DAIS_L, DAIS_T,DAIS_B, C_DAIS_EDGE[0],C_DAIS_EDGE[1],C_DAIS_EDGE[2], t=2)
    # Dais shadow (south/east)
    _hline(DAIS_B-2, DAIS_L,DAIS_R, 20,16,10, t=2)
    _vline(DAIS_R-2, DAIS_T,DAIS_B, 20,16,10, t=2)
    # Dais top texture + star scatter (void/star material accent)
    _floor_texture(DAIS_L+4,DAIS_T+4,DAIS_R-4,DAIS_B-4,
                   (55,48,36), stone_shape, stone_pixels, r_scale=0.25, seed=500)
    _star_scatter(DAIS_L+6, DAIS_T+6, DAIS_R-6, DAIS_B-6, n=22, seed=600)

    # 10. Void pits
    _void_pit(PIT_L[0], PIT_L[1], PIT_L[2])
    _void_pit(PIT_R[0], PIT_R[1], PIT_R[2])

    # 11. Brass trim — dais perimeter, gate thresholds, inner wall gate
    # Dais perimeter brass
    _hline(DAIS_T-1, DAIS_L-1,DAIS_R+1, C_BRASS[0],C_BRASS[1],C_BRASS[2], t=2)
    _hline(DAIS_B, DAIS_L-1,DAIS_R+1, C_BRASS[0],C_BRASS[1],C_BRASS[2], t=2)
    _vline(DAIS_L-1, DAIS_T-1,DAIS_B+2, C_BRASS[0],C_BRASS[1],C_BRASS[2], t=2)
    _vline(DAIS_R, DAIS_T-1,DAIS_B+2, C_BRASS[0],C_BRASS[1],C_BRASS[2], t=2)

    # South gate threshold
    _hline(OB_B-WALL_O, GATE_S_X0,GATE_S_X1, C_BRASS_HI[0],C_BRASS_HI[1],C_BRASS_HI[2], t=3)
    # Inner gate threshold
    _hline(IW_Y, GATE_N_X0,GATE_N_X1, C_BRASS_HI[0],C_BRASS_HI[1],C_BRASS_HI[2], t=3)
    # Left alcove door threshold
    _vline(LAL_R, LDOOR_Y0,LDOOR_Y1, C_THRESHOLD[0],C_THRESHOLD[1],C_THRESHOLD[2], t=2)
    _vline(RAL_L-2, RDOOR_Y0,RDOOR_Y1, C_THRESHOLD[0],C_THRESHOLD[1],C_THRESHOLD[2], t=2)

    # Brass corner marks on outer wall corners
    for cx,cy in [(OB_L,OB_T),(OB_R,OB_T),(OB_L,OB_B),(OB_R,OB_B)]:
        for dy in range(-3,4):
            for dx in range(-3,4):
                if abs(dx)+abs(dy)<=4:
                    _px(cx+dx,cy+dy,C_BRASS[0],C_BRASS[1],C_BRASS[2])

    # 12. Scale floor accent marks on sanctum walls
    if stone_shape and stone_pixels:
        _floor_texture(SANC_L+WALL_I, SANC_T, SANC_L+WALL_I+8, SANC_B,
                       (5,15,8), stone_shape, stone_pixels, r_scale=0.22, seed=700)
        _floor_texture(SANC_R-WALL_I-8, SANC_T, SANC_R-WALL_I, SANC_B,
                       (5,15,8), stone_shape, stone_pixels, r_scale=0.22, seed=800)

    # 13. Legend / labels
    text(buf, 6, 4, "DRAGONWAYNE  TOP-DOWN  PLAYABLE LAYOUT", colour=(108,72,24))
    text(buf, 6, H-22, "S=SANCTUM  D=DAIS  P=PIT  G=GATE  A=ALCOVE", colour=(65,55,38))

    # Zone labels
    text(buf, SANC_L+4, (SANC_T+SANC_B)//2-4, "SANCTUM", colour=(48,70,38))
    text(buf, DAIS_L+4, (DAIS_T+DAIS_B)//2-4, "DAIS", colour=(88,72,44))
    text(buf, (COURT_L+COURT_R)//2-24, (COURT_T+COURT_B)//2-4, "COURTYARD", colour=(40,35,26))
    text(buf, OB_L+WALL_O+4, (LAL_T+LAL_B)//2-4, "ALCV", colour=(40,35,26))
    text(buf, OB_R-WALL_O-40, (RAL_T+RAL_B)//2-4, "ALCV", colour=(40,35,26))
    text(buf, PIT_L[0]-10, PIT_L[1]-4, "PIT", colour=(65,38,8))
    text(buf, PIT_R[0]-10, PIT_R[1]-4, "PIT", colour=(65,38,8))
    text(buf, (PASS_L+PASS_R)//2-12, (PASS_T+OB_B-WALL_O)//2-4, "GATE", colour=(88,72,44))

    return buf

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
    for sub in ("brushes", "dynamics", "palettes"):
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

    # ── Dragonwayne scene ──────────────────────────────────────────────
    print("\nRendering Dragonwayne scene...")
    dw_recipes = {
        "nebula_wash":  build(registry, "nebula_wash"),
        "brass_grain":  build(registry, "brass_grain"),
        "scale_panel":  build(registry, "scale_panel"),
        "void_accent":  build(registry, "void_accent"),
        "charcoal_grain": build(registry, "charcoal_grain"),
        "bristle_rake": build(registry, "bristle_rake"),
    }
    dw_buf = demo_dragonwayne(registry, dw_recipes)
    dw_path = output_dir / "demo_dragonwayne.png"
    save_png(dw_buf, dw_path)
    print(f"  demo_dragonwayne.png  ({dw_buf.width}x{dw_buf.height})")

    print("Rendering Dragonwayne top-down layout...")
    dwtd_recipes = {
        "charcoal_grain": build(registry, "charcoal_grain"),
        "bristle_rake":   build(registry, "bristle_rake"),
        "nebula_wash":    build(registry, "nebula_wash"),
    }
    dwtd_buf = demo_dragonwayne_topdown(registry, dwtd_recipes)
    dwtd_path = output_dir / "demo_dragonwayne_topdown.png"
    save_png(dwtd_buf, dwtd_path)
    print(f"  demo_dragonwayne_topdown.png  ({dwtd_buf.width}x{dwtd_buf.height})")

    print("\nRendering overview sheet...")
    overview_path = output_dir / "demo_overview.png"
    make_overview(outputs, overview_path)
    print(f"  demo_overview.png")

    print(f"\n✓  {len(outputs)} demos + overview written to {output_dir}")
