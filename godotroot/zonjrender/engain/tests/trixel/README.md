# Trixel engine smoke test

Project-relative paths in this bundle:

- `res://engain/tests/trixel/trixel_atlas_smoke.gd`
- `res://engain/tests/trixel/trixel_atlas_smoke.tscn`
- `res://engain/tests/trixel/assets/<terrain>/atlas.png`
- `res://engain/tests/trixel/assets/<terrain>/atlas_meta.json`
- `res://engain/tests/trixel/assets/<terrain>/manifest.json`

## What this proves

This is a blunt little wrench, not a cathedral.

It verifies that Godot can:

1. load the generated Trixel atlas PNGs,
2. read the JSON manifests and atlas metadata,
3. resolve autotile roles at runtime,
4. draw a beach-band sample scene with water, shoreline, sand, grass, forest edge, a pier, and a rock/cliff patch.

## How to use it

1. Copy the `engain/tests/trixel/` folder into your Godot project root so the files land under `res://engain/tests/trixel/`.
2. Open `res://engain/tests/trixel/trixel_atlas_smoke.tscn`.
3. Run the scene.

## Expected result

You should see:

- deep water on top,
- shallow water below it,
- a shoreline band,
- a broad sand band,
- grass and forest edge bands,
- a vertical pier cutting into the water,
- a rock patch and cliff patch on the lower-right.

If the scene looks blurry, set texture filtering to nearest for 2D pixel art in your project settings or texture import settings.

## Included terrain families

- `deep_water`
- `shallow_water`
- `shoreline`
- `sand`
- `grass`
- `forest_edge`
- `pier`
- `rock`
- `cliff`

## Notes

The Python-side Trixel world integration tests passed cleanly before this bundle was assembled: 72 passed, 0 failed.

That means the data plumbing is sane. This scene is the renderer smoke test, the part where the engine gets to stop being philosophical and actually draw the little squares.
