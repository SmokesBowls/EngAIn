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


def _new_material_principled(
    name: str,
    base_color_rgba: Tuple[float, float, float, float],
    metallic: float,
    roughness: float,
) -> bpy.types.Material:
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


def _unlink_from_scene_root(obj: bpy.types.Object) -> None:
    root = bpy.context.scene.collection
    if obj.name in root.objects:
        root.objects.unlink(obj)


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


def _create_torus(name: str, major_radius: float, minor_radius: float, location: Tuple[float, float, float]) -> bpy.types.Object:
    bpy.ops.mesh.primitive_torus_add(
        major_segments=96,
        minor_segments=16,
        major_radius=major_radius,
        minor_radius=minor_radius,
        location=location,
    )
    obj = bpy.context.active_object
    obj.name = name
    return obj


def _create_nexus_core(name: str, radius: float, location: Tuple[float, float, float]) -> bpy.types.Object:
    bpy.ops.mesh.primitive_ico_sphere_add(
        subdivisions=3,
        radius=radius,
        location=location,
    )
    obj = bpy.context.active_object
    obj.name = name
    return obj


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

        nexus_core_enabled = bool(params.get("nexus_core_enabled", False))
        ring_count = max(0, int(params.get("ring_count", 0)))
        damage_state = str(params.get("damage_state", "intact")).strip().lower()

        save_as = params.get("save_as")
        save_as = str(save_as) if save_as else None
    except Exception as exc:
        fail(result_json, f"Bad params: {exc}")
        return

    if height_m <= 0:
        fail(result_json, "height_m must be > 0")
        return

    if damage_state not in {"intact", "weathered", "damaged", "ruined"}:
        fail(result_json, f"Unsupported damage_state: {damage_state!r}")
        return

    effective_height_m = height_m
    tip_enabled = True

    if damage_state == "weathered":
        effective_height_m *= 0.98
    elif damage_state == "damaged":
        effective_height_m *= 0.85
    elif damage_state == "ruined":
        effective_height_m *= 0.60
        tip_enabled = False

    col = _ensure_collection(collection_name)

    mat_stone = _new_material_principled("M_StarNeedle_Stone", (0.10, 0.10, 0.12, 1.0), metallic=0.0, roughness=0.85)
    mat_metal = _new_material_principled("M_StarNeedle_StarMetal", (0.9, 0.78, 0.35, 1.0), metallic=1.0, roughness=0.22)
    mat_ring = _new_material_principled("M_StarNeedle_RingMetal", (0.45, 0.50, 0.60, 1.0), metallic=1.0, roughness=0.30)
    mat_core = _new_material_principled("M_StarNeedle_NexusCore", (0.25, 0.60, 1.0, 1.0), metallic=0.0, roughness=0.12)

    base_depth = max(1.2, effective_height_m * 0.06)
    collar_depth = max(0.8, effective_height_m * 0.04)
    actual_tip_height = tip_height_m if tip_enabled else 0.0
    shaft_depth = max(0.0, effective_height_m - base_depth - collar_depth - actual_tip_height)

    if shaft_depth <= 0.5:
        fail(result_json, "Not enough height for shaft after base/collar/tip. Increase height_m.")
        return

    z0 = 0.0

    base = _create_cone("SN_Base", base_radius_m, base_radius_m, base_depth, verts=96)
    base.location = (0.0, 0.0, z0 + base_depth * 0.5)

    collar = _create_cone("SN_Collar", collar_radius_m, collar_radius_m, collar_depth, verts=96)
    collar.location = (0.0, 0.0, z0 + base_depth + collar_depth * 0.5)

    shaft_top_radius = shaft_radius_top_m
    if not tip_enabled:
        shaft_top_radius = max(shaft_radius_top_m * 2.8, 0.35)

    shaft = _create_cone("SN_Shaft", shaft_radius_base_m, shaft_top_radius, shaft_depth, verts=128)
    shaft.location = (0.0, 0.0, z0 + base_depth + collar_depth + shaft_depth * 0.5)

    tip = None
    if tip_enabled:
        tip = _create_cone("SN_Tip", max(shaft_radius_top_m * 1.2, 0.05), 0.0, actual_tip_height, verts=64)
        tip.location = (0.0, 0.0, z0 + base_depth + collar_depth + shaft_depth + actual_tip_height * 0.5)

    for obj in (base, collar, shaft):
        _link_object(obj, col)
        _assign_material(obj, mat_stone)

    if tip is not None:
        _link_object(tip, col)
        _assign_material(tip, mat_stone)

    created_stars: List[str] = []
    if star_count > 0:
        shaft_bottom_z = z0 + base_depth + collar_depth
        for i in range(star_count):
            t = (i + 1) / (star_count + 1)
            z = shaft_bottom_z + shaft_depth * t
            r_at = (shaft_radius_base_m * (1.0 - t)) + (shaft_top_radius * t)

            star = _create_star_plaque(f"SN_Star_{i+1:02d}", star_outer_radius_m, star_inner_radius_m, star_thickness_m)
            star.rotation_euler = (math.radians(90.0), 0.0, math.radians(18.0 * i))
            star.location = (r_at + star_inset_m, 0.0, z)

            _link_object(star, col)
            _assign_material(star, mat_metal)
            created_stars.append(star.name)

    created_rings: List[str] = []
    if ring_count > 0:
        shaft_bottom_z = z0 + base_depth + collar_depth
        ring_radius = max(base_radius_m * 0.72, shaft_radius_base_m * 1.5)
        ring_thickness = max(base_radius_m * 0.025, 0.05)

        for i in range(ring_count):
            t = (i + 1) / (ring_count + 1)
            z = shaft_bottom_z + shaft_depth * t
            ring = _create_torus(f"SN_Ring_{i+1:02d}", ring_radius, ring_thickness, (0.0, 0.0, z))
            _link_object(ring, col)
            _unlink_from_scene_root(ring)
            _assign_material(ring, mat_ring)
            created_rings.append(ring.name)

    nexus_core_name = None
    if nexus_core_enabled:
        core_radius = max(base_radius_m * 0.35, 0.35)
        core = _create_nexus_core("SN_NexusCore", core_radius, (0.0, 0.0, base_depth * 0.5))
        _link_object(core, col)
        _unlink_from_scene_root(core)
        _assign_material(core, mat_core)
        nexus_core_name = core.name

    bpy.context.view_layer.update()

    try:
        saved_path = _save_or_fail(result_json, save_as)
    except Exception:
        return

    ok(
        result_json,
        result={
            "collection": collection_name,
            "damage_state": damage_state,
            "effective_height_m": effective_height_m,
            "objects": {
                "base": base.name,
                "collar": collar.name,
                "shaft": shaft.name,
                "tip": tip.name if tip is not None else None,
                "stars": created_stars,
                "rings": created_rings,
                "nexus_core": nexus_core_name,
            },
            "saved_blend": saved_path,
        },
    )


main()
