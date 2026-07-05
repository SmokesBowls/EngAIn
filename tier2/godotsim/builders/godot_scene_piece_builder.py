# godot_scene_piece_builder.py
"""
Godot Scene Piece Builder - Pure Scene Assembler
Validates scene piece demands, structures them, and writes standard Godot 4 .tscn files.
No Godot runtime execution, no side effects, no authority overrides.
"""

from __future__ import annotations
import json
import math
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

# Import the MR validation kernel
from tier2.godotsim.kernels.piece3d_mr import validate_pieces, STATUS_ACCEPTED, STATUS_REJECTED, STATUS_SUSPENDED

# Output status constants
STATUS_BUILT = "BUILT"
STATUS_BUILD_REJECTED = "REJECTED"
STATUS_BUILD_SUSPENDED = "SUSPENDED"


def get_transform_str(position: List[float], rotation_deg: Optional[List[float]] = None, scale: Optional[List[float]] = None) -> str:
    """Helper to generate a Godot 4 Transform3D string (row-major basis vector layout)."""
    # Identity basis rows
    bx = [1.0, 0.0, 0.0]
    by = [0.0, 1.0, 0.0]
    bz = [0.0, 0.0, 1.0]

    # Apply scale to basis
    s = scale or [1.0, 1.0, 1.0]
    bx = [bx[0] * s[0], bx[1] * s[0], bx[2] * s[0]]
    by = [by[0] * s[1], by[1] * s[1], by[2] * s[1]]
    bz = [bz[0] * s[2], bz[1] * s[2], bz[2] * s[2]]

    # Apply rotation (Pitch/Yaw/Roll - XYZ order)
    if rotation_deg:
        rx = math.radians(rotation_deg[0])
        ry = math.radians(rotation_deg[1])
        rz = math.radians(rotation_deg[2])
        
        cx, sx = math.cos(rx), math.sin(rx)
        cy, sy = math.cos(ry), math.sin(ry)
        cz, sz = math.cos(rz), math.sin(rz)

        # Rotation Matrices
        mx = [
            [1.0, 0.0, 0.0],
            [0.0, cx, -sx],
            [0.0, sx, cx]
        ]
        my = [
            [cy, 0.0, sy],
            [0.0, 1.0, 0.0],
            [-sy, 0.0, cy]
        ]
        mz = [
            [cz, -sz, 0.0],
            [sz, cz, 0.0],
            [0.0, 0.0, 1.0]
        ]
        
        # Multiply My * Mx
        temp = []
        for r in range(3):
            row = []
            for c in range(3):
                val = 0.0
                for k in range(3):
                    val += my[r][k] * mx[k][c]
                row.append(val)
            temp.append(row)
            
        # Multiply Mz * temp to get final R
        r_mat = []
        for r in range(3):
            row = []
            for c in range(3):
                val = 0.0
                for k in range(3):
                    val += mz[r][k] * temp[k][c]
                row.append(val)
            r_mat.append(row)

        # Godot expects basis vectors to be the rows of the rotation matrix (scaled)
        bx = [r_mat[0][0] * s[0], r_mat[0][1] * s[0], r_mat[0][2] * s[0]]
        by = [r_mat[1][0] * s[1], r_mat[1][1] * s[1], r_mat[1][2] * s[1]]
        bz = [r_mat[2][0] * s[2], r_mat[2][1] * s[2], r_mat[2][2] * s[2]]

    tx, ty, tz = position
    # Format Transform3D in row-by-row order: bx_x, bx_y, bx_z, by_x, by_y, by_z, bz_x, bz_y, bz_z, tx, ty, tz
    return f"Transform3D({bx[0]:.6g}, {bx[1]:.6g}, {bx[2]:.6g}, {by[0]:.6g}, {by[1]:.6g}, {by[2]:.6g}, {bz[0]:.6g}, {bz[1]:.6g}, {bz[2]:.6g}, {tx:.6g}, {ty:.6g}, {tz:.6g})"


def build_godot_scene(
    scene_data: Dict[str, Any],
    output_path: str | Path,
    manifest_path: Optional[str] = None
) -> Tuple[str, List[str]]:
    """
    Validate and build a Godot 4 .tscn file from demanded pieces.

    Args:
        scene_data: The top-level scene dictionary containing 'scene_id' and 'pieces'.
        output_path: The file path where the generated .tscn scene will be written.
        manifest_path: Optional override to the piece baseline manifest JSON path.

    Returns:
        A tuple of (status, reasons) where status is one of BUILT, REJECTED, SUSPENDED.
    """
    reasons: List[str] = []

    # 1. Structural Scene checks
    if not isinstance(scene_data, dict):
        return STATUS_BUILD_REJECTED, ["Scene data is not a dictionary."]

    scene_id = scene_data.get("scene_id")
    if not scene_id:
        return STATUS_BUILD_REJECTED, ["Scene data is missing required 'scene_id'."]

    pieces = scene_data.get("pieces")
    if pieces is None or not isinstance(pieces, list):
        return STATUS_BUILD_REJECTED, ["Scene data is missing required list 'pieces'."]

    # Verify each piece has required piece_id and piece_type
    seen_ids = set()
    for idx, piece in enumerate(pieces):
        if not isinstance(piece, dict):
            return STATUS_BUILD_REJECTED, [f"Piece at index {idx} is not a dictionary."]

        pid = piece.get("piece_id")
        if not pid:
            return STATUS_BUILD_REJECTED, [f"Piece at index {idx} is missing required 'piece_id'."]

        if pid in seen_ids:
            return STATUS_BUILD_REJECTED, [f"Duplicate piece_id '{pid}' found in scene pieces list."]
        seen_ids.add(pid)

        ptype = piece.get("piece_type")
        if not ptype:
            return STATUS_BUILD_REJECTED, [f"Piece '{pid}' (index {idx}) is missing required 'piece_type'."]

    # 2. Perform Piece3D MR Validation
    status, mr_reasons = validate_pieces(pieces, manifest_path)
    if status == STATUS_SUSPENDED:
        return STATUS_BUILD_SUSPENDED, mr_reasons
    elif status == STATUS_REJECTED:
        return STATUS_BUILD_REJECTED, mr_reasons

    # 3. Validation Accepted -> Proceed with TSCN serialization (No partial builds)
    tscn_header = "[gd_scene load_steps=1 format=3]\n\n"
    
    # Track resources and nodes
    ext_resources: List[str] = []
    sub_resources: List[str] = []
    nodes: List[str] = []
    
    # Root Node
    nodes.append(f'[node name="{scene_id}" type="Node3D"]')
    nodes.append("")

    res_idx = 1
    for piece in pieces:
        pid = piece["piece_id"]
        ptype = piece["piece_type"]

        pos = piece.get("position", [0.0, 0.0, 0.0])
        rot = piece.get("rotation", [0.0, 0.0, 0.0])
        scale = piece.get("scale", [1.0, 1.0, 1.0])

        transform_str = get_transform_str(pos, rot, scale)

        if ptype in ("floor", "wall"):
            # Add Subresource BoxMesh
            sub_resources.append(f'[sub_resource type="BoxMesh" id="BoxMesh_{res_idx}"]')
            sub_resources.append("size = Vector3(1, 1, 1)")
            sub_resources.append("")

            nodes.append(f'[node name="{pid}" type="MeshInstance3D" parent="."]')
            nodes.append(f"transform = {transform_str}")
            nodes.append(f'mesh = SubResource("BoxMesh_{res_idx}")')
            nodes.append("")

            # Handle Collision
            if piece.get("collision") is True:
                sub_resources.append(f'[sub_resource type="BoxShape3D" id="BoxShape3D_{res_idx}"]')
                sub_resources.append("size = Vector3(1, 1, 1)")
                sub_resources.append("")

                nodes.append(f'[node name="StaticBody3D" type="StaticBody3D" parent="{pid}"]')
                nodes.append("")
                nodes.append(f'[node name="CollisionShape3D" type="CollisionShape3D" parent="{pid}/StaticBody3D"]')
                nodes.append(f'shape = SubResource("BoxShape3D_{res_idx}")')
                nodes.append("")

            res_idx += 1

        elif ptype == "camera":
            is_current = "true" if piece.get("current") is True else "false"
            nodes.append(f'[node name="{pid}" type="Camera3D" parent="."]')
            nodes.append(f"transform = {transform_str}")
            nodes.append(f"current = {is_current}")
            nodes.append("")

        elif ptype == "light":
            ltype = piece.get("type", "directional")
            if ltype == "directional":
                nodes.append(f'[node name="{pid}" type="DirectionalLight3D" parent="."]')
                nodes.append(f"transform = {transform_str}")
                nodes.append("")
            elif ltype == "omni":
                energy = float(piece.get("energy", 1.0))
                range_val = float(piece.get("range", 5.0))
                shadows = "true" if piece.get("shadows") is True else "false"

                nodes.append(f'[node name="{pid}" type="OmniLight3D" parent="."]')
                nodes.append(f"transform = {transform_str}")
                nodes.append(f"light_energy = {energy}")
                nodes.append(f"omni_range = {range_val}")
                nodes.append(f"shadow_enabled = {shadows}")
                nodes.append("")

        elif ptype == "player":
            root_node = piece.get("root_node", "CharacterBody3D")
            script_attr = ""
            script_path = piece.get("movement_script")
            if script_path:
                ext_resources.append(f'[ext_resource type="Script" path="{script_path}" id="Script_{res_idx}"]')
                script_attr = f'\nscript = ExtResource("Script_{res_idx}")'

            nodes.append(f'[node name="{pid}" type="{root_node}" parent="."]{script_attr}')
            nodes.append(f"transform = {transform_str}")
            nodes.append("")

            # Add child CollisionShape3D (radius=0.5, height=2.0)
            sub_resources.append(f'[sub_resource type="CapsuleShape3D" id="CapsuleShape3D_{res_idx}"]')
            sub_resources.append("radius = 0.5")
            sub_resources.append("height = 2.0")
            sub_resources.append("")

            nodes.append(f'[node name="CollisionShape3D" type="CollisionShape3D" parent="{pid}"]')
            nodes.append(f'shape = SubResource("CapsuleShape3D_{res_idx}")')
            nodes.append("")

            # Add child MeshInstance3D (CapsuleMesh for player body visibility)
            sub_resources.append(f'[sub_resource type="CapsuleMesh" id="CapsuleMesh_{res_idx}"]')
            sub_resources.append("radius = 0.5")
            sub_resources.append("height = 2.0")
            sub_resources.append("")

            nodes.append(f'[node name="MeshInstance3D" type="MeshInstance3D" parent="{pid}"]')
            nodes.append(f'mesh = SubResource("CapsuleMesh_{res_idx}")')
            nodes.append("")

            res_idx += 1

        elif ptype == "marker":
            mesh_type = piece.get("mesh", "cube")
            color_val = piece.get("color")
            collision = piece.get("collision") is True

            # 1. Mesh
            mesh_sub_type = "BoxMesh"
            if mesh_type == "cylinder":
                mesh_sub_type = "CylinderMesh"
            elif mesh_type == "sphere":
                mesh_sub_type = "SphereMesh"

            sub_resources.append(f'[sub_resource type="{mesh_sub_type}" id="{mesh_sub_type}_{res_idx}"]')
            sub_resources.append("size = Vector3(1, 1, 1)" if mesh_sub_type != "SphereMesh" else "radius = 0.5\nheight = 1.0")
            sub_resources.append("")

            # 2. Material
            sub_resources.append(f'[sub_resource type="StandardMaterial3D" id="StandardMaterial3D_{res_idx}"]')
            if isinstance(color_val, list) and len(color_val) >= 3:
                r, g, b = color_val[0], color_val[1], color_val[2]
                a = color_val[3] if len(color_val) > 3 else 1.0
                sub_resources.append(f"albedo_color = Color({r:.6g}, {g:.6g}, {b:.6g}, {a:.6g})")
            elif isinstance(color_val, str):
                sub_resources.append(f'albedo_color = Color("{color_val}")')
            else:
                sub_resources.append("albedo_color = Color(1, 0, 0, 1)")
            sub_resources.append("")

            nodes.append(f'[node name="{pid}" type="MeshInstance3D" parent="."]')
            nodes.append(f"transform = {transform_str}")
            nodes.append(f'mesh = SubResource("{mesh_sub_type}_{res_idx}")')
            nodes.append(f'material_override = SubResource("StandardMaterial3D_{res_idx}")')
            nodes.append("")

            # 3. Collision
            if collision:
                shape_sub_type = "BoxShape3D"
                if mesh_type == "cylinder":
                    shape_sub_type = "CylinderShape3D"
                elif mesh_type == "sphere":
                    shape_sub_type = "SphereShape3D"

                sub_resources.append(f'[sub_resource type="{shape_sub_type}" id="{shape_sub_type}_{res_idx}"]')
                sub_resources.append("size = Vector3(1, 1, 1)" if shape_sub_type != "SphereShape3D" else "radius = 0.5")
                sub_resources.append("")

                nodes.append(f'[node name="StaticBody3D" type="StaticBody3D" parent="{pid}"]')
                nodes.append("")
                nodes.append(f'[node name="CollisionShape3D" type="CollisionShape3D" parent="{pid}/StaticBody3D"]')
                nodes.append(f'shape = SubResource("{shape_sub_type}_{res_idx}")')
                nodes.append("")

            res_idx += 1

        elif ptype in ("box", "platform"):
            collision = piece.get("collision") is True if ptype == "box" else True
            
            sub_resources.append(f'[sub_resource type="BoxMesh" id="BoxMesh_{res_idx}"]')
            sub_resources.append("size = Vector3(1, 1, 1)")
            sub_resources.append("")

            nodes.append(f'[node name="{pid}" type="MeshInstance3D" parent="."]')
            nodes.append(f"transform = {transform_str}")
            nodes.append(f'mesh = SubResource("BoxMesh_{res_idx}")')
            nodes.append("")

            if collision:
                sub_resources.append(f'[sub_resource type="BoxShape3D" id="BoxShape3D_{res_idx}"]')
                sub_resources.append("size = Vector3(1, 1, 1)")
                sub_resources.append("")

                nodes.append(f'[node name="StaticBody3D" type="StaticBody3D" parent="{pid}"]')
                nodes.append("")
                nodes.append(f'[node name="CollisionShape3D" type="CollisionShape3D" parent="{pid}/StaticBody3D"]')
                nodes.append(f'shape = SubResource("BoxShape3D_{res_idx}")')
                nodes.append("")

            res_idx += 1

        elif ptype == "ramp":
            # Ramp must include collision and is built as a sloped box (approximated)
            reasons.append("RAMP_WEDGE_APPROXIMATION_USED")
            
            sub_resources.append(f'[sub_resource type="BoxMesh" id="BoxMesh_{res_idx}"]')
            sub_resources.append("size = Vector3(1, 1, 1)")
            sub_resources.append("")

            nodes.append(f'[node name="{pid}" type="MeshInstance3D" parent="."]')
            nodes.append(f"transform = {transform_str}")
            nodes.append(f'mesh = SubResource("BoxMesh_{res_idx}")')
            nodes.append("")

            sub_resources.append(f'[sub_resource type="BoxShape3D" id="BoxShape3D_{res_idx}"]')
            sub_resources.append("size = Vector3(1, 1, 1)")
            sub_resources.append("")

            nodes.append(f'[node name="StaticBody3D" type="StaticBody3D" parent="{pid}"]')
            nodes.append("")
            nodes.append(f'[node name="CollisionShape3D" type="CollisionShape3D" parent="{pid}/StaticBody3D"]')
            nodes.append(f'shape = SubResource("BoxShape3D_{res_idx}")')
            nodes.append("")

            res_idx += 1

        elif ptype == "trigger_zone":
            monitoring_val = "true" if piece.get("monitoring") is True else "false"
            
            nodes.append(f'[node name="{pid}" type="Area3D" parent="."]')
            nodes.append(f"transform = {transform_str}")
            nodes.append(f"monitoring = {monitoring_val}")
            nodes.append("")

            sub_resources.append(f'[sub_resource type="BoxShape3D" id="BoxShape3D_{res_idx}"]')
            sub_resources.append("size = Vector3(1, 1, 1)")
            sub_resources.append("")

            nodes.append(f'[node name="CollisionShape3D" type="CollisionShape3D" parent="{pid}"]')
            nodes.append(f'shape = SubResource("BoxShape3D_{res_idx}")')
            nodes.append("")

            res_idx += 1

        elif ptype == "door":
            collision = piece.get("collision") is True
            
            sub_resources.append(f'[sub_resource type="BoxMesh" id="BoxMesh_{res_idx}"]')
            sub_resources.append("size = Vector3(1, 1, 1)")
            sub_resources.append("")

            nodes.append(f'[node name="{pid}" type="MeshInstance3D" parent="."]')
            nodes.append(f"transform = {transform_str}")
            nodes.append(f'mesh = SubResource("BoxMesh_{res_idx}")')
            nodes.append(f'material_override = SubResource("StandardMaterial3D_{res_idx}")')
            nodes.append("")

            sub_resources.append(f'[sub_resource type="StandardMaterial3D" id="StandardMaterial3D_{res_idx}"]')
            sub_resources.append("albedo_color = Color(0.4, 0.2, 0.1, 1.0)")
            sub_resources.append("")

            if collision:
                sub_resources.append(f'[sub_resource type="BoxShape3D" id="BoxShape3D_{res_idx}"]')
                sub_resources.append("size = Vector3(1, 1, 1)")
                sub_resources.append("")

                nodes.append(f'[node name="StaticBody3D" type="StaticBody3D" parent="{pid}"]')
                nodes.append("")
                nodes.append(f'[node name="CollisionShape3D" type="CollisionShape3D" parent="{pid}/StaticBody3D"]')
                nodes.append(f'shape = SubResource("BoxShape3D_{res_idx}")')
                nodes.append("")

            res_idx += 1

    # Update load_steps count in tscn header if resources exist
    total_resources = (len(sub_resources) // 3) + len(ext_resources)
    if total_resources > 0:
        tscn_header = f"[gd_scene load_steps={total_resources + 1} format=3]\n\n"

    # Assemble and write file
    ext_content = "\n".join(ext_resources) + "\n\n" if ext_resources else ""
    sub_content = "\n".join(sub_resources) + "\n\n" if sub_resources else ""
    full_content = tscn_header + ext_content + sub_content + "\n".join(nodes)
    
    try:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(full_content, encoding="utf-8")
        msg = f"Scene successfully built and written to {output_path}."
        print(f"[godot_scene_piece_builder][BUILT] {msg}")
        return STATUS_BUILT, [msg]
    except Exception as e:
        err_msg = f"Failed to write scene file: {e}"
        print(f"[godot_scene_piece_builder][ERROR] {err_msg}")
        return STATUS_BUILD_REJECTED, [err_msg]
