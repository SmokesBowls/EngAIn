#!/usr/bin/env python3
"""
chapterroom_index_runner.py — EngAIn Chapterroom Index Runner MVP

PURPOSE:
    Read chapter_index.json
    Loop all chapters
    Run Pass A → Pass B → Pass B5 → Pass C
    Write scene packets to vault/.engain/scene_packets/
    Write one run manifest

INPUT:
    vault/.engain/chapter_index.json

OUTPUT:
    vault/.engain/scene_packets/<chapter_id>/<scene_id>.txt
    vault/.engain/scene_packets/<chapter_id>/<scene_id>.json
    vault/.engain/scene_packets/<chapter_id>/scene_packets_index.json
    vault/.engain/manifests/chapterroom_scene_packet_run_manifest.json

DOES:
    normalize chapters
    detect scene boundaries
    detect environment per scene
    write scene packets (text + JSON)

DOES NOT:
    extract MrLore claims
    decide canon
    compile ZONJ
    touch Godot
    mutate runtime
"""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ── Locate engain root for imports ───────────────────────────────────────────

def _find_engain_root(start: Path) -> Path:
    """Walk up from start looking for the EngAIn repo root (has tier1/ tier2/ tier3/)."""
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

if str(_ENGAIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_ENGAIN_ROOT))

# ── Import passes as Python callables ────────────────────────────────────────

try:
    from tier3.mettaext.chapterroom.passA_chapter_intake import intake as passA_intake
    from tier3.mettaext.chapterroom.passB_scene_boundary_provider import choose_boundaries as passB_choose
    from tier3.mettaext.chapterroom.passC_scene_packet_writer import write_packets as passC_write
except ImportError as e:
    print(f"[RUNNER] ERROR: Cannot import chapterroom passes: {e}", file=sys.stderr)
    print(f"[RUNNER] EngAIn root detected: {_ENGAIN_ROOT}", file=sys.stderr)
    sys.exit(1)

try:
    from tier3.mettaext.chapterroom.passB5_environment_detector import detect_environments as passB5_detect
except ImportError:
    # Fallback: try local directory
    try:
        import importlib.util
        _b5_candidates = [
            _HERE / "passB5_environment_detector.py",
            _ENGAIN_ROOT / "tier3" / "mettaext" / "chapterroom" / "passB5_environment_detector.py",
        ]
        passB5_detect = None
        for _b5_path in _b5_candidates:
            if _b5_path.exists():
                spec = importlib.util.spec_from_file_location("passB5", _b5_path)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                passB5_detect = mod.detect_environments
                break
        if passB5_detect is None:
            raise ImportError("passB5_environment_detector.py not found")
    except Exception as e2:
        print(f"[RUNNER] ERROR: Cannot import passB5: {e2}", file=sys.stderr)
        sys.exit(1)


# ── Manifest I/O ─────────────────────────────────────────────────────────────

def _read_manifest(manifest_path: Path) -> dict:
    if not manifest_path.exists():
        return {}
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def _default_manifest_path() -> Path:
    here = Path(__file__).resolve().parent
    candidates = []
    if len(here.parents) > 1:
        candidates.append(here.parents[1] / "assets" / "engain_manifest.json")
    if len(here.parents) > 2:
        candidates.append(here.parents[2] / "tier1" / "engainos" / "assets" / "engain_manifest.json")
    for c in candidates:
        if c.exists():
            return c
    return _ENGAIN_ROOT / "tier1" / "engainos" / "assets" / "engain_manifest.json"


def _resolve_vault_output(manifest_path: Path) -> tuple[Path, Path]:
    """Return (chapter_index_path, scene_packets_root)."""
    manifest = _read_manifest(manifest_path)
    output_dir = manifest.get("output_dir")
    active_vault = manifest.get("active_vault")

    if output_dir:
        engain_dir = Path(output_dir)
    elif active_vault:
        engain_dir = Path(active_vault) / ".engain"
    else:
        raise ValueError(
            "engain_manifest.json has no output_dir or active_vault. "
            "Run vault_discovery.py first."
        )

    chapter_index = engain_dir / "chapter_index.json"
    scene_packets_root = engain_dir / "scene_packets"
    return chapter_index, scene_packets_root


# ── Scene JSON packet writer ──────────────────────────────────────────────────

def _write_scene_json(scene: dict[str, Any], packet_dir: Path) -> Path:
    """Write a .json companion packet alongside the .txt packet."""
    scene_id = scene["scene_id"]
    safe = re.sub(r"[^a-z0-9_.-]+", "_", scene_id.lower()).strip("_")
    path = packet_dir / f"{safe}.json"

    packet = {
        "contract":      "engain.scene_packet.v1",
        "scene_id":      scene["scene_id"],
        "chapter_id":    scene["chapter_id"],
        "scene_index":   scene["scene_index"],
        "source_file":   scene.get("source_file", ""),
        "book_id":       scene.get("book_id", ""),
        "start_line":    scene["boundary_start_line"],
        "end_line":      scene["boundary_end_line"],
        "boundary_method": scene["boundary_method"],
        "authority_state": scene["authority_state"],
        "authored_scene_boundaries_proven": scene["authored_scene_boundaries_proven"],
        "mr_lore_ready": True,
        "environment":   scene.get("environment", {}),
        "text":          scene.get("text", ""),
    }

    path.write_text(json.dumps(packet, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


# ── Per-chapter runner ────────────────────────────────────────────────────────

import re  # needed for _write_scene_json


def run_chapter(
    chapter: dict[str, Any],
    book: dict[str, Any],
    scene_packets_root: Path,
    intermediate_dir: Path,
    target_words: int,
) -> dict[str, Any]:
    """
    Run Pass A → B → B5 → C for one chapter.

    Returns a result dict for the run manifest.
    """
    chapter_path = Path(chapter["path"])
    chapter_id_stem = chapter["chapter_id"]
    book_id = book["book_id"]

    result: dict[str, Any] = {
        "chapter_id":   chapter_id_stem,
        "book_id":      book_id,
        "source_file":  str(chapter_path),
        "status":       "PENDING",
        "error":        None,
        "scene_count":  0,
        "terrain_mix":  {},
        "scene_packet_index": None,
    }

    try:
        # ── Pass A ──────────────────────────────────────────────────────────
        intermediate_dir.mkdir(parents=True, exist_ok=True)
        passA_out = intermediate_dir / f"out_passA_{chapter_path.stem}.json"
        manifest = passA_intake(chapter_path, passA_out)
        chapter_id = manifest["chapter_id"]

        # ── Pass B ──────────────────────────────────────────────────────────
        proposal = passB_choose(manifest, target_words)

        # Inject source_file and book_id into every scene for traceability
        for scene in proposal.get("scenes", []):
            scene["source_file"] = str(chapter_path)
            scene["book_id"] = book_id

        # Write Pass B JSON for auditability
        safe_chapter = chapter_id.replace("/", "_")
        passB_out = intermediate_dir / f"out_passB_{safe_chapter}.json"
        passB_out.write_text(
            json.dumps(proposal, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        # ── Pass B5 ─────────────────────────────────────────────────────────
        env_proposal = passB5_detect(proposal)

        passB5_out = intermediate_dir / f"out_passB5_{safe_chapter}.json"
        passB5_out.write_text(
            json.dumps(env_proposal, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        # ── Pass C ──────────────────────────────────────────────────────────
        # Override output dir to vault/.engain/scene_packets/
        index = passC_write(env_proposal, scene_packets_root)

        # Write JSON companion packets
        packet_dir = scene_packets_root / "scene_packets" / chapter_id
        for scene in env_proposal.get("scenes", []):
            _write_scene_json(scene, packet_dir)

        # Terrain mix summary
        terrain_mix: dict[str, int] = {}
        for scene in env_proposal.get("scenes", []):
            tf = scene.get("environment", {}).get("terrain_family", "default")
            terrain_mix[tf] = terrain_mix.get(tf, 0) + 1

        result.update({
            "status":             "OK",
            "chapter_id":         chapter_id,
            "scene_count":        index["scene_count"],
            "terrain_mix":        terrain_mix,
            "scene_packet_index": index.get("index_path"),
        })

    except Exception as exc:
        result["status"] = "FAILED"
        result["error"]  = str(exc)
        result["traceback"] = traceback.format_exc()

    return result


# ── Run manifest writer ───────────────────────────────────────────────────────

def write_run_manifest(
    results: list[dict[str, Any]],
    vault_root: Path,
    output_dir: Path,
) -> Path:
    ok      = [r for r in results if r["status"] == "OK"]
    failed  = [r for r in results if r["status"] == "FAILED"]
    total_scenes = sum(r["scene_count"] for r in ok)

    manifest = {
        "contract":        "engain.chapterroom_run_manifest.v1",
        "run_timestamp":   datetime.now(timezone.utc).isoformat(),
        "vault_root":      str(vault_root),
        "chapter_count":   len(results),
        "chapters_ok":     len(ok),
        "chapters_failed": len(failed),
        "total_scenes":    total_scenes,
        "results":         results,
    }

    manifests_dir = output_dir / "manifests"
    manifests_dir.mkdir(parents=True, exist_ok=True)
    path = manifests_dir / "chapterroom_scene_packet_run_manifest.json"
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="EngAIn Chapterroom Index Runner — process all chapters into scene packets."
    )
    parser.add_argument(
        "--manifest", default=None,
        help="Path to engain_manifest.json (auto-detected if omitted).",
    )
    parser.add_argument(
        "--chapter-index", default=None,
        help="Direct path to chapter_index.json (overrides manifest).",
    )
    parser.add_argument(
        "--output-dir", default=None,
        help="Root output dir (overrides vault/.engain from manifest).",
    )
    parser.add_argument(
        "--target-words", type=int, default=900,
        help="Mechanical fallback words per scene for Pass B.",
    )
    parser.add_argument(
        "--book", default=None,
        help="Only process chapters from this book_id (e.g. book_01_book_of_genesis).",
    )
    parser.add_argument(
        "--chapter", default=None,
        help="Only process this chapter stem (e.g. 001_the_ethereal_vigil).",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Discover chapters and print plan without writing anything.",
    )
    args = parser.parse_args()

    # Resolve paths
    manifest_path = Path(args.manifest) if args.manifest else _default_manifest_path()

    if args.chapter_index:
        chapter_index_path = Path(args.chapter_index).resolve()
        engain_dir = chapter_index_path.parent
    else:
        try:
            chapter_index_path, scene_packets_root_base = _resolve_vault_output(manifest_path)
            engain_dir = chapter_index_path.parent
        except ValueError as e:
            print(f"[RUNNER] ERROR: {e}", file=sys.stderr)
            return 1

    if args.output_dir:
        engain_dir = Path(args.output_dir).resolve()

    scene_packets_root = engain_dir
    intermediate_dir   = engain_dir / "intermediate"

    if not chapter_index_path.exists():
        print(f"[RUNNER] ERROR: chapter_index.json not found: {chapter_index_path}", file=sys.stderr)
        print("[RUNNER] Run chapter_discovery.py first.", file=sys.stderr)
        return 1

    # Load chapter index
    index = json.loads(chapter_index_path.read_text(encoding="utf-8"))
    vault_root = Path(index["vault_root"])
    books = index.get("books", [])

    # Apply filters
    if args.book:
        books = [b for b in books if b["book_id"] == args.book]
    if args.chapter:
        for book in books:
            book["chapters"] = [
                c for c in book["chapters"]
                if args.chapter in c["chapter_id"]
            ]

    total_chapters = sum(len(b["chapters"]) for b in books)

    print(f"\n[RUNNER] EngAIn Chapterroom Index Runner")
    print(f"[RUNNER] Vault        : {vault_root}")
    print(f"[RUNNER] Output       : {engain_dir}")
    print(f"[RUNNER] Books        : {len(books)}")
    print(f"[RUNNER] Chapters     : {total_chapters}")
    print(f"[RUNNER] Target words : {args.target_words}")
    if args.dry_run:
        print(f"[RUNNER] DRY RUN — no files will be written\n")

    if args.dry_run:
        for book in books:
            print(f"  {book['book_id']}  ({len(book['chapters'])} chapters)")
            for ch in book["chapters"]:
                print(f"    {ch['chapter_id']}  →  {ch['path']}")
        return 0

    # Run
    results = []
    chapter_num = 0

    for book in books:
        for chapter in book["chapters"]:
            chapter_num += 1
            print(f"[{chapter_num:03d}/{total_chapters}] {chapter['chapter_id']} ...", end=" ", flush=True)

            result = run_chapter(
                chapter=chapter,
                book=book,
                scene_packets_root=scene_packets_root,
                intermediate_dir=intermediate_dir,
                target_words=args.target_words,
            )
            results.append(result)

            if result["status"] == "OK":
                terrain = result["terrain_mix"]
                print(f"OK  scenes={result['scene_count']}  terrain={terrain}")
            else:
                print(f"FAILED  error={result['error']}")

    # Write run manifest
    manifest_out = write_run_manifest(results, vault_root, engain_dir)

    ok_count     = sum(1 for r in results if r["status"] == "OK")
    failed_count = sum(1 for r in results if r["status"] == "FAILED")
    total_scenes = sum(r["scene_count"] for r in results if r["status"] == "OK")

    print(f"\n[RUNNER] CHAPTERROOM_INDEX_RUNNER_COMPLETE = TRUE")
    print(f"[RUNNER] CHAPTERS_OK     = {ok_count}/{total_chapters}")
    print(f"[RUNNER] CHAPTERS_FAILED = {failed_count}")
    print(f"[RUNNER] TOTAL_SCENES    = {total_scenes}")
    print(f"[RUNNER] RUN_MANIFEST    = {manifest_out}")

    if failed_count:
        print(f"\n[RUNNER] FAILED CHAPTERS:")
        for r in results:
            if r["status"] == "FAILED":
                print(f"  {r['chapter_id']}  —  {r['error']}")

    return 0 if failed_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
