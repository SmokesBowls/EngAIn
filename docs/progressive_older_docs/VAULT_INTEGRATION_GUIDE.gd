# VAULT INTEGRATION GUIDE
# =======================
# How to connect VaultClient.gd to your existing zonjrender project.
#
# There are 4 steps. None of them change existing files — you're only
# ADDING a new autoload and a few lines to boot.gd.

# ============================================================
# STEP 1: Copy files to your project
# ============================================================
#
# From this download, copy these files:
#
#   vault_linker.py   → ~/burdens_of_a_forgotten_past/EngAIn/godotroot/zonjrender/
#   VaultClient.gd    → ~/burdens_of_a_forgotten_past/EngAIn/godotroot/zonjrender/autoload/
#
# The vault_linker.py sits next to sim_runtime.py (Python side).
# The VaultClient.gd sits in autoload/ next to SimClient.gd and SceneClient.gd.

# ============================================================
# STEP 2: Register VaultClient as Godot autoload
# ============================================================
#
# In Godot: Project → Project Settings → Autoload tab
#
#   Path:   res://autoload/VaultClient.gd
#   Name:   VaultClient
#   Enable: ✓
#
# Set the export vars in the Inspector (or leave defaults):
#   runtime_base:          http://127.0.0.1:8080
#   default_vault_root:    /home/burdens/obsidian/obsidianburdenNov25
#   default_manifest_path: vault.manifest.json

# ============================================================
# STEP 3: Add vault wiring to boot.gd
# ============================================================
#
# In scripts/boot.gd, add these lines:
#
# --- At the top, with your other @onready vars ---

#   @onready var VaultClient = get_node_or_null("/root/VaultClient")

# --- In _ready(), after _wire_ui() ---

#   if VaultClient:
#       VaultClient.vault_linked.connect(_on_vault_linked)
#       VaultClient.vault_failed.connect(_on_vault_failed)
#       # Auto-link on startup (optional — remove if you want manual linking)
#       VaultClient.link_default()

# --- Add these callback functions ---

# func _on_vault_linked(result: Dictionary) -> void:
#     var count: int = int(result.get("scenes_extracted", 0))
#     _log_ui("[vault] LINKED: %d scenes from %s" % [
#         count, str(result.get("vault_id", "?"))
#     ])
#     # Optionally auto-load first scene
#     var ids: Array = result.get("scene_ids", [])
#     if ids.size() > 0 and SimClient:
#         _log_ui("[vault] Auto-loading first scene: %s" % str(ids[0]))
#         SimClient.scene_load({"scene_id": str(ids[0])})

# func _on_vault_failed(error: String) -> void:
#     _log_ui("[vault] FAIL: %s" % error)

# ============================================================
# STEP 4: Patch sim_runtime.py (Python side)
# ============================================================
#
# You need to add the /vault/link endpoint to sim_runtime.py.
# See patch_vault_endpoint.py for the automated patcher,
# or manually add these code blocks:
#
# A) Import at top of sim_runtime.py:
#
#     from vault_linker import VaultLinker
#
# B) In __init__ (where self.snapshot is created):
#
#     self.vault_linker = VaultLinker()
#     self.vault_scenes = {}
#
# C) In do_POST, add this elif block (after /scene/load):
#
#     elif path == "/vault/link":
#         body = self._read_json_body()
#         manifest = body.get("manifest")
#         vault_root = body.get("vault_root")
#         if not manifest or not vault_root:
#             self._respond_json(400, {"status":"error","error":"need manifest + vault_root"})
#             return
#         result = self.server.runtime.vault_linker.link(manifest, vault_root)
#         if result.get("status") == "ok":
#             loaded = 0
#             for sid, scene in self.server.runtime.vault_linker.get_all_scenes().items():
#                 self.server.runtime.vault_scenes[sid] = scene
#                 loaded += 1
#             result["scenes_registered"] = loaded
#         self._respond_json(200, result)
#         return
#
# D) In do_GET, add this elif block (after /status):
#
#     elif path == "/vault/status":
#         status = self.server.runtime.vault_linker.get_status()
#         status["vault_scenes_registered"] = len(getattr(self.server.runtime, "vault_scenes", {}))
#         self._respond_json(200, status)
#         return
#
# E) OPTIONAL: In the /scene/load handler, add vault fallback:
#    After the normal scene loading logic, before returning "unknown":
#
#     if not scene_data and hasattr(self.server.runtime, "vault_scenes"):
#         req_id = body.get("scene_id", "")
#         if req_id in self.server.runtime.vault_scenes:
#             scene_data = self.server.runtime.vault_scenes[req_id]

# ============================================================
# STEP 5: TEST
# ============================================================
#
# Terminal test (before Godot):
#   cd ~/burdens_of_a_forgotten_past/EngAIn/godotroot/zonjrender
#   python3 sim_runtime.py &
#   bash test_vault_link.sh /home/burdens/obsidian/obsidianburdenNov25
#
# Godot test:
#   Press F5. Watch the Output panel for:
#     [VaultClient] LINKED: vault_id=book01_garden_genesis scenes=XX
#     [vault] LINKED: XX scenes from book01_garden_genesis
#
# Then try a search in the UI — your Obsidian content should appear.

# ============================================================
# ARCHITECTURE SUMMARY
# ============================================================
#
#   Obsidian Vault (markdown files)
#         |
#         | vault.manifest.json tells sim_runtime WHERE to look
#         v
#   VaultClient.gd  --HTTP POST-->  /vault/link  (sim_runtime.py)
#         |                              |
#         |                              v
#         |                     vault_linker.py
#         |                     (reads .md → ZONJ scene dicts)
#         |                              |
#         |                              v
#         |                     vault_scenes{} registry
#         |                              |
#         v                              v
#   vault_linked signal        /scene/load can now serve vault scenes
#         |                              |
#         v                              v
#   boot.gd auto-loads        SimClient → look → real narrative content
#   first scene
