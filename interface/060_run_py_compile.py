#!/usr/bin/env python3
"""
Run py_compile against one Python target.
This is a safe validation command.
"""

from __future__ import annotations

import argparse

from interface_common import append_ledger, print_process_result, repo_path, run_command


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True, help="Python file to compile")
    args = parser.parse_args()

    target = repo_path(args.target)

    print("RUNNING_PY_COMPILE")
    print(f"TARGET={target}")

    result = run_command(["python3", "-m", "py_compile", str(target)])
    print_process_result(result)

    append_ledger(
        {
            "event": "py_compile",
            "target": args.target,
            "exit_code": result.returncode,
            "passed": result.returncode == 0,
        }
    )

    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
