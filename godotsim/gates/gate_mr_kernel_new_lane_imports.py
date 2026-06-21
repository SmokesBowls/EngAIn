# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/godotsim/gates/gate_mr_kernel_new_lane_imports.py

from __future__ import annotations

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

KERNEL_LANE = REPO_ROOT / "godotsim/kernels"
COMBAT_KERNEL = KERNEL_LANE / "combat3d_mr.py"
QUEST_KERNEL = KERNEL_LANE / "quest3d_mr.py"
OLD_COMBAT_KERNEL = REPO_ROOT / "godotengain/engainos/core/combat3d_mr.py"
OLD_QUEST_KERNEL = REPO_ROOT / "godotengain/engainos/core/quest3d_mr.py"

COMBAT_MODULE = "godotsim.kernels.combat3d_mr"
QUEST_MODULE = "godotsim.kernels.quest3d_mr"

COMBAT_PUBLIC_SYMBOLS = {
    "CombatEntity",
    "CombatSnapshot",
    "DamageEvent",
    "CombatOutput",
    "step_combat",
}
QUEST_PUBLIC_SYMBOLS = {
    "QuestConfig",
    "step_quest3d",
    "get_quest_summaries",
}


@dataclass(frozen=True)
class GateResult:
    gate_name: str
    passed: bool
    message: str

    def is_true(self) -> bool:
        return self.passed is True



def _module(module_name: str) -> Any:
    return importlib.import_module(module_name)



def _missing_symbols(module: Any, required: set[str]) -> list[str]:
    return sorted(symbol for symbol in required if not hasattr(module, symbol))



def gate_kernel_lane_exists() -> GateResult:
    required_paths = [KERNEL_LANE, KERNEL_LANE / "__init__.py", COMBAT_KERNEL, QUEST_KERNEL]
    missing = [str(path.relative_to(REPO_ROOT)) for path in required_paths if not path.exists()]
    if missing:
        return GateResult(
            "GATE_KERNEL_LANE_EXISTS",
            False,
            f"Kernel lane is incomplete; missing {missing}",
        )
    return GateResult(
        "GATE_KERNEL_LANE_EXISTS",
        True,
        "Kernel lane exists with __init__.py, combat3d_mr.py, and quest3d_mr.py under godotsim/kernels/.",
    )



def gate_combat_kernel_imports_from_new_lane() -> GateResult:
    try:
        module = _module(COMBAT_MODULE)
    except Exception as exc:
        return GateResult(
            "GATE_COMBAT_KERNEL_IMPORTS_FROM_NEW_LANE",
            False,
            f"Failed to import {COMBAT_MODULE}: {exc!r}",
        )
    module_file = Path(getattr(module, "__file__", "")).resolve()
    if module_file == COMBAT_KERNEL.resolve():
        return GateResult(
            "GATE_COMBAT_KERNEL_IMPORTS_FROM_NEW_LANE",
            True,
            f"{COMBAT_MODULE} imports from {COMBAT_KERNEL.relative_to(REPO_ROOT)}.",
        )
    return GateResult(
        "GATE_COMBAT_KERNEL_IMPORTS_FROM_NEW_LANE",
        False,
        f"{COMBAT_MODULE} resolved to unexpected file {module_file}.",
    )



def gate_quest_kernel_imports_from_new_lane() -> GateResult:
    try:
        module = _module(QUEST_MODULE)
    except Exception as exc:
        return GateResult(
            "GATE_QUEST_KERNEL_IMPORTS_FROM_NEW_LANE",
            False,
            f"Failed to import {QUEST_MODULE}: {exc!r}",
        )
    module_file = Path(getattr(module, "__file__", "")).resolve()
    if module_file == QUEST_KERNEL.resolve():
        return GateResult(
            "GATE_QUEST_KERNEL_IMPORTS_FROM_NEW_LANE",
            True,
            f"{QUEST_MODULE} imports from {QUEST_KERNEL.relative_to(REPO_ROOT)}.",
        )
    return GateResult(
        "GATE_QUEST_KERNEL_IMPORTS_FROM_NEW_LANE",
        False,
        f"{QUEST_MODULE} resolved to unexpected file {module_file}.",
    )



def gate_combat_public_symbols_present() -> GateResult:
    try:
        module = _module(COMBAT_MODULE)
        missing = _missing_symbols(module, COMBAT_PUBLIC_SYMBOLS)
    except Exception as exc:
        return GateResult("GATE_COMBAT_PUBLIC_SYMBOLS_PRESENT", False, f"Combat symbol check failed: {exc!r}")
    if missing:
        return GateResult("GATE_COMBAT_PUBLIC_SYMBOLS_PRESENT", False, f"Missing combat public symbols: {missing}")
    return GateResult(
        "GATE_COMBAT_PUBLIC_SYMBOLS_PRESENT",
        True,
        f"Combat public symbols are present: {sorted(COMBAT_PUBLIC_SYMBOLS)}.",
    )



def gate_quest_public_symbols_present() -> GateResult:
    try:
        module = _module(QUEST_MODULE)
        missing = _missing_symbols(module, QUEST_PUBLIC_SYMBOLS)
    except Exception as exc:
        return GateResult("GATE_QUEST_PUBLIC_SYMBOLS_PRESENT", False, f"Quest symbol check failed: {exc!r}")
    if missing:
        return GateResult("GATE_QUEST_PUBLIC_SYMBOLS_PRESENT", False, f"Missing quest public symbols: {missing}")
    return GateResult(
        "GATE_QUEST_PUBLIC_SYMBOLS_PRESENT",
        True,
        f"Quest public symbols are present: {sorted(QUEST_PUBLIC_SYMBOLS)}.",
    )



def gate_combat_smoke_behavior() -> GateResult:
    try:
        module = _module(COMBAT_MODULE)
        target = module.CombatEntity(entity_id="target", health=10.0, max_health=10.0)
        snapshot = module.CombatSnapshot(entities={"target": target})
        event = module.DamageEvent(source_id="source", target_id="target", amount=3.0)
        output = module.step_combat(snapshot, [event])
        new_target = output.new_snapshot.entities["target"]
    except Exception as exc:
        return GateResult("GATE_COMBAT_SMOKE_BEHAVIOR", False, f"Combat smoke failed: {exc!r}")

    if new_target.health == 7.0 and new_target.health < target.health:
        return GateResult(
            "GATE_COMBAT_SMOKE_BEHAVIOR",
            True,
            "Combat smoke passed: one damage event decreased target health from 10.0 to 7.0.",
        )
    return GateResult(
        "GATE_COMBAT_SMOKE_BEHAVIOR",
        False,
        f"Combat smoke did not decrease health as expected: before={target.health}, after={new_target.health}.",
    )



def gate_quest_smoke_behavior() -> GateResult:
    try:
        module = _module(QUEST_MODULE)
        config = module.QuestConfig()
        snapshot = {"entities": {}, "quest": {"quests": {}, "tick": 0.0}}
        output, accepted, alerts = module.step_quest3d(snapshot, [], config, 0.0)
    except Exception as exc:
        return GateResult("GATE_QUEST_SMOKE_BEHAVIOR", False, f"Quest smoke failed: {exc!r}")

    if isinstance(output, dict) and isinstance(output.get("quest"), dict):
        return GateResult(
            "GATE_QUEST_SMOKE_BEHAVIOR",
            True,
            f"Quest smoke passed: QuestConfig instantiated, step_quest3d returned quest dict with accepted={accepted}, alerts={alerts}.",
        )
    return GateResult(
        "GATE_QUEST_SMOKE_BEHAVIOR",
        False,
        f"Quest smoke did not return a dict containing a quest dict: {output!r}",
    )



def gate_old_files_still_present() -> GateResult:
    missing = [str(path.relative_to(REPO_ROOT)) for path in (OLD_COMBAT_KERNEL, OLD_QUEST_KERNEL) if not path.is_file()]
    if missing:
        return GateResult("GATE_OLD_FILES_STILL_PRESENT", False, f"Old misplaced kernel files are missing: {missing}")
    return GateResult(
        "GATE_OLD_FILES_STILL_PRESENT",
        True,
        "Old misplaced kernel files are still present; no delete/move occurred.",
    )



def _classification(results: list[GateResult]) -> str:
    if all(result.is_true() for result in results):
        return "NEW_KERNEL_LANE_PROVEN"
    return "NEW_KERNEL_LANE_BLOCKED"



def main() -> int:
    results = [
        gate_kernel_lane_exists(),
        gate_combat_kernel_imports_from_new_lane(),
        gate_quest_kernel_imports_from_new_lane(),
        gate_combat_public_symbols_present(),
        gate_quest_public_symbols_present(),
        gate_combat_smoke_behavior(),
        gate_quest_smoke_behavior(),
        gate_old_files_still_present(),
    ]
    classification = _classification(results)
    all_gates = all(result.is_true() for result in results)

    for result in results:
        status = "PASS" if result.is_true() else "FAIL"
        value = "TRUE" if result.is_true() else "FALSE"
        print(f"[gate_mr_kernel_new_lane_imports][{result.gate_name}] {status}: {result.gate_name} = {value}; {result.message}")

    print(f"[gate_mr_kernel_new_lane_imports][CLASSIFICATION] {classification}")
    print(f"[gate_mr_kernel_new_lane_imports][ALL_GATES] {'true' if all_gates else 'false'}")

    return 0 if classification == "NEW_KERNEL_LANE_PROVEN" else 1


if __name__ == "__main__":
    sys.exit(main())
