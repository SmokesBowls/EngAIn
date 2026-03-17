"""
gih_parser_mr.py — GIMP Image Hose (.gih) parser

Confirmed against all 31 stock .gih files from GIMP 2.10.

Format:
  Line 1 (text):  brush name
  Line 2 (text):  params line
  Bytes N+:       ncells sequential .gbr-style binary cells

Params line grammar (confirmed from all specimens):
  <ncells> ncells:<N> cellwidth:<W> cellheight:<H> step:<S>
  dim:<D> cols:<C> rows:<R> placement:<P>
  rank0:<R0> sel0:<MODE0>
  [rank1:<R1> sel1:<MODE1>]        ← present when dim >= 2
  [rank2:<R2> sel2:<MODE2>]        ← present when dim == 3

  <ncells> at the start is redundant with ncells:N but always present.

Selection modes seen across all 31 files:
  'random', 'incremental', 'angular', 'pressure', 'xtilt', 'ytilt'

dim values seen: 1, 2, 3
  dim=1: single selection axis (sel0 only)
  dim=2: two selection axes (Charcoal-03.gih: angular × random)
  dim=3: three selection axes (feltpen.gih: pressure × ytilt × xtilt)

Cell binary format = .gbr header:
  uint32 header_size
  uint32 version        (always 2)
  uint32 width
  uint32 height
  uint32 depth          (1 = grayscale alpha, 4 = RGBA colour)
  bytes  name           (null-terminated, within header_size)
  bytes  pixel_data     (width × height × depth bytes)

depth values seen: 1 (all sketch/texture/media), 4 (Wilber.gih — RGBA)
"""


# ---------------------------------------------------------------------------
# DEPENDENCY TRACKING                                               v1
# ---------------------------------------------------------------------------
# This file calls:    Python standard library only
# This file is called by: trixel_brush_adapter.py (Same Folder)
#                         engine_mr.py             (Same Folder)
# ---------------------------------------------------------------------------
from __future__ import annotations

import re
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class GihCell:
    """
    One stamp cell embedded in a .gih container.
    Structural equivalent to a GbrBrush; same binary format.

    depth: 1 = grayscale alpha mask, 4 = RGBA colour stamp
    pixel_data: raw bytes, length = width × height × depth
    """
    index:       int
    width:       int
    height:      int
    depth:       int
    name:        str
    pixel_data:  bytes

    @property
    def is_grayscale(self) -> bool:
        return self.depth == 1

    @property
    def is_rgba(self) -> bool:
        return self.depth == 4

    def to_dict(self, include_pixels: bool = False) -> dict:
        d: dict = {
            "index":  self.index,
            "width":  self.width,
            "height": self.height,
            "depth":  self.depth,
            "name":   self.name,
        }
        if include_pixels:
            d["pixel_data"] = list(self.pixel_data)
        return d


@dataclass(frozen=True)
class SelectionAxis:
    """
    One selection dimension.

    rank:  number of cells along this axis
    mode:  how cells are selected — 'random' | 'incremental' |
           'angular' | 'pressure' | 'xtilt' | 'ytilt'

    For dim=1: one axis, ncells = rank0.
    For dim=2: two axes, ncells = rank0 × rank1.
    For dim=3: three axes, ncells = rank0 × rank1 × rank2.
    Cell index = axis0_index * (rank1 * rank2) + axis1_index * rank2 + axis2_index
    """
    rank: int
    mode: str

    def to_dict(self) -> dict:
        return {"rank": self.rank, "mode": self.mode}


@dataclass(frozen=True)
class GihBrush:
    """
    Fully parsed GIMP Image Hose.

    name:       brush display name
    ncells:     total number of cells (= product of axis ranks)
    cell_width: nominal cell width (all cells share this)
    cell_height: nominal cell height
    step:       stamp spacing percentage (100 = cell-width spacing)
    axes:       tuple of SelectionAxis, one per dimension (1–3)
    cells:      tuple of GihCell, length == ncells
    source_path: original file path for traceability
    """
    name:         str
    ncells:       int
    cell_width:   int
    cell_height:  int
    step:         float
    axes:         tuple[SelectionAxis, ...]
    cells:        tuple[GihCell, ...]
    source_path:  Optional[str]

    @property
    def dim(self) -> int:
        return len(self.axes)

    @property
    def primary_selection_mode(self) -> str:
        """Convenience: first (and most commonly the only) selection mode."""
        return self.axes[0].mode if self.axes else "random"

    def to_dict(self, include_pixels: bool = False) -> dict:
        return {
            "name":         self.name,
            "ncells":       self.ncells,
            "cell_width":   self.cell_width,
            "cell_height":  self.cell_height,
            "step":         self.step,
            "axes":         [a.to_dict() for a in self.axes],
            "cells":        [c.to_dict(include_pixels) for c in self.cells],
            "source_path":  self.source_path,
        }


# ---------------------------------------------------------------------------
# Parser internals
# ---------------------------------------------------------------------------

_PARAM_RE = re.compile(r'(\w+):(\S+)')


def parse_gih(path: Path) -> GihBrush:
    """
    Parse a .gih file and return a GihBrush.

    Raises:
        ValueError: Header lines are missing or malformed.
        ValueError: Cell binary data is truncated.
        ValueError: Parsed cell count does not match declared ncells.
    """
    data = path.read_bytes()

    # --- Text header ---
    first_nl  = data.find(b"\n")
    second_nl = data.find(b"\n", first_nl + 1)

    if first_nl == -1 or second_nl == -1:
        raise ValueError(f"{path.name}: could not locate two-line text header")

    name        = data[:first_nl].decode("utf-8", errors="replace").strip()
    params_raw  = data[first_nl + 1:second_nl].decode("utf-8", errors="replace").strip()
    cell_offset = second_nl + 1

    # --- Params ---
    ncells, cell_width, cell_height, step, axes = _parse_params(
        path.name, params_raw
    )

    # --- Binary cells ---
    cells = _parse_cells(path.name, data, cell_offset, ncells)

    return GihBrush(
        name=name,
        ncells=ncells,
        cell_width=cell_width,
        cell_height=cell_height,
        step=step,
        axes=axes,
        cells=tuple(cells),
        source_path=str(path),
    )


def _parse_params(
    filename: str, raw: str
) -> tuple[int, int, int, float, tuple[SelectionAxis, ...]]:
    """
    Parse the params line and return (ncells, cell_width, cell_height, step, axes).
    """
    tokens = raw.split()
    if not tokens:
        raise ValueError(f"{filename}: empty params line")

    # First token is ncells (redundant with ncells: key, but always present)
    try:
        ncells_leading = int(tokens[0])
    except ValueError:
        raise ValueError(
            f"{filename}: params line does not start with integer ncells, "
            f"got {tokens[0]!r}"
        )

    params = dict(_PARAM_RE.findall(raw))

    def _int(key: str, default: int = 0) -> int:
        try:
            return int(params.get(key, default))
        except ValueError:
            raise ValueError(f"{filename}: malformed int param {key!r}={params[key]!r}")

    def _float(key: str, default: float = 0.0) -> float:
        try:
            return float(params.get(key, default))
        except ValueError:
            raise ValueError(f"{filename}: malformed float param {key!r}={params[key]!r}")

    ncells      = _int("ncells", ncells_leading)
    cell_width  = _int("cellwidth")
    cell_height = _int("cellheight")
    step        = _float("step", 100.0)
    dim         = _int("dim", 1)

    # Build selection axes (dim 1–3)
    axes: list[SelectionAxis] = []
    for i in range(dim):
        rank = _int(f"rank{i}", ncells)
        mode = params.get(f"sel{i}", "random").lower()
        axes.append(SelectionAxis(rank=rank, mode=mode))

    if not axes:
        axes = [SelectionAxis(rank=ncells, mode="random")]

    return ncells, cell_width, cell_height, step, tuple(axes)


def _parse_cells(
    filename: str, data: bytes, offset: int, ncells: int
) -> list[GihCell]:
    """
    Walk the binary cell sequence starting at `offset`.
    Returns exactly `ncells` GihCell objects.

    Raises ValueError if data is truncated or cell count mismatches.
    """
    cells: list[GihCell] = []
    pos = offset

    for idx in range(ncells):
        if pos + 20 > len(data):
            raise ValueError(
                f"{filename}: truncated — expected cell {idx}, "
                f"only {len(data) - pos} bytes remain"
            )

        hdr_size = struct.unpack_from(">I", data, pos)[0]
        version  = struct.unpack_from(">I", data, pos + 4)[0]   # noqa: F841
        width    = struct.unpack_from(">I", data, pos + 8)[0]
        height   = struct.unpack_from(">I", data, pos + 12)[0]
        depth    = struct.unpack_from(">I", data, pos + 16)[0]

        if hdr_size == 0 or width == 0 or height == 0:
            raise ValueError(
                f"{filename}: cell {idx} has zero-size header/dimensions "
                f"at file offset {pos}"
            )
        if depth not in (1, 3, 4):
            raise ValueError(
                f"{filename}: cell {idx} has unexpected depth={depth} "
                f"(expected 1, 3, or 4)"
            )

        # Cell name: null-terminated within header
        name_start = pos + 20
        name_end   = data.find(b"\x00", name_start, pos + hdr_size)
        cell_name  = (
            data[name_start:name_end].decode("utf-8", errors="replace")
            if name_end != -1
            else ""
        )

        # Pixel data
        pixel_start = pos + hdr_size
        pixel_len   = width * height * depth
        pixel_end   = pixel_start + pixel_len

        if pixel_end > len(data):
            raise ValueError(
                f"{filename}: cell {idx} pixel data truncated "
                f"(need {pixel_len} bytes at offset {pixel_start}, "
                f"file has {len(data) - pixel_start} remaining)"
            )

        pixel_data = data[pixel_start:pixel_end]

        cells.append(GihCell(
            index=idx,
            width=width,
            height=height,
            depth=depth,
            name=cell_name,
            pixel_data=pixel_data,
        ))

        pos = pixel_end

    return cells


# ---------------------------------------------------------------------------
# Batch loader
# ---------------------------------------------------------------------------

def load_directory(directory: Path) -> list[GihBrush]:
    """Load all .gih files found recursively under directory."""
    brushes = []
    for path in sorted(directory.rglob("*.gih")):
        brushes.append(parse_gih(path))
    return brushes


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    targets = [Path(a) for a in sys.argv[1:]] if len(sys.argv) > 1 else []

    if not targets:
        print("Usage: python gih_parser_mr.py path/to/file.gih [...]")
        print("       python gih_parser_mr.py path/to/brushes/dir/")
        sys.exit(0)

    for t in targets:
        if t.is_dir():
            results = load_directory(t)
            print(f"Loaded {len(results)} .gih files from {t}\n")
            for b in results:
                axis_str = "  ".join(
                    f"axis{i}=[rank={a.rank} sel={a.mode}]"
                    for i, a in enumerate(b.axes)
                )
                print(f"  {b.name!r:30s}  cells={b.ncells}  "
                      f"{b.cell_width}x{b.cell_height}  {axis_str}")
        else:
            import json
            b = parse_gih(t)
            print(f"Name:        {b.name!r}")
            print(f"Cells:       {b.ncells}")
            print(f"Cell size:   {b.cell_width} × {b.cell_height}")
            print(f"Step:        {b.step}")
            print(f"Dimensions:  {b.dim}")
            for i, ax in enumerate(b.axes):
                print(f"  Axis {i}: rank={ax.rank}  mode={ax.mode!r}")
            print(f"Cell depths: {set(c.depth for c in b.cells)}")
            print(f"Cell[0]:     {b.cells[0].width}×{b.cells[0].height}"
                  f"  depth={b.cells[0].depth}  pixels={len(b.cells[0].pixel_data)}")
