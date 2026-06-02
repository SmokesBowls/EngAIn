"""trixelcomposer/demand_resolver.py — Deterministic visual demand-resolution service layer.

Transforms semantic runtime visual demands into deterministic visual artifact references
while strictly preserving isolation from canonical world-state authority.
"""

from __future__ import annotations

import os
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional

# Define assets root paths
_HERE = Path(__file__).parent.resolve()
TRIXEL_ASSETS_ROOT = Path(os.environ.get(
    "TRIXEL_ASSETS_ROOT",
    str(_HERE.parent / "godotnew" / "semantic" / "trixel" / "trixelassets"),
))
RECIPES_DIR = _HERE / "recipes"


# Hardcoded registered atlas list for fallback/testing environments where godotnew is not present
REGISTERED_ATLAS_ENTRIES = {
    "cliff", "deep_water", "forest_edge", "grass", "pier", "rock", "sand", "shallow_water", "shoreline"
}


class TrixelDemandResolver:
    """Standalone service to resolve semantic demand packets into visual references."""

    def __init__(self, assets_root: Optional[Path] = None):
        self.assets_root = assets_root or TRIXEL_ASSETS_ROOT
        self._cache: Dict[str, dict] = {}

    def get_registered_atlases(self) -> set[str]:
        """Dynamically detect registered atlases in the asset directory."""
        if not self.assets_root.exists():
            return REGISTERED_ATLAS_ENTRIES
        
        atlases = set()
        for item in self.assets_root.iterdir():
            if item.is_dir() and (item / "atlas_meta.json").exists():
                atlases.add(item.name)
        return atlases if atlases else REGISTERED_ATLAS_ENTRIES

    def resolve_demand(self, demand: dict) -> dict:
        """Resolve a semantic demand packet into a deterministic visual reference."""
        # 1. Validate envelope shape
        if not isinstance(demand, dict):
            return self._build_unresolved_envelope()

        demand_id = demand.get("demand_id", "")
        semantic_context = demand.get("semantic_context", {})
        if not isinstance(semantic_context, dict):
            return self._build_unresolved_envelope()

        terrain = semantic_context.get("terrain", "")
        surface = semantic_context.get("surface", "")
        effect = semantic_context.get("effect")
        world_state = semantic_context.get("world_state")
        world_cell = demand.get("world_cell", {})
        entropy_seed = demand.get("entropy_seed", "")

        # Compute unique cache key for identical demands
        cache_key = self._compute_cache_key(demand)
        if cache_key in self._cache:
            return self._cache[cache_key]

        # 2. Pipeline Stage A: Atlas Lookup (Exact metadata match)
        registered_atlases = self.get_registered_atlases()
        if terrain in registered_atlases:
            ref = f"res://trixel/trixelassets/{terrain}/atlas.png"
            result = {
                "tile_ref": ref,
                "authority_level": "observer_relative",
                "authoritative": False,
                "derivation": "atlas",
            }
            self._cache[cache_key] = result
            return result

        # 3. Pipeline Stage B: Recipe Family Resolution
        recipe_family = self._resolve_recipe_family(terrain, surface, effect)
        
        # 4. Pipeline Stage C: Deterministic Variant Generation
        if recipe_family:
            if entropy_seed:
                # Generate a unique deterministic variant reference
                variant_hash = self._compute_variant_hash(terrain, entropy_seed, world_cell, demand.get("view_address_hint"))
                ref = f"trixel_variant://{recipe_family}_{variant_hash}"
                result = {
                    "tile_ref": ref,
                    "authority_level": "observer_relative",
                    "authoritative": False,
                    "derivation": "generated",
                }
            else:
                ref = f"trixel_recipe://{recipe_family}"
                result = {
                    "tile_ref": ref,
                    "authority_level": "observer_relative",
                    "authoritative": False,
                    "derivation": "recipe",
                }
            self._cache[cache_key] = result
            return result

        # 5. Pipeline Stage E: Explicit Failure / Neutral Fallback Policy
        if terrain:
            # Explicit neutral fallback reference
            result = {
                "tile_ref": "trixel_fallback://neutral_gray",
                "authority_level": "observer_relative",
                "authoritative": False,
                "derivation": "fallback",
            }
        else:
            result = self._build_unresolved_envelope()

        self._cache[cache_key] = result
        return result

    def _compute_cache_key(self, demand: dict) -> str:
        """Derive a stable hash representing unique demand parameters."""
        ctx = demand.get("semantic_context", {})
        cell = demand.get("world_cell", {})
        cell_str = f"{cell.get('x', 0)}_{cell.get('y', 0)}_{cell.get('z', 0)}"
        components = [
            demand.get("demand_id", ""),
            ctx.get("terrain", ""),
            ctx.get("surface", ""),
            ctx.get("effect") or "",
            ctx.get("world_state") or "",
            cell_str,
            demand.get("entropy_seed", ""),
            demand.get("view_address_hint") or ""
        ]
        raw_str = "|".join(components)
        return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()

    def _compute_variant_hash(self, terrain: str, seed: str, cell: dict, view_hint: Optional[str]) -> str:
        cell_str = f"{cell.get('x', 0)}_{cell.get('y', 0)}_{cell.get('z', 0)}"
        raw_str = f"{terrain}|{seed}|{cell_str}|{view_hint or ''}"
        return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()[:16]

    def _resolve_recipe_family(self, terrain: str, surface: str, effect: Optional[str]) -> Optional[str]:
        """Map semantic tags into recipe-family parameters."""
        # Check standard keyword mappings
        tags = [t.lower() for t in [terrain, surface, effect or ""] if t]
        
        keyword_overrides = {
            "molten": "volcano", "lava": "volcano", "fire": "volcano", "obsidian": "volcano", "glow": "volcano", "vrill": "volcano",
            "frost": "tundra", "arctic": "tundra", "snow": "tundra", "ice": "tundra", "frozen": "tundra",
            "sand": "desert", "dune": "desert",
            "abyss": "ocean", "deep": "ocean",
            "dungeon": "cave", "cavern": "cave", "underground": "cave",
            "bog": "swamp", "marsh": "swamp",
            "jungle": "forest", "grove": "forest", "wood": "forest",
            "peak": "mountain", "cliff": "mountain", "highland": "mountain", "summit": "mountain",
            "shore": "beach", "coastal": "beach", "wave": "beach"
        }

        # Check tags against keyword overrides
        for tag in tags:
            for keyword, family in keyword_overrides.items():
                if keyword in tag:
                    return family

        # Fallback check against recipe files directly
        recipe_terrain_dir = RECIPES_DIR / "terrain"
        if recipe_terrain_dir.exists():
            for tag in tags:
                pattern = f"{tag}.*.json"
                matches = list(recipe_terrain_dir.glob(pattern))
                if matches:
                    return tag

        return None

    def _build_unresolved_envelope(self) -> dict:
        return {
            "tile_ref": None,
            "authority_level": "observer_relative",
            "authoritative": False,
            "derivation": "unresolved",
        }


# Standalone module-level convenience function
def resolve_demand(demand: dict) -> dict:
    """Resolve a semantic demand packet independently using a default resolver instance."""
    resolver = TrixelDemandResolver()
    return resolver.resolve_demand(demand)
