#!/usr/bin/env python3
import json
import os
import sys
import subprocess
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
WORLD_RULES = SCRIPT_DIR.parent / "manifests" / "world_rules.json"


def run(cmd):
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True)


def main():
    # Accept optional positional arg; resolve absolute before any chdir
    if len(sys.argv) > 1:
        in_file = Path(sys.argv[1]).resolve()
    else:
        in_file = (SCRIPT_DIR / "03_Fist_contact.txt").resolve()

    # Run all pass scripts from mettaext/ so bare names like "pass1_explicit.py" work
    os.chdir(SCRIPT_DIR)

    if not in_file.exists():
        print(f"ERROR: missing input file: {in_file}")
        sys.exit(1)

    base = in_file.stem

    run([sys.executable, "pass1_explicit.py", str(in_file)])

    # find pass1 output wherever it wrote it
    candidates = list(Path(".").rglob(f"out_pass1_{base}.txt"))
    if not candidates:
        print(f"FAIL: Pass1 did not produce out_pass1_{base}.txt under {Path('.').resolve()}")
        sys.exit(1)
    p1 = candidates[0]
    print("Using Pass1 output:", p1)

    run([sys.executable, "pass2_enhanced.py", str(p1)])

    p2_local = p1.parent / f"out_pass2_{base}.metta"
    p2_cwd = Path(f"out_pass2_{base}.metta")
    p2 = p2_local if p2_local.exists() else p2_cwd
    print("Using Pass2 output:", p2)

    run([sys.executable, "pass3_merge.py", str(p1), str(p2)])

    zonj_local = p1.parent / f"zonj_{base}.json"
    zonj_cwd = Path(f"zonj_{base}.json")
    zonj = zonj_local if zonj_local.exists() else zonj_cwd
    if not zonj.exists():
        print(f"FAIL: Pass3 did not produce {zonj_local} or {zonj_cwd}")
        sys.exit(1)
    print("Using Pass3 output (zonj):", zonj)

    run([sys.executable, "pass4_zon_bridge.py", str(zonj),
         "--era", "FirstAge", "--location", "Beach", "--output-dir", "out",
         "--world-rules", str(WORLD_RULES)])

    p4_zonj = Path("out") / f"{base}.zonj.json"
    if not p4_zonj.exists():
        print(f"FAIL: Pass4 did not produce {p4_zonj.resolve()}")
        sys.exit(1)
    print(f"OK: wrote out/{base}.zon and out/{base}.zonj.json")

    # Pass5: game-ready scene JSON → vault cache (runtime reads from here)
    VAULT_CACHE = Path("/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/.vault_cache/obsidianburdennov25")
    VAULT_CACHE.mkdir(parents=True, exist_ok=True)
    run([sys.executable, "pass5_game_bridge.py", str(p4_zonj),
         "--output", str(VAULT_CACHE),
         "--world-rules", str(WORLD_RULES)])

    game_scene_path = VAULT_CACHE / f"scene.{base}.json"
    if not game_scene_path.exists():
        print(f"FAIL: Pass5 did not produce {game_scene_path.resolve()}")
        sys.exit(1)

    with game_scene_path.open() as f:
        scene = json.load(f)
    event_count = len(scene.get("events", []))
    entity_count = len(scene.get("entities", []))
    print(f"OK: {VAULT_CACHE}/scene.{base}.json — entities: {entity_count}, events: {event_count}")

    # Reload runtime is disabled in this version
    print("[mettaext] Runtime dispatch disabled: METTAEXT_PUSHES_TO_STAGEROOM_ONLY=TRUE")



if __name__ == "__main__":
    main()
