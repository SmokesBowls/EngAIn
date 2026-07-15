"""Public facade. Do not place implementation here yet. Legacy source remains in trixelcomposer/tile_address.py and trixelcomposer/atlas_composer.py."""

try:
    from trixelcomposer.tile_address import *  # noqa: F401,F403
except Exception as exc:
    def _tile_address_import_error(*_args, **_kwargs):
        raise RuntimeError("engain.render.trixel facade unavailable: failed to import trixelcomposer.tile_address") from exc

# atlas_composer contains heavier deps (PIL, scene_server, terminal_trixel); keep guarded.
try:
    from trixelcomposer.atlas_composer import compose_atlas, read_atlas_meta, list_terrain_types  # noqa: F401
except Exception:
    pass
