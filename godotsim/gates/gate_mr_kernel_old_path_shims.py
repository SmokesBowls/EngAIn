# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/godotsim/gates/gate_mr_kernel_old_path_shims.py

from __future__ import annotations

import ast
import importlib
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path("/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

GATE_LIFECYCLE = "ACTIVE_VERIFICATION"
GATE_BOARD = "GODOTSIM_RUNTIME_KERNEL_BOARD"

CANONICAL_COMBAT_MODULE = "godotsim.kernels.combat3d_mr"
CANONICAL_QUEST_MODULE = "godotsim.kernels.quest3d_mr"
OLD_COMBAT_MODULE = "godotengain.engainos.core.combat3d_mr"
OLD_QUEST_MODULE = "godotengain.engainos.core.quest3d_mr"

CANONICAL_COMBAT_PATH = REPO_ROOT / "godotsim/kernels/combat3d_mr.py"
CANONICAL_QUEST_PATH = REPO_ROOT / "godotsim/kernels/quest3d_mr.py"
OLD_COMBAT_PATH = REPO_ROOT / "godotengain/engainos/core/combat3d_mr.py"
OLD_QUEST_PATH = REPO_ROOT / "godotengain/engainos/core/quest3d_mr.py"
COMBAT_BACKUP_PATH = REPO_ROOT / "godotengain/engainos/core/combat3d_mr.py.pre_shim_backup"
QUEST_BACKUP_PATH = REPO_ROOT / "godotengain/engainos/core/quest3d_mr.py.pre_shim_backup"
NEW_LANE_GATE = REPO_ROOT / "godotsim/gates/gate_mr_kernel_new_lane_imports.py"

COMBAT_SYMBOLS = [
    "CombatEntity",
    "DamageEvent",
    "CombatSnapshot",
    "CombatOutput",
    "step_combat",
]
QUEST_SYMBOLS = [
    "QuestConfig",
    "step_quest3d",
    "get_quest_summaries",
]

EXPECTED_COMBAT_ALL = COMBAT_SYMBOLS
EXPECTED_QUEST_ALL = QUEST_SYMBOLS


@dataclass(frozen=True)
class GateResult:
    gate_name: str
    passed: bool
    message: str

    def is_true(self) -> bool:
        return self.passed is True



def _module(name: str) -> Any:
    return importlib.import_module(name)



def _byte_equal(left: Path, right: Path) -> bool:
    return left.read_bytes() == right.read_bytes()



def _shim_shape_ok(path: Path, canonical_module: str, expected_all: list[str]) -> tuple[bool, str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except Exception as exc:
        return False, f"failed to parse shim: {exc!r}"

    body = list(tree.body)
    if not body or not isinstance(body[0], ast.Expr) or not isinstance(body[0].value, ast.Constant) or not isinstance(body[0].value.value, str):
        return False, "missing module docstring"

    statements = body[1:]
    if len(statements) != 2:
        return False, f"expected exactly import and __all__ after docstring, found {len(statements)} statements"

    import_stmt, all_stmt = statements
    if not isinstance(import_stmt, ast.ImportFrom) or import_stmt.module != canonical_module or import_stmt.level != 0:
        return False, f"shim does not import directly from {canonical_module}"

    imported_names = [alias.name for alias in import_stmt.names]
    if imported_names != expected_all:
        return False, f"imported names differ: expected {expected_all}, got {imported_names}"

    if not isinstance(all_stmt, ast.Assign) or len(all_stmt.targets) != 1:
        return False, "__all__ assignment missing or malformed"
    target = all_stmt.targets[0]
    if not isinstance(target, ast.Name) or target.id != "__all__":
        return False, "final assignment is not __all__"
    if not isinstance(all_stmt.value, ast.List):
        return False, "__all__ is not a list literal"
    all_names = []
    for elt in all_stmt.value.elts:
        if not isinstance(elt, ast.Constant) or not isinstance(elt.value, str):
            return False, "__all__ contains non-string literal"
        all_names.append(elt.value)
    if all_names != expected_all:
        return False, f"__all__ differs: expected {expected_all}, got {all_names}"

    return True, "shim contains only docstring, canonical import, and exact __all__ list"



def gate_precondition_new_lane_proven() -> GateResult:
    missing = [
        path.relative_to(REPO_ROOT).as_posix()
        for path in (NEW_LANE_GATE, CANONICAL_COMBAT_PATH, CANONICAL_QUEST_PATH)
        if not path.is_file()
    ]
    if missing:
        return GateResult("GATE_PRECONDITION_NEW_LANE_PROVEN", False, f"New lane precondition files missing: {missing}")
    try:
        combat = _module(CANONICAL_COMBAT_MODULE)
        quest = _module(CANONICAL_QUEST_MODULE)
    except Exception as exc:
        return GateResult("GATE_PRECONDITION_NEW_LANE_PROVEN", False, f"Canonical kernel lane import failed: {exc!r}")
    if Path(combat.__file__).resolve() != CANONICAL_COMBAT_PATH.resolve():
        return GateResult("GATE_PRECONDITION_NEW_LANE_PROVEN", False, f"Combat canonical module resolved unexpectedly: {combat.__file__}")
    if Path(quest.__file__).resolve() != CANONICAL_QUEST_PATH.resolve():
        return GateResult("GATE_PRECONDITION_NEW_LANE_PROVEN", False, f"Quest canonical module resolved unexpectedly: {quest.__file__}")
    return GateResult("GATE_PRECONDITION_NEW_LANE_PROVEN", True, "Canonical godotsim.kernels lane exists and imports from the new lane.")



def gate_pre_shim_backups_exist() -> GateResult:
    missing = [
        path.relative_to(REPO_ROOT).as_posix()
        for path in (COMBAT_BACKUP_PATH, QUEST_BACKUP_PATH)
        if not path.is_file()
    ]
    if missing:
        return GateResult("GATE_PRE_SHIM_BACKUPS_EXIST", False, f"Missing pre-shim backups: {missing}")
    return GateResult("GATE_PRE_SHIM_BACKUPS_EXIST", True, "Pre-shim backups exist for both old misplaced kernel paths.")



def gate_backups_preserve_original_kernels() -> GateResult:
    mismatches = []
    if not _byte_equal(COMBAT_BACKUP_PATH, CANONICAL_COMBAT_PATH):
        mismatches.append("combat backup differs from copy-first canonical combat kernel")
    if not _byte_equal(QUEST_BACKUP_PATH, CANONICAL_QUEST_PATH):
        mismatches.append("quest backup differs from copy-first canonical quest kernel")
    if mismatches:
        return GateResult("GATE_BACKUPS_PRESERVE_ORIGINAL_KERNELS", False, "; ".join(mismatches))
    return GateResult("GATE_BACKUPS_PRESERVE_ORIGINAL_KERNELS", True, "Backups preserve the original pre-shim kernel bytes copied into godotsim/kernels/.")



def gate_old_combat_path_is_shim() -> GateResult:
    ok, message = _shim_shape_ok(OLD_COMBAT_PATH, CANONICAL_COMBAT_MODULE, EXPECTED_COMBAT_ALL)
    return GateResult("GATE_OLD_COMBAT_PATH_IS_SHIM", ok, message)



def gate_old_quest_path_is_shim() -> GateResult:
    ok, message = _shim_shape_ok(OLD_QUEST_PATH, CANONICAL_QUEST_MODULE, EXPECTED_QUEST_ALL)
    return GateResult("GATE_OLD_QUEST_PATH_IS_SHIM", ok, message)



def gate_old_combat_symbols_reexport_canonical() -> GateResult:
    try:
        canonical = _module(CANONICAL_COMBAT_MODULE)
        old = _module(OLD_COMBAT_MODULE)
    except Exception as exc:
        return GateResult("GATE_OLD_COMBAT_SYMBOLS_REEXPORT_CANONICAL", False, f"Combat import failed: {exc!r}")
    bad = [symbol for symbol in COMBAT_SYMBOLS if getattr(old, symbol, None) is not getattr(canonical, symbol, None)]
    if list(getattr(old, "__all__", [])) != EXPECTED_COMBAT_ALL:
        bad.append("__all__")
    if bad:
        return GateResult("GATE_OLD_COMBAT_SYMBOLS_REEXPORT_CANONICAL", False, f"Combat old path failed canonical re-export for: {bad}")
    return GateResult("GATE_OLD_COMBAT_SYMBOLS_REEXPORT_CANONICAL", True, "Old combat path re-exports canonical combat symbols by object identity.")



def gate_old_quest_symbols_reexport_canonical() -> GateResult:
    try:
        canonical = _module(CANONICAL_QUEST_MODULE)
        old = _module(OLD_QUEST_MODULE)
    except Exception as exc:
        return GateResult("GATE_OLD_QUEST_SYMBOLS_REEXPORT_CANONICAL", False, f"Quest import failed: {exc!r}")
    bad = [symbol for symbol in QUEST_SYMBOLS if getattr(old, symbol, None) is not getattr(canonical, symbol, None)]
    if list(getattr(old, "__all__", [])) != EXPECTED_QUEST_ALL:
        bad.append("__all__")
    if bad:
        return GateResult("GATE_OLD_QUEST_SYMBOLS_REEXPORT_CANONICAL", False, f"Quest old path failed canonical re-export for: {bad}")
    return GateResult("GATE_OLD_QUEST_SYMBOLS_REEXPORT_CANONICAL", True, "Old quest path re-exports canonical quest symbols by object identity.")



def gate_active_old_imports_still_resolve() -> GateResult:
    try:
        quest_integration = _module("godotengain.engainos.core.quest3d_integration")
        replay = _module("godotengain.engainos.core.replay")
        zon_bridge = _module("godotengain.engainos.core.zon_bridge")
        canonical_combat = _module(CANONICAL_COMBAT_MODULE)
        canonical_quest = _module(CANONICAL_QUEST_MODULE)
    except Exception as exc:
        return GateResult("GATE_ACTIVE_OLD_IMPORTS_STILL_RESOLVE", False, f"Active old import resolution failed: {exc!r}")

    checks = {
        "quest3d_integration.step_quest3d": getattr(quest_integration, "step_quest3d", None) is canonical_quest.step_quest3d,
        "quest3d_integration.QuestConfig": getattr(quest_integration, "QuestConfig", None) is canonical_quest.QuestConfig,
        "replay.step_combat": getattr(replay, "step_combat", None) is canonical_combat.step_combat,
        "zon_bridge.CombatSnapshot": getattr(zon_bridge, "CombatSnapshot", None) is canonical_combat.CombatSnapshot,
        "zon_bridge.CombatEntity": getattr(zon_bridge, "CombatEntity", None) is canonical_combat.CombatEntity,
        "zon_bridge.DamageEvent": getattr(zon_bridge, "DamageEvent", None) is canonical_combat.DamageEvent,
    }
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        return GateResult("GATE_ACTIVE_OLD_IMPORTS_STILL_RESOLVE", False, f"Old active imports did not resolve to canonical symbols: {failed}")
    return GateResult("GATE_ACTIVE_OLD_IMPORTS_STILL_RESOLVE", True, "quest3d_integration, replay, and zon_bridge old relative imports still resolve to canonical kernel symbols.")



def gate_shim_smoke_behavior() -> GateResult:
    try:
        combat = _module(OLD_COMBAT_MODULE)
        quest = _module(OLD_QUEST_MODULE)
        target = combat.CombatEntity(entity_id="target", health=10.0, max_health=10.0)
        snapshot = combat.CombatSnapshot(entities={"target": target})
        event = combat.DamageEvent(source_id="source", target_id="target", amount=2.0)
        combat_out = combat.step_combat(snapshot, [event])
        quest_out, accepted, alerts = quest.step_quest3d({"entities": {}, "quest": {"quests": {}, "tick": 0.0}}, [], quest.QuestConfig(), 0.0)
    except Exception as exc:
        return GateResult("GATE_SHIM_SMOKE_BEHAVIOR", False, f"Shim smoke failed: {exc!r}")

    if combat_out.new_snapshot.entities["target"].health != 8.0:
        return GateResult("GATE_SHIM_SMOKE_BEHAVIOR", False, "Combat shim smoke did not decrease health from 10.0 to 8.0.")
    if not isinstance(quest_out, dict) or not isinstance(quest_out.get("quest"), dict):
        return GateResult("GATE_SHIM_SMOKE_BEHAVIOR", False, f"Quest shim smoke did not return quest dict: {quest_out!r}")
    return GateResult("GATE_SHIM_SMOKE_BEHAVIOR", True, f"Old path shims execute canonical smoke behavior; quest accepted={accepted}, alerts={alerts}.")



def _classification(results: list[GateResult]) -> str:
    if all(result.is_true() for result in results):
        return "OLD_PATH_SHIMS_ACTIVE"
    return "OLD_PATH_SHIMS_BLOCKED"



def main() -> int:
    results = [
        gate_precondition_new_lane_proven(),
        gate_pre_shim_backups_exist(),
        gate_backups_preserve_original_kernels(),
        gate_old_combat_path_is_shim(),
        gate_old_quest_path_is_shim(),
        gate_old_combat_symbols_reexport_canonical(),
        gate_old_quest_symbols_reexport_canonical(),
        gate_active_old_imports_still_resolve(),
        gate_shim_smoke_behavior(),
    ]
    classification = _classification(results)
    all_gates = all(result.is_true() for result in results)

    for result in results:
        status = "PASS" if result.is_true() else "FAIL"
        value = "TRUE" if result.is_true() else "FALSE"
        print(f"[gate_mr_kernel_old_path_shims][{result.gate_name}] {status}: {result.gate_name} = {value}; {result.message}")

    print(f"[gate_mr_kernel_old_path_shims][CLASSIFICATION] {classification}")
    print(f"[gate_mr_kernel_old_path_shims][ALL_GATES] {'true' if all_gates else 'false'}")

    return 0 if classification == "OLD_PATH_SHIMS_ACTIVE" else 1


if __name__ == "__main__":
    sys.exit(main())
