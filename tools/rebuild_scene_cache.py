#!/usr/bin/env python3
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

# Paths
ENGAIN_ROOT = Path("/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn")
MANIFEST_PATH = ENGAIN_ROOT / "manifests/engain_manifest.json"
CACHE_ROOT = ENGAIN_ROOT / ".engain_cache"
CACHE_PARSED = CACHE_ROOT / "parsed"
CACHE_SCENES = CACHE_PARSED / "scenes"
CACHE_HASHES = CACHE_PARSED / "chapter_hashes.json"

CHAPTER_PATTERN = re.compile(r"^\d+_[a-zA-Z0-9_]+$")
PLAYABLE_SCENE_RE = re.compile(r"^\d+_[a-z0-9_]+$")

if not MANIFEST_PATH.exists():
    print(f"[FAIL] Missing central manifest: {MANIFEST_PATH}")
    sys.exit(1)

manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
active_vault_id = manifest.get("active", {}).get("vault")
vault_entry = manifest["vaults"][active_vault_id]
VAULT_PATH = Path(vault_entry["root"])
VAULT_MANIFEST_PATH = Path(vault_entry["manifest"])
active_scene_lib_id = manifest.get("active", {}).get("scene_library")
scene_lib_entry = manifest["scene_libraries"][active_scene_lib_id]
SCENE_LIBRARY_ROOT = Path(scene_lib_entry["root"])
SCENE_INDEX_PATH = Path(scene_lib_entry["index"])

GAME_SCENES_DIR = ENGAIN_ROOT / "mettaext/compiled/pipeline_work/game_scenes"

def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def _load_vault_sources(vault_manifest_path: Path):
    if not vault_manifest_path.exists():
        print(f"[FAIL] Missing vault manifest: {vault_manifest_path}")
        sys.exit(1)

    try:
        data = json.loads(vault_manifest_path.read_text(encoding="utf-8"))
    except Exception:
        print(f"[FAIL] Invalid JSON in vault manifest: {vault_manifest_path}")
        sys.exit(1)

    source_files = data.get("source_files")
    if not isinstance(source_files, list) or not source_files:
        print("[FAIL] vault.manifest.json must contain a non-empty 'source_files' list")
        sys.exit(1)

    resolved_vault = VAULT_PATH.resolve()

    out = []
    for s in source_files:
        if not isinstance(s, str) or not s.strip():
            print("[FAIL] vault.manifest.json entries must be non-empty strings")
            sys.exit(1)
        p = Path(s)
        if not p.is_absolute():
            p = vault_manifest_path.parent / p
        if not p.exists() or not p.is_file():
            print(f"[WARN] Skipping {p}: file does not exist")
            continue

        resolved_p = p.resolve()

        # Validation Rule 1: source path is inside VAULT_PATH
        try:
            is_relative = resolved_p.is_relative_to(resolved_vault)
        except AttributeError:
            try:
                resolved_p.relative_to(resolved_vault)
                is_relative = True
            except ValueError:
                is_relative = False

        if not is_relative:
            continue

        # Validation Rule 2: source parent is exactly one level below VAULT_PATH
        if resolved_p.parent.parent != resolved_vault:
            continue

        # Validation Rule 3: parent directory starts with book_
        if not resolved_p.parent.name.startswith("book_"):
            continue

        # Validation Rule 4: source file suffix is .md or .txt
        if resolved_p.suffix.lower() not in (".md", ".txt"):
            continue

        # Validation Rule 5: source stem already matches allowed chapter pattern
        if not CHAPTER_PATTERN.match(resolved_p.stem):
            continue

        out.append(resolved_p)
    return out

def merge_game_scene_into_semantic(chapter_stem: str, semantic_path: Path) -> bool:
    game_file = GAME_SCENES_DIR / f"{chapter_stem}.json"
    if not game_file.exists():
        print(f"[MERGE] No game scene found for '{chapter_stem}', skipping merge.")
        return False

    try:
        semantic = json.loads(semantic_path.read_text(encoding="utf-8"))
        game = json.loads(game_file.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[MERGE][WARN] Could not read files for merge ({chapter_stem}): {e}")
        return False

    if not isinstance(semantic, dict) or not isinstance(game, dict):
        print(f"[MERGE][WARN] Unexpected format in one of the merge sources for '{chapter_stem}'")
        return False

    # Merge — preserve all semantic compiler output
    semantic["events"]        = game.get("events", [])
    semantic["locations"]     = game.get("locations", [])
    semantic["initial_state"] = game.get("initial_state", {})
    semantic["game_metadata"] = game.get("metadata", {})   # isolated key

    try:
        semantic_path.write_text(json.dumps(semantic, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[MERGE] Merged game scene into {semantic_path.name} "
              f"({len(semantic['events'])} events, {len(semantic['locations'])} locations)")
        return True
    except Exception as e:
        print(f"[MERGE][WARN] Could not write merged output for '{chapter_stem}': {e}")
        return False

def normalize_scene_id(raw: str) -> str:
    s = raw.lower()
    s = s.replace(".zonj.json", "").replace(".zonj", "").replace(".json", "")
    s = s.replace("zonj_", "").replace("scene.", "")
    s = " ".join(s.split()).replace(" ", "_")
    return s

def build_scene_library():
    scene_dict = {}
    if CACHE_SCENES.exists():
        for path in sorted(CACHE_SCENES.glob("*_with_semantics.zonj.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue

            if not isinstance(data, dict):
                continue

            sid = normalize_scene_id(path.name.replace("_with_semantics", ""))
            if not PLAYABLE_SCENE_RE.match(sid):
                continue

            scene_dict[sid] = {
                "id": sid,
                "name": sid,
                "file": str(path),
                "format_status": "playable",
                "actions": [
                    "Open Scene",
                    "Rerun Parse",
                    "Rerun ZW Compiler",
                    "Rerun AP",
                    "Full Rebuild"
                ]
            }

    if scene_dict:
        items = sorted(scene_dict.values(), key=lambda x: x["id"])
        SCENE_INDEX_PATH.write_text(
            json.dumps({"count": len(items), "scenes": items}, indent=2),
            encoding="utf-8"
        )
        print(f"[OK] Found {len(items)} clean scenes")
        print(f"[OK] Scene index written: {SCENE_INDEX_PATH}")

def _save_hash_cache(data):
    CACHE_PARSED.mkdir(parents=True, exist_ok=True)
    CACHE_HASHES.write_text(json.dumps(data, indent=2), encoding="utf-8")

def main():
    print("========================================")
    print(" 🎫 Scene Cache Rebuild Command")
    print("========================================\n")

    CACHE_SCENES.mkdir(parents=True, exist_ok=True)

    chapters = _load_vault_sources(VAULT_MANIFEST_PATH)
    if not chapters:
        print(f"❌ No chapter source files found under {VAULT_PATH}")
        sys.exit(1)

    base_dir = ENGAIN_ROOT / "mettaext"
    master_script = base_dir / "master_pipeline.py"
    zw_script = base_dir / "zw_compiler.py"
    temp_out = base_dir / "compiled" / "pipeline_work"

    scenes_attempted = len(chapters)
    scenes_rebuilt = 0
    failures = 0
    terrain_family_present = 0
    default_terrain_count = 0

    hashes_updated = {}

    for chapter in chapters:
        print(f"\n[REBUILD] Processing {chapter.name}...")
        
        # Run master_pipeline (forces re-parsing and ignores caches)
        cmd_master = [
            sys.executable,
            str(master_script),
            str(chapter),
            "--output-dir",
            str(temp_out),
            "--manifest",
            str(MANIFEST_PATH)
        ]
        
        result_master = subprocess.run(cmd_master, cwd=base_dir)
        if result_master.returncode != 0:
            print(f"❌ master_pipeline.py failed for {chapter.name}")
            failures += 1
            continue

        produced_zonj = temp_out / f"{chapter.stem}.zonj.json"
        if not produced_zonj.exists():
            print(f"❌ produced_zonj missing for {chapter.name}")
            failures += 1
            continue

        final_out = CACHE_SCENES / f"{chapter.stem}_with_semantics.zonj.json"
        
        # Run ZW-Compiler
        cmd_zw = [
            sys.executable,
            str(zw_script),
            str(produced_zonj),
            str(final_out)
        ]
        
        result_zw = subprocess.run(cmd_zw, cwd=base_dir)
        if result_zw.returncode != 0:
            print(f"❌ zw_compiler.py failed for {chapter.name}")
            failures += 1
            continue

        # Merge game scene
        merge_success = merge_game_scene_into_semantic(chapter.stem, final_out)
        if not merge_success:
            print(f"⚠️ Game scene merge skipped or failed for {chapter.name}")

        # Hash updates
        digest = _sha256_file(chapter)
        hashes_updated[str(chapter.resolve())] = digest

        # Read resolved terrain family for summary
        try:
            scene_data = json.loads(final_out.read_text(encoding="utf-8"))
            
            # Canonical Resolution Logic matching Boot.gd _resolve_terrain_family
            terrain = scene_data.get("terrain_family")
            if not terrain:
                terrain = scene_data.get("@terrain_family")
            if not terrain:
                meta = scene_data.get("metadata", {})
                if isinstance(meta, dict):
                    terrain = meta.get("terrain_family")
            if not terrain:
                t_meta = scene_data.get("terrain_metadata", {})
                if isinstance(t_meta, dict):
                    terrain = t_meta.get("terrain_family")

            # Check if resolved to non-default
            if terrain and terrain != "default" and terrain != "unknown" and terrain != "":
                terrain_family_present += 1
                print(f"✓ Terrain family resolved: {terrain}")
            else:
                default_terrain_count += 1
                print(f"✓ Terrain family: default (or unknown)")

            scenes_rebuilt += 1
        except Exception as e:
            print(f"❌ Failed to parse resulting scene JSON for {chapter.stem}: {e}")
            failures += 1

    # Rebuild scene index
    build_scene_library()

    # Save hash cache so start_button.py sees them as up-to-date
    zw_script_script = base_dir / "zw_compiler.py"
    compiler_fp = _sha256_file(zw_script_script) if zw_script_script.exists() else ""
    _save_hash_cache({
        "chapters": hashes_updated,
        "compiler_fingerprint": compiler_fp
    })

    # Print summary exactly matching task specifications
    print("\n" + "="*40)
    print(" 🎫 REBUILD CACHE SUMMARY")
    print("="*40)
    print(f"  scenes attempted:          {scenes_attempted}")
    print(f"  scenes rebuilt:            {scenes_rebuilt}")
    print(f"  terrain_family present:    {terrain_family_present}")
    print(f"  default terrain count:     {default_terrain_count}")
    print(f"  failures:                  {failures}")
    print("="*40 + "\n")

if __name__ == "__main__":
    main()
