from __future__ import annotations

import math
from pathlib import Path
from typing import Optional, Tuple

import bpy
from mathutils import Vector

from _common import load_params, ok, fail


def _ensure_collection(name: str) -> bpy.types.Collection:
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    return col


def _kelvin_to_rgb(k: int) -> Tuple[float, float, float]:
    temp = max(1000, min(40000, int(k))) / 100.0
    if temp <= 66:
        r = 1.0
        g = max(0.0, min(1.0, (99.4708025861 * math.log(temp) - 161.1195681661) / 255.0))
        b = 0.0 if temp <= 19 else max(0.0, min(1.0, (138.5177312231 * math.log(temp - 10) - 305.0447927307) / 255.0))
    else:
        r = max(0.0, min(1.0, (329.698727446 * ((temp - 60) ** -0.1332047592)) / 255.0))
        g = max(0.0, min(1.0, (288.1221695283 * ((temp - 60) ** -0.0755148492)) / 255.0))
        b = 1.0
    return (r, g, b)


def _create_area_light(name: str, location: Vector, rotation: Vector, energy: float, color: Tuple[float, float, float], size: float, cast_shadows: bool) -> bpy.types.Object:
    data = bpy.data.lights.new(name=name, type="AREA")
    data.energy = float(energy)
    data.color = color
    data.use_shadow = bool(cast_shadows)
    data.shadow_soft_size = 0.25
    data.size = float(size)
    obj = bpy.data.objects.new(name, data)
    obj.location = location
    obj.rotation_euler = rotation
    return obj


def _save_or_fail(result_json: Path) -> None:
    try:
        bpy.ops.wm.save_mainfile()
    except Exception as exc:
        fail(result_json, f"Failed to save .blend: {exc}")
        raise


def main() -> None:
    params, _meta, result_json = load_params()

    rig_type = str(params.get("rig_type", "three_point"))
    if rig_type != "three_point":
        fail(result_json, f"Only rig_type='three_point' is implemented in this starter pack (got {rig_type!r}).")
        return

    target_object: Optional[str] = params.get("target_object")
    rig_scale = float(params.get("rig_scale", 1.0))
    key_energy = float(params.get("key_light_energy", 1200.0))
    fill_ratio = float(params.get("fill_ratio", 0.35))
    rim_ratio = float(params.get("rim_ratio", 0.6))
    kelvin = int(params.get("color_temperature_k", 5500))
    cast_shadows = bool(params.get("cast_shadows", True))
    collection_name = str(params.get("collection_name", "Lighting_Rig"))

    col = _ensure_collection(collection_name)
    scene = bpy.context.scene

    target = Vector((0.0, 0.0, 0.0))
    if target_object and target_object in bpy.data.objects:
        target = bpy.data.objects[target_object].matrix_world.translation

    s = max(0.1, rig_scale)
    key_loc = target + Vector((6.0 * s, -6.0 * s, 10.0 * s))
    fill_loc = target + Vector((-6.0 * s, -6.0 * s, 7.0 * s))
    rim_loc = target + Vector((0.0, 8.0 * s, 10.0 * s))

    color = _kelvin_to_rgb(kelvin)

    def look_at(loc: Vector) -> Vector:
        direction = (target - loc).normalized()
        quat = direction.to_track_quat("-Z", "Y")
        return quat.to_euler()

    key = _create_area_light("Key", key_loc, look_at(key_loc), key_energy, color, size=3.5 * s, cast_shadows=cast_shadows)
    fill = _create_area_light("Fill", fill_loc, look_at(fill_loc), key_energy * fill_ratio, color, size=5.0 * s, cast_shadows=False)
    rim = _create_area_light("Rim", rim_loc, look_at(rim_loc), key_energy * rim_ratio, color, size=2.5 * s, cast_shadows=cast_shadows)

    for l in (key, fill, rim):
        if l.name not in col.objects:
            col.objects.link(l)
        if l.name in scene.collection.objects:
            scene.collection.objects.unlink(l)

    try:
        _save_or_fail(result_json)
    except Exception:
        return

    ok(result_json, result={"collection": collection_name, "lights": [key.name, fill.name, rim.name]})


main()
