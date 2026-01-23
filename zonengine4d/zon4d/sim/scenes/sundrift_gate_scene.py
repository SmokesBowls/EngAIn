# -------------------------------------------------------------
# Sundrift Gate Scene Specification
# -------------------------------------------------------------
# This is the FIRST canonical world_scene.
# It conforms to the EngAIn World Skeleton Format.
# -------------------------------------------------------------

SCENE_SUNDRIFT_GATE = {
    "id": "sundrift_gate_intro",
    "description": "Tran approaches the Sundrift outer gate. Two guards patrol opposite arcs.",

    "entities": [
        {
            "id": "tran",
            "kind": "actor",
            "pos": (-20.0, 0.0, 0.0),
            "tags": ["player", "hero"]
        },
        {
            "id": "guard_a",
            "pos": (0, 0, -5),
            "tags": ["npc", "hostile"],
            "has_perceiver": True
        },
        {
            "id": "guard_b",
            "pos": (0, 0, 5),
            "tags": ["npc", "hostile"],
            "has_perceiver": True
        },
        {
            "id": "gate",
            "kind": "structure",
            "pos": (0.0, 0.0, 0.0),
            "tags": ["static", "gate"]
        }
    ],

    "triggers": [
        {
            "id": "trigger_guard_confront",
            "type": "proximity",
            "entities": ["tran", "guard_a", "guard_b"],
            "distance": 10.0,
            "on_activate": "behavior3d/raise_alert"
        }
    ]
}
