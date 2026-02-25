# TRIXEL PIPELINE v1 - FROZEN

**Status:** LOCKED  
**Scope:** Semantic Intent → Geometry Tools → Runtime Mesh  
**Philosophy:** Trixel is law and intent, not geometry. Mesh tools are chisels that obey that law.

---

## 1. Purpose

Define the contract between:
- **Trixel Composer**: Semantic intent (ZW concepts, AP profiles, collision roles)
- **Geometry Tools**: Topology creators (Wings 3D, MagicaVoxel, etc.)
- **Mesh Processors**: Sanitizers/decimators (MeshLab, etc.)
- **EngAIn Runtime**: Final mesh consumers (Godot + spatial_skin_system)

**Key Principle**: EngAIn/Empire never import geometry tools. Tools produce artifacts that EngAIn validates and consumes.

---

## 2. Pipeline Flow

```
Trixel Composer (semantic intent)
    ↓
    Creates: .trixel manifest (JSON)
    ↓
Wings 3D / MagicaVoxel (topology creation)
    ↓
    Creates: base geometry (.obj, .vox)
    ↓
MeshLab CLI (sanitization/decimation)
    ↓
    Creates: optimized mesh (.obj)
    ↓
mesh_manifest.py (validation/annotation)
    ↓
    Creates: final manifest + mesh reference
    ↓
spatial_skin_system.py (runtime integration)
    ↓
    Creates: Entity3D with skin_3d_id
    ↓
Godot (rendering)
```

---

## 3. Trixel Contract (Required Metadata)

Every mesh MUST have a `.trixel` manifest (JSON sidecar):

```json
{
  "trixel_version": "1.0",
  "zw_concept": "guard",           // Semantic identity
  "ap_profile": "damageable_npc",  // AP rule set
  "collision_role": "solid",       // Physics intent
  "lod_class": "character",        // LOD category
  "placeholder_mesh": "capsule",   // Fallback if 3D unavailable
  "geometry": {
    "source_tool": "wings3d",      // Topology creator
    "source_file": "guard_base.wings",
    "export_format": "obj",
    "vertex_count": 1247,
    "face_count": 2134
  },
  "processing": {
    "meshlab_preset": "character_optimize",
    "target_vertex_count": 800,
    "preserve_uvs": true,
    "preserve_normals": true
  },
  "anchors": [                     // Semantic attachment points
    {
      "name": "hand_right",
      "position": [0.3, 1.2, 0.0],
      "purpose": "weapon_attachment"
    },
    {
      "name": "head",
      "position": [0.0, 1.8, 0.0],
      "purpose": "helmet_attachment"
    }
  ],
  "regions": [                     // Semantic mesh regions
    {
      "name": "torso",
      "material_slot": 0,
      "collision": "body"
    },
    {
      "name": "shield",
      "material_slot": 1,
      "collision": "equipment"
    }
  ]
}
```

---

## 4. Tool Requirements (3-Gate Test)

Any tool in the pipeline MUST pass:

### Gate 1: Local Execution
- ✅ Runs on Linux without cloud/license server
- ✅ Can be installed via package manager or AppImage
- ❌ Requires Windows-only runtime
- ❌ Requires active internet connection

### Gate 2: Scriptable/Headless
- ✅ CLI interface available
- ✅ Can be called from Python/bash
- ✅ Batch processing supported
- ❌ GUI-only operation
- ❌ Manual clicking required

### Gate 3: Metadata Preservation
- ✅ Preserves explicit topology (vertex order, face winding)
- ✅ Supports sidecar metadata (JSON, XML, etc.)
- ✅ Exports clean OBJ/GLTF/FBX
- ❌ Mangles vertex indices
- ❌ Loses metadata on export

---

## 5. Approved Tool Chain

### Tier 1: Primary Tools (Vetted)

**Trixel Composer** (Semantic Intent)
- Purpose: Define ZW concepts, AP profiles, collision roles
- Output: `.trixel` manifest
- Dependencies: None (pure Python)

**Wings 3D** (Topology Creation)
- Purpose: Manual mesh modeling
- Output: `.obj`, `.wings`
- CLI: Limited (export only)
- Status: ✅ Passes 3-gate test

**MeshLab** (Mesh Processing)
- Purpose: Decimation, cleanup, optimization
- Output: `.obj`, `.ply`, `.stl`
- CLI: ✅ Full scripting support (`meshlabserver`)
- Status: ✅ Passes 3-gate test

**MagicaVoxel** (Voxel Creation)
- Purpose: Voxel art → mesh conversion
- Output: `.vox`, `.obj`
- CLI: ⚠️ Limited (export only)
- Status: ✅ Passes 3-gate test (with export scripts)

### Tier 2: Compatibility Tools (Escape Hatches)

**Bforartists** (Blender Fork)
- Purpose: Access Blender ecosystem when needed
- Output: `.blend`, `.fbx`, `.gltf`
- CLI: ✅ Python scripting (`bpy`)
- Status: ✅ Passes 3-gate test
- Note: Use sparingly, not daily workflow

### Tier 3: Forbidden Tools (Avoid)

❌ **Blender** (upstream)
- Reason: UI bloat, unstable Python API, "Blender-Hell"
- Replacement: Bforartists (if Blender ecosystem needed)

❌ **Commercial Cloud Tools**
- Reason: Fails Gate 1 (local execution)

❌ **GUI-Only Tools**
- Reason: Fails Gate 2 (scriptable)

---

## 6. MeshLab Presets

Standard presets for `meshlabserver`:

### `character_optimize.mlx`
```xml
<!-- Optimize character meshes for real-time rendering -->
<filter name="Simplification: Quadric Edge Collapse Decimation">
  <Param name="TargetPerc" value="0.5"/>
  <Param name="QualityThr" value="0.3"/>
  <Param name="PreserveBoundary" value="true"/>
  <Param name="PreserveNormal" value="true"/>
  <Param name="PreserveTopology" value="false"/>
  <Param name="OptimalPlacement" value="true"/>
</filter>
<filter name="Remove Duplicate Faces"/>
<filter name="Remove Duplicate Vertices"/>
<filter name="Repair non-manifold edges"/>
```

### `prop_optimize.mlx`
```xml
<!-- Optimize static props (aggressive decimation) -->
<filter name="Simplification: Quadric Edge Collapse Decimation">
  <Param name="TargetPerc" value="0.3"/>
  <Param name="QualityThr" value="0.2"/>
  <Param name="PreserveBoundary" value="true"/>
  <Param name="PreserveNormal" value="false"/>
</filter>
<filter name="Remove Duplicate Faces"/>
<filter name="Remove Duplicate Vertices"/>
```

Usage:
```bash
meshlabserver -i input.obj -o output.obj -s character_optimize.mlx
```

---

## 7. Voxel → Surface Extraction

For MagicaVoxel `.vox` files:

### Rules
1. **Preserve semantic boundaries**: Each color = separate material region
2. **Maintain block topology**: Don't over-smooth; keep ZW region intent
3. **Generate collision hints**: Solid voxels = collision meshes

### Export Command
```bash
# MagicaVoxel to OBJ (preserves per-face colors)
magicavoxel export guard.vox --format obj --preserve-regions
```

### Post-Processing
```python
# In mesh_manifest.py
def extract_voxel_regions(obj_path: str) -> List[Region]:
    """
    Parse OBJ material groups into semantic regions.
    MagicaVoxel exports one material per color.
    """
    regions = []
    for mtl_group in parse_obj_groups(obj_path):
        regions.append(Region(
            name=mtl_group.name,
            material_slot=mtl_group.index,
            collision=infer_collision_from_color(mtl_group.color)
        ))
    return regions
```

---

## 8. Mesh Manifest Validator

### mesh_manifest.py (Core Module)

```python
@dataclass
class TrixelManifest:
    """Validated Trixel manifest + mesh reference"""
    zw_concept: str
    ap_profile: str
    collision_role: str
    lod_class: str
    placeholder_mesh: str
    mesh_path: str              # Path to final .obj/.glb
    vertex_count: int
    face_count: int
    anchors: List[Anchor]
    regions: List[Region]
    
    def validate(self) -> List[str]:
        """Validate manifest against Trixel contract"""
        errors = []
        
        if not self.zw_concept:
            errors.append("Missing zw_concept")
        
        if not self.ap_profile:
            errors.append("Missing ap_profile")
        
        if not os.path.exists(self.mesh_path):
            errors.append(f"Mesh file not found: {self.mesh_path}")
        
        if self.vertex_count > 5000:
            errors.append(f"Vertex count too high: {self.vertex_count} (max 5000)")
        
        return errors
    
    def to_skin_reference(self) -> str:
        """Generate skin_3d_id for spatial_skin_system"""
        return f"meshes/{self.zw_concept}/{os.path.basename(self.mesh_path)}"


def load_trixel_manifest(json_path: str) -> TrixelManifest:
    """Load and validate .trixel manifest"""
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    manifest = TrixelManifest(**data)
    errors = manifest.validate()
    
    if errors:
        raise ValueError(f"Invalid Trixel manifest: {errors}")
    
    return manifest
```

---

## 9. Integration with spatial_skin_system

```python
# In your game loader:
from mesh_manifest import load_trixel_manifest
from spatial_skin_system import Entity3D, Transform3D

# Load Trixel manifest
manifest = load_trixel_manifest("assets/trixels/guard.trixel")

# Create Entity3D
guard = Entity3D(
    zw_concept=manifest.zw_concept,
    ap_profile=manifest.ap_profile,
    kernel_bindings={"combat": True},
    placeholder_mesh=manifest.placeholder_mesh,
    transform=Transform3D(10, 0, 5),
    skin_3d_id=manifest.to_skin_reference()  # Points to processed mesh
)

# Build render plan (as before)
plan = build_render_plan(guard)
```

---

## 10. Directory Structure

```
assets/
├── trixels/                  # Trixel manifests (semantic intent)
│   ├── guard.trixel
│   ├── merchant.trixel
│   └── door.trixel
├── meshes/                   # Source geometry
│   ├── guard/
│   │   ├── guard_base.wings  # Wings 3D source
│   │   ├── guard_base.obj    # Exported geometry
│   │   └── guard_opt.obj     # MeshLab optimized
│   └── merchant/
│       ├── merchant.vox      # MagicaVoxel source
│       └── merchant.obj      # Exported + optimized
└── runtime/                  # Final assets for Godot
    └── meshes/
        ├── guard/
        │   └── guard.obj     # Symlink to guard_opt.obj
        └── merchant/
            └── merchant.obj
```

---

## 11. Workflow Example

### Step 1: Define Intent (Trixel Composer)
```bash
trixel create guard \
  --concept guard \
  --profile damageable_npc \
  --collision solid \
  --lod character \
  --placeholder capsule
```

Creates: `assets/trixels/guard.trixel`

### Step 2: Create Geometry (Wings 3D)
```bash
# Manual modeling in Wings 3D
# Export: File → Export → Wavefront (.obj)
```

Creates: `assets/meshes/guard/guard_base.obj`

### Step 3: Optimize (MeshLab)
```bash
meshlabserver \
  -i assets/meshes/guard/guard_base.obj \
  -o assets/meshes/guard/guard_opt.obj \
  -s presets/character_optimize.mlx
```

### Step 4: Validate (mesh_manifest.py)
```bash
python3 -m mesh_manifest validate assets/trixels/guard.trixel
```

Output:
```
✓ Manifest valid
✓ Mesh exists (1247 vertices, 2134 faces)
✓ Within vertex budget (< 5000)
✓ All required metadata present
```

### Step 5: Deploy (Runtime)
```bash
python3 -m mesh_manifest deploy assets/trixels/guard.trixel
```

Creates symlink: `runtime/meshes/guard/guard.obj` → `guard_opt.obj`

---

## 12. Future Extensions

### Round-Trip Handshake (Trixel ↔ Mesh Tools)

When a mesh is modified in Wings 3D:

1. Wings 3D exports new `.obj`
2. `mesh_manifest.py` detects change (hash comparison)
3. Validator checks if semantic regions still match
4. If regions changed → flag for Trixel Composer review
5. If only geometry changed → auto-approve

### Voxel → Surface Intelligence

```python
def voxel_to_collision_mesh(vox_path: str, trixel: TrixelManifest):
    """
    Extract collision mesh from voxel data.
    Uses Trixel semantic regions to simplify appropriately.
    """
    # Solid regions (torso, legs) → simplified convex hulls
    # Equipment regions (shield, sword) → preserve detail
    # Decorative regions (cape, hair) → no collision
```

---

## 13. Versioning & Compatibility

**Trixel Pipeline v1 - FROZEN**

Breaking changes require:
- New `.trixel` schema version
- Migration scripts for existing manifests
- Backward compatibility layer for v1

---

## 14. Final Invariants (Non-Negotiable)

1. **Directionality**: Tools → EngAIn, never EngAIn → Tools
2. **3-Gate Test**: All tools must pass Local + Scriptable + Metadata
3. **Trixel is Law**: Geometry obeys semantic intent, not vice versa
4. **Placeholder Fallback**: Every mesh has a placeholder (cube, capsule, etc.)
5. **No Blender-Hell**: Tools stay interchangeable, no lock-in

---

## 15. Document Status

**LOCKED** - This is the contract. Geometry tools are chisels, Trixel is the blueprint.
