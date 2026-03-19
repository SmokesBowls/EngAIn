"""
trixel_brush_adapter.py — Trixel Brush Asset Adapter

Translates parser outputs (GIMP-specific dataclasses) into normalized
Trixel asset models (brush_models_mr.py). Resolves cross-references.
Builds BrushRecipe — the assembled product.

This file is the boundary between "GIMP format knowledge" and
"Trixel brush language." Nothing downstream should ever import a parser.

Public surface:
    adapt_vbr(VbrBrush)     → BrushShapeAsset
    adapt_gbr(GbrBrush)     → BrushShapeAsset
    adapt_pgm(PgmBrush)     → BrushShapeAsset
    adapt_gdyn(DynPreset)   → BrushDynamicsAsset
    adapt_gtp(ToolPreset)   → BrushPresetAsset
    adapt_gpl(Palette)      → PaletteAsset
    adapt_pat(GbrBrush)     → SurfacePatternAsset

    AssetRegistry           — loads files from disk, indexes by name
    AssetRegistry.build_recipe_from_preset(name)  → BrushRecipe
    AssetRegistry.build_recipe_from_parts(...)    → BrushRecipe
"""


# ---------------------------------------------------------------------------
# DEPENDENCY TRACKING                                               v1
# ---------------------------------------------------------------------------
# This file calls:    brush_models_mr.py          (Same Folder)
#                     brushes/vbr_parser_mr.py    (Different Folder: brushes/)
#                     brushes/gbr_parser_mr.py    (Different Folder: brushes/)
#                     brushes/gdyn_parser_mr.py   (Different Folder: brushes/)
#                     brushes/gtp_parser_mr.py    (Different Folder: brushes/)
#                     brushes/gpl_parser_mr.py    (Different Folder: brushes/)
#                     brushes/gih_parser_mr.py    (Different Folder: brushes/)
# This file is called by: engine_debug_mr.py      (Same Folder)
#                          __main__ (CLI direct execution)
# ---------------------------------------------------------------------------
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional

from brush_models_mr import (
    ActiveCurve,
    BrushDynamicsAsset,
    BrushPresetAsset,
    BrushRecipe,
    BrushShapeAsset,
    PaletteAsset,
    GradientAsset,
    FlareAsset,
    SurfacePatternAsset,
    VariantBrushBundle,
)

# Parser imports — guarded so the adapter degrades gracefully if a parser
# is missing (e.g. during incremental development).
try:
    from brushes.vbr_parser_mr import VbrBrush, parse_vbr
    _HAS_VBR = True
except ImportError:
    _HAS_VBR = False

try:
    from brushes.gbr_parser_mr import GbrBrush, PgmBrush, parse_gbr, parse_pgm
    _HAS_GBR = True
except ImportError:
    _HAS_GBR = False

try:
    from brushes.gdyn_parser_mr import DynPreset, parse_gdyn
    _HAS_GDYN = True
except ImportError:
    _HAS_GDYN = False

try:
    from brushes.gtp_parser_mr import ToolPreset, parse_gtp
    _HAS_GTP = True
except ImportError:
    _HAS_GTP = False

try:
    from brushes.gpl_parser_mr import Palette, parse_gpl
    _HAS_GPL = True
except ImportError:
    _HAS_GPL = False

try:
    from brushes.ggr_parser_mr import GgrGradient, parse_ggr
    _HAS_GGR = True
except ImportError:
    _HAS_GGR = False

try:
    from brushes.gflare_parser_mr import ParsedGflare, parse_gflare
    _HAS_GFLARE = True
except ImportError:
    _HAS_GFLARE = False

try:
    from brushes.gih_parser_mr import GihBrush, GihCell, parse_gih
    _HAS_GIH = True
except ImportError:
    _HAS_GIH = False


# ---------------------------------------------------------------------------
# Adapt: parsers → normalized models
# ---------------------------------------------------------------------------

def _gbr_spacing_to_ratio(raw: int) -> float:
    """
    Convert a raw .gbr header spacing integer to the engine spacing ratio.

    GIMP stores brush spacing as an integer where:
        raw = GUI_display_percent * 100
        e.g. GUI shows "128%" → raw = 12800

    Engine geometry (see stroke_to_events):
        stamp_distance = base_radius * 2.0 * spacing_pct
        where base_radius is the half-extent of the brush in pixels.
    So spacing_pct is a fraction of brush *diameter*:
        1.0 → stamps placed one diameter apart (touching)
        0.25 → heavy overlap (quarter-diameter between centres)
        2.0 → stamps with a full-diameter gap between them

    Conversion: ratio = raw / 10000

    Confirmed against 7 GIMP 2.10 stock brushes:
        pixel.gbr       raw=12880  → 1.288  → 2.6px on 1px brush    ✓ slight gap
        Bristles-01     raw=834    → 0.083  → 10.7px on 128px brush  ✓ dense overlap
        Hatch-Pen-01    raw=2632   → 0.263  → 67.4px on 256px brush  ✓ tight hatch
        Charcoal-01     raw=7747   → 0.775  → 99.2px on 128px brush  ✓ medium spacing
        Smoke           raw=12883  → 1.288  → 432.9px on 336px brush ✓ scattered
        Cell-01         raw=12867  → 1.287  → 422.0px on 328px brush ✓ scattered
        galaxy          raw=19271  → 1.927  → 196.6px on 102px brush ✓ wide scatter

    Returns 1.0 (touching) for zero or missing values.
    """
    return (raw / 10000.0) if raw > 0 else 1.0


# Pinning assertions — if these fail, the spacing contract is broken
assert _gbr_spacing_to_ratio(12800) == 1.28,   "_gbr_spacing_to_ratio: 12800 should be 1.28"
assert _gbr_spacing_to_ratio(2632)  == 0.2632, "_gbr_spacing_to_ratio: 2632 should be 0.2632"
assert _gbr_spacing_to_ratio(0)     == 1.0,    "_gbr_spacing_to_ratio: 0 should be 1.0 (fallback)"


def adapt_vbr(brush: "VbrBrush") -> BrushShapeAsset:
    """Convert a parsed VbrBrush into a BrushShapeAsset (parametric)."""
    return BrushShapeAsset(
        name=brush.name,
        source_format="vbr",
        shape_kind="parametric",
        # parametric fields
        radius=brush.radius,
        aspect=brush.aspect,
        hardness=brush.hardness,
        shape_type=brush.shape,
        spikes=brush.spikes,
        angle=brush.gamma,
        # bitmap fields — not applicable
        width=None,
        height=None,
        depth=None,
        bitmap_path=None,
        # common
        spacing_pct=brush.spacing,
    )


def adapt_gbr(brush: "GbrBrush") -> BrushShapeAsset:
    """
    Convert a parsed GbrBrush into a BrushShapeAsset (bitmap).

    GIMP's default .gbr internal name field is often the placeholder string
    "GIMP" rather than a meaningful name. When we detect that, fall back to
    the source filename stem so registry keys are unique and useful.

    spacing_pct: gbr header spacing is a percentage integer (10 = tight).
    Normalized to the vbr-compatible multiplier: header_pct / 10.0
    """
    # Use filename stem when internal name is the GIMP placeholder
    name = brush.name
    if not name or name.upper() in ("GIMP", ""):
        name = Path(brush.source_path).stem if brush.source_path else "gbr_brush"

    spacing_pct = _gbr_spacing_to_ratio(brush.spacing)

    return BrushShapeAsset(
        name=name,
        source_format="gbr",
        shape_kind="bitmap",
        # parametric fields — not applicable
        radius=None,
        aspect=None,
        hardness=None,
        shape_type=None,
        spikes=None,
        angle=None,
        # bitmap fields
        width=brush.width,
        height=brush.height,
        depth=brush.depth,
        bitmap_path=brush.source_path,
        # common
        spacing_pct=spacing_pct,
    )


def adapt_pgm(brush: "PgmBrush") -> BrushShapeAsset:
    """
    Convert a parsed PgmBrush into a BrushShapeAsset (bitmap, grayscale).
    PGM has no spacing header; default to 1.0.
    """
    name = Path(brush.source_path).stem if brush.source_path else "pgm_brush"
    return BrushShapeAsset(
        name=name,
        source_format="pgm",
        shape_kind="bitmap",
        radius=None,
        aspect=None,
        hardness=None,
        shape_type=None,
        spikes=None,
        angle=None,
        width=brush.width,
        height=brush.height,
        depth=1,
        bitmap_path=brush.source_path,
        spacing_pct=1.0,
    )


def adapt_gdyn(preset: "DynPreset") -> BrushDynamicsAsset:
    """
    Convert a parsed DynPreset into a BrushDynamicsAsset.

    Only active (use-X = yes) curves are included.
    Inactive curves are the identity ramp and carry no brush information.
    """
    curves: list[ActiveCurve] = []
    active_channels: set[str] = set()

    _IDENTITY = tuple(i / 255.0 for i in range(256))

    for channel_name, dyn_output in preset.outputs.items():
        if not dyn_output.is_active():
            continue
        active_channels.add(channel_name)
        for input_name in dyn_output.active_inputs:
            if input_name in dyn_output.curves:
                samples = dyn_output.curves[input_name].samples
            else:
                # Older format: flag set but no embedded LUT — use identity ramp
                samples = _IDENTITY
            curves.append(ActiveCurve(
                output_channel=channel_name,
                input_source=input_name,
                samples=samples,
            ))

    return BrushDynamicsAsset(
        name=preset.name,
        source_format="gdyn",
        active_curves=tuple(curves),
        active_channels=frozenset(active_channels),
    )


def adapt_gtp(preset: "ToolPreset") -> BrushPresetAsset:
    """Convert a parsed ToolPreset into a BrushPresetAsset."""
    return BrushPresetAsset(
        name=preset.name,
        source_format="gtp",
        tool=preset.tool,
        opacity=preset.opacity,
        brush_size=preset.brush_size,
        application_mode=preset.application_mode,
        use_jitter=preset.use_jitter,
        dynamics_enabled=preset.dynamics_enabled,
        fade_length=preset.fade_length,
        fade_unit=preset.fade_unit,
        brush_ref=preset.brush_name if preset.use_brush else None,
        dynamics_ref=preset.dynamics_name if preset.use_dynamics else None,
        gradient_ref=preset.gradient_name if preset.use_gradient else None,
        use_brush=preset.use_brush,
        use_dynamics=preset.use_dynamics,
        use_gradient=preset.use_gradient,
        use_pattern=preset.use_pattern,
        use_palette=preset.use_palette,
    )


def adapt_gpl(palette: "Palette") -> PaletteAsset:
    """
    Convert a parsed Palette into a PaletteAsset.

    Labels are stored verbatim. Visibone-style annotations like
    '(255 255 255) #FFFFFF' are preserved; stripping is the caller's job.
    """
    colors: list[tuple[int, int, int]] = []
    labels: list[Optional[str]] = []

    for entry in palette.colors:
        colors.append((entry.r, entry.g, entry.b))
        labels.append(entry.label)

    return PaletteAsset(
        name=palette.name,
        source_format="gpl",
        columns=palette.columns,
        colors=tuple(colors),
        labels=tuple(labels),
    )


def adapt_ggr(gradient: "GgrGradient") -> GradientAsset:
    """Convert a parsed GgrGradient into a GradientAsset."""
    from brush_models_mr import GradientSegment
    segs = []
    for s in gradient.segments:
        segs.append(GradientSegment(
            l=s.l, m=s.m, r=s.r,
            rgba0=(s.r0, s.g0, s.b0, s.a0),
            rgba1=(s.r1, s.g1, s.b1, s.a1),
            blend_type=s.blend_type,
            color_mode=s.color_mode,
        ))
    return GradientAsset(
        name=gradient.name,
        source_format="ggr",
        segments=tuple(segs)
    )

def adapt_gflare(gflare: "ParsedGflare") -> FlareAsset:
    return FlareAsset(
        name=gflare.name,
        source_format="gflare",
        glow_opacity=gflare.glow_opacity, glow_blend=gflare.glow_blend,
        rays_opacity=gflare.rays_opacity, rays_blend=gflare.rays_blend,
        sec_opacity=gflare.sec_opacity, sec_blend=gflare.sec_blend,
        glow_radial=gflare.glow_radial, glow_angular=gflare.glow_angular, glow_size=gflare.glow_size,
        glow_radius=gflare.glow_radius, glow_rotation=gflare.glow_rotation, glow_hue=gflare.glow_hue,
        rays_radial=gflare.rays_radial, rays_angular=gflare.rays_angular, rays_size=gflare.rays_size,
        rays_radius=gflare.rays_radius, rays_rotation=gflare.rays_rotation, rays_hue=gflare.rays_hue,
        rays_count=gflare.rays_count, rays_thickness=gflare.rays_thickness,
        sec_radial=gflare.sec_radial, sec_angular=gflare.sec_angular, sec_size=gflare.sec_size,
        sec_radius=gflare.sec_radius, sec_rotation=gflare.sec_rotation, sec_hue=gflare.sec_hue,
        shape=gflare.shape, shape_edges=gflare.shape_edges, seed=gflare.seed
    )

def adapt_gih(brush: "GihBrush") -> VariantBrushBundle:
    """
    Convert a parsed GihBrush into a VariantBrushBundle.

    Each cell becomes a BrushShapeAsset (bitmap kind).
    The primary selection mode is taken from axis 0.
    Multi-axis bundles (dim=2 or dim=3) expose the full axes list
    in the bundle's selection_mode field as a slash-joined string,
    e.g. 'angular/random' or 'pressure/ytilt/xtilt'.

    step is normalized from the GIH percentage to the same
    spacing_pct convention used by vbr/gbr: step/100.
    """
    cells: list[BrushShapeAsset] = []

    for cell in brush.cells:
        cell_name = f"{brush.name} [{cell.index}]"
        spacing_pct = brush.step / 100.0

        cells.append(BrushShapeAsset(
            name=cell_name,
            source_format="gih",
            shape_kind="bitmap",
            radius=None, aspect=None, hardness=None,
            shape_type=None, spikes=None, angle=None,
            width=cell.width,
            height=cell.height,
            depth=cell.depth,
            bitmap_path=brush.source_path,
            # pixel data is loaded lazily from source_path at stamp time
            spacing_pct=spacing_pct,
        ))

    # Multi-axis mode string: 'random' | 'angular/random' | 'pressure/ytilt/xtilt'
    selection_mode = "/".join(ax.mode for ax in brush.axes)

    return VariantBrushBundle(
        name=brush.name,
        source_format="gih",
        ncells=brush.ncells,
        selection_mode=selection_mode,
        step=brush.step / 100.0,
        cells=tuple(cells),
    )
    """
    Convert a .pat GbrBrush into a SurfacePatternAsset.

    .pat files are identical to .gbr at the binary level but carry RGB
    tileable texture data rather than grayscale alpha masks.
    """
    # Strip internal 'GPAT' prefix from name if present
    name = brush.name
    if name.upper().startswith("GPAT"):
        name = name[4:]

    return SurfacePatternAsset(
        name=name,
        source_format="pat",
        width=brush.width,
        height=brush.height,
        depth=brush.depth,
        bitmap_path=brush.source_path,
    )


# ---------------------------------------------------------------------------
# Recipe ID builder
# ---------------------------------------------------------------------------



def adapt_pat(brush: "GbrBrush") -> SurfacePatternAsset:
    """
    Convert a .pat GbrBrush into a SurfacePatternAsset.

    .pat files are identical to .gbr at the binary level but carry RGB
    tileable texture data rather than grayscale alpha masks.
    """
    # Strip internal 'GPAT' prefix from name if present
    name = brush.name
    if name.upper().startswith("GPAT"):
        name = name[4:]
    # Also apply the same placeholder fallback as gbr
    if not name or name.upper() in ("GIMP", ""):
        name = Path(brush.source_path).stem if brush.source_path else "pat_brush"

    return SurfacePatternAsset(
        name=name,
        source_format="pat",
        width=brush.width,
        height=brush.height,
        depth=brush.depth,
        bitmap_path=brush.source_path,
    )

def _make_recipe_id(
    shape: Optional[BrushShapeAsset],
    dynamics: Optional[BrushDynamicsAsset],
    preset: Optional[BrushPresetAsset],
    palette: Optional[PaletteAsset],
    gradient: Optional[GradientAsset],
    variant_bundle: Optional[VariantBrushBundle],
) -> str:
    """
    Build a deterministic recipe identifier from constituent names.
    Format: '{shape_fmt}:{shape_name}[+dyn:{dyn_name}][+pre:{pre_name}][+pal:{pal_name}]'
    """
    def _slug(s: str) -> str:
        # Replace non-alphanum with underscore
        s = re.sub(r"[^a-zA-Z0-9_-]", "_", s)
        # Collapse consecutive underscores
        s = re.sub(r"_+", "_", s)
        # Strip leading/trailing underscores
        return s.strip("_")

    if variant_bundle:
        parts = [f"gih:{_slug(variant_bundle.name)}"]
    elif shape:
        parts = [f"{shape.source_format}:{_slug(shape.name)}"]
    else:
        parts = ["unknown:unnamed"]

    if dynamics:
        parts.append(f"dyn:{_slug(dynamics.name)}")
    if preset:
        parts.append(f"pre:{_slug(preset.name)}")
    if palette:
        parts.append(f"pal:{_slug(palette.name)}")
    if gradient:
        parts.append(f"ggr:{_slug(gradient.name)}")

    return "+".join(parts)


# ---------------------------------------------------------------------------
# Asset Registry
# ---------------------------------------------------------------------------

class AssetRegistry:
    """
    Loads and indexes Trixel brush assets from a data directory.

    Spacing source priority (highest to lowest):
      1. Format metadata  — vbr/gih store spacing explicitly; always used
      2. spacing_overrides — per-name table set by the caller; deterministic
      3. Raw header value — gbr/pgm spacing from binary header via /10000
      4. Default 1.0      — only when header is zero or missing

    To override spacing for a specific asset:
        registry.spacing_overrides["Hatch-Pen-01"] = 0.5

    Overrides are applied at load time. Re-load the directory after changing them.
    """

    def __init__(self, spacing_overrides: Optional[dict] = None) -> None:
        self.shapes:          dict[str, BrushShapeAsset]    = {}
        self.dynamics:        dict[str, BrushDynamicsAsset] = {}
        self.presets:         dict[str, BrushPresetAsset]   = {}
        self.palettes:        dict[str, PaletteAsset]       = {}
        self.gradients:       dict[str, GradientAsset]      = {}
        self.flares:          dict[str, FlareAsset]         = {}
        self.patterns:        dict[str, SurfacePatternAsset] = {}
        self.variant_bundles: dict[str, VariantBrushBundle] = {}
        self._errors:         list[str]                     = []
        self._collisions:     list[str]                     = []
        # Per-asset-name spacing overrides. Applied after format metadata.
        self.spacing_overrides: dict[str, float] = spacing_overrides or {}

    # --- Loading ---

    def load_from_directory(self, directory: Path) -> None:
        """
        Scan a directory recursively and load all recognized asset files.
        Errors are collected in self.errors rather than raising, so a
        single bad file does not abort the whole load.
        """
        if not directory.exists():
            self._errors.append(f"Directory not found: {directory}")
            return

        for path in sorted(directory.rglob("*")):
            if not path.is_file():
                continue
            ext = path.suffix.lower()
            
            # GFlare files intentionally lack an extension, so catch them by their parent subfolder
            if ext == "" and path.parent.name == "gflare" and _HAS_GFLARE:
                try:
                    with open(path, "rb") as f:
                        magic = f.read(11)
                    if magic == b"GIMP GFlare":
                        try:
                            self._load_gflare(path)
                        except Exception as e:
                            self._errors.append(f"Failed to parse Flare {path.name}: {e}")
                        continue
                except Exception:
                    pass

            try:
                if ext == ".vbr" and _HAS_VBR:
                    self._load_vbr(path)
                elif ext == ".gbr" and _HAS_GBR:
                    self._load_gbr(path)
                elif ext == ".pgm" and _HAS_GBR:
                    self._load_pgm(path)
                elif ext == ".gdyn" and _HAS_GDYN:
                    self._load_gdyn(path)
                elif ext == ".gtp" and _HAS_GTP:
                    self._load_gtp(path)
                elif ext == ".gpl" and _HAS_GPL:
                    self._load_gpl(path)
                elif ext == ".ggr" and _HAS_GGR:
                    self._load_ggr(path)
                elif ext == ".pat" and _HAS_GBR:
                    self._load_pat(path)
                elif ext == ".gih" and _HAS_GIH:
                    self._load_gih(path)
            except Exception as exc:
                self._errors.append(f"{path.name}: {exc}")

    def _register(self, table: dict, name: str, asset, source_path: str) -> None:
        """
        Insert asset into table under name.
        Last-write-wins, but collisions are logged with both source paths
        so the override leaves footprints instead of doing sleight of hand.
        """
        if name in table:
            existing = getattr(table[name], "source_path", None) or \
                       getattr(table[name], "bitmap_path", None) or "unknown"
            self._collisions.append(
                f"name={name!r}  old={existing}  new={source_path}"
            )
        table[name] = asset

    def _apply_spacing_override(self, asset: BrushShapeAsset) -> BrushShapeAsset:
        """Return asset with spacing_pct replaced if an override exists for its name."""
        override = self.spacing_overrides.get(asset.name)
        if override is None:
            return asset
        return BrushShapeAsset(
            name=asset.name, source_format=asset.source_format,
            shape_kind=asset.shape_kind, radius=asset.radius,
            aspect=asset.aspect, hardness=asset.hardness,
            shape_type=asset.shape_type, spikes=asset.spikes,
            angle=asset.angle, width=asset.width, height=asset.height,
            depth=asset.depth, bitmap_path=asset.bitmap_path,
            spacing_pct=float(override),
        )

    def _load_vbr(self, path: Path) -> None:
        asset = self._apply_spacing_override(adapt_vbr(parse_vbr(path)))
        self._register(self.shapes, asset.name, asset, str(path))

    def _load_gbr(self, path: Path) -> None:
        asset = self._apply_spacing_override(adapt_gbr(parse_gbr(path)))
        self._register(self.shapes, asset.name, asset, str(path))

    def _load_pgm(self, path: Path) -> None:
        asset = self._apply_spacing_override(adapt_pgm(parse_pgm(path)))
        self._register(self.shapes, asset.name, asset, str(path))

    def _load_gdyn(self, path: Path) -> None:
        asset = adapt_gdyn(parse_gdyn(path))
        self._register(self.dynamics, asset.name, asset, str(path))

    def _load_gtp(self, path: Path) -> None:
        asset = adapt_gtp(parse_gtp(path))
        self._register(self.presets, asset.name, asset, str(path))

    def _load_gpl(self, path: Path) -> None:
        asset = adapt_gpl(parse_gpl(path))
        self._register(self.palettes, asset.name, asset, str(path))

    def _load_ggr(self, path: Path) -> None:
        asset = adapt_ggr(parse_ggr(path))
        self._register(self.gradients, asset.name, asset, str(path))

    def _load_gflare(self, path: Path) -> None:
        asset = adapt_gflare(parse_gflare(path))
        self._register(self.flares, asset.name, asset, str(path))

    def _load_pat(self, path: Path) -> None:
        raw = parse_gbr(path)
        if raw.depth == 3:
            asset = adapt_pat(raw)
            self._register(self.patterns, asset.name, asset, str(path))
        else:
            asset = adapt_gbr(raw)
            self._register(self.shapes, asset.name, asset, str(path))

    def _load_gih(self, path: Path) -> None:
        asset = adapt_gih(parse_gih(path))
        self._register(self.variant_bundles, asset.name, asset, str(path))

    @property
    def errors(self) -> list[str]:
        return list(self._errors)

    @property
    def collisions(self) -> list[str]:
        """
        Name collisions where a later file overwrote an earlier one.
        Last-write-wins; these are logged for traceability, not blocked.
        """
        return list(self._collisions)

    # --- Stats ---

    def summary(self) -> dict:
        return {
            "shapes":          len(self.shapes),
            "dynamics":        len(self.dynamics),
            "presets":         len(self.presets),
            "palettes":        len(self.palettes),
            "gradients":       len(self.gradients),
            "flares":          len(self.flares),
            "patterns":        len(self.patterns),
            "variant_bundles": len(self.variant_bundles),
            "errors":          len(self._errors),
            "collisions":      len(self._collisions),
        }

    # --- Recipe builders ---

    def classify_preset(self, preset_name: str) -> str:
        """
        Classify a preset into an intent category:
        'brush-usable'  — painting tools (paintbrush, pencil, ink, airbrush)
        'effect-only'   — smudge, blur, dodge/burn, clone, heal
        'crop-layout'   — crop, move, measure, text, selection tools
        'unresolved'    — missing references in registry
        'unknown'       — unhandled tool
        """
        preset = self.presets.get(preset_name)
        if not preset:
            return "unknown"
            
        tool = preset.tool or ""
        
        # 1. Structural/layout tools
        if any(x in tool for x in ("crop", "select", "move", "measure", "text", "path", "zoom", "color-picker", "bucket-fill", "blend")):
            return "crop-layout"
            
        # 2. Effect/modification tools
        if any(x in tool for x in ("smudge", "blur", "dodge", "burn", "heal", "clone", "eraser")):
            return "effect-only"
            
        # 3. Painting tools
        if any(x in tool for x in ("paintbrush", "pencil", "ink", "airbrush", "mypaint-brush")):
            # Validate references
            if preset.use_brush and preset.brush_ref:
                if preset.brush_ref not in self.shapes and preset.brush_ref not in self.variant_bundles:
                    return "unresolved"
            if preset.use_dynamics and preset.dynamics_ref:
                if preset.dynamics_ref not in self.dynamics:
                    return "unresolved"
            if preset.use_gradient and preset.gradient_ref:
                if preset.gradient_ref not in self.gradients:
                    return "unresolved"
            if preset.use_pattern and preset.brush_ref: # patterns are often stored in brush_ref for pattern tools
                if preset.brush_ref not in self.patterns and preset.brush_ref not in self.shapes:
                    return "unresolved"
                    
            return "brush-usable"
            
        return "unknown"

    def build_recipe_from_preset(self, preset_name: str, strict: bool = True) -> Optional[BrushRecipe]:
        """
        Build a BrushRecipe by resolving a named preset's references.

        If strict=True, only returns a recipe if classify_preset() == 'brush-usable'.
        Missing refs are silently skipped if strict is False.
        Returns None if the preset name is not found or fails strict classification.
        """
        if strict and self.classify_preset(preset_name) != "brush-usable":
            return None

        preset = self.presets.get(preset_name)
        if preset is None:
            return None

        # Brush reference can be a shape or a variant bundle (.gih hose)
        shape = self.shapes.get(preset.brush_ref) if preset.brush_ref else None
        bundle = self.variant_bundles.get(preset.brush_ref) if preset.brush_ref and not shape else None
        
        dynamics = self.dynamics.get(preset.dynamics_ref) if preset.dynamics_ref else None
        palette = self.palettes.get(preset.gradient_ref) if preset.gradient_ref and preset.gradient_ref in self.palettes else None
        gradient = self.gradients.get(preset.gradient_ref) if preset.gradient_ref and preset.gradient_ref in self.gradients else None

        recipe_id = _make_recipe_id(shape, dynamics, preset, palette, gradient, bundle)

        return BrushRecipe(
            recipe_id=recipe_id,
            shape=shape,
            dynamics=dynamics,
            preset=preset,
            palette=palette,
            gradient=gradient,
            variant_bundle=bundle,
        )

    def build_recipe_from_bundle(
        self,
        bundle_name: str,
        dynamics_name: Optional[str] = None,
        palette_name: Optional[str] = None,
        gradient_name: Optional[str] = None,
    ) -> Optional[BrushRecipe]:
        """
        Build a BrushRecipe from a VariantBrushBundle (loaded from .gih).

        The bundle replaces the shape slot. shape is None in the resulting
        recipe; the renderer checks is_variant() to dispatch correctly.

        Returns None if bundle_name is not found.
        """
        bundle = self.variant_bundles.get(bundle_name)
        if bundle is None:
            return None

        dynamics = self.dynamics.get(dynamics_name) if dynamics_name else None
        palette  = self.palettes.get(palette_name)  if palette_name  else None
        gradient = self.gradients.get(gradient_name) if gradient_name else None

        recipe_id = _make_recipe_id(None, dynamics, None, palette, gradient, bundle)

        return BrushRecipe(
            recipe_id=recipe_id,
            shape=None,
            dynamics=dynamics,
            preset=None,
            palette=palette,
            gradient=gradient,
            variant_bundle=bundle,
        )

    def build_recipe_from_parts(
        self,
        shape_name: str,
        dynamics_name: Optional[str] = None,
        palette_name: Optional[str] = None,
        gradient_name: Optional[str] = None,
    ) -> Optional[BrushRecipe]:
        """
        Build a BrushRecipe directly from named components.

        Useful for constructing recipes that don't have a .gtp preset file,
        e.g. when testing a vbr brush with a gdyn dynamics profile.

        Returns None if shape_name is not found.
        """
        shape = self.shapes.get(shape_name)
        if shape is None:
            return None

        dynamics = self.dynamics.get(dynamics_name) if dynamics_name else None
        palette  = self.palettes.get(palette_name)  if palette_name  else None
        gradient = self.gradients.get(gradient_name) if gradient_name else None

        recipe_id = _make_recipe_id(shape, dynamics, None, palette, gradient, None)

        return BrushRecipe(
            recipe_id=recipe_id,
            shape=shape,
            dynamics=dynamics,
            preset=None,
            palette=palette,
            gradient=gradient,
            variant_bundle=None,
        )

    def build_recipe_from_dict(self, d: dict) -> Optional[BrushRecipe]:
        """
        Build a BrushRecipe from a plain dict (deserialized from JSON/ZW).
        Convenience for round-tripping exported recipes.

        Looks up components by name. Returns None if required shape is missing.
        """
        shape_name    = d.get("shape_name")
        dynamics_name = d.get("dynamics_name")
        palette_name  = d.get("palette_name")
        preset_name   = d.get("preset_name")

        if preset_name:
            return self.build_recipe_from_preset(preset_name)
        if shape_name:
            return self.build_recipe_from_parts(shape_name, dynamics_name, palette_name)
        return None


# ---------------------------------------------------------------------------
# Smoke test — proves end-to-end path with real files
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data")

    print(f"Loading assets from: {root.resolve()}")
    registry = AssetRegistry()
    registry.load_from_directory(root)

    s = registry.summary()
    print(f"\nRegistry summary:")
    print(f"  shapes:   {s['shapes']}")
    print(f"  dynamics: {s['dynamics']}")
    print(f"  presets:  {s['presets']}")
    print(f"  palettes: {s['palettes']}")
    print(f"  patterns: {s['patterns']}")
    if s['errors']:
        print(f"  errors:   {s['errors']}")
        for e in registry.errors:
            print(f"    ! {e}")

    # Try to build recipes from every loaded preset
    print(f"\nRecipes from presets:")
    for preset_name in sorted(registry.presets):
        recipe = registry.build_recipe_from_preset(preset_name)
        if recipe:
            shape_desc = (
                f"shape={recipe.shape.name!r}" if recipe.shape
                else "shape=<unresolved>"
            )
            dyn_desc = (
                f"dyn={recipe.dynamics.name!r}" if recipe.dynamics
                else "dyn=none"
            )
            print(f"  [{recipe.recipe_id}]  {shape_desc}  {dyn_desc}")

    # Build a manual recipe if we have any shapes + dynamics
    if registry.shapes and registry.dynamics:
        shape_name = next(iter(registry.shapes))
        dyn_name   = next(iter(registry.dynamics))
        recipe = registry.build_recipe_from_parts(shape_name, dyn_name)
        if recipe:
            print(f"\nManual recipe built:")
            print(f"  id:       {recipe.recipe_id}")
            print(f"  opacity:  {recipe.opacity()}")
            print(f"  size:     {recipe.size()}")
            print(f"  dynamics: {recipe.dynamics.active_channels if recipe.dynamics else None}")
            print(f"\nFull recipe JSON:")
            print(json.dumps(recipe.to_dict(), indent=2))
