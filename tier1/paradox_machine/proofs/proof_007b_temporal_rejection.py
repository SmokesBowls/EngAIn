import json
from pathlib import Path

from schemas.temporal_artifact import (
    ProseTemporalArtifact,
    TemporalEvent,
    TemporalLink,
)
from reasoning.temporal_validator import TemporalValidator
from gates.temporal_gate import TemporalGate


OUTPUT_DIR = Path(
    "/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/scratch/game_proofs/proof_007b_temporal_rejection"
)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    artifact = ProseTemporalArtifact(
        artifact_id="proof_007b_temporal_rejection_example",
        source_text=(
            "The guard closed the gate before the player approached. "
            "The player approached before the guard closed the gate."
        ),
    )

    artifact.events.extend(
        [
            TemporalEvent(
                event_id="e1",
                text="guard closed gate",
                event_type="OCCURRENCE",
                source_sentence_index=0,
                discourse_order=1,
            ),
            TemporalEvent(
                event_id="e2",
                text="player approached",
                event_type="OCCURRENCE",
                source_sentence_index=0,
                discourse_order=2,
            ),
        ]
    )

    artifact.tlinks.extend(
        [
            TemporalLink(
                link_id="l1",
                source_id="e1",
                target_id="e2",
                rel_type="BEFORE",
            ),
            TemporalLink(
                link_id="l2",
                source_id="e2",
                target_id="e1",
                rel_type="BEFORE",
            ),
        ]
    )

    artifact.syuzhet_order = ["e1", "e2"]
    artifact.fabula_order_hint = ["CONTRADICTION_EXPECTED"]

    validator = TemporalValidator()
    gate = TemporalGate()

    validation_result = validator.validate(artifact)
    verdict = gate.decide(artifact, validation_result)

    payload = {
        "proof": "Game Proof #007b",
        "name": "Temporal Rejection Path",
        "real_runtime_touched": False,
        "canon_written": False,
        "expected_verdict": "REJECTED",
        "artifact": artifact.to_dict(),
        "validation_result": {
            "is_consistent": validation_result.is_consistent,
            "issues": [issue.__dict__ for issue in validation_result.issues],
            "normalized_relations": {
                f"{source}->{target}": relation
                for (source, target), relation in validation_result.normalized_relations.items()
            },
        },
        "gate_verdict": verdict.__dict__,
        "pass": verdict.verdict == "REJECTED" and validation_result.is_consistent is False,
    }

    out_path = OUTPUT_DIR / "proof_007b_temporal_rejection_result.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("PROOF_007B_TEMPORAL_REJECTION_COMPLETE=TRUE")
    print(f"OUTPUT={out_path}")
    print(f"VERDICT={verdict.verdict}")
    print(f"CONSISTENT={validation_result.is_consistent}")
    print(f"PASS={payload['pass']}")
    print("REAL_RUNTIME_TOUCHED=FALSE")
    print("CANON_WRITTEN=FALSE")


if __name__ == "__main__":
    main()
