# engain_blender_mcp/blender_scripts/list_objects.py
from __future__ import annotations

from typing import Any, Dict, List


def run(params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
    import bpy  # type: ignore

    objs: List[Dict[str, Any]] = []
    for obj in bpy.data.objects:
        objs.append(
            {
                "name": obj.name,
                "type": obj.type,
                "hide_viewport": bool(getattr(obj, "hide_viewport", False)),
                "hide_render": bool(getattr(obj, "hide_render", False)),
            }
        )

    scenes = []
    for scn in bpy.data.scenes:
        scenes.append({"name": scn.name, "frame_start": scn.frame_start, "frame_end": scn.frame_end})

    return {"objects": objs, "scenes": scenes, "object_count": len(objs)}
