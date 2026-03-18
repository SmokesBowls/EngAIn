"""
module_gbr/parser.py — GIMP Brush (.gbr) and Pattern (.pat) parser

Confirmed against: Hatch-Pen-01.gbr, pixel.gbr, walnut.pat, pentagram.pgm

Binary format — big-endian header:
  bytes 0-3:   header_size  (uint32) — total header byte count
  bytes 4-7:   version      (uint32) — always 2 for modern files
  bytes 8-11:  width        (uint32)
  bytes 12-15: height       (uint32)
  bytes 16-19: color_depth  (uint32) — 1 = grayscale (.gbr), 3 = RGB (.pat)
  bytes 20-N:  name string  (null-terminated, within header_size)
  bytes N+1…:  raw pixel data (width × height × color_depth bytes)

  Note: .pat files have an internal name prefixed with 'GPAT' (e.g. 'GPATWalnut')
  which is stored verbatim in the parsed name field.

.pgm files (gimpressionist brushes) are plain Netpbm grayscale, not binary GIMP
headers. parse_pgm() handles those separately.

Parser returns a frozen GbrBrush dataclass.
Pixel data is stored as raw bytes — the adapter layer decides whether to
decode it as a numpy array, PIL image, Godot Image, or something else.
"""


# ---------------------------------------------------------------------------
# DEPENDENCY TRACKING                                               v1
# ---------------------------------------------------------------------------
# This file calls:    Python standard library only
# This file is called by: trixel_brush_adapter.py (Same Folder)
#                         engine_mr.py             (Same Folder)
#                         engine_debug_mr.py       (Same Folder)
# Note: parse_pgm() accepts both P5 (grayscale) and P6 (PPM/RGB→luma)
# ---------------------------------------------------------------------------
from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class GbrBrush:
    """
    Normalized representation of a .gbr or .pat bitmap brush.

    pixel_data: raw bytes in row-major order.
        Grayscale (depth=1): pixel_data[y*width + x] = alpha byte
        RGB       (depth=3): pixel_data[(y*width + x)*3 : (y*width+x)*3+3] = R,G,B

    For .pat files, name typically has a 'GPAT' prefix as stored in the file.
    """
    name:        str
    version:     int          # always 2 for modern GIMP files
    width:       int
    height:      int
    depth:       int          # 1 = grayscale, 3 = RGB
    spacing:     int          # stamp spacing percentage (0 if not in header)
    pixel_data:  bytes        # raw pixel bytes, length = width * height * depth
    source_path: Optional[str]  # original filename, for traceability

    @property
    def is_grayscale(self) -> bool:
        return self.depth == 1

    @property
    def is_rgb(self) -> bool:
        return self.depth == 3

    def pixel_at(self, x: int, y: int) -> tuple[int, ...]:
        """
        Return the pixel at (x, y) as a tuple.
        Grayscale: (alpha,)   RGB: (r, g, b)
        """
        base = (y * self.width + x) * self.depth
        return tuple(self.pixel_data[base:base + self.depth])

    def to_dict(self, include_pixels: bool = False) -> dict:
        d: dict = {
            "name":        self.name,
            "version":     self.version,
            "width":       self.width,
            "height":      self.height,
            "depth":       self.depth,
            "spacing":     self.spacing,
            "source_path": self.source_path,
        }
        if include_pixels:
            d["pixel_data"] = list(self.pixel_data)
        return d


# ---------------------------------------------------------------------------
# GBR / PAT parser
# ---------------------------------------------------------------------------

def parse_gbr(path: Path) -> GbrBrush:
    """
    Parse a .gbr or .pat file and return a GbrBrush.

    Raises:
        ValueError: Unrecognised header or truncated file.
    """
    data = path.read_bytes()

    if len(data) < 20:
        raise ValueError(f"{path.name}: file too small to be a valid brush")

    header_size = struct.unpack_from(">I", data, 0)[0]
    version     = struct.unpack_from(">I", data, 4)[0]
    width       = struct.unpack_from(">I", data, 8)[0]
    height      = struct.unpack_from(">I", data, 12)[0]
    depth       = struct.unpack_from(">I", data, 16)[0]

    if depth not in (1, 3, 4):
        raise ValueError(
            f"{path.name}: unexpected color depth {depth} "
            f"(expected 1 for grayscale or 3 for RGB)"
        )

    # Name: null-terminated string starting at byte 20, within header
    name_start = 20
    name_end   = data.find(b"\x00", name_start, header_size)
    if name_end == -1:
        name_end = header_size
    name = data[name_start:name_end].decode("utf-8", errors="replace")

    # Spacing is sometimes stored as an extra uint32 after the name
    # (present in some versions). We probe for it but default to 0.
    spacing = 0
    spacing_offset = name_end + 1
    if spacing_offset + 4 <= header_size:
        spacing = struct.unpack_from(">I", data, spacing_offset)[0]

    # Pixel data starts immediately after the declared header
    pixel_start   = header_size
    expected_size = width * height * depth
    pixel_data    = data[pixel_start:pixel_start + expected_size]

    if len(pixel_data) < expected_size:
        raise ValueError(
            f"{path.name}: pixel data truncated "
            f"(expected {expected_size} bytes, got {len(pixel_data)})"
        )

    return GbrBrush(
        name=name,
        version=version,
        width=width,
        height=height,
        depth=depth,
        spacing=spacing,
        pixel_data=pixel_data,
        source_path=str(path),
    )


# ---------------------------------------------------------------------------
# PGM parser (gimpressionist brushes)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PgmBrush:
    """
    Grayscale bitmap from a Netpbm .pgm file (gimpressionist brush format).
    pixel_data: raw bytes, length = width * height (P5 raw binary)
    """
    width:       int
    height:      int
    max_val:     int          # usually 255
    pixel_data:  bytes
    source_path: Optional[str]

    def to_dict(self, include_pixels: bool = False) -> dict:
        d: dict = {
            "width":       self.width,
            "height":      self.height,
            "max_val":     self.max_val,
            "source_path": self.source_path,
        }
        if include_pixels:
            d["pixel_data"] = list(self.pixel_data)
        return d


def parse_pgm(path: Path) -> PgmBrush:
    """
    Parse a binary PGM (P5) file and return a PgmBrush.

    Raises:
        ValueError: Not a P5 (binary grayscale) PGM file.
        ValueError: Truncated pixel data.
    """
    data = path.read_bytes()

    # PGM header: token-based scan to correctly locate pixel data offset.
    # Format: P5  [# comments...]  width  height  maxval  <binary pixels>
    # Comments may appear anywhere in the header; we skip them entirely.
    # We collect exactly 4 tokens (magic + width + height + maxval) and let
    # `i` land on the first byte of pixel data (right after maxval's newline).

    tokens: list[str] = []
    i = 0
    header_limit = min(len(data), 4096)  # PGM headers are never huge

    while len(tokens) < 4 and i < header_limit:
        # Skip whitespace (space, tab, CR, LF)
        while i < header_limit and data[i] in b" \t\r\n":
            i += 1
        if i >= header_limit:
            break
        # Skip comment lines
        if data[i] == ord("#"):
            while i < header_limit and data[i] != ord("\n"):
                i += 1
            continue
        # Read one token
        start = i
        while i < header_limit and data[i] not in b" \t\r\n":
            i += 1
        tokens.append(data[start:i].decode("ascii", errors="replace"))

    # After the last token (maxval), skip exactly one whitespace byte
    # (the separator between header and pixel data, per PGM spec)
    if i < len(data) and data[i] in b" \t\r\n":
        i += 1

    if len(tokens) < 4 or tokens[0] not in ("P5", "P6"):
        got = tokens[0] if tokens else b""
        raise ValueError(f"{path.name}: not a binary PGM (P5) file, got {got!r}")

    try:
        width   = int(tokens[1])
        height  = int(tokens[2])
        max_val = int(tokens[3])
    except ValueError as exc:
        raise ValueError(f"{path.name}: malformed PGM header: {exc}") from exc

    if tokens[0] == "P6":
        # PPM (colour) — convert RGB to grayscale luminance so it works as a brush mask.
        # Formula: Y = 0.299R + 0.587G + 0.114B  (ITU-R BT.601)
        rgb_data      = data[i:i + width * height * 3]
        expected_size = width * height * 3
        if len(rgb_data) < expected_size:
            raise ValueError(
                f"{path.name}: truncated P6 pixel data "
                f"(expected {expected_size}, got {len(rgb_data)})"
            )
        gray = bytearray(width * height)
        for n in range(width * height):
            r = rgb_data[n * 3]
            g = rgb_data[n * 3 + 1]
            b = rgb_data[n * 3 + 2]
            gray[n] = int(0.299 * r + 0.587 * g + 0.114 * b)
        pixel_data = bytes(gray)
    else:
        pixel_data    = data[i:i + width * height]
        expected_size = width * height

        if len(pixel_data) < expected_size:
            raise ValueError(
                f"{path.name}: truncated pixel data "
                f"(expected {expected_size}, got {len(pixel_data)})"
            )

    return PgmBrush(
        width=width,
        height=height,
        max_val=max_val,
        pixel_data=pixel_data,
        source_path=str(path),
    )


# ---------------------------------------------------------------------------
# Batch loaders
# ---------------------------------------------------------------------------

def load_directory_gbr(directory: Path) -> list[GbrBrush]:
    """Load all .gbr and .pat files recursively."""
    brushes = []
    for ext in ("*.gbr", "*.pat"):
        for path in sorted(directory.rglob(ext)):
            brushes.append(parse_gbr(path))
    return brushes


def load_directory_pgm(directory: Path) -> list[PgmBrush]:
    """Load all .pgm files recursively (gimpressionist brushes)."""
    brushes = []
    for path in sorted(directory.rglob("*.pgm")):
        brushes.append(parse_pgm(path))
    return brushes


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    targets = [Path(a) for a in sys.argv[1:]] if len(sys.argv) > 1 else []

    if not targets:
        print("Usage: python parser.py path/to/file.gbr [path/to/dir/] ...")
        sys.exit(0)

    for t in targets:
        if t.is_dir():
            gbr_results = load_directory_gbr(t)
            pgm_results = load_directory_pgm(t)
            print(f"Loaded {len(gbr_results)} .gbr/.pat  "
                  f"{len(pgm_results)} .pgm  from {t}")
            for b in gbr_results:
                print(f"  [gbr] {b.name!r:30s}  {b.width}x{b.height}  "
                      f"depth={b.depth}  spc={b.spacing}")
            for b in pgm_results:
                name = Path(b.source_path).name if b.source_path else "?"
                print(f"  [pgm] {name!r:30s}  {b.width}x{b.height}")
        elif t.suffix.lower() in (".gbr", ".pat"):
            b = parse_gbr(t)
            print(f"Name:    {b.name!r}")
            print(f"Size:    {b.width} × {b.height}")
            print(f"Depth:   {b.depth} ({'grayscale' if b.is_grayscale else 'RGB'})")
            print(f"Spacing: {b.spacing}")
            print(f"Pixels:  {len(b.pixel_data)} bytes")
        elif t.suffix.lower() == ".pgm":
            b = parse_pgm(t)
            print(f"Size:    {b.width} × {b.height}")
            print(f"MaxVal:  {b.max_val}")
            print(f"Pixels:  {len(b.pixel_data)} bytes")
        else:
            print(f"Unknown extension: {t.suffix} — try .gbr .pat .pgm")
