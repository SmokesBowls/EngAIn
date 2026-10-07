# Chapterroom Authority Note

CHAPTERROOM_STATUS = SCENE_PROVIDER_LANE

Purpose:
- `chapterroom/` receives chapter-scale narrative input.
- It proposes or accepts scene boundaries.
- It writes scene packets for `passroom/`.

Passes:
- Pass A: chapter intake / chapter identity
- Pass B: scene boundary provider
- Pass C: scene packet writer

Authority rule:
- ABC provides scene packets.
- Pass 1–5 compiles scene packets.
- ABC does not make canon truth by itself.
- Scene boundaries remain drafts unless accepted by human / MrLore / EngAInOS according to the required authority path.
- `authored_scene_boundaries_proven` is a **source fact**, not an acceptance state
  (ruled 2026-10-06; matches the 09-19 splitter design, engain-avatar-audit
  `09-19-2026-scene-boundary-splitter-design-corrected-no-day-rule.md` rule 7):
  - `true` means explicit author-written scene markers (`scene NNN.x — title`,
    optionally heading-prefixed, e.g. `### scene 048.5 — title`) were found in the
    source and used for segmentation (`boundary_method = authored_scene_marker`).
  - It is `false` for every other method (scene tags, markdown headings, blank-line
    clusters, mechanical word chunks).
  - It does **not** imply EngAInOS admission, an accepted runtime stage, or MrLore
    canon promotion. Those are separate authority states owned elsewhere.
  - Superseded wording (pre-09-19): "must remain false unless canon authority
    upgrades it."

Output contract:
- `engain.scene_provider_packet.v1`

Do not:
- Do not force Pass 1–5 to pretend a whole chapter is one scene.
- Do not promote mechanical scene boundaries to authored canon boundaries.
- Do not skip MrLore when canon scene truth is being claimed.
