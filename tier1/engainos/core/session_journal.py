"""
session_journal.py - The durable, per-shared_session_id continuity journal
(item 3, 2026-08-19). Implements the format derived across
08-19-2026-item3-{restart-continuity-derivation,crash-consistency-design,
encoding-selection-design,frame-and-record-shape-design,
framing-integrity-and-write-failure-amendment}.md — this module is the
concrete implementation of those five design passes, none of which
shipped any runtime code themselves.

Scope, exactly as those documents fixed it:
    Persisted:      SessionLedger's Turn stream (as two event kinds,
                     TURN_APPENDED / RESPONSE_COMMITTED) and, derived
                     from RESPONSE_COMMITTED alone at replay time,
                     ContinuityCursorTracker's (provider_id,
                     provider_session_id) -> turn_id state.
    NOT persisted:   PresenceRegistry, SessionClaimRegistry,
                     shared_session_id ownership, native provider
                     transcripts. This module has no knowledge of any of
                     those and imports none of their modules.

Two layers, kept strictly separate (frame-and-record-shape-design.md
§1-3) so the record encoding can change (a project-shaped ZW encoding,
someday) without touching the durability mechanism:

    FILE HEADER  - written once, at journal creation: magic, format
                   version, the original shared_session_id (verified on
                   every open — see FileHeader.write/read below), a
                   checksum.
    FRAME        - one per durable event. Self-describing,
                   length-delimited, whole-frame-checksummed. NOT
                   newline-delimited JSON — a frame is a binary unit, the
                   record body inside it is opaque to this layer.

Frame AND file-header integrity are both split into a fixed-size prefix
(validated first, checksummed on its own) and a variable-size remainder
—the framing-integrity-and-write-failure-amendment.md fix. Without this
split, a corrupted *length* field looks identical to a torn write: both
say "not enough bytes remain." Splitting the check means a corrupted
length is caught by its own header checksum, before it's ever used to
locate anything — never misclassified as a harmless torn tail.

Replay rule (frame-and-record-shape-design.md §4-5, sharpened by the
integrity amendment):
    - Not enough bytes for the next frame's FIXED PREFIX -> clean torn
      tail. Stop. Everything read so far is valid. Not an error.
    - Fixed prefix present but its own HEADER_CHECK fails -> CORRUPTION.
      The declared body length was never trustworthy in the first place;
      treating "not enough bytes" as safe here would let a corrupted
      length masquerade as an interrupted write. Quarantine.
    - Fixed prefix verified, but fewer than BODY_LENGTH + FRAME_CHECK
      bytes remain -> clean torn tail (the header committed; the body
      didn't finish). Stop. Everything read so far, including this
      frame's own now-useless header bytes, is discarded; everything
      before it is valid.
    - Full frame present but FRAME_CHECK doesn't match -> CORRUPTION.
    - turn_id values don't form the exact contiguous 0..N-1 sequence in
      file order -> CORRUPTION, even if every individual frame's own
      checksum was valid (catches e.g. two partial files spliced
      together).
    Corruption NEVER means "skip this frame and look for the next valid
    one." Replay halts immediately and the whole session is quarantined
    — see SessionJournal.quarantine().

The file header gets the identical two-stage treatment for consistency
(framing-integrity-and-write-failure-amendment.md §1), even though its
only realistic live-process failure mode is a crash during the
one-time, already-specially-sequenced creation write (§6 below) rather
than an ordinary interrupted append: ANY defect in the file header —
truncated, checksum-failed, or a shared_session_id that doesn't match
what the caller opened it for — is CORRUPTION, never a "safe, discard,
start empty" case. (A session that never had a journal at all is a
different, ordinary case, handled by SessionJournal.exists() before any
of this runs.)

Torn-tail repair, before the session may be marked writable again
(added after review — a torn tail is safe to IGNORE for a single
replay, but not safe to LEAVE on disk): replay() itself never mutates
the file — it is a pure read reporting `bytes_consumed`, the exact
offset the last verified frame ends at. If that is less than the file's
actual size, torn bytes are sitting at the old EOF. Marking the session
writable in that state and then successfully appending a new frame
would place valid data directly behind those torn bytes — permanently
converting a recoverable torn tail into interior corruption a future
replay could no longer distinguish from real corruption (no journal-
ordering rule stated above would then save it). SessionJournal.
truncate_to() removes exactly those torn bytes — open, ftruncate, fsync
— and SessionLedger._ensure_loaded_locked() calls it (and requires it
to succeed) BEFORE considering replay complete. If the truncation
itself fails, the session is quarantined, never marked writable on an
unproven repair — see truncate_to()'s own docstring.
"""

from __future__ import annotations

import hashlib
import os
import struct
import time
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, List, Optional, Tuple

# --------------------------------------------------------------------------
# Wire format constants. Exact byte widths, deliberately deferred by the
# design passes to "the implementation pass" — fixed here, once.
# --------------------------------------------------------------------------

FORMAT_VERSION = 1

_FILE_MAGIC = b"ENGJ"
_FRAME_MAGIC = b"ENGF"

# FILE HEADER fixed prefix: MAGIC(4s) VERSION(B) SESSION_ID_LENGTH(I) HEADER_PREFIX_CHECK(I)
_FILE_PREFIX_FMT = ">4sBII"
_FILE_PREFIX_SIZE = struct.calcsize(_FILE_PREFIX_FMT)  # 13
# FILE HEADER variable trailer checksum, after the session_id bytes: HEADER_FULL_CHECK(I)
_FILE_TRAILER_FMT = ">I"
_FILE_TRAILER_SIZE = struct.calcsize(_FILE_TRAILER_FMT)  # 4

# FRAME fixed prefix: MAGIC(4s) VERSION(B) RECORD_TYPE(B) BODY_LENGTH(I) HEADER_CHECK(I)
_FRAME_PREFIX_FMT = ">4sBBII"
_FRAME_PREFIX_SIZE = struct.calcsize(_FRAME_PREFIX_FMT)  # 14
# FRAME trailer, after BODY bytes: FRAME_CHECK(I)
_FRAME_TRAILER_FMT = ">I"
_FRAME_TRAILER_SIZE = struct.calcsize(_FRAME_TRAILER_FMT)  # 4

RECORD_TYPE_TURN_APPENDED = 1
RECORD_TYPE_RESPONSE_COMMITTED = 2
_KNOWN_RECORD_TYPES = (RECORD_TYPE_TURN_APPENDED, RECORD_TYPE_RESPONSE_COMMITTED)

# Discriminator tags for the opaque payload/snapshot triples (frame-and-
# record-shape-design.md §7). Never interpreted by this module beyond
# these two branches — a future encoding (e.g. a project-shaped ZW body)
# is a new tag handled by a future version of _decode_blob/_encode_blob,
# with no change to the framing above it.
ENCODING_UTF8_TEXT = "utf8-text"
ENCODING_JSON_UTF8 = "json-utf8"


def _crc32(data: bytes) -> int:
    return zlib.crc32(data) & 0xFFFFFFFF


def _write_all(fd: int, data: bytes) -> None:
    offset = 0
    while offset < len(data):
        offset += os.write(fd, data[offset:])


# --------------------------------------------------------------------------
# Exceptions
# --------------------------------------------------------------------------


class JournalCorruption(Exception):
    """Raised by replay() when the journal fails integrity or sequence
    validation. The caller (SessionLedger) is responsible for quarantining
    the file (see SessionJournal.quarantine()) and refusing further use of
    that shared_session_id — this exception by itself does not move or
    delete anything."""


class JournalWriteFailed(Exception):
    """Raised when a durable append (write/flush/fsync, or the one-time
    directory-fsync at first creation) did not complete successfully. The
    on-disk tail state is now UNCERTAIN — the caller must poison the
    session (see session_ledger.py), never retry blindly on the same
    file."""


# --------------------------------------------------------------------------
# Reconstructed record shapes (replay output, before Turn construction)
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class TurnAppendedRecord:
    turn_id: int
    origin_body: str
    payload: str
    snapshot: Optional[dict]
    timestamp: float


@dataclass(frozen=True)
class ResponseCommittedRecord:
    turn_id: int
    origin_body: str
    actor: str
    provider_id: str
    provider_session_id: str
    payload: str
    snapshot: Optional[dict]
    timestamp: float


@dataclass(frozen=True)
class ReplayResult:
    requests: List[TurnAppendedRecord]
    responses: List[ResponseCommittedRecord]
    # File order, tagged by type — what SessionLedger needs to reconstruct
    # its Turn list in the exact original sequence.
    ordered: List[Tuple[str, object]]  # ("request", TurnAppendedRecord) | ("response", ResponseCommittedRecord)
    # The exact byte offset replay stopped at — the end of the last fully
    # verified frame (or the end of the file header, if there were zero
    # frames). Equal to the file's actual size when there was no torn
    # tail. When it's LESS than the actual file size, a torn final frame
    # (or true garbage) sits at [bytes_consumed, actual_size) — see
    # SessionJournal.truncate_to() and this module's own docstring
    # "Torn-tail repair" section for why that gap must be closed before
    # the session is ever marked writable again.
    bytes_consumed: int


# --------------------------------------------------------------------------
# Low-level exact-length reads. Returns None (never raises) on an
# insufficient-bytes read — that is the ONLY signal this module treats as
# "maybe a torn tail"; every other defect is an explicit CORRUPTION check
# a layer above this function performs on the bytes it got back.
# --------------------------------------------------------------------------


def _read_exact(handle: BinaryIO, size: int) -> Optional[bytes]:
    data = handle.read(size)
    if len(data) < size:
        return None
    return data


# --------------------------------------------------------------------------
# Blob/text encoding helpers for record bodies. Length-prefixed, never
# interpreted beyond the tag (§7 opacity requirement) — payload_bytes and
# snapshot_bytes are stored and returned verbatim; only the two encoding
# tags this module currently understands (ENCODING_UTF8_TEXT,
# ENCODING_JSON_UTF8) are ever decoded back into a Python value, and that
# decoding lives here, not in the frame/header layer above it.
# --------------------------------------------------------------------------


def _pack_short_str(value: str) -> bytes:
    raw = value.encode("utf-8")
    if len(raw) > 255:
        raise ValueError(f"encoding tag too long ({len(raw)} bytes, max 255): {value!r}")
    return struct.pack(">B", len(raw)) + raw


def _unpack_short_str(buf: bytes, offset: int) -> Tuple[str, int]:
    (length,) = struct.unpack_from(">B", buf, offset)
    offset += 1
    raw = buf[offset : offset + length]
    return raw.decode("utf-8"), offset + length


def _pack_text(value: str) -> bytes:
    raw = value.encode("utf-8")
    if len(raw) > 0xFFFF:
        raise ValueError(f"text field too long ({len(raw)} bytes, max 65535)")
    return struct.pack(">H", len(raw)) + raw


def _unpack_text(buf: bytes, offset: int) -> Tuple[str, int]:
    (length,) = struct.unpack_from(">H", buf, offset)
    offset += 2
    raw = buf[offset : offset + length]
    return raw.decode("utf-8"), offset + length


def _pack_blob(raw: bytes) -> bytes:
    return struct.pack(">I", len(raw)) + raw


def _unpack_blob(buf: bytes, offset: int) -> Tuple[bytes, int]:
    (length,) = struct.unpack_from(">I", buf, offset)
    offset += 4
    raw = buf[offset : offset + length]
    return raw, offset + length


def _encode_payload(value: str) -> bytes:
    """Payload is Turn.payload's own type today: str. Encoded verbatim as
    UTF-8 text under the ENCODING_UTF8_TEXT tag — never JSON-wrapped."""
    return _pack_short_str(ENCODING_UTF8_TEXT) + _pack_blob(value.encode("utf-8"))


def _decode_payload(buf: bytes, offset: int) -> Tuple[str, int]:
    encoding, offset = _unpack_short_str(buf, offset)
    raw, offset = _unpack_blob(buf, offset)
    if encoding == ENCODING_UTF8_TEXT:
        return raw.decode("utf-8"), offset
    # An unrecognized future payload_encoding is a real, expected
    # extension point (§7/§15) — this implementation understands exactly
    # one payload encoding today and must not silently misinterpret bytes
    # it doesn't understand as text.
    raise JournalCorruption(f"unknown payload_encoding {encoding!r}")


def _encode_snapshot(value: Optional[dict]) -> bytes:
    if value is None:
        return struct.pack(">B", 0)
    import json

    raw = json.dumps(value, sort_keys=True).encode("utf-8")
    return struct.pack(">B", 1) + _pack_short_str(ENCODING_JSON_UTF8) + _pack_blob(raw)


def _decode_snapshot(buf: bytes, offset: int) -> Tuple[Optional[dict], int]:
    (present,) = struct.unpack_from(">B", buf, offset)
    offset += 1
    if not present:
        return None, offset
    encoding, offset = _unpack_short_str(buf, offset)
    raw, offset = _unpack_blob(buf, offset)
    if encoding != ENCODING_JSON_UTF8:
        raise JournalCorruption(f"unknown snapshot_encoding {encoding!r}")
    import json

    try:
        return json.loads(raw.decode("utf-8")), offset
    except (UnicodeDecodeError, ValueError) as exc:
        raise JournalCorruption(f"snapshot body is not valid JSON: {exc}") from exc


# --------------------------------------------------------------------------
# Record body encode/decode (frame-and-record-shape-design.md §8-10)
# --------------------------------------------------------------------------


def _encode_turn_appended_body(
    turn_id: int, origin_body: str, payload: str, snapshot: Optional[dict], timestamp: float
) -> bytes:
    return (
        struct.pack(">Q", turn_id)
        + _pack_text(origin_body)
        + _encode_payload(payload)
        + _encode_snapshot(snapshot)
        + struct.pack(">d", timestamp)
    )


def _decode_turn_appended_body(body: bytes) -> TurnAppendedRecord:
    offset = 0
    (turn_id,) = struct.unpack_from(">Q", body, offset)
    offset += 8
    origin_body, offset = _unpack_text(body, offset)
    payload, offset = _decode_payload(body, offset)
    snapshot, offset = _decode_snapshot(body, offset)
    (timestamp,) = struct.unpack_from(">d", body, offset)
    offset += 8
    if offset != len(body):
        raise JournalCorruption("TURN_APPENDED body has trailing bytes past its own fields")
    return TurnAppendedRecord(
        turn_id=turn_id, origin_body=origin_body, payload=payload, snapshot=snapshot, timestamp=timestamp
    )


def _encode_response_committed_body(
    turn_id: int,
    origin_body: str,
    actor: str,
    provider_id: str,
    provider_session_id: str,
    payload: str,
    snapshot: Optional[dict],
    timestamp: float,
) -> bytes:
    return (
        struct.pack(">Q", turn_id)
        + _pack_text(origin_body)
        + _pack_text(actor)
        + _pack_text(provider_id)
        + _pack_text(provider_session_id)
        + _encode_payload(payload)
        + _encode_snapshot(snapshot)
        + struct.pack(">d", timestamp)
    )


def _decode_response_committed_body(body: bytes) -> ResponseCommittedRecord:
    offset = 0
    (turn_id,) = struct.unpack_from(">Q", body, offset)
    offset += 8
    origin_body, offset = _unpack_text(body, offset)
    actor, offset = _unpack_text(body, offset)
    provider_id, offset = _unpack_text(body, offset)
    provider_session_id, offset = _unpack_text(body, offset)
    payload, offset = _decode_payload(body, offset)
    snapshot, offset = _decode_snapshot(body, offset)
    (timestamp,) = struct.unpack_from(">d", body, offset)
    offset += 8
    if offset != len(body):
        raise JournalCorruption("RESPONSE_COMMITTED body has trailing bytes past its own fields")
    return ResponseCommittedRecord(
        turn_id=turn_id,
        origin_body=origin_body,
        actor=actor,
        provider_id=provider_id,
        provider_session_id=provider_session_id,
        payload=payload,
        snapshot=snapshot,
        timestamp=timestamp,
    )


def _build_frame(record_type: int, body: bytes) -> bytes:
    prefix = struct.pack(_FRAME_PREFIX_FMT, _FRAME_MAGIC, FORMAT_VERSION, record_type, len(body), 0)
    # HEADER_CHECK covers MAGIC+VERSION+RECORD_TYPE+BODY_LENGTH only —
    # computed over the prefix with the check field itself zeroed, then
    # patched in, so the checksum never covers its own storage location.
    header_check = _crc32(prefix[: -struct.calcsize(">I")])
    prefix = prefix[: -struct.calcsize(">I")] + struct.pack(">I", header_check)
    frame_check = _crc32(prefix + body)
    return prefix + body + struct.pack(_FRAME_TRAILER_FMT, frame_check)


def _build_file_header(shared_session_id: str) -> bytes:
    session_id_bytes = shared_session_id.encode("utf-8")
    prefix = struct.pack(_FILE_PREFIX_FMT, _FILE_MAGIC, FORMAT_VERSION, len(session_id_bytes), 0)
    header_prefix_check = _crc32(prefix[: -struct.calcsize(">I")])
    prefix = prefix[: -struct.calcsize(">I")] + struct.pack(">I", header_prefix_check)
    full_check = _crc32(prefix + session_id_bytes)
    return prefix + session_id_bytes + struct.pack(_FILE_TRAILER_FMT, full_check)


# --------------------------------------------------------------------------
# SessionJournal - the per-shared_session_id journal file
# --------------------------------------------------------------------------


class SessionJournal:
    """One instance per (journal_root, shared_session_id) pair. Stateless
    beyond that — every call opens/closes its own file descriptor(s); no
    handle is held open across calls, matching this being invoked from
    inside SessionLedger's own per-session_id lock rather than needing a
    second layer of exclusion here."""

    def __init__(self, journal_root: Path, shared_session_id: str) -> None:
        self._journal_root = Path(journal_root)
        self._shared_session_id = shared_session_id
        # Filename mapping (frame-and-record-shape-design.md §11):
        # shared_session_id is arbitrary, caller-supplied, and untrusted
        # for filesystem purposes (path traversal, null bytes, OS-reserved
        # names, unbounded length) — never used as a path component
        # directly. A deterministic SHA-256 hex digest is fixed-length,
        # fixed-character-set, and collision-checked on open via the file
        # header's own retained original ID (see replay()).
        self._hex_digest = hashlib.sha256(shared_session_id.encode("utf-8")).hexdigest()

    @property
    def path(self) -> Path:
        return self._journal_root / f"{self._hex_digest}.journal"

    def exists(self) -> bool:
        return self.path.exists()

    # ---- replay -----------------------------------------------------

    def replay(self) -> ReplayResult:
        """Reads and verifies the file header, then reads frames strictly
        in file order, applying the exact rules in this module's own
        docstring. Raises JournalCorruption on anything but a clean torn
        tail; never returns a partial reconstruction past a detected
        problem, and never re-scans past one looking for the next valid
        frame."""
        with open(self.path, "rb") as handle:
            self._read_and_verify_file_header(handle)
            requests: List[TurnAppendedRecord] = []
            responses: List[ResponseCommittedRecord] = []
            ordered: List[Tuple[str, object]] = []
            expected_turn_id = 0
            while True:
                frame_offset = handle.tell()
                prefix = _read_exact(handle, _FRAME_PREFIX_SIZE)
                if prefix is None:
                    break  # clean torn tail (or clean EOF) — stop here, safely
                magic, version, record_type, body_length, header_check = struct.unpack(_FRAME_PREFIX_FMT, prefix)
                verify_prefix = prefix[: -struct.calcsize(">I")]
                if magic != _FRAME_MAGIC or _crc32(verify_prefix) != header_check:
                    raise JournalCorruption(
                        f"frame header invalid at offset {frame_offset} in {self.path}: "
                        "BODY_LENGTH is not trustworthy (bad magic or header checksum) — "
                        "this is corruption, not a torn tail"
                    )
                if version != FORMAT_VERSION:
                    raise JournalCorruption(
                        f"unsupported frame version {version} at offset {frame_offset} in {self.path}"
                    )
                if record_type not in _KNOWN_RECORD_TYPES:
                    raise JournalCorruption(
                        f"unknown record_type {record_type} at offset {frame_offset} in {self.path}"
                    )
                rest = _read_exact(handle, body_length + _FRAME_TRAILER_SIZE)
                if rest is None:
                    break  # header verified, but body/trailer never finished — torn tail
                body, trailer = rest[:-_FRAME_TRAILER_SIZE], rest[-_FRAME_TRAILER_SIZE:]
                (frame_check,) = struct.unpack(_FRAME_TRAILER_FMT, trailer)
                if _crc32(prefix + body) != frame_check:
                    raise JournalCorruption(
                        f"frame checksum mismatch at offset {frame_offset} in {self.path} — "
                        "corruption inside otherwise-committed history"
                    )
                try:
                    if record_type == RECORD_TYPE_TURN_APPENDED:
                        record = _decode_turn_appended_body(body)
                    else:
                        record = _decode_response_committed_body(body)
                except (struct.error, UnicodeDecodeError) as exc:
                    raise JournalCorruption(
                        f"frame body undecodable at offset {frame_offset} in {self.path}: {exc}"
                    ) from exc
                if record.turn_id != expected_turn_id:
                    raise JournalCorruption(
                        f"turn_id sequence gap/out-of-order at offset {frame_offset} in {self.path}: "
                        f"expected {expected_turn_id}, got {record.turn_id}"
                    )
                expected_turn_id += 1
                if record_type == RECORD_TYPE_TURN_APPENDED:
                    requests.append(record)
                    ordered.append(("request", record))
                else:
                    responses.append(record)
                    ordered.append(("response", record))
            return ReplayResult(requests=requests, responses=responses, ordered=ordered, bytes_consumed=frame_offset)

    def _read_and_verify_file_header(self, handle: BinaryIO) -> None:
        prefix = _read_exact(handle, _FILE_PREFIX_SIZE)
        if prefix is None:
            raise JournalCorruption(
                f"file header truncated in {self.path} — no legitimate torn-header case during "
                "ordinary operation; treated as corruption, not an empty session"
            )
        magic, version, session_id_length, header_prefix_check = struct.unpack(_FILE_PREFIX_FMT, prefix)
        verify_prefix = prefix[: -struct.calcsize(">I")]
        if magic != _FILE_MAGIC or _crc32(verify_prefix) != header_prefix_check:
            raise JournalCorruption(f"file header prefix invalid in {self.path}")
        if version != FORMAT_VERSION:
            raise JournalCorruption(f"unsupported journal format version {version} in {self.path}")
        variable = _read_exact(handle, session_id_length + _FILE_TRAILER_SIZE)
        if variable is None:
            raise JournalCorruption(f"file header variable part truncated in {self.path}")
        session_id_bytes, trailer = variable[:-_FILE_TRAILER_SIZE], variable[-_FILE_TRAILER_SIZE:]
        (full_check,) = struct.unpack(_FILE_TRAILER_FMT, trailer)
        if _crc32(prefix + session_id_bytes) != full_check:
            raise JournalCorruption(f"file header checksum mismatch in {self.path}")
        try:
            declared_session_id = session_id_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise JournalCorruption(f"file header shared_session_id is not valid UTF-8 in {self.path}") from exc
        if declared_session_id != self._shared_session_id:
            raise JournalCorruption(
                f"session identity mismatch in {self.path}: header declares {declared_session_id!r}, "
                f"opened for {self._shared_session_id!r}"
            )

    # ---- torn-tail repair -----------------------------------------------

    def truncate_to(self, offset: int) -> None:
        """Repairs a torn final frame left over from a prior crash.

        A torn tail is safe to IGNORE during one single replay — but if
        replay leaves those partial bytes sitting at the old EOF and the
        session is then marked writable, the next successful append
        lands a new, fully valid frame directly behind them. A later
        restart's replay would then see:

            FRAME 0 (valid) FRAME 1 (valid) <torn bytes> FRAME 2 (valid)

        — corruption in the MIDDLE of the stream, indistinguishable from
        real interior corruption, even though every byte that ever
        mattered was actually fine. What was recoverable tail damage
        becomes permanent. This method is the fix: called with
        ReplayResult.bytes_consumed, it physically removes exactly the
        torn bytes — nothing before that offset, nothing decided by
        guessing — so the file's new EOF is the exact end of the last
        verified frame. The caller (SessionLedger._ensure_loaded_locked)
        must call this, and it must succeed, BEFORE the session is ever
        marked loaded/writable — never after, never optionally.

        Raises OSError (open/ftruncate/fsync) on any failure. The
        caller's response is fixed by the design, not a choice this
        method makes: quarantine the session and refuse it, never retry
        blindly and never mark it writable on an unproven truncation —
        the exact same "don't continue on unproven durability" rule the
        live-write poison path already applies, applied here to the
        recovery path instead."""
        flags = os.O_WRONLY
        if hasattr(os, "O_CLOEXEC"):
            flags |= os.O_CLOEXEC
        fd = os.open(str(self.path), flags)
        try:
            os.ftruncate(fd, offset)
            os.fsync(fd)
        finally:
            os.close(fd)

    # ---- append -------------------------------------------------------

    def append_turn_appended(self, turn_id: int, origin_body: str, payload: str, snapshot: Optional[dict], timestamp: float) -> None:
        body = _encode_turn_appended_body(turn_id, origin_body, payload, snapshot, timestamp)
        self._append_frame_bytes(_build_frame(RECORD_TYPE_TURN_APPENDED, body))

    def append_response_committed(
        self,
        turn_id: int,
        origin_body: str,
        actor: str,
        provider_id: str,
        provider_session_id: str,
        payload: str,
        snapshot: Optional[dict],
        timestamp: float,
    ) -> None:
        body = _encode_response_committed_body(
            turn_id, origin_body, actor, provider_id, provider_session_id, payload, snapshot, timestamp
        )
        self._append_frame_bytes(_build_frame(RECORD_TYPE_RESPONSE_COMMITTED, body))

    def _append_frame_bytes(self, frame: bytes) -> None:
        """Commit means write -> flush -> fsync (crash-consistency-
        design.md §4/§6). Any failure at any stage — including the
        one-time directory-fsync at first creation — is reported as
        JournalWriteFailed and the caller (SessionLedger) must poison the
        session; this method never retries and never leaves a partially
        written frame silently unreported."""
        try:
            self._journal_root.mkdir(parents=True, exist_ok=True)
            if not self.path.exists():
                self._create_with_first_frame(frame)
            else:
                self._append_to_existing_file(frame)
        except JournalWriteFailed:
            raise
        except OSError as exc:
            raise JournalWriteFailed(f"durable append failed for {self.path}: {exc}") from exc

    def _create_with_first_frame(self, frame: bytes) -> None:
        """First-creation sequence (frame-and-record-shape-design.md §6):
        content durability (write+flush+fsync of header+first frame
        together) is not sufficient on its own — the new directory entry
        itself needs its own fsync, once, or a crash between the two can
        leave the file's very existence unrecoverable even though its
        bytes were flushed. This cost is paid exactly once per
        shared_session_id, at its first-ever write."""
        header = _build_file_header(self._shared_session_id)
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_CLOEXEC"):
            flags |= os.O_CLOEXEC
        fd = os.open(str(self.path), flags, 0o600)
        try:
            _write_all(fd, header + frame)
            os.fsync(fd)
        finally:
            os.close(fd)

        dir_flags = os.O_RDONLY
        if hasattr(os, "O_DIRECTORY"):
            dir_flags |= os.O_DIRECTORY
        dir_fd = os.open(str(self._journal_root), dir_flags)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)

    def _append_to_existing_file(self, frame: bytes) -> None:
        """Ordinary append to an already-existing, already-durable file.
        No directory fsync needed — the directory entry linking this
        filename to this inode was already made durable at creation
        time (see _create_with_first_frame) and does not change on an
        ordinary append."""
        flags = os.O_WRONLY | os.O_APPEND
        if hasattr(os, "O_CLOEXEC"):
            flags |= os.O_CLOEXEC
        fd = os.open(str(self.path), flags)
        try:
            _write_all(fd, frame)
            os.fsync(fd)
        finally:
            os.close(fd)

    # ---- quarantine -----------------------------------------------------

    def quarantine(self, reason: str) -> Path:
        """Moves this journal out of the active path into
        <journal_root>/corrupt/, logging the reason beside it. Does not
        raise if the source file has already been moved (idempotent —
        a second detection of the same corruption, e.g. by a concurrent
        caller, must not itself crash)."""
        corrupt_dir = self._journal_root / "corrupt"
        corrupt_dir.mkdir(parents=True, exist_ok=True)
        dest = corrupt_dir / f"{self._hex_digest}.journal.{int(time.time() * 1000)}.corrupt"
        try:
            os.replace(self.path, dest)
        except FileNotFoundError:
            return dest
        dest.with_name(dest.name + ".reason.txt").write_text(reason, encoding="utf-8")
        return dest
