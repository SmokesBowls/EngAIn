#!/usr/bin/env python3
import subprocess
import sys
import time
from pathlib import Path
import json

ENGAIN_ROOT = Path("/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn")
MANIFEST_PATH = ENGAIN_ROOT / "manifests/engain_manifest.json"
RUNTIME_URL = "http://127.0.0.1:8080"

if not MANIFEST_PATH.exists():
    print(f"[FAIL] Missing central manifest: {MANIFEST_PATH}")
    sys.exit(1)

manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

active_vault_id = manifest.get("active", {}).get("vault")
VAULT_PATH = Path(manifest["vaults"][active_vault_id]["root"])

active_scene_lib_id = manifest.get("active", {}).get("scene_library")
SCENE_LIBRARY_ROOT = Path(manifest["scene_libraries"][active_scene_lib_id]["root"])
SCENE_INDEX_PATH = Path(manifest["scene_libraries"][active_scene_lib_id]["index"])

INGEST_OUT = SCENE_LIBRARY_ROOT


def run(cmd, cwd=None, allow_failure=False):
    print(f"[RUN] {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd)
    if result.returncode != 0 and not allow_failure:
        print(f"[FAIL] Command failed: {' '.join(cmd)}")
        sys.exit(1)
    return result.returncode


def ensure_stack():
    print("\n=== STEP 1: Ensure runtime stack ===")
    run(["./start_stack.fish"], cwd=ENGAIN_ROOT)
    time.sleep(2)


def run_ingest():
    print("\n=== STEP 2: Run ingest pipeline ===")
    run([
        "python3",
        "engain_ingest.py",
        "--vault", str(VAULT_PATH),
        "--out", str(INGEST_OUT),
        "--pipeline-dir", str(ENGAIN_ROOT / "mettaext")
    ], cwd=ENGAIN_ROOT, allow_failure=True)


def normalize_scene_id(raw: str) -> str:
    s = raw.lower()
    s = s.replace(".zonj.json", "").replace(".zonj", "").replace(".json", "")
    s = s.replace("zonj_", "").replace("scene.", "")

    # normalize whitespace
    s = " ".join(s.split())

    # convert spaces to underscore
    s = s.replace(" ", "_")

    return s


def build_scene_library():
    print("\n=== STEP 3: Build Scene Library ===")
    candidates = [
        SCENE_LIBRARY_ROOT / "scenes",
        SCENE_LIBRARY_ROOT / "runtime_scenes",
        ENGAIN_ROOT / "mettaext/game_scenes",
    ]

    scene_dict = {}

    for d in candidates:
        if not d.exists():
            continue

        for path in sorted(d.glob("*")):
            if not (path.name.endswith(".json") or path.name.endswith(".zonj")):
                continue

            name = path.name
            if name.startswith("scene.") or name.startswith("out_pass1") or name.startswith("out_pass2") or name.startswith("out_pass3") or "first_contact_segmented" in name:
                continue

            sid = normalize_scene_id(name)

            # Skip if we already found a valid playable version of this scene
            if sid in scene_dict and scene_dict[sid]["format_status"] == "playable":
                continue

            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if not isinstance(data, dict):
                    continue

                status = "legacy_playable"
                if "scene_id" in data or "id" in data or "@id" in data:
                    status = "playable"
                elif "payload" in data and isinstance(data["payload"], dict) and ("scene_id" in data["payload"] or "id" in data["payload"]):
                    status = "playable"

                scene_dict[sid] = {
                    "id": sid,
                    "name": sid,
                    "file": str(path),
                    "format_status": status
                }
            except Exception:
                pass

    if not scene_dict:
        print("[FAIL] No valid scenes found in any known directory")
        sys.exit(1)

    index_path = SCENE_INDEX_PATH
    items = list(scene_dict.values())
    items.sort(key=lambda x: x["id"])

    index_path.write_text(json.dumps({
        "count": len(items),
        "scenes": items
    }, indent=2), encoding="utf-8")

    print(f"[OK] Found {len(items)} clean scenes")
    print(f"[OK] Scene index written: {index_path}")


def load_scene(scene_file):
    print(f"\n=== STEP 4: Load scene {scene_file.name} ===")

    data = json.loads(scene_file.read_text())

    cmd = [
        "curl",
        "-X", "POST",
        f"{RUNTIME_URL}/scene/load",
        "-H", "Content-Type: application/json",
        "-d", json.dumps(data)
    ]

    run(cmd)


def confirm_runtime():
    print("\n=== STEP 5: Confirm runtime ===")
    result = subprocess.run(
        ["curl", f"{RUNTIME_URL}/snapshot"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0 or not result.stdout.strip():
        print("[WARN] Could not confirm runtime snapshot")
    else:
        print("[OK] Runtime snapshot received")


def main():
    print("\n==============================")
    print(" EngAIn START BUTTON")
    print("==============================\n")

    ensure_stack()
    run_ingest()
    build_scene_library()

    print("\n==============================")
    print(" SCENE LIBRARY INITIALIZED")
    print("==============================\n")

    print("Next step: Godot scene loader should open and display the index.")


if __name__ == "__main__":
    main()
