"""
brush_models_mr.py — Normalized Trixel Brush Asset Models

Pure data layer. Frozen dataclasses only. No parsing, no I/O, no GIMP knowledge.

These are the types the rest of Trixel talks to.
The parsers produce their own internal types; the adapter converts those
into these. Everything downstream — ZW, ZONJ, AP, Godot — sees only these.

Type hierarchy:
    BrushShapeAsset      — tip geometry, parametric or bitmap
    BrushDynamicsAsset   — input→output response curves
    BrushPresetAsset     — tool configuration snapshot (unresolved refs)
    PaletteAsset         — color swatches
    GradientAsset        — continuous multi-stop color ramps (from .ggr)
    FlareAsset           — atmospheric glow objects (from .gflare)
    SurfacePatternAsset  — tileable texture (stub for .pat)
    VariantBrushBundle   — multi-stamp variant set (stub for .gih)
    BrushRecipe          — fully assembled, reference-resolved brush definition
"""


# ---------------------------------------------------------------------------
# DEPENDENCY TRACKING                                               v1
# ---------------------------------------------------------------------------
# This file calls:    Python standard library only
# This file is called by: trixel_brush_adapter.py (Same Folder)
#                         engine_mr.py             (Same Folder)
#                         engine_debug_mr.py       (Same Folder)
#                         palette_mr.py            (Same Folder)
# ---------------------------------------------------------------------------
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


# ---------------------------------------------------------------------------
# Shape
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BrushShapeAsset:
    """
    Normalized brush tip.

    shape_kind: 'parametric' or 'bitmap'

    Parametric (from .vbr):
        radius, aspect, hardness, spacing_pct, shape_type, spikes, angle
        All bitmap fields are None.

    Bitmap (from .gbr or .pgm):
        width, height, depth, bitmap_path, spacing_px
        All parametric fields are None except spacing_pct which mirrors
        spacing_px as a percentage for uniform downstream handling.

    spacing_pct is always populated regardless of source:
        - vbr: taken directly from file (1.0 = touching stamps)
        - gbr: converted from the header spacing integer (spacing / 10.0)
        - pgm: defaults to 1.0 (no header spacing in PGM)
    """
    name:         str
    source_format: str        # 'vbr' | 'gbr' | 'pgm'
    shape_kind:   str         # 'parametric' | 'bitmap'

    # --- Parametric fields (vbr) ---
    radius:       Optional[float]  # brush size in pixels
    aspect:       Optional[float]  # 25.0 = GIMP default round
    hardness:     Optional[float]  # 0.0 (soft) – 1.0 (hard)
    shape_type:   Optional[str]    # 'circle' | 'square' | 'diamond'
    spikes:       Optional[int]    # polygon spoke count (v1.5 only)
    angle:        Optional[float]  # rotation degrees (gamma field)

    # --- Bitmap fields (gbr / pgm) ---
    width:        Optional[int]
    height:       Optional[int]
    depth:        Optional[int]    # 1 = grayscale alpha mask, 3 = RGB stamp
    bitmap_path:  Optional[str]    # path to source file; load lazily

    # --- Common ---
    spacing_pct:  float            # stamp distance multiplier, always present

    def is_parametric(self) -> bool:
        return self.shape_kind == "parametric"

    def is_bitmap(self) -> bool:
        return self.shape_kind == "bitmap"

    def to_dict(self) -> dict:
        return {
            "name":          self.name,
            "source_format": self.source_format,
            "shape_kind":    self.shape_kind,
            "radius":        self.radius,
            "aspect":        self.aspect,
            "hardness":      self.hardness,
            "shape_type":    self.shape_type,
            "spikes":        self.spikes,
            "angle":         self.angle,
            "width":         self.width,
            "height":        self.height,
            "depth":         self.depth,
            "bitmap_path":   self.bitmap_path,
            "spacing_pct":   self.spacing_pct,
        }


# ---------------------------------------------------------------------------
# Dynamics
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ActiveCurve:
    """
    One live input→output mapping.

    output_channel: what this curve modulates
        e.g. 'opacity', 'size', 'angle', 'jitter', 'color', 'force'
    input_source: what drives it
        e.g. 'pressure', 'velocity', 'direction', 'tilt', 'random', 'fade'
    samples: 256-point LUT, values in [0.0, 1.0]
        samples[0] = output at minimum input
        samples[255] = output at maximum input
    """
    output_channel: str
    input_source:   str
    samples:        tuple[float, ...]   # always length 256

    def sample_at(self, t: float) -> float:
        """
        Interpolate the LUT at normalized input t ∈ [0.0, 1.0].
        Uses nearest-index lookup (floor). Caller can lerp if needed.
        """
        idx = max(0, min(255, int(t * 255)))
        return self.samples[idx]

    def to_dict(self) -> dict:
        return {
            "output_channel": self.output_channel,
            "input_source":   self.input_source,
            "samples":        list(self.samples),
        }


@dataclass(frozen=True)
class BrushDynamicsAsset:
    """
    Normalized dynamics preset.

    active_curves: all live (output, input) mappings as a flat tuple.
        Inactive curves (use-X = no) are excluded.

    active_channels: frozenset of output channel names that have
        at least one active input. Quick membership test.
    """
    name:            str
    source_format:   str                     # 'gdyn'
    active_curves:   tuple[ActiveCurve, ...]
    active_channels: frozenset[str]

    def curves_for(self, output_channel: str) -> list[ActiveCurve]:
        """Return all active curves driving a given output channel."""
        return [c for c in self.active_curves if c.output_channel == output_channel]

    def has_channel(self, output_channel: str) -> bool:
        return output_channel in self.active_channels

    def to_dict(self) -> dict:
        return {
            "name":            self.name,
            "source_format":   self.source_format,
            "active_channels": sorted(self.active_channels),
            "active_curves":   [c.to_dict() for c in self.active_curves],
        }


# ---------------------------------------------------------------------------
# Preset
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BrushPresetAsset:
    """
    Normalized tool configuration snapshot.

    Asset references (brush_ref, dynamics_ref, gradient_ref) are unresolved
    name strings. The adapter resolves them when building a BrushRecipe.
    """
    name:             str
    source_format:    str              # 'gtp'
    tool:             Optional[str]    # e.g. 'gimp-paintbrush-tool'

    # Paint config
    opacity:          Optional[float]  # 0.0 – 1.0
    brush_size:       Optional[float]
    application_mode: Optional[str]    # e.g. 'incremental'
    use_jitter:       bool
    dynamics_enabled: bool
    fade_length:      Optional[float]
    fade_unit:        Optional[str]    # 'percent' | 'pixels' | etc.

    # Unresolved asset references
    brush_ref:        Optional[str]
    dynamics_ref:     Optional[str]
    gradient_ref:     Optional[str]

    # Active slot flags
    use_brush:        bool
    use_dynamics:     bool
    use_gradient:     bool
    use_pattern:      bool
    use_palette:      bool

    def to_dict(self) -> dict:
        return {
            "name":             self.name,
            "source_format":    self.source_format,
            "tool":             self.tool,
            "opacity":          self.opacity,
            "brush_size":       self.brush_size,
            "application_mode": self.application_mode,
            "use_jitter":       self.use_jitter,
            "dynamics_enabled": self.dynamics_enabled,
            "fade_length":      self.fade_length,
            "fade_unit":        self.fade_unit,
            "brush_ref":        self.brush_ref,
            "dynamics_ref":     self.dynamics_ref,
            "gradient_ref":     self.gradient_ref,
            "use_brush":        self.use_brush,
            "use_dynamics":     self.use_dynamics,
            "use_gradient":     self.use_gradient,
            "use_pattern":      self.use_pattern,
            "use_palette":      self.use_palette,
        }


# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PaletteAsset:
    """
    Normalized color palette.

    colors: (r, g, b) tuples, values 0-255, in file order.
    labels: matching tuple of optional string labels (annotations stripped).
    columns: display hint from file header (0 if unset).
    """
    name:    str
    source_format: str           # 'gpl'
    columns: int
    colors:  tuple[tuple[int, int, int], ...]
    labels:  tuple[Optional[str], ...]

    def __len__(self) -> int:
        return len(self.colors)

    def color_at(self, index: int) -> tuple[int, int, int]:
        return self.colors[index]

    def to_hex(self, index: int) -> str:
        r, g, b = self.colors[index]
        return f"#{r:02X}{g:02X}{b:02X}"

    def to_dict(self) -> dict:
        return {
            "name":          self.name,
            "source_format": self.source_format,
            "columns":       self.columns,
            "colors": [
                {"r": r, "g": g, "b": b, "label": lbl,
                 "hex": f"#{r:02X}{g:02X}{b:02X}"}
                for (r, g, b), lbl in zip(self.colors, self.labels)
            ],
        }


# ---------------------------------------------------------------------------
# Gradient
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class GradientSegment:
    """One piecewise segment of a GradientAsset."""
    l: float   # left endpoint [0, 1]
    m: float   # midpoint [l, r]
    r: float   # right endpoint [0, 1]
    rgba0: tuple[float, float, float, float]
    rgba1: tuple[float, float, float, float]
    blend_type: int
    color_mode: int
    
    def to_dict(self) -> dict:
        return {
            "l": self.l, "m": self.m, "r": self.r,
            "rgba0": self.rgba0, "rgba1": self.rgba1,
            "blend_type": self.blend_type, "color_mode": self.color_mode,
        }

@dataclass(frozen=True)
class GradientAsset:
    """
    Normalized continuous color gradient (from .ggr).
    Segments define continuous interpolation across [0, 1] space.
    """
    name: str
    source_format: str           # 'ggr'
    segments: tuple[GradientSegment, ...]
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "source_format": self.source_format,
            "segments": [s.to_dict() for s in self.segments],
        }

# ---------------------------------------------------------------------------
# Atmosphere
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FlareAsset:
    """Normalized Atmospheric Flare object (from .gflare)"""
    name: str
    source_format: str
    
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

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "source_format": self.source_format,
            "shape": self.shape,
        }

# ---------------------------------------------------------------------------
# Surface Pattern
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SurfacePatternAsset:
    """
    Tileable RGB texture (from .pat).
    Pixel data lives on disk; load lazily via bitmap_path.
    """
    name:         str
    source_format: str     # 'pat'
    width:        int
    height:       int
    depth:        int      # always 3 for .pat (RGB)
    bitmap_path:  Optional[str]

    def to_dict(self) -> dict:
        return {
            "name":          self.name,
            "source_format": self.source_format,
            "width":         self.width,
            "height":        self.height,
            "depth":         self.depth,
            "bitmap_path":   self.bitmap_path,
        }


# ---------------------------------------------------------------------------
# Variant Bundle (stub — full implementation comes with .gih parser)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class VariantBrushBundle:
    """
    Multi-stamp variant container (from .gih).

    A bundle holds N bitmap cells and a selection mode that determines
    which cell is stamped on each paint event:
        'random'     — pick any cell at random each stamp
        'incremental'— cycle through cells in order
        'angular'    — choose cell based on stroke direction
        'velocity'   — choose cell based on stroke speed
        'pressure'   — choose cell based on tablet pressure

    cells: tuple of BrushShapeAsset (bitmap kind), one per cell.
    Populated by the .gih parser (not yet implemented).
    """
    name:           str
    source_format:  str   # 'gih'
    ncells:         int
    selection_mode: str   # 'random' | 'incremental' | 'angular' | 'velocity' | 'pressure'
    step:           float # stamp spacing percentage
    cells:          tuple[BrushShapeAsset, ...]

    def to_dict(self) -> dict:
        return {
            "name":           self.name,
            "source_format":  self.source_format,
            "ncells":         self.ncells,
            "selection_mode": self.selection_mode,
            "step":           self.step,
            "cells":          [c.to_dict() for c in self.cells],
        }


# ---------------------------------------------------------------------------
# Recipe — the assembled product
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BrushRecipe:
    """
    A fully assembled, reference-resolved Trixel brush definition.

    This is the primary output of the adapter layer and the primary input
    to the rendering/stroke layer. It knows nothing about GIMP file formats.

    recipe_id: deterministic string identifier built from constituent names.
        Format: '{shape_fmt}:{shape_name}[+dyn:{dyn_name}][+pal:{pal_name}]'
        Stable across runs for the same inputs.

    shape:    always present — defines brush tip geometry
    dynamics: optional — defines input response curves
    preset:   optional — carries tool config (opacity, size, jitter, fade)
    palette:  optional — color set for this recipe
    gradient: Optional[GradientAsset]       # replaces palette when true gradient is used

    variant_bundle: optional — replaces shape when the brush is a .gih hose.
        When present, shape is None and the bundle provides cell selection.
    """
    recipe_id:      str
    shape:          Optional[BrushShapeAsset]
    dynamics:       Optional[BrushDynamicsAsset]
    preset:         Optional[BrushPresetAsset]
    palette:        Optional[PaletteAsset]
    gradient:       Optional[GradientAsset]
    variant_bundle: Optional[VariantBrushBundle]  # replaces shape for .gih

    def has_dynamics(self) -> bool:
        return self.dynamics is not None

    def has_palette(self) -> bool:
        return self.palette is not None

    def is_variant(self) -> bool:
        return self.variant_bundle is not None

    def opacity(self) -> float:
        """Return effective opacity, falling back to 1.0."""
        if self.preset and self.preset.opacity is not None:
            return self.preset.opacity
        return 1.0

    def size(self) -> Optional[float]:
        """Return effective brush size from preset if available."""
        if self.preset and self.preset.brush_size is not None:
            return self.preset.brush_size
        if self.shape and self.shape.radius is not None:
            return self.shape.radius * 2.0
        return None

    def to_dict(self) -> dict:
        """
        Neutral export shape for ZW / ZONJ / AP / Godot.
        No GIMP-specific field names or format references at top level.
        """
        return {
            "recipe_id":      self.recipe_id,
            "shape":          self.shape.to_dict() if self.shape else None,
            "dynamics":       self.dynamics.to_dict() if self.dynamics else None,
            "preset":         self.preset.to_dict() if self.preset else None,
            "palette":        self.palette.to_dict() if self.palette else None,
            "gradient":       self.gradient.to_dict() if self.gradient else None,
            "variant_bundle": self.variant_bundle.to_dict() if self.variant_bundle else None,
        }
