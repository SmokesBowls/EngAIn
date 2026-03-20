"""
test_spacing_ratio.py — Pinned assertions for _gbr_spacing_to_ratio

Runs standalone. No test framework required.

Geometry note: the engine computes stamp_dist = base_radius * 2.0 * spacing_pct
where base_radius is half the brush's larger dimension (pixels).
spacing_pct is center-to-center distance as a fraction of brush diameter.
  1.0 = stamps touching (diameter between centers)
  0.5 = heavy overlap (half-diameter between centers)
  2.0 = gap between stamps (two diameters between centers)
"""

import sys
sys.path.insert(0, ".")
from trixel_brush_adapter import _gbr_spacing_to_ratio


def _assert_close(raw: int, expected: float, desc: str) -> None:
    result = _gbr_spacing_to_ratio(raw)
    if abs(result - expected) > 1e-9:
        raise AssertionError(
            f"_gbr_spacing_to_ratio({raw}) = {result!r}, expected {expected!r}  [{desc}]"
        )


# --- Confirmed specimens from GIMP 2.10 stock library ---

# Dense / overlapping
_assert_close(834,   0.0834, "Bristles-01: hair overlap, 8.3% of brush width")
_assert_close(1359,  0.1359, "Oils-01: paint spread, 13.6% of brush width")
_assert_close(2632,  0.2632, "Hatch-Pen-01: tight crosshatch, 26.3% of brush width")

# Natural / medium
_assert_close(5200,  0.5200, "Pencil-Scratch: medium pressure, 52% of brush width")
_assert_close(6467,  0.6467, "Charcoal-02: soft charcoal, 64.7% of brush width")
_assert_close(7747,  0.7747, "Charcoal-01: natural charcoal feel, 77.5% of brush width")
_assert_close(7763,  0.7763, "Sponge-01: dabbed texture, 77.6% of brush width")

# Wide / spaced
_assert_close(10324, 1.0324, "Texture-01: touching tile stamps, 103.2% of brush width")
_assert_close(12867, 1.2867, "Cell-01: scattered cells, 128.7% of brush width")
_assert_close(12880, 1.2880, "pixel.gbr: slight gap on 1px brush, 128.8% of brush width")
_assert_close(12883, 1.2883, "Smoke: wide scatter, 128.8% of brush width")

# Very wide
_assert_close(19271, 1.9271, "galaxy: sparse splatter, 192.7% of brush width")
_assert_close(25683, 2.5683, "dunes: scattered grain, 256.8% of brush width")
_assert_close(38515, 3.8515, "5x5squareBlur: test squares, 385% of brush width")

# Edge cases
_assert_close(0,     1.0,    "zero → default touching (1.0)")
_assert_close(10000, 1.0,    "10000 → exactly 1.0 (touching)")
_assert_close(12800, 1.28,   "12800 → 1.28 (named in docstring)")

print(f"✓ All {17} spacing assertions pass")
print(f"  Formula: raw / 10000.0  (raw = GUI_percent * 100)")
print(f"  Geometry: stamp_dist = brush_diameter * spacing_pct")
