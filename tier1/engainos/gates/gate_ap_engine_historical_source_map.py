from __future__ import annotations
GATE_LIFECYCLE = "ACTIVE_VERIFICATION"
GATE_BOARD = "ENGAINOS_AP_MIGRATION_AND_CONTRACT_BOARD"


from dataclasses import dataclass, asdict
from pathlib import Path
import ast
import json
from typing import Any

REPO_ROOT = Path("/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn")

HISTORICAL_PATH = REPO_ROOT / "godotengain/engainos/core/ap_engine.py"
ROOT_PATH = REPO_ROOT / "engainos/core/ap_engine.py"
REPORT_PATH = REPO_ROOT / "scratch/ap_engine_historical_source_map_report.json"

@dataclass(frozen=True)
class GateResult:
    gate_name: str
    passed: bool
    status: str
    message: str
    details: dict[str, Any]

TARGET_SYMBOLS = [
    "APInternalRule",
    "StateProvider",
    "ZWAPEngine",
    "load_rules_from_scene",
]

def read_source(path: Path) -> str:
    return path.read_text(encoding="utf-8")

def get_source_segment(source: str, node: ast.AST) -> str:
    segment = ast.get_source_segment(source, node)
    return segment if segment is not None else ""

def collect_target_source() -> dict[str, dict[str, Any]]:
    source = read_source(HISTORICAL_PATH)
    tree = ast.parse(source)

    found: dict[str, dict[str, Any]] = {}

    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name in TARGET_SYMBOLS:
                found[node.name] = {
                    "node_type": type(node).__name__,
                    "lineno": getattr(node, "lineno", None),
                    "end_lineno": getattr(node, "end_lineno", None),
                    "source": get_source_segment(source, node),
                }

    return found

def collect_imports(path: Path) -> list[str]:
    source = read_source(path)
    tree = ast.parse(source)
    imports: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)

        if isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")

    return sorted(set(imports))

def collect_method_names(source_text: str) -> dict[str, list[str]]:
    tree = ast.parse(read_source(HISTORICAL_PATH))
    methods: dict[str, list[str]] = {}

    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name in TARGET_SYMBOLS:
            methods[node.name] = sorted(
                child.name
                for child in node.body
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
            )

    return methods

def gate_source_symbols_extracted() -> GateResult:
    found = collect_target_source()
    missing = sorted(set(TARGET_SYMBOLS) - set(found))

    passed = not missing

    return GateResult(
        gate_name="GATE_SOURCE_SYMBOLS_EXTRACTED",
        passed=passed,
        status="TRUE" if passed else "FALSE",
        message="Historical AP engine target source bodies extracted." if passed else "Some historical AP engine source bodies are missing.",
        details={
            "target_symbols": TARGET_SYMBOLS,
            "missing": missing,
            "found": found,
        },
    )

def gate_imports_recorded() -> GateResult:
    imports = collect_imports(HISTORICAL_PATH)

    passed = True

    return GateResult(
        gate_name="GATE_IMPORTS_RECORDED",
        passed=passed,
        status="TRUE",
        message="Historical AP engine imports recorded.",
        details={
            "imports": imports,
        },
    )

def gate_methods_recorded() -> GateResult:
    methods = collect_method_names(read_source(HISTORICAL_PATH))

    passed = True

    return GateResult(
        gate_name="GATE_METHODS_RECORDED",
        passed=passed,
        status="TRUE",
        message="Historical AP engine class methods recorded.",
        details={
            "methods": methods,
        },
    )

def main() -> int:
    results = [
        gate_source_symbols_extracted(),
        gate_imports_recorded(),
        gate_methods_recorded(),
    ]

    all_passed = all(result.passed for result in results)

    report = {
        "refactor_id": "AP_ENGINE_HISTORICAL_SOURCE_MAP_001",
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
        print(f"[gate_ap_engine_historical_source_map][{result.gate_name}] {label}: {result.message}")

    print("[gate_ap_engine_historical_source_map][MERGE_ALLOWED] false")
    print("[gate_ap_engine_historical_source_map][OVERWRITE_ALLOWED] false")
    print(f"[gate_ap_engine_historical_source_map][REPORT] {REPORT_PATH}")
    print(f"[gate_ap_engine_historical_source_map][ALL_GATES] {'true' if all_passed else 'false'}")

    return 0 if all_passed else 2

if __name__ == "__main__":
    raise SystemExit(main())
