# OP_B — Complete the Topologist handoff

OPERATION_ID: OP_B
SYSTEM: Tier 2 Topologist
SCRIPT_PATH: tier2/topologist/artifactroom/{passroom_signal_converter.py (unchanged), occupancy_evidence.py (new)}; reckoningroom/topology_validator.py, gates/gate_accept_proposed_topology_artifact.py (unchanged)
FUNCTION: convert_spatial_signals_to_artifact -> apply_occupancy_evidence(artifact, records) -> TopologyValidator().validate -> evaluate_topology_artifact_for_acceptance
INPUT_ARTIFACT: pass1_spatial JSON (OP_A)
OUTPUT_ARTIFACT: accepted_spatial_truth packet (issued only by the existing gate)

GATES:
  fixture_three_entities: TRUE (guard, stone_gate, king)
  invalid_before_excluded: TRUE
  olink_and_movelink_preserved: TRUE (1 OLINK inFront, 1 MOVELINK DC->EC)
  twelve_validation_checks_pass: TRUE
  accepted_packet_from_existing_gate: TRUE (DRAFT -> PROPOSED submission -> gate; DRAFT/unvalidated is REJECTED)
  unknown_evidence_remains_unknown: TRUE (no record -> semantic_type unknown, pgt_envelope null)
  provisional_distinguishable_from_evidence: TRUE (envelope.basis = evidence|provisional; evidence needs a quote present in source_prose; provisional needs a reason)
  no_render_or_coordinate_fields: TRUE (PGT units only; policy pixel values not copied; validator's forbidden-key scan passes)

DESIGN NOTES:
  - Envelope values are PGT_SCALE_POLICY_v0.1's own numbers. Height-only classes (structures, giants) stay height-only; w/d are never invented.
  - Provenance lives inside the existing pgt_envelope field: policy_id, occupancy_class, basis, evidence_ref | provisional_reason. Cartographer reads only h/w/d.
  - DEPLINK not implemented.

FILES_CREATED: tier2/topologist/artifactroom/occupancy_evidence.py, tier2/topologist/tests/{__init__.py,test_spatial_handoff.py}
FILES_MODIFIED: none
TESTS_EXECUTED: tier2/topologist/tests (5 tests, 5 subtests)
TESTS_PASSED: 5 (+5 subtests)
TESTS_FAILED: 0
PRE_EXISTING_FAILURES: none in scope (Topologist had no tests)
DEPENDENCY_BLOCKERS:
  - Tier 3 Mettaext emits no occupancy classification evidence. Pass 5 "type": "character" does not establish a human (or any) occupancy class, so real chapters reach Cartographer with every entity unknown/no envelope. Classification records must come from a manuscript-evidence producer, which does not exist yet.
  - Real-chapter spatial hints are noisy (e.g. chapter_38: "weaving", "hundred", "glass fused"); the converter's hint filter is the existing Topologist control and was not changed.
AUTHORITY_BOUNDARY: Only the gate writes ACCEPTED. Enrichment refuses non-DRAFT artifacts.
GIT_COMMIT: (this commit)
