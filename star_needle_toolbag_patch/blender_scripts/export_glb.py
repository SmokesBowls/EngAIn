# engain_blender_mcp/blender_scripts/export_glb.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict


def run(params: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
    import bpy  # type: ignore

    out_glb = params.get("out_glb")
    if not out_glb or not isinstance(out_glb, str):
        raise ValueError("params.out_glb (string) is required")

    selected_only = bool(params.get("selected_only", False))
    apply_modifiers = bool(params.get("apply_modifiers", True))
    export_animations = bool(params.get("export_animations", False))

    out_path = Path(out_glb).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Ensure glTF exporter is enabled (usually bundled)
    try:
        bpy.ops.preferences.addon_enable(module="io_scene_gltf2")
    except Exception:
        # If already enabled or not needed, ignore
        pass

    bpy.ops.export_scene.gltf(
        filepath=str(out_path),
        export_format="GLB",
        use_selection=selected_only,
        export_apply=apply_modifiers,
        export_animations=export_animations,
    )

    return {
        "out_glb": str(out_path),
        "selected_only": selected_only,
        "apply_modifiers": apply_modifiers,
        "export_animations": export_animations,
    }
