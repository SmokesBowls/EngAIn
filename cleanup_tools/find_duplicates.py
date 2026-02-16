#!/usr/bin/env python3
import os
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = REPO_ROOT / "cleanup_reports"

directories = [
    "godotengain/engainos/core",
    "godotsim",
    "core"
]

def find_duplicates():
    module_map = defaultdict(list)

    for root_dir in directories:
        full_root = REPO_ROOT / root_dir
        if not full_root.exists():
            continue
        for root, dirs, files in os.walk(str(full_root)):
            if "__pycache__" in root:
                continue
            for file in files:
                if file.endswith(".py"):
                    rel_path = os.path.relpath(os.path.join(root, file), str(REPO_ROOT))
                    module_map[file].append(rel_path)

    duplicates = {name: paths for name, paths in module_map.items() if len(paths) > 1}

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    with open(str(REPORT_DIR / "duplicate-modules.txt"), "w") as f:
        for name, paths in sorted(duplicates.items()):
            f.write(f"{name}\n")
            for path in sorted(paths):
                f.write(f"  {path}\n")
            f.write("\n")
    
    print(f"Wrote duplicate report to {REPORT_DIR / 'duplicate-modules.txt'}")

if __name__ == "__main__":
    find_duplicates()
