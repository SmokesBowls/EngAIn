"""Public facade. Do not place implementation here yet. Legacy source remains in godotsim/spatial3d_mr.py."""

try:
    from godotsim.spatial3d_mr import *  # noqa: F401,F403
except Exception as exc:
    def _spatial_import_error(*_args, **_kwargs):
        raise RuntimeError("engain.kernels.spatial facade unavailable: failed to import godotsim.spatial3d_mr") from exc
