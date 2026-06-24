#!/usr/bin/env python3
import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path

ENGAIN_ROOT = Path("/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn")
MANIFEST_PATH = ENGAIN_ROOT / "manifests/engain_manifest.json"
RUNTIME_URL = "http://127.0.0.1:8080"
CACHE_ROOT = ENGAIN_ROOT / ".engain_cache"
CACHE_PARSED = CACHE_ROOT / "parsed"
CACHE_SCENES = CACHE_PARSED / "scenes"
CACHE_HASHES = CACHE_PARSED / "chapter_hashes.json"

PLAYABLE_SCENE_RE = re.compile(r"^\d+_[a-z0-9_]+$")
CHAPTER_PATTERN = re.compile(r"^\d+_[a-zA-Z0-9_]+$")

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

cache_parsed_dir = scene_lib_entry.get("cache_parsed_dir")
if not isinstance(cache_parsed_dir, str) or not cache_parsed_dir.strip():
    print("[FAIL] Missing required manifest field scene_libraries.<active>.cache_parsed_dir")
    sys.exit(1)
CACHE_PARSED = Path(cache_parsed_dir)

cache_scenes_dir = scene_lib_entry.get("cache_scenes_dir")
if not isinstance(cache_scenes_dir, str) or not cache_scenes_dir.strip():
    print("[FAIL] Missing required manifest field scene_libraries.<active>.cache_scenes_dir")
    sys.exit(1)
CACHE_SCENES = Path(cache_scenes_dir)

chapter_hashes_path = scene_lib_entry.get("chapter_hashes_path")
if not isinstance(chapter_hashes_path, str) or not chapter_hashes_path.strip():
    print("[FAIL] Missing required manifest field scene_libraries.<active>.chapter_hashes_path")
    sys.exit(1)
CACHE_HASHES = Path(chapter_hashes_path)


def run(cmd, cwd=None, allow_failure=False):
    print(f"[RUN] {' '.join(str(c) for c in cmd)}")
    result = subprocess.run(cmd, cwd=cwd)
    if result.returncode != 0 and not allow_failure:
        print(f"[FAIL] Command failed: {' '.join(str(c) for c in cmd)}")
        sys.exit(1)
    return result.returncode


def ensure_stack():
    print("\n=== STEP 1: Ensure runtime stack ===")
    run(["./start_stack.fish"], cwd=ENGAIN_ROOT)
    time.sleep(2)


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
            print("[FAIL] vault.manifest.json source_files entries must be non-empty strings")
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
            print(f"[WARN] Skipping {p}: outside vault path {VAULT_PATH}")
            continue

        # Validation Rule 2: source parent is exactly one level below VAULT_PATH
        if resolved_p.parent.parent != resolved_vault:
            print(f"[WARN] Skipping {p}: parent is not exactly one level below vault path {VAULT_PATH}")
            continue

        # Validation Rule 3: parent directory starts with book_
        if not resolved_p.parent.name.startswith("book_"):
            print(f"[WARN] Skipping {p}: parent directory must start with 'book_'")
            continue

        # Validation Rule 4: source file suffix is .md or .txt
        if resolved_p.suffix.lower() not in (".md", ".txt"):
            print(f"[WARN] Skipping {p}: suffix must be .md or .txt")
            continue

        # Validation Rule 5: source stem already matches allowed chapter pattern
        if not CHAPTER_PATTERN.match(resolved_p.stem):
            print(f"[WARN] Skipping {p}: stem '{resolved_p.stem}' does not match allowed chapter pattern (e.g. 001_chapter_name or 23_beyond_identity)")
            continue

        out.append(resolved_p)
    return out


def _load_hash_cache():
    if not CACHE_HASHES.exists():
        return {"chapters": {}, "compiler_fingerprint": ""}
    try:
        data = json.loads(CACHE_HASHES.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {"chapters": {}, "compiler_fingerprint": ""}
        data.setdefault("chapters", {})
        data.setdefault("compiler_fingerprint", "")
        return data
    except Exception:
        return {"chapters": {}, "compiler_fingerprint": ""}


def _save_hash_cache(data):
    CACHE_PARSED.mkdir(parents=True, exist_ok=True)
    CACHE_HASHES.write_text(json.dumps(data, indent=2), encoding="utf-8")


def run_cache_aware_pipeline():
    print("\n=== STEP 2: Cache-aware parse/compile orchestration ===")
    CACHE_SCENES.mkdir(parents=True, exist_ok=True)
    state = _load_hash_cache()
    old = state.get("chapters", {})
    compiler_script = ENGAIN_ROOT / "tier3/mettaext/zw_compiler.py"
    compiler_fp = _sha256_file(compiler_script) if compiler_script.exists() else ""
    compiler_changed = compiler_fp != (state.get("compiler_fingerprint") or "")

    chapters = _load_vault_sources(VAULT_MANIFEST_PATH)
    if not chapters:
        print(f"[WARN] No chapter source files found under {VAULT_PATH}")
        return

    updated = {}
    changed = []
    for ch in chapters:
        digest = _sha256_file(ch)
        key = str(ch.resolve())
        updated[key] = digest
        if compiler_changed or old.get(key) != digest:
            changed.append(ch)

    if compiler_changed:
        print("[INFO] Compiler changed; forcing full rebuild of discovered chapters.")

    if not changed:
        print(f"[OK] Cache hit: {len(chapters)} chapters unchanged. Skipping parse/compile.")
        state["chapters"] = updated
        state["compiler_fingerprint"] = compiler_fp
        _save_hash_cache(state)
        return

    base_dir = ENGAIN_ROOT / "mettaext"
    master_script = base_dir / "master_pipeline.py"
    zw_script = base_dir / "zw_compiler.py"
    temp_out = base_dir / "compiled" / "pipeline_work"

    for chapter in changed:
        print(f"\n[CHAPTER] Rebuild {chapter.name}")
        run([sys.executable, str(master_script), str(chapter), "--output-dir", str(temp_out), "--manifest", str(MANIFEST_PATH)], cwd=base_dir)
        produced_zonj = temp_out / f"{chapter.stem}.zonj.json"
        if not produced_zonj.exists():
            print(f"[FAIL] Missing P1-P5 output: {produced_zonj}")
            sys.exit(1)
        final_out = CACHE_SCENES / f"{chapter.stem}_with_semantics.zonj.json"
        run([sys.executable, str(zw_script), str(produced_zonj), str(final_out)], cwd=base_dir)
        merge_game_scene_into_semantic(chapter.stem, final_out)

    state["chapters"] = updated
    state["compiler_fingerprint"] = compiler_fp
    _save_hash_cache(state)
    print(f"[OK] Rebuilt {len(changed)} changed/new chapters.")


GAME_SCENES_DIR = ENGAIN_ROOT / "tier3/mettaext/compiled/pipeline_work/game_scenes"


def merge_game_scene_into_semantic(chapter_stem: str, semantic_path: Path) -> bool:
    """
    Locate the pass5 game_scenes JSON for this chapter and merge its
    events / locations / initial_state into the semantic ZONJ.

    Rules:
      - game_metadata  ← game scene metadata dict  (new key, never overwrites compiler metadata)
      - events         ← from game scene
      - locations      ← from game scene
      - initial_state  ← from game scene
      - zon_blocks, spatial_hints, compiler_report, entities are UNTOUCHED.

    Returns True if merged, False if game scene was not found (non-fatal).
    """
    game_file = GAME_SCENES_DIR / f"{chapter_stem}.json"
    if not game_file.exists():
        # Try the scene_id format that pass5 may emit (strips leading digits prefix)
        # e.g.  03_Fist_contact  ->  03_Fist_contact  (already fine)
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
    print("\n=== STEP 3: Build Scene Library ===")

    scene_dict = {}

    # --- PASS 1: Load ONLY semantic scenes (authoritative) ---
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

    if not scene_dict:
        print("[FAIL] No valid scenes found in any known directory")
        sys.exit(1)

    items = sorted(scene_dict.values(), key=lambda x: x["id"])

    SCENE_INDEX_PATH.write_text(
        json.dumps({"count": len(items), "scenes": items}, indent=2),
        encoding="utf-8"
    )

    print(f"[OK] Found {len(items)} clean scenes")
    print(f"[OK] Scene index written: {SCENE_INDEX_PATH}")



def compile_missing_semantic_scenes():
    print("\n=== STEP 2.5: Compile Missing Semantic Scenes ===")

    raw_dir = SCENE_LIBRARY_ROOT / "scenes"
    if not raw_dir.exists():
        print("[WARN] No raw scene directory found:", raw_dir)
        return

    CACHE_SCENES.mkdir(parents=True, exist_ok=True)

    compiled = 0
    failed = 0

    for f in sorted(raw_dir.glob("*.json")):
        sid = normalize_scene_id(f.name)
        out = CACHE_SCENES / f"{sid}_with_semantics.zonj.json"

        if out.exists():
            continue

        print("[COMPILE]", f.name)

        result = subprocess.run([
            sys.executable,
            str(ENGAIN_ROOT / "tier3/mettaext/zw_compiler.py"),
            str(f),
            str(out)
        ])

        if result.returncode == 0:
            compiled += 1
            merge_game_scene_into_semantic(sid, out)
        else:
            failed += 1
            print("[WARN] Semantic compile failed:", f)

    print(f"[OK] Compiled {compiled} missing semantic scenes")
    if failed:
        print(f"[WARN] {failed} semantic scenes failed to compile")


def merge_all_game_scenes_into_semantics():
    """
    STEP 2.7: Walk every game_scenes JSON and merge it into the
    matching semantic file (if one exists in CACHE_SCENES).

    This catches all chapters that already have a semantic file but
    whose game scene was produced in the same or a prior run — so
    events/locations/initial_state are always up-to-date even if the
    semantic file was not rebuilt this session.
    """
    print("\n=== STEP 2.7: Merge Game Scenes into Semantic Outputs ===")

    if not GAME_SCENES_DIR.exists():
        print("[WARN] Game scenes directory not found:", GAME_SCENES_DIR)
        return

    game_files = sorted(GAME_SCENES_DIR.glob("*.json"))
    if not game_files:
        print("[WARN] No game scene files found in", GAME_SCENES_DIR)
        return

    merged = 0
    skipped = 0

    for gf in game_files:
        stem = gf.stem                          # e.g. "03_Fist_contact"

        # Skip stale artifacts whose stem still contains '.zonj' —
        # these are mis-named outputs from old pipeline runs and would
        # overwrite good merges with empty events.
        if ".zonj" in stem:
            skipped += 1
            continue

        sid  = normalize_scene_id(stem)         # normalised key
        semantic_path = CACHE_SCENES / f"{sid}_with_semantics.zonj.json"

        if not semantic_path.exists():
            skipped += 1
            continue

        if merge_game_scene_into_semantic(stem, semantic_path):
            merged += 1
        else:
            skipped += 1

    print(f"[OK] Merged {merged} game scenes into semantic outputs ({skipped} skipped — no matching semantic file)")


def confirm_runtime():
    print("\n=== STEP 4: Confirm runtime ===")
    result = subprocess.run(["curl", f"{RUNTIME_URL}/snapshot"], capture_output=True, text=True)
    if result.returncode != 0 or not result.stdout.strip():
        print("[WARN] Could not confirm runtime snapshot")
    else:
        print("[OK] Runtime snapshot received")


def confirm_tile_server():
    print("\n=== STEP 5: Confirm Trixel tile server ===")
    result = subprocess.run(["curl", "-s", "http://127.0.0.1:8766/health"], capture_output=True, text=True)
    if result.returncode != 0 or not result.stdout.strip():
        print("[WARN] Could not confirm Trixel tile server (health gate failed)")
    else:
        try:
            res = json.loads(result.stdout)
            if res.get("status") == "ok":
                print("[OK] Trixel tile server health gate passed")
            else:
                print(f"[WARN] Trixel tile server reported unhealthy status: {res}")
        except Exception as e:
            print(f"[WARN] Trixel tile server health response was invalid JSON: {e}")


def main():
    print("\n==============================")
    print(" EngAIn START BUTTON")
    print("==============================\n")
    ensure_stack()
    run_cache_aware_pipeline()
    merge_all_game_scenes_into_semantics()
    build_scene_library()
    confirm_runtime()
    confirm_tile_server()
    print("\n==============================")
    print(" SCENE LIBRARY INITIALIZED")
    print("==============================\n")
    print("Launcher complete. Use scene actions from the generated index.")


if __name__ == "__main__":
    main()


