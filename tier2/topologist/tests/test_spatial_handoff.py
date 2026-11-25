"""Operation B: Mettaext spatial signals -> Topologist artifact -> accepted packet."""
import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tier3/mettaext/passroom"))

from pass1_spatial import process_file  # noqa: E402
from tier2.topologist.artifactroom.passroom_signal_converter import convert_spatial_signals_to_artifact  # noqa: E402
from tier2.topologist.artifactroom.occupancy_evidence import apply_occupancy_evidence  # noqa: E402
from tier2.topologist.artifactroom.topology_artifact import ArtifactLifecycle  # noqa: E402
from tier2.topologist.reckoningroom.topology_validator import TopologyValidator  # noqa: E402
from tier2.topologist.gates.gate_accept_proposed_topology_artifact import evaluate_topology_artifact_for_acceptance  # noqa: E402

FIXTURE = "The guard stood before the stone gate.\nThe king approached the guard.\n"
SID = "scene.recovery.001"
GUARD, GATE, KING = f"{SID}.guard", f"{SID}.stone_gate", f"{SID}.king"


def fixture_artifact():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / "in.txt").write_text(FIXTURE, encoding="utf-8")
        subprocess.run([sys.executable, str(ROOT / "tier3/mettaext/passroom/pass1_explicit.py"),
                        str(tmp / "in.txt"), str(tmp / "explicit.txt")], check=True, capture_output=True)
        spatial = process_file(tmp / "explicit.txt", tmp / "spatial.json")
    return convert_spatial_signals_to_artifact(spatial, "topology.recovery.001", SID)


def submit_and_gate(artifact):
    proposed = replace(artifact, lifecycle=ArtifactLifecycle.PROPOSED)
    report = TopologyValidator().validate(proposed, proposed.to_dict()).to_dict()
    return report, evaluate_topology_artifact_for_acceptance(proposed.to_dict(), report)


class SpatialHandoff(unittest.TestCase):
    def test_fixture_reaches_accepted_packet_with_unknowns_preserved(self):
        art = fixture_artifact()
        self.assertEqual(art.lifecycle, ArtifactLifecycle.DRAFT)
        self.assertEqual(art.entity_ids(), [GUARD, GATE, KING])  # "before" not promoted
        self.assertEqual(len(art.olinks), 1)
        self.assertEqual(len(art.movelinks), 1)
        self.assertEqual(art.qslinks, [])
        report, gate = submit_and_gate(art)
        self.assertTrue(report["passed"])
        self.assertEqual(len(report["checks_run"]), 12)
        self.assertEqual(gate["decision"], "ACCEPTED")
        packet = gate["accepted_spatial_truth_packet"]
        for e in packet["entities"]:
            self.assertEqual((e["semantic_type"], e["pgt_envelope"]), ("unknown", None))

    def test_draft_and_unvalidated_cannot_be_accepted(self):
        art = fixture_artifact()
        report = TopologyValidator().validate(art).to_dict()
        self.assertEqual(evaluate_topology_artifact_for_acceptance(art.to_dict(), report)["decision"], "REJECTED")


class OccupancyEvidence(unittest.TestCase):
    def setUp(self):
        self.art = fixture_artifact()

    def test_cited_and_provisional_envelopes_are_distinguishable(self):
        out = apply_occupancy_evidence(self.art, {
            GUARD: {"semantic_type": "person", "semantic_evidence": "The guard stood",
                    "occupancy_class": "human_standard", "occupancy_basis": "provisional",
                    "provisional_reason": "manuscript does not state the guard's build"},
            GATE: {"semantic_type": "structure", "semantic_evidence": "the stone gate"},
        })
        by_id = {e.entity_id: e for e in out.entities}
        g = by_id[GUARD].pgt_envelope
        self.assertEqual((g["h"], g["w"], g["d"], g["basis"]), (10, 4, 3, "provisional"))
        self.assertEqual(g["policy_id"], "PGT_SCALE_POLICY_v0.1")
        self.assertNotIn("evidence_ref", g)
        # structure typed but no dimensions invented
        self.assertEqual((by_id[GATE].semantic_type.value, by_id[GATE].pgt_envelope), ("structure", None))
        # no record -> stays unknown
        self.assertEqual((by_id[KING].semantic_type.value, by_id[KING].pgt_envelope), ("unknown", None))
        report, gate = submit_and_gate(out)
        self.assertTrue(report["passed"], report)
        self.assertEqual(gate["decision"], "ACCEPTED")

    def test_evidence_basis_requires_citation_from_source(self):
        rec = {"semantic_type": "person", "semantic_evidence": "The king approached",
               "occupancy_class": "human_standard", "occupancy_basis": "evidence",
               "occupancy_evidence": "The king was a tall man"}  # not in the manuscript
        with self.assertRaises(ValueError):
            apply_occupancy_evidence(self.art, {KING: rec})
        rec["occupancy_evidence"] = "The king approached the guard."
        env = apply_occupancy_evidence(self.art, {KING: rec}).entities[2].pgt_envelope
        self.assertEqual((env["basis"], env["evidence_ref"]), ("evidence", "The king approached the guard."))

    def test_refusals(self):
        bad = [
            {GUARD: {"semantic_type": "person"}},                                   # uncited type
            {GATE: {"semantic_type": "structure", "semantic_evidence": "stone gate",
                    "occupancy_class": "human_standard", "occupancy_basis": "provisional",
                    "provisional_reason": "x"}},                                    # class/type mismatch
            {GUARD: {"semantic_type": "person", "semantic_evidence": "guard",
                     "occupancy_class": "human_standard", "occupancy_basis": "provisional"}},  # no reason
            {GUARD: {"semantic_type": "person", "semantic_evidence": "guard",
                     "occupancy_class": "ogre", "occupancy_basis": "provisional",
                     "provisional_reason": "x"}},                                   # not in policy
            {f"{SID}.before": {"semantic_type": "unknown"}},                       # not an entity
        ]
        for records in bad:
            with self.subTest(records=records), self.assertRaises(ValueError):
                apply_occupancy_evidence(self.art, records)
        with self.assertRaises(ValueError):
            apply_occupancy_evidence(replace(self.art, lifecycle=ArtifactLifecycle.PROPOSED), {})


if __name__ == "__main__":
    unittest.main()
