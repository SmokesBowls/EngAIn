from __future__ import annotations

import sys
import threading
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tier1.engainos.core.session_claim_registry import ClaimRejected, SessionClaim, SessionClaimRegistry

SESSION_ID = "shared-hermes-session"


def test_first_claimant_succeeds():
    reg = SessionClaimRegistry()
    result = reg.claim(SESSION_ID, "hermes", "dragon2d-worker", lease_seconds=30.0)
    assert isinstance(result, SessionClaim)
    assert result.instance_id == "dragon2d-worker"


def test_second_claimant_is_rejected_while_first_holds_it():
    reg = SessionClaimRegistry()
    reg.claim(SESSION_ID, "hermes", "dragon2d-worker", lease_seconds=30.0)
    result = reg.claim(SESSION_ID, "hermes", "dragon3d-worker", lease_seconds=30.0)
    assert isinstance(result, ClaimRejected)
    assert result.reason == "SESSION_OCCUPIED"
    assert result.current_instance_id == "dragon2d-worker"


def test_release_lets_a_new_claimant_in():
    reg = SessionClaimRegistry()
    first = reg.claim(SESSION_ID, "hermes", "dragon2d-worker", lease_seconds=30.0)
    assert reg.release(SESSION_ID, first.claim_token) is True

    second = reg.claim(SESSION_ID, "hermes", "dragon3d-worker", lease_seconds=30.0)
    assert isinstance(second, SessionClaim)
    assert second.instance_id == "dragon3d-worker"


def test_release_with_wrong_token_is_rejected():
    reg = SessionClaimRegistry()
    reg.claim(SESSION_ID, "hermes", "dragon2d-worker", lease_seconds=30.0)
    assert reg.release(SESSION_ID, "not-the-real-token") is False
    # still occupied — a foreign token cannot clear it
    result = reg.claim(SESSION_ID, "hermes", "dragon3d-worker", lease_seconds=30.0)
    assert isinstance(result, ClaimRejected)


def test_expired_claim_lets_a_new_claimant_in_without_explicit_release():
    """The crash-recovery path: a claimant that dies mid-dispatch never
    calls release(), so the short lease has to be what saves the next
    claimant, not an assumption that release() always runs."""
    reg = SessionClaimRegistry()
    reg.claim(SESSION_ID, "hermes", "dragon2d-worker", lease_seconds=0.01)
    time.sleep(0.02)
    result = reg.claim(SESSION_ID, "hermes", "dragon3d-worker", lease_seconds=30.0)
    assert isinstance(result, SessionClaim)
    assert result.instance_id == "dragon3d-worker"


def test_current_reads_none_for_expired_claim():
    reg = SessionClaimRegistry()
    reg.claim(SESSION_ID, "hermes", "dragon2d-worker", lease_seconds=0.01)
    time.sleep(0.02)
    assert reg.current(SESSION_ID) is None


def test_same_instance_may_reclaim_its_own_session():
    """Not a race case: a worker renewing/re-entering its own claim (e.g.
    retry after a transient error) should not be rejected by itself."""
    reg = SessionClaimRegistry()
    first = reg.claim(SESSION_ID, "hermes", "dragon2d-worker", lease_seconds=30.0)
    second = reg.claim(SESSION_ID, "hermes", "dragon2d-worker", lease_seconds=30.0)
    assert isinstance(second, SessionClaim)
    assert second.claim_token != first.claim_token  # a fresh token each time


def test_concurrent_claims_only_one_winner():
    """The actual atomicity property, exercised with real threads rather
    than trusted by inspection — many callers racing for one session_id
    must produce exactly one winner, not zero, not two."""
    reg = SessionClaimRegistry()
    winners = []
    lock = threading.Lock()

    def attempt(instance_id: str) -> None:
        result = reg.claim(SESSION_ID, "hermes", instance_id, lease_seconds=30.0)
        if isinstance(result, SessionClaim):
            with lock:
                winners.append(instance_id)

    threads = [threading.Thread(target=attempt, args=(f"worker-{i}",)) for i in range(50)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(winners) == 1
