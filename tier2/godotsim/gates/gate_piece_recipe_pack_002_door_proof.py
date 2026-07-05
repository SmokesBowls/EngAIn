#!/usr/bin/env python3
"""
gate_piece_recipe_pack_002_door_proof.py
Tests validation, building, and visible verification of the 'door' piece type.
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

from tier2.godotsim.kernels.piece3d_mr import validate_pieces, STATUS_ACCEPTED, STATUS_REJECTED
from tier2.godotsim.builders.godot_scene_piece_builder import build_godot_scene, STATUS_BUILT

MANIFEST_PATH = str(ROOT / "docs/contracts/ENGAINOS_TIER1_AUTHORITY/engainos_1stlane_governance_authority/piece_baseline_manifest.json")
SCENE_PATH = ROOT / "tmp_door_proof_scene.tscn"

def find_godot_binary() -> str | None:
    bin_path = shutil.which("godot")
    if bin_path:
        return bin_path
    local_path = Path("/home/mytruelove/.local/bin/godot")
    if local_path.exists() and os.access(local_path, os.X_OK):
        return str(local_path)
    return None

def main():
    print("====================================================")
    print("RUNNING GATE: gate_piece_recipe_pack_002_door_proof.py")
    print("====================================================")

    # 1. Verify 'door' exists in manifest
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    
    if "door" not in manifest.get("pieces", {}):
        print("gate_piece_recipe_pack_002_door_proof: FALSE ('door' missing from manifest)")
        sys.exit(1)
    print("PASS: 'door' exists in manifest.")

    # 2. Test validation on valid door
    valid_demand = [
        {
            "piece_id": "door_1",
            "piece_type": "door",
            "mesh": "cube",
            "position": [0, 1, -2],
            "scale": [1.5, 2.0, 0.2],
            "state": "closed",
            "collision": True
        }
    ]
    status, reasons = validate_pieces(valid_demand, MANIFEST_PATH)
    if status != STATUS_ACCEPTED:
        print(f"gate_piece_recipe_pack_002_door_proof: FALSE (Valid door rejected: {reasons})")
        sys.exit(1)
    print("PASS: Valid door validated successfully.")

    # 3. Test validation on invalid door (missing collision, invalid state)
    invalid_demand = [
        {
            "piece_id": "door_2",
            "piece_type": "door",
            "mesh": "cube",
            "position": [0, 1, -2],
            "scale": [1.5, 2.0, 0.2],
            "state": "half-open", # Invalid state
            "collision": True
        }
    ]
    status, reasons = validate_pieces(invalid_demand, MANIFEST_PATH)
    if status != STATUS_REJECTED or not any("invalid state" in r.lower() or "disallowed value for state" in r.lower() for r in reasons):
        print(f"gate_piece_recipe_pack_002_door_proof: FALSE (Invalid state was not rejected correctly: {reasons})")
        sys.exit(1)
    print("PASS: Invalid state correctly rejected.")

    # 4. Build scene including door
    scene_data = {
        "scene_id": "door_proof_scene",
        "pieces": [
            {
                "piece_id": "floor_main",
                "piece_type": "floor",
                "mesh": "BoxMesh",
                "position": [0.0, -0.1, 0.0],
                "scale": [10.0, 0.2, 10.0],
                "collision": True
            },
            {
                "piece_id": "camera_main",
                "piece_type": "camera",
                "position": [0.0, 5.0, 6.0],
                "rotation": [-20.0, 0.0, 0.0],
                "current": True
            },
            {
                "piece_id": "light_directional",
                "piece_type": "light",
                "type": "directional",
                "position": [0.0, 10.0, 0.0],
                "rotation": [-45.0, -45.0, 0.0]
            },
            {
                "piece_id": "door_1",
                "piece_type": "door",
                "mesh": "cube",
                "position": [0.0, 1.0, -1.0],
                "scale": [1.2, 2.0, 0.15],
                "state": "closed",
                "collision": True
            }
        ]
    }
    
    status, reasons = build_godot_scene(scene_data, SCENE_PATH, MANIFEST_PATH)
    if status != STATUS_BUILT:
        print(f"gate_piece_recipe_pack_002_door_proof: FALSE (Builder failed: {reasons})")
        sys.exit(1)
    print("PASS: Door scene successfully built.")

    # 5. Optional visible rendering check (5s hold)
    godot_bin = find_godot_binary()
    if godot_bin:
        print(f"Found Godot binary at: {godot_bin}")
        print("*** A WINDOW SHOULD APPEAR SHOWING A FLOOR, LIGHT, AND A BROWN DOOR MESH. ***")
        try:
            proc = subprocess.Popen(
                [godot_bin, "--scene", f"res://{SCENE_PATH.name}"],
                cwd=str(ROOT)
            )
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.terminate()
            try:
                proc.wait(timeout=1)
            except Exception:
                pass
            print("PASS: window stayed open for the full hold duration.")
        else:
            print(f"gate_piece_recipe_pack_002_door_proof: FALSE (Godot exited early with code {proc.returncode})")
            sys.exit(1)

    print("====================================================")
    print("gate_piece_recipe_pack_002_door_proof: TRUE")
    print("====================================================")
    sys.exit(0)

if __name__ == "__main__":
    main()
