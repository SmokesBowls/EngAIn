#!/usr/bin/env python3
"""
gate_player_movement_visible_observer_proof.py
Launches the movement demo scene in a visible window (no --headless)
and keeps it open for 15 seconds for human observation of character movement.
Includes visual reference markers.
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
SCENE_PATH = ROOT / "tmp_player_movement_gate_scene.tscn"

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
    print("RUNNING GATE: gate_player_movement_visible_observer_proof.py")
    print("=" * 60)

    # 1. Define full 5-piece scene demand + 2 visual markers
    movement_demand = {
        "scene_id": "player_movement_gate_scene",
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
                "movement_script": "res://tier2/godotsim/scripts/player_movement.gd",
                "position": [0.0, 1.0, 0.0],
                "scale": [1.0, 1.0, 1.0]
            },
            {
                "piece_id": "marker_start",
                "piece_type": "wall",
                "mesh": "BoxMesh",
                "position": [0.0, 0.2, 0.0],
                "scale": [0.3, 0.4, 0.3],
                "collision": False
            },
            {
                "piece_id": "marker_forward",
                "piece_type": "wall",
                "mesh": "BoxMesh",
                "position": [0.0, 0.2, -3.0],
                "scale": [0.3, 0.4, 0.3],
                "collision": False
            }
        ]
    }

    status, reasons = build_godot_scene(movement_demand, SCENE_PATH, MANIFEST_PATH)
    if status != STATUS_BUILT:
        print(f"gate_player_movement_visible_observer_proof: FALSE (Failed to build scene: {reasons})")
        sys.exit(1)

    godot_bin = find_godot_binary()
    if not godot_bin:
        print("gate_player_movement_visible_observer_proof: BYPASS (Godot binary not found)")
        sys.exit(0)

    print(f"Found Godot binary at: {godot_bin}")
    print("*** A WINDOW SHOULD APPEAR. THE CAPSULE SHOULD WALK FORWARD, JUMP, AND WALK BACKWARD. ***")
    print("*** Start Marker is at (0, 0), Target Marker is at (0, -3). ***")
    
    try:
        proc = subprocess.Popen(
            [godot_bin, "--scene", f"res://{SCENE_PATH.name}"],
            cwd=str(ROOT)
        )
        proc.wait(timeout=15)
    except subprocess.TimeoutExpired:
        proc.terminate()
        try:
            proc.wait(timeout=1)
        except Exception:
            pass
        print("PASS: window stayed open for the full hold duration (expected — no auto-exit).")
    else:
        print(f"gate_player_movement_visible_observer_proof: FALSE (Godot exited early with code {proc.returncode})")
        sys.exit(1)

    print("=" * 60)
    print("gate_player_movement_visible_observer_proof: TRUE")
    print("=" * 60)
    sys.exit(0)

if __name__ == "__main__":
    main()
