# engain_blender_mcp/blender_scripts/render_still.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional


def run(params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
    import bpy  # type: ignore

    out_png = params.get("out_png")
    if not out_png or not isinstance(out_png, str):
        raise ValueError("params.out_png (string) is required")

    frame = int(params.get("frame", 1))
    camera_name: Optional[str] = params.get("camera_name")

    scene = bpy.context.scene
    scene.frame_set(frame)

    if camera_name:
        cam_obj = bpy.data.objects.get(camera_name)
        if cam_obj is None:
            raise FileNotFoundError(f"Camera not found: {camera_name}")
        scene.camera = cam_obj

    out_path = Path(out_png).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(out_path)

    bpy.ops.render.render(write_still=True)

    return {
        "out_png": str(out_path),
        "frame": frame,
        "camera": scene.camera.name if scene.camera else None,
    }

