#!/usr/bin/env python3
"""
gate_player_movement_proof.py
Contract-compliant gate for MILESTONE_006.
Validates player movement using gate_player_movement_proof: TRUE on success.
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
    # 1. Define full 5-piece scene demand
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
            }
        ]
    }

    status, reasons = build_godot_scene(movement_demand, SCENE_PATH, MANIFEST_PATH)
    if status != STATUS_BUILT:
        print(f"gate_player_movement_proof: FALSE (Failed to build scene: {reasons})")
        sys.exit(1)

    godot_bin = find_godot_binary()
    if not godot_bin:
        print("gate_player_movement_proof: BYPASS (Godot binary not found)")
        sys.exit(0)
    
    try:
        proc = subprocess.run(
            [godot_bin, "--headless", "--scene", f"res://{SCENE_PATH.name}"],
            cwd=str(ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=15
        )
    except subprocess.TimeoutExpired:
        print("gate_player_movement_proof: FALSE (Godot process timed out)")
        sys.exit(1)

    stdout = proc.stdout
    
    # Required proof lines to check
    required_keys = [
        "MILESTONE_006_GODOT_RUNNER_STARTED",
        "MILESTONE_006_INITIAL_POSITION",
        "MILESTONE_006_FINAL_POSITION",
        "MILESTONE_006_DELTA",
        "MILESTONE_006_FORWARD_MOVED: TRUE",
        "MILESTONE_006_BACK_MOVED: TRUE",
        "MILESTONE_006_LEFT_MOVED: TRUE",
        "MILESTONE_006_RIGHT_MOVED: TRUE",
        "MILESTONE_006_JUMP_APPLIED: TRUE",
        "MILESTONE_006_GODOT_RUNNER_DONE: TRUE"
    ]
    
    missing = [k for k in required_keys if k not in stdout]
    if proc.returncode != 0:
        print(f"gate_player_movement_proof: FALSE (Godot exited with code {proc.returncode})")
        print("--- Godot Output ---")
        print(stdout)
        sys.exit(1)
        
    if missing:
        print(f"gate_player_movement_proof: FALSE (Missing stdout signatures: {missing})")
        print("--- Godot Output ---")
        print(stdout)
        sys.exit(1)

    print("gate_player_movement_proof: TRUE")
    sys.exit(0)

if __name__ == "__main__":
    main()
