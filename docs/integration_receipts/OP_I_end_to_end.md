# OP_I — End-to-end verification (2026-11-25)

Test chapter: book_01_book_of_genesis/003_first_contact.md (vault obsidianburdenNov25, catalog extraction 8da065dbf77f; Pass 1 sha256 34243a13… matches its receipt). Working manuscript untouched; extraction directory not modified.
Evidence: /mnt/data-drive/EngAIn_Recovery/01_ARCHIVES_ORIGINAL/R01_op_i_e2e_2026-11-25/ (MANIFEST.sha256).

| Stage | System | Real input | Result |
|---|---|---|---|
| Explicit + spatial extraction | Mettaext Pass 1 + pass1_spatial | real chapter | 40 signals |
| Relationships + occupancy | Topologist converter + occupancy_evidence | real | 26 entities, 2 OLINK / 7 QSLINK / 6 MOVELINK; all occupancy unknown (no evidence producer) |
| Validation + lifecycle | Topologist validator + gate | real | 12/12 checks, ACCEPTED (technical only) |
| Entity layout | Cartographer | real | REJECTED: 13 unresolved constraints (relations in components disconnected from the anchor) |
| Terrain metrics | Cartographer terrain grant | real | BLOCKED: no physical measurement basis |
| Numerical field | WorldField | — | BLOCKED: no real scene elevation source |
| Request assembly + verification | EngAInOS bound assembler + handshake gate | isolated TEST_ONLY basis + test elevation grid, bound to the real activated scene id | ASSEMBLED |
| Activation | 8080 /scene/activate | real candidate (8765 /load_scene?catalog_id=) | signed, stamped, DRAFT |
| Construction | Trixel3.2D | isolated test request | BUILT, bytes re-hashed |
| Application + presentation | EngAInOS grant + godotnew apply_live | — | APPLIED, receipt godot.trixel32d_live_apply_report.v1 |

VERDICT
  Implementation completion: every operation's code path exists and is tested (OP_A–OP_H).
  Isolated integration verification: PASS (H01 22/22 against real handlers, real Trixel, real Godot; test policy + TEST_ONLY measurement basis + test elevation clearly declared).
  End-to-end on real manuscript truth: NOT PASS. The real chapter stops at Cartographer (REJECTED); terrain metrics and elevation are BLOCKED. No synthetic input was substituted into the production path.
  Production authorization: BLOCKED (all policies deny-all; decisions below).

DEFICIENCIES BY OWNING TIER (not patched elsewhere)
  - Tier 3 Mettaext / Topologist hint filter: real-chapter spatial hints are mostly non-entities ('finally', 'into', 'yards'); Topologist's technical validation accepts them. Technical validity ≠ semantic accuracy.
  - Tier 3: no producer of occupancy classification evidence.
  - Tier 2 Cartographer: multi-component topologies leave cross-component relations unresolved, so real chapters cannot reach a proposal.
  - Tier 2 WorldField / Tier 3: no manuscript-sourced elevation field for a scene.

TESTS (EngAIn full Tier 1 + Tier 2): 813 passed, 4 failed — all pre-existing (3 test_snapshot_ownership; semantic donor integration, HANDSHAKES §1e).
