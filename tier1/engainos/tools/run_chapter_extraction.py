#!/usr/bin/env python3
"""
Run the December-2025 Mettaext pipeline (narrative_to_game.py) on one chapter
named by its Tier 1 catalog_id, and write a provenance receipt beside the output.

    python3 -m tier1.engainos.tools.run_chapter_extraction --catalog-id "book_01_x/001_y.md"

Authority:
- The chapter is chosen only through Tier 1: resolve_active_vault() + build_chapter_catalog().
  A catalog_id not in the live catalog is refused, so no arbitrary path can be read.
- Mettaext runs unchanged as a separate process and calls nothing. It reads a copy of
  the source made here (so nothing it does can write into the vault) and writes only
  under Stageroom.
- Output is a candidate, not accepted state. Nothing is sent to 8765 or 8080.

Layout: <stageroom>/output/narrative_to_game/catalog/<book_id>/<file_name>/<sha12>/
    source/<file_name>   exact bytes extracted (hash re-checked against the catalog)
    game_scenes/         Pass 5 output
    pipeline_work/       Pass 1-4 intermediates
    run.log              pipeline stdout/stderr
    receipt.json         written last; its presence means the run finished
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

from tier1.engainos.tools.chapter_discovery import build_chapter_catalog
from tier1.engainos.tools.vault_discovery import resolve_active_vault

RECEIPT_CONTRACT = "engain.chapter_extraction_receipt.v1"
REPO_ROOT = Path(__file__).resolve().parents[3]
METTAEXT_DIR = REPO_ROOT / "tier3" / "mettaext"
DRIVER = METTAEXT_DIR / "narrative_to_game.py"
PASS_SCRIPTS = ("pass1_explicit.py", "pass2_core.py", "pass3_merge.py",
                "pass4_zon_bridge.py", "pass5_game_bridge.py")
DEFAULT_STAGEROOM = METTAEXT_DIR / "stageroom"


class ExtractionError(Exception):
    pass


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _git(*args: str) -> Optional[str]:
    try:
        r = subprocess.run(["git", "-C", str(REPO_ROOT), *args], capture_output=True, text=True, timeout=30)
        return r.stdout.strip() if r.returncode == 0 else None
    except OSError:
        return None


def extraction_dir(stageroom: Path, entry: dict) -> Path:
    book_id, file_name = entry["catalog_id"].split("/", 1)
    return (stageroom / "output" / "narrative_to_game" / "catalog" / book_id / file_name
            / entry["source_sha256"][:12])


def find_entry(catalog_id: str, manifest_path: Optional[Path] = None) -> tuple[dict, dict]:
    vault = resolve_active_vault(manifest_path)
    if vault["status"] != "ok":
        raise ExtractionError("vault not resolved by Tier 1: " + "; ".join(vault["problems"]))
    catalog = build_chapter_catalog(Path(vault["root"]), Path(vault["manifest_path"]))
    for book in catalog["books"]:
        for entry in book["chapters"]:
            if entry["catalog_id"] == catalog_id:
                return vault, entry
    raise ExtractionError(f"catalog_id not in the live catalog: {catalog_id!r}")


def run_extraction(catalog_id: str, manifest_path: Optional[Path] = None,
                   stageroom: Path = DEFAULT_STAGEROOM) -> dict:
    """Run once per (catalog_id, source hash). Returns the receipt; an existing finished receipt is returned as is."""
    vault, entry = find_entry(catalog_id, manifest_path)
    out = extraction_dir(Path(stageroom), entry)
    receipt_path = out / "receipt.json"
    if receipt_path.is_file():
        return json.loads(receipt_path.read_text(encoding="utf-8"))
    if out.exists():
        raise ExtractionError(f"unfinished earlier run left {out}; inspect it and remove it to retry")

    out.mkdir(parents=True)
    src_copy = out / "source" / Path(entry["path"]).name
    src_copy.parent.mkdir()
    shutil.copyfile(entry["path"], src_copy)
    copied_sha = _sha256(src_copy)
    if copied_sha != entry["source_sha256"]:
        raise ExtractionError(f"source changed while copying ({entry['path']}); rerun to extract the new version")

    cmd = [sys.executable, str(DRIVER), str(src_copy),
           "--output", str(out / "game_scenes"), "--work-dir", str(out / "pipeline_work")]
    started = time.time()
    with (out / "run.log").open("w", encoding="utf-8") as log:
        proc = subprocess.run(cmd, cwd=str(REPO_ROOT), stdout=log, stderr=subprocess.STDOUT)

    outputs = sorted(p for p in out.rglob("*") if p.is_file() and p.name != "receipt.json")
    receipt = {
        "contract": RECEIPT_CONTRACT,
        "status": "candidate" if proc.returncode == 0 else "failed",
        "acceptance": "not accepted",
        "catalog_id": entry["catalog_id"],
        "chapter_id": entry["chapter_id"],
        "source_sha256": entry["source_sha256"],
        "source_path": entry["path"],
        "vault": {k: vault[k] for k in ("vault_id", "root", "source", "authority_fields")},
        "extractor": {
            "driver": str(DRIVER.relative_to(REPO_ROOT)),
            "script_sha256": {name: _sha256(p) for name, p in
                              [(DRIVER.name, DRIVER)] + [(s, METTAEXT_DIR / "passroom" / s) for s in PASS_SCRIPTS]},
            "git_head": _git("rev-parse", "HEAD"),
            "mettaext_dirty": bool(_git("status", "--porcelain", "--", "tier3/mettaext/narrative_to_game.py",
                                        "tier3/mettaext/passroom")),
        },
        "command": cmd,
        "returncode": proc.returncode,
        "started_at": started,
        "finished_at": time.time(),
        "game_scenes": sorted(str(p.relative_to(out)) for p in (out / "game_scenes").glob("*.json")),
        "outputs": [{"path": str(p.relative_to(out)), "sha256": _sha256(p)} for p in outputs],
    }
    receipt_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8")
    return receipt


def extraction_status(catalog_id: str, manifest_path: Optional[Path] = None,
                      stageroom: Path = DEFAULT_STAGEROOM) -> tuple[int, dict]:
    """
    Read-only answer for one chapter: (http_status, body). Only output extracted from the
    chapter's *current* bytes is served; older runs are reported as stale, never returned
    as current. Served files are re-hashed against the receipt.
    """
    vault = resolve_active_vault(manifest_path)
    if vault["status"] != "ok":
        return 503, {"status": "error", "vault": vault}
    try:
        _, entry = find_entry(catalog_id, manifest_path)
    except ExtractionError as e:
        return 404, {"status": "error", "extraction": "unknown_catalog_id", "message": str(e)}

    out = extraction_dir(Path(stageroom), entry)
    base = {"catalog_id": entry["catalog_id"], "source_sha256": entry["source_sha256"]}
    receipt_path = out / "receipt.json"
    if not receipt_path.is_file():
        previous = []
        for r in sorted(out.parent.glob("*/receipt.json")):
            old = json.loads(r.read_text(encoding="utf-8"))
            previous.append({k: old.get(k) for k in ("source_sha256", "status", "finished_at")})
        state = "stale" if previous else "not_extracted"
        return 404, {"status": "error", "extraction": state, **base, "previous": previous}

    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    hashes = {o["path"]: o["sha256"] for o in receipt.get("outputs", [])}
    scenes = {}
    for rel in receipt.get("game_scenes", []):
        p = out / rel
        if not p.is_file() or _sha256(p) != hashes.get(rel):
            return 500, {"status": "error", "extraction": "receipt_mismatch", **base, "path": rel}
        scenes[rel] = json.loads(p.read_text(encoding="utf-8"))
    return 200, {"status": "success", "extraction": receipt["status"], "acceptance": receipt["acceptance"],
                 **base, "receipt": receipt, "game_scenes": scenes}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--catalog-id", required=True)
    ap.add_argument("--manifest", type=Path, default=None, help="engain_manifest.json (default: Tier 1's)")
    ap.add_argument("--stageroom", type=Path, default=DEFAULT_STAGEROOM)
    args = ap.parse_args()
    try:
        r = run_extraction(args.catalog_id, args.manifest, args.stageroom)
    except ExtractionError as e:
        print(f"[REFUSE] {e}", file=sys.stderr)
        return 2
    print(json.dumps({k: r[k] for k in ("status", "catalog_id", "source_sha256", "returncode", "game_scenes")}, indent=2))
    return 0 if r["status"] == "candidate" else 1


if __name__ == "__main__":
    raise SystemExit(main())
