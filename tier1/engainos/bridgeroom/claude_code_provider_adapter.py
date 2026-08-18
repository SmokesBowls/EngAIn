"""
claude_code_provider_adapter.py - Second provider through a ProviderSessionBinding

Same interface as hermes_provider_adapter.dispatch_via_hermes_cli, proving
the point of that module's design: a second provider is a second small
adapter behind the same callable shape, not a second architecture.

    dispatch_via_claude_code_cli(binding: ProviderSessionBinding,
                                  context: List[Turn], player_input: str) -> dict

Does not decide who Claude Code is (Presence already did), does not decide
which provider/model/native session to use (the binding already did — see
provider_session_binding.py), and does not decide what conversation exists
(the Ledger already did). Only takes the binding and performs the
invocation.

Continuity mechanism: binding.provider_session_id is a real Claude Code
session UUID, minted by a `claude -p ... --output-format json` call made
once at REGISTER time (outside this module — same pattern as Hermes:
REGISTER requires the native session as an input, not an output of
dispatch). Every dispatch from here on resumes that exact native session
via `--resume`, which is where Claude Code's own continuity actually lives
— this adapter does not reconstruct conversation text from `context` and
inject it into the prompt, for the same reason hermes_provider_adapter.py
doesn't.

binding.provider_session_id must never be confused with
binding.shared_session_id — see provider_session_binding.py's module
docstring. Switching from Hermes to Claude Code means REGISTERing a new
binding with the same shared_session_id but a different provider_id/
provider_session_id; Claude Code cannot resume Hermes's native transcript,
and this module makes no attempt to.

Verified against the real CLI before being written (2026-08-16):
`claude -p "..." --output-format json` returns a single JSON object on
stdout containing `session_id`, `result` (the response text), and
`is_error`. `--resume <session_id>` preserves that same session_id in the
response and genuinely continues the conversation — confirmed with a real
two-turn recall test before this adapter existed.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from typing import Any, Dict, List

from tier1.engainos.core.provider_session_binding import ProviderSessionBinding
from tier1.engainos.core.session_ledger import Turn


class ClaudeCodeDispatchError(Exception):
    """The claude CLI process itself failed: missing executable, non-zero
    exit, timeout, unparseable JSON output, or is_error=true in the result."""


class ClaudeCodeSessionDrift(Exception):
    """Claude Code returned a session_id different from the one we asked it
    to --resume (binding.provider_session_id). Same as the equivalent
    check in hermes_provider_adapter.py: this checks *which native
    conversation* was answered from, not *who* answered."""


# The one authoritative source for how long a real dispatch through this
# adapter may run — dispatch_via_claude_code_cli's own default below and
# the presence authority server's dispatch-claim TTL (item 1's mutex) both
# read this, so the two can never silently drift out of sync with each
# other.
DEFAULT_TIMEOUT_S = 120.0


def _resolve_claude_executable() -> str:
    exe = shutil.which("claude")
    if exe is None:
        raise ClaudeCodeDispatchError("claude executable not found on PATH")
    return exe


def _build_argv(claude_exe: str, binding: ProviderSessionBinding, player_input: str) -> List[str]:
    argv = [claude_exe, "-p", player_input, "--output-format", "json"]
    if binding.model_id:
        argv += ["--model", binding.model_id]
    # Always resume the vendor-native session — REGISTER is the only place
    # a fresh Claude Code session may be minted (see module docstring).
    # Dispatch never starts a new one, and never uses shared_session_id here.
    argv += ["--resume", binding.provider_session_id]
    return argv


def dispatch_via_claude_code_cli(
    binding: ProviderSessionBinding,
    context: List[Turn],
    player_input: str,
    *,
    timeout_s: float = DEFAULT_TIMEOUT_S,
) -> Dict[str, Any]:
    claude_exe = _resolve_claude_executable()
    argv = _build_argv(claude_exe, binding, player_input)

    try:
        completed = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
    except subprocess.TimeoutExpired as exc:
        raise ClaudeCodeDispatchError(
            f"claude -p exceeded {timeout_s}s for provider_session_id={binding.provider_session_id!r}"
        ) from exc

    if completed.returncode != 0:
        raise ClaudeCodeDispatchError(
            f"claude -p exited {completed.returncode} for "
            f"provider_session_id={binding.provider_session_id!r}: {completed.stderr[-800:]}"
        )

    try:
        parsed = json.loads(completed.stdout)
    except ValueError as exc:
        raise ClaudeCodeDispatchError(
            f"claude -p produced non-JSON stdout: {completed.stdout[-800:]!r}"
        ) from exc

    if parsed.get("is_error"):
        raise ClaudeCodeDispatchError(f"claude -p returned is_error=true: {parsed!r}")

    returned_session_id = parsed.get("session_id")
    if returned_session_id != binding.provider_session_id:
        raise ClaudeCodeSessionDrift(
            f"asked to --resume {binding.provider_session_id!r}, "
            f"claude reported session_id={returned_session_id!r}"
        )

    response_text = str(parsed.get("result", "")).strip()
    return {
        "actor": binding.agent_id,
        "response": response_text,
        "prior_context_turns": len(context),  # audit only — never prompt content
    }
