#!/usr/bin/env python3
"""
launch_bridge.py - Start both godot_adapter and scene_server

Launches:
1. Scene HTTP server (port 8765) in background thread
2. Godot adapter (stdin/stdout bridge) in main thread
"""

import sys
import threading
from scene_server import start_scene_server

def run_scene_server():
    """Run scene server in background thread"""
    try:
        start_scene_server(port=8765)
    except Exception as e:
        print(f"[SceneServer] Error: {e}", file=sys.stderr)

if __name__ == '__main__':
    # Start scene server in background thread
    server_thread = threading.Thread(target=run_scene_server, daemon=True)
    server_thread.start()
    
    print("[LaunchBridge] Scene server started on port 8765", file=sys.stderr)
    
    # Import and run main adapter in foreground
    from godot_adapter import GodotAdapter
    from pathlib import Path
    
    adapter = GodotAdapter()
    if len(sys.argv) > 1:
        adapter.initialize(sys.argv[1])
    else:
        # Default to First Contact
        scene_path = Path.home() / "Downloads/EngAIn/mettaext/game_scenes/03_Fist_contact.json"
        if scene_path.exists():
            adapter.initialize(scene_path)
    
    adapter.run_loop()
