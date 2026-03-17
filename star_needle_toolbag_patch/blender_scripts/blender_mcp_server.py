# engain_blender_mcp/blender_mcp_server.py
from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from mcp.server.fastmcp import FastMCP  # pip install mcp :contentReference[oaicite:2]{index=2}


LOG = logging.getLogger("engain_blender_mcp")


@dataclass(frozen=True)
class BlenderRunResult:
    ok: bool
    exit_code: int
    duration_s: float
    result: Any
    blender_stdout: str
    blender_stderr: str
    error: Optional[str]


def _configure_logging() -> None:
    # IMPORTANT for MCP STDIO: never write non-protocol bytes to stdout.
    # Logging goes to stderr only.
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    handler.setFormatter(fmt)
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()
    root.addHandler(handler)


def _find_blender_bin(blender_bin: str) -> str:
    env_bin = os.environ.get("BLENDER_BIN")
    candidate = env_bin or blender_bin
    resolved = shutil.which(candidate)
    if resolved:
        return resolved
    # If user passed an absolute path, allow it.
    if Path(candidate).exists():
        return str(Path(candidate).resolve())
    raise FileNotFoundError(
        f"Blender binary not found. Tried BLENDER_BIN={env_bin!r} and blender_bin={blender_bin!r}."
    )


def _safe_resolve_script(scripts_dir: Path, script_name: str) -> Path:
    # Allow "foo" or "foo.py"
    name = script_name if script_name.endswith(".py") else f"{script_name}.py"
    scripts_dir = scripts_dir.resolve()
    candidate = (scripts_dir / name).resolve()

    # Prevent path traversal: candidate must stay inside scripts_dir
    try:
        candidate.relative_to(scripts_dir)
    except ValueError as exc:
        raise PermissionError(f"Script path escapes scripts_dir: {candidate}") from exc

    if not candidate.exists():
        raise FileNotFoundError(f"Script not found: {candidate}")

    if candidate.suffix.lower() != ".py":
        raise ValueError(f"Script must be a .py file: {candidate}")

    return candidate


def _run_blender(
    *,
    blender_bin: str,
    entrypoint_py: Path,
    script_py: Path,
    scripts_dir: Path,
    blend_file: Optional[Path],
    params: Dict[str, Any],
    timeout_s: int,
) -> BlenderRunResult:
    start = time.time()

    with tempfile.TemporaryDirectory(prefix="engain_blender_mcp_") as td:
        td_path = Path(td)
        params_json = td_path / "params.json"
        result_json = td_path / "result.json"

        params_payload: Dict[str, Any] = {
            "params": params or {},
            "meta": {
                "scripts_dir": str(scripts_dir.resolve()),
                "script": str(script_py.resolve()),
                "blend_file": str(blend_file.resolve()) if blend_file else None,
                "timestamp_unix": int(time.time()),
            },
        }
        params_json.write_text(json.dumps(params_payload, ensure_ascii=False), encoding="utf-8")

        cmd = [blender_bin]

        # Background mode + predictable startup
        cmd += ["-b", "--factory-startup", "--python-exit-code", "1"]

        # If a .blend is provided, load it
        if blend_file is not None:
            cmd.append(str(blend_file.resolve()))

        # Run our entrypoint inside Blender
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
                timeout=timeout_s,
                check=False,
                stdin=subprocess.DEVNULL,
            )
        except subprocess.TimeoutExpired as exc:
            duration = time.time() - start
            return BlenderRunResult(
                ok=False,
                exit_code=124,
                duration_s=duration,
                result=None,
                blender_stdout=(exc.stdout or ""),
                blender_stderr=(exc.stderr or ""),
                error=f"Blender timed out after {timeout_s}s",
            )

        duration = time.time() - start

        structured: Any = None
        err_msg: Optional[str] = None

        if result_json.exists():
            try:
                structured = json.loads(result_json.read_text(encoding="utf-8"))
            except Exception as exc:
                err_msg = f"Failed to parse result JSON: {exc}"
        else:
            err_msg = "Blender did not produce a result.json (entrypoint may not have run)."

        ok = (proc.returncode == 0) and bool(structured) and bool(structured.get("ok", False))

        # Prefer error from structured payload if present
        if not ok:
            structured_err = None
            if isinstance(structured, dict):
                structured_err = structured.get("error")
            err_msg = structured_err or err_msg or f"Blender exited with code {proc.returncode}"

        return BlenderRunResult(
            ok=ok,
            exit_code=int(proc.returncode),
            duration_s=float(duration),
            result=structured,
            blender_stdout=proc.stdout,
            blender_stderr=proc.stderr,
            error=err_msg,
        )


def build_server(*, scripts_dir: Path, blender_bin: str) -> FastMCP:
    # For HTTP deployments, stateless_http + json_response are recommended. :contentReference[oaicite:3]{index=3}
    mcp = FastMCP("Engain Blender Bridge", stateless_http=True, json_response=True)

    server_dir = Path(__file__).resolve().parent
    entrypoint_py = server_dir / "blender_entrypoint.py"
    scripts_dir = scripts_dir.resolve()
    blender_bin_resolved = _find_blender_bin(blender_bin)

    @mcp.tool()
    def blender_version(timeout_s: int = 10) -> dict:
        """Return Blender version info (runs `blender --version`)."""
        proc = subprocess.run(
            [blender_bin_resolved, "--version"],
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
            stdin=subprocess.DEVNULL,
        )
        return {
            "ok": proc.returncode == 0,
            "exit_code": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }

    @mcp.tool()
    def run_blender_script(
        script: str,
        blend_file: Optional[str] = None,
        params: Optional[dict] = None,
        timeout_s: int = 900,
    ) -> dict:
        """
        Run a Blender Python script from scripts_dir in headless Blender.
        - script: script name like "list_objects" or "list_objects.py" (must exist in scripts_dir)
        - blend_file: optional path to .blend to load
        - params: JSON object passed to the script
        """
        script_py = _safe_resolve_script(scripts_dir, script)

        blend_path = Path(blend_file).expanduser().resolve() if blend_file else None
        if blend_path is not None and not blend_path.exists():
            raise FileNotFoundError(f"blend_file not found: {blend_path}")

        res = _run_blender(
            blender_bin=blender_bin_resolved,
            entrypoint_py=entrypoint_py,
            script_py=script_py,
            scripts_dir=scripts_dir,
            blend_file=blend_path,
            params=params or {},
            timeout_s=int(timeout_s),
        )

        return {
            "ok": res.ok,
            "exit_code": res.exit_code,
            "duration_s": res.duration_s,
            "result": res.result,
            "error": res.error,
            "blender_stdout": res.blender_stdout,
            "blender_stderr": res.blender_stderr,
        }

    # Convenience wrappers (these call the scripts included below)
    @mcp.tool()
    def list_objects(blend_file: str, timeout_s: int = 120) -> dict:
        """List objects in a .blend file."""
        return run_blender_script("list_objects", blend_file=blend_file, params={}, timeout_s=timeout_s)

    @mcp.tool()
    def render_still(
        blend_file: str,
        out_png: str,
        frame: int = 1,
        camera_name: Optional[str] = None,
        timeout_s: int = 900,
    ) -> dict:
        """Render a still PNG from a .blend."""
        return run_blender_script(
            "render_still",
            blend_file=blend_file,
            params={"out_png": out_png, "frame": frame, "camera_name": camera_name},
            timeout_s=timeout_s,
        )

    @mcp.tool()
    def list_blender_scripts() -> dict:
        """List runnable Python scripts in scripts_dir."""
        scripts = []
        for p in sorted(scripts_dir.glob("*.py")):
            if p.name.startswith("_"):
                continue
            scripts.append(p.stem)
        return {"ok": True, "scripts_dir": str(scripts_dir), "scripts": scripts}

    @mcp.tool()
    def bridge_status() -> dict:
        """Basic status: Blender path + scripts dir."""
        return {
            "ok": True,
            "blender_bin": blender_bin_resolved,
            "scripts_dir": str(scripts_dir),
        }

    @mcp.tool()
    def export_glb(
        blend_file: str,
        out_glb: str,
        selected_only: bool = False,
        apply_modifiers: bool = True,
        export_animations: bool = False,
        timeout_s: int = 900,
    ) -> dict:
        """Export a .blend to GLB."""
        return run_blender_script(
            "export_glb",
            blend_file=blend_file,
            params={
                "out_glb": out_glb,
                "selected_only": selected_only,
                "apply_modifiers": apply_modifiers,
                "export_animations": export_animations,
            },
            timeout_s=timeout_s,
        )

    return mcp


def main() -> None:
    _configure_logging()

    parser = argparse.ArgumentParser(prog="engain_blender_mcp")
    parser.add_argument("--scripts-dir", type=str, default=str(Path(__file__).parent / "blender_scripts"))
    parser.add_argument("--blender-bin", type=str, default="blender")
    parser.add_argument(
        "--transport",
        type=str,
        default="stdio",
        choices=["stdio", "streamable-http"],
        help="stdio for desktop clients; streamable-http for a URL endpoint",
    )
def main() -> None:
    _configure_logging()

    parser = argparse.ArgumentParser(prog="engain_blender_mcp")
    parser.add_argument(
        "--scripts-dir",
        type=str,
        default=str(Path(__file__).parent / "blender_scripts"),
    )
    parser.add_argument("--blender-bin", type=str, default="blender")
    parser.add_argument(
        "--transport",
        type=str,
        default="stdio",
        choices=["stdio", "sse", "streamable-http"],
    )
    parser.add_argument("--host", type=str, default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--mount-path",
        type=str,
        default=None,
        help="Only used for SSE transport (optional prefix mount).",
    )

    args = parser.parse_args()

    mcp = build_server(scripts_dir=Path(args.scripts_dir), blender_bin=args.blender_bin)

    # Bind address for HTTP-based transports
    mcp.settings.host = args.host
    mcp.settings.port = args.port

    if args.transport == "stdio":
        mcp.run(transport="stdio")
        return

    if args.transport == "sse":
        mcp.run(transport="sse", mount_path=args.mount_path)
        return

    mcp.run(transport="streamable-http")

if __name__ == "__main__":
    main()
