"""
mesh_intake.py - The Mesh Intake Gate

THE LAW: Single entry point for all geometry entering EngAIn.

All tools must pass through this gate:
- Wings 3D → intake_mesh()
- MeshLab → intake_mesh()
- MagicaVoxel → intake_mesh()
- Blender/AI → intake_mesh()

If it passes here, it's eligible for skin_3d_id binding.
If it fails, it never reaches Godot/EngAIn.
"""

import os
import hashlib
from pathlib import Path
from typing import Tuple, Optional, List

from mesh_manifest import (
    TrixelManifest,
    create_trixel_manifest,
    save_trixel_manifest,
    Anchor,
    Region
)


def count_vertices_faces(obj_path: Path) -> Tuple[int, int]:
    """
    Count vertices and faces in OBJ file.
    
    Simple parser - no heavy dependencies.
    
    Args:
        obj_path: Path to .obj file
    
    Returns:
        (vertex_count, face_count)
    """
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
    """
    Compute SHA256 hash of mesh file.
    
    For change detection and provenance.
    
    Args:
        obj_path: Path to mesh
    
    Returns:
        SHA256 hex string
    """
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
    
    Process:
    1. Read OBJ
    2. Compute vertex/face counts
    3. Compute mesh hash
    4. Build manifest
    5. Validate against Trixel law
    6. Return manifest or raise
    
    Args:
        obj_path: Path to .obj file
        zw_concept: Semantic identity (e.g., "guard")
        ap_profile: AP rule profile (e.g., "damageable_npc")
        collision_role: Physics intent ("solid", "trigger", "none")
        lod_class: LOD category ("character", "prop", "environment", "detail")
        placeholder_mesh: Fallback ("cube", "capsule", etc.)
        source_tool: Tool that created this ("wings3d", "magicavoxel", etc.)
        anchors: Optional attachment points
        regions: Optional mesh regions
    
    Returns:
        Validated TrixelManifest
    
    Raises:
        FileNotFoundError: If OBJ doesn't exist
        ValueError: If validation fails
    
    Example:
        >>> manifest = intake_mesh(
        ...     Path("guard.obj"),
        ...     zw_concept="guard",
        ...     ap_profile="damageable_npc",
        ...     collision_role="solid",
        ...     lod_class="character",
        ...     placeholder_mesh="capsule",
        ...     source_tool="wings3d"
        ... )
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
    
    return manifest
