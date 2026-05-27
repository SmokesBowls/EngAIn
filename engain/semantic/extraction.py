"""Public facade. Do not place implementation here yet. Legacy source remains in godotsim/scene_extractor.py and mettaext/semantic_environment_extractor.py."""

# scene_extractor re-export (if available)
try:
    from godotsim.scene_extractor import *  # noqa: F401,F403
except Exception:
    pass

# semantic_environment_extractor helper re-exports (import-safe)
try:
    from mettaext.semantic_environment_extractor import extract as semantic_extract  # noqa: F401
    from mettaext.semantic_environment_extractor import _score_profile as semantic_score_profile  # noqa: F401
    from mettaext.semantic_environment_extractor import _infer_scale as semantic_infer_scale  # noqa: F401
except Exception:
    pass
