"""Public facade. Do not place implementation here yet. Legacy source remains in terrain/world_field_nucleus.py, terrain/terrain_thresholds.py, and terrain/trixel_world_adapter.py."""

try:
    from terrain.world_field_nucleus import *  # noqa: F401,F403
except Exception as exc:
    def _world_field_import_error(*_args, **_kwargs):
        raise RuntimeError("engain.world.field facade unavailable: failed to import terrain.world_field_nucleus") from exc

try:
    from terrain.terrain_thresholds import *  # noqa: F401,F403
except Exception:
    pass

# trixel_world_adapter uses local absolute-ish imports; keep optional.
try:
    from terrain.trixel_world_adapter import *  # noqa: F401,F403
except Exception:
    pass
