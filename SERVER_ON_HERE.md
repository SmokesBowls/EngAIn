{godot}-renderer

godot --path /home/burdens/burdens_of_a_forgotten_past/EngAIn/godotroot/zonjrender --editor

This is your visual client. It runs the zonjrender Godot project in the editor so you can play the scene, see the spawned “bridge entities”, swap placeholder meshes for real skins, and interact with the runtime through UI tools. It’s the window where your story state becomes pixels, meshes, labels, and camera.
----

{upbge}-editor

cd /home/burdens/Applications/upbge-0.50-linux-x64
./blender --path /home/burdens/burdens_of_a_forgotten_past/EngAIn/upbge/one_path.blend

This is your Blender/UPBGE world editor and alternate renderer. You use it to inspect and author 3D scene composition, test placeholder spawning in a Blender-native game loop, and eventually swap placeholders for Blender-authored assets. It’s where “engine state” can become a Blender scene with live objects.
----

{server 8080}-subsystems

cd /home/burdens/burdens_of_a_forgotten_past/EngAIn/godotsim
python3 sim_runtime.py

This is the main EngAIn simulation runtime. It hosts the live world state and core adapters (Spatial3D/Perception/Behavior/Combat/Inventory/Dialogue), ingests the vault scenes, loads a selected scene, runs the tick loop, and exposes HTTP endpoints like /health, /vault/link, /scene/load, /command, /snapshot, and /transforms. Everything else reads from or writes to this.
----

{local host 8765}-apengine

cd /home/burdens/burdens_of_a_forgotten_past/EngAIn/godotengain/engainos
python3 launch_engine.py

This is the AP/Authority sidecar. It’s the “rules brain” and orchestration layer that sits beside the sim runtime, meant to route AP queries, run rule checks, and coordinate engine-facing interfaces (the “engine ready” router you saw). It’s not the scene API and not the runtime; it’s the policy/authority engine lane.
----

{server 8090}-http 

cd /home/burdens/burdens_of_a_forgotten_past/EngAIn/godotengain/engainos
python3 -m uvicorn engainos_server:app --host 127.0.0.1 --port 8090

This is the optional HTTP facade (FastAPI) that Godot-side UI/HUD clients talk to. It serves endpoints like /api/hud/engine_summary and related “projection” views of the engine state. It’s not required for the sim to run, but it makes the UI layer cleaner and gives Godot a stable API surface for dashboards and tools.
----

{obsidian}-vault

cd /home/burdens/obsidian/obsidianburdenNov25

This is the source-of-truth content vault. It contains your narrative files and the vault.manifest.json. The runtime links to it, extracts/loads scenes, and uses it as the library of canonical content. Think of it as the “world book” the engine reads from and turns into playable scenes.
