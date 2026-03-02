from __future__ import annotations

import argparse
import json
import runpy
import sys
import traceback
from pathlib import Path


def _parse_entry_args() -> argparse.Namespace:
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1 :]
    p = argparse.ArgumentParser(prog="engain_blender_entrypoint")
    p.add_argument("--script", required=True, help="Absolute path to the target Blender-side script")
    p.add_argument("--params-json", required=True, help="Path to params.json written by the MCP server")
    p.add_argument("--result-json", required=True, help="Path to result.json to write back to the MCP server")
    return p.parse_args(argv)


def _write_result(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, default=str), encoding="utf-8")


def main() -> None:
    args = _parse_entry_args()

    script_path = Path(args.script).resolve()
    params_json = Path(args.params_json).resolve()
    result_json = Path(args.result_json).resolve()

    try:
        params_payload = json.loads(params_json.read_text(encoding="utf-8"))
    except Exception as exc:
        _write_result(result_json, {"ok": False, "error": f"Failed to read params JSON: {exc}"})
        return

    scripts_dir = None
    try:
        scripts_dir = Path(params_payload.get("meta", {}).get("scripts_dir", "")).resolve()
    except Exception:
        scripts_dir = None

    # Harden: ensure script is under scripts_dir if provided
    if scripts_dir and scripts_dir.exists():
        try:
            script_path.relative_to(scripts_dir)
        except Exception:
            _write_result(result_json, {"ok": False, "error": f"Script path escapes scripts_dir: {script_path}"})
            return

    # Make scripts root importable so category scripts can do:
    #   sys.path.insert(0, scripts_root)
    #   from _common import setup, write_result
    scripts_root = scripts_dir if (scripts_dir and scripts_dir.exists()) else script_path.parent.parent
    sys.path.insert(0, str(scripts_root))

    # Present a consistent argv to the target script
    sys.argv = [
        str(script_path),
        "--params-json",
        str(params_json),
        "--result-json",
        str(result_json),
    ]

    try:
        runpy.run_path(str(script_path), run_name="__main__")
    except SystemExit as exc:
        code = int(getattr(exc, "code", 1) or 0)
        if code != 0:
            _write_result(result_json, {"ok": False, "error": f"Script exited with code {code}"})
    except Exception:
        tb = traceback.format_exc(limit=50)
        _write_result(result_json, {"ok": False, "error": "Unhandled exception in Blender script", "traceback": tb})


if __name__ == "__main__":
    main()
