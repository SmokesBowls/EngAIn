from __future__ import annotations
GATE_LIFECYCLE = "ACTIVE_VERIFICATION"
GATE_BOARD = "ENGAINOS_AP_MIGRATION_AND_CONTRACT_BOARD"


from dataclasses import dataclass, asdict
from pathlib import Path
import ast
import importlib.util
import json
import os
import sys
from typing import Any

REPO_ROOT = Path("/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn")

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

HISTORICAL_PATH = REPO_ROOT / "godotengain/engainos/core/ap_engine.py"
ZW_PATH = REPO_ROOT / "engainos/core/ap_zw_engine.py"
ROOT_AP_ENGINE_PATH = REPO_ROOT / "engainos/core/ap_engine.py"
REPORT_PATH = REPO_ROOT / "scratch/ap_zw_engine_migration_report.json"

@dataclass(frozen=True)
class GateResult:
    gate_name: str
    passed: bool
    status: str
    message: str
    details: dict[str, Any]

REQUIRED_ZW_SYMBOLS = {
    "LEGACY_SOURCE_AP_ENGINE_MODULE",
    "MIGRATED_AP_ZW_ENGINE_MODULE",
    "APInternalRule",
    "StateProvider",
    "ZWAPEngine",
    "load_rules_from_scene",
}

REQUIRED_ROOT_BOOTSTRAP_SYMBOLS = {
    "DEFAULT_RULES_REGISTERED",
    "register_default_rules",
    "build_default_ap_system",
    "check_default_ap",
    "is_default_valid",
}

FORBIDDEN_IMPORT_ROOTS = {
    "godot",
    "bpy",
    "uvicorn",
    "fastapi",
    "socket",
    "requests",
    "httpx",
    "subprocess",
}

def load_module_from_path(module_name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(module_name, path)

    if spec is None or spec.loader is None:
        raise ImportError(f"Could not create import spec for {path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

def read_source(path: Path) -> str:
    return path.read_text(encoding="utf-8")

def parse_tree(path: Path) -> ast.Module:
    return ast.parse(read_source(path))

def collect_imports(path: Path) -> list[str]:
    tree = parse_tree(path)
    imports: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)

        if isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")

    return sorted(set(imports))

def collect_public_symbols(path: Path) -> set[str]:
    tree = parse_tree(path)
    symbols: set[str] = set()

    for node in tree.body:
        if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
            symbols.add(node.name)

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_"):
            symbols.add(node.name)

        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and not target.id.startswith("_"):
                    symbols.add(target.id)

        if isinstance(node, ast.AnnAssign):
            target = node.target
            if isinstance(target, ast.Name) and not target.id.startswith("_"):
                symbols.add(target.id)

    return symbols

def gate_files_exist() -> GateResult:
    missing = []

    for path in [HISTORICAL_PATH, ZW_PATH, ROOT_AP_ENGINE_PATH]:
        if not path.exists():
            missing.append(str(path))

    passed = not missing

    return GateResult(
        gate_name="GATE_FILES_EXIST",
        passed=passed,
        status="TRUE" if passed else "FALSE",
        message="Historical, migrated ZW engine, and root AP engine files exist." if passed else "One or more required files are missing.",
        details={
            "historical_path": str(HISTORICAL_PATH),
            "zw_path": str(ZW_PATH),
            "root_ap_engine_path": str(ROOT_AP_ENGINE_PATH),
            "missing": missing,
        },
    )

def gate_zw_symbols_preserved() -> GateResult:
    symbols = collect_public_symbols(ZW_PATH)
    missing = sorted(REQUIRED_ZW_SYMBOLS - symbols)

    passed = not missing

    return GateResult(
        gate_name="GATE_ZW_SYMBOLS_PRESERVED",
        passed=passed,
        status="TRUE" if passed else "FALSE",
        message="ap_zw_engine.py preserves historical ZW AP symbols." if passed else "ap_zw_engine.py is missing historical ZW AP symbols.",
        details={
            "required": sorted(REQUIRED_ZW_SYMBOLS),
            "actual": sorted(symbols),
            "missing": missing,
        },
    )

def gate_root_bootstrap_preserved() -> GateResult:
    symbols = collect_public_symbols(ROOT_AP_ENGINE_PATH)
    missing = sorted(REQUIRED_ROOT_BOOTSTRAP_SYMBOLS - symbols)

    passed = not missing

    return GateResult(
        gate_name="GATE_ROOT_AP_ENGINE_BOOTSTRAP_PRESERVED",
        passed=passed,
        status="TRUE" if passed else "FALSE",
        message="Root ap_engine.py default bootstrap remains intact." if passed else "Root ap_engine.py default bootstrap is missing symbols.",
        details={
            "required": sorted(REQUIRED_ROOT_BOOTSTRAP_SYMBOLS),
            "actual": sorted(symbols),
            "missing": missing,
        },
    )

def gate_no_forbidden_imports() -> GateResult:
    imports = collect_imports(ZW_PATH)
    forbidden = [
        item for item in imports
        if item.split(".")[0] in FORBIDDEN_IMPORT_ROOTS
    ]

    passed = not forbidden

    return GateResult(
        gate_name="GATE_NO_FORBIDDEN_IMPORTS",
        passed=passed,
        status="TRUE" if passed else "FALSE",
        message="ap_zw_engine.py has no Godot/server/render/network subprocess imports." if passed else "ap_zw_engine.py has forbidden imports.",
        details={
            "imports": imports,
            "forbidden": forbidden,
        },
    )

def gate_tick_execution_has_hidden_write() -> GateResult:
    source = read_source(ZW_PATH)

    write_fragments = [
        "def execute_tick",
        "self._append_zon_event",
        "def _append_zon_event",
        "timeline.jsonl",
    ]

    fence_fragments = [
        "enable_timeline_write: bool = False",
        "timeline_root: Optional[str] = None",
        "self.enable_timeline_write = enable_timeline_write",
        "self.timeline_root = timeline_root",
        "if not self.enable_timeline_write:",
        "timeline_write_skipped: enable_timeline_write is False",
        "if self.timeline_root:",
    ]

    missing_write_fragments = [
        item for item in write_fragments
        if item not in source
    ]

    missing_fence_fragments = [
        item for item in fence_fragments
        if item not in source
    ]

    write_capability_detected = not missing_write_fragments
    fence_detected = not missing_fence_fragments

    # Passing condition:
    # The engine may contain timeline write capability, but it must be fenced by default.
    passed = write_capability_detected and fence_detected

    return GateResult(
        gate_name="GATE_TICK_EXECUTION_HAS_NO_HIDDEN_WRITE_BYPASS",
        passed=passed,
        status="TRUE" if passed else "FALSE",
        message="execute_tick timeline writing is fenced by explicit enable_timeline_write." if passed else "execute_tick timeline write capability is not fully fenced.",
        details={
            "write_capability_detected": write_capability_detected,
            "missing_write_fragments": missing_write_fragments,
            "fence_detected": fence_detected,
            "missing_fence_fragments": missing_fence_fragments,
            "timeline_write_default": "disabled_when_fence_detected",
            "runtime_wiring_condition": "caller must explicitly opt into enable_timeline_write=True",
        },
    )

def gate_load_rules_path_only() -> GateResult:
    module = load_module_from_path("ap_zw_engine_migration_probe", ZW_PATH)

    scratch_dir = REPO_ROOT / "scratch" / "ap_zw_engine_gate"
    scratch_dir.mkdir(parents=True, exist_ok=True)

    scene_path = scratch_dir / "scene_rules_probe.json"
    scene_path.write_text(
        json.dumps(
            {
                "scene_id": "probe.scene",
                "rules": {
                    "rule_probe": {
                        "tags": ["probe"],
                        "requires": [],
                        "conflicts": [],
                        "effects": [],
                        "priority": 0,
                    }
                },
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    try:
        value = module.load_rules_from_scene(str(scene_path))
        ok = isinstance(value, dict) and "rule_probe" in value
        error = None
    except Exception as exc:
        value = None
        ok = False
        error = {
            "error_type": type(exc).__name__,
            "error": str(exc),
        }

    return GateResult(
        gate_name="GATE_LOAD_RULES_PATH_ONLY",
        passed=ok,
        status="TRUE" if ok else "FALSE",
        message="load_rules_from_scene reads a JSON path and returns rules dict." if ok else "load_rules_from_scene failed path-shaped rules loading.",
        details={
            "scene_path": str(scene_path),
            "value_repr": repr(value),
            "error": error,
        },
    )

def gate_state_provider_local_mutation_only() -> GateResult:
    module = load_module_from_path("ap_zw_engine_state_probe", ZW_PATH)
    provider = module.StateProvider()

    before = provider.snapshot()
    provider.set_flag("hero", "awake", True)
    provider.set_stat("hero", "health", 9)
    provider.set_location("hero", "north_gate")
    provider.add_inventory("hero", "key", 1)
    provider.set_time_dilation("hero", 0.5)
    after = provider.snapshot()

    expected = (
        after["flags"]["hero"]["awake"] is True
        and after["stats"]["hero"]["health"] == 9
        and after["locations"]["hero"] == "north_gate"
        and after["inventory"]["hero"]["key"] == 1
        and after["time_dilation"]["hero"] == 0.5
    )

    return GateResult(
        gate_name="GATE_STATE_PROVIDER_LOCAL_MUTATION_ONLY",
        passed=expected,
        status="TRUE" if expected else "FALSE",
        message="StateProvider mutates only its internal state container in probe." if expected else "StateProvider did not behave as expected.",
        details={
            "before": before,
            "after": after,
        },
    )

def main() -> int:
    results = [
        gate_files_exist(),
    ]

    if results[0].passed:
        results.extend(
            [
                gate_zw_symbols_preserved(),
                gate_root_bootstrap_preserved(),
                gate_no_forbidden_imports(),
                gate_load_rules_path_only(),
                gate_state_provider_local_mutation_only(),
                gate_tick_execution_has_hidden_write(),
            ]
        )

    all_hard_passed = all(result.passed for result in results)

    # Migration can be accepted as quarantined even when hidden-write gate fails,
    # but runtime wiring must remain blocked.
    hidden_write_gate = next(
        (result for result in results if result.gate_name == "GATE_TICK_EXECUTION_HAS_NO_HIDDEN_WRITE_BYPASS"),
        None,
    )

    quarantine_accepted = all(
        result.passed
        for result in results
        if result.gate_name != "GATE_TICK_EXECUTION_HAS_NO_HIDDEN_WRITE_BYPASS"
    )

    runtime_wiring_allowed = hidden_write_gate.passed if hidden_write_gate else False

    report = {
        "refactor_id": "AP_ZW_ENGINE_MIGRATION_001",
        "tier_authority": "ENGAINOS_TIER1",
        "lane": "engainos_core_authority",
        "stack": "engainos",
        "historical_path": str(HISTORICAL_PATH),
        "zw_path": str(ZW_PATH),
        "root_ap_engine_path": str(ROOT_AP_ENGINE_PATH),
        "migration_acceptance": "ACCEPTED" if runtime_wiring_allowed else ("ACCEPTED_QUARANTINED" if quarantine_accepted else "REJECTED"),
        "runtime_wiring_allowed": runtime_wiring_allowed,
        "overwrite_allowed": False,
        "merge_into_root_ap_engine_allowed": False,
        "requires_fence_before_runtime": not runtime_wiring_allowed,
        "gates": [asdict(result) for result in results],
        "acceptance": "ACCEPTED" if runtime_wiring_allowed else ("ACCEPTED_QUARANTINED" if quarantine_accepted else "REJECTED"),
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    for result in results:
        label = "PASS" if result.passed else "FAIL"
        print(f"[gate_ap_zw_engine_migration][{result.gate_name}] {label}: {result.message}")

    print(f"[gate_ap_zw_engine_migration][MIGRATION_ACCEPTANCE] {report['migration_acceptance']}")
    print(f"[gate_ap_zw_engine_migration][RUNTIME_WIRING_ALLOWED] {'true' if runtime_wiring_allowed else 'false'}")
    print("[gate_ap_zw_engine_migration][OVERWRITE_ALLOWED] false")
    print("[gate_ap_zw_engine_migration][MERGE_INTO_ROOT_AP_ENGINE_ALLOWED] false")
    print(f"[gate_ap_zw_engine_migration][REPORT] {REPORT_PATH}")
    print(f"[gate_ap_zw_engine_migration][ALL_HARD_GATES] {'true' if all_hard_passed else 'false'}")

    return 0 if quarantine_accepted else 2

if __name__ == "__main__":
    raise SystemExit(main())
