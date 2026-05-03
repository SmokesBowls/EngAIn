#!/usr/bin/env python3
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ENGAIN_ROOT = Path("/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn")
MANIFEST_PATH = ENGAIN_ROOT / "manifests/engain_manifest.json"
RUNTIME_URL = "http://127.0.0.1:8080"

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


def _discover_chapter_sources(vault_root: Path, vault_manifest_path: Path):
    if not vault_manifest_path.exists():
        print(f"[FAIL] Vault manifest missing: {vault_manifest_path}")
        sys.exit(1)

    data = json.loads(vault_manifest_path.read_text(encoding="utf-8"))
    source_files = data.get("source_files")
    if not isinstance(source_files, list) or not source_files:
        print("[FAIL] vault.manifest.json missing required field: source_files (non-empty list)")
        sys.exit(1)

    out = []
    for rel in source_files:
        if not isinstance(rel, str) or not rel.strip():
            print("[FAIL] vault.manifest.json has invalid source_files entry (must be non-empty string)")
            sys.exit(1)
        p = Path(rel)
        if not p.is_absolute():
            p = vault_root / p
        if not p.exists() or not p.is_file():
            print(f"[FAIL] source_files entry does not resolve to a file: {p}")
            sys.exit(1)
        out.append(p)
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
    compiler_script = ENGAIN_ROOT / "mettaext/zw_compiler.py"
    compiler_fp = _sha256_file(compiler_script) if compiler_script.exists() else ""
    compiler_changed = compiler_fp != (state.get("compiler_fingerprint") or "")

    chapters = _discover_chapter_sources(VAULT_PATH, VAULT_MANIFEST_PATH)
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
        run([sys.executable, str(master_script), str(chapter), "--output-dir", str(temp_out)], cwd=base_dir)
        produced_zonj = temp_out / f"{chapter.stem}.zonj.json"
        if not produced_zonj.exists():
            print(f"[FAIL] Missing P1-P5 output: {produced_zonj}")
            sys.exit(1)
        final_out = CACHE_SCENES / f"{chapter.stem}_with_semantics.zonj.json"
        run([sys.executable, str(zw_script), str(produced_zonj), str(final_out)], cwd=base_dir)

    state["chapters"] = updated
    state["compiler_fingerprint"] = compiler_fp
    _save_hash_cache(state)
    print(f"[OK] Rebuilt {len(changed)} changed/new chapters.")


def normalize_scene_id(raw: str) -> str:
    s = raw.lower()
    s = s.replace(".zonj.json", "").replace(".zonj", "").replace(".json", "")
    s = s.replace("zonj_", "").replace("scene.", "")
    s = " ".join(s.split()).replace(" ", "_")
    return s


def build_scene_library():
    print("\n=== STEP 3: Build Scene Library ===")
    candidates = [CACHE_SCENES, SCENE_LIBRARY_ROOT / "scenes", SCENE_LIBRARY_ROOT / "runtime_scenes", ENGAIN_ROOT / "mettaext/game_scenes"]
    scene_dict = {}
    for d in candidates:
        if not d.exists():
            continue
        for path in sorted(d.glob("*")):
            if not (path.name.endswith(".json") or path.name.endswith(".zonj")):
                continue
            name = path.name
            if name.startswith("scene.") or name.startswith("out_pass"):
                continue
            sid = normalize_scene_id(name)
            if sid in scene_dict and scene_dict[sid]["format_status"] == "playable":
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if not isinstance(data, dict):
                continue
            status = "legacy_playable"
            if any(k in data for k in ("scene_id", "id", "@id")):
                status = "playable"
            elif isinstance(data.get("payload"), dict) and any(k in data["payload"] for k in ("scene_id", "id", "@id")):
                status = "playable"
            scene_dict[sid] = {"id": sid, "name": sid, "file": str(path), "format_status": status,
                               "actions": ["Open Scene", "Rerun Parse", "Rerun ZW Compiler", "Rerun AP", "Full Rebuild"]}
    if not scene_dict:
        print("[FAIL] No valid scenes found in any known directory")
        sys.exit(1)
    items = sorted(scene_dict.values(), key=lambda x: x["id"])
    SCENE_INDEX_PATH.write_text(json.dumps({"count": len(items), "scenes": items}, indent=2), encoding="utf-8")
    print(f"[OK] Found {len(items)} clean scenes")
    print(f"[OK] Scene index written: {SCENE_INDEX_PATH}")


def confirm_runtime():
    print("\n=== STEP 4: Confirm runtime ===")
    result = subprocess.run(["curl", f"{RUNTIME_URL}/snapshot"], capture_output=True, text=True)
    if result.returncode != 0 or not result.stdout.strip():
        print("[WARN] Could not confirm runtime snapshot")
    else:
        print("[OK] Runtime snapshot received")


def main():
    print("\n==============================")
    print(" EngAIn START BUTTON")
    print("==============================\n")
    ensure_stack()
    run_cache_aware_pipeline()
    build_scene_library()
    confirm_runtime()
    print("\n==============================")
    print(" SCENE LIBRARY INITIALIZED")
    print("==============================\n")
    print("Launcher complete. Use scene actions from the generated index.")


if __name__ == "__main__":
    main()
