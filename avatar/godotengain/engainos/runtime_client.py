# runtime_client.py
from __future__ import annotations

import json
import os
import time
import uuid
import urllib.request
import urllib.error
from dataclasses import dataclass
from typing import Any, Dict, Optional


class RuntimeClientError(RuntimeError):
    pass


@dataclass(frozen=True)
class RuntimeResponse:
    status: int
    headers: Dict[str, str]
    body: bytes
    url: str

    def text(self) -> str:
        return self.body.decode("utf-8", errors="replace")

    def json(self) -> Any:
        return json.loads(self.body.decode("utf-8"))


class NGATRTClient:
    """
    Client for YOUR current NGAT-RT server implemented via http.server in sim_runtime.py.
    Endpoints:
      GET  /snapshot
      POST /command
      POST /combat/damage
      POST /inventory/take|drop|wear
      POST /dialogue/say|ask
    """
    def __init__(self, base_url: Optional[str] = None, timeout_s: float = 5.0, retries: int = 1):
        self.base_url = (base_url or os.environ.get("NGAT_RT_BASE_URL", "http://127.0.0.1:8080")).rstrip("/")
        self.timeout_s = float(timeout_s)
        self.retries = int(retries)

    def _url(self, path: str) -> str:
        if not path.startswith("/"):
            path = "/" + path
        return self.base_url + path

    def _request(self, method: str, path: str, payload: Optional[dict] = None) -> RuntimeResponse:
        url = self._url(path)
        trace_id = str(uuid.uuid4())

        headers = {
            "Accept": "application/json",
            "X-Trace-Id": trace_id,
        }

        data = None
        if payload is not None:
            body = dict(payload)
            body.setdefault("trace_id", trace_id)
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json; charset=utf-8"

        last_err: Optional[Exception] = None
        for attempt in range(self.retries + 1):
            try:
                req = urllib.request.Request(url, data=data, method=method.upper(), headers=headers)
                with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                    b = resp.read()
                    return RuntimeResponse(
                        status=int(resp.status),
                        headers={k.lower(): v for k, v in resp.headers.items()},
                        body=b,
                        url=url,
                    )
            except urllib.error.HTTPError as e:
                b = e.read() if hasattr(e, "read") else b""
                return RuntimeResponse(
                    status=int(getattr(e, "code", 0) or 0),
                    headers={k.lower(): v for k, v in getattr(e, "headers", {}).items()} if getattr(e, "headers", None) else {},
                    body=b,
                    url=url,
                )
            except Exception as e:
                last_err = e
                if attempt < self.retries:
                    time.sleep(0.15 * (2 ** attempt))
                    continue
                break
        raise RuntimeClientError(f"{method} {url} failed: {last_err}")

    # ---- Runtime operations ----
    def snapshot(self) -> RuntimeResponse:
        return self._request("GET", "/snapshot")

    def command(self, cmd: dict) -> RuntimeResponse:
        return self._request("POST", "/command", cmd)

    def combat_damage(self, source: str, target: str, damage: float) -> RuntimeResponse:
        return self._request("POST", "/combat/damage", {"source": source, "target": target, "damage": damage})

    def inventory_take(self, actor: str, item: str) -> RuntimeResponse:
        return self._request("POST", "/inventory/take", {"actor": actor, "item": item})

    def inventory_drop(self, actor: str, item: str, location: str = "world") -> RuntimeResponse:
        return self._request("POST", "/inventory/drop", {"actor": actor, "item": item, "location": location})

    def inventory_wear(self, actor: str, item: str) -> RuntimeResponse:
        return self._request("POST", "/inventory/wear", {"actor": actor, "item": item})

    def dialogue_say(self, data: dict) -> RuntimeResponse:
        return self._request("POST", "/dialogue/say", data)

    def dialogue_ask(self, data: dict) -> RuntimeResponse:
        return self._request("POST", "/dialogue/ask", data)

    def probe(self) -> bool:
        try:
            r = self.snapshot()
            return 200 <= r.status < 300
        except Exception:
            return False
