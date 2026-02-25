#!/usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path

def run(cmd):
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True)

def main():
    in_file = Path("03_Fist_contact.txt")
    if not in_file.exists():
        print(f"ERROR: missing input file: {in_file.resolve()}")
        sys.exit(1)

    base = in_file.stem

    run([sys.executable, "pass1_explicit.py", str(in_file)])

    # find pass1 output wherever it wrote it
    candidates = list(Path(".").rglob(f"out_pass1_{base}.txt"))
    if not candidates:
        print(f"FAIL: Pass1 did not produce out_pass1_{base}.txt under {Path('.').resolve()}")
        sys.exit(1)
    p1 = candidates[0]
    print("Using Pass1 output:", p1)

    run([sys.executable, "pass2_core.py", str(p1)])

    p2_local = p1.parent / f"out_pass2_{base}.metta"
    p2_cwd = Path(f"out_pass2_{base}.metta")
    p2 = p2_local if p2_local.exists() else p2_cwd
    print("Using Pass2 output:", p2)

    run([sys.executable, "pass3_merge.py", str(p1), str(p2)])

    zonj_local = p1.parent / f"zonj_{base}.json"
    zonj_cwd = Path(f"zonj_{base}.json")
    zonj = zonj_local if zonj_local.exists() else zonj_cwd
    if not zonj.exists():
        print(f"FAIL: Pass3 did not produce {zonj_local} or {zonj_cwd}")
        sys.exit(1)
    print("Using Pass3 output (zonj):", zonj)

    run([sys.executable, "pass4_zon_bridge.py", str(zonj),
         "--era", "FirstAge", "--location", "Beach", "--output-dir", "out"])

    print(f"OK: wrote out/{base}.zon and out/{base}.zonj.json")

if __name__ == "__main__":
    main()
