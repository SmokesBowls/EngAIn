#!/usr/bin/env python3
"""
mrlore_review_queue_clean_view.py — write a non-authoritative clean review view.

PURPOSE:
    Read the original contradiction review queue and sidecar noise flags, then
    write a filtered display view that hides flagged noise from the view only.
    The original queue remains the source review artifact.

INPUTS:
    vault/.engain/mrlore/review/contradiction_review_queue.jsonl
    vault/.engain/mrlore/review/contradiction_review_queue_noise_flags.jsonl

OUTPUTS:
    vault/.engain/mrlore/review/clean_review_queue.jsonl
    vault/.engain/mrlore/review/clean_review_queue.md
    vault/.engain/manifests/clean_review_queue_manifest.json

DOES NOT:
    delete original queue items
    alter candidates
    reject noisy claims
    resolve contradictions
    promote claims
    write canon
    compile ZONJ
    touch Godot/runtime
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


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


def _default_manifest_path() -> Path:
    candidates = [
        _ENGAIN_ROOT / "tier1" / "engainos" / "assets" / "engain_manifest.json",
        _HERE.parent / "engainos" / "assets" / "engain_manifest.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _resolve_engain_dir_from_manifest(manifest_path: Path) -> Path:
    if not manifest_path.exists():
        raise FileNotFoundError(f"engain_manifest.json not found: {manifest_path}")
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    output_dir = data.get("output_dir")
    active_vault = data.get("active_vault")
    if output_dir:
        return Path(output_dir)
    if active_vault:
        return Path(active_vault) / ".engain"
    raise ValueError("engain_manifest.json has no output_dir or active_vault")


def default_queue_path(manifest_path: Path | None = None, engain_dir: Path | None = None) -> Path:
    if engain_dir is None:
        engain_dir = _resolve_engain_dir_from_manifest(manifest_path or _default_manifest_path())
    return engain_dir / "mrlore" / "review" / "contradiction_review_queue.jsonl"


def default_noise_flags_path(manifest_path: Path | None = None, engain_dir: Path | None = None) -> Path:
    if engain_dir is None:
        engain_dir = _resolve_engain_dir_from_manifest(manifest_path or _default_manifest_path())
    return engain_dir / "mrlore" / "review" / "contradiction_review_queue_noise_flags.jsonl"


def _infer_engain_dir_from_queue_path(queue_path: Path) -> Path:
    resolved = queue_path.resolve()
    for parent in resolved.parents:
        if parent.name == ".engain":
            return parent
    return resolved.parents[2]


def _read_jsonl(path: Path, item_name: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    items: list[dict[str, Any]] = []
    read_errors: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, 1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                read_errors.append({"line": line_number, "error": f"invalid JSON: {exc.msg}"})
                continue
            if not isinstance(item, dict):
                read_errors.append({"line": line_number, "error": f"{item_name} must be a JSON object"})
                continue
            items.append(item)
    return items, read_errors


def _clean_item(item: dict[str, Any], clean_rank: int) -> dict[str, Any]:
    clean = dict(item)
    clean["clean_view_rank"] = clean_rank
    clean["clean_view_status"] = "CLEAN_VIEW_INCLUDED"
    clean["original_queue_item_altered"] = False
    clean["candidate_altered"] = False
    clean["claim_rejected"] = False
    clean["claim_promoted"] = False
    clean["canon_written"] = False
    return clean


def _write_markdown(path: Path, clean_items: list[dict[str, Any]], excluded_count: int) -> None:
    bucket_counts: Counter[str] = Counter(str(item.get("priority_bucket", "<missing>")) for item in clean_items)
    lines = [
        "# MrLore Clean Contradiction Review Queue",
        "",
        "Filtered display view only. Noise-flagged items are hidden from this view, not deleted, rejected, resolved, promoted, or canonized.",
        "",
        f"CLEAN_ITEMS_WRITTEN={len(clean_items)}",
        f"NOISY_ITEMS_EXCLUDED_FROM_VIEW={excluded_count}",
        "",
        "## Bucket Counts",
        "",
    ]
    for bucket in sorted(bucket_counts):
        lines.append(f"- {bucket}: {bucket_counts[bucket]}")
    lines.append("")
    current_bucket: str | None = None
    for item in clean_items:
        bucket = str(item.get("priority_bucket", "<missing>"))
        if bucket != current_bucket:
            current_bucket = bucket
            lines.extend([f"## {bucket}", ""])
        objects = item.get("objects", [])
        if not isinstance(objects, list):
            objects = []
        object_preview = ", ".join(str(obj) for obj in objects[:4])
        if len(objects) > 4:
            object_preview += f", ... (+{len(objects) - 4})"
        lines.append(
            f"- {item.get('queue_id', '')} | {item.get('candidate_id', '')} | "
            f"{item.get('claim_domain', '')} | {item.get('predicate', '')} | "
            f"{item.get('subject', '')} | objects: {object_preview}"
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def run_review_queue_clean_view(queue_path: Path | str, noise_flags_path: Path | str) -> dict[str, Any]:
    queue_file = Path(queue_path).resolve()
    flags_file = Path(noise_flags_path).resolve()
    engain_dir = _infer_engain_dir_from_queue_path(queue_file)
    review_dir = engain_dir / "mrlore" / "review"
    clean_jsonl = review_dir / "clean_review_queue.jsonl"
    clean_md = review_dir / "clean_review_queue.md"
    manifest_path = engain_dir / "manifests" / "clean_review_queue_manifest.json"
    clean_jsonl.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    queue_items, queue_read_errors = _read_jsonl(queue_file, "queue item")
    noise_flags, noise_flag_read_errors = _read_jsonl(flags_file, "noise flag")
    noisy_queue_ids = {str(flag.get("queue_id", "")) for flag in noise_flags if flag.get("queue_id")}

    clean_items = [
        _clean_item(item, clean_rank)
        for clean_rank, item in enumerate(
            [item for item in queue_items if str(item.get("queue_id", "")) not in noisy_queue_ids],
            1,
        )
    ]

    with clean_jsonl.open("w", encoding="utf-8") as handle:
        for item in clean_items:
            handle.write(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n")
    excluded_count = len(queue_items) - len(clean_items)
    _write_markdown(clean_md, clean_items, excluded_count)

    errors: list[str] = []
    if queue_read_errors:
        errors.append("original review queue JSONL had read errors")
    if noise_flag_read_errors:
        errors.append("noise flag JSONL had read errors")

    manifest: dict[str, Any] = {
        "contract": "engain.mrlore_review_queue_clean_view.v1",
        "run_timestamp": datetime.now(timezone.utc).isoformat(),
        "source_review_queue_jsonl": str(queue_file),
        "source_noise_flags_jsonl": str(flags_file),
        "clean_review_queue_jsonl_path": str(clean_jsonl),
        "clean_review_queue_markdown_path": str(clean_md),
        "manifest_path": str(manifest_path),
        "MRLORE_REVIEW_QUEUE_CLEAN_VIEW_COMPLETE": len(errors) == 0,
        "QUEUE_ITEMS_READ": len(queue_items),
        "NOISE_FLAGS_READ": len(noise_flags),
        "CLEAN_ITEMS_WRITTEN": len(clean_items),
        "NOISY_ITEMS_EXCLUDED_FROM_VIEW": excluded_count,
        "ORIGINAL_QUEUE_ALTERED": False,
        "NOISE_FLAGS_ALTERED": False,
        "CANDIDATES_ALTERED": False,
        "CLAIMS_REJECTED": False,
        "CLAIMS_PROMOTED": False,
        "CONTRADICTIONS_RESOLVED": False,
        "CANON_WRITTEN": False,
        "RUNTIME_TOUCHED": False,
        "GODOT_TOUCHED": False,
        "ZONJ_COMPILED": False,
        "ACCEPTED_LORE_PACKET_EXISTS": False,
        "queue_read_errors_count": len(queue_read_errors),
        "queue_read_errors": queue_read_errors[:100],
        "noise_flag_read_errors_count": len(noise_flag_read_errors),
        "noise_flag_read_errors": noise_flag_read_errors[:100],
        "errors": errors,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="MrLore clean review queue view — filtered display only, no authority writes.")
    parser.add_argument("--queue", default=None, help="Path to contradiction_review_queue.jsonl.")
    parser.add_argument("--noise-flags", default=None, help="Path to contradiction_review_queue_noise_flags.jsonl.")
    parser.add_argument("--manifest", default=None, help="Path to engain_manifest.json.")
    parser.add_argument("--engain-dir", default=None, help="Direct path to vault/.engain.")
    args = parser.parse_args()

    try:
        manifest_path = Path(args.manifest) if args.manifest else None
        engain_dir = Path(args.engain_dir) if args.engain_dir else None
        queue_path = Path(args.queue) if args.queue else default_queue_path(manifest_path, engain_dir)
        noise_flags_path = Path(args.noise_flags) if args.noise_flags else default_noise_flags_path(manifest_path, engain_dir)
        manifest = run_review_queue_clean_view(queue_path, noise_flags_path)
    except Exception as exc:
        print(f"[REVIEW_QUEUE_CLEAN_VIEW] ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"[REVIEW_QUEUE_CLEAN_VIEW] MRLORE_REVIEW_QUEUE_CLEAN_VIEW_COMPLETE={manifest['MRLORE_REVIEW_QUEUE_CLEAN_VIEW_COMPLETE']}")
    print(f"[REVIEW_QUEUE_CLEAN_VIEW] QUEUE_ITEMS_READ={manifest['QUEUE_ITEMS_READ']}")
    print(f"[REVIEW_QUEUE_CLEAN_VIEW] NOISE_FLAGS_READ={manifest['NOISE_FLAGS_READ']}")
    print(f"[REVIEW_QUEUE_CLEAN_VIEW] CLEAN_ITEMS_WRITTEN={manifest['CLEAN_ITEMS_WRITTEN']}")
    print(f"[REVIEW_QUEUE_CLEAN_VIEW] NOISY_ITEMS_EXCLUDED_FROM_VIEW={manifest['NOISY_ITEMS_EXCLUDED_FROM_VIEW']}")
    print(f"[REVIEW_QUEUE_CLEAN_VIEW] ORIGINAL_QUEUE_ALTERED={manifest['ORIGINAL_QUEUE_ALTERED']}")
    print(f"[REVIEW_QUEUE_CLEAN_VIEW] CANDIDATES_ALTERED={manifest['CANDIDATES_ALTERED']}")
    print(f"[REVIEW_QUEUE_CLEAN_VIEW] CANON_WRITTEN={manifest['CANON_WRITTEN']}")
    print(f"[REVIEW_QUEUE_CLEAN_VIEW] MANIFEST={manifest['manifest_path']}")
    return 0 if manifest["MRLORE_REVIEW_QUEUE_CLEAN_VIEW_COMPLETE"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
