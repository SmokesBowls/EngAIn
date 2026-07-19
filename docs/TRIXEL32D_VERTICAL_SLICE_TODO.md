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
height interval. No transport, world placement, runtime application route, node
attachment, or collision allocation exists yet.

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

- [ ] Clone the proven EngAIn boot file-drop pattern instead of inventing a new
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

## Current next command

```text
Resume the authority chain passively: transport the exact
HEIGHT_FIELD_CONNECTED_SURFACE built response from Trixel through a
checksum-locked file drop into EngAIn intake validation and the existing
trixel32d_surface_apply.v1 authorization gate. Clone the proven EngAIn boot
file-drop pattern; do not invent a new transport. Byte identity means SHA-256
over the raw stitched built-response file bytes carried by the drop, excluding
the transport envelope, filename, and filesystem metadata. Intake verifies
that checksum before parsing the response. Prove the complete anti-substitution
chain: raw payload checksum → parsed response identity/policy → intent-bound
surface authorization. Surface ID, request ID, intent digest, construction
policy, and payload checksum remain bound end to end; lattice and stitched
responses cannot be substituted for one another; and malformed, truncated,
stale, duplicated, or digest-mismatched drops reject fail-closed. Stale and
duplicate rejection reuse the existing boot file-drop receipt/identity
semantics; introduce no new clock, expiration system, or second receipt ledger.
Collision remains explicitly unauthorized because of the documented
T_JUNCTION_WALL_EDGES limitation. No Godot runtime execution, scene attachment,
placement, collision allocation, or world mutation. Passive transport/intake
validation and gate execution are authorized for this proof only, with no
runtime-quarantine change.
```

The passive stitched-payload transport is the next authority-boundary ticket.
It carries the real connected-surface payload from Trixel into EngAIn intake
and the committed apply-authorization gate without placing it: transport
evidence and intake validation only. Runtime application, node attachment,
collision allocation, and canonical scene mutation remain unauthorized, and
the quarantined runtime attacher in godotollama stays untouched.
