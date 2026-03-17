from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Optional

from mcp.server.fastmcp import FastMCP


LOG = logging.getLogger("engain_blender_mcp")


def _configure_logging() -> None:
    # Never write non-protocol bytes to stdout for MCP stdio.
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()
    root.addHandler(handler)


def _find_blender_bin(blender_bin: str) -> str:
    candidate = os.environ.get("BLENDER_BIN") or blender_bin
    resolved = shutil.which(candidate)
    if resolved:
        return resolved
    p = Path(candidate)
    if p.exists():
        return str(p.resolve())
    raise FileNotFoundError(f"Blender binary not found: {candidate!r} (set BLENDER_BIN if needed)")


def _safe_resolve_script(scripts_dir: Path, script_rel: str) -> Path:
    rel = script_rel.replace("\\", "/").lstrip("/")
    rel = rel if rel.endswith(".py") else f"{rel}.py"
    scripts_dir = scripts_dir.resolve()
    candidate = (scripts_dir / rel).resolve()
    try:
        candidate.relative_to(scripts_dir)
    except ValueError as exc:
        raise PermissionError(f"Script path escapes scripts_dir: {candidate}") from exc
    if not candidate.exists():
        raise FileNotFoundError(f"Script not found: {candidate}")
    return candidate


def _run_blender(
    *,
    blender_bin: str,
    entrypoint_py: Path,
    scripts_dir: Path,
    script_py: Path,
    blend_file: Optional[Path],
    params: Dict[str, Any],
    timeout_s: int,
) -> dict:
    start = time.time()
    with tempfile.TemporaryDirectory(prefix="engain_blender_mcp_") as td:
        td = Path(td)
        params_json = td / "params.json"
        result_json = td / "result.json"

        params_json.write_text(
            json.dumps(
                {
                    "params": params or {},
                    "meta": {
                        "scripts_dir": str(scripts_dir.resolve()),
                        "script": str(script_py.resolve()),
                        "blend_file": str(blend_file.resolve()) if blend_file else None,
                        "timestamp_unix": int(time.time()),
                    },
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        cmd = [blender_bin, "-b", "--factory-startup", "--python-exit-code", "1"]
        if blend_file:
            cmd.append(str(blend_file.resolve()))
        cmd += [
            "--python",
            str(entrypoint_py.resolve()),
            "--",
            "--script",
            str(script_py.resolve()),
            "--params-json",
            str(params_json),
            "--result-json",
            str(result_json),
        ]

        LOG.info("Launching Blender: %s", " ".join(cmd))

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=int(timeout_s),
                check=False,
                stdin=subprocess.DEVNULL,
            )
        except subprocess.TimeoutExpired as exc:
            return {
                "ok": False,
                "error": f"Timed out after {timeout_s}s",
                "exit_code": 124,
                "duration_s": time.time() - start,
                "result": None,
                "blender_stdout": (exc.stdout or ""),
                "blender_stderr": (exc.stderr or ""),
            }

        structured: Any = None
        if result_json.exists():
            try:
                structured = json.loads(result_json.read_text(encoding="utf-8"))
            except Exception as exc:
                structured = {"ok": False, "error": f"Failed to parse result JSON: {exc}"}
        else:
            structured = {"ok": False, "error": "Missing result.json (entrypoint likely failed)"}

        ok_flag = (proc.returncode == 0) and bool(getattr(structured, "get", lambda *_: False)("ok", False))

        return {
            "ok": ok_flag,
            "error": None if ok_flag else (structured.get("error") if isinstance(structured, dict) else f"Exit {proc.returncode}"),
            "exit_code": int(proc.returncode),
            "duration_s": time.time() - start,
            "result": structured,
            "blender_stdout": proc.stdout[-20000:],
            "blender_stderr": proc.stderr[-20000:],
        }


def build_server(*, scripts_dir: Path, blender_bin: str) -> FastMCP:
    mcp = FastMCP("Engain Blender Toolbag", stateless_http=True, json_response=True)

    scripts_dir = scripts_dir.resolve()
    blender_bin_resolved = _find_blender_bin(blender_bin)

    entrypoint_py = Path(__file__).resolve().parent / "blender_entrypoint.py"
    if not entrypoint_py.exists():
        raise FileNotFoundError(f"Missing blender_entrypoint.py at {entrypoint_py}")

    def _run(script: str, *, blend_file: Optional[str], params: dict, timeout_s: int) -> dict:
        script_py = _safe_resolve_script(scripts_dir, script)
        blend_path = Path(blend_file).expanduser().resolve() if blend_file else None
        if blend_path and not blend_path.exists():
            raise FileNotFoundError(f"blend_file not found: {blend_path}")
        return _run_blender(
            blender_bin=blender_bin_resolved,
            entrypoint_py=entrypoint_py,
            scripts_dir=scripts_dir,
            script_py=script_py,
            blend_file=blend_path,
            params=params,
            timeout_s=timeout_s,
        )

    @mcp.tool()
    def bridge_status() -> dict:
        return {"ok": True, "blender_bin": blender_bin_resolved, "scripts_dir": str(scripts_dir)}

    @mcp.tool()
    def blender_version(timeout_s: int = 10) -> dict:
        proc = subprocess.run(
            [blender_bin_resolved, "--version"],
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
            stdin=subprocess.DEVNULL,
        )
        return {"ok": proc.returncode == 0, "exit_code": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}

    @mcp.tool()
    def list_scripts() -> dict:
        tree: dict[str, list[str]] = {}
        for p in sorted(scripts_dir.rglob("*.py")):
            if p.name.startswith("_"):
                continue
            rel = p.relative_to(scripts_dir)
            cat = rel.parts[0] if len(rel.parts) > 1 else "root"
            tree.setdefault(cat, []).append(str(rel.with_suffix("")).replace("\\", "/"))
        return {"ok": True, "scripts": tree}

    @mcp.tool()
    def run_blender_script(script: str, blend_file: Optional[str] = None, params: Optional[dict] = None, timeout_s: int = 900) -> dict:
        return _run(script, blend_file=blend_file, params=params or {}, timeout_s=int(timeout_s))

    # ── Star Needle workflow tools ────────────────────────────────────────
    @mcp.tool()
    def create_shot(
        out_blend: str,
        scene_name: str = "Shot_001",
        frame_start: int = 1,
        frame_end: int = 240,
        fps: float = 24.0,
        resolution_x: int = 1920,
        resolution_y: int = 1080,
        render_engine: str = "CYCLES",
        output_path: str = "/tmp/render/",
        camera_name: str = "Camera_Main",
        timeout_s: int = 60,
    ) -> dict:
        return _run(
            "scene_management/create_shot",
            blend_file=None,
            params=dict(
                out_blend=out_blend,
                scene_name=scene_name,
                frame_start=frame_start,
                frame_end=frame_end,
                fps=fps,
                resolution_x=resolution_x,
                resolution_y=resolution_y,
                render_engine=render_engine,
                output_path=output_path,
                camera_name=camera_name,
            ),
            timeout_s=int(timeout_s),
        )

    @mcp.tool()
    def generate_star_needle(
        blend_file: str,
        collection_name: str = "StarNeedle",
        height_m: float = 60.0,
        base_radius_m: float = 6.0,
        collar_radius_m: float = 4.5,
        shaft_radius_base_m: float = 1.0,
        shaft_radius_top_m: float = 0.15,
        tip_height_m: float = 3.0,
        star_count: int = 6,
        star_outer_radius_m: float = 0.6,
        star_inner_radius_m: float = 0.25,
        star_thickness_m: float = 0.08,
        star_inset_m: float = 0.02,
        save_as: Optional[str] = None,
        timeout_s: int = 180,
    ) -> dict:
        return _run(
            "scene_management/generate_star_needle",
            blend_file=blend_file,
            params=dict(
                collection_name=collection_name,
                height_m=height_m,
                base_radius_m=base_radius_m,
                collar_radius_m=collar_radius_m,
                shaft_radius_base_m=shaft_radius_base_m,
                shaft_radius_top_m=shaft_radius_top_m,
                tip_height_m=tip_height_m,
                star_count=star_count,
                star_outer_radius_m=star_outer_radius_m,
                star_inner_radius_m=star_inner_radius_m,
                star_thickness_m=star_thickness_m,
                star_inset_m=star_inset_m,
                save_as=save_as,
            ),
            timeout_s=int(timeout_s),
        )

    @mcp.tool()
    def create_lighting_rig(
        blend_file: str,
        rig_scale: float = 1.0,
        key_light_energy: float = 1200.0,
        fill_ratio: float = 0.35,
        rim_ratio: float = 0.6,
        color_temperature_k: int = 5500,
        cast_shadows: bool = True,
        collection_name: str = "Lighting_Rig",
        timeout_s: int = 60,
    ) -> dict:
        return _run(
            "scene_management/create_lighting_rig",
            blend_file=blend_file,
            params=dict(
                rig_type="three_point",
                target_object=None,
                rig_scale=rig_scale,
                key_light_energy=key_light_energy,
                fill_ratio=fill_ratio,
                rim_ratio=rim_ratio,
                color_temperature_k=color_temperature_k,
                cast_shadows=cast_shadows,
                collection_name=collection_name,
            ),
            timeout_s=int(timeout_s),
        )

    @mcp.tool()
    def create_camera(
        blend_file: str,
        camera_name: str = "Camera",
        location: Optional[list[float]] = None,
        rotation_euler_deg: Optional[list[float]] = None,
        lens_mm: float = 50.0,
        sensor_width_mm: float = 36.0,
        clip_start: float = 0.1,
        clip_end: float = 2000.0,
        set_active: bool = True,
        timeout_s: int = 60,
    ) -> dict:
        return _run(
            "camera_lighting/create_camera",
            blend_file=blend_file,
            params=dict(
                camera_name=camera_name,
                location=location or [0.0, -20.0, 8.0],
                rotation_euler_deg=rotation_euler_deg or [75.0, 0.0, 0.0],
                lens_mm=lens_mm,
                sensor_width_mm=sensor_width_mm,
                clip_start=clip_start,
                clip_end=clip_end,
                camera_type="PERSP",
                ortho_scale=10.0,
                set_active=set_active,
                collection=None,
            ),
            timeout_s=int(timeout_s),
        )

    @mcp.tool()
    def set_world(
        blend_file: str,
        mode: str = "solid",
        hdri_path: Optional[str] = None,
        hdri_strength: float = 1.0,
        hdri_rotation_deg: float = 0.0,
        background_color: Optional[list[float]] = None,
        timeout_s: int = 60,
    ) -> dict:
        return _run(
            "scene_management/set_world",
            blend_file=blend_file,
            params=dict(
                mode=mode,
                hdri_path=hdri_path,
                hdri_strength=hdri_strength,
                hdri_rotation_deg=hdri_rotation_deg,
                background_color=background_color or [0.05, 0.05, 0.05, 1.0],
                use_sky_texture=False,
                sky_sun_elevation_deg=45.0,
                sky_sun_rotation_deg=0.0,
            ),
            timeout_s=int(timeout_s),
        )

    @mcp.tool()
    def render_still(
        blend_file: str,
        out_png: str,
        frame: int = 1,
        camera_name: Optional[str] = None,
        resolution_x: int = 1920,
        resolution_y: int = 1080,
        samples: int = 128,
        use_denoising: bool = True,
        denoiser: str = "OPENIMAGEDENOISE",
        use_transparent_bg: bool = False,
        timeout_s: int = 3600,
    ) -> dict:
        return _run(
            "camera_lighting/render_still",
            blend_file=blend_file,
            params=dict(
                out_png=out_png,
                frame=frame,
                camera_name=camera_name,
                resolution_x=resolution_x,
                resolution_y=resolution_y,
                resolution_percent=100,
                samples=samples,
                use_denoising=use_denoising,
                denoiser=denoiser,
                file_format="PNG",
                color_depth="16",
                use_transparent_bg=use_transparent_bg,
                render_engine=None,
            ),
            timeout_s=int(timeout_s),
        )

    @mcp.tool()
    def export_glb(
        blend_file: str,
        out_glb: str,
        selected_only: bool = False,
        apply_modifiers: bool = True,
        export_animations: bool = False,
        timeout_s: int = 900,
    ) -> dict:
        return _run(
            "asset_pipeline/export_asset",
            blend_file=blend_file,
            params=dict(
                out_file=out_glb,
                export_format="glb",
                object_names=None,
                selected_only=selected_only,
                apply_modifiers=apply_modifiers,
                export_materials=True,
                export_animations=export_animations,
                export_cameras=False,
                export_lights=False,
                y_up=True,
            ),
            timeout_s=int(timeout_s),
        )




    return mcp


def main() -> None:
    _configure_logging()
    p = argparse.ArgumentParser(prog="engain_blender_mcp")
    p.add_argument("--scripts-dir", type=str, default=str(Path(__file__).parent / "blender_scripts"))
    p.add_argument("--blender-bin", type=str, default="blender")
    p.add_argument("--transport", type=str, default="stdio", choices=["stdio", "sse", "streamable-http"])
    p.add_argument("--host", type=str, default="127.0.0.1")
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--mount-path", type=str, default=None, help="SSE only (optional).")
    args = p.parse_args()

    mcp = build_server(scripts_dir=Path(args.scripts_dir), blender_bin=args.blender_bin)
    mcp.settings.host = args.host
    mcp.settings.port = args.port

    if args.transport == "stdio":
        mcp.run(transport="stdio")
    elif args.transport == "sse":
        mcp.run(transport="sse", mount_path=args.mount_path)
    else:
        mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
