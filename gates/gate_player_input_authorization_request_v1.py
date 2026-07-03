#!/usr/bin/env python3

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

REQUEST_PATH = ROOT / "packets" / "input" / "PLAYER_INPUT_AUTHORIZATION_REQUEST_V1.json"
PRIOR_DECISION_PATH = ROOT / "runtime" / "logs" / "BOOT_SHELL_PRESENTATION_READY_DECISION_V1.json"
DECISION_PATH = ROOT / "runtime" / "logs" / "PLAYER_INPUT_AUTHORIZATION_DECISION_V1.json"

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
        "epoch_valid": request.get("epoch") == "engainos.player_input_authorization",
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
        "execution_allowed",
        "input_requested",
        "input_listener_executes_now",
        "issuer",
        "target",
        "prior_decision_required",
        "input_scope",
        "allowed_outputs",
        "forbidden_outputs",
        "expected_decision_shape",
    ]

    checks = {key: key in payload for key in required_keys}
    checks["@id_valid"] = payload.get("@id") == "PLAYER_INPUT_AUTHORIZATION_REQUEST"
    checks["@when_valid"] = payload.get("@when") == "POST_BOOT_SHELL_PRESENTATION_READY"
    checks["@where_valid"] = payload.get("@where") == "engainos.authority_gate"
    checks["request_type_valid"] = payload.get("request_type") == "authority_decision"

    passed = all(checks.values())

    return GateResult(
        passed=passed,
        gate_name="GATE_CONTRACT_SHAPE",
        message="Contract shape is valid." if passed else "Contract shape is invalid.",
        details=checks,
    )


def gate_prior_decision(prior: dict[str, Any]) -> GateResult:
    checks = {
        "contract_valid": prior.get("contract") == "engainos.boot_shell_presentation_ready_decision.v1",
        "allowed_true": prior.get("allowed") is True,
        "status_valid": prior.get("status") == "BOOT_SHELL_PRESENTATION_READY",
        "boot_shell_ready_true": prior.get("boot_shell_presentation_ready") is True,
        "scene_id_valid": prior.get("scene_id") == "engainos.boot.empty",
        "player_spawned_false": prior.get("player_spawned") is False,
        "entities_spawned_false": prior.get("entities_spawned") is False,
        "player_input_allowed_false": prior.get("player_input_allowed") is False,
        "runtime_mutation_allowed_false": prior.get("runtime_mutation_allowed") is False,
        "next_action_valid": prior.get("next_action") == "PLAYER_INPUT_AUTHORIZATION_REQUEST_V1",
    }

    passed = all(checks.values())

    return GateResult(
        passed=passed,
        gate_name="GATE_PRIOR_DECISION",
        message="Prior boot shell readiness decision permits player input authorization request." if passed else "Prior decision does not permit player input authorization.",
        details=checks,
    )


def gate_no_execution_or_mutation(request: dict[str, Any]) -> GateResult:
    payload = request["payload"]

    checks = {
        "mutation_requested_false": payload.get("mutation_requested") is False,
        "execution_allowed_false": payload.get("execution_allowed") is False,
        "input_requested_true": payload.get("input_requested") is True,
        "input_listener_executes_now_false": payload.get("input_listener_executes_now") is False,
    }

    passed = all(checks.values())

    return GateResult(
        passed=passed,
        gate_name="GATE_NO_EXECUTION_OR_MUTATION",
        message="Packet requests authorization only, not execution or mutation." if passed else "Packet attempts execution or mutation.",
        details=checks,
    )


def gate_input_scope(request: dict[str, Any]) -> GateResult:
    scope = request["payload"].get("input_scope", {})

    allowed_input_events = scope.get("allowed_input_events", [])

    checks = {
        "input_mode_valid": scope.get("input_mode") == "boot_shell_input_probe",
        "allowed_input_events_is_list": isinstance(allowed_input_events, list),
        "may_capture_input_true": scope.get("may_capture_input") is True,
        "may_translate_input_to_packet_true": scope.get("may_translate_input_to_packet") is True,
        "may_mutate_runtime_false": scope.get("may_mutate_runtime") is False,
        "may_spawn_player_false": scope.get("may_spawn_player") is False,
        "may_spawn_entities_false": scope.get("may_spawn_entities") is False,
        "may_open_gameplay_loop_false": scope.get("may_open_gameplay_loop") is False,
        "may_write_canon_false": scope.get("may_write_canon") is False,
        "may_write_quest_state_false": scope.get("may_write_quest_state") is False,
        "may_write_combat_state_false": scope.get("may_write_combat_state") is False,
        "may_write_inventory_state_false": scope.get("may_write_inventory_state") is False,
    }

    passed = all(checks.values())

    return GateResult(
        passed=passed,
        gate_name="GATE_INPUT_SCOPE",
        message="Input scope is limited to boot-shell input probe." if passed else "Input scope exceeds boot-shell authority.",
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
        "player_input_authorized_shape_valid": shape.get("player_input_authorized") == "bool",
        "runtime_mutation_allowed_shape_valid": shape.get("runtime_mutation_allowed") == "bool",
        "player_spawn_allowed_shape_valid": shape.get("player_spawn_allowed") == "bool",
        "entity_spawn_allowed_shape_valid": shape.get("entity_spawn_allowed") == "bool",
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
            "contract": "engainos.player_input_authorization_decision.v1",
            "generated_at": utc_now(),
            "allowed": False,
            "status": "PLAYER_INPUT_AUTHORIZATION_BLOCKED",
            "reason": "Player input authorization rejected.",
            "blocked_by": failed[0].gate_name,
            "player_input_authorized": False,
            "runtime_mutation_allowed": False,
            "player_spawn_allowed": False,
            "entity_spawn_allowed": False,
            "gameplay_start_allowed": False,
            "next_action": "FIX_PLAYER_INPUT_AUTHORIZATION_REQUEST",
        }

    return {
        "contract": "engainos.player_input_authorization_decision.v1",
        "generated_at": utc_now(),
        "allowed": True,
        "status": "PLAYER_INPUT_AUTHORIZED_FOR_BOOT_SHELL",
        "reason": "Boot shell may listen for limited player input. Input may be captured and packetized but may not mutate runtime.",
        "blocked_by": None,
        "player_input_authorized": True,
        "input_mode": "boot_shell_input_probe",
        "runtime_mutation_allowed": False,
        "player_spawn_allowed": False,
        "entity_spawn_allowed": False,
        "gameplay_start_allowed": False,
        "next_action": "PLAYER_INPUT_LISTENER_EXECUTOR_REQUEST_V1",
    }


def write_decision(decision: dict[str, Any]) -> None:
    DECISION_PATH.parent.mkdir(parents=True, exist_ok=True)
    DECISION_PATH.write_text(
        json.dumps(decision, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def print_gate(result: GateResult) -> None:
    status = "PASS" if result.passed else "FAIL"
    print(f"[player_input_authorization][{result.gate_name}] {status}: {result.message}")
    print(json.dumps(result.details, indent=2, sort_keys=True))


def main() -> int:
    results: list[GateResult] = []

    file_gates = [
        gate_file_exists(REQUEST_PATH, "GATE_REQUEST_EXISTS", "Player input authorization request"),
        gate_file_exists(PRIOR_DECISION_PATH, "GATE_PRIOR_DECISION_EXISTS", "Boot shell presentation readiness decision"),
    ]

    results.extend(file_gates)

    if not all(result.passed for result in file_gates):
        for result in results:
            print_gate(result)

        decision = build_decision(results)
        write_decision(decision)

        print("[player_input_authorization][ALL_GATES] false")
        print(json.dumps(decision, indent=2, sort_keys=True))
        print(f"[player_input_authorization][DECISION_WRITTEN] {DECISION_PATH}")
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

        print("[player_input_authorization][ALL_GATES] false")
        print(json.dumps(decision, indent=2, sort_keys=True))
        print(f"[player_input_authorization][DECISION_WRITTEN] {DECISION_PATH}")
        return 1

    results.extend(
        [
            gate_protocol_envelope(request),
            gate_contract_shape(request),
            gate_prior_decision(prior),
            gate_no_execution_or_mutation(request),
            gate_input_scope(request),
            gate_forbidden_outputs(request),
            gate_decision_shape(request),
        ]
    )

    for result in results:
        print_gate(result)

    all_passed = all(result.passed for result in results)

    decision = build_decision(results)
    write_decision(decision)

    print(f"[player_input_authorization][ALL_GATES] {str(all_passed).lower()}")
    print(json.dumps(decision, indent=2, sort_keys=True))
    print(f"[player_input_authorization][DECISION_WRITTEN] {DECISION_PATH}")

    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
