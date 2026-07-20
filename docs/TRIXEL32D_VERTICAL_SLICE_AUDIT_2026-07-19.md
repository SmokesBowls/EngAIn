# Trixel 3.2d Vertical Slice — Read-Only Audit and Forward Handoff

Audited 2026-07-19, evidence-backed, read-only. Every commit hash below was
resolved in its repository and every SHA-256 was recomputed from bytes on
disk during this audit. Nothing was implemented, no slot was cleared, the
quarantine was not touched, and no unrelated dirty file was modified.

Repositories:

- `trixel3.2d` — Trixel authority: ingress, builder, policies, fixtures
- `EngAIn` — EngAInOS authority: assembly, gates, transport, authorization
- `godotollama` — downstream proof repo: passive consumer, apply executor,
  turntable, Blender diagnostic lane
- `texel-studio` — upstream asset snapshot (verified: **no git history**)

## 1. Chain verification — all confirmed

Every stage of the completed slice, its commit(s), and its recomputed
artifact identity:

| Stage | Commit(s) | Artifact identity (recomputed) |
|---|---|---|
| Texel grass tile pinned | trixel3.2d `e78a404` | PNG `ab5cb28b956f418272dacb367395da958671faf7c6e096e2d5b2cf6fa4363d51` ✔ |
| Policy 1: lattice (3×2 first proof) | trixel3.2d `f3cc101`; EngAIn `610399c` | payload `bc1951f5…` byte-identical in trixel3.2d, EngAIn tests, godotollama ✔ |
| Policy 2: stitched `HEIGHT_FIELD_CONNECTED_SURFACE` | trixel3.2d `dfeae71` | payload `86d8b220…` byte-identical trixel3.2d ↔ EngAIn ✔; limitation `T_JUNCTION_WALL_EDGES` |
| Policy 3: complete-edge `HEIGHT_FIELD_COMPLETE_EDGE_CONNECTED_SURFACE` | trixel3.2d `e455138` | payload `49396807…` byte-identical in trixel3.2d, EngAIn, godotollama ×2 (executor + Blender lanes) ✔; limitation `PINCH_EDGE_NON_MANIFOLD` (34 corners, inventory locked) |
| Apply contract gate | EngAIn `e16d0a7` | 50 contract-only toxic proofs |
| Response-side transport | EngAIn `a7e7d7b` | stitched drop → intake → apply gate |
| Request-side transport loop | trixel3.2d `b743c7e`; EngAIn `3eca41e` | live slots, byte-identical rebuild |
| Complete-edge transport | EngAIn `e70e619` | identity-keyed slots `t32ddrop_49396807…`, `t32ddrop_f3a1ca98…` present on disk ✔ |
| Apply-authorization exporter | EngAIn `4e0d1bb` | deterministic artifact `5467c9c6…`, 5 proofs; live export byte-identical to vendored fixture ✔ |
| Passive Godot consumer + rendering boundary | godotollama `b05e704`, `9262f4f`, `d3556ec` | 10 headless tests; retained lattice PNG |
| Isolated Godot apply executor | godotollama `ea14085`; docs `04cf95b` | screenshot `17643d5b…` ✔, live apply report `66bd4d45…` ✔ (uncommitted by doctrine), authorization `5467c9c6…` ✔ |
| Diagnostic turntable | ticket `0b5d898`; godotollama `88ecf6c`; close-out `e8b3b52` | manifest `3c3d127f…` ✔, contact sheet `bcf5f95c…` ✔, deterministic across three runs |
| Blender diagnostic consumer | ticket `96c0370`; godotollama `4679ed4` (user-verified) | 10/10 proofs; exact basis-inverse; normals min-dot 1.0; committed evidence set |
| Ticket/handoff docs | EngAIn `c073871`, `aa6c1aa`, `938b765`, `6714585` | all resolve ✔ |

All 25 referenced commits resolve. All cross-repository vendored copies are
byte-identical to their authority-owned originals. The exporter reproduces
the accepted authorization bytes deterministically, and the turntable and
Blender lanes reproduce their evidence deterministically.

## 2. Ownership boundaries — clean

- Texel → Trixel: only pinned PNG bytes cross; ingress is Trixel-owned.
- Trixel → EngAIn: only checksum-locked built-response bytes cross;
  EngAIn re-validates fail-closed at intake.
- EngAIn → Godot: only two checksum-locked artifacts cross (built
  response + apply authorization); a renderer-side consume report is
  proven **rejected** as authority (executor test 03).
- Trixel → Blender: raw Trixel-owned built-response bytes only, vendored
  byte-identical; Blender is proven outside the authority chain.
- No component invents topology, metric, or appearance downstream; all
  proofs verify exact byte or float32-quantization fidelity.

## 3. Unresolved limitations and open checklist items

1. **`PINCH_EDGE_NON_MANIFOLD`** (complete-edge policy): 34 inventoried
   lattice corners where the true solid's boundary is non-manifold —
   inventory is locked with exact `lattice_x/lattice_y` and height
   intervals in `texel_complete_edge_surface_manifest.json`. Collision is
   denied and untested for every policy.
2. **`T_JUNCTION_WALL_EDGES`** (stitched policy): unrepaired; the stitched
   policy is intentionally absent from the Godot consumer's whitelist.
3. **Collision**: never granted anywhere. The `CollisionGrantEvidence`
   path in the apply gate exists but has only ever been exercised as a
   rejection (tamper proofs). No collision mesh artifact or contract
   exists.
4. **Canonical world**: no canonical placement, no persistence
   (`SCENE_BOUND` only; `CANONICAL_PERSISTENT` requires trusted
   persistence authorization, never exercised), no live application
   route (`REPLACE_EXACT` unexercised), consume report not returned
   through EngAInOS.
5. **Open TODO checkboxes** (verified in the TODO): `recipe_base_colors`
   bootstrap decision; live-route passive consumer replacement;
   live-route report extension and return through EngAInOS; the entire
   final vertical-slice acceptance checklist (intentionally unchecked —
   it describes the live route, not the isolated proofs).
6. **Quarantine**: `godotollama trixel_proof/trixel32d_runtime/` remains
   untracked, byte-untouched, with **zero** references from outside
   itself (re-verified). Disposition is still an undecided ticket.

## 4. Dirty/untracked inventory (verified, untouched)

- trixel3.2d: `TODO.md` modified + untracked doctrine docs
  (`.hermes/`, `3.2_trixel_doctrine.md`, `HANDSHAKE_PROTOCOL.md`,
  handshake notes, `archive/`, `dual_grid3d.md`) — pre-existing,
  outside this slice's scope, disposition belongs to the user.
- EngAIn: `runtime/` trees (requests, built drops, reports, apply
  authorizations — flat historical slots plus identity-keyed slots) —
  intentionally uncommitted live artifacts per slot doctrine.
- godotollama: `screenshot_trixel_profile_broad_terraces.png` modified
  (pre-existing, excluded from every commit, awaiting disposition);
  `pyroclast/` sidecar `.uid`/`.import` files (unrelated lane);
  quarantined `trixel32d_runtime/`.
- texel-studio: snapshot without version control — upstream provenance
  is pinned only through accepted artifact checksums, which is the
  declared design, but the tool itself is unversioned (production risk,
  §6.5).

## 5. Overfit inventory — what is bound to the single grass fixture

Distinguish two kinds. **Proof-lane bindings (by design, acceptable):**
per-fixture constants in the Godot executor tests, turntable harness, and
Blender consumer (`EXPECTED_SURFACE_ID`, counts, node name, transform
origin) — these are evidence locks, not pipeline behavior.

**Pipeline bindings (real generalization debt):**

1. **EngAIn apply-authorization exporter** builds its packet, authority,
   and scene truth by importing **test-module helpers**
   (`complete_edge_apply_packet`, `authority_for`,
   `canonical_scene_truth`) with a hardcoded origin `[2.0, 0.5, -1.0]`.
   There is no production request→authorization path: a second surface
   requires either editing the exporter or writing a parallel one.
2. **Scene truth is a test fixture.** The declared target tuples and slot
   occupancy live in `test_trixel32d_surface_apply.canonical_scene_truth`;
   no authority-owned scene-truth source exists.
3. **Godot passive consumer policy table** whitelists exactly lattice +
   complete-edge; every new policy requires a consumer extension (the
   corrected-ticket doctrine accepts this, but it is a per-policy cost).
4. **Appearance**: every texel-lane cell carries recipe
   `default.generic`; the terrain-recipe registry reconciliation (nine
   WorldField identities) is unexercised by the image-ingress path, and
   the `recipe_base_colors` duplication decision is still open.
5. **Elevation derivation**: `LUMINANCE_HEIGHT` is one of only two
   ingress elevation policies; the grass tile's palette happens to
   produce well-spread terraces. A second tile with a flat-luminance
   palette will produce degenerate height fields with no declared
   policy to say otherwise.
6. **Isolated executor honors exactly** VISIBLE / CREATE_ONLY /
   SCENE_BOUND / PRESENTATION_ONLY — correct for the proof, but the
   remaining declared modes have zero executor coverage.

## 6. Obstacles per goal

### 6.1 Importing a second unrelated tile

**No contract obstacle exists.** The ingress accepts any dimensions and
declared elevation policy; the builder, transport, and gates are
identity-keyed (fresh `t32ddrop_<sha16>` slots). The real obstacles:
exporter/scene-truth hardcoding (§5.1, §5.2), per-fixture proof lanes
needing parametrization or new instances, and no documented end-to-end
recipe for "new tile in, evidence out."

### 6.2 Joining tiles without internal perimeter walls or cracks

**Blocked by missing construction-time adjacency identity.** Verified:
the request contract (both fixture profiles) carries only tile-local
cell keys (`"0,0"`…); no tile origin, no world offset, no neighbor
declaration. The complete-edge builder erects perimeter walls
unconditionally at the tile boundary; two independently built slabs
placed side by side will have doubled internal walls and no guarantee of
bitwise-coincident border vertices (crack risk). Placement identity
exists **only** at the application layer (per-surface transform), which
cannot suppress construction-time geometry.

### 6.3 Canonical Godot-world placement

Blocked by: no authority-owned scene truth (§5.2); no persistence
authorization path exercised; no live application route (the isolated
executor is proof-scoped; the quarantined attacher is rejected); consume
report not returned through EngAInOS; `REPLACE_EXACT`/update lifecycle
unexercised.

### 6.4 Collision authorization

Blocked by, in order: `PINCH_EDGE_NON_MANIFOLD` (geometry must become
manifold or a separate collision representation must exist);
**render-mesh vs collision-mesh separation** — the apply contract
already carries the seam for this (`collision.shape_policy`, e.g.
`CANONICAL_MESH_EXACT` appears in tamper proofs), but no collision-mesh
artifact, contract, or builder exists; `CollisionGrantEvidence` never
exercised as a grant; no physics executor.

### 6.5 Repeatable production use

Manual multi-step choreography across four roots; Texel generation
requires manual visual acceptance and its upstream `requirements.txt`
omits `langchain-openai`; texel-studio is unversioned; no slot-clearing
tool exists (by doctrine — every dispatch needs a fresh identity, which
scales, but flat historical slots are permanently occupied); runtime
artifact retention policy undefined; no CI runs the three proof suites
(EngAIn 138 pytest / Godot 10+12 headless / Blender 10 subprocess).

## 7. Do the contracts already contain enough identity for neighboring tiles?

**Application layer: yes.** `trixel32d_surface_apply.v1` addresses
multiple surfaces today — distinct `(parent_kind, parent_id,
application_slot_id)` tuples, per-surface transforms, occupancy
tracking, and intent digests binding each authorization to one surface.
Two neighboring tiles can be *placed* correctly right now.

**Construction layer: no.** Neither `trixel32d_surface_request` nor
`trixel32d_surface_built` can express where a tile sits relative to
another tile or what lies beyond its border. Seam-free joining therefore
requires a versioned request extension (tile origin + declared neighbor
border data), not a reinterpretation of existing fields. The built
response's `cell_geometry_ranges`/`primitive_provenance` are rich enough
to carry per-edge wall attribution once the request can declare
adjacency.

## 8. Dependency-ordered roadmap — next three smallest tickets

### Ticket A — Second unrelated tile, end to end (generalization proof)

Smallest ticket; no contract changes; flushes §5.1–§5.2 and §6.1.

- Generate and visually accept one new Texel tile with a deliberately
  different palette and height character; pin its PNG SHA-256.
- Ingress → complete-edge build → fresh identity-keyed transport slots →
  intake → apply authorization for a **second declared slot**, requiring:
  a parametrized production exporter (payload path + expected SHA +
  target + transform as validated inputs; test-module imports removed)
  and a first authority-owned declared-scene-truth artifact (may be a
  committed static declaration).
- Isolated Godot application of **both** slabs side by side (distinct
  origins, both `CREATE_ONLY`), one screenshot; Blender diagnostic run
  of the new payload through the existing consumer generalized only by
  parametrizing its expected-identity constants (defaults preserved).
- **Acceptance proofs:** new payload checksum locked; complete ordered
  substitution matrix across all four identities (12 substitutions);
  both slabs applied
  with per-surface invariants; all existing evidence byte-identical;
  every prior suite still green.
- **Forbidden scope:** no adjacency/seam work, no shared borders (tiles
  visibly apart), no collision, no persistence, no canonical world, no
  quarantine contact, no slot clearing.
- **Stop points:** after visual acceptance of the new tile's PNG; after
  presenting dual-slab evidence, before any commit.

### Ticket B — Construction-time adjacency: two tiles, one canonically owned seam

Depends on A (a second tile must exist). Addresses §6.2 and §7.

- Version the request contract (e.g. `tile_placement` block: integer
  tile origin in field units + per-edge neighbor declaration bound to a
  prior authority-owned identity — the neighbor ingress/request checksum
  plus a canonical border-strip digest covering the declared border
  heights/colors. Do **not** bind adjacency to the neighbor built-payload
  SHA-256: reciprocal payload declarations would create a circular
  dependency. Adjacency remains identity-locked, not trusted).
- Builder: suppress perimeter walls along declared shared edges only;
  emit border vertices from the declared shared data so both tiles'
  seam vertices are **bitwise identical**; walls at height differences
  across the seam follow the same complete-edge rule as interior walls.
- **Acceptance proofs:** automated geometric checks — equal heights:
  zero interface-wall primitives; differing heights: exactly one canonical
  exposed interval set, owned once; in all cases: no duplicate walls,
  overlaps, gaps, or new T-junctions. Also prove bitwise vertex coincidence
  where the seam coordinates are shared, re-lock the pinch inventory for
  both tiles, and prove deterministic rebuild. A Blender diagnostic view
  of the joined pair provides an independent seam witness; the joined pair
  still requires visual acceptance.
- **Forbidden scope:** no N×N streaming, no runtime/application
  changes, no collision, no canonical world; undeclared-neighbor
  requests must build exactly as today (backward compatibility proof).
- **Stop points:** contract text review before implementation; joined
  visual evidence before commit.

### Ticket C — Manifold repair policy (collision precursor, still no collision)

Independent of B in mechanism, ordered after it so the repair rule is
proven compatible with seam suppression. Addresses §6.4's first gate.

- Fourth topology policy (complete-edge + pinch repair): resolve the
  locked 34-corner inventory by an explicit, named, deterministic rule.
  The rule must make an explicit connectivity choice or introduce genuine
  geometric separation; index-only vertex duplication at geometrically
  coincident coordinates does not qualify. Declare what solid
  interpretation changes, and state exactly where sampled heights and
  colors are promised to remain preserved. The policy declares its own
  limitation field empty only if the automated check passes.
- **Acceptance proofs:** manifold verification after coordinate welding or
  equivalent point-neighborhood analysis, so geometrically coincident
  non-manifold wedges cannot pass through index statistics alone. Prove
  the declared connectivity or genuine separation, the declared change in
  solid interpretation, and preservation of sampled heights/colors where
  promised. Run an independent Blender-lane witness, but do not treat its
  topology statistics alone as manifold proof. The pinch inventory for the
  new policy must be the locked empty set; complete-edge policy and its
  evidence remain untouched; visual acceptance must show whether any
  declared geometric separation is visible at display scale.
- **Forbidden scope:** **collision remains denied and untested** —
  repair is geometry truth, not authorization; no physics, no collision
  mesh artifact yet, no shape generation, no changes to policies 1–3.
- **Stop points:** repair-rule text review before implementation;
  manifold evidence before commit.

After C, the shortest remaining path is: collision-mesh contract
separation (render vs collision artifact, using the existing
`shape_policy` seam) → first exercised `CollisionGrantEvidence` grant →
authority-owned scene truth hardening → live application route with the
consume report returned through EngAInOS — each as its own ticket.

## 9. Audit boundaries

This audit modified nothing outside this document. Slots, quarantine,
dirty files, and all accepted evidence were read only. This document is
the sole intended commit. Approval and commit of this audit do not issue
Ticket A or authorize any roadmap implementation automatically.
