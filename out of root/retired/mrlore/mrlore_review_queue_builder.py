#!/usr/bin/env python3
"""
mrlore_review_queue_builder.py — build capped contradiction review queues.

PURPOSE:
    Read the contradiction candidate audit summary and contradiction candidates,
    then write a capped human/machine review queue. This makes conflict pressure
    actionable without crossing into authority.

INPUTS:
    vault/.engain/manifests/mrlore_contradiction_candidate_audit_summary.json
    vault/.engain/mrlore/contradictions/contradiction_candidates.jsonl

OUTPUTS:
    vault/.engain/mrlore/review/contradiction_review_queue.jsonl
    vault/.engain/mrlore/review/contradiction_review_queue.md
    vault/.engain/manifests/mrlore_review_queue_manifest.json

DOES NOT:
    resolve contradictions
    promote claims
    reject claims
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

DEFAULT_MAX_ITEMS_PER_BUCKET = 50
PRIORITY_BUCKETS = ("P0", "P2", "P3")


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


def default_audit_summary_path(manifest_path: Path | None = None, engain_dir: Path | None = None) -> Path:
    if engain_dir is None:
        engain_dir = _resolve_engain_dir_from_manifest(manifest_path or _default_manifest_path())
    return engain_dir / "manifests" / "mrlore_contradiction_candidate_audit_summary.json"


def default_candidates_path(manifest_path: Path | None = None, engain_dir: Path | None = None) -> Path:
    if engain_dir is None:
        engain_dir = _resolve_engain_dir_from_manifest(manifest_path or _default_manifest_path())
    return engain_dir / "mrlore" / "contradictions" / "contradiction_candidates.jsonl"


def _infer_engain_dir_from_candidates_path(candidates_path: Path) -> Path:
    resolved = candidates_path.resolve()
    for parent in resolved.parents:
        if parent.name == ".engain":
            return parent
    return resolved.parents[2]


def _read_audit_summary(path: Path) -> tuple[dict[str, Any], list[str]]:
    if not path.exists():
        return {}, [f"contradiction candidate audit summary not found: {path}"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {}, [f"invalid contradiction candidate audit summary JSON: {exc.msg}"]
    if not data.get("MRLORE_CONTRADICTION_CANDIDATE_AUDIT_SUMMARY_COMPLETE", False):
        return data, ["contradiction candidate audit summary is incomplete"]
    return data, []


def _read_candidates(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    candidates: list[dict[str, Any]] = []
    read_errors: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, 1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                candidate = json.loads(line)
            except json.JSONDecodeError as exc:
                read_errors.append({"line": line_number, "error": f"invalid JSON: {exc.msg}"})
                continue
            if not isinstance(candidate, dict):
                read_errors.append({"line": line_number, "error": "candidate must be a JSON object"})
                continue
            candidates.append(candidate)
    return candidates, read_errors


def _priority_bucket(candidate: dict[str, Any]) -> str | None:
    if bool(candidate.get("touches_high_claim_scene", False)):
        return "P0"
    if candidate.get("claim_domain") == "entity" and candidate.get("predicate") == "present_in":
        return "P2"
    return "P3"


def _queue_item(candidate: dict[str, Any], priority_bucket: str, bucket_rank: int, global_rank: int) -> dict[str, Any]:
    return {
        "queue_id": f"review_queue.{priority_bucket.lower()}.{bucket_rank:04d}",
        "priority_bucket": priority_bucket,
        "bucket_rank": bucket_rank,
        "global_rank": global_rank,
        "candidate_id": str(candidate.get("candidate_id", "")),
        "candidate_type": str(candidate.get("candidate_type", "")),
        "claim_domain": str(candidate.get("claim_domain", "")),
        "subject": str(candidate.get("subject", "")),
        "predicate": str(candidate.get("predicate", "")),
        "objects": candidate.get("objects", []),
        "source_scenes": candidate.get("source_scenes", []),
        "touches_high_claim_scene": bool(candidate.get("touches_high_claim_scene", False)),
        "review_flags": candidate.get("review_flags", []),
        "reasons": candidate.get("reasons", []),
        "status": "REVIEW_QUEUED",
        "resolved": False,
        "claim_promoted": False,
        "claim_rejected": False,
        "canon_written": False,
    }


def _write_markdown(path: Path, queue_items: list[dict[str, Any]], bucket_counts: Counter[str], max_items_per_bucket: int) -> None:
    lines = [
        "# MrLore Contradiction Review Queue",
        "",
        "Scope: review queue only. No contradiction resolution, claim promotion, claim rejection, canon write, ZONJ compile, Godot touch, or runtime touch.",
        "",
        f"MAX_ITEMS_PER_BUCKET={max_items_per_bucket}",
        "",
    ]
    for bucket in PRIORITY_BUCKETS:
        lines.extend([f"## {bucket}", ""])
        bucket_items = [item for item in queue_items if item["priority_bucket"] == bucket]
        if not bucket_items:
            lines.extend(["No queued items.", ""])
            continue
        for item in bucket_items:
            objects = item.get("objects", [])
            object_preview = ", ".join(str(obj) for obj in objects[:4])
            if len(objects) > 4:
                object_preview += f", ... (+{len(objects) - 4})"
            lines.append(
                f"- {item['queue_id']} | {item['candidate_id']} | "
                f"{item['claim_domain']} | {item['predicate']} | {item['subject']} | objects: {object_preview}"
            )
        lines.append("")
    lines.extend(
        [
            "## Bucket Counts",
            "",
            *(f"- {bucket}: {bucket_counts[bucket]}" for bucket in PRIORITY_BUCKETS),
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def _base_manifest(audit_file: Path, candidates_file: Path, queue_jsonl: Path, queue_md: Path, manifest_path: Path, max_items_per_bucket: int) -> dict[str, Any]:
    return {
        "contract": "engain.mrlore_review_queue_builder.v1",
        "run_timestamp": datetime.now(timezone.utc).isoformat(),
        "source_audit_summary": str(audit_file),
        "source_candidates_jsonl": str(candidates_file),
        "queue_jsonl_path": str(queue_jsonl),
        "queue_markdown_path": str(queue_md),
        "manifest_path": str(manifest_path),
        "MRLORE_REVIEW_QUEUE_BUILDER_COMPLETE": False,
        "MAX_ITEMS_PER_BUCKET": max_items_per_bucket,
        "CANDIDATES_READ": 0,
        "QUEUE_ITEMS_WRITTEN": 0,
        "P0_ITEMS": 0,
        "P2_ITEMS": 0,
        "P3_ITEMS": 0,
        "CONTRADICTIONS_RESOLVED": False,
        "CLAIMS_PROMOTED": False,
        "CLAIMS_REJECTED": False,
        "CANON_WRITTEN": False,
        "RUNTIME_TOUCHED": False,
        "GODOT_TOUCHED": False,
        "ZONJ_COMPILED": False,
        "ACCEPTED_LORE_PACKET_EXISTS": False,
        "read_errors_count": 0,
        "read_errors": [],
        "errors": [],
    }


def run_review_queue_builder(
    audit_summary_path: Path | str,
    candidates_path: Path | str,
    max_items_per_bucket: int = DEFAULT_MAX_ITEMS_PER_BUCKET,
) -> dict[str, Any]:
    audit_file = Path(audit_summary_path).resolve()
    candidates_file = Path(candidates_path).resolve()
    engain_dir = _infer_engain_dir_from_candidates_path(candidates_file)
    review_dir = engain_dir / "mrlore" / "review"
    queue_jsonl = review_dir / "contradiction_review_queue.jsonl"
    queue_md = review_dir / "contradiction_review_queue.md"
    manifest_path = engain_dir / "manifests" / "mrlore_review_queue_manifest.json"
    review_dir.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    manifest = _base_manifest(audit_file, candidates_file, queue_jsonl, queue_md, manifest_path, max_items_per_bucket)
    audit_summary, errors = _read_audit_summary(audit_file)
    if errors:
        manifest["errors"] = errors
        queue_jsonl.write_text("", encoding="utf-8")
        queue_md.write_text("# MrLore Contradiction Review Queue\n\nNo queue built: audit summary incomplete.\n", encoding="utf-8")
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        return manifest

    candidates, read_errors = _read_candidates(candidates_file)
    errors = []
    if read_errors:
        errors.append("contradiction candidate JSONL had read errors")
    expected_count = audit_summary.get("CANDIDATES_READ")
    if isinstance(expected_count, int) and expected_count != len(candidates):
        errors.append(f"candidate count mismatch: audit_summary={expected_count} jsonl={len(candidates)}")

    selected_by_bucket: dict[str, list[dict[str, Any]]] = {bucket: [] for bucket in PRIORITY_BUCKETS}
    available_by_bucket: Counter[str] = Counter({bucket: 0 for bucket in PRIORITY_BUCKETS})
    for candidate in candidates:
        bucket = _priority_bucket(candidate)
        if bucket not in selected_by_bucket:
            continue
        available_by_bucket[bucket] += 1
        if len(selected_by_bucket[bucket]) < max_items_per_bucket:
            selected_by_bucket[bucket].append(candidate)

    queue_items: list[dict[str, Any]] = []
    global_rank = 1
    for bucket in PRIORITY_BUCKETS:
        for bucket_rank, candidate in enumerate(selected_by_bucket[bucket], 1):
            queue_items.append(_queue_item(candidate, bucket, bucket_rank, global_rank))
            global_rank += 1

    with queue_jsonl.open("w", encoding="utf-8") as handle:
        for item in queue_items:
            handle.write(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n")

    bucket_counts = Counter({bucket: len(selected_by_bucket[bucket]) for bucket in PRIORITY_BUCKETS})
    _write_markdown(queue_md, queue_items, bucket_counts, max_items_per_bucket)

    manifest.update(
        {
            "MRLORE_REVIEW_QUEUE_BUILDER_COMPLETE": len(errors) == 0,
            "CANDIDATES_READ": len(candidates),
            "QUEUE_ITEMS_WRITTEN": len(queue_items),
            "P0_ITEMS": bucket_counts["P0"],
            "P2_ITEMS": bucket_counts["P2"],
            "P3_ITEMS": bucket_counts["P3"],
            "available_by_bucket": {bucket: available_by_bucket[bucket] for bucket in PRIORITY_BUCKETS},
            "selection_policy": "priority order P0, P2, P3; preserve candidate file order within bucket; cap each bucket",
            "read_errors_count": len(read_errors),
            "read_errors": read_errors[:100],
            "errors": errors,
        }
    )
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="MrLore review queue builder — capped review queue only, no authority writes.")
    parser.add_argument("--audit-summary", default=None, help="Path to mrlore_contradiction_candidate_audit_summary.json.")
    parser.add_argument("--candidates", default=None, help="Path to contradiction_candidates.jsonl.")
    parser.add_argument("--max-items-per-bucket", type=int, default=DEFAULT_MAX_ITEMS_PER_BUCKET)
    parser.add_argument("--manifest", default=None, help="Path to engain_manifest.json.")
    parser.add_argument("--engain-dir", default=None, help="Direct path to vault/.engain.")
    args = parser.parse_args()

    try:
        manifest_path = Path(args.manifest) if args.manifest else None
        engain_dir = Path(args.engain_dir) if args.engain_dir else None
        audit_summary_path = Path(args.audit_summary) if args.audit_summary else default_audit_summary_path(manifest_path, engain_dir)
        candidates_path = Path(args.candidates) if args.candidates else default_candidates_path(manifest_path, engain_dir)
        manifest = run_review_queue_builder(audit_summary_path, candidates_path, args.max_items_per_bucket)
    except Exception as exc:
        print(f"[REVIEW_QUEUE_BUILDER] ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"[REVIEW_QUEUE_BUILDER] MRLORE_REVIEW_QUEUE_BUILDER_COMPLETE={manifest['MRLORE_REVIEW_QUEUE_BUILDER_COMPLETE']}")
    print(f"[REVIEW_QUEUE_BUILDER] CANDIDATES_READ={manifest['CANDIDATES_READ']}")
    print(f"[REVIEW_QUEUE_BUILDER] QUEUE_ITEMS_WRITTEN={manifest['QUEUE_ITEMS_WRITTEN']}")
    print(f"[REVIEW_QUEUE_BUILDER] P0_ITEMS={manifest['P0_ITEMS']}")
    print(f"[REVIEW_QUEUE_BUILDER] P2_ITEMS={manifest['P2_ITEMS']}")
    print(f"[REVIEW_QUEUE_BUILDER] P3_ITEMS={manifest['P3_ITEMS']}")
    print(f"[REVIEW_QUEUE_BUILDER] CONTRADICTIONS_RESOLVED={manifest['CONTRADICTIONS_RESOLVED']}")
    print(f"[REVIEW_QUEUE_BUILDER] CLAIMS_PROMOTED={manifest['CLAIMS_PROMOTED']}")
    print(f"[REVIEW_QUEUE_BUILDER] CLAIMS_REJECTED={manifest['CLAIMS_REJECTED']}")
    print(f"[REVIEW_QUEUE_BUILDER] CANON_WRITTEN={manifest['CANON_WRITTEN']}")
    print(f"[REVIEW_QUEUE_BUILDER] RUNTIME_TOUCHED={manifest['RUNTIME_TOUCHED']}")
    print(f"[REVIEW_QUEUE_BUILDER] MANIFEST={manifest['manifest_path']}")
    return 0 if manifest["MRLORE_REVIEW_QUEUE_BUILDER_COMPLETE"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
