"""
demo_bestiary_fauna_sheet.py — Trixel Bestiary: Fauna Sheet

Tests whether the engine can describe living animal forms.
Not material swatches — recognisable creatures.

Each subject gets a cell: silhouette drawn with pixel geometry,
texture applied with recipe stamps. Three sizes per creature
where relevant (distant / mid / close).

Pass criteria: creature is identifiable by outline alone.
Fail criteria: creature reads as a brush test or blob.

Subjects (8):
  bird      — perched silhouette, wing arc, tail point
  frog      — squat wide body, four limb stubs
  deer      — tall body, four legs, head, antler lines
  fish      — teardrop body, tail fan, fin
  insect    — segmented body, six legs, antenna pair
  lizard    — long narrow body, four splayed legs, tapered tail
  rabbit    — round body, upright ears, short tail
  dragonfly — slim thorax, four wing arcs, bulbous eyes
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
import math, sys
from pathlib import Path

_HERE = Path(__file__).parent
sys.path.insert(0, str(_HERE))

from engine_mr import (
    SurfaceBuffer, StrokeEvent, stroke_to_events,
    _render_bitmap, _load_bitmap, DynamicsModifiers,
)
from engine_debug_mr import text, save_png, stamp_blended
from trixel_recipes_mr import build, ALL_RECIPES
from trixel_brush_adapter import AssetRegistry
from world_tree_mr import _find_gimp_data

# ---------------------------------------------------------------------------
# Sheet geometry
# ---------------------------------------------------------------------------
CELL_W   = 160
CELL_H   = 140
COLS     = 4
ROWS     = 2
LABEL_H  = 22
HDR_H    = 28
W        = CELL_W * COLS
H        = HDR_H + ROWS * (CELL_H + LABEL_H)

# ---------------------------------------------------------------------------
# LCG
# ---------------------------------------------------------------------------
def _lcg(s):  return (s * 1664525 + 1013904223) & 0xFFFFFFFF
def _lcgf(s): return _lcg(s) / 0x100000000

# ---------------------------------------------------------------------------
# Shared drawing primitives
# ---------------------------------------------------------------------------

def _px(buf, x, y, r, g, b):
    if 0 <= x < W and 0 <= y < H:
        base = (y * W + x) * 4
        buf.data[base]=r; buf.data[base+1]=g; buf.data[base+2]=b; buf.data[base+3]=255

def _blend_px(buf, x, y, r, g, b, a=180):
    if 0 <= x < W and 0 <= y < H:
        base = (y * W + x) * 4
        t = a / 255.0
        buf.data[base]  = int(buf.data[base]   * (1-t) + r * t)
        buf.data[base+1]= int(buf.data[base+1] * (1-t) + g * t)
        buf.data[base+2]= int(buf.data[base+2] * (1-t) + b * t)

def _fill_cell(buf, cx, cy, r, g, b):
    for y in range(cy, cy + CELL_H):
        for x in range(cx, cx + CELL_W):
            base = (y * W + x) * 4
            buf.data[base]=r; buf.data[base+1]=g; buf.data[base+2]=b; buf.data[base+3]=255

def _ellipse(buf, cx, cy, rx, ry, r, g, b, fill=True, border=True):
    """Draw filled/outlined ellipse."""
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            dist = ((x-cx)/max(rx,1))**2 + ((y-cy)/max(ry,1))**2
            if fill and dist <= 1.0:
                _px(buf, x, y, r, g, b)
            elif border and 0.85 <= dist <= 1.15:
                _px(buf, x, y, max(0,r-20), max(0,g-20), max(0,b-20))

def _arc(buf, cx, cy, rx, ry, a0, a1, r, g, b, thickness=2):
    """Draw arc from angle a0 to a1 (radians)."""
    steps = max(20, int(abs(a1-a0) * max(rx,ry) * 0.8))
    prev = None
    for i in range(steps+1):
        t = a0 + (a1-a0)*i/steps
        x = int(cx + rx * math.cos(t))
        y = int(cy + ry * math.sin(t))
        for dt in range(-thickness//2, thickness//2+1):
            _px(buf, x+dt, y, r, g, b)
            _px(buf, x, y+dt, r, g, b)

def _line(buf, x0, y0, x1, y1, r, g, b, thickness=1):
    """Bresenham line."""
    dx = abs(x1-x0); dy = abs(y1-y0)
    sx = 1 if x1>x0 else -1; sy = 1 if y1>y0 else -1
    err = dx-dy
    cx, cy = x0, y0
    while True:
        for t in range(thickness):
            _px(buf, cx+t, cy, r, g, b)
            _px(buf, cx, cy+t, r, g, b)
        if cx==x1 and cy==y1: break
        e2=2*err
        if e2>-dy: err-=dy; cx+=sx
        if e2<dx:  err+=dx; cy+=sy

def _texture_region(buf, shape, pixels, cx0,cy0,cx1,cy1,
                    r,g,b, r_scale=0.30, pressure=0.35, seed=0):
    """Sparse stamp texture within a region."""
    if not shape or not pixels: return
    br = (shape.radius or (shape.width or 32)/2.0) * r_scale
    sp = shape.spacing_pct
    mods = DynamicsModifiers(opacity=pressure, size_scale=r_scale)
    s = seed
    n_pass = max(1, (cx1-cx0)*(cy1-cy0)//400)
    for i in range(n_pass):
        s = _lcg(s+i*71)
        fx = cx0 + int(_lcgf(s)*(cx1-cx0))
        s = _lcg(s)
        fy = cy0 + int(_lcgf(s)*(cy1-cy0))
        if cx0<=fx<cx1 and cy0<=fy<cy1:
            _render_bitmap(buf, float(fx), float(fy), shape, mods, r,g,b, pixels)

def _pixel_scatter(buf, cx0,cy0,cx1,cy1, r,g,b, n=20, var=20, seed=0):
    s = seed
    for _ in range(n):
        s=_lcg(s); fx=cx0+int(_lcgf(s)*(cx1-cx0))
        s=_lcg(s); fy=cy0+int(_lcgf(s)*(cy1-cy0))
        s=_lcg(s); v=int(_lcgf(s)*var)-var//2
        _px(buf,fx,fy,min(255,r+v),min(255,g+v),min(255,b+v))

def _cell_origin(idx):
    col = idx % COLS
    row = idx // COLS
    cx = col * CELL_W
    cy = HDR_H + row * (CELL_H + LABEL_H)
    return cx, cy

def _cell_label(buf, idx, name, r=160, g=160, b=180):
    cx, cy = _cell_origin(idx)
    text(buf, cx+4, cy+CELL_H+4, name.upper(), colour=(r,g,b))

# ---------------------------------------------------------------------------
# Creature drawers
# ---------------------------------------------------------------------------

def draw_bird(buf, cx, cy, charcoal_shape, charcoal_pixels, seed=10):
    """
    Side-view perching bird.
    Body: horizontal oval. Head: small circle above-forward.
    Tail: pointed rearward. Wing: arc above body. Legs: two thin sticks.
    """
    C_BODY = (38, 32, 28)
    C_WING = (55, 48, 40)
    C_BEAK = (130, 105, 30)
    C_EYE  = (220, 215, 200)

    # Draw three sizes: small (left), medium (centre), large (right)
    configs = [
        (cx+28,  cy+90,  9,  6, 1.0),   # small
        (cx+78,  cy+82,  15, 10, 1.5),  # medium
        (cx+130, cy+72,  22, 15, 2.0),  # large
    ]
    for bx, by, rx, ry, sc in configs:
        # Body
        _ellipse(buf, bx, by, rx, ry, C_BODY[0],C_BODY[1],C_BODY[2])
        # Head
        hr = max(2, int(ry*0.85))
        hx = bx + rx - hr + 1
        hy = by - ry + hr - 1
        _ellipse(buf, hx, hy, hr, hr, C_BODY[0],C_BODY[1],C_BODY[2])
        # Beak (pointing right)
        bkx = hx + hr
        _line(buf, bkx, hy, bkx+int(sc*4), hy, C_BEAK[0],C_BEAK[1],C_BEAK[2])
        # Eye
        _px(buf, hx+int(hr*0.4), hy-int(hr*0.2), C_EYE[0],C_EYE[1],C_EYE[2])
        # Wing arc above body
        _arc(buf, bx-int(rx*0.1), by, rx, int(ry*1.8),
             math.pi*1.1, math.pi*1.9, C_WING[0],C_WING[1],C_WING[2],
             thickness=max(1,int(sc)))
        # Tail pointing left and down
        _line(buf, bx-rx, by+int(ry*0.3), bx-rx-int(sc*6), by+int(ry*0.8),
              C_BODY[0],C_BODY[1],C_BODY[2], thickness=max(1,int(sc)))
        _line(buf, bx-rx, by+int(ry*0.3), bx-rx-int(sc*5), by+int(ry*1.1),
              C_BODY[0]-8,C_BODY[1]-8,C_BODY[2]-8, thickness=max(1,int(sc)))
        # Legs
        leg_y = by + ry
        for lx_off in [-int(rx*0.3), int(rx*0.3)]:
            lx = bx + lx_off
            _line(buf, lx, leg_y, lx, leg_y+int(sc*6), 40,35,28)
            _line(buf, lx, leg_y+int(sc*6), lx-int(sc*3), leg_y+int(sc*8), 40,35,28)
            _line(buf, lx, leg_y+int(sc*6), lx+int(sc*3), leg_y+int(sc*8), 40,35,28)

    # Feather texture on large bird
    if charcoal_shape and charcoal_pixels:
        bx,by,rx,ry,sc = configs[2]
        _texture_region(buf, charcoal_shape, charcoal_pixels,
                        bx-rx, by-ry, bx+rx, by+ry,
                        C_BODY[0]-8,C_BODY[1]-8,C_BODY[2]-8,
                        r_scale=0.22, pressure=0.28, seed=seed)


def draw_frog(buf, cx, cy, charcoal_shape, charcoal_pixels, seed=20):
    """
    Top-down frog: wide flat oval body, four splayed limbs, bulging eyes.
    """
    C_SKIN  = (42, 85, 38)
    C_BELLY = (68, 110, 55)
    C_EYE   = (220, 200, 30)
    C_DARK  = (28, 58, 24)

    configs = [
        (cx+28,  cy+85,  12, 9,  1.0),
        (cx+78,  cy+80,  20, 14, 1.6),
        (cx+128, cy+75,  28, 20, 2.2),
    ]
    for bx,by,rx,ry,sc in configs:
        # Body (wide oval)
        _ellipse(buf, bx, by, rx, ry, C_SKIN[0],C_SKIN[1],C_SKIN[2])
        # Belly highlight
        _ellipse(buf, bx, by+int(ry*0.1), int(rx*0.6), int(ry*0.55),
                 C_BELLY[0],C_BELLY[1],C_BELLY[2], border=False)
        # Eyes (protruding forward-sides)
        er = max(2, int(sc*2.5))
        for ex_off in [-int(rx*0.55), int(rx*0.55)]:
            ex_ = bx + ex_off
            ey_ = by - int(ry*0.7)
            _ellipse(buf, ex_, ey_, er, er, C_DARK[0],C_DARK[1],C_DARK[2])
            _px(buf, ex_, ey_, C_EYE[0],C_EYE[1],C_EYE[2])
        # Front legs (short, forward)
        for side in [-1, 1]:
            flx = bx + side*int(rx*0.85)
            fly_start = by - int(ry*0.3)
            _line(buf, flx, fly_start,
                  flx+side*int(sc*6), fly_start-int(sc*5),
                  C_DARK[0],C_DARK[1],C_DARK[2])
        # Back legs (long, splayed)
        for side in [-1, 1]:
            blx = bx + side*int(rx*0.75)
            bly_start = by + int(ry*0.6)
            knee_x = blx + side*int(sc*7)
            knee_y = bly_start + int(sc*8)
            foot_x = knee_x - side*int(sc*5)
            foot_y = knee_y + int(sc*5)
            _line(buf, blx,bly_start, knee_x,knee_y, C_DARK[0],C_DARK[1],C_DARK[2],
                  thickness=max(1,int(sc*0.5)))
            _line(buf, knee_x,knee_y, foot_x,foot_y, C_DARK[0],C_DARK[1],C_DARK[2])
    # Skin texture on large
    bx,by,rx,ry,sc = configs[2]
    if charcoal_shape and charcoal_pixels:
        _texture_region(buf, charcoal_shape, charcoal_pixels,
                        bx-rx,by-ry,bx+rx,by+ry,
                        C_DARK[0],C_DARK[1],C_DARK[2],
                        r_scale=0.20, pressure=0.20, seed=seed)
    _pixel_scatter(buf, bx-rx,by-ry,bx+rx,by+ry,
                   C_BELLY[0],C_BELLY[1],C_BELLY[2], n=8, seed=seed+5)


def draw_deer(buf, cx, cy, charcoal_shape, charcoal_pixels, seed=30):
    """
    Side-view deer: tall oval body, four stick legs, long neck+head, antlers.
    """
    C_COAT = (145, 95, 45)
    C_BELLY= (185, 145, 80)
    C_LEG  = (110, 70, 30)
    C_ANTL = (88, 60, 25)
    C_NOSE = (48, 30, 20)
    C_EYE  = (20, 15, 10)

    # One large figure centred in cell
    bx, by = cx+80, cy+80
    rx, ry = 28, 18

    # Body
    _ellipse(buf, bx, by, rx, ry, C_COAT[0],C_COAT[1],C_COAT[2])
    # Belly lighter stripe
    _ellipse(buf, bx+4, by+int(ry*0.2), int(rx*0.55), int(ry*0.55),
             C_BELLY[0],C_BELLY[1],C_BELLY[2], border=False)
    # Neck
    nx_btm, ny_btm = bx+rx-6, by-int(ry*0.6)
    nx_top, ny_top = nx_btm+8, ny_btm-18
    _line(buf, nx_btm,ny_btm, nx_top,ny_top, C_COAT[0],C_COAT[1],C_COAT[2], thickness=6)
    # Head
    hx, hy = nx_top+7, ny_top-2
    _ellipse(buf, hx, hy, 9, 7, C_COAT[0],C_COAT[1],C_COAT[2])
    # Snout
    _line(buf, hx+7,hy, hx+14,hy+3, C_COAT[0]-10,C_COAT[1]-10,C_COAT[2]-10)
    _px(buf, hx+14, hy+3, C_NOSE[0],C_NOSE[1],C_NOSE[2])
    # Eye
    _px(buf, hx+3, hy-2, C_EYE[0],C_EYE[1],C_EYE[2])
    # Ear
    _line(buf, hx-1,hy-5, hx+2,hy-11, C_COAT[0],C_COAT[1],C_COAT[2], thickness=2)
    # Antlers (left = viewer side)
    ax, ay = hx-2, hy-11
    _line(buf, ax,ay, ax-5,ay-10, C_ANTL[0],C_ANTL[1],C_ANTL[2])
    _line(buf, ax-5,ay-10, ax-9,ay-16, C_ANTL[0],C_ANTL[1],C_ANTL[2])
    _line(buf, ax-5,ay-10, ax-2,ay-17, C_ANTL[0],C_ANTL[1],C_ANTL[2])
    _line(buf, ax,ay, ax+2,ay-9, C_ANTL[0],C_ANTL[1],C_ANTL[2])
    _line(buf, ax+2,ay-9, ax+5,ay-15, C_ANTL[0],C_ANTL[1],C_ANTL[2])
    # Four legs
    leg_tops = [(bx-int(rx*0.55),by+ry-2),(bx-int(rx*0.15),by+ry-2),
                (bx+int(rx*0.2),by+ry-2),(bx+int(rx*0.55),by+ry-2)]
    for lx,ly in leg_tops:
        knee_y = ly+12
        _line(buf, lx,ly, lx,knee_y, C_LEG[0],C_LEG[1],C_LEG[2], thickness=2)
        _line(buf, lx,knee_y, lx+1,knee_y+12, C_LEG[0]-10,C_LEG[1]-10,C_LEG[2]-10)
    # Tail (small stub right side)
    _ellipse(buf, bx-rx, by-3, 4, 3, 210,200,190, border=False)
    # Coat texture
    if charcoal_shape and charcoal_pixels:
        _texture_region(buf, charcoal_shape, charcoal_pixels,
                        bx-rx,by-ry,bx+rx,by+ry,
                        C_LEG[0],C_LEG[1],C_LEG[2],
                        r_scale=0.25, pressure=0.25, seed=seed)

    # Small silhouette version (top-left)
    bxs,bys = cx+25, cy+95
    rxs,rys = 12, 8
    _ellipse(buf, bxs,bys, rxs,rys, C_COAT[0],C_COAT[1],C_COAT[2])
    _line(buf, bxs+rxs-2,bys-rys, bxs+rxs+8,bys-rys-10, C_COAT[0],C_COAT[1],C_COAT[2],3)
    _ellipse(buf, bxs+rxs+12,bys-rys-10, 5,4, C_COAT[0],C_COAT[1],C_COAT[2])
    for lx in [bxs-int(rxs*0.5),bxs,bxs+int(rxs*0.5),bxs+int(rxs*0.9)]:
        _line(buf, lx,bys+rys, lx,bys+rys+10, C_LEG[0],C_LEG[1],C_LEG[2])


def draw_fish(buf, cx, cy, bristle_shape, bristle_pixels, seed=40):
    """
    Side-view fish: teardrop body, tail fan, dorsal+pectoral fins, scales.
    """
    C_BODY  = (45, 95, 115)
    C_BELLY = (80, 145, 160)
    C_FIN   = (35, 75, 95)
    C_SCALE = (55, 110, 130)
    C_EYE   = (220, 215, 190)

    configs = [
        (cx+25,  cy+88,  11, 7,  1.0),
        (cx+72,  cy+80,  19, 12, 1.7),
        (cx+125, cy+72,  27, 16, 2.4),
    ]
    for bx,by,rx,ry,sc in configs:
        # Body (wider at front, tapers to tail)
        _ellipse(buf, bx-int(rx*0.1), by, int(rx*0.95), ry, C_BODY[0],C_BODY[1],C_BODY[2])
        # Belly
        _ellipse(buf, bx-int(rx*0.1), by+int(ry*0.15), int(rx*0.7), int(ry*0.6),
                 C_BELLY[0],C_BELLY[1],C_BELLY[2], border=False)
        # Tail fan
        tx = bx - rx
        for t_ang, t_len in [(math.pi*0.8, 1.4),(math.pi, 1.6),(math.pi*1.2, 1.4)]:
            _line(buf, tx,by,
                  int(tx+math.cos(t_ang)*sc*t_len*2.5),
                  int(by+math.sin(t_ang)*sc*t_len*2.5),
                  C_FIN[0],C_FIN[1],C_FIN[2], thickness=max(1,int(sc*0.5)))
        # Dorsal fin
        dx_start = bx - int(rx*0.3)
        _arc(buf, bx+int(rx*0.1), by-ry, int(rx*0.4), int(sc*5),
             math.pi*1.1, math.pi*1.9, C_FIN[0],C_FIN[1],C_FIN[2])
        # Pectoral fin
        _line(buf, bx+int(rx*0.3),by, bx+int(rx*0.3)+int(sc*3),by+int(sc*4),
              C_FIN[0],C_FIN[1],C_FIN[2])
        # Eye
        er = max(1, int(sc*1.2))
        ex_ = bx + int(rx*0.55)
        _ellipse(buf, ex_,by-int(ry*0.15), er,er, 12,12,12)
        _px(buf, ex_,by-int(ry*0.15), C_EYE[0],C_EYE[1],C_EYE[2])
        # Mouth
        _px(buf, bx+rx, by+int(ry*0.25), C_BODY[0]-10,C_BODY[1]-10,C_BODY[2]-10)
        # Scale marks on medium+large
        if sc >= 1.5:
            for si in range(0, int(rx*1.6), max(3,int(sc*2))):
                sy_top = by - int(ry * math.sqrt(max(0,1-((si/rx-0.2)**2))))
                _arc(buf, bx-rx+si+int(rx*0.3), by, int(sc*1.5),int(sc*1.5),
                     math.pi*0.8,math.pi*1.6, C_SCALE[0],C_SCALE[1],C_SCALE[2])


def draw_insect(buf, cx, cy, pencil_shape, pencil_pixels, seed=50):
    """
    Side-on insect: three body segments, six legs, two antennae, wing cases.
    Based loosely on a beetle form.
    """
    C_SHELL  = (38, 45, 22)
    C_LEGS   = (28, 35, 16)
    C_ANTL   = (55, 62, 35)
    C_SHINE  = (68, 82, 40)
    C_THORAX = (50, 58, 28)

    configs = [
        (cx+28,  cy+92,  7,  5,  1.0),
        (cx+78,  cy+85,  12, 8,  1.6),
        (cx+130, cy+78,  17, 11, 2.2),
    ]
    for bx,by,rx,ry,sc in configs:
        # Abdomen (rear, larger)
        _ellipse(buf, bx-int(rx*0.25),by, int(rx*0.9),ry, C_SHELL[0],C_SHELL[1],C_SHELL[2])
        # Thorax (middle)
        tx = bx+int(rx*0.55)
        _ellipse(buf, tx,by, int(rx*0.45),int(ry*0.85), C_THORAX[0],C_THORAX[1],C_THORAX[2])
        # Head (front, small)
        hx = tx+int(rx*0.45)+int(sc*3)
        _ellipse(buf, hx,by, int(sc*3),int(sc*2.5), C_SHELL[0],C_SHELL[1],C_SHELL[2])
        # Antennae
        _line(buf, hx,by-int(sc*2),
              hx+int(sc*3),by-int(sc*8), C_ANTL[0],C_ANTL[1],C_ANTL[2])
        _line(buf, hx,by-int(sc*2),
              hx+int(sc*5),by-int(sc*6), C_ANTL[0],C_ANTL[1],C_ANTL[2])
        # Six legs (three per side, from thorax)
        leg_angles = [math.pi*0.7, math.pi*0.9, math.pi*1.1]
        for i,ang in enumerate(leg_angles):
            for side in [1,-1]:
                lx_s = tx + int(math.cos(ang)*int(rx*0.45))
                ly_s = by + side*int(ry*0.85)
                lx_e = lx_s + int(math.cos(ang+side*0.4)*sc*6)
                ly_e = ly_s + side*int(sc*5)
                _line(buf, lx_s,ly_s, lx_e,ly_e, C_LEGS[0],C_LEGS[1],C_LEGS[2])
        # Elytra shine line (down abdomen centre)
        _line(buf, bx-int(rx*0.25),by-int(ry*0.7),
              bx+int(rx*0.5),by-int(ry*0.5),
              C_SHINE[0],C_SHINE[1],C_SHINE[2])


def draw_lizard(buf, cx, cy, pencil_shape, pencil_pixels, seed=60):
    """
    Top-down lizard: narrow elongated body, four splayed legs, long tapering tail.
    """
    C_SKIN   = (68, 85, 45)
    C_BELLY  = (98, 115, 68)
    C_STRIPE = (48, 62, 30)
    C_EYE    = (200, 185, 20)

    configs = [
        (cx+30,  cy+88,  7,  4, 20, 1.0),
        (cx+80,  cy+78,  12, 7, 35, 1.7),
        (cx+132, cy+68,  16, 9, 48, 2.2),
    ]
    for bx,by,brx,bry,tail_len,sc in configs:
        # Body oval
        _ellipse(buf, bx,by, brx,bry, C_SKIN[0],C_SKIN[1],C_SKIN[2])
        # Belly stripe
        _ellipse(buf, bx+int(brx*0.1),by, int(brx*0.55),int(bry*0.55),
                 C_BELLY[0],C_BELLY[1],C_BELLY[2], border=False)
        # Head (forward, triangular approximation)
        hx = bx+brx+int(sc*2)
        _ellipse(buf, hx,by, int(sc*4),int(sc*2.5), C_SKIN[0],C_SKIN[1],C_SKIN[2])
        # Eyes
        for eye_side in [-1,1]:
            _px(buf, hx+int(sc*2),by+eye_side*int(sc*1.5), C_EYE[0],C_EYE[1],C_EYE[2])
        # Tail (tapering line, curves slightly)
        for step in range(tail_len):
            t = step/tail_len
            tx = bx - brx - step
            ty = by + int(math.sin(step*0.15)*sc*2)
            tbrx = max(1, int(bry*(1-t*0.85)))
            if step % 3 == 0:
                _ellipse(buf, tx,ty, tbrx, max(1,tbrx-1),
                         C_SKIN[0],C_SKIN[1],C_SKIN[2], border=False)
        # Four legs (splayed)
        leg_configs = [
            (-int(brx*0.5), -int(bry*0.9), -1,-1, int(sc*7), int(sc*5)),
            ( int(brx*0.3), -int(bry*0.9), +1,-1, int(sc*8), int(sc*5)),
            (-int(brx*0.5),  int(bry*0.9), -1,+1, int(sc*7), int(sc*6)),
            ( int(brx*0.3),  int(bry*0.9), +1,+1, int(sc*8), int(sc*6)),
        ]
        for lx_off,ly_off,sx,sy,llen_x,llen_y in leg_configs:
            lsx = bx+lx_off; lsy = by+ly_off
            _line(buf, lsx,lsy, lsx+sx*llen_x,lsy+sy*llen_y,
                  C_STRIPE[0],C_STRIPE[1],C_STRIPE[2])
        # Dorsal stripe
        _line(buf, hx-1,by, bx-brx,by, C_STRIPE[0],C_STRIPE[1],C_STRIPE[2])
    # Texture on largest
    bx,by,brx,bry,_,sc = configs[2]
    if pencil_shape and pencil_pixels:
        _texture_region(buf, pencil_shape, pencil_pixels,
                        bx-brx,by-bry,bx+brx+20,by+bry,
                        C_STRIPE[0],C_STRIPE[1],C_STRIPE[2],
                        r_scale=0.28, pressure=0.22, seed=seed)


def draw_rabbit(buf, cx, cy, bristle_shape, bristle_pixels, seed=70):
    """
    Side-view rabbit: round body, upright ears, round head, small tail.
    """
    C_FUR   = (175, 158, 138)
    C_INNER = (220, 195, 185)
    C_EYE   = (48, 25, 18)
    C_NOSE  = (185, 120, 115)

    configs = [
        (cx+28,  cy+92,  10, 12, 1.0),
        (cx+75,  cy+84,  17, 20, 1.6),
        (cx+128, cy+76,  24, 28, 2.2),
    ]
    for bx,by,rx,ry,sc in configs:
        # Body
        _ellipse(buf, bx, by, rx, ry, C_FUR[0],C_FUR[1],C_FUR[2])
        # Head (forward-upper)
        hr = max(4, int(rx*0.72))
        hx = bx + int(rx*0.55)
        hy = by - int(ry*0.55)
        _ellipse(buf, hx,hy, hr,hr, C_FUR[0],C_FUR[1],C_FUR[2])
        # Ears (upright)
        for ear_off in [-int(hr*0.35), int(hr*0.25)]:
            ex = hx + ear_off
            ey_btm = hy - hr
            ear_h = int(sc*10)
            _line(buf, ex,ey_btm, ex+int(ear_off*0.2),ey_btm-ear_h,
                  C_FUR[0],C_FUR[1],C_FUR[2], thickness=max(2,int(sc*1.5)))
            # Inner ear
            _line(buf, ex,ey_btm, ex+int(ear_off*0.2),ey_btm-int(ear_h*0.7),
                  C_INNER[0],C_INNER[1],C_INNER[2])
        # Nose
        _px(buf, hx+hr-1, hy, C_NOSE[0],C_NOSE[1],C_NOSE[2])
        # Eye
        _px(buf, hx+int(hr*0.5), hy-int(hr*0.35), C_EYE[0],C_EYE[1],C_EYE[2])
        # Fluffy tail
        _ellipse(buf, bx-rx, by-int(ry*0.1), int(sc*3),int(sc*3),
                 215,205,195, border=False)
        # Front paws
        for px_off in [int(rx*0.2), int(rx*0.55)]:
            _line(buf, hx-int(hr*0.4),hy+hr,
                  hx-int(hr*0.4)+px_off*0, hy+hr+int(sc*4),
                  C_FUR[0]-15,C_FUR[1]-15,C_FUR[2]-15)
        # Back leg (haunches)
        _ellipse(buf, bx-int(rx*0.4),by+int(ry*0.45), int(rx*0.55),int(ry*0.4),
                 C_FUR[0]-10,C_FUR[1]-10,C_FUR[2]-10, border=False)
    # Fur texture on large
    bx,by,rx,ry,sc = configs[2]
    if bristle_shape and bristle_pixels:
        _texture_region(buf, bristle_shape, bristle_pixels,
                        bx-rx,by-ry,bx+rx+10,by+ry,
                        C_FUR[0]-18,C_FUR[1]-18,C_FUR[2]-18,
                        r_scale=0.18, pressure=0.18, seed=seed)


def draw_dragonfly(buf, cx, cy, bristle_shape, bristle_pixels, seed=80):
    """
    Top-down dragonfly: slim segmented body, four wing arcs, bulbous eyes.
    """
    C_BODY   = (18, 88, 88)
    C_WING   = (145, 185, 185)
    C_ACCENT = (12, 125, 125)
    C_EYE    = (155, 12, 12)

    configs = [
        (cx+28,  cy+90,  4,  16, 1.0),
        (cx+78,  cy+82,  6,  26, 1.6),
        (cx+128, cy+74,  8,  36, 2.2),
    ]
    for bx,by,rx,ry,sc in configs:
        # Thorax (upper body)
        _ellipse(buf, bx,by-int(ry*0.2), int(rx*1.3),int(ry*0.25),
                 C_BODY[0],C_BODY[1],C_BODY[2])
        # Abdomen (segmented long tail)
        segs = 7
        for seg in range(segs):
            seg_y = by + int(ry*0.1) + seg * int(ry*0.85/segs)
            seg_rx = max(1, rx - int(seg*rx*0.6/segs))
            seg_col_v = max(0, C_BODY[0]-seg*2)
            _ellipse(buf, bx,seg_y, seg_rx,max(1,int(ry*0.08)),
                     seg_col_v,C_BODY[1],C_BODY[2], border=False)
        # Head
        _ellipse(buf, bx,by-int(ry*0.42), int(rx*1.2),int(rx*1.2),
                 C_BODY[0],C_BODY[1],C_BODY[2])
        # Compound eyes
        for eye_side in [-1,1]:
            _px(buf, bx+eye_side*int(rx*0.9), by-int(ry*0.42),
                C_EYE[0],C_EYE[1],C_EYE[2])
        # Four wings (two per side)
        wing_cx = bx
        wing_cy = by - int(ry*0.15)
        for side,size_factor in [(-1,1.4),(-1,0.9),(1,1.4),(1,0.9)]:
            w_rx = int(sc * 8 * size_factor)
            w_ry = int(sc * 4 * size_factor)
            w_y_off = 0 if abs(size_factor-1.4)<0.1 else int(sc*4)
            _arc(buf, wing_cx+side*w_rx//2, wing_cy-w_y_off,
                 w_rx, w_ry,
                 math.pi*(0.85 if side<0 else 0.0),
                 math.pi*(1.0 if side<0 else 0.15) + math.pi,
                 C_WING[0],C_WING[1],C_WING[2])
        # Accent stripe on abdomen
        _line(buf, bx,by-int(ry*0.1), bx,by+int(ry*0.8),
              C_ACCENT[0],C_ACCENT[1],C_ACCENT[2])

# ---------------------------------------------------------------------------
# Sheet assembly
# ---------------------------------------------------------------------------

CREATURES = [
    ("bird",      draw_bird),
    ("frog",      draw_frog),
    ("deer",      draw_deer),
    ("fish",      draw_fish),
    ("insect",    draw_insect),
    ("lizard",    draw_lizard),
    ("rabbit",    draw_rabbit),
    ("dragonfly", draw_dragonfly),
]


def build_fauna_sheet(registry: AssetRegistry) -> SurfaceBuffer:
    buf = SurfaceBuffer.blank(W, H)

    # Background — dark natural
    for y in range(H):
        for x in range(W):
            base=(y*W+x)*4
            buf.data[base]=12; buf.data[base+1]=14; buf.data[base+2]=10; buf.data[base+3]=255

    # Header
    for y in range(HDR_H):
        for x in range(W):
            base=(y*W+x)*4
            buf.data[base]=18; buf.data[base+1]=20; buf.data[base+2]=15; buf.data[base+3]=255
    text(buf, 6, 6,  "TRIXEL BESTIARY — FAUNA SHEET", colour=(145,175,120))
    text(buf, 6, 16, "three sizes per creature  |  pass = identifiable without label", colour=(90,110,72))

    # Load shapes
    from engine_mr import _load_bitmap
    charcoal  = registry.shapes.get("Charcoal-01")
    bristle   = registry.shapes.get("Bristles-01")
    pencil_s  = registry.shapes.get("Pencil-Scratch")
    c_pixels  = _load_bitmap(charcoal)  if charcoal  else None
    b_pixels  = _load_bitmap(bristle)   if bristle   else None
    p_pixels  = _load_bitmap(pencil_s)  if pencil_s  else None

    shape_map = {
        "bird":      (charcoal,  c_pixels),
        "frog":      (charcoal,  c_pixels),
        "deer":      (charcoal,  c_pixels),
        "fish":      (bristle,   b_pixels),
        "insect":    (pencil_s,  p_pixels),
        "lizard":    (pencil_s,  p_pixels),
        "rabbit":    (bristle,   b_pixels),
        "dragonfly": (bristle,   b_pixels),
    }

    draw_map = {
        "bird":      draw_bird,
        "frog":      draw_frog,
        "deer":      draw_deer,
        "fish":      draw_fish,
        "insect":    draw_insect,
        "lizard":    draw_lizard,
        "rabbit":    draw_rabbit,
        "dragonfly": draw_dragonfly,
    }

    for idx, (name, _) in enumerate(CREATURES):
        cx, cy = _cell_origin(idx)
        # Cell background (slight variation by row)
        row = idx // COLS
        bg = 15 + row*3
        _fill_cell(buf, cx, cy, bg, bg+2, bg-2)
        # Draw creature
        shape, pixels = shape_map[name]
        draw_map[name](buf, cx, cy, shape, pixels, seed=idx*100)
        # Label
        _cell_label(buf, idx, name)

    # Grid dividers
    for col in range(1, COLS):
        for y in range(H):
            base=(y*W+col*CELL_W)*4
            buf.data[base]=8; buf.data[base+1]=10; buf.data[base+2]=6; buf.data[base+3]=255
    for row in range(1, ROWS+1):
        y = HDR_H + row*(CELL_H+LABEL_H) - LABEL_H
        for x in range(W):
            base=(y*W+x)*4
            buf.data[base]=8; buf.data[base+1]=10; buf.data[base+2]=6; buf.data[base+3]=255

    return buf


if __name__ == "__main__":
    import time
    gimp_root = Path(sys.argv[1]) if len(sys.argv)>1 else _find_gimp_data()
    out_path  = Path(sys.argv[2]) if len(sys.argv)>2 else Path("/tmp/bestiary_fauna.png")
    if gimp_root is None: print("No GIMP data found."); sys.exit(1)

    print(f"GIMP: {gimp_root}")
    registry = AssetRegistry()
    for sub in ("brushes","dynamics","palettes"):
        p = gimp_root/sub
        if p.exists(): registry.load_from_directory(p)
    s = registry.summary()
    print(f"shapes={s['shapes']} errors={s['errors']}")

    t0=time.time()
    buf=build_fauna_sheet(registry)
    save_png(buf, out_path)
    print(f"✓  {out_path}  ({W}x{H})  ({time.time()-t0:.1f}s)")
    print()
    print("Pass: each creature reads as itself without needing the label.")
    print("Fail: creature reads as abstract marks or blob.")
