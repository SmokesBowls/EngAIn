# H03 — Visible Trixel construction proof (provisional reference stage)

OPERATION_ID: H03
SCOPE: operator-triggered PROVISIONAL TEST stage only. Not a default terrain policy; nothing runs on selection or activation.
RECEIPTS (durable): /mnt/data-drive/EngAIn_Recovery/01_ARCHIVES_ORIGINAL/H03_reference_stage_2026-11-25/ (MANIFEST.sha256)
  worldfield_grid_receipt.json        WorldField field_from_elevation_grid + emit_grid_facts: 20x20 cells, flat 0.5, grass -> default.generic, fully mapped
  cartographer_measurement_receipt.json Cartographer solve_terrain_metrics(allow_provisional=True): 100x100 m, 5.0 x 5.0 m cells, 2 layers, metric_status "provisional", validator passed
  engainos_dispatch_receipt.json      EngAInOS signed /trixel32d/build -> AUTHORIZED (bound assembly, authority composed with allow_provisional_metrics=True)
  trixel_construction_receipt.json    Trixel3.2D intake receipt + built drop envelope + geometry counts
  godot_consumption_receipt.json      godotnew apply_live report: APPLIED, collision DENIED_NONE, SCENE_BOUND to the activated load
  h03_visible_stage.png               the running godotnew project showing the constructed stage under the candidate capsules

CHANGES (EngAIn):
  - Cartographer solve_terrain_metrics(..., allow_provisional=False): a provisional basis produces a grant only when the caller passes True; grants now carry metric_status (evidence|provisional); validator checks it matches the basis.
  - EngAInOS verify_contribution_chain / assemble_bound_surface_request(..., allow_provisional=False); LiveRouteAuthority / compose_from_environment(allow_provisional_metrics=False). Composition-time only — no env var, no request field. Production launch never sets it; default composition refuses provisional grants (tested, 400, no side effects).
CHANGES (godotnew):
  - main.gd: "Construct reference stage (PROVISIONAL TEST)" button, visible only when ENGAIN_H03_BUILD_CALLER_URL is set (launched by the harness); requires an explicitly activated, presented load; applies via EngAInRuntimeLink.apply_authorization (existing grant gate).
  - tests/h03_reference_stage.py: launches the project against isolated EngAIn services (H01 Services, disposable test policy) and acts as the authorized build caller; operator mode (window) and --selftest --screenshot.

GATES:
  cartographer_measurement_receipt: TRUE
  worldfield_grid_receipt: TRUE
  engainos_dispatch_receipt: TRUE
  trixel_construction_receipt: TRUE
  godot_consumption_receipt: TRUE
  visible_constructed_surface_in_running_godot_project: TRUE (h03_visible_stage.png: 100 m cell-gridded stage under the scene's capsules)
  no_substitute_godot_plane: TRUE (geometry is Trixel's built payload, applied by apply_live)
  no_auto_construction: TRUE (operator button only)
  authorization_gates_intact: TRUE (signed activation, signed build, one-time grant, scene-revision declarations)
  mettaext_lexicon_spatial_manuscript_untouched: TRUE

FINDING (not fixed, prerequisite for "declared appearance"): the stage renders Godot-default grey, not the declared recipe colour. The donor consumer writes Trixel colours as mesh vertex colours (ARRAY_COLOR) but no material with vertex_color_use_as_albedo is attached, so they are not shown. The executor/consumer are byte-identical donor code; changing them needs your decision (patch the port, or apply a vertex-colour material in the godotnew Surfaces container).

TESTS: EngAIn tier1+tier2 822 passed, 4 pre-existing failures (3 test_snapshot_ownership; semantic donor integration HANDSHAKES §1e). godotnew H01 22/22, H02 10/10, T02 24/24, S03a 5/5, H03 selftest APPLIED with 5/5 receipts.
