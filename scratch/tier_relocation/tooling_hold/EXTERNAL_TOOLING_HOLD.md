# External Tooling Hold

## Decision

Mechanimation and Trixel are not being moved into the EngAIn tier graph right now.

They are active / important, but their source authority is unresolved.

## Mechanimation

Current status:

- `EngAIn/mechanimation/` is tracked by EngAIn as normal files.
- It is not a submodule.
- Standalone Mechanimation exists separately at:
  `/mnt/data-drive/EngAIn_Recovery/mechanimation-main`
- Standalone Mechanimation is treated as the cleaner original-form source lineage.
- `EngAIn/mechanimation/` is treated as embedded integration/lab drift copy.

Decision:

- Do not move Mechanimation into `tier2/`.
- Do not delete either copy.
- Do not treat embedded EngAIn copy as source truth without diff/review.
- Mechanimation may remain standalone third-party/art-pipeline tooling.
- EngAIn should consume exported artifacts/packages later, not necessarily source-own the tool.

## Trixel

Current status:

- Trixel is a parallel class authority system, not an EngAIn tier.
- EngAIn should talk only to Trixel Class1.
- Trixel Class1/conductor decides which internal class handles work.
- Class1 conductor is unresolved.
- Terminal Trixel lineage has multiple evolutions.

Observed lineage:

- Standalone `terminal_trixel.py` = original autonomous terminal pixel artist / composer seed.
- EngAIn `terminal_trixel.py` = evolved integration version with recipe rendering, transforms, entity sidecar, replay, and artifact output.
- Both look like Class2 lineage candidates, not Class1 conductor.

Proposed Trixel classes:

- Class1 = conductor / router / Trixel internal authority gate.
- Class2 = tile, brush, environment, composer, recipe render, pixel/artifact tooling.
- Class3 = Trixel 3D.

Decision:

- Do not move full Trixel suite into EngAIn tiers.
- Do not assume any current Trixel copy is Class1.
- Review by function and lineage, not by name.
- Create a classroom/test surface later for Trixel probes.

## Lock

ENGAIN_IS_SPINE_NOT_WAREHOUSE = TRUE
MECHANIMATION_TIER_PLACEMENT = HOLD
TRIXEL_TIER_PLACEMENT = HOLD
TRIXEL_USES_CLASS_NOT_TIER = TRUE
CLASS1_CONDUCTOR_UNRESOLVED = TRUE
STANDALONE_TOOLING_CAN_REMAIN_OUTSIDE_ENGAIN = TRUE
