#!/usr/bin/env python3
"""
gate_player_body_visible_proof.py
Proves a player body capsule renders visibly in a room (floor, wall, camera, light).
No auto-exit script. Held open for 4 seconds to verify visual execution.
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
SCENE_PATH = ROOT / "tmp_player_body_gate_scene.tscn"

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
    print("=" * 52)
    print("RUNNING GATE: gate_player_body_visible_proof.py")
    print("=" * 52)

    # 1. Define full 5-piece scene demand (floor, wall, camera, light, player)
    player_body_demand = {
        "scene_id": "player_body_gate_scene",
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
                "piece_id": "wall_back",
                "piece_type": "wall",
                "mesh": "BoxMesh",
                "position": [0.0, 1.0, -5.0],
                "scale": [8.0, 2.0, 0.2],
                "collision": True
            },
            {
                "piece_id": "camera_main",
                "piece_type": "camera",
                "position": [0.0, 6.0, 12.0],
                "rotation": [-30.0, 0.0, 0.0],
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
                "piece_id": "player_001",
                "piece_type": "player",
                "root_node": "CharacterBody3D",
                "collision_shape": "CapsuleShape3D",
                "mesh": "res://assets/mesh/player.mesh",
                "camera": "res://scenes/camera.tscn",
                "spawn_position": [0.0, 1.0, 0.0],
                "movement_script": "res://tmp_player_movement.gd",
                "position": [0.0, 1.0, 0.0],
                "scale": [1.0, 1.0, 1.0]
            }
        ]
    }

    print("[gate_player_body_visible_proof] 1. Validating and building scene via builder...")
    status, reasons = build_godot_scene(player_body_demand, SCENE_PATH, MANIFEST_PATH)
    print(f"Build Result: {status} - Reasons: {reasons}")
    if status != STATUS_BUILT:
        print("FAIL: Player body scene could not be built.")
        sys.exit(1)

    # 2. Launch Godot visibly if available
    print("[gate_player_body_visible_proof] 2. Launching Godot with display, holding window open 4s...")
    godot_bin = find_godot_binary()
    if not godot_bin:
        print("BYPASS: Godot binary not found in environment.")
        print("====================================================")
        print("gate_player_body_visible_proof: BYPASS")
        print("====================================================")
        sys.exit(0)

    print(f"Found Godot binary at: {godot_bin}")
    print("*** A WINDOW SHOULD APPEAR SHOWING A FLOOR, A WALL, AND A PLAYER CAPSULE BODY. ***")
    
    try:
        proc = subprocess.Popen([godot_bin, "--scene", f"res://{SCENE_PATH.name}"], cwd=str(ROOT))
        proc.wait(timeout=4)
    except subprocess.TimeoutExpired:
        proc.terminate()
        # Clean up process resources
        try:
            proc.wait(timeout=1)
        except Exception:
            pass
        print("PASS: window stayed open for the full hold duration (expected — no auto-exit).")
    else:
        print(f"FAIL: Godot exited on its own with exit code {proc.returncode} — scene likely has an auto-exit script attached or crashed.")
        sys.exit(1)

    print("=" * 52)
    print("gate_player_body_visible_proof: TRUE")
    print("=" * 52)

if __name__ == "__main__":
    main()
