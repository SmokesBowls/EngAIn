from __future__ import annotations

import math
from pathlib import Path
from typing import Optional

import bpy

from _common import load_params, ok, fail


def _ensure_collection(name: str) -> bpy.types.Collection:
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    return col


def _save_or_fail(result_json: Path) -> None:
    try:
        bpy.ops.wm.save_mainfile()
    except Exception as exc:
        fail(result_json, f"Failed to save .blend: {exc}")
        raise


def main() -> None:
    params, _meta, result_json = load_params()

    scene = bpy.context.scene

    camera_name = str(params.get("camera_name", "Camera"))
    location = params.get("location") or [0.0, -10.0, 2.0]
    rotation_euler_deg = params.get("rotation_euler_deg") or [85.0, 0.0, 0.0]
    lens_mm = float(params.get("lens_mm", 50.0))
    sensor_width_mm = float(params.get("sensor_width_mm", 36.0))
    clip_start = float(params.get("clip_start", 0.1))
    clip_end = float(params.get("clip_end", 1000.0))
    camera_type = str(params.get("camera_type", "PERSP"))
    ortho_scale = float(params.get("ortho_scale", 10.0))
    set_active = bool(params.get("set_active", True))
    collection: Optional[str] = params.get("collection")

    cam_data = bpy.data.cameras.new(camera_name)
    cam_data.type = camera_type
    cam_data.lens = lens_mm
    cam_data.sensor_width = sensor_width_mm
    cam_data.clip_start = clip_start
    cam_data.clip_end = clip_end
    if camera_type == "ORTHO":
        cam_data.ortho_scale = ortho_scale

    cam_obj = bpy.data.objects.new(camera_name, cam_data)

    if collection:
        col = _ensure_collection(str(collection))
        col.objects.link(cam_obj)
    else:
        scene.collection.objects.link(cam_obj)

    cam_obj.location = (float(location[0]), float(location[1]), float(location[2]))
    cam_obj.rotation_euler = (
        math.radians(float(rotation_euler_deg[0])),
        math.radians(float(rotation_euler_deg[1])),
        math.radians(float(rotation_euler_deg[2])),
    )

    if set_active:
        scene.camera = cam_obj

    try:
        _save_or_fail(result_json)
    except Exception:
        return

    ok(result_json, result={"camera": cam_obj.name, "active": set_active})


main()
