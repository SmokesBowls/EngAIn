# Current Rehousing Map

## Status

The old flat EngAIn root has been re-housed.

Git currently reports many old tracked paths as deleted because those paths no longer live at the old root locations.

This is expected only if each deleted family has one of the following outcomes:

- moved into an authority tier inside EngAIn
- moved to a sibling lane outside EngAIn
- archived outside EngAIn
- intentionally deleted
- marked for recovery

## Internal authority moves

| Old tracked path | New authority home | Decision |
|---|---|---|
| engainos/ | tier1/engainos/ | MOVED_TO_TIER1 |
| ENGINALITY/ | tier2/engionality/ | MOVED_TO_TIER2 |
| godotsim/ | tier2/godotsim/ | MOVED_TO_TIER2 |
| mettaext/ | tier3/mettaext/ | MOVED_TO_TIER3 |
| mrlore/ | tier1/mrlore/ | MOVED_TO_TIER1 |
| topologist/ | tier2/topologist/ | MOVED_TO_TIER2 |

## External sibling lane moves

| Old tracked path | New sibling home | Decision |
|---|---|---|
| blender/ | ../blender/ | EXTERNALIZED_SIBLING_LANE |
| blender_scripts/ | ../blender_scripts/ | EXTERNALIZED_SIBLING_LANE |
| docs/ | ../docs/ | EXTERNALIZED_SIBLING_LANE |
| assets/ | ../assets/ | EXTERNALIZED_SUPPORT_SURFACE |
| archive/ | ../archive/ | EXTERNALIZED_ARCHIVE |
| gui/ | ../gui/ | EXTERNALIZED_SIBLING_LANE |
| mechanimation/ | ../mechanimation/ | EXTERNALIZED_SIBLING_LANE |
| terrain/ | ../terrain/ | EXTERNALIZED_SIBLING_LANE |
| trixel/ | ../trixel/ | EXTERNALIZED_TIER1_PEER_AUTHORITY |
| trixelcomposer/ | ../trixelcomposer/ | EXTERNALIZED_TRIXEL_FAMILY |
| trixelmap/ | ../trixelmap/ | EXTERNALIZED_TRIXEL_FAMILY |
| trixelpixel/ | ../trixelpixel/ | EXTERNALIZED_TRIXEL_FAMILY |
| trixelworld/ | ../trixelworld/ | EXTERNALIZED_TRIXEL_FAMILY |

## Commit rule

Do not commit a deletion unless its new home is proven or it is explicitly marked INTENTIONALLY_DELETED.

Do not treat sibling lanes as missing. They live beside EngAIn and must be reached later through contract, gate, relay, or probe.

EngAIn root is the authority spine, not the whole garage.
