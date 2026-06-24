#!/usr/bin/env python3
"""
Mettaext Vault Source Indexer

Purpose:
- Index source prose files from an Obsidian-style vault folder.
- Write the index into tier3/mettaext/stageroom/input/vaults/.
- Do not parse canon.
- Do not call runtime.
- Do not dispatch to EngAInOS, MrLore, GodotSim, Engionality, Godot, or Trixel.

Authority:
- Source discovery only.
- Evidence only.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


TEXT_EXTENSIONS = {".md", ".txt"}


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "unknown"


def looks_like_source_file(path: Path) -> bool:
    if path.suffix.lower() not in TEXT_EXTENSIONS:
        return False

    parts = {part.lower() for part in path.parts}

    ignored_dirs = {
        ".obsidian",
        ".git",
        "__pycache__",
        "node_modules",
        ".trash",
        ".stfolder",
        "build",
        "_work",
        "compiled",
        "pipeline_work",
        "proof_output",
        "proofroom",
    }

    if parts & ignored_dirs:
        return False

    # Do not index generated pipeline artifacts as authored source prose.
    generated_prefixes = (
        "out_pass",
        "zonj_",
    )
    if path.name.lower().startswith(generated_prefixes):
        return False

    if path.name.lower().endswith((".zonj.json", ".zon", ".metta")):
        return False

    return True


def detect_source_text_id(path: Path, vault_root: Path) -> str:
    stem = path.stem

    # Preserve explicit chapter-style file names when present.
    # Examples:
    #   chapter.999_abc_smoke.md -> chapter.999_abc_smoke
    #   059_eyes_of_eternity.md -> chapter.059_eyes_of_eternity
    if stem.startswith("chapter."):
        return stem

    match = re.search(r"(?<!\d)(\d{1,4})(?!\d)", stem)
    if match:
        number = match.group(1).zfill(3)
        clean = re.sub(r"^\D*0*\d{1,4}[_\-\.\s]*", "", stem)
        return f"chapter.{number}_{slugify(clean or stem)}"

    rel = path.relative_to(vault_root)
    return f"source.{slugify(str(rel.with_suffix('')))}"


def index_vault(vault_root: Path) -> dict[str, Any]:
    vault_root = vault_root.resolve()

    if not vault_root.exists():
        raise FileNotFoundError(f"Vault root does not exist: {vault_root}")

    files = []
    for path in sorted(vault_root.rglob("*")):
        if not path.is_file():
            continue
        if not looks_like_source_file(path):
            continue

        stat = path.stat()
        rel = path.relative_to(vault_root)

        files.append({
            "source_text_id": detect_source_text_id(path, vault_root),
            "path": str(path),
            "relative_path": str(rel),
            "extension": path.suffix.lower(),
            "size_bytes": stat.st_size,
        })

    return {
        "contract": "mettaext.vault_source_index.v1",
        "source": "mettaext",
        "authority": "source_discovery",
        "vault_app_required": False,
        "vault_root": str(vault_root),
        "has_obsidian_config": (vault_root / ".obsidian").is_dir(),
        "file_count": len(files),
        "files": files,
        "authority_note": "Source index only. Not parse truth, not canon, not runtime.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Index source files from an Obsidian-style vault folder.")
    parser.add_argument(
        "--vault-root",
        required=True,
        help="Path to the vault root. Use the parent folder that contains .obsidian, not .obsidian itself.",
    )
    parser.add_argument(
        "--output",
        default="tier3/mettaext/stageroom/input/vaults/vault_source_index.json",
        help="Output JSON index path.",
    )
    args = parser.parse_args()

    vault_root = Path(args.vault_root)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    index = index_vault(vault_root)
    output_path.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")

    print("VAULT_SOURCE_INDEX_WRITTEN=TRUE")
    print(f"VAULT_ROOT={index['vault_root']}")
    print(f"HAS_OBSIDIAN_CONFIG={str(index['has_obsidian_config']).upper()}")
    print(f"FILE_COUNT={index['file_count']}")
    print(f"OUTPUT={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
