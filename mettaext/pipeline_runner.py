#!/usr/bin/env python3
"""
pipeline_runner.py
Automatic entrypoint that chains the Scene Pipeline (P1-P5)
and the Semantic Compiler (ZW-C), then pushes the result to the Godot simulation runtime.
"""
import sys
import subprocess
import json
import urllib.request
import urllib.error
from pathlib import Path

def run_pipeline(chapter_path_str):
    chapter_path = Path(chapter_path_str).absolute()
    if not chapter_path.exists():
        print(f"❌ Error: Could not find chapter at {chapter_path}")
        sys.exit(1)

    base_dir = Path(__file__).parent
    
    # --- 1. Run Scene Pipeline P1-P5 ---
    print(f"\n[1] Running Ingestion Pipeline (P1-P5) on: {chapter_path.name}")
    master_script = base_dir / "master_pipeline.py"
    out_dir = base_dir / "compiled" / "pipeline_work"
    
    cmd_ingest = [
        sys.executable, str(master_script),
        str(chapter_path),
        "--output-dir", str(out_dir)
    ]
    
    # We suppress standard output of master_pipeline to avoid spam, unless it fails
    res = subprocess.run(cmd_ingest, cwd=str(base_dir), capture_output=True, text=True)
    if res.returncode != 0:
        print("❌ Error running P1-P5 pipeline:")
        print("STDOUT:", res.stdout)
        print("STDERR:", res.stderr)
        sys.exit(1)
    
    # --- 2. Find the produced .zonj ---
    # master_pipeline writes to <stem>.zonj.json
    produced_zonj = out_dir / f"{chapter_path.stem}.zonj.json"
    if not produced_zonj.exists():
        print(f"❌ Error: expected pipeline output {produced_zonj} was not found.")
        sys.exit(1)
    print(f"✅ Produced base scene: {produced_zonj.name}")

    # --- 3. Run ZW-Compiler ---
    print(f"\n[2] Running ZW-Compiler (Semantic Augmentation)")
    compiler_script = base_dir / "zw_compiler.py"
    final_out = base_dir / "compiled" / f"{chapter_path.stem}_with_semantics.zonj.json"
    
    cmd_compile = [
        sys.executable, str(compiler_script),
        str(produced_zonj),
        str(final_out)
    ]
    
    res = subprocess.run(cmd_compile, cwd=str(base_dir), capture_output=True, text=True)
    if res.returncode != 0:
        print("❌ Error running zw_compiler.py:")
        print("STDOUT:", res.stdout)
        print("STDERR:", res.stderr)
        sys.exit(1)
    print(f"✅ Semantic scene exported to: {final_out.name}")

    # --- 4. Report & Validate ---
    print(f"\n[3] Semantic Validation Report")
    try:
        data = json.loads(final_out.read_text())
        report = data.get("compiler_report", {})
        print(json.dumps(report, indent=2))
        
        # Check warnings
        warnings = report.get("warnings", [])
        if warnings:
            print("⚠️ Compiler Warnings Detected:")
            for w in warnings:
                print(f"  - {w}")
    except Exception as e:
        print(f"❌ Could not read compiled output: {e}")

    # --- 5. POST to Runtime ---
    print(f"\n[4] Pushing to Simulation Runtime")
    url = "http://127.0.0.1:8080/scene/load"
    
    try:
        req = urllib.request.Request(
            url,
            data=final_out.read_bytes(),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req) as response:
            status = response.getcode()
            body = response.read().decode('utf-8')
            print(f"✅ POST {url} -> {status} OK")
            print(f"Runtime Response: {body}")
            
    except urllib.error.URLError as e:
        print(f"⚠️ Failed to post to runtime ({url}): {e}")
        print("Note: Ensure the Godot simulation backend (Trixel/GodotSim) is actively running on port 8080.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 pipeline_runner.py path/to/chapter.txt")
        sys.exit(1)
    run_pipeline(sys.argv[1])
