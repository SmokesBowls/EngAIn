# THE SYSTEM → ENGAINOS COMPILATION HANDSHAKE

What tier2 produces for EngAInOS, per system. (This file was originally a terminal
paste that arrived corrupted; restored 2026-07-17. Canonical full version with file
references: `docs/architecture/TIER2_PRODUCTION_MAP.md`.)

**Topologist (9 files)** — produces the qualitative spatial-truth input.
`accepted_spatial_truth` packets (entities + QSLINK/OLINK/MOVELINK) with lifecycle
states and its own acceptance gate. This is the raw material EngAInOS's canon
verification consumes, and the origin of the provenance chain.

**Cartographer (9 files)** — produces the "Authorized metrics" crew block, almost
verbatim. Engine-agnostic metric proposals: x/y/z in `world_cell_y_up`,
`unit = meter`, DRAFT→PROPOSED→REJECTED lifecycle, anchor selection, half-extents —
and it sha256-hashes source packets (`_canonical_hash`), so it also produces the
provenance discipline the trixel Identity block needs. Of the five request blocks in
TRIXEL_ENGAINOS_FINAL_HANDSHAKE.md, cartographer directly supplies Authorized
metrics, co-supplies Identity/provenance, and already declares the Coordinate
declaration pattern (axis contract, coordinate space).

**GodotSim (57 files)** — produces four different things, one of them surprising:

1. **The state being governed.** The nine `kernels/` (spatial3d, combat, inventory,
   dialogue, quest, behavior, perception, navigation, piece3d) are deterministic
   snapshot-in/snapshot-out — the runtime truth that EngAInOS's admission decisions
   are about. spatial3d_mr's bounds are already cited as coordinate authority
   downstream.
2. **A transplanted piece of EngAInOS itself.** `runtime_gateway.py` imports
   tier1.engainos.aproom.reality_mode, intent_shadow, canon.can_edit,
   authority_gate.ACTION_CLASSIFICATION, and ap_complex_rules — it is EngAInOS
   admission control, resident in tier2, checking REPLAY mode,
   FINALIZED-vs-authority, and AP rules before dispatch. This reframes the
   governance wiring gap: governance isn't missing from the live lane, it's present
   but living downstairs, routed to CommandDispatcher instead of
   authority_gate.evaluate().
3. **Construction instructions — the trixel request's fifth block, already
   prototyped.** `embodiment_contract_builder.py` emits `trixel_embodiment.v1` with
   coordinate_authority (from spatial3d), geometry_authority, and a materialization
   block containing `source: trixel_recipe`, `terrain_profile`,
   `recipe_texture_path` — the Construction-instruction /
   appearance-policy-or-recipe-reference block of the final handshake, independently
   evolved. And `godot_scene_piece_builder.py` (demand → validate →
   BUILT/REJECTED/SUSPENDED → .tscn) is a working model of what the surface_built
   consumer should look like.
4. **The evidence system.** Thirteen proof gates (visible-floor, player-movement,
   trigger-zone, recipe-pack…) — the witness layer EngAInOS acceptance leans on.

**Engionality (25 files)** — produces the enforcement substrate that makes EngAInOS
verdicts mean something. `zon4d_kernel` implements `compute_inverse_delta` +
rollback; the runtime loop tracks deltas_in → deltas_ordered → deltas_accepted /
deltas_rejected → inverse_deltas; and it declares
`preflight_delta(snapshot, delta, ms_budget) -> APVerdict`. That is the
accept/apply/reject/roll-back machinery — the mechanism by which "EngAInOS says yes"
becomes applied state and "EngAInOS says no" becomes a clean reversal. Without it,
governance is opinions; with it, it's enforceable. Plus its second lane: affect
packets (gates ready, producer unwired), the merged task system (quest/behavior
planning trees), and the showroom engines (clips/tracks — presentation timing
instructions).
