"""
continuity_cursor_tracker.py - The real identity boundary for recap
decisions: native memory containers, not actor labels.

Corrects a mistake in continuity_context_builder.py's first version, which
triggered a recap by comparing agent_id/actor. That's wrong on both sides:

  - actor can stay the same while the native session underneath it changes
    (an expired Hermes session replaced by a fresh one, still labeled
    "hermes") — a recap would be wrongly skipped, and the fresh session
    would answer from nothing.
  - actor/origin_body can differ while the native session stays identical
    (two doors both currently resolving to the same active provider
    binding) — a recap would be wrongly duplicated into an already-current
    native session.

The only thing that actually determines whether a native session needs a
recap is whether IT has seen the Ledger turns in question — not what label
is currently attached to it. The identity that matters is:

    (provider_id, provider_session_id)

— the exact pair ProviderSessionBinding already carries, naming the actual
native memory container. This tracker records, per that pair, the newest
Ledger turn_id known to have actually reached it via a successful dispatch
round trip. A failed dispatch must never advance this — see
shared_session_bridge.py's placement of the advance() call, after the
response is validated and appended, never before or on any failure path.
"""

from __future__ import annotations

from typing import Dict, Tuple


class ContinuityCursorTracker:
    def __init__(self) -> None:
        self._cursors: Dict[Tuple[str, str], int] = {}

    def last_seen_turn_id(self, provider_id: str, provider_session_id: str) -> int:
        """-1 means this exact native session has never been successfully
        dispatched to before — every turn currently in the Ledger, if any,
        is missing from it."""
        return self._cursors.get((provider_id, provider_session_id), -1)

    def advance(self, provider_id: str, provider_session_id: str, turn_id: int) -> None:
        """Monotonic only — never lets a cursor move backward, in case of
        any out-of-order call (there is currently no concurrency around a
        single native session's dispatch, but this makes that assumption
        explicit rather than silent)."""
        key = (provider_id, provider_session_id)
        if turn_id > self._cursors.get(key, -1):
            self._cursors[key] = turn_id
