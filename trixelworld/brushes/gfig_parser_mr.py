"""
gfig_parser_mr.py — GIMP Gfig (.gfig) Geometric Figure Parser

Gfig files store vector-like geometric objects as named primitives
with control points. This parser extracts those objects so Trixel
can use them as branch scaffold curves, canopy envelope boundaries,
and trunk guides in world_tree_mr.py.

Gfig format (plain text):
    GFIG Version 0.1
    Name: <name>
    Version: <float>
    ObjCount: <int>
    <OPTIONS>...</OPTIONS>
    <PRIMITIVE_TYPE>
    x1 y1
    x2 y2
    ...
    [<EXTRA>
    value
    </EXTRA>]
    </PRIMITIVE_TYPE>
    ...

Primitives seen in stock files:
    ARC     — 3 control points (start, control, end of circular arc)
    LINE    — N ordered points (polyline)
    BEZIER  — N control points (cubic bezier chain)
    STAR    — centre + two radius points + <EXTRA> for spoke count
    SPIRAL  — centre + outer point + <EXTRA> for turns (negative=CCW)
    ELLIPSE — 2 points (centre + edge)
    CIRCLE  — 2 points (centre + edge)

Coordinate space: pixel coordinates within a canvas-size bounding box.
Points must be normalised before use in world_tree_mr.py geometry.

Public surface:
    GfigPoint       — (x, y) named tuple
    GfigObject      — frozen: type + control points + extra params
    GfigFigure      — frozen: name + list of GfigObjects
    parse_gfig(path)     → GfigFigure
    sample_arc(obj, n)   → list[GfigPoint]  (n points along arc)
    sample_line(obj, n)  → list[GfigPoint]  (n points along polyline)
    sample_bezier(obj, n) → list[GfigPoint] (n points along bezier)
    normalise(points, w, h) → list[GfigPoint]  (scale to 0-1 space)
"""

# ---------------------------------------------------------------------------
# DEPENDENCY TRACKING                                               v1
# ---------------------------------------------------------------------------
# This file calls:    Python standard library only
# This file is called by: world_tree_mr.py         (Same Folder)
#                          __main__ (CLI direct execution)
# ---------------------------------------------------------------------------

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class GfigPoint:
    x: float
    y: float

    def __add__(self, other: "GfigPoint") -> "GfigPoint":
        return GfigPoint(self.x + other.x, self.y + other.y)

    def __mul__(self, t: float) -> "GfigPoint":
        return GfigPoint(self.x * t, self.y * t)

    def lerp(self, other: "GfigPoint", t: float) -> "GfigPoint":
        return GfigPoint(
            self.x + (other.x - self.x) * t,
            self.y + (other.y - self.y) * t,
        )


@dataclass(frozen=True)
class GfigObject:
    """
    One geometric primitive from a Gfig file.

    type:   'ARC' | 'LINE' | 'BEZIER' | 'STAR' | 'SPIRAL' | 'ELLIPSE' | 'CIRCLE'
    points: control points in pixel coordinates (source canvas space)
    extra:  integer parameter from <EXTRA> block (spoke count, turn count, etc.)
    """
    type:   str
    points: tuple[GfigPoint, ...]
    extra:  Optional[int] = None

    def point_count(self) -> int:
        return len(self.points)


@dataclass(frozen=True)
class GfigFigure:
    """
    Complete parsed Gfig file.

    name:     figure name from header
    objects:  all geometric objects in file order
    """
    name:    str
    objects: tuple[GfigObject, ...]

    def by_type(self, typename: str) -> list[GfigObject]:
        return [o for o in self.objects if o.type == typename]

    def arcs(self)    -> list[GfigObject]: return self.by_type("ARC")
    def lines(self)   -> list[GfigObject]: return self.by_type("LINE")
    def beziers(self) -> list[GfigObject]: return self.by_type("BEZIER")


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def parse_gfig(path: Path) -> GfigFigure:
    """
    Parse a Gfig file and return a GfigFigure.

    Tolerant of unknown primitive types — they are included with their
    control points but may not be sampleable.
    """
    text   = path.read_text(encoding="utf-8", errors="replace")
    lines  = [l.strip() for l in text.splitlines()]

    name = "unnamed"
    for line in lines[:6]:
        if line.startswith("Name:"):
            name = line[5:].strip().replace("\\040", " ")
            break

    objects: list[GfigObject] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # Detect primitive open tag: <TYPENAME>
        m = re.match(r"^<([A-Z][A-Z0-9_]*)>$", line)
        if m and line not in ("<OPTIONS>", "<EXTRA>"):
            typename = m.group(1)
            close_tag = f"</{typename}>"
            i += 1
            pts: list[GfigPoint] = []
            extra: Optional[int] = None

            while i < len(lines) and lines[i] != close_tag:
                inner = lines[i]
                if inner == "<EXTRA>":
                    # Extra value on next line
                    i += 1
                    if i < len(lines):
                        try:
                            extra = int(lines[i].strip())
                        except ValueError:
                            pass
                    # Skip </EXTRA>
                    i += 1
                    continue
                # Try to parse as "x y" coordinate pair
                parts = inner.split()
                if len(parts) == 2:
                    try:
                        x, y = float(parts[0]), float(parts[1])
                        pts.append(GfigPoint(x, y))
                    except ValueError:
                        pass
                i += 1

            objects.append(GfigObject(
                type=typename,
                points=tuple(pts),
                extra=extra,
            ))
        i += 1

    return GfigFigure(name=name, objects=tuple(objects))


# ---------------------------------------------------------------------------
# Sampling — convert control points into dense point sequences
# ---------------------------------------------------------------------------

def sample_line(obj: GfigObject, n: int) -> list[GfigPoint]:
    """
    Sample n evenly-spaced points along a LINE polyline.
    n=1 returns the midpoint.
    """
    pts = obj.points
    if len(pts) < 2:
        return list(pts)

    # Compute cumulative arc lengths
    lengths = [0.0]
    for a, b in zip(pts, pts[1:]):
        d = math.sqrt((b.x - a.x)**2 + (b.y - a.y)**2)
        lengths.append(lengths[-1] + d)
    total = lengths[-1]
    if total < 1e-6:
        return [pts[0]] * n

    result = []
    for step in range(n):
        t_dist = (step / max(n - 1, 1)) * total
        # Find which segment this falls in
        for seg in range(len(pts) - 1):
            if lengths[seg] <= t_dist <= lengths[seg + 1]:
                seg_len = lengths[seg + 1] - lengths[seg]
                if seg_len < 1e-6:
                    result.append(pts[seg])
                else:
                    t = (t_dist - lengths[seg]) / seg_len
                    result.append(pts[seg].lerp(pts[seg + 1], t))
                break
        else:
            result.append(pts[-1])

    return result


def sample_arc(obj: GfigObject, n: int) -> list[GfigPoint]:
    """
    Sample n points along an ARC defined by 3 control points.

    Gfig ARC stores: start, control (midpoint on arc), end.
    We interpret this as a quadratic Bezier for simplicity —
    it approximates the circular arc well enough for branch guides.
    """
    pts = obj.points
    if len(pts) < 3:
        return sample_line(obj, n)

    p0, p1, p2 = pts[0], pts[1], pts[2]
    result = []
    for step in range(n):
        t  = step / max(n - 1, 1)
        # Quadratic Bezier: B(t) = (1-t)²P0 + 2(1-t)tP1 + t²P2
        mt = 1.0 - t
        x  = mt*mt*p0.x + 2*mt*t*p1.x + t*t*p2.x
        y  = mt*mt*p0.y + 2*mt*t*p1.y + t*t*p2.y
        result.append(GfigPoint(x, y))
    return result


def sample_bezier(obj: GfigObject, n: int) -> list[GfigPoint]:
    """
    Sample n points along a BEZIER curve.

    Gfig BEZIER stores N control points forming a cubic (or higher) chain.
    We split into cubic segments (groups of 4 points, sharing endpoints).
    """
    pts = obj.points
    if len(pts) < 2:
        return list(pts)
    if len(pts) < 4:
        return sample_arc(obj, n)   # fall back to quadratic

    # Collect cubic segments
    segments = []
    i = 0
    while i + 3 < len(pts):
        segments.append((pts[i], pts[i+1], pts[i+2], pts[i+3]))
        i += 3   # cubic segments share endpoint

    if not segments:
        return sample_line(obj, n)

    n_per_seg = max(2, n // len(segments))
    result = []
    for p0, p1, p2, p3 in segments:
        for step in range(n_per_seg):
            t  = step / max(n_per_seg - 1, 1)
            mt = 1.0 - t
            x  = mt**3*p0.x + 3*mt**2*t*p1.x + 3*mt*t**2*p2.x + t**3*p3.x
            y  = mt**3*p0.y + 3*mt**2*t*p1.y + 3*mt*t**2*p2.y + t**3*p3.y
            result.append(GfigPoint(x, y))
    return result[:n]


def sample_object(obj: GfigObject, n: int) -> list[GfigPoint]:
    """Dispatch to the correct sampler for an object's type."""
    if obj.type == "ARC":
        return sample_arc(obj, n)
    elif obj.type == "LINE":
        return sample_line(obj, n)
    elif obj.type in ("BEZIER",):
        return sample_bezier(obj, n)
    else:
        # For STAR, SPIRAL, CIRCLE, ELLIPSE — return control points as-is
        return list(obj.points)


def normalise(
    points: list[GfigPoint],
    source_width: float,
    source_height: float,
) -> list[GfigPoint]:
    """
    Scale a list of GfigPoints from pixel coordinates to [0,1] space.
    Use before mapping into Trixel canopy/trunk geometry.
    """
    return [
        GfigPoint(p.x / max(source_width, 1),
                  p.y / max(source_height, 1))
        for p in points
    ]


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    root_str = sys.argv[1] if len(sys.argv) > 1 else "data/gfig"
    gimp_gfig = Path(root_str)
    files = sorted(gimp_gfig.glob("*")) if gimp_gfig.exists() else []

    if not files:
        print("No gfig files found. Pass path as argument.")
        sys.exit(0)

    print(f"Parsing {len(files)} Gfig files from {gimp_gfig}\n")

    for path in files:
        fig = parse_gfig(path)
        arcs    = len(fig.arcs())
        beziers = len(fig.beziers())
        lines   = len(fig.lines())
        others  = len(fig.objects) - arcs - beziers - lines

        print(f"  {fig.name:30s}  "
              f"arcs={arcs}  beziers={beziers}  lines={lines}  other={others}")

        # Sample the first ARC if present
        if fig.arcs():
            pts = sample_arc(fig.arcs()[0], 5)
            print(f"    arc[0] sample: {[(round(p.x), round(p.y)) for p in pts]}")

        # Sample the first LINE if present
        if fig.lines():
            pts = sample_line(fig.lines()[0], 5)
            print(f"    line[0] sample: {[(round(p.x), round(p.y)) for p in pts]}")

    print()
    print("=== Tree use case: arc as branch curve ===")
    curves = parse_gfig(gimp_gfig / "curves")
    print(f"'curves' figure: {len(curves.arcs())} arcs")
    for i, arc in enumerate(curves.arcs()[:3]):
        pts = sample_arc(arc, 8)
        print(f"  arc {i}: {[(round(p.x), round(p.y)) for p in pts]}")
    print()
    print("Normalised to [0,1] (assuming 256x256 canvas):")
    for i, arc in enumerate(curves.arcs()[:2]):
        pts = normalise(sample_arc(arc, 5), 256, 256)
        print(f"  arc {i}: {[(round(p.x,3), round(p.y,3)) for p in pts]}")
