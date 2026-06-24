# MrLore Salvage Rule

MRLORE_IS_TIER1 = TRUE
MRLORE_CANON_MEMORY_AUTHORITY = TRUE
MRLORE_MOVE_NOW = FALSE
MRLORE_INVENTORY_FIRST = TRUE

Source found:
- `/home/mytruelove/Downloads/obsidianburdenNov25/_mrlore`

Rule:
- MrLore is not Mettaext source input.
- MrLore is not GodotSim runtime input.
- MrLore is not a general vault folder.
- MrLore must be classified before relocation.

Do not move:
- `.venv/`
- `.cache/`
- `__pycache__/`
- `*.pyc`
- generated output folders unless explicitly classified

Potential keep candidates:
- `schema/`
- `tools/`
- `exports/contracts/`
- `proofs/`
- `raw/chapters/`
- `raw/canon_decisions/`

Potential archive candidates:
- old logs
- dryrun logs
- old compile logs
- legacy imported folders

Final intended home, after classification:
- `tier1/mrlore`

No movement is accepted until salvage classification passes.
