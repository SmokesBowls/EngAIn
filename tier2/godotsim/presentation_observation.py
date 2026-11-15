"""Signed Godot presentation-observation intake for the 8080 runtime.

POST /presentation/observation (feature-flagged with TRIXEL32D_LIVE_ROUTE)

Uses the same signed-request contract and client policy as 8765
(tier1.engainos.authority.local_signed_transport), with this server's own
credentials, for clients holding the `observe` role. No second auth system.

What is retained is **authenticated client testimony**: the reporting client
says which runtime load it received and that it is presenting it. Nothing here
verifies the scene tree. The runtime keeps the latest accepted report per
client, in memory (a runtime restart forgets them all, along with the
runtime_instance_id they named), and publishes them through the
non-consuming GET /snapshot/peek envelope as `presentation_observations`.

Body (exact keys):
  observed_load        {runtime_instance_id: str, load_seq: int >= 1, scene_id: str}
                       must be this runtime's current load stamp
  main_instance_id     int > 0   Godot Main instance (changes when Godot restarts)
  local_generation     int >= 0  Godot presentation generation
  presentation_active  bool      Godot is (not) presenting observed_load right now
  report_seq           int >= 1  per-Godot-process report counter

Ordering: for one client and one main_instance_id, report_seq must increase
and local_generation may not decrease. A delayed or replayed report is
therefore refused even when its transport nonce is fresh. A report naming any
load other than the current one (older, newer, another runtime) is refused.
"""

from __future__ import annotations

import copy
import json
import os
import threading
from pathlib import Path
from typing import Any, Mapping

from tier1.engainos.authority.local_signed_transport import (
    DEFAULT_POLICY_PATH,
    DEFAULT_TRANSPORT_DIR,
    HEADER_NONCE,
    HEADER_TIMESTAMP,
    SignedRequestVerifier,
    TransportAuthError,
    compose_verifier,
    load_client_policy,
)

OBSERVATION_PATH = "/presentation/observation"
FLAG_ENV = "TRIXEL32D_LIVE_ROUTE"
SERVER_NAME = "8080"
SERVER_ROUTES = frozenset({"observe"})
TESTIMONY = "AUTHENTICATED_CLIENT_TESTIMONY"
_BODY_KEYS = frozenset({"observed_load", "main_instance_id", "local_generation", "presentation_active", "report_seq"})
_LOAD_KEYS = frozenset({"runtime_instance_id", "load_seq", "scene_id"})


class ObservationRejected(Exception):
    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.message = message


def _int(value: Any, minimum: int) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= minimum


class PresentationObservationIntake:
    def __init__(self, verifier: SignedRequestVerifier, observers: frozenset[str]) -> None:
        if verifier is None or not observers:
            raise ValueError("observation intake requires a verifier and at least one observer")
        self._verifier = verifier
        self._observers = frozenset(observers)
        self._records: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()

    def handle(self, runtime: Any, headers: Mapping[str, str], body: bytes) -> tuple[int, dict[str, Any]]:
        """Authenticate, then validate against the runtime's current load, then retain."""
        try:
            client_id = self._verifier.verify("POST", OBSERVATION_PATH, headers, body)
            if client_id not in self._observers:
                raise ObservationRejected(403, f"client '{client_id}' is not assigned the 'observe' route")
            report = self._parse(body)
            with self._lock:
                stamp = runtime.snapshot.get("scene_activation") if isinstance(runtime.snapshot, dict) else None
                current = (stamp.get("runtime_instance_id"), stamp.get("load_seq"), stamp.get("scene_id")) \
                    if isinstance(stamp, dict) else None
                if current is None or current[0] != runtime.runtime_instance_id:
                    raise ObservationRejected(409, "runtime has no current scene load")
                observed = report["observed_load"]
                if (observed["runtime_instance_id"], observed["load_seq"], observed["scene_id"]) != current:
                    raise ObservationRejected(409, "observation names a load that is not the runtime's current load")
                previous = self._records.get(client_id)
                if previous is not None and previous["main_instance_id"] == report["main_instance_id"]:
                    if report["report_seq"] <= previous["report_seq"]:
                        raise ObservationRejected(409, "observation is out of order or replayed (report_seq)")
                    if previous["observed_load"] == observed and report["local_generation"] < previous["local_generation"]:
                        raise ObservationRejected(409, "observation regresses the presentation generation")
                record = {
                    **report,
                    "client_id": client_id,
                    "transport_nonce": headers.get(HEADER_NONCE),
                    "transport_timestamp": int(headers.get(HEADER_TIMESTAMP)),
                    "testimony": TESTIMONY,
                }
                self._records[client_id] = record
            return 200, {"status": "RETAINED", "observation": copy.deepcopy(record)}
        except TransportAuthError as exc:
            return exc.status, {"status": "REJECTED", "errors": [exc.message]}
        except ObservationRejected as exc:
            return exc.status, {"status": "REJECTED", "errors": [exc.message]}

    def published(self) -> dict[str, dict[str, Any]]:
        with self._lock:
            return copy.deepcopy(self._records)

    @staticmethod
    def _parse(body: bytes) -> dict[str, Any]:
        try:
            report = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ObservationRejected(400, f"observation is not JSON: {type(exc).__name__}") from exc
        if not isinstance(report, dict) or set(report) != _BODY_KEYS:
            raise ObservationRejected(400, f"observation must have exactly {sorted(_BODY_KEYS)}")
        load = report["observed_load"]
        if not isinstance(load, dict) or set(load) != _LOAD_KEYS \
                or not isinstance(load["runtime_instance_id"], str) or not load["runtime_instance_id"] \
                or not _int(load["load_seq"], 1) or not isinstance(load["scene_id"], str) or not load["scene_id"]:
            raise ObservationRejected(400, "observed_load is malformed")
        if not _int(report["main_instance_id"], 1) or not _int(report["local_generation"], 0) \
                or not _int(report["report_seq"], 1) or not isinstance(report["presentation_active"], bool):
            raise ObservationRejected(400, "observation fields have invalid types")
        return report


def compose_from_environment(
    *, policy_path: Path | None = None, transport_dir: Path | None = None,
) -> tuple[PresentationObservationIntake | None, str]:
    """Build the intake, or (None, reason) with no credentials written."""
    if os.environ.get(FLAG_ENV) != "1":
        return None, f"{FLAG_ENV} is not '1'"
    try:
        policy = load_client_policy(policy_path or DEFAULT_POLICY_PATH)
    except (OSError, ValueError) as exc:
        return None, f"client policy is invalid: {exc}"
    if not any(a.routes & SERVER_ROUTES for a in policy.values()):
        return None, "client policy assigns no presentation observer (deny-all)"
    verifier, observers = compose_verifier(policy, SERVER_ROUTES, (transport_dir or DEFAULT_TRANSPORT_DIR) / SERVER_NAME)
    return PresentationObservationIntake(verifier, frozenset(observers)), "composed"
