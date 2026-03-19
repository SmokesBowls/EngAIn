"""
ggr_parser_mr.py — GIMP Gradient (.ggr) Parser

Parses GIMP gradient files into a list of geometric color segments. 
GIMP gradients are piecewise functions. Each segment defines a left, middle, 
and right coordinate [0,1], plus left and right RGBA colors, and a blending type.

Format:
    GIMP Gradient
    Name: <name>
    <segment_count>
    L M R r0 g0 b0 a0 r1 g1 b1 a1 blend_type color_mode
"""

from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class GgrSegment:
    l: float
    m: float
    r: float
    r0: float; g0: float; b0: float; a0: float
    r1: float; g1: float; b1: float; a1: float
    blend_type: int
    color_mode: int

@dataclass(frozen=True)
class GgrGradient:
    name: str
    segments: tuple[GgrSegment, ...]
    source_path: str

def parse_ggr(path: Path) -> GgrGradient:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    if not lines or not lines[0].startswith("GIMP Gradient"):
        raise ValueError("Not a valid GIMP Gradient file")

    name = "unnamed"
    segs = []

    for line in lines[1:]:
        if line.startswith("Name:"):
            name = line[5:].strip()
            continue
        
        parts = line.split()
        if len(parts) == 13:
            try:
                seg = GgrSegment(
                    l=float(parts[0]), m=float(parts[1]), r=float(parts[2]),
                    r0=float(parts[3]), g0=float(parts[4]), b0=float(parts[5]), a0=float(parts[6]),
                    r1=float(parts[7]), g1=float(parts[8]), b1=float(parts[9]), a1=float(parts[10]),
                    blend_type=int(parts[11]), color_mode=int(parts[12])
                )
                segs.append(seg)
            except ValueError:
                pass

    if not name or name.upper() in ("GIMP", ""):
        name = path.stem

    return GgrGradient(
        name=name,
        segments=tuple(segs),
        source_path=str(path),
    )
