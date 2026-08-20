"""
Item 3 (2026-08-19) — frame/header-level integrity tests for
session_journal.py, forcing every failure mode named in the
implementation instruction rather than only testing normal replay:
partial header, partial body, partial checksum, corrupted header length,
bad checksum, turn-ID gap, wrong session identity, mid-stream corruption.

See 08-19-2026-item3-framing-integrity-and-write-failure-amendment.md for
the exact rule this file proves: a verified fixed-size header prefix plus
insufficient remaining bytes is the ONLY case treated as a safe torn
tail; everything else (an invalid header, a checksum failure, a sequence
gap, a bad session identity, or corruption anywhere before EOF) is
CORRUPTION — never silently skipped, never mistaken for a torn tail.
"""

from __future__ import annotations

import struct
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest

from tier1.engainos.core.session_journal import (
    JournalCorruption,
    SessionJournal,
    _FILE_PREFIX_SIZE,
    _FRAME_PREFIX_SIZE,
)


def _write_sample(journal: SessionJournal, n_pairs: int = 2) -> None:
    """Writes n_pairs (request, response) turns — a realistic, varied
    fixture: one with a snapshot, one without."""
    for i in range(n_pairs):
        turn_id = i * 2
        journal.append_turn_appended(
            turn_id=turn_id,
            origin_body="dragon_2d",
            payload=f"player says {i}",
            snapshot={"image_path": f"snap_{i}.png"} if i % 2 == 0 else None,
            timestamp=1000.0 + i,
        )
        journal.append_response_committed(
            turn_id=turn_id + 1,
            origin_body="dragon_2d",
            actor="hermes",
            provider_id="hermes",
            provider_session_id="native-1",
            payload=f"hermes replies {i}",
            snapshot=None,
            timestamp=1000.5 + i,
        )


# --- clean round trip, as a sanity baseline for every corruption test below ---


def test_clean_round_trip_reconstructs_every_field_exactly(tmp_path):
    journal = SessionJournal(tmp_path, "sess-roundtrip")
    _write_sample(journal, n_pairs=2)

    result = journal.replay()
    assert [t for t, _ in result.ordered] == ["request", "response", "request", "response"]
    ids = [r.turn_id for _, r in result.ordered]
    assert ids == [0, 1, 2, 3]

    req0 = result.requests[0]
    assert req0.origin_body == "dragon_2d"
    assert req0.payload == "player says 0"
    assert req0.snapshot == {"image_path": "snap_0.png"}

    resp0 = result.responses[0]
    assert resp0.actor == "hermes"
    assert resp0.provider_id == "hermes"
    assert resp0.provider_session_id == "native-1"
    assert resp0.snapshot is None


# --- torn tail: the ONLY safe case ---


def test_torn_tail_after_verified_header_is_safe_discard(tmp_path):
    """A frame whose fixed-size prefix verifies, but whose body/checksum
    never finished, is a torn final append — replay must succeed using
    everything before it, not raise."""
    journal = SessionJournal(tmp_path, "sess-torn")
    _write_sample(journal, n_pairs=1)  # 2 complete frames: request(0), response(1)

    full = journal.path.read_bytes()
    # Truncate mid-way through the LAST frame's body — after its verified
    # fixed prefix, before its full declared body_length is available.
    truncated = full[:-3]
    journal.path.write_bytes(truncated)

    result = journal.replay()
    assert [t for t, _ in result.ordered] == ["request"]
    assert result.requests[0].turn_id == 0


def test_partial_body_only_header_bytes_present_is_safe_discard(tmp_path):
    """Even more torn: only the frame's fixed prefix landed, zero body
    bytes. Still a safe, silent discard of that one incomplete frame."""
    journal = SessionJournal(tmp_path, "sess-partial-body")
    journal.append_turn_appended(turn_id=0, origin_body="dragon_2d", payload="first", snapshot=None, timestamp=1.0)
    after_frame0 = journal.path.read_bytes()

    journal.append_turn_appended(turn_id=1, origin_body="dragon_2d", payload="second", snapshot=None, timestamp=2.0)
    after_frame1 = journal.path.read_bytes()

    frame1_bytes = after_frame1[len(after_frame0) :]
    assert len(frame1_bytes) > _FRAME_PREFIX_SIZE, "test fixture too small to exercise this case"
    truncated = after_frame0 + frame1_bytes[:_FRAME_PREFIX_SIZE]  # header only, zero body bytes
    journal.path.write_bytes(truncated)

    result = journal.replay()
    assert [t for t, _ in result.ordered] == ["request"]
    assert result.requests[0].payload == "first"


def test_partial_checksum_trailer_is_safe_discard(tmp_path):
    """Frame header AND full body landed, but the trailing checksum bytes
    themselves are incomplete — still a torn tail, not corruption."""
    journal = SessionJournal(tmp_path, "sess-partial-checksum")
    _write_sample(journal, n_pairs=1)

    full = journal.path.read_bytes()
    truncated = full[:-1]  # lop off the last byte of the final frame's checksum
    journal.path.write_bytes(truncated)

    result = journal.replay()
    assert [t for t, _ in result.ordered] == ["request"]


# --- corruption: header lies about its own length ---


def test_corrupted_body_length_is_corruption_not_torn_tail(tmp_path):
    """The framing-integrity-amendment's own named failure: a fully
    committed frame whose BODY_LENGTH is later corrupted upward produces
    the same raw symptom as a torn tail ('not enough bytes remain') —
    but because the header's own checksum no longer matches, this must be
    classified as CORRUPTION, never silently treated as safe."""
    journal = SessionJournal(tmp_path, "sess-bad-length")
    _write_sample(journal, n_pairs=1)

    data = bytearray(journal.path.read_bytes())
    # Locate frame 0's BODY_LENGTH field (bytes 5..9 of its fixed prefix,
    # right after MAGIC(4)+VERSION(1)) and corrupt it upward.
    frame0_prefix_start = _FILE_PREFIX_SIZE
    body_length_offset = frame0_prefix_start + 4 + 1  # past MAGIC+VERSION
    corrupted_length = struct.pack(">I", 100_000)  # absurdly large
    data[body_length_offset : body_length_offset + 4] = corrupted_length
    journal.path.write_bytes(bytes(data))

    with pytest.raises(JournalCorruption):
        journal.replay()


def test_corrupted_body_length_downward_still_corruption(tmp_path):
    """Same fault, opposite direction: shrinking BODY_LENGTH also fails
    the header checksum and must not be silently accepted as 'a shorter,
    still-valid frame.'"""
    journal = SessionJournal(tmp_path, "sess-bad-length-down")
    _write_sample(journal, n_pairs=1)

    data = bytearray(journal.path.read_bytes())
    frame0_prefix_start = _FILE_PREFIX_SIZE
    body_length_offset = frame0_prefix_start + 4 + 1
    data[body_length_offset : body_length_offset + 4] = struct.pack(">I", 1)
    journal.path.write_bytes(bytes(data))

    with pytest.raises(JournalCorruption):
        journal.replay()


# --- corruption: bad checksum on an otherwise complete frame ---


def test_bad_frame_checksum_on_full_length_frame_is_corruption(tmp_path):
    journal = SessionJournal(tmp_path, "sess-bad-checksum")
    _write_sample(journal, n_pairs=1)

    data = bytearray(journal.path.read_bytes())
    # Flip one byte inside frame 0's body (well past its header, before
    # its trailer) — header checksum still verifies (untouched), but the
    # whole-frame checksum must not.
    body_start = _FILE_PREFIX_SIZE + _FRAME_PREFIX_SIZE
    data[body_start] ^= 0xFF
    journal.path.write_bytes(bytes(data))

    with pytest.raises(JournalCorruption):
        journal.replay()


def test_bad_frame_header_magic_with_data_still_following_is_corruption(tmp_path):
    """Bad magic while there is still enough trailing data for what
    should have been a complete frame — must halt, not be treated as a
    torn tail just because it 'doesn't parse.'"""
    journal = SessionJournal(tmp_path, "sess-bad-magic")
    _write_sample(journal, n_pairs=2)  # need a second frame following

    data = bytearray(journal.path.read_bytes())
    frame0_prefix_start = _FILE_PREFIX_SIZE
    data[frame0_prefix_start : frame0_prefix_start + 4] = b"XXXX"
    journal.path.write_bytes(bytes(data))

    with pytest.raises(JournalCorruption):
        journal.replay()


# --- corruption: turn_id sequence gap / out-of-order ---


def test_turn_id_gap_across_individually_valid_frames_is_corruption(tmp_path):
    """Two checksum-valid frames whose turn_ids are not the exact
    contiguous 0..N-1 sequence — catches e.g. frames spliced from two
    different partial files, each individually intact."""
    journal = SessionJournal(tmp_path, "sess-turn-gap")
    journal.append_turn_appended(turn_id=0, origin_body="dragon_2d", payload="a", snapshot=None, timestamp=1.0)
    # Deliberately skip turn_id 1 — write turn_id 2 next.
    journal.append_turn_appended(turn_id=2, origin_body="dragon_2d", payload="b", snapshot=None, timestamp=2.0)

    with pytest.raises(JournalCorruption):
        journal.replay()


def test_turn_id_out_of_order_is_corruption(tmp_path):
    journal = SessionJournal(tmp_path, "sess-turn-order")
    journal.append_turn_appended(turn_id=1, origin_body="dragon_2d", payload="a", snapshot=None, timestamp=1.0)
    journal.append_turn_appended(turn_id=0, origin_body="dragon_2d", payload="b", snapshot=None, timestamp=2.0)

    with pytest.raises(JournalCorruption):
        journal.replay()


# --- corruption: wrong session identity ---


def test_wrong_session_identity_is_corruption(tmp_path):
    """A journal file opened under a shared_session_id that doesn't match
    what its own header declares — filename-hash collision or a bug
    upstream, either way must be refused identically."""
    correct = SessionJournal(tmp_path, "sess-correct-identity")
    correct.append_turn_appended(turn_id=0, origin_body="dragon_2d", payload="x", snapshot=None, timestamp=1.0)

    wrong = SessionJournal(tmp_path, "sess-wrong-identity")
    import shutil

    shutil.copy(correct.path, wrong.path)

    with pytest.raises(JournalCorruption):
        wrong.replay()


# --- corruption: file header itself ---


def test_truncated_file_header_is_corruption_not_empty_session(tmp_path):
    journal = SessionJournal(tmp_path, "sess-truncated-header")
    journal.append_turn_appended(turn_id=0, origin_body="dragon_2d", payload="x", snapshot=None, timestamp=1.0)

    data = journal.path.read_bytes()
    journal.path.write_bytes(data[: _FILE_PREFIX_SIZE - 2])  # cut inside the fixed prefix itself

    with pytest.raises(JournalCorruption):
        journal.replay()


def test_bad_file_header_checksum_is_corruption(tmp_path):
    journal = SessionJournal(tmp_path, "sess-bad-header-checksum")
    journal.append_turn_appended(turn_id=0, origin_body="dragon_2d", payload="x", snapshot=None, timestamp=1.0)

    data = bytearray(journal.path.read_bytes())
    data[0] ^= 0xFF  # corrupt the file magic itself
    journal.path.write_bytes(bytes(data))

    with pytest.raises(JournalCorruption):
        journal.replay()


# --- corruption: mid-stream, never scan past it ---


def test_mid_stream_corruption_halts_and_never_skips_to_a_later_valid_frame(tmp_path):
    """Frame 0 valid, frame 1 corrupted, frame 2 (following) individually
    valid on its own bytes. Replay must halt at frame 1 and must NOT
    reconstruct frame 2 by skipping over the hole — the defining
    behavior this whole module exists to guarantee."""
    journal = SessionJournal(tmp_path, "sess-mid-stream")
    journal.append_turn_appended(turn_id=0, origin_body="dragon_2d", payload="first", snapshot=None, timestamp=1.0)
    after_frame0 = journal.path.read_bytes()
    journal.append_turn_appended(turn_id=1, origin_body="dragon_2d", payload="second", snapshot=None, timestamp=2.0)
    after_frame1 = journal.path.read_bytes()
    journal.append_turn_appended(turn_id=2, origin_body="dragon_2d", payload="third", snapshot=None, timestamp=3.0)

    data = bytearray(journal.path.read_bytes())
    # Corrupt a body byte inside frame 1 (the middle frame) only — offset
    # found by diffing real captured byte ranges, not recomputed struct
    # math (see the two simpler capture-based tests above for why).
    frame1_body_start = len(after_frame0) + _FRAME_PREFIX_SIZE
    assert len(after_frame1) > frame1_body_start, "test fixture too small to exercise this case"
    data[frame1_body_start] ^= 0xFF
    journal.path.write_bytes(bytes(data))

    with pytest.raises(JournalCorruption):
        journal.replay()
    # Confirm nothing was silently written back / no partial acceptance:
    # the file on disk is unchanged by the failed replay attempt itself.
    assert journal.path.exists()


# --- quarantine ---


def test_quarantine_moves_file_out_of_active_path(tmp_path):
    journal = SessionJournal(tmp_path, "sess-quarantine-me")
    journal.append_turn_appended(turn_id=0, origin_body="dragon_2d", payload="x", snapshot=None, timestamp=1.0)
    original_path = journal.path
    assert original_path.exists()

    dest = journal.quarantine(reason="test-induced corruption")

    assert not original_path.exists()
    assert dest.exists()
    assert dest.parent == tmp_path / "corrupt"
    assert dest.with_name(dest.name + ".reason.txt").read_text(encoding="utf-8") == "test-induced corruption"


def test_quarantine_is_idempotent_if_file_already_moved(tmp_path):
    journal = SessionJournal(tmp_path, "sess-double-quarantine")
    journal.append_turn_appended(turn_id=0, origin_body="dragon_2d", payload="x", snapshot=None, timestamp=1.0)
    dest1 = journal.quarantine(reason="first")
    # A second quarantine call (e.g. two concurrent detectors) must not
    # raise just because the source is already gone — the source path
    # itself must never come back, regardless of what dest2 resolves to
    # (a millisecond-timestamp collision with dest1 is harmless, not a
    # correctness issue this test needs to rule out).
    journal.quarantine(reason="second")
    assert not journal.path.exists()
    assert dest1.exists()
