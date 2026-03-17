from __future__ import annotations

from pathlib import Path
from typing import Optional

import bpy

from _common import load_params, ok, fail


def main() -> None:
    params, _meta, result_json = load_params()

    out_file = params.get("out_file")
    if not out_file:
        fail(result_json, "Missing required param: out_file")
        return

    export_format = str(params.get("export_format", "glb")).lower()
    if export_format not in {"glb", "gltf"}:
        fail(result_json, f"Only glb/gltf supported in this starter pack (got {export_format!r})")
        return

    selected_only = bool(params.get("selected_only", False))
    apply_modifiers = bool(params.get("apply_modifiers", True))
    export_materials = bool(params.get("export_materials", True))
    export_animations = bool(params.get("export_animations", False))
    export_cameras = bool(params.get("export_cameras", False))
    export_lights = bool(params.get("export_lights", False))
    y_up = bool(params.get("y_up", True))

    out_path = Path(str(out_file)).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        bpy.ops.export_scene.gltf(
            filepath=str(out_path),
            export_format="GLB" if export_format == "glb" else "GLTF_SEPARATE",
            use_selection=selected_only,
            export_apply=apply_modifiers,
            export_materials="EXPORT" if export_materials else "NONE",
            export_animations=export_animations,
            export_cameras=export_cameras,
            export_lights=export_lights,
            export_yup=y_up,
        )
    except Exception as exc:
        fail(result_json, f"Export failed: {exc}")
        return

    ok(result_json, result={"out_file": str(out_path), "format": export_format, "selected_only": selected_only})


main()
