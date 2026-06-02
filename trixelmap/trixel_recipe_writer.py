"""
Tier 4 Output: Translates tile intent grid into Trixelcomposer-native contracts.
Does not render. Produces map intelligence for composition.
"""
import json
from typing import Dict, List

def write_recipe_and_atlas(terrain_field: Dict[str, Any], resolved_layout: Dict[str, Any]) -> Dict[str, Dict]:
    grid_size = terrain_field["grid_size"]
    
    # 1. Trixelcomposer Recipe: Region definitions, transition rules, landmark placements
    recipe = {
        "version": "1.0",
        "type": "trixelcomposer_recipe",
        "grid_size": grid_size,
        "regions": [],
        "transitions": [],
        "landmarks": []
    }
    
    for rid, r in resolved_layout["regions"].items():
        recipe["regions"].append({
            "id": rid,
            "bounds": r["bounds"],
            "primary_biome_id": _biome_name_to_id(r["terrain_class"]),
            "elevation_center": r.get("centroid", {}).get("x", 0),
            "moisture_profile": "low" if "arid" in r["terrain_class"] else "high"
        })
        for lm in r.get("landmarks", []):
            recipe["landmarks"].append({"region_id": rid, "id": lm, "placement": "center"})

    # Auto-generate transition rules between adjacent biomes
    recipe["transitions"] = [
        {"from_biome": 0, "to_biome": 1, "rule": "steep_slope_blend", "width": 4},
        {"from_biome": 1, "to_biome": 3, "rule": "gradual_fade", "width": 3},
        {"from_biome": 2, "to_biome": 3, "rule": "marsh_drainage_edge", "width": 2},
        {"from_biome": 4, "to_biome": 5, "rule": "coastal_shoreline", "width": 2}
    ]

    # 2. Atlas Plan: Layer definitions, palette assignments, sprite routing
    atlas = {
        "version": "1.0",
        "type": "trixelcomposer_atlas_plan",
        "layers": [
            {"id": "base_terrain", "source": "biome_id", "palette": "terrain_palette.png"},
            {"id": "elevation_shading", "source": "elevation", "mode": "multiply"},
            {"id": "moisture_overlay", "source": "moisture", "mode": "screen"},
            {"id": "landmarks", "source": "landmarks", "z_index": 10}
        ],
        "tile_size": {"x": 16, "y": 16},
        "export_format": "png_grid",
        "seed": 42
    }

    return {"recipe": recipe, "atlas_plan": atlas}

def _biome_name_to_id(name: str) -> int:
    mapping = {
        "frozen_volcanic_peak": 0, "alpine_spine": 1, "wetlands": 2,
        "arid_plains": 3, "coastal_settlement": 4, "default": 5
    }
    return mapping.get(name, 5)
