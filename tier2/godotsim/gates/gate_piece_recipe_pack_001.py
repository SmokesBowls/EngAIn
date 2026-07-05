# gate_piece_recipe_pack_001.py
"""
Gate for verifying piece recipe pack 001 behavior.
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
    print("RUNNING GATE: gate_piece_recipe_pack_001.py")
    print("====================================================")
    
    # 1. Manifest file exists
    print("[gate_piece_recipe_pack_001] 1. Checking if manifest file exists...")
    if not MANIFEST_PATH.exists():
        print(f"FAIL: Manifest file is missing at {MANIFEST_PATH}")
        return False
    print(f"PASS: Manifest exists at {MANIFEST_PATH}")

    # 2. Manifest JSON parses
    print("[gate_piece_recipe_pack_001] 2. Parsing manifest JSON...")
    try:
        with MANIFEST_PATH.open("r", encoding="utf-8") as f:
            manifest = json.load(f)
    except Exception as e:
        print(f"FAIL: Manifest JSON could not be parsed: {e}")
        return False
    print("PASS: Manifest JSON parsed successfully.")

    # 3. Required piece types exist in manifest
    print("[gate_piece_recipe_pack_001] 3. Verifying required piece types exist in manifest...")
    required_types = ["floor", "wall", "camera", "light", "player", "marker", "box", "ramp", "platform", "trigger_zone"]
    pieces = manifest.get("pieces", {})
    for ptype in required_types:
        if ptype not in pieces:
            print(f"FAIL: Piece type '{ptype}' is missing from the baseline manifest pieces.")
            return False
    print(f"PASS: All required piece types exist in manifest: {required_types}")

    # 4. Imports piece3d_mr.py
    print("[gate_piece_recipe_pack_001] 4. Importing piece3d_mr.py...")
    try:
        from tier2.godotsim.kernels.piece3d_mr import validate_pieces, STATUS_ACCEPTED, STATUS_REJECTED, STATUS_SUSPENDED
    except Exception as e:
        print(f"FAIL: Could not import validate_pieces from tier2.godotsim.kernels.piece3d_mr: {e}")
        return False
    print("PASS: Imported validate_pieces successfully.")

    # 5. Valid five-piece demand returns ACCEPTED
    print("[gate_piece_recipe_pack_001] 5. Validating valid five-piece demand...")
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
    print("[gate_piece_recipe_pack_001] 6. Verifying missing required field returns REJECTED...")
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
    print("[gate_piece_recipe_pack_001] 7. Verifying directional light missing 'rotation' returns REJECTED...")
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

    print("[gate_piece_recipe_pack_001] 8. Verifying omni light missing 'energy', 'range', or 'shadows' returns REJECTED...")
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

    # 9. Marker validation
    print("[gate_piece_recipe_pack_001] 9. Verifying marker validation...")
    valid_marker = [
        {
            "piece_type": "marker",
            "mesh": "cube",
            "position": [0, 3, 0],
            "scale": [1, 1, 1],
            "color": [1, 0, 0],
            "collision": True
        }
    ]
    status, reasons = validate_pieces(valid_marker, str(MANIFEST_PATH))
    print(f"Result: {status} - Reasons: {reasons}")
    if status != STATUS_ACCEPTED:
        print("FAIL: Valid marker did not return ACCEPTED.")
        return False
    print("PASS: Valid marker returns ACCEPTED.")

    invalid_marker_missing_mesh = [
        {
            "piece_type": "marker",
            "position": [0, 3, 0],
            "scale": [1, 1, 1],
            "color": [1, 0, 0],
            "collision": True
        }
    ]
    status, reasons = validate_pieces(invalid_marker_missing_mesh, str(MANIFEST_PATH))
    print(f"Result: {status} - Reasons: {reasons}")
    if status != STATUS_REJECTED:
        print("FAIL: Invalid marker missing mesh did not return REJECTED.")
        return False
    expected_reason = "marker missing mesh"
    if not any(expected_reason in r.lower() for r in reasons):
        print(f"FAIL: Reason did not mention '{expected_reason}'. Reasons given: {reasons}")
        return False

    invalid_marker_invalid_mesh = [
        {
            "piece_type": "marker",
            "mesh": "capsule",
            "position": [0, 3, 0],
            "scale": [1, 1, 1],
            "color": [1, 0, 0],
            "collision": True
        }
    ]
    status, reasons = validate_pieces(invalid_marker_invalid_mesh, str(MANIFEST_PATH))
    print(f"Result: {status} - Reasons: {reasons}")
    if status != STATUS_REJECTED:
        print("FAIL: Invalid marker with invalid mesh did not return REJECTED.")
        return False
    expected_reason = "marker disallowed value for mesh"
    if not any(expected_reason in r.lower() for r in reasons):
        print(f"FAIL: Reason did not mention '{expected_reason}'. Reasons given: {reasons}")
        return False

    invalid_marker_missing_collision = [
        {
            "piece_type": "marker",
            "mesh": "cube",
            "position": [0, 3, 0],
            "scale": [1, 1, 1],
            "color": [1, 0, 0]
        }
    ]
    status, reasons = validate_pieces(invalid_marker_missing_collision, str(MANIFEST_PATH))
    print(f"Result: {status} - Reasons: {reasons}")
    if status != STATUS_REJECTED:
        print("FAIL: Invalid marker missing collision did not return REJECTED.")
        return False
    expected_reason = "marker missing collision"
    if not any(expected_reason in r.lower() for r in reasons):
        print(f"FAIL: Reason did not mention '{expected_reason}'. Reasons given: {reasons}")
        return False

    # 10. Box validation
    print("[gate_piece_recipe_pack_001] 10. Verifying box validation...")
    valid_box = [
        {
            "piece_type": "box",
            "mesh": "cube",
            "position": [0, 4, 0],
            "scale": [2, 2, 2],
            "collision": True
        }
    ]
    status, reasons = validate_pieces(valid_box, str(MANIFEST_PATH))
    print(f"Result: {status} - Reasons: {reasons}")
    if status != STATUS_ACCEPTED:
        print("FAIL: Valid box did not return ACCEPTED.")
        return False
    print("PASS: Valid box returns ACCEPTED.")

    invalid_box_missing_mesh = [
        {
            "piece_type": "box",
            "position": [0, 4, 0],
            "scale": [2, 2, 2],
            "collision": True
        }
    ]
    status, reasons = validate_pieces(invalid_box_missing_mesh, str(MANIFEST_PATH))
    print(f"Result: {status} - Reasons: {reasons}")
    if status != STATUS_REJECTED:
        print("FAIL: Invalid box missing mesh did not return REJECTED.")
        return False
    expected_reason = "box missing mesh"
    if not any(expected_reason in r.lower() for r in reasons):
        print(f"FAIL: Reason did not mention '{expected_reason}'. Reasons given: {reasons}")
        return False

    invalid_box_invalid_mesh = [
        {
            "piece_type": "box",
            "mesh": "cylinder",
            "position": [0, 4, 0],
            "scale": [2, 2, 2],
            "collision": True
        }
    ]
    status, reasons = validate_pieces(invalid_box_invalid_mesh, str(MANIFEST_PATH))
    print(f"Result: {status} - Reasons: {reasons}")
    if status != STATUS_REJECTED:
        print("FAIL: Invalid box with invalid mesh did not return REJECTED.")
        return False
    expected_reason = "box disallowed value for mesh"
    if not any(expected_reason in r.lower() for r in reasons):
        print(f"FAIL: Reason did not mention '{expected_reason}'. Reasons given: {reasons}")
        return False

    invalid_box_missing_collision = [
        {
            "piece_type": "box",
            "mesh": "cube",
            "position": [0, 4, 0],
            "scale": [2, 2, 2]
        }
    ]
    status, reasons = validate_pieces(invalid_box_missing_collision, str(MANIFEST_PATH))
    print(f"Result: {status} - Reasons: {reasons}")
    if status != STATUS_REJECTED:
        print("FAIL: Invalid box missing collision did not return REJECTED.")
        return False
    expected_reason = "box missing collision"
    if not any(expected_reason in r.lower() for r in reasons):
        print(f"FAIL: Reason did not mention '{expected_reason}'. Reasons given: {reasons}")
        return False

    # 11. Ramp validation
    print("[gate_piece_recipe_pack_001] 11. Verifying ramp validation...")
    valid_ramp = [
        {
            "piece_type": "ramp",
            "mesh": "wedge",
            "position": [0, 5, 0],
            "rotation": [45, 0, 0],
            "scale": [2, 1, 1],
            "collision": True
        }
    ]
    status, reasons = validate_pieces(valid_ramp, str(MANIFEST_PATH))
    print(f"Result: {status} - Reasons: {reasons}")
    if status != STATUS_ACCEPTED:
        print("FAIL: Valid ramp did not return ACCEPTED.")
        return False
    print("PASS: Valid ramp returns ACCEPTED.")

    invalid_ramp_missing_mesh = [
        {
            "piece_type": "ramp",
            "position": [0, 5, 0],
            "rotation": [45, 0, 0],
            "scale": [2, 1, 1],
            "collision": True
        }
    ]
    status, reasons = validate_pieces(invalid_ramp_missing_mesh, str(MANIFEST_PATH))
    print(f"Result: {status} - Reasons: {reasons}")
    if status != STATUS_REJECTED:
        print("FAIL: Invalid ramp missing mesh did not return REJECTED.")
        return False
    expected_reason = "ramp missing mesh"
    if not any(expected_reason in r.lower() for r in reasons):
        print(f"FAIL: Reason did not mention '{expected_reason}'. Reasons given: {reasons}")
        return False

    invalid_ramp_invalid_mesh = [
        {
            "piece_type": "ramp",
            "mesh": "cylinder",
            "position": [0, 5, 0],
            "rotation": [45, 0, 0],
            "scale": [2, 1, 1],
            "collision": True
        }
    ]
    status, reasons = validate_pieces(invalid_ramp_invalid_mesh, str(MANIFEST_PATH))
    print(f"Result: {status} - Reasons: {reasons}")
    if status != STATUS_REJECTED:
        print("FAIL: Invalid ramp with invalid mesh did not return REJECTED.")
        return False
    expected_reason = "ramp disallowed value for mesh"
    if not any(expected_reason in r.lower() for r in reasons):
        print(f"FAIL: Reason did not mention '{expected_reason}'. Reasons given: {reasons}")
        return False

    invalid_ramp_missing_collision = [
        {
            "piece_type": "ramp",
            "mesh": "wedge",
            "position": [0, 5, 0],
            "rotation": [45, 0, 0],
            "scale": [2, 1, 1]
        }
    ]
    status, reasons = validate_pieces(invalid_ramp_missing_collision, str(MANIFEST_PATH))
    print(f"Result: {status} - Reasons: {reasons}")
    if status != STATUS_REJECTED:
        print("FAIL: Invalid ramp missing collision did not return REJECTED.")
        return False
    expected_reason = "ramp missing collision"
    if not any(expected_reason in r.lower() for r in reasons):
        print(f"FAIL: Reason did not mention '{expected_reason}'. Reasons given: {reasons}")
        return False

    # 12. Platform validation
    print("[gate_piece_recipe_pack_001] 12. Verifying platform validation...")
    valid_platform = [
        {
            "piece_type": "platform",
            "mesh": "cube",
            "position": [0, 6, 0],
            "scale": [3, 1, 1],
            "collision": True
        }
    ]
    status, reasons = validate_pieces(valid_platform, str(MANIFEST_PATH))
    print(f"Result: {status} - Reasons: {reasons}")
    if status != STATUS_ACCEPTED:
        print("FAIL: Valid platform did not return ACCEPTED.")
        return False
    print("PASS: Valid platform returns ACCEPTED.")

    invalid_platform_missing_mesh = [
        {
            "piece_type": "platform",
            "position": [0, 6, 0],
            "scale": [3, 1, 1],
            "collision": True
        }
    ]
    status, reasons = validate_pieces(invalid_platform_missing_mesh, str(MANIFEST_PATH))
    print(f"Result: {status} - Reasons: {reasons}")
    if status != STATUS_REJECTED:
        print("FAIL: Invalid platform missing mesh did not return REJECTED.")
        return False
    expected_reason = "platform missing mesh"
    if not any(expected_reason in r.lower() for r in reasons):
        print(f"FAIL: Reason did not mention '{expected_reason}'. Reasons given: {reasons}")
        return False

    invalid_platform_invalid_mesh = [
        {
            "piece_type": "platform",
            "mesh": "cylinder",
            "position": [0, 6, 0],
            "scale": [3, 1, 1],
            "collision": True
        }
    ]
    status, reasons = validate_pieces(invalid_platform_invalid_mesh, str(MANIFEST_PATH))
    print(f"Result: {status} - Reasons: {reasons}")
    if status != STATUS_REJECTED:
        print("FAIL: Invalid platform with invalid mesh did not return REJECTED.")
        return False
    expected_reason = "platform disallowed value for mesh"
    if not any(expected_reason in r.lower() for r in reasons):
        print(f"FAIL: Reason did not mention '{expected_reason}'. Reasons given: {reasons}")
        return False

    invalid_platform_missing_collision = [
        {
            "piece_type": "platform",
            "mesh": "cube",
            "position": [0, 6, 0],
            "scale": [3, 1, 1]
        }
    ]
    status, reasons = validate_pieces(invalid_platform_missing_collision, str(MANIFEST_PATH))
    print(f"Result: {status} - Reasons: {reasons}")
    if status != STATUS_REJECTED:
        print("FAIL: Invalid platform missing collision did not return REJECTED.")
        return False
    expected_reason = "platform missing collision"
    if not any(expected_reason in r.lower() for r in reasons):
        print(f"FAIL: Reason did not mention '{expected_reason}'. Reasons given: {reasons}")
        return False

    # 13. Trigger zone validation
    print("[gate_piece_recipe_pack_001] 13. Verifying trigger zone validation...")
    valid_trigger_zone = [
        {
            "piece_type": "trigger_zone",
            "shape": "box",
            "position": [0, 7, 0],
            "scale": [4, 1, 1],
            "monitoring": True
        }
    ]
    status, reasons = validate_pieces(valid_trigger_zone, str(MANIFEST_PATH))
    print(f"Result: {status} - Reasons: {reasons}")
    if status != STATUS_ACCEPTED:
        print("FAIL: Valid trigger zone did not return ACCEPTED.")
        return False
    print("PASS: Valid trigger zone returns ACCEPTED.")

    invalid_trigger_zone_missing_shape = [
        {
            "piece_type": "trigger_zone",
            "position": [0, 7, 0],
            "scale": [4, 1, 1],
            "monitoring": True
        }
    ]
    status, reasons = validate_pieces(invalid_trigger_zone_missing_shape, str(MANIFEST_PATH))
    print(f"Result: {status} - Reasons: {reasons}")
    if status != STATUS_REJECTED:
        print("FAIL: Invalid trigger zone missing shape did not return REJECTED.")
        return False
    expected_reason = "trigger_zone missing shape"
    if not any(expected_reason in r.lower() for r in reasons):
        print(f"FAIL: Reason did not mention '{expected_reason}'. Reasons given: {reasons}")
        return False

    invalid_trigger_zone_invalid_shape = [
        {
            "piece_type": "trigger_zone",
            "shape": "cylinder",
            "position": [0, 7, 0],
            "scale": [4, 1, 1],
            "monitoring": True
        }
    ]
    status, reasons = validate_pieces(invalid_trigger_zone_invalid_shape, str(MANIFEST_PATH))
    print(f"Result: {status} - Reasons: {reasons}")
    if status != STATUS_REJECTED:
        print("FAIL: Invalid trigger zone with invalid shape did not return REJECTED.")
        return False
    expected_reason = "trigger_zone disallowed value for shape"
    if not any(expected_reason in r.lower() for r in reasons):
        print(f"FAIL: Reason did not mention '{expected_reason}'. Reasons given: {reasons}")
        return False

    invalid_trigger_zone_missing_monitoring = [
        {
            "piece_type": "trigger_zone",
            "shape": "box",
            "position": [0, 7, 0],
            "scale": [4, 1, 1]
        }
    ]
    status, reasons = validate_pieces(invalid_trigger_zone_missing_monitoring, str(MANIFEST_PATH))
    print(f"Result: {status} - Reasons: {reasons}")
    if status != STATUS_REJECTED:
        print("FAIL: Invalid trigger zone missing monitoring did not return REJECTED.")
        return False
    expected_reason = "trigger_zone missing monitoring"
    if not any(expected_reason in r.lower() for r in reasons):
        print(f"FAIL: Reason did not mention '{expected_reason}'. Reasons given: {reasons}")
        return False

    ok_msg = "All piece recipe pack 001 validations passed."
    print(f"[gate_piece_recipe_pack_001] {ok_msg}")
    return True


if __name__ == "__main__":
    sys.exit(0 if run_gate() else 1)
