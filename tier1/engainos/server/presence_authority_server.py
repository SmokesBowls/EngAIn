#!/usr/bin/env python3
"""
presence_authority_server.py - The one process-shared PresenceRegistry +
SessionClaimRegistry, reachable over HTTP by every worker process.

This is the fix for the false-integration mistake this module's design
history records: importing PresenceRegistry directly into each of the 2D
and 3D avatar worker processes would give each of them a private, in-memory
registry that the other can never see. resolve() would always succeed
locally and never actually catch a real cross-process race. This server
exists so there is exactly one PresenceRegistry and exactly one
SessionClaimRegistry in the whole system, and every worker — regardless of
which process or which repo it lives in — talks to that one instance over
HTTP instead of holding its own.

Binds 127.0.0.1:8767 by default — next in the sequence after the existing
8080 (Tier-2 sim runtime), 8090 (FastAPI facade), 8765 (Tier-1 launch
engine), 8766 (Trixel service), per the 2026-08-16 full audit's port list.

Endpoints (all JSON):
    POST /presence/register    -> PresenceRecord
    POST /presence/renew       -> PresenceRecord | 404
    GET  /presence/resolve?session_id=...  -> PresenceRecord | 404
    POST /presence/deregister  -> {"deregistered": bool}
    POST /claim                -> SessionClaim (200) | ClaimRejected (409)
    POST /release               -> {"released": bool}
    GET  /health                -> {"status": "healthy"}

This server does not decide policy (agent_gateway's job, untouched) and
does not decide conversation content (SessionLedger's job, untouched). It
only makes presence and per-dispatch mutual exclusion real across process
boundaries, which an in-process object cannot do.
"""

from __future__ import annotations

import dataclasses
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict
from urllib.parse import parse_qs, urlparse

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tier1.engainos.core.presence_registry import PresenceRegistry
from tier1.engainos.core.session_claim_registry import ClaimRejected, SessionClaim, SessionClaimRegistry

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8767

presence = PresenceRegistry()
claims = SessionClaimRegistry()


def _record_to_dict(record: Any) -> Dict[str, Any]:
    return dataclasses.asdict(record)


class PresenceAuthorityHandler(BaseHTTPRequestHandler):
    server_version = "EngAInPresenceAuthority/1"

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002 - stdlib signature
        sys.stderr.write("[presence-authority] " + (format % args) + "\n")

    def _send_json(self, status: int, payload: Dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self) -> Dict[str, Any]:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8"))

    def do_GET(self) -> None:  # noqa: N802 - stdlib signature
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self._send_json(200, {"status": "healthy"})
            return
        if parsed.path == "/presence/resolve":
            qs = parse_qs(parsed.query)
            session_id = (qs.get("session_id") or [None])[0]
            if not session_id:
                self._send_json(400, {"error": "session_id query param required"})
                return
            record = presence.resolve(session_id)
            if record is None:
                self._send_json(404, {"error": "PROVIDER_NOT_REGISTERED", "session_id": session_id})
                return
            self._send_json(200, _record_to_dict(record))
            return
        self._send_json(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802 - stdlib signature
        parsed = urlparse(self.path)
        try:
            body = self._read_json_body()
        except (ValueError, json.JSONDecodeError) as exc:
            self._send_json(400, {"error": f"invalid JSON body: {exc}"})
            return

        if parsed.path == "/presence/register":
            record = presence.register(
                agent_id=body["agent_id"],
                instance_id=body["instance_id"],
                session_id=body["session_id"],
                capabilities=body.get("capabilities"),
                endpoint=body.get("endpoint"),
                requested_lease=float(body.get("requested_lease", 300.0)),
            )
            self._send_json(200, _record_to_dict(record))
            return

        if parsed.path == "/presence/renew":
            record = presence.renew(
                instance_id=body["instance_id"],
                extend_by=float(body.get("extend_by", 300.0)),
            )
            if record is None:
                self._send_json(404, {"error": "UNKNOWN_OR_EXPIRED_INSTANCE"})
                return
            self._send_json(200, _record_to_dict(record))
            return

        if parsed.path == "/presence/deregister":
            deregistered = presence.deregister(instance_id=body["instance_id"])
            self._send_json(200, {"deregistered": deregistered})
            return

        if parsed.path == "/claim":
            result = claims.claim(
                session_id=body["session_id"],
                agent_id=body["agent_id"],
                instance_id=body["instance_id"],
                lease_seconds=float(body.get("lease_seconds", 200.0)),
            )
            if isinstance(result, ClaimRejected):
                self._send_json(409, dataclasses.asdict(result))
                return
            self._send_json(200, dataclasses.asdict(result))
            return

        if parsed.path == "/release":
            released = claims.release(session_id=body["session_id"], claim_token=body["claim_token"])
            self._send_json(200, {"released": released})
            return

        self._send_json(404, {"error": "not found"})


def run(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> None:
    server = ThreadingHTTPServer((host, port), PresenceAuthorityHandler)
    server.daemon_threads = True
    print(f"[presence-authority] listening on {host}:{port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        print("[presence-authority] shut down", flush=True)


def _parse_args(argv: Any = None) -> Any:
    import argparse

    parser = argparse.ArgumentParser(description="EngAIn shared presence authority server")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    return parser.parse_args(argv)


if __name__ == "__main__":
    _args = _parse_args()
    run(host=_args.host, port=_args.port)
