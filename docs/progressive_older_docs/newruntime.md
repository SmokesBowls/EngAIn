
Hint: type caja to open the file manager

python3 - <<'PY' | curl -s -X POST http://127.0.0.1:8080/world/sync -H "Content-Type: application/json" -d @- ; echo
import json, subprocess

snap = json.loads(subprocess.check_output(["curl","-s","http://127.0.0.1:8080/snapshot"], text=True))
p = snap.get("payload", snap)
ents = p.get("bridge_entities", [])
assert ents, "No bridge_entities in snapshot"

e = ents[0]
eid = e["entity_id"]
pos = e.get("transform", {}).get("position", {}) or {}
newpos = {"x": float(pos.get("x",0.0)) + 1.0, "y": float(pos.get("y",0.0)), "z": float(pos.get("z",0.0))}

payload = {
  "type": "world_sync",
  "source": "cli",
  "scene_id": p.get("scene_id",""),
  "entities": {
    eid: {"transform": {"position": newpos}}
  }
}
print(json.dumps(payload))
PYbash: /home/burdens/.openclaw/completions/openclaw.bash: No such file or directory
bash: /home/linuxbrew/.linuxbrew/bin/brew: No such file or directory
(base) burdens@pop-os:~$ python3 - <<'PY' | curl -s -X POST http://127.0.0.1:8080/world/sync -H "Content-Type: application/json" -d @- ; echo
> import json, subprocess
> 
> snap = json.loads(subprocess.check_output(["curl","-s","http://127.0.0.1:8080/snapshot"], text=True))
> p = snap.get("payload", snap)
> ents = p.get("bridge_entities", [])
> assert ents, "No bridge_entities in snapshot"
> 
> e = ents[0]
> eid = e["entity_id"]
> pos = e.get("transform", {}).get("position", {}) or {}
> newpos = {"x": float(pos.get("x",0.0)) + 1.0, "y": float(pos.get("y",0.0)), "z": float(pos.get("z",0.0))}
> 
> payload = {
>   "type": "world_sync",
>   "source": "cli",
>   "scene_id": p.get("scene_id",""),
>   "entities": {
>     eid: {"transform": {"position": newpos}}
>   }
> }
> print(json.dumps(payload))
> PY
{"type": "error", "message": "No vault linked or path invalid. Use /vault/link first.", "debug": {"chain": []}}
(base) burdens@pop-os:~$ perl -pi -e 's/^func is_connected\(\) -> bool:/func runtime_is_connected() -> bool:/g' \
  /home/burdens/burdens_of_a_forgotten_past/EngAIn/godotroot/zonjrender/autoload/EngAInClient.gd
(base) burdens@pop-os:~$ grep -R "^func is_connected" -n /home/burdens/burdens_of_a_forgotten_past/EngAIn/godotroot/zonjrender
(base) burdens@pop-os:~$ python3 - <<'PY'
import json
p="/home/burdens/burdens_of_a_forgotten_past/EngAIn/upbge/engain_upbge_config.json"
cfg=json.load(open(p,"r",encoding="utf-8"))
cfg["base_url"]="http://127.0.0.1:8080"
json.dump(cfg, open(p,"w",encoding="utf-8"), indent=2)
print("updated:", p)
PY
updated: /home/burdens/burdens_of_a_forgotten_past/EngAIn/upbge/engain_upbge_config.json
(base) burdens@pop-os:~$ ss -ltnp | grep ':8080'
# then kill the pid shown, e.g.
kill <PID>
LISTEN 0      5          127.0.0.1:8080       0.0.0.0:*    users:(("python3",pid=859623,fd=3))         
bash: syntax error near unexpected token `newline'
(base) burdens@pop-os:~$ cd /home/burdens/burdens_of_a_forgotten_past/EngAIn/godotsim
python3 sim_runtime.py
[BOOT] SceneExtractor loaded (via SceneManager)
[BOOT] SemanticBridge loaded (via SceneManager)
Current working directory: /home/burdens/burdens_of_a_forgotten_past/EngAIn/godotsim
Script location: /home/burdens/burdens_of_a_forgotten_past/EngAIn/godotsim/runtime_core.py
ROOT_DIR: /home/burdens/burdens_of_a_forgotten_past/EngAIn
==================================================
  EngAIn Runtime Server
==================================================

[BOOT] Initializing EngAIn Runtime...
  ✓ Protocol: EngAIn v1.0.1
  ✓ Epoch: runtime_alpha
  ✓ Spatial3D adapter loaded
  ✓ Perception adapter loaded
  ✓ Behavior adapter loaded
  ✓ Combat3D adapter loaded
  ✓ Inventory3D adapter loaded
  ✓ Dialogue3D adapter loaded
  → EngAIn Runtime: Initialized
[PUMP] Using drain: drain_commands arity: 1
[PUMP] Using step : tick arity: 1
[PUMP] Sim pump thread started @ 60Hz
[VAULT] Cannot auto-relink — no link_vault method found on runtime
Traceback (most recent call last):
  File "/home/burdens/burdens_of_a_forgotten_past/EngAIn/godotsim/sim_runtime.py", line 200, in <module>
    main()
    ~~~~^^
  File "/home/burdens/burdens_of_a_forgotten_past/EngAIn/godotsim/sim_runtime.py", line 178, in main
    server = ThreadingHTTPServer(("127.0.0.1", 8080), RuntimeHTTPHandler)  # prevent port zombie on fast restart
  File "/home/burdens/miniconda3/lib/python3.13/socketserver.py", line 457, in __init__
    self.server_bind()
    ~~~~~~~~~~~~~~~~^^
  File "/home/burdens/miniconda3/lib/python3.13/http/server.py", line 140, in server_bind
    socketserver.TCPServer.server_bind(self)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^
  File "/home/burdens/miniconda3/lib/python3.13/socketserver.py", line 478, in server_bind
    self.socket.bind(self.server_address)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
OSError: [Errno 98] Address already in use
(base) burdens@pop-os:~/burdens_of_a_forgotten_past/EngAIn/godotsim$ curl -s -X POST http://127.0.0.1:8080/world/sync \
  -H "Content-Type: application/json" \
  -d '{"type":"world_sync","source":"cli","scene_id":"scene.04_the_convergence","entities":{"Senareth":{"transform":{"position":{"x":123,"y":0,"z":0}}}}}' ; echo
{"type": "error", "message": "No vault linked or path invalid. Use /vault/link first.", "debug": {"chain": []}}
(base) burdens@pop-os:~/burdens_of_a_forgotten_past/EngAIn/godotsim$ python3 - <<'PY'
import json, subprocess
snap=json.loads(subprocess.check_output(["curl","-s","http://127.0.0.1:8080/snapshot"], text=True))
p=snap.get("payload", snap)
for e in p.get("bridge_entities", []):
    if e.get("entity_id")=="Senareth":
        print("Senareth position =", e.get("transform",{}).get("position"))
        break
PY
(base) burdens@pop-os:~/burdens_of_a_forgotten_past/EngAIn/godotsim$ 
