from __future__ import annotations
GATE_LIFECYCLE = "ARCHIVED_NON_SIGNAL"
GATE_BOARD = "ENGAINOS_AP_MIGRATION_AND_CONTRACT_BOARD"


from dataclasses import dataclass, asdict
from pathlib import Path
import importlib.util
import inspect
import json
import sys
from typing import Any

REPO_ROOT = Path("/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn")

OLD_PATH = REPO_ROOT / "godotengain/engainos/core/ap_core.py"
NEW_PATH = REPO_ROOT / "engainos/core/ap_core.py"
REPORT_PATH = REPO_ROOT / "scratch/ap_core_signature_probe_report.json"

@dataclass(frozen=True)
class GateResult:
    gate_name: str
    passed: bool
    status: str
    message: str
    details: dict[str, Any]

PUBLIC_SYMBOLS = [
    "ApRule",
    "ApSystem",
    "Violation",
    "check_ap",
    "is_valid",
    "register_rule",
    "rule_no_double_guard",
    "rule_no_negative_health",
]

def load_module_from_path(module_name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(module_name, path)

    if spec is None or spec.loader is None:
        raise ImportError(f"Could not create import spec for {path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

def normalize_annotation_text(text: str) -> str:
    """
    Normalize module-loader aliases so old/new imports can be compared.

    Example:
      List[historical_ap_core_signature_probe.Violation]
      List[migrated_ap_core_signature_probe.Violation]

    Both become:
      List[Violation]
    """
    replacements = [
        "historical_ap_core_signature_probe.",
        "migrated_ap_core_signature_probe.",
        "historical_ap_core.",
        "migrated_ap_core.",
    ]

    normalized = text
    for item in replacements:
        normalized = normalized.replace(item, "")

    return normalized

def normalized_signature(obj: Any) -> dict[str, Any]:
    sig = inspect.signature(obj)

    params = []
    for name, param in sig.parameters.items():
        params.append(
            {
                "name": name,
                "kind": str(param.kind),
                "default": "EMPTY" if param.default is inspect._empty else repr(param.default),
                "annotation": "EMPTY"
                if param.annotation is inspect._empty
                else normalize_annotation_text(str(param.annotation)),
            }
        )

    return_annotation = (
        "EMPTY"
        if sig.return_annotation is inspect._empty
        else normalize_annotation_text(str(sig.return_annotation))
    )

    return {
        "parameters": params,
        "return_annotation": return_annotation,
    }

def collect_symbol_profiles(module: Any) -> dict[str, dict[str, Any]]:
    profiles: dict[str, dict[str, Any]] = {}

    for symbol in PUBLIC_SYMBOLS:
        if not hasattr(module, symbol):
            profiles[symbol] = {
                "exists": False,
                "type": "missing",
                "normalized_signature": "missing",
            }
            continue

        obj = getattr(module, symbol)

        profiles[symbol] = {
            "exists": True,
            "type": type(obj).__name__,
            "normalized_signature": normalized_signature(obj) if callable(obj) else "not_callable",
        }

    return profiles

def gate_signature_parity(old_profiles: dict[str, Any], new_profiles: dict[str, Any]) -> GateResult:
    passed = old_profiles == new_profiles

    return GateResult(
        gate_name="GATE_SIGNATURE_PARITY_NORMALIZED",
        passed=passed,
        status="TRUE" if passed else "FALSE",
        message="Historical and migrated AP core normalized signatures match." if passed else "Historical and migrated AP core normalized signatures differ.",
        details={
            "old_profiles": old_profiles,
            "new_profiles": new_profiles,
        },
    )

def main() -> int:
    old_module = load_module_from_path("historical_ap_core_signature_probe", OLD_PATH)
    new_module = load_module_from_path("migrated_ap_core_signature_probe", NEW_PATH)

    old_profiles = collect_symbol_profiles(old_module)
    new_profiles = collect_symbol_profiles(new_module)

    results = [
        gate_signature_parity(old_profiles, new_profiles),
    ]

    all_passed = all(result.passed for result in results)

    report = {
        "refactor_id": "AP_CORE_SIGNATURE_PROBE_002",
        "tier_authority": "ENGAINOS_TIER1",
        "lane": "engainos_core_authority",
        "stack": "engainos",
        "old_path": str(OLD_PATH),
        "new_path": str(NEW_PATH),
        "gates": [asdict(result) for result in results],
        "acceptance": "ACCEPTED" if all_passed else "REJECTED",
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    for result in results:
        label = "PASS" if result.passed else "FAIL"
        print(f"[gate_ap_core_signature_probe][{result.gate_name}] {label}: {result.message}")

    print(f"[gate_ap_core_signature_probe][REPORT] {REPORT_PATH}")
    print(f"[gate_ap_core_signature_probe][ALL_GATES] {'true' if all_passed else 'false'}")

    return 0 if all_passed else 2

if __name__ == "__main__":
    raise SystemExit(main())
