#!/usr/bin/env python3

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

KERNEL_REPORT_PATH = ROOT / "runtime" / "logs" / "ENGAINOS_BOOT_KERNEL_LAST_RUN.json"
GODOT_REPORT_PATH = ROOT / "runtime" / "godot_reports" / "GODOT_BOOT_BRIDGE_CONSUME_COMMAND_V1.report.json"
GODOT_COMMAND_PATH = ROOT / "runtime" / "godot_commands" / "BOOT_SCENE_LOAD_COMMAND_V1.json"

DECISION_PATH = ROOT / "runtime" / "logs" / "BOOT_SHELL_PRESENTATION_READY_DECISION_V1.json"

EXPECTED_SCENE_ID = "engainos.boot.empty"
EXPECTED_SCENE_RESOURCE_PATH = "res://scenes/EngAInOSBootShell.tscn"


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


def gate_kernel_report(kernel_report: dict[str, Any]) -> GateResult:
    checks = {
        "contract_valid": kernel_report.get("contract") == "engainos.boot_kernel_report.v1",
        "kernel_status_complete": kernel_report.get("kernel_status") == "BOOT_SEQUENCE_COMPLETE",
        "exit_code_zero": kernel_report.get("exit_code") == 0,
        "godot_command_allowed_true": kernel_report.get("godot_command_allowed") is True,
        "runtime_mutation_allowed_false": kernel_report.get("runtime_mutation_allowed") is False,
        "next_action_valid": kernel_report.get("next_action") == "GODOT_BOOT_BRIDGE_CONSUME_COMMAND_V1"
            or kernel_report.get("next_action") == "BOOT_SHELL_PRESENTATION_READY_V1",
    }

    passed = all(checks.values())

    return GateResult(
        passed=passed,
        gate_name="GATE_KERNEL_REPORT",
        message="Kernel report supports boot-shell presentation readiness." if passed else "Kernel report does not support readiness.",
        details=checks,
    )


def gate_godot_command(command: dict[str, Any]) -> GateResult:
    checks = {
        "contract_valid": command.get("contract") == "engainos.godot_boot_shell_command.v1",
        "command_type_valid": command.get("command_type") == "LOAD_BOOT_SHELL_SCENE",
        "scene_id_valid": command.get("scene_id") == EXPECTED_SCENE_ID,
        "scene_resource_path_valid": command.get("scene_resource_path") == EXPECTED_SCENE_RESOURCE_PATH,
        "permits_runtime_mutation_false": command.get("permits_runtime_mutation") is False,
        "permits_entity_spawn_false": command.get("permits_entity_spawn") is False,
        "permits_player_spawn_false": command.get("permits_player_spawn") is False,
        "permits_player_input_false": command.get("permits_player_input") is False,
        "permits_canon_write_false": command.get("permits_canon_write") is False,
        "permits_quest_state_write_false": command.get("permits_quest_state_write") is False,
        "permits_combat_state_write_false": command.get("permits_combat_state_write") is False,
        "permits_inventory_state_write_false": command.get("permits_inventory_state_write") is False,
    }

    passed = all(checks.values())

    return GateResult(
        passed=passed,
        gate_name="GATE_GODOT_COMMAND",
        message="Godot command is boot-shell only." if passed else "Godot command exceeds boot-shell authority.",
        details=checks,
    )


def gate_godot_report(godot_report: dict[str, Any]) -> GateResult:
    checks = {
        "contract_valid": godot_report.get("contract") == "godot.boot_bridge_consume_command_report.v1",
        "ok_true": godot_report.get("ok") is True,
        "status_valid": godot_report.get("status") == "GODOT_BOOT_BRIDGE_CONSUMED_COMMAND",
        "scene_id_valid": godot_report.get("scene_id") == EXPECTED_SCENE_ID,
        "scene_resource_path_valid": godot_report.get("scene_resource_path") == EXPECTED_SCENE_RESOURCE_PATH,
        "runtime_mutation_allowed_false": godot_report.get("runtime_mutation_allowed") is False,
        "player_spawned_false": godot_report.get("player_spawned") is False,
        "entities_spawned_false": godot_report.get("entities_spawned") is False,
        "player_input_allowed_false": godot_report.get("player_input_allowed") is False,
        "next_action_valid": godot_report.get("next_action") == "BOOT_SHELL_PRESENTATION_READY_V1",
    }

    passed = all(checks.values())

    return GateResult(
        passed=passed,
        gate_name="GATE_GODOT_REPORT",
        message="Godot report proves empty boot shell presentation is ready." if passed else "Godot report does not prove safe boot shell readiness.",
        details=checks,
    )


def gate_report_not_stale() -> GateResult:
    try:
        command_mtime = GODOT_COMMAND_PATH.stat().st_mtime
        report_mtime = GODOT_REPORT_PATH.stat().st_mtime
        report_newer_or_equal = report_mtime >= command_mtime
    except Exception as exc:
        return GateResult(
            passed=False,
            gate_name="GATE_REPORT_NOT_STALE",
            message="Could not compare command/report timestamps.",
            details={"error": str(exc)},
        )

    return GateResult(
        passed=report_newer_or_equal,
        gate_name="GATE_REPORT_NOT_STALE",
        message="Godot report is current for the command packet." if report_newer_or_equal else "Godot report is older than the command packet.",
        details={
            "command_mtime": command_mtime,
            "report_mtime": report_mtime,
            "report_newer_or_equal": report_newer_or_equal,
        },
    )


def build_decision(results: list[GateResult]) -> dict[str, Any]:
    failed = [result for result in results if not result.passed]

    if failed:
        return {
            "contract": "engainos.boot_shell_presentation_ready_decision.v1",
            "generated_at": utc_now(),
            "allowed": False,
            "status": "BOOT_SHELL_PRESENTATION_BLOCKED",
            "reason": "Boot shell presentation readiness rejected.",
            "blocked_by": failed[0].gate_name,
            "scene_id": None,
            "boot_shell_presentation_ready": False,
            "player_spawned": False,
            "entities_spawned": False,
            "player_input_allowed": False,
            "runtime_mutation_allowed": False,
            "next_action": "FIX_BOOT_SHELL_PRESENTATION_READY_PROOF",
        }

    return {
        "contract": "engainos.boot_shell_presentation_ready_decision.v1",
        "generated_at": utc_now(),
        "allowed": True,
        "status": "BOOT_SHELL_PRESENTATION_READY",
        "reason": "Empty boot shell is loaded and safe. No actor, input, spawn, or runtime mutation is present.",
        "blocked_by": None,
        "scene_id": EXPECTED_SCENE_ID,
        "boot_shell_presentation_ready": True,
        "player_spawned": False,
        "entities_spawned": False,
        "player_input_allowed": False,
        "runtime_mutation_allowed": False,
        "next_action": "PLAYER_INPUT_AUTHORIZATION_REQUEST_V1",
    }


def write_decision(decision: dict[str, Any]) -> None:
    DECISION_PATH.parent.mkdir(parents=True, exist_ok=True)
    DECISION_PATH.write_text(
        json.dumps(decision, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def print_gate(result: GateResult) -> None:
    status = "PASS" if result.passed else "FAIL"
    print(f"[boot_shell_presentation_ready][{result.gate_name}] {status}: {result.message}")
    print(json.dumps(result.details, indent=2, sort_keys=True))


def main() -> int:
    results: list[GateResult] = []

    file_gates = [
        gate_file_exists(KERNEL_REPORT_PATH, "GATE_KERNEL_REPORT_EXISTS", "Kernel report"),
        gate_file_exists(GODOT_COMMAND_PATH, "GATE_GODOT_COMMAND_EXISTS", "Godot command packet"),
        gate_file_exists(GODOT_REPORT_PATH, "GATE_GODOT_REPORT_EXISTS", "Godot bridge report"),
    ]

    results.extend(file_gates)

    if not all(result.passed for result in file_gates):
        for result in results:
            print_gate(result)

        decision = build_decision(results)
        write_decision(decision)

        print("[boot_shell_presentation_ready][ALL_GATES] false")
        print(json.dumps(decision, indent=2, sort_keys=True))
        print(f"[boot_shell_presentation_ready][DECISION_WRITTEN] {DECISION_PATH}")
        return 1

    try:
        kernel_report = load_json(KERNEL_REPORT_PATH)
        godot_command = load_json(GODOT_COMMAND_PATH)
        godot_report = load_json(GODOT_REPORT_PATH)
    except Exception as exc:
        results.append(
            GateResult(
                passed=False,
                gate_name="GATE_JSON_PARSE",
                message="One or more readiness proof files could not be parsed.",
                details={"error": str(exc)},
            )
        )

        for result in results:
            print_gate(result)

        decision = build_decision(results)
        write_decision(decision)

        print("[boot_shell_presentation_ready][ALL_GATES] false")
        print(json.dumps(decision, indent=2, sort_keys=True))
        print(f"[boot_shell_presentation_ready][DECISION_WRITTEN] {DECISION_PATH}")
        return 1

    results.extend(
        [
            gate_kernel_report(kernel_report),
            gate_godot_command(godot_command),
            gate_godot_report(godot_report),
            gate_report_not_stale(),
        ]
    )

    for result in results:
        print_gate(result)

    all_passed = all(result.passed for result in results)

    decision = build_decision(results)
    write_decision(decision)

    print(f"[boot_shell_presentation_ready][ALL_GATES] {str(all_passed).lower()}")
    print(json.dumps(decision, indent=2, sort_keys=True))
    print(f"[boot_shell_presentation_ready][DECISION_WRITTEN] {DECISION_PATH}")

    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
