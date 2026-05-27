#!/usr/bin/env python3
"""
Scaffold script for EngAIn/engain/ package structure.
Production-grade, idempotent, and cross-platform safe.
Run from the repository root: /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn
"""
from pathlib import Path
import sys

# Target directory relative to repo root
BASE_DIR = Path("engain")

STRUCTURE = [
    "__init__.py",
    "runtime/__init__.py",
    "runtime/sim.py",
    "semantic/__init__.py",
    "semantic/extraction.py",
    "render/__init__.py",
    "render/trixel.py",
    "world/__init__.py",
    "world/field.py",
    "kernels/__init__.py",
    "kernels/spatial.py",
    "kernels/perception.py",
    "kernels/navigation.py",
]

def scaffold() -> None:
    if not BASE_DIR.is_absolute():
        BASE_DIR.parent.mkdir(parents=True, exist_ok=True)
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    print(f"📁 Ensuring base directory: {BASE_DIR.resolve()}")

    for rel_path in STRUCTURE:
        file_path = BASE_DIR / rel_path
        dir_path = file_path.parent

        dir_path.mkdir(parents=True, exist_ok=True)

        if file_path.exists():
            print(f"⏭️  Skipped (exists): {file_path}")
            continue

        # Safe, minimal placeholder content
        module_name = rel_path.replace("/", ".").replace(".py", "")
        placeholder = f"# EngAIn.engain.{module_name} module\n"
        file_path.write_text(placeholder, encoding="utf-8")
        print(f"✅ Created: {file_path}")

    print("\n✨ Scaffolding complete.")

if __name__ == "__main__":
    try:
        scaffold()
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)