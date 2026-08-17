"""
hermes_provider_adapter.py - Real provider dispatch through a ProviderSessionBinding

The first non-stub implementation of the SharedSessionBridge's
`provider_dispatch` callable (see shared_session_bridge.py). Matches the
stub's exact call signature, so it is a drop-in replacement:

    dispatch_via_hermes_cli(binding: ProviderSessionBinding,
                             context: List[Turn], player_input: str) -> dict

This module does not decide who Hermes is (Presence already did), does not
decide which provider/model/native session to use (the binding already
did — see provider_session_binding.py), and does not decide what
conversation exists (the Ledger already did — context is handed to it,
already read). It only takes the binding and performs the actual provider
invocation.

Continuity mechanism: binding.provider_session_id is a real Hermes CLI
session id, minted by a `hermes chat` call made once at REGISTER time
(outside this module — REGISTER already requires the native session as an
input, not an output; see PROVIDER_PRESENCE_REGISTRY_CONTRACT_v1's REGISTER
operation and ProviderSessionBinding.encode_endpoint). Every dispatch from
here on resumes that exact native session via `--resume`, which is where
Hermes's own continuity actually lives — this adapter does not reconstruct
conversation text from `context` and inject it into the prompt; that would
create a second, competing memory of the conversation, which is exactly
what the continuity contract forbids. The `context` argument is accepted
for shape-compatibility with the stub and future audit/cross-check use;
today it is only used to record how many prior turns existed at dispatch
time — never as prompt content.

binding.provider_session_id must never be confused with
binding.shared_session_id — see provider_session_binding.py's module
docstring for why that conflation is exactly the bug this split fixes.
The old two-key endpoint shape ({"provider": ..., "model": ...}) is gone;
hermes's own internal --provider flag (e.g. "openai-codex", distinct from
EngAIn's own provider_id="hermes") now lives in binding.launch_options,
since it is Hermes-specific plumbing, not a universal binding concept.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from typing import Any, Dict, List

from tier1.engainos.core.provider_session_binding import ProviderSessionBinding
from tier1.engainos.core.session_ledger import Turn

HERMES_SESSION_ID_PATTERN = re.compile(r"(?m)^session_id:\s*([^\s]+)\s*$")


class HermesDispatchError(Exception):
    """The hermes CLI process itself failed: missing executable, non-zero
    exit, timeout, or output that doesn't contain a parseable session_id."""


class HermesSessionDrift(Exception):
    """Hermes returned a session_id different from the one we asked it to
    --resume (binding.provider_session_id). Distinct from
    ResponseActorMismatch (shared_session_bridge.py): that gate checks
    *who* answered; this checks *which native conversation* they answered
    from. A drifted session must not be treated as a valid continuation,
    even if the actor name matches."""


def _resolve_hermes_executable() -> str:
    exe = shutil.which("hermes")
    if exe is None:
        raise HermesDispatchError("hermes executable not found on PATH")
    return exe


def _build_argv(hermes_exe: str, binding: ProviderSessionBinding, player_input: str) -> List[str]:
    argv = [hermes_exe, "chat", "-Q", "--pass-session-id", "--ignore-rules", "--source", "tool"]
    launch_provider = binding.launch_options.get("provider")
    if launch_provider:
        argv += ["--provider", launch_provider]
    if binding.model_id:
        argv += ["-m", binding.model_id]
    # Always resume the vendor-native session — REGISTER is the only place
    # a fresh Hermes session may be minted (see module docstring). Dispatch
    # never starts a new one, and never uses shared_session_id here.
    argv += ["--resume", binding.provider_session_id]
    argv += ["-q", player_input]
    return argv


def dispatch_via_hermes_cli(
    binding: ProviderSessionBinding,
    context: List[Turn],
    player_input: str,
    *,
    timeout_s: float = 90.0,
) -> Dict[str, Any]:
    hermes_exe = _resolve_hermes_executable()
    argv = _build_argv(hermes_exe, binding, player_input)

    try:
        completed = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
    except subprocess.TimeoutExpired as exc:
        raise HermesDispatchError(
            f"hermes chat exceeded {timeout_s}s for provider_session_id={binding.provider_session_id!r}"
        ) from exc

    if completed.returncode != 0:
        raise HermesDispatchError(
            f"hermes chat exited {completed.returncode} for "
            f"provider_session_id={binding.provider_session_id!r}: {completed.stderr[-800:]}"
        )

    match = HERMES_SESSION_ID_PATTERN.search(completed.stderr)
    if match is None:
        raise HermesDispatchError(
            f"hermes chat produced no parseable session_id in stderr: {completed.stderr[-800:]!r}"
        )
    returned_session_id = match.group(1)
    if returned_session_id != binding.provider_session_id:
        raise HermesSessionDrift(
            f"asked to --resume {binding.provider_session_id!r}, "
            f"hermes reported session_id={returned_session_id!r}"
        )

    response_text = completed.stdout.strip()
    return {
        "actor": binding.agent_id,
        "response": response_text,
        "prior_context_turns": len(context),  # audit only — never prompt content
    }
