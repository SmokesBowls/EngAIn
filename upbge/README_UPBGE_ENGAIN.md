 EngAIn → UPBGE bridge (single-folder drop-in)

Drop these files next to `one_path.blend` in:

`/home/burdens/burdens_of_a_forgotten_past/EngAIn/upbge`

This gives you a UPBGE Python Component (`EngAInBridge`) that:
- polls `GET http://127.0.0.1:8080/health`
- optionally sends `POST /cmd` when you press **F5**

## Files (all in the same folder)

- `one_path.blend`
- `engain_http_client.py`
- `engain_upbge_bridge.py`
- `engain_upbge_config.json`
- `run_upbge_game.sh`
- `README_UPBGE_ENGAIN.md`

## Wire it into `one_path.blend`

1) Add a Text object (recommended)
- Add > Text
- Name: `ENGAIN_STATUS_TEXT`
- Put it where your camera can see it

2) Add an Empty for the bridge
- Add > Empty > Plain Axes
- Name: `ENGAIN_BRIDGE`

3) Add the Python Component
- Select `ENGAIN_BRIDGE`
- Object Properties > Components
- Add Component
- Module: `engain_upbge_bridge`
- Class: `EngAInBridge`

Leave defaults for now.

## Run

Terminal launch:

```bash
cd /home/burdens/burdens_of_a_forgotten_past/EngAIn/upbge
chmod +x run_upbge_game.sh
./run_upbge_game.sh
```

In UPBGE, press **P** in the 3D viewport to start the game.

## What you should see

- If EngAIn is running: `ENGAIN OK ...`
- If not: `ENGAIN OFFLINE (...)`

Press **F5** to attempt a ping to `/cmd`. If `/cmd` returns 404, the bridge disables further pings to avoid spam.

## Next step

Once this is green, we extend the bridge to:
- pull a scene payload (ZONJ/ZW) from EngAIn
- spawn placeholder objects into the UPBGE scene
- push player actions back to EngAIn as events
