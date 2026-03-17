"""
module_gpl/parser.py — GIMP Palette (.gpl) parser

Confirmed against: Visibone_2.gpl, Default.gpl

Format (plain text):
  GIMP Palette
  Name: Palette Name
  Columns: N
  # optional comment lines
  R  G  B  optional_name_or_label

Color lines use whitespace-separated R G B with optional trailing label.
Blank lines and lines starting with '#' are skipped.
The (R G G) #RRGGBB annotation in Visibone_2 is treated as part of the
optional name field and stored verbatim — Trixel can strip it downstream.

Parser returns a frozen Palette dataclass.
"""


# ---------------------------------------------------------------------------
# DEPENDENCY TRACKING                                               v1
# ---------------------------------------------------------------------------
# This file calls:    Python standard library only
# This file is called by: trixel_brush_adapter.py (Same Folder)
# ---------------------------------------------------------------------------
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PaletteColor:
    """One color entry from a .gpl file."""
    r:    int          # 0-255
    g:    int
    b:    int
    label: Optional[str]  # trailing label/annotation, stripped of leading whitespace

    def to_hex(self) -> str:
        return f"#{self.r:02X}{self.g:02X}{self.b:02X}"

    def to_dict(self) -> dict:
        return {
            "r":     self.r,
            "g":     self.g,
            "b":     self.b,
            "hex":   self.to_hex(),
            "label": self.label,
        }


@dataclass(frozen=True)
class Palette:
    """
    Full GIMP palette, normalized from a .gpl file.

    colors: tuple of PaletteColor in file order
    columns: suggested display column count (from file header, may be 0)
    """
    name:    str
    columns: int
    colors:  tuple[PaletteColor, ...]

    def __len__(self) -> int:
        return len(self.colors)

    def to_dict(self) -> dict:
        return {
            "name":    self.name,
            "columns": self.columns,
            "colors":  [c.to_dict() for c in self.colors],
        }


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

_COLOR_LINE_RE = re.compile(
    r'^\s*(\d{1,3})\s+(\d{1,3})\s+(\d{1,3})'  # R G B
    r'(?:\s+(.+))?$'                             # optional label
)


def parse_gpl(path: Path) -> Palette:
    """
    Parse a .gpl file and return a Palette.

    Raises:
        ValueError: File does not start with 'GIMP Palette' magic.
        ValueError: A color component is out of 0-255 range.
    """
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()

    if not lines or lines[0].strip() != "GIMP Palette":
        raise ValueError(f"{path.name}: missing 'GIMP Palette' magic")

    name    = path.stem    # fallback
    columns = 0
    colors: list[PaletteColor] = []

    header_done = False

    for raw_line in lines[1:]:
        line = raw_line.strip()

        if not header_done:
            if line.lower().startswith("name:"):
                name = line[5:].strip()
                continue
            if line.lower().startswith("columns:"):
                try:
                    columns = int(line[8:].strip())
                except ValueError:
                    pass
                continue
            if line.startswith("#") or line == "":
                continue
            # First non-header line — switch to color parsing
            header_done = True

        # Color parsing
        if line.startswith("#") or line == "":
            continue

        m = _COLOR_LINE_RE.match(line)
        if not m:
            continue   # malformed line — skip rather than crash

        r, g, b = int(m.group(1)), int(m.group(2)), int(m.group(3))
        for component, val in (("R", r), ("G", g), ("B", b)):
            if not (0 <= val <= 255):
                raise ValueError(
                    f"{path.name}: {component} value {val} out of 0-255 range"
                )

        label = m.group(4).strip() if m.group(4) else None
        colors.append(PaletteColor(r=r, g=g, b=b, label=label))

    return Palette(name=name, columns=columns, colors=tuple(colors))


# ---------------------------------------------------------------------------
# Batch loader
# ---------------------------------------------------------------------------

def load_directory(directory: Path) -> list[Palette]:
    """Load all .gpl files found recursively under directory."""
    palettes = []
    for path in sorted(directory.rglob("*.gpl")):
        palettes.append(parse_gpl(path))
    return palettes


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json
    import sys

    targets = [Path(a) for a in sys.argv[1:]] if len(sys.argv) > 1 else []

    if not targets:
        print("Usage: python parser.py path/to/file.gpl [...]")
        sys.exit(0)

    for t in targets:
        if t.is_dir():
            results = load_directory(t)
            print(f"Loaded {len(results)} .gpl palettes from {t}")
            for p in results:
                print(f"  {p.name!r:30s}  {len(p)} colors  columns={p.columns}")
        else:
            p = parse_gpl(t)
            print(f"Name: {p.name!r}  colors: {len(p)}  columns: {p.columns}")
            for c in p.colors[:8]:
                print(f"  {c.to_hex()}  {c.label!r}")
            if len(p) > 8:
                print(f"  ... {len(p) - 8} more")
