from __future__ import annotations
GATE_LIFECYCLE = "ACTIVE_CONTRACT"
GATE_BOARD = "ENGAINOS_AP_MIGRATION_AND_CONTRACT_BOARD"


from dataclasses import dataclass, asdict
from pathlib import Path
import ast
import json
from typing import Any

REPO_ROOT = Path("/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn")

AP_RUNTIME_PATH = REPO_ROOT / "godotengain/engainos/core/ap_runtime.py"
BEHAVIOR_REPORT_PATH = REPO_ROOT / "scratch/ap_runtime_behavior_probe_report.json"
REPAIR_REPORT_PATH = REPO_ROOT / "scratch/ap_runtime_repair_readiness_report.json"
REPORT_PATH = REPO_ROOT / "scratch/ap_runtime_relay_readiness_report.json"

@dataclass(frozen=True)
class GateResult:
    gate_name: str
    passed: bool
    status: str
    message: str
    details: dict[str, Any]

RELAY_MAY = [
    "load_or_import_repaired_APRuntimeIntegration",
    "validate_caller_context_before_forwarding",
    "forward_caller_supplied_AP_messages",
    "reject_raw_runtime_or_player_input_without_acceptance_marker",
    "return_runtime_response_without_declaring_truth",
]

RELAY_MAY_NOT = [
    "instantiate_ZWAPEngine_directly",
    "mutate_StateProvider_directly",
    "load_scene_files_directly",
    "write_timeline_directly",
    "call_execute_tick_directly",
    "manufacture_allow_execute_true",
    "manufacture_enable_timeline_write_true",
    "manufacture_allow_history_read_true",
    "bypass_APRuntimeIntegration_intent_gates",
    "declare_runtime_truth",
]

def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {
            "__read_error__": {
                "error_type": type(exc).__name__,
                "error": str(exc),
            }
        }

def read_source(path: Path) -> str:
    return path.read_text(encoding="utf-8")

def gate_runtime_repair_report_accepted() -> GateResult:
    report = read_json(REPAIR_REPORT_PATH)

    accepted = report.get("acceptance") == "ACCEPTED_AS_REPAIR_READY"
    repair_ready = report.get("repair_ready") is True
    relay_creation_allowed = report.get("relay_creation_allowed") is False

    passed = accepted and repair_ready and relay_creation_allowed

    return GateResult(
        gate_name="GATE_RUNTIME_REPAIR_REPORT_ACCEPTED",
        passed=passed,
        status="TRUE" if passed else "FALSE",
        message=(
            "AP runtime structural repair report is accepted and still blocks relay creation."
            if passed
            else "AP runtime structural repair report is missing, rejected, or incorrectly authorizes relay creation."
        ),
        details={
            "report_path": str(REPAIR_REPORT_PATH),
            "acceptance": report.get("acceptance"),
            "repair_ready": report.get("repair_ready"),
            "relay_creation_allowed": report.get("relay_creation_allowed"),
            "read_error": report.get("__read_error__"),
        },
    )

def gate_runtime_behavior_report_accepted() -> GateResult:
    report = read_json(BEHAVIOR_REPORT_PATH)

    accepted = report.get("acceptance") == "ACCEPTED_BEHAVIOR_PROVEN"
    behavioral_proof = report.get("behavioral_proof") is True
    relay_next = report.get("relay_readiness_gate_allowed_next") is True
    relay_creation_allowed = report.get("relay_creation_allowed") is False

    passed = accepted and behavioral_proof and relay_next and relay_creation_allowed

    return GateResult(
        gate_name="GATE_RUNTIME_BEHAVIOR_REPORT_ACCEPTED",
        passed=passed,
        status="TRUE" if passed else "FALSE",
        message=(
            "AP runtime behavior proof is accepted and authorizes relay-readiness gate next."
            if passed
            else "AP runtime behavior proof is missing, rejected, or does not authorize relay-readiness gate."
        ),
        details={
            "report_path": str(BEHAVIOR_REPORT_PATH),
            "acceptance": report.get("acceptance"),
            "behavioral_proof": report.get("behavioral_proof"),
            "relay_readiness_gate_allowed_next": report.get("relay_readiness_gate_allowed_next"),
            "relay_creation_allowed": report.get("relay_creation_allowed"),
            "read_error": report.get("__read_error__"),
        },
    )

def gate_runtime_file_stays_in_godotengain() -> GateResult:
    exists = AP_RUNTIME_PATH.exists()
    inside_godotengain = "godotengain/engainos/core/ap_runtime.py" in str(AP_RUNTIME_PATH)

    root_copy = REPO_ROOT / "engainos/core/ap_runtime.py"
    root_copy_exists = root_copy.exists()

    passed = exists and inside_godotengain and not root_copy_exists

    return GateResult(
        gate_name="GATE_RUNTIME_FILE_STAYS_IN_GODOTENGAIN",
        passed=passed,
        status="TRUE" if passed else "FALSE",
        message=(
            "ap_runtime.py remains in godotengain and has not been copied into engainos/core."
            if passed
            else "ap_runtime.py placement violates relay doctrine."
        ),
        details={
            "historical_runtime_path": str(AP_RUNTIME_PATH),
            "historical_runtime_exists": exists,
            "root_core_runtime_path": str(root_copy),
            "root_core_runtime_exists": root_copy_exists,
        },
    )

def gate_runtime_imports_fenced_zw_engine() -> GateResult:
    source = read_source(AP_RUNTIME_PATH)

    required = [
        "from tier1.engainos.core.ap_zw_engine import",
        "ZWAPEngine",
        "StateProvider",
        "APInternalRule",
    ]

    forbidden = [
        "from .ap_engine import ZWAPEngine",
        "from tier1.engainos.core.ap_engine import ZWAPEngine",
    ]

    missing_required = [item for item in required if item not in source]
    forbidden_hits = [item for item in forbidden if item in source]

    passed = not missing_required and not forbidden_hits

    return GateResult(
        gate_name="GATE_RUNTIME_IMPORTS_FENCED_ZW_ENGINE",
        passed=passed,
        status="TRUE" if passed else "FALSE",
        message=(
            "AP runtime imports fenced ZW engine from tier1.engainos.core.ap_zw_engine."
            if passed
            else "AP runtime imports stale or unsafe AP engine path."
        ),
        details={
            "missing_required": missing_required,
            "forbidden_hits": forbidden_hits,
        },
    )

def gate_runtime_intent_gates_exist() -> GateResult:
    source = read_source(AP_RUNTIME_PATH)

    required = [
        'msg.get("allow_execute") is not True',
        '"execution_intent_required"',
        'msg.get("enable_timeline_write") is True',
        '"timeline_write_not_allowed"',
        'self.enable_timeline_write and requested_timeline_write',
        'msg.get("allow_history_read") is not True',
        '"history_read_intent_required"',
    ]

    missing = [item for item in required if item not in source]

    passed = not missing

    return GateResult(
        gate_name="GATE_RUNTIME_INTENT_GATES_EXIST",
        passed=passed,
        status="TRUE" if passed else "FALSE",
        message=(
            "Repaired AP runtime contains execute, timeline, and history intent gates."
            if passed
            else "Repaired AP runtime is missing one or more intent gates."
        ),
        details={
            "required_fragments": required,
            "missing": missing,
        },
    )

def gate_relay_contract_declared() -> GateResult:
    passed = True

    return GateResult(
        gate_name="GATE_RELAY_CONTRACT_DECLARED",
        passed=passed,
        status="TRUE",
        message="AP runtime relay MAY/MAY NOT contract declared.",
        details={
            "relay_may": RELAY_MAY,
            "relay_may_not": RELAY_MAY_NOT,
            "doctrine": "Adapters convert. Gates judge. Relays carry approved calls. Runtime executes.",
        },
    )

def main() -> int:
    results = [
        gate_runtime_file_stays_in_godotengain(),
        gate_runtime_repair_report_accepted(),
        gate_runtime_behavior_report_accepted(),
        gate_runtime_imports_fenced_zw_engine(),
        gate_runtime_intent_gates_exist(),
        gate_relay_contract_declared(),
    ]

    all_passed = all(result.passed for result in results)

    report = {
        "refactor_id": "AP_RUNTIME_RELAY_READINESS_001",
        "tier_authority": "ENGAINOS_TIER1",
        "lane": "ap_runtime_relay_readiness",
        "stack": "engainos_relay_boundary",
        "runtime_bridge_path": str(AP_RUNTIME_PATH),
        "relay_folder_allowed": "engainos/relays",
        "relay_file_allowed_next": "engainos/relays/ap_runtime_relay.py",
        "relay_creation_allowed": all_passed,
        "relay_may": RELAY_MAY,
        "relay_may_not": RELAY_MAY_NOT,
        "gates": [asdict(result) for result in results],
        "acceptance": "ACCEPTED_RELAY_READY" if all_passed else "REJECTED",
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    for result in results:
        label = "TRUE" if result.passed else "FALSE"
        print(f"[gate_ap_runtime_relay_readiness][{result.gate_name}] {label}: {result.message}")

    print(f"[gate_ap_runtime_relay_readiness][ALL_GATES] {'true' if all_passed else 'false'}")
    print(f"[gate_ap_runtime_relay_readiness][RELAY_CREATION_ALLOWED] {'true' if all_passed else 'false'}")
    print(f"[gate_ap_runtime_relay_readiness][REPORT] {REPORT_PATH}")

    return 0 if all_passed else 2

if __name__ == "__main__":
    raise SystemExit(main())
