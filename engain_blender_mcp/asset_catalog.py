"""
ASSET_AUTHORITY_LIBRARY_v1

Authoritative semantic asset records for EngAIn Blender generation.

This file contains truth, not Blender logic.

Invariant:
    Catalog = authority
    Translator = meaning -> build parameters
    Generator = geometry
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict


ASSET_AUTHORITY_LIBRARY: Dict[str, Dict[str, Any]] = {
    "star_needle": {
        "id": "star_needle",
        "class": "nexus_structure",
        "description": "Planetary nexus structure used for resonance, relay, and energy-channeling functions.",
        "known_forms": [
            "intact",
            "weathered",
            "ruined",
        ],
        "default_state": "intact",
        "default_scale": {
            "height_m": 60.0,
            "base_radius_m": 4.0,
        },
        "default_features": [
            "resonance_ring",
            "nexus_core",
        ],
        "visual_profile": {
            "silhouette": "needle",
            "symmetry": "radial",
        },
    }
}


def get_asset_record(asset_id: str) -> Dict[str, Any]:
    """
    Return a deep copy of an asset authority record.

    The catalog itself must not be mutated by translators or callers.
    """
    if asset_id not in ASSET_AUTHORITY_LIBRARY:
        raise KeyError(f"Unknown asset_id: {asset_id!r}")

    return deepcopy(ASSET_AUTHORITY_LIBRARY[asset_id])
