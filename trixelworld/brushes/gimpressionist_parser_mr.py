"""
gimpressionist_parser_mr.py — GIMP Gimpressionist Parser

Parses Gimpressionist assets: 
- Presets (text config files)
- Brushes (PGM/PPM images)
- Papers (PGM/PPM images)
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import re

@dataclass
class ParsedImpressionistPreset:
    name: str
    desc: str
    
    brush_ref: str
    paper_ref: str
    
    brush_relief: float
    brush_density: float
    brush_gamma: float
    brush_aspect: float
    
    paper_relief: float
    paper_scale: float
    paper_invert: bool
    paper_overlay: bool
    
    orient_num: int
    orient_first: float
    orient_last: float
    orient_type: int
    
    size_num: int
    size_first: float
    size_last: float
    size_type: int
    
    general_bg_type: int
    general_tileable: bool
    general_drop_shadow: bool
    general_shadow_darkness: float

@dataclass
class ParsedPnm:
    name: str
    width: int
    height: int
    depth: int # 1 for grayscale, 3 for RGB
    data: bytes
    filepath: Path


def parse_pnm(path: Path | str) -> ParsedPnm:
    """Parses PGM (P5) or PPM (P6) headers and data."""
    if isinstance(path, str):
        path = Path(path)
        
    with open(path, "rb") as f:
        magic = f.readline().strip()
        if magic not in (b"P5", b"P6"):
            raise ValueError(f"Not a valid PGM/PPM file: {path}")
            
        depth = 1 if magic == b"P5" else 3
        
        # Read next line, skip comments
        while True:
            line = f.readline()
            if not line.startswith(b"#"):
                break
                
        dim = line.strip().split()
        width = int(dim[0])
        height = int(dim[1])
        
        # usually 255 follows
        maxval_line = f.readline().strip()
        
        data = f.read()
        
    return ParsedPnm(
        name=path.stem,
        width=width,
        height=height,
        depth=depth,
        data=data,
        filepath=path
    )


def parse_impressionist_preset(path: Path | str) -> ParsedImpressionistPreset:
    if isinstance(path, str):
        path = Path(path)
        
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    
    if not lines or lines[0] != "Preset":
        raise ValueError(f"Not a valid Gimpressionist preset: {path}")
        
    params = {}
    for line in lines[1:]:
        if "=" in line:
            k, v = line.split("=", 1)
            params[k.strip()] = v.strip()
            
    def _float(key, default=0.0):
        return float(params.get(key, default))
        
    def _int(key, default=0):
        return int(params.get(key, default))
        
    def _bool(key, default=0):
        return bool(int(params.get(key, default)))
        
    def _extract_stem(v: str) -> str:
        if not v: return ""
        # e.g. 'Brushes/sphere.ppm' -> 'sphere'
        p = Path(v)
        return p.stem

    return ParsedImpressionistPreset(
        name=path.stem,
        desc=params.get("desc", ""),
        brush_ref=_extract_stem(params.get("selectedbrush", "")),
        paper_ref=_extract_stem(params.get("selectedpaper", "")),
        
        brush_relief=_float("brushrelief"),
        brush_density=_float("brushdensity"),
        brush_gamma=_float("brushgamma"),
        brush_aspect=_float("brushaspect"),
        
        paper_relief=_float("paperrelief"),
        paper_scale=_float("paperscale"),
        paper_invert=_bool("paperinvert"),
        paper_overlay=_bool("paperoverlay"),
        
        orient_num=_int("orientnum"),
        orient_first=_float("orientfirst"),
        orient_last=_float("orientlast"),
        orient_type=_int("orienttype"),
        
        size_num=_int("sizenum"),
        size_first=_float("sizefirst"),
        size_last=_float("sizelast"),
        size_type=_int("sizetype"),
        
        general_bg_type=_int("generalbgtype"),
        general_tileable=_bool("generaltileable"),
        general_drop_shadow=_bool("generaldropshadow"),
        general_shadow_darkness=_float("generalshadowdarkness"),
    )
