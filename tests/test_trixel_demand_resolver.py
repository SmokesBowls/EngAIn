import pytest
from trixelcomposer.demand_resolver import TrixelDemandResolver, resolve_demand

def test_demand_resolver_atlas_hit():
    resolver = TrixelDemandResolver()
    demand = {
        "demand_id": "demand-1",
        "semantic_context": {
            "terrain": "sand",
            "surface": "flat",
            "effect": None,
            "world_state": None,
        },
        "world_cell": {"x": 12, "y": 0, "z": 8},
        "abi_address": None,
        "view_address_hint": None,
        "entropy_seed": "seed-123",
    }
    
    result = resolver.resolve_demand(demand)
    
    assert result["tile_ref"] == "res://trixel/trixelassets/sand/atlas.png"
    assert result["authority_level"] == "observer_relative"
    assert result["authoritative"] is False
    assert result["derivation"] == "atlas"


def test_demand_resolver_recipe_resolution():
    resolver = TrixelDemandResolver()
    demand = {
        "demand_id": "demand-2",
        "semantic_context": {
            "terrain": "volcano",
            "surface": "molten",
            "effect": None,
            "world_state": None,
        },
        "world_cell": {"x": 100, "y": 0, "z": 200},
        "abi_address": None,
        "view_address_hint": None,
        "entropy_seed": "", # Empty seed -> yields base recipe ref
    }
    
    result = resolver.resolve_demand(demand)
    
    assert result["tile_ref"] == "trixel_recipe://volcano"
    assert result["authority_level"] == "observer_relative"
    assert result["authoritative"] is False
    assert result["derivation"] == "recipe"


def test_demand_resolver_deterministic_variant_generation():
    resolver = TrixelDemandResolver()
    demand1 = {
        "demand_id": "demand-3",
        "semantic_context": {
            "terrain": "molten_shore", # Maps to volcano
            "surface": "glow",
            "effect": "vrill_glow",
            "world_state": "active",
        },
        "world_cell": {"x": 15, "y": 1, "z": 22},
        "abi_address": None,
        "view_address_hint": "d15.u1.f22",
        "entropy_seed": "seed-888",
    }
    
    demand2 = {
        "demand_id": "demand-3",
        "semantic_context": {
            "terrain": "molten_shore",
            "surface": "glow",
            "effect": "vrill_glow",
            "world_state": "active",
        },
        "world_cell": {"x": 15, "y": 1, "z": 22},
        "abi_address": None,
        "view_address_hint": "d15.u1.f22",
        "entropy_seed": "seed-888",
    }
    
    # 1. Same input -> same output across calls
    res1 = resolver.resolve_demand(demand1)
    res2 = resolver.resolve_demand(demand2)
    
    assert res1 == res2
    assert res1["derivation"] == "generated"
    assert res1["tile_ref"].startswith("trixel_variant://volcano_")
    assert res1["authority_level"] == "observer_relative"
    assert res1["authoritative"] is False
    
    # 2. Different cell or seed -> different variant
    demand_diff_cell = dict(demand1, world_cell={"x": 16, "y": 1, "z": 22})
    res_diff_cell = resolver.resolve_demand(demand_diff_cell)
    assert res1 != res_diff_cell
    
    demand_diff_seed = dict(demand1, entropy_seed="seed-999")
    res_diff_seed = resolver.resolve_demand(demand_diff_seed)
    assert res1 != res_diff_seed


def test_demand_resolver_fallback_policy():
    resolver = TrixelDemandResolver()
    
    # Unknown terrain with no matching keyword/recipe -> neutral fallback
    demand = {
        "demand_id": "demand-4",
        "semantic_context": {
            "terrain": "alien_sludge",
            "surface": "bubbly",
            "effect": None,
            "world_state": None,
        },
        "world_cell": {"x": 0, "y": 0, "z": 0},
        "abi_address": None,
        "view_address_hint": None,
        "entropy_seed": "seed-111",
    }
    
    result = resolver.resolve_demand(demand)
    
    assert result["tile_ref"] == "trixel_fallback://neutral_gray"
    assert result["derivation"] == "fallback"
    assert result["authority_level"] == "observer_relative"
    assert result["authoritative"] is False


def test_demand_resolver_unresolved_envelope():
    resolver = TrixelDemandResolver()
    
    # Missing terrain completely -> unresolved
    demand = {
        "demand_id": "demand-5",
        "semantic_context": {
            "terrain": "",
            "surface": "",
            "effect": None,
            "world_state": None,
        },
        "world_cell": {},
        "abi_address": None,
        "view_address_hint": None,
        "entropy_seed": "",
    }
    
    result = resolver.resolve_demand(demand)
    
    assert result["tile_ref"] is None
    assert result["derivation"] == "unresolved"
    assert result["authority_level"] == "observer_relative"
    assert result["authoritative"] is False


def test_demand_resolver_caching():
    resolver = TrixelDemandResolver()
    demand = {
        "demand_id": "demand-6",
        "semantic_context": {
            "terrain": "grass",
            "surface": "lush",
            "effect": None,
            "world_state": None,
        },
        "world_cell": {"x": 5, "y": 5, "z": 5},
        "abi_address": None,
        "view_address_hint": None,
        "entropy_seed": "seed-999",
    }
    
    # Initial resolution
    res1 = resolver.resolve_demand(demand)
    # Subsequent resolution (should hit cache)
    res2 = resolver.resolve_demand(demand)
    
    assert res1 is res2  # verify identical object instance retrieved from cache


def test_module_resolve_demand():
    demand = {
        "demand_id": "demand-7",
        "semantic_context": {
            "terrain": "grass",
        },
        "world_cell": {},
        "entropy_seed": "",
    }
    
    # Standalone module-level call should work perfectly
    res = resolve_demand(demand)
    assert res["tile_ref"] == "res://trixel/trixelassets/grass/atlas.png"
    assert res["derivation"] == "atlas"
