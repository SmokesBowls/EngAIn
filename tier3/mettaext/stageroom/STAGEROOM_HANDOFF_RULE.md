# Stageroom Handoff Rule

STAGEROOM_HANDOFF_RULE = TRUE

Mettaext is a producer, not a dispatcher.

Mettaext reads:
- vault text
- authored chapter text
- source prose

Mettaext runs:
- chapterroom ABC
- passroom 1–5

Mettaext writes:
- Pass A chapter intake manifests
- Pass B scene boundary proposals
- Pass C scene packets and indexes
- Pass 1 semantic extraction
- Pass 2 MeTTa inference
- Pass 3 ZONJ candidates
- Pass 4 ZON / canonical ZONJ
- Pass 5 game scene candidates
- mettaext_done_manifest.json

Mettaext does not call:
- EngAInOS
- MrLore
- GodotSim
- Engionality
- Godot
- Trixel

Consumer rule:
- MrLore may read stageroom artifacts for canon review.
- EngAInOS may read stageroom artifacts for declared/runtime acceptance.
- GodotSim may read only EngAInOS-accepted simulation inputs.
- Engionality may read only EngAInOS-accepted scene/entity/context inputs.
- Godot may display only accepted state.
- Trixel lanes may consume only accepted visual/spatial/art demands.

Authority rule:
- Presence in stageroom is not acceptance.
- Presence in stageroom is not canon.
- Presence in stageroom is not runtime truth.
- Presence in stageroom is evidence only.

Final:
- Mettaext leaves evidence.
- The owning authority comes to inspect it.
