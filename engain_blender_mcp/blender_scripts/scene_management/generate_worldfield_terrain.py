"""
generate_worldfield_terrain.py
Dumb geometry builder for WorldField terrain.
Invariant: This script owns geometry and visual mapping ONLY. 
It does not own terrain truth or biome meaning.
"""
from __future__ import annotations
from pathlib import Path
from typing import List, Optional
import bpy
import bmesh
from _common import load_params, ok, fail

# Dumb visual mapping: ID -> RGB. The generator doesn't know what "grass" is.
BIOME_COLORS = {
    0: (0.10, 0.20, 0.50, 1.0),  # deep_water
    1: (0.20, 0.50, 0.70, 1.0),  # shallow_water
    2: (0.80, 0.75, 0.50, 1.0),  # shoreline
    3: (0.30, 0.50, 0.30, 1.0),  # marsh
    4: (0.90, 0.80, 0.50, 1.0),  # desert
    5: (0.30, 0.70, 0.20, 1.0),  # grass
    6: (0.10, 0.40, 0.10, 1.0),  # forest
    7: (0.50, 0.50, 0.50, 1.0),  # mountain
    8: (0.95, 0.95, 0.95, 1.0),  # snow
}

def _ensure_collection(name: str) -> bpy.types.Collection:
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    return col

def _center_object_on_world_origin(obj: bpy.types.Object) -> None:
    """Move object origin to mesh bounds center, then snap that origin to world 0,0,0."""
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    obj.location = (0.0, 0.0, 0.0)
    obj.select_set(False)

def _build_terrain_mesh(
    grid_width: int, grid_height: int, height_values: List[float], 
    cell_size_m: float, max_height_m: float, biome_ids: Optional[List[int]] = None
) -> bpy.types.Object:
    expected = grid_width * grid_height
    if len(height_values) < expected:
        raise ValueError(f"height_values too short: expected {expected}, got {len(height_values)}")

    bm = bmesh.new()
    verts = []
    
    # Create vertices
    for y in range(grid_height):
        for x in range(grid_width):
            idx = y * grid_width + x
            normalized_height = max(0.0, min(1.0, float(height_values[idx])))
            h = normalized_height * max_height_m
            v = bm.verts.new((x * cell_size_m, y * cell_size_m, h))
            verts.append(v)
    bm.verts.ensure_lookup_table()

    # Create faces
    faces = []
    for y in range(grid_height - 1):
        for x in range(grid_width - 1):
            i00 = y * grid_width + x
            i10 = y * grid_width + (x + 1)
            i01 = (y + 1) * grid_width + x
            i11 = (y + 1) * grid_width + (x + 1)
            faces.append(bm.faces.new([verts[i00], verts[i10], verts[i11], verts[i01]]))
    bm.faces.ensure_lookup_table()
    bmesh.ops.recalc_face_normals(bm, faces=faces)

    me = bpy.data.meshes.new("WF_Terrain")
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new("WF_Terrain", me)
    
    # Apply Vertex Colors if biome_ids provided
    if biome_ids and len(biome_ids) >= expected:
        color_attr = me.attributes.new(name="BiomeColor", type='FLOAT_COLOR', domain='POINT')
        for i in range(expected):
            color_id = int(biome_ids[i])
            color_attr.data[i].color = BIOME_COLORS.get(color_id, (1.0, 0.0, 1.0, 1.0)) # Magenta fallback
            
    return obj

def main() -> None:
    params, _meta, result_json = load_params()
    try:
        grid_width = int(params.get("grid_width", 32))
        grid_height = int(params.get("grid_height", 32))
        cell_size_m = float(params.get("cell_size_m", 2.0))
        max_height_m = float(params.get("max_height_m", 8.0))
        height_values = list(params.get("height_values", []))
        biome_ids = params.get("biome_ids") # Optional list of ints
        collection_name = str(params.get("collection_name", "WorldFieldTerrain"))
        save_as = params.get("save_as")
        save_as = str(save_as) if save_as else None
    except Exception as exc:
        fail(result_json, f"Bad params: {exc}")
        return

    try:
        col = _ensure_collection(collection_name)
        terrain_obj = _build_terrain_mesh(grid_width, grid_height, height_values, cell_size_m, max_height_m, biome_ids)
        col.objects.link(terrain_obj)
        bpy.context.view_layer.update()
        _center_object_on_world_origin(terrain_obj)
        bpy.context.view_layer.update()

        if save_as:
            out_path = Path(save_as).expanduser().resolve()
            out_path.parent.mkdir(parents=True, exist_ok=True)
            bpy.ops.wm.save_as_mainfile(filepath=str(out_path))
            saved_path = str(out_path)
        else:
            bpy.ops.wm.save_mainfile()
            saved_path = str(Path(bpy.data.filepath).resolve())

        ok(result_json, result={
            "collection": collection_name,
            "mesh_object": terrain_obj.name,
            "vertex_count": grid_width * grid_height,
            "biome_colors_applied": bool(biome_ids),
            "saved_blend": saved_path,
        })
    except Exception as exc:
        fail(result_json, f"Terrain generation failed: {exc}")
        raise

main()