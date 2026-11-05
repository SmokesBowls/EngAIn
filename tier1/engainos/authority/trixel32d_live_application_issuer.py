from __future__ import annotations

"""Live EngAInOS issuer for one exactly-bound Trixel application grant.

Issuance is authorization only.  This module has no renderer, scene-tree,
transport queue, mesh, collision-object, or application-execution dependency.
"""

import copy
import hashlib
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

from tier1.engainos.gates.gate_trixel32d_handshake import (
    validate_trixel32d_surface_built_bytes,
)
from tier1.engainos.gates.gate_trixel32d_surface_apply import (
    TrustedApplicationAuthority,
    TrustedSceneTruth,
    canonical_application_intent_digest,
    validate_trixel32d_surface_apply,
)

from .trixel32d_live_authority_state import (
    AuthoritySnapshot,
    AuthorityStateError,
    canonical_authorization_artifact_sha256,
    LiveAuthorityState,
    TargetDeclaration,
    UntrustedPrincipal,
)


@dataclass(frozen=True)
class ProposedApplication:
    request_id: str
    surface_id: str
    built_response_sha256: str
    parent_kind: str
    parent_id: str
    application_slot_id: str
    basis_columns: list[list[float]]
    origin: list[float]
    visibility_intent: str
    replacement_mode: str
    replaces_apply_id: str | None
    lifetime_mode: str
    classification: str
    collision_decision: str
    observed_activation_id: str | None
    semantic_main_instance_id: int | None
    semantic_local_generation: int | None


@dataclass(frozen=True)
class IssuanceResult:
    artifact: Mapping[str, Any] | None
    artifact_sha256: str | None
    errors: tuple[str, ...]

    @property
    def authorized(self) -> bool:
        return self.artifact is not None and not self.errors


def _freeze_json(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze_json(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze_json(item) for item in value)
    return value


class LiveApplicationIssuer:
    """Validate, gate, and atomically record a live application authorization."""

    _POLICY_RULE_IDS = (
        "trixel-live-current-activation-v1",
        "trixel-live-semantic-ready-v1",
        "trixel-live-declared-target-v1",
        "trixel-live-slot-cas-v1",
        "trixel-live-presentation-no-collision-v1",
    )

    def __init__(self, state: LiveAuthorityState, *, commit_capability: object) -> None:
        if commit_capability is None:
            raise AuthorityStateError("authorization commit capability is required")
        self.state = state
        self._commit_capability = commit_capability

    def issue(
        self,
        proposed: ProposedApplication,
        *,
        built_response_bytes: bytes,
        trusted_request: Mapping[str, Any],
        principal: Any,
    ) -> IssuanceResult:
        try:
            if not isinstance(proposed, ProposedApplication):
                raise AuthorityStateError("application proposal has invalid shape")
            trusted_principal = self.state.require_trusted_principal(principal)
            if trusted_principal.reality_mode == "REPLAY":
                raise AuthorityStateError("REPLAY reality mode cannot authorize application")
            if trusted_principal.reality_mode == "FINALIZED" and trusted_principal.actor_authority_tier != 3:
                raise AuthorityStateError("FINALIZED application requires Tier 3 authority")
            snapshot = self.state.snapshot_for_issuance()
            target = TargetDeclaration(
                proposed.parent_kind,
                proposed.parent_id,
                proposed.application_slot_id,
            )
            self._evaluate_policy(proposed, snapshot, target)

            if not isinstance(built_response_bytes, bytes):
                raise AuthorityStateError("built response must be exact bytes")
            if not isinstance(trusted_request, Mapping):
                raise AuthorityStateError("trusted Trixel request must be a mapping")
            actual_sha256 = hashlib.sha256(built_response_bytes).hexdigest()
            if actual_sha256 != proposed.built_response_sha256:
                raise AuthorityStateError("built response SHA-256 does not match the proposed binding")
            built_validation = validate_trixel32d_surface_built_bytes(
                built_response_bytes,
                copy.deepcopy(dict(trusted_request)),
                expected_response_sha256=proposed.built_response_sha256,
            )
            if not built_validation.accepted:
                detail = built_validation.errors[0] if built_validation.errors else "unknown failure"
                raise AuthorityStateError(f"built response validation failed: {detail}")

            apply_id = self.state.mint_apply_id()
            decision_id = self.state.mint_decision_id()
            packet = self._build_packet(
                proposed,
                snapshot,
                target,
                trusted_principal,
                apply_id,
                decision_id,
            )
            authority = TrustedApplicationAuthority(
                decision_id=decision_id,
                actor_id=trusted_principal.actor_id,
                actor_authority_tier=trusted_principal.actor_authority_tier,
                reality_mode=trusted_principal.reality_mode,
                authority_revision=trusted_principal.authority_revision,
                runtime_session_id=snapshot.runtime_session_id,
                authorized_intent_sha256=canonical_application_intent_digest(packet),
                ap_rule_ids=self._POLICY_RULE_IDS,
                ap_rule_required=True,
                canonical_persistence_authorized=False,
                collision_grant=None,
            )
            scene_truth = TrustedSceneTruth(
                scene_id=snapshot.activation.scene_id,
                active_scene_revision=snapshot.activation.scene_revision,
                declared_targets=frozenset(
                    (item.parent_kind, item.parent_id, item.application_slot_id)
                    for item in snapshot.declared_targets
                ),
                slot_occupancy=dict(snapshot.slot_occupancy),
            )
            validation = validate_trixel32d_surface_apply(
                packet,
                built_validation=built_validation,
                authority=authority,
                scene_truth=scene_truth,
            )
            if not validation.accepted:
                detail = validation.errors[0] if validation.errors else "unknown failure"
                raise AuthorityStateError(f"application gate rejected: {detail}")

            artifact = {
                "contract": "engainos.trixel32d_live_application_authorization.v1",
                "packet_type": "trixel32d_live_application_authorization",
                "apply_packet": packet,
                "authorized_intent_sha256": authority.authorized_intent_sha256,
                "authority_evidence": {
                    "decision_id": decision_id,
                    "actor_id": trusted_principal.actor_id,
                    "actor_authority_tier": trusted_principal.actor_authority_tier,
                    "reality_mode": trusted_principal.reality_mode,
                    "authority_revision": trusted_principal.authority_revision,
                    "runtime_session_id": snapshot.runtime_session_id,
                    "ap_rule_ids": list(self._POLICY_RULE_IDS),
                },
                "scene_activation": {
                    "activation_id": snapshot.activation.activation_id,
                    "scene_id": snapshot.activation.scene_id,
                    "scene_revision": snapshot.activation.scene_revision,
                },
                "semantic_activation": {
                    "activation_id": snapshot.observation.activation_id,
                    "semantic_main_instance_id": snapshot.observation.semantic_main_instance_id,
                    "semantic_local_generation": snapshot.observation.semantic_local_generation,
                },
                "gate_result": {
                    "gate_name": "gate_trixel32d_surface_apply",
                    "passed": "TRUE",
                },
                "execution_performed": False,
                "renderer_contacted": False,
            }
            artifact_sha256 = canonical_authorization_artifact_sha256(artifact)
            self.state.commit_authorization(
                expected_generation=snapshot.generation,
                decision_id=decision_id,
                apply_id=apply_id,
                target=target,
                replacement_mode=proposed.replacement_mode,
                replaces_apply_id=proposed.replaces_apply_id,
                artifact=artifact,
                built_response_bytes=built_response_bytes,
                trusted_request=trusted_request,
                capability=self._commit_capability,
            )
            return IssuanceResult(
                artifact=_freeze_json(artifact),
                artifact_sha256=artifact_sha256,
                errors=(),
            )
        except AuthorityStateError as exc:
            return IssuanceResult(artifact=None, artifact_sha256=None, errors=(str(exc),))
        except Exception as exc:
            return IssuanceResult(
                artifact=None,
                artifact_sha256=None,
                errors=(f"live application issuance failed closed: {type(exc).__name__}",),
            )

    def _evaluate_policy(
        self,
        proposed: ProposedApplication,
        snapshot: AuthoritySnapshot,
        target: TargetDeclaration,
    ) -> None:
        observation = snapshot.observation
        if proposed.observed_activation_id != observation.activation_id:
            raise AuthorityStateError("application request activation observation is stale")
        if proposed.semantic_main_instance_id != observation.semantic_main_instance_id:
            raise AuthorityStateError("application request Semantic main instance does not match")
        if proposed.semantic_local_generation != observation.semantic_local_generation:
            raise AuthorityStateError("application request Semantic local generation is stale")
        if target not in snapshot.declared_targets:
            raise AuthorityStateError("application request names an undeclared target")
        occupant = snapshot.slot_occupancy.get(target.application_slot_id)
        if proposed.replacement_mode == "CREATE_ONLY":
            if proposed.replaces_apply_id is not None:
                raise AuthorityStateError("CREATE_ONLY may not name a replacement")
            if occupant is not None:
                raise AuthorityStateError("CREATE_ONLY application slot is occupied")
        elif proposed.replacement_mode == "REPLACE_EXACT":
            if occupant != proposed.replaces_apply_id:
                raise AuthorityStateError("REPLACE_EXACT application occupant does not match")
        else:
            raise AuthorityStateError("application replacement mode is unknown")
        if proposed.lifetime_mode != "SCENE_BOUND":
            raise AuthorityStateError("initial live issuer permits SCENE_BOUND lifetime only")
        if proposed.classification != "PRESENTATION_ONLY":
            raise AuthorityStateError("initial live issuer permits PRESENTATION_ONLY classification only")
        if proposed.collision_decision != "DENIED":
            raise AuthorityStateError("initial live issuer requires explicit collision denial")

    @staticmethod
    def _build_packet(
        proposed: ProposedApplication,
        snapshot: AuthoritySnapshot,
        target: TargetDeclaration,
        principal: UntrustedPrincipal,
        apply_id: str,
        decision_id: str,
    ) -> dict[str, Any]:
        return {
            "contract": "trixel32d_surface_apply.v1",
            "packet_type": "trixel32d_surface_apply",
            "apply_id": apply_id,
            "surface_binding": {
                "built_contract": "trixel32d_surface_built.v1",
                "request_id": proposed.request_id,
                "surface_id": proposed.surface_id,
                "built_response_sha256": proposed.built_response_sha256,
            },
            "authorization": {
                "decision": "AUTHORIZED",
                "decision_id": decision_id,
                "issued_by": "engainos",
                "actor_id": principal.actor_id,
                "actor_authority_tier": principal.actor_authority_tier,
                "reality_mode": principal.reality_mode,
                "authority_revision": principal.authority_revision,
                "runtime_session_id": snapshot.runtime_session_id,
                "ap_rule_ids": list(LiveApplicationIssuer._POLICY_RULE_IDS),
            },
            "target": {
                "scene_id": snapshot.activation.scene_id,
                "scene_revision": snapshot.activation.scene_revision,
                "parent_kind": target.parent_kind,
                "parent_id": target.parent_id,
                "application_slot_id": target.application_slot_id,
            },
            "local_to_scene": {
                "space": "SCENE_LOCAL_Y_UP",
                "basis_columns": copy.deepcopy(proposed.basis_columns),
                "origin": list(proposed.origin),
            },
            "visibility": {"intent": proposed.visibility_intent},
            "replacement": {
                "mode": proposed.replacement_mode,
                "replaces_apply_id": proposed.replaces_apply_id,
            },
            "lifetime": {"mode": proposed.lifetime_mode},
            "classification": proposed.classification,
            "collision": {
                "decision": proposed.collision_decision,
                "authorized_by_decision_id": decision_id,
                "shape_policy": "NONE",
                "layer": 0,
                "mask": 0,
            },
        }
