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
`trixel32d_surface_built`, and passes the EngAIn built-response validator. The
exact built response is persisted at
`../trixel3.2d/fixtures/trixel32d_surface_built_3x2_first_proof.json` (SHA-256
`bc1951f55de00aa0114679fab1a46d80439d1b840309b0df4c9b835539dd2929`). The
separate Godot proof at `/mnt/data-drive/godotollama` commit `b05e704` consumes
those exact bytes, validates the response fail-closed, creates one in-memory
`ArrayMesh`, and emits a deterministic consume report; all 10 headless tests
pass under Godot 4.6.1. No transport, scene-tree attachment, world placement,
collision authorization, or runtime application route exists yet.

## Completed foundations

- [x] Define the direction of the handshake:
  - MettaExt and the EngAIn crew provide world facts.
  - EngAInOS assembles and authorizes the request.
  - Trixel 3.2d consumes the request and builds canonical geometry.
  - EngAInOS and GodotSim authorize runtime application.
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

- [ ] Define `trixel32d_surface_apply`.

This contract belongs between EngAInOS and GodotSim after Trixel returns
canonical geometry. It must declare:

- target scene
- surface identity
- parent/runtime location
- local-to-world transform
- visibility intent
- replacement/update behavior
- lifetime/persistence
- collision allowed or denied
- collision layer and mask
- static/dynamic/presentation-only classification

- [ ] Keep world placement outside `trixel32d_surface_built`.
- [ ] Keep collision authorization outside `trixel32d_surface_built`.
- [ ] Require GodotSim to grant physical presence explicitly.

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
EngAInOS / GodotSim apply authorization
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
- [ ] GodotSim grants placement and physics intent.
- [ ] Godot displays the exact Trixel geometry.
- [ ] Godot invents no topology.
- [ ] Godot invents no metric.
- [ ] Godot invents no appearance.
- [ ] Godot creates no unauthorized collision.
- [ ] Godot returns a successful consume report.

## Current next command

```text
Define the trixel32d_surface_apply.v1 runtime application handshake as a
contract-only EngAIn authority artifact. Specify who may authorize application,
target scene and parent identity, surface identity, local-to-world transform,
visibility, replacement/lifetime behavior, and explicit collision grant/layer/
mask/classification. Keep Trixel geometry immutable, keep Godot passive, and
fail closed when any authority-bearing field is absent. Do not wire transport,
attach the fixture to a scene tree, create collision, or mutate runtime/canonical
state in this ticket.
```

The fixture-driven presentation proof is complete in `/mnt/data-drive/godotollama`
at commit `b05e704`: 10/10 headless tests pass under Godot 4.6.1, and
`sha256sum -c SOURCE_FIXTURE.sha256` passes for the 6-cell, 144-position,
216-index response. This proof does not authorize runtime application.
