#!/usr/bin/env python3
"""
mrlore_temporal_aware_queue_summary.py — summarize temporal-aware quality review queue.

PURPOSE:
    Read temporal_aware_quality_review_queue.jsonl and write a compact
    manifest summary for inspection: bucket counts, domains per bucket, top
    subjects/predicates per bucket, scene counts, high-claim overlap, quality
    flag overlap, and temporal pressure for sequential state changes and
    concurrent conflicts. Summary only; no queue, candidate, classification,
    quality flag, claim, contradiction, canon, runtime, Godot, or ZONJ mutation.

INPUT:
    vault/.engain/mrlore/review/temporal_aware_quality_review_queue.jsonl

OUTPUT:
    vault/.engain/manifests/temporal_aware_review_queue_summary.json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_TOP_ITEMS_PER_BUCKET = 12
SEQUENTIAL_CLASSIFICATION = "SEQUENTIAL_STATE_CHANGE"
CONCURRENT_CLASSIFICATION = "CONCURRENT_OBJECT_COLLISION"
SEQUENTIAL_BUCKET = "P3_SEQUENTIAL_STATE_CHANGE"
CONCURRENT_BUCKET = "P0_CONCURRENT_CONFLICT"


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
    return engain_dir / "mrlore" / "review" / "temporal_aware_quality_review_queue.jsonl"


def _infer_engain_dir_from_queue_path(queue_path: Path) -> Path:
    resolved = queue_path.resolve()
    for parent in resolved.parents:
        if parent.name == ".engain":
            return parent
    return resolved.parents[2]


def _read_queue(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
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
                read_errors.append({"line": line_number, "error": "queue item must be a JSON object"})
                continue
            items.append(item)
    return items, read_errors


def _sorted_counter_dict(counter: Counter[str]) -> dict[str, int]:
    return {key: counter[key] for key in sorted(counter)}


def _top_named(counter: Counter[str], field_name: str, limit: int) -> list[dict[str, Any]]:
    return [
        {field_name: key, "count": count}
        for key, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))[:limit]
    ]


def _source_scenes(item: dict[str, Any]) -> list[str]:
    scenes = item.get("source_scenes", [])
    if not isinstance(scenes, list):
        return []
    return [str(scene) for scene in scenes if scene]


def _pressure_summary(
    items: list[dict[str, Any]],
    classification_name: str,
    primary_bucket: str,
    high_claim_items: set[str],
) -> dict[str, Any]:
    pressure_items = [
        item
        for item in items
        if str(item.get("temporal_classification", "") or "") == classification_name
    ]
    by_bucket: Counter[str] = Counter(str(item.get("priority_bucket", "UNKNOWN") or "UNKNOWN") for item in pressure_items)
    summary: dict[str, Any] = {
        "temporal_classification_items": len(pressure_items),
        "quality_flagged_items": sum(1 for item in pressure_items if bool(item.get("entity_quality_flagged", False))),
        "high_claim_scene_items": sum(1 for item in pressure_items if str(item.get("queue_id", "")) in high_claim_items),
        "by_bucket": _sorted_counter_dict(by_bucket),
    }
    if primary_bucket == SEQUENTIAL_BUCKET:
        summary["bucketed_clean_items"] = by_bucket[primary_bucket]
    else:
        summary["bucketed_items"] = by_bucket[primary_bucket]
    return summary


def run_temporal_aware_queue_summary(
    queue_path: Path | str,
    top_items_per_bucket: int = DEFAULT_TOP_ITEMS_PER_BUCKET,
) -> dict[str, Any]:
    queue_file = Path(queue_path).resolve()
    engain_dir = _infer_engain_dir_from_queue_path(queue_file)
    manifest_path = engain_dir / "manifests" / "temporal_aware_review_queue_summary.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    queue_items, read_errors = _read_queue(queue_file)

    bucket_counts: Counter[str] = Counter()
    domain_counts_by_bucket: dict[str, Counter[str]] = defaultdict(Counter)
    subject_counts_by_bucket: dict[str, Counter[str]] = defaultdict(Counter)
    predicate_counts_by_bucket: dict[str, Counter[str]] = defaultdict(Counter)
    source_scene_refs_by_bucket: Counter[str] = Counter()
    unique_scenes_by_bucket: dict[str, set[str]] = defaultdict(set)
    quality_flagged_by_bucket: Counter[str] = Counter()
    quality_reason_counts: Counter[str] = Counter()
    high_claim_scene_by_bucket: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    high_claim_item_ids: set[str] = set()

    for item in queue_items:
        bucket = str(item.get("priority_bucket", "UNKNOWN") or "UNKNOWN")
        domain = str(item.get("claim_domain", "UNKNOWN") or "UNKNOWN")
        subject = str(item.get("subject", "") or "")
        predicate = str(item.get("predicate", "") or "")
        scenes = _source_scenes(item)
        bucket_counts[bucket] += 1
        domain_counts_by_bucket[bucket][domain] += 1
        if subject:
            subject_counts_by_bucket[bucket][subject] += 1
        if predicate:
            predicate_counts_by_bucket[bucket][predicate] += 1
        source_scene_refs_by_bucket[bucket] += len(scenes)
        unique_scenes_by_bucket[bucket].update(scenes)
        status_counts[str(item.get("status", "UNKNOWN") or "UNKNOWN")] += 1
        if bool(item.get("entity_quality_flagged", False)):
            quality_flagged_by_bucket[bucket] += 1
        for reason in item.get("quality_reasons", []) or []:
            if reason:
                quality_reason_counts[str(reason)] += 1
        if bool(item.get("touches_high_claim_scene", False)):
            high_claim_scene_by_bucket[bucket] += 1
            high_claim_item_ids.add(str(item.get("queue_id", "")))

    all_buckets = sorted(bucket_counts)
    scene_counts_by_bucket = {
        bucket: {
            "item_count": bucket_counts[bucket],
            "source_scene_refs": source_scene_refs_by_bucket[bucket],
            "unique_source_scenes": len(unique_scenes_by_bucket[bucket]),
        }
        for bucket in all_buckets
    }

    manifest: dict[str, Any] = {
        "contract": "engain.mrlore_temporal_aware_review_queue_summary.v1",
        "run_timestamp": datetime.now(timezone.utc).isoformat(),
        "source_temporal_aware_queue_jsonl": str(queue_file),
        "manifest_path": str(manifest_path),
        "MRLORE_TEMPORAL_AWARE_QUEUE_SUMMARY_COMPLETE": len(read_errors) == 0,
        "QUEUE_ITEMS_READ": len(queue_items),
        "bucket_counts": _sorted_counter_dict(bucket_counts),
        "domain_counts_by_bucket": {
            bucket: _sorted_counter_dict(domain_counts_by_bucket[bucket]) for bucket in all_buckets
        },
        "top_items_per_bucket_limit": top_items_per_bucket,
        "top_subjects_by_bucket": {
            bucket: _top_named(subject_counts_by_bucket[bucket], "subject", top_items_per_bucket)
            for bucket in all_buckets
        },
        "top_predicates_by_bucket": {
            bucket: _top_named(predicate_counts_by_bucket[bucket], "predicate", top_items_per_bucket)
            for bucket in all_buckets
        },
        "scene_counts_by_bucket": scene_counts_by_bucket,
        "high_claim_scene_overlap": {
            "items": sum(high_claim_scene_by_bucket.values()),
            "by_bucket": _sorted_counter_dict(high_claim_scene_by_bucket),
        },
        "quality_flag_overlap": {
            "items": sum(quality_flagged_by_bucket.values()),
            "by_bucket": _sorted_counter_dict(quality_flagged_by_bucket),
        },
        "quality_reason_counts": _sorted_counter_dict(quality_reason_counts),
        "status_counts": _sorted_counter_dict(status_counts),
        "sequential_state_change_pressure": _pressure_summary(
            queue_items,
            SEQUENTIAL_CLASSIFICATION,
            SEQUENTIAL_BUCKET,
            high_claim_item_ids,
        ),
        "concurrent_conflict_pressure": _pressure_summary(
            queue_items,
            CONCURRENT_CLASSIFICATION,
            CONCURRENT_BUCKET,
            high_claim_item_ids,
        ),
        "QUEUE_ALTERED": False,
        "CANDIDATES_ALTERED": False,
        "CLASSIFICATIONS_ALTERED": False,
        "QUALITY_FLAGS_ALTERED": False,
        "CLAIMS_PROMOTED": False,
        "CLAIMS_REJECTED": False,
        "CONTRADICTIONS_RESOLVED": False,
        "CANON_WRITTEN": False,
        "RUNTIME_TOUCHED": False,
        "GODOT_TOUCHED": False,
        "ZONJ_COMPILED": False,
        "ACCEPTED_LORE_PACKET_EXISTS": False,
        "read_errors_count": len(read_errors),
        "read_errors": read_errors[:100],
        "errors": ["temporal-aware review queue JSONL had read errors"] if read_errors else [],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize MrLore temporal-aware review queue without mutation.")
    parser.add_argument("--queue", default=None, help="Path to temporal_aware_quality_review_queue.jsonl.")
    parser.add_argument("--top-items-per-bucket", type=int, default=DEFAULT_TOP_ITEMS_PER_BUCKET)
    parser.add_argument("--manifest", default=None, help="Path to engain_manifest.json.")
    parser.add_argument("--engain-dir", default=None, help="Direct path to vault/.engain.")
    args = parser.parse_args()

    try:
        manifest_path = Path(args.manifest) if args.manifest else None
        engain_dir = Path(args.engain_dir) if args.engain_dir else None
        queue_path = Path(args.queue) if args.queue else default_queue_path(manifest_path, engain_dir)
        manifest = run_temporal_aware_queue_summary(queue_path, args.top_items_per_bucket)
    except Exception as exc:
        print(f"[TEMPORAL_AWARE_QUEUE_SUMMARY] ERROR: {exc}", file=sys.stderr)
        return 1

    print(
        "[TEMPORAL_AWARE_QUEUE_SUMMARY] "
        f"MRLORE_TEMPORAL_AWARE_QUEUE_SUMMARY_COMPLETE={manifest['MRLORE_TEMPORAL_AWARE_QUEUE_SUMMARY_COMPLETE']}"
    )
    print(f"[TEMPORAL_AWARE_QUEUE_SUMMARY] QUEUE_ITEMS_READ={manifest['QUEUE_ITEMS_READ']}")
    print(f"[TEMPORAL_AWARE_QUEUE_SUMMARY] SEQUENTIAL_STATE_CHANGE_ITEMS={manifest['sequential_state_change_pressure']['temporal_classification_items']}")
    print(f"[TEMPORAL_AWARE_QUEUE_SUMMARY] CONCURRENT_CONFLICT_ITEMS={manifest['concurrent_conflict_pressure']['temporal_classification_items']}")
    print(f"[TEMPORAL_AWARE_QUEUE_SUMMARY] QUALITY_FLAGGED_ITEMS={manifest['quality_flag_overlap']['items']}")
    print(f"[TEMPORAL_AWARE_QUEUE_SUMMARY] HIGH_CLAIM_SCENE_ITEMS={manifest['high_claim_scene_overlap']['items']}")
    print(f"[TEMPORAL_AWARE_QUEUE_SUMMARY] QUEUE_ALTERED={manifest['QUEUE_ALTERED']}")
    print(f"[TEMPORAL_AWARE_QUEUE_SUMMARY] CANDIDATES_ALTERED={manifest['CANDIDATES_ALTERED']}")
    print(f"[TEMPORAL_AWARE_QUEUE_SUMMARY] CLASSIFICATIONS_ALTERED={manifest['CLASSIFICATIONS_ALTERED']}")
    print(f"[TEMPORAL_AWARE_QUEUE_SUMMARY] QUALITY_FLAGS_ALTERED={manifest['QUALITY_FLAGS_ALTERED']}")
    print(f"[TEMPORAL_AWARE_QUEUE_SUMMARY] CLAIMS_REJECTED={manifest['CLAIMS_REJECTED']}")
    print(f"[TEMPORAL_AWARE_QUEUE_SUMMARY] CLAIMS_PROMOTED={manifest['CLAIMS_PROMOTED']}")
    print(f"[TEMPORAL_AWARE_QUEUE_SUMMARY] CONTRADICTIONS_RESOLVED={manifest['CONTRADICTIONS_RESOLVED']}")
    print(f"[TEMPORAL_AWARE_QUEUE_SUMMARY] CANON_WRITTEN={manifest['CANON_WRITTEN']}")
    print(f"[TEMPORAL_AWARE_QUEUE_SUMMARY] RUNTIME_TOUCHED={manifest['RUNTIME_TOUCHED']}")
    print(f"[TEMPORAL_AWARE_QUEUE_SUMMARY] GODOT_TOUCHED={manifest['GODOT_TOUCHED']}")
    print(f"[TEMPORAL_AWARE_QUEUE_SUMMARY] ZONJ_COMPILED={manifest['ZONJ_COMPILED']}")
    print(f"[TEMPORAL_AWARE_QUEUE_SUMMARY] MANIFEST={manifest['manifest_path']}")
    return 0 if manifest["MRLORE_TEMPORAL_AWARE_QUEUE_SUMMARY_COMPLETE"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
