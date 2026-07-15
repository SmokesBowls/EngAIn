# EngAIn Tier Rehousing Map

## Tier structure

```
tier1/  — Authority layer (canon, governance, AP rules)
tier2/  — Simulation runtime layer
tier3/  — Narrative pipeline layer
```

---

## Confirmed moves (complete)

| System | Old path | New path | Import sweep | Notes |
|---|---|---|---|---|
| mrlore | `mrlore/` | `tier1/mrlore/` | Done | tier1.mrlore.* |
| engainos | `godotengain/engainos/` | `tier1/engainos/` | Done | tier1.engainos.* |
| mettaext | `mettaext/` | `tier3/mettaext/` | Done | tier3.mettaext.* |
| godotsim | `godotsim/` | `tier2/godotsim/` | Done | tier2.godotsim.* |

All four systems are importable from repo root with `PYTHONPATH=.` set.

---

## Known pre-existing issues (not caused by the moves)

These were broken before rehousing and remain broken:

| File | Issue |
|---|---|
| `tier1/engainos/engainos_server.py` | Bare imports: `from runtime_client import NGATRTClient`, `from core.authority_gate import evaluate` — only works if run from inside the old engainos dir |
| `tier1/engainos/gates/gate_ap_default_rules_registered.py` | References `tier1.engainos.core.ap_engine` — file is at `aproom/ap_engine.py`, not `core/` |
| `tier1/engainos/gates/gate_ap_zw_engine_timeline_fence.py` | Same: `tier1.engainos.core.ap_zw_engine` — actually in `aproom/` |
| `tier2/godotsim/runtime_core.py` | `ROOT_DIR` is computed as one level up from file — resolves to `tier2/` instead of repo root. Affects asset path lookups at runtime. |

---

## Root-level systems still to assess

### Tier assignment pending

| System | Current path | Recommended tier | External deps | Effort |
|---|---|---|---|---|
| `engain/` | root | tier3 | `tier2.godotsim`, `tier3.mettaext` (already correct) | Low — already partially updated; mostly facade package |
| `facade/` | root | tier1 | `engain_control` only | Low — pure gate system, zero external imports |
| `ENGIONALITY/` | root | tier2 | `engain_control` only | Low — self-contained animation/performance engine |
| `engain_control/` | root | **stay at root** | stdlib only | Zero — imported by everything; moving would cascade |

### Art / tooling tier (no tier defined yet)

| System | Current path | Notes |
|---|---|---|
| `trixelcomposer/` | root | Self-contained FastAPI art server; bare imports (internal only); LibreSprite vendored tree |
| `trixelpixel/` | root | Minimal external deps; ZW bridge script |
| `trixelmap/` | root | Not yet scanned |
| `trixelworld/` | root | Self-contained brush/engine pipeline; all bare imports are internal |
| `mechanimation/` | root | 41 external-ish imports — scan before moving |
| `blender/` | root | 42 external-ish imports — Blender-specific; probably stays near root or blender_scripts/ |
| `terrain/` | root | 28 external-ish imports — scan before moving |

### Heavy / complex — scan before deciding

| System | Current path | Notes |
|---|---|---|
| `trae/` | root | 361 external-ish imports — complex; needs full dependency scan before tier assignment |

### Leave at root permanently

| System | Reason |
|---|---|
| `engain_control/` | Shared utility (`gate_print`, `gate_result`) imported by mrlore, engainos, facade, ENGIONALITY, godotsim. Moving it would require updating every gate file across all tiers. Zero benefit. |
| `gui/` | Standalone ZW GUI; already imports `tier1.engainos.core.zw.zw_parser` correctly |
| `tools/` | Shell scripts; not Python packages |
| `docs/` | Documentation |
| `assets/` | Generated/binary; not packages |
| `manifests/` | Project manifests |
| `archive/` | Historical preservation |
| `scratch/` | Working notes |

---

## Recommended next move order

### 1. `facade/` → tier1/facade (easiest)

- Zero external deps beyond `engain_control` (which stays at root)
- Already uses `facade.gates.*` internally (clean package)
- Import sweep: update `facade.` → `tier1.facade.` in callers

Callers to update:
- `engain_control/engain_master_control_center.py` — string ref `"facade.facade_control_center"`

### 2. `ENGIONALITY/` → tier2/engionality (easy)

- Zero external deps beyond `engain_control`
- Already uses `ENGIONALITY.gates.*` internally
- Import sweep: update `ENGIONALITY.` → `tier2.engionality.` in callers

Callers to update:
- `engain_control/engain_master_control_center.py` — string ref `"ENGIONALITY.engionality_control_center"`

### 3. Trixel family — define tier4 first

No tier slot exists. Decide:
- Create `tier4/` for creative/tooling systems, OR
- Keep trixel family at root as standalone tool servers

The trixel family is internally self-contained. No tier1/2/3 system imports from it. Lowest urgency.

### 4. `trae/` — investigate before committing

361 import stems. Could be an active client or a legacy artifact. Scan fully before deciding tier.

---

## Import path reference (current)

| Package | Import prefix | Launch command |
|---|---|---|
| mrlore | `tier1.mrlore` | `python3 -m tier1.mrlore.mrlore_control_center` |
| engainos | `tier1.engainos` | `cd repo && python3 tier1/engainos/launch_engine.py` |
| mettaext | `tier3.mettaext` | `METTAEXT_NO_DISPATCH=true python3 -m tier3.mettaext` |
| godotsim | `tier2.godotsim` | `cd repo && python3 -m tier2.godotsim.sim_runtime` |

`PYTHONPATH` must include repo root (`.`) for all tier imports to resolve.

---

## AGENTS.md status

AGENTS.md still contains old paths for the moved systems. Key stale references:
- `godotsim/` → now `tier2/godotsim/`
- `godotengain/engainos/` → now `tier1/engainos/`
- `mettaext/` → now `tier3/mettaext/`
- Launch commands use old `cd godotsim && python3 sim_runtime.py` pattern

AGENTS.md has been updated to correct Active Systems paths and verification commands.
Last updated: 2026-06-24
