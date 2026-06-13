#!/usr/bin/env python3
"""
test_trixel_world_stack.py — Integration test for the full Trixel World subsystem.

Exercises:
  1. mr kernel directly (pure functional)
  2. adapter (state management, AP validation, flush)
  3. scene_shell_builder (narrative → deltas)
  4. ZW router (command dispatch, build_scene_shell)
  5. Full pipeline: narrative text → ZW command → scene shell deltas → adapter apply → verify world state
"""

import json
import os
import sys
import tempfile

try:
    from .trixel_world_mr import (
        WorldGridConfig,
        TerrainType,
        Confidence,
        step_trixel_world,
        create_empty_grid,
        make_cell_id,
        resolve_cell_walkability,
        resolve_autotile_role,
        get_walkable_cells,
        get_cells_by_terrain,
        compute_grid_statistics,
        build_example_beach,
    )
    from .trixel_world_adapter import TrixelWorldAdapter
    from .scene_shell_builder import build_scene_shell, classify_scene, SceneHints
    from .trixel_world_zw import TrixelWorldZWRouter
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from trixel_world_mr import (
        WorldGridConfig,
        TerrainType,
        Confidence,
        step_trixel_world,
        create_empty_grid,
        make_cell_id,
        resolve_cell_walkability,
        resolve_autotile_role,
        get_walkable_cells,
        get_cells_by_terrain,
        compute_grid_statistics,
        build_example_beach,
    )
    from trixel_world_adapter import TrixelWorldAdapter
    from scene_shell_builder import build_scene_shell, classify_scene, SceneHints
    from trixel_world_zw import TrixelWorldZWRouter


PASS = 0
FAIL = 0


def check(name: str, condition: bool, detail: str = ""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        msg = f"  ❌ {name}"
        if detail:
            msg += f" — {detail}"
        print(msg)


# ============================================================
# 1. MR KERNEL TESTS
# ============================================================

def test_kernel():
    print("\n═══ 1. MR KERNEL ═══")

    config = WorldGridConfig(grid_width=8, grid_height=8, tile_size=16)
    cells = create_empty_grid(config)
    check("empty grid has 64 cells", len(cells) == 64)
    check("all cells start as void",
          all(c["terrain_type"] == "void" for c in cells.values()))

    # Step: fill a region
    snapshot = {"trixel_world": {"cells": cells, "features": {}, "skin_table": {}, "tick": 0.0}}
    deltas = [{
        "id": "d1", "type": "fill_region",
        "payload": {"x_min": 0, "y_min": 0, "x_max": 7, "y_max": 2, "terrain_type": "deep_water"}
    }]
    out, accepted, alerts = step_trixel_world(snapshot, deltas, config)
    check("fill_region accepted", "d1" in accepted)
    check("no alerts", len(alerts) == 0)

    water_cells = get_cells_by_terrain(out["trixel_world"]["cells"], "deep_water")
    check("24 deep_water cells (8×3)", len(water_cells) == 24)

    # Override test
    cid = make_cell_id(3, 1)
    cell = out["trixel_world"]["cells"][cid]
    check("deep_water cell is not walkable", cell["walkable"] == False)

    deltas2 = [{"id": "d2", "type": "add_override", "payload": {"cell_ids": [cid], "tag": "secret_path"}}]
    out2, acc2, _ = step_trixel_world(out, deltas2, config)
    cell2 = out2["trixel_world"]["cells"][cid]
    check("override tag applied", "secret_path" in cell2["override_tags"])
    check("effective walkability with override", resolve_cell_walkability(cell2) == True)

    # Skin swap doesn't touch mechanics
    deltas3 = [{"id": "d3", "type": "set_skin", "payload": {"cell_ids": [cid], "skin_id": "lava_v1"}}]
    out3, acc3, _ = step_trixel_world(out2, deltas3, config)
    cell3 = out3["trixel_world"]["cells"][cid]
    check("skin changed", cell3["skin_id"] == "lava_v1")
    check("terrain unchanged after skin swap", cell3["terrain_type"] == "deep_water")
    check("walkable unchanged after skin swap", cell3["walkable"] == False)

    # Autotile resolution
    role = resolve_autotile_role("sand", {"n": "sand", "s": "sand", "e": "water", "w": "sand"})
    check("autotile: 3 same + 1 diff = edge_e", role == "edge_e")

    role2 = resolve_autotile_role("pier", {"n": None, "s": None, "e": None, "w": None})
    check("autotile: no neighbors = single", role2 == "single")

    # Example beach scene
    beach = build_example_beach()
    stats = compute_grid_statistics(beach["trixel_world"]["cells"])
    check("beach scene has 256 cells", stats["total_cells"] == 256)
    check("beach has features", len(beach["trixel_world"]["features"]) == 3)
    check("beach walkable > 50%", stats["walkable_pct"] > 50)


# ============================================================
# 2. ADAPTER TESTS
# ============================================================

def test_adapter():
    print("\n═══ 2. ADAPTER ═══")

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        tmp_path = f.name

    try:
        adapter = TrixelWorldAdapter(
            save_path=tmp_path,
            config=WorldGridConfig(grid_width=16, grid_height=16),
            autoload=False,
            autosave=True,
        )

        check("config property accessible", adapter.config.grid_width == 16)

        # Fill sand
        resp = adapter.handle_fill_region(0, 6, 15, 10, TerrainType.SAND.value)
        check("fill_region ok", resp["ok"])

        sand = adapter.get_cells_by_terrain(TerrainType.SAND.value)
        check("sand cells created (5 rows × 16 cols = 80)", len(sand) == 80)

        # Register + apply skin
        resp = adapter.handle_register_skin(
            skin_id="beach_v1", terrain_type="sand", module_family="sand_base",
            asset_ref="res://tiles/beach.png", style_tags=["pixel"],
        )
        check("register_skin ok", resp["ok"])

        resp = adapter.handle_set_skin(sand, "beach_v1")
        check("set_skin ok", resp["ok"])

        cell_with_skin = adapter.get_cell_with_skin(sand[0])
        check("cell has resolved skin_binding", cell_with_skin is not None and cell_with_skin.get("skin_binding") is not None)

        # Add feature
        resp = adapter.handle_add_feature(
            feature_id="test_pier", feature_type="pier",
            cell_ids=[make_cell_id(8, 6), make_cell_id(8, 7)],
            narrative_source="test", confidence="explicit",
        )
        check("add_feature ok", resp["ok"])

        # Walkability
        walk = adapter.get_effective_walkability(make_cell_id(8, 6))
        check("sand cell walkable", walk == True)

        # Override
        forest_cid = make_cell_id(5, 0)  # void/default cell
        adapter.handle_fill_region(5, 0, 5, 0, TerrainType.FOREST_EDGE.value)
        walk_before = adapter.get_effective_walkability(forest_cid)
        check("forest_edge not walkable", walk_before == False)

        adapter.handle_add_override([forest_cid], "secret_path")
        walk_after = adapter.get_effective_walkability(forest_cid)
        check("forest_edge walkable after secret_path override", walk_after == True)

        # Persistence
        adapter.save_snapshot()
        check("snapshot file exists", os.path.exists(tmp_path))

        adapter2 = TrixelWorldAdapter(save_path=tmp_path, autoload=True, autosave=False)
        sand2 = adapter2.get_cells_by_terrain(TerrainType.SAND.value)
        check("loaded adapter has same sand count", len(sand2) == len(sand))

        features = adapter2.get_features()
        check("loaded adapter has test_pier feature", "test_pier" in features)

        # AP validation: reject unknown terrain type
        resp = adapter.handle_set_terrain([sand[0]], "unicorn_dust")
        check("reject unknown terrain_type", resp["ok"] == False)

        # AP validation: reject out-of-bounds fill
        resp = adapter.handle_fill_region(0, 0, 999, 0, TerrainType.SAND.value)
        check("reject out-of-bounds region", resp["ok"] == False)

    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


# ============================================================
# 3. SCENE SHELL BUILDER TESTS
# ============================================================

def test_scene_shell_builder():
    print("\n═══ 3. SCENE SHELL BUILDER ═══")

    config = WorldGridConfig(grid_width=16, grid_height=16)

    # Classify
    hints = SceneHints(
        scene_id="test",
        chapter_text="They built pyramids on the sandy shore near a wooden pier.",
        world_tags=["beach"],
    )
    flags = classify_scene(hints)
    check("classified as beach", flags["is_beach"])
    check("classified has_pier", flags["has_pier"])
    check("classified has_construction", flags["has_construction"])

    # Full build
    text = (
        "They were building pyramids on the sand near a tree ridge. "
        "To the north, the sea lapped at a long wooden pier. "
        "Locals whispered of a secret path through the forest edge."
    )
    deltas = build_scene_shell(
        scene_id="scene_001",
        chapter_text=text,
        config=config,
        corpus_hints={"scene_type": "beach"},
        world_tags=["beach", "pier", "secret"],
    )
    check("deltas generated", len(deltas) > 0)

    types = {d["type"] for d in deltas}
    check("has fill_region deltas", "fill_region" in types)
    check("has add_feature deltas", "add_feature" in types)
    check("has add_override deltas", "add_override" in types)

    # All deltas carry scene_id provenance
    all_tagged = all(d.get("payload", {}).get("scene_id") == "scene_001" for d in deltas)
    check("all deltas tagged with scene_id", all_tagged)

    # Deltas should be applicable to adapter without errors
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        tmp_path = f.name
    try:
        adapter = TrixelWorldAdapter(
            save_path=tmp_path, config=config, autoload=False, autosave=False,
        )
        # Apply each delta through the adapter
        errors = []
        for d in deltas:
            did = adapter.queue_delta(d["type"], d["payload"])
            if did is None:
                errors.append(f"Rejected: {d['id']} ({d['type']})")
        accepted, alerts = adapter.flush()
        check(f"all {len(deltas)} deltas queued (errors: {len(errors)})", len(errors) == 0,
              "; ".join(errors))
        check(f"all deltas accepted by kernel", len(accepted) == len(deltas))

        # Verify resulting world
        stats = compute_grid_statistics(adapter.get_cells())
        check("beach has sand cells", stats["terrain_distribution"].get("sand", 0) > 0)
        check("beach has deep_water cells", stats["terrain_distribution"].get("deep_water", 0) > 0)
        check("beach has pier cells", stats["terrain_distribution"].get("pier", 0) > 0)

        features = adapter.get_features()
        check("pier_main feature exists", "pier_main" in features)
        check("secret_path_01 feature exists", "secret_path_01" in features)
        check("pyramid_site_01 feature exists", "pyramid_site_01" in features)

        # Secret path should make forest cells walkable
        secret_cells = features.get("secret_path_01", {}).get("cell_ids", [])
        if secret_cells:
            walk = adapter.get_effective_walkability(secret_cells[0])
            check("secret_path forest cell is walkable", walk == True)
        else:
            check("secret_path has cells", False, "no cells in secret_path_01")

    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def _feature_cells_from_deltas(deltas, feature_id: str):
    for delta in deltas:
        if delta.get("type") != "add_feature":
            continue
        payload = delta.get("payload", {})
        if payload.get("feature_id") == feature_id:
            return payload.get("cell_ids", [])
    return []

def _coords_from_cell_id(cell_id: str):
    parts = cell_id.split("_")
    return int(parts[1]), int(parts[3])


def test_secret_path_relative_placement():
    print("\n═══ 3b. SECRET PATH RELATIVE PLACEMENT ═══")

    config = WorldGridConfig(grid_width=16, grid_height=16)
    snapshot = {
        "trixel_world": {
            "cells": create_empty_grid(config),
            "features": {},
            "skin_table": {},
            "tick": 0.0,
        }
    }

    for x in range(config.grid_width):
        for y in range(config.grid_height):
            cid = make_cell_id(x, y)
            if y <= 2:
                terrain = TerrainType.DEEP_WATER.value
            elif y <= 4:
                terrain = TerrainType.SHALLOW_WATER.value
            elif y == 5:
                terrain = TerrainType.SHORELINE.value
            elif y <= 10:
                terrain = TerrainType.SAND.value
            elif y <= 13:
                terrain = TerrainType.GRASS.value
            elif y <= 15:
                terrain = TerrainType.FOREST_EDGE.value
            else:
                terrain = TerrainType.VOID.value
            snapshot["trixel_world"]["cells"][cid]["terrain_type"] = terrain
            snapshot["trixel_world"]["cells"][cid]["blocker"] = False

    protected_col = config.grid_width // 2
    protected_cells = [make_cell_id(protected_col, 14), make_cell_id(protected_col, 15)]
    for cid in protected_cells:
        snapshot["trixel_world"]["cells"][cid]["feature_ids"] = ("old_gate",)

    text = "Locals whispered of a secret path through the forest edge."

    deltas_a = build_scene_shell(
        scene_id="scene_secret_a",
        chapter_text=text,
        config=config,
        corpus_hints={"scene_type": "beach"},
        world_tags=["beach", "secret"],
        snapshot=snapshot,
    )
    deltas_b = build_scene_shell(
        scene_id="scene_secret_a",
        chapter_text=text,
        config=config,
        corpus_hints={"scene_type": "beach"},
        world_tags=["beach", "secret"],
        snapshot=snapshot,
    )

    secret_a = _feature_cells_from_deltas(deltas_a, "secret_path_01")
    secret_b = _feature_cells_from_deltas(deltas_b, "secret_path_01")

    check("secret path emitted 2 cells", len(secret_a) == 2)
    check("secret path avoids protected center", all(cid not in protected_cells for cid in secret_a))
    check("secret path placement is deterministic", secret_a == secret_b)
    check(
        "secret path stays on forest_edge rows",
        all(cid.endswith("_cy_014") or cid.endswith("_cy_015") for cid in secret_a),
    )


def test_pier_relative_placement():
    print("\n═══ 3c. PIER RELATIVE PLACEMENT ═══")

    config = WorldGridConfig(grid_width=16, grid_height=16)
    snapshot = {
        "trixel_world": {
            "cells": create_empty_grid(config),
            "features": {},
            "skin_table": {},
            "tick": 0.0,
        }
    }

    for x in range(config.grid_width):
        for y in range(config.grid_height):
            cid = make_cell_id(x, y)
            if y <= 2:
                terrain = TerrainType.DEEP_WATER.value
            elif y <= 4:
                terrain = TerrainType.SHALLOW_WATER.value
            elif y == 5:
                terrain = TerrainType.SHORELINE.value
            elif y <= 10:
                terrain = TerrainType.SAND.value
            elif y <= 13:
                terrain = TerrainType.GRASS.value
            elif y <= 15:
                terrain = TerrainType.FOREST_EDGE.value
            else:
                terrain = TerrainType.VOID.value
            snapshot["trixel_world"]["cells"][cid]["terrain_type"] = terrain
            snapshot["trixel_world"]["cells"][cid]["blocker"] = False

    old_center_a = config.grid_width // 2
    old_center_b = min(config.grid_width - 1, old_center_a + 1)
    protected_cells = [
        make_cell_id(x, y)
        for y in range(0, 6)
        for x in (old_center_a, old_center_b)
    ]
    for cid in protected_cells:
        snapshot["trixel_world"]["cells"][cid]["feature_ids"] = ("old_dock",)

    text = "The waves crashed against the old wooden pier as gulls circled overhead."

    deltas_a = build_scene_shell(
        scene_id="scene_pier_a",
        chapter_text=text,
        config=config,
        corpus_hints={"scene_type": "beach"},
        world_tags=["beach", "pier"],
        snapshot=snapshot,
    )
    deltas_b = build_scene_shell(
        scene_id="scene_pier_a",
        chapter_text=text,
        config=config,
        corpus_hints={"scene_type": "beach"},
        world_tags=["beach", "pier"],
        snapshot=snapshot,
    )

    pier_a = _feature_cells_from_deltas(deltas_a, "pier_main")
    pier_b = _feature_cells_from_deltas(deltas_b, "pier_main")
    coords = [_coords_from_cell_id(cid) for cid in pier_a]
    rows = sorted({y for _, y in coords})

    check("pier emitted 12 cells", len(pier_a) == 12)
    check("pier avoids protected center span", all(cid not in protected_cells for cid in pier_a))
    check("pier placement is deterministic", pier_a == pier_b)
    check("pier footprint spans 6 rows into water", rows == [0, 1, 2, 3, 4, 5])
    check("pier touches shoreline and water", (5 in rows) and any(y < 5 for y in rows))


# ============================================================
# 4. ZW ROUTER TESTS
# ============================================================



def test_construction_relative_placement():
    print("\n═══ 3d. CONSTRUCTION RELATIVE PLACEMENT ═══")

    config = WorldGridConfig(grid_width=16, grid_height=16)
    snapshot = {
        "trixel_world": {
            "cells": create_empty_grid(config),
            "features": {},
            "skin_table": {},
            "tick": 0.0,
        }
    }

    for x in range(config.grid_width):
        for y in range(config.grid_height):
            cid = make_cell_id(x, y)
            if y <= 2:
                terrain = TerrainType.DEEP_WATER.value
            elif y <= 4:
                terrain = TerrainType.SHALLOW_WATER.value
            elif y == 5:
                terrain = TerrainType.SHORELINE.value
            elif y <= 10:
                terrain = TerrainType.SAND.value
            elif y <= 13:
                terrain = TerrainType.GRASS.value
            elif y <= 15:
                terrain = TerrainType.FOREST_EDGE.value
            else:
                terrain = TerrainType.VOID.value
            snapshot["trixel_world"]["cells"][cid]["terrain_type"] = terrain
            snapshot["trixel_world"]["cells"][cid]["blocker"] = False

    protected_cells = [make_cell_id(x, y) for y in range(8, 11) for x in range(5, 8)]
    for cid in protected_cells:
        snapshot["trixel_world"]["cells"][cid]["feature_ids"] = ("old_workcamp",)

    text = "Workers hauled stone across the inland sand toward the pyramid construction site."

    deltas_a = build_scene_shell(
        scene_id="scene_construction_a",
        chapter_text=text,
        config=config,
        corpus_hints={"scene_type": "beach"},
        world_tags=["beach", "construction"],
        snapshot=snapshot,
    )
    deltas_b = build_scene_shell(
        scene_id="scene_construction_a",
        chapter_text=text,
        config=config,
        corpus_hints={"scene_type": "beach"},
        world_tags=["beach", "construction"],
        snapshot=snapshot,
    )

    pyramid_a = _feature_cells_from_deltas(deltas_a, "pyramid_site_01")
    pyramid_b = _feature_cells_from_deltas(deltas_b, "pyramid_site_01")
    coords = [_coords_from_cell_id(cid) for cid in pyramid_a]
    xs = sorted({x for x, _ in coords})
    ys = sorted({y for _, y in coords})

    check("pyramid emitted 9 cells", len(pyramid_a) == 9)
    check("pyramid avoids protected cells", all(cid not in protected_cells for cid in pyramid_a))
    check("pyramid placement is deterministic", pyramid_a == pyramid_b)
    check("pyramid footprint is 3×3", len(xs) == 3 and len(ys) == 3)

    shoreline_rows = {
        cell["y"] for cell in snapshot["trixel_world"]["cells"].values()
        if cell["terrain_type"] == TerrainType.SHORELINE.value
    }
    max_shore = max(shoreline_rows) if shoreline_rows else -1
    check(
        "pyramid inland on sand",
        all(
            snapshot["trixel_world"]["cells"][cid]["terrain_type"] == TerrainType.SAND.value
            and snapshot["trixel_world"]["cells"][cid]["y"] > (max_shore + 1)
            for cid in pyramid_a
        ),
    )

def test_zw_router():
    print("\n═══ 4. ZW ROUTER ═══")

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        tmp_path = f.name

    try:
        router = TrixelWorldZWRouter(
            save_path=tmp_path,
            config=WorldGridConfig(grid_width=16, grid_height=16),
        )

        # fill_region via ZW
        resp = router.handle_zw({
            "command": "!zw/world.fill_region",
            "payload": {"x_min": 0, "y_min": 0, "x_max": 15, "y_max": 3, "terrain_type": "deep_water"},
            "meta": {"request_id": "r1"},
        })
        check("ZW fill_region ok", resp["ok"])
        check("request_id preserved", resp["request_id"] == "r1")

        # register_skin via ZW
        resp = router.handle_zw({
            "command": "!zw/world.register_skin",
            "payload": {
                "skin_id": "ocean_v1", "terrain_type": "deep_water",
                "module_family": "water_deep", "asset_ref": "res://tiles/ocean.png",
                "style_tags": ["pixel"],
            },
            "meta": {"request_id": "r2"},
        })
        check("ZW register_skin ok", resp["ok"])

        # get_cells_by_terrain via ZW
        resp = router.handle_zw({
            "command": "!zw/world.get_cells_by_terrain",
            "payload": {"terrain_type": "deep_water"},
            "meta": {"request_id": "r3"},
        })
        check("ZW get_cells_by_terrain ok", resp["ok"])
        cell_ids = resp["result"].get("cell_ids", [])
        check("64 deep_water cells (16×4)", len(cell_ids) == 64)

        # Unknown command
        resp = router.handle_zw({
            "command": "!zw/world.make_coffee",
            "payload": {},
            "meta": {"request_id": "r4"},
        })
        check("unknown command returns ok=False", resp["ok"] == False)

        # build_scene_shell via ZW
        resp = router.handle_zw({
            "command": "!zw/world.build_scene_shell",
            "payload": {
                "scene_id": "zw_beach_001",
                "chapter_text": "The waves crashed against the old wooden pier as workers hauled stones for the pyramid.",
                "corpus_hints": {"scene_type": "beach"},
                "world_tags": ["beach", "pier"],
                "grid_config": {"grid_width": 16, "grid_height": 16, "tile_size": 16},
            },
            "meta": {"request_id": "r5"},
        })
        check("ZW build_scene_shell ok", resp["ok"])
        shell_deltas = resp["result"].get("deltas", [])
        check("scene shell produced deltas", len(shell_deltas) > 0)
        check("scene_id in response", resp["result"].get("scene_id") == "zw_beach_001")

        # build_scene_shell with missing scene_id
        resp = router.handle_zw({
            "command": "!zw/world.build_scene_shell",
            "payload": {"chapter_text": "some text"},
            "meta": {"request_id": "r6"},
        })
        check("build_scene_shell rejects missing scene_id", resp["ok"] == False)

        # build_scene_shell with empty text
        resp = router.handle_zw({
            "command": "!zw/world.build_scene_shell",
            "payload": {"scene_id": "x", "chapter_text": ""},
            "meta": {"request_id": "r7"},
        })
        check("build_scene_shell rejects empty text", resp["ok"] == False)

    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


# ============================================================
# 5. FULL PIPELINE TEST
# ============================================================

def test_full_pipeline():
    print("\n═══ 5. FULL PIPELINE: narrative → ZW → shell → adapter → verify ═══")

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        tmp_path = f.name

    try:
        router = TrixelWorldZWRouter(
            save_path=tmp_path,
            config=WorldGridConfig(grid_width=16, grid_height=16),
        )

        # Step 1: narrative → scene shell via ZW
        narrative = (
            "The ancient beach stretched for miles, golden sand meeting the dark sea. "
            "A weathered pier jutted out over the shallow water, its planks groaning. "
            "Beyond the tree line, a secret path wound through the forest toward the mountains."
        )

        resp = router.handle_zw({
            "command": "!zw/world.build_scene_shell",
            "payload": {
                "scene_id": "ch01_beach",
                "chapter_text": narrative,
                "world_tags": ["beach", "pier", "secret path"],
                "grid_config": {"grid_width": 16, "grid_height": 16, "tile_size": 16},
            },
            "meta": {"request_id": "pipeline_1"},
        })

        check("pipeline: shell built", resp["ok"])
        deltas = resp["result"].get("deltas", [])
        check(f"pipeline: {len(deltas)} deltas generated", len(deltas) > 5)

        # Step 2: apply deltas through the adapter via ZW
        applied_count = 0
        for d in deltas:
            dtype = d["type"]
            payload = d["payload"]
            # Map builder delta types to ZW commands
            cmd_map = {
                "fill_region": "!zw/world.fill_region",
                "add_feature": "!zw/world.add_feature",
                "add_override": "!zw/world.add_override",
                "assign_feature": "!zw/world.assign_feature",
                "set_terrain": "!zw/world.set_terrain",
                "set_skin": "!zw/world.set_skin",
            }
            cmd = cmd_map.get(dtype)
            if cmd:
                r = router.handle_zw({
                    "command": cmd,
                    "payload": payload,
                    "meta": {"request_id": f"apply_{d['id']}"},
                })
                if r["ok"]:
                    applied_count += 1

        check(f"pipeline: {applied_count}/{len(deltas)} deltas applied via ZW", applied_count == len(deltas))

        # Step 3: verify world state
        snap_resp = router.handle_zw({
            "command": "!zw/world.get_snapshot",
            "payload": {},
            "meta": {"request_id": "verify_1"},
        })
        snapshot = snap_resp["result"]["snapshot"]
        world = snapshot["trixel_world"]
        stats = compute_grid_statistics(world["cells"])

        print(f"\n  📊 Final world: {stats['total_cells']} cells")
        print(f"     Walkable: {stats['walkable_cells']} ({stats['walkable_pct']}%)")
        for terrain, count in sorted(stats["terrain_distribution"].items()):
            if count > 0 and terrain != "void":
                print(f"     {terrain:25s} {count:4d}")

        check("world has sand", stats["terrain_distribution"].get("sand", 0) > 0)
        check("world has deep_water", stats["terrain_distribution"].get("deep_water", 0) > 0)
        check("world has pier", stats["terrain_distribution"].get("pier", 0) > 0)
        check("world has forest_edge", stats["terrain_distribution"].get("forest_edge", 0) > 0)

        features = world["features"]
        print(f"\n  🏗️  Features: {len(features)}")
        for fid, feat in features.items():
            print(f"     {fid}: {feat['feature_type']} ({len(feat['cell_ids'])} cells)")

        check("pier_main exists", "pier_main" in features)
        check("secret_path_01 exists", "secret_path_01" in features)

        # Step 4: skin swap test — change all sand to factory, verify mechanics survive
        sand_resp = router.handle_zw({
            "command": "!zw/world.get_cells_by_terrain",
            "payload": {"terrain_type": "sand"},
            "meta": {"request_id": "get_sand"},
        })
        sand_ids = sand_resp["result"]["cell_ids"]

        router.handle_zw({
            "command": "!zw/world.register_skin",
            "payload": {
                "skin_id": "factory_floor_v1", "terrain_type": "sand",
                "module_family": "factory_base", "style_tags": ["industrial"],
            },
            "meta": {"request_id": "reg_factory"},
        })
        router.handle_zw({
            "command": "!zw/world.set_skin",
            "payload": {"cell_ids": sand_ids, "skin_id": "factory_floor_v1"},
            "meta": {"request_id": "skin_factory"},
        })

        # Verify: terrain unchanged, skin changed
        if sand_ids:
            cell_resp = router.handle_zw({
                "command": "!zw/world.get_cell",
                "payload": {"cell_id": sand_ids[0]},
                "meta": {"request_id": "verify_cell"},
            })
            cell = cell_resp["result"]["cell"]
            check("skin swap: terrain still sand", cell["terrain_type"] == "sand")
            check("skin swap: skin is factory", cell["skin_id"] == "factory_floor_v1")
            check("skin swap: still walkable", cell["walkable"] == True)

        # Step 5: verify secret path walkability
        walk_resp = router.handle_zw({
            "command": "!zw/world.get_walkable_cells",
            "payload": {},
            "meta": {"request_id": "walk_check"},
        })
        walkable_ids = walk_resp["result"]["cell_ids"]
        secret_cells = features.get("secret_path_01", {}).get("cell_ids", [])
        if secret_cells:
            secret_walkable = all(cid in walkable_ids for cid in secret_cells)
            check("secret path cells are walkable", secret_walkable)

        print(f"\n  🌊 World built from narrative: {len(deltas)} deltas, "
              f"{stats['walkable_pct']}% walkable, "
              f"{len(features)} features, "
              f"skin swap preserved mechanics")

    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print("=" * 64)
    print("TRIXEL WORLD SUBSYSTEM — Full Stack Integration Test")
    print("=" * 64)

    test_kernel()
    test_adapter()
    test_scene_shell_builder()
    test_secret_path_relative_placement()
    test_pier_relative_placement()
    test_construction_relative_placement()
    test_zw_router()
    test_full_pipeline()

    print("\n" + "=" * 64)
    total = PASS + FAIL
    print(f"RESULTS: {PASS}/{total} passed, {FAIL} failed")
    if FAIL == 0:
        print("ALL TESTS PASSED ✅")
    else:
        print(f"{FAIL} FAILURES ❌")
    print("=" * 64)
