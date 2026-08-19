"""
session_ledger.py - The shared conversation record (SHARED_SESSION_CONTINUITY_CONTRACT_v1)

One page every door writes on and reads from, keyed only by session_id.
origin_body is provenance metadata on a turn, never an identity, and never a
read filter a body may apply to itself (contract Section 3's governing
invariant: a turn belongs to the session, not to the door that carried it).

Scope note (Stage 4 tiny-implementation proof):
    In-memory, append-only list per session_id, for the lifetime of one
    process. Storage mechanism, retention, notification, and concurrent-write
    ordering are explicitly left open by the contract (its own Section 8) and
    are NOT decided here — turn_id is simply this process's list length,
    which is sufficient to prove the ordering invariant and nothing more.

Append-only is enforced structurally, not just by convention: Turn is a
frozen dataclass, and both append() and every read method hand back a
deepcopy rather than the internally stored object or its stored snapshot
dict. Without this, `ledger.read_last(sid).payload = "rewritten"` (or
mutating a snapshot dict passed into append() after the call returns) would
silently rewrite the Ledger's history with no new turn ever recorded —
exactly what "append-only" is supposed to forbid.

Concurrency (item 2, 2026-08-18 — see
08-18-2026-item2-session-ledger-semantic-derivation.md for the full
derivation): append()'s own turn_id assignment (`len(turns)`) and the
list insertion used to race — two threads appending to the SAME
session_id could read the same length before either inserted, minting a
duplicate turn_id. The contract (§8) only promises turn_id is unique and
monotonic per session_id; it does not require turn_id to equal list
position, but there's also no reason to give that useful, currently-true
equivalence up prematurely (a future persistence/reconstruction layer
would otherwise have to restore it separately). Fixed by making
"determine next turn_id + insert the Turn" one atomic operation per
session_id, via a lock scoped to that session_id alone — a session_id A
append never waits on a session_id B append. Reads (read_since/
read_last) are deliberately NOT locked: no caller was found that needs a
transactional snapshot across a concurrent append, and Python's own
list/GIL semantics already prevent a torn read of already-inserted
elements — adding read locks would strengthen the contract beyond what
any caller requires. This also does not extend to locking the
request/response transaction handle_turn() performs around a real
provider dispatch — see the design note for why that would silently
reintroduce a serialization guarantee the system doesn't have today and
would cost item 1's already-proven provider-dispatch concurrency for no
discovered benefit.
"""

from __future__ import annotations

import threading
import time
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class Turn:
    turn_id: int
    session_id: str
    origin_body: str
    direction: str          # "request" | "response"
    actor: str
    payload: str
    snapshot: Optional[dict] = None
    timestamp: float = field(default_factory=time.time)


class SessionLedger:
    def __init__(self) -> None:
        self._turns: Dict[str, List[Turn]] = {}
        # One lock per session_id, created lazily. _locks_guard protects
        # only the get-or-create of that per-session lock itself (a
        # handful of dict operations) — never the append work — so two
        # different session_ids' appends never wait on each other.
        self._locks: Dict[str, threading.Lock] = {}
        self._locks_guard = threading.Lock()

    def _lock_for(self, session_id: str) -> threading.Lock:
        with self._locks_guard:
            lock = self._locks.get(session_id)
            if lock is None:
                lock = threading.Lock()
                self._locks[session_id] = lock
            return lock

    def append(
        self,
        session_id: str,
        origin_body: str,
        direction: str,
        actor: str,
        payload: str,
        snapshot: Optional[dict] = None,
    ) -> Turn:
        if direction not in ("request", "response"):
            raise ValueError(f"MALFORMED_TURN: direction must be request/response, got {direction!r}")
        # The atomic boundary: determine this session_id's next turn_id
        # and insert the corresponding Turn as one operation. len(turns)
        # is not itself wrong — every SessionLedger starts empty and has
        # no path that loads pre-existing/non-contiguous turns (verified
        # against every real construction site; restart persistence
        # remains deferred) — the bug was the unsynchronized
        # len(turns) -> append() sequence, not this formula.
        with self._lock_for(session_id):
            turns = self._turns.setdefault(session_id, [])
            turn = Turn(
                turn_id=len(turns),
                session_id=session_id,
                origin_body=origin_body,
                direction=direction,
                actor=actor,
                payload=payload,
                snapshot=deepcopy(snapshot),
            )
            turns.append(turn)
        return deepcopy(turn)

    def read_last(self, session_id: str, direction: Optional[str] = None) -> Optional[Turn]:
        for turn in reversed(self._turns.get(session_id, [])):
            if direction is None or turn.direction == direction:
                return deepcopy(turn)
        return None

    def read_since(self, session_id: str, since_turn_id: int) -> List[Turn]:
        return [deepcopy(t) for t in self._turns.get(session_id, []) if t.turn_id > since_turn_id]
