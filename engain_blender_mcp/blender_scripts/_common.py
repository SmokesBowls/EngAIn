from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Tuple


def _parse_args() -> argparse.Namespace:
    argv = sys.argv
    # Entry point resets sys.argv to [script, --params-json, --result-json]
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument("--params-json", required=True)
    p.add_argument("--result-json", required=True)
    return p.parse_known_args(argv[1:])[0]


def load_params() -> Tuple[dict, dict, Path]:
    """
    Returns: (params, meta, result_json_path)
    params: payload["params"] (dict)
    meta:   payload["meta"] (dict)
    """
    args = _parse_args()
    payload = json.loads(Path(args.params_json).read_text(encoding="utf-8"))
    params = payload.get("params") or {}
    meta = payload.get("meta") or {}
    return params, meta, Path(args.result_json)


def write_result(result_json: Path, payload: dict) -> None:
    result_json.parent.mkdir(parents=True, exist_ok=True)
    result_json.write_text(json.dumps(payload, ensure_ascii=False, default=str), encoding="utf-8")


def ok(result_json: Path, result: Any = None, **extra: Any) -> None:
    payload = {"ok": True, "result": result}
    payload.update(extra)
    write_result(result_json, payload)


def fail(result_json: Path, error: str, **extra: Any) -> None:
    payload = {"ok": False, "error": error}
    payload.update(extra)
    write_result(result_json, payload)
