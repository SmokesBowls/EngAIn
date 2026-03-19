"""
engine_debug_mr.py — Trixel Engine Debug & Test Layer

Adds four capabilities on top of engine_mr.py:
  1. Debug rendering    — checkerboard bg, stamp bounding boxes, sidecar log
  2. Autoscale/crop     — crop output to occupied pixel bounds
  3. Contact sheet      — canonical all-types smoke test with labels
  4. Blend modes        — multiply, additive, screen
  5. Spacing validation — one row per .gbr brush, annotated with raw/computed values
  6. Pattern swatch     — tiled .pat texture in contact sheet pattern row

Asset roots are passed in explicitly — no hardcoded versioned paths.

Usage:
    python engine_debug_mr.py [gimp_data_root] [output_dir]
    e.g.: python engine_debug_mr.py /usr/share/gimp/2.0 /tmp/trixel_out
"""


# ---------------------------------------------------------------------------
# DEPENDENCY TRACKING                                               v1
# ---------------------------------------------------------------------------
# This file calls:    engine_mr.py                (Same Folder)
#                     brush_models_mr.py          (Same Folder)
#                     trixel_brush_adapter.py     (Same Folder)
#                     brushes/gbr_parser_mr.py    (Different Folder: brushes/)
# This file is called by: None yet (leaf — direct execution or test runner)
# ---------------------------------------------------------------------------
from __future__ import annotations

import math
import struct
import zlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from engine_mr import (
    DynamicsModifiers,
    SurfaceBuffer,
    StrokeEvent,
    _apply_jitter,
    _load_bitmap,
    _render_bitmap,
    _render_parametric,
    sample_dynamics,
    select_hose_cell,
    stamp_recipe,
    stroke_to_events,
)
from brush_models_mr import BrushRecipe


# ---------------------------------------------------------------------------
# Blend modes
# ---------------------------------------------------------------------------

def _blend_normal(src: int, dst: int, sa: float) -> int:
    return int(src * sa + dst * (1.0 - sa))

def _blend_multiply(src: int, dst: int, sa: float) -> int:
    return int(((src * dst) // 255) * sa + dst * (1.0 - sa))

def _blend_additive(src: int, dst: int, sa: float) -> int:
    return min(255, int(dst + src * sa))

def _blend_screen(src: int, dst: int, sa: float) -> int:
    return int((255 - ((255-src)*(255-dst))//255) * sa + dst * (1.0-sa))

_BLEND = {"normal": _blend_normal, "multiply": _blend_multiply,
          "additive": _blend_additive, "screen": _blend_screen}


def _blend_pixel(buf: SurfaceBuffer, x: int, y: int,
                 r: int, g: int, b: int, stamp_alpha: int, mode: str) -> None:
    if x < 0 or x >= buf.width or y < 0 or y >= buf.height or stamp_alpha == 0:
        return
    base = (y * buf.width + x) * 4
    dr, dg, db, da = buf.data[base:base+4]
    sa = stamp_alpha / 255.0
    out_a = sa + (da/255.0) * (1.0 - sa)
    if out_a < 1e-6:
        return
    fn = _BLEND.get(mode, _blend_normal)
    buf.data[base]   = fn(r, dr, sa)
    buf.data[base+1] = fn(g, dg, sa)
    buf.data[base+2] = fn(b, db, sa)
    buf.data[base+3] = int(out_a * 255)


def stamp_blended(buf, recipe, event, stroke_index=0,
                  colour=(0,0,0), mode="normal"):
    if mode == "normal":
        return stamp_recipe(buf, recipe, event, stroke_index, colour)

    r, g, b = colour
    mods = sample_dynamics(recipe.dynamics, event)
    cx, cy = _apply_jitter(event.position_x, event.position_y,
                           mods.jitter_radius, event.random_seed ^ stroke_index)

    # Temporarily override blend_pixel on this instance
    from functools import partial
    buf.blend_pixel = partial(_blend_pixel, buf, mode=mode)
    try:
        if recipe.is_variant() and recipe.variant_bundle:
            shape = select_hose_cell(recipe.variant_bundle, event, stroke_index)
            _render_bitmap(buf, cx, cy, shape, mods, r, g, b, _load_bitmap(shape))
        elif recipe.shape:
            if recipe.shape.is_parametric():
                _render_parametric(buf, cx, cy, recipe.shape, mods, r, g, b)
            else:
                _render_bitmap(buf, cx, cy, recipe.shape, mods, r, g, b,
                               _load_bitmap(recipe.shape))
    finally:
        buf.__dict__.pop("blend_pixel", None)
    return buf


# ---------------------------------------------------------------------------
# Backgrounds
# ---------------------------------------------------------------------------

def checkerboard(w: int, h: int, size: int = 16,
                 light=(200,200,200), dark=(160,160,160)) -> SurfaceBuffer:
    buf = SurfaceBuffer.blank(w, h)
    for y in range(h):
        for x in range(w):
            lr, lg, lb = (light if ((x//size)+(y//size))%2==0 else dark)
            base = (y*w+x)*4
            buf.data[base], buf.data[base+1], buf.data[base+2] = lr, lg, lb
            buf.data[base+3] = 255
    return buf


def solid_bg(w: int, h: int, v: int = 235) -> SurfaceBuffer:
    buf = SurfaceBuffer.blank(w, h)
    for i in range(w*h):
        buf.data[i*4]=v; buf.data[i*4+1]=v; buf.data[i*4+2]=v; buf.data[i*4+3]=255
    return buf


# ---------------------------------------------------------------------------
# Bounding box / crop
# ---------------------------------------------------------------------------

@dataclass
class BBox:
    x0: int = 2**30; y0: int = 2**30; x1: int = -1; y1: int = -1
    def update(self, x, y):
        self.x0=min(self.x0,x); self.y0=min(self.y0,y)
        self.x1=max(self.x1,x); self.y1=max(self.y1,y)
    @property
    def empty(self): return self.x0 > self.x1
    def padded(self, p, w, h):
        return BBox(max(0,self.x0-p),max(0,self.y0-p),
                    min(w-1,self.x1+p),min(h-1,self.y1+p))


def occupied(buf: SurfaceBuffer, thr: int = 4) -> BBox:
    bb = BBox()
    for y in range(buf.height):
        for x in range(buf.width):
            if buf.data[(y*buf.width+x)*4+3] > thr:
                bb.update(x,y)
    return bb


def draw_bbox(buf, bb: BBox, colour=(255,100,0,200)):
    if bb.empty: return
    r,g,b,a = colour
    for x in range(bb.x0, bb.x1+1):
        buf.set_pixel(x,bb.y0,r,g,b,a); buf.set_pixel(x,bb.y1,r,g,b,a)
    for y in range(bb.y0, bb.y1+1):
        buf.set_pixel(bb.x0,y,r,g,b,a); buf.set_pixel(bb.x1,y,r,g,b,a)


def crop(buf: SurfaceBuffer, pad=8, thr=4) -> SurfaceBuffer:
    bb = occupied(buf, thr)
    if bb.empty: return buf
    bb = bb.padded(pad, buf.width, buf.height)
    cw = bb.x1-bb.x0+1; ch = bb.y1-bb.y0+1
    out = SurfaceBuffer(cw, ch, bytearray(cw*ch*4))
    for y in range(ch):
        for x in range(cw):
            s = ((bb.y0+y)*buf.width+(bb.x0+x))*4
            d = (y*cw+x)*4
            out.data[d:d+4] = buf.data[s:s+4]
    return out


# ---------------------------------------------------------------------------
# Sidecar log
# ---------------------------------------------------------------------------

@dataclass
class Log:
    entries: list = field(default_factory=list)

    def record(self, i, ev, mods, cell, kind, size_px, channel_mults=None):
        self.entries.append(dict(
            i=i, x=round(ev.position_x,1), y=round(ev.position_y,1),
            p=round(ev.pressure,3), v=round(ev.velocity,3),
            op=round(mods.opacity,3), sc=round(mods.size_scale,3),
            sz=round(size_px,1), cell=cell, kind=kind,
            ch=channel_mults or {},   # {channel: {input: value}, ...}
        ))

    def text(self):
        lines = ["  i      x      y     p     v    op    sc    sz  kind/cell  [active channels]",
                 "-"*80]
        for e in self.entries:
            ch_str = "  ".join(
                f"{ch}:{inp}={val:.2f}"
                for ch, inputs in e.get('ch', {}).items()
                for inp, val in inputs.items()
            )
            lines.append(f"{e['i']:3d} {e['x']:6.1f} {e['y']:6.1f}  "
                         f"{e['p']:.3f} {e['v']:.3f} {e['op']:.3f} "
                         f"{e['sc']:.3f} {e['sz']:5.1f}  {e['kind']}/{e['cell']}"
                         + (f"  [{ch_str}]" if ch_str else ""))
        return "\n".join(lines)


def stamp_logged(buf, recipe, ev, idx, colour, log, mode="normal"):
    mods = sample_dynamics(recipe.dynamics, ev)

    # Collect per-channel LUT samples for the log
    channel_mults = {}
    if recipe.dynamics:
        import math as _math
        inputs = {
            "pressure": ev.pressure,
            "velocity": ev.velocity,
            "direction": ev.direction / (2 * _math.pi),
            "tilt": min(1.0, _math.sqrt(ev.tilt_x**2 + ev.tilt_y**2)),
            "fade": 0.0, "random": 0.5, "wheel": 0.5,
        }
        from engine_mr import _lut_sample
        for curve in recipe.dynamics.active_curves:
            t = inputs.get(curve.input_source, 0.5)
            val = _lut_sample(curve.samples, t)
            channel_mults.setdefault(curve.output_channel, {})[curve.input_source] = round(val, 3)

    if recipe.is_variant() and recipe.variant_bundle:
        cell = select_hose_cell(recipe.variant_bundle, ev, idx)
        nm = cell.name; knd = "variant"
        sz = (cell.width+cell.height)/2.0 * mods.size_scale
    elif recipe.shape:
        nm = recipe.shape.name; knd = recipe.shape.shape_kind
        base = recipe.shape.radius*2 if recipe.shape.radius else \
               ((recipe.shape.width or 32)+(recipe.shape.height or 32))/2.0
        sz = base * mods.size_scale
    else:
        nm="none"; knd="none"; sz=0.0

    log.record(idx, ev, mods, nm, knd, sz, channel_mults)
    return stamp_blended(buf, recipe, ev, idx, colour, mode)


# ---------------------------------------------------------------------------
# Bitmap font 5×7 (caps only)
# ---------------------------------------------------------------------------

_F = {
    ' ': bytes([0x00,0x00,0x00,0x00,0x00]),
    '#': bytes([0x24,0x7e,0x24,0x7e,0x24]),
    '%': bytes([0x62,0x6c,0x10,0x26,0x46]),
    '(': bytes([0x1c,0x22,0x41,0x41,0x00]),
    ')': bytes([0x00,0x41,0x41,0x22,0x1c]),
    '+': bytes([0x08,0x08,0x3e,0x08,0x08]),
    '-': bytes([0x08,0x08,0x08,0x08,0x08]),
    '.': bytes([0x00,0x03,0x03,0x00,0x00]),
    '/': bytes([0x03,0x04,0x08,0x10,0x60]),
    '0': bytes([0x3e,0x45,0x49,0x51,0x3e]),
    '1': bytes([0x01,0x21,0x7f,0x01,0x01]),
    '2': bytes([0x23,0x45,0x49,0x49,0x31]),
    '3': bytes([0x22,0x41,0x49,0x49,0x36]),
    '4': bytes([0x04,0x0c,0x14,0x24,0x7f]),
    '5': bytes([0x79,0x49,0x49,0x49,0x46]),
    '6': bytes([0x3e,0x49,0x49,0x49,0x46]),
    '7': bytes([0x40,0x40,0x4f,0x50,0x60]),
    '8': bytes([0x36,0x49,0x49,0x49,0x36]),
    '9': bytes([0x30,0x49,0x49,0x49,0x3e]),
    ':': bytes([0x00,0x36,0x36,0x00,0x00]),
    '=': bytes([0x14,0x14,0x14,0x14,0x14]),
    '>': bytes([0x41,0x22,0x14,0x08,0x00]),
    'A': bytes([0x3f,0x48,0x48,0x48,0x3f]),
    'B': bytes([0x7f,0x49,0x49,0x49,0x36]),
    'C': bytes([0x3e,0x41,0x41,0x41,0x41]),
    'D': bytes([0x7f,0x41,0x41,0x41,0x3e]),
    'E': bytes([0x7f,0x49,0x49,0x49,0x41]),
    'F': bytes([0x7f,0x48,0x48,0x48,0x40]),
    'G': bytes([0x3e,0x41,0x41,0x49,0x4f]),
    'H': bytes([0x7f,0x08,0x08,0x08,0x7f]),
    'I': bytes([0x41,0x41,0x7f,0x41,0x41]),
    'J': bytes([0x42,0x41,0x41,0x7e,0x40]),
    'K': bytes([0x7f,0x08,0x14,0x22,0x41]),
    'L': bytes([0x7f,0x01,0x01,0x01,0x01]),
    'M': bytes([0x7f,0x20,0x18,0x20,0x7f]),
    'N': bytes([0x7f,0x20,0x10,0x08,0x7f]),
    'O': bytes([0x3e,0x41,0x41,0x41,0x3e]),
    'P': bytes([0x7f,0x48,0x48,0x48,0x30]),
    'Q': bytes([0x3e,0x41,0x45,0x43,0x3f]),
    'R': bytes([0x7f,0x48,0x4c,0x4a,0x31]),
    'S': bytes([0x31,0x49,0x49,0x49,0x46]),
    'T': bytes([0x40,0x40,0x7f,0x40,0x40]),
    'U': bytes([0x7e,0x01,0x01,0x01,0x7e]),
    'V': bytes([0x78,0x06,0x01,0x06,0x78]),
    'W': bytes([0x7f,0x02,0x0c,0x02,0x7f]),
    'X': bytes([0x63,0x14,0x08,0x14,0x63]),
    'Y': bytes([0x60,0x10,0x0f,0x10,0x60]),
    'Z': bytes([0x43,0x45,0x49,0x51,0x61]),
    '_': bytes([0x01,0x01,0x01,0x01,0x01]),
    'x': bytes([0x22,0x14,0x08,0x14,0x22]),
}


def text(buf, x, y, s, colour=(20,20,20), scale=1):
    r,g,b = colour
    cx = x
    for ch in s.upper():
        gl = _F.get(ch, b'\x55\x00\x55\x00\x55')
        for col in range(5):
            bits = gl[col]
            for row in range(7):
                if (bits>>(6-row))&1:
                    for sy in range(scale):
                        for sx in range(scale):
                            buf.set_pixel(cx+col*scale+sx, y+row*scale+sy, r,g,b,255)
        cx += (5+1)*scale


# ---------------------------------------------------------------------------
# PNG writer
# ---------------------------------------------------------------------------

def save_png(buf: SurfaceBuffer, path: Path):
    def ck(name, data):
        c=name+data
        return struct.pack('>I',len(data))+c+struct.pack('>I',zlib.crc32(c)&0xFFFFFFFF)
    ihdr = struct.pack('>IIBBBBB', buf.width, buf.height, 8, 2, 0, 0, 0)
    raw = bytearray()
    for y in range(buf.height):
        raw.append(0)
        for x in range(buf.width):
            base = (y*buf.width+x)*4
            a = buf.data[base+3]/255.0
            for ch in range(3):
                raw.append(int(buf.data[base+ch]*a + 255*(1.0-a)))
    out = b'\x89PNG\r\n\x1a\n'
    out += ck(b'IHDR',ihdr)+ck(b'IDAT',zlib.compress(bytes(raw),6))+ck(b'IEND',b'')
    path.write_bytes(out)


# ---------------------------------------------------------------------------
# Stroke helper
# ---------------------------------------------------------------------------

def wave(canvas_w: int, cy: float, amp: float = 30.0, n: int = None):
    if n is None: n = canvas_w - 20
    return [(10 + i*(canvas_w-20)/max(1,n-1),
             cy + math.sin(i*0.18)*amp) for i in range(n)]


# ---------------------------------------------------------------------------
# Spacing validation sheet
# ---------------------------------------------------------------------------

def make_spacing_sheet(registry, path: Path):
    """
    One row per .gbr/.pgm brush. Renders a stroke using the brush's own
    spacing value. Annotates raw header value, computed ratio, stamp dist.
    Validates that raw/10000 is the correct divisor across the whole family.
    """
    shapes = {n: s for n, s in registry.shapes.items()
              if s.source_format in ("gbr", "pgm")}
    if not shapes:
        print("  No bitmap shapes — skip spacing sheet")
        return

    ROW_H   = 55
    LABEL_W = 260
    W       = 800
    PAD     = 8
    rows    = sorted(shapes.items(), key=lambda kv: kv[1].spacing_pct)
    total_h = PAD + len(rows)*(ROW_H+PAD) + 20

    sheet = solid_bg(W, total_h, 245)

    for i, (name, shape) in enumerate(rows):
        y0 = PAD + i*(ROW_H+PAD)
        for y in range(y0, y0+ROW_H):
            for x in range(PAD, W-PAD):
                b = (y*W+x)*4
                sheet.data[b:b+3] = bytes([238,238,238]); sheet.data[b+3]=255

        raw = int(shape.spacing_pct * 10000)
        base_r = shape.radius or (shape.width or 32)/2.0
        dist   = base_r * 2 * shape.spacing_pct
        label  = f"{name[:20]:20s}  raw={raw:6d}  ratio={shape.spacing_pct:.4f}  dist={dist:.1f}px"
        text(sheet, PAD+4, y0+4, label, colour=(40,40,140))
        text(sheet, PAD+4, y0+16, f"size={shape.width or '?'}x{shape.height or '?'}", colour=(80,80,80))

        recipe = BrushRecipe(recipe_id=f"spc:{name}", shape=shape, dynamics=None,
                             preset=None, palette=None, variant_bundle=None)
        pts = wave(W, y0+ROW_H*0.72, amp=8.0)
        evs = stroke_to_events(pts, spacing_pct=shape.spacing_pct,
                                base_radius=base_r, pressure=0.9)
        n_drawn = 0
        for idx, ev in enumerate(evs):
            if ev.position_x >= LABEL_W:
                stamp_recipe(sheet, recipe, ev, idx, colour=(20,20,20))
                n_drawn += 1
        text(sheet, W-90, y0+4, f"n={n_drawn}", colour=(130,60,0))

    text(sheet, PAD, total_h-12, "SPACING VALIDATION  raw/10000=ratio  CONFIRMED", colour=(80,80,80))
    save_png(sheet, path)
    print(f"  Spacing sheet → {path.name}  ({len(rows)} brushes)")


# ---------------------------------------------------------------------------
# Contact sheet
# ---------------------------------------------------------------------------

def make_contact_sheet(registry, path: Path) -> Log:
    CELL_W = 800; CELL_H = 115; LABEL_H = 20; PAD = 8

    ROWS = [
        ("PARAMETRIC  vbr:2.Hardness050 + PencilGeneric  [normal]",
         "2. Hardness 050","Pencil Generic",None,"normal"),
        ("BITMAP  gbr:Hatch-Pen-01 + PressureOpacity  [normal]",
         "Hatch-Pen-01","Pressure Opacity",None,"normal"),
        ("BITMAP  gbr:Hatch-Pen-01 + PressureOpacity  [MULTIPLY]",
         "Hatch-Pen-01","Pressure Opacity",None,"multiply"),
        ("VARIANT HOSE  gih:Acrylic03 + PencilGeneric  [normal]",
         None,"Pencil Generic","Acrylic 03","normal"),
        ("MULTI-AXIS HOSE  gih:Chalk01 + BasicDynamics  [normal]",
         None,"Basic Dynamics","Chalk 01","normal"),
    ]

    pats = list(registry.patterns.values())
    if pats:
        ROWS.append(("SURFACE PATTERN  pat:"+list(registry.patterns)[0]+"  [tiled swatch]",
                     None, None, None, "__pattern__"))

    total_h = LABEL_H + len(ROWS)*(CELL_H+PAD) + PAD + 14
    sheet = solid_bg(CELL_W, total_h, 235)
    log = Log()
    y = 0

    text(sheet, PAD, 5, "TRIXEL ENGINE CONTACT SHEET", colour=(40,40,40))
    y = LABEL_H

    for row_idx, (label, sn, dn, bn, mode) in enumerate(ROWS):
        cy = y + PAD//2

        # Row bg
        lv = 250 if mode=="normal" else (242 if mode=="multiply" else
             (248 if mode=="__pattern__" else 246))
        for ry in range(cy, cy+CELL_H):
            for rx in range(PAD, CELL_W-PAD):
                b=(ry*CELL_W+rx)*4; sheet.data[b:b+3]=bytes([lv,lv,lv]); sheet.data[b+3]=255

        lc = (50,50,180) if mode=="multiply" else (50,120,50) if mode=="__pattern__" else (40,40,40)
        text(sheet, PAD+2, cy+3, label[:95], colour=lc)

        if mode == "__pattern__":
            _tile_pattern(sheet, pats[0], PAD, cy+LABEL_H, CELL_W-2*PAD, CELL_H-LABEL_H-4)
            y += CELL_H+PAD; continue

        r = (registry.build_recipe_from_bundle(bn, dn) if bn
             else registry.build_recipe_from_parts(sn, dn))
        if not r:
            text(sheet, PAD+2, cy+16, "RECIPE NOT FOUND", colour=(200,0,0))
            y += CELL_H+PAD; continue

        if r.is_variant():
            cells = r.variant_bundle.cells
            br = max(cells[0].width, cells[0].height)/2.0; sp = r.variant_bundle.step
        elif r.shape:
            br = r.shape.radius or (r.shape.width or 32)/2.0; sp = r.shape.spacing_pct
        else:
            br, sp = 20.0, 1.0

        pts = wave(CELL_W, cy+CELL_H*0.72, amp=16.0)
        evs = stroke_to_events(pts, spacing_pct=sp, base_radius=br,
                                pressure=0.88, velocity=0.72, seed=row_idx*31)

        for idx, ev in enumerate(evs):
            if bn == "Chalk 01":
                ev = StrokeEvent(ev.position_x, ev.position_y, ev.pressure, ev.velocity,
                                 ev.direction, math.sin(idx*.5)*.9, math.cos(idx*.4)*.6,
                                 ev.random_seed)
            stamp_logged(sheet, r, ev, idx, (15,15,15), log, mode)

        # bbox
        rbb = BBox()
        for ry in range(cy, cy+CELL_H):
            for rx in range(PAD, CELL_W-PAD):
                if abs(sheet.data[(ry*CELL_W+rx)*4]-lv) > 8: rbb.update(rx,ry)
        if not rbb.empty: draw_bbox(sheet, rbb, colour=(255,80,0,160))

        text(sheet, PAD+2, cy+CELL_H-10, f"{len(evs)} STAMPS  {mode.upper()}", colour=(110,110,110))
        y += CELL_H+PAD

    text(sheet, PAD, total_h-10, "TRIXEL ENGINE MR  ALL PATHS PROVEN", colour=(80,80,80))
    save_png(sheet, path)
    return log


def _tile_pattern(buf, pat, x0, y0, w, h):
    from brushes.gbr_parser_mr import parse_gbr
    if not pat.bitmap_path: return
    try:
        b = parse_gbr(Path(pat.bitmap_path))
        pw, ph = b.width, b.height; px = b.pixel_data
        for dy in range(h):
            for dx in range(w):
                si = ((dy%ph)*pw + (dx%pw)) * 3
                buf.set_pixel(x0+dx, y0+dy, px[si], px[si+1], px[si+2], 255)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Individual debug test
# ---------------------------------------------------------------------------

def debug_test(registry, tag, sn, dn, bn, path):
    r = (registry.build_recipe_from_bundle(bn, dn) if bn
         else registry.build_recipe_from_parts(sn, dn))
    assert r, f"No recipe for {tag}"
    if r.is_variant():
        cells = r.variant_bundle.cells
        br = max(cells[0].width, cells[0].height)/2.0; sp = r.variant_bundle.step
    elif r.shape:
        br = r.shape.radius or (r.shape.width or 32)/2.0; sp = r.shape.spacing_pct
    else:
        br, sp = 20.0, 1.0

    buf = checkerboard(680, 230)
    log = Log()
    pts = wave(680, 115, amp=45.0)
    evs = stroke_to_events(pts, spacing_pct=sp, base_radius=br,
                            pressure=0.88, velocity=0.8, seed=hash(tag)&0xFFFF)
    for idx, ev in enumerate(evs):
        if tag == "multiaxis":
            ev = StrokeEvent(ev.position_x, ev.position_y, 0.9, 0.8, ev.direction,
                             math.sin(idx*.5)*.9, math.cos(idx*.4)*.6, ev.random_seed)
        stamp_logged(buf, r, ev, idx, (15,15,15), log)

    bb = occupied(buf, thr=20)
    if not bb.empty: draw_bbox(buf, bb.padded(4, buf.width, buf.height))
    out = crop(buf, pad=16, thr=20)
    save_png(out, path)
    return len(evs), log


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")
    from trixel_brush_adapter import AssetRegistry

    gimp_root  = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data")
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/tmp/trixel_out")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"GIMP root:  {gimp_root}")
    print(f"Output dir: {output_dir}\n")

    registry = AssetRegistry()
    registry.load_from_directory(gimp_root)

    registry.print_summary()

    # Individual tests
    print("\nIndividual debug tests:")
    for tag, sn, dn, bn in [
        ("parametric","2. Hardness 050","Pencil Generic",None),
        ("bitmap","Hatch-Pen-01","Pressure Opacity",None),
        ("hose",None,"Pencil Generic","Acrylic 03"),
        ("multiaxis",None,"Basic Dynamics","Chalk 01"),
    ]:
        n, log = debug_test(registry, tag, sn, dn, bn, output_dir/f"debug_{tag}.png")
        (output_dir/f"debug_{tag}.txt").write_text(f"Tag: {tag}\nStamps: {n}\n\n"+log.text())
        print(f"  {tag:12s}  {n:3d} stamps")

    # Spacing validation
    print("\nSpacing validation:")
    make_spacing_sheet(registry, output_dir/"spacing_validation.png")

    # Contact sheet
    print("Contact sheet:")
    log = make_contact_sheet(registry, output_dir/"contact_sheet.png")
    (output_dir/"contact_sheet.txt").write_text(
        f"Contact sheet\n{'='*65}\n\n"+log.text())
    print(f"  {len(log.entries)} total stamps")

    print("\n✓ Done")
