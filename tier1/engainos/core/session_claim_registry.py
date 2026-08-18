"""
session_claim_registry.py - Per-dispatch mutual exclusion on a live session_id

Separate from PresenceRegistry on purpose. Presence answers "is an instance
reachable for this session" (a longer-lived liveness lease). This answers a
different, narrower question: "who, right now, holds the right to actually
send the next message to this session's provider" — a short-lived mutex held
only for the duration of one dispatch call.

Why this exists at all: two worker processes (the 2D avatar's mailbox worker
and the 3D avatar's mailbox worker) can both be registered as reachable for
the same underlying Hermes session_id at the same time — that's expected and
fine, presence isn't exclusive. What must never happen is both of them
actually calling `hermes chat --resume <session_id>` concurrently, which
could interleave or corrupt one live transcript. CLAIM is the lock around
that specific window; REGISTER/RESOLVE never provided one.

Thread-safe: a single process (the shared presence authority server) holds
one instance of this behind one lock, so "check current claim, then set the
new one" is atomic across every worker process talking to it over HTTP —
which is the entire point. Two separate in-process registries, one per
worker, would not provide this; that was the mistake this module corrects.

Key generalization (item 1, dispatch mutex): the public /claim and /release
HTTP endpoints still only ever pass a plain str session_id — that JSON
contract is unchanged, and every existing string-keyed caller (the
worker-level default-path claim in hermes_session_adapter.py) continues to
work exactly as before. presence_authority_server.py's own /dispatch
handler additionally calls claim()/release() directly, in-process, with a
composite (provider_id, provider_session_id) tuple key — the real identity
of the native transcript being protected (see
08-18-2026-item1-dispatch-mutex-design-analysis.md for why a bare
session_id is the wrong key once bindings can be overridden). Nothing below
cares which shape a key is — only that it is hashable and stable for the
life of one claim — so this widening is a type generalization, not a
semantic change: "who holds the right to dispatch to this key, right now"
means the same thing whether the key is a str or a (provider_id,
provider_session_id) tuple.
"""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass
from typing import Dict, Optional, Union

ClaimKey = Union[str, "tuple[str, str]"]


@dataclass(frozen=True)
class SessionClaim:
    session_id: ClaimKey
    agent_id: str
    instance_id: str
    claim_token: str
    claim_expires_at: float


@dataclass(frozen=True)
class ClaimRejected:
    reason: str  # "SESSION_OCCUPIED"
    current_agent_id: str
    current_instance_id: str
    claim_expires_at: float


class SessionClaimRegistry:
    def __init__(self) -> None:
        self._claims: Dict[ClaimKey, SessionClaim] = {}
        self._lock = threading.Lock()

    def claim(
        self,
        session_id: ClaimKey,
        agent_id: str,
        instance_id: str,
        lease_seconds: float = 200.0,
    ):
        """Atomically claim session_id for the caller, unless someone else
        already holds an unexpired claim on it. Returns a SessionClaim on
        success, a ClaimRejected on failure — never raises for the ordinary
        contention case, since losing a race for a shared resource is not
        exceptional, it's the expected outcome for the loser."""
        now = time.time()
        with self._lock:
            existing = self._claims.get(session_id)
            if existing is not None and existing.claim_expires_at > now and existing.instance_id != instance_id:
                return ClaimRejected(
                    reason="SESSION_OCCUPIED",
                    current_agent_id=existing.agent_id,
                    current_instance_id=existing.instance_id,
                    claim_expires_at=existing.claim_expires_at,
                )
            new_claim = SessionClaim(
                session_id=session_id,
                agent_id=agent_id,
                instance_id=instance_id,
                claim_token=uuid.uuid4().hex,
                claim_expires_at=now + lease_seconds,
            )
            self._claims[session_id] = new_claim
            return new_claim

    def release(self, session_id: ClaimKey, claim_token: str) -> bool:
        """Explicit release after a successful dispatch. Only the exact
        claim_token holder may release — a stale/foreign token cannot clear
        someone else's active claim."""
        with self._lock:
            existing = self._claims.get(session_id)
            if existing is None or existing.claim_token != claim_token:
                return False
            del self._claims[session_id]
            return True

    def current(self, session_id: ClaimKey) -> Optional[SessionClaim]:
        """Read-only inspection. An expired claim reads as absent — the
        short lease is exactly what recovers a crashed holder without
        requiring an explicit release (module docstring)."""
        with self._lock:
            existing = self._claims.get(session_id)
        if existing is None or existing.claim_expires_at <= time.time():
            return None
        return existing
