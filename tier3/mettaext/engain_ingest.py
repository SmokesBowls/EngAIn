#!/usr/bin/env python3
"""
engain_ingest.py - EngAIn Unified Ingest Tool
Turns raw content into engine-ready data.

FIXES in this version:
  - pipeline_dir is resolved to absolute path BEFORE any os.chdir()
  - Pass 1/2/3/4 get correct arg counts
  - Subprocesses run with cwd=workdir
  - safe_copy() prevents PermissionError on re-run
  - --include / --exclude pattern filtering for --scan
  - Built-in junk exclusions: out_pass1_*, continuity/critique notes, READMEs, specs
  - Deduplication: same filename from multiple subdirs processed only once

Usage:
  # Process one chapter
  python3 engain_ingest.py --file 03_Fist_contact.txt --out ./ingested/ --pipeline-dir .

  # Process only canonical chapters (act_*, Chapter_*, Fact_*, B6act*)
  python3 engain_ingest.py --scan . --out ./ingested/ --pipeline-dir . --include "act_*,Chapter_*,chapter_*,Fact_*,B6act*,[0-9][0-9]_*"

  # Process all chapters in a clean book folder
  python3 engain_ingest.py --scan ./book/ --out ./ingested/ --pipeline-dir .

  # Dry run to preview what would be processed
  python3 engain_ingest.py --scan . --out ./ingested/ --dry-run --include "act_*,Chapter_*,chapter_*"

  # Load existing ZONJ files into runtime (dispatch is disabled in this version)
  python3 engain_ingest.py --load-zonj ./game_scenes/ --out ./loaded/

  # Ingest TRIXEL brush score JSONL
  python3 engain_ingest.py --trixel ./scores/ --out ./ingested/
"""

import argparse
import fnmatch
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Built-in junk exclusions for --scan mode
# Files matching any of these patterns are silently skipped
# ---------------------------------------------------------------------------
JUNK_PATTERNS = [
    "out_pass1_*",
    "out_pass2_*",
    "out_pass3_*",
    "zonj_*",
    "continuity *",
    "continuity_*",
    "critique *",
    "critique_*",
    "critiue *",           # typo variant in your repo
    "revised*",
    "revisments*",
    "conversion_*",
    "ARCHITECTURE_MAP*",
    "GUI_CHANGELOG*",
    "GUI_README*",
    "IMMUTABLE_ANCHOR*",
    "INGEST_README*",
    "NARRATIVE_PIPELINE_README*",
    "NARRATIVE_TO_GAME_PROOF*",
    "PASS 3 SPEC*",
    "SESSION_SUMMARY*",
    "UNIFIED_PIPELINE_GUIDE*",
    "mettachaty*",
    "official_*",
    "7kb.txt",
    "fist message*",
    "queens final message*",
    "forged Identity cover page*",
    "* cover page*",
    "legends and God*",
    "INGEST_README*",
    "*.md",               # skip all markdown docs (READMEs, specs)
]

# Canonical chapter filename prefixes — used when --include not specified
CHAPTER_PREFIXES = (
    "act_",
    "chapter_",
    "Chapter_",
    "Chaoter_",   # typo variant in your repo
    "Chapte_",    # typo variant
    "Fact_",
    "B6act",
)

# Single-digit or double-digit numbered chapters: 01_*, 02_*, ...
import re
_NUMBERED_CHAPTER = re.compile(r"^\d{2}_")


def is_junk(filename: str) -> bool:
    """Return True if the file should be excluded by default."""
    for pat in JUNK_PATTERNS:
        if fnmatch.fnmatch(filename, pat):
            return True
    return False


def is_chapter(filename: str) -> bool:
    """Return True if the filename looks like a canonical chapter."""
    if filename.startswith(CHAPTER_PREFIXES):
        return True
    if _NUMBERED_CHAPTER.match(filename):
        return True
    return False


def matches_include(filename: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(filename, p.strip()) for p in patterns)


def matches_exclude(filename: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(filename, p.strip()) for p in patterns)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def resolve_abs(path: Optional[str]) -> Optional[Path]:
    """Resolve a path to absolute, expanding ~ and relative segments."""
    if path is None:
        return None
    return Path(path).expanduser().resolve()


def run_pass(script: Path, args: list, cwd: Path, label: str) -> tuple[bool, str]:
    """Run a pipeline pass script.  Returns (success, error_message)."""
    cmd = [sys.executable, str(script)] + [str(a) for a in args]
    try:
        result = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            err = (result.stderr or result.stdout or "").strip()
            return False, f"{label} failed: {err[:500]}"
        return True, ""
    except FileNotFoundError:
        return False, f"{label} failed: script not found: {script}"
    except Exception as e:
        return False, f"{label} failed: {e}"


def safe_copy(src: Path, dst: Path):
    """Copy src → dst, making the destination writable first if it exists."""
    if dst.exists():
        dst.chmod(0o644)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(src), str(dst))
    dst.chmod(0o644)


def post_scene(runtime_url: str, scene: dict, scene_id: str) -> tuple[bool, str]:
    print("[mettaext] Runtime dispatch disabled: METTAEXT_PUSHES_TO_STAGEROOM_ONLY=TRUE")
    return True, "Dispatch disabled"


# ---------------------------------------------------------------------------
# ZONJ validation
# ---------------------------------------------------------------------------

ZONJ_REQUIRED_KEYS = {"scene_id", "entities", "events"}
ZONJ_ALT_KEYS = {"type", "id", "segments"}  # older format


def is_valid_zonj(data) -> bool:
    if not isinstance(data, dict):
        return False
    if ZONJ_REQUIRED_KEYS.issubset(data.keys()):
        return True
    if "scene_id" in data and ("events" in data or "segments" in data):
        return True
    if data.get("type") == "scene" and "id" in data:
        return True
    return False


# ---------------------------------------------------------------------------
# Mode: --load-zonj
# ---------------------------------------------------------------------------

def cmd_load_zonj(args):
    src_dir = resolve_abs(args.load_zonj)
    out_dir = resolve_abs(args.out)
    runtime = args.runtime
    dry_run = args.dry_run

    if not src_dir.exists():
        print(f"[ERROR] --load-zonj path does not exist: {src_dir}")
        return 1

    json_files = sorted(src_dir.rglob("*.json"))
    valid = []
    for jf in json_files:
        try:
            data = json.loads(jf.read_text(encoding="utf-8"))
            if is_valid_zonj(data):
                valid.append((jf, data))
        except Exception:
            pass

    mode_label = "copy only" if not runtime else runtime
    print("=" * 60)
    print("  EngAIn ZONJ Loader")
    print(f"  ZONJ files found: {len(valid)} / {len(json_files)} scanned")
    print(f"  Runtime: {mode_label}")
    print("=" * 60)

    if dry_run:
        for jf, _ in valid:
            print(f"  [zonj] {jf}")
        return 0

    out_dir.mkdir(parents=True, exist_ok=True)
    loaded = 0
    for jf, data in valid:
        scene_id = data.get("scene_id") or data.get("id") or jf.stem
        dst = out_dir / jf.name
        try:
            safe_copy(jf, dst)
        except Exception as e:
            print(f"  ⚠ {scene_id} → copy failed: {e}")
            continue

        if runtime:
            ok, err = post_scene(runtime, data, scene_id)
            if ok:
                print(f"  ✓ {scene_id} → runtime")
                loaded += 1
            else:
                print(f"  ⚠ {scene_id} → runtime failed: {err}")
        else:
            print(f"  ✓ {scene_id} → {dst.relative_to(out_dir.parent)}")
            loaded += 1

    print(f"  Loaded {loaded}/{len(valid)} scenes")
    return 0


# ---------------------------------------------------------------------------
# Mode: --file / --scan  (full pipeline)
# ---------------------------------------------------------------------------

def run_pipeline(
    input_file: Path,
    pipeline_dir: Path,   # ABSOLUTE path resolved before any chdir
    out_dir: Path,
    dry_run: bool,
    runtime: Optional[str],
) -> tuple[bool, str]:
    """Run Pass1 → Pass2 → Pass3 → Pass4 for a single input file."""

    # Verify pipeline scripts exist
    p1 = pipeline_dir / "pass1_explicit.py"
    p2 = pipeline_dir / "passroom" / "pass2_enhanced.py"
    if not p2.exists():
        p2 = pipeline_dir / "pass2_enhanced.py"
    p3 = pipeline_dir / "pass3_merge.py"
    p4 = pipeline_dir / "pass4_zon_bridge.py"

    for script in [p1, p2, p3]:
        if not script.exists():
            return False, f"Pipeline script not found: {script}"

    # Working directory for intermediates
    workdir = out_dir / "scenes" / "_work"
    workdir.mkdir(parents=True, exist_ok=True)

    base = input_file.stem  # e.g. "03_Fist_contact"

    # Expected output names (derived by each pass script)
    p1_out  = workdir / f"out_pass1_{base}.txt"
    p2_out  = workdir / f"out_pass2_{base}.metta"
    p3_out  = workdir / f"zonj_{base}.json"

    if dry_run:
        return True, f"[dry-run] would process: {input_file.name}"

    # --- Pass 1 ---
    # Copy input into workdir so pass1 writes its output there
    work_input = workdir / input_file.name
    safe_copy(input_file, work_input)

    ok, err = run_pass(p1, [work_input.name], workdir, "Pass 1")
    if not ok:
        return False, err

    if not p1_out.exists():
        # Some versions write next to input, check workdir root
        alt = workdir / f"out_pass1_{input_file.name}"
        if alt.exists():
            alt.rename(p1_out)
        else:
            return False, "Pass 1: output file not found after run"

    # --- Pass 2 ---
    ok, err = run_pass(p2, [p1_out.name], workdir, "Pass 2")
    if not ok:
        return False, err

    if not p2_out.exists():
        return False, "Pass 2: .metta output file not found after run"

    # --- Pass 3 ---
    ok, err = run_pass(p3, [p1_out.name, p2_out.name], workdir, "Pass 3")
    if not ok:
        return False, err

    if not p3_out.exists():
        return False, "Pass 3: ZONJ output file not found after run"

    # --- Pass 4 (optional) ---
    final_out = out_dir / "scenes"
    final_out.mkdir(parents=True, exist_ok=True)
    if p4.exists():
        run_pass(
            p4,
            [p3_out.name, "--era", "Unknown", "--location", "Unknown", "--output-dir", str(final_out)],
            workdir,
            "Pass 4",
        )

    # Copy ZONJ to scenes output
    dst = final_out / p3_out.name
    safe_copy(p3_out, dst)

    # POST to runtime if requested
    if runtime:
        try:
            data = json.loads(p3_out.read_text(encoding="utf-8"))
            ok, err = post_scene(runtime, data, base)
            if not ok:
                return True, f"Pipeline OK but runtime POST failed: {err}"
        except Exception as e:
            return True, f"Pipeline OK but runtime POST error: {e}"

    return True, ""


def cmd_pipeline(args):
    pipeline_dir = resolve_abs(args.pipeline_dir)  # ABSOLUTE — done here, before any chdir
    out_dir      = resolve_abs(args.out)
    runtime      = args.runtime
    dry_run      = args.dry_run

    if not pipeline_dir or not pipeline_dir.exists():
        print(f"[ERROR] --pipeline-dir not found: {pipeline_dir}")
        return 1

    # Parse include/exclude patterns
    include_pats = [p.strip() for p in args.include.split(",")] if args.include else []
    exclude_pats = [p.strip() for p in args.exclude.split(",")] if args.exclude else []

    # Collect input files
    raw_files = []
    if args.file:
        f = resolve_abs(args.file)
        if not f.exists():
            print(f"[ERROR] File not found: {f}")
            return 1
        raw_files = [f]
    elif args.scan:
        scan_dir = resolve_abs(args.scan)
        all_files = sorted(p for p in scan_dir.rglob("*") if p.suffix in {".txt", ".md"})

        seen_stems = set()
        for p in all_files:
            name = p.name
            stem = p.stem

            # Skip junk by default
            if is_junk(name):
                continue

            # Apply explicit include filter (overrides chapter detection)
            if include_pats:
                if not matches_include(name, include_pats):
                    continue
            else:
                # Default: only canonical chapter filenames
                if not is_chapter(name):
                    continue

            # Apply explicit exclude filter
            if exclude_pats and matches_exclude(name, exclude_pats):
                continue

            # Deduplicate: if same stem seen already, keep first occurrence
            if stem in seen_stems:
                continue
            seen_stems.add(stem)

            raw_files.append(p)

    elif args.vault:
        vault_dir = resolve_abs(args.vault)
        all_md = sorted(p for p in vault_dir.rglob("*.md"))
        seen_stems = set()
        for p in all_md:
            if is_junk(p.name):
                continue
            if include_pats and not matches_include(p.name, include_pats):
                continue
            if p.stem not in seen_stems:
                seen_stems.add(p.stem)
                raw_files.append(p)

    counts = {"success": 0, "fail": 0}

    print("=" * 60)
    print("  EngAIn Ingest System")
    print(f"  Files found: {len(raw_files)}")
    print(f"    raw_text: {len(raw_files)}")
    print(f"  Output: {out_dir}")
    print("=" * 60)

    for i, f in enumerate(raw_files, 1):
        label = f.name
        print(f"[{i}/{len(raw_files)}] raw_text             → {label}")
        ok, msg = run_pipeline(f, pipeline_dir, out_dir, dry_run, runtime)
        if ok:
            counts["success"] += 1
            if msg:
                print(f"  ⚠ {msg}")
            else:
                print(f"  ✓ done → {out_dir}/scenes/zonj_{f.stem}.json")
        else:
            counts["fail"] += 1
            print(f"  ✗ {msg}")

    print("=" * 60)
    print("  INGEST COMPLETE")
    print(f"  Total: {len(raw_files)}  Success: {counts['success']}  Failed: {counts['fail']}")
    manifest_path = out_dir / "ingest_manifest.json"
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps({"total": len(raw_files), **counts}, indent=2))
    print(f"  Manifest: {manifest_path}")
    print("=" * 60)
    return 0 if counts["fail"] == 0 else 1


# ---------------------------------------------------------------------------
# Mode: --trixel
# ---------------------------------------------------------------------------

def cmd_trixel(args):
    trixel_dir = resolve_abs(args.trixel)
    out_dir    = resolve_abs(args.out)
    dry_run    = args.dry_run

    jsonl_files = sorted(trixel_dir.rglob("*.jsonl"))
    print("=" * 60)
    print("  EngAIn TRIXEL Ingest")
    print(f"  JSONL score files found: {len(jsonl_files)}")
    print("=" * 60)

    if dry_run:
        for jf in jsonl_files:
            print(f"  [trixel] {jf}")
        return 0

    assets_dir = out_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    for jf in jsonl_files:
        strokes = []
        try:
            for line in jf.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                # Support both flat {x,y,color} and nested {action:{x,y,color}}
                action = obj.get("action", obj)
                if "x" in action and "y" in action:
                    strokes.append(action)
        except Exception as e:
            print(f"  ⚠ {jf.name}: parse error: {e}")
            continue

        manifest = {
            "source": str(jf),
            "stroke_count": len(strokes),
            "asset_id": jf.stem,
        }
        dst_json = assets_dir / f"{jf.stem}_asset.json"
        dst_json.write_text(json.dumps(manifest, indent=2))

        # Reconstruct PNG if Pillow available
        try:
            from PIL import Image
            size = 64
            img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            pixels = img.load()
            for s in strokes:
                x, y = int(s.get("x", 0)), int(s.get("y", 0))
                color = s.get("color", [255, 255, 255])
                if isinstance(color, list) and len(color) >= 3:
                    if 0 <= x < size and 0 <= y < size:
                        pixels[x, y] = tuple(color[:3]) + (255,)
            img_path = assets_dir / f"{jf.stem}.png"
            img.save(str(img_path))
            print(f"  ✓ {jf.stem} → {img_path.name} ({len(strokes)} strokes)")
        except ImportError:
            print(f"  ✓ {jf.stem} → manifest only (pip install pillow for PNG)")
        except Exception as e:
            print(f"  ⚠ {jf.stem} → PNG failed: {e}")

    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="EngAIn Unified Ingest Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process one chapter (pipeline-dir = current directory)
  python3 engain_ingest.py --file 03_Fist_contact.txt --out ./ingested/ --pipeline-dir .

  # Process all chapters in a book folder
  python3 engain_ingest.py --scan ./book/ --out ./ingested/ --pipeline-dir .

  # Load existing ZONJ files into runtime (dispatch is disabled in this version)
  python3 engain_ingest.py --load-zonj ./game_scenes/ --out ./loaded/

  # Dry run
  python3 engain_ingest.py --scan ./book/ --out ./ingested/ --dry-run

  # Ingest TRIXEL scores
  python3 engain_ingest.py --trixel ./scores/ --out ./ingested/
""",
    )

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--file",      help="Process a single chapter file")
    mode.add_argument("--scan",      help="Process all .txt/.md files in a directory")
    mode.add_argument("--vault",     help="Process Obsidian vault directory")
    mode.add_argument("--trixel",    help="Ingest TRIXEL brush score JSONL directory")
    mode.add_argument("--load-zonj", help="Load pre-processed ZONJ files into runtime")

    parser.add_argument("--out",          required=True, help="Output directory")
    parser.add_argument("--pipeline-dir", default=".",   help="Directory containing pass1/2/3/4 scripts (default: current dir)")
    parser.add_argument("--runtime",      default=None,  help="Runtime URL (dispatch is disabled in this version)")
    parser.add_argument("--include",      default=None,  help="Comma-separated glob patterns to include, e.g. 'act_*,Chapter_*'")
    parser.add_argument("--exclude",      default=None,  help="Comma-separated glob patterns to exclude, e.g. 'revised*'")
    parser.add_argument("--no-recursive", action="store_true", help="Don't recurse into subdirectories for --scan")
    parser.add_argument("--dry-run",      action="store_true", help="Discover files without processing")

    args = parser.parse_args()

    if args.load_zonj:
        return cmd_load_zonj(args)
    elif args.trixel:
        return cmd_trixel(args)
    else:
        return cmd_pipeline(args)


if __name__ == "__main__":
    raise SystemExit(main())
