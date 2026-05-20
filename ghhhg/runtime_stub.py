#!/usr/bin/env python3
"""
runtime_stub.py
A tiny HTTP runtime that accepts ZONJ scene POSTs and persists them to disk.

- Listens on --host/--port (default 127.0.0.1:5000)
- Accepts:
    POST /scene   (single scene JSON)
    POST /scenes  (single scene JSON)
    POST /ingest  (single scene JSON)
  and also accepts a list payload (multiple scenes) for convenience.
- Writes JSON files into --out directory.

No external deps. Pure stdlib.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union


def _safe_slug(s: str) -> str:
    s = (s or "").strip()
    s = s.replace(" ", "_")
    s = re.sub(r"[^A-Za-z0-9_\-\.]+", "", s)
    return s or "scene"


def _now_tag() -> str:
    return time.strftime("%Y%m%d_%H%M%S")


def _extract_scene_id(obj: Dict[str, Any]) -> str:
    # Prefer canonical @id, else id
    sid = obj.get("@id") or obj.get("id") or obj.get("scene_id") or obj.get("name")
    if isinstance(sid, str) and sid.strip():
        return _safe_slug(sid)
    return "scene"


class RuntimeState:
    def __init__(self, out_dir: Path):
        self.out_dir = out_dir
        self.out_dir.mkdir(parents=True, exist_ok=True)

    def store_one(self, scene: Dict[str, Any]) -> Path:
        sid = _extract_scene_id(scene)
        fname = f"{sid}__{_now_tag()}.json"
        path = self.out_dir / fname
        path.write_text(json.dumps(scene, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def store_many(self, scenes: List[Dict[str, Any]]) -> List[Path]:
        paths: List[Path] = []
        for sc in scenes:
            if isinstance(sc, dict):
                paths.append(self.store_one(sc))
        return paths


class Handler(BaseHTTPRequestHandler):
    # Set by main()
    state: RuntimeState = None  # type: ignore

    def _send(self, code: int, body: Union[Dict[str, Any], str], content_type: str = "application/json") -> None:
        if isinstance(body, dict):
            data = json.dumps(body, ensure_ascii=False, indent=2).encode("utf-8")
        else:
            data = body.encode("utf-8")
            content_type = "text/plain; charset=utf-8"

        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        if self.path in ("/", "/health", "/healthz"):
            self._send(200, {"ok": True, "service": "engain-runtime-stub"})
            return
        if self.path == "/routes":
            self._send(200, {"routes": ["GET /health", "POST /scene", "POST /scenes", "POST /ingest"]})
            return
        self._send(404, {"ok": False, "error": "not_found", "path": self.path})

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length") or "0")
    raw = self.rfile.read(length) if length > 0 else b""

    try:
        payload = json.loads(raw.decode("utf-8") if raw else "null")
    except Exception as e:
        self._send(400, {"ok": False, "error": "invalid_json", "detail": str(e), "path": self.path})
        return

    # Accept either dict (single scene) or list (many scenes)
    if isinstance(payload, dict):
        p = self.state.store_one(payload)
        self._send(200, {"ok": True, "stored": 1, "files": [str(p)], "path": self.path})
        return
    if isinstance(payload, list):
        scenes = [x for x in payload if isinstance(x, dict)]
        paths = self.state.store_many(scenes)
        self._send(200, {"ok": True, "stored": len(paths), "files": [str(p) for p in paths], "path": self.path})
        return

    self._send(400, {"ok": False, "error": "unsupported_payload_type", "type": str(type(payload)), "path": self.path})
        try:
            payload = json.loads(raw.decode("utf-8") if raw else "null")
        except Exception as e:
            self._send(400, {"ok": False, "error": "invalid_json", "detail": str(e)})
            return

        # Accept either dict (single scene) or list (many scenes)
        if isinstance(payload, dict):
            p = self.state.store_one(payload)
            self._send(200, {"ok": True, "stored": 1, "files": [str(p)]})
            return
        if isinstance(payload, list):
            scenes = [x for x in payload if isinstance(x, dict)]
            paths = self.state.store_many(scenes)
            self._send(200, {"ok": True, "stored": len(paths), "files": [str(p) for p in paths]})
            return

        self._send(400, {"ok": False, "error": "unsupported_payload_type", "type": str(type(payload))})

    # Quiet default logging
    def log_message(self, fmt: str, *args: Any) -> None:
        return


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=5000)
    ap.add_argument("--out", default="./loaded_runtime", help="Directory to store posted scenes")
    args = ap.parse_args()

    out_dir = Path(args.out).expanduser().resolve()
    state = RuntimeState(out_dir)

    Handler.state = state
    server = HTTPServer((args.host, args.port), Handler)

    print(f"[runtime_stub] listening on http://{args.host}:{args.port}")
    print(f"[runtime_stub] writing scenes to: {out_dir}")
    print("[runtime_stub] routes: GET /health, POST /scene, POST /scenes, POST /ingest")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[runtime_stub] shutdown")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
