"""
module_vbr/parser.py — GIMP Vector Brush (.vbr) parser

Handles both v1.0 and v1.5 grammar, confirmed against real stock files:
  1-pixel.vbr, Block-01/02/03.vbr, Hardness-025/050/075/100.vbr, Star.vbr

V1.0 layout (5 numeric fields after name):
  GIMP-VBR / 1.0 / name / radius / aspect / hardness / spacing / gamma

V1.5 layout (adds shape string and spikes int):
  GIMP-VBR / 1.5 / name / shape / radius / aspect / spikes / hardness / spacing / gamma

Parser returns a frozen VbrBrush dataclass.
Adapter layer converts to dict/JSON/ZW downstream.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class VbrBrush:
    """
    Normalized representation of a GIMP .vbr brush.

    Fields confirmed against real file specimens:
      - radius:   brush size in pixels (float, e.g. 10.0)
      - aspect:   ellipse ratio (float; 25.0 is GIMP's default 'round',
                  1.0 means single-pixel tight)
      - hardness: edge softness 0.0 (full soft) to 1.0 (hard edge)
      - spacing:  stamp distance multiplier (1.0 = touching, >1 = gaps)
      - gamma:    v1.5 repurposes as rotation angle in degrees (0.0 default)
      - shape:    v1.5 only — 'circle' | 'square' | 'diamond'
      - spikes:   v1.5 only — polygon/star spoke count (int, 2+ )
      - version:  raw version string from file ('1.0' or '1.5')
    """
    name:     str
    radius:   float
    aspect:   float
    hardness: float
    spacing:  float
    gamma:    float
    shape:    str            # 'circle' for v1.0 (implied), else from file
    spikes:   Optional[int]  # None for v1.0
    version:  str

    def to_dict(self) -> dict:
        return {
            "name":     self.name,
            "version":  self.version,
            "radius":   self.radius,
            "aspect":   self.aspect,
            "hardness": self.hardness,
            "spacing":  self.spacing,
            "gamma":    self.gamma,
            "shape":    self.shape,
            "spikes":   self.spikes,
        }


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

_KNOWN_SHAPES = {"square", "diamond", "circle"}


def parse_vbr(path: Path) -> VbrBrush:
    """
    Parse a .vbr file and return a VbrBrush.

    Raises:
        ValueError  — file does not start with GIMP-VBR magic
        ValueError  — unknown version string
        ValueError  — malformed numeric field
    """
    raw = path.read_text(encoding="utf-8", errors="replace")
    lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]

    if not lines or lines[0] != "GIMP-VBR":
        raise ValueError(f"{path.name}: missing GIMP-VBR magic")

    version = lines[1]

    if version == "1.0":
        return _parse_v10(path.name, version, lines)
    elif version == "1.5":
        return _parse_v15(path.name, version, lines)
    else:
        raise ValueError(f"{path.name}: unknown .vbr version {version!r}")


def _parse_v10(filename: str, version: str, lines: list[str]) -> VbrBrush:
    # lines[0] = GIMP-VBR
    # lines[1] = 1.0
    # lines[2] = name
    # lines[3] = radius
    # lines[4] = aspect
    # lines[5] = hardness
    # lines[6] = spacing
    # lines[7] = gamma
    if len(lines) < 8:
        raise ValueError(f"{filename}: v1.0 requires 8 lines, got {len(lines)}")

    name     = lines[2]
    radius   = _float(filename, "radius",   lines[3])
    aspect   = _float(filename, "aspect",   lines[4])
    hardness = _float(filename, "hardness", lines[5])
    spacing  = _float(filename, "spacing",  lines[6])
    gamma    = _float(filename, "gamma",    lines[7])

    return VbrBrush(
        name=name, version=version,
        radius=radius, aspect=aspect, hardness=hardness,
        spacing=spacing, gamma=gamma,
        shape="circle", spikes=None,
    )


def _parse_v15(filename: str, version: str, lines: list[str]) -> VbrBrush:
    # lines[0] = GIMP-VBR
    # lines[1] = 1.5
    # lines[2] = name
    # lines[3] = shape string (square / diamond / circle)
    # lines[4] = radius
    # lines[5] = aspect
    # lines[6] = spikes (int)
    # lines[7] = hardness
    # lines[8] = spacing
    # lines[9] = gamma / rotation angle
    if len(lines) < 10:
        raise ValueError(f"{filename}: v1.5 requires 10 lines, got {len(lines)}")

    name   = lines[2]
    shape  = lines[3].lower()
    if shape not in _KNOWN_SHAPES:
        # Unknown shape string — store as-is rather than crash
        pass

    radius   = _float(filename, "radius",   lines[4])
    aspect   = _float(filename, "aspect",   lines[5])
    spikes   = _int  (filename, "spikes",   lines[6])
    hardness = _float(filename, "hardness", lines[7])
    spacing  = _float(filename, "spacing",  lines[8])
    gamma    = _float(filename, "gamma",    lines[9])

    return VbrBrush(
        name=name, version=version,
        radius=radius, aspect=aspect, hardness=hardness,
        spacing=spacing, gamma=gamma,
        shape=shape, spikes=spikes,
    )


def _float(filename: str, field: str, raw: str) -> float:
    try:
        return float(raw)
    except ValueError:
        raise ValueError(f"{filename}: expected float for {field!r}, got {raw!r}")


def _int(filename: str, field: str, raw: str) -> int:
    try:
        return int(raw)
    except ValueError:
        raise ValueError(f"{filename}: expected int for {field!r}, got {raw!r}")


# ---------------------------------------------------------------------------
# Batch loader
# ---------------------------------------------------------------------------

def load_directory(directory: Path) -> list[VbrBrush]:
    """Load all .vbr files found recursively under directory."""
    brushes = []
    for path in sorted(directory.rglob("*.vbr")):
        brushes.append(parse_vbr(path))
    return brushes


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    targets = [Path(a) for a in sys.argv[1:]] if len(sys.argv) > 1 else []

    if not targets:
        print("Usage: python parser.py path/to/file.vbr [...]")
        print("       python parser.py path/to/brushes/dir/")
        sys.exit(0)

    for t in targets:
        if t.is_dir():
            results = load_directory(t)
            print(f"Loaded {len(results)} .vbr files from {t}")
            for b in results:
                print(f"  {b.name!r:30s}  r={b.radius:6.1f}  "
                      f"hard={b.hardness:.2f}  spc={b.spacing:5.1f}  "
                      f"shape={b.shape}  spikes={b.spikes}")
        else:
            b = parse_vbr(t)
            import json
            print(json.dumps(b.to_dict(), indent=2))
