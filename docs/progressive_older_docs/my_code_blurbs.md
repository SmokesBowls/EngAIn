    # ── Command queue ────────────────────────────────────────────

    def add_command(self, cmd: Dict[str, Any]):
        """Queue a command for processing on next simulation tick."""
        self.command_queue.append(cmd)

    def drain_commands(self, dt=None):
        """Public method to process queued simulation commands."""
        while self.command_queue:
            cmd = self.command_queue.pop(0)
            self._execute_command(cmd)

        elif action == "select_scene":
            scene_id = cmd.get("scene_id") or cmd.get("id")
            if not scene_id:
                print("[SIM] select_scene missing scene_id")
                return {"status": "error", "message": "missing scene_id"}
            ok = self.select_active_scene(scene_id)
            if ok:
                print(f"[SIM] Activated scene: {scene_id}")
                return {"status": "ok", "scene_id": scene_id}
            else:
                print(f"[SIM] Unknown scene: {scene_id}")
                return {"status": "error", "message": "unknown scene"}

    def tick(self, dt=0.016):
        """Public simulation step."""
        self._process_tick(self._tick_counter)
        self._tick_counter += 1

    # ── Simulation loop ──────────────────────────────────────────

That elif is in the wrong room. It got pasted inside the command queue section, after the while loop, where Python can’t attach it to the _execute_command() action chain. I’m checking the exact spot in your uploaded runtime_core.py so I can give you the correct insertion point instead of a vague bandage.

Thought for 34s

Yeah, that elif is pasted in the wrong place.

It cannot live under drain_commands(). Right now it is sitting after the while loop, so Python sees:

while ...:

then elif ...:

That is invalid, because the elif belongs to the if/elif chain inside _execute_command().

Use this instead.

Filename: EngAIn/godotsim/runtime_core.py

Keep your command queue section like this:

# ── Command queue ────────────────────────────────────────────

def add_command(self, cmd: Dict[str, Any]):
    """Queue a command for processing on next simulation tick."""
    self.command_queue.append(cmd)

def drain_commands(self, dt=None):
    """Public method to process queued simulation commands."""
    while self.command_queue:
        cmd = self.command_queue.pop(0)
        self._execute_command(cmd)

def tick(self, dt=0.016):
    """Public simulation step."""
    self._process_tick(self._tick_counter)
    self._tick_counter += 1

Then put the new branch inside _execute_command().

Filename: EngAIn/godotsim/runtime_core.py

Add it here, for example right after load_scene_from_file and before spawn_entity:

elif action == "select_scene":
    scene_id = cmd.get("scene_id") or cmd.get("id")
    if not scene_id:
        print("[SIM] select_scene missing scene_id")
        return

    ok = self.select_active_scene(scene_id)
    if ok:
        self.snapshot["scene_id"] = scene_id
        print(f"[SIM] Activated scene: {scene_id}")
    else:
        print(f"[SIM] Unknown scene: {scene_id}")

So that whole area should look like this:

elif action == "load_scene_from_file":
    path = cmd.get("path")
    explicit_id = cmd.get("scene_id") or cmd.get("id")
    if path and os.path.exists(path):
        try:
            with open(path, 'r') as f:
                scene_data = json.load(f)
                sid = self.load_scene(scene_data, activate=True, scene_id=explicit_id)
                self.snapshot["scene_id"] = explicit_id or scene_data.get("scene_id") or self.snapshot["scene_id"]
                print(f"[SIM] Loaded scene from file: {path} as '{self.snapshot['scene_id']}'")
        except Exception as e:
            print(f"[SIM] Error loading scene file: {e}")

elif action == "select_scene":
    scene_id = cmd.get("scene_id") or cmd.get("id")
    if not scene_id:
        print("[SIM] select_scene missing scene_id")
        return

    ok = self.select_active_scene(scene_id)
    if ok:
        self.snapshot["scene_id"] = scene_id
        print(f"[SIM] Activated scene: {scene_id}")
    else:
        print(f"[SIM] Unknown scene: {scene_id}")

elif action == "spawn_entity":
    eid = cmd.get("entity_id") or cmd.get("id")
    if eid:
        self.snapshot["entities"][eid] = cmd.get("data", {"id": eid})
        self.snapshot["events"].append({"type": "entity_spawned", "entity_id": eid})

Two other important details:

First, your runtime reads:

action = cmd.get("command") or cmd.get("action") or ""

So your request should be:

{
  "command": "select_scene",
  "scene_id": "scene.03_fist_contact"
}

Not "type": "select_scene".

Second, this usually also needs the dispatcher whitelist updated.

Filename: EngAIn/godotsim/command_dispatcher.py

Wherever you currently have:

if cmd_str in ("spawn_entity", "update_entity", "interact", "reload_blocks", "dump_state", "move_entity", "edit_dialogue", "load_scene_from_file"):

change it to:

if cmd_str in ("spawn_entity", "update_entity", "interact", "reload_blocks", "dump_state", "move_entity", "edit_dialogue", "load_scene_from_file", "select_scene"):

Then test with:

curl -s -X POST http://127.0.0.1:8080/command \
  -H "Content-Type: application/json" \
  -d '{"command":"select_scene","scene_id":"scene.03_fist_contact"}'

And verify with:

curl -s http://127.0.0.1:8080/snapshot | jq -r '.payload.scene_id'

If you want, next I can give you the matching select_chapter.py that reads chapter_registry.json and posts select_scene to 8080.
