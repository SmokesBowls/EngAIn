# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/godotsim/gates/gate_runtime_core_dry_scene_load.py

from __future__ import annotations

import contextlib
import importlib
import io
import socket
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any

REPO_ROOT = Path("/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn")
RUNTIME_DIR = REPO_ROOT / "godotsim/godotsim_legacy"
RUNTIME_SOURCE = RUNTIME_DIR / "runtime_core.py"

for import_path in (REPO_ROOT, RUNTIME_DIR):
    if str(import_path) not in sys.path:
        sys.path.insert(0, str(import_path))

GATE_LIFECYCLE = "ACTIVE_VERIFICATION"
GATE_BOARD = "GODOTSIM_RUNTIME_CORE_BOARD"

DRY_SCENE_ID = "dry_scene.godotsim.proof"
# SceneManager canonicalizes dotted scene ids into the runtime-owned scene id form.
DRY_SCENE_CANONICAL_ID = "scene.dry_scene_godotsim_proof"
DRY_SCENE_DOC: dict[str, Any] = {
    "scene_id": DRY_SCENE_ID,
    "@id": DRY_SCENE_ID,
    "type": "scene",
    "segments": [],
    "entities": [
        {
            "id": "dry_player",
            "entity_id": "dry_player",
            "type": "player",
            "position": [0, 0, 0],
            "collision_role": "actor",
        }
    ],
}


@dataclass(frozen=True)
class GateResult:
    gate_name: str
    passed: bool
    message: str

    def is_true(self) -> bool:
        return self.passed is True


@dataclass
class ProbeState:
    runtime_module: ModuleType | None = None
    runtime: Any | None = None
    snapshot: Any | None = None
    scene_load_result: Any | None = None
    import_error: BaseException | None = None
    instantiate_error: BaseException | None = None
    scene_load_error: BaseException | None = None
    snapshot_error: BaseException | None = None
    shutdown_error: BaseException | None = None
    port_8080_before: bool | None = None
    port_8080_after: bool | None = None


def _port_open(port: int = 8080, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        return sock.connect_ex((host, port)) == 0


def _quiet_call(fn):
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        return fn()


def _load_runtime_module(state: ProbeState) -> ModuleType | None:
    if state.runtime_module is not None or state.import_error is not None:
        return state.runtime_module
    try:
        state.runtime_module = _quiet_call(lambda: importlib.import_module("runtime_core"))
    except BaseException as exc:  # runtime_core uses sys.exit on critical import failure.
        state.import_error = exc
    return state.runtime_module


def _instantiate_runtime(state: ProbeState) -> Any | None:
    if state.runtime is not None or state.instantiate_error is not None:
        return state.runtime
    module = _load_runtime_module(state)
    if module is None:
        return None
    try:
        state.port_8080_before = _port_open(8080)
        state.runtime = _quiet_call(lambda: module.EngAInRuntime())
        state.port_8080_after = _port_open(8080)
    except BaseException as exc:
        state.instantiate_error = exc
        state.port_8080_after = _port_open(8080)
    return state.runtime


def _load_dry_scene(state: ProbeState) -> Any | None:
    if state.scene_load_result is not None or state.scene_load_error is not None:
        return state.scene_load_result
    runtime = _instantiate_runtime(state)
    if runtime is None:
        return None
    try:
        state.scene_load_result = _quiet_call(
            lambda: runtime.scene_manager.load_scene(DRY_SCENE_DOC, activate=True)
        )
    except BaseException as exc:
        state.scene_load_error = exc
    return state.scene_load_result


def _get_snapshot(state: ProbeState) -> Any | None:
    if state.snapshot is not None or state.snapshot_error is not None:
        return state.snapshot
    _load_dry_scene(state)
    runtime = state.runtime
    if runtime is None:
        return None
    try:
        state.snapshot = _quiet_call(runtime.get_snapshot)
    except BaseException as exc:
        state.snapshot_error = exc
    return state.snapshot


def _shutdown_runtime(state: ProbeState) -> bool:
    runtime = state.runtime
    if runtime is None:
        state.shutdown_error = RuntimeError("runtime was not instantiated")
        return False
    try:
        _quiet_call(runtime.shutdown)
    except BaseException as exc:
        state.shutdown_error = exc
        return False
    return True


def _payload(state: ProbeState) -> dict[str, Any] | None:
    snapshot = _get_snapshot(state)
    if not isinstance(snapshot, dict):
        return None
    payload = snapshot.get("payload")
    if not isinstance(payload, dict):
        return None
    return payload


def gate_runtime_core_source_exists(state: ProbeState) -> GateResult:
    if RUNTIME_SOURCE.is_file():
        return GateResult(
            "GATE_RUNTIME_CORE_SOURCE_EXISTS",
            True,
            f"Runtime core source exists at {RUNTIME_SOURCE.relative_to(REPO_ROOT)}.",
        )
    return GateResult(
        "GATE_RUNTIME_CORE_SOURCE_EXISTS",
        False,
        f"Runtime core source missing at {RUNTIME_SOURCE.relative_to(REPO_ROOT)}.",
    )


def gate_runtime_core_imports(state: ProbeState) -> GateResult:
    module = _load_runtime_module(state)
    if module is None:
        return GateResult("GATE_RUNTIME_CORE_IMPORTS", False, f"runtime_core import failed: {state.import_error!r}")
    if not hasattr(module, "EngAInRuntime"):
        return GateResult("GATE_RUNTIME_CORE_IMPORTS", False, "runtime_core imported but EngAInRuntime is missing.")
    return GateResult("GATE_RUNTIME_CORE_IMPORTS", True, "runtime_core imports and exposes EngAInRuntime.")


def gate_runtime_instantiates(state: ProbeState) -> GateResult:
    runtime = _instantiate_runtime(state)
    if runtime is None:
        return GateResult("GATE_RUNTIME_INSTANTIATES", False, f"EngAInRuntime instantiation failed: {state.instantiate_error!r}")
    return GateResult("GATE_RUNTIME_INSTANTIATES", True, "EngAInRuntime instantiated in dry gate mode without invoking sim_runtime.py.")


def gate_scene_manager_exists(state: ProbeState) -> GateResult:
    runtime = _instantiate_runtime(state)
    scene_manager = getattr(runtime, "scene_manager", None) if runtime is not None else None
    if scene_manager is None:
        return GateResult("GATE_SCENE_MANAGER_EXISTS", False, "Runtime has no scene_manager instance.")
    if not callable(getattr(scene_manager, "load_scene", None)):
        return GateResult("GATE_SCENE_MANAGER_EXISTS", False, "Runtime scene_manager has no callable load_scene method.")
    return GateResult("GATE_SCENE_MANAGER_EXISTS", True, "Runtime exposes SceneManager with callable load_scene method.")


def gate_dry_scene_load_call_succeeds(state: ProbeState) -> GateResult:
    result = _load_dry_scene(state)
    if state.scene_load_error is not None:
        return GateResult("GATE_DRY_SCENE_LOAD_CALL_SUCCEEDS", False, f"SceneManager dry load failed: {state.scene_load_error!r}")
    runtime = state.runtime
    active_scene_id = getattr(runtime, "snapshot", {}).get("scene_id") if runtime is not None else None
    if result not in {"accepted_new", "overwritten"}:
        return GateResult("GATE_DRY_SCENE_LOAD_CALL_SUCCEEDS", False, f"Unexpected load_scene result: {result!r}")
    if active_scene_id != DRY_SCENE_CANONICAL_ID:
        return GateResult("GATE_DRY_SCENE_LOAD_CALL_SUCCEEDS", False, f"Dry scene loaded but active scene_id is {active_scene_id!r}, expected canonical {DRY_SCENE_CANONICAL_ID!r}.")
    return GateResult("GATE_DRY_SCENE_LOAD_CALL_SUCCEEDS", True, f"SceneManager loaded and activated in-memory dry scene with result={result!r}; active scene_id={active_scene_id!r}.")


def gate_snapshot_is_dict(state: ProbeState) -> GateResult:
    snapshot = _get_snapshot(state)
    if not isinstance(snapshot, dict):
        error = f"; snapshot error: {state.snapshot_error!r}" if state.snapshot_error else ""
        return GateResult("GATE_SNAPSHOT_IS_DICT", False, f"Snapshot envelope is not a dict: {type(snapshot).__name__}{error}")
    return GateResult("GATE_SNAPSHOT_IS_DICT", True, "Runtime get_snapshot() returned a dict envelope after dry scene load.")


def gate_payload_is_dict(state: ProbeState) -> GateResult:
    payload = _payload(state)
    if not isinstance(payload, dict):
        return GateResult("GATE_PAYLOAD_IS_DICT", False, f"Envelope payload is not a dict: {type(payload).__name__}")
    return GateResult("GATE_PAYLOAD_IS_DICT", True, "Snapshot envelope payload is a dict.")


def gate_payload_scene_id_matches(state: ProbeState) -> GateResult:
    payload = _payload(state)
    if not isinstance(payload, dict):
        return GateResult("GATE_PAYLOAD_SCENE_ID_MATCHES", False, "Payload is not a dict; scene_id cannot be checked.")
    observed = payload.get("scene_id")
    if observed != DRY_SCENE_CANONICAL_ID:
        return GateResult("GATE_PAYLOAD_SCENE_ID_MATCHES", False, f"Payload scene_id mismatch: observed={observed!r}, expected canonical {DRY_SCENE_CANONICAL_ID!r}.")
    return GateResult("GATE_PAYLOAD_SCENE_ID_MATCHES", True, f"Payload scene_id matches canonical dry scene id {DRY_SCENE_CANONICAL_ID!r}.")


def gate_payload_scene_present(state: ProbeState) -> GateResult:
    payload = _payload(state)
    if not isinstance(payload, dict):
        return GateResult("GATE_PAYLOAD_SCENE_PRESENT", False, "Payload is not a dict; scene presence cannot be checked.")
    scene = payload.get("scene")
    scene_raw = payload.get("scene_raw")
    entities = payload.get("entities")
    if not isinstance(scene, dict):
        return GateResult("GATE_PAYLOAD_SCENE_PRESENT", False, f"Payload scene is not a dict: {type(scene).__name__}.")
    if scene.get("scene_id") != DRY_SCENE_CANONICAL_ID:
        return GateResult("GATE_PAYLOAD_SCENE_PRESENT", False, f"Payload scene.scene_id mismatch: {scene.get('scene_id')!r}.")
    if not isinstance(scene_raw, dict) or scene_raw.get("scene_id") != DRY_SCENE_ID:
        return GateResult("GATE_PAYLOAD_SCENE_PRESENT", False, "Payload scene_raw is missing or does not preserve dry source scene id.")
    if not isinstance(entities, dict) or "dry_player" not in entities:
        return GateResult("GATE_PAYLOAD_SCENE_PRESENT", False, "Payload entities do not include dry_player.")
    return GateResult("GATE_PAYLOAD_SCENE_PRESENT", True, "Payload contains active scene, raw scene, and dry_player entity from the in-memory dry scene.")


def gate_server_not_started_by_gate(state: ProbeState) -> GateResult:
    _instantiate_runtime(state)
    before = state.port_8080_before
    after = state.port_8080_after
    if before is None:
        before = _port_open(8080)
    if after is None:
        after = _port_open(8080)
    if before == after:
        state.port_8080_before = before
        state.port_8080_after = after
        return GateResult("GATE_SERVER_NOT_STARTED_BY_GATE", True, f"Port 8080 listening state unchanged by dry gate: before={before}, after={after}.")
    return GateResult("GATE_SERVER_NOT_STARTED_BY_GATE", False, f"Port 8080 listening state changed during gate: before={before}, after={after}.")


def gate_runtime_shutdown(state: ProbeState) -> GateResult:
    runtime = _instantiate_runtime(state)
    if runtime is None:
        return GateResult("GATE_RUNTIME_SHUTDOWN", False, "Runtime was not instantiated; shutdown cannot be proven.")
    ok = _shutdown_runtime(state)
    thread_alive = bool(getattr(getattr(runtime, "sim_thread", None), "is_alive", lambda: False)())
    running = bool(getattr(runtime, "running", True))
    if ok and not running and not thread_alive:
        return GateResult("GATE_RUNTIME_SHUTDOWN", True, "Runtime shutdown completed; running=False and simulation thread is stopped.")
    return GateResult("GATE_RUNTIME_SHUTDOWN", False, f"Runtime shutdown not clean: ok={ok}, running={running}, thread_alive={thread_alive}, error={state.shutdown_error!r}.")


def _classification(results: list[GateResult]) -> str:
    if all(result.is_true() for result in results):
        return "GODOTSIM_DRY_SCENE_LOAD_SNAPSHOT_PROVEN"
    return "GODOTSIM_DRY_SCENE_LOAD_SNAPSHOT_BLOCKED"


def main() -> int:
    state = ProbeState()
    results = [
        gate_runtime_core_source_exists(state),
        gate_runtime_core_imports(state),
        gate_runtime_instantiates(state),
        gate_scene_manager_exists(state),
        gate_dry_scene_load_call_succeeds(state),
        gate_snapshot_is_dict(state),
        gate_payload_is_dict(state),
        gate_payload_scene_id_matches(state),
        gate_payload_scene_present(state),
        gate_server_not_started_by_gate(state),
        gate_runtime_shutdown(state),
    ]

    for result in results:
        status = "PASS" if result.is_true() else "FAIL"
        value = "TRUE" if result.is_true() else "FALSE"
        print(f"[gate_runtime_core_dry_scene_load][{result.gate_name}] {status}: {result.gate_name} = {value}; {result.message}")

    classification = _classification(results)
    all_gates = all(result.is_true() for result in results)
    print(f"[gate_runtime_core_dry_scene_load][CLASSIFICATION] {classification}")
    print(f"[gate_runtime_core_dry_scene_load][ALL_GATES] {'true' if all_gates else 'false'}")

    return 0 if all_gates and classification == "GODOTSIM_DRY_SCENE_LOAD_SNAPSHOT_PROVEN" else 1


if __name__ == "__main__":
    sys.exit(main())
