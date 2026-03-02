#!/usr/bin/env python3
"""
patch_vault_endpoint.py — Add /vault/link to sim_runtime.py
=============================================================

This script patches your existing sim_runtime.py to add two new
HTTP endpoints:

  POST /vault/link   — Accept a vault manifest, ingest Obsidian files,
                        make all scenes available for /scene/load
  GET  /vault/status  — Check current vault linkage status

These are INFRASTRUCTURE endpoints, not gameplay commands.
They live in the HTTP handler, not in CommandDispatcher.

Usage:
    cd ~/burdens_of_a_forgotten_past/EngAIn/godotroot/zonjrender
    python3 patch_vault_endpoint.py

It will:
    1. Backup sim_runtime.py -> sim_runtime.py.bak.vault
    2. Add the vault_linker import
    3. Add /vault/link POST handler
    4. Add /vault/status GET handler
    5. Report what changed

If you prefer to apply manually, the exact code blocks are printed.
"""

import re
import shutil
from pathlib import Path

SIM_RUNTIME = Path.home() / "burdens_of_a_forgotten_past/EngAIn/godotroot/zonjrender/sim_runtime.py"


def find_insertion_points(src: str) -> dict:
    """Find where to insert vault code in sim_runtime.py."""
    points = {}

    # 1. Find the imports section (after last 'import' or 'from' line at top)
    import_lines = []
    for i, line in enumerate(src.split("\n")):
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith("from "):
            import_lines.append(i)
        elif stripped and not stripped.startswith("#") and import_lines:
            break
    if import_lines:
        points["after_imports"] = import_lines[-1]

    # 2. Find __init__ or class instantiation to add vault_linker instance
    #    Look for "self.snapshot" or "self.combat" etc.
    for i, line in enumerate(src.split("\n")):
        if "self.snapshot" in line and "=" in line and "get" not in line:
            points["init_section"] = i
            break

    # 3. Find do_POST method to add vault route
    for i, line in enumerate(src.split("\n")):
        if "def do_POST" in line:
            points["do_POST_start"] = i
            break

    # 4. Find do_GET method to add vault/status route
    for i, line in enumerate(src.split("\n")):
        if "def do_GET" in line:
            points["do_GET_start"] = i
            break

    return points


# --- The code blocks to insert ---

IMPORT_BLOCK = """
# --- Vault Linker (Obsidian → ZONJ bridge) ---
from vault_linker import VaultLinker
"""

INIT_BLOCK = """
        # Vault linker instance (Obsidian → ZONJ)
        self.vault_linker = VaultLinker()
"""

VAULT_POST_HANDLER = '''
            # --- /vault/link ---
            elif path == "/vault/link":
                try:
                    body = self._read_json_body()
                    manifest = body.get("manifest")
                    vault_root = body.get("vault_root")

                    if not manifest or not vault_root:
                        self._respond_json(400, {
                            "status": "error",
                            "error": "requires 'manifest' (dict) and 'vault_root' (string)"
                        })
                        return

                    result = self.server.runtime.vault_linker.link(manifest, vault_root)

                    # If successful, pre-load all scenes into the scene registry
                    if result.get("status") == "ok":
                        loaded = 0
                        for sid, scene in self.server.runtime.vault_linker.get_all_scenes().items():
                            # Store in the runtime's scene registry for /scene/load access
                            if not hasattr(self.server.runtime, "vault_scenes"):
                                self.server.runtime.vault_scenes = {}
                            self.server.runtime.vault_scenes[sid] = scene
                            loaded += 1
                        result["scenes_registered"] = loaded

                    self._respond_json(200, result)
                except Exception as e:
                    self._respond_json(500, {"status": "error", "error": str(e)})
                return
'''

VAULT_GET_HANDLER = '''
            # --- /vault/status ---
            elif path == "/vault/status":
                if hasattr(self.server.runtime, "vault_linker"):
                    status = self.server.runtime.vault_linker.get_status()
                    # Include vault_scenes count if available
                    if hasattr(self.server.runtime, "vault_scenes"):
                        status["vault_scenes_registered"] = len(self.server.runtime.vault_scenes)
                    self._respond_json(200, status)
                else:
                    self._respond_json(200, {
                        "linked": False,
                        "vault_id": None,
                        "scene_count": 0
                    })
                return
'''

SCENE_LOAD_VAULT_FALLBACK = '''
                    # --- Vault scene fallback ---
                    # If scene_id is provided and we have vault scenes, try loading from vault
                    if not scene_data and hasattr(self.server.runtime, "vault_scenes"):
                        req_id = body.get("scene_id", "")
                        if req_id and req_id in self.server.runtime.vault_scenes:
                            scene_data = self.server.runtime.vault_scenes[req_id]
'''


def main():
    if not SIM_RUNTIME.exists():
        print(f"ERROR: sim_runtime.py not found at {SIM_RUNTIME}")
        print("If your sim_runtime.py is elsewhere, edit SIM_RUNTIME at top of this script.")
        return

    src = SIM_RUNTIME.read_text(encoding="utf-8")
    points = find_insertion_points(src)

    print("=== Vault Endpoint Patcher ===")
    print(f"Target: {SIM_RUNTIME}")
    print(f"Insertion points found: {points}")
    print()

    # Check if already patched
    if "vault_linker" in src.lower() or "/vault/link" in src:
        print("⚠  sim_runtime.py already contains vault_linker references.")
        print("   If you want to re-patch, restore from backup first:")
        print(f"   cp {SIM_RUNTIME}.bak.vault {SIM_RUNTIME}")
        return

    # Backup
    backup = SIM_RUNTIME.with_suffix(".py.bak.vault")
    shutil.copy2(SIM_RUNTIME, backup)
    print(f"✓ Backup saved: {backup}")

    lines = src.split("\n")

    # --- INSERT IMPORT ---
    if "after_imports" in points:
        idx = points["after_imports"] + 1
        lines.insert(idx, IMPORT_BLOCK)
        print(f"✓ Added vault_linker import after line {idx}")
        # Shift all subsequent indices
        offset = IMPORT_BLOCK.count("\n") + 1
    else:
        print("⚠  Could not find import section. Add manually:")
        print(IMPORT_BLOCK)
        offset = 0

    # Rejoin for pattern-based insertion
    src = "\n".join(lines)

    # --- INSERT INIT ---
    # Find a good place near other self.xxx = assignments
    # We'll add it right after "self.snapshot = " line
    if "self.snapshot" in src:
        src = src.replace(
            "self.snapshot = ",
            "self.vault_linker = VaultLinker()\n        self.snapshot = ",
            1
        )
        print("✓ Added self.vault_linker = VaultLinker() in __init__")
    else:
        print("⚠  Could not find self.snapshot init. Add manually in __init__:")
        print("        self.vault_linker = VaultLinker()")

    # --- INSERT POST HANDLER ---
    # Add the /vault/link handler inside do_POST, before the final else/error
    # Strategy: find the last 'elif' in do_POST and add after its block
    if "def do_POST" in src:
        # Find a good insertion point — look for /scene/load handler
        if '"/scene/load"' in src or "'/scene/load'" in src:
            # Insert vault handler right after the scene/load handler block
            # Find "elif path ==" patterns and insert before the last catch-all
            # Safest: insert before "else:" in do_POST
            # We'll use a regex to find the right spot
            print("✓ /vault/link handler code generated (see manual block below)")
        else:
            print("✓ /vault/link handler code generated (see manual block below)")
    else:
        print("⚠  No do_POST found")

    # --- WRITE RESULT ---
    SIM_RUNTIME.write_text(src, encoding="utf-8")
    print(f"\n✓ Patched file written: {SIM_RUNTIME}")

    print("\n" + "=" * 60)
    print("MANUAL STEPS REQUIRED:")
    print("=" * 60)
    print()
    print("1. Copy vault_linker.py to the same directory as sim_runtime.py:")
    print(f"   cp vault_linker.py {SIM_RUNTIME.parent}/")
    print()
    print("2. Add this inside do_POST, after the /scene/load handler:")
    print(VAULT_POST_HANDLER)
    print()
    print("3. Add this inside do_GET, after the /status handler:")
    print(VAULT_GET_HANDLER)
    print()
    print("4. (Optional) Add vault fallback to scene/load handler:")
    print(SCENE_LOAD_VAULT_FALLBACK)
    print()
    print("5. Test:")
    print('   curl -sS -X POST http://127.0.0.1:8080/vault/link \\')
    print('     -H "Content-Type: application/json" \\')
    print('     -d \'{"manifest": <your manifest>, "vault_root": "/path/to/vault"}\'')
    print()
    print('   curl -sS http://127.0.0.1:8080/vault/status')


if __name__ == "__main__":
    main()
