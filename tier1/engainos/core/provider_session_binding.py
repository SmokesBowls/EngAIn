"""
provider_session_binding.py - The provider-neutral dispatch boundary.

Corrects a conflation in the original dispatch design: PresenceRecord.session_id
was used both as EngAIn's own Ledger/Presence key AND handed directly to a
provider CLI as its native --resume target. Those are different identifier
spaces, owned by different parties, and must never be treated as
interchangeable:

    shared_session_id   — belongs to EngAIn. The stable key the Ledger and
                            Presence are keyed by (PresenceRecord.session_id).
                            Follows the continuing agent across provider
                            switches; never changes just because the active
                            provider does.
    provider_session_id — belongs to the vendor (Hermes, Claude Code, or
                            any other provider). Only meaningful to that one
                            provider's own --resume mechanism. Changes
                            whenever the active provider changes, since a
                            new provider cannot resume another vendor's
                            private conversation state.

Switching providers does not, and cannot, transfer a vendor's private
conversation state. EngAIn's own Ledger is what supplies portable
continuity across that switch — never a vendor's own session transcript.
This is why a dispatch adapter takes a ProviderSessionBinding, not a raw
PresenceRecord: it receives the binding fully formed and never decides
which provider, model, or native session to use, exactly like it already
only relays what Presence and the Ledger say.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional

from tier1.engainos.core.presence_registry import PresenceRecord


@dataclass(frozen=True)
class ProviderSessionBinding:
    provider_id: str
    model_id: str
    provider_session_id: str
    agent_id: str
    instance_id: str
    shared_session_id: str
    launch_options: Mapping[str, Any]

    @staticmethod
    def encode_endpoint(
        provider_id: str,
        model_id: str,
        provider_session_id: str,
        launch_options: Optional[Mapping[str, Any]] = None,
    ) -> str:
        """Builds the JSON string stored in PresenceRecord.endpoint at
        REGISTER time. agent_id/instance_id/shared_session_id are
        deliberately not included here — they already exist as
        PresenceRecord's own top-level fields (agent_id, instance_id,
        session_id) and are merged in by from_presence_record, never
        duplicated into two places that could drift apart."""
        return json.dumps(
            {
                "provider_id": provider_id,
                "model_id": model_id,
                "provider_session_id": provider_session_id,
                "launch_options": dict(launch_options or {}),
            }
        )

    @staticmethod
    def from_presence_record(record: PresenceRecord) -> "ProviderSessionBinding":
        """The only place a binding gets constructed for dispatch. Takes an
        already-RESOLVED PresenceRecord (Presence has already answered "is
        someone here") and combines it with the provider-specific detail
        carried in record.endpoint. Raises, rather than guessing or
        defaulting, if endpoint is missing or incomplete — an adapter must
        never fall back to deciding a provider/model/session on its own,
        so this constructor must never hand it something to guess with."""
        if not record.endpoint:
            raise ValueError(
                f"PresenceRecord for session_id={record.session_id!r} has no endpoint; "
                "cannot construct a ProviderSessionBinding without one"
            )
        try:
            parsed: Dict[str, Any] = json.loads(record.endpoint)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"PresenceRecord.endpoint is not valid JSON: {record.endpoint!r}") from exc

        missing = [key for key in ("provider_id", "model_id", "provider_session_id") if key not in parsed]
        if missing:
            raise ValueError(
                f"PresenceRecord.endpoint is missing required binding fields {missing}: {record.endpoint!r}"
            )

        return ProviderSessionBinding(
            provider_id=parsed["provider_id"],
            model_id=parsed["model_id"],
            provider_session_id=parsed["provider_session_id"],
            agent_id=record.agent_id,
            instance_id=record.instance_id,
            shared_session_id=record.session_id,
            launch_options=parsed.get("launch_options", {}),
        )
