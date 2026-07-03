#!/usr/bin/env python3

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

REQUEST_PATH = ROOT / "packets" / "boot" / "BOOT_SCENE_LOAD_EXECUTOR_REQUEST_V1.json"
PRIOR_DECISION_PATH = ROOT / "runtime" / "logs" / "BOOT_SCENE_AUTHORIZATION_DECISION_V1.json"
DECISION_PATH = ROOT / "runtime" / "logs" / "BOOT_SCENE_LOAD_EXECUTOR_DECISION_V1.json"

FORBIDDEN_OUTPUTS = {
    "runtime_mutation",
    "entity_spawn",
    "player_spawn",
    "canon_write",
    "quest_state_write",
    "combat_state_write",
    "inventory_state_write",
    "mesh_generation",
    "asset_generation",
    "freeform_godot_command",
}


@dataclass(frozen=True)
class GateResult:
    passed: bool
    gate_name: str
    message: str
    details: dict[str, Any]


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError("JSON root must be an object.")

    return data


def gate_request_exists() -> GateResult:
    passed = REQUEST_PATH.exists() and REQUEST_PATH.is_file()

    return GateResult(
        passed=passed,
        gate_name="GATE_REQUEST_EXISTS",
        message="Boot scene load executor request exists." if passed else "Boot scene load executor request is missing.",
        details={"request_path": str(REQUEST_PATH)},
    )


def gate_prior_decision_exists() -> GateResult:
    passed = PRIOR_DECISION_PATH.exists() and PRIOR_DECISION_PATH.is_file()

    return GateResult(
        passed=passed,
        gate_name="GATE_PRIOR_DECISION_EXISTS",
        message="Prior boot scene authorization decision exists." if passed else "Prior boot scene authorization decision is missing.",
        details={"prior_decision_path": str(PRIOR_DECISION_PATH)},
    )


def gate_protocol_envelope(request: dict[str, Any]) -> GateResult:
    checks = {
        "protocol_valid": request.get("protocol") == "NGAT-RT",
        "version_valid": request.get("version") == "1.0",
        "tick_valid": request.get("tick") == 0,
        "epoch_valid": request.get("epoch") == "engainos.boot_scene_load_executor_request",
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
    checks["@id_valid"] = payload.get("@id") == "BOOT_SCENE_LOAD_EXECUTOR_REQUEST"
    checks["@when_valid"] = payload.get("@when") == "POST_BOOT_SCENE_AUTHORIZATION"
    checks["@where_valid"] = payload.get("@where") == "engainos.authority_gate"
    checks["request_type_valid"] = payload.get("request_type") == "executor_release_decision"
    checks["execution_scope_valid"] = payload.get("execution_scope") == "presentation_boot_shell_only"

    passed = all(checks.values())

    return GateResult(
        passed=passed,
        gate_name="GATE_CONTRACT_SHAPE",
        message="Contract shape is valid." if passed else "Contract shape is invalid.",
        details=checks,
    )


def gate_prior_decision_matches(prior: dict[str, Any]) -> GateResult:
    checks = {
        "prior_allowed_true": prior.get("allowed") is True,
        "prior_scene_id_valid": prior.get("scene_id") == "engainos.boot.empty",
        "prior_scene_load_authorized_true": prior.get("scene_load_authorized") is True,
        "prior_runtime_mutation_false": prior.get("runtime_mutation_allowed") is False,
        "prior_godot_command_false": prior.get("godot_command_allowed") is False,
        "prior_next_action_valid": prior.get("next_action") == "BOOT_SCENE_LOAD_EXECUTOR_REQUEST_V1",
    }

    passed = all(checks.values())

    return GateResult(
        passed=passed,
        gate_name="GATE_PRIOR_DECISION_MATCHES",
        message="Prior authorization decision permits executor request." if passed else "Prior authorization decision does not permit this executor request.",
        details=checks,
    )


def gate_executor_scope(request: dict[str, Any]) -> GateResult:
    executor = request["payload"].get("executor_request", {})

    checks = {
        "executor_id_valid": executor.get("executor_id") == "boot_scene_load_executor_v1",
        "executor_role_valid": executor.get("executor_role") == "load_empty_boot_shell_presentation_only",
        "requested_scene_id_valid": executor.get("requested_scene_id") == "engainos.boot.empty",
        "requested_scene_type_valid": executor.get("requested_scene_type") == "boot_shell",
        "may_call_godot_true": executor.get("may_call_godot") is True,
        "may_load_scene_true": executor.get("may_load_scene") is True,
        "may_spawn_entities_false": executor.get("may_spawn_entities") is False,
        "may_accept_player_input_false": executor.get("may_accept_player_input") is False,
        "may_mutate_runtime_false": executor.get("may_mutate_runtime") is False,
        "may_write_canon_false": executor.get("may_write_canon") is False,
        "may_write_quest_state_false": executor.get("may_write_quest_state") is False,
        "may_write_combat_state_false": executor.get("may_write_combat_state") is False,
        "may_write_inventory_state_false": executor.get("may_write_inventory_state") is False,
    }

    passed = all(checks.values())

    return GateResult(
        passed=passed,
        gate_name="GATE_EXECUTOR_SCOPE",
        message="Executor scope is limited to empty boot shell presentation." if passed else "Executor scope exceeds allowed boot-shell authority.",
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
        "scene_id_shape_valid": shape.get("scene_id") == "string|null",
        "scene_load_executor_allowed_shape_valid": shape.get("scene_load_executor_allowed") == "bool",
        "godot_command_allowed_shape_valid": shape.get("godot_command_allowed") == "bool",
        "runtime_mutation_allowed_shape_valid": shape.get("runtime_mutation_allowed") == "bool",
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
            "contract": "engainos.boot_scene_load_executor_decision.v1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "allowed": False,
            "reason": "Boot scene load executor request rejected.",
            "blocked_by": failed[0].gate_name,
            "scene_id": None,
            "scene_load_executor_allowed": False,
            "godot_command_allowed": False,
            "runtime_mutation_allowed": False,
            "next_action": "FIX_BOOT_SCENE_LOAD_EXECUTOR_REQUEST"
        }

    return {
        "contract": "engainos.boot_scene_load_executor_decision.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "allowed": True,
        "reason": "Boot scene load executor approved for empty boot shell only.",
        "blocked_by": None,
        "scene_id": "engainos.boot.empty",
        "scene_load_executor_allowed": True,
        "godot_command_allowed": True,
        "runtime_mutation_allowed": False,
        "next_action": "BOOT_SCENE_LOAD_EXECUTOR_V1"
    }


def write_decision(decision: dict[str, Any]) -> None:
    DECISION_PATH.parent.mkdir(parents=True, exist_ok=True)
    DECISION_PATH.write_text(
        json.dumps(decision, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def print_gate(result: GateResult) -> None:
    status = "PASS" if result.passed else "FAIL"
    print(f"[boot_scene_load_executor_request][{result.gate_name}] {status}: {result.message}")
    print(json.dumps(result.details, indent=2, sort_keys=True))


def main() -> int:
    results: list[GateResult] = []

    request_exists = gate_request_exists()
    prior_exists = gate_prior_decision_exists()

    results.extend([request_exists, prior_exists])

    if not request_exists.passed or not prior_exists.passed:
        for result in results:
            print_gate(result)

        decision = build_decision(results)
        write_decision(decision)

        print("[boot_scene_load_executor_request][ALL_GATES] false")
        print(json.dumps(decision, indent=2, sort_keys=True))
        print(f"[boot_scene_load_executor_request][DECISION_WRITTEN] {DECISION_PATH}")
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
                details={"error": str(exc)}
            )
        )

        for result in results:
            print_gate(result)

        decision = build_decision(results)
        write_decision(decision)

        print("[boot_scene_load_executor_request][ALL_GATES] false")
        print(json.dumps(decision, indent=2, sort_keys=True))
        print(f"[boot_scene_load_executor_request][DECISION_WRITTEN] {DECISION_PATH}")
        return 1

    results.extend(
        [
            gate_protocol_envelope(request),
            gate_contract_shape(request),
            gate_prior_decision_matches(prior),
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

    print(f"[boot_scene_load_executor_request][ALL_GATES] {str(all_passed).lower()}")
    print(json.dumps(decision, indent=2, sort_keys=True))
    print(f"[boot_scene_load_executor_request][DECISION_WRITTEN] {DECISION_PATH}")

    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
