# MrLore Tier1 Staging Plan

Status: PLAN ONLY. No files moved, deleted, patched, imported, or staged.

Source root:
`/home/mytruelove/Downloads/obsidianburdenNov25/_mrlore`

Planned target root, only after explicit future approval:
`tier1/mrlore`

## Revision: tool archive boundary

Current `_mrlore/tools/` is production-era / legacy tooling. It must not become active Tier1 tooling by being copied.

Rules:

- `archive/old_tools/` is evidence/history only.
- `toolroom/` is not populated with old production tools.
- No old tool becomes active by being copied.
- No old tool decides canon.
- No old tool dispatches runtime.
- Surgical analysis tools are created after `tier1/mrlore` is staged.
- New production tools are created later, only after surgical proof gates.

## Authority boundary

MrLore is a Tier1 canon-memory authority candidate, but this plan does not approve the move.
The staging lane preserves proposal/review/canon separation:

- schema/contracts/raw chapter source may be staged as candidate authority surfaces;
- old tools are archive/evidence only, not active tooling;
- `toolroom/` starts empty except `SURGICAL_TOOLROOM_NOTE.md`;
- logs are archive/evidence only and are not canon;
- proofs may support review but are not canon truth;
- no MrLore path may become EngAIn runtime dispatch during staging.

## Dispatch precondition read

From `mrlore_runtime_dispatch_classification.json`:

- authority_bearing: 0
- tooling_only: 25
- evidence_export_only: 0
- stale_archival: 12
- unsafe_runtime_coupling: 0
- false_positive: 1
- MRLORE_SAFE_TO_STAGE_NO_DISPATCH = TRUE

## Exact target structure

```text
tier1/mrlore/
  schema/                 # copied from schema/; candidate doctrine/schema surface
  contracts/              # copied from exports/contracts/; candidate contract exports
  raw/
    chapters/             # copied from raw/chapters/; source witness lane
    canon_decisions/      # copied/created only if still empty or explicitly populated by approved human decisions
  evidence/
    proofs/               # evidence only; not canon truth
  archive/
    old_tools/            # optional archive/history copy of old _mrlore/tools; never active
  toolroom/
    SURGICAL_TOOLROOM_NOTE.md  # note only; no old production tools
```

## Exact directories/files to copy

Copy manifest written to:
`/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/scratch/tier_relocation/mrlore/mrlore_tier1_copy_manifest.json`

Primary planned copy entries:

1. `schema/` -> `tier1/mrlore/schema/`
   - class: Tier1 schema/contract candidate

2. `exports/contracts/` -> `tier1/mrlore/contracts/`
   - class: candidate contract exports

3. `raw/chapters/` -> `tier1/mrlore/raw/chapters/`
   - class: source witness candidate

4. `raw/canon_decisions/` -> `tier1/mrlore/raw/canon_decisions/`
   - class: human decision lane candidate; currently empty

5. `proofs/` -> `tier1/mrlore/evidence/proofs/`
   - class: evidence only; not canon truth

6. `tools/` -> `tier1/mrlore/archive/old_tools/`
   - class: legacy production-era tool archive only
   - not active tooling
   - no canon authority
   - no runtime dispatch
   - optional archive copy only if future staging gate explicitly keeps old tool history

7. create `tier1/mrlore/toolroom/SURGICAL_TOOLROOM_NOTE.md`
   - note only
   - no copied old production tools
   - surgical analysis tools come later after staging

## Exact files/directories to exclude from active toolroom / authority staging

Exclude manifest written to:
`/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/scratch/tier_relocation/mrlore/mrlore_tier1_exclude_manifest.json`

Hard excludes:

- `.venv/`
- `.cache/`
- `__pycache__/`
- `**/__pycache__/`
- `*.pyc`
- `**/*.pyc`
- `.git/`

Tool boundary excludes:

- old `tools/` must not be copied to `tier1/mrlore/tools/`
- old `tools/` must not be copied into `tier1/mrlore/toolroom/`
- old `tools/_archived/` remains archival and never active
- any old tool `.py` in `toolroom/` is forbidden by this plan

Archive/review/not-approved-for-this-stage excludes:

- `logs/`
- `cocowatch/`
- `raw/artifacts/`
- `raw/math/`
- `raw/ledgers_cache/`
- `raw/ledgers_pending/`
- `raw/editorial_feedback/`
- `raw/ledgers/`
- `raw/notes/`
- `legacy/`
- `review/`
- `stb/`
- `validation/`
- `wiki/`
- `.gitignore`
- `requirements.txt`

## Files needing import/path cleanup after move

Patch nothing in this gate.

Old production-era tool files, if archived under `tier1/mrlore/archive/old_tools/`, are review evidence only. They may be inspected for salvage, but they must not be patched into active use or imported by runtime.

Known old tool files requiring archive-only inspection if kept:

- `tier1/mrlore/archive/old_tools/write_changed_manifest.py` — legacy production-era tool archived as evidence/history only; inspect only if salvage requires it; do not make active; do not import; do not dispatch runtime
- `tier1/mrlore/archive/old_tools/mrlore_run_changed.py` — legacy production-era tool archived as evidence/history only; inspect only if salvage requires it; do not make active; do not import; do not dispatch runtime
- `tier1/mrlore/archive/old_tools/ollama_ingest_cockpit.py` — legacy production-era tool archived as evidence/history only; inspect only if salvage requires it; do not make active; do not import; do not dispatch runtime
- `tier1/mrlore/archive/old_tools/compile_entity_states.py` — legacy production-era tool archived as evidence/history only; inspect only if salvage requires it; do not make active; do not import; do not dispatch runtime
- `tier1/mrlore/archive/old_tools/chapter_ledger_extractor.py` — legacy production-era tool archived as evidence/history only; inspect only if salvage requires it; do not make active; do not import; do not dispatch runtime
- `tier1/mrlore/archive/old_tools/mrlore_rebuild_findings.py` — legacy production-era tool archived as evidence/history only; inspect only if salvage requires it; do not make active; do not import; do not dispatch runtime
- `tier1/mrlore/archive/old_tools/build_registry.py` — legacy production-era tool archived as evidence/history only; inspect only if salvage requires it; do not make active; do not import; do not dispatch runtime
- `tier1/mrlore/archive/old_tools/mrlore_session.py` — legacy production-era tool archived as evidence/history only; inspect only if salvage requires it; do not make active; do not import; do not dispatch runtime
- `tier1/mrlore/archive/old_tools/promote_candidate.py` — legacy production-era tool archived as evidence/history only; inspect only if salvage requires it; do not make active; do not import; do not dispatch runtime
- `tier1/mrlore/archive/old_tools/promotion_eligibility_gate.py` — legacy production-era tool archived as evidence/history only; inspect only if salvage requires it; do not make active; do not import; do not dispatch runtime

## Proof gates required after staging

After a future approved copy/move gate, run these proofs before any Tier1 acceptance:

1. Target existence gate:
   - prove `tier1/mrlore` exists only after explicit approval.

2. Exclude gate:
   - prove staged target contains no `.venv`, `.cache`, `.git`, `__pycache__`, or `*.pyc`.

3. Old tool archive boundary gate:
   - prove no old tool exists under `tier1/mrlore/tools/`.
   - prove no old tool exists under `tier1/mrlore/toolroom/`.
   - if old tools are kept, prove they exist only under `tier1/mrlore/archive/old_tools/`.
   - prove no code imports from `tier1/mrlore/archive/old_tools/`.

4. Toolroom empty gate:
   - prove `tier1/mrlore/toolroom/` contains only `SURGICAL_TOOLROOM_NOTE.md` immediately after staging.
   - prove surgical tools are created only in a later approved gate.

5. Copy-count gate:
   - compare staged counts against `mrlore_tier1_copy_manifest.json`.

6. Dispatch gate:
   - rerun runtime dispatch scan on staged tree.
   - required: authority_bearing = 0 and unsafe_runtime_coupling = 0.

7. No EngAIn runtime import gate:
   - grep active EngAIn runtime for `tier1.mrlore`, `tier1/mrlore`, `_mrlore`, and `archive/old_tools` imports/usages.
   - required: no runtime import/use unless a later explicit contract approves it.

8. Schema/contract gate:
   - schema docs exist under `tier1/mrlore/schema/`.
   - JSON contracts under `tier1/mrlore/contracts/` pass `python3 -m json.tool`.

9. Canon separation gate:
   - logs are absent from Tier1 staging.
   - proofs, if copied, are under `evidence/proofs/` only and marked non-canon.
   - old tools are archive/history only and never accepted as canon truth.

10. Human approval gate:
   - `MRLORE_TIER1_MOVE_APPROVED` remains FALSE until a future human-approved relocation task explicitly changes it.

## Required final booleans

MRLORE_OLD_TOOLS_ACTIVE = FALSE
MRLORE_OLD_TOOLS_ARCHIVE_ONLY = TRUE
MRLORE_TOOLROOM_EMPTY_UNTIL_SURGICAL_TOOLS = TRUE
MRLORE_NEW_SURGICAL_TOOLS_AFTER_MOVE = TRUE
MRLORE_TIER1_MOVE_APPROVED = FALSE
