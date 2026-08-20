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
    POST /dispatch              -> SharedSessionBridge.handle_turn()'s own
                                    return shape (200) | error (404/409/502)
    GET  /health                -> {"status": "healthy"}

This server does not decide policy (agent_gateway's job, untouched). It
does decide conversation content for /dispatch only, via the same
SessionLedger + ContinuityCursorTracker + SharedSessionBridge this
project's proof scripts already use directly in-process — this endpoint
is what makes that reachable from a separate worker process/repo without
vendoring those classes there (see the 2026-08-17 avatar-integration
receipt for why: a second, private copy of the continuity core in each
avatar repo would silently recreate the exact "two truths" problem the
shared presence authority itself was built to fix for PresenceRegistry).

/dispatch's request body carries the caller's OWN ProviderSessionBinding
(see provider_session_binding.py) explicitly — "worker submits the
request plus its ProviderSessionBinding to EngAIn" — rather than this
server guessing or remembering who should answer. The handler REGISTERs
that binding (most-recent-REGISTER-for-a-session_id-wins, same rule
PresenceRegistry already documents) immediately before calling
SharedSessionBridge.handle_turn(), which then resolves it right back via
its own internal step 3. This is deliberately the SAME Presence instance
/presence/register also uses — a caller switching the active provider for
a shared_session_id and a caller resolving "who is active" are reading
and writing the identical registry, not two.

Cursor/Ledger durability (item 3, 2026-08-19 — see
08-19-2026-item3-{restart-continuity-derivation,crash-consistency-design,
encoding-selection-design,frame-and-record-shape-design,
framing-integrity-and-write-failure-amendment}.md): PresenceRegistry and
SessionClaimRegistry remain pure process-lifetime in-memory state,
exactly as before — neither is persisted, unchanged by this item. Ledger
and Cursor are now durable, via `--journal-root` (default: DEFAULT_
JOURNAL_ROOT below). Each shared_session_id's turns are replayed lazily
from its own journal file on first touch after a restart — see
session_ledger.py's own docstring for the full mechanism. A session whose
journal fails integrity/sequence validation is quarantined; a session
whose durable write becomes uncertain while this process is alive is
poisoned. Both refuse ALL further /dispatch activity for that one
session_id only — see _handle_dispatch's early check below and
SessionUnavailable in session_ledger.py. Recovery from either state is a
full process restart (poison) or an operator resolving the quarantined
file (quarantine) — neither is automatic.

Dispatch mutex (item 1, 2026-08-18 — see
08-18-2026-item1-dispatch-mutex-design-analysis.md for the full design):
_handle_dispatch claims (provider_id, provider_session_id) — the real
identity of the native provider transcript a dispatch is about to
invoke — from SessionClaimRegistry before SharedSessionBridge.handle_turn()
runs, and releases it in a finally after handle_turn() returns or raises.
This is a second, independent use of the SAME registry instance the public
/claim and /release endpoints already expose (still string-keyed, still
used unchanged by the existing worker-level client-side claim) — never a
new HTTP surface. A contending caller gets DISPATCH_BUSY (409) immediately;
never queued. The claim's owner identity is a UUID minted fresh per
/dispatch call, never a caller-supplied agent_id/instance_id — see the
design note §6 for why reusing a stable caller identity would let two
genuinely concurrent calls silently "refresh" each other's claim instead
of correctly contending. The claimed key is also used to construct the
turn's ProviderSessionBinding directly from the request body — never from
Presence — see shared_session_bridge.py's own module docstring Correction
for why re-deriving it from Presence inside handle_turn() was unsafe.
"""

from __future__ import annotations

import dataclasses
import json
import sys
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict
from urllib.parse import parse_qs, urlparse

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tier1.engainos.bridgeroom.claude_code_provider_adapter import (
    DEFAULT_TIMEOUT_S as CLAUDE_CODE_DEFAULT_TIMEOUT_S,
    ClaudeCodeDispatchError,
    ClaudeCodeSessionDrift,
    dispatch_via_claude_code_cli,
)
from tier1.engainos.bridgeroom.hermes_provider_adapter import (
    DEFAULT_TIMEOUT_S as HERMES_DEFAULT_TIMEOUT_S,
    HermesDispatchError,
    HermesSessionDrift,
    dispatch_via_hermes_cli,
)
from tier1.engainos.bridgeroom.shared_session_bridge import (
    ProviderNotRegistered,
    ResponseActorMismatch,
    SharedSessionBridge,
)
from tier1.engainos.core.continuity_cursor_tracker import ContinuityCursorTracker
from tier1.engainos.core.presence_registry import PresenceRegistry
from tier1.engainos.core.provider_session_binding import ProviderSessionBinding
from tier1.engainos.core.session_claim_registry import ClaimRejected, SessionClaim, SessionClaimRegistry
from tier1.engainos.core.session_ledger import SessionLedger, SessionUnavailable

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8767
# runtime/sessions/ already existed as a reserved, empty directory before
# this item — see TODO.md/LEGACY_TREE_OUTPUT.md history. Continuity
# journals live here by default; override with --journal-root (or pass
# journal_root=None via compose_state() for a purely in-memory server,
# e.g. in a test that wants item 1/2's original behavior unmodified).
DEFAULT_JOURNAL_ROOT = REPO_ROOT / "runtime" / "sessions"

presence = PresenceRegistry()
claims = SessionClaimRegistry()
cursor = ContinuityCursorTracker()
ledger = SessionLedger(journal_root=DEFAULT_JOURNAL_ROOT, cursor=cursor)

# One dispatcher per provider_id a /dispatch caller may name. Adding a
# provider means adding one entry here — never branching inside
# SharedSessionBridge itself (see its own module docstring).
_PROVIDER_DISPATCHERS = {
    "hermes": dispatch_via_hermes_cli,
    "claude_code": dispatch_via_claude_code_cli,
}

# The dispatch-claim TTL per provider (item 1) — each adapter's own
# enforced subprocess.run(timeout=...) ceiling, read from that adapter
# module directly rather than duplicated as a literal here, so this can
# never silently drift out of sync with the timeout that actually governs
# how long a dispatch call can run. Keys must match _PROVIDER_DISPATCHERS.
_PROVIDER_DISPATCH_TIMEOUT_S = {
    "hermes": HERMES_DEFAULT_TIMEOUT_S,
    "claude_code": CLAUDE_CODE_DEFAULT_TIMEOUT_S,
}

# Fixed safety margin added on top of a provider's own enforced timeout to
# get the claim's lease_seconds — covers the surrounding in-memory Ledger/
# Presence/cursor steps plus subprocess.run's own post-timeout teardown,
# both bounded but not literally zero. See the design note §8b for the
# full derivation of this invariant (claim TTL must exceed the maximum
# possible duration of the protected critical section).
_DISPATCH_CLAIM_MARGIN_SECONDS = 15.0

_DISPATCH_FAILURE_EXCEPTIONS = (
    HermesDispatchError,
    HermesSessionDrift,
    ClaudeCodeDispatchError,
    ClaudeCodeSessionDrift,
)


def _dispatch_claim_lease_seconds(provider_id: str) -> float:
    return _PROVIDER_DISPATCH_TIMEOUT_S[provider_id] + _DISPATCH_CLAIM_MARGIN_SECONDS


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

    def _send_session_unavailable(self, exc: "SessionUnavailable") -> None:
        # item 3: 423 Locked — distinct from every pre-existing dispatch
        # error code (400/404/409/502) so a caller can tell "this session
        # is durably blocked, stop retrying it the normal way" apart from
        # every other rejection reason.
        from tier1.engainos.core.session_ledger import SessionPoisoned, SessionQuarantined

        error = "SESSION_POISONED" if isinstance(exc, SessionPoisoned) else "SESSION_QUARANTINED"
        self._send_json(423, {"error": error, "session_id": exc.session_id, "detail": str(exc)})

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

        if parsed.path == "/dispatch":
            self._handle_dispatch(body)
            return

        self._send_json(404, {"error": "not found"})

    def _handle_dispatch(self, body: Dict[str, Any]) -> None:
        required = (
            "shared_session_id",
            "origin_body",
            "player_input",
            "provider_id",
            "model_id",
            "provider_session_id",
        )
        missing = [key for key in required if key not in body]
        if missing:
            self._send_json(400, {"error": "MISSING_FIELDS", "fields": missing})
            return

        shared_session_id = body["shared_session_id"]
        # item 3: fail fast for a known-blocked session, before touching
        # claims or Presence at all — same "don't do work a rejected
        # caller didn't need" discipline item 1's own claim-first ordering
        # already established. append() inside handle_turn() enforces the
        # identical rule unconditionally below; this is purely an early
        # exit for the common repeated-access-after-poison/quarantine
        # case.
        try:
            ledger.raise_if_blocked(shared_session_id)
        except SessionUnavailable as exc:
            self._send_session_unavailable(exc)
            return

        provider_id = body["provider_id"]
        dispatcher = _PROVIDER_DISPATCHERS.get(provider_id)
        if dispatcher is None:
            self._send_json(
                400,
                {
                    "error": "UNKNOWN_PROVIDER",
                    "provider_id": provider_id,
                    "known_providers": sorted(_PROVIDER_DISPATCHERS),
                },
            )
            return

        provider_session_id = body["provider_session_id"]
        agent_id = body.get("agent_id") or provider_id
        # Presence's own instance_id — a stable-per-caller identity, used
        # only for the liveness registration below. Deliberately NOT used
        # as the dispatch claim's owner identity (see claim_owner_id).
        presence_instance_id = body.get("instance_id") or f"{provider_id}-dispatch"
        launch_options = body.get("launch_options") or {}

        # The turn's binding: constructed directly from this request's own
        # already-validated fields, before any claim or Presence call, and
        # never touched again after this point. This is what makes
        # "claimed_key == actual_invoked" structurally true rather than
        # merely usually true — see shared_session_bridge.py's own module
        # docstring Correction, and this module's own docstring above.
        binding = ProviderSessionBinding(
            provider_id=provider_id,
            model_id=body["model_id"],
            provider_session_id=provider_session_id,
            agent_id=agent_id,
            instance_id=presence_instance_id,
            shared_session_id=body["shared_session_id"],
            launch_options=launch_options,
        )

        # The native-transcript exclusivity claim (item 1). Acquired before
        # any other work — including presence.register() — so a rejected
        # caller never performs a Presence write it didn't need. Keyed on
        # the composite identity, never the bare shared_session_id (see
        # the design note §3 for why either alone is the wrong key), and
        # the owner identity is a fresh UUID per call, never body-derived
        # (see the design note §6 — a caller-supplied identity here would
        # let two genuinely concurrent calls "refresh" each other's claim
        # instead of correctly contending).
        claim_key = (provider_id, provider_session_id)
        claim_owner_id = uuid.uuid4().hex
        claim_result = claims.claim(
            session_id=claim_key,
            agent_id=agent_id,
            instance_id=claim_owner_id,
            lease_seconds=_dispatch_claim_lease_seconds(provider_id),
        )
        if isinstance(claim_result, ClaimRejected):
            self._send_json(
                409,
                {
                    "error": "DISPATCH_BUSY",
                    "provider_id": provider_id,
                    "provider_session_id": provider_session_id,
                    "current_agent_id": claim_result.current_agent_id,
                    "claim_expires_at": claim_result.claim_expires_at,
                },
            )
            return

        try:
            # Most-recent-REGISTER-for-a-session_id-wins (PresenceRegistry's
            # own documented rule) — this is Presence's own liveness/
            # discoverability bookkeeping (meaning 1 in the design note's
            # §9.4), independent of dispatch routing. Its outcome is never
            # read back for `binding`, which is already fixed above —
            # another caller overwriting this shared_session_id's Presence
            # record, even mid-call, cannot change what THIS call invokes.
            presence.register(
                agent_id=agent_id,
                instance_id=presence_instance_id,
                session_id=body["shared_session_id"],
                capabilities=["chat"],
                endpoint=ProviderSessionBinding.encode_endpoint(
                    provider_id=provider_id,
                    model_id=body["model_id"],
                    provider_session_id=provider_session_id,
                    launch_options=launch_options,
                ),
                requested_lease=float(body.get("requested_lease", 300.0)),
            )

            bridge = SharedSessionBridge(
                presence,
                ledger,
                provider_dispatch=dispatcher,
                continuity_cursor_tracker=cursor,
            )
            try:
                result = bridge.handle_turn(
                    session_id=body["shared_session_id"],
                    origin_body=body["origin_body"],
                    player_input=body["player_input"],
                    binding=binding,
                    snapshot=body.get("snapshot"),
                )
            except ProviderNotRegistered as exc:
                self._send_json(404, {"error": "PROVIDER_NOT_REGISTERED", "detail": str(exc)})
                return
            except ResponseActorMismatch as exc:
                self._send_json(409, {"error": "RESPONSE_ACTOR_MISMATCH", "detail": str(exc)})
                return
            except SessionUnavailable as exc:
                # item 3: raised by SessionLedger.append() itself — either
                # step 2's request append (the earliest possible point)
                # newly discovered the session is blocked (a first-touch
                # replay just failed, or the request append's own durable
                # write failed), or step 7's response append did. Either
                # way, no further /dispatch for this session_id until a
                # restart (poison) or an operator resolves the
                # quarantined file — never silently degrade to
                # in-memory-only service, per the crash-consistency
                # design's own durability-honesty requirement.
                self._send_session_unavailable(exc)
                return
            except _DISPATCH_FAILURE_EXCEPTIONS as exc:
                self._send_json(502, {"error": "PROVIDER_DISPATCH_FAILED", "detail": str(exc)})
                return
            self._send_json(200, result)
        finally:
            # Always released — success, any of the three caught failure
            # modes above, or any other exception that escapes this block
            # entirely. A `return` inside the try still runs this.
            claims.release(session_id=claim_key, claim_token=claim_result.claim_token)


def run(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, journal_root: Any = DEFAULT_JOURNAL_ROOT) -> None:
    # journal_root re-composes the module-level ledger only when it
    # differs from the default already installed above — avoids
    # discarding any state a caller (e.g. a test) already set on
    # `ledger`/`cursor` directly, matching the existing pattern for
    # presence/claims (module globals mutated in place by tests/tools
    # rather than passed through run()).
    global ledger
    if journal_root != DEFAULT_JOURNAL_ROOT:
        ledger = SessionLedger(journal_root=journal_root, cursor=cursor)
    server = ThreadingHTTPServer((host, port), PresenceAuthorityHandler)
    server.daemon_threads = True
    print(f"[presence-authority] listening on {host}:{port} journal_root={ledger._journal_root}", flush=True)
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
    parser.add_argument(
        "--journal-root",
        type=Path,
        default=DEFAULT_JOURNAL_ROOT,
        help="Directory for per-shared_session_id continuity journals (item 3). "
        "Pass a fresh empty directory to isolate a test/proof run from real state.",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    _args = _parse_args()
    run(host=_args.host, port=_args.port, journal_root=_args.journal_root)
