#!/usr/bin/env python3
"""
trixel_tileset_generator.py — Visual tile module generator for EngAIn.

Location: engainos/tools/trixel/trixel_tileset_generator.py

Responsibility:
  For a given SkinBinding family (e.g., "beach_primordial_v1"),
  generate a complete set of 16×16 pixel tiles:
    - center, edges (N/S/E/W), corners (NE/NW/SE/SW),
    - inner corners, path variants, single/isolated.
  Output: PNG files + a manifest JSON for Godot TileSet consumption.

It does NOT:
  - change world mechanics or state
  - call the adapter or kernel with write operations
  - depend on Ollama or Empire

It ONLY:
  - reads terrain type + skin binding info
  - generates deterministic procedural pixel art
  - writes PNGs and a manifest to disk

Architecture:
  SkinBinding (from core) → TerrainPalette → TileRenderer → PNG + manifest

Output structure:
  assets/trixels/{skin_family}/
    center.png
    edge_n.png
    edge_s.png
    ...
    manifest.json
"""

from __future__ import annotations

import json
import hashlib
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    from PIL import Image
except ImportError:
    Image = None  # type: ignore

# Import world contract types
try:
    from core.trixel_world_mr import (
        TerrainType, AutotileRole, SkinBinding,
        resolve_autotile_role, get_neighbors, make_cell_id,
    )
except ImportError:
    try:
        from trixel_world.trixel_world_mr import (
            TerrainType, AutotileRole, SkinBinding,
            resolve_autotile_role, get_neighbors, make_cell_id,
        )
    except ImportError:
        # Standalone fallback — define minimal types inline
        pass


# ============================================================
# TERRAIN PALETTES — Visual recipes per terrain type
# ============================================================

@dataclass(frozen=True)
class TerrainPalette:
    """Color palette and pattern rules for a terrain type.

    Each terrain has:
      base_color:   primary fill color (RGB)
      alt_colors:   variation colors for noise/texture
      edge_blend:   color used when this terrain borders another
      pattern:      how to fill the tile ("solid", "noise", "stripe", "dot")
      noise_weight: 0.0 = pure base, 1.0 = heavy variation
    """
    base_color: Tuple[int, int, int]
    alt_colors: Tuple[Tuple[int, int, int], ...] = ()
    edge_blend: Tuple[int, int, int] = (0, 0, 0)
    pattern: str = "noise"
    noise_weight: float = 0.3


# Deterministic palettes — each terrain gets a distinct visual identity
TERRAIN_PALETTES: Dict[str, TerrainPalette] = {
    "sand": TerrainPalette(
        base_color=(222, 196, 148),
        alt_colors=((210, 180, 130), (234, 210, 165), (198, 175, 120)),
        edge_blend=(190, 165, 110),
        pattern="noise",
        noise_weight=0.25,
    ),
    "shoreline": TerrainPalette(
        base_color=(180, 195, 165),
        alt_colors=((170, 190, 155), (190, 200, 175), (160, 180, 145)),
        edge_blend=(150, 170, 140),
        pattern="noise",
        noise_weight=0.35,
    ),
    "shallow_water": TerrainPalette(
        base_color=(100, 160, 200),
        alt_colors=((90, 150, 190), (110, 170, 210), (85, 145, 185)),
        edge_blend=(80, 140, 180),
        pattern="noise",
        noise_weight=0.3,
    ),
    "deep_water": TerrainPalette(
        base_color=(40, 80, 140),
        alt_colors=((35, 70, 130), (50, 90, 150), (30, 65, 120)),
        edge_blend=(25, 60, 110),
        pattern="noise",
        noise_weight=0.2,
    ),
    "forest_edge": TerrainPalette(
        base_color=(45, 90, 40),
        alt_colors=((35, 80, 30), (55, 100, 50), (40, 75, 35), (60, 110, 55)),
        edge_blend=(30, 65, 25),
        pattern="noise",
        noise_weight=0.45,
    ),
    "forest_dense": TerrainPalette(
        base_color=(25, 60, 20),
        alt_colors=((20, 50, 15), (30, 70, 25), (18, 45, 12)),
        edge_blend=(15, 40, 10),
        pattern="noise",
        noise_weight=0.35,
    ),
    "trail": TerrainPalette(
        base_color=(160, 130, 90),
        alt_colors=((150, 120, 80), (170, 140, 100), (145, 115, 75)),
        edge_blend=(130, 105, 70),
        pattern="noise",
        noise_weight=0.2,
    ),
    "pier": TerrainPalette(
        base_color=(120, 85, 50),
        alt_colors=((110, 75, 40), (130, 95, 60), (105, 70, 35)),
        edge_blend=(90, 60, 30),
        pattern="stripe",
        noise_weight=0.15,
    ),
    "rock": TerrainPalette(
        base_color=(130, 130, 130),
        alt_colors=((120, 120, 120), (140, 140, 140), (110, 110, 115)),
        edge_blend=(100, 100, 100),
        pattern="noise",
        noise_weight=0.3,
    ),
    "cliff": TerrainPalette(
        base_color=(100, 95, 85),
        alt_colors=((90, 85, 75), (110, 105, 95), (85, 80, 70)),
        edge_blend=(75, 70, 60),
        pattern="noise",
        noise_weight=0.35,
    ),
    "subterranean_floor": TerrainPalette(
        base_color=(80, 70, 60),
        alt_colors=((70, 60, 50), (90, 80, 70), (65, 55, 45)),
        edge_blend=(55, 45, 35),
        pattern="noise",
        noise_weight=0.3,
    ),
    "subterranean_wall": TerrainPalette(
        base_color=(50, 45, 40),
        alt_colors=((40, 35, 30), (60, 55, 50), (35, 30, 25)),
        edge_blend=(30, 25, 20),
        pattern="noise",
        noise_weight=0.25,
    ),
    "grass": TerrainPalette(
        base_color=(90, 160, 60),
        alt_colors=((80, 150, 50), (100, 170, 70), (75, 140, 45), (110, 175, 80)),
        edge_blend=(65, 130, 40),
        pattern="noise",
        noise_weight=0.35,
    ),
    "dirt": TerrainPalette(
        base_color=(140, 110, 70),
        alt_colors=((130, 100, 60), (150, 120, 80), (125, 95, 55)),
        edge_blend=(110, 85, 50),
        pattern="noise",
        noise_weight=0.25,
    ),
    "stone_floor": TerrainPalette(
        base_color=(155, 155, 150),
        alt_colors=((145, 145, 140), (165, 165, 160), (140, 140, 135)),
        edge_blend=(130, 130, 125),
        pattern="noise",
        noise_weight=0.15,
    ),
    "construction_site": TerrainPalette(
        base_color=(180, 160, 120),
        alt_colors=((170, 150, 110), (190, 170, 130), (165, 145, 105)),
        edge_blend=(150, 135, 95),
        pattern="noise",
        noise_weight=0.3,
    ),
    "void": TerrainPalette(
        base_color=(20, 20, 25),
        alt_colors=((15, 15, 20), (25, 25, 30)),
        edge_blend=(10, 10, 15),
        pattern="solid",
        noise_weight=0.0,
    ),
}


def get_palette(terrain_type: str) -> TerrainPalette:
    """Look up palette for a terrain type, with fallback."""
    return TERRAIN_PALETTES.get(terrain_type, TERRAIN_PALETTES["void"])


# ============================================================
# DETERMINISTIC NOISE — Seeded, pure, no random module
# ============================================================

def _hash_xy(x: int, y: int, seed: int) -> int:
    """Deterministic hash for a pixel coordinate + seed."""
    h = hashlib.md5(f"{x},{y},{seed}".encode()).digest()
    return h[0]  # 0-255


def _noise_color(
    x: int, y: int, seed: int, palette: TerrainPalette
) -> Tuple[int, int, int]:
    """Pick a pixel color using deterministic noise."""
    if palette.pattern == "solid" or not palette.alt_colors:
        return palette.base_color

    h = _hash_xy(x, y, seed)
    weight = palette.noise_weight

    # Decide: base color or alt color?
    if h > int(255 * weight):
        return palette.base_color

    # Pick from alt_colors deterministically
    idx = h % len(palette.alt_colors)
    return palette.alt_colors[idx]


def _stripe_color(
    x: int, y: int, seed: int, palette: TerrainPalette
) -> Tuple[int, int, int]:
    """Horizontal stripe pattern (for pier planks, etc.)."""
    stripe_width = 3 + (seed % 3)  # 3-5 pixel stripes
    band = y % (stripe_width * 2)
    if band < stripe_width:
        return palette.base_color
    else:
        if palette.alt_colors:
            return palette.alt_colors[0]
        return palette.edge_blend


def _get_pixel_color(
    x: int, y: int, seed: int, palette: TerrainPalette
) -> Tuple[int, int, int]:
    """Master pixel color resolver."""
    if palette.pattern == "stripe":
        return _stripe_color(x, y, seed, palette)
    elif palette.pattern == "dot":
        # Dot pattern: base with occasional alt spots
        h = _hash_xy(x, y, seed)
        if h < 20 and palette.alt_colors:
            return palette.alt_colors[h % len(palette.alt_colors)]
        return palette.base_color
    else:
        # Default: noise
        return _noise_color(x, y, seed, palette)


# ============================================================
# EDGE MASKS — Which pixels get blended for autotile edges
# ============================================================

def _edge_mask(
    tile_size: int, role: str
) -> List[Tuple[int, int, float]]:
    """Return list of (x, y, blend_strength) for edge/corner blending.

    blend_strength: 0.0 = no blend (pure terrain), 1.0 = full edge_blend color.
    The mask creates a gradient fade at the tile's open border.
    """
    masks: List[Tuple[int, int, float]] = []
    ts = tile_size
    fade_depth = max(2, ts // 4)  # pixels of fade

    if role in ("edge_n", "corner_nw", "corner_ne"):
        for y in range(fade_depth):
            strength = 1.0 - (y / fade_depth)
            for x in range(ts):
                masks.append((x, y, strength))

    if role in ("edge_s", "corner_sw", "corner_se"):
        for y in range(ts - fade_depth, ts):
            strength = (y - (ts - fade_depth)) / fade_depth
            for x in range(ts):
                masks.append((x, y, strength))

    if role in ("edge_w", "corner_nw", "corner_sw"):
        for x in range(fade_depth):
            strength = 1.0 - (x / fade_depth)
            for y in range(ts):
                masks.append((x, y, strength * 0.7))  # softer horizontal

    if role in ("edge_e", "corner_ne", "corner_se"):
        for x in range(ts - fade_depth, ts):
            strength = (x - (ts - fade_depth)) / fade_depth
            for y in range(ts):
                masks.append((x, y, strength * 0.7))

    # Inner corners: small triangular blend in the corner
    if role == "inner_ne":
        for x in range(ts - fade_depth, ts):
            for y in range(fade_depth):
                s = min((x - (ts - fade_depth)) / fade_depth, 1.0 - (y / fade_depth))
                masks.append((x, y, s * 0.6))

    if role == "inner_nw":
        for x in range(fade_depth):
            for y in range(fade_depth):
                s = min(1.0 - (x / fade_depth), 1.0 - (y / fade_depth))
                masks.append((x, y, s * 0.6))

    if role == "inner_se":
        for x in range(ts - fade_depth, ts):
            for y in range(ts - fade_depth, ts):
                s = min((x - (ts - fade_depth)) / fade_depth, (y - (ts - fade_depth)) / fade_depth)
                masks.append((x, y, s * 0.6))

    if role == "inner_sw":
        for x in range(fade_depth):
            for y in range(ts - fade_depth, ts):
                s = min(1.0 - (x / fade_depth), (y - (ts - fade_depth)) / fade_depth)
                masks.append((x, y, s * 0.6))

    # Path ends: fade at the open end
    if role == "path_end_n":
        for y in range(fade_depth):
            strength = 1.0 - (y / fade_depth)
            for x in range(ts):
                masks.append((x, y, strength * 0.5))

    if role == "path_end_s":
        for y in range(ts - fade_depth, ts):
            strength = (y - (ts - fade_depth)) / fade_depth
            for x in range(ts):
                masks.append((x, y, strength * 0.5))

    if role == "path_end_e":
        for x in range(ts - fade_depth, ts):
            strength = (x - (ts - fade_depth)) / fade_depth
            for y in range(ts):
                masks.append((x, y, strength * 0.5))

    if role == "path_end_w":
        for x in range(fade_depth):
            strength = 1.0 - (x / fade_depth)
            for y in range(ts):
                masks.append((x, y, strength * 0.5))

    return masks


def _blend_color(
    base: Tuple[int, int, int],
    blend: Tuple[int, int, int],
    strength: float,
) -> Tuple[int, int, int]:
    """Linearly blend two RGB colors."""
    s = max(0.0, min(1.0, strength))
    return (
        int(base[0] * (1 - s) + blend[0] * s),
        int(base[1] * (1 - s) + blend[1] * s),
        int(base[2] * (1 - s) + blend[2] * s),
    )


# ============================================================
# TILE RENDERER — Produces a single 16×16 tile
# ============================================================

def render_tile(
    terrain_type: str,
    autotile_role: str,
    tile_size: int = 16,
    variant_seed: int = 0,
) -> List[List[Tuple[int, int, int]]]:
    """Render a single tile as a 2D pixel array.

    Args:
        terrain_type: which terrain palette to use
        autotile_role: edge/corner/center variant
        tile_size: pixels per side (default 16)
        variant_seed: deterministic variation

    Returns:
        pixels[y][x] = (r, g, b) — row-major pixel grid
    """
    palette = get_palette(terrain_type)

    # Fill with base pattern
    pixels = []
    for y in range(tile_size):
        row = []
        for x in range(tile_size):
            color = _get_pixel_color(x, y, variant_seed, palette)
            row.append(color)
        pixels.append(row)

    # Apply edge/corner blending mask
    if autotile_role != "center" and autotile_role != "single":
        mask = _edge_mask(tile_size, autotile_role)
        for mx, my, strength in mask:
            if 0 <= mx < tile_size and 0 <= my < tile_size:
                pixels[my][mx] = _blend_color(
                    pixels[my][mx], palette.edge_blend, strength
                )

    return pixels


def render_tile_to_image(
    terrain_type: str,
    autotile_role: str,
    tile_size: int = 16,
    variant_seed: int = 0,
    scale: int = 1,
) -> Optional["Image.Image"]:
    """Render a tile directly to a PIL Image.

    Args:
        scale: upscale factor (1 = raw 16×16, 4 = 64×64 preview)

    Returns:
        PIL.Image or None if Pillow unavailable.
    """
    if Image is None:
        return None

    pixels = render_tile(terrain_type, autotile_role, tile_size, variant_seed)
    img = Image.new("RGB", (tile_size, tile_size))
    flat = []
    for row in pixels:
        for px in row:
            flat.append(px)
    img.putdata(flat)

    if scale > 1:
        img = img.resize(
            (tile_size * scale, tile_size * scale),
            resample=Image.NEAREST,
        )

    return img


# ============================================================
# FULL AUTOTILE ROLES — What a complete tileset needs
# ============================================================

# Core roles every terrain tileset should have
CORE_ROLES = [
    "center",
    "edge_n", "edge_s", "edge_e", "edge_w",
    "corner_ne", "corner_nw", "corner_se", "corner_sw",
    "inner_ne", "inner_nw", "inner_se", "inner_sw",
    "single",
]

# Additional path roles (for trail, pier, etc.)
PATH_ROLES = [
    "path_straight_h", "path_straight_v",
    "path_turn_ne", "path_turn_nw", "path_turn_se", "path_turn_sw",
    "path_end_n", "path_end_s", "path_end_e", "path_end_w",
    "path_cross",
    "path_t_n", "path_t_s", "path_t_e", "path_t_w",
]

# Terrain types that use path roles
PATH_TERRAINS = {"trail", "pier", "shoreline"}


def get_roles_for_terrain(terrain_type: str) -> List[str]:
    """Determine which autotile roles a terrain needs."""
    roles = list(CORE_ROLES)
    if terrain_type in PATH_TERRAINS:
        roles.extend(PATH_ROLES)
    return roles


# ============================================================
# TILESET GENERATOR — Orchestrates full tileset production
# ============================================================

@dataclass
class TilesetManifest:
    """Describes a generated tileset for Godot consumption."""
    skin_id: str
    terrain_type: str
    module_family: str
    tile_size: int
    style_tags: List[str]
    tiles: Dict[str, str]  # autotile_role → relative PNG path
    variant_count: int = 1
    output_dir: str = ""

    def to_dict(self) -> dict:
        return {
            "skin_id": self.skin_id,
            "terrain_type": self.terrain_type,
            "module_family": self.module_family,
            "tile_size": self.tile_size,
            "style_tags": self.style_tags,
            "tiles": self.tiles,
            "variant_count": self.variant_count,
            "output_dir": self.output_dir,
        }


def generate_tileset(
    skin_id: str,
    terrain_type: str,
    module_family: str,
    output_dir: str,
    tile_size: int = 16,
    variant_count: int = 1,
    style_tags: Optional[List[str]] = None,
    export_scale: int = 1,
) -> TilesetManifest:
    """Generate a complete tileset for one skin binding family.

    Args:
        skin_id: unique skin identifier
        terrain_type: which terrain this visualizes
        module_family: grouping name (e.g., "sand_base")
        output_dir: where to write PNGs + manifest
        tile_size: pixels per tile side (default 16)
        variant_count: how many visual variants per role
        style_tags: metadata tags
        export_scale: upscale factor for PNGs (1 = raw, 4 = preview)

    Returns:
        TilesetManifest describing all generated tiles.
    """
    if Image is None:
        raise RuntimeError(
            "Pillow is required for tileset generation. "
            "Install with: pip install Pillow"
        )

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    roles = get_roles_for_terrain(terrain_type)
    tiles: Dict[str, str] = {}

    for role in roles:
        for variant in range(variant_count):
            # Deterministic seed from skin + role + variant
            seed_str = f"{skin_id}:{role}:{variant}"
            seed = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)

            img = render_tile_to_image(
                terrain_type=terrain_type,
                autotile_role=role,
                tile_size=tile_size,
                variant_seed=seed,
                scale=export_scale,
            )

            if variant_count > 1:
                filename = f"{role}_v{variant}.png"
            else:
                filename = f"{role}.png"

            filepath = out_path / filename
            img.save(filepath)

            # First variant is the canonical entry
            if variant == 0:
                tiles[role] = filename

    # Write manifest
    manifest = TilesetManifest(
        skin_id=skin_id,
        terrain_type=terrain_type,
        module_family=module_family,
        tile_size=tile_size,
        style_tags=style_tags or [],
        tiles=tiles,
        variant_count=variant_count,
        output_dir=str(out_path),
    )

    manifest_path = out_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest.to_dict(), indent=2))

    return manifest


def generate_world_tilesets(
    skin_table: Dict[str, dict],
    base_output_dir: str,
    tile_size: int = 16,
    variant_count: int = 1,
    export_scale: int = 1,
) -> List[TilesetManifest]:
    """Generate tilesets for all skin bindings in a world snapshot.

    Args:
        skin_table: the skin_table dict from a world snapshot
        base_output_dir: root directory for tileset output
        tile_size: pixels per tile
        variant_count: variants per role
        export_scale: upscale factor

    Returns:
        List of TilesetManifest, one per unique module_family.
    """
    # Group skin bindings by module_family to avoid generating duplicates
    families_seen: Dict[str, dict] = {}
    for sid, skin_data in skin_table.items():
        family = skin_data.get("module_family", sid)
        if family not in families_seen:
            families_seen[family] = skin_data

    manifests = []
    for family, skin_data in families_seen.items():
        output_dir = os.path.join(base_output_dir, family)
        manifest = generate_tileset(
            skin_id=skin_data.get("skin_id", family),
            terrain_type=skin_data.get("terrain_type", "void"),
            module_family=family,
            output_dir=output_dir,
            tile_size=tile_size,
            variant_count=variant_count,
            style_tags=skin_data.get("style_tags", []),
            export_scale=export_scale,
        )
        manifests.append(manifest)

    return manifests


def generate_atlas(
    manifest: TilesetManifest,
    columns: int = 4,
) -> Optional[str]:
    """Combine individual tiles into a single atlas PNG.

    Useful for Godot TileSet import — one image, many tiles.

    Args:
        manifest: a generated tileset manifest
        columns: tiles per row in the atlas

    Returns:
        Path to atlas PNG, or None if Pillow unavailable.
    """
    if Image is None:
        return None

    out_path = Path(manifest.output_dir)
    tile_files = list(manifest.tiles.values())

    if not tile_files:
        return None

    # Load first tile to get dimensions
    first_img = Image.open(out_path / tile_files[0])
    tw, th = first_img.size

    rows = (len(tile_files) + columns - 1) // columns
    atlas = Image.new("RGB", (tw * columns, th * rows), (0, 0, 0))

    for i, filename in enumerate(tile_files):
        tile_img = Image.open(out_path / filename)
        col = i % columns
        row = i // columns
        atlas.paste(tile_img, (col * tw, row * th))

    atlas_path = out_path / "atlas.png"
    atlas.save(atlas_path)

    # Write atlas metadata
    atlas_meta = {
        "atlas_path": "atlas.png",
        "tile_width": tw,
        "tile_height": th,
        "columns": columns,
        "rows": rows,
        "tile_order": list(manifest.tiles.keys()),
    }
    (out_path / "atlas_meta.json").write_text(json.dumps(atlas_meta, indent=2))

    return str(atlas_path)


# ============================================================
# SELF-TEST / CLI
# ============================================================

if __name__ == "__main__":
    import sys
    import tempfile

    print("=" * 60)
    print("TRIXEL TILESET GENERATOR — Self Test")
    print("=" * 60)

    if Image is None:
        print("ERROR: Pillow not installed. Run: pip install Pillow")
        sys.exit(1)

    # Use temp dir for test output
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"\nOutput: {tmpdir}")

        # Generate tilesets for a few terrain types
        test_terrains = [
            ("sand", "beach_primordial_v1", "sand_base"),
            ("deep_water", "ocean_primordial_v1", "water_deep_base"),
            ("forest_edge", "forest_primordial_v1", "forest_edge_base"),
            ("pier", "pier_primordial_v1", "pier_base"),
            ("grass", "grass_primordial_v1", "grass_base"),
            ("trail", "trail_primordial_v1", "trail_base"),
        ]

        all_manifests = []

        for terrain, skin_id, family in test_terrains:
            out = os.path.join(tmpdir, family)
            manifest = generate_tileset(
                skin_id=skin_id,
                terrain_type=terrain,
                module_family=family,
                output_dir=out,
                tile_size=16,
                variant_count=1,
                style_tags=["pixel", "primordial"],
                export_scale=1,
            )
            all_manifests.append(manifest)

            tile_count = len(manifest.tiles)
            png_files = list(Path(out).glob("*.png"))
            print(f"\n  {terrain:25s} → {tile_count:2d} roles, {len(png_files)} PNGs")
            print(f"    skin_id:  {manifest.skin_id}")
            print(f"    family:   {manifest.module_family}")
            print(f"    output:   {out}")

        # Generate atlases
        print("\n--- Atlases ---")
        for manifest in all_manifests:
            atlas_path = generate_atlas(manifest)
            if atlas_path:
                atlas_img = Image.open(atlas_path)
                print(f"  {manifest.module_family:25s} → atlas {atlas_img.size[0]}×{atlas_img.size[1]}")

        # Verify tile rendering determinism
        print("\n--- Determinism Check ---")
        pixels_a = render_tile("sand", "center", 16, 42)
        pixels_b = render_tile("sand", "center", 16, 42)
        match = all(
            pixels_a[y][x] == pixels_b[y][x]
            for y in range(16)
            for x in range(16)
        )
        print(f"  Same seed → same pixels: {match}")

        pixels_c = render_tile("sand", "center", 16, 99)
        differ = any(
            pixels_a[y][x] != pixels_c[y][x]
            for y in range(16)
            for x in range(16)
        )
        print(f"  Different seed → different pixels: {differ}")

        # Verify edge blending
        print("\n--- Edge Blending Check ---")
        center_px = render_tile("sand", "center", 16, 0)
        edge_n_px = render_tile("sand", "edge_n", 16, 0)
        # Top row of edge_n should differ from center (blended)
        top_differs = any(
            center_px[0][x] != edge_n_px[0][x]
            for x in range(16)
        )
        print(f"  edge_n top row differs from center: {top_differs}")

        # World-level generation test
        print("\n--- World Tileset Generation ---")
        skin_table = {
            "beach_v1": {
                "skin_id": "beach_v1",
                "terrain_type": "sand",
                "module_family": "sand_base_world",
                "style_tags": ["pixel"],
            },
            "water_v1": {
                "skin_id": "water_v1",
                "terrain_type": "deep_water",
                "module_family": "water_base_world",
                "style_tags": ["pixel"],
            },
        }
        world_out = os.path.join(tmpdir, "world_tilesets")
        manifests = generate_world_tilesets(
            skin_table=skin_table,
            base_output_dir=world_out,
            variant_count=2,
        )
        print(f"  Generated {len(manifests)} tileset families")
        for m in manifests:
            pngs = list(Path(m.output_dir).glob("*.png"))
            print(f"    {m.module_family}: {len(m.tiles)} roles, {len(pngs)} PNGs (with variants)")

        print("\n" + "=" * 60)
        print("TILESET GENERATOR TEST COMPLETE")
        print("=" * 60)
