# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/godotsim/gates/gate_runtime_core_dry_command_gateway.py

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
ENGAINOS_CORE_DIR = REPO_ROOT / "godotengain/engainos/core"
RUNTIME_CORE_SOURCE = RUNTIME_DIR / "runtime_core.py"
RUNTIME_GATEWAY_SOURCE = RUNTIME_DIR / "runtime_gateway.py"
COMMAND_DISPATCHER_SOURCE = RUNTIME_DIR / "command_dispatcher.py"

for import_path in (REPO_ROOT, RUNTIME_DIR, ENGAINOS_CORE_DIR):
    if str(import_path) not in sys.path:
        sys.path.insert(0, str(import_path))

GATE_LIFECYCLE = "ACTIVE_VERIFICATION"
GATE_BOARD = "GODOTSIM_RUNTIME_CORE_BOARD"

TOXIC_MISSING_IDENTITY_COMMAND: dict[str, Any] = {
    "command": "move_entity",
    "entity_id": "dry_player",
    "position": [1, 0, 0],
}

VALID_IDENTITY_MUTATION_COMMAND: dict[str, Any] = {
    "command": "move_entity",
    "entity_id": "dry_player",
    "position": [1, 0, 0],
    "reality_mode": "DRAFT",
    "actor_authority_tier": 1,
    "actor_id": "dry_gate",
    "source_system": "godotsim_dry_gate",
}

REPLAY_MUTATION_COMMAND: dict[str, Any] = {
    **VALID_IDENTITY_MUTATION_COMMAND,
    "reality_mode": "REPLAY",
}

READ_ONLY_COMMAND: dict[str, Any] = {
    "command": "look",
    "actor_id": "dry_gate",
    "source_system": "godotsim_dry_gate",
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
    gateway_module: ModuleType | None = None
    dispatcher_module: ModuleType | None = None
    runtime: Any | None = None
    gateway: Any | None = None
    missing_identity_decision: Any | None = None
    replay_decision: Any | None = None
    read_only_decision: Any | None = None
    valid_identity_decision: Any | None = None
    import_error: BaseException | None = None
    gateway_import_error: BaseException | None = None
    dispatcher_import_error: BaseException | None = None
    instantiate_error: BaseException | None = None
    gateway_error: BaseException | None = None
    missing_identity_error: BaseException | None = None
    replay_error: BaseException | None = None
    read_only_error: BaseException | None = None
    valid_identity_error: BaseException | None = None
    shutdown_error: BaseException | None = None
    port_8080_before: bool | None = None
    port_8080_after: bool | None = None
    runtime_loop_stopped_for_dry_dispatch: bool = False


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
    except BaseException as exc:  # runtime_core may sys.exit on critical import failure.
        state.import_error = exc
    return state.runtime_module


def _load_dispatcher_module(state: ProbeState) -> ModuleType | None:
    if state.dispatcher_module is not None or state.dispatcher_import_error is not None:
        return state.dispatcher_module
    try:
        state.dispatcher_module = _quiet_call(lambda: importlib.import_module("command_dispatcher"))
    except BaseException as exc:
        state.dispatcher_import_error = exc
    return state.dispatcher_module


def _load_gateway_module(state: ProbeState) -> ModuleType | None:
    if state.gateway_module is not None or state.gateway_import_error is not None:
        return state.gateway_module
    try:
        state.gateway_module = _quiet_call(lambda: importlib.import_module("runtime_gateway"))
    except BaseException as exc:
        state.gateway_import_error = exc
    return state.gateway_module


def _stop_runtime_loop_for_dry_dispatch(runtime: Any) -> None:
    """Stop the background loop before dispatch probes so queued commands do not execute."""
    if not bool(getattr(runtime, "running", False)):
        return
    setattr(runtime, "running", False)
    sim_thread = getattr(runtime, "sim_thread", None)
    if sim_thread is not None and callable(getattr(sim_thread, "join", None)):
        sim_thread.join(timeout=2.0)


def _instantiate_runtime(state: ProbeState) -> Any | None:
    if state.runtime is not None or state.instantiate_error is not None:
        return state.runtime
    module = _load_runtime_module(state)
    if module is None:
        return None
    try:
        state.port_8080_before = _port_open(8080)
        state.runtime = _quiet_call(lambda: module.EngAInRuntime())
        _stop_runtime_loop_for_dry_dispatch(state.runtime)
        state.runtime_loop_stopped_for_dry_dispatch = True
        state.port_8080_after = _port_open(8080)
    except BaseException as exc:
        state.instantiate_error = exc
        state.port_8080_after = _port_open(8080)
    return state.runtime


def _get_gateway(state: ProbeState) -> Any | None:
    if state.gateway is not None or state.gateway_error is not None:
        return state.gateway
    runtime = _instantiate_runtime(state)
    gateway_module = _load_gateway_module(state)
    if runtime is None or gateway_module is None:
        return None
    dispatcher = getattr(runtime, "command_dispatcher", None)
    try:
        state.gateway = gateway_module.RuntimeGateway(runtime, dispatcher)
    except BaseException as exc:
        state.gateway_error = exc
    return state.gateway


def _submit_missing_identity(state: ProbeState) -> Any | None:
    if state.missing_identity_decision is not None or state.missing_identity_error is not None:
        return state.missing_identity_decision
    gateway = _get_gateway(state)
    if gateway is None:
        return None
    try:
        state.missing_identity_decision = _quiet_call(lambda: gateway.submit(dict(TOXIC_MISSING_IDENTITY_COMMAND)))
    except BaseException as exc:
        state.missing_identity_error = exc
    return state.missing_identity_decision


def _submit_replay(state: ProbeState) -> Any | None:
    if state.replay_decision is not None or state.replay_error is not None:
        return state.replay_decision
    gateway = _get_gateway(state)
    if gateway is None:
        return None
    try:
        state.replay_decision = _quiet_call(lambda: gateway.submit(dict(REPLAY_MUTATION_COMMAND)))
    except BaseException as exc:
        state.replay_error = exc
    return state.replay_decision


def _submit_read_only(state: ProbeState) -> Any | None:
    if state.read_only_decision is not None or state.read_only_error is not None:
        return state.read_only_decision
    gateway = _get_gateway(state)
    if gateway is None:
        return None
    try:
        state.read_only_decision = _quiet_call(lambda: gateway.submit(dict(READ_ONLY_COMMAND)))
    except BaseException as exc:
        state.read_only_error = exc
    return state.read_only_decision


def _submit_valid_identity(state: ProbeState) -> Any | None:
    if state.valid_identity_decision is not None or state.valid_identity_error is not None:
        return state.valid_identity_decision
    gateway = _get_gateway(state)
    if gateway is None:
        return None
    try:
        state.valid_identity_decision = _quiet_call(lambda: gateway.submit(dict(VALID_IDENTITY_MUTATION_COMMAND)))
    except BaseException as exc:
        state.valid_identity_error = exc
    return state.valid_identity_decision


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


def gate_runtime_core_imports(state: ProbeState) -> GateResult:
    if not RUNTIME_CORE_SOURCE.is_file():
        return GateResult("GATE_RUNTIME_CORE_IMPORTS", False, f"runtime_core source missing at {RUNTIME_CORE_SOURCE.relative_to(REPO_ROOT)}.")
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
    if not state.runtime_loop_stopped_for_dry_dispatch:
        return GateResult("GATE_RUNTIME_INSTANTIATES", False, "Runtime instantiated but dry gate did not stop the background simulation loop before dispatch probes.")
    return GateResult("GATE_RUNTIME_INSTANTIATES", True, "EngAInRuntime instantiated; dry gate stopped its local simulation loop before command dispatch probes.")


def gate_command_dispatcher_exists(state: ProbeState) -> GateResult:
    if not COMMAND_DISPATCHER_SOURCE.is_file():
        return GateResult("GATE_COMMAND_DISPATCHER_EXISTS", False, f"command_dispatcher source missing at {COMMAND_DISPATCHER_SOURCE.relative_to(REPO_ROOT)}.")
    module = _load_dispatcher_module(state)
    if module is None:
        return GateResult("GATE_COMMAND_DISPATCHER_EXISTS", False, f"command_dispatcher import failed: {state.dispatcher_import_error!r}")
    runtime = _instantiate_runtime(state)
    dispatcher = getattr(runtime, "command_dispatcher", None) if runtime is not None else None
    if dispatcher is None:
        return GateResult("GATE_COMMAND_DISPATCHER_EXISTS", False, "Runtime has no command_dispatcher instance.")
    if not callable(getattr(dispatcher, "dispatch", None)):
        return GateResult("GATE_COMMAND_DISPATCHER_EXISTS", False, "Runtime command_dispatcher has no callable dispatch method.")
    return GateResult("GATE_COMMAND_DISPATCHER_EXISTS", True, "Runtime exposes CommandDispatcher with callable dispatch method.")


def gate_runtime_gateway_imports(state: ProbeState) -> GateResult:
    if not RUNTIME_GATEWAY_SOURCE.is_file():
        return GateResult("GATE_RUNTIME_GATEWAY_IMPORTS", False, f"runtime_gateway source missing at {RUNTIME_GATEWAY_SOURCE.relative_to(REPO_ROOT)}.")
    module = _load_gateway_module(state)
    if module is None:
        return GateResult("GATE_RUNTIME_GATEWAY_IMPORTS", False, f"runtime_gateway import failed: {state.gateway_import_error!r}")
    if not hasattr(module, "RuntimeGateway"):
        return GateResult("GATE_RUNTIME_GATEWAY_IMPORTS", False, "runtime_gateway imported but RuntimeGateway is missing.")
    if _get_gateway(state) is None:
        return GateResult("GATE_RUNTIME_GATEWAY_IMPORTS", False, f"RuntimeGateway construction failed: {state.gateway_error!r}")
    return GateResult("GATE_RUNTIME_GATEWAY_IMPORTS", True, "runtime_gateway imports and RuntimeGateway constructs against the dry runtime and dispatcher.")


def gate_missing_identity_mutation_rejected(state: ProbeState) -> GateResult:
    decision = _submit_missing_identity(state)
    if state.missing_identity_error is not None:
        return GateResult("GATE_MISSING_IDENTITY_MUTATION_REJECTED", False, f"Toxic command submission raised: {state.missing_identity_error!r}")
    if decision is None:
        return GateResult("GATE_MISSING_IDENTITY_MUTATION_REJECTED", False, "No gateway decision produced for missing-identity mutation.")
    reason = str(getattr(decision, "reason", ""))
    accepted = bool(getattr(decision, "accepted", True))
    if not accepted and "reality_mode" in reason and "actor_authority_tier" in reason:
        return GateResult("GATE_MISSING_IDENTITY_MUTATION_REJECTED", True, f"Malformed mutation rejected: accepted={accepted}, reason={reason!r}.")
    return GateResult("GATE_MISSING_IDENTITY_MUTATION_REJECTED", False, f"Expected rejection mentioning reality_mode and actor_authority_tier; got accepted={accepted}, reason={reason!r}.")


def gate_replay_mutation_rejected_if_supported(state: ProbeState) -> GateResult:
    decision = _submit_replay(state)
    if state.replay_error is not None:
        return GateResult("GATE_REPLAY_MUTATION_REJECTED_IF_SUPPORTED", False, f"REPLAY command submission raised: {state.replay_error!r}")
    if decision is None:
        return GateResult("GATE_REPLAY_MUTATION_REJECTED_IF_SUPPORTED", False, "No gateway decision produced for REPLAY mutation.")
    reason = str(getattr(decision, "reason", ""))
    accepted = bool(getattr(decision, "accepted", True))
    if not accepted and "REPLAY" in reason:
        return GateResult("GATE_REPLAY_MUTATION_REJECTED_IF_SUPPORTED", True, f"REPLAY mutation rejected by governance: accepted={accepted}, reason={reason!r}.")
    return GateResult("GATE_REPLAY_MUTATION_REJECTED_IF_SUPPORTED", False, f"Expected REPLAY rejection; got accepted={accepted}, reason={reason!r}.")


def gate_read_only_command_allowed_if_classified(state: ProbeState) -> GateResult:
    gateway_module = _load_gateway_module(state)
    classification = getattr(gateway_module, "ACTION_CLASSIFICATION", {}) if gateway_module is not None else {}
    look_class = classification.get("look", {}) if isinstance(classification, dict) else {}
    if look_class.get("mutation_class") != "read_only":
        return GateResult("GATE_READ_ONLY_COMMAND_ALLOWED_IF_CLASSIFIED", True, "look is not classified read_only in ACTION_CLASSIFICATION; read-only allowance probe bypassed by classification state.")

    decision = _submit_read_only(state)
    if state.read_only_error is not None:
        return GateResult("GATE_READ_ONLY_COMMAND_ALLOWED_IF_CLASSIFIED", False, f"Read-only command submission raised: {state.read_only_error!r}")
    if decision is None:
        return GateResult("GATE_READ_ONLY_COMMAND_ALLOWED_IF_CLASSIFIED", False, "No gateway decision produced for read-only command.")
    accepted = bool(getattr(decision, "accepted", False))
    result = getattr(decision, "result", None)
    if accepted and isinstance(result, dict):
        return GateResult("GATE_READ_ONLY_COMMAND_ALLOWED_IF_CLASSIFIED", True, f"Classified read-only command allowed without mutation identity fields; dispatcher result type={result.get('type')!r}.")
    return GateResult("GATE_READ_ONLY_COMMAND_ALLOWED_IF_CLASSIFIED", False, f"Expected classified read-only command to be accepted; got accepted={accepted}, result={result!r}.")


def gate_valid_identity_mutation_reaches_known_dispatcher_result(state: ProbeState) -> GateResult:
    decision = _submit_valid_identity(state)
    if state.valid_identity_error is not None:
        return GateResult("GATE_VALID_IDENTITY_MUTATION_REACHES_KNOWN_DISPATCHER_RESULT", False, f"Valid identity command submission raised: {state.valid_identity_error!r}")
    if decision is None:
        return GateResult("GATE_VALID_IDENTITY_MUTATION_REACHES_KNOWN_DISPATCHER_RESULT", False, "No gateway decision produced for valid identity mutation.")
    accepted = bool(getattr(decision, "accepted", False))
    reason = str(getattr(decision, "reason", ""))
    result = getattr(decision, "result", None)
    if accepted and isinstance(result, dict) and result.get("status") in {"queued", "accepted", "ok"}:
        return GateResult("GATE_VALID_IDENTITY_MUTATION_REACHES_KNOWN_DISPATCHER_RESULT", True, f"Valid identity mutation passed gateway and reached known dispatcher-level result: {result!r}.")
    if not accepted and reason and "Missing required mutation identity fields" not in reason:
        return GateResult("GATE_VALID_IDENTITY_MUTATION_REACHES_KNOWN_DISPATCHER_RESULT", True, f"Valid identity mutation passed identity gate and was rejected later by known governance layer: reason={reason!r}.")
    return GateResult("GATE_VALID_IDENTITY_MUTATION_REACHES_KNOWN_DISPATCHER_RESULT", False, f"Valid identity mutation did not prove identity-gate passage; accepted={accepted}, reason={reason!r}, result={result!r}.")


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
        return GateResult("GATE_SERVER_NOT_STARTED_BY_GATE", True, f"Port 8080 listening state unchanged by dry command gate: before={before}, after={after}.")
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
        return "GODOTSIM_DRY_COMMAND_GATEWAY_PROVEN"
    return "GODOTSIM_DRY_COMMAND_GATEWAY_BLOCKED"


def main() -> int:
    state = ProbeState()
    results = [
        gate_runtime_core_imports(state),
        gate_runtime_instantiates(state),
        gate_command_dispatcher_exists(state),
        gate_runtime_gateway_imports(state),
        gate_missing_identity_mutation_rejected(state),
        gate_replay_mutation_rejected_if_supported(state),
        gate_read_only_command_allowed_if_classified(state),
        gate_valid_identity_mutation_reaches_known_dispatcher_result(state),
        gate_server_not_started_by_gate(state),
        gate_runtime_shutdown(state),
    ]

    for result in results:
        status = "PASS" if result.is_true() else "FAIL"
        value = "TRUE" if result.is_true() else "FALSE"
        print(f"[gate_runtime_core_dry_command_gateway][{result.gate_name}] {status}: {result.gate_name} = {value}; {result.message}")

    classification = _classification(results)
    all_gates = all(result.is_true() for result in results)
    print(f"[gate_runtime_core_dry_command_gateway][CLASSIFICATION] {classification}")
    print(f"[gate_runtime_core_dry_command_gateway][ALL_GATES] {'true' if all_gates else 'false'}")

    return 0 if all_gates and classification == "GODOTSIM_DRY_COMMAND_GATEWAY_PROVEN" else 1


if __name__ == "__main__":
    sys.exit(main())
