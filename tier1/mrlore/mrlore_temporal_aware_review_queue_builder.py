#!/usr/bin/env python3
"""
mrlore_temporal_aware_review_queue_builder.py — build review queue with temporal sidecar priority.

PURPOSE:
    Read contradiction candidates, temporal collision classifications, entity
    quality flags, and high-claim scene review metadata. Write a new temporal-
    aware quality-aware review queue without changing source candidates,
    classifications, claims, or authority state.

INPUTS:
    vault/.engain/mrlore/contradictions/contradiction_candidates.jsonl
    vault/.engain/mrlore/contradictions/temporal_collision_classifications.jsonl
    vault/.engain/mrlore/claims/entity_candidate_quality_flags.jsonl
    vault/.engain/manifests/high_claim_scene_review_manifest.json

OUTPUTS:
    vault/.engain/mrlore/review/temporal_aware_quality_review_queue.jsonl
    vault/.engain/mrlore/review/temporal_aware_quality_review_queue.md
    vault/.engain/manifests/mrlore_temporal_aware_review_queue_manifest.json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PRIORITY_BUCKETS = (
    "P0_CONCURRENT_CONFLICT",
    "P1_DURABLE_STATE_CONTINUITY_REVIEW",
    "P2_TEMPORAL_ORDER_UNKNOWN",
    "P3_SEQUENTIAL_STATE_CHANGE",
    "P4_ENVIRONMENT_REVIEW",
    "P5_CLEAN_ENTITY_REVIEW",
    "P9_ENTITY_QUALITY_FLAGGED",
)

CLASSIFICATION_TO_BUCKET = {
    "CONCURRENT_OBJECT_COLLISION": "P0_CONCURRENT_CONFLICT",
    "DURABLE_STATE_CONTINUITY_REVIEW": "P1_DURABLE_STATE_CONTINUITY_REVIEW",
    "TEMPORAL_ORDER_UNKNOWN_REVIEW": "P2_TEMPORAL_ORDER_UNKNOWN",
    "SEQUENTIAL_STATE_CHANGE": "P3_SEQUENTIAL_STATE_CHANGE",
}


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


def default_candidates_path(manifest_path: Path | None = None, engain_dir: Path | None = None) -> Path:
    if engain_dir is None:
        engain_dir = _resolve_engain_dir_from_manifest(manifest_path or _default_manifest_path())
    return engain_dir / "mrlore" / "contradictions" / "contradiction_candidates.jsonl"


def default_classifications_path(manifest_path: Path | None = None, engain_dir: Path | None = None) -> Path:
    if engain_dir is None:
        engain_dir = _resolve_engain_dir_from_manifest(manifest_path or _default_manifest_path())
    return engain_dir / "mrlore" / "contradictions" / "temporal_collision_classifications.jsonl"


def default_quality_flags_path(manifest_path: Path | None = None, engain_dir: Path | None = None) -> Path:
    if engain_dir is None:
        engain_dir = _resolve_engain_dir_from_manifest(manifest_path or _default_manifest_path())
    return engain_dir / "mrlore" / "claims" / "entity_candidate_quality_flags.jsonl"


def default_high_claim_manifest_path(manifest_path: Path | None = None, engain_dir: Path | None = None) -> Path:
    if engain_dir is None:
        engain_dir = _resolve_engain_dir_from_manifest(manifest_path or _default_manifest_path())
    return engain_dir / "manifests" / "high_claim_scene_review_manifest.json"


def _infer_engain_dir_from_candidates_path(candidates_path: Path) -> Path:
    resolved = candidates_path.resolve()
    for parent in resolved.parents:
        if parent.name == ".engain":
            return parent
    return resolved.parents[2]


def _read_jsonl(path: Path, noun: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    records: list[dict[str, Any]] = []
    read_errors: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, 1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                read_errors.append({"path": str(path), "line": line_number, "error": f"invalid JSON: {exc.msg}"})
                continue
            if not isinstance(record, dict):
                read_errors.append({"path": str(path), "line": line_number, "error": f"{noun} must be a JSON object"})
                continue
            records.append(record)
    return records, read_errors


def _read_high_claim_scenes(path: Path) -> tuple[set[str], list[str]]:
    if not path.exists():
        return set(), [f"high claim scene review manifest not found: {path}"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return set(), [f"invalid high claim scene review manifest JSON: {exc.msg}"]
    if not data.get("MRLORE_HIGH_CLAIM_SCENE_REVIEW_MANIFEST_COMPLETE", False):
        return set(), ["high claim scene review manifest is incomplete"]
    scenes = {
        str(item.get("SOURCE_SCENE", ""))
        for item in data.get("review_required_scenes", [])
        if isinstance(item, dict) and item.get("SOURCE_SCENE")
    }
    return scenes, []


def _classification_index(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for record in records:
        candidate_id = str(record.get("candidate_id", ""))
        if candidate_id:
            indexed[candidate_id] = record
    return indexed


def _claim_ids_from_candidate(candidate: dict[str, Any]) -> set[str]:
    claim_ids: set[str] = set()
    refs_by_object = candidate.get("object_claim_refs", {})
    if isinstance(refs_by_object, dict):
        for refs in refs_by_object.values():
            if not isinstance(refs, list):
                continue
            for ref in refs:
                if isinstance(ref, dict) and ref.get("claim_id"):
                    claim_ids.add(str(ref["claim_id"]))
    return claim_ids


def _quality_indexes(flags: list[dict[str, Any]]) -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]]]:
    by_claim_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_subject: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for flag in flags:
        claim_id = str(flag.get("claim_id", ""))
        subject = str(flag.get("subject", ""))
        if claim_id:
            by_claim_id[claim_id].append(flag)
        if subject:
            by_subject[subject].append(flag)
    return by_claim_id, by_subject


def _quality_match(candidate: dict[str, Any], by_claim_id: dict[str, list[dict[str, Any]]], by_subject: dict[str, list[dict[str, Any]]]) -> tuple[bool, str, list[str], list[str]]:
    reasons: set[str] = set()
    matched_claim_ids: set[str] = set()
    for claim_id in _claim_ids_from_candidate(candidate):
        if claim_id in by_claim_id:
            matched_claim_ids.add(claim_id)
            for flag in by_claim_id[claim_id]:
                reasons.update(str(reason) for reason in flag.get("quality_reasons", []) if reason)
    if matched_claim_ids:
        return True, "claim_ref", sorted(reasons), sorted(matched_claim_ids)

    subject = str(candidate.get("subject", ""))
    if subject in by_subject:
        for flag in by_subject[subject]:
            if flag.get("claim_id"):
                matched_claim_ids.add(str(flag["claim_id"]))
            reasons.update(str(reason) for reason in flag.get("quality_reasons", []) if reason)
        return True, "subject", sorted(reasons), sorted(matched_claim_ids)
    return False, "none", [], []


def _touches_high_claim_scene(candidate: dict[str, Any], high_claim_scenes: set[str]) -> bool:
    candidate_scenes = {str(scene) for scene in candidate.get("source_scenes", []) if scene}
    return bool(candidate.get("touches_high_claim_scene", False)) or bool(candidate_scenes & high_claim_scenes)


def _priority_bucket(candidate: dict[str, Any], quality_flagged: bool, classification: str) -> str:
    if candidate.get("claim_domain") == "entity" and quality_flagged:
        return "P9_ENTITY_QUALITY_FLAGGED"
    if classification in CLASSIFICATION_TO_BUCKET:
        return CLASSIFICATION_TO_BUCKET[classification]
    if candidate.get("claim_domain") == "environment":
        return "P4_ENVIRONMENT_REVIEW"
    if candidate.get("claim_domain") == "entity":
        return "P5_CLEAN_ENTITY_REVIEW"
    return "P5_CLEAN_ENTITY_REVIEW"


def _queue_item(
    candidate: dict[str, Any],
    temporal_classification: dict[str, Any] | None,
    priority_bucket: str,
    bucket_rank: int,
    global_rank: int,
    quality_flagged: bool,
    quality_match: str,
    quality_reasons: list[str],
    matched_quality_claim_ids: list[str],
    touches_high_claim_scene: bool,
) -> dict[str, Any]:
    classification = temporal_classification or {}
    review_flags = list(candidate.get("review_flags", []))
    if quality_flagged:
        review_flags.append("ENTITY_CANDIDATE_QUALITY_REVIEW_REQUIRED")
    if touches_high_claim_scene:
        review_flags.append("CLAIM_DENSITY_REVIEW_REQUIRED")
    return {
        "queue_id": f"temporal_aware_review_queue.{priority_bucket.lower()}.{bucket_rank:04d}",
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
        "touches_high_claim_scene": touches_high_claim_scene,
        "temporal_classification": str(classification.get("classification", "REVIEW_REQUIRED")),
        "temporal_basis": str(classification.get("temporal_basis", "UNCLASSIFIED_TEMPORAL_REVIEW")),
        "temporal_indexes": classification.get("temporal_indexes", []),
        "temporal_reason": str(classification.get("reason", "no temporal classification sidecar record")),
        "entity_quality_flagged": quality_flagged,
        "quality_flag_match": quality_match,
        "quality_reasons": quality_reasons,
        "matched_quality_claim_ids": matched_quality_claim_ids,
        "review_flags": review_flags,
        "reasons": candidate.get("reasons", []),
        "status": "TEMPORAL_AWARE_REVIEW_QUEUED",
        "authority_effect": "NONE",
        "candidate_altered": False,
        "classification_altered": False,
        "claim_promoted": False,
        "claim_rejected": False,
        "contradiction_resolved": False,
        "canon_written": False,
    }


def _write_markdown(path: Path, queue_items: list[dict[str, Any]], bucket_counts: Counter[str]) -> None:
    lines = [
        "# MrLore Temporal-Aware Quality Review Queue",
        "",
        "Scope: temporal-aware display queue only. Sequential movement remains visible but is not prioritized as a paradox. No candidate mutation, classification mutation, claim mutation, contradiction resolution, canon write, ZONJ compile, Godot touch, or runtime touch.",
        "",
    ]
    for bucket in PRIORITY_BUCKETS:
        lines.extend([f"## {bucket}", ""])
        bucket_items = [item for item in queue_items if item["priority_bucket"] == bucket]
        if not bucket_items:
            lines.extend(["No queued items.", ""])
            continue
        for item in bucket_items:
            quality = " QUALITY_FLAGGED" if item["entity_quality_flagged"] else ""
            lines.append(
                f"- {item['queue_id']} | {item['candidate_id']} | {item['claim_domain']} | "
                f"{item['predicate']} | {item['temporal_classification']} | {item['subject']} | scenes={len(item.get('source_scenes', []))}{quality}".rstrip()
            )
        lines.append("")
    lines.extend(["## Bucket Counts", ""])
    lines.extend(f"- {bucket}: {bucket_counts[bucket]}" for bucket in PRIORITY_BUCKETS)
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def run_temporal_aware_review_queue_builder(
    candidates_path: Path | str,
    temporal_classifications_path: Path | str,
    quality_flags_path: Path | str,
    high_claim_manifest_path: Path | str,
) -> dict[str, Any]:
    candidates_file = Path(candidates_path).resolve()
    classifications_file = Path(temporal_classifications_path).resolve()
    quality_flags_file = Path(quality_flags_path).resolve()
    high_claim_file = Path(high_claim_manifest_path).resolve()
    engain_dir = _infer_engain_dir_from_candidates_path(candidates_file)
    review_dir = engain_dir / "mrlore" / "review"
    queue_jsonl = review_dir / "temporal_aware_quality_review_queue.jsonl"
    queue_md = review_dir / "temporal_aware_quality_review_queue.md"
    manifest_path = engain_dir / "manifests" / "mrlore_temporal_aware_review_queue_manifest.json"
    review_dir.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    candidates, candidate_read_errors = _read_jsonl(candidates_file, "candidate")
    temporal_classifications, classification_read_errors = _read_jsonl(classifications_file, "temporal classification")
    quality_flags, quality_read_errors = _read_jsonl(quality_flags_file, "quality flag")
    high_claim_scenes, high_claim_errors = _read_high_claim_scenes(high_claim_file)

    classifications_by_candidate = _classification_index(temporal_classifications)
    by_claim_id, by_subject = _quality_indexes(quality_flags)

    selected_by_bucket: dict[str, list[dict[str, Any]]] = {bucket: [] for bucket in PRIORITY_BUCKETS}
    quality_flagged_items_marked = 0
    missing_temporal_classification_count = 0
    for candidate in candidates:
        flagged, match_kind, quality_reasons, matched_claim_ids = _quality_match(candidate, by_claim_id, by_subject)
        if flagged:
            quality_flagged_items_marked += 1
        temporal_classification = classifications_by_candidate.get(str(candidate.get("candidate_id", "")))
        if temporal_classification is None:
            missing_temporal_classification_count += 1
        classification_name = str((temporal_classification or {}).get("classification", "REVIEW_REQUIRED"))
        bucket = _priority_bucket(candidate, flagged, classification_name)
        selected_by_bucket[bucket].append(
            {
                "candidate": candidate,
                "temporal_classification": temporal_classification,
                "quality_flagged": flagged,
                "quality_match": match_kind,
                "quality_reasons": quality_reasons,
                "matched_quality_claim_ids": matched_claim_ids,
                "touches_high_claim_scene": _touches_high_claim_scene(candidate, high_claim_scenes),
            }
        )

    queue_items: list[dict[str, Any]] = []
    global_rank = 1
    bucket_counts: Counter[str] = Counter({bucket: 0 for bucket in PRIORITY_BUCKETS})
    for bucket in PRIORITY_BUCKETS:
        for bucket_rank, payload in enumerate(selected_by_bucket[bucket], 1):
            bucket_counts[bucket] += 1
            queue_items.append(
                _queue_item(
                    payload["candidate"],
                    payload["temporal_classification"],
                    bucket,
                    bucket_rank,
                    global_rank,
                    payload["quality_flagged"],
                    payload["quality_match"],
                    payload["quality_reasons"],
                    payload["matched_quality_claim_ids"],
                    payload["touches_high_claim_scene"],
                )
            )
            global_rank += 1

    with queue_jsonl.open("w", encoding="utf-8") as handle:
        for item in queue_items:
            handle.write(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n")
    _write_markdown(queue_md, queue_items, bucket_counts)

    read_errors = candidate_read_errors + classification_read_errors + quality_read_errors
    errors: list[str] = []
    if candidate_read_errors:
        errors.append("contradiction candidate JSONL had read errors")
    if classification_read_errors:
        errors.append("temporal collision classification JSONL had read errors")
    if quality_read_errors:
        errors.append("entity candidate quality flag JSONL had read errors")
    errors.extend(high_claim_errors)

    manifest: dict[str, Any] = {
        "contract": "engain.mrlore_temporal_aware_review_queue_builder.v1",
        "run_timestamp": datetime.now(timezone.utc).isoformat(),
        "source_candidates_jsonl": str(candidates_file),
        "source_temporal_classifications_jsonl": str(classifications_file),
        "source_quality_flags_jsonl": str(quality_flags_file),
        "source_high_claim_scene_review_manifest": str(high_claim_file),
        "queue_jsonl_path": str(queue_jsonl),
        "queue_markdown_path": str(queue_md),
        "manifest_path": str(manifest_path),
        "MRLORE_TEMPORAL_AWARE_REVIEW_QUEUE_BUILDER_COMPLETE": len(errors) == 0,
        "CANDIDATES_READ": len(candidates),
        "TEMPORAL_CLASSIFICATIONS_READ": len(temporal_classifications),
        "QUALITY_FLAGS_READ": len(quality_flags),
        "HIGH_CLAIM_SCENES_READ": len(high_claim_scenes),
        "QUEUE_ITEMS_WRITTEN": len(queue_items),
        "QUALITY_FLAGGED_ITEMS_MARKED": quality_flagged_items_marked,
        "MISSING_TEMPORAL_CLASSIFICATION_COUNT": missing_temporal_classification_count,
        "P0_CONCURRENT_CONFLICT_ITEMS": bucket_counts["P0_CONCURRENT_CONFLICT"],
        "P1_DURABLE_STATE_CONTINUITY_REVIEW_ITEMS": bucket_counts["P1_DURABLE_STATE_CONTINUITY_REVIEW"],
        "P2_TEMPORAL_ORDER_UNKNOWN_ITEMS": bucket_counts["P2_TEMPORAL_ORDER_UNKNOWN"],
        "P3_SEQUENTIAL_STATE_CHANGE_ITEMS": bucket_counts["P3_SEQUENTIAL_STATE_CHANGE"],
        "P4_ENVIRONMENT_REVIEW_ITEMS": bucket_counts["P4_ENVIRONMENT_REVIEW"],
        "P5_CLEAN_ENTITY_REVIEW_ITEMS": bucket_counts["P5_CLEAN_ENTITY_REVIEW"],
        "P9_ENTITY_QUALITY_FLAGGED_ITEMS": bucket_counts["P9_ENTITY_QUALITY_FLAGGED"],
        "SIDE_CAR_ONLY": True,
        "CANDIDATES_ALTERED": False,
        "CLASSIFICATIONS_ALTERED": False,
        "QUALITY_FLAGS_ALTERED": False,
        "CLAIMS_ALTERED": False,
        "CLAIMS_PROMOTED": False,
        "CLAIMS_REJECTED": False,
        "CONTRADICTIONS_RESOLVED": False,
        "CANON_WRITTEN": False,
        "RUNTIME_TOUCHED": False,
        "GODOT_TOUCHED": False,
        "ZONJ_COMPILED": False,
        "ENGINE_AGNOSTIC": True,
        "GODOT_USED_AS_TEMPORAL_AUTHORITY": False,
        "ACCEPTED_LORE_PACKET_EXISTS": False,
        "selection_policy": "write all candidates; quality-flagged entity candidates to P9; otherwise temporal sidecar buckets concurrent/durable/unknown/sequential before environment/clean entity review; no authority effect",
        "read_errors_count": len(read_errors),
        "read_errors": read_errors[:100],
        "errors": errors,
        "errors_count": len(errors),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="MrLore temporal-aware quality review queue builder — no authority writes.")
    parser.add_argument("--candidates", default=None, help="Path to contradiction_candidates.jsonl.")
    parser.add_argument("--temporal-classifications", default=None, help="Path to temporal_collision_classifications.jsonl.")
    parser.add_argument("--quality-flags", default=None, help="Path to entity_candidate_quality_flags.jsonl.")
    parser.add_argument("--high-claim-manifest", default=None, help="Path to high_claim_scene_review_manifest.json.")
    parser.add_argument("--manifest", default=None, help="Path to engain_manifest.json.")
    parser.add_argument("--engain-dir", default=None, help="Direct path to vault/.engain.")
    args = parser.parse_args()

    try:
        manifest_path = Path(args.manifest) if args.manifest else None
        engain_dir = Path(args.engain_dir) if args.engain_dir else None
        candidates_path = Path(args.candidates) if args.candidates else default_candidates_path(manifest_path, engain_dir)
        classifications_path = Path(args.temporal_classifications) if args.temporal_classifications else default_classifications_path(manifest_path, engain_dir)
        quality_flags_path = Path(args.quality_flags) if args.quality_flags else default_quality_flags_path(manifest_path, engain_dir)
        high_claim_manifest_path = Path(args.high_claim_manifest) if args.high_claim_manifest else default_high_claim_manifest_path(manifest_path, engain_dir)
        manifest = run_temporal_aware_review_queue_builder(candidates_path, classifications_path, quality_flags_path, high_claim_manifest_path)
    except Exception as exc:
        print(f"[TEMPORAL_AWARE_REVIEW_QUEUE] ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"MRLORE_TEMPORAL_AWARE_REVIEW_QUEUE_BUILDER_COMPLETE={manifest['MRLORE_TEMPORAL_AWARE_REVIEW_QUEUE_BUILDER_COMPLETE']}")
    print(f"CANDIDATES_READ={manifest['CANDIDATES_READ']}")
    print(f"TEMPORAL_CLASSIFICATIONS_READ={manifest['TEMPORAL_CLASSIFICATIONS_READ']}")
    print(f"QUALITY_FLAGS_READ={manifest['QUALITY_FLAGS_READ']}")
    print(f"QUEUE_ITEMS_WRITTEN={manifest['QUEUE_ITEMS_WRITTEN']}")
    print(f"P0_CONCURRENT_CONFLICT_ITEMS={manifest['P0_CONCURRENT_CONFLICT_ITEMS']}")
    print(f"P1_DURABLE_STATE_CONTINUITY_REVIEW_ITEMS={manifest['P1_DURABLE_STATE_CONTINUITY_REVIEW_ITEMS']}")
    print(f"P2_TEMPORAL_ORDER_UNKNOWN_ITEMS={manifest['P2_TEMPORAL_ORDER_UNKNOWN_ITEMS']}")
    print(f"P3_SEQUENTIAL_STATE_CHANGE_ITEMS={manifest['P3_SEQUENTIAL_STATE_CHANGE_ITEMS']}")
    print(f"P4_ENVIRONMENT_REVIEW_ITEMS={manifest['P4_ENVIRONMENT_REVIEW_ITEMS']}")
    print(f"P5_CLEAN_ENTITY_REVIEW_ITEMS={manifest['P5_CLEAN_ENTITY_REVIEW_ITEMS']}")
    print(f"P9_ENTITY_QUALITY_FLAGGED_ITEMS={manifest['P9_ENTITY_QUALITY_FLAGGED_ITEMS']}")
    print(f"SIDE_CAR_ONLY={manifest['SIDE_CAR_ONLY']}")
    print(f"CANDIDATES_ALTERED={manifest['CANDIDATES_ALTERED']}")
    print(f"CLASSIFICATIONS_ALTERED={manifest['CLASSIFICATIONS_ALTERED']}")
    print(f"CLAIMS_ALTERED={manifest['CLAIMS_ALTERED']}")
    print(f"CLAIMS_PROMOTED={manifest['CLAIMS_PROMOTED']}")
    print(f"CLAIMS_REJECTED={manifest['CLAIMS_REJECTED']}")
    print(f"CONTRADICTIONS_RESOLVED={manifest['CONTRADICTIONS_RESOLVED']}")
    print(f"CANON_WRITTEN={manifest['CANON_WRITTEN']}")
    print(f"RUNTIME_TOUCHED={manifest['RUNTIME_TOUCHED']}")
    print(f"GODOT_TOUCHED={manifest['GODOT_TOUCHED']}")
    print(f"ZONJ_COMPILED={manifest['ZONJ_COMPILED']}")
    print(f"ENGINE_AGNOSTIC={manifest['ENGINE_AGNOSTIC']}")
    print(f"GODOT_USED_AS_TEMPORAL_AUTHORITY={manifest['GODOT_USED_AS_TEMPORAL_AUTHORITY']}")
    print(f"errors_count={manifest['errors_count']}")
    print(f"QUEUE={manifest['queue_jsonl_path']}")
    print(f"MANIFEST={manifest['manifest_path']}")
    return 0 if manifest["MRLORE_TEMPORAL_AWARE_REVIEW_QUEUE_BUILDER_COMPLETE"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
