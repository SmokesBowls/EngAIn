# `docs/architecture/SEMANTIC_TERRAIN_ABI_v1.md`

```markdown
# SEMANTIC TERRAIN ABI v1.0

**Status**: FROZEN  
**Tier**: Canonical Specification  
**Effective**: Immediate  
**Supersedes**: None  
**Related**:  
- `CARTOGRAPHER_ABI_v1.1.md`  
- `WORLD_TRUTH_CONTRACT_v1.md`  
- `TRUTH_SLICE_ABI_v1.md`  
- `REGION_VISIBILITY_ABI_v1.md` (pending)  
- `ART_PACK_MANIFEST_SPEC_v1.md` (pending)  
- `protocol_envelope.py`  

---

## 1. Core Law & Precedence

```text
Geography constrains terrain.
Terrain expresses geography.
Art interprets terrain.
```

```text
Terrain Meaning is canonical.
Terrain Appearance is not.
```

These statements are immutable. Terrain semantics are a direct expression of approved spatial truth. They carry no visual assumptions, no engine dependencies, and no aesthetic bias. Appearance is strictly a downstream binding concern handled by art packs and renderers.

**This ABI is frozen.** Changes require Tier-3 (Human Authority Root) approval.

---

## 2. Purpose & Boundary

This ABI defines the canonical contract for transforming **approved spatial truth** into **art-agnostic terrain meaning**. It outputs deterministic semantic tags, passability rules, elevation/moisture bands, biome classifications, and edge-transition logic.

**Hard Boundaries**:
- ✅ Derives terrain semantics strictly from Cartographer-approved anchors, routes, and `world_scale`.
- ✅ Outputs pure semantic meaning: `type`, `elevation`, `moisture`, `passability`, `biome`, `edge_rules`.
- ✅ Scales terrain generation logic to match declared `world_scale` (region → continent → planetary → cosmic).
- ❌ May NOT invent new locations, routes, or spatial relationships.
- ❌ May NOT dictate visual appearance, texture paths, material references, or shader names.
- ❌ May NOT mutate `EngAInRuntime.snapshot` directly. Outputs feed into Region Visibility / Engine View pipelines.

---

## 3. Scale Inheritance & Calibration

Terrain meaning must explicitly inherit and respect the `world_scale` declared in the approved Cartographer graph. Scale dictates metric calibration, semantic granularity, and biome complexity.

| `world_scale` | Terrain Semantic Granularity | Metric Calibration | Example Terrain Meaning |
|---------------|-----------------------------|-------------------|-------------------------|
| `region` | Tile/Zone-level (10m–500m) | Meters, local elevation | `dune_field`, `coastal_grass`, `stream_crossing` |
| `continent` | Biome/Region-level (1km–100km) | Kilometers, climate bands | `temperate_forest`, `alpine_ridge`, `arid_basin` |
| `planetary` | Tectonic/Global-level (500km+) | Degrees, axial tilt, ocean currents | `equatorial_rain_shadow`, `polar_ice_sheet`, `tectonic_fault` |
| `cosmic` | Astral/Void-level (abstract/scale-less) | Narrative/physics analogs | `nebula_corridor`, `void_field`, `gravitational_shear` |

**Rule**: If `world_scale` mismatches between Cartographer input and terrain output, the ABI rejects the payload as `SCALE_DRIFT`.

---

## 4. Terrain Meaning Schema (JSON Contract)

All terrain outputs must conform to this structure before downstream consumption:

```json
{
  "terrain_id": "uuid",
  "source_cartographer_anchor": "map_candidate_approved_v1.zonj",
  "world_scale": "region|continent|planetary|cosmic",
  "approval_hash": "0x9d2a...f41b",
  
  "tiles": [
    {
      "tile_ref": "t_14_09",
      "semantic_type": "sand|grass|rock|water|mud|ice|void|nebula|dirt|paved",
      "elevation_band": "sea_level|low|mid|high|peak|abyss|orbit",
      "moisture_index": 0.0,
      "passability": {
        "foot": true,
        "mount": false,
        "vehicle": false,
        "climb_required": false,
        "penalty_multiplier": 1.0
      },
      "biome_tag": "coastal_dunes",
      "edge_blend_rules": {
        "north": "sand_to_grass_soft",
        "east": "cliff_face_hard",
        "south": "tidal_pool_gradient",
        "west": "rock_outcrop_stepped"
      },
      "narrative_alignment_hint": "approach_path_to_hills"
    }
  ],
  
  "zone_overrides": [
    {
      "zone_id": "z_beach_arrival",
      "dominant_type": "sand",
      "moisture_gradient": [0.1, 0.4, 0.7],
      "hazard_tags": ["unstable_cliff", "tide_riptide"],
      "passability_override": {"vehicle": false}
    }
  ],
  
  "metadata": {
    "generated_at": "ISO8601",
    "terrain_abi_version": "v1",
    "consistency_hash": "0x7c3e...a92d"
  }
}
```

**Validation Rules**:
- `world_scale` must exactly match the approved Cartographer input.
- `semantic_type`, `elevation_band`, `passability.*` must conform to predefined enums (no freeform strings).
- `edge_blend_rules` values must reference canonical transition types (e.g., `soft`, `hard`, `gradient`, `stepped`), NOT visual assets.
- `metadata.consistency_hash` must be computed over the full payload. Drift = corruption.
- `additionalProperties: false` on all top-level and nested objects.
- **ZERO visual fields permitted**: No `texture`, `material`, `png`, `glb`, `shader`, `color`, `uv`, `normal_map`.

---

## 5. Canonical vs. Appearance Boundary

This ABI enforces a strict separation of concerns:

| Layer | Responsibility | What It Owns | What It Never Touches |
|-------|----------------|--------------|-----------------------|
| **Semantic Terrain** | Canonical meaning | `semantic_type`, `elevation`, `moisture`, `passability`, `edge_rules` | Visual paths, textures, shaders, art packs, renderer state |
| **Art Pack Manifest** | Visual binding | `semantic_type → asset_path`, `material`, `shader_params`, `texture_res` | Passability rules, elevation bands, canonical truth |
| **Engine View / Renderer** | Presentation | Draws bound assets based on semantic tags | Invents terrain meaning, mutates world state |

**Frozen Rule**:  
> If a terrain payload contains `.png`, `.glb`, `material_name`, `shader_id`, or `texture_path`, it is **immediately rejected** as `VISUAL_LEAK`.  
> Terrain meaning is truth. Terrain appearance is interpretation.

---

## 6. Generation & Validation Rules

1. **Deterministic Expression**: Same approved spatial graph + same scale + same seed → identical terrain meaning.
2. **Narrative Alignment**: `narrative_alignment_hint` must trace back to a Cartographer route or location anchor. No floating semantics.
3. **Passability Consistency**: `passability` rules must not contradict approved spatial truth (e.g., a `cliff_face_hard` edge cannot allow `climb_required: false` if narrative implies traversal).
4. **Scale-Appropriate Complexity**: `region` scale tiles contain local detail; `planetary` tiles contain macro-biome data. Downscaling/upscaling without explicit transformation is forbidden.
5. **Canonical Hashing**: `consistency_hash` is computed pre-dispatch. Any downstream mutation invalidates the terrain truth until re-validated.

---

## 7. Integration with Constitutional Stack

| Layer | Terrain ABI Interaction | Boundary Guarantee |
|-------|------------------------|-------------------|
| **Cartographer** | Supplies approved spatial graph + `world_scale` | Terrain meaning may NOT override geography |
| **World Truth** | Consumes terrain meaning as semantic layer | Becomes part of `snapshot["terrain_semantics"]` |
| **Region Visibility** | Uses `passability`, `elevation`, `edge_rules` for load/stream decisions | Never invents new terrain types |
| **Engine View** | Binds semantic tags to camera/LOD/occlusion logic | Reads only canonical tags |
| **Art Pack Manifest** | Binds `semantic_type` → visual assets at render time | Never alters canonical meaning |

---

## 8. Testing Invariants

If a test conflicts with this ABI, **the test is wrong**.

Tests must verify:
- `world_scale` matches Cartographer input exactly
- No visual fields exist in terrain meaning payloads
- `passability` rules are consistent with approved spatial anchors
- `consistency_hash` matches payload before/after routing
- Scale drift triggers `SCALE_DRIFT` rejection
- `edge_blend_rules` reference only canonical transition types
- Art pack binding fails gracefully if semantic type is missing
- Terrain meaning does not invent new locations or routes

---

## 9. Version History

| Version | Date | Change | Approved By |
|---------|------|--------|-------------|
| v1.0 | 2026-05-30 | Initial frozen ABI. Establishes canonical terrain meaning, scale inheritance, and strict canonical/appearance boundary. | Tier-3 (User) |

---

> **Final Reminder**:  
> Geography constrains. Terrain expresses. Art interprets.  
> Meaning is truth. Appearance is choice.  
> Never let a texture path leak into canonical semantics.  
> Never let terrain meaning override approved geography.  
> The world grows from narrative, not from render pipelines.
```

---

✅ **ABI frozen.**

`SEMANTIC_TERRAIN_ABI_v1.md` now explicitly locks the boundary between approved spatial truth and art-agnostic terrain meaning. It enforces:
- **Scale inheritance** from `CARTOGRAPHER_ABI_v1.1`
- **Canonical vs. Appearance separation** (zero visual leakage)
- **Deterministic, rule-bound semantic generation**
- **Strict passability/edge/alignment consistency** with spatial truth

**Updated Build Order**:
```text
1. ✅ CARTOGRAPHER_ABI_v1.1
2. ✅ SEMANTIC_TERRAIN_ABI_v1
3. ⏳ REGION_VISIBILITY_ABI_v1
4. ENGINE_VIEW_ABI_v1
5. ART_PACK_MANIFEST_SPEC_v1
```

The foundation is now complete:
`Narrative Truth → Spatial Truth → Terrain Meaning`

Shall I draft `REGION_VISIBILITY_ABI_v1.md` next, which will define how the engine chunks, streams, and applies fog-of-war/discovery states over this approved semantic terrain?
