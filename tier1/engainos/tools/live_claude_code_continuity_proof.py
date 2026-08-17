#!/usr/bin/env python3
"""
live_claude_code_continuity_proof.py - Second provider, same proof shape.

Real `claude` CLI, real bridge, real Ledger, real Presence. Same scenario as
live_hermes_continuity_proof.py, same assertions, only the adapter and the
endpoint differ — that sameness is the actual point: a second provider is a
second small adapter behind SharedSessionBridge's existing callable shape,
not a second architecture.

Deliberately NOT a pytest test, for the same reason as the Hermes proof:
kept as a plain script so no test-harness environment variable can ever
collide with a provider CLI's own safety checks. (claude was not observed to
have Hermes's specific PYTEST_CURRENT_TEST guard, but the point of avoiding
pytest here isn't "this particular guard" — it's not depending on knowing
every provider CLI's internals to be sure none of them will ever add one.)

Costs real usage against the authenticated Claude account: 2 session-
bootstrap calls + 2 dispatch calls, minimum, per run.

Run:
    python3 tier1/engainos/tools/live_claude_code_continuity_proof.py
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import uuid

from tier1.engainos.bridgeroom.claude_code_provider_adapter import dispatch_via_claude_code_cli
from tier1.engainos.bridgeroom.shared_session_bridge import ProviderNotRegistered, SharedSessionBridge
from tier1.engainos.core.presence_registry import PresenceRegistry
from tier1.engainos.core.provider_session_binding import ProviderSessionBinding
from tier1.engainos.core.session_ledger import SessionLedger

RECEIPT_PATH = REPO_ROOT / "runtime" / "logs" / "SHARED_SESSION_CONTINUITY_LIVE_CLAUDE_CODE_PROOF_V1.report.json"


def _new_shared_session_id() -> str:
    """EngAIn's own identifier — deliberately never the vendor-native
    session id minted below. See provider_session_binding.py."""
    return f"shared-{uuid.uuid4().hex}"


class ProofFailure(Exception):
    pass


def check(condition: bool, message: str) -> None:
    if not condition:
        raise ProofFailure(message)
    print(f"  OK  {message}")


def mint_real_claude_session() -> str:
    """REGISTER's own contract requires session_id as an input, not
    something a dispatcher mints — same pattern as the Hermes proof."""
    claude_exe = shutil.which("claude")
    if not claude_exe:
        raise ProofFailure("claude not found on PATH")
    completed = subprocess.run(
        [
            claude_exe, "-p",
            "Session bootstrap for an EngAIn shared-session continuity proof. Reply with exactly: READY",
            "--output-format", "json",
        ],
        capture_output=True, text=True, timeout=90,
    )
    if completed.returncode != 0:
        raise ProofFailure(f"bootstrap call failed (exit {completed.returncode}): {completed.stderr}")
    try:
        parsed = json.loads(completed.stdout)
    except ValueError as exc:
        raise ProofFailure(f"bootstrap call produced non-JSON stdout: {completed.stdout!r}") from exc
    if parsed.get("is_error"):
        raise ProofFailure(f"bootstrap call returned is_error=true: {parsed!r}")
    session_id = parsed.get("session_id")
    if not session_id:
        raise ProofFailure(f"bootstrap call returned no session_id: {parsed!r}")
    return session_id


def run() -> dict:
    receipt: dict = {
        "schema": "engain.live_claude_code_continuity_proof.v1",
        "started_at": time.time(),
    }

    print("1. Minting real Claude Code session (the vendor-native provider_session_id)...")
    provider_session_id = mint_real_claude_session()
    shared_session_id = _new_shared_session_id()
    receipt["provider_session_id"] = provider_session_id
    receipt["shared_session_id"] = shared_session_id
    print(f"   provider_session_id = {provider_session_id}")
    print(f"   shared_session_id   = {shared_session_id}  (EngAIn's own — deliberately not the same value)")

    presence = PresenceRegistry()
    ledger = SessionLedger()
    presence.register(
        "claude_code", "CC-LIVE-1", shared_session_id, ["chat", "code"],
        endpoint=ProviderSessionBinding.encode_endpoint(
            provider_id="claude_code", model_id="", provider_session_id=provider_session_id,
        ),
    )
    bridge = SharedSessionBridge(presence=presence, ledger=ledger, provider_dispatch=dispatch_via_claude_code_cli)
    session_id = shared_session_id  # every bridge/ledger call below uses EngAIn's key, never the vendor's

    print("\n2. Ask through dragon_2d: remember 'copper rain'...")
    said_2d = bridge.handle_turn(session_id, "dragon_2d", "Remember the phrase: copper rain. Reply with exactly: noted.")
    print(f"   dragon_2d <- claude_code: {said_2d['response']!r}")
    check(said_2d["actor"] == "claude_code", "response actor is claude_code")
    check(said_2d["origin_body"] == "dragon_2d", "response returned through dragon_2d")

    print("\n3. Verify request + real Claude Code answer landed in the Ledger...")
    request_turn = ledger.read_since(session_id, since_turn_id=-1)[0]
    check(request_turn.direction == "request" and request_turn.origin_body == "dragon_2d",
          "request turn recorded with origin_body=dragon_2d")
    response_turn_2d = ledger.read_last(session_id, direction="response")
    check(response_turn_2d is not None and response_turn_2d.origin_body == "dragon_2d",
          "response turn recorded with origin_body=dragon_2d")

    print("\n4. Ask through dragon_3d: what phrase did I tell you?...")
    asked_3d = bridge.handle_turn(
        session_id, "dragon_3d",
        "What phrase did I just ask you to remember? Reply with only the phrase, nothing else.",
    )
    print(f"   dragon_3d <- claude_code: {asked_3d['response']!r}")

    print("\n5. Verify real Claude Code answered 'copper rain'...")
    check("copper rain" in asked_3d["response"].lower(), "3D door's answer contains the phrase told to the 2D door")

    print("\n6. Verify the answer was produced through the real provider adapter...")
    check(bridge._dispatch is dispatch_via_claude_code_cli, "bridge is wired to dispatch_via_claude_code_cli, not the stub")

    print("\n7. Verify both exchanges belong to the same session_id...")
    all_turns = ledger.read_since(session_id, since_turn_id=-1)
    check(all(t.session_id == session_id for t in all_turns), "every turn carries the same session_id")
    check({t.origin_body for t in all_turns} == {"dragon_2d", "dragon_3d"}, "both origin_bodies are represented in the one Ledger")

    print("\n8. Verify the bridge still holds no private conversation state...")
    check(set(vars(bridge).keys()) == {"_presence", "_ledger", "_dispatch", "_continuity", "_cursor"},
          "bridge instance holds only the two shared authorities, the dispatcher, and the stateless continuity builder")

    receipt["continuity_proof"] = "PASS"
    receipt["turns"] = [
        {"turn_id": t.turn_id, "origin_body": t.origin_body, "direction": t.direction, "actor": t.actor, "payload": t.payload}
        for t in all_turns
    ]

    print("\n--- Failure proof: Presence loss during real dispatch ---")
    provider_session_id_2 = mint_real_claude_session()
    session_id_2 = _new_shared_session_id()
    receipt["failure_proof_provider_session_id"] = provider_session_id_2
    receipt["failure_proof_shared_session_id"] = session_id_2
    print(f"   provider_session_id = {provider_session_id_2}")
    print(f"   shared_session_id   = {session_id_2}")

    presence2 = PresenceRegistry()
    ledger2 = SessionLedger()
    presence2.register(
        "claude_code", "CC-LIVE-2", session_id_2, ["chat", "code"],
        endpoint=ProviderSessionBinding.encode_endpoint(
            provider_id="claude_code", model_id="", provider_session_id=provider_session_id_2,
        ),
    )

    def deregister_right_after_real_dispatch(binding, context, player_input):
        result = dispatch_via_claude_code_cli(binding, context, player_input)
        presence2.deregister("CC-LIVE-2")  # Claude Code "leaves" the instant its real answer lands
        return result

    bridge2 = SharedSessionBridge(presence=presence2, ledger=ledger2, provider_dispatch=deregister_right_after_real_dispatch)

    print("   dispatch begins -> real claude call in flight -> presence deregisters right after it returns...")
    raised = None
    try:
        bridge2.handle_turn(session_id_2, "dragon_2d", "Reply with exactly: should not be recorded")
    except ProviderNotRegistered as exc:
        raised = exc

    check(raised is not None, "ProviderNotRegistered was raised")
    check(ledger2.read_last(session_id_2, direction="request") is not None, "player's request remains in the Ledger")
    check(ledger2.read_last(session_id_2, direction="response") is None, "no response was appended")

    receipt["failure_proof"] = "PASS"
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
