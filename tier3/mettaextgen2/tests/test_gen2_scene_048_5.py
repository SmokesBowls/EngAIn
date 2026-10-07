"""End-to-end acceptance for Gen2 on the real scene 048.5 (Book 09).

The success criteria are those set on 2026-10-06 for the first Gen2 lever.
Read-only: inputs are the Chapterroom stageroom output and the pinned vault
chapter. Skipped when either is absent.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from tier3.mettaextgen2.compare_legacy import DEFAULT_PASSROOM_ROOT, legacy_entities
from tier3.mettaextgen2.lib.artifact_schema import validate_parse_artifact_v2
from tier3.mettaextgen2.lib.lane_line import find_forbidden
from tier3.mettaextgen2.orchestrator import DEFAULT_CHAPTERROOM_ROOT, main, run_scene

CHAPTER = "chapter.book009.048_the_ledger_born"
SCENE = "scene.book009.048_the_ledger_born.scene005"
SOURCE = Path("/mnt/data-drive/obsidianburdenNov25not vault/book_09_bureaucratic_debt/048_the_ledger_born.md")
INDEX = DEFAULT_CHAPTERROOM_ROOT / "scene_packets" / CHAPTER / "scene_packets_index.json"
LEGACY_JUNK = {"Chapter", "Core", "Stage", "Mail", "Ridge", "Node", "Gamma", "Sound", "Echo", "Falcon",
               "Dragon", "Applicator", "Faraxar", "Sath", "Covenant", "Mikas"}


@unittest.skipUnless(SOURCE.is_file() and INDEX.is_file(), "Book 09 source or stageroom output not present")
class TestScene0485(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.artifact = run_scene(DEFAULT_CHAPTERROOM_ROOT, CHAPTER, SCENE)
        cls.source_text = SOURCE.read_text(encoding="utf-8")
        cls.by_surface = {e["surface"]: e for e in cls.artifact["declared_entities"]}
        cls.accepted = {s for s, e in cls.by_surface.items() if e["status"] != "REJECTED"}

    def test_1_no_fake_entities(self):
        self.assertFalse(LEGACY_JUNK & self.accepted, f"fake entities accepted: {LEGACY_JUNK & self.accepted}")
        for word in ("Three", "Teachers", "Protectors"):
            self.assertEqual(self.by_surface[word]["status"], "REJECTED")
        self.assertNotIn("Let", self.by_surface)

    def test_2_mika_covenant_referenced(self):
        e = self.by_surface["Mika Covenant"]
        self.assertEqual(e["presence"], "referenced")
        self.assertIn("grave and memory only", e["notes"])

    def test_3_five_mikas_referenced_not_present(self):
        e = self.by_surface["Five Mikas"]
        self.assertEqual(e["presence"], "referenced")
        self.assertEqual(e["entity_type"], "group")
        self.assertIn("remote/interstitial watchers only", e["notes"])

    def test_4_genuine_entities_discoverable(self):
        self.assertEqual(self.by_surface["Geralt"]["presence"], "present")
        self.assertEqual(self.by_surface["Zephyr"]["presence"], "present")
        self.assertEqual(self.by_surface["Karvex"]["status"], "CANDIDATE")
        self.assertEqual(self.by_surface["Karvex"]["presence"], "unknown")
        locations = {l["surface"] for l in self.artifact["declared_locations"]}
        self.assertTrue({"Falcon Ridge", "Mika's grave"} <= locations)
        # Out-of-scene names stay discoverable as metadata constraints, not entities.
        subjects = {c.get("subject") for c in self.artifact["metadata_constraints"]}
        self.assertIn("Zaron", subjects)
        zaron = next(c for c in self.artifact["metadata_constraints"] if c.get("subject") == "Zaron")
        self.assertEqual(zaron["kind"], "non_inference")

    def test_5_every_claim_has_exact_provenance(self):
        sid = self.artifact["source_text_id"]
        spans = []
        for section in ("declared_entities", "declared_locations"):
            for item in self.artifact[section]:
                spans.append(item["source_span"])
                spans.extend(item["evidence"])
        for al in self.artifact["alias_candidates"]:
            spans.extend(al["evidence"])
        spans.extend(c["source_span"] for c in self.artifact["metadata_constraints"])
        self.assertTrue(spans)
        for sp in spans:
            self.assertEqual(sp["source_text_id"], sid)
            self.assertEqual(self.source_text[sp["char_start"]:sp["char_end"]], sp["text"])
            self.assertTrue(467 <= sp["line"] <= 542, sp)

    def test_6_no_downstream_owned_interpretation(self):
        self.assertEqual(find_forbidden(self.artifact), [])
        self.assertIsNone(self.artifact["scene"]["runtime_stage_id"])
        self.assertEqual(self.artifact["canon_claims"], [])
        self.assertTrue(all(e["local_ref"].startswith("ent_") for e in self.artifact["declared_entities"]))

    def test_7_artifact_validates_and_identity_is_inherited(self):
        self.assertEqual(validate_parse_artifact_v2(self.artifact, self.source_text), [])
        scene = self.artifact["scene"]
        self.assertEqual(scene["chapterroom_scene_id"], SCENE)
        self.assertEqual(scene["source_scene_label"], "048.5")
        self.assertTrue(scene["authored_scene_boundaries_proven"])

    def test_deterministic(self):
        again = run_scene(DEFAULT_CHAPTERROOM_ROOT, CHAPTER, SCENE)
        self.assertEqual(json.dumps(again, sort_keys=True), json.dumps(self.artifact, sort_keys=True))

    def test_mika_ambiguity_preserved_not_forced(self):
        mika = [a for a in self.artifact["alias_candidates"] if a["surface"] == "Mika"]
        self.assertTrue(mika)
        covenant = self.by_surface["Mika Covenant"]["local_ref"]
        five = self.by_surface["Five Mikas"]["local_ref"]
        for a in mika:
            self.assertEqual((a["candidate_ref"], a["alternatives"]), (covenant, [five]))

    def test_improves_on_legacy(self):
        legacy = {e["name"] for e in legacy_entities(DEFAULT_PASSROOM_ROOT, SCENE)}
        self.assertTrue({"Chapter", "Core", "Stage"} <= legacy, "legacy baseline changed; re-check comparison")
        self.assertFalse({"Chapter", "Core", "Stage"} & set(self.by_surface))

    def test_cli_exit_codes(self):
        import io, contextlib
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(["--chapter-id", CHAPTER, "--scene-id", SCENE]), 0)
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(["--chapter-id", CHAPTER, "--scene-id", "scene.nope"]), 2)


if __name__ == "__main__":
    unittest.main()
