# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/godotsim/gates/gate_mr_kernel_shim_plan.py

from __future__ import annotations

import ast
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path("/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

GATE_LIFECYCLE = "PLAN_VERIFICATION"
GATE_BOARD = "GODOTSIM_RUNTIME_KERNEL_BOARD"

CANONICAL_TARGET_LANE = REPO_ROOT / "godotsim/kernels"
MISPLACED_COMBAT_KERNEL = REPO_ROOT / "godotengain/engainos/core/combat3d_mr.py"
MISPLACED_QUEST_KERNEL = REPO_ROOT / "godotengain/engainos/core/quest3d_mr.py"
LEGACY_COMBAT_KERNEL = REPO_ROOT / "godotsim/godotsim_legacy/combat3d_mr.py"

PLAN_READ_FILES = (
    REPO_ROOT / "godotsim/gates/gate_mr_kernel_placement_classification.py",
    REPO_ROOT / "godotsim/gates/gate_mr_kernel_relocation_readiness.py",
    REPO_ROOT / "godotengain/engainos/core/quest3d_integration.py",
    REPO_ROOT / "godotengain/engainos/core/replay.py",
    REPO_ROOT / "godotengain/engainos/core/zon_bridge.py",
    REPO_ROOT / "godotsim/godotsim_legacy/combat3d_adapter.py",
    REPO_ROOT / "godotsim/godotsim_legacy/combat3d_integration.py",
)

OLD_ENGAINOS_CORE_IMPORT_SITES = (
    REPO_ROOT / "godotengain/engainos/core/quest3d_integration.py",
    REPO_ROOT / "godotengain/engainos/core/replay.py",
    REPO_ROOT / "godotengain/engainos/core/zon_bridge.py",
)
GODOTSIM_LEGACY_IMPORT_SITES = (
    REPO_ROOT / "godotsim/godotsim_legacy/combat3d_adapter.py",
    REPO_ROOT / "godotsim/godotsim_legacy/combat3d_integration.py",
)

COMBAT_IMPORT_NAMES = {"combat3d_mr", ".combat3d_mr"}
QUEST_IMPORT_NAMES = {"quest3d_mr", ".quest3d_mr"}
KERNEL_IMPORT_NAMES = COMBAT_IMPORT_NAMES | QUEST_IMPORT_NAMES

EXPECTED_PUBLIC_IMPORTS = {
    "combat3d_mr": {"CombatSnapshot", "CombatEntity", "DamageEvent", "step_combat"},
    "quest3d_mr": {"step_quest3d", "QuestConfig"},
}


@dataclass(frozen=True)
class ImportHit:
    path: Path
    line: int
    import_name: str
    symbols: tuple[str, ...]

    def label(self) -> str:
        try:
            rel = self.path.relative_to(REPO_ROOT)
        except ValueError:
            rel = self.path
        suffix = " import " + ",".join(self.symbols) if self.symbols else ""
        return f"{rel}:{self.line} imports {self.import_name}{suffix}"


@dataclass(frozen=True)
class PlanGateResult:
    gate_name: str
    value: bool
    expected: bool
    message: str

    def matches_expected(self) -> bool:
        return self.value is self.expected

    def value_text(self) -> str:
        return "TRUE" if self.value else "FALSE"



def _import_from_name(node: ast.ImportFrom) -> str:
    return f"{'.' * int(node.level or 0)}{node.module or ''}"



def _find_kernel_imports(paths: Iterable[Path], names: set[str]) -> list[ImportHit]:
    hits: list[ImportHit] = []
    for path in paths:
        if not path.exists() or not path.is_file():
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in names:
                        hits.append(ImportHit(path, node.lineno, alias.name, ()))
            elif isinstance(node, ast.ImportFrom):
                import_name = _import_from_name(node)
                if import_name in names:
                    hits.append(
                        ImportHit(
                            path,
                            node.lineno,
                            import_name,
                            tuple(alias.name for alias in node.names if alias.name != "*"),
                        )
                    )
    return hits



def _public_symbols(path: Path) -> set[str]:
    if not path.exists() or not path.is_file():
        return set()
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    symbols: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_"):
            symbols.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and not target.id.startswith("_"):
                    symbols.add(target.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and not node.target.id.startswith("_"):
            symbols.add(node.target.id)
    return symbols



def _imported_symbols_by_kernel() -> dict[str, set[str]]:
    """Symbols that old misplaced EngAInOS core shims must preserve.

    GodotSim legacy plain imports are inspected by this gate, but they are not old
    EngAInOS package-relative shim obligations. They prove why new target imports
    must be checked separately before touching runtime imports.
    """
    imported = {"combat3d_mr": set(), "quest3d_mr": set()}
    for hit in _find_kernel_imports(OLD_ENGAINOS_CORE_IMPORT_SITES, KERNEL_IMPORT_NAMES):
        kernel = hit.import_name.lstrip(".")
        if hit.symbols:
            imported.setdefault(kernel, set()).update(hit.symbols)
    return imported



def _missing_public_symbols() -> dict[str, list[str]]:
    combat_symbols = _public_symbols(MISPLACED_COMBAT_KERNEL) | _public_symbols(LEGACY_COMBAT_KERNEL)
    quest_symbols = _public_symbols(MISPLACED_QUEST_KERNEL)
    available = {
        "combat3d_mr": combat_symbols,
        "quest3d_mr": quest_symbols,
    }
    imported = _imported_symbols_by_kernel()
    required = {
        kernel: EXPECTED_PUBLIC_IMPORTS[kernel] | imported.get(kernel, set())
        for kernel in EXPECTED_PUBLIC_IMPORTS
    }
    return {
        kernel: sorted(symbol for symbol in symbols if symbol not in available.get(kernel, set()))
        for kernel, symbols in required.items()
        if any(symbol not in available.get(kernel, set()) for symbol in symbols)
    }



def gate_target_kernel_lane_declared() -> PlanGateResult:
    value = CANONICAL_TARGET_LANE.relative_to(REPO_ROOT).as_posix() == "godotsim/kernels"
    return PlanGateResult(
        "GATE_TARGET_KERNEL_LANE_DECLARED",
        value,
        True,
        "Canonical MR kernel lane is declared as godotsim/kernels/; not legacy, client, quarantine, or EngAInOS core.",
    )



def gate_copy_before_move_required() -> PlanGateResult:
    old_imports = _find_kernel_imports(OLD_ENGAINOS_CORE_IMPORT_SITES, KERNEL_IMPORT_NAMES)
    source_files_exist = MISPLACED_COMBAT_KERNEL.is_file() and MISPLACED_QUEST_KERNEL.is_file()
    value = source_files_exist and bool(old_imports)
    return PlanGateResult(
        "GATE_COPY_BEFORE_MOVE_REQUIRED",
        value,
        True,
        "Copy-first is required because source kernels exist and old active imports still depend on old paths.",
    )



def gate_compatibility_shims_required() -> PlanGateResult:
    old_imports = _find_kernel_imports(OLD_ENGAINOS_CORE_IMPORT_SITES, KERNEL_IMPORT_NAMES)
    value = bool(old_imports)
    return PlanGateResult(
        "GATE_COMPATIBILITY_SHIMS_REQUIRED",
        value,
        True,
        "Compatibility shims are required while active EngAInOS core imports still target .combat3d_mr/.quest3d_mr: "
        + "; ".join(hit.label() for hit in old_imports),
    )



def gate_public_symbols_must_be_preserved() -> PlanGateResult:
    missing = _missing_public_symbols()
    value = not missing
    imported = _imported_symbols_by_kernel()
    return PlanGateResult(
        "GATE_PUBLIC_SYMBOLS_MUST_BE_PRESERVED",
        value,
        True,
        "Shims must re-export imported public symbols. Required symbols observed: "
        + "; ".join(f"{kernel}={sorted(symbols)}" for kernel, symbols in imported.items())
        + (f"; missing={missing}" if missing else "; all required symbols are present in current kernel sources."),
    )



def gate_delete_old_files_now() -> PlanGateResult:
    old_imports = _find_kernel_imports(OLD_ENGAINOS_CORE_IMPORT_SITES, KERNEL_IMPORT_NAMES)
    target_imports = _find_kernel_imports(OLD_ENGAINOS_CORE_IMPORT_SITES + GODOTSIM_LEGACY_IMPORT_SITES, {"godotsim.kernels.combat3d_mr", "godotsim.kernels.quest3d_mr"})
    value = bool(target_imports) and not old_imports
    return PlanGateResult(
        "GATE_DELETE_OLD_FILES_NOW",
        value,
        False,
        "Old files must not be deleted now; old active imports remain and target godotsim.kernels imports are not fully proven.",
    )



def gate_ready_to_create_shims() -> PlanGateResult:
    old_imports = _find_kernel_imports(OLD_ENGAINOS_CORE_IMPORT_SITES, KERNEL_IMPORT_NAMES)
    missing = _missing_public_symbols()
    read_files_available = all(path.is_file() for path in PLAN_READ_FILES)
    value = (
        CANONICAL_TARGET_LANE.relative_to(REPO_ROOT).as_posix() == "godotsim/kernels"
        and MISPLACED_COMBAT_KERNEL.is_file()
        and MISPLACED_QUEST_KERNEL.is_file()
        and bool(old_imports)
        and not missing
        and read_files_available
    )
    return PlanGateResult(
        "GATE_READY_TO_CREATE_SHIMS",
        value,
        True,
        "Shim creation is the next safe step after copy-first target creation; runtime imports and kernel behavior must remain unchanged in this gate.",
    )



def _classification(results: list[PlanGateResult]) -> str:
    by_name = {result.gate_name: result for result in results}
    if (
        by_name["GATE_TARGET_KERNEL_LANE_DECLARED"].value
        and by_name["GATE_COPY_BEFORE_MOVE_REQUIRED"].value
        and by_name["GATE_COMPATIBILITY_SHIMS_REQUIRED"].value
        and by_name["GATE_PUBLIC_SYMBOLS_MUST_BE_PRESERVED"].value
        and not by_name["GATE_DELETE_OLD_FILES_NOW"].value
        and by_name["GATE_READY_TO_CREATE_SHIMS"].value
    ):
        return "SHIM_PLAN_READY_COPY_FIRST"
    return "SHIM_PLAN_BLOCKED"



def main() -> int:
    results = [
        gate_target_kernel_lane_declared(),
        gate_copy_before_move_required(),
        gate_compatibility_shims_required(),
        gate_public_symbols_must_be_preserved(),
        gate_delete_old_files_now(),
        gate_ready_to_create_shims(),
    ]
    all_gates = all(result.matches_expected() for result in results)
    classification = _classification(results)

    for result in results:
        status = "PASS" if result.matches_expected() else "FAIL"
        print(f"[gate_mr_kernel_shim_plan][{result.gate_name}] {status}: {result.gate_name} = {result.value_text()}; {result.message}")

    print(f"[gate_mr_kernel_shim_plan][CLASSIFICATION] {classification}")
    print(f"[gate_mr_kernel_shim_plan][ALL_GATES] {'true' if all_gates else 'false'}")

    return 0 if all_gates and classification == "SHIM_PLAN_READY_COPY_FIRST" else 1


if __name__ == "__main__":
    sys.exit(main())
