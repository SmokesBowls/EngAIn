"""
Item 3 (2026-08-19) — SessionLedger-level persistence tests: durable
round trip through the real Ledger API, lazy per-session replay-on-
first-touch, poison-on-write-failure, quarantine-on-corruption, and
isolation between a blocked session and every other session. Forces the
failure modes named in the implementation instruction rather than only
testing normal replay: failed write, failed flush, failed fsync,
repeated access after poison, simultaneous first-touch, and isolation
between a poisoned session and a healthy one.

See session_ledger.py's own module docstring for the mechanism this
proves, and 08-19-2026-item3-framing-integrity-and-write-failure-
amendment.md §2 for the poison policy being enforced here.
"""

from __future__ import annotations

import sys
import threading
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest

from tier1.engainos.core.continuity_cursor_tracker import ContinuityCursorTracker
from tier1.engainos.core.session_journal import SessionJournal
from tier1.engainos.core.session_ledger import SessionLedger, SessionPoisoned, SessionQuarantined


def _append_request(ledger: SessionLedger, session_id: str, text: str):
    return ledger.append(session_id, "dragon_2d", "request", "player", text)


def _append_response(ledger: SessionLedger, session_id: str, text: str, provider_session_id: str = "native-1"):
    return ledger.append(
        session_id,
        "dragon_2d",
        "response",
        "hermes",
        text,
        provider_id="hermes",
        provider_session_id=provider_session_id,
    )


# --- durable round trip through the real Ledger API ------------------------


def test_persisted_append_survives_a_fresh_ledger_instance(tmp_path):
    """Not a real OS process restart (see the live tool for that) — but
    the same journal_root read by a genuinely NEW SessionLedger +
    ContinuityCursorTracker object graph, proving the durable file (not
    any in-process cache) is what carries the state across."""
    cursor1 = ContinuityCursorTracker()
    ledger1 = SessionLedger(journal_root=tmp_path, cursor=cursor1)
    sid = "sess-round-trip"
    _append_request(ledger1, sid, "hello")
    _append_response(ledger1, sid, "hi back")
    _append_request(ledger1, sid, "how are you")
    _append_response(ledger1, sid, "fine", provider_session_id="native-2")

    cursor2 = ContinuityCursorTracker()
    ledger2 = SessionLedger(journal_root=tmp_path, cursor=cursor2)
    turns = ledger2.read_since(sid, since_turn_id=-1)
    assert [t.turn_id for t in turns] == [0, 1, 2, 3]
    assert [t.direction for t in turns] == ["request", "response", "request", "response"]
    assert turns[0].actor == "player"
    assert turns[1].actor == "hermes"
    assert turns[0].payload == "hello"
    assert turns[3].payload == "fine"

    # Cursor state also reconstructed, purely from RESPONSE_COMMITTED
    # frames — no separate cursor file exists.
    assert cursor2.last_seen_turn_id("hermes", "native-1") == 1
    assert cursor2.last_seen_turn_id("hermes", "native-2") == 3
    assert cursor2.last_seen_turn_id("hermes", "native-3") == -1


def test_non_persistent_ledger_unaffected_by_journal_root_default(tmp_path):
    """journal_root=None (the default, matching every pre-item-3 call
    site) must behave exactly as before — no files written anywhere."""
    ledger = SessionLedger()
    sid = "sess-in-memory-only"
    _append_request(ledger, sid, "hi")
    assert not (tmp_path / f"{sid}.journal").exists()
    turns = ledger.read_since(sid, since_turn_id=-1)
    assert len(turns) == 1


def test_response_without_provider_fields_is_rejected_when_persisted(tmp_path):
    ledger = SessionLedger(journal_root=tmp_path)
    with pytest.raises(ValueError):
        ledger.append("sess-x", "dragon_2d", "response", "hermes", "hi")


# --- write / flush / fsync failure -> poison --------------------------------


def test_failed_write_poisons_only_that_session(tmp_path):
    ledger = SessionLedger(journal_root=tmp_path)
    healthy_sid = "sess-healthy-a"
    doomed_sid = "sess-doomed-a"

    with mock.patch("tier1.engainos.core.session_journal.os.write", side_effect=OSError("simulated disk full")):
        with pytest.raises(SessionPoisoned):
            _append_request(ledger, doomed_sid, "this will fail")

    # Repeated access after poison — every subsequent call, not just the
    # first, must keep refusing.
    with pytest.raises(SessionPoisoned):
        _append_request(ledger, doomed_sid, "retry 1")
    with pytest.raises(SessionPoisoned):
        _append_request(ledger, doomed_sid, "retry 2")
    with pytest.raises(SessionPoisoned):
        ledger.raise_if_blocked(doomed_sid)

    # A completely different session_id is unaffected.
    _append_request(ledger, healthy_sid, "still works")
    turns = ledger.read_since(healthy_sid, since_turn_id=-1)
    assert len(turns) == 1
    assert turns[0].payload == "still works"

    # The poisoned session never actually recorded the failed turn in
    # memory either — durable-first ordering means the in-memory turns
    # list for it is still whatever it was before the failed attempt
    # (empty, here).
    assert ledger.read_since(doomed_sid, since_turn_id=-1) == []


def test_failed_fsync_poisons_only_that_session(tmp_path):
    ledger = SessionLedger(journal_root=tmp_path)
    healthy_sid = "sess-healthy-b"
    doomed_sid = "sess-doomed-b"

    with mock.patch("tier1.engainos.core.session_journal.os.fsync", side_effect=OSError("simulated I/O error")):
        with pytest.raises(SessionPoisoned):
            _append_request(ledger, doomed_sid, "fsync will fail")

    with pytest.raises(SessionPoisoned):
        _append_request(ledger, doomed_sid, "still poisoned")

    _append_request(ledger, healthy_sid, "unaffected")
    assert len(ledger.read_since(healthy_sid, since_turn_id=-1)) == 1


def test_failed_write_mid_stream_flush_poisons_only_that_session(tmp_path):
    """Simulates a partial write (some bytes accepted, then failure) —
    the 'flush' half of write->flush->fsync, at the os.write level this
    module actually uses (write() returning a short count is looped;
    this forces the loop itself to raise partway through)."""
    ledger = SessionLedger(journal_root=tmp_path)
    doomed_sid = "sess-doomed-partial-write"

    call_count = {"n": 0}
    real_write = __import__("os").write

    def flaky_write(fd, data):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return min(2, len(data))  # accept a couple bytes, forcing a second loop iteration
        raise OSError("simulated mid-write I/O failure")

    with mock.patch("tier1.engainos.core.session_journal.os.write", side_effect=flaky_write):
        with pytest.raises(SessionPoisoned):
            _append_request(ledger, doomed_sid, "partial write victim")

    with pytest.raises(SessionPoisoned):
        _append_request(ledger, doomed_sid, "still poisoned")


def test_failed_directory_fsync_at_first_creation_poisons_session(tmp_path):
    """The one-time directory-fsync at first creation (frame-and-record-
    shape-design.md §6) failing must poison exactly like a content-fsync
    failure — existence durability matters too."""
    ledger = SessionLedger(journal_root=tmp_path)
    doomed_sid = "sess-doomed-dirfsync"

    real_fsync = __import__("os").fsync
    calls = {"n": 0}

    def fsync_second_call_fails(fd):
        calls["n"] += 1
        if calls["n"] == 1:
            return real_fsync(fd)  # content fsync succeeds
        raise OSError("simulated directory fsync failure")

    with mock.patch("tier1.engainos.core.session_journal.os.fsync", side_effect=fsync_second_call_fails):
        with pytest.raises(SessionPoisoned):
            _append_request(ledger, doomed_sid, "dir fsync victim")


def test_post_durability_in_memory_mutation_failure_poisons_session(tmp_path):
    """Disk commit succeeds; the corresponding RAM mutation unexpectedly
    fails (§13's harder case) — must ALSO poison, not just a durable-
    write failure."""
    ledger = SessionLedger(journal_root=tmp_path)
    sid = "sess-ram-mutation-fails"

    class ExplodingList(list):
        def append(self, *_args, **_kwargs):
            raise RuntimeError("simulated in-memory corruption")

    # Prime the session so _turns[sid] exists, then swap it for a list
    # whose append() always raises — the durable write for the NEXT
    # append will succeed on disk, but the bare list.append() after it
    # must not be allowed to fail silently.
    ledger._turns[sid] = ExplodingList()
    ledger._loaded.add(sid)

    with pytest.raises(SessionPoisoned):
        _append_request(ledger, sid, "this durable write succeeds, memory doesn't")

    with pytest.raises(SessionPoisoned):
        _append_request(ledger, sid, "still poisoned")

    # The durable write DID land — replaying fresh reconstructs it,
    # confirming disk stayed correct even though memory poisoned itself.
    fresh = SessionLedger(journal_root=tmp_path)
    turns = fresh.read_since(sid, since_turn_id=-1)
    assert len(turns) == 1
    assert turns[0].payload == "this durable write succeeds, memory doesn't"


# --- quarantine at the Ledger level, and its isolation ----------------------


def test_corrupted_journal_quarantines_only_that_session(tmp_path):
    # Build a valid journal for one session directly via SessionJournal,
    # then corrupt it on disk before any SessionLedger ever touches it.
    corrupt_sid = "sess-quarantine-me"
    journal = SessionJournal(tmp_path, corrupt_sid)
    journal.append_turn_appended(turn_id=0, origin_body="dragon_2d", payload="x", snapshot=None, timestamp=1.0)
    data = bytearray(journal.path.read_bytes())
    data[-1] ^= 0xFF  # corrupt the final frame's checksum byte
    journal.path.write_bytes(bytes(data))

    ledger = SessionLedger(journal_root=tmp_path)
    with pytest.raises(SessionQuarantined):
        _append_request(ledger, corrupt_sid, "should never land")

    # Repeated access keeps refusing.
    with pytest.raises(SessionQuarantined):
        ledger.raise_if_blocked(corrupt_sid)

    # File actually moved out of the active path.
    assert not journal.path.exists()
    assert (tmp_path / "corrupt").exists()
    assert any((tmp_path / "corrupt").iterdir())

    # A different, healthy session_id is completely unaffected.
    healthy_sid = "sess-healthy-c"
    _append_request(ledger, healthy_sid, "fine")
    assert len(ledger.read_since(healthy_sid, since_turn_id=-1)) == 1


# --- simultaneous first-touch -----------------------------------------------


def test_simultaneous_first_touch_replays_exactly_once(tmp_path):
    """Two threads racing append() for the SAME, not-yet-touched
    session_id, with a real pre-existing journal on disk from a 'prior
    run,' must not double-replay — the existing per-session_id lock
    already serializes this; this test proves it, not assumes it."""
    sid = "sess-simultaneous-first-touch"
    journal = SessionJournal(tmp_path, sid)
    journal.append_turn_appended(turn_id=0, origin_body="dragon_2d", payload="prior", snapshot=None, timestamp=1.0)
    journal.append_response_committed(
        turn_id=1,
        origin_body="dragon_2d",
        actor="hermes",
        provider_id="hermes",
        provider_session_id="native-1",
        payload="prior reply",
        snapshot=None,
        timestamp=1.5,
    )

    replay_calls = {"n": 0}
    real_replay = SessionJournal.replay

    def counting_replay(self):
        replay_calls["n"] += 1
        return real_replay(self)

    ledger = SessionLedger(journal_root=tmp_path)
    barrier = threading.Barrier(2)
    errors = []

    def touch(text: str) -> None:
        try:
            barrier.wait(timeout=5)
            _append_request(ledger, sid, text)
        except Exception as exc:  # pragma: no cover - surfaced via `errors`
            errors.append(exc)

    with mock.patch.object(SessionJournal, "replay", counting_replay):
        t1 = threading.Thread(target=touch, args=("from-thread-1",))
        t2 = threading.Thread(target=touch, args=("from-thread-2",))
        t1.start()
        t2.start()
        t1.join(timeout=5)
        t2.join(timeout=5)

    assert not errors, f"unexpected errors: {errors}"
    assert replay_calls["n"] == 1, "journal was replayed more than once for a single first touch"

    turns = ledger.read_since(sid, since_turn_id=-1)
    # 2 replayed (prior request+response) + 2 new appends, contiguous.
    assert [t.turn_id for t in turns] == [0, 1, 2, 3]
    new_payloads = {t.payload for t in turns[2:]}
    assert new_payloads == {"from-thread-1", "from-thread-2"}


def test_simultaneous_first_touch_on_fresh_session_no_journal_yet(tmp_path):
    """The no-prior-journal case of the same race: two threads both
    touching a brand-new session_id for the first time concurrently must
    still produce exactly 0..N-1, unique, no duplicates — item 2's own
    proven guarantee, now re-verified with persistence engaged."""
    sid = "sess-fresh-concurrent"
    ledger = SessionLedger(journal_root=tmp_path)
    barrier = threading.Barrier(20)
    errors = []

    def touch(i: int) -> None:
        try:
            barrier.wait(timeout=5)
            _append_request(ledger, sid, f"msg-{i}")
        except Exception as exc:  # pragma: no cover
            errors.append(exc)

    threads = [threading.Thread(target=touch, args=(i,)) for i in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=5)

    assert not errors, f"unexpected errors: {errors}"
    ids = [t.turn_id for t in ledger.read_since(sid, since_turn_id=-1)]
    assert sorted(ids) == list(range(20))

    # Reload fresh to confirm the durable file agrees with memory.
    reloaded = SessionLedger(journal_root=tmp_path)
    reloaded_ids = [t.turn_id for t in reloaded.read_since(sid, since_turn_id=-1)]
    assert sorted(reloaded_ids) == list(range(20))
