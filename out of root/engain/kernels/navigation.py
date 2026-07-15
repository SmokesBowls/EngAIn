"""Public facade. Do not place implementation here yet. Legacy source remains in godotsim/navigation_mr.py."""

try:
    from tier2.godotsim.navigation_mr import *  # noqa: F401,F403
except Exception as exc:
    def _navigation_import_error(*_args, **_kwargs):
        raise RuntimeError("engain.kernels.navigation facade unavailable: failed to import tier2.godotsim.navigation_mr") from exc
