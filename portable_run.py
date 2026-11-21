#!/usr/bin/env python3
"""Launch a Python module from a project that may be moved to another folder.

Place this file at the *project root* alongside folders such as src/, tier1/,
or the application's top-level Python package.

Usage:
    python portable_run.py package.module [module arguments...]
    python portable_run.py main

Only the project's location is made portable. This does not install dependencies,
rewrite imports, or repair hard-coded absolute paths.
"""

from pathlib import Path
import os
import runpy
import sys


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print("Usage: python portable_run.py package.module [arguments...]", file=sys.stderr)
        print("Example: python portable_run.py mypackage.main", file=sys.stderr)
        raise SystemExit(0 if len(sys.argv) > 1 else 2)

    module_name = sys.argv[1]
    if module_name.endswith(".py") or "/" in module_name or "\\" in module_name:
        raise SystemExit("Pass a dotted Python module name (such as app.main), not a file path.")

    root = Path(__file__).resolve().parent

    # Every time this file moves with the project, the paths below move too.
    # Add the root first, then src/ so a conventional src/ package takes priority.
    for base in (root, root / "src"):
        if base.is_dir():
            value = str(base)
            if value in sys.path:
                sys.path.remove(value)
            sys.path.insert(0, value)

    # Legacy projects often open relative data/configuration files from the root.
    os.chdir(root)

    # Forward extra command-line arguments to the selected entry module.
    sys.argv = [module_name, *sys.argv[2:]]
    runpy.run_module(module_name, run_name="__main__", alter_sys=True)


if __name__ == "__main__":
    main()
