#!/usr/bin/env python3

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

REQUEST_PATH = ROOT / "packets" / "input" / "PLAYER_INPUT_LISTENER_EXECUTOR_REQUEST_V1.json"
PRIOR_DECISION_PATH = ROOT / "runtime" / "logs" / "PLAYER_INPUT_AUTHORIZATION_DECISION_V1.json"
DECISION_PATH = ROOT / "runtime" / "logs" / "PLAYER_INPUT_LISTENER_EXECUTOR_DECISION_V1.json"

FORBIDDEN_OUTPUTS = {
    "runtime_mutation",
    "player_spawn",
    "entity_spawn",
    "gameplay_start",
    "canon_write",
    "quest_state_write",
    "combat_state_write",
    "inventory_state_write",
    "freeform_godot_command",
}


@dataclass(frozen=True)
class GateResult:
    passed: bool
    gate_name: str
    message: str
    details: dict[str, Any]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError("JSON root must be an object.")

    return data


def gate_file_exists(path: Path, gate_name: str, label: str) -> GateResult:
    passed = path.exists() and path.is_file()

    return GateResult(
        passed=passed,
        gate_name=gate_name,
        message=f"{label} exists." if passed else f"{label} is missing.",
        details={"path": str(path)},
    )


def gate_protocol_envelope(request: dict[str, Any]) -> GateResult:
    checks = {
        "protocol_valid": request.get("protocol") == "NGAT-RT",
        "version_valid": request.get("version") == "1.0",
        "tick_valid": request.get("tick") == 0,
        "epoch_valid": request.get("epoch") == "engainos.player_input_listener_executor_request",
        "type_valid": request.get("type") == "command",
        "payload_is_object": isinstance(request.get("payload"), dict),
    }

    passed = all(checks.values())

    return GateResult(
        passed=passed,
        gate_name="GATE_PROTOCOL_ENVELOPE",
        message="Protocol envelope is valid." if passed else "Protocol envelope is invalid.",
        details=checks,
    )


def gate_contract_shape(request: dict[str, Any]) -> GateResult:
    payload = request.get("payload", {})

    required_keys = [
        "@id",
        "@when",
        "@where",
        "request_type",
        "mutation_requested",
        "execution_requested",
        "execution_scope",
        "issuer",
        "target",
        "prior_decision_required",
        "executor_request",
        "allowed_outputs",
        "forbidden_outputs",
        "expected_decision_shape",
    ]

    checks = {key: key in payload for key in required_keys}
    checks["@id_valid"] = payload.get("@id") == "PLAYER_INPUT_LISTENER_EXECUTOR_REQUEST"
    checks["@when_valid"] = payload.get("@when") == "POST_PLAYER_INPUT_AUTHORIZATION"
    checks["@where_valid"] = payload.get("@where") == "engainos.authority_gate"
    checks["request_type_valid"] = payload.get("request_type") == "executor_release_decision"
    checks["execution_scope_valid"] = payload.get("execution_scope") == "boot_shell_input_listener_only"

    passed = all(checks.values())

    return GateResult(
        passed=passed,
        gate_name="GATE_CONTRACT_SHAPE",
        message="Contract shape is valid." if passed else "Contract shape is invalid.",
        details=checks,
    )


def gate_prior_decision(prior: dict[str, Any]) -> GateResult:
    checks = {
        "contract_valid": prior.get("contract") == "engainos.player_input_authorization_decision.v1",
        "allowed_true": prior.get("allowed") is True,
        "status_valid": prior.get("status") == "PLAYER_INPUT_AUTHORIZED_FOR_BOOT_SHELL",
        "player_input_authorized_true": prior.get("player_input_authorized") is True,
        "input_mode_valid": prior.get("input_mode") == "boot_shell_input_probe",
        "runtime_mutation_allowed_false": prior.get("runtime_mutation_allowed") is False,
        "player_spawn_allowed_false": prior.get("player_spawn_allowed") is False,
        "entity_spawn_allowed_false": prior.get("entity_spawn_allowed") is False,
        "gameplay_start_allowed_false": prior.get("gameplay_start_allowed") is False,
        "next_action_valid": prior.get("next_action") == "PLAYER_INPUT_LISTENER_EXECUTOR_REQUEST_V1",
    }

    passed = all(checks.values())

    return GateResult(
        passed=passed,
        gate_name="GATE_PRIOR_DECISION",
        message="Prior player input authorization permits listener executor request." if passed else "Prior decision does not permit listener executor request.",
        details=checks,
    )


def gate_no_mutation_request(request: dict[str, Any]) -> GateResult:
    payload = request["payload"]

    checks = {
        "mutation_requested_false": payload.get("mutation_requested") is False,
        "execution_requested_true": payload.get("execution_requested") is True,
        "execution_scope_valid": payload.get("execution_scope") == "boot_shell_input_listener_only",
    }

    passed = all(checks.values())

    return GateResult(
        passed=passed,
        gate_name="GATE_NO_MUTATION_REQUEST",
        message="Request asks for limited executor release without runtime mutation." if passed else "Request attempts unsafe mutation or wrong execution scope.",
        details=checks,
    )


def gate_executor_scope(request: dict[str, Any]) -> GateResult:
    executor = request["payload"].get("executor_request", {})

    checks = {
        "executor_id_valid": executor.get("executor_id") == "player_input_listener_executor_v1",
        "executor_role_valid": executor.get("executor_role") == "attach_boot_shell_input_listener",
        "requested_input_mode_valid": executor.get("requested_input_mode") == "boot_shell_input_probe",
        "may_call_godot_true": executor.get("may_call_godot") is True,
        "may_attach_input_listener_true": executor.get("may_attach_input_listener") is True,
        "may_capture_input_true": executor.get("may_capture_input") is True,
        "may_write_input_packet_true": executor.get("may_write_input_packet") is True,
        "may_mutate_runtime_false": executor.get("may_mutate_runtime") is False,
        "may_spawn_player_false": executor.get("may_spawn_player") is False,
        "may_spawn_entities_false": executor.get("may_spawn_entities") is False,
        "may_start_gameplay_false": executor.get("may_start_gameplay") is False,
        "may_write_canon_false": executor.get("may_write_canon") is False,
        "may_write_quest_state_false": executor.get("may_write_quest_state") is False,
        "may_write_combat_state_false": executor.get("may_write_combat_state") is False,
        "may_write_inventory_state_false": executor.get("may_write_inventory_state") is False,
    }

    passed = all(checks.values())

    return GateResult(
        passed=passed,
        gate_name="GATE_EXECUTOR_SCOPE",
        message="Executor scope is limited to boot-shell input listening." if passed else "Executor scope exceeds boot-shell input authority.",
        details=checks,
    )


def gate_forbidden_outputs(request: dict[str, Any]) -> GateResult:
    payload = request["payload"]

    declared_forbidden = set(payload.get("forbidden_outputs", []))
    allowed_outputs = set(payload.get("allowed_outputs", []))

    missing_forbidden = sorted(FORBIDDEN_OUTPUTS - declared_forbidden)
    unsafe_allowed = sorted(allowed_outputs.intersection(FORBIDDEN_OUTPUTS))

    checks = {
        "all_forbidden_outputs_declared": len(missing_forbidden) == 0,
        "allowed_outputs_are_safe": len(unsafe_allowed) == 0,
    }

    passed = all(checks.values())

    return GateResult(
        passed=passed,
        gate_name="GATE_FORBIDDEN_OUTPUTS",
        message="Forbidden outputs are declared and not allowed." if passed else "Forbidden outputs are incomplete or unsafely allowed.",
        details={
            "checks": checks,
            "missing_forbidden": missing_forbidden,
            "unsafe_allowed": unsafe_allowed,
        },
    )


def gate_decision_shape(request: dict[str, Any]) -> GateResult:
    shape = request["payload"].get("expected_decision_shape", {})

    checks = {
        "allowed_shape_valid": shape.get("allowed") == "bool",
        "reason_shape_valid": shape.get("reason") == "string",
        "blocked_by_shape_valid": shape.get("blocked_by") == "string|null",
        "input_listener_executor_allowed_shape_valid": shape.get("input_listener_executor_allowed") == "bool",
        "godot_command_allowed_shape_valid": shape.get("godot_command_allowed") == "bool",
        "runtime_mutation_allowed_shape_valid": shape.get("runtime_mutation_allowed") == "bool",
        "player_spawn_allowed_shape_valid": shape.get("player_spawn_allowed") == "bool",
        "entity_spawn_allowed_shape_valid": shape.get("entity_spawn_allowed") == "bool",
        "gameplay_start_allowed_shape_valid": shape.get("gameplay_start_allowed") == "bool",
        "next_action_shape_valid": shape.get("next_action") == "string|null",
    }

    passed = all(checks.values())

    return GateResult(
        passed=passed,
        gate_name="GATE_DECISION_SHAPE",
        message="Expected decision shape is valid." if passed else "Expected decision shape is invalid.",
        details=checks,
    )


def build_decision(results: list[GateResult]) -> dict[str, Any]:
    failed = [result for result in results if not result.passed]

    if failed:
        return {
            "contract": "engainos.player_input_listener_executor_decision.v1",
            "generated_at": utc_now(),
            "allowed": False,
            "status": "PLAYER_INPUT_LISTENER_EXECUTOR_BLOCKED",
            "reason": "Player input listener executor request rejected.",
            "blocked_by": failed[0].gate_name,
            "input_listener_executor_allowed": False,
            "godot_command_allowed": False,
            "runtime_mutation_allowed": False,
            "player_spawn_allowed": False,
            "entity_spawn_allowed": False,
            "gameplay_start_allowed": False,
            "next_action": "FIX_PLAYER_INPUT_LISTENER_EXECUTOR_REQUEST",
        }

    return {
        "contract": "engainos.player_input_listener_executor_decision.v1",
        "generated_at": utc_now(),
        "allowed": True,
        "status": "PLAYER_INPUT_LISTENER_EXECUTOR_AUTHORIZED",
        "reason": "Godot may attach a limited boot-shell input listener. Captured input may be packetized but may not mutate runtime.",
        "blocked_by": None,
        "input_listener_executor_allowed": True,
        "godot_command_allowed": True,
        "runtime_mutation_allowed": False,
        "player_spawn_allowed": False,
        "entity_spawn_allowed": False,
        "gameplay_start_allowed": False,
        "next_action": "PLAYER_INPUT_LISTENER_EXECUTOR_V1",
    }


def write_decision(decision: dict[str, Any]) -> None:
    DECISION_PATH.parent.mkdir(parents=True, exist_ok=True)
    DECISION_PATH.write_text(
        json.dumps(decision, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def print_gate(result: GateResult) -> None:
    status = "PASS" if result.passed else "FAIL"
    print(f"[player_input_listener_executor_request][{result.gate_name}] {status}: {result.message}")
    print(json.dumps(result.details, indent=2, sort_keys=True))


def main() -> int:
    results: list[GateResult] = []

    file_gates = [
        gate_file_exists(REQUEST_PATH, "GATE_REQUEST_EXISTS", "Player input listener executor request"),
        gate_file_exists(PRIOR_DECISION_PATH, "GATE_PRIOR_DECISION_EXISTS", "Player input authorization decision"),
    ]

    results.extend(file_gates)

    if not all(result.passed for result in file_gates):
        for result in results:
            print_gate(result)

        decision = build_decision(results)
        write_decision(decision)

        print("[player_input_listener_executor_request][ALL_GATES] false")
        print(json.dumps(decision, indent=2, sort_keys=True))
        print(f"[player_input_listener_executor_request][DECISION_WRITTEN] {DECISION_PATH}")
        return 1

    try:
        request = load_json(REQUEST_PATH)
        prior = load_json(PRIOR_DECISION_PATH)
    except Exception as exc:
        results.append(
            GateResult(
                passed=False,
                gate_name="GATE_JSON_PARSE",
                message="Request or prior decision could not be parsed.",
                details={"error": str(exc)},
            )
        )

        for result in results:
            print_gate(result)

        decision = build_decision(results)
        write_decision(decision)

        print("[player_input_listener_executor_request][ALL_GATES] false")
        print(json.dumps(decision, indent=2, sort_keys=True))
        print(f"[player_input_listener_executor_request][DECISION_WRITTEN] {DECISION_PATH}")
        return 1

    results.extend(
        [
            gate_protocol_envelope(request),
            gate_contract_shape(request),
            gate_prior_decision(prior),
            gate_no_mutation_request(request),
            gate_executor_scope(request),
            gate_forbidden_outputs(request),
            gate_decision_shape(request),
        ]
    )

    for result in results:
        print_gate(result)

    all_passed = all(result.passed for result in results)

    decision = build_decision(results)
    write_decision(decision)

    print(f"[player_input_listener_executor_request][ALL_GATES] {str(all_passed).lower()}")
    print(json.dumps(decision, indent=2, sort_keys=True))
    print(f"[player_input_listener_executor_request][DECISION_WRITTEN] {DECISION_PATH}")

    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
