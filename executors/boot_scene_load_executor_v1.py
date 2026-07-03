#!/usr/bin/env python3

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

PRIOR_DECISION_PATH = ROOT / "runtime" / "logs" / "BOOT_SCENE_LOAD_EXECUTOR_DECISION_V1.json"

COMMAND_DIR = ROOT / "runtime" / "godot_commands"
COMMAND_PATH = COMMAND_DIR / "BOOT_SCENE_LOAD_COMMAND_V1.json"

REPORT_PATH = ROOT / "runtime" / "logs" / "BOOT_SCENE_LOAD_EXECUTOR_V1.report.json"


BOOT_SCENE_ID = "engainos.boot.empty"
BOOT_SCENE_RESOURCE_PATH = "res://scenes/EngAInOSBootShell.tscn"

FORBIDDEN_EXECUTOR_ACTIONS = {
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
        message="Prior executor decision exists." if passed else "Prior executor decision is missing.",
        details={"prior_decision_path": str(PRIOR_DECISION_PATH)},
    )


def check_prior_decision_allows_execution(decision: dict[str, Any]) -> CheckResult:
    checks = {
        "contract_valid": decision.get("contract") == "engainos.boot_scene_load_executor_decision.v1",
        "allowed_true": decision.get("allowed") is True,
        "scene_id_valid": decision.get("scene_id") == BOOT_SCENE_ID,
        "scene_load_executor_allowed_true": decision.get("scene_load_executor_allowed") is True,
        "godot_command_allowed_true": decision.get("godot_command_allowed") is True,
        "runtime_mutation_allowed_false": decision.get("runtime_mutation_allowed") is False,
        "next_action_valid": decision.get("next_action") == "BOOT_SCENE_LOAD_EXECUTOR_V1",
    }

    passed = all(checks.values())

    return CheckResult(
        passed=passed,
        check_name="CHECK_PRIOR_DECISION_ALLOWS_EXECUTION",
        message="Prior decision allows boot scene load executor." if passed else "Prior decision does not allow boot scene load executor.",
        details=checks,
    )


def check_command_scope() -> CheckResult:
    command = build_command_packet(dry_run=True)

    forbidden_flags = {
        "permits_runtime_mutation": command.get("permits_runtime_mutation"),
        "permits_entity_spawn": command.get("permits_entity_spawn"),
        "permits_player_spawn": command.get("permits_player_spawn"),
        "permits_player_input": command.get("permits_player_input"),
        "permits_canon_write": command.get("permits_canon_write"),
        "permits_quest_state_write": command.get("permits_quest_state_write"),
        "permits_combat_state_write": command.get("permits_combat_state_write"),
        "permits_inventory_state_write": command.get("permits_inventory_state_write"),
    }

    checks = {
        "contract_valid": command.get("contract") == "engainos.godot_boot_shell_command.v1",
        "command_type_valid": command.get("command_type") == "LOAD_BOOT_SHELL_SCENE",
        "scene_id_valid": command.get("scene_id") == BOOT_SCENE_ID,
        "scene_resource_path_valid": command.get("scene_resource_path") == BOOT_SCENE_RESOURCE_PATH,
        "all_forbidden_permissions_false": all(value is False for value in forbidden_flags.values()),
        "allowed_actions_exact": command.get("allowed_actions") == [
            "godot_load_declared_empty_boot_shell"
        ],
        "forbidden_actions_complete": set(command.get("forbidden_actions", [])) == FORBIDDEN_EXECUTOR_ACTIONS,
    }

    passed = all(checks.values())

    return CheckResult(
        passed=passed,
        check_name="CHECK_COMMAND_SCOPE",
        message="Godot command packet scope is boot-shell only." if passed else "Godot command packet scope is unsafe.",
        details={
            "checks": checks,
            "forbidden_flags": forbidden_flags,
        },
    )


def build_command_packet(*, dry_run: bool = False) -> dict[str, Any]:
    return {
        "contract": "engainos.godot_boot_shell_command.v1",
        "generated_at": utc_now(),
        "generated_by": "BOOT_SCENE_LOAD_EXECUTOR_V1",
        "dry_run": dry_run,

        "command_type": "LOAD_BOOT_SHELL_SCENE",
        "scene_id": BOOT_SCENE_ID,
        "scene_resource_path": BOOT_SCENE_RESOURCE_PATH,
        "scene_type": "boot_shell",

        "allowed_actions": [
            "godot_load_declared_empty_boot_shell"
        ],

        "forbidden_actions": sorted(FORBIDDEN_EXECUTOR_ACTIONS),

        "permits_runtime_mutation": False,
        "permits_entity_spawn": False,
        "permits_player_spawn": False,
        "permits_player_input": False,
        "permits_canon_write": False,
        "permits_quest_state_write": False,
        "permits_combat_state_write": False,
        "permits_inventory_state_write": False,

        "proof": {
            "prior_decision_path": str(PRIOR_DECISION_PATH),
            "executor_report_path": str(REPORT_PATH),
            "command_path": str(COMMAND_PATH),
            "note": "This command is presentation-only. It may load an empty boot shell scene and nothing else."
        }
    }


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
        "contract": "engainos.boot_scene_load_executor_report.v1",
        "generated_at": utc_now(),
        "executor_id": "BOOT_SCENE_LOAD_EXECUTOR_V1",
        "status": status,
        "exit_code": exit_code,

        "scene_id": BOOT_SCENE_ID,
        "scene_resource_path": BOOT_SCENE_RESOURCE_PATH,

        "command_written": command_written,
        "command_path": str(COMMAND_PATH) if command_written else None,

        "godot_command_allowed": command_written,
        "runtime_mutation_allowed": False,
        "scene_load_executor_ran": command_written,

        "next_action": "GODOT_BOOT_BRIDGE_CONSUME_COMMAND_V1" if command_written else "FIX_BOOT_SCENE_LOAD_EXECUTOR_V1",

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
    print(f"[boot_scene_load_executor][{check.check_name}] {status}: {check.message}")
    print(json.dumps(check.details, indent=2, sort_keys=True))


def main() -> int:
    checks: list[CheckResult] = []

    prior_exists = check_prior_decision_exists()
    checks.append(prior_exists)

    if not prior_exists.passed:
        for check in checks:
            print_check(check)

        write_report(
            status="BOOT_SCENE_LOAD_EXECUTOR_BLOCKED",
            exit_code=1,
            checks=checks,
            command_written=False,
        )

        print("[boot_scene_load_executor][ALL_CHECKS] false")
        print(f"[boot_scene_load_executor][REPORT_WRITTEN] {REPORT_PATH}")
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
            status="BOOT_SCENE_LOAD_EXECUTOR_BLOCKED",
            exit_code=1,
            checks=checks,
            command_written=False,
        )

        print("[boot_scene_load_executor][ALL_CHECKS] false")
        print(f"[boot_scene_load_executor][REPORT_WRITTEN] {REPORT_PATH}")
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
            status="BOOT_SCENE_LOAD_EXECUTOR_BLOCKED",
            exit_code=1,
            checks=checks,
            command_written=False,
        )

        print("[boot_scene_load_executor][ALL_CHECKS] false")
        print(f"[boot_scene_load_executor][REPORT_WRITTEN] {REPORT_PATH}")
        return 1

    command = build_command_packet(dry_run=False)
    write_command_packet(command)

    write_report(
        status="BOOT_SCENE_LOAD_EXECUTOR_COMPLETE",
        exit_code=0,
        checks=checks,
        command_written=True,
    )

    print("[boot_scene_load_executor][COMMAND_WRITTEN]", COMMAND_PATH)
    print("[boot_scene_load_executor][ALL_CHECKS] true")
    print("[boot_scene_load_executor][NEXT_ACTION] GODOT_BOOT_BRIDGE_CONSUME_COMMAND_V1")
    print("[boot_scene_load_executor][RUNTIME_MUTATION_ALLOWED] false")
    print(f"[boot_scene_load_executor][REPORT_WRITTEN] {REPORT_PATH}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
