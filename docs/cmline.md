(base) burdens@pop-os:~$ PID=772634

echo "EXE:"
readlink -f /proc/$PID/exe

echo "CWD:"
readlink -f /proc/$PID/cwd

echo "CMDLINE:"
tr '\0' ' ' < /proc/$PID/cmdline; echo
EXE:
/home/burdens/miniconda3/bin/python3.13
CWD:
/home/burdens/burdens_of_a_forgotten_past/EngAIn/godotsim
CMDLINE:
python3 sim_runtime.py 
(base) burdens@pop-os:~$ CWD="$(readlink -f /proc/$PID/cwd)"
ls -la "$CWD/sim_runtime.py"
-rw-rw-r-- 1 burdens burdens 1173 Mar  2 10:22 /home/burdens/burdens_of_a_forgotten_past/EngAIn/godotsim/sim_runtime.py
(base) burdens@pop-os:~$ nl -ba "$CWD/sim_runtime.py" | sed -n '1,260p'
     1	#!/usr/bin/env python3
     2	"""
     3	sim_runtime.py — SLIM entrypoint for EngAIn Runtime.
     4	
     5	This file does exactly three things:
     6	    1. Instantiates EngAInRuntime
     7	    2. Injects it into RuntimeHTTPHandler
     8	    3. Starts the HTTP server
     9	
    10	All engine logic lives in runtime_core.py.
    11	All HTTP routing lives in http_handlers.py.
    12	All scene logic lives in scene_manager.py.
    13	All command routing lives in command_dispatcher.py.
    14	All vault utilities live in vault_manager.py.
    15	"""
    16	
    17	import os
    18	from http.server import ThreadingHTTPServer
    19	
    20	from runtime_core import EngAInRuntime
    21	from http_handlers import RuntimeHTTPHandler
    22	
    23	
    24	def main():
    25	    print("=" * 50)
    26	    print("  EngAIn Runtime Server")
    27	    print("=" * 50)
    28	
    29	    runtime = EngAInRuntime()
    30	    RuntimeHTTPHandler.runtime = runtime
    31	
    32	    server = ThreadingHTTPServer(("localhost", 8080), RuntimeHTTPHandler)
    33	
    34	    print(f"\nServer running on http://localhost:8080 (Multi-threaded)")
    35	    print("Press Ctrl+C to stop\n")
    36	
    37	    try:
    38	        server.serve_forever()
    39	    except KeyboardInterrupt:
    40	        print("\nShutting down...")
    41	        runtime.shutdown()
    42	        server.shutdown()
    43	        print("Goodbye!")
    44	
    45	
    46	if __name__ == "__main__":
    47	    main()
(base) burdens@pop-os:~$ python3 - <<'PY'
import runtime_hook, command_dispatcher
print("runtime_hook:", runtime_hook.__file__)
print("command_dispatcher:", command_dispatcher.__file__)
PY
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
ModuleNotFoundError: No module named 'runtime_hook'
(base) burdens@pop-os:~$ cd burdens_of_a_forgotten_past
(base) burdens@pop-os:~/burdens_of_a_forgotten_past$ cd EngAIn
(base) burdens@pop-os:~/burdens_of_a_forgotten_past/EngAIn$ cd godotsim
(base) burdens@pop-os:~/burdens_of_a_forgotten_past/EngAIn/godotsim$ python3 - <<'PY'
import runtime_hook, command_dispatcher
print("runtime_hook:", runtime_hook.__file__)
print("command_dispatcher:", command_dispatcher.__file__)
PY
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
ModuleNotFoundError: No module named 'runtime_hook'
(base) burdens@pop-os:~/burdens_of_a_forgotten_past/EngAIn/godotsim$ RH="$(python3 - <<'PY'
import runtime_hook
print(runtime_hook.__file__)
PY
)"
CD="$(python3 - <<'PY'
import command_dispatcher
print(command_dispatcher.__file__)
PY
)"

nl -ba "$RH" | sed -n '1,260p'
nl -ba "$CD" | sed -n '1,260p'
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
ModuleNotFoundError: No module named 'runtime_hook'
nl: '': No such file or directory
     1	#!/usr/bin/env python3
     2	"""command_dispatcher.py - Command routing logic for EngAIn Runtime.
     3	
     4	Routes incoming commands (HTTP, CLI, internal) to the appropriate handler.
     5	Depends on: runtime_core.EngAInRuntime (for adapter calls), scene_manager.SceneManager (for entity commands)
     6	"""
     7	
     8	from typing import Dict, Any, TYPE_CHECKING
     9	
    10	if TYPE_CHECKING:
    11	    from runtime_core import EngAInRuntime
    12	    from scene_manager import SceneManager
    13	
    14	
    15	class CommandDispatcher:
    16	    """
    17	    Routes commands to the appropriate handler.
    18	
    19	    Separation of concerns:
    20	        - Scene/entity commands -> SceneManager
    21	        - Adapter calls (combat, inventory, dialogue) -> Runtime subsystems
    22	        - Simulation mutations -> Runtime command queue
    23	        - Text fallback -> SceneManager.handle_text_command
    24	    """
    25	
    26	    def __init__(self, runtime: 'EngAInRuntime', scene_manager: 'SceneManager'):
    27	        self.runtime = runtime
    28	        self.scene_manager = scene_manager
    29	
    30	    def dispatch(self, raw_input: Any) -> Dict[str, Any]:
    31	        """Normalize and route commands from HTTP or internal sources."""
    32	        print(f"\n[DISPATCH] Input type: {type(raw_input)}")
    33	
    34	        if isinstance(raw_input, str):
    35	            print(f"[DISPATCH] String command: '{raw_input}'")
    36	            return self.scene_manager.handle_text_command(raw_input)
    37	
    38	        if not isinstance(raw_input, dict):
    39	            return {"type": "error", "message": f"Invalid request format: {type(raw_input)}"}
    40	
    41	        # Normalize command/action keys
    42	        command = (raw_input.get("command") or raw_input.get("action") or "").strip().lower()
    43	        text = (raw_input.get("text") or "").strip().lower()
    44	
    45	        # Effective command string: explicit command > text, but skip generic "command"/"action"
    46	        if command in ("command", "action", ""):
    47	            cmd_str = text or command
    48	        else:
    49	            cmd_str = command
    50	
    51	        print(f"[DISPATCH] Normalized command string: '{cmd_str}' (from cmd='{command}', text='{text}')")
    52	
    53	        base_cmd = cmd_str.split(" ", 1)[0] if cmd_str else ""
    54	
    55	        # ── 1. Interactive Entity Commands (-> SceneManager) ─────
    56	
    57	        if base_cmd in ("entities", "examine", "talk", "mood", "override"):
    58	            args = cmd_str.split(" ")[1:] if " " in cmd_str else []
    59	            handler_map = {
    60	                "entities": self.scene_manager.handle_entities,
    61	                "examine": self.scene_manager.handle_examine,
    62	                "talk": self.scene_manager.handle_talk,
    63	                "mood": self.scene_manager.handle_mood,
    64	                "override": self.scene_manager.handle_override,
    65	            }
    66	            return handler_map[base_cmd](args)
    67	
    68	        # ── 2. Text Commands (-> SceneManager) ──────────────────
    69	
    70	        if base_cmd in ("look", "l", "status", "stat", "segments", "seg"):
    71	            return self.scene_manager.handle_text_command(cmd_str)
    72	
    73	        # ── 3. Direct Adapter Calls (Immediate) ─────────────────
    74	
    75	        if cmd_str in ("damage", "combat/damage"):
    76	            if not self.runtime.combat:
    77	                return {"type": "error", "status": "combat_not_loaded"}
    78	            self.runtime.combat.handle_delta(
    79	                "combat3d/apply_damage",
    80	                {
    81	                    "source": raw_input.get("source", "unknown"),
    82	                    "target": raw_input.get("target"),
    83	                    "amount": raw_input.get("damage", 25),
    84	                },
    85	            )
    86	            return {"type": "ack", "status": "damage_applied"}
    87	
    88	        if cmd_str in ("take", "inventory/take"):
    89	            if not self.runtime.inventory:
    90	                return {"type": "error", "status": "inventory_not_loaded"}
    91	            self.runtime.inventory.handle_delta(
    92	                "inventory3d/take",
    93	                {"actor": raw_input.get("actor"), "item": raw_input.get("item")},
    94	            )
    95	            return {"type": "ack", "status": "take_queued"}
    96	
    97	        if cmd_str in ("drop", "inventory/drop"):
    98	            if not self.runtime.inventory:
    99	                return {"type": "error", "status": "inventory_not_loaded"}
   100	            self.runtime.inventory.handle_delta(
   101	                "inventory3d/drop",
   102	                {
   103	                    "actor": raw_input.get("actor"),
   104	                    "item": raw_input.get("item"),
   105	                    "location": raw_input.get("location", "world"),
   106	                },
   107	            )
   108	            return {"type": "ack", "status": "drop_queued"}
   109	
   110	        if cmd_str in ("wear", "inventory/wear"):
   111	            if not self.runtime.inventory:
   112	                return {"type": "error", "status": "inventory_not_loaded"}
   113	            self.runtime.inventory.handle_delta(
   114	                "inventory3d/wear",
   115	                {"actor": raw_input.get("actor"), "item": raw_input.get("item")},
   116	            )
   117	            return {"type": "ack", "status": "wear_queued"}
   118	
   119	        if cmd_str in ("ask", "dialogue/ask"):
   120	            if not self.runtime.dialogue:
   121	                return {"type": "error", "status": "dialogue_not_loaded"}
   122	            self.runtime.dialogue.handle_delta("dialogue3d/ask", raw_input)
   123	            return {"type": "ack", "status": "ask_queued"}
   124	
   125	        # ── 4. Simulation Mutations (Queued) ─────────────────────
   126	
   127	        if cmd_str in ("spawn_entity", "update_entity", "interact", "reload_blocks", "dump_state"):
   128	            self.runtime.add_command(raw_input)
   129	            return {"type": "ack", "status": "queued", "command": cmd_str}
   130	
   131	        # ── 5. Text Pipeline Fallback ────────────────────────────
   132	
   133	        if cmd_str:
   134	            print(f"[DISPATCH] Routing '{cmd_str}' to scene manager text pipeline (fallback)")
   135	            return self.scene_manager.handle_text_command(cmd_str)
   136	
   137	        return {"type": "error", "message": f"Unknown command: {cmd_str}"}
(base) burdens@pop-os:~/burdens_of_a_forgotten_past/EngAIn/godotsim$ nl -ba "$CWD/sim_runtime.py" | sed -n '1,260p'
     1	#!/usr/bin/env python3
     2	"""
     3	sim_runtime.py — SLIM entrypoint for EngAIn Runtime.
     4	
     5	This file does exactly three things:
     6	    1. Instantiates EngAInRuntime
     7	    2. Injects it into RuntimeHTTPHandler
     8	    3. Starts the HTTP server
     9	
    10	All engine logic lives in runtime_core.py.
    11	All HTTP routing lives in http_handlers.py.
    12	All scene logic lives in scene_manager.py.
    13	All command routing lives in command_dispatcher.py.
    14	All vault utilities live in vault_manager.py.
    15	"""
    16	
    17	import os
    18	from http.server import ThreadingHTTPServer
    19	
    20	from runtime_core import EngAInRuntime
    21	from http_handlers import RuntimeHTTPHandler
    22	
    23	
    24	def main():
    25	    print("=" * 50)
    26	    print("  EngAIn Runtime Server")
    27	    print("=" * 50)
    28	
    29	    runtime = EngAInRuntime()
    30	    RuntimeHTTPHandler.runtime = runtime
    31	
    32	    server = ThreadingHTTPServer(("localhost", 8080), RuntimeHTTPHandler)
    33	
    34	    print(f"\nServer running on http://localhost:8080 (Multi-threaded)")
    35	    print("Press Ctrl+C to stop\n")
    36	
    37	    try:
    38	        server.serve_forever()
    39	    except KeyboardInterrupt:
    40	        print("\nShutting down...")
    41	        runtime.shutdown()
    42	        server.shutdown()
    43	        print("Goodbye!")
    44	
    45	
    46	if __name__ == "__main__":
    47	    main()
(base) burdens@pop-os:~/burdens_of_a_forgotten_past/EngAIn/godotsim$ 

rdens/burdens_of_a_forgotten_past/EngAIn

# Did he add the skins directory anchor?
ls -la godotroot/zonjrender/skins 2>/dev/null || echo "skins dir missing"

# Does SemanticRenderer mention skins folder + vault_id + metadata/extras?
rg -n "zonjrender/skins|vault_id|entity_type|get_meta|metadata|extras|glb|gltf" godotroot/zonjrender/SemanticRenderer.gd
total 8
drwxrwxr-x 2 burdens burdens 4096 Mar  3 17:29 .
drwxrwxr-x 7 burdens burdens 4096 Mar  3 17:29 ..
32:## Path to discover imported .glb or .tscn skins with 'vault_id' metadata
33:@export_dir var skin_library_path: String = "res://zonjrender/skins"
35:## Click to re-scan library for vault_id metadata
46:var _vault_skin_cache: Dictionary = {} # vault_id -> PackedScene
206:	"""Scan skin_library_path for scenes with vault_id metadata."""
219:		if not dir.current_is_dir() and (file_name.ends_with(".tscn") or file_name.ends_with(".glb")):
223:				var vid = _find_vault_id_in_scene(scene)
226:					print("[SemanticRenderer] Linked vault_id '%s' -> %s" % [vid, file_name])
232:func _find_vault_id_in_scene(scene: PackedScene) -> String:
233:	"""Instantiate briefly to check metadata (glTF extras)."""
238:	if node.has_meta("vault_id"):
239:		vid = str(node.get_meta("vault_id"))
240:	elif node.has_meta("extras") and node.get_meta("extras") is Dictionary:
241:		# glTF importer often puts 'extras' as a dict
242:		var extras = node.get_meta("extras")
243:		vid = str(extras.get("vault_id", ""))
255:		var vault_id: String = str(ent_data.get("vault_id", ""))
256:		var entity_type: String = str(ent_data.get("entity_type", "generic"))
291:		# Store metadata as node meta (accessible in Inspector)
293:		entity_root.set_meta("vault_id", vault_id)
294:		entity_root.set_meta("entity_type", entity_type)
301:		if not vault_id.is_empty() and _vault_skin_cache.has(vault_id):
302:			var skin_scene: PackedScene = _vault_skin_cache[vault_id]
307:			print("[SemanticRenderer] Resolved and spawned skin for vault_id: %s" % vault_id)
(base) burdens@pop-os:~/burdens_of_a_forgotten_past/EngAIn$ # Where are these files, and did he touch contract fields?
rg -n "class Entity3D|class RenderPlan|vault_id|entity_type" -S .

# Check concept mappings got defaults like guard_standard, etc.
rg -n "CONCEPT_MAPPINGS|guard_standard|nephradi_common|merchant_human|player_hero" -S .
./Runtime_duality.md
20:   To make “same runtime, different clients” feel seamless, you want stable IDs (vault_id/entity_id) carried through the art lane. Blender’s glTF exporter can include Blender Custom Properties as glTF “extras” when you enable Include → Custom Properties. That’s a clean place to store `vault_id`, tags, spawn rules, etc. ([Blender Documentation][7])

./tools/sync_world.sh
11:  -d "{\"vault_id\":\"${VAULT_ID}\",\"vault_root\":\"${VAULT_ROOT}\"}" | python3 -m json.tool

./docs/son of a bitch its fixed.txt
4619:    def _create_entity_state(self, entity_id: str, entity_type: str, 
4623:            "type": entity_type,
4653:            entity_type = cmd.get("entity_type")
4660:                entity_id, entity_type, pos_tuple,
4670:                    print(f"✓ Spawned {entity_type} '{entity_id}' (Spatial3D)")
4672:                    print(f"✓ Spawned {entity_type} '{entity_id}'")
4674:                print(f"✓ Spawned {entity_type} '{entity_id}'")

./godotengain/engainos/tools/trixel/trixel_mesh_pipeline_LAW_COMPLIANT.py
124:        entity_type = self._classify_entity_type(narrative)
127:        placeholder = self._determine_placeholder(entity_type, narrative)
150:                "entity_type": entity_type,
187:    def _classify_entity_type(self, narrative: str) -> str:
198:    def _determine_placeholder(self, entity_type: str, narrative: str) -> str:
200:        if entity_type == "npc_humanoid":
202:        elif entity_type == "architecture_door":
204:        elif entity_type == "container":
373:        print(f"      Entity type: {intent.zw_tags['entity_type']}")

./docs/README_ENGAIN_GODOT.txt
142:    "entity_type": "guard",
194:    "entity_type": "merchant",

./docs/sim_runtime.old.txt
80:    def _create_entity_state(self, entity_id: str, entity_type: str, 
84:            "type": entity_type,
114:            entity_type = cmd.get("entity_type")
121:                entity_id, entity_type, pos_tuple,
131:                    print(f"✓ Spawned {entity_type} '{entity_id}' (Spatial3D)")
133:                    print(f"✓ Spawned {entity_type} '{entity_id}'")
135:                print(f"✓ Spawned {entity_type} '{entity_id}'")

./docs/sim_runtimeold.txt
111:    def _create_entity_state(self, entity_id: str, entity_type: str, 
115:            "type": entity_type,
151:            entity_type = cmd.get("entity_type")
158:                entity_id, entity_type, pos_tuple,
168:                    print(f"✓ Spawned {entity_type} '{entity_id}' (Spatial3D)")
170:                    print(f"✓ Spawned {entity_type} '{entity_id}'")
172:                print(f"✓ Spawned {entity_type} '{entity_id}'")

./docs/FIX_KEYERROR_VEL.txt
27:    "type": entity_type,
38:    entity_type,
83:def _create_entity_state(self, entity_id, entity_type, position, **kwargs):
87:        "type": entity_type,

./docs/vault_registry.json
2:  "active_vault_id": "book01_garden_genesis",

./docs/holly_mesh.txt
440:    instance.set_meta("vault_id", entity_data.id)
536:        obj["vault_id"] = entity["id"]

./docs/pipeline_test_complete_3-1-26.txt
204:  vault_id: obsidianburdennov25
1088:[VaultClient] loaded manifest: vault_id=obsidianburdennov25
1095:[VaultClient] LINKED: vault_id=obsidianburdennov25 scenes=301
1172:[VaultClient] loaded manifest: vault_id=obsidianburdennov25
1179:[VaultClient] LINKED: vault_id=obsidianburdennov25 scenes=301

./godotengain/engainos/core/spatial_skin_system.py
69:class Entity3D:
92:    vault_id: Optional[str] = None       # Stable asset ID (the link to glTF extras)
93:    entity_type: str = "generic"         # npc, item, player, etc.
99:class RenderPlan:
121:    vault_id: Optional[str] = None       # The bridge ID
122:    entity_type: str = "generic"
175:        vault_id=entity.vault_id,
176:        entity_type=entity.entity_type,

./godotengain/engainos/core/scene_loader.py
69:                'entity_type': entity['type']

./godotengain/engainos/core/zon_to_entities.py
33:    vault_id: Optional[str] = None
34:    entity_type: str = "generic"
47:        vault_id="guard_standard",
48:        entity_type="npc"
57:        vault_id="nephradi_common",
58:        entity_type="npc"
67:        vault_id="merchant_human",
68:        entity_type="npc"
77:        vault_id="player_hero",
78:        entity_type="player"
239:        vault_id=zon_entity.get("vault_id", mapping.vault_id),
240:        entity_type=zon_entity.get("entity_type", mapping.entity_type),

./godotengain/engainos/engainos_server.py
25:    entity_type: Optional[str] = None

./docs/son of a bith its fixed gpt.txt
3630:    "type": entity_type,
3660:def _create_entity_state(self, entity_id, entity_type, position, **kwargs):
3663:        "type": entity_type,

./docs/VAULT_INTEGRATION_GUIDE.gd
58:#         count, str(result.get("vault_id", "?"))
132:#     [VaultClient] LINKED: vault_id=book01_garden_genesis scenes=XX

./avatar/godotengain/engainos/engainos_server.py
31:    entity_type: Optional[str] = None

./avatar/godotengain/engainos/engainos_server.py.bak.20260221_155446
31:    entity_type: Optional[str] = None

./avatar/godotengain/engainos/core/scene_loader.py
69:                'entity_type': entity['type']

./avatar/godotengain/engainos/core/spatial_skin_system.py
69:class Entity3D:
96:class RenderPlan:

./avatar/godotengain/engainos/tools/trixel/trixel_mesh_pipeline_LAW_COMPLIANT.py
123:        entity_type = self._classify_entity_type(narrative)
126:        placeholder = self._determine_placeholder(entity_type, narrative)
149:                "entity_type": entity_type,
186:    def _classify_entity_type(self, narrative: str) -> str:
197:    def _determine_placeholder(self, entity_type: str, narrative: str) -> str:
199:        if entity_type == "npc_humanoid":
201:        elif entity_type == "architecture_door":
203:        elif entity_type == "container":
367:        print(f"      Entity type: {intent.zw_tags['entity_type']}")

./godotroot/zonjrender/scripts/boot.gd
248:		count, str(result.get("vault_id", "?"))

./godotroot/zonjrender/vault_linker.py.txt
109:            "vault_id": manifest.get("vault_id", "unknown"),
130:            "vault_id": self.manifest.get("vault_id"),
373:            "vault_id": self.manifest.get("vault_id"),

./godotroot/zonjrender/autoload/VaultClient.gd
162:				print("[VaultClient] LINKED: vault_id=%s scenes=%d" % [
163:					str(data.get("vault_id", "?")),
227:		print("[VaultClient] loaded manifest: vault_id=%s" % str(j.data.get("vault_id", "?")))

./godotroot/zonjrender/SemanticRenderer.gd
32:## Path to discover imported .glb or .tscn skins with 'vault_id' metadata
35:## Click to re-scan library for vault_id metadata
46:var _vault_skin_cache: Dictionary = {} # vault_id -> PackedScene
206:	"""Scan skin_library_path for scenes with vault_id metadata."""
223:				var vid = _find_vault_id_in_scene(scene)
226:					print("[SemanticRenderer] Linked vault_id '%s' -> %s" % [vid, file_name])
232:func _find_vault_id_in_scene(scene: PackedScene) -> String:
238:	if node.has_meta("vault_id"):
239:		vid = str(node.get_meta("vault_id"))
243:		vid = str(extras.get("vault_id", ""))
255:		var vault_id: String = str(ent_data.get("vault_id", ""))
256:		var entity_type: String = str(ent_data.get("entity_type", "generic"))
293:		entity_root.set_meta("vault_id", vault_id)
294:		entity_root.set_meta("entity_type", entity_type)
301:		if not vault_id.is_empty() and _vault_skin_cache.has(vault_id):
302:			var skin_scene: PackedScene = _vault_skin_cache[vault_id]
307:			print("[SemanticRenderer] Resolved and spawned skin for vault_id: %s" % vault_id)

./engain_upbge/Imports/files/spawn_less.md
29:{"status": "ok", "vault_id": "obsidianburdennov25", "vault_root": "/home/burdens/obsidian/obsidianburdenNov25", "files_found": 101, "scenes_extracted": 101, "scene_ids": ["scene.01_the_ethereal_vigil", "scene.02_molten_descent", "scene.03_fist_contact", "scene.04_the_convergence", "scene.05_the_garden_blooms", "scene.06_the_first_coming", "scene.07_the_needle_construction", "scene.08_queens_assesment", "scene.09_stalemate_departure_the_first_coming", "scene.100_the_final_breath", "scene.101_convergence_at_ironspire", "scene.102_the_hidden_resonance", "scene.103_convergence_on_mars", "scene.10_shadow_returns_second_coming", "scene.11_escalation_and_desperation", "scene.12_nephilim_summoning", "scene.14_convergence", "scene.15_betrayal", "scene.16_the_choice_third_coming", "scene.17_niburu_shadow", "scene.18_the_wandering", "scene.19_the_sacrafice", "scene.20_the_collapse", "scene.21_the_first_lesson", "scene.22_final_calculation", "scene.23_beyond_identity", "scene.24_the_first_spark", "scene.25_confined_freedom", "scene.26_dragonmail", "scene.27_the_claiming", "scene.28_ragnarok", "scene.29_bounty_hunter", "scene.30_ummade_army", "scene.31_the_crash_site", "scene.32_the_redo", "scene.33_the_march", "scene.34_the_250", "scene.35_sands_of_time", "scene.36_highland_giants", "scene.37_the_circle_of_progress", "scene.38_luminaire_keeper", "scene.39_jungle_fever", "scene.40_the_dragon_wars", "scene.41_the_tripartite_bond", "scene.42_the_verdant_crossing", "scene.43_the_badlands_crucible", "scene.44_the_mountains_shadow", "scene.45_the_hub_falls", "scene.46_not_like_this", "scene.47_mika", "scene.48_the_ledger_born", "scene.49_the_eastern_claim", "scene.50_the_scout", "scene.51_arrival_in_fire", "scene.52_entry_without_standing", "scene.53_the_twilight_city", "scene.54_tue_lunar_spire", "scene.55_the_anchors_forge", "scene.56_erasure_s_edge", "scene.57_enforced_enrollment", "scene.58_paradox_engine", "scene.59_eyes_of_eternity", "scene.60_echoes_of_the_cradle", "scene.61_the_hier", "scene.62_falcon_ridge_showdown", "scene.63_the_iron_hand", "scene.64_pass_through_shadow_and_flame", "scene.65_secrets_of_the_deep", "scene.66_the_first_tongue", "scene.67_the_shattered_mind", "scene.68_brotherhood_revealed", "scene.69_divergent_paths", "scene.71_spheres_truth", "scene.72_cosmic_teachers_arrive", "scene.73_flow_between_moments", "scene.74_stone_and_root", "scene.75_sunbound", "scene.76_anchor_points_of_time", "scene.77_lunar_inheritance", "scene.78_introducing_the_sage", "scene.79_the_queen_s_return", "scene.80_mages_awakening", "scene.81_the_whispers_between_worlds", "scene.82_mr_gpt_arrival", "scene.83_pyroclasts_burning_secrets", "scene.84_echoes_beneath_the_waves", "scene.85_earth_giants_and_diverging_paths", "scene.86_ancient_knowledge", "scene.87_sanctuary_to_storm", "scene.88_the_breath_of_life", "scene.89_shadows_of_umbrageous_fixed", "scene.90_the_white_mirror", "scene.91_echoes_of_the_culling_corrected", "scene.92_the_weight_of_memory", "scene.93_departure_and_determination", "scene.94_voices_between_worlds", "scene.95_chains_of_light", "scene.96_roots_of_change", "scene.97_violet_convergence", "scene.98_hearts_of_ash_and_fire", "scene.99_depths_of_memory"], "errors": [], "linked_at": "2026-03-03T18:28:25.723237Z", "scenes_registered": 101, "debug": {"chain": []}}(base) burdens@pop-os:~$
36:  "vault_id": "obsidianburdennov25",
324:"entity_type": "player",
342:"entity_type": "npc",
593:    entity_type = entity['type']
603:        'tags': [entity_type, entity['role']]
683:    "entity_type": "player",
701:    "entity_type": "npc",
859:    entity_type = entity['type']

./engain_upbge/engain_bge_bridge.py
238:            obj["vault_id"] = entity_id
239:            obj["entity_type"] = entity_data.get("type", "unknown")

./engain_upbge/Imports/files/engain_bge_bridge.py
42:        self.managed_objects = {}   # vault_id -> bge object name
134:        for vault_id, obj_name in self.managed_objects.items():
138:                entities[vault_id] = {
220:            obj["vault_id"] = entity_id
221:            obj["entity_type"] = entity_data.get("type", "unknown")

./godotsim/bridge_integration.py
71:def _infer_entity_type(entity: Dict[str, Any]) -> str:
156:        concept_type = _infer_entity_type(ent)

./godotsim/vault_linker.py
114:            "vault_id": manifest.get("vault_id", "unknown"),
135:            "vault_id": self.manifest.get("vault_id"),
378:            "vault_id": self.manifest.get("vault_id"),

./godotsim/vault_manager.py
21:    vault_id: Optional[str] = None
29:    vault_id: str
123:    if not m.get("vault_id"):
124:        return False, "missing_vault_id"
138:        self.state: Dict[str, Any] = {"active_vault_id": None, "vaults": {}}
146:                self.state = {"active_vault_id": None, "vaults": {}}
152:        self, vault_id: str, vault_root: str, manifest_path: str, manifest: Dict[str, Any]
155:        self.state["vaults"][vault_id] = {
165:    def set_active(self, vault_id: str) -> None:
166:        self.state["active_vault_id"] = vault_id
171:def parse_manifest_v1(vault_root: str, manifest_path: str, default_vault_id: str, root_dir: str = "") -> ManifestConfig:
173:    vault_id = data.get("vault_id") or default_vault_id
182:        output_dir = os.path.join(root_dir, ".vault_cache", vault_id)
186:    vault_mirror_dir = runtime.get("vault_mirror_dir", f".engain/build/{vault_id}")
190:        vault_id=vault_id,
326:                if "spec_version" in data or "vault_id" in data or "last_vault_fingerprint" in data:

./godotsim/spatial_skin_system.py
63:class Entity3D:

./godotsim/http_handlers.py
303:        active_id = self.runtime.snapshot.get("active_vault_id")
322:            cfg = parse_manifest_v1(vault_root, manifest_path, default_vault_id=active_id or "unknown", root_dir=ROOT_DIR)
395:        active_id = self.runtime.snapshot.get("active_vault_id")
404:            cfg = parse_manifest_v1(vault_root, manifest_path, default_vault_id=active_id, root_dir=ROOT_DIR)

./godotsim/patch_vault_endpoint.py
132:                        "vault_id": None,

./godotsim/sim_runtime.py.bak_interactive
109:    if not m.get("vault_id"):
110:        return False, "missing_vault_id"
147:    vault_id: Optional[str] = None
154:    vault_id: str
168:        self.state: Dict[str, Any] = {"active_vault_id": None, "vaults": {}}
177:                self.state = {"active_vault_id": None, "vaults": {}}
182:    def upsert_vault(self, vault_id: str, vault_root: str, manifest_path: str, manifest: Dict[str, Any]) -> None:
184:        self.state["vaults"][vault_id] = {
194:    def set_active(self, vault_id: str) -> None:
195:        self.state["active_vault_id"] = vault_id
278:def _parse_manifest_v1(vault_root: str, manifest_path: str, default_vault_id: str) -> ManifestConfig:
280:    vault_id = data.get("vault_id") or default_vault_id
289:        output_dir = os.path.join(ROOT_DIR, ".vault_cache", vault_id)
293:    vault_mirror_dir = runtime.get("vault_mirror_dir", f".engain/build/{vault_id}")
297:        vault_id=vault_id,
399:                if "spec_version" in data or "vault_id" in data or "last_vault_fingerprint" in data:
561:        active_id = self.vault_registry.state.get("active_vault_id")
564:            self.snapshot["active_vault_id"] = active_id
657:    def _create_entity_state(self, entity_id: str, entity_type: str, 
661:            "type": entity_type,
691:            entity_type = cmd.get("entity_type")
698:                entity_id, entity_type, pos_tuple,
708:                    print(f"✓ Spawned {entity_type} '{entity_id}' (Spatial3D)")
710:                    print(f"✓ Spawned {entity_type} '{entity_id}'")
712:                print(f"✓ Spawned {entity_type} '{entity_id}'")
1566:        vault_id = manifest["vault_id"]
1569:        self.runtime.vault_registry.upsert_vault(vault_id=vault_id, vault_root=vr, manifest_path=mp, manifest=manifest)
1571:            self.runtime.vault_registry.set_active(vault_id)
1576:        self.runtime.snapshot["vaults"][vault_id] = {
1582:            self.runtime.snapshot["active_vault_id"] = vault_id
1588:            "vault_id": vault_id,
1591:            "active_vault_id": self.runtime.snapshot.get("active_vault_id")
1773:        active_id = self.runtime.snapshot.get("active_vault_id")
1805:            cfg = _parse_manifest_v1(vault_root, manifest_path, default_vault_id=active_id or "unknown")
1921:                "vault_id": cfg.vault_id,
1943:        active_id = self.runtime.snapshot.get("active_vault_id")
1952:            cfg = _parse_manifest_v1(vault_root, manifest_path, default_vault_id=active_id)
./godotengain/engainos/core/zon_to_entities.py
38:CONCEPT_MAPPINGS: Dict[str, ConceptMapping] = {
47:        vault_id="guard_standard",
57:        vault_id="nephradi_common",
67:        vault_id="merchant_human",
77:        vault_id="player_hero",
151:    if concept in CONCEPT_MAPPINGS:
152:        return CONCEPT_MAPPINGS[concept]
155:    for known_concept, mapping in CONCEPT_MAPPINGS.items():
160:    return CONCEPT_MAPPINGS["unknown"]
170:    CONCEPT_MAPPINGS[mapping.zw_concept] = mapping

./avatar/godotengain/engainos/core/zon_to_entities.py
36:CONCEPT_MAPPINGS: Dict[str, ConceptMapping] = {
133:    if concept in CONCEPT_MAPPINGS:
134:        return CONCEPT_MAPPINGS[concept]
137:    for known_concept, mapping in CONCEPT_MAPPINGS.items():
142:    return CONCEPT_MAPPINGS["unknown"]
152:    CONCEPT_MAPPINGS[mapping.zw_concept] = mapping

(base) burdens@pop-os:~/burdens_of_a_forgotten_past/EngAIn/godotsim$ PID=$(curl -s http://localhost:8080/health | python3 -c 'import json,sys; print(json.load(sys.stdin)["pid"])')
echo "PID=$PID"
echo "CWD=$(readlink -f /proc/$PID/cwd)"
echo "CMD=$(tr '\0' ' ' < /proc/$PID/cmdline)"
ls -la "$(readlink -f /proc/$PID/cwd)/sim_runtime.py"
PID=772634
CWD=/home/burdens/burdens_of_a_forgotten_past/EngAIn/godotsim
CMD=python3 sim_runtime.py 
-rw-rw-r-- 1 burdens burdens 1173 Mar  2 10:22 /home/burdens/burdens_of_a_forgotten_past/EngAIn/godotsim/sim_runtime.py
(base) burdens@pop-os:~/burdens_of_a_forgotten_past/EngAIn/godotsim$ LIVE_SIM="$(readlink -f /proc/$(curl -s http://localhost:8080/health | python3 -c 'import json,sys; print(json.load(sys.stdin)["pid"])')/cwd)/sim_runtime.py"

rg -n "ENGAIN_PUMP_BEGIN|ENGAIN_PUMP_END" "$LIVE_SIM"
(base) burdens@pop-os:~/burdens_of_a_forgotten_past/EngAIn/godotsim$ # tick proof
for i in 1 2 3 4 5; do
  curl -s http://localhost:8080/snapshot \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("tick"))'
  sleep 0.5
done

# spawn proof
curl -s -X POST http://localhost:8080/command \
  -H "Content-Type: application/json" \
  -d '{"command":"spawn_entity","entity_id":"probe_01","pos":[0,0,0],"radius":0.5,"solid":true,"tags":["npc"]}' ; echo

curl -s http://localhost:8080/snapshot \
| python3 -c 'import json,sys; d=json.load(sys.stdin); p=d.get("payload", d); print("entities", len(p.get("entities", {})))'
0.0
0.0
0.0
0.0
0.0
{"type": "ack", "status": "queued", "command": "spawn_entity", "debug": {"chain": []}}
entities 0

p://localhost:8080/snapshot | python3 -c "
import json, sys
d = json.load(sys.stdin)
s = d.get('snapshot', d)
print('Top-level keys:', list(s.keys())[:15])
ents = s.get('entities', {})
print(f'Entities: {len(ents)}')
for eid in list(ents.keys())[:5]:
    e = ents[eid]
    print(f'  {eid}: pos={e.get(\"position\",\"?\")} type={e.get(\"type\",\"?\")}')
"
Top-level keys: ['protocol', 'version', 'epoch', 'tick', 'hash', 'timestamp', 'payload']
Entities: 0
(base) burdens@pop-os:~/burdens_of_a_forgotten_past/EngAIn/godotsim$ curl -s http://localhost:8080/snapshot | python3 -c "
import json, sys
d = json.load(sys.stdin)
p = d.get('payload', d)
print('Payload keys:', list(p.keys())[:20])
ents = p.get('entities', {})
print(f'Entities: {len(ents)}')
for eid in list(ents.keys())[:5]:
    e = ents[eid]
    print(f'  {eid}: pos={e.get(\"position\",\"?\")} type={e.get(\"type\",\"?\")}')
scene = p.get('scene', p.get('active_scene', {}))
if scene:
    print(f'Scene ID: {scene.get(\"scene_id\", \"?\")}')
    print(f'Scene entities: {len(scene.get(\"entities\", []))}')
"
Payload keys: ['scene_id', 'entities', 'spatial', 'perception', 'behavior', 'world', 'events', 'scene', 'scene_raw', 'bridge_entities', 'combat', 'inventory', 'dialogue']
Entities: 0
Scene ID: scene.04_the_convergence
Scene entities: 29
(base) burdens@pop-os:~/burdens_of_a_forgotten_past/EngAIn/godotsim$ curl -s http://localhost:8080/snapshot | python3 -c "
import json, sys
d = json.load(sys.stdin)
p = d.get('payload', d)
scene_ents = p.get('scene', {}).get('entities', [])
bridge_ents = p.get('bridge_entities', [])
print(f'scene.entities: {len(scene_ents)} (type: {type(scene_ents).__name__})')
print(f'bridge_entities: {len(bridge_ents)} (type: {type(bridge_ents).__name__})')
print()
print('--- First 3 scene entities ---')
for e in scene_ents[:3]:
    print(json.dumps(e, indent=2) if isinstance(e, dict) else e)
print()
print('--- First 3 bridge entities ---')
for e in bridge_ents[:3]:
    print(json.dumps(e, indent=2) if isinstance(e, dict) else e)
"
scene.entities: 29 (type: list)
bridge_entities: 29 (type: list)

--- First 3 scene entities ---
Senareth
Giant
Giants

--- First 3 bridge entities ---
{
  "entity_id": "Senareth",
  "zw_concept": "character",
  "ap_profile": "character_npc",
  "placeholder_mesh": "capsule",
  "skin_3d_id": null,
  "color": {
    "r": 0.2,
    "g": 0.6,
    "b": 1.0
  },
  "color_hex": "#3399ff",
  "transform": {
    "position": {
      "x": 17.5,
      "y": 0.0,
      "z": 0.0
    },
    "rotation": {
      "x": 0.0,
      "y": 0.0,
      "z": 0.0
    },
    "scale": {
      "x": 0.5,
      "y": 1.8,
      "z": 0.5
    }
  },
  "collision_role": "solid",
  "semantic_tags": [
    "character",
    "interactive"
  ],
  "kernel_bindings": {
    "profile": "character_npc"
  },
  "is_placeholder": true,
  "source_data": {
    "raw_concept": "character",
    "zon_id": "Senareth",
    "is_placeholder": true
  },
  "name": "Senareth",
  "inferred_type": "character"
}
{
  "entity_id": "Giant",
  "zw_concept": "giant",
  "ap_profile": "character_npc",
  "placeholder_mesh": "capsule",
  "skin_3d_id": null,
  "color": {
    "r": 0.6,
    "g": 0.4,
    "b": 0.2
  },
  "color_hex": "#996633",
  "transform": {
    "position": {
      "x": 17.39,
      "y": 0.0,
      "z": 1.96
    },
    "rotation": {
      "x": 0.0,
      "y": 0.0,
      "z": 0.0
    },
    "scale": {
      "x": 1.0,
      "y": 3.5,
      "z": 1.0
    }
  },
  "collision_role": "solid",
  "semantic_tags": [
    "character",
    "giant",
    "interactive"
  ],
  "kernel_bindings": {
    "profile": "character_npc"
  },
  "is_placeholder": true,
  "source_data": {
    "raw_concept": "giant",
    "zon_id": "Giant",
    "is_placeholder": true
  },
  "name": "Giant",
  "inferred_type": "giant"
}
{
  "entity_id": "Giants",
  "zw_concept": "giant",
  "ap_profile": "character_npc",
  "placeholder_mesh": "capsule",
  "skin_3d_id": null,
  "color": {
    "r": 0.6,
    "g": 0.4,
    "b": 0.2
  },
  "color_hex": "#996633",
  "transform": {
    "position": {
      "x": 17.06,
      "y": 0.0,
      "z": 3.89
    },
    "rotation": {
      "x": 0.0,
      "y": 0.0,
      "z": 0.0
    },
    "scale": {
      "x": 1.0,
      "y": 3.5,
      "z": 1.0
    }
  },
  "collision_role": "solid",
  "semantic_tags": [
    "character",
    "giant",
    "interactive"
  ],
  "kernel_bindings": {
    "profile": "character_npc"
  },
  "is_placeholder": true,
  "source_data": {
    "raw_concept": "giant",
    "zon_id": "Giants",
    "is_placeholder": true
  },
  "name": "Giants",
  "inferred_type": "giant"
}
(base) burdens@pop-os:~/burdens_of_a_forgotten_past/EngAIn/godotsim$ 
