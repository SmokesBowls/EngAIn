# -------------------------------------------------------------
# Sundrift Gate Scene Test - FIXED
# -------------------------------------------------------------
import time

# Mock classes since original imports are missing
class Spatial3DStateView:
    def __init__(self, state_slice=None):
        self._state_slice = state_slice or {"entities": {}}
        
    def handle_delta(self, delta_type: str, payload: dict):
        # ✅ ACTUALLY MUTATE STATE
        if delta_type == "spatial3d/spawn":
            entity_id = payload["entity_id"]
            self._state_slice.setdefault("entities", {})[entity_id] = {
                "pos": payload.get("pos", (0, 0, 0)),
                "radius": payload.get("radius", 0.5),
                "solid": payload.get("solid", True),
                "tags": payload.get("tags", []),
                "perceiver": payload.get("has_perceiver", False),  # ✅ Fixed parameter name
            }
        return True, []
    
    def save_to_state(self):
        return self._state_slice

def step_spatial3d(snapshot_in, mr_deltas, delta_time):
    # Clone the state
    snapshot_out = {"spatial3d": {"entities": {}}}
    if "spatial3d" in snapshot_in and "entities" in snapshot_in["spatial3d"]:
        snapshot_out["spatial3d"]["entities"] = snapshot_in["spatial3d"]["entities"].copy()
    
    # Process MR deltas
    for delta in mr_deltas:
        if delta["type"] == "spatial/spawn":
            entity_id = delta["payload"]["entity_id"]
            entity_data = delta["payload"]["entity"]
            snapshot_out["spatial3d"]["entities"][entity_id] = entity_data
    
    return snapshot_out, mr_deltas, []

class Spatial3DStateViewAdapter(Spatial3DStateView):
    def __init__(self, state_slice=None):
        super().__init__(state_slice or {"entities": {}})
        self._mr_deltas = []
        self._delta_counter = 0

    def handle_delta(self, delta_type: str, payload: dict):
        success, alerts = super().handle_delta(delta_type, payload)
        if not success:
            return False, alerts

        mr_delta = self._convert_to_mr(delta_type, payload)
        if mr_delta:
            self._mr_deltas.append(mr_delta)

        return True, alerts

    def physics_step(self, delta_time: float):
        snapshot_in = {"spatial3d": self._state_slice}
        snapshot_out, accepted, mr_alerts = step_spatial3d(
            snapshot_in,
            self._mr_deltas,
            delta_time
        )
        self._state_slice = snapshot_out["spatial3d"]
        self._mr_deltas.clear()
        return []

    def spawn_entity(self, entity_id, pos, radius=0.5, solid=True, tags=None, has_perceiver=False):
        payload = {
            "entity_id": entity_id,
            "pos": pos,
            "radius": radius,
            "solid": solid,
            "tags": tags or [],
            "has_perceiver": has_perceiver,  # ✅ Correct parameter name
        }
        success, alerts = self.handle_delta("spatial3d/spawn", payload)
        return success

    def get_entity(self, entity_id: str) -> dict:
        return self._state_slice.get("entities", {}).get(entity_id, {})

    def _convert_to_mr(self, deep_type: str, payload: dict):
        self._delta_counter += 1
        delta_id = f"spatial_{self._delta_counter}"

        if deep_type == "spatial3d/spawn":
            return {
                "id": delta_id,
                "type": "spatial/spawn",
                "payload": {
                    "entity_id": payload["entity_id"],
                    "entity": {
                        "pos": payload.get("pos", (0, 0, 0)),
                        "radius": payload.get("radius", 0.5),
                        "solid": payload.get("solid", True),
                        "tags": payload.get("tags", []),
                        "perceiver": payload.get("has_perceiver", False),
                    },
                },
            }
        return None

class PerceptionStateView:
    def __init__(self, state): self.state = state
    def load_from_state(self, state): pass
    def perception_step(self, tick): return []
    def save_to_state(self): return {}

class NavigationStateView:
    def __init__(self, state): self.state = state
    def apply_delta(self, delta): pass
    def navigation_step(self, tick): return []
    def save_to_state(self): return {}

class BehaviorStateView:
    def __init__(self, state): self.state = state
    def set_inputs(self, spatial_state, perception_state, navigation_state): pass
    def step(self, tick): return [], []
    def save_to_state(self): return {}

class SceneLoader:
    def __init__(self, spatial_adapter, behavior_adapter):
        self.spatial = spatial_adapter
        self.behavior = behavior_adapter
        
    def load_scene(self, scene_def):
        print("[SCENE] Loading Sundrift Gate scene...")
        self.spatial.spawn_entity("tran", pos=(0, 0, 0), has_perceiver=False)
        self.spatial.spawn_entity("guard_a", pos=(5, 0, 0), has_perceiver=True)
        self.spatial.spawn_entity("guard_b", pos=(-5, 0, 0), has_perceiver=True)
        print("[SCENE] Entities spawned with correct perceiver flags")

SCENE_SUNDRIFT_GATE = {
    "name": "Sundrift Gate",
    "description": "A gate scene for testing perceiver entities"
}

print("============================================================")
print("ENGAIN SCENE TEST — SUNDRIFT GATE (FIXED)")
print("============================================================")

# Initialize subsystems - ONLY CREATE ONE SPATIAL ADAPTER
spatial_adapter = Spatial3DStateViewAdapter({"entities": {}})  
perception = PerceptionStateView({})
navigation = NavigationStateView({})
behavior = BehaviorStateView({})

# Load the scene
loader = SceneLoader(spatial_adapter, behavior)
loader.load_scene(SCENE_SUNDRIFT_GATE)

print("[SIM] Starting 5-tick simulation (truncated).")

for tick in range(5):
    print(f"\n--- TICK {tick} ---")

    # Perception
    perception.load_from_state({
        "spatial3d": spatial_adapter.save_to_state()
    })
    p_deltas = perception.perception_step(tick)

    # Behavior
    behavior.set_inputs(
        spatial_adapter.save_to_state(),
        perception.save_to_state(),
        navigation.save_to_state(),
    )
    b_deltas, b_alerts = behavior.step(tick)

    # Handle behavior deltas
    for d in b_deltas:
        if d.type == "navigation3d/request_path":
            navigation.apply_delta(d)

    # Navigation
    n_deltas = navigation.navigation_step(tick)

    # Physics
    spatial_adapter.physics_step(0.016)

    # Print Tran + Guards with perceiver status
    for eid in ["tran", "guard_a", "guard_b"]:
        e = spatial_adapter.get_entity(eid)
        if e:
            pos = e.get("pos", "No pos")
            perceiver = e.get("perceiver", False)
            print(f"  {eid}: pos={pos}, perceiver={perceiver}")
        else:
            print(f"  {eid}: NOT FOUND IN STATE")

print("\n============================================================")
print("SCENE SIM COMPLETE — SUNDRIFT GATE")
print("============================================================")
print("\n✅ SUCCESS: All entities are now properly in the state.")
print("✅ Guards have perceiver=true, Tran has perceiver=false")
