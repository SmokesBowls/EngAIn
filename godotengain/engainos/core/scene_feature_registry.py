# scene_feature_registry.py

from typing import Protocol, Dict, List, Any
from .trixel_world_mr import WorldGridConfig

class FeatureGenerator(Protocol):
    def __call__(
        self,
        *,
        scene_id: str,
        config: WorldGridConfig,
        snapshot: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Return deltas (add_feature, fill_region, add_override, etc.) for this feature.
        MUST treat `snapshot` as read‑only. Never mutate the adapter!
        """

_FEATURE_REGISTRY: Dict[str, FeatureGenerator] = {}
_registered_defaults: bool = False

def register_feature(name: str, generator: FeatureGenerator) -> None:
    """Register a feature generator."""
    _FEATURE_REGISTRY[name] = generator

def get_feature_generator(name: str) -> FeatureGenerator | None:
    """Fetch a registered generator."""
    return _FEATURE_REGISTRY.get(name)

def ensure_default_features_registered() -> None:
    """Lazy‑load default beach features. Safe to call multiple times."""
    global _registered_defaults
    if _registered_defaults:
        return
    from .scene_features_beach import register_beach_features
    register_beach_features()
    _registered_defaults = True
