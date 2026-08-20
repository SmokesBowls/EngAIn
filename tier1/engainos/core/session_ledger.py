"""
session_ledger.py - The shared conversation record (SHARED_SESSION_CONTINUITY_CONTRACT_v1)

One page every door writes on and reads from, keyed only by session_id.
origin_body is provenance metadata on a turn, never an identity, and never a
read filter a body may apply to itself (contract Section 3's governing
invariant: a turn belongs to the session, not to the door that carried it).

Scope note (Stage 4 tiny-implementation proof):
    In-memory, append-only list per session_id, for the lifetime of one
    process. Storage mechanism, retention, notification, and concurrent-write
    ordering are explicitly left open by the contract (its own Section 8) and
    are NOT decided here — turn_id is simply this process's list length,
    which is sufficient to prove the ordering invariant and nothing more.

Append-only is enforced structurally, not just by convention: Turn is a
frozen dataclass, and both append() and every read method hand back a
deepcopy rather than the internally stored object or its stored snapshot
dict. Without this, `ledger.read_last(sid).payload = "rewritten"` (or
mutating a snapshot dict passed into append() after the call returns) would
silently rewrite the Ledger's history with no new turn ever recorded —
exactly what "append-only" is supposed to forbid.

Concurrency (item 2, 2026-08-18 — see
08-18-2026-item2-session-ledger-semantic-derivation.md for the full
derivation): append()'s own turn_id assignment (`len(turns)`) and the
list insertion used to race — two threads appending to the SAME
session_id could read the same length before either inserted, minting a
duplicate turn_id. The contract (§8) only promises turn_id is unique and
monotonic per session_id; it does not require turn_id to equal list
position, but there's also no reason to give that useful, currently-true
equivalence up prematurely (a future persistence/reconstruction layer
would otherwise have to restore it separately). Fixed by making
"determine next turn_id + insert the Turn" one atomic operation per
session_id, via a lock scoped to that session_id alone — a session_id A
append never waits on a session_id B append. Reads (read_since/
read_last) are deliberately NOT locked: no caller was found that needs a
transactional snapshot across a concurrent append, and Python's own
list/GIL semantics already prevent a torn read of already-inserted
elements — adding read locks would strengthen the contract beyond what
any caller requires. This also does not extend to locking the
request/response transaction handle_turn() performs around a real
provider dispatch — see the design note for why that would silently
reintroduce a serialization guarantee the system doesn't have today and
would cost item 1's already-proven provider-dispatch concurrency for no
discovered benefit.

Persistence (item 3, 2026-08-19 — see
08-19-2026-item3-{restart-continuity-derivation,crash-consistency-design,
encoding-selection-design,frame-and-record-shape-design,
framing-integrity-and-write-failure-amendment}.md for the full
derivation): OPT IN, via the `journal_root` constructor argument. When
None (the default — every existing construction site in this repo),
SessionLedger behaves exactly as it did before this item: pure
in-memory, no journal, no replay, no poison/quarantine machinery
engaged at all. When `journal_root` is given, item 2's existing
per-session_id lock is reused (not a second, independent persistence
lock — design note §12) for three additional jobs, all performed inside
that same critical section:

  1. Lazy, per-session replay-on-first-touch (design note §14, sharpened
     by the integrity amendment §3): the first append() call for a given
     session_id in this process generation replays that session's
     journal, if one exists, before minting any new turn_id — "replay
     this session if it hasn't been replayed yet" is the first action
     taken inside the lock, exactly the same lock that already
     serializes appends, so two concurrent first-touches for the same
     session_id never race. If replay stopped short of a torn final
     frame (a prior crash mid-write), those torn bytes are physically
     truncated off — fsync'd — BEFORE the session is ever marked
     loaded/writable (review correction, post-implementation): leaving
     torn bytes at the old EOF and then appending a new valid frame
     behind them would permanently convert a safely-discardable torn
     tail into interior corruption a future replay could no longer tell
     apart from real corruption. If the truncation itself fails, the
     session is quarantined — never marked writable on an unproven
     repair. See session_journal.py's own "Torn-tail repair" section.
  2. Durable write BEFORE the in-memory mutation (design note §6/§12):
     the frame is fully constructed and fsync'd to disk before
     `turns.append(turn)` ever runs — never the other way around.
  3. Poison-on-uncertainty (design note §13, amendment §2): if the
     durable write itself fails, OR if it succeeds but the immediately-
     following in-memory mutation (list append / cursor advance)
     unexpectedly raises, this one session_id is marked poisoned and
     every subsequent append() (and, at the /dispatch layer above this,
     every subsequent dispatch attempt) for it raises SessionPoisoned
     until a full process restart. A session whose journal fails
     integrity/sequence validation at replay time is quarantined
     instead (SessionQuarantined) — its journal file is moved out of the
     active path (see session_journal.SessionJournal.quarantine()) and
     it is refused the same way. Neither failure mode for one
     session_id has any effect on any other session_id — isolation is
     structural, via the same per-session_id lock/state map that already
     isolates unrelated sessions' concurrency (see
     test_session_ledger_persistence.py).

Response turns additionally carry `provider_id`/`provider_session_id`
(required whenever `journal_root` is set — see RESPONSE_COMMITTED's
field shape in the frame/record design note) and, when a
`cursor` (ContinuityCursorTracker) was supplied at construction,
`cursor.advance(...)` is called as part of the SAME post-durability
in-memory step as `turns.append(turn)` — collapsing what
shared_session_bridge.py used to do as two separate calls (one inside
this lock, one after it) into one, so both bare mutations that must
follow a durable response write happen back-to-back under the poison
guard described above, not with a gap between them.
"""

from __future__ import annotations

import threading
import time
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set

from tier1.engainos.core.session_journal import JournalCorruption, JournalWriteFailed, SessionJournal


@dataclass(frozen=True)
class Turn:
    turn_id: int
    session_id: str
    origin_body: str
    direction: str          # "request" | "response"
    actor: str
    payload: str
    snapshot: Optional[dict] = None
    timestamp: float = field(default_factory=time.time)


class SessionUnavailable(Exception):
    """Common base for the two reasons a session_id may refuse any further
    append/dispatch in this process generation. Never raised directly —
    always one of the two subclasses below."""

    def __init__(self, session_id: str, message: str) -> None:
        super().__init__(message)
        self.session_id = session_id


class SessionQuarantined(SessionUnavailable):
    """The session's durable journal failed integrity or turn_id-sequence
    validation at replay time. Its journal file has been moved to
    <journal_root>/corrupt/ (see SessionJournal.quarantine()) — a human
    must resolve it; recovery is not automatic."""


class SessionPoisoned(SessionUnavailable):
    """A durable write for this session either failed outright, or
    succeeded but the immediately-following in-memory mutation
    unexpectedly raised — the on-disk tail and/or in-memory state is no
    longer provably trustworthy. Recovery is a full process restart
    (which clears this in-memory flag and replays fresh next touch)."""


class SessionLedger:
    def __init__(
        self,
        journal_root: Optional[Path] = None,
        cursor: Optional["object"] = None,
    ) -> None:
        self._turns: Dict[str, List[Turn]] = {}
        # One lock per session_id, created lazily. _locks_guard protects
        # only the get-or-create of that per-session lock itself (a
        # handful of dict operations) — never the append work — so two
        # different session_ids' appends never wait on each other.
        self._locks: Dict[str, threading.Lock] = {}
        self._locks_guard = threading.Lock()

        # Persistence (item 3) — see this module's own docstring. Both
        # None by default, matching every pre-item-3 construction site
        # exactly: no journal_root means none of the code below this
        # point ever runs.
        self._journal_root = Path(journal_root) if journal_root is not None else None
        self._cursor = cursor  # ContinuityCursorTracker, typed loosely to avoid a hard import cycle
        self._loaded: Set[str] = set()
        # Only ever holds BLOCKED sessions (quarantined or poisoned) —
        # absence from this dict means "healthy" (or "not yet replayed",
        # distinguished by _loaded).
        self._blocked: Dict[str, SessionUnavailable] = {}

    def _lock_for(self, session_id: str) -> threading.Lock:
        with self._locks_guard:
            lock = self._locks.get(session_id)
            if lock is None:
                lock = threading.Lock()
                self._locks[session_id] = lock
            return lock

    def raise_if_blocked(self, session_id: str) -> None:
        """Cheap, lock-free early check a caller above this class (e.g.
        /dispatch) may use to fail fast before doing any other work for a
        known-blocked session_id. append() enforces the identical rule
        unconditionally regardless of whether a caller checks this
        first — this exists only to avoid wasted work (a Presence write,
        a dispatch claim) for a session already known to be refused."""
        blocked = self._blocked.get(session_id)
        if blocked is not None:
            raise blocked

    def _journal_for(self, session_id: str) -> SessionJournal:
        assert self._journal_root is not None
        return SessionJournal(self._journal_root, session_id)

    def _ensure_loaded_locked(self, session_id: str) -> None:
        """Must only be called while holding _lock_for(session_id). Lazy,
        per-session replay-on-first-touch (design note §14) — the first
        thing any locked operation does for a session_id this process
        generation hasn't touched yet. Never called when journal_root is
        None."""
        blocked = self._blocked.get(session_id)
        if blocked is not None:
            raise blocked
        if session_id in self._loaded:
            return
        journal = self._journal_for(session_id)
        if not journal.exists():
            self._loaded.add(session_id)
            return
        try:
            result = journal.replay()
        except JournalCorruption as exc:
            journal.quarantine(reason=str(exc))
            blocked = SessionQuarantined(session_id, f"session {session_id!r} quarantined: {exc}")
            self._blocked[session_id] = blocked
            raise blocked from exc

        # Torn-tail repair — MUST happen, and MUST succeed, before this
        # session is ever marked loaded/writable (session_journal.py's
        # own docstring, "Torn-tail repair" section). replay() itself
        # never mutates the file; if it stopped short of the file's
        # actual size, torn bytes from an interrupted prior write are
        # still sitting at the old EOF. Leaving them there and then
        # appending a new, valid frame would place that new frame
        # directly behind the torn bytes — permanently converting a
        # safely-discardable torn tail into interior corruption a future
        # replay could no longer tell apart from real corruption.
        actual_size = journal.path.stat().st_size
        if result.bytes_consumed < actual_size:
            try:
                journal.truncate_to(result.bytes_consumed)
            except OSError as exc:
                # Truncation itself is unproven — per the design's own
                # "don't continue on unproven durability" rule (already
                # applied to live writes via poison), this session must
                # not be marked writable on a repair that might not have
                # actually landed. Quarantine, don't retry, don't guess.
                journal.quarantine(reason=f"torn-tail repair truncate failed at offset {result.bytes_consumed}: {exc}")
                blocked = SessionQuarantined(
                    session_id,
                    f"session {session_id!r} quarantined: torn-tail repair failed "
                    f"(truncate to {result.bytes_consumed} of {actual_size} bytes): {exc}",
                )
                self._blocked[session_id] = blocked
                raise blocked from exc

        turns: List[Turn] = []
        for kind, record in result.ordered:
            if kind == "request":
                turns.append(
                    Turn(
                        turn_id=record.turn_id,
                        session_id=session_id,
                        origin_body=record.origin_body,
                        direction="request",
                        actor="player",  # contract-level constant, reconstructed not stored
                        payload=record.payload,
                        snapshot=record.snapshot,
                        timestamp=record.timestamp,
                    )
                )
            else:
                turns.append(
                    Turn(
                        turn_id=record.turn_id,
                        session_id=session_id,
                        origin_body=record.origin_body,
                        direction="response",
                        actor=record.actor,
                        payload=record.payload,
                        snapshot=record.snapshot,
                        timestamp=record.timestamp,
                    )
                )
                if self._cursor is not None:
                    self._cursor.advance(record.provider_id, record.provider_session_id, record.turn_id)
        self._turns[session_id] = turns
        self._loaded.add(session_id)

    def append(
        self,
        session_id: str,
        origin_body: str,
        direction: str,
        actor: str,
        payload: str,
        snapshot: Optional[dict] = None,
        provider_id: Optional[str] = None,
        provider_session_id: Optional[str] = None,
    ) -> Turn:
        if direction not in ("request", "response"):
            raise ValueError(f"MALFORMED_TURN: direction must be request/response, got {direction!r}")
        if direction == "response" and self._journal_root is not None:
            if provider_id is None or provider_session_id is None:
                raise ValueError(
                    "MALFORMED_TURN: provider_id/provider_session_id are required on a response "
                    "turn once journal_root is configured (see RESPONSE_COMMITTED's field shape)"
                )
        # The atomic boundary: determine this session_id's next turn_id
        # and insert the corresponding Turn as one operation. len(turns)
        # is not itself wrong — every SessionLedger starts empty (or, with
        # persistence, is fully reconstructed by _ensure_loaded_locked
        # before this line ever runs) — the bug item 2 fixed was the
        # unsynchronized len(turns) -> append() sequence, not this
        # formula.
        with self._lock_for(session_id):
            if self._journal_root is not None:
                self._ensure_loaded_locked(session_id)  # raises SessionQuarantined/SessionPoisoned if blocked
            turns = self._turns.setdefault(session_id, [])
            turn = Turn(
                turn_id=len(turns),
                session_id=session_id,
                origin_body=origin_body,
                direction=direction,
                actor=actor,
                payload=payload,
                snapshot=deepcopy(snapshot),
            )

            if self._journal_root is not None:
                journal = self._journal_for(session_id)
                try:
                    if direction == "request":
                        journal.append_turn_appended(
                            turn_id=turn.turn_id,
                            origin_body=origin_body,
                            payload=payload,
                            snapshot=turn.snapshot,
                            timestamp=turn.timestamp,
                        )
                    else:
                        journal.append_response_committed(
                            turn_id=turn.turn_id,
                            origin_body=origin_body,
                            actor=actor,
                            provider_id=provider_id,
                            provider_session_id=provider_session_id,
                            payload=payload,
                            snapshot=turn.snapshot,
                            timestamp=turn.timestamp,
                        )
                except JournalWriteFailed as exc:
                    # Durable write itself failed/uncertain — poison
                    # immediately. The in-memory turns list is NOT
                    # mutated below (we raise before reaching it), so
                    # memory stays consistent with "this turn never
                    # happened," matching the durable state.
                    blocked = SessionPoisoned(session_id, f"session {session_id!r} poisoned: {exc}")
                    self._blocked[session_id] = blocked
                    raise blocked from exc

            # Durable write (if any) has succeeded. What remains is the
            # bare in-memory mutation(s) — per design note §13, "about as
            # close to cannot meaningfully fail as ordinary Python gets,
            # without claiming it's literally impossible." If one of
            # these DOES raise, the disk and memory have now diverged:
            # poison this session (when persisted) rather than let it
            # keep serving against a Ledger/Cursor that reality no longer
            # agrees with.
            try:
                turns.append(turn)
                if direction == "response" and self._cursor is not None:
                    self._cursor.advance(provider_id, provider_session_id, turn.turn_id)
            except Exception as exc:
                if self._journal_root is not None:
                    blocked = SessionPoisoned(
                        session_id, f"session {session_id!r} poisoned: post-durability in-memory mutation failed: {exc}"
                    )
                    self._blocked[session_id] = blocked
                    raise blocked from exc
                raise
        return deepcopy(turn)

    def _try_ensure_loaded(self, session_id: str) -> None:
        """Best-effort replay-on-first-touch for the READ path only. The
        blocking rule this module enforces (SessionQuarantined /
        SessionPoisoned) is scoped to append()/dispatch, per instruction
        — never to reads. A session that is already blocked, or becomes
        blocked while this call is replaying it, simply yields whatever
        is already in memory (empty, if replay never got the chance to
        run) rather than raising — a read can never itself corrupt
        anything, so there is no correctness reason to refuse it, and
        refusing it would silently invent a stronger rule than the one
        actually specified."""
        try:
            with self._lock_for(session_id):
                self._ensure_loaded_locked(session_id)
        except SessionUnavailable:
            pass

    def read_last(self, session_id: str, direction: Optional[str] = None) -> Optional[Turn]:
        if self._journal_root is not None:
            self._try_ensure_loaded(session_id)
        for turn in reversed(self._turns.get(session_id, [])):
            if direction is None or turn.direction == direction:
                return deepcopy(turn)
        return None

    def read_since(self, session_id: str, since_turn_id: int) -> List[Turn]:
        if self._journal_root is not None:
            self._try_ensure_loaded(session_id)
        return [deepcopy(t) for t in self._turns.get(session_id, []) if t.turn_id > since_turn_id]
