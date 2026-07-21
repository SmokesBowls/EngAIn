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
(report, authorization drop, request/response drops) per slot doctrine.
The apply-authorization exporter
`executors/trixel32d_apply_authorization_export_v1.py` is committed with
five focused proofs (EngAIn `4e0d1bb`): deterministic bytes reproducing the
accepted artifact SHA-256 exactly, emission only after the unchanged apply
gate returns TRUE, gate-level rejection of unaccepted validations, and
fail-closed refusal (gate refusal or occupied slot) with no partial output.
The modified
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

**Turntable ticket COMPLETED AND ACCEPTED** (issued `0b5d898`, implemented
godotollama `88ecf6c`, visual acceptance 2026-07-19). The unmodified
isolated apply executor applied the accepted complete-edge surface exactly
once; only the diagnostic camera orbited (eight azimuths, fixed 27°
elevation, one fixed orthographic projection). Per-view invariants held at
every capture: surface identity, 3700/5754 counts, identical mesh instance
object, declared target tuple, authorized transform, authorization intent
digest, collision DENIED_NONE. Accepted evidence: manifest SHA-256
`3c3d127f57a4fa61c321f372911327ef463b7a44bb8e9b6fa091630899168da1`
(locks all eight frame hashes), contact sheet SHA-256
`bcf5f95cd0f695061ee705e1c94587dfedf50b6d75f75842b39b59a0c13f8e6c`.
Frames, contact sheet, and pre-acceptance manifest were byte-identical
across three independent harness runs — the render lane is deterministic.
The accepted application screenshot (`17643d5b…`) was verified
byte-identical before and after every run. Boundaries unchanged:
canonical-world integration and collision remain NOT authorized; the
quarantined attacher's disposition is a separate pending decision.

**Blender diagnostic COMPLETED AND ACCEPTED** (ticket issued EngAIn
`96c0370`, implemented godotollama
`4679ed4bd8ffbf807612dcb6cca456a14e155049`, visual acceptance
2026-07-19). Blender consumed the raw checksum-locked complete-edge payload
(`49396807a2d119328608b44203c0a8aae20cfe5ac0028e880676ac538bb7745b`)
directly and retained genuine triangulated geometry with complete wall edges;
the beauty render coherently matches the accepted Godot slab's silhouette,
terraces, cavities, and colors, while the wireframe visibly proves the mesh
is not a smoothed, subdivided, or disguised flat image.

Accepted artifact SHA-256 locks:

- `.blend`: `aa783451ad0a0dd4f25333329593b20d5e620b9a5c515507891ce9d45998efa3`
- beauty render: `d0bdb965f2212392310a24ca8474ce6b1fbc201b3a5930c79197a5dc9d5aae36`
- wireframe render: `c2a8cc02c2af49a1117a2d400a6bcd6a5bfbf2d9467b9136a9e339d23ed7a956`
- diagnostic report: `c073f6ac5a35da1a68a8a6defcb3db3708dee3797c1b45f0886f1c36dfac6076`
- accepted evidence manifest: `593e22795c445754d55b144b14ea6d3daa6a187e1eb6b5b676c1f32128a17383`

The accepted manifest records `visual_acceptance: "accepted 2026-07-19"`.
Standard is the diagnostic display transform only; numeric payload color
verification remains the color-identity authority. The ten focused tests
passed with zero failures immediately before the implementation commit, and
an independent staged-scope review passed. The accepted artifacts are closed
evidence and must not be regenerated or replaced by a presentation-only
revision. Boundaries remain unchanged: Blender is diagnostic only; no
collision-readiness, manifold, physics, export-authority, persistence,
transport, or canonical-world claim is authorized; Godot evidence, runtime
artifacts, quarantine, and the unrelated broad-terraces screenshot remain
untouched.

Roadmap Ticket A is issued (user decision 2026-07-19, per the approved
audit `ba11bde` §8; completed ticket texts remain in git history at
`0b5d898` and `96c0370`):

```text
Ticket A — second unrelated tile, end to end (generalization proof).

Generate one new Texel tile with a deliberately different palette and
height character; visually accept it and pin its PNG SHA-256 (stop
point 1). Ingress through the unchanged Trixel image ingress with a
declared elevation policy; build under
HEIGHT_FIELD_COMPLETE_EDGE_CONNECTED_SURFACE; lock the new payload
checksum and its own pinch inventory. Transport on fresh identity-keyed
slots through the unchanged intake. Replace the fixture-bound
apply-authorization exporter with a parametrized production exporter
(payload path, expected SHA, declared target, transform as validated
inputs; test-module imports removed) and add the first authority-owned
declared-scene-truth artifact with at least two declared unoccupied
slots; the accepted authorization artifact and every occupied slot stay
byte-untouched in place. Authorize both surfaces on distinct slots;
apply both slabs side by side in the isolated executor (distinct
origins, both CREATE_ONLY, visibly apart), one screenshot; run the
Blender diagnostic on the new payload with its expected-identity
constants parametrized, defaults preserved.

Acceptance: complete ordered substitution matrix across all four payload
identities (12 ordered substitutions) at the checksum and policy layers;
per-surface invariants on both applied slabs; every prior suite green;
all existing evidence byte-identical.

Forbidden: no adjacency/seam work, no shared borders, no collision, no
persistence, no canonical world, no quarantine contact, no slot
clearing.

Stop points: after the new tile's PNG visual acceptance; after dual-slab
evidence, before any commit.
```

This ticket authorizes local Texel generation, headless Godot and
Blender execution, and fresh identity-keyed slot dispatches for this
proof only. It authorizes no adjacency, no collision, no persistence, no
canonical world mutation, and no contact with the quarantined attacher.

## SESSION HANDOFF — Ticket A BOTH stop points reached, PAUSED for review, NOTHING COMMITTED (2026-07-20)

**READ THIS FIRST NEXT SESSION.** Ticket A's implementation is functionally
complete end to end — stop point 1 (new tile PNG acceptance) and stop
point 2 (dual-slab application evidence) are both done and were presented
for review — but **no commit has been made in any of the three repos**
(trixel3.2d, EngAIn, godotollama). Do not resume further ticket work and
do not commit anything until the user has explicitly reviewed the
dual-slab evidence and given a go-ahead; this handoff exists so a fresh
session can pick up cleanly either to await/relay that review or, once
approved, to execute the scoped multi-repo commit described below.

### What was done, by lane

**Stop point 1 — stone tile generated and accepted (2026-07-19/20).** A
second Texel tile ("stone": weathered gray rock, palette
`#7d7d78,#9a9a94,#5c5c58,#c2c2ba,#3f3f3c,#a89f8a`, generated via direct
`run_agent_stream` invocation, local Ollama `qwen3.5:9b`, no Texel server
needed) was pinned and visually accepted. Luminance spread 61.8 vs grass's
104.96 — genuinely distinct height character, not just recolored.

**Stop point 2 — dual-slab application evidence (2026-07-20).** Both
slabs applied side by side through the *unmodified* isolated Godot apply
executor, on distinct declared slots, 20 units apart (visibly separate,
no adjacency/seam work). Screenshot and full evidence set presented and
awaiting review.

**One regression was hit and fixed during this work, worth knowing about
before touching the exporter again:** the parametrized exporter initially
read scene truth from ONE shared file for both tiles. Since that file now
declares 4 targets (grass's original 3 plus stone's new slot), grass's
*regenerated* artifact stopped being byte-identical to the frozen
`5467c9c6…` lock — the existing committed regression test caught this
immediately. Fix: `build_artifact()` keeps an inline
`_HISTORICAL_GRASS_SCENE_TRUTH` constant (the exact original 3-target
scene truth) as its default, and only reads the new authority-owned
`TRIXEL32D_SCENE_TRUTH_V1.json` file when `scene_truth_path` is passed
explicitly (which the stone path always does). If you ever add a third
tile, follow the same pattern — do not point the default (grass) path at
a scene-truth file that can drift out from under it.

### Exact artifact inventory (all uncommitted; hashes for post-commit verification)

**trixel3.2d** (`git status --short` shows exactly these six new files
plus the pre-existing dirty `TODO.md`/doctrine docs, which are NOT part
of this work and must not be swept into any commit for this ticket):

- `fixtures/texel/texel_stone_tile_16x16.png` —
  `7efca9f08a39585274660d028e6de293edca914f62fc9a8795e14068d77ebca2`
- `fixtures/texel/texel_stone_tile_16x16.pin.json` —
  `45387466b90b81ad2f836a1d2d106a43635629bacd6f99ea3fcaa2eb0cfe24d6`
- `fixtures/texel/texel_stone_tile_complete_edge_surface_built_response.json`
  — `939c10c2a2de957b49c9a042b74c6e2aeac75ff03bbe037200cd35794962c7ce`
  (surface `t32dsurface_e33b7a00b15a4b68`, request
  `t32dreq_47840250a37b492f`, 3648 vertices, 5664 indices, 1888 triangles,
  31 pinch corners)
- `fixtures/texel/texel_stone_tile_complete_edge_surface_render.png` —
  `78ca79e70ea90cfa868a3c906301f97abec6983bbb710dee95b7d3300ee14182`
  (LOCKED — do not regenerate; already visually accepted)
- `fixtures/texel/texel_stone_tile_complete_edge_surface_manifest.json` —
  **post-acceptance** `774c49747110ea9c89a7205910b8cd630407367d655c64a3c11df141f0c1014b`
  (`visual_acceptance: "accepted 2026-07-20"`; the pre-acceptance
  generator-reproducible candidate was `1fc1e29db7b06d8e4aa9fbc586207e8c26cb6571c71143fe15dc501a1dc957b0`
  — the generator will always reproduce the *candidate* bytes, not the
  accepted ones, since it cannot know about acceptance; that divergence
  is correct and expected, not a bug)
- `tools/render_texel_stone_tile_complete_edge_surface_evidence.py` — the
  generator. Self-authoritative: computes and asserts its own
  welded-mesh witness before writing (no manual post-generation repair
  needed), refuses to overwrite the default `fixtures/texel/` slot if any
  of its three output files already exist there (occupation is the
  consume state), and remains freely rerunnable via
  `TEXEL_STONE_TILE_OUT_DIR=<isolated dir>` for determinism proofs only.

**EngAIn** (`git status --short`: one modified file, five new paths, plus
live `runtime/` artifacts which stay uncommitted by slot doctrine):

- `executors/trixel32d_apply_authorization_export_v1.py` (**modified**) —
  parametrized production exporter, zero test-module imports.
  `build_artifact()` with no args still reproduces the frozen grass lock
  `5467c9c6d9e05aca564a9dbd042af62eb4893b87234c91f1d5f32b44b5fd039f`
  exactly (regression-tested). New `main_stone()` function exports the
  stone authorization into its own identity-keyed slot without touching
  the module-level `EXPORT_DIR`/`ARTIFACT_PATH` globals that the original
  5 tests monkeypatch — do not merge these two code paths.
- `tier1/engainos/authority/TRIXEL32D_SCENE_TRUTH_V1.json` (**new**) —
  first authority-owned declared-scene-truth artifact. 4 declared
  targets, 2 unoccupied (`slot-surface-3x2`, `slot-surface-stone-16x16`).
- `tier1/engainos/tests/fixtures/trixel32d_request_texel_stone_complete_edge.json`
  (**new**) — `7618ea248dea825fa1cd7a188a0eb19527d45f1f009a09aa17a2dea537191808`,
  derived deterministically from Trixel's own `build_request()`, not
  hand-written.
- `tier1/engainos/tests/fixtures/trixel32d_surface_built_texel_stone_complete_edge.json`
  (**new**) — byte-identical vendored copy of the Trixel-owned payload,
  `939c10c2a2de957b49c9a042b74c6e2aeac75ff03bbe037200cd35794962c7ce`.
- `tier1/engainos/tests/test_trixel32d_ticket_a_dual_slab.py` (**new**) —
  15 tests: 3 stone-export acceptance checks plus the complete 12-case
  ordered substitution matrix across the four payload identities
  (payload_sha256 ×4, request_id ×4, topology_policy ×2 via the lattice
  fixture as the meaningful third source since grass/stone share the same
  policy string, surface_id ×2), each proven at the actual layer where
  that identity is checked (built-response validation or the apply gate's
  built-binding cross-check).
- Suite: **153/153** (138 baseline + 15 new).
- Live, uncommitted by slot doctrine: stone authorization artifact at
  `runtime/trixel32d_apply_authorizations/t32ddrop_939c10c2a2de957b/TRIXEL32D_SURFACE_APPLY_AUTHORIZATION_V1.json`
  (`0fa0472de5241fb5b09ff08a58c4dd73403b76a21de9d5d46343c1e1e7bc8f01`,
  apply_id `t32dapply_939c10c2a2de957b`, slot
  `slot-surface-stone-16x16`, origin `[22.0, 0.5, -1.0]`); stone request
  drop at `runtime/trixel32d_requests/t32ddrop_7618ea248dea825f/`; stone
  built drop + intake receipt at
  `runtime/trixel32d_built_drops/t32ddrop_939c10c2a2de957b/` and
  `runtime/trixel32d_reports/t32ddrop_939c10c2a2de957b/`. Grass's
  original slots (`t32ddrop_49396807a2d11932`, `t32ddrop_f3a1ca98d229acdc`)
  verified byte-untouched throughout — re-verify this again before
  committing if any further work happens in between.

**godotollama** (`git status --short`: two modified files — one is this
work, one is pre-existing and unrelated — plus new paths; quarantine and
`pyroclast/` untouched):

- `blender_proof/trixel32d_complete_edge/scripts/trixel32d_blender_consumer.py`
  (**modified**) — the five expected-identity constants
  (`EXPECTED_SURFACE_ID`, `EXPECTED_REQUEST_ID`, `EXPECTED_VERTEX_COUNT`,
  `EXPECTED_INDEX_COUNT`, `EXPECTED_TRIANGLE_COUNT`) are now overridable
  via `--expected-surface-id` / `--expected-request-id` /
  `--expected-vertex-count` / `--expected-index-count` /
  `--expected-triangle-count`; every default reproduces the original
  grass invocation exactly. Existing 10 tests and the committed grass
  evidence in `output/` are unchanged and were re-verified byte-identical
  after this edit.
- `trixel_proof/screenshot_trixel_profile_broad_terraces.png` (**modified,
  pre-existing, NOT this work**) — do not include in any commit for this
  ticket; its disposition is a separate, still-open decision from an
  earlier session.
- `blender_proof/trixel32d_complete_edge/fixtures/trixel32d_surface_built_texel_stone_complete_edge.json`
  (**new**) — `939c10c2a2de957b49c9a042b74c6e2aeac75ff03bbe037200cd35794962c7ce`.
- `blender_proof/trixel32d_complete_edge/output_stone/` (**new**,
  accepted evidence for the stone Blender diagnostic — presented, not yet
  separately re-confirmed by the user the way the grass Blender lane was,
  since it was shown as part of this same dual-slab presentation): beauty
  render `822893a09f096516c881be449c2d69fc411aec41ae30e67b485c57a49f8cf1cf`,
  wireframe `67b8b81c805251e065b231d0cd994c8c999ba0db40f2a9f14a71973b8f752748`,
  `.blend` `532c8eeaef58ee239f5eec382019e0e5658c8d67d840a9705b74deb2dd91f7ca`,
  report `e5ebbb7d0973a88ad3d55e1af88aa95e02031fed8cdca4aaac08e0bf83250d99`,
  manifest `fe46a4672f22bbacb00c10b3b18742fef93ded0056210fb74b4a7a7c5f151096`.
  Normal-agreement dot exactly 1.0; 3648 vertices, 1888 triangles.
- `trixel_proof/trixel32d_apply_executor/fixtures/trixel32d_apply_authorization_stone_complete_edge.json`
  (**new**) — `0fa0472de5241fb5b09ff08a58c4dd73403b76a21de9d5d46343c1e1e7bc8f01`.
- `trixel_proof/trixel32d_apply_executor/fixtures/trixel32d_surface_built_texel_stone_complete_edge.json`
  (**new**) — `939c10c2a2de957b49c9a042b74c6e2aeac75ff03bbe037200cd35794962c7ce`.
- `trixel_proof/trixel32d_apply_executor/tests/test_trixel32d_apply_executor_dual_slab.gd`
  (**new**) — 4/4 tests: stone canonical apply accepted; grass
  authorization against stone payload rejected; stone authorization
  against grass payload rejected (these two are the third,
  Godot-executor layer of the substitution matrix); distinct
  slots/apply_ids/node-names between the two applied surfaces.
- `trixel_proof/trixel32d_apply_executor/diagnostics/trixel32d_dual_slab_visual_harness.gd`
  (**new**) — the executor itself was NOT modified; this harness only
  calls it twice.
- `trixel_proof/trixel32d_apply_executor/screenshots/dual_slab/` (**new**)
  — screenshot `ad706f1f8cf789c9070668502462911e0c83bfcb99b2d8c3015dc6f7e350d457`,
  manifest `5d5911a1e0e90a75e46c310b77a0a54062b155e6d37c369faba19309e848b39d`.
  172587 foreground pixels; both slabs confirmed on distinct slots,
  distinct apply_ids, 20 units apart.
- Existing suites re-verified unchanged: apply executor 12/12, passive
  lattice 10/10. Quarantine (`trixel_proof/trixel32d_runtime/`) confirmed
  zero outside references, byte-untouched, uncommitted.

### Resume steps, in order

1. **Wait for explicit user review approval of the dual-slab evidence**
   (screenshot + full hash set above) before doing anything else. Do not
   self-approve and do not proceed to commit on the strength of the
   suites being green alone — every prior ticket in this project required
   an explicit human visual-acceptance step first, and this one is no
   different.
2. Once approved, commit in this order, each a separate scoped commit
   (do not squash across repos, matching every prior ticket in this
   project):
   a. **trixel3.2d** — the six files listed above only. Exclude
      `TODO.md` and the untracked doctrine docs (`.hermes/`,
      `3.2_trixel_doctrine.md`, `HANDSHAKE_PROTOCOL.md`, handshake notes,
      `archive/`, `dual_grid3d.md`) — none of that is this work.
   b. **EngAIn** — the exporter edit, the new authority artifact, the two
      new fixtures, and the new dual-slab test file. Exclude all
      `runtime/` paths (live artifacts stay uncommitted by slot
      doctrine, same as every prior ticket).
   c. **godotollama** — the Blender consumer edit, all new stone/dual-slab
      fixtures, tests, harness, and evidence directories. Exclude
      `trixel_proof/screenshot_trixel_profile_broad_terraces.png`
      (pre-existing, unrelated) and the quarantined
      `trixel_proof/trixel32d_runtime/` (untouched, undecided).
   d. **EngAIn docs** — a final close-out commit to this TODO file
      recording the three implementation commit hashes and marking
      Ticket A COMPLETED AND ACCEPTED, mirroring the close-out style used
      for the turntable and Blender-diagnostic tickets above.
3. Before every commit above, re-run: EngAIn `pytest tier1/engainos/tests/`
   (expect 153), Godot lattice + executor + dual-slab suites (expect
   10/10, 12/12, 4/4), Trixel `pytest` (expect 65), and re-checksum every
   hash in this handoff to confirm nothing drifted while waiting for
   review.
4. Do not touch: the quarantined attacher (disposition still separately
   pending), `broad_terraces.png` (separately pending), collision
   authorization (still denied everywhere), canonical-world placement,
   or persistence — none of that is in scope for Ticket A's closure.

### What comes after Ticket A closes (for context only — not authorized yet)

Per the approved audit (`ba11bde` §8), the next two roadmap tickets are
**B — construction-time adjacency** (a versioned request extension so two
tiles can share a seam with zero internal walls; the request contract
currently has no tile-origin or neighbor-declaration field at all — this
is real, unstarted work, not a rename) and **C — manifold repair policy**
for the locked pinch-corner inventories (a fourth topology policy;
collision stays denied throughout). Neither is issued yet. Issue Ticket B
only after Ticket A is fully committed and closed, and only on explicit
user instruction — the same discipline used for every ticket so far in
this project.

## SUPERSEDING FINAL-REVIEW GATE — authorization provenance completed (2026-07-20)

This section supersedes the earlier handoff instruction to wait for visual
review. The dual-slab screenshot was explicitly accepted by the human
reviewer with no adjacency or seamlessness claim. Ticket A is **not yet
finally approved**; it is now `PENDING_FINAL_REVIEW` with the former visual
and authorization-provenance blockers closed.

The accepted visual bytes were not regenerated or altered:

- screenshot: `trixel32d_dual_slab_complete_edge.png`
- screenshot SHA-256: `ad706f1f8cf789c9070668502462911e0c83bfcb99b2d8c3015dc6f7e350d457`
- accepted visual evidence manifest SHA-256:
  `96b338ba1f2f44d464995bedccf3b45333d8735674983e662af3b886f055fe9c`
- visual acceptance: `accepted 2026-07-20`

Both application authorizations were freshly generated through the same
parametrized production entrypoint,
`build_ticket_a_artifact(tile)`, in
`executors/trixel32d_apply_authorization_export_v1.py`:

- grass authorization SHA-256:
  `d4445c00e4e79268512a80083a88ff52dd576a62d3b6da469f7c43da25d23374`
- stone authorization SHA-256:
  `0a5e70d5673c66a219e40a4b90e38b74771c52f175cba2dfe103cacb17e066d5`

Both artifacts carry the same explicit source binding:

- scene-truth artifact:
  `tier1/engainos/authority/TRIXEL32D_SCENE_TRUTH_V1.json`
- scene-truth SHA-256:
  `95e2c827ba6c22c5949c9cee662a0f724cca530836312dca2a6430e07b2bb3c3`
- scene-truth contract: `engainos.trixel32d_scene_truth.v1`

Both also resolve distinct, preissued intent decisions from the same
EngAInOS-owned authority artifact rather than deriving trusted authority from
the packet being exported:

- authority decision artifact:
  `tier1/engainos/authority/TRIXEL32D_TICKET_A_APPLICATION_DECISIONS_V1.json`
- authority decision artifact SHA-256:
  `8c6996de0e05aab7d2d1440a4fd833d25445b0e3fbe00f19e649d4e5a4b777c9`
- grass decision: `engainos-ticket-a-grass-application-v1`
- stone decision: `engainos-ticket-a-stone-application-v1`

The exporter hashes and parses each authority input from the same captured
byte buffer, rejects substituted scene-truth paths, rejects intent/decision
mismatches, and restricts the legacy self-contained path to byte-for-byte
reproduction of the frozen historical grass authorization only.

The dual-slab Godot application proof now consumes only those two fresh
Ticket A fixtures and passes 4/4. The frozen historical grass authorization
remains byte-identical at
`5467c9c6d9e05aca564a9dbd042af62eb4893b87234c91f1d5f32b44b5fd039f`
and is not referenced by the Ticket A dual-slab application test.

The machine-readable closeout evidence is:

`trixel_proof/trixel32d_apply_executor/screenshots/dual_slab/trixel32d_dual_slab_authorization_provenance_manifest.json`

Manifest SHA-256:
`8efdcc5f854aed91ad7e0158963164eb618529a3594888f7ceb410b854267f59`

No collision, persistence, canonical-world placement, adjacency, seam, or
quarantine authority is granted by this proof.

## TICKET A CLOSEOUT — COMPLETED AND ACCEPTED (2026-07-20)

Final human review passed and explicitly approved Ticket A for the scoped
artifact-only commits below. This section supersedes the prior
`PENDING_FINAL_REVIEW` status. Ticket A is now `COMPLETED_AND_ACCEPTED` within
its bounded generalization-proof scope.

Implementation/evidence commits, in ownership order:

1. Trixel3.2d stone tile and proof artifacts:
   `7ef63361e2299142b7077c82fedba8898c962e0c`
2. EngAIn authority, exporter, fixtures, and toxic proofs:
   `8c7ff35ad1206ac1a5b80a448180056887c55e87`
3. Godot/Blender consumer proof and accepted dual-slab evidence:
   `610499af117a743cd4ce0159c6cdd7a856e49e00`

Commit-object verification reproduced the accepted locks:

- grass authorization: `d4445c00e4e79268512a80083a88ff52dd576a62d3b6da469f7c43da25d23374`
- stone authorization: `0a5e70d5673c66a219e40a4b90e38b74771c52f175cba2dfe103cacb17e066d5`
- common scene truth: `95e2c827ba6c22c5949c9cee662a0f724cca530836312dca2a6430e07b2bb3c3`
- common authority decisions: `8c6996de0e05aab7d2d1440a4fd833d25445b0e3fbe00f19e649d4e5a4b777c9`
- frozen historical grass: `5467c9c6d9e05aca564a9dbd042af62eb4893b87234c91f1d5f32b44b5fd039f`
- accepted screenshot: `ad706f1f8cf789c9070668502462911e0c83bfcb99b2d8c3015dc6f7e350d457`
- accepted visual manifest: `96b338ba1f2f44d464995bedccf3b45333d8735674983e662af3b886f055fe9c`
- authorization-provenance manifest: `8efdcc5f854aed91ad7e0158963164eb618529a3594888f7ceb410b854267f59`

Final verification was EngAIn 159/159, Trixel3.2d 65/65, Godot passive
consumer 10/10, Godot apply executor 12/12, and authority-bound dual-slab
application 4/4. Independent fail-closed review returned PASS with no security
or logic findings.

Every runtime path remained outside the EngAIn commit. Superseded untracked
authorization artifacts, the old visual-capture harness that depends on them,
pre-existing unrelated files, generated Godot import metadata, and the
quarantined runtime attacher were deliberately excluded and were not removed.

This acceptance proves only that two independently authorized, unrelated slabs
can coexist on distinct declared slots through the isolated application
executor. It grants and claims no adjacency, seamlessness, collision,
persistence, canonical-world placement, quarantine promotion, or later-roadmap
authority.
