# piece3d_mr.py
"""
Piece3D MR Kernel - Pure Functional Piece Validation
Deterministic, renderer-agnostic, snapshot-in/snapshot-out.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

# Constants for status
STATUS_ACCEPTED = "ACCEPTED"
STATUS_REJECTED = "REJECTED"
STATUS_SUSPENDED = "SUSPENDED"


def find_manifest_path() -> Path:
    """Find the piece baseline manifest file path robustly."""
    possible_paths = [
        Path("/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/docs/contracts/ENGAINOS_TIER1_AUTHORITY/engainos_1stlane_governance_authority/piece_baseline_manifest.json"),
        Path(__file__).resolve().parents[3] / "docs/contracts/ENGAINOS_TIER1_AUTHORITY/engainos_1stlane_governance_authority/piece_baseline_manifest.json",
        Path("docs/contracts/ENGAINOS_TIER1_AUTHORITY/engainos_1stlane_governance_authority/piece_baseline_manifest.json"),
    ]
    for p in possible_paths:
        if p.exists():
            return p
    raise FileNotFoundError("Could not find piece_baseline_manifest.json")


def load_baseline_manifest(manifest_path: Optional[str] = None) -> Dict[str, Any]:
    """Load and parse the piece baseline manifest JSON."""
    if manifest_path:
        path = Path(manifest_path)
    else:
        path = find_manifest_path()

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def validate_pieces(
    demanded_pieces: List[Dict[str, Any]],
    manifest_path: Optional[str] = None
) -> Tuple[str, List[str]]:
    """
    Validate a list of demanded pieces against the baseline manifest.

    Args:
        demanded_pieces: List of dictionaries, each representing a demanded piece.
        manifest_path: Optional path override to the piece_baseline_manifest.json.

    Returns:
        A tuple of (status, reasons) where status is one of ACCEPTED, REJECTED, SUSPENDED,
        and reasons is a list of strings explaining the decision.
    """
    reasons: List[str] = []
    
    try:
        manifest = load_baseline_manifest(manifest_path)
    except Exception as e:
        err_msg = f"Failed to load baseline manifest: {e}"
        print(f"[piece3d_mr][ERROR] {err_msg}")
        return STATUS_REJECTED, [err_msg]

    # Basic structure check
    spec_version = manifest.get("spec_version")
    if spec_version != "engainos.piece_baseline.v1":
        err_msg = f"Unsupported spec_version: {spec_version}"
        print(f"[piece3d_mr][ERROR] {err_msg}")
        return STATUS_REJECTED, [err_msg]

    default_policy = manifest.get("default_policy", "none")
    piece_specs = manifest.get("pieces", {})
    demand_schema = manifest.get("demand_schema", {})
    
    # Extract discriminator key from manifest schema
    discriminator_key = demand_schema.get("piece_discriminator", "piece_type")
    discriminator_required = demand_schema.get("piece_discriminator_required", True)
    must_match_piece_key = demand_schema.get("piece_discriminator_must_match_piece_key", True)

    if not demanded_pieces:
        sus_msg = "No demanded pieces provided for validation."
        print(f"[piece3d_mr][SUSPENDED] {sus_msg}")
        return STATUS_SUSPENDED, [sus_msg]

    for idx, piece in enumerate(demanded_pieces):
        if not isinstance(piece, dict):
            err_msg = f"piece index {idx} is not a valid dictionary"
            print(f"[piece3d_mr][REJECTED] {err_msg}")
            return STATUS_REJECTED, [err_msg]

        # Enforce discriminator key
        piece_type = piece.get(discriminator_key)
        if not piece_type:
            if discriminator_required:
                err_msg = f"piece index {idx} missing {discriminator_key}"
                print(f"[piece3d_mr][REJECTED] {err_msg}")
                return STATUS_REJECTED, [err_msg]
            else:
                continue

        piece_type = str(piece_type).strip().lower()

        # Check if type is defined in the manifest
        if piece_type not in piece_specs:
            if must_match_piece_key or default_policy == "none":
                err_msg = f"{piece_type} type not allowed by policy"
                print(f"[piece3d_mr][REJECTED] {err_msg}")
                return STATUS_REJECTED, [err_msg]
            else:
                continue

        spec = piece_specs[piece_type]

        # 1. Validate required fields
        required_fields = spec.get("required_fields", [])
        for field in required_fields:
            if field not in piece:
                err_msg = f"{piece_type} missing {field}"
                print(f"[piece3d_mr][REJECTED] {err_msg}")
                return STATUS_REJECTED, [err_msg]

        # 2. Validate allowed values
        allowed_values = spec.get("allowed_values", {})
        for field, allowed_list in allowed_values.items():
            if field in piece:
                val = piece[field]
                if val not in allowed_list:
                    err_msg = f"{piece_type} disallowed value for {field}: {val}"
                    print(f"[piece3d_mr][REJECTED] {err_msg}")
                    return STATUS_REJECTED, [err_msg]

        # 3. Validate conditional required fields
        conditional_required = spec.get("conditional_required_fields", {})
        for trigger_field, conditions in conditional_required.items():
            if trigger_field in piece:
                trigger_value = piece[trigger_field]
                if trigger_value in conditions:
                    cond_required = conditions[trigger_value]
                    for field in cond_required:
                        if field not in piece:
                            err_msg = f"{piece_type} missing conditional field {field} because {trigger_field} is {trigger_value}"
                            print(f"[piece3d_mr][REJECTED] {err_msg}")
                            return STATUS_REJECTED, [err_msg]

    ok_msg = "All demanded pieces validated successfully against the baseline manifest."
    print(f"[piece3d_mr][ACCEPTED] {ok_msg}")
    return STATUS_ACCEPTED, [ok_msg]


# New validation for marker
def validate_marker(piece: Dict[str, Any]) -> Tuple[str, List[str]]:
    required_fields = ["mesh", "position", "scale", "color", "collision"]
    allowed_meshes = ["cube", "cylinder", "sphere"]
    allowed_collision = [True, False]

    reasons: List[str] = []

    for field in required_fields:
        if field not in piece:
            reasons.append(f"marker missing {field}")
            return STATUS_REJECTED, reasons

    mesh = piece.get("mesh")
    if mesh not in allowed_meshes:
        reasons.append(f"marker disallowed value for mesh: {mesh}")
        return STATUS_REJECTED, reasons

    collision = piece.get("collision")
    if collision not in allowed_collision:
        reasons.append(f"marker disallowed value for collision: {collision}")
        return STATUS_REJECTED, reasons

    return STATUS_ACCEPTED, []


# New validation for box
def validate_box(piece: Dict[str, Any]) -> Tuple[str, List[str]]:
    required_fields = ["mesh", "position", "scale", "collision"]
    allowed_meshes = ["cube"]
    allowed_collision = [True, False]

    reasons: List[str] = []

    for field in required_fields:
        if field not in piece:
            reasons.append(f"box missing {field}")
            return STATUS_REJECTED, reasons

    mesh = piece.get("mesh")
    if mesh not in allowed_meshes:
        reasons.append(f"box disallowed value for mesh: {mesh}")
        return STATUS_REJECTED, reasons

    collision = piece.get("collision")
    if collision not in allowed_collision:
        reasons.append(f"box disallowed value for collision: {collision}")
        return STATUS_REJECTED, reasons

    return STATUS_ACCEPTED, []


# New validation for ramp
def validate_ramp(piece: Dict[str, Any]) -> Tuple[str, List[str]]:
    required_fields = ["mesh", "position", "rotation", "scale", "collision"]
    allowed_meshes = ["wedge"]
    allowed_collision = [True]

    reasons: List[str] = []

    for field in required_fields:
        if field not in piece:
            reasons.append(f"ramp missing {field}")
            return STATUS_REJECTED, reasons

    mesh = piece.get("mesh")
    if mesh not in allowed_meshes:
        reasons.append(f"ramp disallowed value for mesh: {mesh}")
        return STATUS_REJECTED, reasons

    collision = piece.get("collision")
    if collision not in allowed_collision:
        reasons.append(f"ramp disallowed value for collision: {collision}")
        return STATUS_REJECTED, reasons

    return STATUS_ACCEPTED, []


# New validation for platform
def validate_platform(piece: Dict[str, Any]) -> Tuple[str, List[str]]:
    required_fields = ["mesh", "position", "scale", "collision"]
    allowed_meshes = ["cube"]
    allowed_collision = [True]

    reasons: List[str] = []

    for field in required_fields:
        if field not in piece:
            reasons.append(f"platform missing {field}")
            return STATUS_REJECTED, reasons

    mesh = piece.get("mesh")
    if mesh not in allowed_meshes:
        reasons.append(f"platform disallowed value for mesh: {mesh}")
        return STATUS_REJECTED, reasons

    collision = piece.get("collision")
    if collision not in allowed_collision:
        reasons.append(f"platform disallowed value for collision: {collision}")
        return STATUS_REJECTED, reasons

    return STATUS_ACCEPTED, []


# New validation for trigger_zone
def validate_trigger_zone(piece: Dict[str, Any]) -> Tuple[str, List[str]]:
    required_fields = ["shape", "position", "scale", "monitoring"]
    allowed_shapes = ["box"]
    allowed_monitoring = [True, False]

    reasons: List[str] = []

    for field in required_fields:
        if field not in piece:
            reasons.append(f"trigger_zone missing {field}")
            return STATUS_REJECTED, reasons

    shape = piece.get("shape")
    if shape not in allowed_shapes:
        reasons.append(f"trigger_zone disallowed value for shape: {shape}")
        return STATUS_REJECTED, reasons

    monitoring = piece.get("monitoring")
    if monitoring not in allowed_monitoring:
        reasons.append(f"trigger_zone disallowed value for monitoring: {monitoring}")
        return STATUS_REJECTED, reasons

    return STATUS_ACCEPTED, []


# Update validate_pieces to include new validations
def validate_pieces(
    demanded_pieces: List[Dict[str, Any]],
    manifest_path: Optional[str] = None
) -> Tuple[str, List[str]]:
    reasons: List[str] = []
    
    try:
        manifest = load_baseline_manifest(manifest_path)
    except Exception as e:
        err_msg = f"Failed to load baseline manifest: {e}"
        print(f"[piece3d_mr][ERROR] {err_msg}")
        return STATUS_REJECTED, [err_msg]

    # Basic structure check
    spec_version = manifest.get("spec_version")
    if spec_version != "engainos.piece_baseline.v1":
        err_msg = f"Unsupported spec_version: {spec_version}"
        print(f"[piece3d_mr][ERROR] {err_msg}")
        return STATUS_REJECTED, [err_msg]

    default_policy = manifest.get("default_policy", "none")
    piece_specs = manifest.get("pieces", {})
    demand_schema = manifest.get("demand_schema", {})
    
    # Extract discriminator key from manifest schema
    discriminator_key = demand_schema.get("piece_discriminator", "piece_type")
    discriminator_required = demand_schema.get("piece_discriminator_required", True)
    must_match_piece_key = demand_schema.get("piece_discriminator_must_match_piece_key", True)

    if not demanded_pieces:
        sus_msg = "No demanded pieces provided for validation."
        print(f"[piece3d_mr][SUSPENDED] {sus_msg}")
        return STATUS_SUSPENDED, [sus_msg]

    for idx, piece in enumerate(demanded_pieces):
        if not isinstance(piece, dict):
            err_msg = f"piece index {idx} is not a valid dictionary"
            print(f"[piece3d_mr][REJECTED] {err_msg}")
            return STATUS_REJECTED, [err_msg]

        # Enforce discriminator key
        piece_type = piece.get(discriminator_key)
        if not piece_type:
            if discriminator_required:
                err_msg = f"piece index {idx} missing {discriminator_key}"
                print(f"[piece3d_mr][REJECTED] {err_msg}")
                return STATUS_REJECTED, [err_msg]
            else:
                continue

        piece_type = str(piece_type).strip().lower()

        # Check if type is defined in the manifest
        if piece_type not in piece_specs:
            if must_match_piece_key or default_policy == "none":
                err_msg = f"{piece_type} type not allowed by policy"
                print(f"[piece3d_mr][REJECTED] {err_msg}")
                return STATUS_REJECTED, [err_msg]
            else:
                continue

        spec = piece_specs[piece_type]

        # 1. Validate required fields
        required_fields = spec.get("required_fields", [])
        for field in required_fields:
            if field not in piece:
                err_msg = f"{piece_type} missing {field}"
                print(f"[piece3d_mr][REJECTED] {err_msg}")
                return STATUS_REJECTED, [err_msg]

        # 2. Validate allowed values
        allowed_values = spec.get("allowed_values", {})
        for field, allowed_list in allowed_values.items():
            if field in piece:
                val = piece[field]
                if val not in allowed_list:
                    err_msg = f"{piece_type} disallowed value for {field}: {val}"
                    print(f"[piece3d_mr][REJECTED] {err_msg}")
                    return STATUS_REJECTED, [err_msg]

        # 3. Validate conditional required fields
        conditional_required = spec.get("conditional_required_fields", {})
        for trigger_field, conditions in conditional_required.items():
            if trigger_field in piece:
                trigger_value = piece[trigger_field]
                if trigger_value in conditions:
                    cond_required = conditions[trigger_value]
                    for field in cond_required:
                        if field not in piece:
                            err_msg = f"{piece_type} missing conditional field {field} because {trigger_field} is {trigger_value}"
                            print(f"[piece3d_mr][REJECTED] {err_msg}")
                            return STATUS_REJECTED, [err_msg]

        # 4. Validate specific types
        if piece_type == "marker":
            status, reasons = validate_marker(piece)
            if status != STATUS_ACCEPTED:
                return status, reasons

        elif piece_type == "box":
            status, reasons = validate_box(piece)
            if status != STATUS_ACCEPTED:
                return status, reasons

        elif piece_type == "ramp":
            status, reasons = validate_ramp(piece)
            if status != STATUS_ACCEPTED:
                return status, reasons

        elif piece_type == "platform":
            status, reasons = validate_platform(piece)
            if status != STATUS_ACCEPTED:
                return status, reasons

        elif piece_type == "trigger_zone":
            status, reasons = validate_trigger_zone(piece)
            if status != STATUS_ACCEPTED:
                return status, reasons

    ok_msg = "All demanded pieces validated successfully against the baseline manifest."
    print(f"[piece3d_mr][ACCEPTED] {ok_msg}")
    return STATUS_ACCEPTED, [ok_msg]
