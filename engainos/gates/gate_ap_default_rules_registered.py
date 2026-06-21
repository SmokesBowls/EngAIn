from __future__ import annotations
GATE_LIFECYCLE = "ACTIVE_CONTRACT"
GATE_BOARD = "ENGAINOS_AP_MIGRATION_AND_CONTRACT_BOARD"


from dataclasses import dataclass, asdict
from pathlib import Path
import ast
import json
import sys
from typing import Any

REPO_ROOT = Path("/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn")

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

AP_CORE_PATH = REPO_ROOT / "engainos/core/ap_core.py"
AP_ENGINE_PATH = REPO_ROOT / "engainos/core/ap_engine.py"
REPORT_PATH = REPO_ROOT / "scratch/ap_default_rules_registered_report.json"

@dataclass(frozen=True)
class GateResult:
    gate_name: str
    passed: bool
    status: str
    message: str
    details: dict[str, Any]

FORBIDDEN_IMPORTS = {
    "godot",
    "bpy",
    "uvicorn",
    "fastapi",
    "socket",
    "requests",
    "httpx",
    "subprocess",
}

def normalize_violations(violations: list[Any]) -> list[dict[str, Any]]:
    normalized = []

    for violation in violations:
        if hasattr(violation, "__dict__"):
            normalized.append(dict(violation.__dict__))
        else:
            normalized.append({"repr": repr(violation)})

    return normalized

def collect_imports(path: Path) -> list[str]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    imports: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)

        if isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")

    return sorted(set(imports))

def gate_files_exist() -> GateResult:
    missing = []

    if not AP_CORE_PATH.exists():
        missing.append(str(AP_CORE_PATH))

    if not AP_ENGINE_PATH.exists():
        missing.append(str(AP_ENGINE_PATH))

    passed = not missing

    return GateResult(
        gate_name="GATE_FILES_EXIST",
        passed=passed,
        status="TRUE" if passed else "FALSE",
        message="AP core and AP engine files exist." if passed else "Required AP files are missing.",
        details={"missing": missing},
    )

def gate_no_forbidden_imports() -> GateResult:
    imports = collect_imports(AP_ENGINE_PATH)
    forbidden = [
        item for item in imports
        if item.split(".")[0] in FORBIDDEN_IMPORTS
    ]

    passed = not forbidden

    return GateResult(
        gate_name="GATE_NO_FORBIDDEN_IMPORTS",
        passed=passed,
        status="TRUE" if passed else "FALSE",
        message="AP engine has no bridge/render/server imports." if passed else "AP engine imports forbidden bridge/render/server modules.",
        details={
            "imports": imports,
            "forbidden": forbidden,
        },
    )

def gate_default_rules_declared() -> GateResult:
    from engainos.core import ap_engine

    expected = {
        "no_negative_health",
        "no_double_guard",
    }

    actual = set(getattr(ap_engine, "DEFAULT_RULES_REGISTERED", []))
    missing = sorted(expected - actual)

    passed = not missing

    return GateResult(
        gate_name="GATE_DEFAULT_RULES_DECLARED",
        passed=passed,
        status="TRUE" if passed else "FALSE",
        message="Default AP rules are declared." if passed else "Default AP rules are missing from declaration list.",
        details={
            "expected": sorted(expected),
            "actual": sorted(actual),
            "missing": missing,
        },
    )

def gate_default_system_rejects_negative_health() -> GateResult:
    from engainos.core.ap_engine import check_default_ap, is_default_valid

    snapshot = {
        "entities": {
            "hero": {
                "health": 10
            }
        }
    }
    delta = {
        "entities": {
            "hero": {
                "health": -1
            }
        }
    }

    violations = check_default_ap(snapshot, delta)
    valid = is_default_valid(snapshot, delta)

    passed = len(violations) >= 1 and valid is False

    return GateResult(
        gate_name="GATE_REJECTS_NEGATIVE_HEALTH",
        passed=passed,
        status="TRUE" if passed else "FALSE",
        message="Default AP rejects negative health." if passed else "Default AP did not reject negative health.",
        details={
            "snapshot": snapshot,
            "delta": delta,
            "violations": normalize_violations(violations),
            "is_valid": valid,
        },
    )

def gate_default_system_rejects_double_guard() -> GateResult:
    from engainos.core.ap_engine import check_default_ap, is_default_valid

    snapshot = {}
    delta = {
        "guards": {
            "north_gate": "guard_001",
            "south_gate": "guard_001"
        }
    }

    violations = check_default_ap(snapshot, delta)
    valid = is_default_valid(snapshot, delta)

    passed = len(violations) >= 1 and valid is False

    return GateResult(
        gate_name="GATE_REJECTS_DOUBLE_GUARD",
        passed=passed,
        status="TRUE" if passed else "FALSE",
        message="Default AP rejects double guard." if passed else "Default AP did not reject double guard.",
        details={
            "snapshot": snapshot,
            "delta": delta,
            "violations": normalize_violations(violations),
            "is_valid": valid,
        },
    )

def gate_default_system_allows_valid_delta() -> GateResult:
    from engainos.core.ap_engine import check_default_ap, is_default_valid

    snapshot = {
        "entities": {
            "hero": {
                "health": 10
            }
        }
    }
    delta = {
        "entities": {
            "hero": {
                "health": 9
            }
        },
        "guards": {
            "north_gate": "guard_001",
            "south_gate": "guard_002"
        }
    }

    violations = check_default_ap(snapshot, delta)
    valid = is_default_valid(snapshot, delta)

    passed = len(violations) == 0 and valid is True

    return GateResult(
        gate_name="GATE_ALLOWS_VALID_DELTA",
        passed=passed,
        status="TRUE" if passed else "FALSE",
        message="Default AP allows valid delta." if passed else "Default AP rejected a valid delta.",
        details={
            "snapshot": snapshot,
            "delta": delta,
            "violations": normalize_violations(violations),
            "is_valid": valid,
        },
    )

def main() -> int:
    results = [
        gate_files_exist(),
    ]

    if results[0].passed:
        results.extend(
            [
                gate_no_forbidden_imports(),
                gate_default_rules_declared(),
                gate_default_system_rejects_negative_health(),
                gate_default_system_rejects_double_guard(),
                gate_default_system_allows_valid_delta(),
            ]
        )

    all_passed = all(result.passed for result in results)

    report = {
        "refactor_id": "AP_DEFAULT_RULES_REGISTERED_001",
        "tier_authority": "ENGAINOS_TIER1",
        "lane": "engainos_core_authority",
        "stack": "engainos",
        "ap_core_path": str(AP_CORE_PATH),
        "ap_engine_path": str(AP_ENGINE_PATH),
        "authority_change": "no",
        "behavior_change": "yes_default_rules_now_explicitly_registered",
        "schema_change": "no",
        "runtime_output_change": "yes_ap_default_engine_now_rejects_invalid_deltas",
        "gates": [asdict(result) for result in results],
        "acceptance": "ACCEPTED" if all_passed else "REJECTED",
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    for result in results:
        label = "PASS" if result.passed else "FAIL"
        print(f"[gate_ap_default_rules_registered][{result.gate_name}] {label}: {result.message}")

    print(f"[gate_ap_default_rules_registered][REPORT] {REPORT_PATH}")
    print(f"[gate_ap_default_rules_registered][ALL_GATES] {'true' if all_passed else 'false'}")

    return 0 if all_passed else 2

if __name__ == "__main__":
    raise SystemExit(main())
