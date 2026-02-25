"""
mesh_intake.py - The Mesh Intake Gate

THE LAW: Single entry point for all geometry entering EngAIn.
"""

import os
import hashlib
from pathlib import Path
from typing import Tuple, Optional, List

from mesh_manifest import (
    TrixelManifest,
    create_trixel_manifest,
    Anchor,
    Region
)


def count_vertices_faces(obj_path: Path) -> Tuple[int, int]:
    """Count vertices and faces in OBJ file."""
    if not os.path.exists(obj_path):
        raise FileNotFoundError(f"OBJ not found: {obj_path}")
    
    verts, faces = 0, 0
    
    with open(obj_path, 'r') as f:
        for line in f:
            stripped = line.strip()
            if stripped.startswith('v '):
                verts += 1
            elif stripped.startswith('f '):
                faces += 1
    
    return verts, faces


def compute_mesh_hash(obj_path: Path) -> str:
    """Compute SHA256 hash of mesh file."""
    sha256 = hashlib.sha256()
    
    with open(obj_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    
    return sha256.hexdigest()


def intake_mesh(
    obj_path: Path,
    *,
    zw_concept: str,
    ap_profile: str,
    collision_role: str,
    lod_class: str,
    placeholder_mesh: str,
    source_tool: str,
    anchors: Optional[List[Anchor]] = None,
    regions: Optional[List[Region]] = None
) -> TrixelManifest:
    """
    THE MESH INTAKE GATE - Single entry point for all geometry.
    
    Returns:
        Validated TrixelManifest
    
    Raises:
        FileNotFoundError: If OBJ doesn't exist
        ValueError: If validation fails
    """
    # 1. Verify file exists
    if not obj_path.exists():
        raise FileNotFoundError(f"Mesh not found: {obj_path}")
    
    # 2. Compute stats
    verts, faces = count_vertices_faces(obj_path)
    mesh_hash = compute_mesh_hash(obj_path)
    
    # 3. Build manifest
    manifest = create_trixel_manifest(
        zw_concept=zw_concept,
        ap_profile=ap_profile,
        collision_role=collision_role,
        lod_class=lod_class,
        placeholder_mesh=placeholder_mesh,
        source_tool=source_tool,
        source_file=str(obj_path),
        export_format="obj",
        vertex_count=verts,
        face_count=faces
    )
    
    # 4. Set computed fields
    manifest.mesh_path = str(obj_path)
    manifest.mesh_hash = mesh_hash
    
    if anchors:
        manifest.anchors = anchors
    if regions:
        manifest.regions = regions
    
    # 5. Validate against Trixel law
    errors = manifest.validate()
    if errors:
        raise ValueError(
            f"INTAKE REJECTED: {obj_path}\n" +
            "\n".join(f"  - {e}" for e in errors)
        )
    
    # 6. Return validated manifest
    return manifest
