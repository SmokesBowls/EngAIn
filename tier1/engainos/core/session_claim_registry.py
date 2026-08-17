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
"""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class SessionClaim:
    session_id: str
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
        self._claims: Dict[str, SessionClaim] = {}
        self._lock = threading.Lock()

    def claim(
        self,
        session_id: str,
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

    def release(self, session_id: str, claim_token: str) -> bool:
        """Explicit release after a successful dispatch. Only the exact
        claim_token holder may release — a stale/foreign token cannot clear
        someone else's active claim."""
        with self._lock:
            existing = self._claims.get(session_id)
            if existing is None or existing.claim_token != claim_token:
                return False
            del self._claims[session_id]
            return True

    def current(self, session_id: str) -> Optional[SessionClaim]:
        """Read-only inspection. An expired claim reads as absent — the
        short lease is exactly what recovers a crashed holder without
        requiring an explicit release (module docstring)."""
        with self._lock:
            existing = self._claims.get(session_id)
        if existing is None or existing.claim_expires_at <= time.time():
            return None
        return existing
