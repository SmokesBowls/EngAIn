"""Unit tests for Gen2 libraries and modules on synthetic scenes (no vault needed)."""

from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from tier3.mettaextgen2.lib.annotations import (
    AnnotationStore, ModuleOutput, NewAnnotation, SceneInput,
)
from tier3.mettaextgen2.lib.artifact_schema import validate_parse_artifact_v2
from tier3.mettaextgen2.lib.lane_line import find_forbidden
from tier3.mettaextgen2.lib.source import SourceDocument, SpanError
from tier3.mettaextgen2.modules.artifact_assembler import assemble
from tier3.mettaextgen2.modules.entity_extractor import EntityExtractor
from tier3.mettaextgen2.modules.linguistic_annotator import LinguisticAnnotator
from tier3.mettaextgen2.modules.metadata_reader import MetadataReader, classify
from tier3.mettaextgen2.modules.presence_detector import PresenceDetector, classify_qualifier
from tier3.mettaextgen2.modules.reconciler import Reconciler
from tier3.mettaextgen2.modules.scene_segmenter import SceneSegmenter
from tier3.mettaextgen2.orchestrator import default_modules, order_modules

SCENE = (
    "### scene 001.2 — test scene\n"
    "```yaml\n"
    "scene meta:\n"
    "  location: Old Mill / Ashford Bridge\n"
    "  participants: Corin; Talia (memory only); Nine Wardens (remote watchers only)\n"
    "  Zaron state: no death, dormancy, or merger is inferred\n"
    "  Key state: custody unresolved\n"
    "  time: Y12 M3 D4, editorial placement\n"
    "  focus: Corin recalls Brannoc.\n"
    "```\n"
    "ACT 2: THE MILL\n"
    "\n"
    "Three days later, at Talia’s grave, Corin waited by the Old Mill.\n"
    "“Talia. Of course,” Corin said. Teachers. Protectors.\n"
    "Brannoc was a warning. Dorran was another. The Nine Wardens watched from Ashford Bridge.\n"
)
SCENE_INPUT = SceneInput(
    chapter_id="chapter.book001.001_test", chapterroom_scene_id="scene.book001.001_test.scene002",
    source_scene_label="001.2", source_scene_title="test scene", boundary_method="authored_scene_marker",
    authored_scene_boundaries_proven=True, packet_path="(synthetic)",
)


def _doc(text: str = SCENE) -> SourceDocument:
    tmp = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8")
    tmp.write(text)
    tmp.close()
    return SourceDocument.from_file(Path(tmp.name), 1, len(text.splitlines()))


def _run(doc: SourceDocument):
    store = AnnotationStore()
    for module in order_modules(default_modules()):
        store.add(module, module.run(doc, SCENE_INPUT, store.view()))
    return store


class TestSource(unittest.TestCase):
    def test_span_text_is_raw_slice_and_line_is_correct(self):
        doc = _doc()
        start = doc.text.index("Corin waited")
        span = doc.span(start, start + 5)
        self.assertEqual(span.text, "Corin")
        self.assertEqual(span.line, doc.text[:start].count("\n") + 1)
        self.assertEqual(doc.line_text(span.line).split(",")[0], "Three days later")

    def test_blank_and_out_of_region_spans_refused(self):
        doc = SourceDocument.from_file(_doc().path, 11, 12)
        with self.assertRaises(SpanError):
            doc.span(0, 5)  # before region
        blank = doc.text.index("\n\nThree") + 1
        with self.assertRaises(SpanError):
            doc.span(blank - 1, blank)


class TestStoreContract(unittest.TestCase):
    def test_undeclared_kind_rejected_atomically(self):
        doc = _doc()
        store = AnnotationStore()
        module = SceneSegmenter()
        out = ModuleOutput(annotations=[
            NewAnnotation("region", doc.line_span(1), {"region_type": "scene_header"}),
            NewAnnotation("entity_mention", doc.line_span(1), {}),
        ])
        with self.assertRaises(ValueError):
            store.add(module, out)
        self.assertEqual(store.view().all(), ())

    def test_values_are_frozen(self):
        doc = _doc()
        store = AnnotationStore()
        store.add(SceneSegmenter(), ModuleOutput([NewAnnotation("region", doc.line_span(1), {"region_type": "x"})]))
        with self.assertRaises(TypeError):
            store.view().all()[0].value["region_type"] = "y"


class TestModules(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = _doc()
        cls.store = _run(cls.doc)
        cls.view = cls.store.view()

    def _kinds(self, kind):
        return self.view.by_kind(kind)

    def test_structure_not_tokenised(self):
        surfaces = {t.value["surface"] for t in self._kinds("token")}
        self.assertNotIn("ACT", surfaces)
        self.assertFalse(surfaces & {"Old", "Mill"} - {"Old", "Mill"})  # only from prose
        self.assertNotIn("Zaron", surfaces)   # yaml never tokenised as prose
        self.assertNotIn("Key", surfaces)

    def test_metadata_kinds(self):
        kinds = {(c.value["key"], c.value["kind"]) for c in self._kinds("metadata_constraint")}
        self.assertIn(("Zaron state", "non_inference"), kinds)
        self.assertIn(("Key state", "unresolved_state"), kinds)
        self.assertIn(("time", "editorial_placement"), kinds)
        participants = [c.value for c in self._kinds("metadata_constraint") if c.value["kind"] == "presence_qualifier"]
        self.assertEqual([(p["subject"], p["qualifier"]) for p in participants],
                         [("Corin", None), ("Talia", "memory only"), ("Nine Wardens", "remote watchers only")])
        talia = next(c for c in self._kinds("metadata_constraint") if c.value.get("subject") == "Talia")
        self.assertEqual(talia.span.text, "Talia (memory only)")

    def test_rejections_and_mentions(self):
        rejected = {r.value["surface"]: r.value["reason"] for r in self._kinds("entity_rejection")}
        self.assertEqual(rejected.get("Three"), "number_word")
        self.assertEqual(rejected.get("Teachers"), "initial_capital_only")
        self.assertEqual(rejected.get("Protectors"), "initial_capital_only")
        # A name seen only sentence-initially, with no other evidence, is indistinguishable
        # from "Teachers." and is rejected (documented, conservative).
        self.assertEqual(rejected.get("Dorran"), "initial_capital_only")
        brannoc = next(m for m in self._kinds("entity_mention") if m.value["surface"] == "Brannoc")
        self.assertEqual(brannoc.value["basis"], "corroborated_by_metadata_text")
        prose = {m.value["surface"] for m in self._kinds("entity_mention") if m.value["evidence_class"] == "PROSE"}
        self.assertTrue({"Talia", "Corin", "Nine Wardens", "Brannoc", "Ashford Bridge", "Old Mill"} <= prose)
        self.assertNotIn("The", prose)

    def test_reconciled_presence_and_locations(self):
        ents = {e.value["surface"]: e for e in self._kinds("reconciled_entity")}
        self.assertEqual(ents["Corin"].value["presence"], "present")
        self.assertEqual(ents["Talia"].value["presence"], "referenced")
        self.assertEqual(ents["Nine Wardens"].value["presence"], "referenced")
        self.assertEqual(ents["Nine Wardens"].value["entity_type"], "group")
        self.assertEqual(ents["Brannoc"].value["status"], "CANDIDATE")
        self.assertEqual(ents["Brannoc"].value["presence"], "unknown")
        self.assertEqual(ents["Three"].value["status"], "REJECTED")
        self.assertEqual(ents["Dorran"].value["status"], "REJECTED")
        locs = {l.value["surface"] for l in self._kinds("reconciled_location")}
        self.assertEqual(locs, {"Old Mill", "Ashford Bridge"})
        self.assertNotIn("Old Mill", ents)

    def test_assembled_artifact_validates_and_is_deterministic(self):
        a1 = assemble(self.doc, SCENE_INPUT, self.view, [{"name": "x", "version": "0", "implementation_kind": "rules"}], [], [])
        a2 = assemble(self.doc, SCENE_INPUT, _run(self.doc).view(), [{"name": "x", "version": "0", "implementation_kind": "rules"}], [], [])
        self.assertEqual(json.dumps(a1, sort_keys=True), json.dumps(a2, sort_keys=True))
        self.assertEqual(validate_parse_artifact_v2(a1, self.doc.text), [])


class TestNonPlainLocation(unittest.TestCase):
    """Regression (corpus run 2026-10-06, scene 055.4): a block-scalar `location:`
    reached the reconciler with no subject and crashed it, silently emptying the
    artifact's entities."""

    def test_block_scalar_location_does_not_break_reconciler(self):
        text = ("### scene 001.1 — block location\n```yaml\nlocation: >-\n  Old Mill\n"
                "participants: Corin\n```\nCorin waited by the Old Mill.\n")
        doc = _doc(text)
        store = _run(doc)
        locs = [l.value["surface"] for l in store.view().by_kind("reconciled_location")]
        ents = [e.value["surface"] for e in store.view().by_kind("reconciled_entity")]
        self.assertEqual(locs, ["Old Mill"])
        self.assertIn("Corin", ents)


class TestValidatorAndLaneLine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = _doc()
        cls.artifact = assemble(cls.doc, SCENE_INPUT, _run(cls.doc).view(),
                                [{"name": "x", "version": "0", "implementation_kind": "rules"}], [], [])

    def _errors(self, mutate):
        a = copy.deepcopy(self.artifact)
        mutate(a)
        return validate_parse_artifact_v2(a, self.doc.text)

    def test_forbidden_keys_anywhere(self):
        self.assertEqual(find_forbidden({"a": [{"b": {"affect_state": 1}}]}), ["$.a[0].b.affect_state"])
        self.assertTrue(self._errors(lambda a: a["declared_entities"][0].update(position=[0, 0, 0])))
        self.assertTrue(self._errors(lambda a: a["declared_entities"][0].update(spawnable=True)))
        self.assertTrue(self._errors(lambda a: a.update(terrain_profile="beach")))

    def test_tampered_span_text_rejected(self):
        errs = self._errors(lambda a: a["declared_entities"][0]["source_span"].update(text="Nobody"))
        self.assertTrue(any("does not match raw source" in e for e in errs))

    def test_authority_fields_rejected(self):
        self.assertTrue(self._errors(lambda a: a["scene"].update(runtime_stage_id="scene.book001.chapter001.stage002")))
        self.assertTrue(self._errors(lambda a: a.update(canon_claims=[{"x": 1}])))
        self.assertTrue(self._errors(lambda a: a["alias_candidates"].append(
            {"surface": "x", "candidate_ref": "ent_999", "scope": "global", "status": "COMMITTED",
             "evidence": [], "confidence": 0.5, "alternatives": []})))


class TestClassifiers(unittest.TestCase):
    def test_presence_qualifiers(self):
        self.assertEqual(classify_qualifier(None), "present")
        self.assertEqual(classify_qualifier("grave and memory only"), "referenced")
        self.assertEqual(classify_qualifier("remote/interstitial watchers only"), "referenced")
        self.assertEqual(classify_qualifier("absent"), "absent")
        self.assertEqual(classify_qualifier("damaged manifested form"), "unknown")

    def test_metadata_classification_priority(self):
        self.assertEqual(classify("Zaron state", "no death, dormancy, merger, departure, or reintegration is inferred"), "non_inference")
        self.assertEqual(classify("Oreck state", "Does not return; fate unknown, not established dead."), "non_inference")
        self.assertEqual(classify("Key state", "custody unresolved"), "unresolved_state")
        self.assertEqual(classify("time", "Y17,511 M6 D22"), "editorial_placement")
        self.assertEqual(classify("focus", "Geralt reports"), "assertion")


class TestOrchestration(unittest.TestCase):
    def test_dag_order_respects_requires(self):
        names = [m.name for m in order_modules(default_modules())]
        self.assertLess(names.index("scene_segmenter"), names.index("metadata_reader"))
        self.assertLess(names.index("metadata_reader"), names.index("entity_extractor"))
        self.assertLess(names.index("linguistic_annotator"), names.index("entity_extractor"))
        self.assertEqual(names[-1], "reconciler")

    def test_missing_producer_is_an_error(self):
        with self.assertRaises(ValueError):
            order_modules([EntityExtractor()])


if __name__ == "__main__":
    unittest.main()
