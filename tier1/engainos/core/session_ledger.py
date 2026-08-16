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
"""

from __future__ import annotations

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
