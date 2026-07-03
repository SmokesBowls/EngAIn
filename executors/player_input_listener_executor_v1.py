#!/usr/bin/env python3

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

PRIOR_DECISION_PATH = ROOT / "runtime" / "logs" / "PLAYER_INPUT_LISTENER_EXECUTOR_DECISION_V1.json"

COMMAND_DIR = ROOT / "runtime" / "godot_commands"
COMMAND_PATH = COMMAND_DIR / "PLAYER_INPUT_LISTENER_COMMAND_V1.json"

REPORT_PATH = ROOT / "runtime" / "logs" / "PLAYER_INPUT_LISTENER_EXECUTOR_V1.report.json"

INPUT_PACKET_DIR = ROOT / "runtime" / "input_packets"
INPUT_PACKET_PATH = INPUT_PACKET_DIR / "PLAYER_INPUT_PACKET_V1.json"

BOOT_SCENE_ID = "engainos.boot.empty"
INPUT_MODE = "boot_shell_input_probe"

FORBIDDEN_EXECUTOR_ACTIONS = {
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
class CheckResult:
    passed: bool
    check_name: str
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


def check_prior_decision_exists() -> CheckResult:
    passed = PRIOR_DECISION_PATH.exists() and PRIOR_DECISION_PATH.is_file()

    return CheckResult(
        passed=passed,
        check_name="CHECK_PRIOR_DECISION_EXISTS",
        message="Prior input listener executor decision exists." if passed else "Prior input listener executor decision is missing.",
        details={"prior_decision_path": str(PRIOR_DECISION_PATH)},
    )


def check_prior_decision_allows_execution(decision: dict[str, Any]) -> CheckResult:
    checks = {
        "contract_valid": decision.get("contract") == "engainos.player_input_listener_executor_decision.v1",
        "allowed_true": decision.get("allowed") is True,
        "status_valid": decision.get("status") == "PLAYER_INPUT_LISTENER_EXECUTOR_AUTHORIZED",
        "input_listener_executor_allowed_true": decision.get("input_listener_executor_allowed") is True,
        "godot_command_allowed_true": decision.get("godot_command_allowed") is True,
        "runtime_mutation_allowed_false": decision.get("runtime_mutation_allowed") is False,
        "player_spawn_allowed_false": decision.get("player_spawn_allowed") is False,
        "entity_spawn_allowed_false": decision.get("entity_spawn_allowed") is False,
        "gameplay_start_allowed_false": decision.get("gameplay_start_allowed") is False,
        "next_action_valid": decision.get("next_action") == "PLAYER_INPUT_LISTENER_EXECUTOR_V1",
    }

    passed = all(checks.values())

    return CheckResult(
        passed=passed,
        check_name="CHECK_PRIOR_DECISION_ALLOWS_EXECUTION",
        message="Prior decision allows player input listener executor." if passed else "Prior decision does not allow player input listener executor.",
        details=checks,
    )


def build_command_packet(*, dry_run: bool) -> dict[str, Any]:
    return {
        "contract": "engainos.godot_player_input_listener_command.v1",
        "generated_at": utc_now(),
        "generated_by": "PLAYER_INPUT_LISTENER_EXECUTOR_V1",
        "dry_run": dry_run,

        "command_type": "ATTACH_BOOT_SHELL_INPUT_LISTENER",
        "scene_id": BOOT_SCENE_ID,
        "input_mode": INPUT_MODE,

        "allowed_input_events": [
            "ui_accept",
            "ui_cancel",
            "text_submitted"
        ],

        "allowed_actions": [
            "godot_attach_boot_shell_input_listener",
            "godot_capture_boot_shell_input",
            "godot_write_player_input_packet"
        ],

        "forbidden_actions": sorted(FORBIDDEN_EXECUTOR_ACTIONS),

        "input_packet_contract": "engainos.player_input_packet.v1",
        "input_packet_path": "res://runtime/input_packets/PLAYER_INPUT_PACKET_V1.json",

        "permits_runtime_mutation": False,
        "permits_player_spawn": False,
        "permits_entity_spawn": False,
        "permits_gameplay_start": False,
        "permits_canon_write": False,
        "permits_quest_state_write": False,
        "permits_combat_state_write": False,
        "permits_inventory_state_write": False,

        "proof": {
            "prior_decision_path": str(PRIOR_DECISION_PATH),
            "executor_report_path": str(REPORT_PATH),
            "command_path": str(COMMAND_PATH),
            "input_packet_path": str(INPUT_PACKET_PATH),
            "note": "This command only permits boot-shell input capture and packet writing. It does not permit runtime mutation."
        }
    }


def check_command_scope() -> CheckResult:
    command = build_command_packet(dry_run=True)

    forbidden_flags = {
        "permits_runtime_mutation": command.get("permits_runtime_mutation"),
        "permits_player_spawn": command.get("permits_player_spawn"),
        "permits_entity_spawn": command.get("permits_entity_spawn"),
        "permits_gameplay_start": command.get("permits_gameplay_start"),
        "permits_canon_write": command.get("permits_canon_write"),
        "permits_quest_state_write": command.get("permits_quest_state_write"),
        "permits_combat_state_write": command.get("permits_combat_state_write"),
        "permits_inventory_state_write": command.get("permits_inventory_state_write"),
    }

    checks = {
        "contract_valid": command.get("contract") == "engainos.godot_player_input_listener_command.v1",
        "command_type_valid": command.get("command_type") == "ATTACH_BOOT_SHELL_INPUT_LISTENER",
        "scene_id_valid": command.get("scene_id") == BOOT_SCENE_ID,
        "input_mode_valid": command.get("input_mode") == INPUT_MODE,
        "input_packet_contract_valid": command.get("input_packet_contract") == "engainos.player_input_packet.v1",
        "all_forbidden_permissions_false": all(value is False for value in forbidden_flags.values()),
        "allowed_actions_exact": command.get("allowed_actions") == [
            "godot_attach_boot_shell_input_listener",
            "godot_capture_boot_shell_input",
            "godot_write_player_input_packet"
        ],
        "forbidden_actions_complete": set(command.get("forbidden_actions", [])) == FORBIDDEN_EXECUTOR_ACTIONS,
    }

    passed = all(checks.values())

    return CheckResult(
        passed=passed,
        check_name="CHECK_COMMAND_SCOPE",
        message="Godot input listener command scope is boot-shell input only." if passed else "Godot input listener command scope is unsafe.",
        details={
            "checks": checks,
            "forbidden_flags": forbidden_flags,
        },
    )


def write_command_packet(command: dict[str, Any]) -> None:
    COMMAND_DIR.mkdir(parents=True, exist_ok=True)
    COMMAND_PATH.write_text(
        json.dumps(command, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def write_report(
    *,
    status: str,
    exit_code: int,
    checks: list[CheckResult],
    command_written: bool,
) -> None:
    report = {
        "contract": "engainos.player_input_listener_executor_report.v1",
        "generated_at": utc_now(),
        "executor_id": "PLAYER_INPUT_LISTENER_EXECUTOR_V1",
        "status": status,
        "exit_code": exit_code,

        "scene_id": BOOT_SCENE_ID,
        "input_mode": INPUT_MODE,

        "command_written": command_written,
        "command_path": str(COMMAND_PATH) if command_written else None,

        "input_packet_path": str(INPUT_PACKET_PATH),
        "godot_command_allowed": command_written,
        "runtime_mutation_allowed": False,
        "player_spawn_allowed": False,
        "entity_spawn_allowed": False,
        "gameplay_start_allowed": False,

        "next_action": "GODOT_INPUT_LISTENER_BRIDGE_CONSUME_COMMAND_V1" if command_written else "FIX_PLAYER_INPUT_LISTENER_EXECUTOR_V1",

        "checks": [
            {
                "check_name": check.check_name,
                "passed": check.passed,
                "message": check.message,
                "details": check.details,
            }
            for check in checks
        ],
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(report, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def print_check(check: CheckResult) -> None:
    status = "PASS" if check.passed else "FAIL"
    print(f"[player_input_listener_executor][{check.check_name}] {status}: {check.message}")
    print(json.dumps(check.details, indent=2, sort_keys=True))


def main() -> int:
    checks: list[CheckResult] = []

    prior_exists = check_prior_decision_exists()
    checks.append(prior_exists)

    if not prior_exists.passed:
        for check in checks:
            print_check(check)

        write_report(
            status="PLAYER_INPUT_LISTENER_EXECUTOR_BLOCKED",
            exit_code=1,
            checks=checks,
            command_written=False,
        )

        print("[player_input_listener_executor][ALL_CHECKS] false")
        print(f"[player_input_listener_executor][REPORT_WRITTEN] {REPORT_PATH}")
        return 1

    try:
        prior_decision = load_json(PRIOR_DECISION_PATH)
    except Exception as exc:
        checks.append(
            CheckResult(
                passed=False,
                check_name="CHECK_PRIOR_DECISION_PARSE",
                message="Prior executor decision could not be parsed.",
                details={"error": str(exc), "prior_decision_path": str(PRIOR_DECISION_PATH)},
            )
        )

        for check in checks:
            print_check(check)

        write_report(
            status="PLAYER_INPUT_LISTENER_EXECUTOR_BLOCKED",
            exit_code=1,
            checks=checks,
            command_written=False,
        )

        print("[player_input_listener_executor][ALL_CHECKS] false")
        print(f"[player_input_listener_executor][REPORT_WRITTEN] {REPORT_PATH}")
        return 1

    checks.extend(
        [
            check_prior_decision_allows_execution(prior_decision),
            check_command_scope(),
        ]
    )

    for check in checks:
        print_check(check)

    all_passed = all(check.passed for check in checks)

    if not all_passed:
        write_report(
            status="PLAYER_INPUT_LISTENER_EXECUTOR_BLOCKED",
            exit_code=1,
            checks=checks,
            command_written=False,
        )

        print("[player_input_listener_executor][ALL_CHECKS] false")
        print(f"[player_input_listener_executor][REPORT_WRITTEN] {REPORT_PATH}")
        return 1

    INPUT_PACKET_DIR.mkdir(parents=True, exist_ok=True)

    command = build_command_packet(dry_run=False)
    write_command_packet(command)

    write_report(
        status="PLAYER_INPUT_LISTENER_EXECUTOR_COMPLETE",
        exit_code=0,
        checks=checks,
        command_written=True,
    )

    print("[player_input_listener_executor][COMMAND_WRITTEN]", COMMAND_PATH)
    print("[player_input_listener_executor][ALL_CHECKS] true")
    print("[player_input_listener_executor][NEXT_ACTION] GODOT_INPUT_LISTENER_BRIDGE_CONSUME_COMMAND_V1")
    print("[player_input_listener_executor][RUNTIME_MUTATION_ALLOWED] false")
    print(f"[player_input_listener_executor][REPORT_WRITTEN] {REPORT_PATH}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
