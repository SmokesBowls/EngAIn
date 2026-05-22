# trixel_world_adapter.py
# Connects WorldField (float terrain state) to TrixelWorld (semantic terrain grid).
#
# Responsibility:
#   - Receive dirty chunk data from GodotWorldFieldBridge
#   - Convert floats → terrain strings via terrain_thresholds
#   - Push changes into the TrixelWorld adapter's semantic grid
#   - Emit delta events for downstream consumers (Godot, ZW broker, etc.)
#
# This is the AP rule layer between the two systems.
# It does NOT own state — WorldField owns floats, TrixelWorld owns semantics.

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from terrain_thresholds import value_to_terrain, VALID_TERRAIN_TYPES


# ---------------------------------------------------------------------------
# AP threshold rules
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ThresholdRule:
    """
    Fires when a cell's float value crosses a boundary and the resulting
    terrain type changes.  callback receives (world_x, world_y, old_terrain, new_terrain).
    """
    name: str
    callback: Callable[[int, int, str, str], None]


# ---------------------------------------------------------------------------
# Cell delta — what changed
# ---------------------------------------------------------------------------

@dataclass
class TerrainDelta:
    world_x: int
    world_y: int
    old_terrain: str
    new_terrain: str


# ---------------------------------------------------------------------------
# Adapter
# ---------------------------------------------------------------------------

class TrixelWorldFieldAdapter:
    """
    Sits between GodotWorldFieldBridge (dirty float chunks) and the
    TrixelWorld semantic grid.

    Usage:
        adapter = TrixelWorldFieldAdapter(grid_width=48, grid_height=48)
        adapter.register_rule(ThresholdRule("log_changes", my_callback))

        # When WorldField produces dirty chunks:
        deltas = adapter.apply_dirty_chunks(dirty_chunks)
        terrain_grid = adapter.get_terrain_grid()
    """

    def __init__(self, grid_width: int = 48, grid_height: int = 48, default_terrain: str = "grass"):
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.default_terrain = default_terrain

        # Semantic terrain grid — 2D list[list[str]]
        self._grid: list[list[str]] = [
            [default_terrain] * grid_width for _ in range(grid_height)
        ]

        # AP rules
        self._rules: list[ThresholdRule] = []

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register_rule(self, rule: ThresholdRule) -> None:
        self._rules.append(rule)

    # ------------------------------------------------------------------
    # Core update
    # ------------------------------------------------------------------

    def apply_dirty_chunks(self, dirty_chunks: list[dict]) -> list[TerrainDelta]:
        """
        Process dirty chunk dicts from GodotWorldFieldBridge.
        Returns list of TerrainDelta for each cell that changed terrain type.
        """
        deltas: list[TerrainDelta] = []

        for chunk in dirty_chunks:
            cx, cy = chunk["chunk_key"]
            size: int = chunk["size"]
            data: list[float] = chunk["data"]

            world_origin_x = cx * size
            world_origin_y = cy * size

            for local_y in range(size):
                world_y = world_origin_y + local_y
                if world_y < 0 or world_y >= self.grid_height:
                    continue

                for local_x in range(size):
                    world_x = world_origin_x + local_x
                    if world_x < 0 or world_x >= self.grid_width:
                        continue

                    idx = local_y * size + local_x
                    new_terrain = value_to_terrain(data[idx])
                    old_terrain = self._grid[world_y][world_x]

                    if new_terrain != old_terrain:
                        self._grid[world_y][world_x] = new_terrain
                        delta = TerrainDelta(world_x, world_y, old_terrain, new_terrain)
                        deltas.append(delta)
                        self._fire_rules(delta)

        return deltas

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_terrain_grid(self) -> list[list[str]]:
        """Return current semantic terrain grid (2D list of strings)."""
        return [row[:] for row in self._grid]

    def get_terrain_at(self, world_x: int, world_y: int) -> str:
        if 0 <= world_y < self.grid_height and 0 <= world_x < self.grid_width:
            return self._grid[world_y][world_x]
        return ""

    def as_trixel_plan(self) -> dict:
        """
        Return a plan dict that TrixelEnvironmentPlanner would produce —
        so Boot.gd / SemanticRenderer can consume it directly.
        """
        return {
            "terrain_grid": self.get_terrain_grid(),
            "prop_placements": [],
            "landmark_nodes": [],
            "terrain_family": "world_field",
            "environment": "dynamic",
            "map_size": {
                "x": self.grid_width,
                "y": self.grid_height,
            },
        }

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _fire_rules(self, delta: TerrainDelta) -> None:
        for rule in self._rules:
            try:
                rule.callback(delta.world_x, delta.world_y, delta.old_terrain, delta.new_terrain)
            except Exception as e:
                print(f"[TrixelWorldFieldAdapter] Rule '{rule.name}' raised: {e}")


# ---------------------------------------------------------------------------
# Convenience: wire WorldField + Bridge + Adapter together
# ---------------------------------------------------------------------------

def make_wired_field(
    grid_width: int = 48,
    grid_height: int = 48,
    chunk_size: int = 32,
) -> tuple:
    """
    Returns (world_field, bridge, adapter) fully wired.

    Example:
        field, bridge, adapter = make_wired_field(48, 48)
        bridge.handle_edit(24.0, 24.0, 'add', radius=4, strength=0.4)
        dirty = bridge.get_dirty_data()       # already cleared flags
        deltas = adapter.apply_dirty_chunks(dirty)
        plan = adapter.as_trixel_plan()       # ready for SemanticRenderer
    """
    # Import here to avoid circular dependency if moved to separate package
    import sys, os
    sys.path.insert(0, os.path.dirname(__file__))
    from world_field_nucleus import WorldField, GodotWorldFieldBridge

    world_field = WorldField(chunk_size=chunk_size)
    bridge = GodotWorldFieldBridge(world_field)
    adapter = TrixelWorldFieldAdapter(grid_width=grid_width, grid_height=grid_height)
    return world_field, bridge, adapter


# ---------------------------------------------------------------------------
# Terrain palette — colour hints per terrain type for downstream consumers
# ---------------------------------------------------------------------------

TERRAIN_PALETTE = {
    "deep_water":    "#1a3a5c",
    "shallow_water": "#2d6a8f",
    "shoreline":     "#c8b878",
    "sand":          "#d4c278",
    "grass":         "#4a8c3f",
    "forest_edge":   "#2d5e28",
    "rock":          "#7a7a7a",
    "cliff":         "#5a5050",
    "pier":          "#8b6914",
}


# ---------------------------------------------------------------------------
# CLI demo — called by TrixelEnvironmentPlanner.gd via OS.execute
# ---------------------------------------------------------------------------

def cli_demo(width: int = 48, height: int = 48, scene_id: str = None, out_path: str = None, scene_json: str = None) -> None:
    """
    Generate a demo terrain and print JSON to stdout.
    Output contract:
        {
            "terrain_grid":    Array[Array[str]],
            "terrain_palette": Dict[str, str],
            "source":          "world_field"
        }
    """
    import json
    import os

    profile = "default"
    if scene_json and os.path.exists(scene_json):
        try:
            with open(scene_json, 'r', encoding='utf-8') as f:
                scene_data = json.load(f)
            
            metadata_str = ""
            for key in ["terrain_family", "@terrain_family", "environment", "terrain_metadata", "level_design", "region", "@region"]:
                val = scene_data.get(key)
                if isinstance(val, dict):
                    metadata_str += " " + " ".join(str(v) for v in val.values())
                elif val:
                    metadata_str += " " + str(val)
                    
            metadata_str = metadata_str.lower()
            
            if "beach" in metadata_str or "coastal" in metadata_str:
                profile = "coastal"
            elif any(word in metadata_str for word in ["shadow", "ambient", "wasteland", "ash"]):
                profile = "wasteland"
        except Exception as e:
            pass

    _, bridge, adapter = make_wired_field(width, height)

    cx, cy = width // 2, height // 2
    all_dirty: list[dict] = []

    if profile == "coastal":
        # Island/coastline map
        # Base: deep water
        all_dirty += bridge.handle_edit(float(cx), float(cy), "add", radius=width * 2, strength=0.0)
        # Island on one side
        all_dirty += bridge.handle_edit(float(cx + 8), float(cy), "add", radius=14, strength=0.5) # Grass/sand
        all_dirty += bridge.handle_edit(float(cx + 12), float(cy - 5), "add", radius=8, strength=0.2)
        all_dirty += bridge.handle_edit(float(cx + 8), float(cy), "smooth", radius=6)
    elif profile == "wasteland":
        # Ash plain / wasteland map
        # Base: rock
        all_dirty += bridge.handle_edit(float(cx), float(cy), "add", radius=width * 2, strength=0.85) # Rock
        # Cliffs and rugged terrain
        all_dirty += bridge.handle_edit(float(cx), float(cy), "add", radius=10, strength=0.2) # Cliff
        all_dirty += bridge.handle_edit(float(cx - 8), float(cy + 8), "add", radius=6, strength=-0.3) # Forest edge / ash
        all_dirty += bridge.handle_edit(float(cx), float(cy), "smooth", radius=4)
    else:
        # Central hill
        all_dirty += bridge.handle_edit(float(cx), float(cy), "add", radius=10, strength=0.6)
        all_dirty += bridge.handle_edit(float(cx), float(cy), "add", radius=5,  strength=0.3)
        all_dirty += bridge.handle_edit(float(cx), float(cy), "smooth", radius=3)

        # Secondary feature — a ridge toward the north-east
        all_dirty += bridge.handle_edit(float(cx + 10), float(cy - 10), "add", radius=6, strength=0.4)
        all_dirty += bridge.handle_edit(float(cx + 10), float(cy - 10), "smooth", radius=2)

    adapter.apply_dirty_chunks(all_dirty)

    result = {
        "terrain_grid":    adapter.get_terrain_grid(),
        "terrain_palette": TERRAIN_PALETTE,
        "source":          "world_field",
        "profile":         profile,
    }
    if scene_id:
        result["scene_id"] = scene_id

    json_str = json.dumps(result)
    print(json_str)

    if out_path:
        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(json_str)


# ---------------------------------------------------------------------------
# Smoke test / CLI entry
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    import json
    import os

    parser = argparse.ArgumentParser(description="TrixelWorldFieldAdapter CLI")
    parser.add_argument("--demo", action="store_true", help="Output demo terrain JSON to stdout")
    parser.add_argument("--width",  type=int, default=48, help="Grid width")
    parser.add_argument("--height", type=int, default=48, help="Grid height")
    parser.add_argument("--scene-id", type=str, default=None, help="Optional scene ID")
    parser.add_argument("--out", type=str, default=None, help="Optional path to save the plan JSON")
    
    # Tier 1: Direct in-memory extraction string
    parser.add_argument("--context", type=str, default="", help="Raw metadata text context from runtime_scene_doc")
    # Tier 2: File-based cache fallback
    parser.add_argument("--scene-json", type=str, default=None, help="Path to cached scene JSON file")
    args = parser.parse_args()

    if args.demo:
        context_text = ""
        resolved_source = "default_fallback"

        # TIER 1: Check primary runtime context
        if args.context and args.context.strip():
            context_text = args.context.lower()
            resolved_source = "runtime_context"

        # TIER 2: Fall back to file parser if context string is missing/empty
        elif args.scene_json and os.path.exists(args.scene_json):
            try:
                with open(args.scene_json, 'r', encoding='utf-8') as f:
                    scene_data = json.load(f)
                
                # Extract structural keys for evaluation
                metadata_str = ""
                for key in ["terrain_family", "environment", "level_design", "region", "metadata"]:
                    val = scene_data.get(key)
                    if isinstance(val, dict):
                        metadata_str += " " + " ".join(str(v) for v in val.values())
                    elif val:
                        metadata_str += " " + str(val)
                
                context_text = metadata_str.lower()
                resolved_source = f"cached_file ({os.path.basename(args.scene_json)})"
            except Exception as e:
                print(f"[Trixel CLI Warning] Failed to parse file payload: {e}")

        # Profile Inference Engine based on resolved text profile
        profile = "default"
        if context_text:
            if "beach" in context_text or "coastal" in context_text or "shoreline" in context_text:
                profile = "coastal"
            elif any(word in context_text for word in ["shadow", "ambient", "wasteland", "ash", "molten"]):
                profile = "wasteland"

        # Build field matrix
        _, bridge, adapter = make_wired_field(args.width, args.height)
        cx, cy = args.width // 2, args.height // 2
        all_dirty = []

        if profile == "coastal":
            all_dirty += bridge.handle_edit(float(cx), float(cy), "add", radius=args.width * 2, strength=0.0)
            all_dirty += bridge.handle_edit(float(cx + 8), float(cy), "add", radius=14, strength=0.5)
            all_dirty += bridge.handle_edit(float(cx + 12), float(cy - 5), "add", radius=8, strength=0.2)
            all_dirty += bridge.handle_edit(float(cx + 8), float(cy), "smooth", radius=6)
        elif profile == "wasteland":
            all_dirty += bridge.handle_edit(float(cx), float(cy), "add", radius=args.width * 2, strength=0.85)
            all_dirty += bridge.handle_edit(float(cx), float(cy), "add", radius=10, strength=0.2)
            all_dirty += bridge.handle_edit(float(cx - 8), float(cy + 8), "add", radius=6, strength=-0.3)
            all_dirty += bridge.handle_edit(float(cx), float(cy), "smooth", radius=4)
        else:
            all_dirty += bridge.handle_edit(float(cx), float(cy), "add", radius=10, strength=0.6)
            all_dirty += bridge.handle_edit(float(cx), float(cy), "smooth", radius=3)

        adapter.apply_dirty_chunks(all_dirty)

        # Ship it to stdout JSON contract
        result = {
            "terrain_grid":    adapter.get_terrain_grid(),
            "terrain_palette": TERRAIN_PALETTE,
            "source":          "world_field",
            "profile":         profile,
            "resolved_via":    resolved_source
        }
        if args.scene_id:
            result["scene_id"] = args.scene_id

        print(json.dumps(result))

        if args.out:
            os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
            with open(args.out, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=4)
