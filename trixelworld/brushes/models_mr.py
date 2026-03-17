"""
models_mr.py — Trixel Brush Asset Models

Six normalized asset types that sit between the GIMP format parsers
and the Trixel rendering/engine layer.

These are format-neutral. They do not know about .vbr, .gdyn, .gtp, etc.
They speak Trixel.

The adapter (trixel_brush_adapter.py) is the only code that maps
parser output → these types. Everything downstream of the adapter
works exclusively with these.

All dataclasses are frozen=True following EngAIn kernel conventions.
No I/O, no side effects, no mutable state.

Asset types
-----------
BrushShapeAsset    — the tip geometry of a brush (parametric or bitmap)
BrushDynamicsAsset — how input signals (pressure, velocity, etc.) modulate outputs
BrushPresetAsset   — a complete ready-to-use brush recipe
PaletteAsset       — a named ordered set of color swatches
SurfacePatternAsset — a tileable RGB texture (from .pat files)
VariantBrushBundle  — a multi-cell brush bundle with selection logic (.gih)

Supporting types
----------------
SwatchColor        — one palette entry (RGB + optional label)
CurveChannel       — one active (output, input) LUT mapping
AssetRegistry      — maps asset names → loaded asset objects
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


# ============================================================
# PALETTE
# ============================================================

@dataclass(frozen=True)
class SwatchColor:
    """One color entry in a palette."""
    r: int   # 0–255
    g: int
    b: int
    label: Optional[str]  # raw label from file, may include annotations

    def to_hex(self) -> str:
        return f"#{self.r:02X}{self.g:02X}{self.b:02X}"

    def to_dict(self) -> dict:
        return {"r": self.r, "g": self.g, "b": self.b,
                "hex": self.to_hex(), "label": self.label}


@dataclass(frozen=True)
class PaletteAsset:
    """Named ordered set of swatches."""
    name: str
    columns: int                   # display hint from file header (0 = unset)
    colors: tuple[SwatchColor, ...]
    source_file: Optional[str]

    def __len__(self) -> int:
        return len(self.colors)

    def to_dict(self) -> dict:
        return {
            "name":        self.name,
            "columns":     self.columns,
            "color_count": len(self.colors),
            "colors":      [c.to_dict() for c in self.colors],
            "source_file": self.source_file,
        }


# ============================================================
# BRUSH SHAPE
# ============================================================

@dataclass(frozen=True)
class BrushShapeAsset:
    """
    The physical tip of a brush.

    kind = 'parametric': generated from math (from .vbr)
      Relevant fields: radius, aspect, hardness, spacing, gamma, shape, spikes
      pixel_data, width, height, depth are None

    kind = 'bitmap': a stored alpha mask (from .gbr or .pgm)
      Relevant fields: width, height, depth, pixel_data
      radius, aspect, hardness, spacing, gamma, shape, spikes may be None

    spacing is present in both kinds: it controls stamp distance.
    For parametric brushes it comes from the .vbr file.
    For bitmap brushes it comes from the .gbr header (may be 0 if absent).
    """
    name:  str
    kind:  str   # 'parametric' | 'bitmap'

    # ---- Parametric fields (kind='parametric') ----
    radius:   Optional[float]   # brush tip size in pixels
    aspect:   Optional[float]   # ellipse ratio (25.0 = GIMP default round)
    hardness: Optional[float]   # edge softness 0.0–1.0
    gamma:    Optional[float]   # rotation angle in degrees (v1.5 .vbr only)
    shape:    Optional[str]     # 'circle' | 'square' | 'diamond'
    spikes:   Optional[int]     # polygon spoke count (v1.5 only)

    # ---- Shared / bitmap fields ----
    spacing:    Optional[float]  # stamp distance multiplier (1.0 = touching)
    width:      Optional[int]    # bitmap: pixel width
    height:     Optional[int]    # bitmap: pixel height
    depth:      Optional[int]    # bitmap: 1=grayscale, 3=RGB
    pixel_data: Optional[bytes]  # raw pixel bytes (row-major)

    source_file: Optional[str]

    def to_dict(self, include_pixels: bool = False) -> dict:
        d: dict = {
            "name":        self.name,
            "kind":        self.kind,
            "radius":      self.radius,
            "aspect":      self.aspect,
            "hardness":    self.hardness,
            "spacing":     self.spacing,
            "gamma":       self.gamma,
            "shape":       self.shape,
            "spikes":      self.spikes,
            "width":       self.width,
            "height":      self.height,
            "depth":       self.depth,
            "source_file": self.source_file,
        }
        if include_pixels and self.pixel_data:
            d["pixel_data"] = list(self.pixel_data)
        return d


# ============================================================
# BRUSH DYNAMICS
# ============================================================

@dataclass(frozen=True)
class CurveChannel:
    """
    One live (output_channel, input_signal) LUT mapping.

    output_channel: e.g. 'opacity', 'size', 'angle'
    input_signal:   e.g. 'pressure', 'velocity', 'direction'
    samples:        256-point LUT, values in [0.0, 1.0]
    """
    output_channel: str
    input_signal:   str
    samples:        tuple[float, ...]  # length 256

    def to_dict(self) -> dict:
        return {
            "output_channel": self.output_channel,
            "input_signal":   self.input_signal,
            "samples":        list(self.samples),
        }


@dataclass(frozen=True)
class BrushDynamicsAsset:
    """
    How input signals modulate brush output channels.

    active_channels: names of outputs that have at least one live input
    curves: only live (output, input) pairs — inactive pairs are omitted
    """
    name:            str
    active_channels: tuple[str, ...]
    curves:          tuple[CurveChannel, ...]
    source_file:     Optional[str]

    def channels_for(self, output: str) -> tuple[CurveChannel, ...]:
        """Return all active curves for a given output channel."""
        return tuple(c for c in self.curves if c.output_channel == output)

    def to_dict(self) -> dict:
        return {
            "name":            self.name,
            "active_channels": list(self.active_channels),
            "curves":          [c.to_dict() for c in self.curves],
            "source_file":     self.source_file,
        }


# ============================================================
# BRUSH PRESET
# ============================================================

@dataclass(frozen=True)
class BrushPresetAsset:
    """
    A complete ready-to-use brush recipe.

    Resolved references are embedded directly (shape, dynamics).
    Unresolved references are kept as bare name strings for late binding.
    Both are present simultaneously: if shape is not None, shape_ref is its name.
    If shape is None but shape_ref is set, resolution failed at build time.
    """
    name: str
    tool: Optional[str]  # e.g. 'gimp-paintbrush-tool'

    # Resolved assets
    shape:    Optional[BrushShapeAsset]
    dynamics: Optional[BrushDynamicsAsset]

    # Unresolved name refs (preserved for diagnostics / late binding)
    shape_ref:    Optional[str]
    dynamics_ref: Optional[str]
    gradient_ref: Optional[str]

    # Paint settings
    foreground_rgb:   Optional[tuple[float, float, float]]  # linear RGB 0.0–1.0
    opacity:          Optional[float]      # 0.0–1.0
    brush_size:       Optional[float]      # pixels
    application_mode: Optional[str]        # 'incremental' etc.
    use_jitter:       bool
    dynamics_enabled: bool
    fade_length:      Optional[float]
    fade_unit:        Optional[str]        # 'percent' etc.

    # Active slot flags
    use_brush:    bool
    use_dynamics: bool
    use_gradient: bool

    source_file: Optional[str]

    def is_fully_resolved(self) -> bool:
        """True if all referenced assets were found in the registry."""
        needs_shape    = self.use_brush    and self.shape_ref is not None
        needs_dynamics = self.use_dynamics and self.dynamics_ref is not None
        shape_ok    = (not needs_shape)    or (self.shape    is not None)
        dynamics_ok = (not needs_dynamics) or (self.dynamics is not None)
        return shape_ok and dynamics_ok

    def to_dict(self, include_pixels: bool = False) -> dict:
        return {
            "name":             self.name,
            "tool":             self.tool,
            "shape_ref":        self.shape_ref,
            "dynamics_ref":     self.dynamics_ref,
            "gradient_ref":     self.gradient_ref,
            "shape":            self.shape.to_dict(include_pixels) if self.shape else None,
            "dynamics":         self.dynamics.to_dict() if self.dynamics else None,
            "foreground_rgb":   list(self.foreground_rgb) if self.foreground_rgb else None,
            "opacity":          self.opacity,
            "brush_size":       self.brush_size,
            "application_mode": self.application_mode,
            "use_jitter":       self.use_jitter,
            "dynamics_enabled": self.dynamics_enabled,
            "fade_length":      self.fade_length,
            "fade_unit":        self.fade_unit,
            "use_brush":        self.use_brush,
            "use_dynamics":     self.use_dynamics,
            "use_gradient":     self.use_gradient,
            "fully_resolved":   self.is_fully_resolved(),
            "source_file":      self.source_file,
        }


# ============================================================
# SURFACE PATTERN
# ============================================================

@dataclass(frozen=True)
class SurfacePatternAsset:
    """
    A tileable RGB texture from a .pat file.
    pixel_data: raw bytes, width × height × 3.
    """
    name:        str
    width:       int
    height:      int
    pixel_data:  bytes
    source_file: Optional[str]

    def to_dict(self, include_pixels: bool = False) -> dict:
        d: dict = {
            "name":        self.name,
            "width":       self.width,
            "height":      self.height,
            "source_file": self.source_file,
        }
        if include_pixels:
            d["pixel_data"] = list(self.pixel_data)
        return d


# ============================================================
# VARIANT BRUSH BUNDLE (.gih placeholder)
# ============================================================

@dataclass(frozen=True)
class VariantBrushBundle:
    """
    Multi-cell brush bundle. Each cell is a BrushShapeAsset (bitmap).
    Selection mode controls which cell is used per stamp.

    This is the normalized form for .gih (GIMP Image Hose) files.
    The gih_parser_mr.py module populates cells; until then, cells is empty.

    selection_mode: 'random' | 'constant' | 'incremental'
                  | 'angular' | 'velocity' | 'pressure'
    """
    name:           str
    cell_count:     int
    cell_width:     int
    cell_height:    int
    selection_mode: str
    cells:          tuple[BrushShapeAsset, ...]
    source_file:    Optional[str]

    def to_dict(self, include_pixels: bool = False) -> dict:
        return {
            "name":           self.name,
            "cell_count":     self.cell_count,
            "cell_width":     self.cell_width,
            "cell_height":    self.cell_height,
            "selection_mode": self.selection_mode,
            "cells_loaded":   len(self.cells),
            "source_file":    self.source_file,
        }


# ============================================================
# REGISTRY
# ============================================================

@dataclass(frozen=True)
class AssetRegistry:
    """
    Immutable snapshot of all loaded Trixel brush assets, indexed by name.

    The adapter's build_registry() function populates this from parsed files.
    Downstream systems read from here; nothing writes to it after construction.
    """
    shapes:   dict[str, BrushShapeAsset]
    dynamics: dict[str, BrushDynamicsAsset]
    palettes: dict[str, PaletteAsset]
    patterns: dict[str, SurfacePatternAsset]
    bundles:  dict[str, VariantBrushBundle]

    def summary(self) -> dict:
        return {
            "shapes":   len(self.shapes),
            "dynamics": len(self.dynamics),
            "palettes": len(self.palettes),
            "patterns": len(self.patterns),
            "bundles":  len(self.bundles),
        }
