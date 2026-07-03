import json
from pathlib import Path


RESULT_PATH = Path(
    "/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/scratch/game_proofs/paradox_machine_gate_triad/paradox_machine_gate_triad_result.json"
)


def main() -> None:
    if not RESULT_PATH.exists():
        print("PARADOX_MACHINE_GATE_TRIAD_RESULT_FOUND=FALSE")
        print(f"MISSING_PATH={RESULT_PATH}")
        raise SystemExit(1)

    payload = json.loads(RESULT_PATH.read_text(encoding="utf-8"))

    print("PARADOX_MACHINE_GATE_TRIAD_RESULT_FOUND=TRUE")
    print(f"RESULT_PATH={RESULT_PATH}")
    print(f"STATUS={payload.get('status', 'UNKNOWN')}")
    print(f"REAL_RUNTIME_TOUCHED={str(payload.get('real_runtime_touched')).upper()}")
    print(f"CANON_WRITTEN={str(payload.get('canon_written')).upper()}")

    print("")
    print("PROOF_RESULTS:")

    for proof in payload.get("proof_results", []):
        print(
            f"- {proof.get('name')}: "
            f"expected={proof.get('expected_verdict')} "
            f"actual={proof.get('actual_verdict')} "
            f"passed={proof.get('passed')}"
        )


if __name__ == "__main__":
    main()
