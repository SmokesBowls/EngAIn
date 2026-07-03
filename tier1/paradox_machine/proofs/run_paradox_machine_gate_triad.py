import json
import subprocess
import sys
from pathlib import Path


OUTPUT_DIR = Path(
    "/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/scratch/game_proofs/paradox_machine_gate_triad"
)

PROOFS = [
    {
        "name": "game_proof_007",
        "module": "proofs.proof_007_temporal_mvp",
        "expected_verdict": "ACCEPTED",
    },
    {
        "name": "game_proof_007b",
        "module": "proofs.proof_007b_temporal_rejection",
        "expected_verdict": "REJECTED",
    },
    {
        "name": "game_proof_008",
        "module": "proofs.proof_008_spatiotemporal_gate_stub",
        "expected_verdict": "SUSPENDED",
    },
]


def run_proof(module_name: str) -> dict:
    result = subprocess.run(
        [sys.executable, "-m", module_name],
        capture_output=True,
        text=True,
        check=False,
    )

    return {
        "module": module_name,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "passed_process": result.returncode == 0,
    }


def extract_verdict(stdout: str) -> str:
    for line in stdout.splitlines():
        if line.startswith("VERDICT="):
            return line.split("=", 1)[1].strip()
    return "UNKNOWN"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    proof_results = []

    for proof in PROOFS:
        run_result = run_proof(proof["module"])
        actual_verdict = extract_verdict(run_result["stdout"])

        proof_passed = (
            run_result["passed_process"]
            and actual_verdict == proof["expected_verdict"]
            and "REAL_RUNTIME_TOUCHED=FALSE" in run_result["stdout"]
            and "CANON_WRITTEN=FALSE" in run_result["stdout"]
        )

        proof_results.append(
            {
                "name": proof["name"],
                "module": proof["module"],
                "expected_verdict": proof["expected_verdict"],
                "actual_verdict": actual_verdict,
                "passed": proof_passed,
                "process": run_result,
            }
        )

    triad_passed = all(item["passed"] for item in proof_results)

    payload = {
        "proof": "Paradox Machine Gate Triad",
        "status": "PASS" if triad_passed else "FAIL",
        "real_runtime_touched": False,
        "canon_written": False,
        "proof_results": proof_results,
    }

    out_path = OUTPUT_DIR / "paradox_machine_gate_triad_result.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("PARADOX_MACHINE_GATE_TRIAD_RUNNER_COMPLETE=TRUE")
    print(f"OUTPUT={out_path}")
    print(f"STATUS={payload['status']}")
    print("REAL_RUNTIME_TOUCHED=FALSE")
    print("CANON_WRITTEN=FALSE")

    if not triad_passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
