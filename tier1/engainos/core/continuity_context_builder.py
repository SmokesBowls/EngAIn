"""
continuity_context_builder.py - Moves ledger-context injection out of proof
scripts and into the real dispatch path.

live_cross_provider_portability_proof.py (2026-08-16) hand-wrote the recap
prose for each provider switch directly in the proof script — real, but not
production: nothing about a real mailbox request would ever come in
pre-annotated with "here is what the other provider said." This module is
that missing piece, made real and reusable: given the Ledger context
SharedSessionBridge.handle_turn() already reads, and the actor about to
answer next, decide whether a recap is needed at all, and build it the same
way every time — not by hand, per script, per test.

The rule this encodes, generalized from the proof: a provider resuming its
OWN prior turn already has that memory natively (that is the entire point
of provider_session_id/--resume — see provider_session_binding.py's module
docstring). Injecting a recap on every turn regardless would be exactly the
"second, competing memory of the conversation" the provider adapters'
docstrings already forbid. A recap is only warranted, and only injected,
when the actor about to answer is different from whoever produced the most
recent response — i.e., exactly at a provider switch, and only then.

This builder never touches the Ledger's own record of what the player
said — SharedSessionBridge still appends the bare, unmodified player_input
at step 2, before this runs. This only affects what gets *dispatched*, at
step 5, never what gets *recorded*.
"""

from __future__ import annotations

from typing import List, Optional

from tier1.engainos.core.session_ledger import Turn


class ContinuityContextBuilder:
    """Stateless by design — every call is a pure function of the context
    and player_input handed to it. Kept as a class (rather than a bare
    function) because a future revision may want to hold provider-specific
    formatting preferences; none exist yet, and none are invented here."""

    def build(
        self,
        context: List[Turn],
        player_input: str,
        target_agent_id: str,
    ) -> str:
        """Returns the string to actually dispatch. Equal to player_input,
        unmodified, whenever no recap is warranted — same provider
        continuing, or no prior context to recap at all."""
        last_response = self._last_response(context)
        if last_response is None or last_response.actor == target_agent_id:
            return player_input

        lines = [
            "You are taking over this session from a different provider "
            "you have no memory of. Here is EngAIn's own record of the "
            "relevant prior exchange, not your own memory:",
        ]
        for turn in context:
            if turn.direction == "request":
                lines.append(f"  User said: {turn.payload!r}")
            else:
                lines.append(f"  A different assistant ({turn.actor}) replied: {turn.payload!r}")
        lines.append(f"Now: {player_input}")
        return "\n".join(lines)

    @staticmethod
    def _last_response(context: List[Turn]) -> Optional[Turn]:
        for turn in reversed(context):
            if turn.direction == "response":
                return turn
        return None
