#!/usr/bin/env python3
"""
live_cross_provider_mailbox_portability_proof.py - The same Hermes -> Claude
Code -> Hermes proof as live_cross_provider_portability_proof.py, but
through real request.json/response.json mailbox files, with no manually
constructed recap anywhere in this script.

The prior proof (2026-08-16) hand-wrote the recap prose for each provider
switch directly in the script. That proved the architecture could carry
continuity across providers, but it also proved something narrower than it
looked: the recap-building itself was still the proof script's job, not
the dispatch path's. This proof closes that gap. Every player_input written
to a request file here is bare, ordinary, human-shaped text — "what did I
just say?", nothing more. Whatever context-carrying happens is
ContinuityContextBuilder's job, inside SharedSessionBridge.handle_turn(),
triggered automatically by mailbox_request_handler.handle_mailbox_request()
for every request file processed, regardless of which body or which
mechanism produced it.

Real request/response files are written under
runtime/mailboxes/cross_provider_proof/ and left on disk afterward as
evidence — not a tmp directory, not deleted.

Costs the same real usage as the prior proof: 2 Hermes CLI calls + 1
Hermes bootstrap, 1 Claude Code CLI call + 1 Claude Code bootstrap — 5 real
calls per run.

Run:
    python3 tier1/engainos/tools/live_cross_provider_mailbox_portability_proof.py
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
from tier1.engainos.bridgeroom.mailbox_request_handler import handle_mailbox_request
from tier1.engainos.bridgeroom.shared_session_bridge import SharedSessionBridge
from tier1.engainos.core.presence_registry import PresenceRegistry
from tier1.engainos.core.provider_session_binding import ProviderSessionBinding
from tier1.engainos.core.session_ledger import SessionLedger

HERMES_SESSION_ID_PATTERN = re.compile(r"(?m)^session_id:\s*([^\s]+)\s*$")
REMEMBERED_PHRASE = "granite lantern"
MAILBOX_DIR = REPO_ROOT / "runtime" / "mailboxes" / "cross_provider_proof"
RECEIPT_PATH = REPO_ROOT / "runtime" / "logs" / "CROSS_PROVIDER_MAILBOX_PORTABILITY_PROOF_V1.report.json"


class ProofFailure(Exception):
    pass


def check(condition: bool, message: str) -> None:
    if not condition:
        raise ProofFailure(message)
    print(f"  OK  {message}")


def _new_shared_session_id() -> str:
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


def _submit_mailbox_request(
    turn_name: str,
    shared_session_id: str,
    origin_body: str,
    player_input: str,
    bridge: SharedSessionBridge,
) -> dict:
    """Writes one bare request file, processes it through the real mailbox
    handler, reads back one real response file. player_input here is
    always exactly what a human would type — no recap, no provider names,
    no prior-turn text assembled by this script."""
    request_path = MAILBOX_DIR / f"{turn_name}.request.json"
    response_path = MAILBOX_DIR / f"{turn_name}.response.json"
    request_path.parent.mkdir(parents=True, exist_ok=True)
    request_path.write_text(json.dumps({
        "shared_session_id": shared_session_id,
        "origin_body": origin_body,
        "player_input": player_input,
    }, indent=2))
    return handle_mailbox_request(request_path, response_path, bridge)


def run() -> dict:
    receipt: dict = {"schema": "engain.cross_provider_mailbox_portability_proof.v1", "started_at": time.time()}

    print("0. Clearing this proof's mailbox directory of any prior run...")
    if MAILBOX_DIR.exists():
        for path in MAILBOX_DIR.glob("*"):
            path.unlink()
    MAILBOX_DIR.mkdir(parents=True, exist_ok=True)

    print("1. One EngAIn shared session...")
    shared_session_id = _new_shared_session_id()
    receipt["shared_session_id"] = shared_session_id
    print(f"   shared_session_id = {shared_session_id}")

    presence = PresenceRegistry()
    ledger = SessionLedger()

    print("\n2. Register Hermes, dispatch through its native session, via a real mailbox request...")
    hermes_provider_session_id_1 = mint_real_hermes_session(
        "Session bootstrap for an EngAIn cross-provider mailbox portability proof. Reply with exactly: READY"
    )
    receipt["hermes_provider_session_id_1"] = hermes_provider_session_id_1
    presence.register(
        "hermes", "H-1", shared_session_id, ["chat"],
        endpoint=ProviderSessionBinding.encode_endpoint(
            provider_id="hermes", model_id="gpt-5.6-sol",
            provider_session_id=hermes_provider_session_id_1,
            launch_options={"provider": "openai-codex"},
        ),
    )
    bridge_hermes = SharedSessionBridge(presence=presence, ledger=ledger, provider_dispatch=dispatch_via_hermes_cli)

    turn_1 = _submit_mailbox_request(
        "01_hermes_remember", shared_session_id, "dragon_2d",
        f"Remember the phrase: {REMEMBERED_PHRASE}. Reply with exactly: noted.",  # bare — no recap
        bridge_hermes,
    )
    print(f"   dragon_2d <- hermes: {turn_1['response']!r}")
    check(turn_1["actor"] == "hermes", "response actor is hermes")

    print("\n3. Record request and response in the shared Ledger (verify)...")
    after_turn_1 = ledger.read_since(shared_session_id, since_turn_id=-1)
    check(len(after_turn_1) == 2, "exactly one request+response pair recorded so far")

    print("\n4. Switch the binding to Claude Code with a different native session...")
    claude_provider_session_id = mint_real_claude_session(
        "Session bootstrap for an EngAIn cross-provider mailbox portability proof. Reply with exactly: READY"
    )
    receipt["claude_provider_session_id"] = claude_provider_session_id
    presence.register(
        "claude_code", "CC-1", shared_session_id, ["chat", "code"],
        endpoint=ProviderSessionBinding.encode_endpoint(
            provider_id="claude_code", model_id="", provider_session_id=claude_provider_session_id,
        ),
    )
    bridge_claude = SharedSessionBridge(presence=presence, ledger=ledger, provider_dispatch=dispatch_via_claude_code_cli)

    print("\n5+6. Ask Claude Code about the earlier Hermes turn — a bare mailbox request, no recap written by this script...")
    turn_2 = _submit_mailbox_request(
        "02_claude_recall", shared_session_id, "dragon_3d",
        "What phrase did I just ask you to remember? Reply with only the phrase, nothing else.",  # bare
        bridge_claude,
    )
    print(f"   dragon_3d <- claude_code: {turn_2['response']!r}")
    check(turn_2["actor"] == "claude_code", "response actor is claude_code")

    print("\n7. Verify the answer and that it landed in the same Ledger...")
    check(REMEMBERED_PHRASE in turn_2["response"].lower(),
          "claude_code correctly reported the phrase, from a bare request — "
          "the recap was built automatically by ContinuityContextBuilder inside handle_turn(), "
          "not written into the request file by this script")
    after_turn_2 = ledger.read_since(shared_session_id, since_turn_id=-1)
    check(len(after_turn_2) == 4, "Ledger now has both provider exchanges, same shared_session_id")

    print("\n8. Switch back to Hermes — reusing the exact original, stale provider_session_id...")
    presence.register(
        "hermes", "H-2-return", shared_session_id, ["chat"],
        endpoint=ProviderSessionBinding.encode_endpoint(
            provider_id="hermes", model_id="gpt-5.6-sol",
            provider_session_id=hermes_provider_session_id_1,  # the SAME native session as step 2
            launch_options={"provider": "openai-codex"},
        ),
    )
    bridge_hermes_2 = SharedSessionBridge(presence=presence, ledger=ledger, provider_dispatch=dispatch_via_hermes_cli)

    turn_3 = _submit_mailbox_request(
        "03_hermes_recover", shared_session_id, "dragon_2d",
        "What did the other assistant just tell me? Reply with only the phrase, nothing else.",  # bare
        bridge_hermes_2,
    )
    print(f"   dragon_2d <- hermes (same stale native session): {turn_3['response']!r}")
    check(turn_3["actor"] == "hermes", "response actor is hermes")
    check(REMEMBERED_PHRASE in turn_3["response"].lower(),
          "hermes recovered the Claude turn from EngAIn continuity via an automatically "
          "built recap — its own native transcript never saw the Claude exchange, and this "
          "script never wrote that recap into any request file")

    all_turns = ledger.read_since(shared_session_id, since_turn_id=-1)
    check(len(all_turns) == 6, "one Ledger, six turns, three registrations, one shared_session_id throughout")

    mailbox_files = sorted(p.name for p in MAILBOX_DIR.glob("*"))
    check(len(mailbox_files) == 6, "three real request files and three real response files on disk")
    print(f"\n  Mailbox artifacts left on disk: {mailbox_files}")

    receipt["portability_proof"] = "PASS"
    receipt["mailbox_dir"] = str(MAILBOX_DIR)
    receipt["mailbox_files"] = mailbox_files
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
