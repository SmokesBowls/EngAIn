
from __future__ import annotations
GATE_LIFECYCLE = "ACTIVE_CONTRACT"
GATE_BOARD = "ENGAINOS_SYSTEM_CONTRACT_BOARD"

from dataclasses import dataclass, asdict
from pathlib import Path
import importlib.util
import inspect
import json
import sys
from typing import Any

REPO_ROOT = Path("/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn")

AP_CORE_PATH = REPO_ROOT / "engainos/core/ap_core.py"
REPORT_PATH = REPO_ROOT / "scratch/ap_core_rule_activation_report.json"

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
    if isinstance(value, list):
        return [normalize_value(item) for item in value]

    if hasattr(value, "__dict__"):
        return {
            "type_name": type(value).__name__,
            "fields": dict(value.__dict__),
        }

    return value

def call_safely(fn: Any, *args: Any, **kwargs: Any) -> dict[str, Any]:
    try:
        value = fn(*args, **kwargs)
        return {
            "ok": True,
            "value": normalize_value(value),
            "value_type": type(value).__name__,
        }
    except Exception as exc:
        return {
            "ok": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }

def gate_builtin_rule_functions_exist(module: Any) -> GateResult:
    required = [
        "rule_no_negative_health",
        "rule_no_double_guard",
    ]

    missing = [name for name in required if not hasattr(module, name)]
    passed = not missing

    return GateResult(
        gate_name="GATE_BUILTIN_RULE_FUNCTIONS_EXIST",
        passed=passed,
        status="TRUE" if passed else "FALSE",
        message="Built-in AP rule functions exist." if passed else "Built-in AP rule functions are missing.",
        details={
            "required": required,
            "missing": missing,
        },
    )

def gate_builtin_rule_function_responses(module: Any) -> GateResult:
    cases = []

    rule_no_negative_health = getattr(module, "rule_no_negative_health")
    rule_no_double_guard = getattr(module, "rule_no_double_guard")

    cases.append(
        {
            "case_id": "direct_negative_health_in_delta",
            "result": call_safely(
                rule_no_negative_health,
                {"health": 10},
                {"health": -1},
            ),
        }
    )

    cases.append(
        {
            "case_id": "direct_negative_health_in_snapshot",
            "result": call_safely(
                rule_no_negative_health,
                {"health": -1},
                {},
            ),
        }
    )

    cases.append(
        {
            "case_id": "direct_double_guard",
            "result": call_safely(
                rule_no_double_guard,
                {"guard": True},
                {"double_guard": True},
            ),
        }
    )

    # This gate passes if the functions are callable.
    # It does not require them to reject yet because we first need to learn their actual rule semantics.
    passed = all(item["result"]["ok"] for item in cases)

    return GateResult(
        gate_name="GATE_BUILTIN_RULE_FUNCTION_RESPONSES",
        passed=passed,
        status="TRUE" if passed else "FALSE",
        message="Built-in AP rule functions can be called." if passed else "One or more built-in AP rule functions cannot be called.",
        details={
            "cases": cases,
        },
    )

def gate_custom_rule_activation(module: Any) -> GateResult:
    """
    This tests the AP mechanism itself.

    We register a custom rule that always rejects when delta contains:
      {"force_reject": True}

    If check_ap returns a violation and is_valid returns False, the AP mechanism is active.
    """

    def reject_force_reject(snapshot: dict[str, Any], delta: dict[str, Any]) -> str | None:
        if delta.get("force_reject") is True:
            return "force_reject was true"
        return None

    before = call_safely(module.check_ap, {}, {"force_reject": True})

    register_result = call_safely(
        module.register_rule,
        "test_force_reject",
        reject_force_reject,
        "error",
    )

    after_check = call_safely(module.check_ap, {}, {"force_reject": True})
    after_valid = call_safely(module.is_valid, {}, {"force_reject": True})

    after_check_value = after_check.get("value")
    after_valid_value = after_valid.get("value")

    violation_count = len(after_check_value) if isinstance(after_check_value, list) else 0

    passed = (
        register_result["ok"]
        and after_check["ok"]
        and after_valid["ok"]
        and violation_count >= 1
        and after_valid_value is False
    )

    return GateResult(
        gate_name="GATE_CUSTOM_RULE_ACTIVATION",
        passed=passed,
        status="TRUE" if passed else "FALSE",
        message="AP core activates registered rules." if passed else "AP core did not prove registered rule activation.",
        details={
            "before_registration_check": before,
            "register_result": register_result,
            "after_registration_check": after_check,
            "after_registration_is_valid": after_valid,
            "violation_count_after_registration": violation_count,
        },
    )

def gate_ap_system_introspection(module: Any) -> GateResult:
    details: dict[str, Any] = {}

    details["module_symbols"] = sorted(
        name for name in dir(module)
        if not name.startswith("__")
    )

    if hasattr(module, "ApSystem"):
        ApSystem = getattr(module, "ApSystem")
        details["ApSystem_signature"] = str(inspect.signature(ApSystem))

        system_result = call_safely(ApSystem)
        details["ApSystem_construct"] = system_result

        if system_result["ok"]:
            system = ApSystem()
            details["ApSystem_dir"] = sorted(
                name for name in dir(system)
                if not name.startswith("__")
            )

            for attr in ["rules", "_rules", "registry", "_registry"]:
                if hasattr(system, attr):
                    value = getattr(system, attr)
                    details[f"ApSystem_attr_{attr}"] = normalize_value(value)

    passed = True

    return GateResult(
        gate_name="GATE_AP_SYSTEM_INTROSPECTION",
        passed=passed,
        status="TRUE",
        message="AP system introspection report written.",
        details=details,
    )

def main() -> int:
    module = load_module_from_path("migrated_ap_core_rule_activation", AP_CORE_PATH)

    results = [
        gate_builtin_rule_functions_exist(module),
        gate_builtin_rule_function_responses(module),
        gate_custom_rule_activation(module),
        gate_ap_system_introspection(module),
    ]

    all_passed = all(result.passed for result in results)

    report = {
        "refactor_id": "AP_CORE_RULE_ACTIVATION_001",
        "tier_authority": "ENGAINOS_TIER1",
        "lane": "engainos_core_authority",
        "stack": "engainos",
        "ap_core_path": str(AP_CORE_PATH),
        "gates": [asdict(result) for result in results],
        "acceptance": "ACCEPTED" if all_passed else "REJECTED",
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    for result in results:
        label = "PASS" if result.passed else "FAIL"
        print(f"[gate_ap_core_rule_activation][{result.gate_name}] {label}: {result.message}")

    print(f"[gate_ap_core_rule_activation][REPORT] {REPORT_PATH}")
    print(f"[gate_ap_core_rule_activation][ALL_GATES] {'true' if all_passed else 'false'}")

    return 0 if all_passed else 2

if __name__ == "__main__":
    raise SystemExit(main())
