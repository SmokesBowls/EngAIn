"""
gflare_parser_mr.py — GIMP GFlare Parser

Parses GIMP flare definitions which define 3 combined layers of glowing shapes:
- Glow
- Rays
- Second Flares (SecFlares)

Files typically lack extensions and start with 'GIMP GFlare 0.25'.
Space characters in gradient references are escaped as \\040.
"""

from dataclasses import dataclass
from pathlib import Path
import math

@dataclass
class ParsedGflare:
    name: str
    
    glow_opacity: float; glow_blend: str
    rays_opacity: float; rays_blend: str
    sec_opacity: float; sec_blend: str
    
    glow_radial: str; glow_angular: str; glow_size: str
    glow_radius: float; glow_rotation: float; glow_hue: float
    
    rays_radial: str; rays_angular: str; rays_size: str
    rays_radius: float; rays_rotation: float; rays_hue: float
    rays_count: int; rays_thickness: float
    
    sec_radial: str; sec_angular: str; sec_size: str
    sec_radius: float; sec_rotation: float; sec_hue: float
    
    shape: str; shape_edges: int; seed: int

def parse_gflare(path: Path | str) -> ParsedGflare:
    if isinstance(path, str):
        path = Path(path)
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    
    if not lines or not lines[0].startswith("GIMP GFlare"):
        raise ValueError("Not a valid GIMP GFlare file")
        
    def _grad(s: str) -> str:
        return s.replace("\\040", " ")
        
    def _floats(s: str) -> list[float]:
        return [float(x) for x in s.split()]
        
    # lines[1] -> 95.300003 NORMAL
    gp = lines[1].split();  glow_op = float(gp[0]); glow_bl = gp[1]
    rp = lines[2].split();  rays_op = float(rp[0]); rays_bl = rp[1]
    sp = lines[3].split();  sec_op  = float(sp[0]); sec_bl  = sp[1]
    
    gr1 = _floats(lines[7])
    rr1 = _floats(lines[11])
    rc = lines[12].split(); r_cnt = int(rc[0]); r_thk = float(rc[1])
    sr1 = _floats(lines[16])
    
    shp = lines[17].split()
    shape = shp[0]; shape_edges = int(shp[1]); seed = int(shp[2]) if len(shp)>2 else 1
    
    name = path.stem
    
    return ParsedGflare(
        name=name,
        glow_opacity=glow_op, glow_blend=glow_bl,
        rays_opacity=rays_op, rays_blend=rays_bl,
        sec_opacity=sec_op, sec_blend=sec_bl,
        
        glow_radial=_grad(lines[4]), glow_angular=_grad(lines[5]), glow_size=_grad(lines[6]),
        glow_radius=gr1[0], glow_rotation=gr1[1], glow_hue=gr1[2],
        
        rays_radial=_grad(lines[8]), rays_angular=_grad(lines[9]), rays_size=_grad(lines[10]),
        rays_radius=rr1[0], rays_rotation=rr1[1], rays_hue=rr1[2],
        rays_count=r_cnt, rays_thickness=r_thk,
        
        sec_radial=_grad(lines[13]), sec_angular=_grad(lines[14]), sec_size=_grad(lines[15]),
        sec_radius=sr1[0], sec_rotation=sr1[1], sec_hue=sr1[2],
        
        shape=shape, shape_edges=shape_edges, seed=seed
    )
