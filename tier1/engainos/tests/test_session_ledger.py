"""
Item 2 (2026-08-18) — SessionLedger.append()'s turn_id atomicity, proven
with real threads, not simulated. See
08-18-2026-item2-session-ledger-semantic-derivation.md for the design
this implements: the required invariant is atomic/unique/monotonic
per-session_id turn_id assignment, nothing stronger — no lock spans a
provider dispatch, and unrelated session_ids must never contend.
"""

from __future__ import annotations

import sys
import threading
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tier1.engainos.core.session_ledger import SessionLedger


def test_concurrent_appends_to_one_session_produce_unique_contiguous_ids():
    """Real threads racing append() for the SAME session_id — the exact
    shape of the original bug — must never mint a duplicate turn_id, and
    with an initially empty ledger the result must be exactly 0..N-1."""
    ledger = SessionLedger()
    session_id = "concurrent-one-session"
    total = 50

    def do_append(i: int) -> None:
        ledger.append(session_id, "dragon_2d", "request", "player", f"msg-{i}")

    threads = [threading.Thread(target=do_append, args=(i,)) for i in range(total)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    turns = ledger.read_since(session_id, since_turn_id=-1)
    ids = [t.turn_id for t in turns]
    assert len(ids) == total, "an append was lost"
    assert len(set(ids)) == total, "a turn_id was duplicated"
    assert sorted(ids) == list(range(total)), "ids are not contiguous 0..N-1"


def test_turn_id_monotonically_matches_stored_append_order():
    """read_since()'s own iteration order (physical append order) must
    already be sorted by turn_id — position i in the returned list has
    turn_id i — under real concurrent writers, not just sequential ones."""
    ledger = SessionLedger()
    session_id = "concurrent-order-check"
    total = 30

    def do_append(i: int) -> None:
        ledger.append(session_id, "dragon_2d", "request", "player", f"msg-{i}")

    threads = [threading.Thread(target=do_append, args=(i,)) for i in range(total)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    turns = ledger.read_since(session_id, since_turn_id=-1)
    for position, turn in enumerate(turns):
        assert turn.turn_id == position, (
            f"list position {position} holds turn_id {turn.turn_id} — "
            "append order and turn_id order have diverged"
        )


def test_independent_session_ids_do_not_contend():
    """Different session_ids must use different locks — one session_id's
    in-flight append must never block a completely unrelated one."""
    ledger = SessionLedger()
    lock_a = ledger._lock_for("session-A")
    lock_a.acquire()
    try:
        done = threading.Event()

        def append_b() -> None:
            ledger.append("session-B", "dragon_3d", "request", "player", "hi")
            done.set()

        t = threading.Thread(target=append_b)
        t.start()
        assert done.wait(timeout=5), "session-B's append blocked on an unrelated session-A lock"
        t.join(timeout=5)
    finally:
        lock_a.release()

    turns_b = ledger.read_since("session-B", since_turn_id=-1)
    assert len(turns_b) == 1
    assert turns_b[0].turn_id == 0


def test_concurrent_appends_across_many_sessions_all_land_correctly():
    """A broader real-concurrency sanity check: many threads, many
    distinct session_ids, interleaved — every session ends up with
    exactly the turns it should have, contiguous from 0."""
    ledger = SessionLedger()
    session_ids = [f"session-{i}" for i in range(10)]
    per_session = 20

    def do_append(session_id: str, i: int) -> None:
        ledger.append(session_id, "dragon_2d", "request", "player", f"{session_id}-{i}")

    threads = [
        threading.Thread(target=do_append, args=(sid, i))
        for sid in session_ids
        for i in range(per_session)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    for sid in session_ids:
        ids = [t.turn_id for t in ledger.read_since(sid, since_turn_id=-1)]
        assert sorted(ids) == list(range(per_session)), f"{sid} has wrong/duplicate turn_ids: {ids}"
