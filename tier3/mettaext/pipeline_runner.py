#!/usr/bin/env python3
"""
pipeline_runner.py
Automatic entrypoint that chains the Scene Ingestion (ABC)
and the Passroom compilation (Pass 1–5) and writes the done manifest.

Authority:
- Evidence only.
- Consumers pull from stageroom.
- Mettaext does not dispatch.
"""

from __future__ import annotations

import sys
import subprocess
import json
from pathlib import Path


def run_pipeline(chapter_path_str: str) -> None:
    chapter_path = Path(chapter_path_str).absolute()
    if not chapter_path.exists():
        print(f"❌ Error: Could not find chapter at {chapter_path}")
        sys.exit(1)

    base_dir = Path(__file__).parent
    engain_root = base_dir.parents[1]
    
    world_rules_path = engain_root / "tier1" / "engainos" / "assets" / "world_rules.json"

    # --- 1. Run Scene Ingestion (ABC) ---
    print(f"\n[1] Running Chapterroom Ingestion (ABC) on: {chapter_path.name}")
    cmd_abc = [
        sys.executable,
        "-m",
        "tier3.mettaext.chapterroom.chapterroom_runner",
        str(chapter_path),
        "--output-dir",
        "tier3/mettaext/stageroom/output/chapterroom"
    ]
    subprocess.run(cmd_abc, cwd=str(engain_root), check=True)

    # --- 2. Read index and packets ---
    output_dir = engain_root / "tier3" / "mettaext" / "stageroom" / "output" / "chapterroom"
    passA_path = output_dir / f"out_passA_{chapter_path.stem}.json"
    if not passA_path.exists():
        print(f"❌ Missing Pass A output: {passA_path}")
        sys.exit(1)
        
    with passA_path.open("r", encoding="utf-8") as f:
        passA_data = json.load(f)
    chapter_id = passA_data["chapter_id"]

    index_path = output_dir / "scene_packets" / chapter_id / "scene_packets_index.json"
    if not index_path.exists():
        print(f"❌ Missing scene packets index: {index_path}")
        sys.exit(1)
        
    with index_path.open("r", encoding="utf-8") as f:
        index_data = json.load(f)

    packets = index_data.get("packets", [])
    print(f"\n[2] Running Passroom compilation (Pass 1-5) on {len(packets)} scene packets")

    for packet in packets:
        scene_id = packet["scene_id"]
        packet_path = Path(packet["packet_path"])
        if not packet_path.is_absolute():
            packet_path = engain_root / packet_path
            
        print(f"\n--- Compiling Scene Packet: {scene_id} ---")
        scene_out_dir = engain_root / "tier3" / "mettaext" / "stageroom" / "output" / "passroom" / scene_id
        scene_out_dir.mkdir(parents=True, exist_ok=True)

        # Pass 1
        print("Running Pass 1...")
        p1_out = scene_out_dir / f"out_pass1_{scene_id}.txt"
        subprocess.run([
            sys.executable, "-m", "tier3.mettaext.passroom.pass1_explicit",
            str(packet_path), str(p1_out)
        ], cwd=str(engain_root), check=True)

        # Pass 1 Spatial
        print("Running Pass 1 Spatial...")
        p1_spatial_out = scene_out_dir / f"out_pass1_spatial_{scene_id}.json"
        subprocess.run([
            sys.executable, "-m", "tier3.mettaext.passroom.pass1_spatial",
            str(p1_out),
            "--output", str(p1_spatial_out)
        ], cwd=str(engain_root), check=True)

        # Pass 2
        print("Running Pass 2...")
        subprocess.run([
            sys.executable, "-m", "tier3.mettaext.passroom.pass2_enhanced",
            str(p1_out)
        ], cwd=str(engain_root), check=True)
        p2_out = scene_out_dir / f"out_pass2_{scene_id}.metta"

        # Pass 3
        print("Running Pass 3...")
        p3_out = scene_out_dir / f"zonj_{scene_id}.json"
        subprocess.run([
            sys.executable, "-m", "tier3.mettaext.passroom.pass3_merge",
            str(p1_out), str(p2_out), str(p3_out)
        ], cwd=str(engain_root), check=True)

        # Pass 4
        print("Running Pass 4...")
        subprocess.run([
            sys.executable, "-m", "tier3.mettaext.passroom.pass4_zon_bridge",
            str(p3_out),
            "--era", "FirstAge",
            "--location", "Beach",
            "--output-dir", str(scene_out_dir),
            "--world-rules", str(world_rules_path)
        ], cwd=str(engain_root), check=True)
        p4_out = scene_out_dir / f"{scene_id}.zonj.json"

        # Pass 5
        print("Running Pass 5...")
        subprocess.run([
            sys.executable, "-m", "tier3.mettaext.passroom.pass5_game_bridge",
            str(p4_out),
            "--output", str(scene_out_dir / "game_scenes"),
            "--world-rules", str(world_rules_path),
            "--spatial-dir", str(scene_out_dir)
        ], cwd=str(engain_root), check=True)

    source_text_id = chapter_path.stem
    if not source_text_id.startswith("chapter."):
        source_text_id = f"chapter.{source_text_id}"

    subprocess.run([
        sys.executable, "-m", "tier3.mettaext.stageroom_manifest",
        "--source-text-id", source_text_id
    ], cwd=str(engain_root), check=True)
    
    print("\n[mettaext] Runtime dispatch disabled: METTAEXT_PUSHES_TO_STAGEROOM_ONLY=TRUE")
    print("✓ Pipeline complete!")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python3 -m tier3.mettaext.pipeline_runner path/to/chapter.txt")
        sys.exit(1)
    run_pipeline(sys.argv[1])


if __name__ == "__main__":
    main()
