# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/godotsim/gates/gate_mr_kernel_relocation_readiness.py

from __future__ import annotations

import ast
import importlib
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path("/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from engain_control.gate_result import GateResult

GATE_LIFECYCLE = "ACTIVE_VERIFICATION"
GATE_BOARD = "GODOTSIM_RUNTIME_KERNEL_BOARD"

GODOTSIM_LEGACY_COMBAT_KERNEL = REPO_ROOT / "godotsim/godotsim_legacy/combat3d_mr.py"
GODOTSIM_LEGACY_IMPORT_SITES = (
    REPO_ROOT / "godotsim/godotsim_legacy/combat3d_adapter.py",
    REPO_ROOT / "godotsim/godotsim_legacy/combat3d_integration.py",
)
OLD_ENGAINOS_CORE_IMPORT_SITES = (
    REPO_ROOT / "godotengain/engainos/core/quest3d_integration.py",
    REPO_ROOT / "godotengain/engainos/core/replay.py",
    REPO_ROOT / "godotengain/engainos/core/zon_bridge.py",
)

CANONICAL_COMBAT_MODULE = "godotsim.kernels.combat3d_mr"
CANONICAL_QUEST_MODULE = "godotsim.kernels.quest3d_mr"
OLD_COMBAT_MODULE = "godotengain.engainos.core.combat3d_mr"
OLD_QUEST_MODULE = "godotengain.engainos.core.quest3d_mr"

COMBAT_IMPORT_NAMES = {"combat3d_mr", ".combat3d_mr"}
CANONICAL_COMBAT_IMPORT_NAMES = {"godotsim.kernels.combat3d_mr"}
GODOTSIM_LEGACY_ACTIVE_COMBAT_IMPORT_NAMES = COMBAT_IMPORT_NAMES | CANONICAL_COMBAT_IMPORT_NAMES
QUEST_IMPORT_NAMES = {"quest3d_mr", ".quest3d_mr"}
KERNEL_IMPORT_NAMES = COMBAT_IMPORT_NAMES | QUEST_IMPORT_NAMES

COMBAT_SYMBOLS = (
    "CombatEntity",
    "DamageEvent",
    "CombatSnapshot",
    "CombatOutput",
    "step_combat",
)
QUEST_SYMBOLS = (
    "QuestConfig",
    "step_quest3d",
    "get_quest_summaries",
)

EXPECTED_GATE_STATES = {
    "GATE_GODOTSIM_LOCAL_COMBAT_KERNEL_EXISTS": "TRUE",
    "GATE_GODOTSIM_LOCAL_IMPORTS_FOUND": "TRUE",
    "GATE_OLD_ENGAINOS_CORE_IMPORTS_FOUND": "FALSE",
    "GATE_GODOTSIM_LEGACY_OLD_IMPORTS_FOUND": "FALSE",
    "GATE_RELOCATION_REQUIRES_SHIM": "FALSE",
    "GATE_COMPATIBILITY_SHIMS_ACTIVE": "TRUE",
    "GATE_RELOCATION_BRIDGED": "FALSE",
    "GATE_RELOCATION_READY": "TRUE",
}


@dataclass(frozen=True)
class ImportHit:
    path: Path
    line: int
    import_name: str
    symbol: str = ""

    def label(self) -> str:
        suffix = f" import {self.symbol}" if self.symbol else ""
        try:
            rel = self.path.relative_to(REPO_ROOT)
        except ValueError:
            rel = self.path
        return f"{rel}:{self.line} imports {self.import_name}{suffix}"



def _module(module_name: str) -> Any:
    return importlib.import_module(module_name)



def _import_from_name(node: ast.ImportFrom) -> str:
    prefix = "." * int(node.level or 0)
    module = node.module or ""
    return f"{prefix}{module}"



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
                        hits.append(ImportHit(path, node.lineno, alias.name))
            elif isinstance(node, ast.ImportFrom):
                import_name = _import_from_name(node)
                if import_name in names:
                    imported_symbols = ",".join(alias.name for alias in node.names)
                    hits.append(ImportHit(path, node.lineno, import_name, imported_symbols))

    return hits



def _compatibility_shims_active() -> tuple[bool, str]:
    try:
        canonical_combat = _module(CANONICAL_COMBAT_MODULE)
        canonical_quest = _module(CANONICAL_QUEST_MODULE)
        old_combat = _module(OLD_COMBAT_MODULE)
        old_quest = _module(OLD_QUEST_MODULE)
    except Exception as exc:
        return False, f"Failed importing canonical/old kernel modules: {exc!r}"

    failures = []
    for symbol in COMBAT_SYMBOLS:
        if getattr(old_combat, symbol, None) is not getattr(canonical_combat, symbol, None):
            failures.append(f"combat.{symbol}")
    for symbol in QUEST_SYMBOLS:
        if getattr(old_quest, symbol, None) is not getattr(canonical_quest, symbol, None):
            failures.append(f"quest.{symbol}")

    if failures:
        return False, "Old path shims do not re-export canonical objects for: " + ", ".join(failures)

    return True, "Old misplaced kernel paths are compatibility shims re-exporting canonical godotsim.kernels symbols by object identity."



def gate_godotsim_local_combat_kernel_exists(packet: dict[str, Any]) -> GateResult:
    if GODOTSIM_LEGACY_COMBAT_KERNEL.exists() and GODOTSIM_LEGACY_COMBAT_KERNEL.is_file():
        return GateResult(
            "GATE_GODOTSIM_LOCAL_COMBAT_KERNEL_EXISTS",
            "TRUE",
            f"Local GodotSim combat kernel exists at {GODOTSIM_LEGACY_COMBAT_KERNEL.relative_to(REPO_ROOT)}.",
        )

    return GateResult(
        "GATE_GODOTSIM_LOCAL_COMBAT_KERNEL_EXISTS",
        "FALSE",
        f"Local GodotSim combat kernel is missing at {GODOTSIM_LEGACY_COMBAT_KERNEL.relative_to(REPO_ROOT)}.",
    )



def gate_godotsim_local_imports_found(packet: dict[str, Any]) -> GateResult:
    hits = _find_kernel_imports(GODOTSIM_LEGACY_IMPORT_SITES, GODOTSIM_LEGACY_ACTIVE_COMBAT_IMPORT_NAMES)
    if hits:
        return GateResult(
            "GATE_GODOTSIM_LOCAL_IMPORTS_FOUND",
            "TRUE",
            "GodotSim legacy files already import local combat3d_mr: " + "; ".join(hit.label() for hit in hits),
        )

    return GateResult(
        "GATE_GODOTSIM_LOCAL_IMPORTS_FOUND",
        "FALSE",
        "No active GodotSim legacy imports of combat3d_mr were found in the approved proof paths.",
    )



def gate_old_engainos_core_imports_found(packet: dict[str, Any]) -> GateResult:
    hits = _find_kernel_imports(OLD_ENGAINOS_CORE_IMPORT_SITES, KERNEL_IMPORT_NAMES)
    if hits:
        return GateResult(
            "GATE_OLD_ENGAINOS_CORE_IMPORTS_FOUND",
            "TRUE",
            "EngAInOS core still imports MR kernels from the old package path: " + "; ".join(hit.label() for hit in hits),
        )

    return GateResult(
        "GATE_OLD_ENGAINOS_CORE_IMPORTS_FOUND",
        "FALSE",
        "No old EngAInOS core imports of combat3d_mr or quest3d_mr were found in the approved proof paths.",
    )



def gate_godotsim_legacy_old_imports_found(packet: dict[str, Any]) -> GateResult:
    hits = _find_kernel_imports(GODOTSIM_LEGACY_IMPORT_SITES, COMBAT_IMPORT_NAMES)
    if hits:
        return GateResult(
            "GATE_GODOTSIM_LEGACY_OLD_IMPORTS_FOUND",
            "TRUE",
            "Active GodotSim legacy callers still import flat old combat3d_mr: " + "; ".join(hit.label() for hit in hits),
        )

    return GateResult(
        "GATE_GODOTSIM_LEGACY_OLD_IMPORTS_FOUND",
        "FALSE",
        "No active GodotSim legacy flat imports of combat3d_mr were found in the approved proof paths.",
    )


def gate_relocation_requires_shim(packet: dict[str, Any]) -> GateResult:
    old_core_hits = _find_kernel_imports(OLD_ENGAINOS_CORE_IMPORT_SITES, KERNEL_IMPORT_NAMES)
    godotsim_legacy_old_hits = _find_kernel_imports(GODOTSIM_LEGACY_IMPORT_SITES, COMBAT_IMPORT_NAMES)
    if old_core_hits or godotsim_legacy_old_hits:
        return GateResult(
            "GATE_RELOCATION_REQUIRES_SHIM",
            "TRUE",
            "Old import sites still block deletion/review until callers migrate to godotsim.kernels.",
        )

    return GateResult(
        "GATE_RELOCATION_REQUIRES_SHIM",
        "FALSE",
        "No shim is required by the inspected active import sites.",
    )



def gate_compatibility_shims_active(packet: dict[str, Any]) -> GateResult:
    active, message = _compatibility_shims_active()
    return GateResult(
        "GATE_COMPATIBILITY_SHIMS_ACTIVE",
        "TRUE" if active else "FALSE",
        message,
    )



def gate_relocation_bridged(packet: dict[str, Any]) -> GateResult:
    old_core_hits = _find_kernel_imports(OLD_ENGAINOS_CORE_IMPORT_SITES, KERNEL_IMPORT_NAMES)
    shims_active, shim_message = _compatibility_shims_active()
    if old_core_hits and shims_active:
        return GateResult(
            "GATE_RELOCATION_BRIDGED",
            "TRUE",
            "Relocation is bridged: old import callers remain, but active compatibility shims re-export canonical godotsim.kernels symbols.",
        )

    blockers = []
    if not old_core_hits:
        blockers.append("old core imports were not found; bridge no longer applies")
    if not shims_active:
        blockers.append(shim_message)
    return GateResult(
        "GATE_RELOCATION_BRIDGED",
        "FALSE",
        "Relocation bridge is not proven: " + "; ".join(blockers),
    )



def gate_relocation_ready(packet: dict[str, Any]) -> GateResult:
    local_kernel_exists = GODOTSIM_LEGACY_COMBAT_KERNEL.exists() and GODOTSIM_LEGACY_COMBAT_KERNEL.is_file()
    local_imports_found = bool(_find_kernel_imports(GODOTSIM_LEGACY_IMPORT_SITES, GODOTSIM_LEGACY_ACTIVE_COMBAT_IMPORT_NAMES))
    old_core_imports_found = bool(_find_kernel_imports(OLD_ENGAINOS_CORE_IMPORT_SITES, KERNEL_IMPORT_NAMES))
    godotsim_legacy_old_imports_found = bool(_find_kernel_imports(GODOTSIM_LEGACY_IMPORT_SITES, COMBAT_IMPORT_NAMES))

    if local_kernel_exists and local_imports_found and not old_core_imports_found and not godotsim_legacy_old_imports_found:
        return GateResult(
            "GATE_RELOCATION_READY",
            "TRUE",
            "Relocation readiness passed: local GodotSim combat kernel/imports are present and old EngAInOS core imports are absent.",
        )

    blockers = []
    if not local_kernel_exists:
        blockers.append("missing godotsim/godotsim_legacy/combat3d_mr.py")
    if not local_imports_found:
        blockers.append("missing approved GodotSim local combat3d_mr imports")
    if old_core_imports_found:
        blockers.append("active old EngAInOS core imports have not migrated to godotsim.kernels yet")
    if godotsim_legacy_old_imports_found:
        blockers.append("active GodotSim legacy imports have not migrated from flat combat3d_mr to godotsim.kernels yet")

    return GateResult(
        "GATE_RELOCATION_READY",
        "FALSE",
        "Relocation is bridged but not ready for deletion/removal: " + "; ".join(blockers),
    )



def _classification(results: list[GateResult]) -> str:
    by_name = {result.gate_name: result for result in results}
    if by_name["GATE_RELOCATION_READY"].is_true():
        return "RELOCATION_READY"
    if by_name["GATE_GODOTSIM_LEGACY_OLD_IMPORTS_FOUND"].is_true():
        return "RELOCATION_BLOCKED_GODOTSIM_LEGACY_IMPORTS"
    if by_name["GATE_RELOCATION_BRIDGED"].is_true() and by_name["GATE_RELOCATION_REQUIRES_SHIM"].is_true():
        return "RELOCATION_BRIDGED_IMPORT_MIGRATION_REQUIRED"
    if by_name["GATE_RELOCATION_REQUIRES_SHIM"].is_true():
        return "RELOCATION_BLOCKED_IMPORT_SHIM_REQUIRED"
    return "RELOCATION_BLOCKED_READINESS_REQUIREMENTS_NOT_MET"



def _matches_expected(result: GateResult) -> bool:
    return result.passed == EXPECTED_GATE_STATES[result.gate_name]



def main() -> int:
    packet: dict[str, Any] = {}
    results = [
        gate_godotsim_local_combat_kernel_exists(packet),
        gate_godotsim_local_imports_found(packet),
        gate_old_engainos_core_imports_found(packet),
        gate_godotsim_legacy_old_imports_found(packet),
        gate_relocation_requires_shim(packet),
        gate_compatibility_shims_active(packet),
        gate_relocation_bridged(packet),
        gate_relocation_ready(packet),
    ]

    for result in results:
        status = "PASS" if _matches_expected(result) else "FAIL"
        print(f"[gate_mr_kernel_relocation_readiness][{result.gate_name}] {status}: {result.gate_name} = {result.passed}; {result.message}")

    classification = _classification(results)
    all_gates = all(_matches_expected(result) for result in results)
    print(f"[gate_mr_kernel_relocation_readiness][CLASSIFICATION] {classification}")
    print(f"[gate_mr_kernel_relocation_readiness][ALL_GATES] {'true' if all_gates else 'false'}")

    return 0 if all_gates and classification == "RELOCATION_READY" else 1


if __name__ == "__main__":
    sys.exit(main())
