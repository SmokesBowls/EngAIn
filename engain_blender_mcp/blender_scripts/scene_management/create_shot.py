from __future__ import annotations

from pathlib import Path

import bpy

from _common import load_params, ok, fail


def main() -> None:
    params, _meta, result_json = load_params()

    out_blend = params.get("out_blend")
    if not out_blend:
        fail(result_json, "Missing required param: out_blend")
        return

    scene = bpy.context.scene
    scene.name = str(params.get("scene_name", "Shot_001"))

    # Clear objects
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)

    # Frame/rate
    scene.frame_start = int(params.get("frame_start", 1))
    scene.frame_end = int(params.get("frame_end", 240))
    scene.render.fps = int(float(params.get("fps", 24.0)))

    # Resolution
    scene.render.resolution_x = int(params.get("resolution_x", 1920))
    scene.render.resolution_y = int(params.get("resolution_y", 1080))
    scene.render.resolution_percentage = 100

    # Engine
    engine = str(params.get("render_engine", "CYCLES"))
    scene.render.engine = engine

    # Output base (directory or file prefix)
    output_path = str(params.get("output_path", "/tmp/render/"))
    Path(output_path).expanduser().resolve().mkdir(parents=True, exist_ok=True)
    scene.render.filepath = output_path

    # Camera
    camera_name = str(params.get("camera_name", "Camera_Main"))
    cam_data = bpy.data.cameras.new(camera_name)
    cam_obj = bpy.data.objects.new(camera_name, cam_data)
    scene.collection.objects.link(cam_obj)
    cam_obj.location = (0.0, -20.0, 8.0)
    cam_obj.rotation_euler = (1.309, 0.0, 0.0)  # ~75deg in radians
    scene.camera = cam_obj

    # Save
    out_path = Path(out_blend).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        bpy.ops.wm.save_as_mainfile(filepath=str(out_path))
    except Exception as exc:
        fail(result_json, f"Failed to save .blend: {exc}")
        return

    ok(result_json, result={"out_blend": str(out_path), "scene": scene.name, "camera": camera_name})


main()
