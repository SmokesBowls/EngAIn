# EngAIn — Verified Capabilities

Only what has been run and passed. Each line names the command that proves it. Run from the EngAIn root with `PYTHONDONTWRITEBYTECODE=1`.

## Regression baseline (2026-11-25, HEAD `ca9c425c`)

`python -m pytest -q -p no:cacheprovider tier1/engainos/tests tier2` → **822 passed, 4 failed**. All 4 are pre-existing:
- `tier2/godotsim/test_snapshot_ownership.py` ×3 (fail at HEAD before any of this work)
- `tier1/engainos/tests/test_trixel32d_semantic_integration.py` (frozen donor sends no activation stamp; HANDSHAKES §1e)

A new failure beyond these four is a regression.

## Capabilities

| Capability | Proof | Result |
|---|---|---|
| Dec-2025 Mettaext reproduces its 5 anchored game scenes byte-exact (with pass1_spatial added) | anchor zip `/mnt/data-drive/EngAIn_Recovery/01_ARCHIVES_ORIGINAL/mettaext_dec2025_anchor/` re-run, see `docs/integration_receipts/OP_A_spatial_extraction.md` | 5/5 |
| Spatial signals → Topologist accepted packet (12 checks), unknown stays unknown | `tier2/topologist/tests` | 5 + 5 subtests |
| Cartographer layout never reads PGT as meters without a basis; terrain grant from declared extents; provisional only when explicitly allowed | `tier2/cartographer/tests` | 10 |
| WorldField grid facts read the same field that holds elevation; all mapped recipes exist in Trixel | `tier2/worldfield/tests` | 5 |
| Bound request assembly; asymmetric grid through real Trixel is not mirrored (right=+X, forward=−Z) | `tier1/engainos/tests/test_trixel32d_bound_assembly.py` | 10 |
| Signed `/scene/activate`: unsigned/forged/mode-claims refused, runtime mode decides, stamp enforced, snapshot reads consistent under concurrent activation | `tier2/godotsim/test_scene_activation_auth.py` | 12 |
| Live route: per-scene revision-bound declarations, provenance must name the active scene, proof grant refused, provisional refused by default | `tier1/engainos/tests/test_trixel32d_live_route.py` | 85 |
| Extract endpoint: resolver-only ids, one run at a time, receipt returned | `tier1/engainos/tests/test_chapter_extraction_route.py` | 5 |
| End-to-end with real Godot + real Trixel under isolated test policy | godotnew `tests/h01_runtime_link_check.py` | 22/22 |
| Visible Trixel surface in Godot (provisional 100×100 m test stage) | godotnew `tests/h03_reference_stage.py --selftest`; receipts + screenshot `/mnt/data-drive/EngAIn_Recovery/01_ARCHIVES_ORIGINAL/H03_reference_stage_2026-11-25/` | APPLIED, 5/5 receipts |

## Verified NOT to work (on real manuscript truth)

Real chapter `book_01_book_of_genesis/003_first_contact.md` (`docs/integration_receipts/OP_I_end_to_end.md`, evidence `/mnt/data-drive/EngAIn_Recovery/01_ARCHIVES_ORIGINAL/R01_op_i_e2e_2026-11-25/`):
40 spatial signals → topology ACCEPTED (technical) but entities are mostly non-entities → Cartographer REJECTED (13 unresolved cross-component relations). Terrain metrics and elevation BLOCKED (no source).
