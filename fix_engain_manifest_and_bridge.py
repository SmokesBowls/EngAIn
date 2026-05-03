#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ENGAIN_ROOT = Path("/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn")
VAULT_ROOT = Path("/home/mytruelove/obsidian/obsidianburdenNov25")
MANIFEST_PATH = VAULT_ROOT / "vault.manifest.json"

CANONICAL_SCENE_DIR = ENGAIN_ROOT / "mettaext" / "ingested" / "runtime_scenes"
CANONICAL_CACHE_DIR = ENGAIN_ROOT / ".vault_cache" / "obsidianburdennov25"
VAULT_MIRROR_DIR = VAULT_ROOT / ".engain" / "build" / "obsidianburdennov25"

def main() -> int:
    if not MANIFEST_PATH.exists():
        raise SystemExit(f"ERROR: manifest not found: {MANIFEST_PATH}")

    if not CANONICAL_SCENE_DIR.exists():
        raise SystemExit(f"ERROR: canonical scene dir not found: {CANONICAL_SCENE_DIR}")

    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    content = data.setdefault("content", {})
    build = data.setdefault("build", {})
    runtime = data.setdefault("runtime", {})

    content.setdefault("source_markdown", {"dir": "."})
    content["zonj_scenes"] = {
        "dir": str(CANONICAL_SCENE_DIR)
    }

    build["output_dir"] = str(CANONICAL_CACHE_DIR)

    runtime["mirror_to_vault"] = True
    runtime["vault_mirror_dir"] = ".engain/build/obsidianburdennov25"
    runtime["make_mirror_readonly"] = True

    CANONICAL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    VAULT_MIRROR_DIR.mkdir(parents=True, exist_ok=True)

    MANIFEST_PATH.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print("Updated manifest:")
    print(MANIFEST_PATH)
    print()
    print(json.dumps(data, indent=2, ensure_ascii=False))
    print()
    print("Validation:")
    print(f"  scene_dir exists: {CANONICAL_SCENE_DIR.exists()}  -> {CANONICAL_SCENE_DIR}")
    print(f"  cache_dir exists: {CANONICAL_CACHE_DIR.exists()}  -> {CANONICAL_CACHE_DIR}")
    print(f"  vault_mirror exists: {VAULT_MIRROR_DIR.exists()}  -> {VAULT_MIRROR_DIR}")

    zonj_files = sorted(CANONICAL_SCENE_DIR.glob("*.zonj"))
    print(f"  zonj count: {len(zonj_files)}")
    for p in zonj_files[:10]:
        print(f"    - {p.name}")

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
