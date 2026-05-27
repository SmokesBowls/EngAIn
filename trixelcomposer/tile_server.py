"""
tile_server.py — Trixel Compositor HTTP Server

Serves rendered terrain tiles from trixelcomposer to Godot (or any HTTP client).
Runs on port 8766, separate from godotengain (8765) and EngAInOS (8080).

Start:
    python3 tile_server.py
    python3 tile_server.py --port 8766 --host 0.0.0.0

Godot autoload: TrixelTileClient.gd points to this server.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse

_HERE = Path(__file__).parent.resolve()
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from trixel_render_bridge import compile_scene, render_scene, DEFAULT_TILE_DIR  # noqa: E402
from atlas_composer import compose_atlas, list_terrain_types, read_atlas_meta  # noqa: E402

app = FastAPI(title="Trixel Compositor Tile Server", version="1.0.0")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "tile_dir": DEFAULT_TILE_DIR}


@app.get("/tile")
async def tile(
    scene_id:      str           = Query(...,       description="Scene identifier"),
    terrain:       str           = Query("default", description="Terrain type (volcano, beach, forest …)"),
    environment:   str           = Query("unknown", description="Biome context"),
    terrain_family: Optional[str] = Query(None,     description="Alias for terrain (godotengain compat)"),
) -> dict:
    """Render a terrain tile and return output paths.

    Response:
        {
          "scene_id":     str,
          "png":          str,        # absolute filesystem path — load with Image.load_from_file()
          "entity_layer": str | null, # path to entity JSON sidecar
          "recipe":       dict,       # compiled recipe
          "out_dir":      str,
        }
    """
    scene_data = {
        "terrain":     terrain_family or terrain,
        "environment": environment,
        "entities":    [],
    }
    try:
        result = render_scene(scene_id, scene_data)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return result


@app.get("/compile")
async def compile(
    scene_id:    str = Query(...),
    terrain:     str = Query("default"),
    environment: str = Query("unknown"),
) -> dict:
    """Compile recipe only — no PNG render."""
    scene_data = {"terrain": terrain, "environment": environment, "entities": []}
    try:
        recipe = compile_scene(scene_id, scene_data)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return recipe


@app.get("/atlas")
async def atlas(
    terrain:     str = Query(...,       description="Terrain type (shoreline, sand, grass, …)"),
    environment: str = Query("unknown", description="Biome context"),
    seed:        int = Query(42,        description="Base RNG seed for tile variation"),
) -> dict:
    """Generate (or cache-hit) a semantic replacement atlas PNG.

    The output has the same UV layout as the original atlas_meta.json so it
    can be used as a drop-in albedo_texture in SemanticRenderer._load_atlas_for().

    Response:
        {
          "terrain":  str,
          "png":      str,        # absolute filesystem path — load with Image.load_from_file()
          "meta":     dict,       # atlas_meta.json content (tile_order, columns, tile_w, tile_h)
        }
    """
    try:
        meta = read_atlas_meta(terrain)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    try:
        out_path = compose_atlas(terrain, environment=environment, seed=seed)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return {"terrain": terrain, "png": str(out_path), "meta": meta}


@app.get("/atlas/list")
async def atlas_list() -> dict:
    """List terrain types that have atlas_meta.json in TRIXEL_ASSETS_ROOT."""
    return {"terrain_types": list_terrain_types()}


@app.get("/tile.png")
async def tile_png(
    path: str = Query(..., description="Absolute path to PNG (as returned by /tile)"),
) -> FileResponse:
    """Serve a PNG by absolute filesystem path — only needed when Godot can't access the filesystem directly."""
    p = Path(path)
    if not p.exists() or not p.is_file():
        raise HTTPException(status_code=404, detail=f"PNG not found: {path}")
    return FileResponse(str(p), media_type="image/png")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Trixel tile server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8766)
    args = parser.parse_args()
    uvicorn.run(app, host=args.host, port=args.port)
