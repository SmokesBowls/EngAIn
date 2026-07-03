#!/usr/bin/env python3

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

PACKET_PATH = ROOT / "packets" / "boot" / "BOOT_SCENE_AUTHORIZATION_REQUEST_V1.json"
DECISION_PATH = ROOT / "runtime" / "logs" / "BOOT_SCENE_AUTHORIZATION_DECISION_V1.json"


FORBIDDEN_OUTPUTS = {
    "runtime_mutation",
    "scene_spawn",
    "godot_command_execution",
    "canon_finalization",
    "mesh_generation",
    "asset_generation",
    "quest_state_write",
    "combat_state_write",
    "inventory_state_write",
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


def gate_packet_exists() -> GateResult:
    passed = PACKET_PATH.exists() and PACKET_PATH.is_file()

    return GateResult(
        passed=passed,
        gate_name="GATE_PACKET_EXISTS",
        message="Boot scene authorization packet exists." if passed else "Boot scene authorization packet is missing.",
        details={"packet_path": str(PACKET_PATH)},
    )


def gate_protocol_envelope(packet: dict[str, Any]) -> GateResult:
    checks = {
        "protocol_valid": packet.get("protocol") == "NGAT-RT",
        "version_valid": packet.get("version") == "1.0",
        "tick_valid": packet.get("tick") == 0,
        "epoch_valid": packet.get("epoch") == "engainos.boot_scene_authorization",
        "type_valid": packet.get("type") == "command",
        "payload_is_object": isinstance(packet.get("payload"), dict),
    }

    passed = all(checks.values())

    return GateResult(
        passed=passed,
        gate_name="GATE_PROTOCOL_ENVELOPE",
        message="Protocol envelope is valid." if passed else "Protocol envelope is invalid.",
        details=checks,
    )


def gate_contract_shape(packet: dict[str, Any]) -> GateResult:
    payload = packet.get("payload", {})

    required_keys = [
        "@id",
        "@when",
        "@where",
        "request_type",
        "mutation_requested",
        "execution_allowed",
        "godot_command_requested",
        "issuer",
        "target",
        "requested_scene",
        "reality_context",
        "authority_context",
        "allowed_outputs",
        "forbidden_outputs",
        "ap_preflight",
    ]

    checks = {key: key in payload for key in required_keys}
    checks["@id_valid"] = payload.get("@id") == "BOOT_SCENE_AUTHORIZATION_REQUEST"
    checks["@when_valid"] = payload.get("@when") == "POST_SYSTEM_HEALTH_PREFLIGHT"
    checks["@where_valid"] = payload.get("@where") == "engainos.authority_gate"
    checks["request_type_valid"] = payload.get("request_type") == "authority_decision"

    passed = all(checks.values())

    return GateResult(
        passed=passed,
        gate_name="GATE_CONTRACT_SHAPE",
        message="Contract shape is valid." if passed else "Contract shape is invalid.",
        details=checks,
    )


def gate_no_runtime_mutation(packet: dict[str, Any]) -> GateResult:
    payload = packet["payload"]
    reality = payload.get("reality_context", {})

    checks = {
        "mutation_requested_false": payload.get("mutation_requested") is False,
        "execution_allowed_false": payload.get("execution_allowed") is False,
        "godot_command_requested_false": payload.get("godot_command_requested") is False,
        "canon_write_false": reality.get("canon_write") is False,
        "runtime_write_false": reality.get("runtime_write") is False,
        "replay_write_false": reality.get("replay_write") is False,
        "scene_load_requested_true": reality.get("scene_load_requested") is True,
        "scene_load_executes_now_false": reality.get("scene_load_executes_now") is False,
    }

    passed = all(checks.values())

    return GateResult(
        passed=passed,
        gate_name="GATE_NO_RUNTIME_MUTATION",
        message="Request asks for authorization only and performs no mutation." if passed else "Request attempts execution or mutation.",
        details=checks,
    )


def gate_boot_scene_scope(packet: dict[str, Any]) -> GateResult:
    scene = packet["payload"].get("requested_scene", {})

    checks = {
        "scene_id_valid": scene.get("scene_id") == "engainos.boot.empty",
        "scene_type_valid": scene.get("scene_type") == "boot_shell",
        "allows_player_input_false": scene.get("allows_player_input") is False,
        "allows_runtime_mutation_false": scene.get("allows_runtime_mutation") is False,
        "allows_spawn_false": scene.get("allows_spawn") is False,
        "allows_canon_write_false": scene.get("allows_canon_write") is False,
        "allows_quest_state_false": scene.get("allows_quest_state") is False,
        "allows_combat_state_false": scene.get("allows_combat_state") is False,
        "allows_inventory_state_false": scene.get("allows_inventory_state") is False,
    }

    passed = all(checks.values())

    return GateResult(
        passed=passed,
        gate_name="GATE_BOOT_SCENE_SCOPE",
        message="Requested boot scene is a non-mutating boot shell." if passed else "Requested boot scene exceeds boot-shell authority.",
        details=checks,
    )


def gate_authority_context(packet: dict[str, Any]) -> GateResult:
    authority = packet["payload"].get("authority_context", {})

    required_sequence = [
        "protocol_envelope_validation",
        "contract_shape_validation",
        "no_runtime_mutation_validation",
        "boot_scene_scope_validation",
        "authorization_decision_report",
    ]

    checks = {
        "tier_valid": authority.get("tier") == "TIER1",
        "authority_owner_valid": authority.get("authority_owner") == "EngAInOS",
        "truth_anchor_required": authority.get("truth_anchor_required") is True,
        "truth_anchor_valid": authority.get("truth_anchor") == "ENGAINOS_BOOT_SCENE_AUTHORITY_BOUNDARY",
        "required_gate_sequence_valid": authority.get("required_gate_sequence") == required_sequence,
    }

    passed = all(checks.values())

    return GateResult(
        passed=passed,
        gate_name="GATE_AUTHORITY_CONTEXT",
        message="Authority context is valid." if passed else "Authority context is invalid.",
        details=checks,
    )


def gate_forbidden_outputs(packet: dict[str, Any]) -> GateResult:
    payload = packet["payload"]

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
        message="Forbidden outputs are declared and not allowed." if passed else "Forbidden outputs are incomplete or allowed unsafely.",
        details={
            "checks": checks,
            "missing_forbidden": missing_forbidden,
            "unsafe_allowed": unsafe_allowed,
        },
    )


def gate_ap_preflight(packet: dict[str, Any]) -> GateResult:
    ap = packet["payload"].get("ap_preflight", {})
    shape = ap.get("expected_decision_shape", {})

    checks = {
        "decision_requested_true": ap.get("decision_requested") is True,
        "requested_decision_valid": ap.get("requested_decision") == "MAY_BOOT_SCENE_LOAD",
        "allowed_shape_valid": shape.get("allowed") == "bool",
        "reason_shape_valid": shape.get("reason") == "string",
        "blocked_by_shape_valid": shape.get("blocked_by") == "string|null",
        "scene_load_authorized_shape_valid": shape.get("scene_load_authorized") == "bool",
        "runtime_mutation_allowed_shape_valid": shape.get("runtime_mutation_allowed") == "bool",
        "godot_command_allowed_shape_valid": shape.get("godot_command_allowed") == "bool",
        "next_action_shape_valid": shape.get("next_action") == "string|null",
    }

    passed = all(checks.values())

    return GateResult(
        passed=passed,
        gate_name="GATE_AP_PREFLIGHT",
        message="AP preflight decision request is valid." if passed else "AP preflight decision request is invalid.",
        details=checks,
    )


def build_decision(results: list[GateResult]) -> dict[str, Any]:
    failed = [result for result in results if not result.passed]

    if failed:
        return {
            "contract": "engainos.boot_scene_authorization_decision.v1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "allowed": False,
            "reason": "Boot scene authorization rejected.",
            "blocked_by": failed[0].gate_name,
            "scene_id": None,
            "scene_load_authorized": False,
            "runtime_mutation_allowed": False,
            "godot_command_allowed": False,
            "next_action": "FIX_BOOT_SCENE_AUTHORIZATION_PACKET"
        }

    return {
        "contract": "engainos.boot_scene_authorization_decision.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "allowed": True,
        "reason": "Boot scene authorization approved. A later executor may load the empty boot shell only.",
        "blocked_by": None,
        "scene_id": "engainos.boot.empty",
        "scene_load_authorized": True,
        "runtime_mutation_allowed": False,
        "godot_command_allowed": False,
        "next_action": "BOOT_SCENE_LOAD_EXECUTOR_REQUEST_V1"
    }


def write_decision(decision: dict[str, Any]) -> None:
    DECISION_PATH.parent.mkdir(parents=True, exist_ok=True)
    DECISION_PATH.write_text(
        json.dumps(decision, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def print_gate(result: GateResult) -> None:
    status = "PASS" if result.passed else "FAIL"
    print(f"[boot_scene_authorization][{result.gate_name}] {status}: {result.message}")
    print(json.dumps(result.details, indent=2, sort_keys=True))


def main() -> int:
    results: list[GateResult] = []

    packet_exists = gate_packet_exists()
    results.append(packet_exists)

    if not packet_exists.passed:
        for result in results:
            print_gate(result)

        decision = build_decision(results)
        write_decision(decision)

        print("[boot_scene_authorization][ALL_GATES] false")
        print(json.dumps(decision, indent=2, sort_keys=True))
        print(f"[boot_scene_authorization][DECISION_WRITTEN] {DECISION_PATH}")
        return 1

    try:
        packet = load_json(PACKET_PATH)
    except Exception as exc:
        results.append(
            GateResult(
                passed=False,
                gate_name="GATE_PACKET_JSON_PARSE",
                message="Boot scene authorization packet could not be parsed.",
                details={"error": str(exc), "packet_path": str(PACKET_PATH)},
            )
        )

        for result in results:
            print_gate(result)

        decision = build_decision(results)
        write_decision(decision)

        print("[boot_scene_authorization][ALL_GATES] false")
        print(json.dumps(decision, indent=2, sort_keys=True))
        print(f"[boot_scene_authorization][DECISION_WRITTEN] {DECISION_PATH}")
        return 1

    results.extend(
        [
            gate_protocol_envelope(packet),
            gate_contract_shape(packet),
            gate_no_runtime_mutation(packet),
            gate_boot_scene_scope(packet),
            gate_authority_context(packet),
            gate_forbidden_outputs(packet),
            gate_ap_preflight(packet),
        ]
    )

    for result in results:
        print_gate(result)

    all_passed = all(result.passed for result in results)
    decision = build_decision(results)
    write_decision(decision)

    print(f"[boot_scene_authorization][ALL_GATES] {str(all_passed).lower()}")
    print(json.dumps(decision, indent=2, sort_keys=True))
    print(f"[boot_scene_authorization][DECISION_WRITTEN] {DECISION_PATH}")

    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
