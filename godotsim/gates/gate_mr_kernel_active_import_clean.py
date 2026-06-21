# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/godotsim/gates/gate_mr_kernel_active_import_clean.py

from __future__ import annotations

import ast
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path("/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

GATE_LIFECYCLE = "ACTIVE_VERIFICATION"
GATE_BOARD = "GODOTSIM_RUNTIME_KERNEL_BOARD"

ACTIVE_PATHS = (
    REPO_ROOT / "godotsim/godotsim_legacy",
    REPO_ROOT / "godotengain/engainos/core",
    REPO_ROOT / "engainos",
    REPO_ROOT / "godotsim",
    REPO_ROOT / "engain",
    REPO_ROOT / "ENGIONALITY",
    REPO_ROOT / "mrlore",
    REPO_ROOT / "mettaext",
)

NON_ACTIVE_CLIENT_TREE = REPO_ROOT / "godotengain/eng-a-in-os-game-client-(4.4)"
NON_ACTIVE_TEST_TREE = REPO_ROOT / "godotengain/engainos/tests"

GODOTSIM_ACTIVE_CALLERS = (
    REPO_ROOT / "godotsim/godotsim_legacy/combat3d_adapter.py",
    REPO_ROOT / "godotsim/godotsim_legacy/combat3d_integration.py",
)
OLD_ENGAINOS_CORE_ACTIVE_CALLERS = (
    REPO_ROOT / "godotengain/engainos/core/quest3d_integration.py",
    REPO_ROOT / "godotengain/engainos/core/replay.py",
    REPO_ROOT / "godotengain/engainos/core/zon_bridge.py",
)

OLD_COMBAT_SHIM = REPO_ROOT / "godotengain/engainos/core/combat3d_mr.py"
OLD_QUEST_SHIM = REPO_ROOT / "godotengain/engainos/core/quest3d_mr.py"
COMBAT_BACKUP = REPO_ROOT / "godotengain/engainos/core/combat3d_mr.py.pre_shim_backup"
QUEST_BACKUP = REPO_ROOT / "godotengain/engainos/core/quest3d_mr.py.pre_shim_backup"

OLD_KERNEL_MODULES = {
    "combat3d_mr",
    "quest3d_mr",
    ".combat3d_mr",
    ".quest3d_mr",
    "godotengain.engainos.core.combat3d_mr",
    "godotengain.engainos.core.quest3d_mr",
}
CANONICAL_KERNEL_MODULES = {
    "godotsim.kernels.combat3d_mr",
    "godotsim.kernels.quest3d_mr",
}


@dataclass(frozen=True)
class GateResult:
    gate_name: str
    passed: bool
    message: str

    def is_true(self) -> bool:
        return self.passed is True


@dataclass(frozen=True)
class ImportHit:
    path: Path
    line: int
    import_name: str
    symbols: str = ""

    def label(self) -> str:
        try:
            rel = self.path.relative_to(REPO_ROOT)
        except ValueError:
            rel = self.path
        suffix = f" import {self.symbols}" if self.symbols else ""
        return f"{rel}:{self.line} imports {self.import_name}{suffix}"


def _iter_python_files(paths: Iterable[Path]) -> list[Path]:
    files: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        if not path.exists():
            continue
        candidates = [path] if path.is_file() else sorted(path.rglob("*.py"))
        for candidate in candidates:
            resolved = candidate.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            files.append(candidate)
    return files


def _import_from_name(node: ast.ImportFrom) -> str:
    prefix = "." * int(node.level or 0)
    module = node.module or ""
    return f"{prefix}{module}"


def _find_imports(paths: Iterable[Path], module_names: set[str]) -> list[ImportHit]:
    hits: list[ImportHit] = []
    for path in _iter_python_files(paths):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in module_names:
                        hits.append(ImportHit(path, node.lineno, alias.name))
            elif isinstance(node, ast.ImportFrom):
                import_name = _import_from_name(node)
                if import_name in module_names:
                    symbols = ",".join(alias.name for alias in node.names)
                    hits.append(ImportHit(path, node.lineno, import_name, symbols))
    return hits


def _labels(hits: list[ImportHit], limit: int = 12) -> str:
    labels = [hit.label() for hit in hits[:limit]]
    if len(hits) > limit:
        labels.append(f"... {len(hits) - limit} more")
    return "; ".join(labels)


def gate_current_godotsim_active_imports_canonical() -> GateResult:
    old_hits = _find_imports(GODOTSIM_ACTIVE_CALLERS, OLD_KERNEL_MODULES)
    canonical_hits = _find_imports(GODOTSIM_ACTIVE_CALLERS, {"godotsim.kernels.combat3d_mr"})
    if old_hits:
        return GateResult(
            "GATE_CURRENT_GODOTSIM_ACTIVE_IMPORTS_CANONICAL",
            False,
            "GodotSim active callers still use old MR imports: " + _labels(old_hits),
        )
    if len({hit.path.resolve() for hit in canonical_hits}) != len(GODOTSIM_ACTIVE_CALLERS):
        return GateResult(
            "GATE_CURRENT_GODOTSIM_ACTIVE_IMPORTS_CANONICAL",
            False,
            "Not every GodotSim active caller imports canonical godotsim.kernels.combat3d_mr.",
        )
    return GateResult(
        "GATE_CURRENT_GODOTSIM_ACTIVE_IMPORTS_CANONICAL",
        True,
        "GodotSim active callers import canonical godotsim.kernels.combat3d_mr and no flat old combat3d_mr imports remain.",
    )


def gate_old_engainos_core_active_imports_canonical() -> GateResult:
    old_hits = _find_imports(OLD_ENGAINOS_CORE_ACTIVE_CALLERS, OLD_KERNEL_MODULES)
    canonical_hits = _find_imports(OLD_ENGAINOS_CORE_ACTIVE_CALLERS, CANONICAL_KERNEL_MODULES)
    if old_hits:
        return GateResult(
            "GATE_OLD_ENGAINOS_CORE_ACTIVE_IMPORTS_CANONICAL",
            False,
            "EngAInOS core active callers still use old MR imports: " + _labels(old_hits),
        )
    if len({hit.path.resolve() for hit in canonical_hits}) != len(OLD_ENGAINOS_CORE_ACTIVE_CALLERS):
        return GateResult(
            "GATE_OLD_ENGAINOS_CORE_ACTIVE_IMPORTS_CANONICAL",
            False,
            "Not every EngAInOS core active caller imports canonical godotsim.kernels MR modules.",
        )
    return GateResult(
        "GATE_OLD_ENGAINOS_CORE_ACTIVE_IMPORTS_CANONICAL",
        True,
        "EngAInOS core active callers import canonical godotsim.kernels MR modules and no old relative MR imports remain.",
    )


def gate_duplicate_client_tree_old_imports_known() -> GateResult:
    hits = _find_imports((NON_ACTIVE_CLIENT_TREE,), OLD_KERNEL_MODULES)
    if not hits:
        return GateResult(
            "GATE_DUPLICATE_CLIENT_TREE_OLD_IMPORTS_KNOWN",
            False,
            "Duplicate client tree old MR imports were expected as known non-runtime leftovers, but none were found.",
        )
    return GateResult(
        "GATE_DUPLICATE_CLIENT_TREE_OLD_IMPORTS_KNOWN",
        True,
        "Duplicate client tree old MR imports are known non-runtime leftovers: " + _labels(hits),
    )


def gate_test_old_imports_known() -> GateResult:
    hits = _find_imports((NON_ACTIVE_TEST_TREE,), OLD_KERNEL_MODULES)
    if not hits:
        return GateResult(
            "GATE_TEST_OLD_IMPORTS_KNOWN",
            False,
            "Test old MR imports were expected as known non-runtime leftovers, but none were found.",
        )
    return GateResult(
        "GATE_TEST_OLD_IMPORTS_KNOWN",
        True,
        "Test old MR imports are known non-runtime leftovers: " + _labels(hits),
    )


def gate_non_active_imports_do_not_block_runtime() -> GateResult:
    active_old_hits = _find_imports(ACTIVE_PATHS, OLD_KERNEL_MODULES)
    client_hits = _find_imports((NON_ACTIVE_CLIENT_TREE,), OLD_KERNEL_MODULES)
    test_hits = _find_imports((NON_ACTIVE_TEST_TREE,), OLD_KERNEL_MODULES)
    if active_old_hits:
        return GateResult(
            "GATE_NON_ACTIVE_IMPORTS_DO_NOT_BLOCK_RUNTIME",
            False,
            "Runtime-blocking old MR imports remain in active paths: " + _labels(active_old_hits),
        )
    if not client_hits or not test_hits:
        return GateResult(
            "GATE_NON_ACTIVE_IMPORTS_DO_NOT_BLOCK_RUNTIME",
            False,
            "Non-active leftover proof incomplete: duplicate client hits="
            f"{len(client_hits)}, test hits={len(test_hits)}.",
        )
    return GateResult(
        "GATE_NON_ACTIVE_IMPORTS_DO_NOT_BLOCK_RUNTIME",
        True,
        "Old MR imports are absent from active runtime paths; remaining old imports are confined to duplicate client/tests non-active paths.",
    )


def gate_shims_still_present() -> GateResult:
    missing = [path.relative_to(REPO_ROOT).as_posix() for path in (OLD_COMBAT_SHIM, OLD_QUEST_SHIM) if not path.is_file()]
    if missing:
        return GateResult("GATE_SHIMS_STILL_PRESENT", False, f"Missing old path shims: {missing}")
    return GateResult("GATE_SHIMS_STILL_PRESENT", True, "Old combat and quest shim files are still present; no shim deletion occurred.")


def gate_backups_still_present() -> GateResult:
    missing = [path.relative_to(REPO_ROOT).as_posix() for path in (COMBAT_BACKUP, QUEST_BACKUP) if not path.is_file()]
    if missing:
        return GateResult("GATE_BACKUPS_STILL_PRESENT", False, f"Missing pre-shim backups: {missing}")
    return GateResult("GATE_BACKUPS_STILL_PRESENT", True, "Pre-shim backup files are still present; no backup deletion occurred.")


def _classification(results: list[GateResult]) -> str:
    if all(result.is_true() for result in results):
        return "ACTIVE_IMPORTS_CLEAN_SHIMS_RETAINED"
    return "ACTIVE_IMPORTS_NOT_CLEAN"


def main() -> int:
    results = [
        gate_current_godotsim_active_imports_canonical(),
        gate_old_engainos_core_active_imports_canonical(),
        gate_duplicate_client_tree_old_imports_known(),
        gate_test_old_imports_known(),
        gate_non_active_imports_do_not_block_runtime(),
        gate_shims_still_present(),
        gate_backups_still_present(),
    ]

    for result in results:
        status = "PASS" if result.is_true() else "FAIL"
        value = "TRUE" if result.is_true() else "FALSE"
        print(f"[gate_mr_kernel_active_import_clean][{result.gate_name}] {status}: {result.gate_name} = {value}; {result.message}")

    classification = _classification(results)
    all_gates = all(result.is_true() for result in results)
    print(f"[gate_mr_kernel_active_import_clean][CLASSIFICATION] {classification}")
    print(f"[gate_mr_kernel_active_import_clean][ALL_GATES] {'true' if all_gates else 'false'}")

    return 0 if all_gates and classification == "ACTIVE_IMPORTS_CLEAN_SHIMS_RETAINED" else 1


if __name__ == "__main__":
    sys.exit(main())
