# Authority-owned scene target declarations (live Trixel route)

One file per scene: `<scene_id>.json`, contract `engainos.trixel32d_scene_truth.v1`:

    {"contract": "engainos.trixel32d_scene_truth.v1",
     "scene_id": "<id>",
     "scene_revision": "scene-sha256:<sha256 of the activated scene's canonical JSON>",
     "declared_targets": [[parent_kind, parent_id, application_slot_id], ...],
     "slot_occupancy": {"<slot>": "<occupant apply id>"}}

No file for the active scene, a different revision, or a malformed file -> the
build is refused (409). Declarations are authority decisions; none are shipped
for real scenes. The proof artifact `../TRIXEL32D_SCENE_TRUTH_V1.json` is used
only by the Ticket A exporter and its tests.
