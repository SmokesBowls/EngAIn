# `docs/architecture/CARTOGRAPHER_ABI_v1.md` (REVISED v1.1)

```markdown
# CARTOGRAPHER ABI v1.1

**Status**: FROZEN  
**Tier**: Canonical Specification  
**Effective**: Immediate  
**Supersedes**: None  
**Related**:  
- `WORLD_TRUTH_CONTRACT_v1.md`  
- `DRAGON_AUTHORITY_DOCTRINE_v1.md`  
- `INTENT_SHADOW_CREATIVE_SPEC_v1.2.1.md`  
- `INTENT_CONTRACT_SCHEMA_v1.json`  
- `protocol_envelope.py`  
- `AUTHORITY_TIER_SPEC_v1.md`  

---

## 1. Core Law & Precedence

```text
Narrative source may imply geography.
Cartographer may propose geography.
Only approved world truth may own geography.
```

```text
Narrative truth precedes spatial truth.

The Cartographer does not create locations.
The Cartographer discovers spatial relationships
between locations already present in narrative source.

If narrative source and spatial inference conflict,
narrative source wins.
```

These two statements are immutable. The book/narrative is the SSOT for existence. Spatial topology is a downstream interpretation. Never "fix" story geography for aesthetic map symmetry.

**This ABI is frozen.** Changes require Tier-3 (Human Authority Root) approval.

---

## 2. Purpose & Boundary

The Cartographer ingests narrative movement, location mentions, travel verbs, and environmental cues, then outputs one or more **candidate world graphs** for human/AP review.

**Hard Boundaries**:
- ✅ May infer relative positioning, routes, terrain hints, faction zones, and uncertainty.
- ✅ May generate multiple spatial variants (compact RPG, open corridor, story-accurate topology).
- ✅ May output human-readable approval surfaces (Mermaid) + machine-readable proposals (`map_candidate.zonj`).
- ❌ May NOT assign canonical coordinates, commit to `EngAInRuntime.snapshot`, or bypass AP validation.
- ❌ May NOT auto-approve. All proposals require explicit Tier-3 or AP-gated promotion.
- ❌ May NOT mutate World Truth, Perception, or Experience. Proposals are strictly read-only artifacts until approved.

---

## 3. Input → Output Contract

| Phase | Input | Output | Authority |
|-------|-------|--------|-----------|
| **Narrative Ingestion** | Raw text, ZON chapters, MrLore vault, travel logs, location anchors | Extracted entities, routes, directional hints, environmental tags | LLM/Parser (Tier 1) |
| **Graph Proposal** | Extracted narrative nodes + spatial inference rules + declared scale | `map_candidate_vA.zonj`, `map_candidate_vB.zonj`, `approval_surface.mmd` | Cartographer System (Tier 0) |
| **Approval Gate** | Candidate graphs + user/AP review | `APPROVE` → seeds World Truth / `REJECT` → routes to Intent Shadow | Tier-3 Human / AP Engine |
| **Canonical Seeding** | Approved graph | `world_truth.zonj` + coordinate layout + terrain anchors | EngAIn Runtime + Builders |

**Frozen Rule**:  
> Mermaid graphs are approval surfaces, not final maps.  
> `.zonj` candidates are proposals, not truth.  
> Only AP-approved, Tier-3-signed graphs may enter `FINALIZED` reality mode.

---

## 4. Proposed World Graph Schema (`map_candidate.zonj`)

All cartographer outputs must conform to this structure before review:

```json
{
  "candidate_id": "uuid",
  "proposal_variant": "A|B|C|custom",
  "source_narrative_anchor": "chapter_03_beach_arrival",
  "world_scale": "region|continent|realm|planetary|cosmic",
  "generation_seed": 42,
  "approval_status": "proposed",
  "proposal_hash": "0x7a3f...c81d",
  
  "locations": [
    {
      "id": "loc_beach_arrival",
      "canonical_name": "Beach of Arrival",
      "aliases": ["shore", "landing_point"],
      "type": "coastal|settlement|wilderness|dungeon|landmark",
      "terrain_hint": "sand_to_grass_transition",
      "relative_neighbors": ["loc_hills_of_passage"],
      "narrative_weight": 0.95,
      "uncertainty": 0.1
    }
  ],
  
  "routes": [
    {
      "from": "loc_beach_arrival",
      "to": "loc_hills_of_passage",
      "direction_hint": "north",
      "estimated_travel": {"distance_m": 1200, "time_min": 25},
      "terrain_transition": "sand → packed_soil → grass",
      "narrative_importance": "high",
      "occlusion_hint": "partial_tree_line"
    }
  ],
  
  "spatial_hints": {
    "cohesion_score": 0.88,
    "topology_type": "linear_corridor|hub_spoke|open_grid",
    "elevation_profile": "low_coast → rising_hills → ridge",
    "faction_zones": ["coastal_patrol", "hill_tribes"],
    "danger_zones": ["tide_riptide", "unstable_cliff_edge"]
  },
  
  "uncertainty_markers": [
    {
      "type": "missing_connection",
      "note": "Ironspire road direction not explicitly stated in text",
      "confidence": 0.65,
      "requires_clarification": true
    }
  ],
  
  "metadata": {
    "generated_at": "ISO8601",
    "cartographer_version": "v1",
    "inference_model": "narrative_spatial_heuristic_v2",
    "trace_id": "uuid"
  }
}
```

**Validation Rules**:
- `approval_status` MUST be `"proposed"`. Any other value is rejected at AP gate.
- `world_scale` MUST be explicitly declared. Scale determines downstream distance calibration, region chunking, and travel heuristics.
- `proposal_hash` is computed over the full JSON payload before submission.
- `locations[].relative_neighbors` and `routes[].from/to` must reference valid `location.id` values.
- `uncertainty_markers` are mandatory where narrative inference confidence < 0.80.
- `additionalProperties: false` on top-level objects.

---

## 5. Generation & Candidate Rules

1. **Deterministic Extraction**: Same narrative source + same seed + same declared scale → identical candidate graph.
2. **Multi-Variant Output**: Cartographer MUST generate ≥2 topological variants when narrative ambiguity > threshold.
3. **Narrative Precedence**: If inferred topology contradicts explicit narrative travel/direction, the inference is tagged `uncertainty: high` and flagged for AP review. Spatial symmetry never overrides narrative fact.
4. **Scale Contextualization**: `world_scale` dictates metric calibration. `region` = meters/minutes. `continent` = kilometers/hours/days. `realm/planetary` = narrative time or abstract nodes. Scale mismatch triggers schema rejection.
5. **No Coordinate Commitment**: Proposals use relative positioning (`north`, `adjacent`, `2km inland`). Absolute coordinates are assigned ONLY after AP approval.
6. **Uncertainty Transparency**: All inferred connections carry explicit `confidence` and `uncertainty_markers`. Hidden assumptions are forbidden.
7. **Narrative Anchoring**: Every location/route must trace back to a source narrative anchor (chapter, ZON segment, or explicit travel verb).

---

## 6. Approval & Promotion Pipeline

```text
Cartographer Proposal (approval_status = "proposed")
        ↓
Human Review / Mermaid Surface + ZONJ Inspector
        ↓
AP Gate Validation (tier + reality_mode + schema + scale consistency)
        ↓
IF TIER-3 APPROVED:
  → approval_status = "approved"
  → approval_signature = "gpg/ssh_signed_hash"
  → seeds WORLD_TRUTH_CONTRACT_v1 coordinate/layout builders
  → proposal archived in Creative Memory with lineage_tag
IF REJECTED/DEFERRED:
  → routes to INTENT_SHADOW_CREATIVE_SPEC (Creative Memory lane)
  → retains as dormant variant for future iteration
```

**Hard Rules**:
- `approved` status requires cryptographic signature from Tier-3 actor.
- Once approved, the candidate graph becomes a **read-only truth seed**. Builders generate terrain/coordinates from it, but the seed itself never mutates.
- `proposal_hash` must match AP verification. Hash drift = proposal corruption.

---

## 7. Rejection & Shadow Routing

Rejected or deferred map candidates are routed to `Intent Shadow` under the **Creative Memory** lane.

```json
{
  "shadow_id": "uuid",
  "lane": "creative",
  "entry_type": "rejected_proposal",
  "content_snapshot": "truncated map_candidate.zonj",
  "lane_metadata": {
    "branch_point": true,
    "sequel_hook": "alt_coastal_topology_v2",
    "narrative_theme": "divergent_geography",
    "exploration_confidence": 0.78
  },
  "metadata": {
    "actor_id": "cartographer_v1",
    "reality_mode": "DRAFT",
    "source_contract": "CARTOGRAPHER_ABI_v1"
  }
}
```

**Rule**: Rejected proposals may seed future cartographer runs, but NEVER auto-resurrect without explicit user/AP trigger.

---

## 8. Integration with Constitutional Stack

| Layer | Cartographer Interaction | Boundary Guarantee |
|-------|-------------------------|-------------------|
| **World Truth** | Seeds approved layouts | Never mutates `snapshot`. Only approved graphs enter truth. |
| **AP Gate** | Validates schema + tier + hash + scale | Blocks `"approved"` without signature. Routes malformed proposals to shadow. |
| **Intent Shadow** | Archives rejected/deferred variants | Preserves as dormant potential. No auto-mutation. |
| **Terrain/Region ABIs** | Downstream consumers | Terrain/visibility systems MAY NOT run until cartographer graph is `approved`. |
| **Renderers** | Zero interaction | Cartographer outputs spatial logic, not visuals. Art packs bind later. |

---

## 9. Testing Invariants

If a test conflicts with this ABI, **the test is wrong**.

Tests must verify:
- `approval_status` is always `"proposed"` before AP gate
- `world_scale` is present and matches declared enum values
- No absolute coordinates exist in `map_candidate.zonj`
- `proposal_hash` matches payload before and after routing
- Rejected variants route to Creative Memory with correct lane metadata
- Tier-3 signature is required for `approved` status transition
- Cartographer generates identical output for identical seed + source
- Narrative precedence test: explicit book direction > inferred spatial symmetry
- Mermaid surface contains NO executable or state-mutating directives

---

## 10. Version History

| Version | Date | Change | Approved By |
|---------|------|--------|-------------|
| v1.0 | 2026-05-30 | Initial frozen ABI. Defines cartographer as proposal-only engine with explicit approval gate, shadow routing, and narrative anchoring. | Tier-3 (User) |
| v1.1 | 2026-05-30 | Added explicit narrative precedence law. Added `world_scale` field + validation rules. Updated testing invariants. | Tier-3 (User) |

---

> **Final Reminder**:  
> The cartographer draws possibilities.  
> The world truth owns geography.  
> Narrative truth precedes spatial truth.  
> The user decides which possibility becomes reality.  
> Never let a proposal become canon without approval.  
> Never let approval bypass signature.  
> Never let a map speak for truth.
```

---

✅ **ABI Revised & Frozen (v1.1)**

The two requested additions are now explicitly baked into the contract:
1. **Narrative Precedence Clause**: Frozen in Section 1 and Section 5. Spatial inference never overrides explicit narrative travel/direction. The book remains authoritative.
2. **World Scale Declaration**: Added as a required top-level field in the schema with strict enum validation. Scale dictates downstream distance calibration, region chunking, and travel heuristics.

The dependency chain is now crystal clear:
```text
Narrative Truth → Cartographer Proposal (with Scale) → AP/Tier-3 Approval → World Truth → Semantic Terrain → Region Visibility → Engine View → Renderer
```

**Next in build order**:  
`2. SEMANTIC_TERRAIN_ABI_v1` (approved anchors + scale → terrain meaning)

Shall I draft `SEMANTIC_TERRAIN_ABI_v1.md` now, strictly bound to consume approved cartographer graphs and output art-agnostic terrain semantics?
