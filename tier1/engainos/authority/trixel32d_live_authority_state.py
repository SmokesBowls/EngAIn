from __future__ import annotations

"""Trusted live authority state for Trixel application issuance.

This module owns correlation and authorization records only.  It does not import
Godot, transport geometry, mutate scenes, or execute an application.
"""

import base64
import copy
import fcntl
import hashlib
import json
import os
import secrets
import stat
import threading
from dataclasses import asdict, dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any, Callable, Mapping

from tier1.engainos.gates.gate_trixel32d_handshake import (
    BuiltSurfaceValidation,
    validate_trixel32d_surface_built_bytes,
)
from tier1.engainos.gates.gate_trixel32d_surface_apply import (
    TrustedApplicationAuthority,
    TrustedSceneTruth,
    canonical_application_intent_digest,
    validate_trixel32d_surface_apply,
)


class AuthorityStateError(RuntimeError):
    """Fail-closed live authority state error."""


def _reject_nonfinite_json(token: str) -> Any:
    raise ValueError(f"non-finite JSON constant is forbidden: {token}")


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def canonical_authorization_artifact_sha256(artifact: Mapping[str, Any]) -> str:
    try:
        payload = json.dumps(
            dict(artifact),
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise AuthorityStateError("authorization artifact is not canonical JSON") from exc
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class UntrustedPrincipal:
    """Principal-shaped value; trusted only when registered by this state owner."""

    actor_id: str
    actor_authority_tier: int
    reality_mode: str
    authority_revision: str
    trust_token: str = field(repr=False)


@dataclass(frozen=True)
class SceneActivation:
    runtime_session_id: str
    activation_id: str
    scene_id: str
    scene_revision: str


@dataclass(frozen=True)
class SemanticActivationObservation:
    runtime_session_id: str
    activation_id: str
    scene_id: str
    scene_revision: str
    semantic_main_instance_id: int
    semantic_local_generation: int


@dataclass(frozen=True)
class TargetDeclaration:
    parent_kind: str
    parent_id: str
    application_slot_id: str


@dataclass(frozen=True)
class AuthoritySnapshot:
    generation: int
    runtime_session_id: str
    authority_revision: str
    activation: SceneActivation
    observation: SemanticActivationObservation
    declared_targets: frozenset[TargetDeclaration]
    slot_occupancy: Mapping[str, str]


class LiveAuthorityState:
    """Runtime-scoped trusted state with a durable append-only decision ledger."""

    _REALITY_MODES = frozenset({"DRAFT", "FINALIZED", "REPLAY"})
    _PARENT_KINDS = frozenset({"SCENE_ROOT", "RUNTIME_CONTAINER", "ENTITY_MOUNT"})

    def __init__(
        self,
        ledger_path: Path | str,
        authority_revision: str,
        *,
        principal_registration_capability: object,
        trusted_state_mutation_capability: object,
        authorization_commit_capability: object,
        decision_consumption_capability: object,
        id_factory: Callable[[], str] | None = None,
    ) -> None:
        if principal_registration_capability is None:
            raise AuthorityStateError("principal registration capability is required")
        if trusted_state_mutation_capability is None:
            raise AuthorityStateError("trusted state mutation capability is required")
        if authorization_commit_capability is None:
            raise AuthorityStateError("authorization commit capability is required")
        if decision_consumption_capability is None:
            raise AuthorityStateError("decision consumption capability is required")
        capabilities = (
            principal_registration_capability,
            trusted_state_mutation_capability,
            authorization_commit_capability,
            decision_consumption_capability,
        )
        if len({id(capability) for capability in capabilities}) != len(capabilities):
            raise AuthorityStateError("privileged capabilities must be separate objects")
        if not isinstance(authority_revision, str) or not authority_revision:
            raise AuthorityStateError("authority revision must be a non-empty string")
        self.ledger_path = Path(ledger_path)
        self.authority_revision = authority_revision
        self.runtime_session_id = f"engain-session-{secrets.token_hex(16)}"
        self._principal_registration_capability = principal_registration_capability
        self._trusted_state_mutation_capability = trusted_state_mutation_capability
        self._authorization_commit_capability = authorization_commit_capability
        self._decision_consumption_capability = decision_consumption_capability
        self._id_factory = id_factory or (lambda: secrets.token_hex(16))
        self._lock = threading.RLock()
        self._ledger_lock_fd: int | None = None
        self._closed = False
        self._generation = 0
        self._activation: SceneActivation | None = None
        self._observation: SemanticActivationObservation | None = None
        self._targets: dict[str, set[TargetDeclaration]] = {}
        self._slot_occupancy: dict[str, str] = {}
        self._trusted_principals: dict[str, tuple[str, int, str, str]] = {}
        self._decisions: dict[str, dict[str, Any]] = {}
        self._apply_ids: set[str] = set()
        self._consumed: set[tuple[str, str]] = set()
        self._acquire_ledger_ownership()
        try:
            self._load_ledger()
        except Exception:
            self.close()
            raise

    def _acquire_ledger_ownership(self) -> None:
        try:
            self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
            base_flags = os.O_RDWR | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
            created = False
            try:
                fd = os.open(self.ledger_path, base_flags | os.O_CREAT | os.O_EXCL, 0o600)
                created = True
            except FileExistsError:
                fd = os.open(self.ledger_path, base_flags)
            try:
                ledger_stat = os.fstat(fd)
                if not stat.S_ISREG(ledger_stat.st_mode):
                    raise OSError("durable authority ledger must be a regular file")
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                os.fchmod(fd, 0o600)
            except Exception:
                os.close(fd)
                raise
            self._ledger_lock_fd = fd
            if created:
                directory_fd = os.open(
                    self.ledger_path.parent,
                    os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0),
                )
                try:
                    os.fsync(directory_fd)
                finally:
                    os.close(directory_fd)
        except OSError as exc:
            raise AuthorityStateError("durable authority ledger is already owned or unsafe") from exc

    def close(self) -> None:
        """Release this runtime's exclusive authority-ledger ownership."""
        with self._lock:
            if self._closed:
                return
            self._closed = True
            fd = self._ledger_lock_fd
            self._ledger_lock_fd = None
            if fd is not None:
                try:
                    fcntl.flock(fd, fcntl.LOCK_UN)
                finally:
                    os.close(fd)

    def _require_open(self) -> None:
        if self._closed or self._ledger_lock_fd is None:
            raise AuthorityStateError("live authority state is closed")

    def __enter__(self) -> "LiveAuthorityState":
        self._require_open()
        return self

    def __exit__(self, _exc_type: Any, _exc: Any, _traceback: Any) -> None:
        self.close()

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass

    @property
    def decision_count(self) -> int:
        with self._lock:
            return len(self._decisions)

    @property
    def slot_occupancy(self) -> dict[str, str]:
        with self._lock:
            return dict(self._slot_occupancy)

    @property
    def current_observation(self) -> SemanticActivationObservation | None:
        with self._lock:
            return self._observation

    def register_trusted_principal(
        self,
        actor_id: str,
        actor_authority_tier: int,
        reality_mode: str,
        *,
        capability: object,
    ) -> UntrustedPrincipal:
        """Register a principal supplied by the trusted server composition root.

        HTTP/request handlers must resolve their authenticated identity first and
        must never receive the registration capability.
        """
        if capability is not self._principal_registration_capability:
            raise AuthorityStateError("trusted principal registration capability is invalid")
        if not isinstance(actor_id, str) or not actor_id:
            raise AuthorityStateError("trusted principal actor_id must be non-empty")
        if isinstance(actor_authority_tier, bool) or actor_authority_tier not in (0, 1, 2, 3):
            raise AuthorityStateError("trusted principal tier must be an integer from 0 through 3")
        if reality_mode not in self._REALITY_MODES:
            raise AuthorityStateError("trusted principal reality mode is unknown")
        token = secrets.token_hex(32)
        identity = (actor_id, actor_authority_tier, reality_mode, self.authority_revision)
        with self._lock:
            self._require_open()
            self._trusted_principals[token] = identity
        return UntrustedPrincipal(*identity, trust_token=token)

    def require_trusted_principal(self, principal: Any) -> UntrustedPrincipal:
        if not isinstance(principal, UntrustedPrincipal):
            raise AuthorityStateError("application issuance requires a trusted principal")
        identity = (
            principal.actor_id,
            principal.actor_authority_tier,
            principal.reality_mode,
            principal.authority_revision,
        )
        with self._lock:
            self._require_open()
            if self._trusted_principals.get(principal.trust_token) != identity:
                raise AuthorityStateError("application issuance requires a trusted principal")
        return principal

    def _require_trusted_state_mutation(self, capability: object) -> None:
        if capability is not self._trusted_state_mutation_capability:
            raise AuthorityStateError("trusted state mutation capability is invalid")

    def activate_scene(
        self, normalized_scene: Mapping[str, Any], *, capability: object
    ) -> SceneActivation:
        self._require_trusted_state_mutation(capability)
        if not isinstance(normalized_scene, Mapping):
            raise AuthorityStateError("activated scene must be a mapping")
        scene_copy = copy.deepcopy(dict(normalized_scene))
        scene_id = scene_copy.get("scene_id") or scene_copy.get("@id")
        if not isinstance(scene_id, str) or not scene_id:
            raise AuthorityStateError("activated scene identity is missing")
        try:
            canonical = json.dumps(
                scene_copy,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            ).encode("utf-8")
        except (TypeError, ValueError) as exc:
            raise AuthorityStateError("activated scene is not deterministically serializable") from exc
        revision = f"scene-sha256:{hashlib.sha256(canonical).hexdigest()}"
        activation = SceneActivation(
            runtime_session_id=self.runtime_session_id,
            activation_id=f"engain-activation-{self._next_hex()}",
            scene_id=scene_id,
            scene_revision=revision,
        )
        with self._lock:
            self._require_open()
            self._activation = activation
            self._observation = None
            self._slot_occupancy = {}
            self._generation += 1
        return activation

    def declare_target(
        self,
        scene_id: str,
        scene_revision: str,
        target: TargetDeclaration,
        *,
        capability: object,
    ) -> None:
        self._require_trusted_state_mutation(capability)
        if not isinstance(target, TargetDeclaration):
            raise AuthorityStateError("target declaration must be authority-owned")
        if target.parent_kind not in self._PARENT_KINDS:
            raise AuthorityStateError("target declaration parent kind is invalid")
        if not target.parent_id or not target.application_slot_id:
            raise AuthorityStateError("target declaration identities must be non-empty")
        with self._lock:
            self._require_open()
            activation = self._activation
            if activation is None:
                raise AuthorityStateError("target declaration requires an active scene")
            if scene_id != activation.scene_id or scene_revision != activation.scene_revision:
                raise AuthorityStateError("target declaration does not match the current scene activation")
            same_activation = self._targets.setdefault(activation.activation_id, set())
            for declared in same_activation:
                if (
                    declared.application_slot_id == target.application_slot_id
                    and declared != target
                ):
                    raise AuthorityStateError("application slot identity is ambiguous")
            same_activation.add(target)
            self._generation += 1

    def observe_semantic_activation(
        self, observation: SemanticActivationObservation, *, capability: object
    ) -> None:
        self._require_trusted_state_mutation(capability)
        if not isinstance(observation, SemanticActivationObservation):
            raise AuthorityStateError("Semantic activation observation has invalid shape")
        if isinstance(observation.semantic_main_instance_id, bool) or not isinstance(
            observation.semantic_main_instance_id, int
        ) or observation.semantic_main_instance_id <= 0:
            raise AuthorityStateError("Semantic main instance identity must be a positive integer")
        if isinstance(observation.semantic_local_generation, bool) or not isinstance(
            observation.semantic_local_generation, int
        ) or observation.semantic_local_generation < 0:
            raise AuthorityStateError("Semantic local generation must be a non-negative integer")
        with self._lock:
            self._require_open()
            activation = self._activation
            if activation is None:
                raise AuthorityStateError("no server-owned scene activation exists")
            if observation.runtime_session_id != self.runtime_session_id:
                raise AuthorityStateError("Semantic observation runtime session does not match")
            if observation.activation_id != activation.activation_id:
                raise AuthorityStateError("Semantic observation activation identity does not match")
            if observation.scene_id != activation.scene_id:
                raise AuthorityStateError("Semantic observation scene identity does not match")
            if observation.scene_revision != activation.scene_revision:
                raise AuthorityStateError("Semantic observation scene revision does not match")
            if self._observation is not None:
                if observation.semantic_main_instance_id != self._observation.semantic_main_instance_id:
                    raise AuthorityStateError("Semantic main instance changed within one activation")
                if observation.semantic_local_generation <= self._observation.semantic_local_generation:
                    raise AuthorityStateError("Semantic local generation is stale")
            self._observation = observation
            self._generation += 1

    def snapshot_for_issuance(self) -> AuthoritySnapshot:
        with self._lock:
            self._require_open()
            if self._activation is None:
                raise AuthorityStateError("server-owned scene activation is missing")
            if self._observation is None:
                raise AuthorityStateError("Semantic activation observation is missing")
            declarations = frozenset(self._targets.get(self._activation.activation_id, set()))
            return AuthoritySnapshot(
                generation=self._generation,
                runtime_session_id=self.runtime_session_id,
                authority_revision=self.authority_revision,
                activation=self._activation,
                observation=self._observation,
                declared_targets=declarations,
                slot_occupancy=MappingProxyType(dict(self._slot_occupancy)),
            )

    def commit_authorization(
        self,
        *,
        expected_generation: int,
        decision_id: str,
        apply_id: str,
        target: TargetDeclaration,
        replacement_mode: str,
        replaces_apply_id: str | None,
        artifact: Mapping[str, Any],
        built_response_bytes: bytes,
        trusted_request: Mapping[str, Any],
        capability: object,
    ) -> None:
        if capability is not self._authorization_commit_capability:
            raise AuthorityStateError("authorization commit capability is invalid")
        with self._lock:
            self._require_open()
            if expected_generation != self._generation:
                raise AuthorityStateError("live authority state changed before authorization commitment")
            if decision_id in self._decisions:
                raise AuthorityStateError("decision identity was already issued")
            if apply_id in self._apply_ids:
                raise AuthorityStateError("application identity was already issued")
            snapshot = self.snapshot_for_issuance()
            if target not in snapshot.declared_targets:
                raise AuthorityStateError("application target is undeclared")
            occupant = self._slot_occupancy.get(target.application_slot_id)
            if replacement_mode == "CREATE_ONLY":
                if occupant is not None:
                    raise AuthorityStateError("CREATE_ONLY application slot is occupied")
            elif replacement_mode == "REPLACE_EXACT":
                if occupant != replaces_apply_id:
                    raise AuthorityStateError("REPLACE_EXACT application occupant does not match")
            else:
                raise AuthorityStateError("replacement mode is unknown")
            artifact_copy = copy.deepcopy(dict(artifact))
            artifact_sha256 = canonical_authorization_artifact_sha256(artifact_copy)
            evidence = artifact_copy.get("authority_evidence")
            if not isinstance(evidence, dict):
                raise AuthorityStateError("authorization artifact lacks authority evidence")
            event = {
                "event": "authorization_issued",
                "runtime_session_id": self.runtime_session_id,
                "authority_revision": self.authority_revision,
                "actor_id": evidence.get("actor_id"),
                "actor_authority_tier": evidence.get("actor_authority_tier"),
                "reality_mode": evidence.get("reality_mode"),
                "ap_rule_ids": evidence.get("ap_rule_ids"),
                "decision_id": decision_id,
                "apply_id": apply_id,
                "scene_id": snapshot.activation.scene_id,
                "scene_revision": snapshot.activation.scene_revision,
                "activation_id": snapshot.activation.activation_id,
                "semantic_main_instance_id": snapshot.observation.semantic_main_instance_id,
                "semantic_local_generation": snapshot.observation.semantic_local_generation,
                "replacement_mode": replacement_mode,
                "replaces_apply_id": replaces_apply_id,
                "built_response_b64": base64.b64encode(built_response_bytes).decode("ascii"),
                "trusted_request": copy.deepcopy(dict(trusted_request)),
                "slot": asdict(target),
                "artifact_sha256": artifact_sha256,
                "artifact": artifact_copy,
            }
            try:
                self._validate_ledger_artifact_bindings(event, artifact_copy, 0)
                registered_actor = (
                    event["actor_id"],
                    event["actor_authority_tier"],
                    event["reality_mode"],
                    event["authority_revision"],
                ) in self._trusted_principals.values()
                if not registered_actor:
                    raise ValueError("artifact actor does not resolve to a registered trusted principal")
                packet = artifact_copy["apply_packet"]
                expected_built_sha256 = packet["surface_binding"]["built_response_sha256"]
                built_validation = validate_trixel32d_surface_built_bytes(
                    built_response_bytes,
                    copy.deepcopy(dict(trusted_request)),
                    expected_response_sha256=expected_built_sha256,
                )
                if not built_validation.accepted:
                    detail = built_validation.errors[0] if built_validation.errors else "unknown build rejection"
                    raise ValueError(f"exact built response fails validation: {detail}")
                scene_truth = TrustedSceneTruth(
                    scene_id=snapshot.activation.scene_id,
                    active_scene_revision=snapshot.activation.scene_revision,
                    declared_targets=frozenset(
                        (item.parent_kind, item.parent_id, item.application_slot_id)
                        for item in snapshot.declared_targets
                    ),
                    slot_occupancy=dict(snapshot.slot_occupancy),
                )
                self._validate_artifact_through_active_gate(
                    event, artifact_copy, built_validation, scene_truth, 0
                )
            except (KeyError, TypeError, ValueError) as exc:
                raise AuthorityStateError(f"authorization artifact is invalid: {exc}") from exc
            self._append_event(event)
            self._decisions[decision_id] = event
            self._apply_ids.add(apply_id)
            self._slot_occupancy[target.application_slot_id] = apply_id
            self._generation += 1

    def consume_authorization(
        self,
        decision_id: str,
        apply_id: str,
        *,
        applied_artifact_sha256: str,
        capability: object,
    ) -> None:
        if capability is not self._decision_consumption_capability:
            raise AuthorityStateError("decision consumption capability is invalid")
        key = (decision_id, apply_id)
        with self._lock:
            self._require_open()
            if key in self._consumed:
                raise AuthorityStateError("authorization decision was already consumed")
            decision = self._decisions.get(decision_id)
            if decision is None or decision.get("apply_id") != apply_id:
                raise AuthorityStateError("authorization decision does not resolve exactly")
            if decision.get("artifact_sha256") != applied_artifact_sha256:
                raise AuthorityStateError("applied authorization artifact hash does not match")
            if decision.get("runtime_session_id") != self.runtime_session_id:
                raise AuthorityStateError("authorization belongs to a different runtime session")
            if self._activation is None or decision.get("activation_id") != self._activation.activation_id:
                raise AuthorityStateError("authorization belongs to a different scene activation")
            if (
                self._observation is None
                or decision.get("semantic_main_instance_id")
                != self._observation.semantic_main_instance_id
                or decision.get("semantic_local_generation")
                != self._observation.semantic_local_generation
            ):
                raise AuthorityStateError("authorization belongs to a different Semantic observation")
            slot = decision.get("slot")
            slot_id = slot.get("application_slot_id") if isinstance(slot, dict) else None
            if not isinstance(slot_id, str) or self._slot_occupancy.get(slot_id) != apply_id:
                raise AuthorityStateError("authorized application no longer occupies its reserved slot")
            event = {
                "event": "authorization_consumed",
                "runtime_session_id": self.runtime_session_id,
                "decision_id": decision_id,
                "apply_id": apply_id,
                "artifact_sha256": applied_artifact_sha256,
            }
            self._append_event(event)
            self._consumed.add(key)

    def _next_hex(self) -> str:
        value = self._id_factory()
        if (
            not isinstance(value, str)
            or len(value) != 32
            or any(ch not in "0123456789abcdef" for ch in value)
        ):
            raise AuthorityStateError("identity factory must return exactly 32 lowercase hexadecimal characters")
        return value

    def mint_apply_id(self) -> str:
        return f"t32dapply_{self._next_hex()[-16:]}"

    def mint_decision_id(self) -> str:
        return f"engainos-live-application-{self._next_hex()}"

    @staticmethod
    def _validate_ledger_artifact_bindings(
        event: Mapping[str, Any], artifact: Mapping[str, Any], line_number: int
    ) -> None:
        packet = artifact.get("apply_packet")
        authority = packet.get("authorization") if isinstance(packet, dict) else None
        target = packet.get("target") if isinstance(packet, dict) else None
        evidence = artifact.get("authority_evidence")
        scene = artifact.get("scene_activation")
        semantic = artifact.get("semantic_activation")
        gate_result = artifact.get("gate_result")
        collision = packet.get("collision") if isinstance(packet, dict) else None
        replacement = packet.get("replacement") if isinstance(packet, dict) else None
        if not isinstance(packet, dict):
            raise ValueError(f"record {line_number} lacks application packet")
        expected_artifact_keys = {
            "contract",
            "packet_type",
            "apply_packet",
            "authorized_intent_sha256",
            "authority_evidence",
            "scene_activation",
            "semantic_activation",
            "gate_result",
            "execution_performed",
            "renderer_contacted",
        }
        if set(artifact) != expected_artifact_keys:
            raise ValueError(f"record {line_number} has noncanonical artifact schema")
        if not all(isinstance(value, dict) for value in (authority, target, evidence, scene, semantic, gate_result, collision)):
            raise ValueError(f"record {line_number} has malformed nested artifact evidence")
        if not isinstance(evidence, dict):
            raise ValueError(f"record {line_number} has malformed authority evidence")
        nested_schemas = (
            (packet, {
                "contract", "packet_type", "apply_id", "surface_binding", "authorization",
                "target", "local_to_scene", "visibility", "replacement", "lifetime",
                "classification", "collision",
            }, "apply packet"),
            (packet.get("surface_binding"), {
                "built_contract", "request_id", "surface_id", "built_response_sha256",
            }, "surface binding"),
            (authority, {
                "decision", "decision_id", "issued_by", "actor_id", "actor_authority_tier",
                "reality_mode", "authority_revision", "runtime_session_id", "ap_rule_ids",
            }, "authorization"),
            (target, {
                "scene_id", "scene_revision", "parent_kind", "parent_id", "application_slot_id",
            }, "target"),
            (packet.get("local_to_scene"), {"space", "basis_columns", "origin"}, "local transform"),
            (packet.get("visibility"), {"intent"}, "visibility"),
            (packet.get("replacement"), {"mode", "replaces_apply_id"}, "replacement"),
            (packet.get("lifetime"), {"mode"}, "lifetime"),
            (collision, {
                "decision", "authorized_by_decision_id", "shape_policy", "layer", "mask",
            }, "collision"),
            (scene, {"activation_id", "scene_id", "scene_revision"}, "scene activation"),
            (semantic, {
                "activation_id", "semantic_main_instance_id", "semantic_local_generation",
            }, "Semantic activation"),
            (gate_result, {"gate_name", "passed"}, "gate result"),
        )
        for value, expected_keys, label in nested_schemas:
            if not isinstance(value, dict) or set(value) != expected_keys:
                raise ValueError(f"record {line_number} has noncanonical {label} schema")
        if set(evidence) != {
            "decision_id",
            "actor_id",
            "actor_authority_tier",
            "reality_mode",
            "authority_revision",
            "runtime_session_id",
            "ap_rule_ids",
        }:
            raise ValueError(f"record {line_number} has noncanonical authority evidence")
        expected_digest = canonical_application_intent_digest(packet)
        bindings = (
            (artifact.get("contract"), "engainos.trixel32d_live_application_authorization.v1"),
            (artifact.get("packet_type"), "trixel32d_live_application_authorization"),
            (packet.get("contract"), "trixel32d_surface_apply.v1"),
            (packet.get("packet_type"), "trixel32d_surface_apply"),
            (artifact.get("authorized_intent_sha256"), expected_digest),
            (packet.get("apply_id"), event["apply_id"]),
            (authority.get("decision_id") if isinstance(authority, dict) else None, event["decision_id"]),
            (
                authority.get("runtime_session_id") if isinstance(authority, dict) else None,
                event["runtime_session_id"],
            ),
            (authority.get("decision") if isinstance(authority, dict) else None, "AUTHORIZED"),
            (authority.get("issued_by") if isinstance(authority, dict) else None, "engainos"),
            (
                authority.get("actor_id") if isinstance(authority, dict) else None,
                event["actor_id"],
            ),
            (evidence.get("actor_id"), event["actor_id"]),
            (
                authority.get("actor_authority_tier") if isinstance(authority, dict) else None,
                event["actor_authority_tier"],
            ),
            (evidence.get("actor_authority_tier"), event["actor_authority_tier"]),
            (
                authority.get("reality_mode") if isinstance(authority, dict) else None,
                event["reality_mode"],
            ),
            (evidence.get("reality_mode"), event["reality_mode"]),
            (
                authority.get("authority_revision") if isinstance(authority, dict) else None,
                event["authority_revision"],
            ),
            (evidence.get("authority_revision"), event["authority_revision"]),
            (
                authority.get("ap_rule_ids") if isinstance(authority, dict) else None,
                event["ap_rule_ids"],
            ),
            (evidence.get("ap_rule_ids"), event["ap_rule_ids"]),
            (target.get("scene_id") if isinstance(target, dict) else None, event["scene_id"]),
            (target.get("scene_revision") if isinstance(target, dict) else None, event["scene_revision"]),
            (target.get("parent_kind") if isinstance(target, dict) else None, event["slot"]["parent_kind"]),
            (target.get("parent_id") if isinstance(target, dict) else None, event["slot"]["parent_id"]),
            (
                target.get("application_slot_id") if isinstance(target, dict) else None,
                event["slot"]["application_slot_id"],
            ),
            (evidence.get("decision_id") if isinstance(evidence, dict) else None, event["decision_id"]),
            (
                evidence.get("runtime_session_id") if isinstance(evidence, dict) else None,
                event["runtime_session_id"],
            ),
            (scene.get("activation_id") if isinstance(scene, dict) else None, event["activation_id"]),
            (scene.get("scene_id") if isinstance(scene, dict) else None, event["scene_id"]),
            (scene.get("scene_revision") if isinstance(scene, dict) else None, event["scene_revision"]),
            (
                semantic.get("activation_id") if isinstance(semantic, dict) else None,
                event["activation_id"],
            ),
            (
                semantic.get("semantic_main_instance_id") if isinstance(semantic, dict) else None,
                event["semantic_main_instance_id"],
            ),
            (
                semantic.get("semantic_local_generation") if isinstance(semantic, dict) else None,
                event["semantic_local_generation"],
            ),
            (
                replacement.get("mode") if isinstance(replacement, dict) else None,
                event["replacement_mode"],
            ),
            (
                replacement.get("replaces_apply_id") if isinstance(replacement, dict) else None,
                event["replaces_apply_id"],
            ),
            (
                collision.get("authorized_by_decision_id") if isinstance(collision, dict) else None,
                event["decision_id"],
            ),
            (
                gate_result.get("gate_name") if isinstance(gate_result, dict) else None,
                "gate_trixel32d_surface_apply",
            ),
            (gate_result.get("passed") if isinstance(gate_result, dict) else None, "TRUE"),
            (artifact.get("execution_performed"), False),
            (artifact.get("renderer_contacted"), False),
        )
        if any(actual != expected for actual, expected in bindings):
            raise ValueError(f"record {line_number} artifact bindings disagree with durable event")

    @staticmethod
    def _validate_artifact_through_active_gate(
        event: Mapping[str, Any],
        artifact: Mapping[str, Any],
        built_validation: BuiltSurfaceValidation,
        scene_truth: TrustedSceneTruth,
        line_number: int,
    ) -> None:
        packet = artifact["apply_packet"]
        authority_record = packet["authorization"]
        authority = TrustedApplicationAuthority(
            decision_id=event["decision_id"],
            actor_id=event["actor_id"],
            actor_authority_tier=event["actor_authority_tier"],
            reality_mode=event["reality_mode"],
            authority_revision=event["authority_revision"],
            runtime_session_id=event["runtime_session_id"],
            authorized_intent_sha256=artifact["authorized_intent_sha256"],
            ap_rule_ids=tuple(event["ap_rule_ids"]),
            ap_rule_required=True,
            canonical_persistence_authorized=False,
            collision_grant=None,
        )
        validation = validate_trixel32d_surface_apply(
            packet,
            built_validation=built_validation,
            authority=authority,
            scene_truth=scene_truth,
        )
        if not validation.accepted:
            detail = validation.errors[0] if validation.errors else "unknown gate rejection"
            raise ValueError(f"record {line_number} fails active application gate: {detail}")
        if authority_record.get("decision_id") != authority.decision_id:
            raise ValueError(f"record {line_number} gate authority identity disagrees")

    def _read_locked_ledger(self) -> bytes:
        self._require_open()
        assert self._ledger_lock_fd is not None
        os.lseek(self._ledger_lock_fd, 0, os.SEEK_SET)
        chunks: list[bytes] = []
        while True:
            chunk = os.read(self._ledger_lock_fd, 65536)
            if not chunk:
                return b"".join(chunks)
            chunks.append(chunk)

    def _load_ledger(self) -> None:
        try:
            raw = self._read_locked_ledger()
            if raw and not raw.endswith(b"\n"):
                raise ValueError("unterminated final ledger record")
            replay_slot_occupancy: dict[tuple[str, str, str, str, str], str] = {}
            for line_number, line in enumerate(raw.splitlines(), start=1):
                event = json.loads(
                    line.decode("utf-8"),
                    object_pairs_hook=_unique_json_object,
                    parse_constant=_reject_nonfinite_json,
                )
                if not isinstance(event, dict):
                    raise ValueError(f"record {line_number} is not an object")
                event_type = event.get("event")
                decision_id = event.get("decision_id")
                apply_id = event.get("apply_id")
                if not isinstance(decision_id, str) or not decision_id:
                    raise ValueError(f"record {line_number} lacks decision_id")
                if not isinstance(apply_id, str) or not apply_id:
                    raise ValueError(f"record {line_number} lacks apply_id")
                if event_type == "authorization_issued":
                    required_keys = {
                        "event",
                        "runtime_session_id",
                        "authority_revision",
                        "actor_id",
                        "actor_authority_tier",
                        "reality_mode",
                        "ap_rule_ids",
                        "decision_id",
                        "apply_id",
                        "scene_id",
                        "scene_revision",
                        "activation_id",
                        "semantic_main_instance_id",
                        "semantic_local_generation",
                        "replacement_mode",
                        "replaces_apply_id",
                        "built_response_b64",
                        "trusted_request",
                        "slot",
                        "artifact_sha256",
                        "artifact",
                    }
                    if set(event) != required_keys:
                        raise ValueError(f"record {line_number} has a noncanonical issuance schema")
                    for name in (
                        "runtime_session_id",
                        "authority_revision",
                        "actor_id",
                        "reality_mode",
                        "scene_id",
                        "scene_revision",
                        "activation_id",
                    ):
                        if not isinstance(event.get(name), str) or not event[name]:
                            raise ValueError(f"record {line_number} lacks {name}")
                    if event["authority_revision"] != self.authority_revision:
                        raise ValueError(f"record {line_number} belongs to a different authority revision")
                    actor_tier = event.get("actor_authority_tier")
                    if isinstance(actor_tier, bool) or not isinstance(actor_tier, int) or actor_tier < 0:
                        raise ValueError(f"record {line_number} has invalid actor authority tier")
                    ap_rule_ids = event.get("ap_rule_ids")
                    if not isinstance(ap_rule_ids, list) or not ap_rule_ids or not all(
                        isinstance(rule_id, str) and rule_id for rule_id in ap_rule_ids
                    ):
                        raise ValueError(f"record {line_number} has invalid AP rule IDs")
                    slot = event.get("slot")
                    if not isinstance(slot, dict) or set(slot) != {
                        "parent_kind",
                        "parent_id",
                        "application_slot_id",
                    }:
                        raise ValueError(f"record {line_number} has invalid slot binding")
                    if not all(isinstance(value, str) and value for value in slot.values()):
                        raise ValueError(f"record {line_number} has empty slot binding")
                    semantic_main = event.get("semantic_main_instance_id")
                    semantic_generation = event.get("semantic_local_generation")
                    if isinstance(semantic_main, bool) or not isinstance(semantic_main, int) or semantic_main <= 0:
                        raise ValueError(f"record {line_number} has invalid Semantic main identity")
                    if (
                        isinstance(semantic_generation, bool)
                        or not isinstance(semantic_generation, int)
                        or semantic_generation < 0
                    ):
                        raise ValueError(f"record {line_number} has invalid Semantic generation")
                    if decision_id in self._decisions or apply_id in self._apply_ids:
                        raise ValueError(f"record {line_number} reuses an identity")
                    artifact = event.get("artifact")
                    if not isinstance(artifact, dict):
                        raise ValueError(f"record {line_number} lacks authorization artifact")
                    artifact_sha256 = event.get("artifact_sha256")
                    if (
                        not isinstance(artifact_sha256, str)
                        or len(artifact_sha256) != 64
                        or any(ch not in "0123456789abcdef" for ch in artifact_sha256)
                        or canonical_authorization_artifact_sha256(artifact) != artifact_sha256
                    ):
                        raise ValueError(f"record {line_number} has invalid authorization artifact hash")
                    self._validate_ledger_artifact_bindings(event, artifact, line_number)
                    packet = artifact["apply_packet"]
                    binding = packet["surface_binding"]
                    encoded_built_response = event.get("built_response_b64")
                    trusted_request = event.get("trusted_request")
                    if not isinstance(encoded_built_response, str) or not isinstance(trusted_request, dict):
                        raise ValueError(f"record {line_number} lacks durable built-response evidence")
                    try:
                        durable_built_bytes = base64.b64decode(
                            encoded_built_response.encode("ascii"), validate=True
                        )
                    except (UnicodeEncodeError, ValueError) as exc:
                        raise ValueError(
                            f"record {line_number} has malformed durable built-response evidence"
                        ) from exc
                    durable_built_validation = validate_trixel32d_surface_built_bytes(
                        durable_built_bytes,
                        trusted_request,
                        expected_response_sha256=binding["built_response_sha256"],
                    )
                    if not durable_built_validation.accepted:
                        detail = (
                            durable_built_validation.errors[0]
                            if durable_built_validation.errors
                            else "unknown build rejection"
                        )
                        raise ValueError(
                            f"record {line_number} durable built response fails validation: {detail}"
                        )
                    target_record = packet["target"]
                    slot_id = target_record["application_slot_id"]
                    replay_slot_key = (
                        event["runtime_session_id"],
                        event["activation_id"],
                        target_record["parent_kind"],
                        target_record["parent_id"],
                        slot_id,
                    )
                    prior_occupant = replay_slot_occupancy.get(replay_slot_key)
                    durable_occupancy = (
                        {slot_id: prior_occupant} if prior_occupant is not None else {}
                    )
                    durable_scene_truth = TrustedSceneTruth(
                        scene_id=event["scene_id"],
                        active_scene_revision=event["scene_revision"],
                        declared_targets=frozenset({(
                            target_record["parent_kind"],
                            target_record["parent_id"],
                            slot_id,
                        )}),
                        slot_occupancy=durable_occupancy,
                    )
                    self._validate_artifact_through_active_gate(
                        event,
                        artifact,
                        durable_built_validation,
                        durable_scene_truth,
                        line_number,
                    )
                    replay_slot_occupancy[replay_slot_key] = apply_id
                    self._decisions[decision_id] = event
                    self._apply_ids.add(apply_id)
                elif event_type == "authorization_consumed":
                    if set(event) != {
                        "event",
                        "runtime_session_id",
                        "decision_id",
                        "apply_id",
                        "artifact_sha256",
                    }:
                        raise ValueError(f"record {line_number} has a noncanonical consumption schema")
                    if not isinstance(event.get("runtime_session_id"), str) or not event["runtime_session_id"]:
                        raise ValueError(f"record {line_number} lacks runtime_session_id")
                    if decision_id not in self._decisions:
                        raise ValueError(f"record {line_number} consumes an unknown decision")
                    issuance = self._decisions[decision_id]
                    if issuance.get("apply_id") != apply_id:
                        raise ValueError(f"record {line_number} consumption binding mismatches")
                    if issuance.get("runtime_session_id") != event.get("runtime_session_id"):
                        raise ValueError(f"record {line_number} consumption session binding mismatches")
                    if issuance.get("artifact_sha256") != event.get("artifact_sha256"):
                        raise ValueError(f"record {line_number} consumption artifact binding mismatches")
                    key = (decision_id, apply_id)
                    if key in self._consumed:
                        raise ValueError(f"record {line_number} repeats consumption")
                    self._consumed.add(key)
                else:
                    raise ValueError(f"record {line_number} has unknown event type")
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            raise AuthorityStateError(f"durable authority ledger is invalid: {exc}") from exc

    def _append_event(self, event: Mapping[str, Any]) -> None:
        self._require_open()
        try:
            payload = json.dumps(
                dict(event),
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            ).encode("utf-8") + b"\n"
            assert self._ledger_lock_fd is not None
            os.lseek(self._ledger_lock_fd, 0, os.SEEK_END)
            written = 0
            while written < len(payload):
                count = os.write(self._ledger_lock_fd, payload[written:])
                if count <= 0:
                    raise OSError("authority ledger write made no progress")
                written += count
            os.fsync(self._ledger_lock_fd)
        except (OSError, TypeError, ValueError) as exc:
            raise AuthorityStateError(f"durable authority ledger append failed: {exc}") from exc
