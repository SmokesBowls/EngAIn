   Canonical authority map — current local checkout
    
    The key correction is that “tier” currently has three different meanings:
    
    1. Filesystem/architectural tier: tier1/, tier2/, tier3/.
    2. System jurisdiction: canon review, topology, metrics, simulation, affect, extraction, geometry, governance.
    3. Actor authority tier: runtime authorization levels 0–3.
    
    These are not interchangeable.
    
    actor_authority_tier=3 means Human Authority Root under the runtime authority model. It must not be inferred merely because a subsystem lives in tier3/ or because an older
    subsystem packet says authority_tier: 3.
    
    Evidence:
    
    - Runtime actor tiers are explicitly 0–3: tier1/engainos/aproom/authority_validator.py:16-22.
    - FINALIZED mutation requires actor Tier 3: authority_validator.py:35-43.
    - EngAInOS expects actor_authority_tier in the inbound authority envelope: tier1/engainos/aproom/authority_gate.py:23-31.
    - Some older system contracts use the same field to mean subsystem rank, for example MrLore and Mettaext:
      - docs/contracts/MRLORE_TIER1_AUTHORITY/MRLORE_TIER1_CANON_REVIEW_CONTRACT_v1.md:57-66
      - docs/contracts/METTAEXT_TIER3_EXTRACTION_MANAGEMENT/METTAEXT_TIER3_PARSE_AUTHORITY_CONTRACT_v1.md:57-66
    
    That collision is unsafe. The canonical map below treats directory tier as deployment structure and actor authority tier as runtime identity only.
    
    Executive map
    
    Authority: Human Authority Root
    Structural tier: Cross-cutting actor tier 3
    Current classification: CURRENT + AUTHORITATIVE policy; CURRENT + TRANSITIONAL general enforcement
    Actual jurisdiction: Finalized/canonical mutation permission
    ────────────────────────────────────────
    Authority: EngAInOS
    Structural tier: Tier 1
    Current classification: CURRENT + TRANSITIONAL
    Actual jurisdiction: Governance, AP, admission, declared-scene truth
    ────────────────────────────────────────
    Authority: MrLore
    Structural tier: Tier 1 directory
    Current classification: CURRENT + TRANSITIONAL
    Actual jurisdiction: Narrative/canon review and concurrence
    ────────────────────────────────────────
    Authority: Topologist
    Structural tier: Tier 2
    Current classification: CURRENT + TRANSITIONAL
    Actual jurisdiction: Qualitative, coordinate-free spatial truth
    ────────────────────────────────────────
    Authority: Cartographer
    Structural tier: Tier 2
    Current classification: CURRENT + TRANSITIONAL
    Actual jurisdiction: Metric-layout proposals
    ────────────────────────────────────────
    Authority: WorldField
    Structural tier: Tier 2
    Current classification: CURRENT + TRANSITIONAL
    Actual jurisdiction: 2D field values, terrain classification and grid facts
    ────────────────────────────────────────
    Authority: GodotSim
    Structural tier: Tier 2
    Current classification: CURRENT + AUTHORITATIVE in live simulation; CURRENT + TRANSITIONAL at EngAInOS boundary
    Actual jurisdiction: Active runtime snapshot and simulation execution
    ────────────────────────────────────────
    Authority: Engionality
    Structural tier: Tier 2
    Current classification: CURRENT + TRANSITIONAL
    Actual jurisdiction: Affect/performance/synchronization execution
    ────────────────────────────────────────
    Authority: Mettaext
    Structural tier: Tier 3
    Current classification: CURRENT + AUTHORITATIVE as evidence producer only
    Actual jurisdiction: Prose segmentation/extraction/compilation
    ────────────────────────────────────────
    Authority: Trixel 3.2d
    Structural tier: External peer; no EngAIn tier
    Current classification: CURRENT + AUTHORITATIVE for canonical local geometry
    Actual jurisdiction: Topology realization, geometry, ordering, appearance realization and provenance
    ────────────────────────────────────────
    Authority: Godot
    Structural tier: External/client lane
    Current classification: CURRENT + TRANSITIONAL presentation; not truth authority
    Actual jurisdiction: Passive materialization and proof-scoped application
    ────────────────────────────────────────
    Authority: tier2/trixel32d/
    Structural tier: None
    Current classification: PROPOSAL / NOT IMPLEMENTED
    Actual jurisdiction: No authoritative code exists there
    ────────────────────────────────────────
    Authority: Old 2D Trixel family
    Structural tier: Evicted archive/sibling
    Current classification: LEGACY / SUPERSEDED
    Actual jurisdiction: Replaced by the one-Trixel 3.2d direction
    
    1. Human Authority Root
    
    Classification
    
    - Authority policy: CURRENT + AUTHORITATIVE
    - General gateway enforcement: CURRENT + TRANSITIONAL
    
    Authoritative location
    
    - Runtime actor matrix:
      tier1/engainos/aproom/authority_validator.py
    - Concrete Trixel authority decisions:
      tier1/engainos/authority/TRIXEL32D_TICKET_A_APPLICATION_DECISIONS_V1.json
    - Trixel declared scene truth:
      tier1/engainos/authority/TRIXEL32D_SCENE_TRUTH_V1.json
    
    Tier
    
    - Actor authority tier 3.
    - This is not a filesystem tier.
    
    Jurisdiction
    
    - Finalized/canonical mutation authorization.
    - Human-root decisions can authorize a specific intent.
    - They do not transfer geometry, topology, simulation, or presentation ownership to the human actor.
    
    Entry point
    
    At the generic level:
    
    - Authority context enters through actor_authority_tier and reality_mode.
    - tier1/engainos/aproom/authority_gate.py:522-566
    
    At the current Trixel proof boundary:
    
    - Authority decisions are read by the exporter:
      executors/trixel32d_apply_authorization_export_v1.py:163-207.
    
    Output contract
    
    - engainos.trixel32d_application_decisions.v1
    - Each decision carries actor, tier, reality mode, intent digest, AP rules, persistence authorization, and collision grant:
      tier1/engainos/authority/TRIXEL32D_TICKET_A_APPLICATION_DECISIONS_V1.json:1-42.
    
    Why enforcement is transitional
    
    The general authority_gate.evaluate() still has the reality-mode integration explicitly stubbed:
    
    - tier1/engainos/aproom/authority_gate.py:548-550
    
    Consequently, the policy is authoritative, but not every generic EngAInOS route enforces the complete matrix through one canonical implementation.
    
    2. EngAInOS
    
    Classification
    
    CURRENT + TRANSITIONAL
    
    Authoritative location
    
    tier1/engainos/
    
    Tier
    
    - Structural Tier 1.
    - Runtime actor tier remains caller-specific and dynamic.
    
    Jurisdiction
    
    EngAInOS owns:
    
    - governance;
    - AP and contract decisions;
    - declared scene/entity truth;
    - subsystem-output admission;
    - application placement and collision authorization;
    - conversion into accepted runtime actions.
    
    The current doctrine states this at:
    
    - docs/contracts/ENGAINOS_TIER1_AUTHORITY/ENGAINOS_AUTHORITY_MAP.md:19-39
    
    Entry points
    
    Generic authority:
    
    - evaluate(flat_inbound_contract):
      tier1/engainos/aproom/authority_gate.py:522-566
    - HTTP facade:
      POST /api/command:
      tier1/engainos/engainos_server.py:255-307
    
    Trixel-specific authority:
    
    - Built-response validation:
      tier1/engainos/gates/gate_trixel32d_handshake.py
    - Application gate:
      tier1/engainos/gates/gate_trixel32d_surface_apply.py
    - Request assembly:
      tier1/engainos/bridgeroom/trixel32d_request_assembler.py:96
    - Request dispatch:
      tier1/engainos/bridgeroom/trixel32d_request_dispatch.py:44
    - Response intake:
      tier1/engainos/bridgeroom/trixel32d_built_drop_intake.py:103
    - Apply-authorization exporter:
      executors/trixel32d_apply_authorization_export_v1.py
    
    Output contracts
    
    Generic:
    
    - Public ENGAINOS_RUNTIME_AUTHORITY_CONTRACT_v1 projection through APDecision.to_contract_dict():
      tier1/engainos/aproom/authority_gate.py:166-190
    - Core fields are allowed, trace_id, stage, reason, errors, and, when accepted, ap_decision, optional output, and optional runtime_action.
    
    Trixel:
    
    - trixel32d_surface_request.v1
    - engainos.trixel32d_request_drop.v1
    - intake receipt for exact built bytes
    - trixel32d_surface_apply.v1
    - engainos.trixel32d_apply_authorization.v1
    
    Why transitional
    
    There are currently two authority paths:
    
    1. Tier-1 facade authority at /api/command.
    2. A more complete mutation gateway physically located inside GodotSim:
       tier2/godotsim/runtime_gateway.py.
    
    The actual port-8080 command route constructs that gateway directly:
    
    - tier2/godotsim/http_handlers.py:293-298
    
    That gateway imports EngAInOS reality/AP/canon logic:
    
    - tier2/godotsim/runtime_gateway.py:28-41
    
    This is working code, but the authority location is split. docs/architecture/TIER2_PRODUCTION_MAP.md:59-72 already identifies that as a migration target.
    
    The facade is also incomplete beyond the direct command fast path:
    
    - Only action == "command" is forwarded: engainos_server.py:281-293
    - Other authorized actions stop at CONVERSION_NOT_IMPLEMENTED: engainos_server.py:295-307
    
    3. MrLore
    
    Classification
    
    CURRENT + TRANSITIONAL
    
    Authoritative location
    
    tier1/mrlore/
    
    Tier
    
    - Structural Tier 1.
    - The current control-center fixture says authority_tier: 3, but that is old subsystem-ranking semantics, not a safe Human Root credential:
      tier1/mrlore/mrlore_control_center.py:19-24.
    
    Jurisdiction
    
    What is actually implemented:
    
    - narrative contradiction checks;
    - source-prose/layout concurrence;
    - stamping a metric-layout proposal CONCURRED without changing its coordinates.
    
    What doctrine assigns more broadly:
    
    - canon review;
    - lore continuity;
    - contradiction detection;
    - source anchoring;
    - human-review stops.
    
    The broad doctrine appears at:
    
    - docs/contracts/MRLORE_TIER1_AUTHORITY/MRLORE_TIER1_CANON_REVIEW_CONTRACT_v1.md:30-48
    
    Entry point
    
    Current executable authority slice:
    
    - verify_concurrence(...):
      tier1/mrlore/mrlore_narrative_concurrence_checker.py
    - evaluate_metric_layout_for_concurrence(...):
      tier1/mrlore/gates/gate_narrative_concurrence.py:12-53
    - Manual proof orchestration:
      tools/gameproof/run_gameproof_008.py:116-162
    
    The general mrlore_control_center is a gate-board/control-center fixture, not the complete canon-review runtime.
    
    Output contract
    
    Current implemented output:
    
    - narratively_concurred_metric_layout
    - lifecycle CONCURRED
    - source topology/layout IDs
    - contradictions
    - unresolved findings
    - unmodified embedded metric layout
    
    Evidence:
    
    - tier1/mrlore/gates/gate_narrative_concurrence.py:32-52
    
    Broad mrlore.canon_review_packet.v1:
    
    - PROPOSAL / NOT IMPLEMENTED as the general producer boundary.
    - There are validators/fixtures for it, but no broad canonical producer-to-EngAInOS flow.
    
    Why transitional
    
    The current proof stops before EngAInOS authority:
    
    - tools/gameproof/run_gameproof_008.py:211-222
    
    Therefore MrLore has a real concurrence gate, but the full path:
    
    text
    MrLore review
    → EngAInOS declared-truth acceptance
    → canonical state
    
    
    is not currently implemented.
    
    4. Topologist
    
    Classification
    
    CURRENT + TRANSITIONAL
    
    Authoritative location
    
    tier2/topologist/
    
    Tier
    
    Structural Tier 2.
    
    Jurisdiction
    
    - Qualitative, coordinate-free spatial relations.
    - Entities and QSLINK, OLINK, MOVELINK.
    - Acceptance of a validated proposed topology artifact as spatial truth.
    - It explicitly rejects render and coordinate fields.
    
    Evidence:
    
    - Coordinate/render rejection:
      tier2/topologist/gates/gate_accept_proposed_topology_artifact.py:118-124
    
    Entry point
    
    - Artifact model:
      tier2/topologist/artifactroom/topology_artifact.py
    - Validator:
      tier2/topologist/reckoningroom/topology_validator.py
    - Acceptance gate:
      evaluate_topology_artifact_for_acceptance(...):
      tier2/topologist/gates/gate_accept_proposed_topology_artifact.py:46
    - Current orchestration:
      tools/gameproof/run_gameproof_006.py:109-118
    
    Output contract
    
    accepted_spatial_truth:
    
    - source_artifact_id
    - entities
    - qslinks
    - olinks
    - movelinks
    
    Evidence:
    
    - gate_accept_proposed_topology_artifact.py:126-146
    
    Why transitional
    
    The implementation is concrete, but the current entry is a manual proof pipeline. It is not wired into a continuously running EngAInOS ingestion/admission service.
    
    5. Cartographer
    
    Classification
    
    CURRENT + TRANSITIONAL
    
    Authoritative location
    
    tier2/cartographer/
    
    Tier
    
    Structural Tier 2.
    
    Jurisdiction
    
    - Deterministic metric-layout solving from accepted qualitative spatial truth.
    - Coordinates, unit/scale, placement constraints and metric proposals.
    - It does not own topology, canon concurrence, application, or runtime acceptance.
    
    Entry point
    
    - Solver:
      build_metric_layout(accepted_spatial_truth):
      tier2/cartographer/layoutroom/topology_metric_layout_solver.py:272-284
    - Proposal gate:
      evaluate_metric_layout_for_proposal(...):
      tier2/cartographer/gates/gate_propose_metric_layout.py:12-49
    - Current orchestration:
      tools/gameproof/run_gameproof_007.py:86-141
    
    Output contract
    
    proposed_metric_layout with lifecycle PROPOSED.
    
    The gate explicitly says it still requires MrLore concurrence and EngAInOS verification:
    
    - tier2/cartographer/gates/gate_propose_metric_layout.py:30-48
    
    Why transitional
    
    Cartographer currently owns metric proposal generation, not accepted metric truth. Its own output says it is proposal-only.
    
    No implemented milestone was found that promotes:
    
    text
    narratively_concurred_metric_layout
    → EngAInOS-accepted metric grant
    
    
    That promotion remains PROPOSAL / NOT IMPLEMENTED.
    
    6. WorldField
    
    Classification
    
    CURRENT + TRANSITIONAL
    
    Authoritative location
    
    tier2/worldfield/
    
    Tier
    
    Structural Tier 2.
    
    Jurisdiction
    
    - 2D float-field state;
    - sculpt/edit operators;
    - terrain classification;
    - semantic terrain grid;
    - dense row-major grid facts for the Trixel request.
    
    The float-state owner is explicit:
    
    - tier2/worldfield/world_field_nucleus.py:1-3
    - WorldField stores chunked 2D float data:
      world_field_nucleus.py:25-45
    
    The adapter boundary says:
    
    - WorldField owns floats.
    - The semantic adapter owns classified terrain state.
    - The adapter does not own WorldField state.
    
    Evidence:
    
    - tier2/worldfield/trixel_world_adapter.py:1-12
    
    Entry points
    
    - WorldField.apply_operator(...):
      world_field_nucleus.py:47-55
    - GodotWorldFieldBridge.handle_edit(...):
      world_field_nucleus.py:123-144
    - emit_grid_facts(...):
      tier2/worldfield/grid_facts_emitter.py:79-118
    
    Output contract
    
    worldfield_grid_facts.v1:
    
    - width and height;
    - DENSE coverage;
    - row-major cells;
    - field_x, field_y, elevation, terrain, recipe;
    - unmapped terrain identities;
    - fully_mapped.
    
    Evidence:
    
    - tier2/worldfield/grid_facts_emitter.py:79-118
    
    Why transitional
    
    - Current use is through tests/proofs and Trixel request assembly.
    - The terrain-to-recipe reconciliation table is explicitly a proposal awaiting Trixel concurrence:
      grid_facts_emitter.py:32-39.
    - It is not proven as the live GodotSim runtime’s authoritative terrain state.
    
    7. GodotSim
    
    Classification
    
    CURRENT + AUTHORITATIVE inside the active simulation lane.
    
    Its EngAInOS boundary remains CURRENT + TRANSITIONAL.
    
    Authoritative location
    
    tier2/godotsim/
    
    Tier
    
    Structural Tier 2.
    
    Jurisdiction
    
    Actual current jurisdiction:
    
    - active runtime snapshot;
    - scene and entity runtime state;
    - spatial simulation;
    - perception;
    - behavior;
    - combat;
    - inventory;
    - dialogue;
    - command execution;
    - HTTP snapshot publication.
    
    The actual current state object is:
    
    - EngAInRuntime.snapshot:
      tier2/godotsim/runtime_core.py:191-204
    
    The simulation tick writes accepted kernel results back into that snapshot:
    
    - runtime_core.py:380-463
    
    Entry point
    
    text
    python3 -m tier2.godotsim.sim_runtime
    
    
    Implementation:
    
    - tier2/godotsim/sim_runtime.py:216-265
    - HTTP server: 127.0.0.1:8080
    - Server creation: sim_runtime.py:247-255
    
    Mutation admission entry:
    
    - POST /command
    - RuntimeGateway.submit(...):
      tier2/godotsim/http_handlers.py:293-298
    - Gateway contract:
      tier2/godotsim/runtime_gateway.py:1-15
    
    Output contract
    
    Actual current output is runtime HTTP JSON and snapshot state, not the aspirational SpatialSimPacket.
    
    Important outputs include:
    
    - /snapshot
    - /health
    - /command
    - command-specific JSON results
    - the normalized runtime snapshot
    
    The documented godotsim.spatial_sim_packet.v1 is PROPOSAL / NOT IMPLEMENTED as a current emitted wire contract. There were zero code hits for that contract in tier2/godotsim.
    
    Why authoritative
    
    GodotSim is the current live runtime SSOT in executable code. This is stronger evidence than the older doctrine saying it merely reports spatial evidence to EngAInOS.
    
    Why the boundary is transitional
    
    The current runtime owns and mutates its snapshot directly, while authority doctrine says EngAInOS should admit subsystem outputs. Governance code has been imported into the Tier-2
    runtime gateway rather than completely surrounding it from Tier 1.
    
    8. Engionality
    
    Classification
    
    CURRENT + TRANSITIONAL
    
    Authoritative location
    
    tier2/engionality/
    
    Tier
    
    Structural Tier 2.
    
    Jurisdiction
    
    Current code covers:
    
    - deterministic tick ordering;
    - ZON4D-like delta application;
    - snapshots and rollback;
    - generated domain views;
    - animation/audio/dialogue/camera/FX performance tasks;
    - synchronization/performance scheduling.
    
    Entry points
    
    - Runtime construction:
      build_runtime(...):
      tier2/engionality/controlroom/bootstrap.py:258
    - Tick execution:
      EnginalityRuntime.run_tick(...):
      tier2/engionality/controlroom/runtime_loop.py:186-233
    - Performance scheduling:
      runtime_loop.py:432-466
    - Control-center gate fixture:
      tier2/engionality/engionality_control_center.py
    
    Output contracts
    
    Actual current code outputs:
    
    - TickContext
    - Snapshot
    - PerformanceTask
    
    PerformanceTask fields:
    
    - id
    - tick_id
    - scene_time
    - task_type
    - payload
    - priority
    
    Evidence:
    
    - tier2/engionality/controlroom/task_types.py:17-35
    
    Declared but only partially implemented boundary:
    
    - engionality.affect_packet.v1
    
    It is present in gate validators and fixtures:
    
    - tier2/engionality/gates/gate_required_fields.py:10-14
    - tier2/engionality/engionality_control_center.py:17-22
    
    No production emitter or EngAInOS consumer path was found.
    
    Why transitional
    
    Most importantly, AP is skipped in the actual tick:
    
    - tier2/engionality/controlroom/runtime_loop.py:203-210
    
    The bootstrap AP implementation accepts everything:
    
    - tier2/engionality/controlroom/bootstrap.py:194-213
    
    The performance ABI is explicitly a logging bridge “until Godot/audio ABI is wired”:
    
    - bootstrap.py:223-230
    
    Therefore Engionality is a real subsystem, but not an admitted runtime authority lane yet.
    
    9. Mettaext
    
    Classification
    
    CURRENT + AUTHORITATIVE within its deliberately narrow jurisdiction: evidence production.
    
    It is not authoritative over canon, runtime truth, or mutation.
    
    Authoritative location
    
    tier3/mettaext/
    
    Tier
    
    Structural Tier 3.
    
    Jurisdiction
    
    - source-prose intake;
    - chapter segmentation;
    - scene-boundary proposals;
    - semantic extraction;
    - inference;
    - ZON/ZONJ construction;
    - game-scene candidates;
    - stageroom evidence manifest.
    
    Entry point
    
    Current full-pipeline runner:
    
    text
    python3 -m tier3.mettaext.pipeline_runner <chapter>
    
    
    Implementation:
    
    - tier3/mettaext/pipeline_runner.py
    
    Final evidence manifest:
    
    text
    python3 -m tier3.mettaext.stageroom_manifest ...
    
    
    Implementation:
    
    - tier3/mettaext/stageroom_manifest.py:72-96
    
    Important migration correction:
    
    - There is no tier3/mettaext/main.py.
    - Therefore the relocation document’s python3 -m tier3.mettaext launch command is LEGACY / SUPERSEDED as written:
      scratch/tier_relocation/TIER_REHOUSING_MAP.md:121-126.
    
    Output contracts
    
    Chapterroom:
    
    - engain.scene_provider_packet.v1
    - tier3/mettaext/chapterroom/CHAPTERROOM_AUTHORITY_NOTE.md:22-24
    
    Pipeline artifacts:
    
    - Pass A/B/C artifacts
    - Pass 1 text
    - Pass 2 MeTTa
    - Pass 3 ZONJ candidate
    - Pass 4 ZON/canonical ZONJ
    - Pass 5 game-scene candidate
    
    Completion output:
    
    - mettaext.stageroom_run_manifest.v1
    - authority: structured_witness
    - run_state: METTAEXT_DONE
    
    Evidence:
    
    - tier3/mettaext/stageroom_manifest.py:35-69
    
    Authority boundary
    
    Mettaext explicitly stops after writing evidence:
    
    - no EngAInOS call;
    - no MrLore call;
    - no GodotSim call;
    - no Engionality call;
    - no Trixel call.
    
    Evidence:
    
    - tier3/mettaext/stageroom/STAGEROOM_AUTHORITY_NOTE.md:121-152
    - tier3/mettaext/stageroom/STAGEROOM_HANDOFF_RULE.md:27-47
    
    The old mettaext.parse_artifact.v1 direct-to-EngAInOS boundary is PROPOSAL / NOT IMPLEMENTED. There were no code hits for that contract in tier3/mettaext.
    
    10. Trixel 3.2d — resolved
    
    Classification
    
    CURRENT + AUTHORITATIVE for canonical Trixel-local geometry.
    
    Authoritative location
    
    text
    /home/mytruelove/Desktop/burdens_of_a_forgotten_past/trixel3.2d
    
    
    Repository:
    
    text
    git@github.com:SmokesBowls/trixel3.2d.git
    
    
    Current local tracked HEAD:
    
    text
    7ef6336 [verified] feat(texel): add stone tile proof artifacts
    
    
    The local branch is seven commits ahead of origin/main. The relevant tracked sequence is:
    
    - f3cc101 canonical surface fixture
    - e78a404 Texel image ingress
    - dfeae71 connected-slab topology
    - b743c7e checksum-locked request-drop consumer
    - e455138 complete-edge connected-surface topology
    - 8af47a8 Trixel-owned WorldField→WorldCell projection
    - 7ef6336 second stone-tile proof
    
    Tier
    
    Trixel 3.2d is not an EngAIn tier1/, tier2/, or tier3/ package.
    
    Canonical tier designation:
    
    text
    External peer construction authority
    
    
    It must not be assigned actor authority tier 1, 2, or 3.
    
    Jurisdiction
    
    Trixel owns:
    
    - request validation at its construction boundary;
    - WorldField→WorldCell projection;
    - topology realization;
    - canonical local geometry;
    - deterministic ordering;
    - normals;
    - UVs;
    - colors/appearance realization;
    - per-cell geometry ranges;
    - primitive provenance;
    - local-space metadata.
    
    This boundary is explicit:
    
    - docs/contracts/TRIXEL32D_SURFACE_APPLY_CONTRACT_v1.md:91-97
    
    It does not own:
    
    - scene placement;
    - runtime parent/slot;
    - transform authorization;
    - visibility authorization;
    - replacement/lifetime;
    - collision authorization;
    - canonical persistence;
    - runtime or canon mutation.
    
    Entry points
    
    Library entry:
    
    - consume_surface_request_packet(...):
      /home/mytruelove/Desktop/burdens_of_a_forgotten_past/trixel3.2d/trixel/trixel32d_surface_consumer.py:44-55
    
    File-drop entry:
    
    - consume_request_drop(...):
      /home/mytruelove/Desktop/burdens_of_a_forgotten_past/trixel3.2d/trixel/trixel32d_request_drop_consumer.py:54-66
    
    Builder:
    
    - build_canonical_surface(...):
      /home/mytruelove/Desktop/burdens_of_a_forgotten_past/trixel3.2d/trixel/trixel32d_surface_builder.py:24-31
    
    Projection authority:
    
    - worldfield_to_worldcell_projection.v1:
      /home/mytruelove/Desktop/burdens_of_a_forgotten_past/trixel3.2d/trixel/trixel32d_worldfield_to_worldcell_projection.py:7-53
    
    Output contract
    
    trixel32d_surface_built.v1:
    
    - packet_type: trixel32d_surface_built
    - request_id
    - deterministic surface_id
    - status: BUILT | REJECTED
    - local spatial metadata
    - topology policy
    - appearance
    - geometry
    - cell geometry ranges
    - primitive provenance
    - rejected cells
    - errors
    
    Evidence:
    
    - /home/mytruelove/Desktop/burdens_of_a_forgotten_past/trixel3.2d/trixel/trixel32d_surface_emitter.py:7-66
    
    Transport wrapper:
    
    - engainos.trixel32d_built_drop.v1
    - Exact response bytes plus SHA-256 identity:
      trixel32d_request_drop_consumer.py:174-202
    
    The specific tier2/trixel32d/ resolution
    
    Classification:
    
    PROPOSAL / NOT IMPLEMENTED
    
    Evidence:
    
    - tier2/trixel32d is absent from the current Git tree.
    - git log --all -- tier2/trixel32d returned no history.
    - No current code imports tier2.trixel32d.
    - The original tier migration did not move Trixel there. It explicitly said no tier slot had been defined:
      scratch/tier_relocation/TIER_REHOUSING_MAP.md:103-109.
    - Current EngAIn HEAD tracks:
      - tier1/mrlore
      - tier1/engainos
      - tier2/godotsim
      - tier2/engionality
      - tier2/topologist
      - tier2/cartographer
      - tier2/worldfield
      - tier3/mettaext
    - It does not track tier2/trixel32d.
    
    So the prior assumption that tier2/trixel32d/ existed should be retired. It appears to have been an inferred destination, not a completed migration.
    
    The older Trixel paths
    
    Classification:
    
    LEGACY / SUPERSEDED
    
    This includes:
    
    - old trixel/
    - trixelcomposer/
    - trixelpixel/
    - trixelmap/
    - trixelworld/
    - tier2/godotsim/trixel_composer.py
    - old four-Trixel authority doctrine
    
    The eviction record is explicit:
    
    - /home/mytruelove/Desktop/burdens_of_a_forgotten_past/trixel_legacy_2d/EVICTION_MANIFEST.md:1-20
    - The one-Trixel future and retained re-entry socket are recorded at:
      EVICTION_MANIFEST.md:25-31
    
    The intermediate CURRENT_REHOUSING_MAP.md statement that ../trixel/ was an externalized Tier-1 peer is now LEGACY / SUPERSEDED:
    
    - manifests/relocation_proof/CURRENT_REHOUSING_MAP.md:28-44
    
    It predates the explicit July 16 eviction and the Trixel 3.2d construction work.
    
    Trixel application status
    
    The build/transport/authorization/application chain is no longer merely contract-only.
    
    Current status:
    
    - Trixel construction: CURRENT + AUTHORITATIVE
    - Checksum file-drop transport: CURRENT + AUTHORITATIVE for the proof transport
    - EngAInOS apply authorization: CURRENT + AUTHORITATIVE within Ticket A proof scope
    - Godot application executor: CURRENT + TRANSITIONAL, proof scope only
    - Canonical-world integration: PROPOSAL / NOT IMPLEMENTED
    - Collision: PROPOSAL / NOT IMPLEMENTED and explicitly denied
    
    The isolated Godot executor is at:
    
    text
    /mnt/data-drive/godotollama/trixel_proof/trixel32d_apply_executor/godot/trixel32d_apply_executor.gd
    
    
    It consumes exact EngAInOS authorization and emits:
    
    - godot.trixel32d_apply_report.v1
    - APPLIED | REJECTED
    - exact IDs and SHA-256 locks
    - target
    - transform applied
    - node name/class
    - collision result
    - godot_runtime_scope: ISOLATED_APPLY_EXECUTOR_PROOF_ONLY
    
    Evidence:
    
    - Executor authority input: trixel32d_apply_executor.gd:3-20
    - Materialization/application: trixel32d_apply_executor.gd:153-181
    - Report shape: trixel32d_apply_executor.gd:184-204
    
    The proof manifest explicitly disclaims canonical integration, persistence and collision:
    
    - /mnt/data-drive/godotollama/trixel_proof/trixel32d_apply_executor/trixel32d_apply_executor_evidence_manifest.json:33-38
    
    11. Godot
    
    Classification
    
    CURRENT + TRANSITIONAL presentation/application client.
    
    It is not a state-truth authority.
    
    Authoritative location for the current Trixel proof
    
    text
    /mnt/data-drive/godotollama/trixel_proof/trixel32d_apply_executor/
    
    
    Jurisdiction
    
    - Materialize already-authorized geometry.
    - Attach a presentation-only MeshInstance3D under the exact declared parent.
    - Apply exact authorized transform and visibility.
    - Report what happened.
    
    Godot may not decide:
    
    - topology;
    - geometry;
    - target;
    - transform;
    - collision;
    - lifetime;
    - replacement;
    - persistence;
    - canon.
    
    Evidence:
    
    - docs/contracts/TRIXEL32D_SURFACE_APPLY_CONTRACT_v1.md:99-113
    
    Output contract
    
    godot.trixel32d_apply_report.v1, proof-scoped.
    
    It does not become authority merely because rendering succeeded.
    
    Superseded and non-implemented declarations
    
    LEGACY / SUPERSEDED
    
    - Old root-level Trixel family and four-Trixel authority doctrine.
    - ../trixel/ as the current Trixel authority location.
    - python3 -m tier3.mettaext as a valid entry point; no main.py exists.
    - Any interpretation of filesystem tier as actor mutation tier.
    - Old Trixel application docs saying transport and apply execution do not exist; code and committed proofs now exist.
    - Generic godotsim.spatial_sim_packet.v1 as the actual live GodotSim output.
    - Generic mettaext.parse_artifact.v1 as the actual Mettaext handoff.
    
    PROPOSAL / NOT IMPLEMENTED
    
    - tier2/trixel32d/
    - Broad MrLore CanonReviewPacket production and promotion into EngAInOS declared truth.
    - EngAInOS acceptance of Cartographer’s narratively concurred metrics.
    - Continuous Topologist→Cartographer→MrLore→EngAInOS orchestration.
    - Production Engionality→EngAInOS AffectPacket flow.
    - Generic GodotSim→EngAInOS SpatialSimPacket flow.
    - Production/canonical Trixel scene application.
    - Trixel collision generation or admission.
    - Canonical persistence of applied Trixel surfaces.
    
    UNKNOWN
    
    - The final replacement for the missing frozen AUTHORITY_TIER_SPEC_v1.md. The path referenced by project guidance does not exist in the current checkout; only executable fragments
    such as authority_validator.py remain.
    - Whether the untracked doctrine files in the external Trixel checkout are intended to become normative. They were not used as current authority.
    - The eventual production transport mechanism for Trixel beyond the currently proven checksum-locked file-drop.
    - The eventual canonical persistence owner for applied surfaces.
    - Whether MrLore’s old authority_tier: 3 packet field will be renamed before any general EngAInOS integration. It must not be treated as Human Root authority in its current
    ambiguous form.
    - Whether Mettaext’s old authority_tier: 3 proposal will be similarly corrected.
    
    Canonical chain right now
    
    The honest current chain is:
    
    text
    Source prose
      → Mettaext
          evidence/candidates only
      → Topologist
          accepted qualitative spatial truth, manually orchestrated
      → Cartographer
          proposed metric layout
      → MrLore
          narratively concurred layout
      → [missing generalized EngAInOS promotion stage]
    
    
    The working Trixel-specific chain is further advanced:
    
    text
    WorldField/grid facts
    + Cartographer-style metric grant
    + provenance
    + EngAInOS construction policy
      → EngAInOS trixel32d_surface_request
      → checksum-locked request drop
      → external Trixel 3.2d
      → trixel32d_surface_built.v1
      → checksum-locked built drop
      → EngAInOS exact-byte validation
      → EngAInOS apply authorization
      → isolated passive Godot apply executor
      → godot.trixel32d_apply_report.v1
    
    
    That chain is real but proof-scoped. It does not establish canonical-world integration.
    
    Repository-state qualification
    
    - EngAIn primary checkout: clean at 7120f16.
    - External Trixel checkout: local tracked HEAD 7ef6336, seven commits ahead of origin/main; it also contains an existing modified TODO.md and untracked documentation/archive
    material. Those uncommitted files were not treated as canonical.
    - Godot apply-proof repository: local branch one commit ahead of origin, with an existing modified screenshot. The committed executor and proof files were used as evidence.
    - No files were changed.
    - No project code or tests were run; this was a read-only static and Git-history authority audit.
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

────────────────────────────────────────
● [ASYNC DELEGATION BATCH COMPLETE — deleg_278b24ff]
A background fan-out of 3 subagent(s) you dispatched earlier has finished. All ran in parallel and waited on each other; their consolidated results are below. You may have moved on since 
dispatching — act on these or re-dispatch if things have changed.
... (+82 more lines)
─────────────────────────────────────
Full live transcript (complete tool/assistant trace): /home/mytruelove/.hermes/cache/delegation/live/deleg_278b24ff/task-2.log
────────────────────────────────────────

  ┊ 📖 read      subagent-summary-0-20260830_084510_947773.txt  0.1s
  ┊ 📖 read      subagent-summary-1-20260830_084510_956352.txt  0.1s
  ┊ 📖 read      subagent-summary-2-20260830_084510_959104.txt  0.1s
  ┊ 📖 read      gate_server_entrypoint_repair_lane.py L232-381  0.1s
  ┊ 📖 read      gate_server_entrypoint_repair_lane.py L340-429  0.1s
  ┊ 📖 read      safe_runtime_server_entrypoint.py L190-259  0.1s
  ┊ 📖 read      mrlore_review_rail_health_runner.py  0.1s
  ┊ 📖 read      MRLORE_LONG_TERM_CONTINUATION_MEMO.md L20-119  0.1s
  ┊ 📖 read      mrlore_scene_intake_runner.py L80-179  0.1s

╭─ ⚕ Hermes ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
    The completed subagent cross-check corroborates the Trixel resolution, but it exposes one material correction and several sharper classifications to my previous map.
    
    Correction: GodotSim’s codebase is current, but its existing port-8080 server is not an approved current runtime entrypoint.
    
    1. GodotSim correction
    
    Replace my earlier broad statement:
    
    > “GodotSim is the current live runtime SSOT.”
    
    with the more precise map:
    
    - GodotSim location and simulation jurisdiction: CURRENT + AUTHORITATIVE
    - EngAInRuntime.snapshot as the implemented simulation state container: CURRENT + TRANSITIONAL
    - sim_runtime.py/RuntimeHTTPHandler as the approved port-8080 server: LEGACY / SUPERSEDED
    - Safe replacement server: PROPOSAL / NOT IMPLEMENTED
    - godotsim.spatial_sim_packet.v1 producer: PROPOSAL / NOT IMPLEMENTED
    
    Tier-1 blocker law explicitly says the old server is unsafe because only /command passes through RuntimeGateway, while scene, vault, and world routes can mutate directly:
    
    - tier1/engainos/gates/gate_server_entrypoint_repair_lane.py:242-260
    
    The authoritative repair gate requires port 8080 to remain closed:
    
    - gate_server_entrypoint_repair_lane.py:336-345
    
    It says no safe server entrypoint has been identified:
    
    - gate_server_entrypoint_repair_lane.py:348-366
    
    Its final authority output is unambiguous:
    
    - SERVER_RUNTIME_LANE = BLOCKED
    - PORT_8080_ALLOWED = False
    - SAFE_SERVER_ENTRYPOINT_IDENTIFIED = False
    
    Evidence:
    
    - gate_server_entrypoint_repair_lane.py:387-410
    
    The proposed replacement is still scaffold-only:
    
    - tier1/engainos/server/safe_runtime_server_entrypoint.py:198-208
    
    Therefore the canonical GodotSim entry-point row should now be:
    
    | Field                           | Canonical result                                                                 |
    |---------------------------------|----------------------------------------------------------------------------------|
    | Location                        | tier2/godotsim/                                                                  |
    | Structural tier                 | Tier 2                                                                           |
    | Jurisdiction                    | Simulation execution and snapshot production                                     |
    | Current implementation entry    | EngAInRuntime and RuntimeGateway; usable as code, not approved as the old server |
    | Approved network entry          | None                                                                             |
    | Old sim_runtime.py server       | LEGACY / SUPERSEDED and blocked                                                  |
    | Replacement server              | PROPOSAL / NOT IMPLEMENTED                                                       |
    | Actual output                   | EngAIn protocol-envelope snapshots and command decisions                         |
    | Intended cross-authority output | godotsim.spatial_sim_packet.v1 — PROPOSAL / NOT IMPLEMENTED                      |
    
    2. MrLore refinement
    
    The earlier map correctly classified broad canon finalization as unimplemented, but it understated how much working pre-canon machinery exists.
    
    Revised dimensional classification:
    
    - Authoritative location: CURRENT + AUTHORITATIVE
    - Canon/lore review jurisdiction: CURRENT + AUTHORITATIVE
    - Pre-canon review pipeline: CURRENT + AUTHORITATIVE
    - Metric-layout concurrence slice: CURRENT + AUTHORITATIVE
    - mrlore.canon_review_packet.v1 production handoff: CURRENT + TRANSITIONAL
    - Writing/finalizing canon: PROPOSAL / NOT IMPLEMENTED
    - MrLore packet authority tier: UNKNOWN because current sources conflict
    
    The current review rail explicitly does not:
    
    - decide canon;
    - promote or reject claims;
    - resolve contradictions;
    - touch runtime;
    - compile ZONJ.
    
    Evidence:
    
    - tier1/mrlore/mrlore_review_rail_health_runner.py:3-23
    - Safety flags: mrlore_review_rail_health_runner.py:69-84
    
    Current working outputs include:
    
    - proposed claims;
    - temporal and cosmic enrichment;
    - entity-quality flags;
    - contradiction candidates;
    - temporal collision classifications;
    - review queues and review views.
    
    Evidence:
    
    - tier1/mrlore/docs/MRLORE_LONG_TERM_CONTINUATION_MEMO.md:21-78
    
    The scene-intake boundary is a real implemented contract:
    
    - engain.mrlore_scene_intake_manifest.v1
    - tier1/mrlore/mrlore_scene_intake_runner.py:141-164
    
    The unresolved tier conflict is now more explicit:
    
    - Lane instructions say MrLore packet tier 1.
    - Live gate and control-center fixture require tier 3.
    - The active contract also calls MrLore Tier 3.
    
    Therefore:
    
    text
    MrLore filesystem tier = Tier 1
    MrLore subsystem jurisdiction = canon/lore review
    MrLore actor_authority_tier = UNKNOWN / unsafe to infer
    
    
    MrLore must not be granted Human Root mutation power merely because its current fixture carries authority_tier: 3.
    
    3. Cartographer refinement
    
    Cartographer is best split as:
    
    - Metric-layout proposal authority: CURRENT + AUTHORITATIVE
    - Topologist→Cartographer integration: CURRENT + TRANSITIONAL
    - Cartographer→Trixel authorized metric grant: PROPOSAL / NOT IMPLEMENTED
    - Final accepted metric truth: outside Cartographer; requires MrLore and EngAInOS
    
    The current Trixel assembler accepts a separate hand-supplied grant containing:
    
    - cell_width
    - cell_depth
    - max_height_layers
    - vertical measurement rule
    - granted_by = cartographer
    
    Evidence:
    
    - tier1/engainos/bridgeroom/trixel32d_request_assembler.py:169-185
    
    But current tests hand-write that grant:
    
    - tier1/engainos/tests/test_trixel32d_request_assembler.py:27-41
    
    Cartographer’s actual artifact is an entity-position metric layout, not that Trixel surface-metric grant.
    
    Thus the direct Cartographer→Trixel metric authority seam is not yet implemented.
    
    4. Topologist refinement
    
    Topologist is similarly dimensional:
    
    - Qualitative topology artifact authority: CURRENT + AUTHORITATIVE
    - Internal PROPOSED → ACCEPTED topology gate: CURRENT + AUTHORITATIVE
    - Mettaext→Topologist file seam: CURRENT + TRANSITIONAL
    - Topologist→Cartographer handoff: CURRENT + TRANSITIONAL
    - Live Topologist provenance in Trixel requests: PROPOSAL / NOT IMPLEMENTED
    
    The Trixel assembler presently accepts a supplied topology_artifact_id, but the current proof uses a fixture ID rather than a live Topologist artifact:
    
    - tier1/engainos/bridgeroom/trixel32d_request_assembler.py:187-193
    - tier1/engainos/tests/test_trixel32d_request_assembler.py:37-41
    
    5. Mettaext refinement
    
    The subagent confirms the previous result:
    
    - Location: CURRENT + AUTHORITATIVE
    - Evidence-production jurisdiction: CURRENT + AUTHORITATIVE
    - Current full entry: tier3.mettaext.pipeline_runner
    - python3 -m tier3.mettaext: LEGACY / SUPERSEDED
    - master_pipeline.py: LEGACY / SUPERSEDED
    - run1time.py: LEGACY / SUPERSEDED
    - mettaext.stageroom_run_manifest.v1: CURRENT + AUTHORITATIVE
    - engain.scene_provider_packet.v1: CURRENT + AUTHORITATIVE
    - mettaext.parse_artifact.v1: PROPOSAL / NOT IMPLEMENTED
    - Automatic consumption of mettaext_done_manifest.json: PROPOSAL / NOT IMPLEMENTED
    
    The currently working Mettaext→Topologist seam is more concrete than the general stageroom handoff:
    
    - Mettaext emits out_pass1_spatial_*.
    - Topologist consumes it through passroom_signal_converter.
    - Game Proof #005 directly connects those APIs.
    
    6. Engionality confirmation
    
    No change to the previous overall result:
    
    - Location/jurisdiction: CURRENT + AUTHORITATIVE
    - Runtime and performance machinery: CURRENT + TRANSITIONAL
    - Affect-packet validators: CURRENT + AUTHORITATIVE as validation rails
    - Live engionality.affect_packet.v1 producer: PROPOSAL / NOT IMPLEMENTED
    - Production EngAInOS consumer: PROPOSAL / NOT IMPLEMENTED
    - Real AP enforcement: PROPOSAL / NOT IMPLEMENTED
    
    Current run_tick() still skips the AP/conflict stages and accepts every ordered delta:
    
    - tier2/engionality/controlroom/runtime_loop.py:203-211
    
    7. Trixel confirmation
    
    The subagent independently reached the same resolution:
    
    text
    tier2/trixel32d/
        PROPOSAL / NOT IMPLEMENTED
        absent from current Git tree
        no exact-path Git history
    
    
    text
    /home/mytruelove/Desktop/burdens_of_a_forgotten_past/trixel3.2d
        CURRENT + AUTHORITATIVE
        external peer geometry authority
    
    
    The authoritative ownership remains:
    
    - Trixel: projection, topology realization, canonical local geometry, ordering, normals, UVs, colors, cell ownership ranges and provenance.
    - EngAInOS: request assembly, validation, admission, target, transform, visibility, replacement, lifetime and collision authorization.
    - Godot: proof-scoped passive materialization.
    - GodotSim: future physical admission/execution, but no currently approved server route.
    - Canonical persistence: PROPOSAL / NOT IMPLEMENTED.
    
    Final corrected top-level map
    
    | System               | Location/jurisdiction                                       | Current execution/integration                                      |
    |----------------------|-------------------------------------------------------------|--------------------------------------------------------------------|
    | Human Root           | CURRENT + AUTHORITATIVE                                     | CURRENT + TRANSITIONAL enforcement                                 |
    | EngAInOS             | CURRENT + AUTHORITATIVE jurisdiction                        | CURRENT + TRANSITIONAL implementation                              |
    | MrLore               | CURRENT + AUTHORITATIVE review authority                    | CURRENT + TRANSITIONAL handoff; canon write not implemented        |
    | Topologist           | CURRENT + AUTHORITATIVE qualitative topology                | CURRENT + TRANSITIONAL integration                                 |
    | Cartographer         | CURRENT + AUTHORITATIVE metric proposals                    | CURRENT + TRANSITIONAL integration                                 |
    | WorldField           | CURRENT + AUTHORITATIVE field/grid facts                    | CURRENT + TRANSITIONAL integration                                 |
    | GodotSim             | CURRENT + AUTHORITATIVE simulation code                     | Existing server LEGACY / SUPERSEDED; replacement not implemented   |
    | Engionality          | CURRENT + AUTHORITATIVE synchronization/affect jurisdiction | CURRENT + TRANSITIONAL runtime; production handoff not implemented |
    | Mettaext             | CURRENT + AUTHORITATIVE evidence production                 | Automatic authority consumption not implemented                    |
    | Trixel 3.2d          | CURRENT + AUTHORITATIVE external geometry authority         | CURRENT + TRANSITIONAL proof seam                                  |
    | Godot                | Presentation only                                           | CURRENT + TRANSITIONAL proof executor                              |
    | tier2/trixel32d      | None                                                        | PROPOSAL / NOT IMPLEMENTED                                         |
    | Old 2D Trixel family | Evicted/archive                                             | LEGACY / SUPERSEDED                                                |
    
    The key correction is therefore not to demote GodotSim’s simulation jurisdiction, but to distinguish that jurisdiction from its blocked legacy server entrypoint. No files were
    changed.
╰────────────
