"""The lane line in machine-readable form (GEN2_OUTPUT_CONTRACT.md §3.1).

Keys that belong to another lane's interpretation, or to an authority Gen2
does not hold, must never appear anywhere in a Gen2 artifact. Producer
describes; consumer interprets.
"""

from __future__ import annotations

from typing import Any, List

FORBIDDEN_KEYS = frozenset({
    # GodotSim placement / physics
    "position", "velocity", "collision", "collision_role", "rotation", "transform",
    "spawn", "spawnable", "despawn",
    # Engionality affect interpretation
    "affect_state", "intensity", "stability", "relationship_deltas", "scene_mood",
    # trixelmap / WorldField terrain interpretation
    "terrain_profile", "environment_type", "terrain_grid",
    # Topologist interpretation
    "qslinks", "olinks", "movelinks", "rcc8", "rel_type",
    # identity minted only by EngAInOS
    "canonical_id", "entity_id",
    # permission / canon authority
    "allowed", "ap_allowed", "canon", "admitted", "accepted",
    "accepted_runtime_truth", "canon_status",
})


def find_forbidden(obj: Any, path: str = "$") -> List[str]:
    """Return JSON paths of every forbidden key, at any depth."""
    hits: List[str] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            here = f"{path}.{key}"
            if key in FORBIDDEN_KEYS:
                hits.append(here)
            hits.extend(find_forbidden(value, here))
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            hits.extend(find_forbidden(value, f"{path}[{i}]"))
    return hits
