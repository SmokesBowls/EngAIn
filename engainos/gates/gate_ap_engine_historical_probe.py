from __future__ import annotations
GATE_LIFECYCLE = "ACTIVE_VERIFICATION"
GATE_BOARD = "ENGAINOS_AP_MIGRATION_AND_CONTRACT_BOARD"


from dataclasses import dataclass, asdict
from pathlib import Path
import importlib.util
import inspect
import json
import sys
from typing import Any

REPO_ROOT = Path("/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn")

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

HISTORICAL_PATH = REPO_ROOT / "godotengain/engainos/core/ap_engine.py"
ROOT_PATH = REPO_ROOT / "engainos/core/ap_engine.py"
REPORT_PATH = REPO_ROOT / "scratch/ap_engine_historical_probe_report.json"

@dataclass(frozen=True)
class GateResult:
    gate_name: str
    passed: bool
    status: str
    message: str
    details: dict[str, Any]

HISTORICAL_SYMBOLS = [
    "CANONICAL_AP_ENGINE_MODULE",
    "APInternalRule",
    "StateProvider",
    "ZWAPEngine",
    "load_rules_from_scene",
]

ROOT_BOOTSTRAP_SYMBOLS = [
    "DEFAULT_RULES_REGISTERED",
    "register_default_rules",
    "build_default_ap_system",
    "check_default_ap",
    "is_default_valid",
]

def load_module_from_path(module_name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(module_name, path)

    if spec is None or spec.loader is None:
        raise ImportError(f"Could not create import spec for {path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

def safe_signature(obj: Any) -> str:
    try:
        return str(inspect.signature(obj))
    except Exception as exc:
        return f"<signature_error:{type(exc).__name__}:{exc}>"

def safe_construct(cls: Any) -> dict[str, Any]:
    try:
        instance = cls()
        return {
            "ok": True,
            "type": type(instance).__name__,
            "dir": sorted(name for name in dir(instance) if not name.startswith("__")),
            "dict": dict(getattr(instance, "__dict__", {})),
        }
    except Exception as exc:
        return {
            "ok": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }

def describe_symbol(module: Any, symbol: str) -> dict[str, Any]:
    if not hasattr(module, symbol):
        return {
            "exists": False,
            "type": "missing",
        }

    obj = getattr(module, symbol)

    profile: dict[str, Any] = {
        "exists": True,
        "type": type(obj).__name__,
        "repr": repr(obj),
        "callable": callable(obj),
    }

    if callable(obj):
        profile["signature"] = safe_signature(obj)

    if inspect.isclass(obj):
        profile["construct_no_args"] = safe_construct(obj)

    return profile

def gate_historical_symbols_present(historical: Any) -> GateResult:
    profiles = {
        symbol: describe_symbol(historical, symbol)
        for symbol in HISTORICAL_SYMBOLS
    }

    missing = [
        symbol for symbol, profile in profiles.items()
        if not profile["exists"]
    ]

    passed = not missing

    return GateResult(
        gate_name="GATE_HISTORICAL_SYMBOLS_PRESENT",
        passed=passed,
        status="TRUE" if passed else "FALSE",
        message="Historical AP engine symbols are present." if passed else "Historical AP engine symbols are missing.",
        details={
            "required": HISTORICAL_SYMBOLS,
            "missing": missing,
            "profiles": profiles,
        },
    )

def gate_root_bootstrap_still_present(root: Any) -> GateResult:
    profiles = {
        symbol: describe_symbol(root, symbol)
        for symbol in ROOT_BOOTSTRAP_SYMBOLS
    }

    missing = [
        symbol for symbol, profile in profiles.items()
        if not profile["exists"]
    ]

    passed = not missing

    return GateResult(
        gate_name="GATE_ROOT_BOOTSTRAP_STILL_PRESENT",
        passed=passed,
        status="TRUE" if passed else "FALSE",
        message="Root AP default bootstrap symbols are present." if passed else "Root AP default bootstrap symbols are missing.",
        details={
            "required": ROOT_BOOTSTRAP_SYMBOLS,
            "missing": missing,
            "profiles": profiles,
        },
    )

def gate_historical_load_rules_probe(historical: Any) -> GateResult:
    if not hasattr(historical, "load_rules_from_scene"):
        return GateResult(
            gate_name="GATE_HISTORICAL_LOAD_RULES_PROBE",
            passed=False,
            status="FALSE",
            message="load_rules_from_scene is missing.",
            details={},
        )

    fn = getattr(historical, "load_rules_from_scene")

    scratch_dir = REPO_ROOT / "scratch" / "ap_engine_probe_scenes"
    scratch_dir.mkdir(parents=True, exist_ok=True)

    scene_cases = [
        {
            "case_id": "empty_json_object",
            "filename": "empty_json_object.json",
            "content": {},
        },
        {
            "case_id": "ap_rules_empty_list",
            "filename": "ap_rules_empty_list.json",
            "content": {
                "scene_id": "probe.empty_rules",
                "ap_rules": [],
            },
        },
        {
            "case_id": "rules_empty_list",
            "filename": "rules_empty_list.json",
            "content": {
                "scene_id": "probe.rules_empty",
                "rules": [],
            },
        },
        {
            "case_id": "ap_rules_dict_shape",
            "filename": "ap_rules_dict_shape.json",
            "content": {
                "scene_id": "probe.dict_rules",
                "ap_rules": {
                    "rule_001": {
                        "id": "rule_001",
                        "type": "ap_rule",
                        "tags": ["probe"],
                        "inputs": [],
                        "requires": [],
                        "conflicts": [],
                        "effects": [],
                        "priority": 0,
                    }
                },
            },
        },
    ]

    cases = []

    for case in scene_cases:
        scene_path = scratch_dir / case["filename"]
        scene_path.write_text(json.dumps(case["content"], indent=2, sort_keys=True), encoding="utf-8")

        try:
            value = fn(str(scene_path))
            cases.append(
                {
                    "case_id": case["case_id"],
                    "scene_path": str(scene_path),
                    "content": case["content"],
                    "ok": True,
                    "value_type": type(value).__name__,
                    "value_repr": repr(value),
                }
            )
        except Exception as exc:
            cases.append(
                {
                    "case_id": case["case_id"],
                    "scene_path": str(scene_path),
                    "content": case["content"],
                    "ok": False,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }
            )

    passed = any(case["ok"] for case in cases)

    signal_quality = "SIGNAL" if passed else "SIGNAL_FAIL"

    return GateResult(
        gate_name="GATE_HISTORICAL_LOAD_RULES_PROBE",
        passed=passed,
        status="TRUE" if passed else "FALSE",
        message="Historical load_rules_from_scene accepts path-shaped scene inputs." if passed else "Historical load_rules_from_scene failed with path-shaped scene inputs.",
        details={
            "signature": safe_signature(fn),
            "signal_quality": signal_quality,
            "cases": cases,
        },
    )

def main() -> int:
    historical = load_module_from_path("historical_ap_engine_probe", HISTORICAL_PATH)
    root = load_module_from_path("root_ap_engine_probe", ROOT_PATH)

    results = [
        gate_historical_symbols_present(historical),
        gate_root_bootstrap_still_present(root),
        gate_historical_load_rules_probe(historical),
    ]

    all_passed = all(result.passed for result in results)

    report = {
        "refactor_id": "AP_ENGINE_HISTORICAL_PROBE_001",
        "tier_authority": "ENGAINOS_TIER1",
        "lane": "engainos_core_authority",
        "stack": "engainos",
        "historical_path": str(HISTORICAL_PATH),
        "root_path": str(ROOT_PATH),
        "merge_allowed": False,
        "overwrite_allowed": False,
        "gates": [asdict(result) for result in results],
        "acceptance": "ACCEPTED_FOR_MERGE_DESIGN" if all_passed else "REJECTED",
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    for result in results:
        label = "PASS" if result.passed else "FAIL"
        print(f"[gate_ap_engine_historical_probe][{result.gate_name}] {label}: {result.message}")

    print("[gate_ap_engine_historical_probe][MERGE_ALLOWED] false")
    print("[gate_ap_engine_historical_probe][OVERWRITE_ALLOWED] false")
    print(f"[gate_ap_engine_historical_probe][REPORT] {REPORT_PATH}")
    print(f"[gate_ap_engine_historical_probe][ALL_GATES] {'true' if all_passed else 'false'}")

    return 0 if all_passed else 2

if __name__ == "__main__":
    raise SystemExit(main())
