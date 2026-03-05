"""
engain_controller.py - UPBGE Logic Brick Entry Point
=====================================================
Called by a Logic Brick (Script mode) every tick.
Initializes the EngAIn bridge once, then calls tick() each frame.

Logic Brick Setup:
    Object: EngAInController (Empty)
    Sensor: Always (Tap: OFF = runs every frame)
    Controller: Python (Script mode) -> engain_controller.py
    Actuator: (none needed)

IMPORTANT: Use Script mode, NOT Module mode.
           Module mode has known issues in UPBGE 0.50.
"""

from bge import logic

controller = logic.getCurrentController()
owner = controller.owner
scene = logic.getCurrentScene()

# === First-time initialization ===
if not hasattr(logic, 'engain_initialized'):
    print("")
    print("=" * 50)
    print("  EngAIn UPBGE Client Starting")
    print("=" * 50)
    print(f"  Scene: {scene.name}")
    print(f"  Objects: {len(scene.objects)}")
    print(f"  Owner: {owner.name}")

    try:
        from engain_bge_bridge import EngAInBridge

        # --- CONFIGURATION ---
        ENGAIN_URL = "http://localhost:8080"
        POLL_INTERVAL = 0.5  # seconds between HTTP polls
        # ---------------------

        logic.engain_bridge = EngAInBridge(
            base_url=ENGAIN_URL,
            poll_interval=POLL_INTERVAL,
        )
        logic.engain_initialized = True
        logic.engain_tick_count = 0

        # Verify EntityTemplate exists
        if "EntityTemplate" in scene.objects:
            print("  EntityTemplate: FOUND")
        else:
            print("  EntityTemplate: NOT FOUND - spawning will fail!")
            print("  Create a Cube named 'EntityTemplate' in main collection")

        print("  Bridge: READY")
        print("=" * 50)
        print("")

    except ImportError as e:
        print(f"  FATAL: Cannot import engain_bge_bridge: {e}")
        print(f"  Make sure engain_bge_bridge.py is next to your .blend file")
        logic.engain_initialized = False
        logic.engain_bridge = None

    except Exception as e:
        print(f"  FATAL: Bridge init failed: {e}")
        logic.engain_initialized = False
        logic.engain_bridge = None

# === Every-frame tick ===
if getattr(logic, 'engain_initialized', False) and logic.engain_bridge:
    logic.engain_bridge.tick()
    logic.engain_tick_count += 1

    # Debug output every ~5 seconds (300 ticks at 60fps)
    if logic.engain_tick_count % 300 == 0:
        logic.engain_bridge.debug_print()
