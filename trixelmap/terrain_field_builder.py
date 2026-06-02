"""
Tier 3 Terrain Field: Solved layout → tile intent grid with elevation/biome/moisture.
Pure functional, deterministic interpolation.
"""
import numpy as np
from typing import Dict, List

def build_terrain_field(resolved_layout: Dict[str, Any]) -> Dict[str, Any]:
    grid_size = resolved_layout["grid_size"]
    terrain = resolved_layout["regions"]
    
    # Initialize fields
    elevation = np.full((grid_size, grid_size), 0.5)
    moisture = np.full((grid_size, grid_size), 0.5)
    biome_id = np.full((grid_size, grid_size), -1, dtype=int)
    
    biome_map = {
        "frozen_volcanic_peak": 0, "alpine_spine": 1, "wetlands": 2,
        "arid_plains": 3, "coastal_settlement": 4, "default": 5
    }
    
    for rid, r in terrain.items():
        b = r["bounds"]
        x1, y1, x2, y2 = b["x_min"], b["y_min"], b["x_max"], b["y_max"]
        mask = np.zeros((grid_size, grid_size), dtype=bool)
        mask[y1:y2, x1:x2] = True
        
        # Terrain-specific field modifiers
        if r["terrain_class"] == "frozen_volcanic_peak":
            elevation[mask] = 0.9; moisture[mask] = 0.3; biome_id[mask] = biome_map["frozen_volcanic_peak"]
        elif r["terrain_class"] == "alpine_spine":
            elevation[mask] = 0.8; moisture[mask] = 0.4; biome_id[mask] = biome_map["alpine_spine"]
        elif r["terrain_class"] == "wetlands":
            elevation[mask] = 0.2; moisture[mask] = 0.9; biome_id[mask] = biome_map["wetlands"]
        elif r["terrain_class"] == "arid_plains":
            elevation[mask] = 0.4; moisture[mask] = 0.15; biome_id[mask] = biome_map["arid_plains"]
        elif r["terrain_class"] == "coastal_settlement":
            elevation[mask] = 0.3; moisture[mask] = 0.6; biome_id[mask] = biome_map["coastal_settlement"]
        else:
            biome_id[mask] = biome_map["default"]

    # Smooth transitions (Gaussian blur approx)
    for _ in range(2):
        elevation = _smooth(elevation); moisture = _smooth(moisture)
    
    # Convert to serializable tile intent grid
    tile_grid = []
    for y in range(grid_size):
        for x in range(grid_size):
            tile_grid.append({
                "x": x, "y": y,
                "elevation": float(elevation[y, x]),
                "moisture": float(moisture[y, x]),
                "biome_id": int(biome_id[y, x]),
                "region_id": _find_region_id(x, y, terrain)
            })
            
    return {"version": "1.0", "grid_size": grid_size, "tiles": tile_grid}

def _smooth(arr: np.ndarray, k: int = 3) -> np.ndarray:
    return np.pad(arr, k//2, mode="edge")
    # Simplified smoothing for production stub; replace with scipy.ndimage.gaussian_filter in full build

def _find_region_id(x: int, y: int, terrain: Dict) -> str:
    for rid, r in terrain.items():
        b = r["bounds"]
        if b["x_min"] <= x < b["x_max"] and b["y_min"] <= y < b["y_max"]:
            return rid
    return "ocean"
