"""
mesh_manifest.py - Trixel Manifest Validator

Bridges semantic intent (Trixel) with geometry reality (mesh files).

Responsibilities:
1. Load and validate .trixel manifests
2. Verify mesh files exist and meet constraints
3. Generate skin_3d_id references for spatial_skin_system
4. Detect changes for round-trip workflows

This module is the CONTRACT ENFORCER between Trixel law and mesh tools.
"""

import json
import os
import hashlib
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
from pathlib import Path


@dataclass
class Anchor:
    """Semantic attachment point on a mesh"""
    name: str                # e.g., "hand_right", "head"
    position: List[float]    # [x, y, z]
    purpose: str             # e.g., "weapon_attachment", "helmet_attachment"


@dataclass
class Region:
    """Semantic mesh region (for materials, collision, etc.)"""
    name: str                # e.g., "torso", "shield"
    material_slot: int       # Material index in mesh
    collision: str           # e.g., "body", "equipment", "none"


@dataclass
class GeometryInfo:
    """Geometry source and export information"""
    source_tool: str         # e.g., "wings3d", "magicavoxel"
    source_file: str         # Path to source file
    export_format: str       # e.g., "obj", "gltf"
    vertex_count: int
    face_count: int


@dataclass
class Processing:
    """Mesh processing pipeline information"""
    meshlab_preset: Optional[str] = None     # e.g., "character_optimize"
    target_vertex_count: Optional[int] = None
    preserve_uvs: bool = True
    preserve_normals: bool = True


@dataclass
class TrixelManifest:
    """
    Complete Trixel manifest with validation.
    
    This is the CONTRACT between semantic intent and geometry reality.
    Every 3D mesh MUST have a valid manifest.
    """
    # Core semantic identity (REQUIRED)
    trixel_version: str          # Manifest schema version
    zw_concept: str              # Semantic identity (e.g., "guard")
    ap_profile: str              # AP rule set (e.g., "damageable_npc")
    collision_role: str          # Physics intent (e.g., "solid", "trigger")
    lod_class: str               # LOD category (e.g., "character", "prop")
    placeholder_mesh: str        # Fallback (e.g., "capsule", "cube")
    
    # Geometry reference
    geometry: GeometryInfo
    
    # Optional processing pipeline
    processing: Processing = field(default_factory=Processing)
    
    # Semantic metadata
    anchors: List[Anchor] = field(default_factory=list)
    regions: List[Region] = field(default_factory=list)
    
    # Runtime fields (set by validator)
    manifest_path: Optional[str] = None
    mesh_path: Optional[str] = None
    mesh_hash: Optional[str] = None
    
    def validate(self) -> List[str]:
        """
        Validate manifest against Trixel Pipeline v1 contract.
        
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        
        # Check required fields
        if not self.trixel_version:
            errors.append("Missing trixel_version")
        elif self.trixel_version != "1.0":
            errors.append(f"Unsupported trixel_version: {self.trixel_version}")
        
        if not self.zw_concept:
            errors.append("Missing zw_concept")
        
        if not self.ap_profile:
            errors.append("Missing ap_profile")
        
        if not self.collision_role:
            errors.append("Missing collision_role")
        elif self.collision_role not in ["solid", "trigger", "none", "static"]:
            errors.append(f"Invalid collision_role: {self.collision_role}")
        
        if not self.lod_class:
            errors.append("Missing lod_class")
        elif self.lod_class not in ["character", "prop", "environment", "detail"]:
            errors.append(f"Invalid lod_class: {self.lod_class}")
        
        if not self.placeholder_mesh:
            errors.append("Missing placeholder_mesh")
        elif self.placeholder_mesh not in ["cube", "capsule", "cylinder", "plane", "sphere"]:
            errors.append(f"Invalid placeholder_mesh: {self.placeholder_mesh}")
        
        # Check geometry constraints
        if self.geometry.vertex_count > 5000:
            errors.append(
                f"Vertex count too high: {self.geometry.vertex_count} (max 5000 for real-time)"
            )
        
        if self.geometry.vertex_count <= 0:
            errors.append("Invalid vertex_count (must be > 0)")
        
        if self.geometry.face_count <= 0:
            errors.append("Invalid face_count (must be > 0)")
        
        # Check mesh file exists
        if self.mesh_path and not os.path.exists(self.mesh_path):
            errors.append(f"Mesh file not found: {self.mesh_path}")
        
        # Validate anchors
        for anchor in self.anchors:
            if len(anchor.position) != 3:
                errors.append(f"Anchor '{anchor.name}' has invalid position (must be [x,y,z])")
        
        # Validate regions
        material_slots = set()
        for region in self.regions:
            if region.material_slot in material_slots:
                errors.append(f"Duplicate material_slot: {region.material_slot}")
            material_slots.add(region.material_slot)
        
        return errors
    
    def is_valid(self) -> bool:
        """Check if manifest is valid"""
        return len(self.validate()) == 0
    
    def to_skin_reference(self) -> str:
        """
        Generate skin_3d_id for spatial_skin_system.
        
        Returns:
            Path like "meshes/guard/guard_opt.obj"
        """
        if not self.mesh_path:
            raise ValueError("mesh_path not set - call resolve_mesh_path() first")
        
        # Generate relative path for runtime
        mesh_filename = os.path.basename(self.mesh_path)
        return f"meshes/{self.zw_concept}/{mesh_filename}"
    
    def compute_mesh_hash(self) -> str:
        """
        Compute hash of mesh file for change detection.
        
        Returns:
            SHA256 hash of mesh file
        """
        if not self.mesh_path or not os.path.exists(self.mesh_path):
            return ""
        
        sha256 = hashlib.sha256()
        with open(self.mesh_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """Export to dictionary for JSON serialization"""
        return asdict(self)


def load_trixel_manifest(json_path: str) -> TrixelManifest:
    """
    Load and validate .trixel manifest from JSON file.
    
    Args:
        json_path: Path to .trixel manifest file
    
    Returns:
        Validated TrixelManifest
    
    Raises:
        ValueError: If manifest is invalid
        FileNotFoundError: If manifest file doesn't exist
    """
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"Manifest not found: {json_path}")
    
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    # Parse nested structures
    geometry_data = data.pop('geometry')
    geometry = GeometryInfo(**geometry_data)
    
    processing_data = data.pop('processing', {})
    processing = Processing(**processing_data)
    
    anchors_data = data.pop('anchors', [])
    anchors = [Anchor(**a) for a in anchors_data]
    
    regions_data = data.pop('regions', [])
    regions = [Region(**r) for r in regions_data]
    
    # Create manifest
    manifest = TrixelManifest(
        **data,
        geometry=geometry,
        processing=processing,
        anchors=anchors,
        regions=regions
    )
    
    # Set manifest path
    manifest.manifest_path = json_path
    
    # Resolve mesh path (relative to manifest)
    manifest_dir = os.path.dirname(json_path)
    source_dir = os.path.join(manifest_dir, "..", "meshes", manifest.zw_concept)
    
    # Look for optimized mesh first, fall back to base
    for candidate in [
        os.path.join(source_dir, f"{manifest.zw_concept}_opt.{geometry.export_format}"),
        os.path.join(source_dir, f"{manifest.zw_concept}_base.{geometry.export_format}"),
        os.path.join(source_dir, f"{manifest.zw_concept}.{geometry.export_format}"),
    ]:
        if os.path.exists(candidate):
            manifest.mesh_path = candidate
            manifest.mesh_hash = manifest.compute_mesh_hash()
            break
    
    # Validate
    errors = manifest.validate()
    if errors:
        raise ValueError(f"Invalid Trixel manifest '{json_path}':\n" + "\n".join(f"  - {e}" for e in errors))
    
    return manifest


def save_trixel_manifest(manifest: TrixelManifest, json_path: str):
    """
    Save Trixel manifest to JSON file.
    
    Args:
        manifest: TrixelManifest to save
        json_path: Output path for .trixel file
    """
    # Validate before saving
    errors = manifest.validate()
    if errors:
        raise ValueError(f"Cannot save invalid manifest:\n" + "\n".join(f"  - {e}" for e in errors))
    
    # Convert to dict and save
    data = manifest.to_dict()
    
    # Remove runtime fields
    data.pop('manifest_path', None)
    data.pop('mesh_path', None)
    data.pop('mesh_hash', None)
    
    with open(json_path, 'w') as f:
        json.dump(data, f, indent=2)


def create_trixel_manifest(
    zw_concept: str,
    ap_profile: str,
    collision_role: str,
    lod_class: str,
    placeholder_mesh: str,
    source_tool: str,
    source_file: str,
    export_format: str = "obj",
    vertex_count: int = 0,
    face_count: int = 0
) -> TrixelManifest:
    """
    Create a new Trixel manifest with sensible defaults.
    
    This is the programmatic equivalent of `trixel create` CLI.
    """
    geometry = GeometryInfo(
        source_tool=source_tool,
        source_file=source_file,
        export_format=export_format,
        vertex_count=vertex_count,
        face_count=face_count
    )
    
    return TrixelManifest(
        trixel_version="1.0",
        zw_concept=zw_concept,
        ap_profile=ap_profile,
        collision_role=collision_role,
        lod_class=lod_class,
        placeholder_mesh=placeholder_mesh,
        geometry=geometry
    )


def detect_mesh_changes(manifest: TrixelManifest) -> Optional[str]:
    """
    Detect if mesh file has changed since manifest was created.
    
    Returns:
        None if unchanged, description of change if modified
    """
    if not manifest.mesh_path:
        return "Mesh path not resolved"
    
    if not os.path.exists(manifest.mesh_path):
        return "Mesh file missing"
    
    current_hash = manifest.compute_mesh_hash()
    
    if not manifest.mesh_hash:
        return "No baseline hash (first check)"
    
    if current_hash != manifest.mesh_hash:
        return f"Mesh modified (hash changed)"
    
    return None  # Unchanged


# CLI-style convenience functions
def validate_manifest_file(json_path: str) -> bool:
    """
    Validate a .trixel manifest file (CLI entry point).
    
    Returns:
        True if valid, False otherwise (prints errors)
    """
    try:
        manifest = load_trixel_manifest(json_path)
        print(f"✓ Manifest valid: {json_path}")
        print(f"  Concept: {manifest.zw_concept}")
        print(f"  Profile: {manifest.ap_profile}")
        print(f"  Mesh: {manifest.mesh_path or 'NOT FOUND'}")
        if manifest.mesh_path:
            print(f"  Geometry: {manifest.geometry.vertex_count} verts, {manifest.geometry.face_count} faces")
        return True
    except Exception as e:
        print(f"✗ Validation failed: {json_path}")
        print(f"  Error: {e}")
        return False
