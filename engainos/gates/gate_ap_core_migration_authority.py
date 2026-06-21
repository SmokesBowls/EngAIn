# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/engainos/gates/gate_ap_core_migration_authority.py

from __future__ import annotations
GATE_LIFECYCLE = "PREFLIGHT"
GATE_BOARD = "ENGAINOS_AP_MIGRATION_AND_CONTRACT_BOARD"


from dataclasses import dataclass, asdict
from pathlib import Path
import ast
import json
from typing import Any

REPO_ROOT = Path("/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn")

SOURCE_PATH = REPO_ROOT / "godotengain/engainos/core/ap_core.py"
DEST_PATH = REPO_ROOT / "engainos/core/ap_core.py"
REPORT_PATH = REPO_ROOT / "scratch/ap_core_migration_report.json"

@dataclass(frozen=True)
class GateResult:
    gate_name: str
    passed: bool
    status: str
    message: str
    details: dict[str, Any]

FORBIDDEN_IMPORT_PREFIXES = (
    "bpy",
    "godot",
    "uvicorn",
    "fastapi",
    "socket",
    "requests",
    "httpx",
    "subprocess",
)

FORBIDDEN_NAME_FRAGMENTS = (
    "scene_server",
    "godot_adapter",
    "scene_loader",
    "runtime_client",
    "render",
    "spawn",
    "despawn",
    "mesh",
    "snapshot_write",
    "bridge_write",
)

FORBIDDEN_CALLS = (
    "open",
    "exec",
    "eval",
    "compile",
    "subprocess",
    "socket",
    "requests",
    "httpx",
)

def read_json_report(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}

def report_acceptance_is(report: dict[str, Any], expected: str = "ACCEPTED") -> bool:
    return report.get("acceptance") == expected

def existing_destination_review_passes(repo_root: Path) -> tuple[bool, dict[str, Any]]:
    scratch = repo_root / "scratch"

    signature = read_json_report(scratch / "ap_core_signature_probe_report.json")
    behavior = read_json_report(scratch / "ap_core_behavior_parity_report.json")
    activation = read_json_report(scratch / "ap_core_rule_activation_report.json")
    active = read_json_report(scratch / "active_gates_report.json")

    checks = {
        "signature_acceptance": report_acceptance_is(signature),
        "behavior_acceptance": report_acceptance_is(behavior),
        "behavior_authority_change_no": behavior.get("authority_change") == "no",
        "behavior_behavior_change_no": behavior.get("behavior_change") == "no",
        "behavior_runtime_output_change_no": behavior.get("runtime_output_change") == "no",
        "behavior_schema_change_no": behavior.get("schema_change") == "no",
        "behavior_signal_quality_signal": behavior.get("signal_quality") == "SIGNAL",
        "activation_acceptance": report_acceptance_is(activation),
        "active_gate_board_acceptance": report_acceptance_is(active),
        "active_gate_board_zero_failed": active.get("gate_count_failed") == 0,
    }

    return all(checks.values()), checks

def read_source(path: Path) -> str:
    return path.read_text(encoding="utf-8")

def parse_ast(source: str) -> ast.Module:
    return ast.parse(source)

def collect_imports(tree: ast.Module) -> list[str]:
    imports: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)

        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            imports.append(module)

    return sorted(set(imports))

def collect_public_symbols(tree: ast.Module) -> dict[str, list[str]]:
    classes: list[str] = []
    functions: list[str] = []

    for node in tree.body:
        if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
            classes.append(node.name)

        if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
            functions.append(node.name)

        if isinstance(node, ast.AsyncFunctionDef) and not node.name.startswith("_"):
            functions.append(node.name)

    return {
        "classes": sorted(classes),
        "functions": sorted(functions),
    }

def collect_called_names(tree: ast.Module) -> list[str]:
    calls: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func

            if isinstance(func, ast.Name):
                calls.append(func.id)

            if isinstance(func, ast.Attribute):
                calls.append(func.attr)

    return sorted(set(calls))

def collect_string_hits(source: str, fragments: tuple[str, ...]) -> list[str]:
    lowered = source.lower()
    return sorted(fragment for fragment in fragments if fragment.lower() in lowered)

def gate_source_exists() -> GateResult:
    passed = SOURCE_PATH.exists() and SOURCE_PATH.is_file()
    return GateResult(
        gate_name="GATE_SOURCE_EXISTS",
        passed=passed,
        status="TRUE" if passed else "FALSE",
        message="Historical ap_core.py exists." if passed else "Historical ap_core.py is missing.",
        details={"source_path": str(SOURCE_PATH)},
    )


def gate_import_boundary(imports: list[str]) -> GateResult:
    forbidden = [
        item for item in imports
        if item == "godot" or item.startswith(FORBIDDEN_IMPORT_PREFIXES)
    ]

    passed = len(forbidden) == 0
    return GateResult(
        gate_name="GATE_IMPORT_BOUNDARY",
        passed=passed,
        status="TRUE" if passed else "FALSE",
        message="Imports stay inside EngAInOS authority/core boundary." if passed else "Forbidden bridge/runtime imports found.",
        details={"imports": imports, "forbidden_imports": forbidden},
    )

def gate_no_bridge_or_render_language(source: str) -> GateResult:
    hits = collect_string_hits(source, FORBIDDEN_NAME_FRAGMENTS)
    passed = len(hits) == 0

    return GateResult(
        gate_name="GATE_NO_BRIDGE_OR_RENDER_LANGUAGE",
        passed=passed,
        status="TRUE" if passed else "FALSE",
        message="No obvious Godot bridge/render/spawn language found." if passed else "Bridge/render/spawn language found; file may be mixed-lane.",
        details={"hits": hits},
    )

def gate_no_forbidden_runtime_calls(calls: list[str]) -> GateResult:
    hits = [
        call for call in calls
        if call in FORBIDDEN_CALLS
    ]

    passed = len(hits) == 0
    return GateResult(
        gate_name="GATE_NO_FORBIDDEN_RUNTIME_CALLS",
        passed=passed,
        status="TRUE" if passed else "FALSE",
        message="No forbidden runtime side-effect calls found." if passed else "Runtime side-effect calls found.",
        details={"called_names": calls, "forbidden_calls": hits},
    )

def classify(results: list[GateResult]) -> str:
    if any(result.status == "FALSE" for result in results):
        return "BLOCKED_PENDING_TIER1_LANE_ASSIGNMENT"

    return "ENGAINOS_CORE_AUTHORITY"

def main() -> int:
    results: list[GateResult] = []

    source_exists = gate_source_exists()
    results.append(source_exists)

    if DEST_PATH.exists():
        reviewed, review_details = existing_destination_review_passes(REPO_ROOT)

        if reviewed:
            results.append(GateResult(
                gate_name="GATE_DESTINATION_REVIEWED_EXISTING_ACCEPTED",
                passed=True,
                status="TRUE",
                message="Existing destination accepted after companion proof review.",
                details=review_details,
            ))
        else:
            results.append(GateResult(
                gate_name="GATE_DESTINATION_NOT_OVERWRITTEN",
                passed=False,
                status="FALSE",
                message="Destination already exists; companion proof review missing or failed.",
                details=review_details,
            ))
    else:
        results.append(GateResult(
            gate_name="GATE_DESTINATION_NOT_OVERWRITTEN",
            passed=True,
            status="TRUE",
            message="Destination does not exist; migration may proceed without overwrite.",
            details={"destination_path": str(DEST_PATH)},
        ))

    source = ""
    imports: list[str] = []
    symbols: dict[str, list[str]] = {"classes": [], "functions": []}
    calls: list[str] = []

    if source_exists.passed:
        source = read_source(SOURCE_PATH)
        tree = parse_ast(source)
        imports = collect_imports(tree)
        symbols = collect_public_symbols(tree)
        calls = collect_called_names(tree)

        results.append(gate_import_boundary(imports))
        results.append(gate_no_bridge_or_render_language(source))
        results.append(gate_no_forbidden_runtime_calls(calls))

    all_passed = all(result.passed for result in results)
    if all_passed:
        if DEST_PATH.exists():
            classification = "ACCEPTED_REVIEWED_EXISTING_DESTINATION"
        else:
            classification = "ACCEPTED_READY_TO_MIGRATE"
        acceptance = "ACCEPTED"
    else:
        classification = "BLOCKED_PENDING_TIER1_LANE_ASSIGNMENT"
        acceptance = "BLOCKED_PENDING_TIER1_LANE_ASSIGNMENT"

    report = {
        "refactor_id": "AP_CORE_MIGRATION_001",
        "tier_authority": "ENGAINOS_TIER1",
        "lane": "engainos_core_authority",
        "stack": "engainos",
        "source_path": str(SOURCE_PATH),
        "destination_path": str(DEST_PATH),
        "classification": classification,
        "behavior_change": "no",
        "authority_change": "no",
        "schema_change": "unknown_until_behavior_tests",
        "runtime_output_change": "unknown_until_behavior_tests",
        "imports": imports,
        "public_symbols": symbols,
        "called_names": calls,
        "gates": [asdict(result) for result in results],
        "acceptance": acceptance,
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    for result in results:
        label = "PASS" if result.passed else "FAIL"
        print(f"[gate_ap_core_migration_authority][{result.gate_name}] {label}: {result.message}")

    print(f"[gate_ap_core_migration_authority][CLASSIFICATION] {classification}")
    print(f"[gate_ap_core_migration_authority][REPORT] {REPORT_PATH}")
    print(f"[gate_ap_core_migration_authority][ALL_GATES] {'true' if all_passed else 'false'}")

    return 0 if all_passed else 2

if __name__ == "__main__":
    raise SystemExit(main())
