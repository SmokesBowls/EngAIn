"""Acceptance tests G1-G13 for grammatical entity identification, dialogue
attribution and prose presence (claude/GEN2_GRAMMATICAL_ENTITY_PLAN.md, approved
2026-10-29 with decisions: chapter context, prose presence as low-confidence
evidence with communication never physical, rules only, references deferred).

Book 1 cases quote the manuscript; the others isolate one rule each.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tier3.mettaextgen2.lib.annotations import AnnotationStore, SceneInput
from tier3.mettaextgen2.lib.artifact_schema import validate_parse_artifact_v2
from tier3.mettaextgen2.lib.source import SourceDocument
from tier3.mettaextgen2.modules.artifact_assembler import assemble
from tier3.mettaextgen2.orchestrator import default_modules, order_modules

SCENE_INPUT = SceneInput(
    chapter_id="chapter.book001.001_test", chapterroom_scene_id="scene.book001.001_test.scene001",
    source_scene_label="001.1", source_scene_title="test", boundary_method="authored_scene_marker",
    authored_scene_boundaries_proven=True, packet_path="(synthetic)",
)


def _artifact(prose: str, yaml: str = "") -> dict:
    text = "### scene 001.1 — test\n" + (f"```yaml\n{yaml}\n```\n" if yaml else "") + prose + "\n"
    tmp = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8")
    tmp.write(text)
    tmp.close()
    doc = SourceDocument.from_file(Path(tmp.name), 1, len(text.splitlines()))
    store = AnnotationStore()
    for module in order_modules(default_modules()):
        store.add(module, module.run(doc, SCENE_INPUT, store.view()))
    artifact = assemble(doc, SCENE_INPUT, store.view(), [], [], [])
    assert validate_parse_artifact_v2(artifact, doc.text) == []
    return artifact


def _entities(a: dict) -> dict:
    return {e["surface"]: e for e in a["declared_entities"]}


def _accepted(a: dict) -> set:
    return {e["surface"] for e in a["declared_entities"] if e["status"] != "REJECTED"}


def _speakers(a: dict) -> list:
    refs = {e["local_ref"]: e["surface"] for e in a["declared_entities"]}
    return [(refs.get(s["speaker_ref"]), sorted(refs[r] for r in s["alternatives"]), s["confidence"])
            for s in a["speech"]]


class TestGrammaticalEntities(unittest.TestCase):
    def test_g1_speech_tag_after_straight_closing_quote(self):
        a = _artifact('"The Pelagor survived," Vaelith summarized. "Transformed into something new."')
        self.assertIn("speech_tag_speaker", _entities(a)["Vaelith"]["notes"])
        self.assertEqual([s[0] for s in _speakers(a)], ["Vaelith", "Vaelith"])
        self.assertEqual([s[2] for s in _speakers(a)], [0.9, 0.75])

    def test_g2_subject_through_relative_clause(self):
        a = _artifact("Theron, whose consciousness specialized in temporal mechanics, "
                      "extended his awareness through the observation channels.")
        self.assertIn("grammatical_subject", _entities(a)["Theron"]["notes"])
        self.assertNotIn("Consciousness", _accepted(a))

    def test_g3_possessor_of_a_mind_noun_subject(self):
        a = _artifact("Mordain's consciousness resonated through the assembly one final time.")
        self.assertIn("possessor_of_subject", _entities(a)["Mordain"]["notes"])

    def test_g4_subject_and_listed_names(self):
        a = _artifact("Senareth had selected three Nephoretti—Elyraen for observation skills, "
                      "Vairis for practical thinking, and Kyreth, whose consciousness carried an unusual gift.")
        self.assertTrue({"Senareth", "Nephoretti", "Elyraen", "Vairis", "Kyreth"} <= _accepted(a))
        # Types are not inferred from prose in this phase: Nephoretti is a candidate, not typed a group.
        self.assertEqual(_entities(a)["Nephoretti"]["entity_type"], "unknown")

    def test_g5_inverted_tag(self):
        a = _artifact('"Three thousand years," said Mordain, whose consciousness maintained the archives.')
        self.assertEqual(_speakers(a)[0][0], "Mordain")

    def test_g6_pronoun_tag_stays_unresolved_without_gender_filter(self):
        a = _artifact("Lyaris watched the vrill currents. Theron listened beside her.\n\n"
                      '"The planetary core stabilizes," she observed.')
        speaker, alternatives, confidence = _speakers(a)[0]
        self.assertIsNone(speaker)
        self.assertTrue({"Lyaris", "Theron"} <= set(alternatives))
        self.assertEqual(confidence, 0.3)

    def test_g7_capitalised_non_names_rejected(self):
        a = _artifact('"Look," she said. Tomorrow we leave. Waves crashed against the rocks. '
                      "Understanding struck Zephyr like a physical force.")
        self.assertFalse({"Look", "Tomorrow", "Waves", "Understanding"} & _accepted(a))
        self.assertIn("Zephyr", _accepted(a))


class TestPresenceAndReferences(unittest.TestCase):
    def test_g8_physical_action_is_low_confidence_presence(self):
        torhh = _entities(_artifact("Torhh stood by the entrance."))["Torhh"]
        self.assertEqual((torhh["status"], torhh["presence"]), ("CANDIDATE", "present"))
        self.assertIn("physical", torhh["notes"])
        self.assertIn("low confidence", torhh["notes"])

    def test_g9_object_of_memory_is_referenced(self):
        self.assertEqual(_entities(_artifact("She remembered Torhh's laugh."))["Torhh"]["presence"], "referenced")

    def test_g10_speaking_and_being_mentioned_are_not_presence(self):
        a = _artifact('"Torhh would know," Kyreth said.')
        ents = _entities(a)
        self.assertEqual(ents["Kyreth"]["presence"], "unknown")      # communication only
        self.assertIn("communication", ents["Kyreth"]["notes"])
        self.assertEqual(ents["Torhh"]["presence"], "unknown")       # a mention inside dialogue
        self.assertEqual(_speakers(a)[0][0], "Kyreth")

    def test_g11_explicit_absence_and_simile(self):
        self.assertEqual(_entities(_artifact("Torhh was not there."))["Torhh"]["presence"], "absent")
        a = _artifact("Torhh walked along the ridge like a shadow.")
        self.assertEqual(_entities(a)["Torhh"]["presence"], "present")
        self.assertEqual(_accepted(a), {"Torhh"})

    def test_g12_unpaired_quotes_are_not_guessed(self):
        a = _artifact('"We wait, Senareth said, watching the tree line.')
        self.assertEqual(a["speech"], [])

    def test_g13_description_not_merged_into_a_named_entity(self):
        a = _artifact("Torhh and Kyreth stood near the shore. A jade-green Giant watched from the ridge.")
        self.assertIn("Giant", _accepted(a))
        self.assertFalse([x for x in a["alias_candidates"] if "Giant" in x["surface"]])


class TestMetadataAndContradictions(unittest.TestCase):
    PROSE = '"We should establish shelter," Vairis said. Torhh stood by the entrance.'

    def test_same_prose_result_with_and_without_yaml(self):
        bare = _artifact(self.PROSE)
        meta = _artifact(self.PROSE, 'scene: "001.1"\nparticipants: Vairis; Torhh')
        self.assertEqual([s[0] for s in _speakers(bare)], [s[0] for s in _speakers(meta)])
        self.assertTrue(_accepted(bare) <= _accepted(meta))

    def test_metadata_outranks_prose_and_conflict_is_flagged(self):
        a = _artifact(self.PROSE, 'scene: "001.1"\nparticipants: Vairis; Torhh (absent)')
        torhh = _entities(a)["Torhh"]
        self.assertEqual((torhh["evidence_class"], torhh["presence"]), ("AUTHOR_METADATA", "absent"))
        flags = [f for f in a["continuity_flags"] if f["subject_ref"] == torhh["local_ref"]]
        self.assertEqual(len(flags), 1)
        self.assertIn("metadata 'absent' vs prose", flags[0]["issue"])

    def test_prose_contradiction_is_kept_unresolved(self):
        a = _artifact("Torhh stood by the entrance. Torhh was not there.")
        self.assertEqual(_entities(a)["Torhh"]["presence"], "unknown")
        self.assertEqual(len(a["continuity_flags"]), 1)

    def test_quoted_term_is_not_speech(self):
        a = _artifact('Some resented their "liberation" as ingratitude.')
        self.assertEqual(a["speech"], [])


if __name__ == "__main__":
    unittest.main()
