"""
Compatibility shim for historical misplaced Quest3D MR kernel path.

Canonical implementation now lives at:
    godotsim.kernels.quest3d_mr

Do not add logic here.
"""

from godotsim.kernels.quest3d_mr import (
    QuestConfig,
    step_quest3d,
    get_quest_summaries,
)

__all__ = [
    "QuestConfig",
    "step_quest3d",
    "get_quest_summaries",
]
