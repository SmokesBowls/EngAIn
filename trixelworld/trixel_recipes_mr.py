"""
trixel_recipes_mr.py — Trixel Named Recipe Definitions

Pure functional. No I/O. No asset loading.

This file defines the *intent* layer: named visual outcomes expressed as
frozen dataclasses. Each TrixelRecipeDef names a desired mark, specifies
which assets assemble it, and declares the ColourContext mode that gives
it style discipline.

The registry provides the parts. This file describes what to ask for.

Named outcomes (the floor):
    HARD_PIXEL      — crisp 1px mark, no falloff, no dynamics variation
    HATCH_TEXTURE   — dense crosshatch pattern, pressure modulates opacity
    CHARCOAL_GRAIN  — rough bitmap grain, soft edges, slight jitter
    BRISTLE_RAKE    — multi-bristle stamp, dense overlap, pressure-driven size
    OIL_SMEAR       — large bitmap stamp, low spacing, multiply blend

Public surface:
    TrixelRecipeDef             — frozen dataclass, one named outcome
    ALL_RECIPES                 — dict[str, TrixelRecipeDef], all known recipes
    build(registry, name)       → BrushRecipe | None
    build_all(registry)         → dict[str, BrushRecipe]
    describe(name)              → str  (human summary)
"""

# ---------------------------------------------------------------------------
# DEPENDENCY TRACKING                                               v1
# ---------------------------------------------------------------------------
# This file calls:    brush_models_mr.py          (Same Folder)
#                     trixel_brush_adapter.py     (Same Folder)
# This file is called by: trixel_demo_mr.py       (Same Folder)
#                          __main__ (CLI direct execution)
# ---------------------------------------------------------------------------

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from trixel_brush_adapter import AssetRegistry
    from brush_models_mr import BrushRecipe


# ---------------------------------------------------------------------------
# Recipe definition type
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TrixelRecipeDef:
    """
    Declares the intent for one named Trixel visual outcome.

    Fields:
        name         — canonical identifier, used as dict key
        label        — human display name
        shape_name   — asset name in registry.shapes (for bitmap/parametric)
        bundle_name  — asset name in registry.variant_bundles (for hose)
                       Exactly one of shape_name or bundle_name must be set.
        dynamics_name — asset name in registry.dynamics (None = no dynamics)
        palette_name  — asset name in registry.palettes (None = no palette)
        colour_mode   — ColourContext mode string (see palette_mr.py)
                        'index' | 'sequential' | 'gradient' | 'nearest' |
                        'elevation' | 'material' | 'dynamics'
        blend_mode    — rendering blend mode: 'normal' | 'multiply' |
                        'additive' | 'screen'
        spacing_override — override the asset's native spacing (None = use asset value)
        description   — one-sentence summary of intended visual result
    """
    name:              str
    label:             str
    shape_name:        Optional[str]
    bundle_name:       Optional[str]
    dynamics_name:     Optional[str]
    palette_name:      Optional[str]
    colour_mode:       str
    blend_mode:        str
    spacing_override:  Optional[float]
    description:       str

    def uses_bundle(self) -> bool:
        return self.bundle_name is not None

    def uses_shape(self) -> bool:
        return self.shape_name is not None


# ---------------------------------------------------------------------------
# Named recipe definitions
# ---------------------------------------------------------------------------

_HARD_PIXEL = TrixelRecipeDef(
    name="hard_pixel",
    label="Hard Pixel Mark",
    shape_name="1. Pixel",
    bundle_name=None,
    dynamics_name=None,            # no dynamics — every stamp identical
    palette_name=None,
    colour_mode="index",
    blend_mode="normal",
    spacing_override=None,          # uses native 1.288 ratio
    description=(
        "Crisp single-pixel parametric mark. No falloff, no dynamics. "
        "The hardest, most deliberate mark Trixel can place."
    ),
)

_HATCH_TEXTURE = TrixelRecipeDef(
    name="hatch_texture",
    label="Hatch Texture Mark",
    shape_name="Hatch-Pen-01",
    bundle_name=None,
    dynamics_name="Pressure Opacity",   # pressure controls opacity only
    palette_name=None,
    colour_mode="index",
    blend_mode="multiply",              # multiply makes hatching additive
    spacing_override=None,              # native 0.2632 — dense
    description=(
        "Dense crosshatch bitmap stamp with multiply blend. "
        "Pressure modulates opacity. Repeated stamps build up ink density."
    ),
)

_CHARCOAL_GRAIN = TrixelRecipeDef(
    name="charcoal_grain",
    label="Charcoal Grain Mark",
    shape_name="Charcoal-01",
    bundle_name=None,
    dynamics_name="Pencil Generic",     # drives opacity, size, slight jitter
    palette_name=None,
    colour_mode="index",
    blend_mode="normal",
    spacing_override=0.6,              # tighter than native 0.775 for richer grain
    description=(
        "Rough bitmap grain from Charcoal-01. Pencil Generic dynamics give "
        "organic size and opacity variation. Medium density."
    ),
)

_BRISTLE_RAKE = TrixelRecipeDef(
    name="bristle_rake",
    label="Bristle Rake Mark",
    shape_name="Bristles-01",
    bundle_name=None,
    dynamics_name="Basic Dynamics",    # opacity + size from pressure/velocity
    palette_name=None,
    colour_mode="index",
    blend_mode="normal",
    spacing_override=None,             # native 0.083 — very dense, continuous
    description=(
        "Dense multi-bristle overlap with Basic Dynamics driving size. "
        "Very tight spacing produces continuous bristle texture."
    ),
)

_OIL_SMEAR = TrixelRecipeDef(
    name="oil_smear",
    label="Oil Smear Mark",
    shape_name="Oils-01",
    bundle_name=None,
    dynamics_name="Pressure Opacity",
    palette_name=None,
    colour_mode="index",
    blend_mode="normal",
    spacing_override=0.5,             # tighter than native 0.136 for paint body
    description=(
        "Large oil paint bitmap stamp. Tight spacing builds up paint body. "
        "Pressure controls transparency — press harder for full colour."
    ),
)

_ACRYLIC_VARIANT = TrixelRecipeDef(
    name="acrylic_variant",
    label="Acrylic Variant Hose",
    shape_name=None,
    bundle_name="Acrylic 03",
    dynamics_name="Pencil Generic",
    palette_name=None,
    colour_mode="gradient",            # gradient along stroke
    blend_mode="normal",
    spacing_override=None,
    description=(
        "Four-cell acrylic hose with random cell selection and gradient colour. "
        "Produces natural media variation across the stroke."
    ),
)

_TERRAIN_STROKE = TrixelRecipeDef(
    name="terrain_stroke",
    label="Terrain Colour Stroke",
    shape_name="2. Hardness 050",
    bundle_name=None,
    dynamics_name="Pencil Generic",
    palette_name="Topographic",
    colour_mode="elevation",           # colour driven by stroke position
    blend_mode="normal",
    spacing_override=None,
    description=(
        "Soft parametric brush with Topographic palette in elevation mode. "
        "Demonstrates palette-as-material: colour encodes world height."
    ),
)



_NEBULA_WASH = TrixelRecipeDef(
    name="nebula_wash",
    label="Nebula Atmosphere Wash",
    shape_name="Smoke",
    bundle_name=None,
    dynamics_name="Dynamics Random",
    palette_name=None,
    colour_mode="index",
    blend_mode="screen",
    spacing_override=1.1,
    description=(
        "Smoke bitmap in screen blend with random dynamics. "
        "Large soft stamp for nebula atmosphere, gas clouds, void glow."
    ),
)

_BRASS_GRAIN = TrixelRecipeDef(
    name="brass_grain",
    label="Burnt Brass Grain",
    shape_name="Charcoal-02",
    bundle_name=None,
    dynamics_name="Pencil Generic",
    palette_name=None,
    colour_mode="index",
    blend_mode="normal",
    spacing_override=0.55,
    description=(
        "Charcoal-02 grain in warm brass/copper tones. "
        "Directional grain for metal surfaces, lore trim, and ancient fixtures."
    ),
)

_SCALE_PANEL = TrixelRecipeDef(
    name="scale_panel",
    label="Dragon Scale Panel",
    shape_name="Hatch-Pen-01",
    bundle_name=None,
    dynamics_name="Pressure Opacity",
    palette_name=None,
    colour_mode="index",
    blend_mode="multiply",
    spacing_override=0.30,
    description=(
        "Hatch-Pen-01 in multiply at tight spacing. "
        "Short-segment vertical strokes produce scale-like tessellation "
        "for roofing, paneling, and armoured surfaces."
    ),
)

_VOID_ACCENT = TrixelRecipeDef(
    name="void_accent",
    label="Void Essence Accent",
    shape_name="Smoke",
    bundle_name=None,
    dynamics_name="Dynamics Random",
    palette_name=None,
    colour_mode="index",
    blend_mode="screen",
    spacing_override=1.3,
    description=(
        "Smoke bitmap, screen blend, warm bronze tones. "
        "Sparse accent for void portals, dark lore windows, and enchanted recesses."
    ),
)

# ---------------------------------------------------------------------------
# Public registry of all named recipes
# ---------------------------------------------------------------------------

ALL_RECIPES: dict[str, TrixelRecipeDef] = {
    r.name: r for r in [
        _HARD_PIXEL,
        _HATCH_TEXTURE,
        _CHARCOAL_GRAIN,
        _BRISTLE_RAKE,
        _OIL_SMEAR,
        _ACRYLIC_VARIANT,
        _TERRAIN_STROKE,
        _NEBULA_WASH,
        _BRASS_GRAIN,
        _SCALE_PANEL,
        _VOID_ACCENT,
    ]
}


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------

def build(registry: "AssetRegistry", name: str) -> Optional["BrushRecipe"]:
    """
    Assemble a named TrixelRecipeDef into a live BrushRecipe.

    Returns None if the named recipe is not in ALL_RECIPES, or if a
    required asset is not found in the registry. Errors are silent so
    callers can gracefully degrade when optional assets are absent.
    """
    defn = ALL_RECIPES.get(name)
    if defn is None:
        return None

    # Apply spacing override to registry if set
    original_spacing = None
    override_shape_name = defn.shape_name

    if defn.spacing_override is not None and override_shape_name:
        shape = registry.shapes.get(override_shape_name)
        if shape:
            # Build a replacement shape with overridden spacing
            from brush_models_mr import BrushShapeAsset
            shape = BrushShapeAsset(
                name=shape.name,
                source_format=shape.source_format,
                shape_kind=shape.shape_kind,
                radius=shape.radius, aspect=shape.aspect,
                hardness=shape.hardness, shape_type=shape.shape_type,
                spikes=shape.spikes, angle=shape.angle,
                width=shape.width, height=shape.height,
                depth=shape.depth, bitmap_path=shape.bitmap_path,
                spacing_pct=defn.spacing_override,
            )
            # Temporarily insert into registry for recipe build
            registry.shapes[override_shape_name + "__override__"] = shape
            override_shape_name = override_shape_name + "__override__"

    if defn.uses_bundle():
        recipe = registry.build_recipe_from_bundle(
            defn.bundle_name,
            dynamics_name=defn.dynamics_name,
            palette_name=defn.palette_name,
        )
    else:
        recipe = registry.build_recipe_from_parts(
            override_shape_name or defn.shape_name,
            dynamics_name=defn.dynamics_name,
            palette_name=defn.palette_name,
        )

    # Clean up temporary override key
    if defn.spacing_override is not None and override_shape_name and "__override__" in override_shape_name:
        registry.shapes.pop(override_shape_name, None)

    return recipe


def build_all(registry: "AssetRegistry") -> dict[str, "BrushRecipe"]:
    """
    Attempt to build every named recipe. Returns only those that succeed.
    Missing assets are silently skipped.
    """
    results = {}
    for name in ALL_RECIPES:
        recipe = build(registry, name)
        if recipe is not None:
            results[name] = recipe
    return results


def describe(name: str) -> str:
    """Return the description string for a named recipe, or 'unknown'."""
    defn = ALL_RECIPES.get(name)
    return defn.description if defn else f"Unknown recipe: {name!r}"


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")
    from trixel_brush_adapter import AssetRegistry
    from pathlib import Path

    registry = AssetRegistry()
    registry.load_from_directory(Path("/usr/share/gimp/2.0/brushes"))
    registry.load_from_directory(Path("/usr/share/gimp/2.0/dynamics"))
    registry.load_from_directory(Path("/usr/share/gimp/2.0/palettes"))

    print("=== Trixel Named Recipes ===\n")
    recipes = build_all(registry)

    for name, defn in ALL_RECIPES.items():
        recipe = recipes.get(name)
        status = "✓" if recipe else "✗ MISSING ASSETS"
        dyn_ch = sorted(recipe.dynamics.active_channels) if recipe and recipe.dynamics else []
        pal    = recipe.palette.name if recipe and recipe.palette else "none"
        print(f"  [{status}] {defn.label}")
        print(f"           {defn.description}")
        if recipe:
            print(f"           id={recipe.recipe_id}")
            print(f"           dynamics={dyn_ch}  palette={pal}  blend={defn.blend_mode}")
        print()

    built = len(recipes)
    total = len(ALL_RECIPES)
    print(f"Built {built}/{total} recipes successfully.")
    if built < total:
        missing = [n for n in ALL_RECIPES if n not in recipes]
        print(f"Missing assets for: {missing}")
