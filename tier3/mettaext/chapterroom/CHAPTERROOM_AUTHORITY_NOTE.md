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
- `authored_scene_boundaries_proven` must remain false unless canon authority upgrades it.

Output contract:
- `engain.scene_provider_packet.v1`

Do not:
- Do not force Pass 1–5 to pretend a whole chapter is one scene.
- Do not promote mechanical scene boundaries to authored canon boundaries.
- Do not skip MrLore when canon scene truth is being claimed.
