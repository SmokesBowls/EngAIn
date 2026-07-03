#!/usr/bin/env python3
"""
mrlore_scene_intake_runner.py — EngAIn MrLore Scene Intake MVP

PURPOSE:
    Read chapterroom_scene_boundary_review_manifest.json
    Select MRLORE_READY chapters only
    Load scene packet .json files
    Count scenes loaded
    Emit mrlore_scene_intake_manifest.json

INPUT:
    vault/.engain/manifests/chapterroom_scene_boundary_review_manifest.json
    vault/.engain/scene_packets/

OUTPUT:
    vault/.engain/manifests/mrlore_scene_intake_manifest.json

DOES NOT:
    extract claims
    write canon
    touch runtime
    touch Godot
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ── Locate EngAIn root ────────────────────────────────────────────────────────

def _find_engain_root(start: Path) -> Path:
    cur = start.resolve()
    for _ in range(8):
        if (cur / "tier1").exists() and (cur / "tier2").exists() and (cur / "tier3").exists():
            return cur
        parent = cur.parent
        if parent == cur:
            break
        cur = parent
    return start.resolve()


_HERE = Path(__file__).resolve().parent
_ENGAIN_ROOT = _find_engain_root(_HERE)


# ── Manifest resolution ───────────────────────────────────────────────────────

def _default_manifest_path() -> Path:
    candidates = [
        _ENGAIN_ROOT / "tier1" / "engainos" / "assets" / "engain_manifest.json",
        _HERE.parent / "engainos" / "assets" / "engain_manifest.json",
    ]
    for c in candidates:
        if c.exists():
            return c
    return candidates[0]


def _resolve_engain_dir(manifest_path: Path) -> Path:
    if not manifest_path.exists():
        raise FileNotFoundError(f"engain_manifest.json not found: {manifest_path}")
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    output_dir = data.get("output_dir")
    active_vault = data.get("active_vault")
    if output_dir:
        return Path(output_dir)
    if active_vault:
        return Path(active_vault) / ".engain"
    raise ValueError(
        "engain_manifest.json has no output_dir or active_vault. "
        "Run vault_discovery.py first."
    )


# ── Scene packet loading ──────────────────────────────────────────────────────

def _json_path_for_packet(txt_path: str) -> Path:
    return Path(txt_path).with_suffix(".json")


def load_chapter_scenes(
    chapter_id: str,
    scene_packets_dir: Path,
) -> tuple[list[dict[str, Any]], list[str]]:
    """
    Load all scene packet JSON files for one chapter.

    Returns (scenes, errors).
    scenes — list of intake scene entries.
    errors — list of problem descriptions (missing files, parse failures).
    """
    index_path = scene_packets_dir / chapter_id / "scene_packets_index.json"
    if not index_path.exists():
        return [], [f"scene_packets_index.json missing: {index_path}"]

    try:
        index = json.loads(index_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [], [f"Failed to parse scene_packets_index.json for {chapter_id}: {exc}"]

    scenes: list[dict[str, Any]] = []
    errors: list[str] = []

    for packet in index.get("packets", []):
        scene_id = packet.get("scene_id", "")
        txt_path = packet.get("packet_path", "")
        json_path = _json_path_for_packet(txt_path)

        if not json_path.exists():
            errors.append(f"Scene JSON missing: {json_path}")
            continue

        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"Failed to parse {json_path}: {exc}")
            continue

        scenes.append({
            "scene_id":      scene_id,
            "scene_index":   packet.get("scene_index"),
            "packet_json":   str(json_path),
            "boundary_method":   packet.get("boundary_method"),
            "authority_state":   packet.get("authority_state"),
            "mr_lore_ready": data.get("mr_lore_ready", False),
        })

    return scenes, errors


# ── Intake manifest writer ────────────────────────────────────────────────────

def write_intake_manifest(
    ready_chapters: list[dict[str, Any]],
    skipped_chapters: list[dict[str, Any]],
    review_manifest_path: Path,
    engain_dir: Path,
) -> Path:
    total_scenes = sum(ch["scene_count"] for ch in ready_chapters)

    manifest: dict[str, Any] = {
        "contract":               "engain.mrlore_scene_intake_manifest.v1",
        "run_timestamp":          datetime.now(timezone.utc).isoformat(),
        "source_review_manifest": str(review_manifest_path),
        "engain_dir":             str(engain_dir),
        "chapters_ready":         len(ready_chapters),
        "chapters_skipped":       len(skipped_chapters),
        "total_scenes_loaded":    total_scenes,
        "chapters":               ready_chapters,
        "skipped":                skipped_chapters,
    }

    out_path = engain_dir / "manifests" / "mrlore_scene_intake_manifest.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return out_path


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="EngAIn MrLore Scene Intake — build confirmed input list from MRLORE_READY chapters."
    )
    parser.add_argument(
        "--manifest", default=None,
        help="Path to engain_manifest.json (auto-detected if omitted).",
    )
    parser.add_argument(
        "--engain-dir", default=None,
        help="Direct path to vault/.engain (overrides manifest).",
    )
    parser.add_argument(
        "--review-manifest", default=None,
        help="Path to chapterroom_scene_boundary_review_manifest.json (default: <engain-dir>/manifests/...).",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print plan without writing output.",
    )
    args = parser.parse_args()

    # ── Resolve engain_dir ────────────────────────────────────────────────────
    if args.engain_dir:
        engain_dir = Path(args.engain_dir).resolve()
    else:
        manifest_path = Path(args.manifest) if args.manifest else _default_manifest_path()
        try:
            engain_dir = _resolve_engain_dir(manifest_path)
        except (FileNotFoundError, ValueError) as exc:
            print(f"[INTAKE] ERROR: {exc}", file=sys.stderr)
            return 1

    scene_packets_dir = engain_dir / "scene_packets"

    # ── Resolve review manifest path ──────────────────────────────────────────
    if args.review_manifest:
        review_manifest_path = Path(args.review_manifest).resolve()
    else:
        review_manifest_path = engain_dir / "manifests" / "chapterroom_scene_boundary_review_manifest.json"

    if not review_manifest_path.exists():
        print(f"[INTAKE] ERROR: Review manifest not found: {review_manifest_path}", file=sys.stderr)
        print("[INTAKE] Run the chapterroom boundary review step first.", file=sys.stderr)
        return 1

    # ── Load review manifest ──────────────────────────────────────────────────
    try:
        review = json.loads(review_manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"[INTAKE] ERROR: Failed to parse review manifest: {exc}", file=sys.stderr)
        return 1

    ready_entries = [e for e in review.get("ready", []) if e.get("status") == "MRLORE_READY"]
    skipped_raw   = review.get("review_required", [])

    print(f"\n[INTAKE] MrLore Scene Intake Runner")
    print(f"[INTAKE] engain_dir       : {engain_dir}")
    print(f"[INTAKE] review manifest  : {review_manifest_path}")
    print(f"[INTAKE] MRLORE_READY     : {len(ready_entries)}")
    print(f"[INTAKE] Review required  : {len(skipped_raw)}")

    if args.dry_run:
        print(f"[INTAKE] DRY RUN — no files will be written\n")
        for entry in ready_entries:
            print(f"  {entry['chapter_id']}  scenes={entry.get('scene_count', '?')}")
        print(f"\n[INTAKE] SKIPPED (boundary review required):")
        for entry in skipped_raw:
            print(f"  {entry['chapter_id']}  scenes={entry.get('scene_count', '?')}  reason={entry.get('reason','')}")
        return 0

    # ── Load scene packets per MRLORE_READY chapter ───────────────────────────
    ready_chapters: list[dict[str, Any]] = []
    all_errors: list[str] = []
    total_loaded = 0

    for entry in ready_entries:
        chapter_id = entry["chapter_id"]
        scenes, errors = load_chapter_scenes(chapter_id, scene_packets_dir)
        all_errors.extend(errors)
        total_loaded += len(scenes)

        ready_chapters.append({
            "chapter_id":   chapter_id,
            "scene_count":  len(scenes),
            "status":       "MRLORE_READY",
            "errors":       errors,
            "scenes":       scenes,
        })

        status_tag = f"OK  scenes={len(scenes)}" if not errors else f"WARN  scenes={len(scenes)}  errors={len(errors)}"
        print(f"  {chapter_id}  {status_tag}")

    # ── Build skipped list ────────────────────────────────────────────────────
    skipped_chapters = [
        {
            "chapter_id":  e["chapter_id"],
            "scene_count": e.get("scene_count"),
            "status":      e.get("status", "SCENE_BOUNDARY_REVIEW_REQUIRED"),
            "reason":      e.get("reason", ""),
        }
        for e in skipped_raw
    ]

    # ── Write intake manifest ─────────────────────────────────────────────────
    out_path = write_intake_manifest(
        ready_chapters=ready_chapters,
        skipped_chapters=skipped_chapters,
        review_manifest_path=review_manifest_path,
        engain_dir=engain_dir,
    )

    print(f"\n[INTAKE] MRLORE_SCENE_INTAKE_COMPLETE = TRUE")
    print(f"[INTAKE] CHAPTERS_READY       = {len(ready_chapters)}")
    print(f"[INTAKE] CHAPTERS_SKIPPED     = {len(skipped_chapters)}")
    print(f"[INTAKE] TOTAL_SCENES_LOADED  = {total_loaded}")
    print(f"[INTAKE] INTAKE_MANIFEST      = {out_path}")

    if all_errors:
        print(f"\n[INTAKE] WARNINGS ({len(all_errors)} total):")
        for err in all_errors[:20]:
            print(f"  {err}")
        if len(all_errors) > 20:
            print(f"  ... and {len(all_errors) - 20} more")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
