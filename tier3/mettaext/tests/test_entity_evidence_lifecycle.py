"""
test_entity_evidence_lifecycle.py — Tests for Boundary 6: Entity Evidence Lifecycle & Runtime Exclusion

Goal: preserve unknown/non-spawnable entity observations (e.g., Igigi) as structured
semantic evidence through Pass 2/3/4 without adding them to runtime/spawnable entity collections.

Lifecycle of Igigi:
  Pass 2 UNKNOWN
  → structured Pass 2/3 evidence
  → structured Pass 4 evidence
  → absent from runtime/spawnable @entities if non-spawnable
  → absent from Pass 5 runtime entities
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tier3.mettaext import pipeline_runner, world_rules_loader
from tier3.mettaext.passroom import (
    pass1_explicit,
    pass2_enhanced,
    pass2_entity_filter,
    pass3_merge,
    pass4_zon_bridge,
    pass5_game_bridge,
)


class TestEntityEvidenceLifecycle(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp_dir.name)

        world_rules_loader.load_rules()

        # Create source text with unknown entity Igigi and known spawnable entity Vairis
        self.source_text = (
            "# Chapter 201: Entity Evidence Test\n"
            "Vairis walked along the stone wall.\n"
            "Igigi stood silent in the shadows.\n"
            "\"The path is clear,\" Igigi observed."
        )
        self.ch_file = self.tmp_path / "201_entity_lifecycle.txt"
        self.ch_file.write_text(self.source_text, encoding="utf-8")

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_pass2_metta_preserves_structured_entity_evidence(self):
        """
        Verify Pass 2 writes structured metta atoms for entity candidates
        (e.g., Igigi as unknown/non-spawnable), not just comment lines starting with ';'.
        """
        pass1_out = self.tmp_path / "out_pass1_201_entity_lifecycle.txt"
        pass1_explicit.process_file(self.ch_file, pass1_out)

        segments = pass2_enhanced.load_segments(str(pass1_out))
        characters = pass2_enhanced.extract_characters(segments)
        filtered_chars = pass2_entity_filter.filter_entities(characters)

        self.assertIn("Igigi", filtered_chars)
        self.assertFalse(filtered_chars["Igigi"].known)
        self.assertFalse(filtered_chars["Igigi"].spawnable)
        self.assertEqual(filtered_chars["Igigi"].classification, "unknown")

        pass2_out = self.tmp_path / "out_pass2_201_entity_lifecycle.metta"
        speakers = pass2_enhanced.infer_speakers_enhanced(segments, filtered_chars)
        emotions = pass2_enhanced.infer_emotions_enhanced(segments, filtered_chars)
        actions = pass2_enhanced.infer_actions_enhanced(segments)
        thoughts = pass2_enhanced.infer_thoughts_enhanced(segments, filtered_chars)
        relationships = pass2_enhanced.infer_relationships(segments, filtered_chars)

        pass2_enhanced.write_metta(
            str(pass2_out),
            speakers,
            emotions,
            actions,
            thoughts,
            filtered_chars,
            relationships,
        )

        metta_content = pass2_out.read_text(encoding="utf-8")
        non_comment_lines = [
            line.strip()
            for line in metta_content.splitlines()
            if line.strip() and not line.strip().startswith(";")
        ]

        # Check for structured entity atom: (entity Igigi ...) or (entity_candidate Igigi ...)
        entity_atoms = [
            line for line in non_comment_lines
            if line.startswith("(entity") and "Igigi" in line
        ]
        self.assertTrue(
            len(entity_atoms) > 0,
            f"Pass 2 metta must contain structured entity atoms (e.g. (entity Igigi ...)), but found only comments or speaker atoms:\n{metta_content}",
        )


    def test_pass3_zonj_preserves_structured_entity_evidence(self):
        """
        Verify Pass 3 ZONJ scene output contains structured evidence of observed entities
        (e.g., in top-level observed_entities or inferred entity candidates), preserving Igigi's classification.
        """
        pass1_out = self.tmp_path / "out_pass1_201_entity_lifecycle.txt"
        pass1_explicit.process_file(self.ch_file, pass1_out)

        pass2_out = self.tmp_path / "out_pass2_201_entity_lifecycle.metta"
        segments = pass2_enhanced.load_segments(str(pass1_out))
        characters = pass2_entity_filter.filter_entities(pass2_enhanced.extract_characters(segments))
        pass2_enhanced.write_metta(
            str(pass2_out),
            pass2_enhanced.infer_speakers_enhanced(segments, characters),
            pass2_enhanced.infer_emotions_enhanced(segments, characters),
            pass2_enhanced.infer_actions_enhanced(segments),
            pass2_enhanced.infer_thoughts_enhanced(segments, characters),
            characters,
            pass2_enhanced.infer_relationships(segments, characters),
        )

        p1_segs = pass3_merge.parse_pass1(str(pass1_out))
        p2_data = pass3_merge.parse_pass2(str(pass2_out))
        zonj = pass3_merge.merge_to_zonj(p1_segs, p2_data, str(pass1_out), str(pass2_out))

        # Check if structured entity evidence for Igigi is preserved in ZONJ
        entities_obs = (
            zonj.get("entities_observed")
            or zonj.get("observed_entities")
            or (zonj.get("inferred") or {}).get("entities")
        )
        self.assertIsNotNone(
            entities_obs,
            f"Pass 3 ZONJ must preserve structured entity evidence, but none was found in keys of zonj: {list(zonj.keys())}",
        )
        igigi_obs = [e for e in entities_obs if (isinstance(e, dict) and e.get("name") == "Igigi") or e == "Igigi"]
        self.assertTrue(len(igigi_obs) > 0, "Pass 3 ZONJ must preserve structured evidence for Igigi")

    def test_pass4_zon_preserves_structured_evidence_and_excludes_non_spawnable_from_at_entities(self):
        """
        Verify Pass 4 ZON:
        1. Excludes unknown/non-spawnable Igigi from @entities (the runtime spawnable collection).
        2. Preserves Igigi in structured observation/evidence sections.
        """
        pass1_out = self.tmp_path / "out_pass1_201_entity_lifecycle.txt"
        pass1_explicit.process_file(self.ch_file, pass1_out)
        pass2_out = self.tmp_path / "out_pass2_201_entity_lifecycle.metta"
        segments = pass2_enhanced.load_segments(str(pass1_out))
        characters = pass2_entity_filter.filter_entities(pass2_enhanced.extract_characters(segments))
        pass2_enhanced.write_metta(
            str(pass2_out),
            pass2_enhanced.infer_speakers_enhanced(segments, characters),
            pass2_enhanced.infer_emotions_enhanced(segments, characters),
            pass2_enhanced.infer_actions_enhanced(segments),
            pass2_enhanced.infer_thoughts_enhanced(segments, characters),
            characters,
            pass2_enhanced.infer_relationships(segments, characters),
        )

        p1_segs = pass3_merge.parse_pass1(str(pass1_out))
        p2_data = pass3_merge.parse_pass2(str(pass2_out))
        zonj_dict = pass3_merge.merge_to_zonj(p1_segs, p2_data, str(pass1_out), str(pass2_out))

        zonj_file = self.tmp_path / "zonj_201_entity_lifecycle.json"
        zonj_file.write_text(json.dumps(zonj_dict), encoding="utf-8")

        world_rules_file = Path("tier1/engainos/assets/world_rules.json")
        bridge = pass4_zon_bridge.ZONBridge(world_rules_path=world_rules_file)
        zon_canonical = bridge.convert_to_zonj(zonj_file, pass4_zon_bridge.ZONMetadata())

        at_entities = zon_canonical.get("@entities", [])
        self.assertNotIn(
            "Igigi",
            at_entities,
            f"Igigi (unknown/non-spawnable) MUST NOT be present in @entities runtime spawnable list, got: {at_entities}",
        )

        # Check structured evidence section in Pass 4
        inferred = zon_canonical.get("=inferred", {})
        entities_obs = (
            zon_canonical.get("=entities_observed")
            or zon_canonical.get("=observed_entities")
            or inferred.get("entities")
            or inferred.get("entity_candidates")
        )
        self.assertIsNotNone(
            entities_obs,
            "Pass 4 ZON must contain structured entity observation evidence",
        )
        igigi_obs = [e for e in entities_obs if (isinstance(e, dict) and e.get("name") == "Igigi") or e == "Igigi"]
        self.assertTrue(len(igigi_obs) > 0, "Pass 4 ZON must preserve Igigi in structured evidence")

    def test_pass5_game_scene_excludes_non_spawnable_from_runtime_entities(self):
        """
        Verify Pass 5 game scene output excludes Igigi from runtime spawnable entities array.
        """
        pass1_out = self.tmp_path / "out_pass1_201_entity_lifecycle.txt"
        pass1_explicit.process_file(self.ch_file, pass1_out)
        pass2_out = self.tmp_path / "out_pass2_201_entity_lifecycle.metta"
        segments = pass2_enhanced.load_segments(str(pass1_out))
        characters = pass2_entity_filter.filter_entities(pass2_enhanced.extract_characters(segments))
        pass2_enhanced.write_metta(
            str(pass2_out),
            pass2_enhanced.infer_speakers_enhanced(segments, characters),
            pass2_enhanced.infer_emotions_enhanced(segments, characters),
            pass2_enhanced.infer_actions_enhanced(segments),
            pass2_enhanced.infer_thoughts_enhanced(segments, characters),
            characters,
            pass2_enhanced.infer_relationships(segments, characters),
        )

        p1_segs = pass3_merge.parse_pass1(str(pass1_out))
        p2_data = pass3_merge.parse_pass2(str(pass2_out))
        zonj_dict = pass3_merge.merge_to_zonj(p1_segs, p2_data, str(pass1_out), str(pass2_out))
        zonj_file = self.tmp_path / "zonj_201_entity_lifecycle.json"
        zonj_file.write_text(json.dumps(zonj_dict), encoding="utf-8")

        world_rules_file = Path("tier1/engainos/assets/world_rules.json")
        bridge4 = pass4_zon_bridge.ZONBridge(world_rules_path=world_rules_file)
        zon_canonical = bridge4.convert_to_zonj(zonj_file, pass4_zon_bridge.ZONMetadata())

        bridge5 = pass5_game_bridge.GameBridge(world_rules_path=world_rules_file)
        game_scene = bridge5.convert_zon_to_game(zon_canonical)

        runtime_entities = game_scene.get("entities", [])
        spawned_ids = [e.get("id") for e in runtime_entities if isinstance(e, dict)]
        spawned_names = [e.get("name") for e in runtime_entities if isinstance(e, dict)]

        self.assertNotIn("igigi", spawned_ids, f"Igigi MUST NOT be spawned in Pass 5 game scene entities: {spawned_ids}")
        self.assertNotIn("Igigi", spawned_names, f"Igigi MUST NOT be spawned in Pass 5 game scene entities: {spawned_names}")


if __name__ == "__main__":
    unittest.main()
