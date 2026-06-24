# Syscheck Authority Note

SYSCHECK_STATUS = ROOT_AUDIT_LEDGER

Meaning:
- `syscheck/` is not active runtime authority.
- `syscheck/` is not an EngAInOS lane.
- `syscheck/` stores root-audit reports, import cleanup reports, rename detection, Git bucket reports, and inventory snapshots.
- These files explain cleanup history; they do not execute runtime behavior.

Do not delete blindly.
Do not use syscheck reports as live authority without re-running current proof.

Active authority/runtime paths:
- `engainos/aproom/`
- `engainos/bridgeroom/`
- `engainos/core/`
- `engainos/gates/`
- `engainos/validators/`
- `godotsim/`

Relationship to scratch:
- `scratch/` = gate proof ledger
- `syscheck/` = root audit ledger

Archive rule:
- `syscheck/` may move to `/mnt/data-drive/EngAIn_Recovery/01_ARCHIVES_ORIGINAL/` only after root cleanup is stable and a replacement audit manifest exists.
