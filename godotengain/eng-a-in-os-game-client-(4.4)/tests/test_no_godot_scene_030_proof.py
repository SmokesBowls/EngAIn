import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from godotengain.engainos.core.no_godot_scene_proof import (
    NoGodotSceneProofError,
    prove_scene_030_ummade_army,
    prove_declared_scene_snapshot,
)

EXPECTED_IDS = ["geralt", "mika", "oreck", "zaron"]


def test_scene_030_no_godot_proof_accepts_only_declared_authority_snapshot():
    proof = prove_scene_030_ummade_army()

    assert proof["status"] == "PASS"
    assert proof["scene_id"] == "scene.030_ummade_army"
    assert proof["bridge_entities_count"] == 4
    assert proof["entity_ids"] == EXPECTED_IDS
    assert proof["entity_names_normalized"] == EXPECTED_IDS
    assert proof["source_kind"] == "declared_snapshot_artifact"
    assert proof["authority_owner"] == "EngAInOS"
    assert proof["entity_source"] == "declared_bridge_entities"
    assert proof["godot_required"] is False
    assert proof["godot_imported"] is False
    assert proof["godotsim_imported"] is False


def test_no_godot_proof_rejects_prose_derived_or_godotsim_inferred_entities(tmp_path):
    for entity_source in ("prose_derived_word_entities", "godotsim_inferred_entities"):
        artifact = _artifact(tmp_path, entity_source=entity_source)
        try:
            prove_declared_scene_snapshot(artifact)
        except NoGodotSceneProofError as exc:
            assert entity_source in str(exc)
        else:
            raise AssertionError(f"accepted forbidden entity_source={entity_source}")


def test_no_godot_proof_rejects_wrong_scene_id_and_wrong_entity_counts(tmp_path):
    for scene_id in ("?", "scene._"):
        artifact = _artifact(tmp_path, scene_id=scene_id)
        try:
            prove_declared_scene_snapshot(artifact)
        except NoGodotSceneProofError as exc:
            assert "scene_id" in str(exc)
        else:
            raise AssertionError(f"accepted forbidden scene_id={scene_id}")

    for entities in ([], EXPECTED_IDS[:3], EXPECTED_IDS + ["extra"]):
        artifact = _artifact(tmp_path, entity_ids=entities)
        try:
            prove_declared_scene_snapshot(artifact)
        except NoGodotSceneProofError as exc:
            assert "bridge_entities" in str(exc) or "entity ids" in str(exc)
        else:
            raise AssertionError(f"accepted forbidden entities={entities}")


def _artifact(
    tmp_path: Path,
    scene_id: str = "scene.030_ummade_army",
    entity_source: str = "declared_bridge_entities",
    entity_ids=None,
) -> Path:
    ids = EXPECTED_IDS if entity_ids is None else list(entity_ids)
    path = tmp_path / "artifact.json"
    path.write_text(
        json.dumps(
            {
                "scene_id": scene_id,
                "source_kind": "declared_snapshot_artifact",
                "authority_owner": "EngAInOS",
                "entity_source": entity_source,
                "godot_required": False,
                "bridge_entities": [
                    {"id": entity_id, "name": entity_id.title()} for entity_id in ids
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return path
