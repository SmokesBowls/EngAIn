# EngAIn — Next Operation

## Where development stopped (2026-11-25)

Last completed: **H04b** — independent world environment viewport in godotnew (`a2c4bd4`). It opens from the chapter selector, shows only the runtime's entities for the current activation stamp, routes authorized Trixel surfaces into its own `Surfaces` node, and shows an honest empty world otherwise. No terrain exists for real scenes.

## Candidate next operations (none started)

1. **Environment source** (needs D2, and D1 for metrics): decide where a scene's environment comes from, then implement it in the owning tier (WorldField/Mettaext), not in Godot.
2. **Surface colour** (needs D9): make declared Trixel appearance visible.
3. **Production wiring** (needs D3–D6): policies, credentials in `start_stack.fish`, a build caller.
4. **Entity quality**: Topologist hint filter / runtime entity resolution / Cartographer multi-component layout.

## To resume

```bash
cd ~/Desktop/burdens_of_a_forgotten_past/EngAIn && git log --oneline -15
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tier1/engainos/tests tier2   # expect 822 pass / 4 known fails
cd /mnt/data-drive/devvm-projects/engain-chapter-selector && python3 tests/h04_world_check.py  # expect H04 PASS
```
Read in this order: this file → OPEN_BLOCKERS.md → godotnew `docs/continuity/NEXT_OPERATION.md`.
