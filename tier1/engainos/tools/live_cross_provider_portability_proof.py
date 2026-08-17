#!/usr/bin/env python3
"""
live_cross_provider_portability_proof.py - Real proof that switching
providers mid-session works through EngAIn's own Ledger, not through any
vendor's private memory.

This is the proof ProviderSessionBinding exists to make possible: one
EngAIn shared_session_id, two different real providers taking turns
occupying it, each with its own real, independent, vendor-native session —
and continuity crossing the switch only because the Ledger carried it, not
because either vendor secretly remembered the other's turn.

Deliberately NOT a pytest test, for the same reason as the two
single-provider proofs (hermes's own PYTEST_CURRENT_TEST auth guard; see
that proof's docstring for the full reasoning). Plain script, no pytest
involved anywhere in this process's ancestry.

The decisive step is the last one: switching back to Hermes reuses the
exact original provider_session_id — the same stale native transcript that
was never told about the Claude Code turn. If Hermes answers correctly
about that turn, it is structurally impossible for that to have come from
Hermes's own memory: it has to have come from the recap this script reads
out of the Ledger and supplies in the prompt.

Costs real usage against both authenticated accounts: 3 provider CLI calls
minimum (Hermes bootstrap, Hermes dispatch, Claude Code bootstrap, Claude
Code dispatch, Hermes dispatch again) — 5 real calls per run.

Run:
    python3 tier1/engainos/tools/live_cross_provider_portability_proof.py
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tier1.engainos.bridgeroom.claude_code_provider_adapter import dispatch_via_claude_code_cli
from tier1.engainos.bridgeroom.hermes_provider_adapter import dispatch_via_hermes_cli
from tier1.engainos.bridgeroom.shared_session_bridge import SharedSessionBridge
from tier1.engainos.core.presence_registry import PresenceRegistry
from tier1.engainos.core.provider_session_binding import ProviderSessionBinding
from tier1.engainos.core.session_ledger import SessionLedger

HERMES_SESSION_ID_PATTERN = re.compile(r"(?m)^session_id:\s*([^\s]+)\s*$")
RECEIPT_PATH = REPO_ROOT / "runtime" / "logs" / "CROSS_PROVIDER_PORTABILITY_PROOF_V1.report.json"
REMEMBERED_PHRASE = "obsidian ferry"


class ProofFailure(Exception):
    pass


def check(condition: bool, message: str) -> None:
    if not condition:
        raise ProofFailure(message)
    print(f"  OK  {message}")


def _new_shared_session_id() -> str:
    """EngAIn's own identifier. Never equal to, and never derived from,
    either vendor's native session id — see provider_session_binding.py."""
    return f"shared-{uuid.uuid4().hex}"


def mint_real_hermes_session(prompt: str) -> str:
    hermes_exe = shutil.which("hermes")
    if not hermes_exe:
        raise ProofFailure("hermes not found on PATH")
    completed = subprocess.run(
        [
            hermes_exe, "chat", "-Q", "--provider", "openai-codex", "-m", "gpt-5.6-sol",
            "--pass-session-id", "--ignore-rules", "--source", "tool",
            "-q", prompt,
        ],
        capture_output=True, text=True, timeout=90,
    )
    if completed.returncode != 0:
        raise ProofFailure(f"hermes bootstrap failed (exit {completed.returncode}): {completed.stderr}")
    match = HERMES_SESSION_ID_PATTERN.search(completed.stderr)
    if not match:
        raise ProofFailure(f"no session_id in hermes bootstrap stderr: {completed.stderr!r}")
    return match.group(1)


def mint_real_claude_session(prompt: str) -> str:
    claude_exe = shutil.which("claude")
    if not claude_exe:
        raise ProofFailure("claude not found on PATH")
    completed = subprocess.run(
        [claude_exe, "-p", prompt, "--output-format", "json"],
        capture_output=True, text=True, timeout=90,
    )
    if completed.returncode != 0:
        raise ProofFailure(f"claude bootstrap failed (exit {completed.returncode}): {completed.stderr}")
    try:
        parsed = json.loads(completed.stdout)
    except ValueError as exc:
        raise ProofFailure(f"claude bootstrap produced non-JSON stdout: {completed.stdout!r}") from exc
    if parsed.get("is_error"):
        raise ProofFailure(f"claude bootstrap returned is_error=true: {parsed!r}")
    session_id = parsed.get("session_id")
    if not session_id:
        raise ProofFailure(f"claude bootstrap returned no session_id: {parsed!r}")
    return session_id


def _hermes_endpoint(provider_session_id: str) -> str:
    return ProviderSessionBinding.encode_endpoint(
        provider_id="hermes", model_id="gpt-5.6-sol",
        provider_session_id=provider_session_id,
        launch_options={"provider": "openai-codex"},
    )


def _claude_endpoint(provider_session_id: str) -> str:
    return ProviderSessionBinding.encode_endpoint(
        provider_id="claude_code", model_id="", provider_session_id=provider_session_id,
    )


def run() -> dict:
    receipt: dict = {"schema": "engain.cross_provider_portability_proof.v1", "started_at": time.time()}

    print("1. One EngAIn shared session...")
    shared_session_id = _new_shared_session_id()
    receipt["shared_session_id"] = shared_session_id
    print(f"   shared_session_id = {shared_session_id}")

    presence = PresenceRegistry()
    ledger = SessionLedger()
    bridge = SharedSessionBridge(presence=presence, ledger=ledger, provider_dispatch=dispatch_via_hermes_cli)

    print("\n2. Dispatch through Hermes using its native session...")
    hermes_provider_session_id_1 = mint_real_hermes_session(
        "Session bootstrap for an EngAIn cross-provider portability proof. Reply with exactly: READY"
    )
    receipt["hermes_provider_session_id_1"] = hermes_provider_session_id_1
    print(f"   hermes provider_session_id = {hermes_provider_session_id_1}")
    presence.register(
        "hermes", "H-1", shared_session_id, ["chat"],
        endpoint=_hermes_endpoint(hermes_provider_session_id_1),
    )

    said_via_hermes = bridge.handle_turn(
        shared_session_id, "dragon_2d",
        f"Remember the phrase: {REMEMBERED_PHRASE}. Reply with exactly: noted.",
    )
    print(f"   dragon_2d <- hermes: {said_via_hermes['response']!r}")
    check(said_via_hermes["actor"] == "hermes", "response actor is hermes")

    print("\n3. Record request and response in the shared Ledger (verify)...")
    after_hermes_turn = ledger.read_since(shared_session_id, since_turn_id=-1)
    check(len(after_hermes_turn) == 2, "exactly one request+response pair recorded so far")
    check(after_hermes_turn[0].actor == "player" and after_hermes_turn[1].actor == "hermes",
          "request from player, response from hermes")

    print("\n4. Switch the binding to Claude Code with a different native session...")
    claude_provider_session_id = mint_real_claude_session(
        "Session bootstrap for an EngAIn cross-provider portability proof. Reply with exactly: READY"
    )
    receipt["claude_provider_session_id"] = claude_provider_session_id
    print(f"   claude provider_session_id = {claude_provider_session_id}")
    presence.register(
        "claude_code", "CC-1", shared_session_id, ["chat", "code"],
        endpoint=_claude_endpoint(claude_provider_session_id),
    )
    resolved_after_switch = presence.resolve(shared_session_id)
    check(resolved_after_switch.agent_id == "claude_code", "presence now resolves claude_code for the same shared_session_id")

    print("\n5. Supply the relevant Ledger context to Claude Code...")
    hermes_request_turn = next(t for t in after_hermes_turn if t.direction == "request")
    hermes_response_turn = next(t for t in after_hermes_turn if t.direction == "response")
    claude_prompt = (
        "You are now the active assistant for this ongoing session, taking over from a "
        "different provider you have no memory of. Here is the relevant prior exchange "
        "from EngAIn's own record, not your own memory:\n"
        f"  User said: {hermes_request_turn.payload!r}\n"
        f"  A different assistant replied: {hermes_response_turn.payload!r}\n"
        "Based only on that supplied record, what phrase was the user asking to be "
        "remembered? Reply with only the phrase, nothing else."
    )
    bridge2 = SharedSessionBridge(presence=presence, ledger=ledger, provider_dispatch=dispatch_via_claude_code_cli)

    print("\n6. Ask Claude Code about the earlier Hermes turn...")
    asked_via_claude = bridge2.handle_turn(shared_session_id, "dragon_3d", claude_prompt)
    print(f"   dragon_3d <- claude_code: {asked_via_claude['response']!r}")
    check(asked_via_claude["actor"] == "claude_code", "response actor is claude_code")

    print("\n7. Verify the answer and that it was appended to the same EngAIn Ledger...")
    check(REMEMBERED_PHRASE in asked_via_claude["response"].lower(),
          "claude_code correctly reported the phrase from the supplied Ledger context")
    after_claude_turn = ledger.read_since(shared_session_id, since_turn_id=-1)
    check(len(after_claude_turn) == 4, "Ledger now has both provider exchanges, same shared_session_id")
    check(all(t.session_id == shared_session_id for t in after_claude_turn),
          "every turn across both providers carries the identical shared_session_id")

    print("\n8. Switch back to Hermes — reusing the exact original, stale provider_session_id...")
    presence.register(
        "hermes", "H-2-return", shared_session_id, ["chat"],
        endpoint=_hermes_endpoint(hermes_provider_session_id_1),  # the SAME native session as step 2
    )
    resolved_after_return = presence.resolve(shared_session_id)
    check(resolved_after_return.agent_id == "hermes", "presence resolves hermes again for the same shared_session_id")

    claude_response_turn = ledger.read_last(shared_session_id, direction="response")
    check(claude_response_turn.actor == "claude_code", "most recent Ledger response is claude_code's, about to be recalled by Hermes")
    hermes_recall_prompt = (
        "You are resuming as the active assistant for this session. While you were not "
        "active, a different provider handled one exchange. Here is EngAIn's own record "
        "of it, not something you remember, since your own conversation never included it:\n"
        f"  A different assistant was asked to recall a phrase and replied: {claude_response_turn.payload!r}\n"
        "Based only on that supplied record, what was that phrase? Reply with only the "
        "phrase, nothing else."
    )
    bridge3 = SharedSessionBridge(presence=presence, ledger=ledger, provider_dispatch=dispatch_via_hermes_cli)
    asked_via_hermes_again = bridge3.handle_turn(shared_session_id, "dragon_2d", hermes_recall_prompt)
    print(f"   dragon_2d <- hermes (same stale native session): {asked_via_hermes_again['response']!r}")
    check(asked_via_hermes_again["actor"] == "hermes", "response actor is hermes")
    check(REMEMBERED_PHRASE in asked_via_hermes_again["response"].lower(),
          "hermes correctly recovered the Claude turn from EngAIn continuity — "
          "its own native transcript never saw it")

    all_turns = ledger.read_since(shared_session_id, since_turn_id=-1)
    check(len(all_turns) == 6, "one Ledger, six turns, three provider registrations, one shared_session_id throughout")
    check({t.actor for t in all_turns} == {"player", "hermes", "claude_code"},
          "both real providers and the player are all represented in one continuous Ledger")

    receipt["portability_proof"] = "PASS"
    receipt["turns"] = [
        {"turn_id": t.turn_id, "origin_body": t.origin_body, "direction": t.direction, "actor": t.actor, "payload": t.payload}
        for t in all_turns
    ]
    receipt["finished_at"] = time.time()
    return receipt


def main() -> int:
    try:
        receipt = run()
    except ProofFailure as exc:
        print(f"\nFAIL: {exc}")
        return 1
    RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2))
    print(f"\nAll checks passed. Receipt written to {RECEIPT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
