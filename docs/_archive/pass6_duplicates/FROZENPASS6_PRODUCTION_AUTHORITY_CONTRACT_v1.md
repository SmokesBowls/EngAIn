Understood. I am strictly following your directive: **only the contract file is being created.** No scripts, no runtime modifications, no Trixel/Blender changes. 

Here is the exact content for `docs/pipeline/contracts/PASS6_PRODUCTION_AUTHORITY_CONTRACT_v1.md`, incorporating the required **Authority Inputs** section.

***

```markdown
# PASS6_PRODUCTION_AUTHORITY_CONTRACT_v1.md

## 1. Purpose and Scope
This contract defines the constitutional boundaries, emission schema, and governance rules for **Pass 6 (Production Manifest Generator)** within the EngAIn narrative-to-game pipeline. 

Pass 6 is the absolute boundary between **Semantic Interpretation** (Passes 1–5) and **Deterministic Manufacturing** (Trixel, Blender, Godot, Runtime). Pass 6 emits *intent and routing contracts*; it never emits *solved state or coordinates*.

## 2. Authority Boundaries & Deferrals
Pass 6 does not own truth. It routes truth to the appropriate manufacturing departments. It explicitly defers to the following existing authorities:

| Domain | Pass 6 Emits (Intent) | Defers To (Existing Authority) |
| :--- | :--- | :--- |
| **Spatial/Location** | Region IDs, adjacency hints, terrain class | `location_authority_registry.json`, `spatial_reasoner.py` |
| **Entity/Semantic** | Concept IDs, AP profiles, spawn hints | `world_rules.json`, `semantic_bridge.py` |
| **Geometry/Mesh** | ZW concepts, LOD classes, anchor roles | `mesh_manifest.py`, `mesh_intake.py` |
| **Terrain/Trixel** | Terrain families, surface types, atlas hints | `terrain_thresholds.py`, `demand_resolver.py` |
| **Runtime State** | Scene IDs, global flags, active systems | `EngAInRuntime.snapshot`, `protocol_envelope.py` |

## 3. Integration with Authority Tiers
In accordance with `AUTHORITY_TIER_SPEC_v1.md`, Pass 6 manifests are classified as **Tier 0 (Proposed/Draft)** intent. 
* Pass 6 output is **read-only** regarding the live simulation.
* Manufacturing compilers (Trixel, Blender) may consume Tier 0 manifests to generate assets.
* The Runtime (`sim_runtime.py`) must validate and promote Tier 0 intents to **Tier 1 (Imbued)** or **Tier 2 (Finalized)** state via the `scene_shell_builder.py` and `protocol_envelope.py` before mutating the live snapshot.

## 4. Authority Inputs
Pass 6 must consult the following canonical sources to validate its emissions and ensure constitutional compliance. These inputs act as the lookup tables and governance laws for the Production Manifest Generator.

### Required Lookup Sources
* **`location_authority_registry.json`** — Validates spatial claims, region IDs, and location confidence levels (CONFIRMED, CANDIDATE, LOW_CONFIDENCE). Pass 6 must not emit finalized Trixel recipes for locations flagged as LOW_CONFIDENCE without routing them to a DRAFT reality mode.
* **`world_rules.json`** — Canonical entity ontology, spawnability rules, cardinality, and ZW tag enforcement. Pass 6 must verify all `concept_id` emissions against this registry.

### Governance & Compliance Laws
* **`AUTHORITY_TIER_SPEC_v1.md`** — Defines reality modes (DRAFT, IMBUED, FINALIZED, DREAM, REPLAY) and validation tier metrics (Tiers 0–3) governing state mutability.
* **`RUNTIME_STATE_AUTHORITY_CONTRACT_v1.md`** — Establishes `EngAInRuntime.snapshot` as the live simulation Single Source of Truth (SSOT) and protocol envelope rules. Pass 6 must format its runtime block to be safely wrappable by the Protocol Envelope.
* **`MRLORE_AUTHORITY_CONTRACT_v1.md`** — Outlines MrLore's authority to audit, score, and propose narrative changes. Pass 6 must respect narrative stability and canon compliance scores, embedding them in the manifest's governance envelope.
* **`COMPLIANCE_REPORT.txt`** — ABI compliance rules (e.g., COORDINATE_ABI_v1). Pass 6 must emit contracts that strictly avoid flagged ambiguities, such as coordinate namespace collisions and camera orientation hard-coding.

## 5. The Production Manifest Schema (`production_manifest.json`)
Pass 6 shall emit a single JSON artifact per scene/chapter, strictly adhering to this schema:

```json
{
  "manifest_version": "1.0",
  "scene_id": "scene.03_fist_contact",
  "source_chapter": "03_Fist_contact",
  
  "governance": {
    "authority_tier": 0,
    "reality_mode": "DRAFT",
    "mrlore_canon_score": 0.92,
    "location_authority_status": "CONFIRMED",
    "abi_compliance_hash": "sha256:..."
  },

  "semantic": {
    "entities": [
      {
        "concept_id": "vairis",
        "ap_profile": "damageable_npc",
        "collision_role": "solid",
        "placement_strategy": "social_cluster"
      }
    ]
  },

  "spatial": {
    "location_authority_ref": "beach_landing",
    "terrain_class": "beach",
    "adjacency_hints": ["inland_plains"],
    "landmarks": ["shoreline", "landing_site"]
  },

  "terrain": {
    "terrain_family": "beach",
    "environment": "coastal",
    "surface_types": ["sand", "wet_rock", "foam"]
  },

  "trixel": {
    "atlas_hints": ["beach_base", "coastal_foam_overlay"],
    "recipe_family": "coastal_standard"
  },

  "geometry": {
    "zw_concepts": ["vrill_conduit", "wreckage_hull"],
    "lod_requirements": ["hero_prop", "background_debris"]
  },

  "runtime": {
    "systems_active": ["vrill_current", "tidal_physics"],
    "global_flags_to_set": ["pelagor_survivors_detected"],
    "epoch_hint": "FirstAge"
  }
}
```

## 6. Prohibited Actions (The "Thou Shalt Nots")
1. **No Hardcoded Coordinates:** Pass 6 shall never emit `[x, y, z]` vectors. Spatial resolution is the exclusive domain of `spatial_reasoner.py`.
2. **No Direct Prose Parsing:** Pass 6 shall only consume structured Pass 5 (`game_scene.json`) output. It shall not read raw text, ZONJ, or vault markdown.
3. **No Asset Path Resolution:** Pass 6 shall not emit Godot `res://` paths or Blender file paths. It emits `zw_concepts` and `atlas_hints`, which the `demand_resolver.py` and `mesh_manifest.py` resolve.
4. **No State Mutation:** Pass 6 shall not make HTTP POST requests to `sim_runtime.py` or mutate `EngAInRuntime.snapshot`. It only writes the manifest to disk.

## 7. Compliance and Auditing
Pass 6 output is subject to audit by `MrLore` (for narrative drift) and the `authority_validator.py` (for schema compliance). Any manifest failing validation shall be quarantined and shall not be consumed by downstream manufacturing compilers.
```

***

The contract is defined. The foundation is locked. Awaiting your signal to proceed to the next phase.
