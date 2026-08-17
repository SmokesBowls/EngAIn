from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest

from tier1.engainos.core.presence_registry import PresenceRegistry
from tier1.engainos.core.provider_session_binding import ProviderSessionBinding

SHARED_SESSION_ID = "20260817_shared_engain_session"


def test_binding_round_trips_through_a_real_presence_record():
    presence = PresenceRegistry()
    endpoint = ProviderSessionBinding.encode_endpoint(
        provider_id="hermes",
        model_id="gpt-5.6-sol",
        provider_session_id="20260731_065008_63a62d",
        launch_options={"provider": "openai-codex"},
    )
    record = presence.register(
        agent_id="hermes",
        instance_id="H-1",
        session_id=SHARED_SESSION_ID,
        capabilities=["chat"],
        endpoint=endpoint,
    )

    binding = ProviderSessionBinding.from_presence_record(record)

    assert binding.provider_id == "hermes"
    assert binding.model_id == "gpt-5.6-sol"
    assert binding.provider_session_id == "20260731_065008_63a62d"
    assert binding.agent_id == "hermes"
    assert binding.instance_id == "H-1"
    assert binding.shared_session_id == SHARED_SESSION_ID
    assert binding.launch_options == {"provider": "openai-codex"}


def test_shared_session_id_and_provider_session_id_are_never_the_same_field():
    """The exact conflation this module exists to prevent: they may
    coincidentally hold equal string values, but they must always be
    reachable as two distinct attributes, never one field doing both
    jobs."""
    presence = PresenceRegistry()
    endpoint = ProviderSessionBinding.encode_endpoint(
        provider_id="hermes", model_id="m", provider_session_id="vendor-native-id-123"
    )
    record = presence.register("hermes", "H-1", SHARED_SESSION_ID, endpoint=endpoint)
    binding = ProviderSessionBinding.from_presence_record(record)

    assert binding.shared_session_id == SHARED_SESSION_ID
    assert binding.provider_session_id == "vendor-native-id-123"
    assert binding.shared_session_id != binding.provider_session_id


def test_switching_provider_keeps_shared_session_id_but_changes_provider_session_id():
    presence = PresenceRegistry()
    hermes_endpoint = ProviderSessionBinding.encode_endpoint(
        provider_id="hermes", model_id="gpt-5.6-sol", provider_session_id="hermes-native-session"
    )
    record_1 = presence.register("hermes", "H-1", SHARED_SESSION_ID, endpoint=hermes_endpoint)
    binding_1 = ProviderSessionBinding.from_presence_record(record_1)

    claude_endpoint = ProviderSessionBinding.encode_endpoint(
        provider_id="claude_code", model_id="sonnet", provider_session_id="claude-native-session"
    )
    record_2 = presence.register("claude_code", "CC-1", SHARED_SESSION_ID, endpoint=claude_endpoint)
    binding_2 = ProviderSessionBinding.from_presence_record(record_2)

    assert binding_1.shared_session_id == binding_2.shared_session_id == SHARED_SESSION_ID
    assert binding_1.provider_id != binding_2.provider_id
    assert binding_1.provider_session_id != binding_2.provider_session_id


def test_missing_endpoint_raises_rather_than_letting_an_adapter_guess():
    presence = PresenceRegistry()
    record = presence.register("hermes", "H-1", SHARED_SESSION_ID)  # no endpoint supplied
    with pytest.raises(ValueError, match="no endpoint"):
        ProviderSessionBinding.from_presence_record(record)


def test_incomplete_endpoint_raises_naming_the_missing_fields():
    presence = PresenceRegistry()
    record = presence.register("hermes", "H-1", SHARED_SESSION_ID, endpoint='{"provider_id": "hermes"}')
    with pytest.raises(ValueError, match="model_id"):
        ProviderSessionBinding.from_presence_record(record)


def test_launch_options_default_to_empty_when_absent():
    presence = PresenceRegistry()
    endpoint = ProviderSessionBinding.encode_endpoint(
        provider_id="hermes", model_id="m", provider_session_id="s"
    )
    record = presence.register("hermes", "H-1", SHARED_SESSION_ID, endpoint=endpoint)
    binding = ProviderSessionBinding.from_presence_record(record)
    assert binding.launch_options == {}
