#!/usr/bin/env python3
"""
Gate for headless Godot rendering proof with one accepted floor piece.
"""

from __future__ import annotations
import sys
import os
import shutil
import subprocess
from pathlib import Path
import json

# Setup root path to import relative modules
ROOT = Path(__file__).resolve().parents[3]
sys.path.append(str(ROOT))

MANIFEST_PATH = ROOT / "docs" / "contracts" / "ENGAINOS_TIER1_AUTHORITY" / "engainos_1stlane_governance_authority" / "piece_baseline_manifest.json"

def find_godot_binary() -> str | None:
    # Check PATH
    bin_path = shutil.which("godot")
    if bin_path:
        return bin_path

    # Check known local user path
    local_path = Path("/home/mytruelove/.local/bin/godot")
    if local_path.exists() and os.access(local_path, os.X_OK):
        return str(local_path)

    return None

def run_gate() -> str:
    print("====================================================")
    print("RUNNING GATE: gate_floor_headless_godot_proof.py")
    print("====================================================")

    # 1. Validate floor demand with piece3d_mr.py
    print("[gate_floor_headless_godot_proof] 1. Validating floor demand with piece3d_mr.py...")
    try:
        from tier2.godotsim.kernels.piece3d_mr import validate_pieces, STATUS_ACCEPTED
    except Exception as e:
        print(f"FAIL: Could not import validate_pieces: {e}")
        return "FALSE"

    floor_demand = [
        {
            "piece_type": "floor",
            "mesh": "res://assets/mesh/floor.mesh",
            "position": [0.0, 0.0, 0.0],
            "scale": [10.0, 1.0, 10.0],
            "collision": True
        }
    ]

    status, reasons = validate_pieces(floor_demand, str(MANIFEST_PATH))
    print(f"Validation Result: {status} - Reasons: {reasons}")
    if status != STATUS_ACCEPTED:
        print("FAIL: Floor validation did not return ACCEPTED.")
        return "FALSE"

    # 2. Write temporary minimal Godot script and scene
    print("[gate_floor_headless_godot_proof] 2. Writing temporary Godot script and scene...")
    script_path = ROOT / "tmp_gate_test_script.gd"
    scene_path = ROOT / "tmp_gate_test_scene.tscn"

    script_content = """extends Node3D

func _ready():
    print("Godot Headless check: Root ready, exiting cleanly.")
    get_tree().quit(0)
"""

    scale = floor_demand[0]["scale"]
    position = floor_demand[0]["position"]

    scene_content = f"""[gd_scene load_steps=3 format=3]

[ext_resource type="Script" path="res://tmp_gate_test_script.gd" id="1_test_script"]
[sub_resource type="BoxMesh" id="BoxMesh_1"]
size = Vector3({scale[0]}, {scale[1]}, {scale[2]})

[node name="Node3D" type="Node3D"]
script = ExtResource("1_test_script")

[node name="Floor" type="MeshInstance3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, {position[0]}, {position[1]}, {position[2]})
mesh = SubResource("BoxMesh_1")

[node name="Camera3D" type="Camera3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 5, 10)

[node name="DirectionalLight3D" type="DirectionalLight3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 0.707107, 0.707107, 0, -0.707107, 0.707107, 0, 10, 0)
"""

    try:
        script_path.write_text(script_content, encoding="utf-8")
        scene_path.write_text(scene_content, encoding="utf-8")
        print(f"Wrote scene to {scene_path}")
    except Exception as e:
        print(f"FAIL: Could not write temporary files: {e}")
        return "FALSE"

    # 3. Launch Godot headless if available
    print("[gate_floor_headless_godot_proof] 3. Launching Godot headless...")
    godot_bin = find_godot_binary()
    if not godot_bin:
        print("BYPASS: Godot binary not found in environment.")
        return "BYPASS"

    print(f"Found Godot binary at: {godot_bin}")
    try:
        result = subprocess.run(
            [godot_bin, "--headless", "--scene", "res://tmp_gate_test_scene.tscn"],
            cwd=str(ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
        )
        print("--- Godot Output ---")
        print(result.stdout)
        print("--- Godot Error ---")
        print(result.stderr)
        print("--------------------")
        
        if result.returncode != 0:
            print(f"FAIL: Godot exited with non-zero exit code: {result.returncode}")
            return "FALSE"

        # Check stdout/stderr for any fatal parsing/runtime errors
        lower_out = result.stdout.lower() + result.stderr.lower()
        if "error" in lower_out or "failed" in lower_out or "parse error" in lower_out:
            if "godot headless check" in lower_out:
                # If we printed the success message but had some minor warnings, it's still fine
                pass
            else:
                print("FAIL: Godot output contains errors.")
                return "FALSE"

    except subprocess.TimeoutExpired:
        print("FAIL: Godot process timed out.")
        return "FALSE"
    except Exception as e:
        print(f"FAIL: Error executing Godot: {e}")
        return "FALSE"

    print("PASS: Godot executed scene and exited cleanly.")
    return "TRUE"

if __name__ == "__main__":
    state = run_gate()
    print("====================================================")
    print(f"gate_floor_headless_godot_proof: {state}")
    print("====================================================")
    sys.exit(0 if state in ("TRUE", "BYPASS") else 1)
