"""
AP Runtime Repair Readiness Gate

Purpose:
  Prove whether godotengain/engainos/core/ap_runtime.py is structurally
  repaired enough to be considered for a future engainos/relays/ap_runtime_relay.py
  gate, OR confirm it is still broken and must not be relayed to.

This gate does NOT migrate ap_runtime.py.
This gate does NOT create the relay.
This gate does NOT execute engine.execute_tick or any live AP call.
This gate only inspects source structure.

Authority:
  TIER_AUTHORITY: ENGAINOS_TIER1
  LANE: ap_runtime_repair_readiness
  STACK: godotengain/engainos/core (inspection only, no writes to this path)

One-Line Rule:
  This gate may prove ap_runtime.py is still broken.
  This gate may not declare it safe to call.
"""

from __future__ import annotations
GATE_LIFECYCLE = "ACTIVE_CONTRACT"
GATE_BOARD = "ENGAINOS_AP_MIGRATION_AND_CONTRACT_BOARD"


from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import ast
import json
import sys

REPO_ROOT = Path("/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn")
AP_RUNTIME_PATH = REPO_ROOT / "godotengain/engainos/core/ap_runtime.py"
REPORT_PATH = REPO_ROOT / "scratch/ap_runtime_repair_readiness_report.json"

# Message types the historical handle_message() dispatch table refers to.
# If new ones are added to the real file, update this list deliberately —
# do not infer it dynamically, since that could silently hide a future
# dispatch-without-handler bug instead of catching it.
EXPECTED_DISPATCHED_MESSAGE_TYPES = {
    "ap_evaluate_rule": "_handle_evaluate_rule",
    "ap_simulate_tick": "_handle_simulate_tick",
    "ap_execute_tick": "_handle_execute_tick",
    "ap_execution_history": "_handle_execution_history",
    "ap_list_rules": "_handle_list_rules",
    "ap_get_rule": "_handle_get_rule",
}

FENCE_FRAGMENTS = [
    "enable_timeline_write",
]

@dataclass(frozen=True)
class GateResult:
    gate_name: str
    status: str  # "TRUE" | "FALSE" | "BYPASS"
    message: str
    details: Dict[str, Any] = field(default_factory=dict)

# ============================================================================
# SOURCE LOADING
# ============================================================================

def load_source(path: Path) -> str:
    """
    Read source text from disk.
    Raises FileNotFoundError if the path does not exist.
    This function performs no execution, only a read.
    """
    return path.read_text(encoding="utf-8")

def parse_module(source: str) -> ast.Module:
    return ast.parse(source)

# ============================================================================
# STRUCTURAL HELPERS
# ============================================================================

def find_class(tree: ast.Module, class_name: str) -> Optional[ast.ClassDef]:
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return node
    return None

def find_method(class_node: ast.ClassDef, method_name: str) -> Optional[ast.FunctionDef]:
    for node in class_node.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == method_name:
            return node
    return None

def find_all_methods(class_node: ast.ClassDef) -> Dict[str, ast.FunctionDef]:
    methods: Dict[str, ast.FunctionDef] = {}
    for node in class_node.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            methods[node.name] = node
    return methods

def statements_after_return(func_node: ast.FunctionDef) -> List[ast.stmt]:
    """
    Walk a function body's top-level statements and return any statements
    that appear after an unconditional `return` at the same block level.

    This intentionally only checks the top-level statement list of the
    function body (not nested if/for/while blocks), because that is
    exactly the shape of the bug we are looking for: a `return` followed
    by a dangling dict literal / dead block at the same indentation.
    """
    dead: List[ast.stmt] = []
    seen_return = False

    for stmt in func_node.body:
        if seen_return:
            dead.append(stmt)
            continue
        if isinstance(stmt, ast.Return):
            seen_return = True

    return dead

def source_segment(source: str, node: ast.AST) -> str:
    segment = ast.get_source_segment(source, node)
    return segment if segment is not None else ""

# ============================================================================
# GATES
# ============================================================================

def gate_file_exists() -> GateResult:
    if not AP_RUNTIME_PATH.exists():
        return GateResult(
            "GATE_FILE_EXISTS",
            "FALSE",
            f"ap_runtime.py not found at expected historical path: {AP_RUNTIME_PATH}",
        )
    return GateResult(
        "GATE_FILE_EXISTS",
        "TRUE",
        "ap_runtime.py found at historical path",
        {"path": str(AP_RUNTIME_PATH)},
    )

def gate_no_dead_code_blocks(source: str, tree: ast.Module) -> GateResult:
    """
    TRUE only when no top-level statement in any method body is dead
    (unreachable because it follows an unconditional return at the
    same block level).

    This specifically catches the known historical bug: an orphaned
    `{'type': 'ap_simulate_result', 'result': result}` dict literal
    sitting directly below an early `return` in _handle_evaluate_rule,
    with no enclosing function header of its own.
    """
    class_node = find_class(tree, "APRuntimeIntegration")
    if class_node is None:
        return GateResult(
            "GATE_NO_DEAD_CODE_BLOCKS",
            "FALSE",
            "APRuntimeIntegration class not found; cannot inspect method bodies",
        )

    violations: List[Dict[str, Any]] = []

    for method_name, method_node in find_all_methods(class_node).items():
        dead_stmts = statements_after_return(method_node)
        for stmt in dead_stmts:
            violations.append(
                {
                    "method": method_name,
                    "lineno": getattr(stmt, "lineno", None),
                    "snippet": source_segment(source, stmt)[:200],
                }
            )

    if violations:
        return GateResult(
            "GATE_NO_DEAD_CODE_BLOCKS",
            "FALSE",
            f"Found {len(violations)} dead statement(s) after unconditional return",
            {"violations": violations},
        )

    return GateResult(
        "GATE_NO_DEAD_CODE_BLOCKS",
        "TRUE",
        "No dead code found after unconditional returns in inspected methods",
    )

def gate_all_dispatched_handlers_defined(tree: ast.Module) -> GateResult:
    """
    TRUE only when every message type referenced in handle_message's
    dispatch logic resolves to a method that actually exists on the class.

    This catches the known historical bug: handle_message dispatches
    'ap_simulate_tick' to self._handle_simulate_tick, but that method
    is never defined anywhere in the class body.
    """
    class_node = find_class(tree, "APRuntimeIntegration")
    if class_node is None:
        return GateResult(
            "GATE_ALL_DISPATCHED_HANDLERS_DEFINED",
            "FALSE",
            "APRuntimeIntegration class not found; cannot verify dispatch table",
        )

    defined_methods = set(find_all_methods(class_node).keys())

    missing: List[Dict[str, str]] = []
    for msg_type, handler_name in EXPECTED_DISPATCHED_MESSAGE_TYPES.items():
        if handler_name not in defined_methods:
            missing.append({"message_type": msg_type, "expected_handler": handler_name})

    if missing:
        return GateResult(
            "GATE_ALL_DISPATCHED_HANDLERS_DEFINED",
            "FALSE",
            f"{len(missing)} dispatched message type(s) have no defined handler method",
            {"missing": missing, "defined_methods": sorted(defined_methods)},
        )

    return GateResult(
        "GATE_ALL_DISPATCHED_HANDLERS_DEFINED",
        "TRUE",
        "Every expected dispatched message type resolves to a defined handler method",
        {"defined_methods": sorted(defined_methods)},
    )

def gate_execute_tick_respects_timeline_fence(source: str, tree: ast.Module) -> GateResult:
    """
    TRUE only when _handle_execute_tick's call into engine.execute_tick
    is conditioned on (or explicitly threads through) the same
    enable_timeline_write fence already proven in ap_zw_engine.py.

    This is a source-pattern check, not a behavioral one: it looks for
    the fence fragment anywhere in the method body. A FALSE result here
    means the method calls execute_tick unconditionally, which would
    silently bypass the fence that ap_zw_engine.py already proved exists
    and is meaningful.
    """
    class_node = find_class(tree, "APRuntimeIntegration")
    if class_node is None:
        return GateResult(
            "GATE_EXECUTE_TICK_RESPECTS_TIMELINE_FENCE",
            "FALSE",
            "APRuntimeIntegration class not found; cannot inspect _handle_execute_tick",
        )

    method_node = find_method(class_node, "_handle_execute_tick")
    if method_node is None:
        return GateResult(
            "GATE_EXECUTE_TICK_RESPECTS_TIMELINE_FENCE",
            "FALSE",
            "_handle_execute_tick method not found",
        )

    method_source = source_segment(source, method_node)
    calls_execute_tick = "execute_tick(" in method_source
    fence_present = any(fragment in method_source for fragment in FENCE_FRAGMENTS)

    if not calls_execute_tick:
        return GateResult(
            "GATE_EXECUTE_TICK_RESPECTS_TIMELINE_FENCE",
            "BYPASS",
            "_handle_execute_tick does not call engine.execute_tick; fence is not applicable",
            {"method_source": method_source[:500]},
        )

    if calls_execute_tick and not fence_present:
        return GateResult(
            "GATE_EXECUTE_TICK_RESPECTS_TIMELINE_FENCE",
            "FALSE",
            "_handle_execute_tick calls engine.execute_tick without referencing the "
            "enable_timeline_write fence; this would silently bypass the fence proven "
            "in ap_zw_engine.py",
            {"method_source": method_source[:1000]},
        )

    return GateResult(
        "GATE_EXECUTE_TICK_RESPECTS_TIMELINE_FENCE",
        "TRUE",
        "_handle_execute_tick references the enable_timeline_write fence before calling execute_tick",
        {"method_source": method_source[:1000]},
    )

def gate_rule_loading_path_is_validated(source: str, tree: ast.Module) -> GateResult:
    """
    TRUE only when scenes_dir / rule-loading paths are not silently
    resolved from an unanchored relative default.

    This is a narrow, conservative check: it flags the known historical
    pattern of `scenes_dir or "scenes"` (a bare relative string with no
    project-root anchoring) inside __init__. It does not attempt to
    fully validate the rest of the rule-loading pipeline; it only proves
    whether the specific known-risky default is still present.
    """
    class_node = find_class(tree, "APRuntimeIntegration")
    if class_node is None:
        return GateResult(
            "GATE_RULE_LOADING_PATH_IS_VALIDATED",
            "FALSE",
            "APRuntimeIntegration class not found; cannot inspect __init__",
        )

    init_node = find_method(class_node, "__init__")
    if init_node is None:
        return GateResult(
            "GATE_RULE_LOADING_PATH_IS_VALIDATED",
            "FALSE",
            "__init__ method not found",
        )

    init_source = source_segment(source, init_node)

    # Known-risky historical pattern: bare relative default with no anchoring.
    risky_pattern_present = 'or "scenes"' in init_source or "or 'scenes'" in init_source

    if risky_pattern_present:
        return GateResult(
            "GATE_RULE_LOADING_PATH_IS_VALIDATED",
            "FALSE",
            "scenes_dir defaults to an unanchored relative 'scenes' string with no "
            "project-root validation; rule files would be globbed from whatever the "
            "process current working directory happens to be",
            {"init_source": init_source[:500]},
        )

    return GateResult(
        "GATE_RULE_LOADING_PATH_IS_VALIDATED",
        "TRUE",
        "No unanchored relative scenes_dir default detected in __init__",
        {"init_source": init_source[:500]},
    )

# ============================================================================
# PRINT / REPORT
# ============================================================================

def print_gate_results(script_name: str, results: List[GateResult]) -> None:
    for result in results:
        print(f"[{script_name}][{result.gate_name}] {result.status}: {result.message}")

    any_false = any(r.status == "FALSE" for r in results)
    final = "false" if any_false else "true"
    print(f"[{script_name}][ALL_GATES] {final}")

def main() -> int:
    script_name = "gate_ap_runtime_repair_readiness"

    file_gate = gate_file_exists()

    if file_gate.status != "TRUE":
        print_gate_results(script_name, [file_gate])
        report = {
            "refactor_id": "AP_RUNTIME_REPAIR_READINESS_001",
            "tier_authority": "ENGAINOS_TIER1",
            "lane": "ap_runtime_repair_readiness",
            "ap_runtime_path": str(AP_RUNTIME_PATH),
            "gates": [asdict(file_gate)],
            "repair_ready": False,
            "relay_creation_allowed": False,
            "acceptance": "REJECTED",
        }
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
        return 2

    try:
        source = load_source(AP_RUNTIME_PATH)
        tree = parse_module(source)
    except SyntaxError as exc:
        syntax_gate = GateResult(
            "GATE_FILE_PARSES",
            "FALSE",
            f"ap_runtime.py could not be parsed as valid Python: {exc}",
        )
        print_gate_results(script_name, [file_gate, syntax_gate])
        report = {
            "refactor_id": "AP_RUNTIME_REPAIR_READINESS_001",
            "tier_authority": "ENGAINOS_TIER1",
            "lane": "ap_runtime_repair_readiness",
            "ap_runtime_path": str(AP_RUNTIME_PATH),
            "gates": [asdict(file_gate), asdict(syntax_gate)],
            "repair_ready": False,
            "relay_creation_allowed": False,
            "acceptance": "REJECTED",
        }
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
        return 2

    results = [
        file_gate,
        gate_no_dead_code_blocks(source, tree),
        gate_all_dispatched_handlers_defined(tree),
        gate_execute_tick_respects_timeline_fence(source, tree),
        gate_rule_loading_path_is_validated(source, tree),
    ]

    all_passed = all(r.status in ("TRUE", "BYPASS") for r in results)

    report = {
        "refactor_id": "AP_RUNTIME_REPAIR_READINESS_001",
        "tier_authority": "ENGAINOS_TIER1",
        "lane": "ap_runtime_repair_readiness",
        "ap_runtime_path": str(AP_RUNTIME_PATH),
        "gates": [asdict(r) for r in results],
        "repair_ready": all_passed,
        "relay_creation_allowed": False,
        "note": (
            "relay_creation_allowed is hardcoded False. This gate proves repair "
            "readiness only. A separate gate_ap_runtime_relay_readiness.py must be "
            "created and passed before engainos/relays/ap_runtime_relay.py may call "
            "into this file."
        ),
        "acceptance": "ACCEPTED_AS_REPAIR_READY" if all_passed else "REJECTED_NOT_REPAIR_READY",
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    print_gate_results(script_name, results)
    print(f"[{script_name}][REPAIR_READY] {'true' if all_passed else 'false'}")
    print(f"[{script_name}][RELAY_CREATION_ALLOWED] false")
    print(f"[{script_name}][REPORT] {REPORT_PATH}")

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
