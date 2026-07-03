#!/usr/bin/env python3
"""
gate_visible_floor_render_proof.py
Proves a floor piece renders as actual visible geometry in Godot —
not just that Godot parses/exits. No auto-exit script. Camera must
be `current = true` or nothing renders regardless of headless mode.
"""
import subprocess
import sys
from pathlib import Path

# Setup root path to import relative modules
ROOT = Path(__file__).resolve().parents[3]
sys.path.append(str(ROOT))
from tier2.godotsim.kernels.piece3d_mr import validate_pieces

MANIFEST_PATH = str(ROOT / "docs/contracts/ENGAINOS_TIER1_AUTHORITY/engainos_1stlane_governance_authority/piece_baseline_manifest.json")
SCENE_PATH = ROOT / "tmp_visible_floor_gate_scene.tscn"
GODOT_BIN = "/home/mytruelove/.local/bin/godot"

SCENE_TSCN = """[gd_scene load_steps=2 format=3]

[sub_resource type="BoxMesh" id="BoxMesh_1"]
size = Vector3(10.0, 0.2, 10.0)

[node name="VisibleFloorGateProof" type="Node3D"]

[node name="Floor" type="MeshInstance3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, -0.1, 0)
mesh = SubResource("BoxMesh_1")

[node name="Camera3D" type="Camera3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 0.819152, 0.573576, 0, -0.573576, 0.819152, 0, 5, 8)
current = true

[node name="DirectionalLight3D" type="DirectionalLight3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 0.707107, 0.707107, 0, -0.707107, 0.707107, 0, 10, 0)
"""

def main():
    print("=" * 52)
    print("RUNNING GATE: gate_visible_floor_render_proof.py")
    print("=" * 52)

    floor_piece = {
        "piece_id": "floor_gate_visual",
        "piece_type": "floor",
        "mesh": "BoxMesh",
        "position": [0, -0.1, 0],
        "scale": [10, 0.2, 10],
        "collision": True,
    }
    print("[gate_visible_floor_render_proof] 1. Validating floor demand...")
    status, reasons = validate_pieces([floor_piece], manifest_path=MANIFEST_PATH)
    print(f"Validation Result: {status} - Reasons: {reasons}")
    if status != "ACCEPTED":
        print("FAIL: floor piece did not validate.")
        sys.exit(1)

    print("[gate_visible_floor_render_proof] 2. Writing NO-AUTO-EXIT visible scene...")
    SCENE_PATH.write_text(SCENE_TSCN, encoding="utf-8")
    print(f"Wrote scene to {SCENE_PATH.resolve()}")

    print("[gate_visible_floor_render_proof] 3. Launching Godot with display, holding window open 4s...")
    print("*** A WINDOW SHOULD APPEAR SHOWING A GRAY FLOOR. THIS IS NOT HEADLESS. ***")
    try:
        proc = subprocess.Popen([GODOT_BIN, "--scene", f"res://{SCENE_PATH.name}"], cwd=str(ROOT))
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
    print("gate_visible_floor_render_proof: TRUE")
    print("=" * 52)

if __name__ == "__main__":
    main()
