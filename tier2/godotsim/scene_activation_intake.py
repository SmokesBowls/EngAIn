"""Signed scene-activation intake for the 8080 runtime.

POST /scene/activate (feature-flagged with ENGAIN_SCENE_ACTIVATION_AUTH=1)

Same signed-request contract as /presentation/observation
(tier1.engainos.authority.local_signed_transport), with this route's own
vocabulary {"activate"}, client policy file and credential directory —
the editor-route pattern. No second auth system.

What a client may NOT send: an actor id, an authority tier or a reality
mode. The body has exactly two keys; anything else is refused. The
`activate` role is route-only (load_client_policy refuses an actor or tier
on a non-actor role), so holding it proves which binding sent the bytes and
nothing about actor authority.

Who decides:
  - the runtime's own published reality mode (aproom.reality_mode.get_context):
    DRAFT permits a candidate activation; REPLAY refuses; every other mode
    refuses because no contract defines activation there (fail closed);
  - canon: a FINALIZED scene is refused here outright (no tier on this path);
  - SceneManager's activation stamp (T03-R3): stale or missing preconditions
    are refused by the manager itself.

Activation here is DRAFT runtime activation, never canonical acceptance.

Body (exact keys):
  scene                       the candidate scene document (from 8765 /load_scene)
  expected_scene_activation   the stamp the client last observed, or null for an
                              empty runtime
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping

from tier1.engainos.authority.local_signed_transport import (
    DEFAULT_TRANSPORT_DIR,
    SignedRequestVerifier,
    TransportAuthError,
    compose_verifier,
    load_client_policy,
)

ACTIVATION_PATH = "/scene/activate"
FLAG_ENV = "ENGAIN_SCENE_ACTIVATION_AUTH"
POLICY_ENV = "ENGAIN_SCENE_ACTIVATION_POLICY"
SERVER_NAME = "8080_activation"
ACTIVATION_ROUTES = frozenset({"activate"})
DEFAULT_POLICY_PATH = (
    Path(__file__).resolve().parents[2] / "tier1" / "engainos" / "authority"
    / "SCENE_ACTIVATION_CLIENT_POLICY_V1.json"
)
_BODY_KEYS = frozenset({"scene", "expected_scene_activation"})


class ActivationRejected(Exception):
    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.message = message


def runtime_mode_permits_activation() -> None:
    """Raise ActivationRejected unless the runtime's actual mode is DRAFT."""
    from tier1.engainos.aproom.reality_mode import RealityMode, get_context
    mode = get_context().mode
    if mode is RealityMode.DRAFT:
        return
    if mode is RealityMode.REPLAY:
        raise ActivationRejected(403, "runtime is in REPLAY; scene activation is blocked")
    raise ActivationRejected(
        403, f"runtime mode {mode.value} has no defined scene-activation policy; refusing (fail closed)")


class SceneActivationIntake:
    def __init__(self, verifier: SignedRequestVerifier, activators: frozenset[str]) -> None:
        if verifier is None or not activators:
            raise ValueError("activation intake requires a verifier and at least one activator")
        self._verifier = verifier
        self._activators = frozenset(activators)

    def authenticate(self, headers: Mapping[str, str], body: bytes) -> tuple[str, dict[str, Any], Any]:
        """Verify the signature and role, then parse. Returns (client_id, scene, expected)."""
        client_id = self._verifier.verify("POST", ACTIVATION_PATH, headers, body)
        if client_id not in self._activators:
            raise ActivationRejected(403, f"client '{client_id}' is not assigned the 'activate' route")
        try:
            parsed = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ActivationRejected(400, f"activation is not JSON: {type(exc).__name__}") from exc
        if not isinstance(parsed, dict) or set(parsed) != _BODY_KEYS:
            raise ActivationRejected(
                400, f"activation must have exactly {sorted(_BODY_KEYS)}; actor, tier and mode are not client-declared")
        if not isinstance(parsed["scene"], dict) or not parsed["scene"]:
            raise ActivationRejected(400, "scene must be a non-empty object")
        return client_id, parsed["scene"], parsed["expected_scene_activation"]


def compose_from_environment(
    *, policy_path: Path | None = None, transport_dir: Path | None = None,
) -> tuple[SceneActivationIntake | None, str]:
    """Build the intake, or (None, reason) with no credentials written."""
    if os.environ.get(FLAG_ENV) != "1":
        return None, f"{FLAG_ENV} is not '1'"
    path = policy_path or Path(os.environ.get(POLICY_ENV) or DEFAULT_POLICY_PATH)
    try:
        policy = load_client_policy(path, known_routes=ACTIVATION_ROUTES)
    except (OSError, ValueError) as exc:
        return None, f"activation client policy is invalid: {exc}"
    if not any(a.routes & ACTIVATION_ROUTES for a in policy.values()):
        return None, "activation client policy assigns no activator (deny-all)"
    verifier, activators = compose_verifier(
        policy, ACTIVATION_ROUTES, (transport_dir or DEFAULT_TRANSPORT_DIR) / SERVER_NAME)
    return SceneActivationIntake(verifier, frozenset(activators)), "composed"


__all__ = [
    "ACTIVATION_PATH", "ActivationRejected", "SceneActivationIntake", "TransportAuthError",
    "compose_from_environment", "runtime_mode_permits_activation",
]
