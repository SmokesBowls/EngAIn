#!/usr/bin/env python3
import sys
import os
import json
import subprocess
import signal
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = REPO_ROOT / "cleanup_reports"

def get_repo_class(path):
    rel_path = os.path.relpath(path, str(REPO_ROOT))
    if rel_path.startswith("godotengain/engainos"):
        return "engainos"
    if rel_path.startswith("godotsim"):
        return "godotsim"
    if rel_path.startswith("core"):
        return "core"
    return "other"

def trace_entrypoint(entrypoint_path, output_json):
    print(f"Tracing {entrypoint_path}...")
    
    trace_script = f"""
import sys
import os
import json
import time
import signal
import importlib.util

REPO_ROOT = {repr(str(REPO_ROOT))}

def get_repo_class(path):
    rel_path = os.path.relpath(path, REPO_ROOT)
    if rel_path.startswith("godotengain/engainos"):
        return "engainos"
    if rel_path.startswith("godotsim"):
        return "godotsim"
    if rel_path.startswith("core"):
        return "core"
    return "other"

def dump_modules(ok_val=True):
    final_modules = sys.modules.copy()
    imported_repo_files = []
    counts = {{"engainos": 0, "godotsim": 0, "core": 0, "other": 0}}

    for name, mod in final_modules.items():
        if mod and hasattr(mod, "__file__") and mod.__file__:
            file_path = os.path.abspath(mod.__file__)
            if file_path.startswith(REPO_ROOT):
                rel_path = os.path.relpath(file_path, REPO_ROOT)
                cls = get_repo_class(file_path)
                imported_repo_files.append({{"name": name, "path": rel_path, "class": cls}})
                counts[cls] += 1

    result = {{
        "entrypoint": {repr(entrypoint_path)},
        "ok": ok_val,
        "counts": counts,
        "imported_files": sorted(imported_repo_files, key=lambda x: x["path"])
    }}
    with open("trace_temp.json", "w") as f:
        json.dump(result, f, indent=2)

def signal_handler(signum, frame):
    dump_modules(ok_val=True) # Terminated early but imports happened
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

try:
    path = {repr(os.path.abspath(entrypoint_path))}
    sys.path.insert(0, os.path.dirname(path))
    spec = importlib.util.spec_from_file_location("__main__", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["__main__"] = module
    spec.loader.exec_module(module)
except Exception as e:
    dump_modules(ok_val=False)
    sys.exit(1)

dump_modules(ok_val=True)
"""
    
    trace_temp = REPO_ROOT / "trace_temp.json"
    if trace_temp.exists():
        trace_temp.unlink()
        
    try:
        proc = subprocess.Popen([sys.executable, "-c", trace_script], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            print(f"Timeout expired for {entrypoint_path}, killing process...")
            proc.terminate()
            proc.wait(timeout=2)
            
        if trace_temp.exists():
            data = json.load(trace_temp.open())
            with open(output_json, "w") as f:
                json.dump(data, f, indent=2)
            print(f"Generated {output_json}")
            trace_temp.unlink()
        else:
            print(f"Failed to generate {output_json}")
            
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Trace entrypoints
    trace_entrypoint("godotengain/engainos/launch_engine.py", REPORT_DIR / "import-trace-launch-engine.json")
    trace_entrypoint("godotsim/sim_runtime.py", REPORT_DIR / "import-trace-godotsim-sim.json")
    
    # 2. Trace all tests
    tests_dir = REPO_ROOT / "godotengain/engainos/tests"
    if tests_dir.exists():
        for test_file in tests_dir.glob("test_*.py"):
            rel_path = test_file.relative_to(REPO_ROOT)
            out_name = f"import-trace-test-{test_file.stem}.json"
            trace_entrypoint(str(rel_path), REPORT_DIR / out_name)
