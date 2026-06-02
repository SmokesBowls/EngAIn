# scene_server.py (selector/compiler logic)
from pathlib import Path
import hashlib
import json
from typing import Dict, List, Optional

RECIPES_DIR = Path(__file__).parent / "recipes"
TRANSITIONS_DIR = RECIPES_DIR / "transitions"
TRIXELMAP_RECIPE_PATH = Path(__file__).parent.parent / "trixelmap" / "out" / "trixelcomposer_recipe.json"

# Maps trixelmap primary_biome_id → terrain string used by recipes/terrain/
_BIOME_ID_TO_TERRAIN: Dict[int, str] = {
    0: "mountain",   # frozen_volcanic_peak
    1: "mountain",   # alpine_spine
    2: "swamp",      # wetlands
    3: "desert",     # arid_plains
    4: "beach",      # coastal_settlement
    5: "default",    # fallback
}

KEYWORD_OVERRIDES: Dict[str, str] = {
    "molten": "volcano",   "lava": "volcano",    "fire": "volcano",
    "inferno": "volcano",  "magma": "volcano",   "ember": "volcano",
    "cinder": "volcano",   "ashen": "volcano",
    "frost": "tundra",     "arctic": "tundra",   "snow": "tundra",
    "ice": "tundra",       "frozen": "tundra",
    "sand": "desert",      "dune": "desert",
    "abyss": "ocean",      "deep": "ocean",
    "dungeon": "cave",     "cavern": "cave",     "underground": "cave",
    "bog": "swamp",        "marsh": "swamp",
    "jungle": "forest",    "grove": "forest",    "wood": "forest",
    "peak": "mountain",    "cliff": "mountain",  "highland": "mountain",
    "summit": "mountain",
}


def _resolve_terrain(scene_id: str, terrain_hint: str) -> str:
    name_lower = scene_id.lower()
    for keyword, override in KEYWORD_OVERRIDES.items():
        if keyword in name_lower:
            return override
    return terrain_hint or "default"


def list_recipes(terrain: Optional[str] = None) -> List[Path]:
    """Return all recipe files under recipes/terrain/, optionally filtered by terrain prefix."""
    terrain_dir = RECIPES_DIR / "terrain"
    if not terrain_dir.exists():
        return []
    pattern = f"{terrain}.*.json" if terrain else "*.json"
    return sorted(terrain_dir.glob(pattern))


def _select_recipe_path(terrain: str, env: str) -> Path:
    """Find the best recipe file for terrain+env. Prefers env match, else first variant."""
    candidates = list_recipes(terrain)
    if not candidates:
        candidates = list_recipes("default")
    if not candidates:
        raise ValueError(f"No recipe found for terrain={terrain!r}, env={env!r}")

    for path in candidates:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if data.get("environment", "").lower() == env.lower():
                return path
        except Exception:
            continue

    return candidates[0]


def _load_region_authority() -> Dict[str, dict]:
    """
    Load trixelmap region registry. Returns {region_id: region_dict}.
    Fails silently — keyword fallback takes over if file is missing or malformed.
    """
    if not TRIXELMAP_RECIPE_PATH.exists():
        return {}
    try:
        data = json.loads(TRIXELMAP_RECIPE_PATH.read_text(encoding="utf-8"))
        return {r["id"]: r for r in data.get("regions", [])}
    except Exception:
        return {}


# Module-level cache — loaded once per process
_REGION_AUTHORITY: Optional[Dict[str, dict]] = None


def _resolve_terrain_from_region(scene_id: str, terrain_hint: str) -> str:
    """
    Priority order:
      1. Exact region_id match in trixelmap authority  → biome_id → terrain
      2. Keyword match in scene_id                     → terrain override
      3. terrain_hint passthrough                      → hint or "default"
    """
    global _REGION_AUTHORITY
    if _REGION_AUTHORITY is None:
        _REGION_AUTHORITY = _load_region_authority()

    # 1. Chronicles authority — exact region id match
    region = _REGION_AUTHORITY.get(scene_id)
    if region is not None:
        biome_id = region.get("primary_biome_id", 5)
        return _BIOME_ID_TO_TERRAIN.get(biome_id, "default")

    # 2. Keyword fallback (existing logic inlined)
    name_lower = scene_id.lower()
    for keyword, override in KEYWORD_OVERRIDES.items():
        if keyword in name_lower:
            return override

    # 3. Hint passthrough
    return terrain_hint or "default"


def compile_recipe(scene_doc: dict) -> dict:
    """Select recipe book entry → inject scene values → emit final recipe JSON."""
    scene_id = scene_doc.get("scene_id", "unknown")
    env = scene_doc.get("environment", "unknown")
    entity_count = scene_doc.get("entity_count", 0)
    terrain_hint = scene_doc.get("terrain", "default")
    entities = scene_doc.get("entities", [])

    terrain = _resolve_terrain_from_region(scene_id, terrain_hint)
    recipe_path = _select_recipe_path(terrain, env)
    recipe = json.loads(recipe_path.read_text(encoding="utf-8"))

    # Inject scene-specific values
    recipe["scene_id"] = scene_id
    recipe["terrain"] = terrain
    recipe["entity_count"] = entity_count
    recipe.setdefault("canvas", {})["width"] = 16
    recipe.setdefault("canvas", {})["height"] = 16

    # Inject normalised entity positions into every entity_marker pass
    if entities:
        xs = [e["position"]["x"] for e in entities if "position" in e]
        x_min, x_max = (min(xs), max(xs)) if xs else (0, 1)
        x_range = (x_max - x_min) or 1
        entity_markers = [
            {
                "id": e.get("id", "unknown"),
                "name": e.get("name", "?"),
                "nx": round((e.get("position", {}).get("x", 0) - x_min) / x_range, 4),
            }
            for e in entities
        ]
        for step in recipe.get("passes", []):
            if step.get("type") == "entity_marker":
                step["entities"] = entity_markers

    # Seed deterministic RNG for reproducibility
    base_seed = int.from_bytes(
        hashlib.md5(scene_id.encode()).digest()[:4], "little"
    ) & 0x7FFFFFFF
    for i, step in enumerate(recipe.get("passes", [])):
        if step.get("seed") is None:
            step["seed"] = base_seed + i

    return recipe


def list_transitions() -> List[Path]:
    """Return all transition recipe files under recipes/transitions/."""
    if not TRANSITIONS_DIR.exists():
        return []
    return sorted(TRANSITIONS_DIR.glob("*.json"))


def compile_transition(edge_doc: dict) -> dict:
    """Load a transition recipe by edge name and inject scene values."""
    edge_name = edge_doc.get("edge", "")
    scene_id = edge_doc.get("scene_id", "unknown")

    path = TRANSITIONS_DIR / f"{edge_name}.json"
    if not path.exists():
        available = [p.stem for p in list_transitions()]
        raise ValueError(
            f"No transition recipe {edge_name!r}. Available: {available}"
        )

    recipe = json.loads(path.read_text(encoding="utf-8"))
    recipe["scene_id"] = scene_id
    recipe.setdefault("canvas", {})["width"] = 16
    recipe.setdefault("canvas", {})["height"] = 16

    base_seed = int.from_bytes(
        hashlib.md5(scene_id.encode()).digest()[:4], "little"
    ) & 0x7FFFFFFF
    for i, step in enumerate(recipe.get("passes", [])):
        if step.get("seed") is None:
            step["seed"] = base_seed + i

    return recipe


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Trixel scene recipe selector/compiler",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  python3 scene_server.py --list\n"
            "  python3 scene_server.py --compile lava_pit_003\n"
            "  python3 scene_server.py --compile lava_pit_003 --out recipe.json\n"
            "  python3 scene_server.py --compile shore_01 --terrain beach --env coastal\n"
            "  python3 scene_server.py --compile-edge shoreline\n"
            "  python3 scene_server.py --compile-edge lava_to_ash --out edge.json"
        ),
    )
    parser.add_argument("--list", action="store_true", help="List all terrain and transition recipes")
    parser.add_argument("--compile", metavar="SCENE_ID", help="Compile terrain recipe for SCENE_ID")
    parser.add_argument("--terrain", default="default", help="Terrain hint (overridden by keyword match)")
    parser.add_argument("--env", default="unknown", help="Environment hint for variant selection")
    parser.add_argument("--compile-edge", metavar="EDGE_NAME", help="Compile transition recipe by edge name")
    parser.add_argument("--out", metavar="FILE", help="Write compiled recipe JSON to FILE instead of stdout")
    args = parser.parse_args()

    if args.list:
        terrain_recipes = list_recipes()
        transition_recipes = list_transitions()
        if not terrain_recipes and not transition_recipes:
            print("No recipes found.", file=sys.stderr)
            sys.exit(1)

        print(f"Terrain recipes ({len(terrain_recipes)}):")
        for path in terrain_recipes:
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                print(f"  {path.stem:<40}  {data.get('terrain','?'):<12}  {data.get('environment','?'):<14}  {data.get('label','?')}")
            except Exception:
                print(f"  {path.name}  (unreadable)")

        print(f"\nTransition recipes ({len(transition_recipes)}):")
        for path in transition_recipes:
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                a = data.get("terrain_a", "?")
                b = data.get("terrain_b", "?")
                print(f"  {path.stem:<40}  {a:<12} → {b:<12}  {data.get('label','?')}")
            except Exception:
                print(f"  {path.name}  (unreadable)")

    elif args.compile:
        scene_doc = {
            "scene_id": args.compile,
            "terrain": args.terrain,
            "environment": args.env,
        }
        try:
            recipe = compile_recipe(scene_doc)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            sys.exit(1)

        output = json.dumps(recipe, indent=2)
        if args.out:
            out_path = Path(args.out)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(output, encoding="utf-8")
            print(f"compiled: {args.compile} → {out_path}  ({len(recipe['passes'])} passes, terrain={recipe['terrain']})")
        else:
            print(output)

    elif args.compile_edge:
        edge_doc = {"edge": args.compile_edge, "scene_id": args.compile_edge}
        try:
            recipe = compile_transition(edge_doc)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            sys.exit(1)

        output = json.dumps(recipe, indent=2)
        if args.out:
            out_path = Path(args.out)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(output, encoding="utf-8")
            print(f"compiled edge: {args.compile_edge} → {out_path}  ({len(recipe['passes'])} passes)")
        else:
            print(output)

    else:
        parser.print_help()
