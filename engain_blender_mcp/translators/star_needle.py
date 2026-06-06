"""
Star Needle translator.

Turns the Star Needle authority record into dumb generator parameters.

No Blender imports.
No file writes.
No catalog mutation.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List


def translate_star_needle(asset_record: Dict[str, Any], overrides: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """
    Translate canonical Star Needle authority into build parameters for generate_star_needle.py.

    Catalog authority is treated as read-only. All mutable values are copied before use.
    """
    overrides = deepcopy(overrides or {})

    if asset_record.get("id") != "star_needle":
        raise ValueError(f"Expected asset_record id 'star_needle', got {asset_record.get('id')!r}")

    scale: Dict[str, Any] = dict(asset_record.get("default_scale", {}))
    scale.update(dict(overrides.get("scale", {})))

    features: List[str] = list(asset_record.get("default_features", []))

    for feature in overrides.get("add_features", []):
        if feature not in features:
            features.append(feature)

    remove_features = set(overrides.get("remove_features", []))
    features = [feature for feature in features if feature not in remove_features]

    state = str(overrides.get("state", asset_record.get("default_state", "intact")))

    star_count = 8 if "nexus_core" in features else 6
    if state == "weathered":
        star_count = max(4, star_count - 1)
    elif state == "ruined":
        star_count = max(3, star_count - 3)

    return {
        "height_m": float(scale.get("height_m", 60.0)),
        "base_radius_m": float(scale.get("base_radius_m", 4.0)),
        "star_count": int(star_count),
        "nexus_core_enabled": "nexus_core" in features,
        "ring_count": 3 if "resonance_ring" in features else 0,
        "damage_state": state,
        "asset_id": asset_record["id"],
    }
