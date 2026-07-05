#!/usr/bin/env python3
"""
gate_piece_recipe_pack_001_visible_proof.py
Launches the scene containing marker, box, ramp, platform, and trigger_zone pieces
in a visible window (no --headless) and keeps it open for 5 seconds.
"""

from __future__ import annotations
import subprocess
import sys
import shutil
import os
from pathlib import Path

# Setup root path to import relative modules
ROOT = Path(__file__).resolve().parents[3]
sys.path.append(str(ROOT))

from tier2.godotsim.kernels.piece3d_mr import validate_pieces
from tier2.godotsim.builders.godot_scene_piece_builder import build_godot_scene, STATUS_BUILT

MANIFEST_PATH = str(ROOT / "docs/contracts/ENGAINOS_TIER1_AUTHORITY/engainos_1stlane_governance_authority/piece_baseline_manifest.json")
SCENE_PATH = ROOT / "tmp_piece_recipe_pack_001_visible_scene.tscn"

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

def main():
    print("=" * 60)
    print("RUNNING GATE: gate_piece_recipe_pack_001_visible_proof.py")
    print("=" * 60)

    # Define 10-piece demo scene composition
    demo_demand = {
        "scene_id": "recipe_pack_visible_scene",
        "pieces": [
            {
                "piece_id": "floor_main",
                "piece_type": "floor",
                "mesh": "BoxMesh",
                "position": [0.0, -0.1, 0.0],
                "scale": [15.0, 0.2, 15.0],
                "collision": True
            },
            {
                "piece_id": "camera_main",
                "piece_type": "camera",
                "position": [0.0, 8.0, 15.0],
                "rotation": [-25.0, 0.0, 0.0],
                "current": True
            },
            {
                "piece_id": "light_directional",
                "piece_type": "light",
                "type": "directional",
                "position": [0.0, 15.0, 0.0],
                "rotation": [-45.0, -45.0, 0.0]
            },
            {
                "piece_id": "marker_cube",
                "piece_type": "marker",
                "mesh": "cube",
                "position": [-4.0, 0.5, -2.0],
                "scale": [1.0, 1.0, 1.0],
                "color": [1.0, 0.2, 0.2, 1.0], # Red
                "collision": False
            },
            {
                "piece_id": "marker_sphere",
                "piece_type": "marker",
                "mesh": "sphere",
                "position": [-2.0, 0.5, -2.0],
                "scale": [1.0, 1.0, 1.0],
                "color": [0.2, 1.0, 0.2, 1.0], # Green
                "collision": False
            },
            {
                "piece_id": "marker_cylinder",
                "piece_type": "marker",
                "mesh": "cylinder",
                "position": [0.0, 0.5, -2.0],
                "scale": [1.0, 1.0, 1.0],
                "color": [0.2, 0.2, 1.0, 1.0], # Blue
                "collision": False
            },
            {
                "piece_id": "box_1",
                "piece_type": "box",
                "mesh": "cube",
                "position": [2.0, 0.5, -2.0],
                "scale": [1.0, 1.0, 1.0],
                "collision": True
            },
            {
                "piece_id": "ramp_1",
                "piece_type": "ramp",
                "mesh": "wedge",
                "position": [4.0, 0.5, -2.0],
                "rotation": [30.0, 0.0, 0.0],
                "scale": [1.2, 1.0, 3.0],
                "collision": True
            },
            {
                "piece_id": "platform_1",
                "piece_type": "platform",
                "mesh": "cube",
                "position": [0.0, 3.0, -4.0],
                "scale": [3.0, 0.2, 3.0],
                "collision": True
            },
            {
                "piece_id": "trigger_zone_1",
                "piece_type": "trigger_zone",
                "shape": "box",
                "position": [0.0, 1.0, 2.0],
                "scale": [2.0, 2.0, 2.0],
                "monitoring": True
            }
        ]
    }

    status, reasons = build_godot_scene(demo_demand, SCENE_PATH, MANIFEST_PATH)
    if status != STATUS_BUILT:
        print(f"gate_piece_recipe_pack_001_visible_proof: FALSE (Failed to build scene: {reasons})")
        sys.exit(1)

    godot_bin = find_godot_binary()
    if not godot_bin:
        print("gate_piece_recipe_pack_001_visible_proof: BYPASS (Godot binary not found)")
        sys.exit(0)

    print(f"Found Godot binary at: {godot_bin}")
    print("*** A WINDOW SHOULD APPEAR SHOWING THE ROOM WITH ALL RECIPE PACK 001 PIECES. ***")
    
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
        print("PASS: window stayed open for the full hold duration (expected — no auto-exit).")
    else:
        print(f"gate_piece_recipe_pack_001_visible_proof: FALSE (Godot exited early with code {proc.returncode})")
        sys.exit(1)

    print("=" * 60)
    print("gate_piece_recipe_pack_001_visible_proof: TRUE")
    print("=" * 60)
    sys.exit(0)

if __name__ == "__main__":
    main()
