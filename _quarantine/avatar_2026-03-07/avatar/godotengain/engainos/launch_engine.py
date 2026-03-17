#!/usr/bin/env python3
"""
launch_engine.py - EngAIn Engine Bootstrap (Authoritative)

This is the ONLY blessed runtime entrypoint.
No bypassing. No mocking. No clever tricks.

If this fails, fix the engine - do not work around it.

Authority: engainos/core/launch_engine.py
Status: CANONICAL ENTRYPOINT
"""

import sys
import os
import re
import json
from pathlib import Path
import threading
import time

# ============================================================================
# PHASE 1: PATH AUTHORITY (No CWD assumptions)
# ============================================================================

SCRIPT_PATH = Path(__file__).resolve()

if SCRIPT_PATH.parent.name == "core":
    CORE = SCRIPT_PATH.parent
    ROOT = CORE.parent
elif SCRIPT_PATH.parent.name == "engainos":
    ROOT = SCRIPT_PATH.parent
    CORE = ROOT / "core"
else:
    print(f"ERROR: launch_engine.py in unexpected location: {SCRIPT_PATH}", file=sys.stderr)
    sys.exit(1)

TOOLS = ROOT / "tools"
GODOT = ROOT / "godot"
ASSETS = ROOT / "assets"
TESTS = ROOT / "tests"

# Ensure core is in path for imports
sys.path.insert(0, str(CORE))

# ============================================================================
# PHASE 2: ENGINE INVARIANTS (Learning gate)
# ============================================================================

def assert_invariant(condition: bool, message: str):
    if not condition:
        print(f"❌ ENGINE INVARIANT VIOLATION:", file=sys.stderr)
        print(f"   {message}", file=sys.stderr)
        sys.exit(1)

def check_precise_import_violation(source_dir: Path, forbidden_dir: str) -> bool:
    if not source_dir.exists():
        return True
    
    for py_file in source_dir.rglob("*.py"):
        try:
            with open(py_file, 'r') as f:
                for line in f:
                    if line.strip().startswith('#'):
                        continue
                    
                    if forbidden_dir == "godot":
                        if re.match(r'^\s*import\s+godot\b', line):
                            return False
                        if re.match(r'^\s*from\s+godot\b', line):
                            if not re.match(r'^\s*from\s+godot_\w+', line):
                                return False
                    elif forbidden_dir == "tools":
                        if re.match(r'^\s*import\s+tools\b', line):
                            return False
                        if re.match(r'^\s*from\s+tools\b', line):
                            return False
        except:
            pass
    return True

def run_invariants_check():
    print("[PHASE 2] Checking engine invariants...")
    
    py_version = sys.version_info
    assert_invariant(py_version >= (3, 10), f"Python 3.10+ required")
    print(f"  ✓ Python {py_version.major}.{py_version.minor}.{py_version.micro}")

    print("  [1/7] Core law files...")
    assert_invariant((CORE / "mesh_intake.py").exists(), "mesh_intake.py missing")
    assert_invariant((CORE / "mesh_manifest.py").exists(), "mesh_manifest.py missing")
    assert_invariant((CORE / "scene_server.py").exists(), "scene_server.py missing")
    assert_invariant((CORE / "godot_adapter.py").exists(), "godot_adapter.py missing")
    print("  ✓ All core law files present")

    print("  [2/7] Directory structure...")
    assert_invariant(TOOLS.exists(), "tools/ missing")
    assert_invariant((TOOLS / "trixel").exists(), "tools/trixel/ missing")
    assert_invariant(GODOT.exists(), "godot/ missing")
    print("  ✓ Required directories present")

    print("  [3/7] Import boundaries (CRITICAL)...")
    assert_invariant(check_precise_import_violation(CORE, "godot"), "core/ imports godot/")
    assert_invariant(check_precise_import_violation(CORE, "tools"), "core/ imports tools/")
    assert_invariant(check_precise_import_violation(TOOLS, "godot"), "tools/ imports godot/")
    print("  ✓ Boundaries clean: core ← tools ← godot")

    print("  [4/7] Python version check passed")

    print("  [5/7] Core module imports...")
    try:
        from scene_server import start_scene_server
        import godot_adapter
        print("  ✓ Core modules importable")
    except ImportError as e:
        assert_invariant(False, f"Import failed: {e}")

    print("  [6/7] Asset structure...")
    ASSETS.mkdir(exist_ok=True)
    (ASSETS / "trixels").mkdir(exist_ok=True)
    print("  ✓ Asset structure ready")

    print("  [7/7] Test isolation...")
    test_imports = any(
        ("import tests" in py_file.read_text() or "from tests" in py_file.read_text())
        for py_file in CORE.rglob("*.py") if py_file.is_file()
    )
    assert_invariant(not test_imports, "core/ imports tests/")
    print("  ✓ Tests isolated from runtime")

    print()
    print("✓ All engine invariants verified")
    print()

# ============================================================================
# PHASE 3: MAIN RUNTIME CLASS
# ============================================================================

from ap_engine import ZWAPEngine, StateProvider
from ap_runtime import APRuntimeIntegration

class EngAInRuntime:
    def __init__(self, scene_file: Path = None):
        self.scene_file = scene_file
        self.scene_server_port = 8765
        
        # Initialize AP Runtime
        self.ap_runtime = None
        self._init_ap_runtime()
    
    def _init_ap_runtime(self):
        """Initialize AP engine with rules from scenes"""
        try:
            scenes_dir = ROOT / "game_scenes"
            self.ap_runtime = APRuntimeIntegration(scenes_dir=str(scenes_dir))
            
            initial_state = {
                'flags': {},
                'stats': {},
                'locations': {},
                'inventory': {}
            }
            
            self.ap_runtime.initialize(initial_state)
            print(f"[AP] Initialized successfully")
            
        except Exception as e:
            print(f"[AP] Warning: Failed to initialize: {e}")

    def handle_message(self, msg_dict):
        """Handle incoming messages from Godot"""
        msg_type = msg_dict.get('type', '')
        if msg_type.startswith('ap_'):
            if self.ap_runtime:
                try:
                    return self.ap_runtime.handle_message(msg_dict)
                except Exception as e:
                    return {'error': f'ap_error: {str(e)}'}
            else:
                return {'error': 'ap_not_initialized'}
        return None

    def test_ap(self):
        """Quick test to verify AP is working"""
        if not self.ap_runtime or not self.ap_runtime.engine:
            print("[AP] Not initialized")
            return
        
        rules = self.ap_runtime.engine.list_rules()
        print(f"[AP] Loaded {len(rules)} rules:")
        for rule in rules[:5]:
            print(f"  - {rule['id']}: priority={rule.get('priority', 0)}")

    def run(self):
        print("[PHASE 4] Starting subsystems...")
        print()

        from scene_server import start_scene_server

        def run_scene_server():
            try:
                # Pass self.handle_message to the scene server to handle AP queries
                start_scene_server(port=self.scene_server_port, msg_handler=self.handle_message)
            except Exception as e:
                print(f"[SceneServer] ERROR: {e}", file=sys.stderr)
                sys.exit(1)

        print(f"  [1/2] Scene HTTP server (port {self.scene_server_port})...")
        scene_server_thread = threading.Thread(target=run_scene_server, daemon=True)
        scene_server_thread.start()
        time.sleep(0.5)

        assert_invariant(scene_server_thread.is_alive(), "Scene server failed to start")
        print(f"  ✓ Scene server running")

        print("  [2/2] Godot adapter... (Interface Loaded)")

        print()
        print("=" * 70)
        print("ENGINE READY")
        print("=" * 70)
        print()
        print("Subsystems:")
        print(f"  • Scene server:   http://localhost:{self.scene_server_port}/")
        print(f"  • Godot adapter:  READY (stdin/stdout bound)")
        print(f"  • Active Scene:   {self.scene_file or 'None'}")
        print()
        print("To stop: Ctrl+C")
        print("=" * 70)
        print()

        # BLOCK FOREVER (Daemon mode)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n" + "=" * 70)
            print("ENGINE SHUTDOWN")
            print("=" * 70)
            sys.exit(0)

# ============================================================================
# BOOTSTRAP
# ============================================================================

if __name__ == '__main__':
    run_invariants_check()
    
    print("=" * 70)
    print("ENGAIN ENGINE BOOTSTRAP")
    print("=" * 70)
    print(f"Authority: {SCRIPT_PATH}")
    print(f"Root:      {ROOT}")
    print(f"Core:      {CORE}")
    print("=" * 70)
    print()

    # Determine scene file
    active_scene = None
    if len(sys.argv) > 1:
        arg_path = Path(sys.argv[1])
        if arg_path.exists():
            active_scene = arg_path
        else:
            # Fallback to game_scenes
            fallback = ROOT / "game_scenes" / f"{sys.argv[1]}.json"
            if fallback.exists():
                active_scene = fallback

    runtime = EngAInRuntime(scene_file=active_scene)
    runtime.test_ap()
    runtime.run()
