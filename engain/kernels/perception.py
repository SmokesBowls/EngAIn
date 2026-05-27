"""Public facade. Do not place implementation here yet. Legacy source remains in godotsim/perception_mr.py."""

try:
    from godotsim.perception_mr import *  # noqa: F401,F403
except Exception as exc:
    def _perception_import_error(*_args, **_kwargs):
        raise RuntimeError("engain.kernels.perception facade unavailable: failed to import godotsim.perception_mr") from exc
