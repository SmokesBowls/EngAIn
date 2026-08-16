"""
presence_registry.py - Live provider presence (PROVIDER_PRESENCE_REGISTRY_CONTRACT_v1)

Answers exactly one question: is a specific instance of an already-authorized
agent reachable right now, under which session?

Does NOT answer, and must never be asked to answer, whether that agent is
allowed to act. That is agent_gateway.py's job alone. This module has no
import of, and no opinion about, agent_gateway.

Scope note (Stage 4 tiny-implementation proof):
    This is the smallest possible REGISTER/RESOLVE/DEREGISTER needed to prove
    the contract's shape. Persistence, retention, concurrent-writer ordering,
    and background lease-expiry sweeping are explicitly left open by the
    contract (see its own Section 8) and are NOT solved here. Storage is a
    plain in-memory dict for the lifetime of one process. Lease expiry is
    checked lazily on RESOLVE (time.time() vs lease_until), not swept by a
    timer.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, replace
from typing import Dict, List, Optional


@dataclass(frozen=True)
class PresenceRecord:
    """DYNAMIC / PRESENCE record — never merged with agent_gateway's
    STATIC / POLICY record (contract Section 5).

    Frozen, with capabilities stored as a tuple, so that a caller holding a
    record returned by resolve() cannot mutate the registry's own state out
    from under it (e.g. `record.agent_id = "someone-else"`), which would be
    an authority leak — a Presence record silently rewritten without ever
    going through REGISTER/RENEW."""

    agent_id: str
    instance_id: str
    session_id: str
    capabilities: tuple[str, ...]
    endpoint: Optional[str]
    lease_until: float


class PresenceRegistry:
    """In-memory REGISTER / RENEW / RESOLVE / DEREGISTER / EXPIRE.

    Keyed by session_id for RESOLVE, since that is what callers (the shared
    session bridge) actually have in hand. Keyed by instance_id internally
    for RENEW/DEREGISTER, since a session could in principle be resolved by
    more than one past instance over time (contract Gate 4 leaves this open;
    this proof does not attempt to resolve ambiguity beyond "most recent
    REGISTER for a session_id wins").
    """

    def __init__(self) -> None:
        self._by_session: Dict[str, PresenceRecord] = {}
        self._by_instance: Dict[str, PresenceRecord] = {}

    def register(
        self,
        agent_id: str,
        instance_id: str,
        session_id: str,
        capabilities: Optional[List[str]] = None,
        endpoint: Optional[str] = None,
        requested_lease: float = 300.0,
    ) -> PresenceRecord:
        record = PresenceRecord(
            agent_id=agent_id,
            instance_id=instance_id,
            session_id=session_id,
            capabilities=tuple(capabilities or ()),
            endpoint=endpoint,
            lease_until=time.time() + requested_lease,
        )
        self._by_session[session_id] = record
        self._by_instance[instance_id] = record
        return record

    def renew(self, instance_id: str, extend_by: float = 300.0) -> Optional[PresenceRecord]:
        """Renews a still-live lease. Deliberately does NOT resurrect an
        already-expired instance — the contract does not say RENEW may act
        as a second REGISTER, so an expired instance must go through
        REGISTER again, not RENEW. An expired record found here is expired
        (§4/§5's presence side), matching what resolve() already refuses."""
        record = self._by_instance.get(instance_id)
        if record is None:
            return None

        now = time.time()
        if record.lease_until <= now:
            self.expire(instance_id)
            return None

        renewed = replace(record, lease_until=now + extend_by)
        self._by_instance[instance_id] = renewed
        if self._by_session.get(record.session_id) is record:
            self._by_session[record.session_id] = renewed
        return renewed

    def resolve(self, session_id: str) -> Optional[PresenceRecord]:
        """RESOLVE. Returns None (→ PROVIDER_NOT_REGISTERED at the caller)
        when nothing was ever registered for this session, or when the last
        registration's lease has lapsed. The returned record is frozen, so
        no caller-side mutation risk exists (see PresenceRecord docstring)."""
        record = self._by_session.get(session_id)
        if record is None:
            return None
        if record.lease_until < time.time():
            return None
        return record

    def deregister(self, instance_id: str) -> bool:
        """Voluntary clean-exit path."""
        record = self._by_instance.pop(instance_id, None)
        if record is None:
            return False
        if self._by_session.get(record.session_id) is record:
            del self._by_session[record.session_id]
        return True

    def expire(self, instance_id: str) -> bool:
        """Involuntary path — same effect as deregister for this proof.
        A real lease-timeout sweep is out of scope here (see module docstring)."""
        return self.deregister(instance_id)
