#!/usr/bin/env python3

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------
# ENGAINOS BOOT KERNEL
#
# This is NOT a gate.
# This is NOT gameplay.
# This is NOT Godot execution.
# This is NOT authority by itself.
#
# This is the boot executor / brainstem.
#
# EngAInOS remains the TIER1 authority.
# This kernel only runs declared gates in order and halts on first failure.
# ---------------------------------------------------------------------


ROOT = Path(__file__).resolve().parent

REPORT_DIR = ROOT / "runtime" / "logs"
REPORT_PATH = REPORT_DIR / "ENGAINOS_BOOT_KERNEL_LAST_RUN.json"
NEXT_ACTION_AFTER_SUCCESS = "BOOT_SCENE_AUTHORIZATION_REQUEST_V1"
NEXT_ACTION_AFTER_FAILURE = "FIX_FAILED_BOOT_GATE"


BOOT_SEQUENCE = [
    {
        "gate_id": "BOOTSTRAP_PREFLIGHT",
        "path": "gates/gate_engainos_bootstrap_preflight_v1.py",
        "required": True,
        "description": "Verify root, folder layout, authority files, and runtime log/session writability."
    },
    {
        "gate_id": "SYSTEM_HEALTH_PREFLIGHT",
        "path": "gates/gate_engainos_system_health_preflight_v1.py",
        "required": True,
        "description": "Verify declared systems, lanes, authority owners, and read-only health state."
    },
    {
        "gate_id": "BOOT_SCENE_AUTHORIZATION_REQUEST",
        "path": "gates/gate_boot_scene_authorization_request_v1.py",
        "required": True,
        "description": "Ask EngAInOS whether the empty boot shell scene may be authorized."
    },
    {
        "gate_id": "BOOT_SCENE_LOAD_EXECUTOR_REQUEST",
        "path": "gates/gate_boot_scene_load_executor_request_v1.py",
        "required": True,
        "description": "Ask EngAInOS whether the empty boot shell load executor may be released."
    },
    {
        "gate_id": "BOOT_SCENE_LOAD_EXECUTOR",
        "path": "executors/boot_scene_load_executor_v1.py",
        "required": True,
        "description": "Write the Godot-facing empty boot shell load command packet."
    },
]


@dataclass(frozen=True)
class KernelStepResult:
    gate_id: str
    path: str
    required: bool
    status: str
    returncode: int | None
    message: str


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_report(
    *,
    started_at: str,
    finished_at: str,
    kernel_status: str,
    exit_code: int,
    results: list[KernelStepResult],
) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    auth_decision_path = REPORT_DIR / "BOOT_SCENE_AUTHORIZATION_DECISION_V1.json"
    exec_decision_path = REPORT_DIR / "BOOT_SCENE_LOAD_EXECUTOR_DECISION_V1.json"
    exec_report_path = REPORT_DIR / "BOOT_SCENE_LOAD_EXECUTOR_V1.report.json"
    godot_report_path = REPORT_DIR.parent / "godot_reports" / "GODOT_BOOT_BRIDGE_CONSUME_COMMAND_V1.report.json"

    scene_load_authorized = False
    scene_load_executor_allowed = False
    scene_load_executor_ran = False
    godot_command_written = False
    godot_bridge_consumed = False
    boot_shell_loaded = False
    player_spawned = False
    entities_spawned = False
    player_input_allowed = False
    next_action = NEXT_ACTION_AFTER_SUCCESS if kernel_status == "BOOT_SEQUENCE_COMPLETE" else NEXT_ACTION_AFTER_FAILURE
    godot_command_allowed = False
    runtime_mutation_allowed = False

    if kernel_status == "BOOT_SEQUENCE_COMPLETE":
        if godot_report_path.exists():
            try:
                with godot_report_path.open("r", encoding="utf-8") as f:
                    dec = json.load(f)
                    if dec.get("ok"):
                        godot_bridge_consumed = True
                        boot_shell_loaded = True
                        player_spawned = dec.get("player_spawned", False)
                        entities_spawned = dec.get("entities_spawned", False)
                        player_input_allowed = dec.get("player_input_allowed", False)
                        next_action = dec.get("next_action", next_action)
                        runtime_mutation_allowed = dec.get("runtime_mutation_allowed", False)
                        scene_load_executor_ran = True
                        scene_load_executor_allowed = True
                        scene_load_authorized = True
                        godot_command_written = True
                        godot_command_allowed = True
            except Exception:
                pass

        if not godot_bridge_consumed:
            if exec_report_path.exists():
                try:
                    with exec_report_path.open("r", encoding="utf-8") as f:
                        dec = json.load(f)
                        scene_load_executor_ran = dec.get("scene_load_executor_ran", False)
                        godot_command_written = dec.get("command_written", False)
                        next_action = dec.get("next_action", next_action)
                        godot_command_allowed = dec.get("godot_command_allowed", False)
                        runtime_mutation_allowed = dec.get("runtime_mutation_allowed", False)
                    if scene_load_executor_ran:
                        scene_load_executor_allowed = True
                        scene_load_authorized = True
                except Exception:
                    pass
            elif exec_decision_path.exists():
                try:
                    with exec_decision_path.open("r", encoding="utf-8") as f:
                        dec = json.load(f)
                        scene_load_executor_allowed = dec.get("scene_load_executor_allowed", False)
                        next_action = dec.get("next_action", next_action)
                        godot_command_allowed = dec.get("godot_command_allowed", False)
                        runtime_mutation_allowed = dec.get("runtime_mutation_allowed", False)
                    if scene_load_executor_allowed:
                        scene_load_authorized = True
                except Exception:
                    pass
            elif auth_decision_path.exists():
                try:
                    with auth_decision_path.open("r", encoding="utf-8") as f:
                        dec = json.load(f)
                        scene_load_authorized = dec.get("scene_load_authorized", False)
                        next_action = dec.get("next_action", next_action)
                        godot_command_allowed = dec.get("godot_command_allowed", False)
                        runtime_mutation_allowed = dec.get("runtime_mutation_allowed", False)
                except Exception:
                    pass

    report: dict[str, Any] = {
        "contract": "engainos.boot_kernel_report.v1",
        "authority_owner": "EngAInOS",
        "authority_tier": "TIER1",
        "kernel_role": "boot_executor",
        "kernel_status": kernel_status,
        "exit_code": exit_code,
        "started_at": started_at,
        "finished_at": finished_at,
        "root": str(ROOT),
        "scene_may_load": scene_load_authorized,
        "scene_load_authorized_by_decision": scene_load_authorized,
        "scene_load_executor_allowed": scene_load_executor_allowed,
        "scene_load_executor_ran": scene_load_executor_ran,
        "godot_command_written": godot_command_written,
        "godot_boot_bridge_consumed_command": godot_bridge_consumed,
        "boot_shell_loaded": boot_shell_loaded,
        "player_spawned": player_spawned,
        "entities_spawned": entities_spawned,
        "player_input_allowed": player_input_allowed,
        "runtime_mutation_allowed": runtime_mutation_allowed,
        "godot_command_allowed": godot_command_allowed,
        "next_action": next_action,
        "results": [
            {
                "gate_id": result.gate_id,
                "path": result.path,
                "required": result.required,
                "status": result.status,
                "returncode": result.returncode,
                "message": result.message,
            }
            for result in results
        ],
    }

    REPORT_PATH.write_text(
        json.dumps(report, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def resolve_gate_path(relative_path: str) -> Path:
    return ROOT / relative_path


def execute_gate(gate_id: str, gate_path: Path) -> int:
    print(f"[ENGAINOS_KERNEL][EXECUTE] {gate_id}: {gate_path}", flush=True)

    result = subprocess.run(
        [sys.executable, str(gate_path)],
        cwd=str(ROOT),
        capture_output=False,
        text=True,
    )

    return int(result.returncode)


def execute_kernel() -> int:
    started_at = utc_now()
    results: list[KernelStepResult] = []

    print("[ENGAINOS_KERNEL] Starting boot sequence...", flush=True)
    print(f"[ENGAINOS_KERNEL] ROOT: {ROOT}", flush=True)

    for step in BOOT_SEQUENCE:
        gate_id = str(step["gate_id"])
        relative_path = str(step["path"])
        required = bool(step.get("required", True))

        gate_path = resolve_gate_path(relative_path)

        if not gate_path.exists() or not gate_path.is_file():
            message = f"Gate missing at {relative_path}"
            print(f"[ENGAINOS_KERNEL][CRITICAL_FAILURE] {message}", flush=True)

            results.append(
                KernelStepResult(
                    gate_id=gate_id,
                    path=relative_path,
                    required=required,
                    status="MISSING",
                    returncode=None,
                    message=message,
                )
            )

            finished_at = utc_now()
            write_report(
                started_at=started_at,
                finished_at=finished_at,
                kernel_status="BOOT_BLOCKED",
                exit_code=1,
                results=results,
            )

            print(f"[ENGAINOS_KERNEL][REPORT_WRITTEN] {REPORT_PATH}", flush=True)
            return 1

        returncode = execute_gate(gate_id, gate_path)

        if returncode != 0:
            message = f"{gate_id} failed with exit code {returncode}"
            print(f"[ENGAINOS_KERNEL][BOOT_BLOCKED] {message}", flush=True)

            results.append(
                KernelStepResult(
                    gate_id=gate_id,
                    path=relative_path,
                    required=required,
                    status="FALSE",
                    returncode=returncode,
                    message=message,
                )
            )

            finished_at = utc_now()
            write_report(
                started_at=started_at,
                finished_at=finished_at,
                kernel_status="BOOT_BLOCKED",
                exit_code=returncode,
                results=results,
            )

            print(f"[ENGAINOS_KERNEL][REPORT_WRITTEN] {REPORT_PATH}", flush=True)
            return returncode

        message = f"{gate_id} returned TRUE"
        print(f"[ENGAINOS_KERNEL][GATE_ACCEPTED] {message}", flush=True)

        results.append(
            KernelStepResult(
                gate_id=gate_id,
                path=relative_path,
                required=required,
                status="TRUE",
                returncode=returncode,
                message=message,
            )
        )

    finished_at = utc_now()

    write_report(
        started_at=started_at,
        finished_at=finished_at,
        kernel_status="BOOT_SEQUENCE_COMPLETE",
        exit_code=0,
        results=results,
    )

    auth_decision_path = REPORT_DIR / "BOOT_SCENE_AUTHORIZATION_DECISION_V1.json"
    exec_decision_path = REPORT_DIR / "BOOT_SCENE_LOAD_EXECUTOR_DECISION_V1.json"
    exec_report_path = REPORT_DIR / "BOOT_SCENE_LOAD_EXECUTOR_V1.report.json"
    godot_report_path = REPORT_DIR.parent / "godot_reports" / "GODOT_BOOT_BRIDGE_CONSUME_COMMAND_V1.report.json"

    scene_load_authorized = False
    scene_load_executor_allowed = False
    scene_load_executor_ran = False
    godot_command_written = False
    godot_bridge_consumed = False
    boot_shell_loaded = False
    player_spawned = False
    entities_spawned = False
    player_input_allowed = False
    next_action = NEXT_ACTION_AFTER_SUCCESS
    godot_command_allowed = False
    runtime_mutation_allowed = False

    if godot_report_path.exists():
        try:
            with godot_report_path.open("r", encoding="utf-8") as f:
                dec = json.load(f)
                if dec.get("ok"):
                    godot_bridge_consumed = True
                    boot_shell_loaded = True
                    player_spawned = dec.get("player_spawned", False)
                    entities_spawned = dec.get("entities_spawned", False)
                    player_input_allowed = dec.get("player_input_allowed", False)
                    next_action = dec.get("next_action", next_action)
                    runtime_mutation_allowed = dec.get("runtime_mutation_allowed", False)
                    scene_load_executor_ran = True
                    scene_load_executor_allowed = True
                    scene_load_authorized = True
                    godot_command_written = True
                    godot_command_allowed = True
        except Exception:
            pass

    if not godot_bridge_consumed:
        if exec_report_path.exists():
            try:
                with exec_report_path.open("r", encoding="utf-8") as f:
                    dec = json.load(f)
                    scene_load_executor_ran = dec.get("scene_load_executor_ran", False)
                    godot_command_written = dec.get("command_written", False)
                    next_action = dec.get("next_action", next_action)
                    godot_command_allowed = dec.get("godot_command_allowed", False)
                    runtime_mutation_allowed = dec.get("runtime_mutation_allowed", False)
                if scene_load_executor_ran:
                    scene_load_executor_allowed = True
                    scene_load_authorized = True
            except Exception:
                pass
        elif exec_decision_path.exists():
            try:
                with exec_decision_path.open("r", encoding="utf-8") as f:
                    dec = json.load(f)
                    scene_load_executor_allowed = dec.get("scene_load_executor_allowed", False)
                    next_action = dec.get("next_action", next_action)
                    godot_command_allowed = dec.get("godot_command_allowed", False)
                    runtime_mutation_allowed = dec.get("runtime_mutation_allowed", False)
                if scene_load_executor_allowed:
                    scene_load_authorized = True
            except Exception:
                pass
        elif auth_decision_path.exists():
            try:
                with auth_decision_path.open("r", encoding="utf-8") as f:
                    dec = json.load(f)
                    scene_load_authorized = dec.get("scene_load_authorized", False)
                    next_action = dec.get("next_action", next_action)
                    godot_command_allowed = dec.get("godot_command_allowed", False)
                    runtime_mutation_allowed = dec.get("runtime_mutation_allowed", False)
            except Exception:
                pass

    print("[ENGAINOS_KERNEL][BOOT_SEQUENCE_COMPLETE] Systems are ready for scene authorization.", flush=True)
    print(f"[ENGAINOS_KERNEL][REPORT_WRITTEN] {REPORT_PATH}", flush=True)
    print("", flush=True)

    if godot_bridge_consumed:
        for res in results:
            print(f"{res.gate_id}: {res.status}", flush=True)
        print("BOOT_SEQUENCE_COMPLETE: TRUE", flush=True)
        print("", flush=True)
        print("ENGAINOS_BOOT_KERNEL: TRUE", flush=True)
        print(f"GODOT_COMMAND_WRITTEN: {str(godot_command_written).upper()}", flush=True)
        print(f"GODOT_BOOT_BRIDGE_CONSUMED_COMMAND: {str(godot_bridge_consumed).upper()}", flush=True)
        print(f"BOOT_SHELL_LOADED: {str(boot_shell_loaded).upper()}", flush=True)
        print("", flush=True)
        print(f"PLAYER_SPAWNED: {str(player_spawned).lower()}", flush=True)
        print(f"ENTITIES_SPAWNED: {str(entities_spawned).lower()}", flush=True)
        print(f"PLAYER_INPUT_ALLOWED: {str(player_input_allowed).lower()}", flush=True)
        print(f"RUNTIME_MUTATION_ALLOWED: {str(runtime_mutation_allowed).lower()}", flush=True)
        print("", flush=True)
        print(f"NEXT_ACTION:\n{next_action}", flush=True)
    else:
        for res in results:
            print(f"{res.gate_id}: {res.status}", flush=True)
        print("BOOT_SEQUENCE_COMPLETE: TRUE", flush=True)
        print("", flush=True)
        if exec_report_path.exists():
            print(f"GODOT_COMMAND_WRITTEN: {str(godot_command_written).lower()}", flush=True)
            print(f"GODOT_COMMAND_ALLOWED: {str(godot_command_allowed).lower()}", flush=True)
            print(f"RUNTIME_MUTATION_ALLOWED: {str(runtime_mutation_allowed).lower()}", flush=True)
            print("", flush=True)
            print(f"NEXT_ACTION:\n{next_action}", flush=True)
        elif exec_decision_path.exists():
            print(f"SCENE_LOAD_EXECUTOR_ALLOWED: {str(scene_load_executor_allowed).lower()}", flush=True)
            print(f"GODOT_COMMAND_ALLOWED: {str(godot_command_allowed).lower()}", flush=True)
            print(f"RUNTIME_MUTATION_ALLOWED: {str(runtime_mutation_allowed).lower()}", flush=True)
            print("", flush=True)
            print(f"NEXT_ACTION:\n{next_action}", flush=True)
        else:
            print(f"SCENE_LOAD_AUTHORIZED_BY_DECISION: {str(scene_load_authorized).lower()}", flush=True)
            print(f"GODOT_COMMAND_ALLOWED: {str(godot_command_allowed).lower()}", flush=True)
            print(f"RUNTIME_MUTATION_ALLOWED: {str(runtime_mutation_allowed).lower()}", flush=True)
            print(f"NEXT_ACTION: {next_action}", flush=True)
    print("", flush=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(execute_kernel())
