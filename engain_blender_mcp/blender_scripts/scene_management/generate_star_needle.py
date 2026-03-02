from __future__ import annotations

import math
from pathlib import Path
from typing import List, Tuple

import bpy
import bmesh
from mathutils import Vector

from _common import load_params, ok, fail


def _ensure_collection(name: str) -> bpy.types.Collection:
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    return col


def _new_material_principled(name: str, base_color_rgba: Tuple[float, float, float, float], metallic: float, roughness: float) -> bpy.types.Material:
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nt = mat.node_tree
    if not nt:
        return mat
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (300, 0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (0, 0)
    bsdf.inputs["Base Color"].default_value = base_color_rgba
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def _link_object(obj: bpy.types.Object, col: bpy.types.Collection) -> None:
    if obj.name not in col.objects:
        col.objects.link(obj)


def _mesh_object_from_bmesh(name: str, bm: bmesh.types.BMesh) -> bpy.types.Object:
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return bpy.data.objects.new(name, me)


def _create_cone(name: str, radius1: float, radius2: float, depth: float, verts: int = 64) -> bpy.types.Object:
    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=False,
        segments=verts,
        radius1=radius1,
        radius2=radius2,
        depth=depth,
    )
    return _mesh_object_from_bmesh(name, bm)


def _create_star_plaque(name: str, outer_r: float, inner_r: float, thickness: float) -> bpy.types.Object:
    bm = bmesh.new()

    pts: List[Vector] = []
    for i in range(10):
        ang = (math.pi * 2.0) * (i / 10.0)
        r = outer_r if (i % 2 == 0) else inner_r
        pts.append(Vector((math.cos(ang) * r, math.sin(ang) * r, 0.0)))

    verts = [bm.verts.new(p) for p in pts]
    bm.faces.new(verts)

    bm.faces.ensure_lookup_table()
    face = bm.faces[0]
    res = bmesh.ops.extrude_face_region(bm, geom=[face])
    verts_extr = [g for g in res["geom"] if isinstance(g, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, verts=verts_extr, vec=Vector((0.0, 0.0, thickness)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    return _mesh_object_from_bmesh(name, bm)


def _assign_material(obj: bpy.types.Object, mat: bpy.types.Material) -> None:
    if obj.type != "MESH":
        return
    if not obj.data.materials:
        obj.data.materials.append(mat)
    else:
        obj.data.materials[0] = mat


def _save_or_fail(result_json: Path, save_as: str | None) -> str:
    try:
        if save_as:
            out_path = Path(save_as).expanduser().resolve()
            out_path.parent.mkdir(parents=True, exist_ok=True)
            bpy.ops.wm.save_as_mainfile(filepath=str(out_path))
            return str(out_path)
        bpy.ops.wm.save_mainfile()
        return str(Path(bpy.data.filepath).resolve())
    except Exception as exc:
        fail(result_json, f"Failed to save .blend: {exc}")
        raise


def main() -> None:
    params, _meta, result_json = load_params()

    try:
        collection_name = str(params.get("collection_name", "StarNeedle"))
        height_m = float(params.get("height_m", 60.0))
        base_radius_m = float(params.get("base_radius_m", 6.0))
        collar_radius_m = float(params.get("collar_radius_m", 4.5))
        shaft_radius_base_m = float(params.get("shaft_radius_base_m", 1.0))
        shaft_radius_top_m = float(params.get("shaft_radius_top_m", 0.15))
        tip_height_m = float(params.get("tip_height_m", 3.0))

        star_count = int(params.get("star_count", 6))
        star_outer_radius_m = float(params.get("star_outer_radius_m", 0.6))
        star_inner_radius_m = float(params.get("star_inner_radius_m", 0.25))
        star_thickness_m = float(params.get("star_thickness_m", 0.08))
        star_inset_m = float(params.get("star_inset_m", 0.02))

        save_as = params.get("save_as")
        save_as = str(save_as) if save_as else None
    except Exception as exc:
        fail(result_json, f"Bad params: {exc}")
        return

    if height_m <= 0:
        fail(result_json, "height_m must be > 0")
        return

    col = _ensure_collection(collection_name)

    mat_stone = _new_material_principled("M_StarNeedle_Stone", (0.10, 0.10, 0.12, 1.0), metallic=0.0, roughness=0.85)
    mat_metal = _new_material_principled("M_StarNeedle_StarMetal", (0.9, 0.78, 0.35, 1.0), metallic=1.0, roughness=0.22)

    base_depth = max(1.2, height_m * 0.06)
    collar_depth = max(0.8, height_m * 0.04)
    shaft_depth = max(0.0, height_m - base_depth - collar_depth - tip_height_m)
    if shaft_depth <= 0.5:
        fail(result_json, "Not enough height for shaft after base/collar/tip. Increase height_m.")
        return

    z0 = 0.0
    base = _create_cone("SN_Base", base_radius_m, base_radius_m, base_depth, verts=96)
    base.location = (0.0, 0.0, z0 + base_depth * 0.5)

    collar = _create_cone("SN_Collar", collar_radius_m, collar_radius_m, collar_depth, verts=96)
    collar.location = (0.0, 0.0, z0 + base_depth + collar_depth * 0.5)

    shaft = _create_cone("SN_Shaft", shaft_radius_base_m, shaft_radius_top_m, shaft_depth, verts=128)
    shaft.location = (0.0, 0.0, z0 + base_depth + collar_depth + shaft_depth * 0.5)

    tip = _create_cone("SN_Tip", max(shaft_radius_top_m * 1.2, 0.05), 0.0, tip_height_m, verts=64)
    tip.location = (0.0, 0.0, z0 + base_depth + collar_depth + shaft_depth + tip_height_m * 0.5)

    for obj in (base, collar, shaft, tip):
        _link_object(obj, col)
        _assign_material(obj, mat_stone)
        obj.data.use_auto_smooth = True
        obj.data.auto_smooth_angle = math.radians(60.0)

    created_stars: List[str] = []
    if star_count > 0:
        shaft_bottom_z = z0 + base_depth + collar_depth
        for i in range(star_count):
            t = (i + 1) / (star_count + 1)
            z = shaft_bottom_z + shaft_depth * t
            r_at = (shaft_radius_base_m * (1.0 - t)) + (shaft_radius_top_m * t)

            star = _create_star_plaque(f"SN_Star_{i+1:02d}", star_outer_radius_m, star_inner_radius_m, star_thickness_m)
            star.rotation_euler = (math.radians(90.0), 0.0, math.radians(18.0 * i))
            star.location = (r_at + star_inset_m, 0.0, z)

            _link_object(star, col)
            _assign_material(star, mat_metal)
            star.data.use_auto_smooth = True
            star.data.auto_smooth_angle = math.radians(60.0)
            created_stars.append(star.name)

    bpy.context.view_layer.update()

    try:
        saved_path = _save_or_fail(result_json, save_as)
    except Exception:
        return

    ok(
        result_json,
        result={
            "collection": collection_name,
            "objects": {"base": base.name, "collar": collar.name, "shaft": shaft.name, "tip": tip.name, "stars": created_stars},
            "saved_blend": saved_path,
        },
    )


main()
