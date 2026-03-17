# UPBGE .blend Setup Guide for EngAIn

## Prerequisites
- UPBGE 0.50 installed
- sim_runtime.py running on localhost:8080
- Both .py scripts from this kit next to your .blend file

## Folder Structure
    engain_upbge/
        engain_upbge.blend
        engain_controller.py
        engain_bge_bridge.py

## Step 1: Create EngAInController
1. Add > Empty > Plain Axes
2. Rename to exactly: EngAInController

## Step 2: Logic Bricks on EngAInController
1. Add Sensor: Always (Tap: UNCHECKED, True Level: ON)
2. Add Controller: Python (Script mode, NOT Module)
3. Script: engain_controller.py
4. Connect sensor output to controller input

## Step 3: Create EntityTemplate
1. Add > Mesh > Cube
2. Rename to exactly: EntityTemplate
3. Scale to 0.3 (S -> 0.3 -> Enter)
4. CRITICAL: Keep in main Scene Collection (NOT excluded/hidden)
5. Move far away: G -> Z -> -100 -> Enter

Why main collection? UPBGE scene.addObject() only sees active collections.
If excluded, you get: requested name EntityTemplate did not match any KX_GameObject

## Step 4: Test WITHOUT sim_runtime
1. Save (Ctrl+S)
2. Press P
3. Terminal should show:
   EngAIn UPBGE Client Starting
   EntityTemplate: FOUND
   Bridge: READY
   Connection failed (expected - sim_runtime not running)
4. Press ESC

## Step 5: Connect to sim_runtime
1. Terminal 1: cd ~/burdens_of_a_forgotten_past/EngAIn/godotsim && python3 sim_runtime.py
2. Wait for Server running on http://localhost:8080
3. In UPBGE: Press P
4. Should see: [EngAIn Bridge] Connected to sim_runtime!

## Step 6: Load a scene
In terminal 2:
    curl -X POST http://localhost:8080/scene/load -H Content-Type:application/json -d {"scene_id":"scene.04_the_convergence"}

Entities spawn as colored cubes:
  Blue = player, Green = NPC, Red = hostile, Gold = item, Gray = unknown

## Troubleshooting

EntityTemplate did not match:
  -> Move it back to main Scene Collection in Outliner

Cannot import engain_bge_bridge:
  -> Both .py files must be in same folder as .blend

Connection refused keeps repeating:
  -> Start sim_runtime.py first

Objects spawn but invisible:
  -> Check camera angle, verify EntityTemplate has a mesh

## Whats Next

Phase 2: Add keyboard sensors (L=load scene, D=debug, Space=look command)
Phase 3: Stop game, edit spawned objects in Blender, restart, bridge syncs changes
Phase 4: Run Godot AND UPBGE simultaneously - same sim_runtime, two views
