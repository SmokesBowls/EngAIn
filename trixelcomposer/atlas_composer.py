"""
atlas_composer.py — Generate semantic replacement atlases for the Godot trixelassets system.

Architecture:
  atlas_meta.json  (in trixelassets)  =  UV topology contract  — tile_order, columns, tile_w/h
  trixelcomposer recipes              =  semantic surface layer — shimmer, foam, glow, etc.

For each role in tile_order, the composer:
  1. compiles a recipe for that terrain type
  2. applies a role-specific transform (edge_n → flip_y, edge_w → rotate_90, etc.)
  3. renders a 16×16 tile via RecipeRenderer (no session, no temp files)
  4. pastes it at the correct atlas position

The result is a drop-in replacement atlas.png with the same UV layout as the original.
SemanticRenderer reads the same atlas_meta.json and addresses UV regions identically;
only the pixel content changes.

Usage:
    from atlas_composer import compose_atlas
    path = compose_atlas("shoreline", environment="coastal")
    # → .zw/atlases/trixel_atlas_shoreline_<hash>.png
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_HERE = Path(__file__).parent.resolve()
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from PIL import Image as PILImage

from scene_server import compile_recipe
from terminal_trixel import RecipeRenderer, TerminalCanvas

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

TRIXEL_ASSETS_ROOT = Path(os.environ.get(
    "TRIXEL_ASSETS_ROOT",
    str(_HERE.parent / "godotnew" / "semantic" / "trixel" / "trixelassets"),
))

ATLAS_OUT_DIR = _HERE / ".zw" / "atlases"

# Role-specific transform overrides.
# The atlas topology layer decides shape; the transform makes surface effects
# face the correct direction for each edge/corner role.
#
# Convention: effects (foam, shimmer, h_band) are authored "pointing south"
# (toward +Y in UV space).  Transforms rotate/flip them to match each role's
# exposed direction.
_ROLE_TRANSFORMS: Dict[str, Dict[str, Any]] = {
    "center":          {},
    "single":          {},

    # Edge roles — exposed edge faces that direction
    "edge_n":          {"flip_y": True},     # effects point north
    "edge_s":          {},                   # effects point south (default)
    "edge_e":          {"rotate": 270},
    "edge_w":          {"rotate": 90},

    # Outer corners — the exposed corner is in that direction
    "corner_ne":       {"rotate": 270},
    "corner_nw":       {"flip_y": True},
    "corner_se":       {},
    "corner_sw":       {"rotate": 90},

    # Inner corners (concave) — mirror of outer
    "inner_ne":        {"rotate": 270},
    "inner_nw":        {"flip_y": True},
    "inner_se":        {},
    "inner_sw":        {"rotate": 90},

    # Path topology — directional orientation
    "path_straight_h": {},
    "path_straight_v": {"rotate": 90},
    "path_turn_ne":    {},
    "path_turn_nw":    {"flip_x": True},
    "path_turn_se":    {"flip_y": True},
    "path_turn_sw":    {"rotate": 180},
    "path_end_n":      {"flip_y": True},
    "path_end_s":      {},
    "path_end_e":      {"rotate": 270},
    "path_end_w":      {"rotate": 90},
    "path_cross":      {},
    "path_t_n":        {"flip_y": True},
    "path_t_s":        {},
    "path_t_e":        {"rotate": 270},
    "path_t_w":        {"rotate": 90},
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compose_atlas(
    terrain:     str,
    environment: str = "unknown",
    seed:        int = 42,
) -> Path:
    """Generate a semantic replacement atlas PNG for the given terrain type.

    The output has the same UV layout as the original atlas_meta.json so it
    can be used as a drop-in replacement by SemanticRenderer.

    Returns: absolute path to the generated atlas PNG.
    """
    meta = _read_atlas_meta(terrain)
    tile_order: List[str] = meta["tile_order"]
    columns:    int       = int(meta.get("columns", 4))
    tile_w:     int       = int(meta.get("tile_width", 16))
    tile_h:     int       = int(meta.get("tile_height", 16))

    rows      = (len(tile_order) + columns - 1) // columns
    atlas_img = PILImage.new("RGB", (columns * tile_w, rows * tile_h), (0, 0, 0))

    print(f"[atlas_composer] Composing {terrain} atlas: "
          f"{len(tile_order)} roles · {columns}×{rows} grid · {tile_w}×{tile_h}px/tile")

    for i, role in enumerate(tile_order):
        col = i % columns
        row = i // columns
        tile_img = _render_role(terrain, role, environment, seed, i)
        if tile_img.size != (tile_w, tile_h):
            tile_img = tile_img.resize((tile_w, tile_h), PILImage.NEAREST)
        atlas_img.paste(tile_img, (col * tile_w, row * tile_h))
        print(f"  [{i + 1}/{len(tile_order)}] {role}")

    ATLAS_OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = ATLAS_OUT_DIR / f"trixel_atlas_{terrain}_{seed}.png"
    atlas_img.save(str(out_path))
    print(f"[atlas_composer] Atlas saved: {out_path}")
    return out_path


def read_atlas_meta(terrain: str) -> Dict[str, Any]:
    """Public wrapper — returns the atlas_meta.json dict for the given terrain."""
    return _read_atlas_meta(terrain)


def list_terrain_types() -> List[str]:
    """Return terrain types that have an atlas_meta.json in TRIXEL_ASSETS_ROOT."""
    if not TRIXEL_ASSETS_ROOT.exists():
        return []
    return [
        d.name
        for d in sorted(TRIXEL_ASSETS_ROOT.iterdir())
        if d.is_dir() and (d / "atlas_meta.json").exists()
    ]


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------

def _read_atlas_meta(terrain: str) -> Dict[str, Any]:
    path = TRIXEL_ASSETS_ROOT / terrain / "atlas_meta.json"
    if not path.exists():
        raise FileNotFoundError(
            f"No atlas_meta for terrain '{terrain}' at: {path}\n"
            f"TRIXEL_ASSETS_ROOT = {TRIXEL_ASSETS_ROOT}"
        )
    return json.loads(path.read_text())


def _render_role(
    terrain:     str,
    role:        str,
    environment: str,
    base_seed:   int,
    role_index:  int,
) -> PILImage.Image:
    """Compile and render a single role tile using the trixelcomposer pipeline."""

    scene_doc = {
        "scene_id":     f"{terrain}_atlas_{role}",
        "terrain":      terrain,
        "environment":  environment,
        "entity_count": 0,
        "entities":     [],
    }

    try:
        recipe = compile_recipe(scene_doc)
    except Exception as exc:
        print(f"  [WARN] compile_recipe failed for {terrain}:{role} — {exc}. Using empty tile.")
        return PILImage.new("RGB", (16, 16), (80, 80, 80))

    # Per-role seed variation — keeps adjacent tiles visually distinct
    role_seed = (base_seed + role_index * 7919) & 0x7FFFFFFF
    for pass_ in recipe.get("passes", []):
        if pass_.get("seed") is not None:
            pass_["seed"] = role_seed

    # Role-specific transform — directs surface effects toward the exposed edge
    transform = _ROLE_TRANSFORMS.get(role, {})
    if transform:
        recipe["transform"] = transform

    canvas   = TerminalCanvas(
        recipe.get("canvas", {}).get("width",  16),
        recipe.get("canvas", {}).get("height", 16),
    )
    renderer = RecipeRenderer(canvas)
    renderer.execute(recipe)
    canvas.apply_transform(recipe.get("transform", {}))

    return _canvas_to_pil(canvas)


def _canvas_to_pil(canvas: TerminalCanvas) -> PILImage.Image:
    img = PILImage.new("RGB", (canvas.width, canvas.height))
    for y in range(canvas.height):
        for x in range(canvas.width):
            r, g, b = canvas.canvas[y][x]
            img.putpixel((x, y), (r, g, b))
    return img


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Compose a semantic replacement atlas for a terrain type",
        epilog=(
            "examples:\n"
            "  python3 atlas_composer.py --terrain shoreline\n"
            "  python3 atlas_composer.py --terrain sand --env desert --seed 77\n"
            "  python3 atlas_composer.py --list"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--terrain", help="Terrain type (shoreline, sand, grass, …)")
    parser.add_argument("--env",     default="unknown", help="Environment hint")
    parser.add_argument("--seed",    type=int, default=42, help="Base RNG seed")
    parser.add_argument("--list",    action="store_true", help="List available terrain types")
    args = parser.parse_args()

    if args.list:
        types = list_terrain_types()
        if types:
            for t in types:
                print(t)
        else:
            print(f"(no atlas_meta.json found under {TRIXEL_ASSETS_ROOT})")
        sys.exit(0)

    if not args.terrain:
        parser.error("--terrain is required (or use --list)")

    out = compose_atlas(args.terrain, environment=args.env, seed=args.seed)
    print(json.dumps({"terrain": args.terrain, "atlas": str(out)}))
