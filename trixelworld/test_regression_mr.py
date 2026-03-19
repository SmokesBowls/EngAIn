#!/usr/bin/env python3
import sys
import subprocess
from pathlib import Path

def main():
    print("=== Trixel Engine Regression Harness ===")

    scripts = [
        "trixel_recipes_mr.py",
        "trixel_demo_mr.py",
        "engine_mr.py",
    ]

    expected_outputs = [
        Path("/tmp/trixel_demo/demo_beach_scene.png"),
        Path("/tmp/trixel_demo/demo_atmosphere_flare.png"),
        Path("/tmp/trixel_demo/demo_impressionist.png"),
    ]

    # Clean previous outputs
    for p in expected_outputs:
        if p.exists():
            p.unlink()

    for script in scripts:
        print(f"\n--- Running {script} ---")
        res = subprocess.run([sys.executable, script], capture_output=True, text=True)
        
        # We print stdout so we can see what happened
        print(res.stdout)
        if res.stderr:
            print("STDERR:", res.stderr, file=sys.stderr)

        if res.returncode != 0:
            print(f"\n[!] FAILED: {script} returned non-zero exit code {res.returncode}")
            sys.exit(1)

        # Fail if asset counts are zero
        if "shapes:          0" in res.stdout or "palettes:        0" in res.stdout:
            print(f"\n[!] FAILED: Asset counts are zero in {script}")
            sys.exit(1)

        # Check for build failures specifically out of recipes
        if "✗ MISSING ASSETS" in res.stdout:
            print(f"\n[!] FAILED: Critical named recipe failed to build in {script}")
            sys.exit(1)

    print("\n--- Checking Expected Outputs ---")
    missing = False
    for p in expected_outputs:
        if not p.exists():
            print(f"[!] FAILED: Expected output {p} is missing!")
            missing = True
        else:
            print(f"[✓] Found {p.name}")

    if missing:
        sys.exit(1)

    print("\n[✓] ALL REGRESSION CHECKS PASSED")

if __name__ == "__main__":
    main()
