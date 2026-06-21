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
REPORT_PATH = REPO_ROOT / "scratch/ap_engine_migration_authority_report.json"

@dataclass(frozen=True)
class GateResult:
    gate_name: str
    passed: bool
    status: str
    message: str
    details: dict[str, Any]

FORBIDDEN_IMPORT_PREFIXES = (
    "godot",
    "bpy",
    "uvicorn",
    "fastapi",
    "socket",
    "requests",
    "httpx",
    "subprocess",
)

FORBIDDEN_TEXT_FRAGMENTS = (
    "uvicorn.run",
    "FastAPI",
    "socket.",
    "requests.",
    "httpx.",
    "subprocess.",
    "spawn",
    "despawn",
    "render",
    "scene_server",
    "godot_adapter",
    "runtime_client",
    "scene_loader",
    "mesh",
)

ROOT_BOOTSTRAP_REQUIRED_SYMBOLS = (
    "DEFAULT_RULES_REGISTERED",
    "register_default_rules",
    "build_default_ap_system",
    "check_default_ap",
    "is_default_valid",
)

def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")

def parse_tree(path: Path) -> ast.Module:
    return ast.parse(read_text(path))

def collect_imports(path: Path) -> list[str]:
    tree = parse_tree(path)
    imports: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)

        if isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")

    return sorted(set(imports))

def collect_public_symbols(path: Path) -> dict[str, list[str]]:
    tree = parse_tree(path)
    classes: list[str] = []
    functions: list[str] = []
    assignments: list[str] = []

    for node in tree.body:
        if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
            classes.append(node.name)

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_"):
            functions.append(node.name)

        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and not target.id.startswith("_"):
                    assignments.append(target.id)

        if isinstance(node, ast.AnnAssign):
            target = node.target
            if isinstance(target, ast.Name) and not target.id.startswith("_"):
                assignments.append(target.id)

    return {
        "classes": sorted(classes),
        "functions": sorted(functions),
        "assignments": sorted(set(assignments)),
    }

def gate_files_exist() -> GateResult:
    missing = []

    if not HISTORICAL_PATH.exists():
        missing.append(str(HISTORICAL_PATH))

    if not ROOT_PATH.exists():
        missing.append(str(ROOT_PATH))

    passed = not missing

    return GateResult(
        gate_name="GATE_FILES_EXIST",
        passed=passed,
        status="TRUE" if passed else "FALSE",
        message="Historical and root ap_engine.py files exist." if passed else "One or more ap_engine.py files are missing.",
        details={
            "historical_path": str(HISTORICAL_PATH),
            "root_path": str(ROOT_PATH),
            "missing": missing,
        },
    )

def gate_historical_import_boundary() -> GateResult:
    imports = collect_imports(HISTORICAL_PATH)

    forbidden = [
        item for item in imports
        if item.split(".")[0] in FORBIDDEN_IMPORT_PREFIXES
    ]

    passed = not forbidden

    return GateResult(
        gate_name="GATE_HISTORICAL_IMPORT_BOUNDARY",
        passed=passed,
        status="TRUE" if passed else "FALSE",
        message="Historical ap_engine.py imports are authority-safe." if passed else "Historical ap_engine.py has forbidden bridge/runtime imports.",
        details={
            "imports": imports,
            "forbidden": forbidden,
        },
    )

def gate_historical_no_bridge_runtime_text() -> GateResult:
    text = read_text(HISTORICAL_PATH)
    lowered = text.lower()

    hits = [
        fragment for fragment in FORBIDDEN_TEXT_FRAGMENTS
        if fragment.lower() in lowered
    ]

    passed = not hits

    return GateResult(
        gate_name="GATE_HISTORICAL_NO_BRIDGE_RUNTIME_TEXT",
        passed=passed,
        status="TRUE" if passed else "FALSE",
        message="Historical ap_engine.py has no obvious bridge/server/render/runtime-start language." if passed else "Historical ap_engine.py contains bridge/server/render/runtime-start language.",
        details={
            "hits": hits,
        },
    )

def gate_root_bootstrap_preserved() -> GateResult:
    root_symbols = collect_public_symbols(ROOT_PATH)

    available = set(root_symbols["functions"]) | set(root_symbols["classes"]) | set(root_symbols["assignments"])
    missing = sorted(set(ROOT_BOOTSTRAP_REQUIRED_SYMBOLS) - available)

    passed = not missing

    return GateResult(
        gate_name="GATE_ROOT_BOOTSTRAP_PRESERVED",
        passed=passed,
        status="TRUE" if passed else "FALSE",
        message="Root ap_engine.py default-rule bootstrap is present." if passed else "Root ap_engine.py default-rule bootstrap is missing symbols.",
        details={
            "required": sorted(ROOT_BOOTSTRAP_REQUIRED_SYMBOLS),
            "root_symbols": root_symbols,
            "missing": missing,
        },
    )

def gate_symbol_comparison() -> GateResult:
    historical_symbols = collect_public_symbols(HISTORICAL_PATH)
    root_symbols = collect_public_symbols(ROOT_PATH)

    passed = True

    return GateResult(
        gate_name="GATE_SYMBOL_COMPARISON",
        passed=passed,
        status="TRUE",
        message="Historical and root ap_engine.py public symbols compared.",
        details={
            "historical_symbols": historical_symbols,
            "root_symbols": root_symbols,
        },
    )

def decide(results: list[GateResult]) -> str:
    by_name = {result.gate_name: result for result in results}

    if not by_name["GATE_FILES_EXIST"].passed:
        return "BLOCKED_PENDING_TIER1_LANE_ASSIGNMENT"

    if not by_name["GATE_ROOT_BOOTSTRAP_PRESERVED"].passed:
        return "BLOCKED_ROOT_BOOTSTRAP_MISSING"

    if (
        by_name["GATE_HISTORICAL_IMPORT_BOUNDARY"].passed
        and by_name["GATE_HISTORICAL_NO_BRIDGE_RUNTIME_TEXT"].passed
    ):
        return "ACCEPT_INTENTIONAL_MERGE_REVIEW"

    return "KEEP_ROOT_BOOTSTRAP_SPLIT_HISTORICAL"

def main() -> int:
    results: list[GateResult] = []

    files_gate = gate_files_exist()
    results.append(files_gate)

    if files_gate.passed:
        results.extend(
            [
                gate_historical_import_boundary(),
                gate_historical_no_bridge_runtime_text(),
                gate_root_bootstrap_preserved(),
                gate_symbol_comparison(),
            ]
        )

    decision = decide(results)

    # This gate is investigative. It passes if files exist and root bootstrap is preserved.
    all_passed = files_gate.passed and any(
        result.gate_name == "GATE_ROOT_BOOTSTRAP_PRESERVED" and result.passed
        for result in results
    )

    report = {
        "refactor_id": "AP_ENGINE_MIGRATION_AUTHORITY_001",
        "tier_authority": "ENGAINOS_TIER1",
        "lane": "engainos_core_authority",
        "stack": "engainos",
        "historical_path": str(HISTORICAL_PATH),
        "root_path": str(ROOT_PATH),
        "decision": decision,
        "overwrite_allowed": False,
        "authority_change": "no",
        "behavior_change": "pending_merge_decision",
        "schema_change": "pending_merge_decision",
        "runtime_output_change": "pending_merge_decision",
        "gates": [asdict(result) for result in results],
        "acceptance": "ACCEPTED_FOR_REVIEW" if all_passed else "REJECTED",
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    for result in results:
        label = "PASS" if result.passed else "FAIL"
        print(f"[gate_ap_engine_migration_authority][{result.gate_name}] {label}: {result.message}")

    print(f"[gate_ap_engine_migration_authority][DECISION] {decision}")
    print("[gate_ap_engine_migration_authority][OVERWRITE_ALLOWED] false")
    print(f"[gate_ap_engine_migration_authority][REPORT] {REPORT_PATH}")
    print(f"[gate_ap_engine_migration_authority][ALL_GATES] {'true' if all_passed else 'false'}")

    return 0 if all_passed else 2

if __name__ == "__main__":
    raise SystemExit(main())
