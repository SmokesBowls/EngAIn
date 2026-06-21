# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/godotsim/gates/gate_runtime_core_dry_snapshot.py

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

ENVELOPE_KEYS = {
    "protocol",
    "version",
    "epoch",
    "tick",
    "timestamp",
    "hash",
    "payload",
}

PAYLOAD_KEYS = {
    "scene_id",
    "entities",
    "spatial",
    "perception",
    "behavior",
    "world",
    "events",
    "scene",
    "scene_raw",
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
    import_error: BaseException | None = None
    instantiate_error: BaseException | None = None
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


def _get_snapshot(state: ProbeState) -> Any | None:
    if state.snapshot is not None or state.snapshot_error is not None:
        return state.snapshot
    runtime = _instantiate_runtime(state)
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
        return GateResult(
            "GATE_RUNTIME_CORE_IMPORTS",
            False,
            f"runtime_core import failed: {state.import_error!r}",
        )
    if not hasattr(module, "EngAInRuntime"):
        return GateResult("GATE_RUNTIME_CORE_IMPORTS", False, "runtime_core imported but EngAInRuntime is missing.")
    return GateResult("GATE_RUNTIME_CORE_IMPORTS", True, "runtime_core imports and exposes EngAInRuntime.")


def gate_runtime_instantiates(state: ProbeState) -> GateResult:
    runtime = _instantiate_runtime(state)
    if runtime is None:
        return GateResult(
            "GATE_RUNTIME_INSTANTIATES",
            False,
            f"EngAInRuntime instantiation failed: {state.instantiate_error!r}",
        )
    return GateResult("GATE_RUNTIME_INSTANTIATES", True, "EngAInRuntime instantiated in dry gate mode without invoking sim_runtime.py.")


def gate_snapshot_is_dict(state: ProbeState) -> GateResult:
    snapshot = _get_snapshot(state)
    if not isinstance(snapshot, dict):
        error = f"; snapshot error: {state.snapshot_error!r}" if state.snapshot_error else ""
        return GateResult("GATE_SNAPSHOT_IS_DICT", False, f"Snapshot envelope is not a dict: {type(snapshot).__name__}{error}")
    return GateResult("GATE_SNAPSHOT_IS_DICT", True, "Runtime get_snapshot() returned a dict envelope.")


def gate_snapshot_has_protocol_envelope_keys(state: ProbeState) -> GateResult:
    snapshot = _get_snapshot(state)
    if not isinstance(snapshot, dict):
        return GateResult("GATE_SNAPSHOT_HAS_PROTOCOL_ENVELOPE_KEYS", False, "Snapshot is not a dict; envelope keys cannot be checked.")
    missing = sorted(ENVELOPE_KEYS - set(snapshot.keys()))
    if missing:
        return GateResult("GATE_SNAPSHOT_HAS_PROTOCOL_ENVELOPE_KEYS", False, f"Snapshot envelope missing keys: {missing}")
    return GateResult("GATE_SNAPSHOT_HAS_PROTOCOL_ENVELOPE_KEYS", True, f"Snapshot envelope includes required keys: {sorted(ENVELOPE_KEYS)}.")


def gate_payload_is_dict(state: ProbeState) -> GateResult:
    snapshot = _get_snapshot(state)
    payload = snapshot.get("payload") if isinstance(snapshot, dict) else None
    if not isinstance(payload, dict):
        return GateResult("GATE_PAYLOAD_IS_DICT", False, f"Envelope payload is not a dict: {type(payload).__name__}")
    return GateResult("GATE_PAYLOAD_IS_DICT", True, "Snapshot envelope payload is a dict.")


def gate_payload_has_runtime_family_keys(state: ProbeState) -> GateResult:
    snapshot = _get_snapshot(state)
    payload = snapshot.get("payload") if isinstance(snapshot, dict) else None
    if not isinstance(payload, dict):
        return GateResult("GATE_PAYLOAD_HAS_RUNTIME_FAMILY_KEYS", False, "Payload is not a dict; runtime family keys cannot be checked.")
    missing = sorted(PAYLOAD_KEYS - set(payload.keys()))
    if missing:
        return GateResult("GATE_PAYLOAD_HAS_RUNTIME_FAMILY_KEYS", False, f"Payload missing runtime family keys: {missing}")
    return GateResult("GATE_PAYLOAD_HAS_RUNTIME_FAMILY_KEYS", True, f"Payload includes required runtime family keys: {sorted(PAYLOAD_KEYS)}.")


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
        return GateResult(
            "GATE_SERVER_NOT_STARTED_BY_GATE",
            True,
            f"Port 8080 listening state unchanged by dry gate: before={before}, after={after}.",
        )
    return GateResult(
        "GATE_SERVER_NOT_STARTED_BY_GATE",
        False,
        f"Port 8080 listening state changed during gate: before={before}, after={after}.",
    )


def gate_runtime_shutdown(state: ProbeState) -> GateResult:
    runtime = _instantiate_runtime(state)
    if runtime is None:
        return GateResult("GATE_RUNTIME_SHUTDOWN", False, "Runtime was not instantiated; shutdown cannot be proven.")
    ok = _shutdown_runtime(state)
    thread_alive = bool(getattr(getattr(runtime, "sim_thread", None), "is_alive", lambda: False)())
    running = bool(getattr(runtime, "running", True))
    if ok and not running and not thread_alive:
        return GateResult("GATE_RUNTIME_SHUTDOWN", True, "Runtime shutdown completed; running=False and simulation thread is stopped.")
    return GateResult(
        "GATE_RUNTIME_SHUTDOWN",
        False,
        f"Runtime shutdown not clean: ok={ok}, running={running}, thread_alive={thread_alive}, error={state.shutdown_error!r}.",
    )


def _classification(results: list[GateResult]) -> str:
    if all(result.is_true() for result in results):
        return "GODOTSIM_DRY_RUNTIME_CORE_SNAPSHOT_PROVEN"
    return "GODOTSIM_DRY_RUNTIME_CORE_SNAPSHOT_BLOCKED"


def main() -> int:
    state = ProbeState()
    results = [
        gate_runtime_core_source_exists(state),
        gate_runtime_core_imports(state),
        gate_runtime_instantiates(state),
        gate_snapshot_is_dict(state),
        gate_snapshot_has_protocol_envelope_keys(state),
        gate_payload_is_dict(state),
        gate_payload_has_runtime_family_keys(state),
        gate_server_not_started_by_gate(state),
        gate_runtime_shutdown(state),
    ]

    for result in results:
        status = "PASS" if result.is_true() else "FAIL"
        value = "TRUE" if result.is_true() else "FALSE"
        print(f"[gate_runtime_core_dry_snapshot][{result.gate_name}] {status}: {result.gate_name} = {value}; {result.message}")

    classification = _classification(results)
    all_gates = all(result.is_true() for result in results)
    print(f"[gate_runtime_core_dry_snapshot][CLASSIFICATION] {classification}")
    print(f"[gate_runtime_core_dry_snapshot][ALL_GATES] {'true' if all_gates else 'false'}")

    return 0 if all_gates and classification == "GODOTSIM_DRY_RUNTIME_CORE_SNAPSHOT_PROVEN" else 1


if __name__ == "__main__":
    sys.exit(main())
