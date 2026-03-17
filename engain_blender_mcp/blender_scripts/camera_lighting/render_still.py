from __future__ import annotations

from pathlib import Path
from typing import Optional

import bpy

from _common import load_params, ok, fail


def _safe_set(obj, attr: str, value) -> None:
    if hasattr(obj, attr):
        setattr(obj, attr, value)


def main() -> None:
    params, _meta, result_json = load_params()

    out_png = params.get("out_png")
    if not out_png:
        fail(result_json, "Missing required param: out_png")
        return

    frame = int(params.get("frame", 1))
    camera_name: Optional[str] = params.get("camera_name")

    scene = bpy.context.scene

    if params.get("render_engine"):
        scene.render.engine = str(params["render_engine"])

    # Resolution & sampling
    scene.render.resolution_x = int(params.get("resolution_x", scene.render.resolution_x))
    scene.render.resolution_y = int(params.get("resolution_y", scene.render.resolution_y))
    scene.render.resolution_percentage = int(params.get("resolution_percent", scene.render.resolution_percentage))

    samples = int(params.get("samples", 128))
    if hasattr(scene, "cycles"):
        scene.cycles.samples = samples

    use_denoising = bool(params.get("use_denoising", True))
    denoiser = str(params.get("denoiser", "OPENIMAGEDENOISE"))

    # Try both Scene and ViewLayer denoise flags (varies by Blender version)
    if hasattr(scene, "cycles"):
        _safe_set(scene.cycles, "use_denoising", use_denoising)
        _safe_set(scene.cycles, "denoiser", denoiser)
    for vl in scene.view_layers:
        if hasattr(vl, "cycles"):
            _safe_set(vl.cycles, "use_denoising", use_denoising)

    # Camera
    if camera_name:
        cam_obj = bpy.data.objects.get(str(camera_name))
        if not cam_obj or cam_obj.type != "CAMERA":
            fail(result_json, f"camera_name not found or not a camera: {camera_name}")
            return
        scene.camera = cam_obj
    if scene.camera is None:
        fail(result_json, "No active camera in scene")
        return

    # Output setup
    out_path = Path(out_png).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    file_format = str(params.get("file_format", "PNG"))
    color_depth = str(params.get("color_depth", "16"))
    scene.render.image_settings.file_format = file_format
    scene.render.image_settings.color_depth = color_depth
    scene.render.film_transparent = bool(params.get("use_transparent_bg", False))

    # Blender uses scene.render.filepath as a prefix; giving a full filename works for still renders.
    scene.render.filepath = str(out_path)

    scene.frame_set(frame)

    try:
        bpy.ops.render.render(write_still=True)
    except Exception as exc:
        fail(result_json, f"Render failed: {exc}")
        return

    ok(result_json, result={"out": str(out_path), "frame": frame, "engine": scene.render.engine})


main()
