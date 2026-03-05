from __future__ import annotations

from dataclasses import dataclass
import json
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class EngAInResponse:
    ok: bool
    status: int
    data: Optional[Dict[str, Any]]
    error: Optional[str]
    elapsed_ms: int


class EngAInHttpClient:
    """Tiny stdlib-only HTTP JSON client for talking to the EngAIn runtime.

    Designed to run inside UPBGE without external dependencies.
    """

    def __init__(self, base_url: str, timeout_s: float = 0.25) -> None:
        base_url = (base_url or "").strip()
        if not base_url:
            raise ValueError("base_url is required")
        self.base_url = base_url.rstrip("/")
        self.timeout_s = float(timeout_s)

    def get_json(self, path: str) -> EngAInResponse:
        return self._request_json(method="GET", path=path, payload=None)

    def post_json(self, path: str, payload: Dict[str, Any]) -> EngAInResponse:
        return self._request_json(method="POST", path=path, payload=payload)

    def _request_json(self, method: str, path: str, payload: Optional[Dict[str, Any]]) -> EngAInResponse:
        start = time.perf_counter()
        url = self._join(self.base_url, path)

        headers = {"Accept": "application/json"}
        body: Optional[bytes] = None
        if payload is not None:
            body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            headers["Content-Type"] = "application/json; charset=utf-8"

        req = urllib.request.Request(url=url, data=body, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                status = int(getattr(resp, "status", 200))
                raw = resp.read() or b""

                data = _safe_json_parse(raw)
                elapsed_ms = int((time.perf_counter() - start) * 1000)
                return EngAInResponse(ok=(200 <= status < 300), status=status, data=data, error=None, elapsed_ms=elapsed_ms)

        except urllib.error.HTTPError as e:
            status = int(getattr(e, "code", 0) or 0)
            try:
                raw = e.read() or b""

            except Exception:
                raw = b""

            data = _safe_json_parse(raw)
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            return EngAInResponse(ok=False, status=status, data=data, error=f"HTTPError: {e}", elapsed_ms=elapsed_ms)

        except urllib.error.URLError as e:
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            return EngAInResponse(ok=False, status=0, data=None, error=f"URLError: {e}", elapsed_ms=elapsed_ms)

        except Exception as e:
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            return EngAInResponse(ok=False, status=0, data=None, error=f"Error: {e}", elapsed_ms=elapsed_ms)

    @staticmethod
    def _join(base: str, path: str) -> str:
        path = (path or "").strip()
        if not path:
            return base
        if path.startswith("/"):
            return base + path
        return base + "/" + path


def _safe_json_parse(raw: bytes) -> Optional[Dict[str, Any]]:
    if not raw:
        return None
    try:
        txt = raw.decode("utf-8")
    except Exception:
        txt = raw.decode("utf-8", errors="replace")
    txt = txt.strip()
    if not txt:
        return None
    try:
        val = json.loads(txt)
    except Exception:
        return {"raw": txt}
    if isinstance(val, dict):
        return val
    return {"value": val}
