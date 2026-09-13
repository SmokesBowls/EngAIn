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

Coordination-report addition (2026-09-12): a coordination_report
(the Editor coordination lane's engain.editor_report.v1, carried
separately from player_input — see /dispatch's own body and
SharedSessionBridge.handle_turn()'s parameter of the same name) may also
be folded into what gets dispatched, as its own clearly labeled block.
It is never concatenated with or substituted for player_input's own
text — see build()'s own doc below for exactly how the two stay
distinct.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from tier1.engainos.core.session_ledger import Turn


def _format_coordination_report(coordination_report: Dict[str, Any]) -> str:
    """Renders the Editor's coordination report as its own labeled block,
    textually distinct from both player_input and the missing-context
    recap below. Field access is defensive (.get with a default) — this
    builder does not validate the report's own shape; that already
    happened wherever it was produced (see godot_engain_3d_avatar's
    write_editor_report()/EDITOR_REPORT_KEYS validation) — a builder is
    the wrong place to re-litigate that."""
    status = coordination_report.get("status", "unknown")
    summary = coordination_report.get("execution_summary") or coordination_report.get("body", "")
    return (
        "EngAIn's Editor has a coordination report for you (not something "
        "the player said):\n"
        f"  status: {status}\n"
        f"  summary: {summary}"
    )


class ContinuityContextBuilder:
    """Stateless by design — every call is a pure function of the context,
    player_input, last_seen_turn_id, and (optionally) coordination_report
    handed to it. It does not own or look up cursor state itself;
    ContinuityCursorTracker does that, and the caller (SharedSessionBridge)
    supplies the answer."""

    def build(
        self,
        context: List[Turn],
        player_input: str,
        last_seen_turn_id: int,
        coordination_report: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Returns the string to actually dispatch. Equal to player_input,
        unmodified, whenever the target native session has already seen
        everything currently in context (last_seen_turn_id covers it) AND
        no coordination_report accompanies this turn — unchanged from
        this function's pre-existing behavior in either respect.

        coordination_report, when present, is prepended as its own block
        (see _format_coordination_report()) — structurally the same
        treatment as the missing-context recap below: both wrap around
        player_input, neither ever rewrites or merges into it. This is
        what "carried separately from player_input" means in practice:
        by construction, not by convention."""
        missing = [t for t in context if t.turn_id > last_seen_turn_id]
        if not missing and coordination_report is None:
            return player_input

        blocks: List[str] = []
        if coordination_report is not None:
            blocks.append(_format_coordination_report(coordination_report))

        if missing:
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
            blocks.append("\n".join(lines))

        blocks.append(f"Now: {player_input}")
        return "\n\n".join(blocks)
