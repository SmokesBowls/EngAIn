#!/usr/bin/env python3
"""Gate: Verify that ap_zw_engine.py no longer claims CANONICAL_AP_ENGINE_MODULE
and that it correctly declares LEGACY_SOURCE_AP_ENGINE_MODULE and
MIGRATED_AP_ZW_ENGINE_MODULE.
"""

from __future__ import annotations
GATE_LIFECYCLE = "ACTIVE_VERIFICATION"
GATE_BOARD = "ENGAINOS_AP_MIGRATION_AND_CONTRACT_BOARD"


from dataclasses import dataclass, asdict
from pathlib import Path
import ast
import json
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ZW_ENGINE_PATH = PROJECT_ROOT / "engainos/core/ap_zw_engine.py"
REPORT_PATH = PROJECT_ROOT / "scratch/ap_zw_engine_canonical_claim_report.json"

@dataclass(frozen=True)
class GateResult:
    gate_name: str
    passed: bool
    status: str
    message: str
    details: dict[str, Any]

def collect_module_assignments(file_path: Path) -> dict[str, Any]:
    source = file_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    assignments: dict[str, Any] = {}

    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    try:
                        assignments[target.id] = ast.literal_eval(node.value)
                    except Exception:
                        assignments[target.id] = "<non_literal>"

        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            try:
                assignments[node.target.id] = ast.literal_eval(node.value)
            except Exception:
                assignments[node.target.id] = "<non_literal>"

    return assignments

def gate_no_stale_canonical_claim() -> GateResult:
    assignments = collect_module_assignments(ZW_ENGINE_PATH)

    has_canonical = "CANONICAL_AP_ENGINE_MODULE" in assignments

    legacy_value = assignments.get("LEGACY_SOURCE_AP_ENGINE_MODULE")
    migrated_value = assignments.get("MIGRATED_AP_ZW_ENGINE_MODULE")

    passed = (
        not has_canonical
        and legacy_value == "godotengain.engainos.core.ap_engine"
        and migrated_value == "engainos.core.ap_zw_engine"
    )

    return GateResult(
        gate_name="GATE_ZW_ENGINE_CANONICAL_CLAIM",
        passed=passed,
        status="TRUE" if passed else "FALSE",
        message=(
            "Canonical claim removed; legacy provenance and migrated module identity are correct."
            if passed
            else "Canonical claim or migration identity constants are incorrect."
        ),
        details={
            "has_CANONICAL_AP_ENGINE_MODULE": has_canonical,
            "LEGACY_SOURCE_AP_ENGINE_MODULE": legacy_value,
            "MIGRATED_AP_ZW_ENGINE_MODULE": migrated_value,
            "expected_legacy": "godotengain.engainos.core.ap_engine",
            "expected_migrated": "engainos.core.ap_zw_engine",
        },
    )

def main() -> int:
    results = [
        gate_no_stale_canonical_claim(),
    ]

    all_passed = all(result.passed for result in results)

    report = {
        "refactor_id": "AP_ZW_ENGINE_CANONICAL_CLAIM_001",
        "tier_authority": "ENGAINOS_TIER1",
        "lane": "engainos_core_authority",
        "stack": "engainos",
        "zw_engine_path": str(ZW_ENGINE_PATH),
        "gates": [asdict(result) for result in results],
        "acceptance": "ACCEPTED" if all_passed else "REJECTED",
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    for result in results:
        label = "PASS" if result.passed else "FAIL"
        print(f"[gate_ap_zw_engine_canonical_claim][{result.gate_name}] {label}: {result.message}")

    print(f"[gate_ap_zw_engine_canonical_claim][REPORT] {REPORT_PATH}")
    print(f"[gate_ap_zw_engine_canonical_claim][ALL_GATES] {'true' if all_passed else 'false'}")

    return 0 if all_passed else 2

if __name__ == "__main__":
    raise SystemExit(main())
