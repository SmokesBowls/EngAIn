"""No-Godot declared scene proof for scene.030_ummade_army.

EngAInOS is authoritative. This module validates a declared snapshot/artifact
without importing, opening, calling, or requiring Godot. GodotSim observations and
prose-derived word entities are rejected as non-authoritative for this proof.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

EXPECTED_SCENE_ID = "scene.030_ummade_army"
EXPECTED_ENTITY_IDS = ("geralt", "mika", "oreck", "zaron")
EXPECTED_SOURCE_KIND = "declared_snapshot_artifact"
EXPECTED_AUTHORITY_OWNER = "EngAInOS"
EXPECTED_ENTITY_SOURCE = "declared_bridge_entities"

PROOF_ARTIFACT_PATH = (
    Path(__file__).resolve().parents[1]
    / "proofs"
    / "scene.030_ummade_army.declared_snapshot.json"
)


class NoGodotSceneProofError(ValueError):
    """Raised when a declared scene artifact fails the no-Godot proof."""


def prove_scene_030_ummade_army() -> dict[str, Any]:
    """Validate the frozen no-Godot proof artifact for scene.030_ummade_army."""

    return prove_declared_scene_snapshot(PROOF_ARTIFACT_PATH)


def prove_declared_scene_snapshot(path: str | Path) -> dict[str, Any]:
    """Validate an EngAInOS-owned declared scene/snapshot artifact.

    The proof is intentionally narrow:
    - exact scene id only;
    - exactly four declared bridge entities;
    - exact ids geralt, mika, oreck, zaron;
    - declared artifact source only;
    - no Godot or GodotSim dependency.
    """

    artifact_path = Path(path)
    data = _load_json_object(artifact_path)

    _require_equal(data.get("scene_id"), EXPECTED_SCENE_ID, "scene_id")
    _require_equal(data.get("source_kind"), EXPECTED_SOURCE_KIND, "source_kind")
    _require_equal(data.get("authority_owner"), EXPECTED_AUTHORITY_OWNER, "authority_owner")
    _require_equal(data.get("entity_source"), EXPECTED_ENTITY_SOURCE, "entity_source")
    _require_equal(data.get("godot_required"), False, "godot_required")

    bridge_entities = data.get("bridge_entities")
    if not isinstance(bridge_entities, list):
        raise NoGodotSceneProofError("bridge_entities must be a declared list")
    if len(bridge_entities) != len(EXPECTED_ENTITY_IDS):
        raise NoGodotSceneProofError(
            f"bridge_entities count must be 4, got {len(bridge_entities)}"
        )

    entity_ids: list[str] = []
    entity_names_normalized: list[str] = []
    for index, entity in enumerate(bridge_entities):
        if not isinstance(entity, dict):
            raise NoGodotSceneProofError(f"bridge_entities[{index}] must be an object")
        entity_id = _normalize_token(entity.get("id") or entity.get("entity_id") or entity.get("@id"))
        entity_name = _normalize_token(entity.get("name") or entity_id)
        if not entity_id:
            raise NoGodotSceneProofError(f"bridge_entities[{index}] has empty id")
        entity_ids.append(entity_id)
        entity_names_normalized.append(entity_name)

    if tuple(entity_ids) != EXPECTED_ENTITY_IDS:
        raise NoGodotSceneProofError(
            f"bridge_entities entity ids must be {list(EXPECTED_ENTITY_IDS)}, got {entity_ids}"
        )
    if tuple(entity_names_normalized) != EXPECTED_ENTITY_IDS:
        raise NoGodotSceneProofError(
            "bridge_entities normalized names must match declared ids "
            f"{list(EXPECTED_ENTITY_IDS)}, got {entity_names_normalized}"
        )

    godot_imported = "godot" in sys.modules
    godotsim_imported = any(name == "godotsim" or name.startswith("godotsim.") for name in sys.modules)
    if godot_imported:
        raise NoGodotSceneProofError("Godot module is imported; no-Godot proof is invalid")
    if godotsim_imported:
        raise NoGodotSceneProofError("GodotSim module is imported; authority proof is invalid")

    return {
        "status": "PASS",
        "scene_id": EXPECTED_SCENE_ID,
        "bridge_entities_count": len(bridge_entities),
        "entity_ids": entity_ids,
        "entity_names_normalized": entity_names_normalized,
        "source_kind": data["source_kind"],
        "source_path": str(artifact_path),
        "authority_owner": data["authority_owner"],
        "entity_source": data["entity_source"],
        "godot_required": False,
        "godot_imported": False,
        "godotsim_imported": False,
        "contract": [
            "EngAInOS owns declared truth.",
            "GodotSim may simulate declared truth.",
            "GodotSim may not invent authority.",
            "Godot may only display what it is handed.",
        ],
    }


def _load_json_object(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise NoGodotSceneProofError(f"declared snapshot/artifact not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise NoGodotSceneProofError(f"declared snapshot/artifact is not valid JSON: {path}") from exc
    if not isinstance(data, dict):
        raise NoGodotSceneProofError("declared snapshot/artifact root must be an object")
    return data


def _require_equal(actual: Any, expected: Any, field: str) -> None:
    if actual != expected:
        raise NoGodotSceneProofError(f"{field} must be {expected!r}, got {actual!r}")


def _normalize_token(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower().replace(" ", "_")


if __name__ == "__main__":
    print(json.dumps(prove_scene_030_ummade_army(), indent=2, sort_keys=True))
