"""
Stage 4 tiny-implementation proof for:
    PROVIDER_PRESENCE_REGISTRY_CONTRACT_v1.md
    SHARED_SESSION_CONTINUITY_CONTRACT_v1.md
    ENGAIN_AVATAR_DRAGON_BRIDGE_CONTRACT_v1_AMENDMENT_1_SHARED_SESSION.md

The proof asked for: say something through 2D, switch to 3D, ask "what did I
just say?", and have the answer come from the same Ledger-backed session —
not from luck, cached body memory, or a private director handshake.

Deliberately narrow, per instruction: this does not test persistence across
process restarts, retention, notification, or concurrency. Those remain open
per both contracts' own Section 8 / Section 8.
"""

from __future__ import annotations

from pathlib import Path
import sys

# tests/ -> engainos -> tier1 -> EngAIn (repo root). parents[2] would land on
# tier1, not the repo root — caught in review; harmless today only because
# pytest is already invoked from the repo root, which is on sys.path before
# this file's own bootstrap ever runs.
REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import dataclasses

import pytest

from tier1.engainos.bridgeroom.shared_session_bridge import (
    ProviderNotRegistered,
    ResponseActorMismatch,
    SharedSessionBridge,
)
from tier1.engainos.core.presence_registry import PresenceRegistry
from tier1.engainos.core.provider_session_binding import ProviderSessionBinding
from tier1.engainos.core.session_ledger import SessionLedger


SESSION_ID = "20260816_proof_session"
TEST_ENDPOINT = ProviderSessionBinding.encode_endpoint(
    provider_id="hermes", model_id="test-model", provider_session_id="provider-native-session-x"
)


def _bridge() -> SharedSessionBridge:
    return SharedSessionBridge(presence=PresenceRegistry(), ledger=SessionLedger())


def test_body_switch_is_not_session_switch():
    """The proof scenario, verbatim."""
    bridge = _bridge()
    bridge._presence.register(
        agent_id="hermes",
        instance_id="H-8F31",
        session_id=SESSION_ID,
        capabilities=["chat"],
        endpoint=TEST_ENDPOINT,
    )

    said_through_2d = bridge.handle_turn(
        session_id=SESSION_ID,
        origin_body="dragon_2d",
        player_input="remember the word banana",
    )
    assert said_through_2d["origin_body"] == "dragon_2d"
    assert said_through_2d["actor"] == "hermes"

    asked_through_3d = bridge.handle_turn(
        session_id=SESSION_ID,
        origin_body="dragon_3d",
        player_input="what did I just say?",
    )

    # Different door...
    assert asked_through_3d["origin_body"] == "dragon_3d"
    # ...same session, same active actor, and the answer demonstrably came
    # from the Ledger's record of the *other* door's turn, not from luck.
    assert asked_through_3d["actor"] == "hermes"
    assert "banana" in asked_through_3d["response"]
    assert "dragon_2d" not in asked_through_3d["response"]  # provenance stayed
    # metadata (§3), never leaked into the answer as if it were content


def test_ledger_has_one_true_order_regardless_of_door():
    """Any door reading the Ledger back gets the same answer (contract §3's
    governing invariant), proven here by reading directly instead of only
    through handle_turn."""
    bridge = _bridge()
    bridge._presence.register("hermes", "H-1", SESSION_ID, ["chat"], endpoint=TEST_ENDPOINT)
    bridge.handle_turn(SESSION_ID, "dragon_2d", "hello from 2D")

    last_response = bridge._ledger.read_last(SESSION_ID, direction="response")
    assert last_response is not None
    assert last_response.origin_body == "dragon_2d"  # provenance recorded...
    # ...but READ_LAST takes no origin_body argument at all: there is no way
    # for a different door to filter to "only my own turns". That absence is
    # the proof, not an assertion about a returned value.


def test_no_active_provider_preserves_request_turn():
    """Presence governs whether somebody may answer. Presence does not
    govern whether the player's words happened. PROVIDER_NOT_REGISTERED
    must not be able to erase turn 1."""
    bridge = _bridge()
    # Nothing registered for this session at all.
    with pytest.raises(ProviderNotRegistered):
        bridge.handle_turn(SESSION_ID, "dragon_2d", "hello?")

    preserved = bridge._ledger.read_last(SESSION_ID, direction="request")
    assert preserved is not None
    assert preserved.turn_id == 0
    assert preserved.direction == "request"
    assert preserved.actor == "player"
    assert preserved.origin_body == "dragon_2d"
    assert preserved.payload == "hello?"
    # And, symmetrically, no response exists to pair with it.
    assert bridge._ledger.read_last(SESSION_ID, direction="response") is None


def test_lapsed_lease_preserves_request_turn():
    """Same asymmetry, expired-lease flavor: an expired Presence record means
    there is no valid responder, but it does not erase the fact that the
    player spoke."""
    bridge = _bridge()
    bridge._presence.register(
        "hermes", "H-2", SESSION_ID, ["chat"], requested_lease=-1.0,  # already expired
    )
    with pytest.raises(ProviderNotRegistered):
        bridge.handle_turn(SESSION_ID, "dragon_2d", "still there?")

    preserved = bridge._ledger.read_last(SESSION_ID, direction="request")
    assert preserved is not None
    assert preserved.turn_id == 0
    assert preserved.direction == "request"
    assert preserved.actor == "player"
    assert preserved.origin_body == "dragon_2d"
    assert preserved.payload == "still there?"
    assert bridge._ledger.read_last(SESSION_ID, direction="response") is None


def test_response_actor_mismatch_is_rejected_not_recorded():
    """Gate 11: a response is only accepted from the actor Presence says is
    ACTIVE. A misbehaving/spoofed dispatcher must be rejected outright, and
    must never reach the Ledger."""
    presence = PresenceRegistry()
    ledger = SessionLedger()
    presence.register("hermes", "H-3", SESSION_ID, ["chat"], endpoint=TEST_ENDPOINT)

    def wrong_actor_dispatch(binding, context, player_input):
        return {"actor": "someone-else", "response": "I am not who Presence says I am"}

    bridge = SharedSessionBridge(presence=presence, ledger=ledger, provider_dispatch=wrong_actor_dispatch)

    with pytest.raises(ResponseActorMismatch):
        bridge.handle_turn(SESSION_ID, "dragon_2d", "hello")

    # The request was appended (step 2 happens before dispatch), but no
    # response turn exists — the mismatch must not silently become history.
    assert ledger.read_last(SESSION_ID, direction="response") is None
    assert ledger.read_last(SESSION_ID, direction="request") is not None


def test_bridge_holds_no_conversation_state_of_its_own():
    """Amendment Gate 13, checked structurally: a SharedSessionBridge
    instance has no attribute that could hold per-body conversation state —
    only references to the two shared authorities, the dispatcher, and the
    stateless continuity context builder (added later; every call to it is
    a pure function of arguments it's handed, holding nothing between
    calls — see continuity_context_builder.py)."""
    bridge = _bridge()
    assert set(vars(bridge).keys()) == {"_presence", "_ledger", "_dispatch", "_continuity"}


def test_presence_deregistered_during_dispatch_blocks_the_response():
    """Step 3 resolves Presence; step 5 dispatch takes real time; Hermes can
    deregister in between. A response claiming to still be "hermes" must not
    be appended just because it was ACTIVE when dispatch *started*. Request
    stays; response does not."""
    presence = PresenceRegistry()
    ledger = SessionLedger()
    presence.register("hermes", "H-1", SESSION_ID, ["chat"], endpoint=TEST_ENDPOINT)

    def deregisters_mid_call(binding, context, player_input):
        presence.deregister("H-1")  # Hermes leaves while "answering"
        return {"actor": "hermes", "response": "still here, honestly"}

    bridge = SharedSessionBridge(presence=presence, ledger=ledger, provider_dispatch=deregisters_mid_call)

    with pytest.raises(ProviderNotRegistered):
        bridge.handle_turn(SESSION_ID, "dragon_2d", "you still there?")

    assert ledger.read_last(SESSION_ID, direction="request") is not None
    assert ledger.read_last(SESSION_ID, direction="response") is None


def test_presence_actor_changed_during_dispatch_blocks_the_stale_response():
    """The other half of the same race: Hermes is replaced by a different
    ACTIVE actor mid-dispatch. A response still claiming to be the old actor
    is a stale answer and must be rejected, not appended."""
    presence = PresenceRegistry()
    ledger = SessionLedger()
    presence.register("hermes", "H-1", SESSION_ID, ["chat"], endpoint=TEST_ENDPOINT)

    def swaps_actor_mid_call(binding, context, player_input):
        presence.deregister("H-1")
        presence.register("claude_code", "C-1", SESSION_ID, ["chat"], endpoint=TEST_ENDPOINT)
        return {"actor": "hermes", "response": "stale answer from the old occupant"}

    bridge = SharedSessionBridge(presence=presence, ledger=ledger, provider_dispatch=swaps_actor_mid_call)

    with pytest.raises(ResponseActorMismatch):
        bridge.handle_turn(SESSION_ID, "dragon_2d", "who's there?")

    assert ledger.read_last(SESSION_ID, direction="request") is not None
    assert ledger.read_last(SESSION_ID, direction="response") is None


def test_turn_is_frozen():
    ledger = SessionLedger()
    turn = ledger.append(SESSION_ID, "dragon_2d", "request", "player", "hello")
    with pytest.raises(dataclasses.FrozenInstanceError):
        turn.payload = "history has been rewritten"


def test_snapshot_is_deep_copied_on_append_and_on_every_read():
    """append() must not store the caller's dict by reference, and each
    read must hand back its own copy — otherwise one reader mutating its
    copy would rewrite the Ledger's stored history for every other reader."""
    ledger = SessionLedger()
    original_snapshot = {"image_path": "snapshots/x.png"}
    ledger.append(SESSION_ID, "dragon_2d", "request", "player", "hello", snapshot=original_snapshot)

    original_snapshot["image_path"] = "tampered-by-caller-after-append"
    stored = ledger.read_last(SESSION_ID)
    assert stored.snapshot["image_path"] == "snapshots/x.png"

    stored.snapshot["image_path"] = "tampered-by-a-reader"
    stored_again = ledger.read_last(SESSION_ID)
    assert stored_again.snapshot["image_path"] == "snapshots/x.png"


def test_presence_record_is_frozen():
    presence = PresenceRegistry()
    record = presence.register("hermes", "H-1", SESSION_ID, ["chat"])
    with pytest.raises(dataclasses.FrozenInstanceError):
        record.agent_id = "someone-else"  # would otherwise be an authority leak


def test_renew_cannot_resurrect_an_expired_instance():
    """An instance whose lease has already lapsed must go through REGISTER
    again, not RENEW — RENEW is not a second REGISTER."""
    presence = PresenceRegistry()
    presence.register("hermes", "H-1", SESSION_ID, ["chat"], requested_lease=-1.0)
    assert presence.resolve(SESSION_ID) is None

    renewed = presence.renew("H-1", extend_by=300.0)

    assert renewed is None
    assert presence.resolve(SESSION_ID) is None
