# filename: blender_scripts/engain_blender_ops.py
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

# Blender imports (only available when running inside Blender)
import bpy  # type: ignore


def _fail(code: str, detail: Optional[str] = None, **extra: Any) -> None:
    out: Dict[str, Any] = {"ok": False, "error": code}
    if detail:
        out["detail"] = detail
    out.update(extra)
    print(json.dumps(out, ensure_ascii=False))
    raise SystemExit(1)


def _ok(**data: Any) -> None:
    out: Dict[str, Any] = {"ok": True}
    out.update(data)
    print(json.dumps(out, ensure_ascii=False))
    raise SystemExit(0)


def _load_job() -> Dict[str, Any]:
    p = os.environ.get("ENGAIN_BLEND_OP_JSON", "").strip()
    if not p:
        _fail("missing_env", "ENGAIN_BLEND_OP_JSON not set")
    path = Path(p).expanduser()
    if not path.exists():
        _fail("job_file_missing", str(path))
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        _fail("job_json_parse_error", str(e), job_path=str(path))


def _open_blend(blend_file: str) -> None:
    bf = Path(blend_file)
    if not bf.exists():
        _fail("blend_not_found", str(bf))
    if bf.suffix.lower() != ".blend":
        _fail("blend_ext_invalid", str(bf))
    try:
        bpy.ops.wm.open_mainfile(filepath=str(bf))
    except Exception as e:
        _fail("open_mainfile_failed", str(e), blend_file=str(bf))


def _ensure_addon(module_name: str) -> None:
    # Some exporters are add-ons; try enable, ignore if already enabled.
    try:
        bpy.ops.preferences.addon_enable(module=module_name)
    except Exception:
        # If it's already enabled or not needed, continuing may still work.
        pass


def op_list_objects() -> None:
    objs = []
    for o in bpy.data.objects:
        objs.append({"name": o.name, "type": o.type})
    _ok(objects=objs, count=len(objs))


def op_export_glb(params: Dict[str, Any]) -> None:
    out_glb = str(params.get("out_glb", "")).strip()
    if not out_glb:
        _fail("missing_param", "out_glb")
    outp = Path(out_glb).expanduser()
    if outp.suffix.lower() != ".glb":
        _fail("out_ext_invalid", str(outp))

    outp.parent.mkdir(parents=True, exist_ok=True)

    selected_only = bool(params.get("selected_only", False))
    apply_modifiers = bool(params.get("apply_modifiers", True))
    export_animations = bool(params.get("export_animations", False))

    _ensure_addon("io_scene_gltf2")

    if selected_only:
        # Blender exporter keys off selection; ensure a deterministic selection state.
        bpy.ops.object.select_all(action="DESELECT")
        # If user wants selected_only, they should have selection saved in file.
        # We keep this strict rather than guessing.
        # If nothing is selected, export may be empty, and that's a real signal.
        pass

    try:
        # Blender operator supports glTF 2.0 export; exact params depend on Blender version.
        # Keep to a minimal, widely-supported set. :contentReference[oaicite:2]{index=2}
        bpy.ops.export_scene.gltf(
            filepath=str(outp),
            export_format="GLB",
            use_selection=selected_only,
            export_apply=apply_modifiers,
            export_animations=export_animations,
        )
    except Exception as e:
        _fail("export_glb_failed", str(e), out_glb=str(outp))

    _ok(out_glb=str(outp), selected_only=selected_only, apply_modifiers=apply_modifiers, export_animations=export_animations)


def op_render_still(params: Dict[str, Any]) -> None:
    out_png = str(params.get("out_png", "")).strip()
    if not out_png:
        _fail("missing_param", "out_png")
    outp = Path(out_png).expanduser()
    if outp.suffix.lower() != ".png":
        _fail("out_ext_invalid", str(outp))
    outp.parent.mkdir(parents=True, exist_ok=True)

    frame = params.get("frame", 1)
    try:
        frame_i = int(frame)
    except Exception:
        frame_i = 1

    camera_name = params.get("camera_name", None)
    if camera_name:
        cam = bpy.data.objects.get(str(camera_name))
        if not cam or cam.type != "CAMERA":
            _fail("camera_not_found", str(camera_name))
        bpy.context.scene.camera = cam

    scene = bpy.context.scene
    scene.frame_set(frame_i)
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(outp)

    try:
        bpy.ops.render.render(write_still=True)
    except Exception as e:
        _fail("render_failed", str(e), out_png=str(outp), frame=frame_i)

    _ok(out_png=str(outp), frame=frame_i, camera_name=camera_name)


def main() -> None:
    job = _load_job()
    op = str(job.get("op", "")).strip()
    blend_file = str(job.get("blend_file", "")).strip()
    params = job.get("params", {}) or {}

    if not op:
        _fail("missing_op")

    if blend_file:
        _open_blend(blend_file)

    if op == "list_objects":
        op_list_objects()
    elif op == "export_glb":
        if not isinstance(params, dict):
            _fail("params_must_be_object")
        op_export_glb(params)
    elif op == "render_still":
        if not isinstance(params, dict):
            _fail("params_must_be_object")
        op_render_still(params)
    else:
        _fail("unknown_op", op)


if __name__ == "__main__":
    main()
