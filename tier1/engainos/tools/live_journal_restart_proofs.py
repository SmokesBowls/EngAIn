#!/usr/bin/env python3
"""
live_journal_restart_proofs.py - Item 3's two required real process-
restart proofs, per implementation instruction:

  1. Complete Ledger + Cursor reconstruction from an actual journal,
     across a genuine OS process restart (not just a new object in this
     same process — a real `python3` subprocess, spawned fresh, reading
     the same durable file this process wrote).
  2. Truncating the final frame at multiple byte offsets and proving
     only fully committed frames survive recovery — each truncation
     point verified by another genuinely separate subprocess.

Both proofs write real files to a fresh, isolated temp directory (never
runtime/sessions/ — this tool must not depend on, or pollute, real
server state) and use only the public SessionLedger/ContinuityCursorTracker
API in this process, and the identical public API again in the child
subprocess, to reconstruct state — no shortcuts, no internal-attribute
peeking on the "after restart" side.

Run:
    python3 tier1/engainos/tools/live_journal_restart_proofs.py
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tier1.engainos.core.continuity_cursor_tracker import ContinuityCursorTracker
from tier1.engainos.core.session_ledger import SessionLedger

RECEIPT_PATH = REPO_ROOT / "runtime" / "logs" / "LIVE_JOURNAL_RESTART_PROOFS_V1.report.json"

# The child subprocess's own program, kept as one literal string so both
# proofs below can reuse it with different arguments — genuinely a
# separate `python3` invocation each time (a real process, not a thread
# or a re-imported module in this same interpreter).
_RECONSTRUCT_PROGRAM = r"""
import json, sys
sys.path.insert(0, {repo_root!r})
from tier1.engainos.core.continuity_cursor_tracker import ContinuityCursorTracker
from tier1.engainos.core.session_ledger import SessionLedger

journal_root = {journal_root!r}
session_ids = {session_ids!r}

cursor = ContinuityCursorTracker()
ledger = SessionLedger(journal_root=journal_root, cursor=cursor)

out = {{"sessions": {{}}}}
for sid in session_ids:
    turns = ledger.read_since(sid, since_turn_id=-1)
    out["sessions"][sid] = {{
        "turns": [
            {{
                "turn_id": t.turn_id, "direction": t.direction, "actor": t.actor,
                "origin_body": t.origin_body, "payload": t.payload, "snapshot": t.snapshot,
            }}
            for t in turns
        ],
    }}
    # Probe every (provider_id, provider_session_id) pair this proof
    # process itself knows about, passed in explicitly — see cursor_probes.
out["cursor"] = {{}}
for provider_id, provider_session_id in {cursor_probes!r}:
    out["cursor"][f"{{provider_id}}|{{provider_session_id}}"] = cursor.last_seen_turn_id(provider_id, provider_session_id)

print(json.dumps(out))
"""


class ProofFailure(Exception):
    pass


def check(condition: bool, message: str) -> None:
    if not condition:
        raise ProofFailure(message)
    print(f"  OK  {message}")


def _run_reconstruction_subprocess(
    journal_root: Path, session_ids: List[str], cursor_probes: List[List[str]]
) -> Dict[str, Any]:
    program = _RECONSTRUCT_PROGRAM.format(
        repo_root=str(REPO_ROOT),
        journal_root=str(journal_root),
        session_ids=session_ids,
        cursor_probes=[tuple(p) for p in cursor_probes],
    )
    completed = subprocess.run(
        [sys.executable, "-c", program],
        capture_output=True, text=True, timeout=30,
    )
    if completed.returncode != 0:
        raise ProofFailure(
            f"reconstruction subprocess failed (exit {completed.returncode}): {completed.stderr}"
        )
    try:
        return json.loads(completed.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError) as exc:
        raise ProofFailure(f"reconstruction subprocess produced no parseable JSON: {completed.stdout!r}") from exc


# --------------------------------------------------------------------------
# Proof 1: complete Ledger + Cursor reconstruction from an actual journal,
# across a real process restart.
# --------------------------------------------------------------------------


def proof_full_reconstruction() -> Dict[str, Any]:
    print("\n=== Proof 1: full Ledger + Cursor reconstruction across a real process restart ===")
    with tempfile.TemporaryDirectory(prefix="engain-item3-restart-proof-") as tmp:
        journal_root = Path(tmp)
        cursor = ContinuityCursorTracker()
        ledger = SessionLedger(journal_root=journal_root, cursor=cursor)

        sid_a, sid_b = "proof-session-a", "proof-session-b"

        # Session A: two exchanges on one native provider session, one
        # with a snapshot.
        ledger.append(sid_a, "dragon_2d", "request", "player", "hello a", snapshot={"image_path": "a0.png"})
        ledger.append(sid_a, "dragon_2d", "response", "hermes", "hi a", provider_id="hermes", provider_session_id="native-a-1")
        ledger.append(sid_a, "dragon_2d", "request", "player", "how are you a")
        ledger.append(sid_a, "dragon_2d", "response", "hermes", "fine a", provider_id="hermes", provider_session_id="native-a-1")

        # Session B: a provider switch mid-session (two distinct native
        # provider sessions touch the same shared_session_id).
        ledger.append(sid_b, "dragon_3d", "request", "player", "hello b")
        ledger.append(sid_b, "dragon_3d", "response", "claude_code", "hi b", provider_id="claude_code", provider_session_id="native-b-1")
        ledger.append(sid_b, "dragon_3d", "request", "player", "switch now")
        ledger.append(sid_b, "dragon_3d", "response", "hermes", "switched b", provider_id="hermes", provider_session_id="native-b-2")

        before = {
            sid_a: [(t.turn_id, t.direction, t.payload) for t in ledger.read_since(sid_a, since_turn_id=-1)],
            sid_b: [(t.turn_id, t.direction, t.payload) for t in ledger.read_since(sid_b, since_turn_id=-1)],
        }
        before_cursor = {
            "hermes|native-a-1": cursor.last_seen_turn_id("hermes", "native-a-1"),
            "claude_code|native-b-1": cursor.last_seen_turn_id("claude_code", "native-b-1"),
            "hermes|native-b-2": cursor.last_seen_turn_id("hermes", "native-b-2"),
        }
        print(f"  Before (this process): {json.dumps(before)}")
        print(f"  Before cursor: {before_cursor}")

        # This process's own SessionLedger/ContinuityCursorTracker are now
        # deliberately discarded (fall out of scope) — the only thing that
        # can possibly supply the "after" state is the durable journal
        # files on disk, read by a completely separate `python3` process.
        del ledger, cursor

        after = _run_reconstruction_subprocess(
            journal_root,
            [sid_a, sid_b],
            [["hermes", "native-a-1"], ["claude_code", "native-b-1"], ["hermes", "native-b-2"]],
        )
        print(f"  After (real subprocess): {json.dumps(after)}")

        after_a = [(t["turn_id"], t["direction"], t["payload"]) for t in after["sessions"][sid_a]["turns"]]
        after_b = [(t["turn_id"], t["direction"], t["payload"]) for t in after["sessions"][sid_b]["turns"]]

        check(after_a == before[sid_a], "session A's full turn sequence reconstructed exactly")
        check(after_b == before[sid_b], "session B's full turn sequence reconstructed exactly")
        check(
            after["sessions"][sid_a]["turns"][0]["snapshot"] == {"image_path": "a0.png"},
            "session A's snapshot survived reconstruction verbatim",
        )
        check(after["cursor"] == before_cursor, "cursor state reconstructed exactly from RESPONSE_COMMITTED frames alone")

        return {"proof": "full_reconstruction", "result": "PASS", "before": before, "after": after}


# --------------------------------------------------------------------------
# Proof 2: truncating the final frame at multiple byte offsets — only
# fully committed frames survive recovery, verified by a real subprocess
# for each truncation point.
# --------------------------------------------------------------------------


def proof_truncation_recovery() -> Dict[str, Any]:
    print("\n=== Proof 2: truncated final frame at multiple byte offsets — real subprocess recovery ===")
    trial_results: List[Dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="engain-item3-truncation-proof-") as tmp:
        journal_root = Path(tmp)
        cursor = ContinuityCursorTracker()
        ledger = SessionLedger(journal_root=journal_root, cursor=cursor)
        sid = "proof-truncation-session"

        # Capture the file's exact byte length after each of 4 complete
        # frames (2 request/response pairs), so we know precisely where
        # "the last frame" starts for the truncation trials below.
        boundaries: List[int] = []
        ledger.append(sid, "dragon_2d", "request", "player", "first")
        journal_path = journal_root / f"{__import__('hashlib').sha256(sid.encode()).hexdigest()}.journal"
        boundaries.append(journal_path.stat().st_size)
        ledger.append(sid, "dragon_2d", "response", "hermes", "first ack", provider_id="hermes", provider_session_id="native-t")
        boundaries.append(journal_path.stat().st_size)
        ledger.append(sid, "dragon_2d", "request", "player", "second")
        boundaries.append(journal_path.stat().st_size)
        # This 4th append is the one whose frame we'll truncate at several
        # points — a RESPONSE_COMMITTED frame (the larger/more field-rich
        # of the two record types), giving more interior byte offsets to
        # choose from.
        ledger.append(sid, "dragon_2d", "response", "hermes", "second ack", provider_id="hermes", provider_session_id="native-t")
        final_size = journal_path.stat().st_size
        del ledger, cursor

        last_frame_start = boundaries[2]  # end of the 3rd complete frame == start of the 4th
        last_frame_len = final_size - last_frame_start
        check(last_frame_len > 8, "fixture's final frame is large enough to offer multiple interior truncation points")

        full_bytes = journal_path.read_bytes()
        assert len(full_bytes) == final_size

        # Multiple distinct interior offsets within the final frame: just
        # past its fixed prefix start, roughly a third in, and one byte
        # short of complete.
        offsets = sorted(
            {
                last_frame_start + 1,
                last_frame_start + max(2, last_frame_len // 3),
                last_frame_start + max(3, (last_frame_len * 2) // 3),
                final_size - 1,
            }
        )
        print(f"  Complete file: {final_size} bytes. Final frame spans [{last_frame_start}, {final_size}). "
              f"Truncation offsets under test: {offsets}")

        for offset in offsets:
            journal_path.write_bytes(full_bytes[:offset])
            after = _run_reconstruction_subprocess(journal_root, [sid], [["hermes", "native-t"]])
            turns = after["sessions"][sid]["turns"]
            ids = [t["turn_id"] for t in turns]
            ok = ids == [0, 1, 2]  # exactly the 3 fully-committed frames before the truncated 4th
            print(f"  offset={offset:4d} -> recovered turn_ids={ids} "
                  f"{'OK' if ok else 'MISMATCH'}")
            trial_results.append({"offset": offset, "recovered_turn_ids": ids, "pass": ok})
            check(ok, f"truncation at offset {offset} recovers exactly turns [0, 1, 2], nothing torn or fabricated")
            # cursor must reflect only the one fully-committed response
            # (turn 1) — the truncated 4th frame's cursor evidence must
            # never appear.
            cursor_ok = after["cursor"]["hermes|native-t"] == 1
            check(cursor_ok, f"truncation at offset {offset} leaves cursor at turn 1 (the last committed response), not 3")

        # Sanity control: truncating to EXACTLY the clean frame boundary
        # (no interior corruption at all — the 4th frame was simply never
        # started) must also recover exactly [0, 1, 2], proving the
        # interior-offset trials above aren't passing for a trivial
        # reason.
        journal_path.write_bytes(full_bytes[:last_frame_start])
        after = _run_reconstruction_subprocess(journal_root, [sid], [["hermes", "native-t"]])
        boundary_ids = [t["turn_id"] for t in after["sessions"][sid]["turns"]]
        check(boundary_ids == [0, 1, 2], "clean frame-boundary truncation (control case) also recovers exactly [0, 1, 2]")

        # Restore the untruncated file and confirm all 4 frames are
        # recoverable when nothing is torn — the full-fixture control.
        journal_path.write_bytes(full_bytes)
        after = _run_reconstruction_subprocess(journal_root, [sid], [["hermes", "native-t"]])
        full_ids = [t["turn_id"] for t in after["sessions"][sid]["turns"]]
        check(full_ids == [0, 1, 2, 3], "untruncated file (control case) recovers all 4 committed frames")

    return {"proof": "truncation_recovery", "result": "PASS", "trials": trial_results}


def main() -> int:
    receipt: Dict[str, Any] = {
        "schema": "engain.live_journal_restart_proofs.v1",
        "started_at": time.time(),
    }
    try:
        receipt["proof_1_full_reconstruction"] = proof_full_reconstruction()
        receipt["proof_2_truncation_recovery"] = proof_truncation_recovery()
    except ProofFailure as exc:
        print(f"\nFAIL: {exc}")
        receipt["result"] = "FAIL"
        receipt["failure"] = str(exc)
        RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
        RECEIPT_PATH.write_text(json.dumps(receipt, indent=2))
        return 1

    receipt["result"] = "PASS"
    receipt["finished_at"] = time.time()
    RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2))
    print(f"\nAll checks passed. Receipt written to {RECEIPT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
