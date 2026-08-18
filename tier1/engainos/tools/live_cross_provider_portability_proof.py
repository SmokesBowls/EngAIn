#!/usr/bin/env python3
"""
live_cross_provider_portability_proof.py - Real proof that switching
providers mid-session works through EngAIn's own Ledger, not through any
vendor's private memory.

Rewritten 2026-08-17: the first version hand-wrote the recap prose for each
provider switch directly in this script. That was real, but it also meant
this proof could never have caught the identity-boundary bug that turned
out to be real (see continuity_cursor_tracker.py's module docstring) — a
hand-written recap doesn't exercise ContinuityCursorTracker at all. Every
player_input here is now bare, ordinary text, same as
live_cross_provider_mailbox_portability_proof.py. Whatever context-carrying
happens is entirely ContinuityContextBuilder + ContinuityCursorTracker's
job, inside SharedSessionBridge.handle_turn(), keyed on
(provider_id, provider_session_id) — never on actor/agent_id.

Because this proof uses three separate SharedSessionBridge instances (one
per provider_dispatch), it explicitly constructs and shares ONE
ContinuityCursorTracker across all three — exactly the requirement
SharedSessionBridge.__init__ documents. Without that, each bridge would
default to its own fresh tracker and the proof would recap every single
turn regardless of whether it was actually needed, silently defeating the
whole point of the fix.

Deliberately NOT a pytest test, for the same reason as the two
single-provider proofs (hermes's own PYTEST_CURRENT_TEST auth guard; see
that proof's docstring for the full reasoning). Plain script, no pytest
involved anywhere in this process's ancestry.

The decisive step is the last one: switching back to Hermes reuses the
exact original provider_session_id — the same stale native transcript that
was never told about the Claude Code turn. If Hermes answers correctly
about that turn, it is structurally impossible for that to have come from
Hermes's own memory: it has to have come from the cursor-driven recap
ContinuityContextBuilder assembled automatically.

Costs real usage against both authenticated accounts: 5 real calls per run
(Hermes bootstrap + dispatch, Claude Code bootstrap + dispatch, Hermes
dispatch again).

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
from tier1.engainos.core.continuity_cursor_tracker import ContinuityCursorTracker
from tier1.engainos.core.presence_registry import PresenceRegistry
from tier1.engainos.core.provider_session_binding import ProviderSessionBinding
from tier1.engainos.core.session_ledger import SessionLedger

HERMES_SESSION_ID_PATTERN = re.compile(r"(?m)^session_id:\s*([^\s]+)\s*$")
RECEIPT_PATH = REPO_ROOT / "runtime" / "logs" / "CROSS_PROVIDER_PORTABILITY_PROOF_V1.report.json"
REMEMBERED_PHRASE = "amber compass"


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


# handle_turn() requires an explicit binding (item 1) rather than
# re-deriving one from Presence — see shared_session_bridge.py's own
# Correction note. These mirror _hermes_endpoint/_claude_endpoint above,
# built from the exact same fields.
def _hermes_binding(provider_session_id: str, agent_id: str, instance_id: str, shared_session_id: str) -> ProviderSessionBinding:
    return ProviderSessionBinding(
        provider_id="hermes", model_id="gpt-5.6-sol", provider_session_id=provider_session_id,
        agent_id=agent_id, instance_id=instance_id, shared_session_id=shared_session_id,
        launch_options={"provider": "openai-codex"},
    )


def _claude_binding(provider_session_id: str, agent_id: str, instance_id: str, shared_session_id: str) -> ProviderSessionBinding:
    return ProviderSessionBinding(
        provider_id="claude_code", model_id="", provider_session_id=provider_session_id,
        agent_id=agent_id, instance_id=instance_id, shared_session_id=shared_session_id,
        launch_options={},
    )


def run() -> dict:
    receipt: dict = {"schema": "engain.cross_provider_portability_proof.v1", "started_at": time.time()}

    print("1. One EngAIn shared session...")
    shared_session_id = _new_shared_session_id()
    receipt["shared_session_id"] = shared_session_id
    print(f"   shared_session_id = {shared_session_id}")

    presence = PresenceRegistry()
    ledger = SessionLedger()
    cursor = ContinuityCursorTracker()  # shared explicitly across all three bridge instances below

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
    bridge_hermes_1 = SharedSessionBridge(
        presence=presence, ledger=ledger, provider_dispatch=dispatch_via_hermes_cli,
        continuity_cursor_tracker=cursor,
    )

    said_via_hermes = bridge_hermes_1.handle_turn(
        shared_session_id, "dragon_2d",
        f"Remember the phrase: {REMEMBERED_PHRASE}. Reply with exactly: noted.",  # bare — no recap
        binding=_hermes_binding(hermes_provider_session_id_1, "hermes", "H-1", shared_session_id),
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
    bridge_claude = SharedSessionBridge(
        presence=presence, ledger=ledger, provider_dispatch=dispatch_via_claude_code_cli,
        continuity_cursor_tracker=cursor,
    )

    print("\n5+6. Ask Claude Code about the earlier Hermes turn — a bare request, no recap written by this script...")
    asked_via_claude = bridge_claude.handle_turn(
        shared_session_id, "dragon_3d",
        "What phrase did I just ask you to remember? Reply with only the phrase, nothing else.",  # bare
        binding=_claude_binding(claude_provider_session_id, "claude_code", "CC-1", shared_session_id),
    )
    print(f"   dragon_3d <- claude_code: {asked_via_claude['response']!r}")
    check(asked_via_claude["actor"] == "claude_code", "response actor is claude_code")

    print("\n7. Verify the answer and that it was appended to the same EngAIn Ledger...")
    check(REMEMBERED_PHRASE in asked_via_claude["response"].lower(),
          "claude_code correctly reported the phrase, recapped automatically by the cursor-driven builder")
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
    bridge_hermes_2 = SharedSessionBridge(
        presence=presence, ledger=ledger, provider_dispatch=dispatch_via_hermes_cli,
        continuity_cursor_tracker=cursor,
    )

    asked_via_hermes_again = bridge_hermes_2.handle_turn(
        shared_session_id, "dragon_2d",
        "What did the other assistant just tell me? Reply with only the phrase, nothing else.",  # bare
        binding=_hermes_binding(hermes_provider_session_id_1, "hermes", "H-2-return", shared_session_id),
    )
    print(f"   dragon_2d <- hermes (same stale native session): {asked_via_hermes_again['response']!r}")
    check(asked_via_hermes_again["actor"] == "hermes", "response actor is hermes")
    check(REMEMBERED_PHRASE in asked_via_hermes_again["response"].lower(),
          "hermes correctly recovered the Claude turn via the cursor-driven recap — "
          "its own native transcript never saw it, and this script wrote no recap prose")

    all_turns = ledger.read_since(shared_session_id, since_turn_id=-1)
    check(len(all_turns) == 6, "one Ledger, six turns, three provider registrations, one shared_session_id throughout")
    check({t.actor for t in all_turns} == {"player", "hermes", "claude_code"},
          "both real providers and the player are all represented in one continuous Ledger")

    # The identity-boundary property this rewrite exists to prove: the
    # cursor for hermes's ORIGINAL native session lands exactly on its own
    # step-8 response turn_id — it never advanced during the Claude turn,
    # since that dispatched to a completely different (provider_id,
    # provider_session_id) pair.
    cursor_after_return = cursor.last_seen_turn_id("hermes", hermes_provider_session_id_1)
    check(cursor_after_return == asked_via_hermes_again["turn_id"],
          "hermes's original native session's cursor advanced exactly to its own step-8 response — "
          "never bumped by the intervening Claude Code turn")

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
