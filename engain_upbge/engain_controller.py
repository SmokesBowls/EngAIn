"""
engain_controller.py - UPBGE Logic Brick Entry Point
=====================================================
Called by a Logic Brick (Script mode) every tick.
Initializes the EngAIn bridge, then calls tick() each frame.

Logic Brick Setup:
    Object: EngAInController (Empty)
    Sensor: Always (Tap: OFF = runs every frame)
    Controller: Python (Script mode) -> engain_controller.py
    Actuator: (none needed)
"""

from bge import logic
import os
import sys
import time

controller = logic.getCurrentController()
owner = controller.owner
scene = logic.getCurrentScene()

# Ensure .blend directory is importable (engain_bge_bridge.py lives next to blend)
blend_dir = logic.expandPath("//")
if blend_dir and os.path.isdir(blend_dir) and blend_dir not in sys.path:
    sys.path.insert(0, blend_dir)

# Init state (allow retry with backoff if something fails)
if not hasattr(logic, "engain_bridge"):
    logic.engain_bridge = None
    logic.engain_tick_count = 0
    logic.engain_init_last_try = 0.0
    logic.engain_init_retry_secs = 5.0

if logic.engain_bridge is None:
    now = time.time()
    if now - logic.engain_init_last_try >= logic.engain_init_retry_secs:
        logic.engain_init_last_try = now

        print("")
        print("=" * 50)
        print("  EngAIn UPBGE Client Starting")
        print("=" * 50)
        print(f"  Scene: {scene.name}")
        print(f"  Objects: {len(scene.objects)}")
        print(f"  Owner: {owner.name}")

        try:
            from engain_bge_bridge import EngAInBridge

            ENGAIN_URL = "http://localhost:8080"
            POLL_INTERVAL = 0.5

            logic.engain_bridge = EngAInBridge(
                base_url=ENGAIN_URL,
                poll_interval=POLL_INTERVAL,
            )

            if "EntityTemplate" in scene.objects:
                print("  EntityTemplate: FOUND")
            else:
                print("  EntityTemplate: NOT FOUND - spawning will fail!")
                print("  Create a Cube named 'EntityTemplate' in the main Scene Collection")

            print("  Bridge: READY")
            print("=" * 50)
            print("")

        except Exception as e:
            logic.engain_bridge = None
            print(f"  Bridge init failed (will retry): {e}")
            print("=" * 50)
            print("")

# Tick
if logic.engain_bridge is not None:
    logic.engain_bridge.tick()
    logic.engain_tick_count += 1

    if logic.engain_tick_count % 300 == 0:
        logic.engain_bridge.debug_print()
