#!/usr/bin/env python3
"""
live_hermes_continuity_proof.py - Real hermes, real bridge, real proof.

Deliberately NOT a pytest test — see
tier1/engainos/tests/test_shared_session_continuity_live_hermes_proof.py for
why: hermes's own auth guard refuses real-auth access whenever
PYTEST_CURRENT_TEST is set, and stripping that variable inside the
production adapter was considered and explicitly declined. Running this as
a plain script means that variable is never set in the first place, so the
real provider call proceeds exactly as it would for a human running
`hermes chat` directly.

Reuses SharedSessionBridge, PresenceRegistry, and SessionLedger exactly as
built — nothing about the Ledger or bridge logic is touched here. The only
thing this script adds is dispatch_via_hermes_cli in place of
stub_provider_dispatch, and the assertions that make up the proof.

Costs real usage against the authenticated openai-codex / gpt-5.6-sol
provider: 2 session-bootstrap calls + 2 dispatch calls, minimum, per run.

Run:
    python3 tier1/engainos/tools/live_hermes_continuity_proof.py
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tier1.engainos.bridgeroom.hermes_provider_adapter import dispatch_via_hermes_cli
from tier1.engainos.bridgeroom.shared_session_bridge import ProviderNotRegistered, SharedSessionBridge
from tier1.engainos.core.presence_registry import PresenceRegistry
from tier1.engainos.core.session_ledger import SessionLedger

HERMES_ENDPOINT = '{"provider": "openai-codex", "model": "gpt-5.6-sol"}'
HERMES_SESSION_ID_PATTERN = re.compile(r"(?m)^session_id:\s*([^\s]+)\s*$")
RECEIPT_PATH = REPO_ROOT / "runtime" / "logs" / "SHARED_SESSION_CONTINUITY_LIVE_HERMES_PROOF_V1.report.json"


class ProofFailure(Exception):
    pass


def check(condition: bool, message: str) -> None:
    if not condition:
        raise ProofFailure(message)
    print(f"  OK  {message}")


def mint_real_hermes_session() -> str:
    """REGISTER's own contract requires session_id as an input, not
    something a dispatcher mints. This mirrors what an operator bootstrapping
    a fresh `hermes chat` would do before registering it into EngAIn."""
    hermes_exe = shutil.which("hermes")
    if not hermes_exe:
        raise ProofFailure("hermes not found on PATH")
    completed = subprocess.run(
        [
            hermes_exe, "chat", "-Q", "--provider", "openai-codex", "-m", "gpt-5.6-sol",
            "--pass-session-id", "--ignore-rules", "--source", "tool",
            "-q", "Session bootstrap for an EngAIn shared-session continuity proof. Reply with exactly: READY",
        ],
        capture_output=True, text=True, timeout=90,
    )
    if completed.returncode != 0:
        raise ProofFailure(f"bootstrap call failed (exit {completed.returncode}): {completed.stderr}")
    match = HERMES_SESSION_ID_PATTERN.search(completed.stderr)
    if not match:
        raise ProofFailure(f"no session_id in bootstrap stderr: {completed.stderr!r}")
    return match.group(1)


def run() -> dict:
    receipt: dict = {
        "schema": "engain.live_hermes_continuity_proof.v1",
        "started_at": time.time(),
    }

    print("1. Minting real hermes session (REGISTER's session_id, minted out-of-band)...")
    session_id = mint_real_hermes_session()
    receipt["session_id"] = session_id
    print(f"   session_id = {session_id}")

    presence = PresenceRegistry()
    ledger = SessionLedger()
    presence.register("hermes", "H-LIVE-1", session_id, ["chat"], endpoint=HERMES_ENDPOINT)
    bridge = SharedSessionBridge(presence=presence, ledger=ledger, provider_dispatch=dispatch_via_hermes_cli)

    print("\n2. Ask through dragon_2d: remember 'copper rain'...")
    said_2d = bridge.handle_turn(session_id, "dragon_2d", "Remember the phrase: copper rain. Reply with exactly: noted.")
    print(f"   dragon_2d <- hermes: {said_2d['response']!r}")
    check(said_2d["actor"] == "hermes", "response actor is hermes")
    check(said_2d["origin_body"] == "dragon_2d", "response returned through dragon_2d")

    print("\n3. Verify request + real hermes answer landed in the Ledger...")
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
    print(f"   dragon_3d <- hermes: {asked_3d['response']!r}")

    print("\n5. Verify real hermes answered 'copper rain'...")
    check("copper rain" in asked_3d["response"].lower(), "3D door's answer contains the phrase told to the 2D door")

    print("\n6. Verify the answer was produced through the real provider adapter...")
    check(bridge._dispatch is dispatch_via_hermes_cli, "bridge is wired to dispatch_via_hermes_cli, not the stub")

    print("\n7. Verify both exchanges belong to the same session_id...")
    all_turns = ledger.read_since(session_id, since_turn_id=-1)
    check(all(t.session_id == session_id for t in all_turns), "every turn carries the same session_id")
    check({t.origin_body for t in all_turns} == {"dragon_2d", "dragon_3d"}, "both origin_bodies are represented in the one Ledger")

    print("\n8. Verify the bridge still holds no private conversation state...")
    check(set(vars(bridge).keys()) == {"_presence", "_ledger", "_dispatch"},
          "bridge instance holds only the two shared authorities + dispatcher")

    receipt["continuity_proof"] = "PASS"
    receipt["turns"] = [
        {"turn_id": t.turn_id, "origin_body": t.origin_body, "direction": t.direction, "actor": t.actor, "payload": t.payload}
        for t in all_turns
    ]

    print("\n--- Failure proof: Presence loss during real dispatch ---")
    session_id_2 = mint_real_hermes_session()
    receipt["failure_proof_session_id"] = session_id_2
    print(f"   session_id = {session_id_2}")

    presence2 = PresenceRegistry()
    ledger2 = SessionLedger()
    presence2.register("hermes", "H-LIVE-2", session_id_2, ["chat"], endpoint=HERMES_ENDPOINT)

    def deregister_right_after_real_dispatch(record, context, player_input):
        result = dispatch_via_hermes_cli(record, context, player_input)
        presence2.deregister("H-LIVE-2")  # Hermes "leaves" the instant its real answer lands
        return result

    bridge2 = SharedSessionBridge(presence=presence2, ledger=ledger2, provider_dispatch=deregister_right_after_real_dispatch)

    print("   dispatch begins -> real hermes call in flight -> presence deregisters right after it returns...")
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
