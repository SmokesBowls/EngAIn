# Trixel 3.2d first elbow-to-elbow vertical slice

Authored by the user 2026-07-17; checkbox states maintained as implementations land.
The contracts and provider responsibilities are specified; this tracks the
executable connections.

## Target execution chain

- [ ] **MettaExt** produces the source scene/world facts.
- [ ] **Topologist** accepts the qualitative spatial relationships and establishes
      the provenance origin.
- [ ] **Cartographer** grants coordinates, axis declarations, horizontal scale, and
      the authorized vertical metric.
- [x] **WorldField** emits `worldfield_grid_facts.v1` containing width, height, one
      row-major record for every grid coordinate (`field_x`, `field_y`,
      `elevation`, `terrain`, `recipe`), and visible reporting of unmapped terrain
      names.
- [x] **EngAInOS** assembles, authorizes, and validates one complete
      `trixel32d_surface_request`. *(Proven on the 3×2 first-proof fixture with
      stub provenance ids; live provider wiring for the three rows above is
      pending.)*
- [ ] **EngAInOS** dispatches the validated request to Trixel 3.2d.
- [ ] **Trixel 3.2d** projects the field, applies the declared recipe and topology
      policy, and returns `trixel32d_surface_built`.
- [ ] **EngAInOS / GodotSim** authorize world placement and collision intent.
- [ ] **Godot** passively materializes the delivered geometry and writes a consume
      report.
- [ ] The consume report returns through the authorized route.

## Existing foundations

- [x] WorldField grid-facts emitter (`tier2/worldfield/grid_facts_emitter.py`)
- [x] Trixel request vocabulary (`TRIXEL_ENGAINOS_FINAL_HANDSHAKE.md` mirror +
      `docs/contracts/TRIXEL32D_SURFACE_REQUEST_CONTRACT_v1.md`)
- [x] Crew/provider ownership map (`docs/architecture/TIER2_PRODUCTION_MAP.md`,
      `docs/contracts/TRIXEL32D_REQUEST_ASSEMBLY_AND_CONSUMER_v1.md`)
- [x] WorldField-to-WorldCell coordinate projection proof (trixel3.2d,
      `worldfield_to_worldcell_projection.v1`, gate-proven)
- [x] Trixel terrain recipe registry and deterministic recipe-render proof
      (trixel3.2d `recipes/terrain/` + schema)
- [x] EngAInOS request validator (`gates/gate_trixel32d_handshake.py` —
      note: the RESPONSE validator `validate_trixel32d_surface_built` also already
      exists in the same gate file)
- [x] Historical Godot surface-generation proof
      (`~/godotollama-task-performer-main/trixel_proof/worldfield_surface_builder.gd`)
- [x] Godot consumer authority analysis
      (`docs/contracts/TRIXEL32D_REQUEST_ASSEMBLY_AND_CONSUMER_v1.md` §2)

## Missing implementations

- [x] EngAInOS `trixel32d_surface_request` assembler
      (`tier1/engainos/bridgeroom/trixel32d_request_assembler.py`, 2026-07-17 —
      fail-closed join of grid facts + metric grant + provenance + construction
      policy; deterministic content-hash request_id; self-checks against the
      validator gate; 6/6 tests incl. rejection proofs)
- [ ] EngAInOS-to-Trixel dispatch route *(recommended: clone the proven boot
      kernel ↔ Godot file-drop protocol — commands/reports dirs + strict contract
      strings)*
- [ ] Complete Trixel surface builder (trixel3.2d side)
- [ ] `trixel32d_surface_built` emitter (trixel3.2d side; EngAIn-side validator
      already exists)
- [ ] EngAInOS/GodotSim surface-application authorization
- [ ] World-placement transform declaration (v2 contract field)
- [ ] Explicit collision grant and policy (v2 contract field; GodotSim's grant)
- [ ] Passive Godot geometry consumer (~40 lines: parse → validate fail-closed →
      materialize delivered arrays → apply declared appearance/placement →
      collision only if granted)
- [ ] Godot consume-report packet
- [ ] Consume-report return route

## First proof fixture — IMPLEMENTED

`tier1/engainos/tests/test_trixel32d_request_assembler.py` sculpts a real 3×2
WorldField patch (six cells; three distinct elevations 0.45/0.50/0.85; two recipe
identities `default.generic` + `mountain.rocky_ridge`; authorized metric
cell 0.1 m / 6 height layers; topology `HEIGHT_FIELD_CELL_EXTRUSION`) and drives
it through emitter → assembler → validator gate. Collision intentionally absent
for the first presentation proof. World placement not yet declared (v2 field).

## Required acceptance gates

- [ ] MettaExt-derived source identity survives the full route. *(Survives
      assembly — `identity.source_scene_id` proven; full route pending.)*
- [ ] Topologist provenance survives the full route. *(Survives assembly; full
      route pending.)*
- [x] Cartographer's authorized metric survives assembly unchanged (test-proven);
      full-route survival pending.
- [x] WorldField emits every coordinate exactly once.
- [x] WorldField cell order is deterministic and row-major (assembler REJECTS
      violations — test-proven).
- [x] Unmapped terrain names remain visible and are never guessed (emitter
      surfaces them; assembler refuses them by name — test-proven).
- [x] EngAInOS assembles one complete authorized request (gate-validated).
- [x] EngAInOS rejects incomplete or contradictory provider data (wrong metric
      authority, missing vertical metric, undeclared recipe colors — test-proven).
- [ ] Trixel rejects malformed requests before constructing geometry.
- [ ] Trixel returns deterministic canonical geometry.
- [ ] Every returned cell has traceable geometry ownership or provenance.
- [ ] Godot displays the exact geometry delivered by Trixel.
- [ ] Godot does not invent topology.
- [ ] Godot does not invent axis mapping or scale.
- [ ] Godot does not invent terrain colors or material identity.
- [ ] Godot does not create collision without an explicit grant.
- [ ] Godot writes a successful consume report containing the consumed geometry
      counts and applied declarations.

## Design notes recorded during assembler build

- The v1 validator gate requires per-cell `base_color` RGBA. Until trixel3.2d
  recipes carry authoritative colors, colors enter as a DECLARED
  `construction_policy.recipe_base_colors` table — the assembler joins declared
  inputs and never invents a color; a recipe without a declared color is a
  REJECT. When recipes become color-authoritative, the table collapses into
  recipe data and `base_color` demotes to debug.
- Orientation vectors are doctrine constants stamped by the assembler
  (`right=[1,0,0]`, `forward=[0,0,-1]`, `up=[0,1,0]`, right-handed, Y-up,
  tolerance 1e-4) — no provider may improvise them.
- `request_id` is a sha256 content hash over the assembled body + provenance:
  same inputs, same identity — replayable and audit-friendly.
- `planar_config.center_column/center_row` are the deterministic geometric
  center `(n-1)/2`, matching the contract's 3×2 fixture.
