# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/gates/gate_engainos_bootstrap_preflight_v1.py

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path("/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn")

MANIFEST_PATH = ROOT / "engainos" / "boot" / "ENGAINOS_BOOT_LAYOUT_MANIFEST_V1.json"

SESSION_ROOT = ROOT / "runtime" / "sessions"
LOG_ROOT = ROOT / "runtime" / "logs"


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
        raise ValueError("Manifest root must be a JSON object.")

    return data


def gate_root_exists() -> GateResult:
    passed = ROOT.exists() and ROOT.is_dir()

    return GateResult(
        passed=passed,
        gate_name="GATE_ROOT_EXISTS",
        message="EngAIn root exists." if passed else "EngAIn root is missing.",
        details={"root": str(ROOT)},
    )


def gate_manifest_exists() -> GateResult:
    passed = MANIFEST_PATH.exists() and MANIFEST_PATH.is_file()

    return GateResult(
        passed=passed,
        gate_name="GATE_MANIFEST_EXISTS",
        message="Boot layout manifest exists." if passed else "Boot layout manifest is missing.",
        details={"manifest_path": str(MANIFEST_PATH)},
    )


def gate_manifest_shape(manifest: dict[str, Any]) -> GateResult:
    checks = {
        "contract_valid": manifest.get("contract") == "engainos.boot_layout_manifest.v1",
        "authority_owner_valid": manifest.get("authority_owner") == "EngAInOS",
        "authority_tier_valid": manifest.get("authority_tier") == "TIER1",
        "required_directories_is_list": isinstance(manifest.get("required_directories"), list),
        "required_files_is_list": isinstance(manifest.get("required_files"), list),
        "forbidden_boot_actions_is_list": isinstance(manifest.get("forbidden_boot_actions"), list),
    }

    passed = all(checks.values())

    return GateResult(
        passed=passed,
        gate_name="GATE_MANIFEST_SHAPE",
        message="Boot manifest shape is valid." if passed else "Boot manifest shape is invalid.",
        details=checks,
    )


def gate_required_directories(manifest: dict[str, Any]) -> GateResult:
    required_directories = manifest.get("required_directories", [])

    missing = []
    present = []

    for rel_path in required_directories:
        path = ROOT / rel_path
        if path.exists() and path.is_dir():
            present.append(rel_path)
        else:
            missing.append(rel_path)

    passed = len(missing) == 0

    return GateResult(
        passed=passed,
        gate_name="GATE_REQUIRED_DIRECTORIES",
        message="All required directories exist." if passed else "One or more required directories are missing.",
        details={
            "present": present,
            "missing": missing,
        },
    )


def gate_required_files(manifest: dict[str, Any]) -> GateResult:
    required_files = manifest.get("required_files", [])

    missing = []
    present = []

    for rel_path in required_files:
        path = ROOT / rel_path
        if path.exists() and path.is_file():
            present.append(rel_path)
        else:
            missing.append(rel_path)

    passed = len(missing) == 0

    return GateResult(
        passed=passed,
        gate_name="GATE_REQUIRED_FILES",
        message="All required authority files exist." if passed else "One or more required authority files are missing.",
        details={
            "present": present,
            "missing": missing,
        },
    )


def gate_forbidden_boot_actions_declared(manifest: dict[str, Any]) -> GateResult:
    forbidden = set(manifest.get("forbidden_boot_actions", []))

    required_forbidden = {
        "scene_spawn",
        "runtime_mutation",
        "canon_write",
        "godot_command_execution",
        "asset_generation",
        "mesh_generation",
        "quest_state_write",
        "combat_state_write",
        "inventory_state_write",
    }

    missing_forbidden = sorted(required_forbidden - forbidden)

    passed = len(missing_forbidden) == 0

    return GateResult(
        passed=passed,
        gate_name="GATE_FORBIDDEN_BOOT_ACTIONS_DECLARED",
        message="Forbidden boot actions are declared." if passed else "Forbidden boot action list is incomplete.",
        details={
            "required_forbidden": sorted(required_forbidden),
            "manifest_forbidden": sorted(forbidden),
            "missing_forbidden": missing_forbidden,
        },
    )


def gate_runtime_session_dirs_writable() -> GateResult:
    checks: dict[str, bool] = {}

    for path in [SESSION_ROOT, LOG_ROOT]:
        try:
            path.mkdir(parents=True, exist_ok=True)
            probe = path / ".write_probe"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink()
            checks[str(path)] = True
        except Exception:
            checks[str(path)] = False

    passed = all(checks.values())

    return GateResult(
        passed=passed,
        gate_name="GATE_RUNTIME_SESSION_DIRS_WRITABLE",
        message="Runtime session/log directories are writable." if passed else "Runtime session/log directories are not writable.",
        details=checks,
    )


def build_boot_decision(results: list[GateResult]) -> dict[str, Any]:
    failed = [result for result in results if not result.passed]

    if failed:
        return {
            "boot_allowed": False,
            "boot_status": "BOOT_BLOCKED",
            "blocked_by": failed[0].gate_name,
            "reason": failed[0].message,
            "systems_may_initialize": False,
            "scene_may_load": False,
            "runtime_mutation_allowed": False,
            "next_action": "FIX_LAYOUT_OR_AUTHORITY_FILES_THEN_RETRY"
        }

    session_id = datetime.now(timezone.utc).strftime("engainos_session_%Y%m%dT%H%M%SZ")

    return {
        "boot_allowed": True,
        "boot_status": "BOOT_ACCEPTED",
        "blocked_by": None,
        "reason": "Root, layout, authority files, and runtime session paths are valid.",
        "session_id": session_id,
        "systems_may_initialize": True,
        "scene_may_load": False,
        "runtime_mutation_allowed": False,
        "next_action": "SYSTEM_HEALTH_PREFLIGHT"
    }


def print_gate(result: GateResult) -> None:
    status = "PASS" if result.passed else "FAIL"
    print(f"[engainos_bootstrap_preflight][{result.gate_name}] {status}: {result.message}")
    print(json.dumps(result.details, indent=2, sort_keys=True))


def main() -> int:
    results: list[GateResult] = []

    root_gate = gate_root_exists()
    results.append(root_gate)

    manifest_gate = gate_manifest_exists()
    results.append(manifest_gate)

    if not root_gate.passed or not manifest_gate.passed:
        for result in results:
            print_gate(result)

        decision = build_boot_decision(results)
        print("[engainos_bootstrap_preflight][ALL_GATES] false")
        print(json.dumps(decision, indent=2, sort_keys=True))
        return 1

    try:
        manifest = load_json(MANIFEST_PATH)
    except Exception as exc:
        results.append(
            GateResult(
                passed=False,
                gate_name="GATE_MANIFEST_JSON_PARSE",
                message="Boot manifest could not be parsed.",
                details={"error": str(exc), "manifest_path": str(MANIFEST_PATH)},
            )
        )

        for result in results:
            print_gate(result)

        decision = build_boot_decision(results)
        print("[engainos_bootstrap_preflight][ALL_GATES] false")
        print(json.dumps(decision, indent=2, sort_keys=True))
        return 1

    results.extend(
        [
            gate_manifest_shape(manifest),
            gate_required_directories(manifest),
            gate_required_files(manifest),
            gate_forbidden_boot_actions_declared(manifest),
            gate_runtime_session_dirs_writable(),
        ]
    )

    for result in results:
        print_gate(result)

    all_passed = all(result.passed for result in results)
    decision = build_boot_decision(results)

    print(f"[engainos_bootstrap_preflight][ALL_GATES] {str(all_passed).lower()}")
    print(json.dumps(decision, indent=2, sort_keys=True))

    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
