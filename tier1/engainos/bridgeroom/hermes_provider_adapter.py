"""
hermes_provider_adapter.py - Real provider dispatch through PresenceRecord.endpoint

The first non-stub implementation of the SharedSessionBridge's
`provider_dispatch` callable (see shared_session_bridge.py). Matches the
stub's exact call signature, so it is a drop-in replacement:

    dispatch_via_hermes_cli(record: PresenceRecord, context: List[Turn],
                             player_input: str) -> dict

This module does not decide who Hermes is (Presence already did — record is
handed to it, already resolved) and does not decide what conversation
exists (the Ledger already did — context is handed to it, already read). It
only takes the resolved endpoint and performs the actual provider
invocation.

Continuity mechanism: PresenceRecord.session_id is a real Hermes CLI session
id, minted by a `hermes chat` call made once at REGISTER time (outside this
module — REGISTER already requires session_id as an input, not an output;
see PROVIDER_PRESENCE_REGISTRY_CONTRACT_v1's REGISTER operation). Every
dispatch from here on resumes that exact session via `--resume`, which is
where Hermes's own continuity actually lives — this adapter does not
reconstruct conversation text from `context` and inject it into the prompt;
that would create a second, competing memory of the conversation, which is
exactly what the continuity contract forbids (its own Section 3: a body, or
anything acting like one, must not hold private conversation state). The
`context` argument is accepted, for shape-compatibility with the stub and so
a future adapter revision can use it for audit/cross-check, but the current
implementation's only use of it is to record how many prior turns existed at
dispatch time — never as prompt content.

Endpoint shape (deliberately explicit and boring, per instruction): a JSON
string, e.g. '{"provider": "openai-codex", "model": "gpt-5.6-sol"}'. Both
keys optional — when absent, hermes's own configured default provider/model
is used, not a value hardcoded here. This module never chooses a default
provider or model of its own; it only relays what PresenceRecord.endpoint
says, exactly like it only relays what Presence and the Ledger say.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from typing import Any, Dict, List, Optional

from tier1.engainos.core.presence_registry import PresenceRecord
from tier1.engainos.core.session_ledger import Turn

HERMES_SESSION_ID_PATTERN = re.compile(r"(?m)^session_id:\s*([^\s]+)\s*$")


class HermesDispatchError(Exception):
    """The hermes CLI process itself failed: missing executable, non-zero
    exit, timeout, or output that doesn't contain a parseable session_id."""


class HermesSessionDrift(Exception):
    """Hermes returned a session_id different from the one we asked it to
    --resume. Distinct from ResponseActorMismatch (shared_session_bridge.py):
    that gate checks *who* answered; this checks *which conversation* they
    answered from. A drifted session must not be treated as a valid
    continuation of this session_id, even if the actor name matches."""


def _parse_endpoint(endpoint: Optional[str]) -> Dict[str, str]:
    if not endpoint:
        return {}
    try:
        parsed = json.loads(endpoint)
    except (TypeError, ValueError) as exc:
        raise HermesDispatchError(f"PresenceRecord.endpoint is not valid JSON: {endpoint!r}") from exc
    if not isinstance(parsed, dict):
        raise HermesDispatchError(f"PresenceRecord.endpoint must decode to an object: {endpoint!r}")
    return parsed


def _resolve_hermes_executable() -> str:
    exe = shutil.which("hermes")
    if exe is None:
        raise HermesDispatchError("hermes executable not found on PATH")
    return exe


def _build_argv(hermes_exe: str, record: PresenceRecord, player_input: str) -> List[str]:
    endpoint = _parse_endpoint(record.endpoint)
    argv = [hermes_exe, "chat", "-Q", "--pass-session-id", "--ignore-rules", "--source", "tool"]
    if endpoint.get("provider"):
        argv += ["--provider", endpoint["provider"]]
    if endpoint.get("model"):
        argv += ["-m", endpoint["model"]]
    # Always resume — REGISTER is the only place a fresh Hermes session may
    # be minted (see module docstring). Dispatch never starts a new one.
    argv += ["--resume", record.session_id]
    argv += ["-q", player_input]
    return argv


def dispatch_via_hermes_cli(
    record: PresenceRecord,
    context: List[Turn],
    player_input: str,
    *,
    timeout_s: float = 90.0,
) -> Dict[str, Any]:
    hermes_exe = _resolve_hermes_executable()
    argv = _build_argv(hermes_exe, record, player_input)

    try:
        completed = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
    except subprocess.TimeoutExpired as exc:
        raise HermesDispatchError(
            f"hermes chat exceeded {timeout_s}s for session_id={record.session_id!r}"
        ) from exc

    if completed.returncode != 0:
        raise HermesDispatchError(
            f"hermes chat exited {completed.returncode} for session_id={record.session_id!r}: "
            f"{completed.stderr[-800:]}"
        )

    match = HERMES_SESSION_ID_PATTERN.search(completed.stderr)
    if match is None:
        raise HermesDispatchError(
            f"hermes chat produced no parseable session_id in stderr: {completed.stderr[-800:]!r}"
        )
    returned_session_id = match.group(1)
    if returned_session_id != record.session_id:
        raise HermesSessionDrift(
            f"asked to --resume {record.session_id!r}, hermes reported session_id={returned_session_id!r}"
        )

    response_text = completed.stdout.strip()
    return {
        "actor": record.agent_id,
        "response": response_text,
        "prior_context_turns": len(context),  # audit only — never prompt content
    }
