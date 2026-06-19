# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/trixel/gates/gate_adapter_output_shape.py

from __future__ import annotations

from typing import Any

from engain_control.gate_result import GateResult


SAMPLE_SPATIAL_AUTHORITY: dict[str, Any] = {
    "spatial_authority": {
        "version": "1.0",
        "region_count": 7,
        "regions": {
            "coastal_margin": {
                "terrain_class": "shoreline_transition",
                "quadrant": [0.2, 0.3],
                "neighbors": ["shallow_water", "sand"]
            }
        },
        "landmarks": {
            "tide_pool": {"region": "coastal_margin", "type": "feature"}
        },
        "edges": [
            {"source": "deep_basin", "target": "shallow_bay", "type": "depth_gradient"}
        ]
    }
}


SAMPLE_RESOLVED_LAYOUT: dict[str, Any] = {
    "layout": {
        "grid_size": 100,
        "centroids": {
            "coastal_margin": {
                "x": 20, "y": 30,
                "bounds": {"x_min": 10, "x_max": 30, "y_min": 20, "y_max": 40}
            }
        },
        "terrain_class_map": {
            "coastal_margin": "shoreline_transition"
        },
        "relation_vectors": {
            "coastal_margin": {"shallow_water": [30, 50], "sand": [-10, 10]}
        }
    }
}


SAMPLE_TERRAIN_FIELD: dict[str, Any] = {
    "terrain_intent": {
        "profile": "coastal_transition",
        "thresholds": {
            "deep_water": {"min": 0.00, "max": 0.10},
            "shallow_water": {"min": 0.10, "max": 0.22},
            "shoreline_transition": {"min": 0.22, "max": 0.30}
        },
        "region_elevation_targets": {
            "coastal_margin": 0.26
        },
        "smoothing": {
            "kernel": "gaussian_approximation",
            "sigma": 1.5,
            "iterations": 2,
            "note": "Current _smooth() is production stub - not real Gaussian blur yet"
        }
    }
}


SAMPLE_RECIPE: dict[str, Any] = {
    "recipe": {
        "name": "coastal_authority_map",
        "version": "1.0",
        "canvas_size": 16,
        "region_brush_bindings": {
            "deep_water": "terrain_stroke_water",
            "shallow_water": "terrain_stroke_shore"
        },
        "layer_order": ["deep_water", "shallow_water"],
        "blend_mode": "normal",
        "authoritative": False,
        "authority_level": "observer_relative",
        "deterministic_seed": 20260616,
        "handoff_note": "Recipe derived from spatial authority, not final art"
    }
}


SAMPLE_ATLAS_PLAN: dict[str, Any] = {
    "atlas_plan": {
        "atlas_meta": "coastal_atlas_meta.json",
        "uv_regions": {
            "water_zone": {"u": 0.0, "v": 0.0, "width": 0.25, "height": 0.25}
        },
        "region_to_uv": {
            "coastal_margin": "shore_zone"
        },
        "landmark_uv_overrides": {
            "tide_pool": {"u": 0.1, "v": 0.1, "scale": 0.5}
        },
        "composer_handoff": "Atlas plan preserves UV topology contract - renderer owns pixel truth"
    }
}


def gate_spatial_authority_shape(packet: dict[str, Any]) -> GateResult:
    """Validate spatial_authority.json shape."""
    sa = SAMPLE_SPATIAL_AUTHORITY.get("spatial_authority")
    
    if not isinstance(sa, dict):
        return GateResult("gate_spatial_authority_shape", "FALSE", "spatial_authority must be a dict")
    
    if "version" not in sa or "region_count" not in sa or "regions" not in sa:
        return GateResult("gate_spatial_authority_shape", "FALSE", "Missing required fields")
    
    if not isinstance(sa["regions"], dict) or len(sa["regions"]) == 0:
        return GateResult("gate_spatial_authority_shape", "FALSE", "regions must be non-empty dict")
    
    return GateResult("gate_spatial_authority_shape", "TRUE", "spatial_authority shape is valid")


def gate_resolved_layout_shape(packet: dict[str, Any]) -> GateResult:
    """Validate resolved_layout.json shape."""
    layout = SAMPLE_RESOLVED_LAYOUT.get("layout")
    
    if not isinstance(layout, dict):
        return GateResult("gate_resolved_layout_shape", "FALSE", "layout must be a dict")
    
    if "grid_size" not in layout or "centroids" not in layout:
        return GateResult("gate_resolved_layout_shape", "FALSE", "Missing required fields")
    
    if layout["grid_size"] != 100:
        return GateResult("gate_resolved_layout_shape", "FALSE", "grid_size must be 100")
    
    return GateResult("gate_resolved_layout_shape", "TRUE", "resolved_layout shape is valid")


def gate_terrain_field_shape(packet: dict[str, Any]) -> GateResult:
    """Validate terrain_field.json shape."""
    tf = SAMPLE_TERRAIN_FIELD.get("terrain_intent")
    
    if not isinstance(tf, dict):
        return GateResult("gate_terrain_field_shape", "FALSE", "terrain_intent must be a dict")
    
    if "thresholds" not in tf or "region_elevation_targets" not in tf:
        return GateResult("gate_terrain_field_shape", "FALSE", "Missing required fields")
    
    return GateResult("gate_terrain_field_shape", "TRUE", "terrain_field shape is valid")


def gate_recipe_shape(packet: dict[str, Any]) -> GateResult:
    """Validate trixelcomposer_recipe.json shape."""
    recipe = SAMPLE_RECIPE.get("recipe")
    
    if not isinstance(recipe, dict):
        return GateResult("gate_recipe_shape", "FALSE", "recipe must be a dict")
    
    if recipe.get("authoritative") is not False:
        return GateResult("gate_recipe_shape", "FALSE", "recipe must have authoritative: false")
    
    if recipe.get("authority_level") != "observer_relative":
        return GateResult("gate_recipe_shape", "FALSE", "authority_level must be observer_relative")
    
    return GateResult("gate_recipe_shape", "TRUE", "recipe shape is valid")


def gate_atlas_plan_shape(packet: dict[str, Any]) -> GateResult:
    """Validate trixelcomposer_atlas_plan.json shape."""
    ap = SAMPLE_ATLAS_PLAN.get("atlas_plan")
    
    if not isinstance(ap, dict):
        return GateResult("gate_atlas_plan_shape", "FALSE", "atlas_plan must be a dict")
    
    if "uv_regions" not in ap or "region_to_uv" not in ap:
        return GateResult("gate_atlas_plan_shape", "FALSE", "Missing required fields")
    
    return GateResult("gate_atlas_plan_shape", "TRUE", "atlas_plan shape is valid")