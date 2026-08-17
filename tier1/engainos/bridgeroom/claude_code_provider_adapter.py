"""
claude_code_provider_adapter.py - Second provider through PresenceRecord.endpoint

Same interface as hermes_provider_adapter.dispatch_via_hermes_cli, proving
the point of that module's design: a second provider is a second small
adapter behind the same callable shape, not a second architecture.

    dispatch_via_claude_code_cli(record: PresenceRecord, context: List[Turn],
                                  player_input: str) -> dict

Does not decide who Claude Code is (Presence already did) and does not
decide what conversation exists (the Ledger already did). Only takes the
resolved endpoint and performs the invocation.

Continuity mechanism: PresenceRecord.session_id is a real Claude Code
session UUID, minted by a `claude -p ... --output-format json` call made
once at REGISTER time (outside this module — same pattern as Hermes: REGISTER
requires session_id as an input, not an output of dispatch). Every dispatch
from here on resumes that exact session via `--resume`, which is where
Claude Code's own continuity actually lives — this adapter does not
reconstruct conversation text from `context` and inject it into the prompt,
for the same reason hermes_provider_adapter.py doesn't: that would create a
second, competing memory of the conversation.

Endpoint shape: a JSON string, e.g. '{"model": "sonnet"}'. The key is
optional — when absent, Claude Code's own configured default model is used,
never a value hardcoded here.

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
from typing import Any, Dict, List, Optional

from tier1.engainos.core.presence_registry import PresenceRecord
from tier1.engainos.core.session_ledger import Turn


class ClaudeCodeDispatchError(Exception):
    """The claude CLI process itself failed: missing executable, non-zero
    exit, timeout, unparseable JSON output, or is_error=true in the result."""


class ClaudeCodeSessionDrift(Exception):
    """Claude Code returned a session_id different from the one we asked it
    to --resume. Distinct from ResponseActorMismatch (shared_session_bridge.py),
    same as the equivalent check in hermes_provider_adapter.py: this checks
    *which conversation* was answered from, not *who* answered."""


def _parse_endpoint(endpoint: Optional[str]) -> Dict[str, str]:
    if not endpoint:
        return {}
    try:
        parsed = json.loads(endpoint)
    except (TypeError, ValueError) as exc:
        raise ClaudeCodeDispatchError(f"PresenceRecord.endpoint is not valid JSON: {endpoint!r}") from exc
    if not isinstance(parsed, dict):
        raise ClaudeCodeDispatchError(f"PresenceRecord.endpoint must decode to an object: {endpoint!r}")
    return parsed


def _resolve_claude_executable() -> str:
    exe = shutil.which("claude")
    if exe is None:
        raise ClaudeCodeDispatchError("claude executable not found on PATH")
    return exe


def _build_argv(claude_exe: str, record: PresenceRecord, player_input: str) -> List[str]:
    endpoint = _parse_endpoint(record.endpoint)
    argv = [claude_exe, "-p", player_input, "--output-format", "json"]
    if endpoint.get("model"):
        argv += ["--model", endpoint["model"]]
    # Always resume — REGISTER is the only place a fresh Claude Code session
    # may be minted (see module docstring). Dispatch never starts a new one.
    argv += ["--resume", record.session_id]
    return argv


def dispatch_via_claude_code_cli(
    record: PresenceRecord,
    context: List[Turn],
    player_input: str,
    *,
    timeout_s: float = 120.0,
) -> Dict[str, Any]:
    claude_exe = _resolve_claude_executable()
    argv = _build_argv(claude_exe, record, player_input)

    try:
        completed = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
    except subprocess.TimeoutExpired as exc:
        raise ClaudeCodeDispatchError(
            f"claude -p exceeded {timeout_s}s for session_id={record.session_id!r}"
        ) from exc

    if completed.returncode != 0:
        raise ClaudeCodeDispatchError(
            f"claude -p exited {completed.returncode} for session_id={record.session_id!r}: "
            f"{completed.stderr[-800:]}"
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
    if returned_session_id != record.session_id:
        raise ClaudeCodeSessionDrift(
            f"asked to --resume {record.session_id!r}, claude reported session_id={returned_session_id!r}"
        )

    response_text = str(parsed.get("result", "")).strip()
    return {
        "actor": record.agent_id,
        "response": response_text,
        "prior_context_turns": len(context),  # audit only — never prompt content
    }
