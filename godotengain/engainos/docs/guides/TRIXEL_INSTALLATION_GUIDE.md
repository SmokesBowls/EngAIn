# Trixel Pipeline Installation Guide

## Correct File Placement

```
engainos/
├── core/                           ← LAW (never put tools here)
│   ├── zw_protocol.py
│   ├── zon_memory.py
│   ├── ap_rules.py
│   └── mesh_intake.py              ← Existing HARD GATE
│
├── tools/                          ← ← ← TRIXEL GOES HERE
│   ├── trixel/
│   │   ├── __init__.py
│   │   ├── trixel_mesh_pipeline.py    ← Main pipeline (this file)
│   │   ├── trixel_composer.py         ← Can split out later
│   │   ├── wings_adapter.py           ← Can split out later
│   │   └── meshlab_adapter.py         ← Can split out later
│   │
│   └── narrative/                  ← Your existing extraction tools
│       └── semantic_extractor.py
│
├── assets/
│   ├── meshes/
│   │   ├── raw/                    ← Wings output (pre-cleanup)
│   │   ├── clean/                  ← MeshLab output (sanitized)
│   │   └── templates/              ← Base meshes
│   │
│   └── trixels/                    ← .trixel manifests (authoritative)
│       ├── guard_theron.trixel
│       └── merchant_mara.trixel
│
├── godot/                          ← RUNTIME ONLY (never calls Trixel)
│   └── test_bridge.gd
│
└── tests/
    └── test_trixel_pipeline.py
```

## Installation Steps

### 1. Create Directory Structure

```bash
cd engainos

# Create tools directory if it doesn't exist
mkdir -p tools/trixel

# Create asset directories
mkdir -p assets/meshes/raw
mkdir -p assets/meshes/clean
mkdir -p assets/meshes/templates
mkdir -p assets/trixels
```

### 2. Copy Trixel Pipeline

```bash
# Copy the law-compliant version
cp trixel_mesh_pipeline_LAW_COMPLIANT.py tools/trixel/trixel_mesh_pipeline.py

# Create __init__.py
touch tools/trixel/__init__.py
```

### 3. Verify Integration Points

The pipeline imports from your existing law:

```python
# In tools/trixel/trixel_mesh_pipeline.py
from mesh_intake import intake_mesh  # ← Must exist in core/
from mesh_manifest import load_trixel_manifest  # ← Must exist in core/
```

Make sure these exist:
- `core/mesh_intake.py` - The HARD GATE
- `core/mesh_manifest.py` - Trixel manifest handling

### 4. Test the Pipeline

```bash
cd tools/trixel

# Test with example narrative
python trixel_mesh_pipeline.py guard_theron "A towering guard in heavy armor"

# Should output:
# [1/5] Trixel: Extracting semantic intent...
# [2/5] Wings: Building mesh...
# [3/5] MeshLab: Sanitizing...
# [4/5] Trixel: Visual judgment (advisory)...
# [5/5] mesh_intake: Law enforcement (HARD GATE)...
# ✓ LAW APPROVED or ✗ LAW REJECTED
```

## The Two Critical Fixes

### Fix 1: NO `.skin` files - Use `.trixel` via mesh_intake

❌ **OLD (wrong):**
```python
metadata_path = mesh_path.with_suffix('.skin')
with open(metadata_path, 'w') as f:
    json.dump(metadata, f)
```

✅ **NEW (correct):**
```python
# mesh_intake creates the .trixel manifest
result = intake_mesh(
    mesh_path=str(clean_mesh),
    zw_concept=intent.zw_concept,
    ap_profile=intent.zw_tags["ap_profile"],
    placeholder_mesh=intent.placeholder_type,
    source_tool="trixel_pipeline"
)
# result contains path to .trixel manifest
```

**Why:** 
- `.trixel` is already law
- mesh_intake enforces the schema
- No parallel metadata systems

### Fix 2: Trixel Advises, Intake Decides

❌ **OLD (wrong):**
```python
if trixel.validate_mesh():
    accept_mesh()  # Trixel has authority
```

✅ **NEW (correct):**
```python
# Trixel judges (advisory)
judgment = trixel.judge_mesh_quality(mesh, intent)

# mesh_intake decides (authoritative)
result = intake_mesh(
    mesh_path=mesh,
    trixel_judgment=judgment  # Advisory only
)

# Law makes final call
if result["status"] == "accepted":
    # Mesh passed law
```

**Why:**
- Trixel = visual expert (judges quality)
- mesh_intake = law (enforces standards)
- Separation of concerns

## Data Flow (Correct)

```
Narrative Text
    ↓
[Trixel Composer]
    ↓ SemanticIntent (advisory)
[Wings 3D]
    ↓ raw.obj
[MeshLab]
    ↓ clean.obj
[Trixel Composer]
    ↓ TrixelJudgment (advisory)
[mesh_intake.py] ← ← ← HARD GATE (authoritative)
    ↓ .trixel manifest (if approved)
[Core / ZON]
    ↓ Entity binding (if law approved)
[Godot]
    ↓ Rendering (overlay only)
```

## What Godot Never Sees

Godot ONLY sees:
- `.trixel` manifest (from assets/trixels/)
- `.glb` mesh (from assets/meshes/clean/)
- Entity state (from core/zon)

Godot NEVER sees:
- Narrative text
- Trixel judgments
- Wings/MeshLab
- mesh_intake results
- Raw/intermediate meshes

## Integration with Existing Systems

### With semantic_extractor.py

```python
# In tools/narrative/semantic_extractor.py

from tools.trixel.trixel_mesh_pipeline import TrixelMeshPipeline

# After extracting concepts from narrative:
concepts = extract_concepts(chapter_text)

# Generate meshes for each concept:
pipeline = TrixelMeshPipeline()
for concept_data in concepts:
    artifact = pipeline.generate_mesh_from_narrative(
        narrative=concept_data["narrative_context"],
        zw_concept=concept_data["zw_concept"]
    )
    
    if artifact.law_approved:
        print(f"✓ {concept_data['zw_concept']} approved by law")
    else:
        print(f"✗ {concept_data['zw_concept']} rejected by law")
```

### With mesh_intake.py

```python
# In core/mesh_intake.py (existing law)

def intake_mesh(
    mesh_path: str,
    zw_concept: str,
    ap_profile: str,
    collision_role: str,
    lod_class: str,
    placeholder_mesh: str,
    source_tool: str,
    trixel_judgment: Optional[Dict] = None  # ← Advisory from Trixel
) -> Dict[str, Any]:
    """
    HARD GATE: Enforce mesh law.
    
    trixel_judgment is advisory only - law makes final call.
    """
    # Validate mesh meets standards
    if not _validate_topology(mesh_path):
        return {"status": "rejected", "reason": "Invalid topology"}
    
    # Validate against AP profile
    if not _validate_ap_profile(mesh_path, ap_profile):
        return {"status": "rejected", "reason": "AP profile mismatch"}
    
    # Consider Trixel's advisory (but law decides)
    if trixel_judgment and trixel_judgment["visual_match_score"] < 0.5:
        # Law can override Trixel, or vice versa
        pass
    
    # Create .trixel manifest
    manifest_path = _create_trixel_manifest(
        mesh_path, zw_concept, ap_profile, placeholder_mesh
    )
    
    return {
        "status": "accepted",
        "manifest_path": manifest_path,
        "trixel_judgment": trixel_judgment
    }
```

### With test_bridge.gd (Godot)

```gdscript
# Godot NEVER calls Trixel pipeline
# It only loads .trixel manifests created by mesh_intake

func load_entity(zw_concept: String):
    # Load .trixel manifest
    var manifest = load_trixel_manifest(zw_concept)
    
    # Spawn placeholder
    var placeholder = create_placeholder(manifest.placeholder_mesh)
    
    # Load approved mesh
    var mesh = load(manifest.mesh_path)
    swap_mesh(placeholder, mesh)
```

## Verification Checklist

- [ ] Trixel pipeline in `tools/trixel/` (not `core/`)
- [ ] Pipeline calls `mesh_intake.py` (not creating `.skin` files)
- [ ] Trixel provides `TrixelJudgment` (advisory only)
- [ ] mesh_intake makes final decision (authoritative)
- [ ] `.trixel` manifests in `assets/trixels/`
- [ ] Godot loads from manifests (never calls Trixel)
- [ ] Raw meshes stay in `assets/meshes/raw/`
- [ ] Clean meshes in `assets/meshes/clean/`

## Common Mistakes to Avoid

❌ **DON'T:**
- Put Trixel in `core/` (it's a tool, not law)
- Create `.skin` files (use `.trixel` via mesh_intake)
- Let Trixel have final authority (that's mesh_intake's job)
- Let Godot call Trixel directly (breaks law)
- Put meshes in `godot/` (they belong in `assets/`)

✅ **DO:**
- Keep Trixel in `tools/`
- Route all meshes through mesh_intake
- Treat Trixel as advisory expert
- Keep Godot as pure consumer
- Maintain single source of truth (`.trixel` manifests)

## Next Steps

1. **Install external tools:**
   - Wings 3D for mesh creation
   - MeshLab for mesh cleanup

2. **Create base templates:**
   - `assets/meshes/templates/humanoid_base.obj`
   - `assets/meshes/templates/door_base.obj`

3. **Test integration:**
   - Run pipeline with example narrative
   - Verify mesh_intake creates `.trixel`
   - Load in Godot via test_bridge

4. **Integrate with narrative pipeline:**
   - Hook Trixel into semantic_extractor
   - Batch-generate meshes for chapters

## Summary

**Location:** `tools/trixel/` (NOT `core/`)  
**Authority:** Advisory (NOT authoritative)  
**Output:** Submits to mesh_intake (NOT creates `.skin`)  
**Integration:** Via mesh_intake (NOT direct Godot)

This maintains clean separation:
- **Trixel** = semantic + visual expert
- **mesh_intake** = law enforcer
- **core** = runtime binder
- **Godot** = visual overlay
