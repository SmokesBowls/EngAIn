# EngAInOS Client Authority Boundary

EngAInOS is authoritative.

This folder contains the official EngAInOS Godot game client:

- project.godot
- Main.tscn

Godot is visualization/client only.

Old Godot projects were moved outside the EngAIn repo to:

../EngAIn_fallback_godot_clients/

Those projects are preserved as fallback clients, but they are not authority and must not be imported by EngAInOS authority code.

Authority proof must remain no-Godot:

python -m pytest godotengain/engainos/tests/test_no_godot_scene_030_proof.py -q
python -m godotengain.engainos.core.no_godot_scene_proof
