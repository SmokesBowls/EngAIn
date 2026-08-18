#!/usr/bin/env python3
"""
live_dispatch_mutex_contention_proof.py - Item 1's dispatch mutex, proven
against a real, standalone presence_authority_server.py process and a real
Hermes CLI call — not the pytest fixture, not a fake dispatcher.

Starts the real server as its own subprocess (the same way
runtime_composition.py's SupervisedPresenceAuthority does), mints one real
Hermes session, then fires two concurrent real HTTP POST /dispatch
requests at the real server targeting the identical
(provider_id="hermes", provider_session_id=<that real session>) native
transcript. Exactly one must actually reach the provider and get a real
response; the other must be rejected immediately with DISPATCH_BUSY,
never queued, never touching the real Hermes CLI at all.

Costs one real usage call against the authenticated openai-codex /
gpt-5.6-sol provider (the session-bootstrap call) — the contended dispatch
itself only actually reaches Hermes once, by design; the rejected caller
never does.

Run:
    python3 tier1/engainos/tools/live_dispatch_mutex_contention_proof.py
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Tuple

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

HERMES_SESSION_ID_PATTERN = re.compile(r"(?m)^session_id:\s*([^\s]+)\s*$")
SERVER_SCRIPT = REPO_ROOT / "tier1" / "engainos" / "server" / "presence_authority_server.py"
RECEIPT_PATH = REPO_ROOT / "runtime" / "logs" / "LIVE_DISPATCH_MUTEX_CONTENTION_PROOF_V1.report.json"
HOST = "127.0.0.1"
PORT = 8768  # distinct from the default 8767, so this can run alongside a normal launch


class ProofFailure(Exception):
    pass


def check(condition: bool, message: str) -> None:
    if not condition:
        raise ProofFailure(message)
    print(f"  OK  {message}")


def mint_real_hermes_session() -> str:
    hermes_exe = shutil.which("hermes")
    if not hermes_exe:
        raise ProofFailure("hermes not found on PATH")
    completed = subprocess.run(
        [
            hermes_exe, "chat", "-Q", "--provider", "openai-codex", "-m", "gpt-5.6-sol",
            "--pass-session-id", "--ignore-rules", "--source", "tool",
            "-q", "Session bootstrap for an EngAIn dispatch-mutex contention proof. Reply with exactly: READY",
        ],
        capture_output=True, text=True, timeout=90,
    )
    if completed.returncode != 0:
        raise ProofFailure(f"bootstrap call failed (exit {completed.returncode}): {completed.stderr}")
    match = HERMES_SESSION_ID_PATTERN.search(completed.stderr)
    if not match:
        raise ProofFailure(f"no session_id in bootstrap stderr: {completed.stderr!r}")
    return match.group(1)


def _post(path: str, payload: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"http://{HOST}:{PORT}{path}", data=data, method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def run() -> dict:
    receipt: dict = {"schema": "engain.live_dispatch_mutex_contention_proof.v1", "started_at": time.time()}

    print("1. Minting one real Hermes session (the contended native transcript)...")
    provider_session_id = mint_real_hermes_session()
    receipt["provider_session_id"] = provider_session_id
    print(f"   provider_session_id = {provider_session_id}")

    print(f"\n2. Starting a real, standalone presence_authority_server.py on {HOST}:{PORT}...")
    server_process = subprocess.Popen([sys.executable, str(SERVER_SCRIPT), "--host", HOST, "--port", str(PORT)])
    try:
        deadline = time.monotonic() + 15.0
        healthy = False
        while time.monotonic() < deadline:
            try:
                with urllib.request.urlopen(f"http://{HOST}:{PORT}/health", timeout=1.0) as resp:
                    if resp.status == 200:
                        healthy = True
                        break
            except (urllib.error.URLError, OSError):
                pass
            time.sleep(0.05)
        check(healthy, "real presence authority process became healthy")

        shared_session_id = "shared-live-dispatch-mutex-contention"
        results: Dict[str, Tuple[int, Dict[str, Any]]] = {}
        entered_real_dispatch = threading.Event()

        def body(player_input: str) -> Dict[str, Any]:
            return {
                "shared_session_id": shared_session_id, "origin_body": "dragon_2d",
                "player_input": player_input, "provider_id": "hermes",
                "model_id": "gpt-5.6-sol", "provider_session_id": provider_session_id,
                "launch_options": {"provider": "openai-codex"},
            }

        def send_a() -> None:
            print("\n3. Caller A: dispatching for real — a genuine `hermes chat --resume` call in flight...")
            entered_real_dispatch.set()
            results["a"] = _post("/dispatch", body("Reply with exactly: A-ACK"))

        thread_a = threading.Thread(target=send_a)
        thread_a.start()
        # No fixed sleep-and-hope: wait for confirmation A's request has
        # actually been sent, then give the real network+subprocess round
        # trip a realistic head start before firing B — a real dispatch
        # takes on the order of seconds, not milliseconds, so this window
        # reliably lands B while A still holds the claim.
        assert entered_real_dispatch.wait(timeout=5)
        time.sleep(0.3)

        print("4. Caller B: sent while A's real dispatch is still in flight — must be rejected, never queued...")
        results["b"] = _post("/dispatch", body("Reply with exactly: B-SHOULD-NEVER-RUN"))

        thread_a.join(timeout=120)
        check("a" in results, "caller A's real dispatch completed")

        status_a, resp_a = results["a"]
        status_b, resp_b = results["b"]
        receipt["caller_a_status"] = status_a
        receipt["caller_a_response"] = resp_a
        receipt["caller_b_status"] = status_b
        receipt["caller_b_response"] = resp_b

        check(status_a == 200, f"caller A's real dispatch succeeded (got {status_a}: {resp_a})")
        check(resp_a.get("response") is not None, "caller A received a real Hermes response")
        check(status_b == 409, f"caller B was rejected while A held the claim (got {status_b}: {resp_b})")
        check(resp_b.get("error") == "DISPATCH_BUSY", "caller B's rejection is DISPATCH_BUSY")
        check(resp_b.get("provider_id") == "hermes", "DISPATCH_BUSY names the contended provider_id")
        check(resp_b.get("provider_session_id") == provider_session_id, "DISPATCH_BUSY names the contended provider_session_id")

        print(f"\n   A <- hermes: {resp_a['response']!r}")
        print(f"   B <- REJECTED: {resp_b}")

    finally:
        print("\n5. Shutting down the real presence authority process...")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_process.kill()
            server_process.wait(timeout=5)
        check(server_process.returncode is not None, "presence authority process reaped, no orphan")

    receipt["proof"] = "PASS"
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
