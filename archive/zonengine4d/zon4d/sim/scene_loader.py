# -------------------------------------------------------------
# EngAIn Scene Loader
# -------------------------------------------------------------
# Loads a world_scene into Spatial3D + Behavior3D.
# -------------------------------------------------------------

from spatial3d_adapter import Spatial3DStateViewAdapter
from behavior_adapter import BehaviorStateView
from behavior_mr import BehaviorStateType

# scene_loader.py

class SceneLoader:
    def __init__(self, spatial_adapter, behavior_adapter, perception_adapter=None):
        self.spatial = spatial_adapter
        self.behavior = behavior_adapter
        self.perception = perception_adapter  # may be None

    def load_scene(self, scene: dict):
        print(f"[SCENE LOADER] Loading scene: {scene['id']}")

        # ---- ENTITIES ----
        for e in scene.get("entities", []):
            # 1. Spawn entity into Spatial3D
            self.spatial.spawn_entity(
                entity_id=e["id"],
                pos=e["pos"],
                tags=e.get("tags", []),
                perceiver=e.get("has_perceiver", False)
            )

            # 2. Register perceiver if declared
            if e.get("has_perceiver") and self.perception:
                self.perception.register_perceiver(e["id"])

            # 3. Seed behavior if present
            if "behavior" in e:
                self.behavior.add_agent(e["id"], e["behavior"])

        print("[SCENE LOADER] Scene loaded successfully.")

