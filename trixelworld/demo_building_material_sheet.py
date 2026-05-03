"""
demo_building_material_sheet.py — Trixel Building Material Atlas

A vocabulary atlas for construction surfaces.
Not a beauty piece — a system reference.

Layout: 3 columns per material row
  LEFT   (300px): base fill — colour + primary texture
  MIDDLE (300px): surface breakup — grain, variation, depth
  RIGHT  (300px): edge/seam/wear — how joints, damage, age read

Materials (16 rows):
  1.  Stone Block Wall      — cut stone, mortar joints
  2.  Rough Cliff Stone     — uncut rock, fracture planes
  3.  Brick / Masonry       — regular coursing, mortar
  4.  Plaster / Stucco      — smooth skin, crack lines
  5.  Timber Beam           — directional grain, knot marks
  6.  Plank Wall            — horizontal boards, gap seams
  7.  Roof Tile / Shingles  — overlapping courses
  8.  Weathered Wood        — grey rot, dark pockets
  9.  Sandstone / Ruin      — soft crumble, pitted surface
  10. Metal Trim / Gate     — hard edge, specular line
  11. Glass / Window        — flat fill, diagonal highlight
  12. Ground Path / Dirt    — packed earth, wheel ruts
  13. Crystal Shards        — ruby, quartz, emerald variants
  14. Star Needle           — bright point scatter, rays
  15. Void Needle           — dark absorption, cold glow
  16. Dragon Skin           — scaled tessellation, ridge shadow

Each column is STRICTLY INDEPENDENT — no recipe bleeds across column boundary.
This is the fix for the horizontal hatch bleed: every stroke path is clipped
to its column x-range.
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
from engine_debug_mr import text, save_png, stamp_blended
from trixel_recipes_mr import build
from trixel_brush_adapter import AssetRegistry
from world_tree_mr import _find_gimp_data
from brush_models_mr import BrushShapeAsset


# ---------------------------------------------------------------------------
# LCG
# ---------------------------------------------------------------------------
def _lcg(s):  return (s * 1664525 + 1013904223) & 0xFFFFFFFF
def _lcg_f(s): return _lcg(s) / 0x100000000


# ---------------------------------------------------------------------------
# Sheet geometry
# ---------------------------------------------------------------------------
COL_W    = 300     # width of each column
COLS     = 3       # base | breakup | edge/wear
LABEL_W  = 120     # left label column
W        = LABEL_W + COL_W * COLS   # 1020px total
ROW_H    = 72      # height per material row
HEADER_H = 28
N_ROWS   = 16
H        = HEADER_H + ROW_H * N_ROWS

# Column x offsets (absolute)
CX = [LABEL_W, LABEL_W + COL_W, LABEL_W + COL_W * 2]


# ---------------------------------------------------------------------------
# Drawing primitives — all CLIPPED to column bounds
# ---------------------------------------------------------------------------

def _fill_rect(buf, x0, y0, x1, y1, r, g, b):
    """Solid fill within rectangle."""
    for y in range(max(0,y0), min(H,y1)):
        for x in range(max(0,x0), min(W,x1)):
            base = (y * W + x) * 4
            buf.data[base]=r; buf.data[base+1]=g; buf.data[base+2]=b; buf.data[base+3]=255


def _gradient_rect(buf, x0, y0, x1, y1, r0,g0,b0, r1,g1,b1, vertical=True):
    for y in range(max(0,y0), min(H,y1)):
        for x in range(max(0,x0), min(W,x1)):
            t = (y-y0)/(y1-y0) if vertical else (x-x0)/(x1-x0)
            r=int(r0+t*(r1-r0)); g=int(g0+t*(g1-g0)); b=int(b0+t*(b1-b0))
            base = (y * W + x) * 4
            buf.data[base]=r; buf.data[base+1]=g; buf.data[base+2]=b; buf.data[base+3]=255


def _strokes(buf, shape, registry, cx0, cx1, y0,
             rows=4, row_gap=14, y_offset=8,
             pressure=0.5, radius_scale=1.0, spacing_scale=1.0,
             colour=(80,80,80), blend="normal",
             wave_amp=2.0, wave_freq=0.04,
             seg_len=None, seed=0, vertical=False):
    """
    Place stroke rows CLIPPED to [cx0, cx1].
    seg_len=None means full column width; otherwise short segments.
    vertical=True rotates strokes 90 degrees (for planks/beams).
    """
    s = shape
    if s is None: return
    pixels = _load_bitmap(s)
    if pixels is None: return
    br = (s.radius or (s.width or 32) / 2.0) * radius_scale
    sp = s.spacing_pct * spacing_scale
    mods = DynamicsModifiers(opacity=pressure, size_scale=radius_scale)

    lseed = seed
    col_span = cx1 - cx0

    for row in range(rows):
        lseed = _lcg(lseed + row * 97)
        if vertical:
            y_pos_start = y0 + y_offset
            y_pos_end   = y0 + ROW_H - y_offset
            x_pos = cx0 + row * (col_span // max(rows,1)) + col_span // (rows*2)
            if seg_len:
                n_segs = max(1, col_span // (seg_len + 10))
                for seg in range(n_segs):
                    lseed = _lcg(lseed + seg * 61)
                    ys = y0 + y_offset + int(_lcg_f(lseed) * (ROW_H - y_offset*2 - seg_len))
                    pts = [(x_pos + math.sin(j*0.3)*wave_amp, ys+j*(seg_len//8))
                           for j in range(9)]
                    evs = stroke_to_events(pts, spacing_pct=sp, base_radius=br,
                                            pressure=pressure, seed=lseed+seg)
                    for idx, ev in enumerate(evs):
                        if cx0 <= ev.position_x < cx1:
                            if blend == "normal":
                                _render_bitmap(buf, ev.position_x, ev.position_y,
                                               s, mods, colour[0],colour[1],colour[2], pixels)
                            else:
                                stamp_blended(buf, build_from_shape(s, registry), ev, idx, colour, blend)
            else:
                pts = [(x_pos + math.sin(j*wave_freq*8)*wave_amp,
                        y_pos_start + j*(y_pos_end-y_pos_start)//10)
                       for j in range(11)]
                evs = stroke_to_events(pts, spacing_pct=sp, base_radius=br,
                                        pressure=pressure, seed=lseed)
                for idx, ev in enumerate(evs):
                    if cx0 <= ev.position_x < cx1:
                        _render_bitmap(buf, ev.position_x, ev.position_y,
                                       s, mods, colour[0],colour[1],colour[2], pixels)
        else:
            y_pos = y0 + y_offset + row * row_gap
            if seg_len:
                n_segs = max(2, col_span // (seg_len + 8))
                for seg in range(n_segs):
                    lseed = _lcg(lseed + seg * 61)
                    xs = cx0 + int(_lcg_f(lseed) * (col_span - seg_len))
                    xe = min(xs + seg_len, cx1)
                    pts = [(xs + x, y_pos + math.sin((xs+x)*wave_freq)*wave_amp)
                           for x in range(0, xe-xs, 2)]
                    evs = stroke_to_events(pts, spacing_pct=sp, base_radius=br,
                                            pressure=pressure, seed=lseed+seg)
                    for idx, ev in enumerate(evs):
                        if cx0 <= ev.position_x < cx1:
                            _render_bitmap(buf, ev.position_x, ev.position_y,
                                           s, mods, colour[0],colour[1],colour[2], pixels)
            else:
                pts = [(cx0 + x, y_pos + math.sin((cx0+x)*wave_freq)*wave_amp)
                       for x in range(0, col_span, 2)]
                evs = stroke_to_events(pts, spacing_pct=sp, base_radius=br,
                                        pressure=pressure, seed=lseed)
                for idx, ev in enumerate(evs):
                    if cx0 <= ev.position_x < cx1:
                        _render_bitmap(buf, ev.position_x, ev.position_y,
                                       s, mods, colour[0],colour[1],colour[2], pixels)


def _single_stamps(buf, shape, cx0, cx1, y0, n=20, scale=0.25,
                   colour=(80,80,80), seed=0, opacity=0.8):
    """Place n individual stamps scattered in column, no paths."""
    if shape is None: return
    pixels = _load_bitmap(shape)
    if pixels is None: return
    mods = DynamicsModifiers(opacity=opacity, size_scale=scale)
    s = seed
    for i in range(n):
        s = _lcg(s + i * 71)
        fx = cx0 + int(_lcg_f(s) * (cx1 - cx0))
        s = _lcg(s)
        fy = y0 + 4 + int(_lcg_f(s) * (ROW_H - 8))
        if cx0 <= fx < cx1:
            _render_bitmap(buf, float(fx), float(fy), shape, mods,
                           colour[0], colour[1], colour[2], pixels)


def _bundle_stamps(buf, bundle_cells, cx0, cx1, y0, n=12, scale=0.20,
                   colour=(80,80,80), seed=0):
    """Single stamps from a variant bundle, size-capped."""
    if not bundle_cells: return
    s = seed
    for i in range(n):
        s = _lcg(s + i * 83)
        cell = bundle_cells[int(_lcg_f(s) * len(bundle_cells)) % len(bundle_cells)]
        shape = BrushShapeAsset(
            name=cell.name, source_format="gih", shape_kind="bitmap",
            radius=None, aspect=None, hardness=None, shape_type=None,
            spikes=None, angle=None,
            width=cell.width, height=cell.height, depth=cell.depth,
            bitmap_path=cell.bitmap_path, spacing_pct=1.0,
        )
        pixels = _load_bitmap(shape)
        if not pixels: continue
        s = _lcg(s)
        fx = cx0 + int(_lcg_f(s) * (cx1 - cx0))
        s = _lcg(s)
        fy = y0 + 4 + int(_lcg_f(s) * (ROW_H - 8))
        s = _lcg(s)
        sc = scale * (0.8 + _lcg_f(s) * 0.4)
        mods = DynamicsModifiers(opacity=0.75, size_scale=sc)
        if cx0 <= fx < cx1:
            _render_bitmap(buf, float(fx), float(fy), shape, mods,
                           colour[0], colour[1], colour[2], pixels)


def _mortar_lines(buf, cx0, cx1, y0, course_h=14, offset=True,
                  col=(120,115,108)):
    """Draw regular masonry coursing lines."""
    pixel_r = BrushShapeAsset(
        name="pixel", source_format="gbr", shape_kind="bitmap",
        radius=None, aspect=None, hardness=None, shape_type=None,
        spikes=None, angle=None,
        width=1, height=1, depth=1,
        bitmap_path=None, spacing_pct=1.29,
    )
    mods = DynamicsModifiers(opacity=1.0, size_scale=1.0)
    # Horizontal mortar courses
    for course in range(ROW_H // course_h + 1):
        my = y0 + course * course_h
        if my >= y0 + ROW_H: break
        for x in range(cx0, cx1):
            base = (my * W + x) * 4
            buf.data[base]=col[0]; buf.data[base+1]=col[1]; buf.data[base+2]=col[2]
    # Vertical joints — alternating offset
    for course in range(ROW_H // course_h + 1):
        my_top = y0 + course * course_h
        brick_w = 36
        shift = (brick_w // 2) if (course % 2 == 1 and offset) else 0
        bx = cx0 + shift
        while bx < cx1:
            for vy in range(my_top, min(my_top + course_h, y0 + ROW_H)):
                base = (vy * W + bx) * 4
                buf.data[base]=col[0]; buf.data[base+1]=col[1]; buf.data[base+2]=col[2]
            bx += brick_w


def _pixel_scatter(buf, cx0, cx1, y0, n=60, colour=(120,120,120),
                   bright_range=40, seed=0):
    """Scatter single pixels for grain/debris."""
    s = seed
    for _ in range(n):
        s = _lcg(s)
        fx = cx0 + int(_lcg_f(s) * (cx1 - cx0))
        s = _lcg(s)
        fy = y0 + 2 + int(_lcg_f(s) * (ROW_H - 4))
        s = _lcg(s)
        bright = int(_lcg_f(s) * bright_range)
        r = min(255, colour[0] + bright)
        g = min(255, colour[1] + bright)
        b = min(255, colour[2] + bright)
        if 0 <= fx < W and 0 <= fy < H:
            base = (fy * W + fx) * 4
            buf.data[base]=r; buf.data[base+1]=g; buf.data[base+2]=b; buf.data[base+3]=255


def _seam_line(buf, cx0, cx1, y0, y_frac=0.5, col=(60,55,50), thickness=1):
    """Horizontal seam or edge line at y_frac position in row."""
    sy = y0 + int(ROW_H * y_frac)
    for t in range(thickness):
        for x in range(cx0, cx1):
            yy = sy + t
            if 0 <= yy < H:
                base = (yy * W + x) * 4
                buf.data[base]=col[0]; buf.data[base+1]=col[1]; buf.data[base+2]=col[2]


def build_from_shape(s, registry):
    """Build a minimal recipe wrapper for stamp_blended."""
    from brush_models_mr import BrushRecipe
    return BrushRecipe(
        recipe_id=f"raw:{s.name}", shape=s,
        dynamics=None, preset=None, palette=None, variant_bundle=None,
    )


# ---------------------------------------------------------------------------
# Row label + column headers
# ---------------------------------------------------------------------------

def _row_label(buf, y0, name, num):
    """Draw row label in left panel."""
    _fill_rect(buf, 0, y0, LABEL_W, y0 + ROW_H, 22, 22, 26)
    text(buf, 4, y0 + 4, f"{num:02d}", colour=(100, 100, 120))
    # Wrap name at 14 chars
    words = name.split()
    line = ""
    ly = y0 + 18
    for w in words:
        if len(line) + len(w) + 1 > 13:
            text(buf, 4, ly, line, colour=(200, 200, 210))
            ly += 12; line = w
        else:
            line = (line + " " + w).strip()
    if line:
        text(buf, 4, ly, line, colour=(200, 200, 210))


def _col_dividers(buf, y0):
    """Vertical dividers between columns."""
    for col_x in [LABEL_W, LABEL_W+COL_W, LABEL_W+COL_W*2]:
        for y in range(y0, y0 + ROW_H):
            base = (y * W + col_x) * 4
            buf.data[base]=18; buf.data[base+1]=18; buf.data[base+2]=22; buf.data[base+3]=255
    # Bottom divider
    for x in range(W):
        base = ((y0 + ROW_H - 1) * W + x) * 4
        buf.data[base]=18; buf.data[base+1]=18; buf.data[base+2]=22; buf.data[base+3]=255


# ---------------------------------------------------------------------------
# 16 material rows
# ---------------------------------------------------------------------------

def row_stone_block(buf, r, y0, seed=100):
    C = [CX[0], CX[1], CX[2]]
    h = r.shapes.get("Hatch-Pen-01"); c1 = r.shapes.get("Charcoal-01")
    sw = r.variant_bundles.get("Stone Work 01")

    # BASE: grey stone fill with light charcoal grain
    _gradient_rect(buf, C[0],y0, C[1],y0+ROW_H, 95,92,88, 80,78,74)
    if c1: _strokes(buf, c1, r, C[0],C[1], y0, rows=3, row_gap=20,
                    pressure=0.25, radius_scale=0.5, colour=(65,62,58), seed=seed)

    # BREAKUP: stone work stamps + hatch for surface texture
    _gradient_rect(buf, C[1],y0, C[2],y0+ROW_H, 92,89,85, 78,76,72)
    if sw: _bundle_stamps(buf, sw.cells, C[1],C[2], y0, n=22, scale=0.36,
                           colour=(52,49,45), seed=seed+200)   # darker, larger
    if h: _strokes(buf, h, r, C[1],C[2], y0, rows=2, row_gap=28,
                    pressure=0.45, radius_scale=0.28, seg_len=60,
                    colour=(42,40,36), seed=seed+300)

    # EDGE/WEAR: mortar joints — HIGH CONTRAST (dark mortar on light stone)
    _gradient_rect(buf, C[2],y0, W,y0+ROW_H, 88,85,82, 72,70,66)
    _mortar_lines(buf, C[2],W, y0, course_h=16, col=(35,32,28))  # much darker mortar
    _pixel_scatter(buf, C[2],W, y0, n=40, colour=(55,52,50), seed=seed+400)
    _seam_line(buf, C[2],W, y0, y_frac=0.88, col=(40,38,35), thickness=2)


def row_rough_cliff(buf, r, y0, seed=110):
    C = [CX[0], CX[1], CX[2]]
    c2 = r.shapes.get("Charcoal-02"); ps = r.shapes.get("Pencil-Scratch")
    b1 = r.shapes.get("Bristles-01")

    # BASE: dark irregular rock
    _gradient_rect(buf, C[0],y0, C[1],y0+ROW_H, 58,54,50, 45,42,38)
    if c2: _strokes(buf, c2, r, C[0],C[1], y0, rows=4, row_gap=15,
                    pressure=0.55, radius_scale=0.35, seg_len=80,
                    colour=(38,35,32), seed=seed)

    # BREAKUP: fracture planes — LIGHT exposed rock on dark base = visible contrast
    _gradient_rect(buf, C[1],y0, C[2],y0+ROW_H, 55,52,48, 42,40,36)
    # Light fracture plane highlight (fresh-broken rock is lighter)
    if ps: _strokes(buf, ps, r, C[1],C[2], y0, rows=4, row_gap=14,
                    pressure=0.55, radius_scale=0.32, seg_len=50,
                    colour=(85,82,76), wave_amp=4.0, seed=seed+100)  # LIGHT
    if b1: _strokes(buf, b1, r, C[1],C[2], y0, rows=3, row_gap=18,
                    pressure=0.22, radius_scale=0.22, colour=(28,26,22), seed=seed+150)  # DARK
    _pixel_scatter(buf, C[1],C[2], y0, n=20, colour=(95,90,84), bright_range=20, seed=seed+180)

    # EDGE/WEAR: water stain = blue-grey tint + dark wet seams
    _gradient_rect(buf, C[2],y0, W,y0+ROW_H, 44,46,50, 32,34,38)  # blue-grey shift
    if c2: _strokes(buf, c2, r, C[2],W, y0, rows=4, row_gap=15,
                    pressure=0.60, radius_scale=0.22, seg_len=40,
                    colour=(18,20,25), wave_amp=5.0, seed=seed+200)  # near-black blue
    _pixel_scatter(buf, C[2],W, y0, n=25, colour=(62,65,72), bright_range=15, seed=seed+300)


def row_brick_masonry(buf, r, y0, seed=120):
    C = [CX[0], CX[1], CX[2]]
    c1 = r.shapes.get("Charcoal-01")

    # BASE: warm red-brown brick fill
    _fill_rect(buf, C[0],y0, C[1],y0+ROW_H, 148,78,58)
    if c1: _strokes(buf, c1, r, C[0],C[1], y0, rows=3, row_gap=20,
                    pressure=0.22, radius_scale=0.4, colour=(118,60,44), seed=seed)

    # BREAKUP: coursing + variation in brick colour
    _fill_rect(buf, C[1],y0, C[2],y0+ROW_H, 145,76,56)
    _mortar_lines(buf, C[1],C[2], y0, course_h=16, col=(155,142,128))
    if c1:
        # Brick face variation — short scattered per-brick marks
        _strokes(buf, c1, r, C[1],C[2], y0, rows=5, row_gap=12,
                 pressure=0.18, radius_scale=0.38, seg_len=28,
                 colour=(108,52,38), seed=seed+100)

    # EDGE/WEAR: spalled corners, dark mortar shadow, worn face
    _fill_rect(buf, C[2],y0, W,y0+ROW_H, 138,72,52)
    _mortar_lines(buf, C[2],W, y0, course_h=16, col=(90,80,70))
    _pixel_scatter(buf, C[2],W, y0, n=50, colour=(88,44,30), bright_range=25, seed=seed+200)
    # Shadow at base of each course
    for course in range(ROW_H // 16 + 1):
        sy = y0 + course * 16 + 14
        if sy < y0 + ROW_H:
            for x in range(C[2], W):
                base = (sy * W + x) * 4
                buf.data[base]=max(0,buf.data[base]-30)
                buf.data[base+1]=max(0,buf.data[base+1]-25)


def row_plaster_stucco(buf, r, y0, seed=130):
    C = [CX[0], CX[1], CX[2]]
    b2 = r.shapes.get("Bristles-02"); c1 = r.shapes.get("Charcoal-01")

    # BASE: pale off-white plaster
    _fill_rect(buf, C[0],y0, C[1],y0+ROW_H, 225,218,205)
    if b2: _strokes(buf, b2, r, C[0],C[1], y0, rows=5, row_gap=12,
                    pressure=0.15, radius_scale=0.25, colour=(200,194,182), seed=seed)

    # BREAKUP: finer bristle grain + subtle charcoal texture
    _fill_rect(buf, C[1],y0, C[2],y0+ROW_H, 222,215,202)
    if b2: _strokes(buf, b2, r, C[1],C[2], y0, rows=7, row_gap=9,
                    pressure=0.12, radius_scale=0.20, colour=(195,188,175), seed=seed+100)
    if c1: _strokes(buf, c1, r, C[1],C[2], y0, rows=2, row_gap=30,
                    pressure=0.10, radius_scale=0.38, colour=(210,204,192), seed=seed+150)

    # BREAKUP: add visible crack network in mid column (darken crack grooves)
    if b2: _strokes(buf, b2, r, C[1],C[2], y0, rows=7, row_gap=9,
                    pressure=0.12, radius_scale=0.20, colour=(195,188,175), seed=seed+100)
    # Prominent cracks in mid
    s_mid = seed + 250
    for crack in range(5):
        s_mid = _lcg(s_mid + crack * 83)
        cxs = C[1] + int(_lcg_f(s_mid) * (COL_W - 40))
        s_mid = _lcg(s_mid)
        cys = y0 + 6 + int(_lcg_f(s_mid) * (ROW_H - 12))
        cx_, cy_ = cxs, cys
        for step in range(30):
            s_mid = _lcg(s_mid)
            cx_ += int((_lcg_f(s_mid) - 0.4) * 3) + 1
            s_mid = _lcg(s_mid)
            cy_ += int((_lcg_f(s_mid) - 0.5) * 2)
            if C[1] <= cx_ < C[2] and y0 <= cy_ < y0 + ROW_H:
                base = (cy_ * W + cx_) * 4
                buf.data[base]=118; buf.data[base+1]=112; buf.data[base+2]=100

    # EDGE/WEAR: aged colour shift — warm pink-yellow tint, stain at base
    _fill_rect(buf, C[2],y0, W,y0+ROW_H, 225,210,188)  # warm aged ivory
    if b2: _strokes(buf, b2, r, C[2],W, y0, rows=4, row_gap=14,
                    pressure=0.22, radius_scale=0.20, colour=(195,178,155), seed=seed+200)
    # Damp stain band at base of wall
    _gradient_rect(buf, C[2], y0+int(ROW_H*0.65), W, y0+ROW_H, 200,185,162, 160,145,115)
    # Cracks on wear column — deeper and darker
    s = seed + 300
    for crack in range(4):
        s = _lcg(s + crack * 97)
        cx_start = C[2] + int(_lcg_f(s) * (W - C[2] - 40))
        s = _lcg(s)
        cy_start = y0 + 5 + int(_lcg_f(s) * (ROW_H - 10))
        cx_, cy_ = cx_start, cy_start
        for step in range(32):
            s = _lcg(s)
            cx_ += int((_lcg_f(s) - 0.4) * 3) + 1
            s = _lcg(s)
            cy_ += int((_lcg_f(s) - 0.5) * 2)
            if C[2] <= cx_ < W and y0 <= cy_ < y0 + ROW_H:
                base = (cy_ * W + cx_) * 4
                buf.data[base]=105; buf.data[base+1]=95; buf.data[base+2]=80


def row_timber_beam(buf, r, y0, seed=140):
    C = [CX[0], CX[1], CX[2]]
    c1 = r.shapes.get("Charcoal-01")
    ch3 = r.variant_bundles.get("Charcoal 03")  # 32x128 narrow — ideal for grain

    # BASE: warm brown beam, VERTICAL grain strokes
    _gradient_rect(buf, C[0],y0, C[1],y0+ROW_H, 118,72,38, 95,58,28, vertical=False)
    if c1: _strokes(buf, c1, r, C[0],C[1], y0, rows=6, pressure=0.35,
                    radius_scale=0.28, colour=(85,52,24), vertical=True,
                    seg_len=ROW_H, seed=seed)

    # BREAKUP: Charcoal 03 narrow cells for tight grain + pencil scratch knots
    _gradient_rect(buf, C[1],y0, C[2],y0+ROW_H, 115,70,36, 92,56,26, vertical=False)
    if ch3: _bundle_stamps(buf, ch3.cells, C[1],C[2], y0, n=20, scale=0.30,
                            colour=(75,46,20), seed=seed+100)
    ps = r.shapes.get("Pencil-Scratch")
    if ps: _single_stamps(buf, ps, C[1],C[2], y0, n=8, scale=0.40,
                           colour=(55,32,12), seed=seed+150)

    # EDGE/WEAR: end grain cross-section view + split line + shadow edge
    _gradient_rect(buf, C[2],y0, W,y0+ROW_H, 98,60,30, 78,48,22, vertical=False)
    if c1: _strokes(buf, c1, r, C[2],W, y0, rows=8, row_gap=8,
                    pressure=0.40, radius_scale=0.22, colour=(68,40,16), seed=seed+200)
    _seam_line(buf, C[2],W, y0, y_frac=0.0, col=(40,24,8), thickness=3)
    _seam_line(buf, C[2],W, y0, y_frac=1.0, col=(40,24,8), thickness=2)


def row_plank_wall(buf, r, y0, seed=150):
    C = [CX[0], CX[1], CX[2]]
    c2 = r.shapes.get("Charcoal-02")

    # BASE: horizontal planks — dark brown, charcoal grain
    _fill_rect(buf, C[0],y0, C[1],y0+ROW_H, 88,62,38)
    if c2: _strokes(buf, c2, r, C[0],C[1], y0, rows=4, row_gap=16,
                    pressure=0.38, radius_scale=0.28, colour=(65,44,26), seed=seed)

    # BREAKUP: plank separation lines + grain variation per plank
    _fill_rect(buf, C[1],y0, C[2],y0+ROW_H, 86,60,36)
    plank_h = 18
    for plank in range(ROW_H // plank_h + 1):
        py = y0 + plank * plank_h
        # Plank gap line
        if py < y0 + ROW_H:
            for x in range(C[1], C[2]):
                base = (py * W + x) * 4
                buf.data[base]=40; buf.data[base+1]=28; buf.data[base+2]=15
        # Per-plank grain offset
        if c2 and py + 2 < y0 + ROW_H:
            for stroke in range(3):
                s_ = seed + plank * 31 + stroke * 7
                pts = [(C[1] + x, py + 8 + math.sin((C[1]+x)*0.05)*2.5)
                       for x in range(0, COL_W, 2)]
                evs = stroke_to_events(pts, spacing_pct=c2.spacing_pct,
                                        base_radius=(c2.width or 64)/2.0 * 0.22,
                                        pressure=0.28, seed=s_)
                for idx, ev in enumerate(evs):
                    if C[1] <= ev.position_x < C[2]:
                        from engine_mr import DynamicsModifiers
                        mods = DynamicsModifiers(opacity=0.28, size_scale=0.22)
                        pixels = _load_bitmap(c2)
                        if pixels:
                            _render_bitmap(buf, ev.position_x, ev.position_y,
                                           c2, mods, 52,36,18, pixels)

    # EDGE/WEAR: nail heads + split grain + weathering darks
    _fill_rect(buf, C[2],y0, W,y0+ROW_H, 75,52,30)
    if c2: _strokes(buf, c2, r, C[2],W, y0, rows=4, row_gap=16,
                    pressure=0.45, radius_scale=0.25, colour=(48,32,14), seed=seed+200)
    # Nail heads: dark pixel pairs
    s = seed + 300
    for nail in range(12):
        s = _lcg(s + nail * 53)
        nx = C[2] + int(_lcg_f(s) * (W - C[2]))
        s = _lcg(s)
        ny = y0 + int(_lcg_f(s) * ROW_H)
        for dy in range(-1,2):
            for dx in range(-1,2):
                if 0 <= nx+dx < W and 0 <= ny+dy < H:
                    base = ((ny+dy)*W + nx+dx)*4
                    buf.data[base]=25; buf.data[base+1]=20; buf.data[base+2]=15


def row_roof_shingle(buf, r, y0, seed=160):
    C = [CX[0], CX[1], CX[2]]
    h = r.shapes.get("Hatch-Pen-01"); c1 = r.shapes.get("Charcoal-01")

    # BASE: dark grey-brown shingle mass
    _gradient_rect(buf, C[0],y0, C[1],y0+ROW_H, 72,65,58, 55,50,44)
    if c1: _strokes(buf, c1, r, C[0],C[1], y0, rows=4, row_gap=16,
                    pressure=0.35, radius_scale=0.38, colour=(45,40,35), seed=seed)

    # BREAKUP: overlapping course shadow lines
    _gradient_rect(buf, C[1],y0, C[2],y0+ROW_H, 70,63,56, 52,48,42)
    course_h = 14
    for course in range(ROW_H // course_h + 1):
        cy_bottom = y0 + course * course_h + course_h - 1
        if cy_bottom < y0 + ROW_H:
            for x in range(C[1], C[2]):
                base = (cy_bottom * W + x) * 4
                buf.data[base]=30; buf.data[base+1]=27; buf.data[base+2]=23
    if h: _strokes(buf, h, r, C[1],C[2], y0, rows=3, row_gap=18,
                    pressure=0.28, radius_scale=0.20, seg_len=40,
                    colour=(38,34,30), seed=seed+100)

    # EDGE/WEAR: moss patches + lichen pixel scatter + ridge highlight
    _gradient_rect(buf, C[2],y0, W,y0+ROW_H, 65,62,55, 50,47,42)
    _pixel_scatter(buf, C[2],W, y0, n=35, colour=(48,62,32), bright_range=20, seed=seed+200)
    if c1: _single_stamps(buf, c1, C[2],W, y0, n=8, scale=0.4,
                           colour=(38,50,25), seed=seed+250)
    _seam_line(buf, C[2],W, y0, y_frac=0.08, col=(85,80,72), thickness=2)


def row_weathered_wood(buf, r, y0, seed=170):
    C = [CX[0], CX[1], CX[2]]
    c2 = r.shapes.get("Charcoal-02"); sp1 = r.shapes.get("Sponge-01")
    ps = r.shapes.get("Pencil-Scratch")

    # BASE: silvery-grey weathered wood
    _fill_rect(buf, C[0],y0, C[1],y0+ROW_H, 115,108,98)
    if c2: _strokes(buf, c2, r, C[0],C[1], y0, rows=4, row_gap=16,
                    pressure=0.32, radius_scale=0.26, colour=(85,80,72), seed=seed)

    # BREAKUP: sponge dark rot patches + pencil scratch checks
    _fill_rect(buf, C[1],y0, C[2],y0+ROW_H, 110,104,94)
    if sp1: _single_stamps(buf, sp1, C[1],C[2], y0, n=5, scale=0.12,
                            colour=(55,50,44), seed=seed+100)
    if ps: _strokes(buf, ps, r, C[1],C[2], y0, rows=5, row_gap=12,
                    pressure=0.35, radius_scale=0.32, seg_len=55,
                    colour=(75,70,62), wave_amp=3.0, seed=seed+150)

    # EDGE/WEAR: end split, dark crevice, exposed grain
    _fill_rect(buf, C[2],y0, W,y0+ROW_H, 100,95,85)
    if c2: _strokes(buf, c2, r, C[2],W, y0, rows=6, row_gap=10,
                    pressure=0.45, radius_scale=0.22, seg_len=40,
                    colour=(52,48,42), wave_amp=5.0, seed=seed+200)
    _pixel_scatter(buf, C[2],W, y0, n=25, colour=(38,35,30), bright_range=15, seed=seed+300)
    _seam_line(buf, C[2],W, y0, y_frac=0.5, col=(30,27,22), thickness=3)


def row_sandstone_ruin(buf, r, y0, seed=180):
    C = [CX[0], CX[1], CX[2]]
    b1 = r.shapes.get("Bristles-01"); c1 = r.shapes.get("Charcoal-01")

    _gradient_rect(buf, C[0],y0, C[1],y0+ROW_H, 188,155,98, 168,138,82)
    if b1: _strokes(buf, b1, r, C[0],C[1], y0, rows=5, row_gap=12,
                    pressure=0.22, radius_scale=0.22, colour=(148,122,72), seed=seed)

    _gradient_rect(buf, C[1],y0, C[2],y0+ROW_H, 182,150,95, 162,134,78)
    if c1: _strokes(buf, c1, r, C[1],C[2], y0, rows=3, row_gap=20,
                    pressure=0.30, radius_scale=0.40, seg_len=70,
                    colour=(138,112,64), seed=seed+100)
    _pixel_scatter(buf, C[1],C[2], y0, n=45, colour=(120,98,58), seed=seed+150)

    _gradient_rect(buf, C[2],y0, W,y0+ROW_H, 170,140,88, 148,122,68)
    _mortar_lines(buf, C[2],W, y0, course_h=20, col=(130,108,65))
    if b1: _strokes(buf, b1, r, C[2],W, y0, rows=4, row_gap=15,
                    pressure=0.35, radius_scale=0.25, seg_len=50,
                    colour=(108,88,50), seed=seed+200)
    _pixel_scatter(buf, C[2],W, y0, n=60, colour=(95,76,42), bright_range=20, seed=seed+300)


def row_metal_trim(buf, r, y0, seed=190):
    C = [CX[0], CX[1], CX[2]]
    c1 = r.shapes.get("Charcoal-01")

    _gradient_rect(buf, C[0],y0, C[1],y0+ROW_H, 88,90,95, 62,64,68)
    if c1: _strokes(buf, c1, r, C[0],C[1], y0, rows=3, row_gap=22,
                    pressure=0.20, radius_scale=0.35, colour=(50,52,56), seed=seed)

    _gradient_rect(buf, C[1],y0, C[2],y0+ROW_H, 85,87,92, 60,62,66)
    if c1:
        _strokes(buf, c1, r, C[1],C[2], y0, rows=2, row_gap=28,
                 pressure=0.18, radius_scale=0.30, colour=(45,46,50), seed=seed+100)
        # Strong specular line — bright enough to read clearly
        _strokes(buf, c1, r, C[1],C[2], y0, rows=1, row_gap=1,
                 pressure=0.70, radius_scale=0.15, colour=(195,200,210),
                 wave_amp=0.5, seed=seed+150)
    # Edge polish: pixel-bright highlight at very top
    for x in range(C[1], C[2]):
        base = ((y0+3) * W + x) * 4
        buf.data[base]=185; buf.data[base+1]=190; buf.data[base+2]=200

    _gradient_rect(buf, C[2],y0, W,y0+ROW_H, 78,80,85, 55,57,62)
    _seam_line(buf, C[2],W, y0, y_frac=0.14, col=(18,19,22), thickness=4)  # deeper
    _seam_line(buf, C[2],W, y0, y_frac=0.86, col=(18,19,22), thickness=4)
    # STRUCTURED rivets — evenly spaced, not random
    rivet_y_top = y0 + int(ROW_H * 0.14)
    rivet_y_bot = y0 + int(ROW_H * 0.86)
    n_rivets = 6
    for ri in range(n_rivets):
        rx_ = C[2] + int((W - C[2]) * (ri + 0.5) / n_rivets)
        for ry_ in [rivet_y_top, rivet_y_bot]:
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    dist = dx*dx + dy*dy
                    if dist <= 4 and 0<=rx_+dx<W and 0<=ry_+dy<H:
                        bright = 155 if dist <= 1 else 110
                        base = ((ry_+dy)*W + rx_+dx)*4
                        buf.data[base]=bright; buf.data[base+1]=bright; buf.data[base+2]=bright+10
    if c1: _strokes(buf, c1, r, C[2],W, y0, rows=1,
                    pressure=0.65, radius_scale=0.12,
                    colour=(168,172,182), wave_amp=0.3, y_offset=ROW_H//2, seed=seed+500)


def row_glass_window(buf, r, y0, seed=200):
    C = [CX[0], CX[1], CX[2]]
    b2 = r.shapes.get("Bristles-02")

    _fill_rect(buf, C[0],y0, C[1],y0+ROW_H, 32,55,88)
    _gradient_rect(buf, C[0],y0, C[1],y0+ROW_H//2, 48,78,128, 32,55,88)

    _fill_rect(buf, C[1],y0, C[2],y0+ROW_H, 30,52,85)
    if b2:
        # Diagonal highlight sweep (simulate reflection)
        for stripe in range(4):
            xs = C[1] + stripe * 50
            pts = [(xs + k, y0 + 4 + k // 2) for k in range(0, COL_W - stripe*50, 2)
                   if xs+k < C[2]]
            evs = stroke_to_events(pts, spacing_pct=b2.spacing_pct,
                                    base_radius=(b2.width or 32)/2*0.25,
                                    pressure=0.25, seed=seed+stripe)
            mods = DynamicsModifiers(opacity=0.25, size_scale=0.25)
            pixels = _load_bitmap(b2)
            for idx, ev in enumerate(evs):
                if C[1] <= ev.position_x < C[2]:
                    _render_bitmap(buf, ev.position_x, ev.position_y,
                                   b2, mods, 140,175,220, pixels)

    _fill_rect(buf, C[2],y0, W,y0+ROW_H, 28,48,80)
    # Frame lines
    _seam_line(buf, C[2],W, y0, y_frac=0.0, col=(55,58,62), thickness=4)
    _seam_line(buf, C[2],W, y0, y_frac=1.0, col=(55,58,62), thickness=4)
    # Vertical mullion
    mx = (C[2] + W) // 2
    for y in range(y0, y0 + ROW_H):
        for dx in range(-2, 3):
            if 0 <= mx+dx < W:
                base = (y * W + mx+dx) * 4
                buf.data[base]=50; buf.data[base+1]=52; buf.data[base+2]=58
    # Dirt/condensation scatter
    _pixel_scatter(buf, C[2],W, y0, n=30, colour=(48,75,115), bright_range=20, seed=seed+300)


def row_ground_path(buf, r, y0, seed=210):
    C = [CX[0], CX[1], CX[2]]
    b1 = r.shapes.get("Bristles-01"); c1 = r.shapes.get("Charcoal-01")

    _gradient_rect(buf, C[0],y0, C[1],y0+ROW_H, 118,98,68, 98,80,54)
    if b1: _strokes(buf, b1, r, C[0],C[1], y0, rows=5, row_gap=12,
                    pressure=0.25, radius_scale=0.22, colour=(88,70,46), seed=seed)

    _gradient_rect(buf, C[1],y0, C[2],y0+ROW_H, 115,95,65, 95,78,52)
    if c1: _strokes(buf, c1, r, C[1],C[2], y0, rows=3, row_gap=20,
                    pressure=0.32, radius_scale=0.38, colour=(78,62,40), seed=seed+100)
    _pixel_scatter(buf, C[1],C[2], y0, n=50, colour=(68,54,34), seed=seed+150)

    # Wear: rut lines (parallel wheel tracks)
    _gradient_rect(buf, C[2],y0, W,y0+ROW_H, 108,88,60, 88,72,48)
    rut_y1 = y0 + ROW_H // 3; rut_y2 = y0 + 2 * ROW_H // 3
    for rut_y in [rut_y1, rut_y2]:
        for y in range(max(y0, rut_y-3), min(y0+ROW_H, rut_y+3)):
            depth = 1 - abs(y - rut_y) / 3
            for x in range(C[2], W):
                base = (y * W + x) * 4
                buf.data[base] = max(0, buf.data[base] - int(30 * depth))
                buf.data[base+1] = max(0, buf.data[base+1] - int(25 * depth))
    if b1: _strokes(buf, b1, r, C[2],W, y0, rows=4, row_gap=15,
                    pressure=0.20, radius_scale=0.18, colour=(65,50,30), seed=seed+200)


def row_crystal_shard(buf, r, y0, seed=220):
    """Ruby / Quartz / Emerald — three sub-panels."""
    c1 = r.shapes.get("Charcoal-01"); b2 = r.shapes.get("Bristles-02")
    # Subdivide each column into 3 crystal types
    sub_w = COL_W // 3

    palettes = [
        ((188, 30, 45), (240, 80, 90), (120, 15, 20)),    # Ruby
        ((210, 218, 228), (245, 248, 255), (155, 162, 172)),  # Quartz
        ((28, 155, 68), (80, 210, 112), (15, 95, 40)),    # Emerald
    ]

    for col_idx, (base_c, highlight_c, shadow_c) in enumerate(palettes):
        x0 = CX[0] + col_idx * sub_w
        x1 = x0 + sub_w

        # Crystal facet fill
        _gradient_rect(buf, x0,y0, x1,y0+ROW_H,
                        base_c[0], base_c[1], base_c[2],
                        shadow_c[0], shadow_c[1], shadow_c[2])

        # Facet line — diagonal sharp edge
        for step in range(min(x1-x0, ROW_H)):
            fx = x0 + step
            fy = y0 + step
            if 0 <= fx < W and 0 <= fy < H:
                base = (fy * W + fx) * 4
                buf.data[base]=highlight_c[0]; buf.data[base+1]=highlight_c[1]
                buf.data[base+2]=highlight_c[2]

        # Internal refraction — light scatter via pixel
        _pixel_scatter(buf, x0,x1, y0, n=20,
                        colour=highlight_c, bright_range=0, seed=seed+col_idx*100)

    # Replicate structure across columns 2 and 3 with variation
    for extra_col in [1, 2]:
        x_off = CX[extra_col]
        for col_idx, (base_c, highlight_c, shadow_c) in enumerate(palettes):
            x0 = x_off + col_idx * sub_w
            x1 = x0 + sub_w
            _gradient_rect(buf, x0,y0, x1,y0+ROW_H,
                            base_c[0], base_c[1], base_c[2],
                            shadow_c[0], shadow_c[1], shadow_c[2])
            for step in range(0, min(x1-x0, ROW_H), 2):
                fx = x0 + step; fy = y0 + step
                if 0<=fx<W and 0<=fy<H:
                    base=(fy*W+fx)*4
                    buf.data[base]=highlight_c[0]; buf.data[base+1]=highlight_c[1]
                    buf.data[base+2]=highlight_c[2]
            _pixel_scatter(buf, x0,x1, y0, n=15+extra_col*5,
                            colour=highlight_c, bright_range=0, seed=seed+col_idx*100+extra_col*33)


def row_star_needle(buf, r, y0, seed=230):
    C = [CX[0], CX[1], CX[2]]

    # BASE: deep space void
    _fill_rect(buf, C[0],y0, W,y0+ROW_H, 8,6,18)

    # Star points — pixel clusters radiating from centres
    s = seed
    n_stars = [5, 8, 12]
    for ci, (col_x, n_st) in enumerate(zip(C, n_stars)):
        for star in range(n_st):
            s = _lcg(s + star * 97)
            sx_ = col_x + int(_lcg_f(s) * COL_W)
            s = _lcg(s)
            sy_ = y0 + 6 + int(_lcg_f(s) * (ROW_H - 12))
            s = _lcg(s)
            mag = 0.5 + _lcg_f(s) * 1.5  # star magnitude

            # Core: burnt brass — warm amber/copper, not cold white
            core_r = min(255, int(200 + mag * 55))
            core_g = min(255, int(130 + mag * 35))
            core_b = min(255, int(30  + mag * 15))
            for dy in range(-1,2):
                for dx in range(-1,2):
                    if col_x <= sx_+dx < col_x+COL_W and y0 <= sy_+dy < y0+ROW_H:
                        base = ((sy_+dy)*W + sx_+dx)*4
                        buf.data[base]=core_r; buf.data[base+1]=core_g; buf.data[base+2]=core_b

            # Brass needle rays — warm falloff
            ray_len = int(mag * 9)
            for ray_dx, ray_dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                for step in range(1, ray_len+1):
                    rx_ = sx_ + ray_dx*step
                    ry_ = sy_ + ray_dy*step
                    falloff = max(0, 1.0 - step/ray_len)
                    if col_x <= rx_ < col_x+COL_W and y0 <= ry_ < y0+ROW_H:
                        base = (ry_*W + rx_)*4
                        buf.data[base]  = min(255, buf.data[base]   + int(core_r * falloff * 0.75))
                        buf.data[base+1]= min(255, buf.data[base+1] + int(core_g * falloff * 0.60))
                        buf.data[base+2]= min(255, buf.data[base+2] + int(core_b * falloff * 0.40))


def row_void_needle(buf, r, y0, seed=240):
    C = [CX[0], CX[1], CX[2]]
    sm = r.shapes.get("Smoke"); c2 = r.shapes.get("Charcoal-02")

    # BASE: near-black with cold dark blue tint
    _fill_rect(buf, C[0],y0, W,y0+ROW_H, 5,5,12)

    # Smoke stamps: dark bronze absorption pools — warm not cold
    if sm:
        br = (sm.width or 167) / 2.0
        sp = sm.spacing_pct
        mods = DynamicsModifiers(opacity=0.25, size_scale=0.18)
        pixels = _load_bitmap(sm)
        s = seed
        for ci, col_x in enumerate(C):
            for si in range(3):
                s = _lcg(s + si * 83 + ci * 211)
                fx = col_x + int(_lcg_f(s) * COL_W)
                s = _lcg(s)
                fy = y0 + 6 + int(_lcg_f(s) * (ROW_H - 12))
                if col_x <= fx < col_x+COL_W:
                    # Dark bronze smoke: deep warm brown, not cold blue-purple
                    _render_bitmap(buf, float(fx), float(fy), sm, mods,
                                   42, 22, 5, pixels)

    # Void centres: dark bronze absorption — warm amber rim, not cold glow
    s2 = seed + 500
    for ci, col_x in enumerate(C):
        n_voids = 3 + ci * 2
        for vi in range(n_voids):
            s2 = _lcg(s2 + vi * 67)
            vx = col_x + int(_lcg_f(s2) * COL_W)
            s2 = _lcg(s2)
            vy = y0 + 6 + int(_lcg_f(s2) * (ROW_H - 12))
            # Dark bronze centre
            for dy in range(-2,3):
                for dx in range(-2,3):
                    if col_x <= vx+dx < col_x+COL_W and y0 <= vy+dy < y0+ROW_H:
                        base=((vy+dy)*W+vx+dx)*4
                        buf.data[base]=8; buf.data[base+1]=4; buf.data[base+2]=0
            # Warm amber absorption rim — heat shimmer, not cold
            for angle_step in range(16):
                ang = angle_step * math.pi / 8
                for dist in range(3, 9):
                    rx_=int(vx+math.cos(ang)*dist); ry_=int(vy+math.sin(ang)*dist)
                    falloff=1.0-dist/9.0
                    if col_x<=rx_<col_x+COL_W and y0<=ry_<y0+ROW_H:
                        base=(ry_*W+rx_)*4
                        buf.data[base]  =min(255,buf.data[base]  +int(65*falloff))  # amber R
                        buf.data[base+1]=min(255,buf.data[base+1]+int(35*falloff))  # amber G
                        buf.data[base+2]=min(255,buf.data[base+2]+int( 5*falloff))  # very little B


def row_dragon_skin(buf, r, y0, seed=250):
    C = [CX[0], CX[1], CX[2]]
    h = r.shapes.get("Hatch-Pen-01"); c1 = r.shapes.get("Charcoal-01")

    # BASE: deep green-black scale fill
    _gradient_rect(buf, C[0],y0, C[1],y0+ROW_H, 22,55,35, 14,38,24)
    if c1: _strokes(buf, c1, r, C[0],C[1], y0, rows=4, row_gap=16,
                    pressure=0.30, radius_scale=0.35, colour=(12,30,18), seed=seed)

    # BREAKUP: scale tessellation — offset rows of arc-top shapes
    _gradient_rect(buf, C[1],y0, C[2],y0+ROW_H, 20,52,32, 12,36,22)
    scale_w = 18; scale_h = 12
    s = seed + 100
    for row in range(ROW_H // scale_h + 1):
        row_y = y0 + row * scale_h
        x_shift = (scale_w // 2) if row % 2 else 0
        for col_step in range(COL_W // scale_w + 2):
            sx_ = C[1] + col_step * scale_w + x_shift - scale_w
            if sx_ + scale_w < C[1] or sx_ >= C[2]: continue
            # Scale top arc — dark ridge line
            for step in range(scale_w):
                arc_y = row_y + int((1 - math.sin(step / scale_w * math.pi)) * scale_h // 2)
                fx = sx_ + step; fy = arc_y
                if C[1] <= fx < C[2] and y0 <= fy < y0 + ROW_H:
                    base = (fy * W + fx) * 4
                    buf.data[base]=8; buf.data[base+1]=22; buf.data[base+2]=14

    # EDGE/WEAR: lighter belly-scale transition + battle damage (hatch gashes)
    _gradient_rect(buf, C[2],y0, W,y0+ROW_H, 38,75,50, 25,55,36)
    # Same scale pattern, brighter
    for row in range(ROW_H // scale_h + 1):
        row_y = y0 + row * scale_h
        x_shift = (scale_w // 2) if row % 2 else 0
        for col_step in range(COL_W // scale_w + 2):
            sx_ = C[2] + col_step * scale_w + x_shift - scale_w
            if sx_ + scale_w < C[2] or sx_ >= W: continue
            for step in range(scale_w):
                arc_y = row_y + int((1-math.sin(step/scale_w*math.pi))*scale_h//2)
                fx = sx_+step; fy = arc_y
                if C[2]<=fx<W and y0<=fy<y0+ROW_H:
                    base=(fy*W+fx)*4
                    buf.data[base]=15; buf.data[base+1]=38; buf.data[base+2]=25
    if h: _strokes(buf, h, r, C[2],W, y0, rows=2, row_gap=28,
                    pressure=0.45, radius_scale=0.18, seg_len=45,
                    colour=(8,20,12), seed=seed+200)


# ---------------------------------------------------------------------------
# Sheet assembly
# ---------------------------------------------------------------------------

MATERIALS = [
    ("Stone Block", row_stone_block),
    ("Rough Cliff", row_rough_cliff),
    ("Brick Masonry", row_brick_masonry),
    ("Plaster Stucco", row_plaster_stucco),
    ("Timber Beam", row_timber_beam),
    ("Plank Wall", row_plank_wall),
    ("Roof Shingle", row_roof_shingle),
    ("Weathered Wood", row_weathered_wood),
    ("Sandstone Ruin", row_sandstone_ruin),
    ("Metal Trim", row_metal_trim),
    ("Glass Window", row_glass_window),
    ("Ground Path", row_ground_path),
    ("Crystal Shard", row_crystal_shard),
    ("Star Field", row_star_needle),    # renamed
    ("Void Essence", row_void_needle),  # renamed
    ("Dragon Skin", row_dragon_skin),
]


def build_sheet(registry: AssetRegistry) -> SurfaceBuffer:
    from engine_mr import SurfaceBuffer
    buf = SurfaceBuffer.blank(W, H)

    # Background
    for y in range(H):
        for x in range(W):
            base = (y * W + x) * 4
            buf.data[base]=14; buf.data[base+1]=14; buf.data[base+2]=18; buf.data[base+3]=255

    # Header
    for y in range(HEADER_H):
        for x in range(W):
            base = (y * W + x) * 4
            buf.data[base]=22; buf.data[base+1]=22; buf.data[base+2]=28; buf.data[base+3]=255
    text(buf, 6, 6, "TRIXEL BUILDING MATERIAL ATLAS", colour=(210,210,230))
    text(buf, 6, 16, "LEFT=base fill  MID=surface breakup  RIGHT=edge/seam/wear",
         colour=(140,140,160))

    # Column headers
    hdr_y = HEADER_H - 1
    for ci, label in enumerate(["BASE FILL", "SURFACE BREAKUP", "EDGE / SEAM / WEAR"]):
        text(buf, CX[ci] + 4, 6, label, colour=(160, 160, 180))

    # Each material row
    for row_i, (name, fn) in enumerate(MATERIALS):
        y0 = HEADER_H + row_i * ROW_H
        fn(buf, registry, y0, seed=(row_i + 1) * 100)
        _row_label(buf, y0, name, row_i + 1)
        _col_dividers(buf, y0)

    return buf


# ---------------------------------------------------------------------------
# Entry
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import time

    gimp_root = Path(sys.argv[1]) if len(sys.argv) > 1 else _find_gimp_data()
    out_path  = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/tmp/building_material_sheet.png")

    if gimp_root is None:
        print("Could not find GIMP data. Pass path as argument."); sys.exit(1)

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
    print(f"shapes={s['shapes']} bundles={s['variant_bundles']} errors={s['errors']}")

    print("Building atlas...")
    buf = build_sheet(registry)

    save_png(buf, out_path)
    print(f"✓  {out_path}  ({W}x{H})  ({time.time()-t0:.1f}s)")
    print(f"\n16 materials × 3 columns = 48 panels")
    print(f"Each column answers one question:")
    print(f"  LEFT:  does this colour and primary texture read as the material?")
    print(f"  MID:   does surface variation add depth without destroying identity?")
    print(f"  RIGHT: do joints, seams, wear, and age behave correctly?")
