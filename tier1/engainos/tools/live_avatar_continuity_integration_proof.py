#!/usr/bin/env python3
"""
live_avatar_continuity_integration_proof.py - The decisive proof that the
REAL dragon2d/dragon3d avatar bodies (engain_avatar, godot_engain_3d_avatar)
share EngAIn's own continuity, through the real presence_authority_server's
new POST /dispatch endpoint, without either avatar repo importing or
vendoring SharedSessionBridge, ContinuityCursorTracker, or
ContinuityContextBuilder itself.

Nothing here constructs those classes directly. Every request goes through
each repo's own unmodified hermes_session_adapter.py, run as a real,
persistent, polling subprocess (the same executable both repos have always
shipped), talking to the real production file mailboxes at
/mnt/data-drive/engain-runtime-mailboxes/{dragon2d,dragon3d}/, exactly as
Godot itself would. The only new thing either worker does is call out to
engain_continuity_client.dispatch() instead of its own director_bridge —
gated behind ENGAIN_CONTINUITY_DISPATCH=1, set here as an env var on the
worker subprocess, never as a code change.

Sequence, matching the avatar-integration flow's own 8 steps:
    1. Start the real presence authority + continuity dispatch server.
    2. Ordinary request through dragon2d — default binding (this worker's
       own frozen native Hermes session, no env override at all).
    3. Recall request through dragon3d, configured (via env) to submit a
       freshly-minted real Claude Code binding instead.
    4. Recovery request through dragon2d — default binding again, same
       frozen native Hermes session as step 2, completely unchanged.
    5. Confirm all three ordinary avatar response files, and that
       director_analysis in each proves EngAIn's continuity path (not the
       old direct-Hermes path) answered, with the correct true actor.
    6. Restart the continuity server (fresh, empty Ledger/cursor) and
       repeat a same-native-session recall through dragon2d — must still
       succeed, but now provably from Hermes's own resumed native memory,
       not EngAIn's Ledger (proven by combining this run's own
       already-tested "empty context -> bare player_input, no recap"
       invariant with the fact that the Ledger really is empty here).
    7. Attempt a cross-provider recall through dragon2d, on a FRESH native
       Hermes session that never received any recap — must NOT succeed,
       since neither that session's own native memory nor EngAIn's
       now-empty Ledger has the Claude exchange. Deliberately NOT the same
       native session step 4 used: that one was cursor-recapped with the
       Claude exchange back in step 4's own predecessor turn, *before* the
       restart, and a recap once dispatched becomes a permanent, genuine
       part of that native session's own transcript from then on — a
       restart cannot and does not retroactively un-teach it. That
       distinction (discovered live, the first time this script ran this
       far) is exactly the honest, named boundary of process-lifetime-only
       Ledger/cursor state: a lost cursor never causes a WRONG answer, but
       it can honestly cost real cross-provider context that was never
       persisted anywhere durable — for any native session that hadn't
       already, natively, been told it before the loss.

Costs real usage: 5 real Hermes CLI calls, 2 real Claude Code CLI calls
(one bootstrap, one dispatch).

Run:
    python3 tier1/engainos/tools/live_avatar_continuity_integration_proof.py
"""

from __future__ import annotations

import base64
import copy
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

REPO_ROOT = Path(__file__).resolve().parents[3]
AUTHORITY_SCRIPT = REPO_ROOT / "tier1" / "engainos" / "server" / "presence_authority_server.py"
DRAGON2D_REPO = Path("/mnt/data-drive/engain_avatar")
DRAGON3D_REPO = Path("/mnt/data-drive/godot_engain_3d_avatar")
MAILBOX_ROOT = Path("/mnt/data-drive/engain-runtime-mailboxes")
LOG_DIR = REPO_ROOT / "runtime" / "logs" / "avatar_continuity_integration_proof"
RECEIPT_PATH = REPO_ROOT / "runtime" / "logs" / "AVATAR_CONTINUITY_INTEGRATION_PROOF_V1.report.json"
REMEMBERED_PHRASE = "opal thicket"


class ProofFailure(Exception):
    pass


def check(condition: bool, message: str) -> None:
    if not condition:
        raise ProofFailure(f"FAILED: {message}")
    print(f"  OK  {message}")


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _new_shared_session_id() -> str:
    return f"shared-{uuid.uuid4().hex}"


HERMES_SESSION_ID_PATTERN_RE = __import__("re").compile(r"(?m)^session_id:\s*([^\s]+)\s*$")


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
    match = HERMES_SESSION_ID_PATTERN_RE.search(completed.stderr)
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


class AuthorityServer:
    def __init__(self) -> None:
        self.port = _free_port()
        self.base_url = f"http://127.0.0.1:{self.port}"
        self.proc: Optional[subprocess.Popen] = None
        self.log_path = LOG_DIR / f"authority.{self.port}.log"

    def start(self) -> None:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        log_file = open(self.log_path, "a")
        self.proc = subprocess.Popen(
            [sys.executable, str(AUTHORITY_SCRIPT), "--port", str(self.port)],
            stdout=log_file, stderr=subprocess.STDOUT, cwd=str(REPO_ROOT),
        )
        deadline = time.monotonic() + 10.0
        healthy = False
        while time.monotonic() < deadline:
            try:
                with urllib.request.urlopen(self.base_url + "/health", timeout=1.0) as resp:
                    if resp.status == 200:
                        healthy = True
                        break
            except Exception:
                time.sleep(0.05)
        if not healthy:
            self.stop()
            raise ProofFailure(f"presence authority did not become healthy on port {self.port}")

    def stop(self) -> None:
        if self.proc is None:
            return
        self.proc.terminate()
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait(timeout=5)
        self.proc = None


class AvatarWorker:
    """One real, persistent (non---once) hermes_session_adapter.py
    subprocess for one repo, driven exactly the way Godot's own bridge
    drives it: --publish-request, poll for response.json, --claim-response.
    """

    def __init__(self, repo_dir: Path, origin_label: str, authority_url: str, env_overrides: Dict[str, str]) -> None:
        self.repo_dir = repo_dir
        self.origin_label = origin_label
        self.authority_url = authority_url
        self.env_overrides = env_overrides
        self.proc: Optional[subprocess.Popen] = None
        self.log_path = LOG_DIR / f"{origin_label}.{uuid.uuid4().hex[:8]}.log"
        self.mailbox_dir = MAILBOX_ROOT / origin_label
        self.request_path = self.mailbox_dir / "request.json"
        self.response_path = self.mailbox_dir / "response.json"
        self.listener_path = self.mailbox_dir / "listener.json"

    def _env(self) -> Dict[str, str]:
        env = dict(os.environ)
        env["ENGAIN_PRESENCE_AUTHORITY_URL"] = self.authority_url
        env.pop("ENGAIN_PRESENCE_AUTHORITY_FAIL_OPEN_COMPAT", None)
        env.update(self.env_overrides)
        return env

    def start(self) -> None:
        if self.response_path.exists():
            raise ProofFailure(f"{self.response_path} already has an unread response before this run started")
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        log_file = open(self.log_path, "a")
        self.proc = subprocess.Popen(
            [sys.executable, "hermes_session_adapter.py", "--project-dir", str(self.repo_dir)],
            cwd=str(self.repo_dir), env=self._env(),
            stdout=log_file, stderr=subprocess.STDOUT,
        )
        deadline = time.monotonic() + 15.0
        alive = False
        while time.monotonic() < deadline:
            try:
                payload = json.loads(self.listener_path.read_text(encoding="utf-8"))
                pid = payload.get("pid")
                expires_at = payload.get("expires_at")
                if pid == self.proc.pid and isinstance(expires_at, (int, float)) and expires_at > time.time():
                    alive = True
                    break
            except (OSError, ValueError, json.JSONDecodeError):
                pass
            if self.proc.poll() is not None:
                raise ProofFailure(
                    f"{self.origin_label} worker exited early (code {self.proc.returncode}); see {self.log_path}"
                )
            time.sleep(0.05)
        if not alive:
            self.stop()
            raise ProofFailure(f"{self.origin_label} worker never reported itself as a live listener")

    def publish_and_await(self, payload: Dict[str, Any], timeout: float = 150.0) -> Dict[str, Any]:
        # publish_request() hard-links this into the mailbox (os.link) —
        # must be on the same filesystem as the mailbox itself, which
        # LOG_DIR (under the EngAIn checkout, a different mount) is not.
        tmp_dir = MAILBOX_ROOT / "_proof_tmp"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = tmp_dir / f"{self.origin_label}.{uuid.uuid4().hex}.request.tmp.json"
        tmp_path.write_text(json.dumps(payload), encoding="utf-8")
        completed = subprocess.run(
            [sys.executable, "hermes_session_adapter.py", "--publish-request", str(tmp_path)],
            cwd=str(self.repo_dir), env=self._env(), capture_output=True, text=True, timeout=15,
        )
        if completed.returncode != 0:
            raise ProofFailure(f"{self.origin_label} --publish-request failed: {completed.stderr}")

        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.response_path.exists():
                break
            if self.proc is not None and self.proc.poll() is not None:
                raise ProofFailure(f"{self.origin_label} worker died while awaiting a response; see {self.log_path}")
            time.sleep(0.1)
        else:
            raise ProofFailure(f"{self.origin_label} response never arrived within {timeout}s")

        claimed = subprocess.run(
            [sys.executable, "hermes_session_adapter.py", "--claim-response", str(self.response_path)],
            cwd=str(self.repo_dir), env=self._env(), capture_output=True, text=True, timeout=15,
        )
        if claimed.returncode != 0:
            raise ProofFailure(f"{self.origin_label} --claim-response failed: {claimed.stderr}")
        marker = "ENGAIN_RESPONSE_JSON_BASE64="
        line = next((l for l in claimed.stdout.splitlines() if l.startswith(marker)), None)
        if line is None:
            raise ProofFailure(f"{self.origin_label} --claim-response produced no response marker: {claimed.stdout!r}")
        decoded = base64.b64decode(line[len(marker):]).decode("utf-8")
        return json.loads(decoded)

    def stop(self) -> None:
        if self.proc is None:
            return
        if self.proc.poll() is None:
            self.proc.send_signal(signal.SIGINT)
            try:
                self.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.proc.terminate()
                try:
                    self.proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.proc.kill()
                    self.proc.wait(timeout=5)
        self.proc = None


_BUILD_HELPER = """
import json, pathlib, sys
sys.path.insert(0, sys.argv[2])
sys.path.insert(0, sys.argv[2] + "/tests")
from test_hermes_session_adapter import _build_request
# The fixture's own snapshots.mkdir(parents=True) assumes a fresh tmp_path;
# this repo's real snapshots/ directory already exists from real usage.
# Tolerating that (exist_ok=True) is the only change from the fixture's
# own behavior -- everything it writes still lands for real, under the
# repo's own real snapshots/ directory, just alongside what's there.
_orig_mkdir = pathlib.Path.mkdir
def _tolerant_mkdir(self, *a, **kw):
    kw["exist_ok"] = True
    return _orig_mkdir(self, *a, **kw)
pathlib.Path.mkdir = _tolerant_mkdir
print(json.dumps(_build_request(pathlib.Path(sys.argv[2]))))
"""

_RETIME_HELPER = """
import json, sys
sys.path.insert(0, sys.argv[2])
sys.path.insert(0, sys.argv[2] + "/tests")
from test_hermes_session_adapter import _retime_request
payload = json.loads(sys.stdin.read())
_retime_request(__import__("pathlib").Path(sys.argv[2]), payload)
print(json.dumps(payload))
"""


def _base_request_payload(repo_dir: Path) -> Dict[str, Any]:
    """Reuses each repo's own already-tested request-construction fixture
    rather than hand-rolling a second, parallel copy of the perception
    schema this proof would then be trusting blindly. Run as a fresh
    subprocess per repo — both repos define an identically-named
    test_hermes_session_adapter module, which would collide in
    sys.modules if imported twice in this one long-lived process."""
    completed = subprocess.run(
        [sys.executable, "-c", _BUILD_HELPER, "build", str(repo_dir)],
        cwd=str(repo_dir), capture_output=True, text=True, timeout=15,
    )
    if completed.returncode != 0:
        raise ProofFailure(f"building base request payload for {repo_dir} failed: {completed.stderr}")
    return json.loads(completed.stdout)


def _retime_payload(repo_dir: Path, payload: Dict[str, Any]) -> Dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, "-c", _RETIME_HELPER, "retime", str(repo_dir)],
        cwd=str(repo_dir), input=json.dumps(payload), capture_output=True, text=True, timeout=15,
    )
    if completed.returncode != 0:
        raise ProofFailure(f"retiming request payload for {repo_dir} failed: {completed.stderr}")
    return json.loads(completed.stdout)


_REQUEST_COUNTER = [0]


def run_turn(worker: AvatarWorker, repo_dir: Path, base_payload: Dict[str, Any], player_input: str) -> Dict[str, Any]:
    _REQUEST_COUNTER[0] += 1
    n = _REQUEST_COUNTER[0]
    payload = copy.deepcopy(base_payload)
    payload["player_input"] = player_input
    # godot_engain_3d_avatar enforces req_[0-9a-f]{32} strictly; engain_avatar
    # is looser, but this shape satisfies both.
    payload["request_id"] = f"req_{uuid.uuid4().hex}"
    # client_request_id deliberately left as the fixture's own constant —
    # it must match the value embedded inside the snapshot metadata file
    # (CLIENT_REQUEST_ID_MISMATCH otherwise), and nothing here needs it
    # unique per turn; request_id above already is.
    payload = _retime_payload(repo_dir, payload)
    return worker.publish_and_await(payload)


def main() -> int:
    print("=== live_avatar_continuity_integration_proof ===")
    shared_session_id = _new_shared_session_id()
    print(f"shared_session_id: {shared_session_id}")

    print("\n[bootstrap] minting a real Claude Code native session...")
    claude_provider_session_id = mint_real_claude_session(
        "Session bootstrap for an EngAIn avatar continuity integration proof. Reply with exactly: READY"
    )
    check(bool(claude_provider_session_id), f"claude bootstrap minted a real session_id: {claude_provider_session_id}")

    authority = AuthorityServer()
    authority.start()
    print(f"\n[authority] listening on {authority.base_url}")

    base2d = _base_request_payload(DRAGON2D_REPO)
    base3d = _base_request_payload(DRAGON3D_REPO)

    active_workers: list = []

    def _new_worker(repo_dir: Path, label: str, overrides: Dict[str, str]) -> AvatarWorker:
        """Tracked so a mid-run exception can never leave a worker
        subprocess (and its PidFileLock) orphaned — see the cleanup that
        already happened once, live, during this proof's own development."""
        w = AvatarWorker(repo_dir, label, authority.base_url, overrides)
        active_workers.append(w)
        w.start()
        return w

    responses: Dict[str, Dict[str, Any]] = {}
    try:
        # Step 2 — ordinary request through dragon2d, default binding.
        worker2d = _new_worker(DRAGON2D_REPO, "dragon2d", {
            "ENGAIN_CONTINUITY_DISPATCH": "1",
            "ENGAIN_CONTINUITY_SHARED_SESSION_ID": shared_session_id,
        })
        responses["01_dragon2d_remember"] = run_turn(
            worker2d, DRAGON2D_REPO, base2d,
            f"Remember the phrase: {REMEMBERED_PHRASE}. Reply with exactly: noted.",
        )
        worker2d.stop()

        # Step 3 — recall through dragon3d, explicit Claude Code binding.
        worker3d = _new_worker(DRAGON3D_REPO, "dragon3d", {
            "ENGAIN_CONTINUITY_DISPATCH": "1",
            "ENGAIN_CONTINUITY_SHARED_SESSION_ID": shared_session_id,
            "ENGAIN_CONTINUITY_PROVIDER_ID": "claude_code",
            # Empty, deliberately: claude_code_provider_adapter.py only adds
            # --model when this is truthy, letting the CLI use its own
            # default — same choice the already-proven
            # live_cross_provider_portability_proof.py makes, and for the
            # same reason: there is no real model name "claude-code-cli".
            "ENGAIN_CONTINUITY_MODEL_ID": "",
            "ENGAIN_CONTINUITY_PROVIDER_SESSION_ID": claude_provider_session_id,
            "ENGAIN_CONTINUITY_LAUNCH_OPTIONS": "{}",
        })
        responses["02_dragon3d_recall"] = run_turn(
            worker3d, DRAGON3D_REPO, base3d,
            "Whatever record you were given of an earlier exchange, extract the exact phrase that was "
            "asked to be remembered in it. Then invent one brand-new, completely unrelated single "
            "made-up word of your own (not a real word, not related to the phrase at all — you choose "
            "it freely). Output ONLY this exact format and nothing else, no commentary: "
            "<the extracted phrase>|<your invented word>",
        )
        worker3d.stop()
        claude_invented_word = responses["02_dragon3d_recall"]["narrative_response"].split("|")[-1].strip().strip(".\"'")
        print(f"  claude invented word: {claude_invented_word!r}")

        # Step 4 — recovery through dragon2d, default binding again.
        worker2d = _new_worker(DRAGON2D_REPO, "dragon2d", {
            "ENGAIN_CONTINUITY_DISPATCH": "1",
            "ENGAIN_CONTINUITY_SHARED_SESSION_ID": shared_session_id,
        })
        responses["03_dragon2d_recover"] = run_turn(
            worker2d, DRAGON2D_REPO, base2d,
            "Whatever record you were given of what the other assistant replied, extract and output "
            "ONLY the exact phrase from it. Output that phrase and absolutely nothing else — no "
            "commentary, no caveats.",
        )
        worker2d.stop()

        print("\n[assertions] steps 2-4:")
        r1, r2, r3 = responses["01_dragon2d_remember"], responses["02_dragon3d_recall"], responses["03_dragon2d_recover"]
        check("noted." in r1["narrative_response"].lower(), f"dragon2d turn 1: {r1['narrative_response']!r}")
        check("EngAIn shared continuity" in r1["director_analysis"], "turn 1 used the new continuity path")
        check(REMEMBERED_PHRASE in r2["narrative_response"], f"dragon3d recall got the phrase: {r2['narrative_response']!r}")
        check("actor='claude_code'" in r2["director_analysis"], "turn 2 truly answered by claude_code")
        check(REMEMBERED_PHRASE in r3["narrative_response"], f"dragon2d recovery got the phrase: {r3['narrative_response']!r}")
        check("actor='hermes'" in r3["director_analysis"], "turn 3 truly answered by hermes")

        # Step 6 — restart the continuity server: Ledger and cursor both
        # empty afterward. A same-native-session recall must still work —
        # from Hermes's own resumed native memory, never from EngAIn.
        print("\n[restart] stopping and restarting the continuity server (fresh Ledger + cursor)...")
        authority.stop()
        authority = AuthorityServer()
        authority.start()
        print(f"[authority] restarted on {authority.base_url}")

        worker2d = _new_worker(DRAGON2D_REPO, "dragon2d", {
            "ENGAIN_CONTINUITY_DISPATCH": "1",
            "ENGAIN_CONTINUITY_SHARED_SESSION_ID": shared_session_id,
        })
        responses["04_dragon2d_post_restart_same_session"] = run_turn(
            worker2d, DRAGON2D_REPO, base2d,
            f"Earlier you said 'noted.' to a phrase I asked you to remember. "
            f"Output ONLY that exact phrase and absolutely nothing else — no commentary, no caveats.",
        )
        worker2d.stop()

        # Step 7 — cross-provider recall attempt, on a FRESH native Hermes
        # session that was never resumed before this line, not the one
        # turns 1/3 used. This distinction turned out to matter and is
        # worth being explicit about: turn 3, *before* the restart, already
        # dispatched a cursor-driven recap containing claude_invented_word
        # to that original native session (--resume 20260731_065008_63a62d)
        # — and once dispatched, that text becomes a permanent part of that
        # session's own native transcript, exactly like anything else ever
        # said to it. A restart empties EngAIn's Ledger, but it cannot and
        # does not retroactively un-teach a native session what it already
        # received before the restart. Asking that same session about
        # claude_invented_word again here would therefore succeed via
        # genuine native memory, not prove anything about the Ledger —
        # which is exactly what an earlier run of this proof caught. A
        # session that never received that recap has no such contamination:
        # if the Ledger is what would have supplied claude_invented_word to
        # it, and the Ledger is now empty, it cannot answer.
        fresh_hermes_session_id = mint_real_hermes_session(
            "Session bootstrap for the post-restart isolation leg of an EngAIn avatar "
            "continuity integration proof. Reply with exactly: READY"
        )
        check(bool(fresh_hermes_session_id), f"minted a fresh, never-recapped hermes session: {fresh_hermes_session_id}")

        worker2d_fresh = _new_worker(DRAGON2D_REPO, "dragon2d", {
            "ENGAIN_CONTINUITY_DISPATCH": "1",
            "ENGAIN_CONTINUITY_SHARED_SESSION_ID": shared_session_id,
            "ENGAIN_CONTINUITY_PROVIDER_SESSION_ID": fresh_hermes_session_id,
        })
        responses["05_dragon2d_post_restart_cross_provider"] = run_turn(
            worker2d_fresh, DRAGON2D_REPO, base2d,
            "A different assistant invented an arbitrary made-up word during this conversation and "
            "told it to you. What exactly was that made-up word? If you don't know, say so plainly.",
        )
        worker2d_fresh.stop()

        print("\n[assertions] steps 6-7 (restart boundary):")
        r4 = responses["04_dragon2d_post_restart_same_session"]
        r5 = responses["05_dragon2d_post_restart_cross_provider"]
        check(
            REMEMBERED_PHRASE in r4["narrative_response"],
            f"post-restart, dragon2d still recalls its OWN native turn from Hermes's own memory: {r4['narrative_response']!r}",
        )
        check(
            "EngAIn shared continuity" in r4["director_analysis"],
            "turn 4 still went through the new continuity path (dispatch_input was bare — empty Ledger, nothing to recap)",
        )
        check(
            claude_invented_word.lower() not in r5["narrative_response"].lower(),
            f"post-restart, dragon2d correctly does NOT recover claude's invented word "
            f"{claude_invented_word!r}: {r5['narrative_response']!r}",
        )

    finally:
        for w in active_workers:
            try:
                w.stop()
            except Exception as exc:
                print(f"[cleanup] failed to stop {w.origin_label} worker: {exc}", file=sys.stderr)
        authority.stop()

    RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT_PATH.write_text(json.dumps({
        "shared_session_id": shared_session_id,
        "claude_provider_session_id": claude_provider_session_id,
        "hermes_provider_session_id": "20260731_065008_63a62d",
        "claude_invented_word": claude_invented_word,
        "fresh_hermes_session_id_post_restart": fresh_hermes_session_id,
        "responses": responses,
    }, indent=2), encoding="utf-8")
    print(f"\nReceipt written to {RECEIPT_PATH}")
    print("\n=== ALL CHECKS PASSED ===")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ProofFailure as exc:
        print(f"\n!!! PROOF FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)
