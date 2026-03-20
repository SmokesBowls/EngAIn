"""
demo_bestiary_flora_sheet.py — Trixel Bestiary: Flora Sheet

Tests whether the engine can describe living plant forms.

Subjects (8):
  mushroom       — cap arc over stem, spotted
  flower         — centre disc + petal arcs, stem
  reed           — tall tapering vertical + seed head
  shrub          — clustered irregular mass, ground anchored
  vine           — curved climbing line + leaf stamps
  fungal cluster — group of 4-7 varied mushrooms close together
  shore plant    — fan of upward bristle strokes at water edge
  fern           — central spine + paired frond arcs each side
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
from engine_debug_mr import text, save_png
from trixel_brush_adapter import AssetRegistry
from world_tree_mr import _find_gimp_data

CELL_W = 160; CELL_H = 140
COLS = 4; ROWS = 2; LABEL_H = 22; HDR_H = 28
W = CELL_W * COLS
H = HDR_H + ROWS * (CELL_H + LABEL_H)

def _lcg(s):  return (s*1664525+1013904223)&0xFFFFFFFF
def _lcgf(s): return _lcg(s)/0x100000000

def _px(buf,x,y,r,g,b):
    if 0<=x<W and 0<=y<H:
        base=(y*W+x)*4; buf.data[base]=r; buf.data[base+1]=g; buf.data[base+2]=b; buf.data[base+3]=255

def _fill_cell(buf,cx,cy,r,g,b):
    for y in range(cy,cy+CELL_H):
        for x in range(cx,cx+CELL_W):
            base=(y*W+x)*4; buf.data[base]=r; buf.data[base+1]=g; buf.data[base+2]=b; buf.data[base+3]=255

def _ellipse(buf,cx,cy,rx,ry,r,g,b,fill=True,border=True):
    for y in range(int(cy-ry)-1,int(cy+ry)+2):
        for x in range(int(cx-rx)-1,int(cx+rx)+2):
            dist=((x-cx)/max(rx,1))**2+((y-cy)/max(ry,1))**2
            if fill and dist<=1.0: _px(buf,x,y,r,g,b)
            elif border and 0.82<=dist<=1.18: _px(buf,x,y,max(0,r-20),max(0,g-20),max(0,b-20))

def _arc(buf,cx,cy,rx,ry,a0,a1,r,g,b,thickness=2):
    steps=max(20,int(abs(a1-a0)*max(rx,ry)*0.8))
    for i in range(steps+1):
        t=a0+(a1-a0)*i/steps
        x=int(cx+rx*math.cos(t)); y=int(cy+ry*math.sin(t))
        for dt in range(-thickness//2,thickness//2+1):
            _px(buf,x+dt,y,r,g,b); _px(buf,x,y+dt,r,g,b)

def _line(buf,x0,y0,x1,y1,r,g,b,thickness=1):
    dx=abs(x1-x0); dy=abs(y1-y0)
    sx=1 if x1>x0 else -1; sy=1 if y1>y0 else -1
    err=dx-dy; cx,cy=x0,y0
    while True:
        for t in range(thickness): _px(buf,cx+t,cy,r,g,b); _px(buf,cx,cy+t,r,g,b)
        if cx==x1 and cy==y1: break
        e2=2*err
        if e2>-dy: err-=dy; cx+=sx
        if e2<dx:  err+=dx; cy+=sy

def _texture(buf,shape,pixels,x0,y0,x1,y1,r,g,b,r_scale=0.25,pressure=0.25,seed=0):
    if not shape or not pixels: return
    from engine_mr import DynamicsModifiers
    mods=DynamicsModifiers(opacity=pressure,size_scale=r_scale)
    s=seed; n=max(1,(x1-x0)*(y1-y0)//350)
    for i in range(n):
        s=_lcg(s+i*71); fx=x0+int(_lcgf(s)*(x1-x0))
        s=_lcg(s);       fy=y0+int(_lcgf(s)*(y1-y0))
        if x0<=fx<x1 and y0<=fy<y1:
            _render_bitmap(buf,float(fx),float(fy),shape,mods,r,g,b,pixels)

def _cell_origin(idx):
    col=idx%COLS; row=idx//COLS
    return col*CELL_W, HDR_H+row*(CELL_H+LABEL_H)

def _cell_label(buf,idx,name):
    cx,cy=_cell_origin(idx)
    text(buf,cx+4,cy+CELL_H+4,name.upper(),colour=(120,155,90))

# ---------------------------------------------------------------------------
# Plant drawers
# ---------------------------------------------------------------------------

def draw_mushroom(buf,cx,cy,charcoal,c_px,seed=10):
    C_CAP  = (175, 62, 38); C_CAP_U = (210, 85, 52)
    C_STEM = (195, 178, 148); C_SPOT = (235, 225, 210)
    C_GILL = (155, 55, 30)

    configs = [(cx+28,cy+95,12,8,18,1.0),(cx+80,cy+88,20,13,28,1.6),(cx+132,cy+80,28,18,40,2.2)]
    for bx,by,rx,ry,stem_h,sc in configs:
        # Stem
        _ellipse(buf,bx,by,int(rx*0.35),int(stem_h*0.45),C_STEM[0],C_STEM[1],C_STEM[2])
        # Cap (arch — top half of ellipse only)
        cap_cy=by-int(stem_h*0.4)
        _ellipse(buf,bx,cap_cy,rx,ry,C_CAP[0],C_CAP[1],C_CAP[2])
        # Underside gills (flat bottom of cap)
        _line(buf,bx-rx,cap_cy,bx+rx,cap_cy,C_GILL[0],C_GILL[1],C_GILL[2])
        for gi in range(-int(rx*0.7),int(rx*0.7),max(2,int(rx*0.25))):
            _line(buf,bx+gi,cap_cy,bx+gi,cap_cy+int(ry*0.2),C_GILL[0],C_GILL[1],C_GILL[2])
        # Spots
        s=seed+int(sc*100)
        for _ in range(max(2,int(3*sc))):
            s=_lcg(s); sx_=bx+int((_lcgf(s)-0.5)*rx*1.2)
            s=_lcg(s); sy_=cap_cy-int(_lcgf(s)*ry*0.85)
            sr=max(1,int(sc*1.2))
            _ellipse(buf,sx_,sy_,sr,sr,C_SPOT[0],C_SPOT[1],C_SPOT[2])
        # Cap highlight
        _arc(buf,bx-int(rx*0.2),cap_cy-int(ry*0.3),int(rx*0.45),int(ry*0.4),
             math.pi*1.2,math.pi*1.8,C_CAP_U[0],C_CAP_U[1],C_CAP_U[2])
    if charcoal and c_px:
        bx,by,rx,ry,sh,sc=configs[2]
        _texture(buf,charcoal,c_px,bx-rx,by-sh-ry,bx+rx,by,
                 C_CAP[0]-20,C_CAP[1]-15,C_CAP[2]-10,r_scale=0.25,pressure=0.22,seed=seed)


def draw_flower(buf,cx,cy,bristle,b_px,seed=20):
    C_PETAL=[(225,85,95),(245,155,60),(250,235,80),(140,185,230),(195,120,200)]
    C_DISC =(238,200,42); C_DISC_D=(185,145,22)
    C_STEM =(48,88,35); C_LEAF=(55,98,40)

    configs=[(cx+28,cy+95,10,1.0),(cx+80,cy+85,17,1.6),(cx+132,cy+75,24,2.2)]
    for i,(bx,by,r,sc) in enumerate(configs):
        petal_col=C_PETAL[i%len(C_PETAL)]
        # Stem
        _line(buf,bx,by,bx,by+int(sc*18),C_STEM[0],C_STEM[1],C_STEM[2],thickness=max(1,int(sc)))
        # Leaf on stem
        lx=bx+int(sc*5); ly=by+int(sc*10)
        _ellipse(buf,lx+int(sc*3),ly,int(sc*6),int(sc*3),C_LEAF[0],C_LEAF[1],C_LEAF[2])
        # Petals (6, radiating)
        n_petals=6
        for pi in range(n_petals):
            ang=pi*2*math.pi/n_petals
            px_=bx+int(math.cos(ang)*r*1.55)
            py_=by+int(math.sin(ang)*r*1.55)
            _ellipse(buf,px_,py_,int(r*0.52),int(r*0.35),
                     petal_col[0],petal_col[1],petal_col[2])
        # Centre disc
        _ellipse(buf,bx,by,int(r*0.5),int(r*0.5),C_DISC[0],C_DISC[1],C_DISC[2])
        _ellipse(buf,bx,by,int(r*0.28),int(r*0.28),C_DISC_D[0],C_DISC_D[1],C_DISC_D[2],border=False)


def draw_reed(buf,cx,cy,bristle,b_px,seed=30):
    C_STALK=(62,88,42); C_HEAD=(88,62,38); C_HEAD_L=(110,80,50)
    C_LEAF=(52,78,35)

    for ri,(bx,by_base,h,sc) in enumerate([
        (cx+28,cy+CELL_H-8,55,1.0),(cx+70,cy+CELL_H-8,75,1.4),
        (cx+105,cy+CELL_H-8,68,1.2),(cx+138,cy+CELL_H-8,58,1.0)]):
        wave=math.sin(ri*1.2)*3
        # Stalk
        for y in range(int(sc*h)):
            t=y/max(sc*h,1)
            stalk_x=bx+int(math.sin(t*math.pi*0.8)*wave)
            _px(buf,stalk_x,by_base-y,C_STALK[0],C_STALK[1],C_STALK[2])
            if sc>1.1:
                _px(buf,stalk_x+1,by_base-y,C_STALK[0]-10,C_STALK[1]-10,C_STALK[2]-10)
        # Seed head (oval at top)
        top_y=by_base-int(sc*h)
        _ellipse(buf,bx+int(wave*0.3),top_y,max(2,int(sc*4)),max(3,int(sc*9)),
                 C_HEAD[0],C_HEAD[1],C_HEAD[2])
        # Seed head texture
        _arc(buf,bx+int(wave*0.3)-int(sc*2),top_y,int(sc*2.5),int(sc*3),
             math.pi*1.1,math.pi*1.9,C_HEAD_L[0],C_HEAD_L[1],C_HEAD_L[2])
        # Side leaf (mid-height)
        leaf_y=by_base-int(sc*h*0.45)
        leaf_dx=int(sc*12)*(-1 if ri%2==0 else 1)
        _arc(buf,bx+leaf_dx//2,leaf_y,abs(leaf_dx),int(sc*4),
             math.pi*(0.8 if ri%2==1 else 1.2),
             math.pi*(1.2 if ri%2==1 else 1.8),
             C_LEAF[0],C_LEAF[1],C_LEAF[2])
    if bristle and b_px:
        _texture(buf,bristle,b_px,cx,cy+CELL_H-12,cx+CELL_W,cy+CELL_H,
                 C_STALK[0]-10,C_STALK[1]-10,C_STALK[2]-10,r_scale=0.15,pressure=0.20,seed=seed)


def draw_shrub(buf,cx,cy,bristle,b_px,seed=40):
    C_OUTER=(35,68,25); C_MID=(48,88,35); C_LIGHT=(62,108,45); C_DARK=(22,45,16)
    C_TWIG=(55,40,22)

    bx,by=cx+CELL_W//2, cy+CELL_H-22
    # Ground anchor
    _line(buf,bx-20,by,bx+20,by,C_TWIG[0],C_TWIG[1],C_TWIG[2],thickness=3)
    # Main mass — overlapping irregular ellipses
    s=seed
    masses=[]
    for i in range(7):
        s=_lcg(s+i*83)
        mx=bx+int((_lcgf(s)-0.5)*38)
        s=_lcg(s); my=by-20-int(_lcgf(s)*28)
        s=_lcg(s); mrx=18+int(_lcgf(s)*16)
        s=_lcg(s); mry=14+int(_lcgf(s)*12)
        col_v=int(_lcgf(_lcg(s))*3)
        cols=[(C_OUTER),(C_MID),(C_DARK)][col_v]
        _ellipse(buf,mx,my,mrx,mry,cols[0],cols[1],cols[2])
        masses.append((mx,my,mrx,mry))
    # Top highlight clusters
    s=seed+100
    for i in range(4):
        s=_lcg(s+i*61)
        hx=bx+int((_lcgf(s)-0.5)*20)
        s=_lcg(s); hy=by-45-int(_lcgf(s)*15)
        _ellipse(buf,hx,hy,10,8,C_LIGHT[0],C_LIGHT[1],C_LIGHT[2],border=False)
    # Bristle texture over mass
    if bristle and b_px:
        _texture(buf,bristle,b_px,bx-40,by-55,bx+40,by,
                 C_DARK[0],C_DARK[1],C_DARK[2],r_scale=0.18,pressure=0.22,seed=seed)
    # Second smaller shrub
    bx2=bx-38
    _ellipse(buf,bx2,by-15,14,10,C_OUTER[0],C_OUTER[1],C_OUTER[2])
    _ellipse(buf,bx2,by-25,10,8,C_MID[0],C_MID[1],C_MID[2])


def draw_vine(buf,cx,cy,charcoal,c_px,seed=50):
    C_VINE=(42,65,22); C_LEAF=(52,90,32); C_LEAF_V=(38,72,24); C_TENDRIL=(48,72,28)

    # Main climbing vine — S-curve from bottom to top
    s=seed
    vine_pts=[]
    for step in range(30):
        t=step/29
        vx=cx+int(CELL_W*0.3+math.sin(t*math.pi*2.5+0.8)*CELL_W*0.28)
        vy=cy+CELL_H-8-int(t*(CELL_H-22))
        vine_pts.append((vx,vy))
    for i in range(len(vine_pts)-1):
        _line(buf,vine_pts[i][0],vine_pts[i][1],vine_pts[i+1][0],vine_pts[i+1][1],
              C_VINE[0],C_VINE[1],C_VINE[2],thickness=2)
    # Second vine
    for step in range(20):
        t=step/19
        vx=cx+int(CELL_W*0.65+math.sin(t*math.pi*1.8+2.0)*CELL_W*0.18)
        vy=cy+CELL_H-8-int(t*(CELL_H*0.65))
        if step>0: _line(buf,prev_vx,prev_vy,vx,vy,C_VINE[0],C_VINE[1],C_VINE[2])
        prev_vx,prev_vy=vx,vy
    # Leaves — heart-shaped ovals at intervals
    s=seed+10
    for step in range(0,len(vine_pts)-1,4):
        vx,vy=vine_pts[step]
        s=_lcg(s+step*53)
        lx_off=int((_lcgf(s)-0.5)*18)
        s=_lcg(s); ly_off=int((_lcgf(s)-0.5)*12)
        leaf_col=C_LEAF if _lcgf(_lcg(s))>0.4 else C_LEAF_V
        lrx=6+int(_lcgf(s)*6); lry=4+int(_lcgf(s)*5)
        _ellipse(buf,vx+lx_off,vy+ly_off,lrx,lry,leaf_col[0],leaf_col[1],leaf_col[2])
        # Midrib
        _line(buf,vx+lx_off-lrx+2,vy+ly_off,vx+lx_off+lrx-2,vy+ly_off,
              leaf_col[0]-12,leaf_col[1]-12,leaf_col[2]-12)
        # Tendril curl
        if step%8==0:
            _arc(buf,vx+lx_off+lrx,vy+ly_off,4,3,0,math.pi*1.5,
                 C_TENDRIL[0],C_TENDRIL[1],C_TENDRIL[2])


def draw_fungal_cluster(buf,cx,cy,charcoal,c_px,seed=60):
    C_CAPS=[(175,62,38),(145,52,30),(130,145,55),(88,55,30),(165,80,42)]
    C_STEM=(195,178,148); C_SPOT=(235,225,210)

    # 6 mushrooms of varying size packed together
    positions=[(cx+32,cy+CELL_H-12,9,6,14),(cx+58,cy+CELL_H-12,14,9,20),
               (cx+88,cy+CELL_H-12,11,7,16),(cx+112,cy+CELL_H-12,8,5,12),
               (cx+132,cy+CELL_H-12,13,8,19),(cx+75,cy+CELL_H-8,17,11,25)]
    for i,(bx,by,rx,ry,sh) in enumerate(positions):
        cap_col=C_CAPS[i%len(C_CAPS)]
        # Stem
        _ellipse(buf,bx,by-int(sh*0.3),int(rx*0.32),int(sh*0.48),C_STEM[0],C_STEM[1],C_STEM[2])
        # Cap
        cap_cy=by-int(sh*0.55)
        _ellipse(buf,bx,cap_cy,rx,ry,cap_col[0],cap_col[1],cap_col[2])
        # Gill line
        _line(buf,bx-rx,cap_cy,bx+rx,cap_cy,max(0,cap_col[0]-30),max(0,cap_col[1]-20),max(0,cap_col[2]-15))
        # Spots (1-3 per cap)
        s=seed+i*37
        for _ in range(1+int(rx/8)):
            s=_lcg(s); spx=bx+int((_lcgf(s)-0.5)*rx*1.1)
            s=_lcg(s); spy=cap_cy-int(_lcgf(s)*ry*0.8)
            _px(buf,spx,spy,C_SPOT[0],C_SPOT[1],C_SPOT[2])
    # Ground/mycelium
    if charcoal and c_px:
        _texture(buf,charcoal,c_px,cx+20,cy+CELL_H-6,cx+CELL_W-20,cy+CELL_H,
                 48,38,22,r_scale=0.20,pressure=0.25,seed=seed)


def draw_shore_plant(buf,cx,cy,bristle,b_px,seed=70):
    C_STALK=(48,88,50); C_PALE=(75,118,68); C_DARK=(32,65,35)
    C_WATER=(28,52,88); C_SAND=(148,128,85)

    # Water line and sand
    water_y=cy+CELL_H-28
    for y in range(water_y,cy+CELL_H):
        for x in range(cx,cx+CELL_W):
            t=(y-water_y)/max(CELL_H-28,1)
            base=(y*W+x)*4
            buf.data[base]=int(28+t*8); buf.data[base+1]=int(52+t*15); buf.data[base+2]=int(88+t*20)
    # Sand band
    for y in range(water_y-6,water_y):
        for x in range(cx,cx+CELL_W):
            base=(y*W+x)*4; buf.data[base]=C_SAND[0]; buf.data[base+1]=C_SAND[1]; buf.data[base+2]=C_SAND[2]

    # Fan of upward blades from water edge
    n_blades=14
    s=seed
    for bi in range(n_blades):
        s=_lcg(s+bi*71)
        bx=cx+12+int(_lcgf(s)*(CELL_W-24))
        s=_lcg(s); blade_h=22+int(_lcgf(s)*35)
        s=_lcg(s); lean=int((_lcgf(s)-0.5)*12)
        s=_lcg(s); col_choice=_lcgf(s)
        col=C_PALE if col_choice>0.5 else (C_STALK if col_choice>0.2 else C_DARK)
        thickness=1 if blade_h<30 else 2
        # Blade curves slightly
        for step in range(blade_h):
            t=step/blade_h
            bx_t=bx+lean+int(math.sin(t*math.pi)*lean*0.4)
            _px(buf,bx_t,water_y-step-4,col[0],col[1],col[2])
            if thickness==2: _px(buf,bx_t+1,water_y-step-4,col[0]-8,col[1]-8,col[2]-8)
        # Blade tip (taper to 1px)
        _px(buf,bx+lean+int(lean*0.4),water_y-blade_h-4,col[0]+15,col[1]+15,col[2]+10)
    # Bristle texture on sand
    if bristle and b_px:
        _texture(buf,bristle,b_px,cx,water_y-8,cx+CELL_W,water_y,
                 C_SAND[0]-20,C_SAND[1]-20,C_SAND[2]-20,r_scale=0.16,pressure=0.18,seed=seed)


def draw_fern(buf,cx,cy,charcoal,c_px,seed=80):
    C_FROND=(38,85,35); C_FROND_L=(52,108,45); C_SPINE=(30,68,28); C_NEW=(68,128,52)

    bx,by=cx+CELL_W//2, cy+CELL_H-18
    # Central spine
    spine_h=int(CELL_H*0.75)
    spine_pts=[(bx+int(math.sin(t*math.pi*0.6)*5),by-int(t*spine_h))
               for t in [i/12 for i in range(13)]]
    for i in range(len(spine_pts)-1):
        _line(buf,spine_pts[i][0],spine_pts[i][1],
              spine_pts[i+1][0],spine_pts[i+1][1],
              C_SPINE[0],C_SPINE[1],C_SPINE[2],thickness=2)
    # Paired fronds along spine
    frond_pairs=[(0.15,22),(0.28,26),(0.42,28),(0.55,24),(0.68,20),(0.80,15),(0.90,10)]
    for t_frac,frond_len in frond_pairs:
        si=int(t_frac*12)
        if si>=len(spine_pts): continue
        sx,sy=spine_pts[si]
        for side in [-1,1]:
            # Frond arc
            f_rx=frond_len; f_ry=int(frond_len*0.3)
            # Angle of frond relative to spine direction
            if si+1<len(spine_pts):
                dx=spine_pts[si+1][0]-sx; dy=spine_pts[si+1][1]-sy
                spine_ang=math.atan2(dy,dx)
            else:
                spine_ang=-math.pi/2
            frond_ang=spine_ang+side*math.pi*0.55
            # Draw frond as a series of small leaflets
            n_leaflets=max(3,frond_len//5)
            for li in range(n_leaflets):
                lt=li/max(n_leaflets-1,1)
                lx=int(sx+math.cos(frond_ang)*frond_len*lt)
                ly=int(sy+math.sin(frond_ang)*frond_len*lt)
                leaflet_r=max(1,int((1-lt*0.6)*4))
                col=C_FROND if lt<0.6 else C_FROND_L
                _ellipse(buf,lx,ly,leaflet_r,max(1,leaflet_r-1),col[0],col[1],col[2])
    # New frond (curled fiddlehead at top)
    if len(spine_pts)>0:
        fx,fy=spine_pts[-1]
        _arc(buf,fx,fy,5,5,0,math.pi*1.8,C_NEW[0],C_NEW[1],C_NEW[2],thickness=2)
    # Texture on frond mass
    if charcoal and c_px:
        _texture(buf,charcoal,c_px,bx-35,by-spine_h,bx+35,by,
                 C_SPINE[0],C_SPINE[1],C_SPINE[2],r_scale=0.22,pressure=0.18,seed=seed)

# ---------------------------------------------------------------------------
# Sheet assembly
# ---------------------------------------------------------------------------

PLANTS = [
    ("mushroom",       draw_mushroom),
    ("flower",         draw_flower),
    ("reed",           draw_reed),
    ("shrub",          draw_shrub),
    ("vine",           draw_vine),
    ("fungal cluster", draw_fungal_cluster),
    ("shore plant",    draw_shore_plant),
    ("fern",           draw_fern),
]


def build_flora_sheet(registry: AssetRegistry) -> SurfaceBuffer:
    buf = SurfaceBuffer.blank(W, H)
    # Background — dark earth tones
    for y in range(H):
        for x in range(W):
            base=(y*W+x)*4; t=y/H
            buf.data[base]=int(10+t*4); buf.data[base+1]=int(12+t*5); buf.data[base+2]=int(8+t*3); buf.data[base+3]=255
    # Header
    for y in range(HDR_H):
        for x in range(W):
            base=(y*W+x)*4; buf.data[base]=16; buf.data[base+1]=20; buf.data[base+2]=12; buf.data[base+3]=255
    text(buf,6,6,"TRIXEL BESTIARY — FLORA SHEET",colour=(120,175,90))
    text(buf,6,16,"organic plant forms  |  pass = recognisable silhouette without label",colour=(78,110,58))

    from engine_mr import _load_bitmap
    charcoal=registry.shapes.get("Charcoal-01"); c_px=_load_bitmap(charcoal) if charcoal else None
    bristle=registry.shapes.get("Bristles-01");  b_px=_load_bitmap(bristle)  if bristle  else None

    shape_map={
        "mushroom":      (charcoal,c_px),
        "flower":        (bristle, b_px),
        "reed":          (bristle, b_px),
        "shrub":         (bristle, b_px),
        "vine":          (charcoal,c_px),
        "fungal cluster":(charcoal,c_px),
        "shore plant":   (bristle, b_px),
        "fern":          (charcoal,c_px),
    }
    draw_map={n:fn for n,fn in PLANTS}

    for idx,(name,_) in enumerate(PLANTS):
        cx,cy=_cell_origin(idx)
        row=idx//COLS; bg=12+row*3
        _fill_cell(buf,cx,cy,bg,bg+3,bg-2)
        shape,pixels=shape_map[name]
        draw_map[name](buf,cx,cy,shape,pixels,seed=idx*100)
        _cell_label(buf,idx,name)

    # Grid dividers
    for col in range(1,COLS):
        for y in range(H):
            base=(y*W+col*CELL_W)*4; buf.data[base]=7; buf.data[base+1]=9; buf.data[base+2]=5; buf.data[base+3]=255
    for row in range(1,ROWS+1):
        y=HDR_H+row*(CELL_H+LABEL_H)-LABEL_H
        for x in range(W):
            base=(y*W+x)*4; buf.data[base]=7; buf.data[base+1]=9; buf.data[base+2]=5; buf.data[base+3]=255

    return buf


if __name__ == "__main__":
    import time
    gimp_root=Path(sys.argv[1]) if len(sys.argv)>1 else _find_gimp_data()
    out_path =Path(sys.argv[2]) if len(sys.argv)>2 else Path("/tmp/bestiary_flora.png")
    if gimp_root is None: print("No GIMP data."); sys.exit(1)
    print(f"GIMP: {gimp_root}")
    registry=AssetRegistry()
    for sub in ("brushes","dynamics","palettes"):
        p=gimp_root/sub
        if p.exists(): registry.load_from_directory(p)
    s=registry.summary(); print(f"shapes={s['shapes']} errors={s['errors']}")
    t0=time.time()
    buf=build_flora_sheet(registry)
    save_png(buf,out_path)
    print(f"✓  {out_path}  ({W}x{H})  ({time.time()-t0:.1f}s)")
