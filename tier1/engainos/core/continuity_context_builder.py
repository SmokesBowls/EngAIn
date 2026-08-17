"""
continuity_context_builder.py - Moves ledger-context injection out of proof
scripts and into the real dispatch path.

Corrected (2026-08-17): the first version decided whether to recap by
comparing agent_id/actor labels. That is the wrong identity boundary — see
continuity_cursor_tracker.py's module docstring for the concrete failure
cases (a same-labeled actor whose native session was silently replaced;
two different doors resolving to the same still-current native session).
This version takes last_seen_turn_id — the ContinuityCursorTracker's
answer for the exact (provider_id, provider_session_id) pair about to be
dispatched to — and recaps precisely the Ledger turns that pair has not
seen. Nothing here compares actor names anymore.

The rule this encodes, generalized from the proof: a native session that
has already seen a Ledger turn — whether because it produced the response
itself, or because an earlier dispatch already recapped it — must not be
told about it again. Injecting a redundant recap would be exactly the
"second, competing memory of the conversation" the provider adapters'
docstrings already forbid. A recap is warranted only for the turns a given
native session has not yet observed, and only those turns.

This builder never touches the Ledger's own record of what the player
said — SharedSessionBridge still appends the bare, unmodified player_input
at step 2, before this runs. This only affects what gets *dispatched*, at
step 5, never what gets *recorded*.
"""

from __future__ import annotations

from typing import List

from tier1.engainos.core.session_ledger import Turn


class ContinuityContextBuilder:
    """Stateless by design — every call is a pure function of the context,
    player_input, and last_seen_turn_id handed to it. It does not own or
    look up cursor state itself; ContinuityCursorTracker does that, and the
    caller (SharedSessionBridge) supplies the answer."""

    def build(
        self,
        context: List[Turn],
        player_input: str,
        last_seen_turn_id: int,
    ) -> str:
        """Returns the string to actually dispatch. Equal to player_input,
        unmodified, whenever the target native session has already seen
        everything currently in context (last_seen_turn_id covers it)."""
        missing = [t for t in context if t.turn_id > last_seen_turn_id]
        if not missing:
            return player_input

        lines = [
            "This native session does not have the following prior turns "
            "in its own memory (either because it is new, or because a "
            "different provider session handled them). Here is EngAIn's "
            "own record of what it is missing:",
        ]
        for turn in missing:
            if turn.direction == "request":
                lines.append(f"  User said: {turn.payload!r}")
            else:
                lines.append(f"  A different assistant ({turn.actor}) replied: {turn.payload!r}")
        lines.append(f"Now: {player_input}")
        return "\n".join(lines)
