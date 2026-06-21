"""
Compatibility shim for historical misplaced Combat3D MR kernel path.

Canonical implementation now lives at:
    godotsim.kernels.combat3d_mr

Do not add logic here.
"""

from godotsim.kernels.combat3d_mr import (
    CombatEntity,
    DamageEvent,
    CombatSnapshot,
    CombatOutput,
    step_combat,
)

__all__ = [
    "CombatEntity",
    "DamageEvent",
    "CombatSnapshot",
    "CombatOutput",
    "step_combat",
]
