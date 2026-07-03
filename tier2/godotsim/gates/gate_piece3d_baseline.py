#!/usr/bin/env python3
"""
Gate for verifying piece3d baseline behavior and kernel validation.
"""

from __future__ import annotations
import sys
from pathlib import Path
import json

# Setup root path to import relative modules
ROOT = Path(__file__).resolve().parents[3]
sys.path.append(str(ROOT))

MANIFEST_PATH = ROOT / "docs" / "contracts" / "ENGAINOS_TIER1_AUTHORITY" / "engainos_1stlane_governance_authority" / "piece_baseline_manifest.json"

def run_gate() -> bool:
    print("====================================================")
    print("RUNNING GATE: gate_piece3d_baseline.py")
    print("====================================================")
    
    # 1. Manifest file exists
    print("[gate_piece3d_baseline] 1. Checking if manifest file exists...")
    if not MANIFEST_PATH.exists():
        print(f"FAIL: Manifest file is missing at {MANIFEST_PATH}")
        return False
    print(f"PASS: Manifest exists at {MANIFEST_PATH}")

    # 2. Manifest JSON parses
    print("[gate_piece3d_baseline] 2. Parsing manifest JSON...")
    try:
        with MANIFEST_PATH.open("r", encoding="utf-8") as f:
            manifest = json.load(f)
    except Exception as e:
        print(f"FAIL: Manifest JSON could not be parsed: {e}")
        return False
    print("PASS: Manifest JSON parsed successfully.")

    # 3. Required piece types exist in manifest
    print("[gate_piece3d_baseline] 3. Verifying required piece types exist in manifest...")
    required_types = ["floor", "wall", "camera", "light", "player"]
    pieces = manifest.get("pieces", {})
    for ptype in required_types:
        if ptype not in pieces:
            print(f"FAIL: Piece type '{ptype}' is missing from the baseline manifest pieces.")
            return False
    print(f"PASS: All required piece types exist in manifest: {required_types}")

    # 4. Imports piece3d_mr.py
    print("[gate_piece3d_baseline] 4. Importing piece3d_mr.py...")
    try:
        from tier2.godotsim.kernels.piece3d_mr import validate_pieces, STATUS_ACCEPTED, STATUS_REJECTED, STATUS_SUSPENDED
    except Exception as e:
        print(f"FAIL: Could not import validate_pieces from tier2.godotsim.kernels.piece3d_mr: {e}")
        return False
    print("PASS: Imported validate_pieces successfully.")

    # 5. Valid five-piece demand returns ACCEPTED
    print("[gate_piece3d_baseline] 5. Validating valid five-piece demand...")
    valid_demand = [
        {
            "piece_type": "floor",
            "mesh": "res://assets/mesh/floor.mesh",
            "position": [0, 0, 0],
            "scale": [1, 1, 1],
            "collision": True
        },
        {
            "piece_type": "wall",
            "mesh": "res://assets/mesh/wall.mesh",
            "position": [0, 2.5, -5],
            "scale": [1, 1, 1],
            "collision": True
        },
        {
            "piece_type": "camera",
            "position": [0, 5, 10],
            "rotation": [-15, 0, 0],
            "current": True
        },
        {
            "piece_type": "light",
            "type": "directional",
            "position": [0, 10, 0],
            "rotation": [45, 0, 0]
        },
        {
            "piece_type": "player",
            "root_node": "KinematicBody",
            "collision_shape": "BoxShape",
            "mesh": "res://assets/mesh/player.mesh",
            "camera": "res://scenes/camera.tscn",
            "spawn_position": [0, 1, 0],
            "movement_script": "res://scripts/player_movement.gd"
        }
    ]
    status, reasons = validate_pieces(valid_demand, str(MANIFEST_PATH))
    print(f"Result: {status} - Reasons: {reasons}")
    if status != STATUS_ACCEPTED:
        print("FAIL: Valid five-piece demand did not return ACCEPTED.")
        return False
    print("PASS: Valid five-piece demand returns ACCEPTED.")

    # 6. Missing required field returns REJECTED with specific reason
    print("[gate_piece3d_baseline] 6. Verifying missing required field returns REJECTED...")
    invalid_demand_missing = [
        {
            "piece_type": "floor",
            "mesh": "res://assets/mesh/floor.mesh",
            "position": [0, 0, 0],
            # Missing scale
            "collision": True
        }
    ]
    status, reasons = validate_pieces(invalid_demand_missing, str(MANIFEST_PATH))
    print(f"Result: {status} - Reasons: {reasons}")
    if status != STATUS_REJECTED:
        print("FAIL: Missing required field did not return REJECTED.")
        return False
    expected_reason = "floor missing scale"
    if not any(expected_reason in r.lower() for r in reasons):
        print(f"FAIL: Reason did not mention '{expected_reason}'. Reasons given: {reasons}")
        return False
    
    # Print the specific visual payload layout requested by the user
    for r in reasons:
        if expected_reason in r.lower():
            print(f"\n{expected_reason}")
            print("→ REJECTED")
            print("→ reason names the piece")
            print("→ reason names the missing field\n")

    print("PASS: Missing required field returns REJECTED with expected reason.")

    # 7. Light conditional fields are enforced
    print("[gate_piece3d_baseline] 7. Verifying directional light missing 'rotation' returns REJECTED...")
    invalid_light_directional = [
        {
            "piece_type": "light",
            "type": "directional",
            "position": [0, 10, 0]
            # Missing rotation (conditional required field for directional)
        }
    ]
    status, reasons = validate_pieces(invalid_light_directional, str(MANIFEST_PATH))
    print(f"Result: {status} - Reasons: {reasons}")
    if status != STATUS_REJECTED:
        print("FAIL: Directional light missing 'rotation' did not return REJECTED.")
        return False
    expected_reason = "light missing conditional field rotation"
    if not any(expected_reason in r.lower() for r in reasons):
        print(f"FAIL: Reason did not mention '{expected_reason}'. Reasons given: {reasons}")
        return False
    print("PASS: Directional light missing conditional field 'rotation' is rejected correctly.")

    print("[gate_piece3d_baseline] 8. Verifying omni light missing 'energy', 'range', or 'shadows' returns REJECTED...")
    invalid_light_omni = [
        {
            "piece_type": "light",
            "type": "omni",
            "position": [0, 10, 0],
            "energy": 1.0,
            # Missing range and shadows
        }
    ]
    status, reasons = validate_pieces(invalid_light_omni, str(MANIFEST_PATH))
    print(f"Result: {status} - Reasons: {reasons}")
    if status != STATUS_REJECTED:
        print("FAIL: Omni light missing conditional required fields did not return REJECTED.")
        return False
    # Check that at least one of range or shadows is listed as missing
    if not any("range" in r.lower() or "shadows" in r.lower() for r in reasons):
        print(f"FAIL: Reasons did not mention missing conditional fields. Reasons given: {reasons}")
        return False
    print("PASS: Omni light missing conditional fields is rejected correctly.")

    print("====================================================")
    print("🎉 ALL PIECE3D BASELINE GATE CHECKS PASSED!")
    print("gate_piece3d_baseline: TRUE")
    print("====================================================")
    return True

if __name__ == "__main__":
    success = run_gate()
    sys.exit(0 if success else 1)
