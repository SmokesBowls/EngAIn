from __future__ import annotations
GATE_LIFECYCLE = "ACTIVE_VERIFICATION"
GATE_BOARD = "ENGAINOS_AP_MIGRATION_AND_CONTRACT_BOARD"


from dataclasses import dataclass, asdict
from pathlib import Path
import importlib.util
import json
import sys
from typing import Any

REPO_ROOT = Path("/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn")

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

OLD_PATH = REPO_ROOT / "godotengain/engainos/core/ap_core.py"
NEW_PATH = REPO_ROOT / "engainos/core/ap_core.py"
REPORT_PATH = REPO_ROOT / "scratch/ap_core_behavior_parity_report.json"

@dataclass(frozen=True)
class GateResult:
    gate_name: str
    passed: bool
    status: str
    message: str
    details: dict[str, Any]

def load_module_from_path(module_name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(module_name, path)

    if spec is None or spec.loader is None:
        raise ImportError(f"Could not create import spec for {path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

def normalize_value(value: Any) -> Any:
    """
    Convert return values into comparable plain data.

    Violation objects from old/new modules are different Python classes after
    import-from-path, so compare their fields instead of class identity.
    """
    if isinstance(value, list):
        return [normalize_value(item) for item in value]

    if hasattr(value, "__dict__"):
        return {
            "type_name": type(value).__name__,
            "fields": dict(value.__dict__),
        }

    return value

def run_behavior_cases(module: Any) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []

    test_cases = [
        {
            "case_id": "schema_correct_negative_health_rejected",
            "expected_valid": False,
            "expected_min_violations": 1,
            "snapshot": {
                "entities": {
                    "hero": {
                        "health": 10
                    }
                }
            },
            "delta": {
                "entities": {
                    "hero": {
                        "health": -1
                    }
                }
            },
        },
        {
            "case_id": "schema_correct_duplicate_guard_rejected",
            "expected_valid": False,
            "expected_min_violations": 1,
            "snapshot": {},
            "delta": {
                "guards": {
                    "north_gate": "guard_001",
                    "south_gate": "guard_001"
                }
            },
        },
        {
            "case_id": "schema_correct_valid_delta_allowed",
            "expected_valid": True,
            "expected_min_violations": 0,
            "snapshot": {
                "entities": {
                    "hero": {
                        "health": 10
                    }
                }
            },
            "delta": {
                "entities": {
                    "hero": {
                        "health": 9
                    }
                },
                "guards": {
                    "north_gate": "guard_001",
                    "south_gate": "guard_002"
                }
            },
        },
    ]

    for case in test_cases:
        snapshot = case["snapshot"]
        delta = case["delta"]

        try:
            # Important:
            # ap_core.check_ap uses whatever rules are already registered in that module.
            # For historical parity, we also directly call the built-in rule functions to prove
            # the real schema triggers the same rule logic in both old and new files.
            direct_negative_health = module.rule_no_negative_health(snapshot, delta)
            direct_double_guard = module.rule_no_double_guard(snapshot, delta)

            violations = module.check_ap(snapshot, delta)
            valid = module.is_valid(snapshot, delta)

            direct_rule_hits = [
                item for item in [direct_negative_health, direct_double_guard]
                if item is not None
            ]

            observed_min_violations = len(direct_rule_hits)

            # This gate accepts either direct rule hits or check_ap violations.
            # Why:
            # ap_core.py is mechanism-level and may not auto-register built-ins.
            # ap_engine.py proves default registration separately.
            effective_violation_count = max(
                observed_min_violations,
                len(violations) if isinstance(violations, list) else 0,
            )

            effective_valid = effective_violation_count == 0

            cases.append(
                {
                    "case_id": case["case_id"],
                    "ok": True,
                    "snapshot": snapshot,
                    "delta": delta,
                    "expected_valid": case["expected_valid"],
                    "expected_min_violations": case["expected_min_violations"],
                    "direct_negative_health": normalize_value(direct_negative_health),
                    "direct_double_guard": normalize_value(direct_double_guard),
                    "check_ap": normalize_value(violations),
                    "is_valid": normalize_value(valid),
                    "effective_violation_count": effective_violation_count,
                    "effective_valid": effective_valid,
                    "contract_signal": (
                        effective_valid == case["expected_valid"]
                        and effective_violation_count >= case["expected_min_violations"]
                    ),
                }
            )
        except Exception as exc:
            cases.append(
                {
                    "case_id": case["case_id"],
                    "ok": False,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                    "contract_signal": False,
                }
            )

    return cases

def gate_files_exist() -> GateResult:
    missing = []

    if not OLD_PATH.exists():
        missing.append(str(OLD_PATH))

    if not NEW_PATH.exists():
        missing.append(str(NEW_PATH))

    passed = not missing

    return GateResult(
        gate_name="GATE_FILES_EXIST",
        passed=passed,
        status="TRUE" if passed else "FALSE",
        message="Historical and migrated ap_core.py files exist." if passed else "One or more ap_core.py files are missing.",
        details={
            "old_path": str(OLD_PATH),
            "new_path": str(NEW_PATH),
            "missing": missing,
        },
    )

def gate_schema_correct_behavior_parity(old_module: Any, new_module: Any) -> GateResult:
    old_cases = run_behavior_cases(old_module)
    new_cases = run_behavior_cases(new_module)

    parity_passed = old_cases == new_cases
    old_signal = all(case.get("contract_signal") is True for case in old_cases)
    new_signal = all(case.get("contract_signal") is True for case in new_cases)

    passed = parity_passed and old_signal and new_signal

    if passed:
        message = "Historical and migrated AP core behavior matches using schema-correct payloads."
        signal_quality = "SIGNAL"
    elif parity_passed:
        message = "Historical and migrated AP core match, but schema-correct contract behavior was not fully exercised."
        signal_quality = "NON_SIGNAL"
    else:
        message = "Historical and migrated AP core behavior differs using schema-correct payloads."
        signal_quality = "SIGNAL_FAIL"

    return GateResult(
        gate_name="GATE_SCHEMA_CORRECT_BEHAVIOR_PARITY",
        passed=passed,
        status="TRUE" if passed else "FALSE",
        message=message,
        details={
            "signal_quality": signal_quality,
            "parity_passed": parity_passed,
            "old_signal": old_signal,
            "new_signal": new_signal,
            "old_cases": old_cases,
            "new_cases": new_cases,
        },
    )

def main() -> int:
    results: list[GateResult] = []

    files_gate = gate_files_exist()
    results.append(files_gate)

    if files_gate.passed:
        old_module = load_module_from_path("historical_ap_core_schema_correct", OLD_PATH)
        new_module = load_module_from_path("migrated_ap_core_schema_correct", NEW_PATH)

        results.append(gate_schema_correct_behavior_parity(old_module, new_module))

    all_passed = all(result.passed for result in results)

    report = {
        "refactor_id": "AP_CORE_SCHEMA_CORRECT_BEHAVIOR_PARITY_001",
        "tier_authority": "ENGAINOS_TIER1",
        "lane": "engainos_core_authority",
        "stack": "engainos",
        "old_path": str(OLD_PATH),
        "new_path": str(NEW_PATH),
        "behavior_change": "no" if all_passed else "yes_or_unknown",
        "authority_change": "no",
        "schema_change": "no",
        "runtime_output_change": "no" if all_passed else "unknown",
        "signal_quality": "SIGNAL" if all_passed else "UNKNOWN_OR_FAIL",
        "gates": [asdict(result) for result in results],
        "acceptance": "ACCEPTED" if all_passed else "REJECTED",
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    for result in results:
        label = "PASS" if result.passed else "FAIL"
        print(f"[gate_ap_core_behavior_parity][{result.gate_name}] {label}: {result.message}")

    print(f"[gate_ap_core_behavior_parity][REPORT] {REPORT_PATH}")
    print(f"[gate_ap_core_behavior_parity][ALL_GATES] {'true' if all_passed else 'false'}")

    return 0 if all_passed else 2

if __name__ == "__main__":
    raise SystemExit(main())
