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
        gradient_name — asset name in registry.gradients (None = no gradient)
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
    gradient_name:     Optional[str]
    colour_mode:       str
    blend_mode:        str
    spacing_override:  Optional[float]
    description:       str
    imp_preset_name:   Optional[str] = None
    
    # Generic style knobs
    surface_strength: float = 1.0
    pixelization_strength: float = 0.0
    dither_amount: float = 0.0
    edge_breakup: float = 0.0
    atmosphere_intensity: float = 1.0

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
    palette_name="Topographic",
    gradient_name=None,
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
    palette_name="Topographic",
    gradient_name=None,
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
    palette_name="Topographic",
    gradient_name=None,
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
    palette_name="Topographic",
    gradient_name=None,
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
    palette_name="Topographic",
    gradient_name=None,
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
    palette_name="Topographic",
    gradient_name="Default",
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
    gradient_name=None,
    colour_mode="elevation",           # colour driven by stroke position
    blend_mode="normal",
    spacing_override=None,
    description=(
        "Soft parametric brush with Topographic palette in elevation mode. "
        "Demonstrates palette-as-material: colour encodes world height."
    ),
)


# ---------------------------------------------------------------------------
# Public registry of all named recipes
# ---------------------------------------------------------------------------

_BEACH_SKY = TrixelRecipeDef(
    name="beach_sky", label="Sky Band", shape_name="1. Pixel", bundle_name=None,
    dynamics_name=None, palette_name="Topographic", gradient_name=None,
    colour_mode="gradient", blend_mode="normal", spacing_override=0.1,
    description="Flat gradient sky fill."
)

_BEACH_SUN = TrixelRecipeDef(
    name="beach_sun", label="Horizon Light", shape_name="1. Pixel", bundle_name=None,
    dynamics_name=None, palette_name="Topographic", gradient_name=None,
    colour_mode="nearest", blend_mode="additive", spacing_override=0.1,
    description="Intense additive core light for atmosphere mapping.",
    atmosphere_intensity=2.0
)

_BEACH_WATER = TrixelRecipeDef(
    name="beach_water", label="Water Surface", shape_name="Hatch-Pen-01", bundle_name=None,
    dynamics_name="Pressure Opacity", palette_name="Topographic", gradient_name=None,
    colour_mode="elevation", blend_mode="normal", spacing_override=0.2,
    description="Layered waves and ripples.",
    surface_strength=1.5
)

_BEACH_FOAM = TrixelRecipeDef(
    name="beach_foam", label="Foam Edge", shape_name="1. Pixel", bundle_name=None,
    dynamics_name="Pressure Opacity", palette_name="Topographic", gradient_name=None,
    colour_mode="nearest", blend_mode="screen", spacing_override=5.0,
    imp_preset_name="Weave", description="Textured foamy weave along shoreline."
)

_BEACH_WET_SAND = TrixelRecipeDef(
    name="beach_wet_sand", label="Wet Sand", shape_name="1. Pixel", bundle_name=None,
    dynamics_name=None, palette_name="Topographic", gradient_name=None,
    colour_mode="gradient", blend_mode="normal", spacing_override=0.2,
    description="Smooth, slightly reflective firm packed sand."
)

_BEACH_DRY_SAND = TrixelRecipeDef(
    name="beach_dry_sand", label="Dry Sand", shape_name="1. Pixel", bundle_name=None,
    dynamics_name="Pencil Generic", palette_name="Topographic", gradient_name=None,
    colour_mode="index", blend_mode="normal", spacing_override=6.0,
    imp_preset_name="Canvas", description="Dry loose grainy sand with high breakup."
)

_BEACH_ROCK = TrixelRecipeDef(
    name="beach_rock", label="Rock", shape_name="Charcoal-01", bundle_name=None,
    dynamics_name="Pencil Generic", palette_name="Topographic", gradient_name=None,
    colour_mode="nearest", blend_mode="normal", spacing_override=4.0,
    imp_preset_name="Painted_Rock", description="Harsh geometric rocky outcropping."
)

_BEACH_DRIFTWOOD = TrixelRecipeDef(
    name="beach_driftwood", label="Driftwood", shape_name="Charcoal-01", bundle_name=None,
    dynamics_name="Pencil Generic", palette_name="Topographic", gradient_name=None,
    colour_mode="nearest", blend_mode="normal", spacing_override=4.0,
    imp_preset_name="Bark", description="Weathered wood and bleached driftwood grains."
)

_BEACH_GRASS = TrixelRecipeDef(
    name="beach_grass", label="Dune Fringe", shape_name="Charcoal-01", bundle_name=None,
    dynamics_name="Fade Tapering", palette_name="Topographic", gradient_name=None,
    colour_mode="nearest", blend_mode="normal", spacing_override=0.8,
    imp_preset_name="Stratum", description="Windswept grass/fringe over the dunes."
)

ALL_RECIPES: dict[str, TrixelRecipeDef] = {
    r.name: r for r in [
        _HARD_PIXEL,
        _HATCH_TEXTURE,
        _CHARCOAL_GRAIN,
        _BRISTLE_RAKE,
        _OIL_SMEAR,
        _ACRYLIC_VARIANT,
        _TERRAIN_STROKE,
        _BEACH_SKY,
        _BEACH_SUN,
        _BEACH_WATER,
        _BEACH_FOAM,
        _BEACH_WET_SAND,
        _BEACH_DRY_SAND,
        _BEACH_ROCK,
        _BEACH_DRIFTWOOD,
        _BEACH_GRASS,
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
            gradient_name=defn.gradient_name,
            imp_preset_name=defn.imp_preset_name,
        )
    else:
        recipe = registry.build_recipe_from_parts(
            override_shape_name or defn.shape_name,
            dynamics_name=defn.dynamics_name,
            palette_name=defn.palette_name,
            gradient_name=defn.gradient_name,
            imp_preset_name=defn.imp_preset_name,
        )

    # Clean up temporary override key
    if defn.spacing_override is not None and override_shape_name and "__override__" in override_shape_name:
        registry.shapes.pop(override_shape_name, None)

    if recipe is None:
        return None

    from dataclasses import replace
    recipe = replace(
        recipe,
        colour_mode=defn.colour_mode,
        blend_mode=defn.blend_mode,
        spacing_override=defn.spacing_override,
        surface_strength=defn.surface_strength,
        pixelization_strength=defn.pixelization_strength,
        dither_amount=defn.dither_amount,
        edge_breakup=defn.edge_breakup,
        atmosphere_intensity=defn.atmosphere_intensity,
    )
    
    recipe.validate()

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
    from pathlib import Path

    sys.path.insert(0, ".")
    from trixel_brush_adapter import AssetRegistry

    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data")

    print(f"Loading assets from: {root.resolve()}")
    registry = AssetRegistry()
    registry.load_from_directory(root)

    s = registry.summary()
    print("\nRegistry summary:")
    print(f"  shapes:          {s['shapes']}")
    print(f"  dynamics:        {s['dynamics']}")
    print(f"  presets:         {s['presets']}")
    print(f"  palettes:        {s['palettes']}")
    print(f"  gradients:       {s['gradients']}")
    print(f"  patterns:        {s['patterns']}")
    print(f"  variant_bundles: {s['variant_bundles']}")
    print(f"  errors:          {s['errors']}")
    print(f"  collisions:      {s['collisions']}")

    if s["errors"]:
        for e in registry.errors:
            print(f"    ! {e}")

    print("\n=== Trixel Named Recipes ===\n")
    recipes = build_all(registry)

    for name, defn in ALL_RECIPES.items():
        recipe = recipes.get(name)
        status = "✓" if recipe else "✗ MISSING ASSETS"

        dyn_ch = sorted(recipe.dynamics.active_channels) if recipe and recipe.dynamics else []
        pal = recipe.palette.name if recipe and recipe.palette else "none"
        ggr = recipe.gradient.name if recipe and recipe.gradient else "none"
        shape = recipe.shape.name if recipe and recipe.shape else "none"
        bundle = recipe.variant_bundle.name if recipe and recipe.variant_bundle else "none"

        print(f"  [{status}] {defn.label}")
        print(f"           {defn.description}")
        if recipe:
            print(f"           id={recipe.recipe_id}")
            print(
                f"           shape={shape}  bundle={bundle}  "
                f"dynamics={dyn_ch}  palette={pal}  gradient={ggr}  "
                f"blend={defn.blend_mode}"
            )
        print()

    built = len(recipes)
    total = len(ALL_RECIPES)
    print(f"Built {built}/{total} recipes successfully.")
    if built < total:
        missing = [n for n in ALL_RECIPES if n not in recipes]
        print(f"Missing assets for: {missing}")
