"""Live EngAInOS routes on the launch_engine scene server (8765).

  POST /trixel32d/build    build, validate and authorize one scene-bound surface
  POST /trixel32d/consume  consume one authorization and return a signed one-time grant

Glue only. Every decision stays in the existing modules:

  local_signed_transport    request authentication + server-owned client policy
  assemble_surface_request  (trixel32d_request_assembler)
  -> dispatch_request_drop  (trixel32d_request_dispatch)
  -> trixel3.2d consume_trixel32d_request_drop.py  (subprocess + file drop)
  -> intake_built_drop      (trixel32d_built_drop_intake)
  -> LiveApplicationIssuer  (authority/trixel32d_live_application_issuer)
  -> write_intake_receipt   (receipt references the ledger entry)
  consume: LiveAuthorityState.consume_authorization -> GrantSigner

Disabled unless TRIXEL32D_LIVE_ROUTE=1. Placement is scene_bound only and
collision is denied only.

8765 is an integration boundary, not an authority of its own:

  caller identity     every request is signed (local_signed_transport) and is
                      verified before the body is parsed. actor_id and tier come
                      only from the server-owned client policy entry for the
                      authenticated client. The body never supplies them.
  reality mode        read from the 8080 runtime's published reality context.
                      Only the trixel32d_surface_apply.v1 modes (DRAFT,
                      FINALIZED, REPLAY) are handled. Any other value is refused.
  observation_source  Godot's presentation testimony: the signed report the
                      policy's single `observe` client made to 8080, read back
                      from 8080's non-consuming /snapshot/peek. It must name
                      the current runtime load (observed_load) and say Godot is
                      actively presenting it. It is testimony, not verified
                      presentation state.

compose_from_environment() is the composition root's single entry. It
returns no authority (route 503), and takes no ledger lock, while the flag is
off, the policy assigns no 8765 role, or it does not assign exactly one
presentation observer.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import threading
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable, Mapping

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tier1.engainos.authority.local_signed_transport import (
    DEFAULT_POLICY_PATH,
    DEFAULT_TRANSPORT_DIR,
    KNOWN_ROUTES,
    ClientAssignment,
    SignedRequestVerifier,
    TransportAuthError,
    compose_verifier,
    load_client_policy,
)
from tier1.engainos.authority.trixel32d_application_grant import GrantSigner
from tier1.engainos.authority.trixel32d_live_application_issuer import (
    LiveApplicationIssuer,
    ProposedApplication,
)
from tier1.engainos.authority.trixel32d_live_authority_state import (
    AuthorityStateError,
    LiveAuthorityState,
    SceneActivation,
    SemanticActivationObservation,
    TargetDeclaration,
    UntrustedPrincipal,
)
from tier1.engainos.bridgeroom.trixel32d_built_drop_intake import (
    PAYLOAD_FILENAME,
    RECEIPT_FILENAME,
    intake_built_drop,
    write_intake_receipt,
)
from tier1.engainos.bridgeroom.trixel32d_request_assembler import (
    ASSEMBLED,
    assemble_surface_request,
)
from tier1.engainos.bridgeroom.trixel32d_request_dispatch import (
    dispatch_request_drop,
)

ROUTES = {"/trixel32d/build": "build", "/trixel32d/consume": "consume"}
SERVER_ROUTES = frozenset(ROUTES.values())
ROUTE_PATH = "/trixel32d/build"
FLAG_ENV = "TRIXEL32D_LIVE_ROUTE"
RUNTIME_URL_ENV = "TRIXEL32D_RUNTIME_URL"
DEFAULT_RUNTIME_URL = "http://127.0.0.1:8080"
AUTHORITY_REVISION = "trixel32d-live-route-v1"
# trixel32d_surface_apply.v1 §7 defines handling for these runtime reality modes only.
SUPPORTED_REALITY_MODES = frozenset({"DRAFT", "FINALIZED", "REPLAY"})

RUNTIME_DIR = REPO_ROOT / "runtime"
LEDGER_PATH = RUNTIME_DIR / "trixel32d_live_authority" / "live_authority_ledger.jsonl"
TRANSPORT_DIR = DEFAULT_TRANSPORT_DIR
SERVER_NAME = "8765"  # this server's credential subdirectory under TRANSPORT_DIR
GRANT_PUBLIC_KEY_FILENAME = "trixel32d_grant_public_key.pem"
POLICY_PATH = DEFAULT_POLICY_PATH
SCENE_TRUTH_PATH = REPO_ROOT / "tier1" / "engainos" / "authority" / "TRIXEL32D_SCENE_TRUTH_V1.json"
AUTHORIZATION_FILENAME = "TRIXEL32D_LIVE_APPLICATION_AUTHORIZATION.json"
TRIXEL_TOOL = REPO_ROOT.parent / "trixel3.2d" / "tools" / "consume_trixel32d_request_drop.py"
TRIXEL_TIMEOUT_S = 120

_HEX64 = re.compile(r"^[0-9a-f]{64}$")

LoadIdentity = tuple[str, int, str]
# Returns Godot's latest testimony as reported to the runtime:
#   {"observed_load": {"runtime_instance_id": str, "load_seq": int, "scene_id": str},
#    "main_instance_id": int, "local_generation": int}
# It takes no argument on purpose: the source reports what Godot saw, not what the server expects.
ObservationSource = Callable[[], Mapping[str, Any]]


class RouteError(Exception):
    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.message = message


class LiveRouteAuthority:
    """Process-wide trusted state for the routes. Holds every privileged capability.

    Owns the ledger flock for its lifetime: one per process, built once by
    compose_from_environment(). Every input is required; there is no partially
    composed authority.
    """

    def __init__(
        self,
        ledger_path: Path,
        *,
        verifier: SignedRequestVerifier,
        client_policy: Mapping[str, ClientAssignment],
        observation_source: ObservationSource,
        grant_signer: GrantSigner,
    ) -> None:
        if verifier is None or not client_policy or observation_source is None or grant_signer is None:
            raise ValueError("live route authority requires verifier, client policy, observation source and grant signer")
        self._capabilities = tuple(object() for _ in range(4))
        self._state = LiveAuthorityState(
            ledger_path,
            AUTHORITY_REVISION,
            principal_registration_capability=self._capabilities[0],
            trusted_state_mutation_capability=self._capabilities[1],
            authorization_commit_capability=self._capabilities[2],
            decision_consumption_capability=self._capabilities[3],
        )
        self._issuer = LiveApplicationIssuer(self._state, commit_capability=self._capabilities[2])
        self._verifier = verifier
        self._policy = dict(client_policy)
        self._observation_source = observation_source
        self._grant_signer = grant_signer
        self._principals: dict[tuple[str, int, str], UntrustedPrincipal] = {}
        self._lock = threading.Lock()
        self._load_identity: LoadIdentity | None = None

    @property
    def runtime_session_id(self) -> str:
        return self._state.runtime_session_id

    @property
    def grant_public_key_pem(self) -> str:
        return self._grant_signer.public_key_pem

    def close(self) -> None:
        self._state.close()

    def authenticate(self, method: str, path: str, headers: Mapping[str, str], body: bytes,
                     route: str) -> tuple[str, ClientAssignment]:
        client_id = self._verifier.verify(method, path, headers, body)
        assignment = self._policy.get(client_id)
        if assignment is None or route not in assignment.routes:
            raise RouteError(403, f"client '{client_id}' is not assigned the '{route}' route")
        return client_id, assignment

    def principal_for(self, assignment: ClientAssignment, reality_mode: str) -> UntrustedPrincipal:
        if assignment.actor_id is None or assignment.actor_authority_tier is None:
            raise AuthorityStateError("client holds no actor assignment")
        key = (assignment.actor_id, assignment.actor_authority_tier, reality_mode)
        with self._lock:
            principal = self._principals.get(key)
            if principal is None:
                principal = self._state.register_trusted_principal(*key, capability=self._capabilities[0])
                self._principals[key] = principal
            return principal

    def sync_activation(
        self, scene: dict[str, Any], load_identity: LoadIdentity, scene_truth: Mapping[str, Any]
    ) -> SceneActivation:
        """Activate only when the runtime's load identity changed; return the current activation."""
        mutate = self._capabilities[1]
        with self._lock:
            if load_identity != self._load_identity:
                # A new runtime load is a new activation: occupancy restarts with it.
                activation = self._state.activate_scene(scene, capability=mutate)
                for parent_kind, parent_id, application_slot_id in scene_truth.get("declared_targets") or []:
                    self._state.declare_target(
                        activation.scene_id,
                        activation.scene_revision,
                        TargetDeclaration(parent_kind, parent_id, application_slot_id),
                        capability=mutate,
                    )
                self._load_identity = load_identity
            return self._current_activation()

    def _record_testimony(self, activation: SceneActivation) -> SemanticActivationObservation:
        """Read Godot's testimony, require it to name the current load, and record it. Caller holds the lock."""
        if self._current_activation() != activation:
            raise RouteError(409, "runtime scene activation changed during the request; retry")
        reported = self._observation_source()
        observed_load, main_instance_id, local_generation = _parse_testimony(reported)
        if observed_load != self._load_identity:
            # Testimony about another load (older, newer, or another runtime) never
            # stands in for the current activation.
            raise RouteError(409, "Godot observation names a different runtime scene load; stale or mismatched")
        observation = SemanticActivationObservation(
            runtime_session_id=self._state.runtime_session_id,
            activation_id=activation.activation_id,
            scene_id=activation.scene_id,
            scene_revision=activation.scene_revision,
            semantic_main_instance_id=main_instance_id,
            semantic_local_generation=local_generation,
        )
        if observation != self._state.current_observation:
            self._state.observe_semantic_activation(observation, capability=self._capabilities[1])
        return observation

    def authorize(
        self,
        *,
        activation: SceneActivation,
        proposal: Callable[[SemanticActivationObservation], ProposedApplication],
        built_response_bytes: bytes,
        trusted_request: Mapping[str, Any],
        principal: UntrustedPrincipal,
    ) -> Any:
        """Record the testimony for `activation`, then issue. Returns the IssuanceResult."""
        with self._lock:
            observation = self._record_testimony(activation)
            return self._issuer.issue(
                proposal(observation),
                built_response_bytes=built_response_bytes,
                trusted_request=trusted_request,
                principal=principal,
            )

    def consume(
        self,
        *,
        activation: SceneActivation,
        client_id: str,
        decision_id: str,
        apply_id: str,
        artifact_sha256: str,
        caller_testimony: tuple[LoadIdentity, int, int],
        reality_mode: str,
    ) -> dict[str, str]:
        """Atomically validate and consume one authorization; return its signed one-time grant."""
        with self._lock:
            observation = self._record_testimony(activation)
            reported = (self._load_identity, observation.semantic_main_instance_id,
                        observation.semantic_local_generation)
            if caller_testimony != reported:
                raise RouteError(409, "consumer's presentation testimony disagrees with the reported Godot observation")
            decision = self._state.issued_decision(decision_id)
            if decision is not None and decision.get("reality_mode") != reality_mode:
                raise RouteError(409, "runtime reality mode changed since the authorization was issued")
            runtime_instance_id, load_seq, scene_id = self._load_identity
            # Signed before consumption so a signing failure consumes nothing; if
            # consumption is then refused, the grant is discarded unseen.
            grant = self._grant_signer.mint({
                "client_id": client_id,
                "decision_id": decision_id,
                "apply_id": apply_id,
                "artifact_sha256": artifact_sha256,
                "runtime_session_id": self._state.runtime_session_id,
                "activation_id": activation.activation_id,
                "scene_id": activation.scene_id,
                "scene_revision": activation.scene_revision,
                "observed_load": {"runtime_instance_id": runtime_instance_id, "load_seq": load_seq,
                                  "scene_id": scene_id},
                "semantic_main_instance_id": observation.semantic_main_instance_id,
                "semantic_local_generation": observation.semantic_local_generation,
            })
            self._state.consume_authorization(
                decision_id, apply_id, applied_artifact_sha256=artifact_sha256,
                capability=self._capabilities[3],
            )
            return grant

    def _current_activation(self) -> SceneActivation:
        activation = self._state.current_activation
        if activation is None:
            raise AuthorityStateError("server-owned scene activation is missing")
        return activation


def enabled() -> bool:
    return os.environ.get(FLAG_ENV) == "1"


def compose_from_environment(
    *,
    observation_source: ObservationSource | None = None,
    ledger_path: Path | None = None,
    policy_path: Path | None = None,
    transport_dir: Path | None = None,
) -> tuple[LiveRouteAuthority | None, str]:
    """Build the process authority, or return (None, reason) without touching the ledger.

    Every refusal is decided before the ledger lock, credentials or keys exist.
    `observation_source` overrides the policy-derived one (tests only).
    """
    if not enabled():
        return None, f"{FLAG_ENV} is not '1'"
    try:
        policy = load_client_policy(policy_path or POLICY_PATH, KNOWN_ROUTES)
    except (OSError, ValueError) as exc:
        return None, f"client policy is invalid: {exc}"
    if not any(a.routes & SERVER_ROUTES for a in policy.values()):
        return None, "client policy has no client assignments for 8765 (deny-all)"
    if observation_source is None:
        observers = sorted(cid for cid, a in policy.items() if "observe" in a.routes)
        if len(observers) != 1:
            return None, f"B3: client policy must assign exactly one presentation observer (found {len(observers)})"
        observation_source = runtime_observation_source(observers[0])
    try:
        signer = GrantSigner()
    except AuthorityStateError as exc:
        return None, str(exc)
    directory = (transport_dir or TRANSPORT_DIR) / SERVER_NAME
    verifier, clients = compose_verifier(policy, SERVER_ROUTES, directory)
    (directory / GRANT_PUBLIC_KEY_FILENAME).write_text(signer.public_key_pem, encoding="ascii")
    authority = LiveRouteAuthority(
        ledger_path or LEDGER_PATH,
        verifier=verifier,
        client_policy=clients,
        observation_source=observation_source,
        grant_signer=signer,
    )
    return authority, "composed"


def runtime_observation_source(observer_client_id: str) -> ObservationSource:
    """Godot's latest authenticated report, as retained by 8080, read without consuming anything."""
    def read() -> Mapping[str, Any] | None:
        envelope = _get_runtime_peek()
        records = envelope.get("presentation_observations") if isinstance(envelope, dict) else None
        record = records.get(observer_client_id) if isinstance(records, dict) else None
        if not isinstance(record, dict) or record.get("client_id") != observer_client_id:
            raise RouteError(409, "no presentation observation has been reported by the configured observer")
        return record
    return read


def handle_http(method: str, path: str, headers: Mapping[str, str], body: bytes,
                authority: LiveRouteAuthority | None) -> tuple[int, dict[str, Any]]:
    """Return (http_status, json_body). Authentication precedes parsing and every side effect."""
    try:
        route = ROUTES.get(path)
        if route is None:
            raise RouteError(404, "unknown trixel32d route")
        if authority is None:
            raise RouteError(503, "live route authority was not composed at server start")
        client_id, assignment = authority.authenticate(method, path, headers, body, route)
        parsed = _parse_body(body)
        if route == "build":
            return 200, _build(parsed, authority, assignment)
        return 200, _consume(parsed, authority, client_id)
    except TransportAuthError as exc:
        return exc.status, {"status": "REJECTED", "errors": [exc.message]}
    except RouteError as exc:
        return exc.status, {"status": "REJECTED", "errors": [exc.message]}


def _parse_body(body: bytes) -> dict[str, Any]:
    try:
        parsed = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RouteError(400, f"body is not JSON: {type(exc).__name__}") from exc
    return _require_dict(parsed, "body")


def _require_dict(node: Any, where: str) -> dict[str, Any]:
    if not isinstance(node, dict):
        raise RouteError(400, f"{where} must be a JSON object")
    return node


def _load_json_file(path: Path, what: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RouteError(503, f"{what} unavailable at {path}: {type(exc).__name__}") from exc


def _parse_load_identity(stamp: Any) -> LoadIdentity:
    """Validate one runtime load stamp {runtime_instance_id, load_seq, scene_id}."""
    if not isinstance(stamp, Mapping):
        raise RouteError(409, "runtime snapshot has no scene load identity")
    identity = (stamp.get("runtime_instance_id"), stamp.get("load_seq"), stamp.get("scene_id"))
    if not isinstance(identity[0], str) or not identity[0] or isinstance(identity[1], bool) \
            or not isinstance(identity[1], int) or identity[1] < 1 \
            or not isinstance(identity[2], str) or not identity[2]:
        raise RouteError(409, "runtime scene load identity is malformed")
    return identity


def _parse_testimony(reported: Any) -> tuple[LoadIdentity, Any, Any]:
    if not isinstance(reported, Mapping):
        raise RouteError(409, "Godot observation is malformed")
    if reported.get("presentation_active") is not True:
        raise RouteError(409, "Godot observation does not report active presentation of its load")
    try:
        observed_load = _parse_load_identity(reported.get("observed_load"))
    except RouteError as exc:
        raise RouteError(409, f"Godot observation: {exc.message}") from exc
    # Integer validity is enforced by LiveAuthorityState.observe_semantic_activation.
    return observed_load, reported.get("main_instance_id"), reported.get("local_generation")


def _runtime_reality_mode(context: Any, scene_id: str) -> str:
    """The runtime's published reality mode, refused unless the apply contract defines its handling."""
    if not isinstance(context, Mapping) or not isinstance(context.get("mode"), str):
        raise RouteError(409, "runtime reality mode is not published")
    if context.get("scene_id") is not None and context.get("scene_id") != scene_id:
        raise RouteError(409, f"runtime reality context is scoped to '{context.get('scene_id')}', not the active scene")
    mode = context["mode"]
    if mode not in SUPPORTED_REALITY_MODES:
        raise RouteError(
            409,
            f"runtime reality mode '{mode}' has no defined handling in trixel32d_surface_apply.v1 "
            f"(defines {', '.join(sorted(SUPPORTED_REALITY_MODES))}); refusing",
        )
    return mode


def _get_runtime_peek() -> Any:
    base = os.environ.get(RUNTIME_URL_ENV, DEFAULT_RUNTIME_URL).rstrip("/")
    url = base + "/snapshot/peek"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return json.loads(resp.read() or b"{}")
    except (urllib.error.URLError, OSError, json.JSONDecodeError) as exc:
        raise RouteError(502, f"runtime snapshot unavailable at {url}: {exc}") from exc


def _fetch_runtime_scene() -> tuple[dict[str, Any], LoadIdentity, Any]:
    """Read the active scene, its load identity and reality context without consuming runtime events."""
    envelope = _get_runtime_peek()
    payload = envelope.get("payload", envelope) if isinstance(envelope, dict) else None
    scene = payload.get("scene") if isinstance(payload, dict) else None
    if not isinstance(scene, dict) or not scene:
        raise RouteError(409, "runtime snapshot has no active scene")
    identity = _parse_load_identity(payload.get("scene_activation"))
    # The scene, its id and its load stamp must all name the same activation.
    scene_id = scene.get("scene_id") or scene.get("@id")
    if not scene_id or identity[2] != scene_id or payload.get("scene_id") != scene_id:
        raise RouteError(409, "runtime scene and its load identity disagree")
    # Published at envelope level by 8080 (outside the checksummed payload).
    return scene, identity, envelope.get("reality_context")


def _current_runtime(authority: LiveRouteAuthority) -> tuple[SceneActivation, str, dict[str, Any]]:
    """Sync the activation to the runtime's current load; return it with the reality mode and scene truth."""
    scene, load_identity, reality_context = _fetch_runtime_scene()
    scene_id = scene.get("scene_id") or scene.get("@id")
    reality_mode = _runtime_reality_mode(reality_context, scene_id)
    scene_truth = _load_json_file(SCENE_TRUTH_PATH, "scene truth")
    if not isinstance(scene_truth, dict) or scene_truth.get("scene_id") != scene_id:
        raise RouteError(409, f"no authority-owned target declarations for active scene '{scene_id}'")
    try:
        activation = authority.sync_activation(scene, load_identity, scene_truth)
    except AuthorityStateError as exc:
        raise RouteError(403, str(exc)) from exc
    return activation, reality_mode, scene_truth


def _build(body: dict[str, Any], authority: LiveRouteAuthority, assignment: ClientAssignment) -> dict[str, Any]:
    placement = _require_dict(body.get("placement"), "placement")
    collision = _require_dict(body.get("collision"), "collision")
    if placement.get("mode") != "scene_bound":
        raise RouteError(403, "placement.mode must be exactly 'scene_bound'")
    if collision.get("mode") != "denied":
        raise RouteError(403, "collision.mode must be exactly 'denied'")
    surface = _require_dict(body.get("surface"), "surface")

    activation, reality_mode, scene_truth = _current_runtime(authority)
    target = TargetDeclaration(
        placement.get("parent_kind"), placement.get("parent_id"), placement.get("application_slot_id")
    )
    # Occupancy declared by scene truth exists outside this ledger; honor it here.
    if target.application_slot_id in (scene_truth.get("slot_occupancy") or {}):
        raise RouteError(409, f"application slot '{target.application_slot_id}' is declared occupied")

    status, request, reasons = assemble_surface_request(
        surface.get("grid_facts"),
        surface.get("metric_grant"),
        surface.get("provenance"),
        surface.get("construction_policy"),
    )
    if status != ASSEMBLED:
        raise RouteError(400, f"request assembly rejected: {'; '.join(reasons)}")
    try:
        principal = authority.principal_for(assignment, reality_mode)
    except AuthorityStateError as exc:
        raise RouteError(403, str(exc)) from exc

    request_id = request["identity"]["request_id"]
    request_bytes = json.dumps(request, sort_keys=True, separators=(",", ":")).encode("utf-8")
    # Pending work belongs to one session and activation; a reload or restart gets a fresh slot.
    slot_key = f"{authority.runtime_session_id}\n{activation.activation_id}\n".encode("utf-8") + request_bytes
    slot_id = "t32ddrop_" + hashlib.sha256(slot_key).hexdigest()[:16]
    request_dir = RUNTIME_DIR / "trixel32d_requests" / slot_id
    response_dir = RUNTIME_DIR / "trixel32d_built_drops" / slot_id
    report_dir = RUNTIME_DIR / "trixel32d_reports" / slot_id
    receipt_path = report_dir / RECEIPT_FILENAME
    authorization_path = report_dir / AUTHORIZATION_FILENAME
    built_drop_ref = str(response_dir.relative_to(RUNTIME_DIR.parent))

    dispatch = dispatch_request_drop(request_dir, request_bytes, generated_by="engainos")
    if not dispatch.dispatched:
        raise RouteError(409, f"request dispatch rejected: {dispatch.errors[0]}")

    try:
        consumer = subprocess.run(
            [sys.executable, str(TRIXEL_TOOL), str(request_dir), str(response_dir), request_id],
            cwd=TRIXEL_TOOL.parents[1],
            capture_output=True,
            text=True,
            timeout=TRIXEL_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired as exc:
        raise RouteError(502, f"trixel consumer timed out after {TRIXEL_TIMEOUT_S}s") from exc
    except OSError as exc:
        raise RouteError(502, f"trixel consumer could not start: {exc}") from exc
    try:
        consumer_result = json.loads(consumer.stdout.strip())
    except json.JSONDecodeError as exc:
        raise RouteError(502, f"trixel consumer output is not JSON (exit {consumer.returncode})") from exc
    if consumer.returncode != 0 or not isinstance(consumer_result, dict):
        raise RouteError(422, f"trixel consumer rejected the request: {consumer_result}")

    # The consumer's claimed checksum is only a lookup key; intake re-hashes the bytes
    # and validates them against the request EngAInOS assembled.
    intake = intake_built_drop(
        response_dir,
        trusted_request=request,
        expected_payload_sha256=consumer_result.get("response_sha256"),
        expected_topology_policy=request["construction"]["topology_policy"],
        receipt_path=receipt_path,
    )
    if not intake.accepted:
        raise RouteError(422, f"built drop intake rejected: {intake.errors[0]}")
    # Re-read is safe: the issuer re-hashes these bytes against the intake checksum.
    built_bytes = (response_dir / PAYLOAD_FILENAME).read_bytes()
    built_sha256 = intake.receipt["payload_sha256"]

    def proposal(observation: SemanticActivationObservation) -> ProposedApplication:
        return ProposedApplication(
            request_id=request_id,
            surface_id=intake.receipt["surface_id"],
            built_response_sha256=built_sha256,
            parent_kind=target.parent_kind,
            parent_id=target.parent_id,
            application_slot_id=target.application_slot_id,
            basis_columns=placement.get("basis_columns"),
            origin=placement.get("origin"),
            visibility_intent=placement.get("visibility"),
            replacement_mode="CREATE_ONLY",
            replaces_apply_id=None,
            lifetime_mode="SCENE_BOUND",
            classification="PRESENTATION_ONLY",
            collision_decision="DENIED",
            # Set only after authorize() matched Godot's observed_load to this activation's load.
            observed_activation_id=observation.activation_id,
            semantic_main_instance_id=observation.semantic_main_instance_id,
            semantic_local_generation=observation.semantic_local_generation,
        )

    try:
        issuance = authority.authorize(
            activation=activation,
            proposal=proposal,
            built_response_bytes=built_bytes,
            trusted_request=request,
            principal=principal,
        )
    except AuthorityStateError as exc:
        raise RouteError(403, str(exc)) from exc
    if not issuance.authorized:
        raise RouteError(403, f"application issuance rejected: {issuance.errors[0]}")

    evidence = issuance.artifact["authority_evidence"]
    ledger_entry = {
        "decision_id": evidence["decision_id"],
        "apply_id": issuance.artifact["apply_packet"]["apply_id"],
        "artifact_sha256": issuance.artifact_sha256,
        "runtime_session_id": evidence["runtime_session_id"],
    }
    artifact = json.loads(json.dumps(issuance.artifact, default=_thaw))
    try:
        # The executor locks on these exact bytes: the ledger's canonical serialization.
        artifact_bytes = json.dumps(artifact, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
        if hashlib.sha256(artifact_bytes).hexdigest() != issuance.artifact_sha256:
            raise ValueError("authorization file bytes do not reproduce the ledger artifact hash")
        report_dir.mkdir(parents=True, exist_ok=True)
        with open(authorization_path, "xb") as handle:
            handle.write(artifact_bytes)
        write_intake_receipt(receipt_path, intake, ledger_entry=ledger_entry)
    except (OSError, ValueError) as exc:
        # The ledger entry is the authorization; it stands and keeps the slot occupied,
        # so a retry cannot be issued a second one. Say so instead of failing anonymously.
        raise RouteError(
            500,
            f"authorization {ledger_entry['decision_id']} is recorded in the authority ledger "
            f"but its evidence files were not written: {type(exc).__name__}: {exc}",
        ) from exc
    return {
        "status": "AUTHORIZED",
        "request_id": request_id,
        "surface_id": intake.receipt["surface_id"],
        "built_response_sha256": built_sha256,
        "built_drop_dir": built_drop_ref,
        "authorization_file": str(authorization_path.relative_to(RUNTIME_DIR.parent)),
        "authorization_sha256": issuance.artifact_sha256,
        "ledger_entry": ledger_entry,
        "authorization": artifact,
    }


def _consume(body: dict[str, Any], authority: LiveRouteAuthority, client_id: str) -> dict[str, Any]:
    decision_id, apply_id = body.get("decision_id"), body.get("apply_id")
    artifact_sha256 = body.get("artifact_sha256")
    if not isinstance(decision_id, str) or not decision_id or not isinstance(apply_id, str) or not apply_id:
        raise RouteError(400, "decision_id and apply_id must be non-empty strings")
    if not isinstance(artifact_sha256, str) or not _HEX64.fullmatch(artifact_sha256):
        raise RouteError(400, "artifact_sha256 must be 64 lowercase hexadecimal characters")
    caller_load, main_instance_id, local_generation = _parse_testimony(body)

    activation, reality_mode, _scene_truth = _current_runtime(authority)
    try:
        grant = authority.consume(
            activation=activation,
            client_id=client_id,
            decision_id=decision_id,
            apply_id=apply_id,
            artifact_sha256=artifact_sha256,
            caller_testimony=(caller_load, main_instance_id, local_generation),
            reality_mode=reality_mode,
        )
    except AuthorityStateError as exc:
        raise RouteError(403, str(exc)) from exc
    return {"status": "GRANTED", **grant}


def _thaw(value: Any) -> Any:
    # Issuer returns MappingProxyType/tuple-frozen JSON; serialize it back as plain JSON.
    if hasattr(value, "items"):
        return dict(value)
    raise TypeError(f"not JSON serializable: {type(value).__name__}")
