from pathlib import Path

from zwcodecs.json_to_zw import json_file_to_zw_file


INPUT_PATH = Path(
    "/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/scratch/game_proofs/paradox_machine_gate_triad/paradox_machine_gate_triad_result.json"
)

OUTPUT_PATH = Path(
    "/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/scratch/game_proofs/paradox_machine_gate_triad/paradox_machine_gate_triad_result.zw.txt"
)


def main() -> None:
    if not INPUT_PATH.exists():
        print("GATE_TRIAD_JSON_FOUND=FALSE")
        print(f"MISSING_PATH={INPUT_PATH}")
        raise SystemExit(1)

    json_file_to_zw_file(str(INPUT_PATH), str(OUTPUT_PATH))

    print("GATE_TRIAD_ZW_EXPORT_COMPLETE=TRUE")
    print(f"INPUT={INPUT_PATH}")
    print(f"OUTPUT={OUTPUT_PATH}")
    print("REAL_RUNTIME_TOUCHED=FALSE")
    print("CANON_WRITTEN=FALSE")


if __name__ == "__main__":
    main()
