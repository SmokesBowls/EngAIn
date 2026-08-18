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


def test_composite_key_claim_and_release():
    """Item 1: the presence authority's own /dispatch handler claims a
    (provider_id, provider_session_id) tuple directly, in-process — never
    through the public /claim HTTP endpoint. The registry itself doesn't
    care: a tuple key works exactly like a string key."""
    reg = SessionClaimRegistry()
    key = ("hermes", "native-session-A")
    result = reg.claim(key, "hermes", "req-a-uuid", lease_seconds=30.0)
    assert isinstance(result, SessionClaim)
    assert result.session_id == key
    assert reg.release(key, result.claim_token) is True


def test_composite_key_second_claimant_rejected_while_first_holds_it():
    reg = SessionClaimRegistry()
    key = ("hermes", "native-session-A")
    reg.claim(key, "hermes", "req-a-uuid", lease_seconds=30.0)
    result = reg.claim(key, "hermes", "req-b-uuid", lease_seconds=30.0)
    assert isinstance(result, ClaimRejected)
    assert result.reason == "SESSION_OCCUPIED"
    assert result.current_instance_id == "req-a-uuid"


def test_composite_key_does_not_collide_with_a_string_key():
    """(provider_id, provider_session_id) and a bare session_id string
    live in the same dict but are never the same key, even if their text
    happens to overlap — a hashability/equality sanity check, not just an
    assumption."""
    reg = SessionClaimRegistry()
    tuple_key = ("hermes", SESSION_ID)
    string_key = SESSION_ID
    first = reg.claim(tuple_key, "hermes", "req-a-uuid", lease_seconds=30.0)
    second = reg.claim(string_key, "hermes", "req-b-uuid", lease_seconds=30.0)
    assert isinstance(first, SessionClaim)
    assert isinstance(second, SessionClaim)  # no false contention between the two distinct keys
    assert reg.current(tuple_key).claim_token == first.claim_token
    assert reg.current(string_key).claim_token == second.claim_token


def test_composite_key_different_provider_session_pairs_do_not_contend():
    """The three-way comparison item 1's design note proves the key from:
    same provider/different session, and different provider/same textual
    session_id, must both proceed concurrently — checked here at the
    registry level directly."""
    reg = SessionClaimRegistry()
    same_provider_diff_session = reg.claim(("hermes", "123"), "hermes", "req-1", lease_seconds=30.0)
    same_provider_diff_session_2 = reg.claim(("hermes", "456"), "hermes", "req-2", lease_seconds=30.0)
    diff_provider_same_text = reg.claim(("claude_code", "123"), "claude_code", "req-3", lease_seconds=30.0)
    assert isinstance(same_provider_diff_session, SessionClaim)
    assert isinstance(same_provider_diff_session_2, SessionClaim)
    assert isinstance(diff_provider_same_text, SessionClaim)


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
