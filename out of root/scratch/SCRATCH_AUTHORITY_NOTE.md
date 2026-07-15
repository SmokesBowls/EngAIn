# Scratch Authority Note

SCRATCH_STATUS = PROOF_LEDGER

Meaning:
- `scratch/` is not active runtime authority.
- `scratch/` is not imported by EngAInOS during normal boot.
- `scratch/` stores proof receipts, probe fixtures, and continuation notes from gate work.
- `engainos/gates/*` writes and reads these reports.

Do not delete blindly.
Do not archive until gate report paths are intentionally migrated.

Active authority paths:
- `engainos/aproom/`
- `engainos/bridgeroom/`
- `engainos/core/`
- `engainos/gates/`
- `engainos/validators/`

Archive rule:
- Old scratch evidence may move to `/mnt/data-drive/EngAIn_Recovery/01_ARCHIVES_ORIGINAL/` only after a manifest records what reports were preserved and gate report paths are updated.
- Do not move `CONTINUE_FROM_HERE.md` until a newer continuation checkpoint exists.
