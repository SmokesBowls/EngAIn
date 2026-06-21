# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/godotsim/gates/gate_mr_kernel_placement_classification.py

from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path("/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from engain_control.gate_result import GateResult

GATE_LIFECYCLE = "ACTIVE_VERIFICATION"
GATE_BOARD = "GODOTSIM_RUNTIME_KERNEL_BOARD"

REPO_ROOT = Path("/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn")
SOURCE_COMBAT = REPO_ROOT / "godotengain/engainos/core/combat3d_mr.py"
SOURCE_QUEST = REPO_ROOT / "godotengain/engainos/core/quest3d_mr.py"

FORBIDDEN_IMPORTS = {"fastapi", "uvicorn", "socket", "subprocess", "http.server", "requests", "httpx"}
FORBIDDEN_CALLS = {"open", "exec", "eval", "compile", "subprocess", "socket", "requests", "httpx"}


def gate_files_exist(packet: dict[str, Any]) -> GateResult:
    combat_ok = SOURCE_COMBAT.exists() and SOURCE_COMBAT.is_file()
    quest_ok = SOURCE_QUEST.exists() and SOURCE_QUEST.is_file()

    if not combat_ok or not quest_ok:
        missing = []
        if not combat_ok:
            missing.append(str(SOURCE_COMBAT))
        if not quest_ok:
            missing.append(str(SOURCE_QUEST))
        return GateResult(
            "gate_files_exist",
            "FALSE",
            f"Misplaced MR kernel files not found at expected sources: {missing}",
        )

    return GateResult(
        "gate_files_exist",
        "TRUE",
        "Both misplaced MR kernel files exist under godotengain/engainos/core/",
    )


def gate_pure_logic_checks(packet: dict[str, Any]) -> GateResult:
    violations = []
    
    for path in (SOURCE_COMBAT, SOURCE_QUEST):
        if not path.exists():
            continue
            
        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except Exception as e:
            violations.append(f"{path.name} failed parsing: {e}")
            continue

        # 1. Check imports
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)

        for imp in imports:
            for forbidden in FORBIDDEN_IMPORTS:
                if imp == forbidden or imp.startswith(forbidden + "."):
                    violations.append(f"{path.name} imports forbidden module: {imp}")

        # 2. Check forbidden calls
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                func_name = None
                if isinstance(func, ast.Name):
                    func_name = func.id
                elif isinstance(func, ast.Attribute):
                    func_name = func.attr
                    
                if func_name in FORBIDDEN_CALLS:
                    violations.append(f"{path.name} has forbidden runtime/effect call: {func_name}")

        # 3. Check that they don't claim EngAInOS authority metadata (like GATE_LIFECYCLE or GATE_BOARD)
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        if target.id in ("GATE_LIFECYCLE", "GATE_BOARD"):
                            violations.append(f"{path.name} claims authority metadata: {target.id}")

    if violations:
        return GateResult(
            "gate_pure_logic_checks",
            "FALSE",
            f"MR kernels failed pure logic validation: {violations}",
        )

    return GateResult(
        "gate_pure_logic_checks",
        "TRUE",
        "MR kernels pass all pure logic, import boundary, and non-authority checks.",
    )


def main() -> int:
    dummy_packet = {}
    r1 = gate_files_exist(dummy_packet)
    r2 = gate_pure_logic_checks(dummy_packet)
    
    results = [r1, r2]
    all_passed = all(r.is_true() for r in results)
    
    for r in results:
        print(f"[gate_mr_kernel_placement_classification][{r.gate_name}] {'PASS' if r.is_true() else 'FAIL'}: {r.message}")
        
    classification = "GODOTSIM_RUNTIME_KERNEL_CANDIDATE" if all_passed else "MISPLACED_OR_IMPURE_KERNEL"
    print(f"[gate_mr_kernel_placement_classification][CLASSIFICATION] {classification}")
    print(f"[gate_mr_kernel_placement_classification][ALL_GATES] {'true' if all_passed else 'false'}")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
