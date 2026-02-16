#!/usr/bin/env python3
import os
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ROOT_TO_SCAN = REPO_ROOT / "godotengain/engainos"
REPORT_DIR = REPO_ROOT / "cleanup_reports"

ENTRYPOINTS = {
    "launch_engine.py",
    "engainos_server.py",
    "runtime_api.py",
    "runtime_client.py",
    "inspect_godot_adapter.py",
    "check_boundaries_precise.py",
}

# Dynamically find all trace files
TRACE_FILES = list(REPORT_DIR.glob("import-trace-*.json"))

def find_unused():
    # 1. Collect all modules from traces
    used_by_traces = set()
    for tf in TRACE_FILES:
        if tf.exists():
            try:
                data = json.loads(tf.read_text(encoding="utf-8"))
                for item in data.get("imported_files", []):
                    path = item.get("path")
                    if path:
                        used_by_traces.add(os.path.normpath(path))
            except Exception as e:
                print(f"Warning: could not read {tf}: {e}")

    # 2. Collect all .py files in canonical root
    all_py_files = []
    for root, dirs, files in os.walk(str(ROOT_TO_SCAN)):
        if "__pycache__" in root:
            continue
        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, str(REPO_ROOT))
                all_py_files.append(os.path.normpath(rel_path))

    # 3. Static scan for imports
    # We'll look for both absolute and relative imports
    imported_names = set()
    for py_file in all_py_files:
        try:
            with open(os.path.join(str(REPO_ROOT), py_file), "r") as f:
                content = f.read()
                # matches: import name, from name import ...
                matches = re.findall(r"^\s*(?:import|from)\s+([a-zA-Z0-9_\.]+)", content, re.MULTILINE)
                for m in matches:
                    imported_names.add(m.split(".")[0])
        except:
            pass

    # 4. Scan Godot files
    godot_refs = set()
    for root, dirs, files in os.walk(str(ROOT_TO_SCAN)):
        for file in files:
            if file.endswith((".gd", ".tscn")):
                try:
                    with open(os.path.join(root, file), "r") as f:
                        content = f.read()
                        for py_file in all_py_files:
                            name = os.path.splitext(os.path.basename(py_file))[0]
                            # Look for the filename in Godot scripts/scenes
                            if name in content:
                                godot_refs.add(py_file)
                except:
                    pass

    # 5. Determine unused
    unused_candidates = []
    for py_file in all_py_files:
        basename = os.path.basename(py_file)
        name = os.path.splitext(basename)[0]
        
        is_trace_used = py_file in used_by_traces
        is_entrypoint = basename in ENTRYPOINTS or basename.startswith("test_")
        is_statically_imported = name in imported_names
        is_godot_ref = py_file in godot_refs
        
        if not (is_trace_used or is_entrypoint or is_statically_imported or is_godot_ref):
            reasons = []
            if not is_trace_used: reasons.append("no-trace")
            if not is_statically_imported: reasons.append("no-static-imports")
            if not is_godot_ref: reasons.append("no-godot-refs")
            if not is_entrypoint: reasons.append("not-entrypoint")
            
            unused_candidates.append({
                "path": py_file,
                "reasons": reasons
            })

    # Write output
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    with open(str(REPORT_DIR / "unused-candidates.txt"), "w") as f:
        for cand in sorted(unused_candidates, key=lambda x: x["path"]):
            f.write(f"path: {cand['path']}\n")
            f.write(f"reason flags: {', '.join(cand['reasons'])}\n\n")
    
    print(f"Wrote {len(unused_candidates)} unused candidates to {REPORT_DIR / 'unused-candidates.txt'}")

if __name__ == "__main__":
    find_unused()
