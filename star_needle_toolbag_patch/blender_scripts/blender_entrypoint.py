# engain_blender_mcp/blender_entrypoint.py
from __future__ import annotations

import argparse
import json
import sys
import traceback
from contextlib import redirect_stderr, redirect_stdout
from importlib.machinery import SourceFileLoader
from io import StringIO
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, Optional


def _blender_args() -> list[str]:
    # Blender passes args in sys.argv; everything after `--` is user args.
    if "--" not in sys.argv:
        return []
    idx = sys.argv.index("--")
    return sys.argv[idx + 1 :]


def _load_module_from_path(script_path: Path) -> ModuleType:
    loader = SourceFileLoader(script_path.stem, str(script_path))
    mod = ModuleType(loader.name)
    loader.exec_module(mod)
    return mod


def _call_script(mod: ModuleType, payload: Dict[str, Any]) -> Any:
    # Try common entrypoints so existing scripts need minimal edits.
    # Preferred: run(params, meta) or run(payload)
    if hasattr(mod, "run") and callable(getattr(mod, "run")):
        fn = getattr(mod, "run")
        try:
            return fn(payload.get("params", {}), payload.get("meta", {}))
        except TypeError:
            return fn(payload)
    if hasattr(mod, "main") and callable(getattr(mod, "main")):
        fn = getattr(mod, "main")
        try:
            return fn(payload.get("params", {}))
        except TypeError:
            return fn(payload)
    if hasattr(mod, "execute") and callable(getattr(mod, "execute")):
        fn = getattr(mod, "execute")
        try:
            return fn(payload.get("params", {}))
        except TypeError:
            return fn(payload)
    # Fallback: module import side effects only
    return {"note": "No run/main/execute function found; module imported successfully."}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--script", required=True)
    ap.add_argument("--params-json", required=True)
    ap.add_argument("--result-json", required=True)
    args = ap.parse_args(_blender_args())

    script_path = Path(args.script).resolve()
    params_path = Path(args.params_json).resolve()
    result_path = Path(args.result_json).resolve()

    out: Dict[str, Any] = {
        "ok": False,
        "result": None,
        "stdout": "",
        "stderr": "",
        "error": None,
        "traceback": None,
    }

    stdout_buf = StringIO()
    stderr_buf = StringIO()

    try:
        payload = json.loads(params_path.read_text(encoding="utf-8"))
    except Exception as exc:
        out["error"] = f"Failed to read params JSON: {exc}"
        result_path.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
        return 2

    try:
        with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
            mod = _load_module_from_path(script_path)
            result = _call_script(mod, payload)

        out["ok"] = True
        out["result"] = result
    except Exception as exc:
        out["error"] = str(exc)
        out["traceback"] = traceback.format_exc()
    finally:
        out["stdout"] = stdout_buf.getvalue()
        out["stderr"] = stderr_buf.getvalue()

        # Ensure JSON-serializable output
        try:
            json.dumps(out, ensure_ascii=False)
        except TypeError:
            out["result"] = {"non_json_result": repr(out["result"])}
            out["ok"] = False
            out["error"] = out["error"] or "Script returned non-JSON-serializable result"

        result_path.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")

    return 0 if out["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
