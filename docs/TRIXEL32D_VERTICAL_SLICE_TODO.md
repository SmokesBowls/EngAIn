# Trixel 3.2d Vertical Slice TODO

> **START HERE NEXT SESSION.** This is the authoritative handoff (user-authored
> 2026-07-17, end of day; supersedes TRIXEL32D_VERTICAL_SLICE_PLAN.md). The
> canonical fixture is already exported and gate-verified:
> `tier1/engainos/tests/fixtures/trixel32d_request_3x2_first_proof.json`
> (request_id `t32dreq_8b14a3bac98d1025`). Jump to **Current next command** at
> the bottom.

**Current status:** EngAInOS can assemble and validate a complete deterministic
`trixel32d_surface_request`, and Trixel 3.2d consumes the canonical 3×2 fixture
fail-closed, builds deterministic canonical geometry, emits
`trixel32d_surface_built`, and passes the identity-complete EngAIn built-response
boundary. The exact built response is vendored at
`tier1/engainos/tests/fixtures/trixel32d_surface_built_3x2_first_proof.json`
(SHA-256
`bc1951f55de00aa0114679fab1a46d80439d1b840309b0df4c9b835539dd2929`) and remains
byte-identical to the Trixel-owned fixture. The separate Godot proof at
`/mnt/data-drive/godotollama` commit `b05e704` consumes those exact bytes,
validates the response fail-closed, creates one in-memory
`ArrayMesh`, and emits a deterministic consume report; all 10 headless tests
pass under Godot 4.6.1. A standalone diagnostic harness subsequently assigned that
exact returned object unchanged to a temporary `MeshInstance3D`, displayed the
supplied vertex colors, rendered and validated a 960×720 PNG, and reported the
fixture checksum, mesh counts, and AABB. The harness is accepted as the completed
rendering-boundary proof for this fixture. Its retained picture is evidence, not a
fixture-design target, and must not be revisited or replaced. A cube, curved
pixel-truth surface, or other visual experiment requires a new checksum-locked
fixture, a new Trixel-built mesh, and a separate proof. The accepted harness,
proof test, and retained image are committed in `/mnt/data-drive/godotollama` at
`9262f4f`. The `trixel32d_surface_apply.v1` application validator is implemented,
review-hardened, and committed (`e16d0a7`): trusted authority evidence is bound to
exactly one application intent by a canonical intent digest, scene targeting uses
complete parent-to-slot tuples, and the gate wrapper is FALSE (never SKIPPED) for
any packet claiming the apply contract with mismatched discriminators. Texel
Studio is a committed upstream asset-authoring component (see its section below).
The first Texel-to-Trixel handshake is committed in trixel3.2d: `e78a404` adds
the checksum-pinned grass fixture, the smallest pure Trixel-side image ingress,
and the visually accepted pixel-to-geometry proof; `dfeae71` adds the
`HEIGHT_FIELD_CONNECTED_SURFACE` stitched-slab policy
(`t32dsurface_f024725d200e470c`, one coherent terrain slab, exact colors and
heights preserved) with the declared `T_JUNCTION_WALL_EDGES` limitation that
keeps this geometry explicitly not collision-ready until walls are split per
height interval. The passive response-side transport boundary is committed
(`a7e7d7b`): the exact stitched built response crosses a checksum-locked file
drop into EngAIn intake validation and the unchanged apply-authorization gate,
with three-layer lattice/stitched anti-substitution, fail-closed rejection of
malformed/truncated/stale/duplicated/digest-mismatched drops, clock-free
receipt/identity consume semantics, and collision still unauthorized under
`T_JUNCTION_WALL_EDGES`. The request-side loop is committed (trixel3.2d
`b743c7e`, EngAIn `3eca41e`) and proven live across the real runtime slots:
the complete passive chain now exists on disk — validated request drop →
Trixel deterministic rebuild (byte-identical to the pinned stitched payload)
→ built-response drop → EngAIn intake → intent-bound apply authorization →
receipt. The only remaining boundary is Godot execution/application;
collision stays separately blocked by `T_JUNCTION_WALL_EDGES` until that
geometry limitation is repaired. World placement, runtime application route,
node attachment, and collision allocation still do not exist. The quarantined Godot runtime attacher has been audited read-only against trixel32d_surface_apply.v1: verdict — it cannot be promoted as-is (it self-authorizes from a renderer-side consume report and takes an unvalidated caller-supplied parent as its placement destination); it remains untouched in quarantine. The third construction policy is committed (trixel3.2d `e455138`): `HEIGHT_FIELD_COMPLETE_EDGE_CONNECTED_SURFACE` (`COMPLETE_EDGE_SLAB` / `SHARED_COMPLETE_EDGES`, surface `t32dsurface_cd7eee9d7877c948`, payload SHA-256 `49396807a2d119328608b44203c0a8aae20cfe5ac0028e880676ac538bb7745b`) — the stitched slab rebuilt with complete shared wall edges and zero T-junctions, visually accepted 2026-07-19. Its declared limitation `PINCH_EDGE_NON_MANIFOLD` is locked exactly (34 inventoried lattice corners where the true solid's boundary is non-manifold); no claim is made about downstream collision tooling — collision remains denied and untested. The complete-edge passive transport is committed (`e70e619`) and proven live on fresh identity-keyed slots: policy-aware intake, byte-identical vendored fixtures, six-permutation substitution matrices at the checksum and policy layers plus intent-digest separation, and the unchanged apply gate authorizing the intent-bound complete-edge surface. Slot doctrine: flat slots remain preserved historical proof artifacts; identity-keyed subdirectory slots are normative for new dispatches; no migration, clearing, or deletion is authorized. The isolated Godot apply executor is completed, visually accepted, and committed (godotollama `ea14085`, 2026-07-19): the accepted complete-edge slab was applied through the checksum-locked EngAIn apply authorization into a live scene tree under the declared target with the authorized transform, screenshot and apply-report hashes locked in the evidence manifest — isolated runtime application only; canonical-world integration and collision remain unauthorized; quarantine disposition remains a separate pending decision.

## Completed foundations

- [x] Define the direction of the handshake:
  - MettaExt and the EngAIn crew provide world facts.
  - EngAInOS assembles and authorizes the request.
  - Trixel 3.2d consumes the request and builds canonical geometry.
  - EngAInOS alone authorizes runtime application and collision intent.
  - GodotSim may execute or refuse exact physical declarations; it does not grant AP.
  - Godot materializes the supplied geometry and returns a report.

- [x] Define the five `trixel32d_surface_request` information blocks:
  - Identity and provenance
  - Grid facts
  - Coordinate declaration
  - Authorized metrics
  - Construction instruction

- [x] Map tier2 crew responsibilities:
  - Topologist: accepted qualitative spatial truth and provenance origin
  - Cartographer: metric coordinates, units, axis contract, extents, and source hashes
  - WorldField: complete per-cell grid facts
  - GodotSim: runtime state, embodiment/materialization evidence, and proof gates
  - Engionality: accept/apply/reject/rollback machinery
  - EngAInOS: final assembly, authorization, validation, and routing

- [x] Rehouse the terrain lane as `tier2/worldfield/`.

- [x] Preserve WorldField's responsibilities:
  - sparse 2D float field
  - terrain sculpting
  - per-cell normalized elevation
  - threshold-based terrain classification
  - terrain delta events
  - terrain-plan generation

- [x] Implement `tier2/worldfield/grid_facts_emitter.py`.

- [x] Emit `worldfield_grid_facts.v1` with: width, height, row-major complete
      coverage, field_x, field_y, elevation, terrain, recipe, explicit
      `unmapped_terrains`.

- [x] Reconcile nine WorldField terrain identities with existing Trixel recipe
      identities.

- [x] Fail visibly on unmapped terrain names instead of guessing.

- [x] Preserve Trixel's existing proven contracts:
  - `worldfield_to_worldcell_projection.v1`
  - terrain recipe registry
  - deterministic recipe rendering
  - coordinate seam lock
  - request validator
  - built-response validator

## EngAInOS request assembler — completed

- [x] Implement `tier1/engainos/bridgeroom/trixel32d_request_assembler.py`.

- [x] Join the declared crew contributions:
  - `worldfield_grid_facts.v1`
  - Cartographer metric grant
  - MettaExt/Topologist/Cartographer provenance
  - EngAInOS construction policy

- [x] Require Cartographer as the declared metric authority.

- [x] Stamp the locked orientation doctrine:
  - field_x → RIGHT
  - field_y → FORWARD
  - standard Y-up
  - explicit finite orientation vectors

- [x] Mint deterministic request IDs from canonical content hashes.

- [x] Validate assembled packets with the existing EngAInOS Trixel handshake gate.

- [x] Reject missing, contradictory, unauthorized, shuffled, or incomplete inputs.

- [x] Add the real 3×2 first-proof test fixture:
  - six WorldField cells
  - three elevations
  - two recipe identities
  - six authorized height layers
  - one topology policy
  - no collision
  - no world placement

- [x] Pass all six EngAIn-side assembler tests.

- [x] Commit the assembler and tests: `610399c`.

## Temporary bootstrap decision

- [ ] Review `recipe_base_colors`.

The current request validator requires RGBA values, while appearance is intended
to be recipe-driven. EngAInOS currently receives a declared `recipe_base_colors`
table through construction policy and rejects recipes without a declared color.

This is acceptable for the first proof because the assembler does not invent
colors.

Before the final contract is frozen, decide whether Trixel's recipe registry
should become the sole color authority. The eventual request may carry:

```text
recipe identity
recipe version/hash
```

instead of duplicating recipe-owned colors.

## Trixel-side fixture build — completed

### Build the Trixel-side fixture consumer and canonical surface builder

- [x] Export or preserve the exact passing 3×2 assembled request as a canonical
      fixture. → `tier1/engainos/tests/fixtures/trixel32d_request_3x2_first_proof.json`
      (exported 2026-07-17, re-validated through the gate after export:
      request_id `t32dreq_8b14a3bac98d1025`).

- [x] Add a Trixel-side request consumer that:
  - loads the fixture;
  - validates its contract and packet type;
  - verifies deterministic row-major coverage;
  - rejects missing or duplicated cells;
  - verifies all metrics and orientation declarations;
  - rejects unresolved recipe mappings;
  - invokes no EngAIn implementation code.

- [x] Build the smallest canonical Trixel surface from that fixture.

- [x] Use Trixel's proven coordinate mapping:

```text
field_x   → world_cell_x
field_y   → world_cell_z
elevation → world_cell_y
```

- [x] Apply the declared authorized vertical metric.
- [x] Apply one explicit topology policy.
- [x] Preserve cell ownership and provenance.
- [x] Emit `trixel32d_surface_built`.
- [x] Return either:
  - `BUILT` with canonical geometry and provenance; or
  - `REJECTED` with `geometry = null` and the first blocking error.
- [x] Pass the existing EngAIn built-response validator.

- [x] Persist the exact canonical built response at
      `../trixel3.2d/fixtures/trixel32d_surface_built_3x2_first_proof.json` and
      lock canonical regeneration equivalence in the Trixel tests.

## Required `trixel32d_surface_built` proof

- [x] Include contract/version.
- [x] Include request ID and surface ID.
- [x] Include `BUILT` or `REJECTED` status.
- [x] Include local Y-up coordinate-space declaration.
- [x] Include canonical vertex positions.
- [x] Include deterministic triangle indices and winding.
- [x] Include UV or pixel-address mapping.
- [x] Include cell geometry ranges.
- [x] Include primitive or cell provenance.
- [x] Include topology-policy identity.
- [x] Include declared appearance truth.
- [x] Include explicit normals policy.
- [x] Include explicit tangents policy.
- [x] Include errors for rejected results.
- [x] Produce byte-stable or canonically equivalent results from identical inputs.

## EngAIn built-response identity boundary — completed

- [x] Vendor the exact canonical 3×2 built-response bytes under EngAIn tests.
- [x] Independently pin SHA-256
      `bc1951f55de00aa0114679fab1a46d80439d1b840309b0df4c9b835539dd2929`.
- [x] Require exact `trixel32d_surface_built.v1` contract and packet type.
- [x] Require a separately supplied request that passes the complete request gate;
      reject self-embedded `request_context` authority.
- [x] Match response `request_id` to trusted `identity.request_id`.
- [x] Require response topology to match trusted
      `construction.topology_policy`, then recompute deterministic `surface_id`
      from that trusted topology.
- [x] Hash and parse the same response byte buffer.
- [x] Return the calculated response digest with a deeply immutable accepted packet.
- [x] Reject missing, stale, swapped, unknown, duplicate, or nonstandard JSON
      identity material with no input mutation and no accepted partial packet.
- [x] Keep dict-only validation semantic-only; application binding must consume
      the byte-level validation result.

## Trixel acceptance gates

- [x] Every request cell is consumed exactly once.
- [x] Every source cell has a terminal disposition.
- [x] Every canonical primitive has ownership or structural provenance.
- [x] No geometry is created from undeclared input.
- [x] No undeclared cell loss occurs.
- [x] No undeclared merge occurs.
- [x] No undeclared split occurs.
- [x] No undeclared topology inference occurs.
- [x] Recipe identities are resolved explicitly.
- [x] Coordinate orientation is preserved.
- [x] Authorized metrics are preserved.
- [x] Compilation is deterministic.
- [x] Malformed requests fail before geometry construction.
- [x] Rejected results contain no partial geometry.

## Transport — after the fixture builder passes

The first transported payload is the stitched `HEIGHT_FIELD_CONNECTED_SURFACE`
built response (trixel3.2d `dfeae71`), moved passively response-side first: the
current next command proves the drop → intake → apply-gate boundary without
placement. Collision stays unauthorized under `T_JUNCTION_WALL_EDGES`.

### Response-side built-drop intake — completed

- [x] Clone the boot file-drop pattern for the built-response boundary:
      fixed-name envelope + payload drop, fixed-path receipt as the consume
      state (identity semantics, no clock, no second ledger). → `a7e7d7b`,
      `tier1/engainos/bridgeroom/trixel32d_built_drop_intake.py`.
- [x] Verify SHA-256 over raw payload bytes against the envelope declaration
      and the caller-supplied trusted expected identity before parsing.
- [x] Make the handshake gate policy-aware (mirrored topology↔gap-fill pairs;
      stitched per-cell surface inventory) with lattice validation and the
      canonical 3×2 fixtures byte-identical.
- [x] Prove transported-unchanged, end-to-end intent-bound authorization,
      three-layer anti-substitution, fail-closed drop rejection, receipt only
      after intake plus apply-gate TRUE, and collision GRANTED rejecting under
      the proof authority. 11 proofs; suite 209 passed; proof runner
      `executors/trixel32d_built_drop_intake_proof_v1.py`.

### Request-side transport loop — completed

- [x] EngAInOS dispatcher validates request bytes through the existing
      validator before writing and dispatches the exact bytes unchanged;
      invalid requests dispatch nothing; occupied slots refuse duplicates.
      → EngAIn `3eca41e`, `tier1/engainos/bridgeroom/trixel32d_request_dispatch.py`.
- [x] Trixel command consumer verifies the payload checksum before parsing,
      validates/builds through the existing consumer and builder unchanged,
      and serializes the response exactly once with the declared canonical
      serialization — rebuilt response byte-identical to the pinned stitched
      payload. → trixel3.2d `b743c7e`.
- [x] Live loop proof across the real runtime slots with a hardened
      subprocess boundary; request-ID correlation end to end; 14 new proofs
      (10 Trixel + 4 EngAIn); suites 53 and 213 passed.
      → `executors/trixel32d_request_loop_proof_v1.py`.

Slot-occupancy doctrine: successful and REJECTED outcomes both intentionally
occupy their drop/receipt slots — occupation is the consume state. Clearing a
slot is a separate, explicitly authorized destructive operation reserved for
a future operational ticket; no slot-clearing tool exists yet, and live
drops/receipts under `runtime/` stay uncommitted.

- [x] Clone the proven EngAIn boot file-drop pattern instead of inventing a new
      transport.

Suggested request path:

```text
runtime/trixel32d_requests/TRIXEL32D_SURFACE_REQUEST_V1.json
```

Suggested response path:

```text
runtime/trixel32d_reports/TRIXEL32D_SURFACE_BUILT_V1.json
```

- [ ] Implement an EngAInOS dispatcher that writes only validated requests.
- [ ] Implement a Trixel command consumer that:
  - validates the exact contract string;
  - consumes each request deterministically;
  - writes a built or rejected response;
  - never mutates EngAIn state directly.
- [ ] Preserve request ID correlation across request and response.
- [ ] Refuse stale, malformed, mismatched, or incomplete packets.
- [ ] Add transport-level request → act → report gates.

## Runtime application handshake

- [x] Define `trixel32d_surface_apply.v1` as a contract-only authority artifact:
      `docs/contracts/TRIXEL32D_SURFACE_APPLY_CONTRACT_v1.md`.

This is an EngAInOS-issued authorization for a future executor after Trixel
returns canonical geometry; it is not a new EngAInOS-to-GodotSim transport. It
declares:

- target scene
- surface identity
- parent/runtime location
- Trixel-local-to-declared-scene transform
- visibility intent
- replacement/update behavior
- lifetime/persistence
- collision allowed or denied
- collision layer and mask
- static/dynamic/presentation-only classification

- [x] Keep world placement outside `trixel32d_surface_built`.
- [x] Keep collision authorization outside `trixel32d_surface_built`.
- [x] Require explicit EngAInOS collision authorization; GodotSim may execute or
      refuse the exact physical declaration but may not grant AP or rewrite it.

### Application authorization gate — completed

- [x] Implement `tier1/engainos/gates/gate_trixel32d_surface_apply.py` with
      contract-only toxic proofs (50 tests) at
      `tier1/engainos/tests/test_trixel32d_surface_apply.py`; commit `e16d0a7`.
- [x] Closed-world validation at every object level; canonical `t32dapply_`
      identity; surface binding cross-checked against the byte-level
      `BuiltSurfaceValidation` result (dict-only semantic substitutes reject).
- [x] Bind `TrustedApplicationAuthority` to exactly one application intent via a
      deterministic canonical intent digest covering apply_id, surface binding,
      target, transform, visibility, replacement, lifetime, classification, and
      collision declaration; reusing one authority for any other intent rejects.
- [x] Validate targeting against trusted complete
      (parent_kind, parent_id, application_slot_id) tuples; a declared slot
      cannot be used under a foreign declared parent.
- [x] REPLAY always rejects; FINALIZED requires the Tier 3 human authority
      root; ap_rule_ids must match accepted AP evidence.
- [x] Require a strictly positive basis-column determinant; explicit
      VISIBLE/HIDDEN only; CREATE_ONLY/REPLACE_EXACT with exact occupancy;
      CANONICAL_PERSISTENT requires explicit trusted persistence authorization.
- [x] Collision DENIED requires NONE/0/0; GRANTED requires spatial
      classification plus trusted `CollisionGrantEvidence` covering the exact
      scene revision, binding, transform, policy, layer, and mask; flipping a
      digested DENIED declaration to GRANTED rejects.
- [x] Gate wrapper returns SKIPPED only when neither discriminator claims the
      apply contract; a claiming packet with a missing or mismatched
      discriminator is FALSE.

## Passive Godot consumer

- [x] Complete the fixture-driven passive materialization proof in the separate
      Godot repository (`/mnt/data-drive/godotollama`, commit `b05e704`):
  - hashes the exact bytes subsequently parsed;
  - receives the expected fixture checksum from the headless proof harness;
  - validates the complete built response before materialization;
  - maps positions, normals, UVs, colors, and indices without regeneration;
  - creates exactly one in-memory `ArrayMesh`;
  - rejects on the first blocking error with no mesh or arrays;
  - creates no material, collision, transform, scene-tree attachment, transport,
    or canonical/runtime mutation;
  - passes all 10 headless tests under Godot 4.6.1.

### Diagnostic rendering-boundary proof — accepted and closed

**The harness proves that Godot can render the exact passive-consumer return without
rebuilding or duplicating the mesh. This evidence is accepted; do not reopen it to
improve or replace the retained picture.**

- [x] Add a standalone diagnostic harness under
      `/mnt/data-drive/godotollama/trixel_proof/trixel32d_passive/diagnostics/`.
- [x] Verify the canonical fixture checksum before calling the existing public
      `Consumer.consume_file(...)` entry point.
- [x] Temporarily attach the exact returned mesh object without rebuilding it.
- [x] Produce and validate a 960×720 PNG as retained diagnostic evidence.
- [x] Change the diagnostic camera source to the requested clearly oblique
      `Vector3(1.35, 0.9, 1.15).normalized()` direction. The retained PNG still
      predates this camera-source change and is intentionally not rerendered.
- [x] Accept the harness as the completed rendering-boundary proof and commit its
      script, proof test, and retained image without modifying the canonical
      fixture, passive consumer, project configuration, or authority path.

Closure rule:

- do not revisit this picture or use a new picture to replace this evidence;
- a cube, curved pixel-truth surface, or other geometry experiment starts with a
  new fixture and a new Trixel-built mesh and closes under its own separate proof;
- this harness authorizes no collision, physics, world placement, transport,
  runtime wiring, application transform, or canonical mutation.

- [ ] Replace the old Godot terrain proof's authority-heavy behavior in the live
      application route with a passive consumer that:
  - parses the delivered packet;
  - validates contract and status;
  - materializes delivered positions and indices;
  - applies declared UVs or pixel mapping;
  - applies declared appearance;
  - applies the authorized transform;
  - creates collision only when explicitly granted;
  - avoids generating terrain topology;
  - avoids inventing axis mapping;
  - avoids inventing scale;
  - avoids inventing terrain colors;
  - avoids silent defaults;
  - fails closed on missing declarations.

- [ ] Keep legitimate downstream render operations:
  - ArrayMesh or SurfaceTool materialization
  - engine material creation from declared appearance
  - nearest-neighbor texture application
  - viewport/camera/presentation work
  - verification and reporting

## Godot consume report

- [x] Emit the fixture-proof `godot.trixel32d_surface_consume_report.v1` with
      response/surface identities, acceptance result, first blocking error,
      exact source checksum, geometry counts, mapped Godot array types/counts,
      and passive-materialization status.

- [ ] Extend the live-route report only after the application contract exists to
      include coordinate/winding verification, declared appearance application,
      authorized transform application, and collision applied-or-denied state.

- [ ] Return the report through EngAInOS.

## First complete elbow-to-elbow proof

Run only the 3×2 fixture through:

```text
WorldField
    ↓
EngAInOS request assembler
    ↓
request validator
    ↓
Trixel surface builder
    ↓
built-response validator
    ↓
EngAInOS application authorization
    ↓
future GodotSim/runtime exact execution or refusal
    ↓
passive Godot consumer
    ↓
consume report
```

## Final vertical-slice acceptance

- [ ] Source scene identity survives the full route.
- [ ] Topologist provenance survives the full route.
- [ ] Cartographer source hashes survive the full route.
- [ ] Cartographer's metric grant survives unchanged.
- [ ] WorldField emits every cell exactly once.
- [ ] EngAInOS authorizes one complete request.
- [ ] Trixel consumes the exact authorized request.
- [ ] Trixel returns deterministic canonical geometry.
- [ ] Every returned primitive is attributable.
- [ ] EngAInOS validates the returned surface.
- [ ] EngAInOS authorizes exact placement and collision intent.
- [ ] GodotSim/runtime executes that exact physical declaration or refuses it.
- [ ] Godot displays the exact Trixel geometry.
- [ ] Godot invents no topology.
- [ ] Godot invents no metric.
- [ ] Godot invents no appearance.
- [ ] Godot creates no unauthorized collision.
- [ ] Godot returns a successful consume report.

## Upstream asset authoring — Texel Studio (committed component)

Texel Studio is a committed upstream asset-authoring component of this slice,
not an optional future investigation (user decision 2026-07-18). Snapshot:
`~/Desktop/burdens_of_a_forgotten_past/texel-studio` (no git history; dated
2026-07-02).

- Texel's only required deliverable is the completed 2D image. Whatever Texel
  does to produce that image is its own lane and is not contract-governed.
- The accepted image bytes are checksum-locked (SHA-256) and cross into Trixel
  unchanged. Texel output is untrusted producer input, pinned byte-exact like
  the canonical 3×2 fixture was.
- The existing Trixel request consumes structured grid rows, not PNG bytes.
  Decoding the pinned image bytes into the existing grid-facts representation
  is Trixel's lane — an image ingress owned by Trixel, never a conversion
  responsibility placed inside Texel.

```text
Texel
  → completed PNG bytes
  → SHA-256 lock
Trixel image ingress
  → existing grid facts
  → existing construction
  → geometry
```
- Determinism means the pinned accepted artifact bytes are stable; it does not
  require the Ollama agent to recreate the same image from the same prompt.
- Palette/masks, generator revision, and tool trace are optional provenance
  only, held outside geometry authority. Any of them becomes mandatory only if
  an existing Trixel input contract demonstrably requires it.
- Trixel handles all interpretation and constructs all geometry — never Texel.
  Texel never touches Godot.
- Local Ollama models installed (2026-07-18): `qwen3.5:9b`,
  `qwen2.5-coder:7b-instruct`, `qwen2.5:7b-instruct`, `llama3.2:latest`,
  `spindle/botforgodot:latest`. Texel's concept-art step requires Gemini and
  may be skipped; agent painting runs fully local.
- License: source-available. Generated assets are freely usable; do not host
  Texel as a competing SaaS.

### Completed Texel-to-Trixel milestones

- [x] Discover Texel's actual local invocation path (`server.py` →
      `POST /api/jobs` kind `sprite.generate`, local Ollama `qwen3.5:9b`;
      upstream `requirements.txt` omits the needed `langchain-openai`).
- [x] Generate, visually accept, and checksum-pin the 16×16 grass tile
      (SHA-256 `ab5cb28b956f418272dacb367395da958671faf7c6e096e2d5b2cf6fa4363d51`).
- [x] Add the smallest pure Trixel-side image ingress into the existing
      `pixel_field_data` representation; prove dimensions, orientation,
      byte-exact RGBA, transparency policy, and source non-mutation;
      construct and visually accept the first geometry. → trixel3.2d `e78a404`.
- [x] Add the `HEIGHT_FIELD_CONNECTED_SURFACE` stitched-slab policy: internal
      faces removed, walls only at height differences, one welded component,
      full boundary coincidence; lattice policy unchanged. Declared
      `T_JUNCTION_WALL_EDGES` limitation preserved in the builder docstring
      and `fixtures/texel/texel_connected_surface_manifest.json`; collision
      remains unauthorized for this geometry. → trixel3.2d `dfeae71`.

### Quarantined runtime attacher — read-only audit completed

- [x] Audit `godotollama trixel_proof/trixel32d_runtime/` against
      `trixel32d_surface_apply.v1` (read-only; nothing modified, executed,
      promoted, or deleted; no Godot run; no scene mutation).
- Verdict: **cannot be promoted as-is.** The attacher's only inbound
  authority is a `godot.trixel32d_surface_consume_report.v1` dictionary —
  no apply packet, no trusted authority evidence, no intent digest, no
  byte-level response binding. The attachment target is an unvalidated
  caller-supplied `Node3D`; identity-local placement makes world placement
  caller-controlled. No replacement/occupancy, visibility, lifetime,
  classification, or collision declarations exist.
- Render-only subset eligible for a future isolated apply executor: the
  five-step mutation mechanism (create `MeshInstance3D`, deterministic
  name, set transform, assign exact mesh object, `add_child`), the
  fail-closed no-node-on-reject shape, the report-vs-buffer count
  cross-check idea, and the report emission pattern. The entire authority
  head must be replaced, never promoted.
- The isolated Godot application ticket is drafted but not issued. Order of
  return: manifold payload first, then its passive-chain transport ticket,
  and only then the isolated Godot application proposal.

## Isolated Godot apply executor — COMPLETED AND ACCEPTED (2026-07-19)

The isolated Godot apply-executor ticket (issued `c073871`, consumer clause
corrected `aa6c1aa`, pre-reboot handoff `938b765`) is CLOSED. The pre-reboot
environmental blocker was confirmed as the NVIDIA driver/session mismatch:
after reboot the pre-existing lattice visual-harness test passed completely
unchanged (green pixels 41490, foreground 366×533) with no consumer,
renderer, or threshold modification.

**Implementation commit: godotollama `ea14085`** — the policy-aware
passive-consumer extension (lattice + complete-edge only; lattice branch
behavior-identical) and `trixel_proof/trixel32d_apply_executor/` complete:
executor, 12 headless tests, byte-identical checksum-locked fixtures, the
apply-executor visual harness, the accepted screenshot, and the evidence
manifest (`trixel32d_apply_executor_evidence_manifest.json`).

**Visual acceptance granted 2026-07-19** — coherent slab, correct terraces
and colors, oblique depth, complete framing, no visual fragmentation.
Locked evidence:

- Screenshot SHA-256
  `17643d5bb16f34391c32b628f08bd563eefee49ac41006088620094bd621cdc4`
  (`trixel_proof/trixel32d_apply_executor/screenshots/trixel32d_apply_executor_complete_edge.png`)
- Apply-report SHA-256
  `66bd4d45fec925d168699fa4ef9ddfae624e388fb9f79a485d2da33f27e02e71`
  (`runtime/godot_reports/GODOT_TRIXEL32D_APPLY_EXECUTOR_V1.report.json`,
  live artifact, stays uncommitted; result `APPLIED`)
- Surface `t32dsurface_cd7eee9d7877c948`; payload SHA-256
  `49396807a2d119328608b44203c0a8aae20cfe5ac0028e880676ac538bb7745b`;
  authorization SHA-256
  `5467c9c6d9e05aca564a9dbd042af62eb4893b87234c91f1d5f32b44b5fd039f`
- Target `RUNTIME_CONTAINER / container-terrain-proof / slot-surface-3x2`;
  transform origin `(2.0, 0.5, -1.0)`; `VISIBLE`; `CREATE_ONLY`;
  collision `DENIED_NONE`; scope `ISOLATED_APPLY_EXECUTOR_PROOF_ONLY`

Pre-commit re-verification: 12/12 executor tests and 10/10 lattice tests
green immediately before `ea14085`; zero references to
`trixel_proof/trixel32d_runtime/` outside the quarantine itself.

Invocation doctrine (recorded from this proof): visual harnesses hang under
plain `--headless` (dummy renderer produces no frames); the accepted
invocation is the lattice test wrapper's child-process pattern —
`--display-driver x11 --rendering-driver opengl3 --audio-driver Dummy
--position -10000,-10000 --resolution 960x720`.

Still uncommitted by explicit scope: the live EngAIn runtime artifacts
(report, authorization drop, request/response drops) per slot doctrine, and
EngAIn `executors/trixel32d_apply_authorization_export_v1.py` (proven live,
gate TRUE; awaiting its own commit decision). The modified
`trixel_proof/screenshot_trixel_profile_broad_terraces.png` in godotollama
predates this ticket, was excluded from `ea14085`, and remains untouched
awaiting disposition.

**This proof establishes isolated runtime application only.** It authorizes
no canonical-world integration, no collision (`PINCH_EDGE_NON_MANIFOLD`
remains; collision denied and untested), no persistence, no transport
changes. The quarantined runtime attacher stays untouched, unreferenced,
and uncommitted; its disposition is a separate decision now unblocked by
this accepted proof.

## Current next command

**Prior ticket COMPLETED AND ACCEPTED** (godotollama `ea14085`, evidence
hashes locked in the section above): the isolated Godot apply executor is
proven — the first authorized runtime application of Trixel-built geometry
into a live Godot scene tree. No next ticket is auto-issued. Canonical-world
integration and collision are explicitly NOT authorized by this proof; the
quarantined attacher's disposition is a separate pending decision. The
completed ticket text is retained below for provenance.

```text
Build a new isolated Godot apply executor in godotollama under
trixel_proof/trixel32d_apply_executor/. The quarantined attacher at
trixel_proof/trixel32d_runtime/ stays untouched and unreferenced. The sole
candidate surface is the accepted complete-edge payload (surface
t32dsurface_cd7eee9d7877c948, payload SHA-256
49396807a2d119328608b44203c0a8aae20cfe5ac0028e880676ac538bb7745b). Inbound
authority is exactly two checksum-locked artifacts: the intake-validated
complete-edge built response, and an EngAIn-exported apply-authorization
artifact carrying the accepted trixel32d_surface_apply.v1 packet with its
gate-TRUE result and intent digest — never a renderer-side consume report.
The executor re-verifies payload bytes before parsing. Materialize through
the existing passive-consumer lane, extended only to recognize the declared
complete-edge policy. Preserve the lattice path behavior-identically; do
not freeze the consumer file byte-identically. (Corrected 2026-07-19: the
prior "preserved passive consumer unchanged" wording was unsatisfiable —
the consumer's topology whitelist hard-rejects non-lattice payloads; a
second consumer was rejected to avoid validation drift.) The executor
mirrors the already-proven policy/declaration table, preserves all
existing lattice tests unchanged and green, validates complete-edge
canonical top/bottom/wall ordering with variable triangle counts, rejects
mixed declarations and all three-policy substitutions fail-closed, and
keeps materialization separate from application authorization. It resolves
the authorized
(parent_kind, parent_id, application_slot_id) target from a declared scene
manifest mirroring the trusted scene truth, applies the authorized
basis-column transform, honors explicit VISIBLE and CREATE_ONLY, and
refuses everything else fail-closed with no node. Collision must be
NONE/DENIED: PINCH_EDGE_NON_MANIFOLD remains and collision is denied and
untested. Proof: headless Godot tests covering acceptance plus
authority-substitution toxics — a consume-report-only input must reject —
one rendered screenshot of the applied complete-edge slab as visual
evidence, and a runtime apply report returned through the existing report
path. Quarantine disposition is decided only after this executor's proof
is accepted.
```

This ticket authorizes headless Godot execution and scene-tree attachment
for the isolated executor's proof only. It authorizes no collision, no
persistence, no canonical world mutation, no transport changes, and no
contact with the quarantined attacher.
