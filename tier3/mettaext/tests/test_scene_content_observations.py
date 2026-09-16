"""
test_scene_content_observations.py — RED tests for Boundary 7: Non-Character Scene Content Observations

Goal: Determine where Mettaext should structurally preserve non-character scene contents —
structures, settlement features, terrain features, boundaries, and similar "what exists here" observations.

Fixture: Falcon Ridge founding scene (book_08/047_mika.md)
Required observations to track:
- Falcon Ridge / settlement
- hut
- barracks
- irrigated fields
- perimeter wall
- archive / stone archive building

Target Authority Split:
- Mettaext = WHAT EXISTS in the scene (narrative observation authority)
- GodotSim = WHERE/HOW those things exist spatially
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tier3.mettaext import world_rules_loader
from tier3.mettaext.passroom import (
    pass1_explicit,
    pass2_enhanced,
    pass2_entity_filter,
    pass3_merge,
    pass4_zon_bridge,
    pass5_game_bridge,
)


class TestSceneContentObservations(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp_dir.name)

        world_rules_loader.load_rules()

        # Primary fixture: Falcon Ridge founding text from book_08/047_mika.md
        self.source_text = (
            "# Chapter 047: Falcon Ridge Founding\n"
            "Month 1 was raw survival. The first structure was a simple hut of stone and timber.\n"
            "The second was a long barracks for the soldiers.\n"
            "Month 2 brought order. They planted the first fields, creating irrigated fields with ditches.\n"
            "Month 3 saw the valley become a settlement. A low perimeter wall began to snake around the approaches.\n"
            "A year had gentled Falcon Ridge. The archive was Mika's pride—a solid stone archive building."
        )
        self.ch_file = self.tmp_path / "047_falcon_ridge.txt"
        self.ch_file.write_text(self.source_text, encoding="utf-8")

        self.required_observations = {
            "falcon ridge",
            "hut",
            "barracks",
            "irrigated fields",
            "perimeter wall",
            "archive",
        }

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_pass2_extracts_and_serializes_non_character_scene_features(self):
        """
        Verify Pass 2 extracts non-character scene contents (structures, settlement features, boundaries)
        and serializes them into machine-parseable .metta atoms (e.g., (feature ...) or (structure ...)).
        """
        pass1_out = self.tmp_path / "out_pass1_047_falcon_ridge.txt"
        pass1_explicit.process_file(self.ch_file, pass1_out)

        segments = pass2_enhanced.load_segments(str(pass1_out))
        characters = pass2_entity_filter.filter_entities(pass2_enhanced.extract_characters(segments))

        scene_objects = pass2_enhanced.extract_scene_objects(segments)
        pass2_out = self.tmp_path / "out_pass2_047_falcon_ridge.metta"
        pass2_enhanced.write_metta(
            str(pass2_out),
            pass2_enhanced.infer_speakers_enhanced(segments, characters),
            pass2_enhanced.infer_emotions_enhanced(segments, characters),
            pass2_enhanced.infer_actions_enhanced(segments),
            pass2_enhanced.infer_thoughts_enhanced(segments, characters),
            characters,
            pass2_enhanced.infer_relationships(segments, characters),
            scene_objects=scene_objects,
        )

        metta_content = pass2_out.read_text(encoding="utf-8")
        non_comment_lines = [
            line.strip()
            for line in metta_content.splitlines()
            if line.strip() and not line.strip().startswith(";")
        ]

        # Check for structured scene_object metta atoms
        feature_atoms = [
            line for line in non_comment_lines
            if line.startswith("(scene_object") or line.startswith("(feature") or line.startswith("(structure")
        ]

        self.assertTrue(
            len(feature_atoms) > 0,
            f"Pass 2 metta must contain structured (scene_object ...) atoms, but found none:\n{metta_content}",
        )

    def test_pass3_zonj_preserves_structured_non_character_scene_features(self):
        """
        Verify Pass 3 ZONJ scene output contains a structured representation of observed non-character scene elements
        under scene['scene_content_observed'].
        """
        pass1_out = self.tmp_path / "out_pass1_047_falcon_ridge.txt"
        pass1_explicit.process_file(self.ch_file, pass1_out)

        pass2_out = self.tmp_path / "out_pass2_047_falcon_ridge.metta"
        segments = pass2_enhanced.load_segments(str(pass1_out))
        characters = pass2_entity_filter.filter_entities(pass2_enhanced.extract_characters(segments))
        scene_objects = pass2_enhanced.extract_scene_objects(segments)
        pass2_enhanced.write_metta(
            str(pass2_out),
            pass2_enhanced.infer_speakers_enhanced(segments, characters),
            pass2_enhanced.infer_emotions_enhanced(segments, characters),
            pass2_enhanced.infer_actions_enhanced(segments),
            pass2_enhanced.infer_thoughts_enhanced(segments, characters),
            characters,
            pass2_enhanced.infer_relationships(segments, characters),
            scene_objects=scene_objects,
        )

        p1_segs = pass3_merge.parse_pass1(str(pass1_out))
        p2_data = pass3_merge.parse_pass2(str(pass2_out))
        zonj = pass3_merge.merge_to_zonj(p1_segs, p2_data, str(pass1_out), str(pass2_out))

        features_obs = (
            zonj.get("scene_content_observed")
            or zonj.get("scene_features")
            or zonj.get("features_observed")
        )
        self.assertIsNotNone(
            features_obs,
            f"Pass 3 ZONJ must preserve structured non-character scene feature observations in scene_content_observed, but keys were: {list(zonj.keys())}",
        )
        obs_names = {item.get("name", "").lower() for item in features_obs if isinstance(item, dict)}
        self.assertTrue(
            any("hut" in name for name in obs_names),
            f"Pass 3 ZONJ scene_content_observed must contain 'hut', got: {obs_names}",
        )

    def test_pass4_zon_preserves_non_character_scene_inventory_in_memory_fabric(self):
        """
        Verify Pass 4 ZON format preserves non-character scene elements in =scene_content_observed.
        """
        pass1_out = self.tmp_path / "out_pass1_047_falcon_ridge.txt"
        pass1_explicit.process_file(self.ch_file, pass1_out)

        pass2_out = self.tmp_path / "out_pass2_047_falcon_ridge.metta"
        segments = pass2_enhanced.load_segments(str(pass1_out))
        characters = pass2_entity_filter.filter_entities(pass2_enhanced.extract_characters(segments))
        scene_objects = pass2_enhanced.extract_scene_objects(segments)
        pass2_enhanced.write_metta(
            str(pass2_out),
            pass2_enhanced.infer_speakers_enhanced(segments, characters),
            pass2_enhanced.infer_emotions_enhanced(segments, characters),
            pass2_enhanced.infer_actions_enhanced(segments),
            pass2_enhanced.infer_thoughts_enhanced(segments, characters),
            characters,
            pass2_enhanced.infer_relationships(segments, characters),
            scene_objects=scene_objects,
        )

        p1_segs = pass3_merge.parse_pass1(str(pass1_out))
        p2_data = pass3_merge.parse_pass2(str(pass2_out))
        zonj_dict = pass3_merge.merge_to_zonj(p1_segs, p2_data, str(pass1_out), str(pass2_out))

        zonj_file = self.tmp_path / "zonj_047_falcon_ridge.json"
        zonj_file.write_text(json.dumps(zonj_dict), encoding="utf-8")

        world_rules_file = Path("tier1/engainos/assets/world_rules.json")
        bridge4 = pass4_zon_bridge.ZONBridge(world_rules_path=world_rules_file)
        zon_canonical = bridge4.convert_to_zonj(zonj_file, pass4_zon_bridge.ZONMetadata())

        features_section = (
            zon_canonical.get("=scene_content_observed")
            or zon_canonical.get("scene_content_observed")
            or (zon_canonical.get("=inferred") or {}).get("scene_objects")
        )
        self.assertIsNotNone(
            features_section,
            f"Pass 4 ZON must contain =scene_content_observed section, got keys: {list(zon_canonical.keys())}",
        )

    def test_pass5_game_scene_exposes_structured_scene_inventory_without_runtime_actor_promotion(self):
        """
        Verify Pass 5 game scene output exposes a structured scene_inventory of non-character observations
        (structures, settlement features, boundaries) without promoting them into runtime spawnable characters.
        """
        pass1_out = self.tmp_path / "out_pass1_047_falcon_ridge.txt"
        pass1_explicit.process_file(self.ch_file, pass1_out)

        pass2_out = self.tmp_path / "out_pass2_047_falcon_ridge.metta"
        segments = pass2_enhanced.load_segments(str(pass1_out))
        characters = pass2_entity_filter.filter_entities(pass2_enhanced.extract_characters(segments))
        scene_objects = pass2_enhanced.extract_scene_objects(segments)
        pass2_enhanced.write_metta(
            str(pass2_out),
            pass2_enhanced.infer_speakers_enhanced(segments, characters),
            pass2_enhanced.infer_emotions_enhanced(segments, characters),
            pass2_enhanced.infer_actions_enhanced(segments),
            pass2_enhanced.infer_thoughts_enhanced(segments, characters),
            characters,
            pass2_enhanced.infer_relationships(segments, characters),
            scene_objects=scene_objects,
        )

        p1_segs = pass3_merge.parse_pass1(str(pass1_out))
        p2_data = pass3_merge.parse_pass2(str(pass2_out))
        zonj_dict = pass3_merge.merge_to_zonj(p1_segs, p2_data, str(pass1_out), str(pass2_out))

        zonj_file = self.tmp_path / "zonj_047_falcon_ridge.json"
        zonj_file.write_text(json.dumps(zonj_dict), encoding="utf-8")

        world_rules_file = Path("tier1/engainos/assets/world_rules.json")
        bridge4 = pass4_zon_bridge.ZONBridge(world_rules_path=world_rules_file)
        zon_canonical = bridge4.convert_to_zonj(zonj_file, pass4_zon_bridge.ZONMetadata())

        bridge5 = pass5_game_bridge.GameBridge(world_rules_path=world_rules_file)
        game_scene = bridge5.convert_zon_to_game(zon_canonical)

        # 1. Non-character features must NOT be promoted to runtime characters in game_scene["entities"]
        runtime_entities = game_scene.get("entities", [])
        runtime_names = [
            e.get("name", "").lower() for e in runtime_entities if isinstance(e, dict)
        ]
        for item in ["hut", "barracks", "perimeter wall", "archive"]:
            self.assertNotIn(
                item,
                runtime_names,
                f"Non-character scene feature '{item}' must NOT be promoted to a runtime character in game_scene['entities']",
            )

        # 2. game_scene must expose a structured scene_inventory
        inventory = (
            game_scene.get("scene_inventory")
            or (game_scene.get("metadata") or {}).get("scene_inventory")
        )
        self.assertIsNotNone(
            inventory,
            f"Pass 5 game scene output must expose scene_inventory, got top-level keys: {list(game_scene.keys())}",
        )

    def test_pass2_observation_phrase_fidelity_preserves_full_noun_phrases(self):
        """
        Boundary 7B: Verify Pass 2 preserves full meaningful noun phrases
        ('Falcon Ridge', 'perimeter wall', 'irrigated fields', 'archive', 'barracks', 'hut')
        without fragmenting them into sub-word junk entries ('perimeter', 'fields', 'irrigation', 'falcon', 'star').
        """
        pass1_out = self.tmp_path / "out_pass1_047_falcon_ridge.txt"
        pass1_explicit.process_file(self.ch_file, pass1_out)

        segments = pass2_enhanced.load_segments(str(pass1_out))
        scene_objects = pass2_enhanced.extract_scene_objects(segments)

        extracted_names = {obj.name for obj in scene_objects.values()}

        # 1. Whole observed phrases must be preserved
        expected_phrases = {
            "Falcon Ridge",
            "perimeter wall",
            "irrigated fields",
            "archive",
            "barracks",
            "hut",
        }
        for phrase in expected_phrases:
            self.assertIn(
                phrase,
                extracted_names,
                f"Pass 2 extraction must preserve whole observed phrase '{phrase}', got extracted names: {extracted_names}",
            )

        # 2. Span-overlapping fragments must NOT be emitted as standalone junk entries
        forbidden_fragments = {"perimeter", "irrigation", "star", "falcon"}
        for frag in forbidden_fragments:
            self.assertNotIn(
                frag,
                extracted_names,
                f"Pass 2 extraction must suppress span-overlapping fragment '{frag}', got extracted names: {extracted_names}",
            )


if __name__ == "__main__":
    unittest.main()
