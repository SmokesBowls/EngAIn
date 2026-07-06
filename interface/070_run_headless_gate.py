#!/usr/bin/env python3
"""
Run a GodotSim gate in headless mode.
This command only runs Python gate files.
"""

from __future__ import annotations

import argparse
import os
import subprocess

from interface_common import REPO_ROOT, append_ledger, print_process_result, repo_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True, help="Gate Python file to run")
    args = parser.parse_args()

    target = repo_path(args.target)

    command = ["python3", str(target), "--headless"]

    env = dict(os.environ)
    env["PYTHONPATH"] = "."

    print("RUNNING_HEADLESS_GATE")
    print(f"TARGET={target}")
    print(f"COMMAND={' '.join(command)}")

    result = subprocess.run(
        command,
        cwd=str(REPO_ROOT),
        env=env,
        text=True,
        capture_output=True,
    )

    print_process_result(result)

    append_ledger(
        {
            "event": "headless_gate",
            "target": args.target,
            "exit_code": result.returncode,
            "passed": result.returncode == 0,
            "stdout_excerpt": result.stdout[-3000:],
            "stderr_excerpt": result.stderr[-3000:],
        }
    )

    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
