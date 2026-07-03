import json
from pathlib import Path

from extraction.naive_temporal_extractor import NaiveTemporalExtractor
from reasoning.temporal_validator import TemporalValidator
from gates.temporal_gate import TemporalGate


OUTPUT_DIR = Path(
    "/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/scratch/game_proofs/proof_007_temporal_mvp"
)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    extractor = NaiveTemporalExtractor()
    validator = TemporalValidator()
    gate = TemporalGate()

    artifact = extractor.extract_gate_example()
    validation_result = validator.validate(artifact)
    verdict = gate.decide(artifact, validation_result)

    payload = {
        "proof": "Game Proof #007",
        "name": "TemporalArtifact MVP",
        "real_runtime_touched": False,
        "canon_written": False,
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
    }

    out_path = OUTPUT_DIR / "proof_007_temporal_mvp_result.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("PROOF_007_TEMPORAL_MVP_COMPLETE=TRUE")
    print(f"OUTPUT={out_path}")
    print(f"VERDICT={verdict.verdict}")
    print(f"CONSISTENT={validation_result.is_consistent}")
    print("REAL_RUNTIME_TOUCHED=FALSE")
    print("CANON_WRITTEN=FALSE")


if __name__ == "__main__":
    main()