#!/usr/bin/env python3
"""
mrlore_quality_aware_review_queue_builder.py — build review queue with entity quality flags.

PURPOSE:
    Read contradiction candidates, entity candidate quality flags, and the high
    claim scene review manifest. Write a new quality-aware review queue that
    marks/down-ranks likely extraction-noise entity candidates without deleting
    candidates, rejecting claims, promoting claims, resolving contradictions, or
    writing canon.

INPUTS:
    vault/.engain/mrlore/contradictions/contradiction_candidates.jsonl
    vault/.engain/mrlore/claims/entity_candidate_quality_flags.jsonl
    vault/.engain/manifests/high_claim_scene_review_manifest.json

OUTPUTS:
    vault/.engain/mrlore/review/quality_aware_contradiction_review_queue.jsonl
    vault/.engain/mrlore/review/quality_aware_contradiction_review_queue.md
    vault/.engain/manifests/quality_aware_review_queue_manifest.json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PRIORITY_BUCKETS = ("P0_HIGH_CLAIM", "P1_ENVIRONMENT", "P2_CLEAN_ENTITY", "P3_OTHER", "P9_ENTITY_QUALITY_FLAGGED")


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


def _priority_bucket(candidate: dict[str, Any], quality_flagged: bool, touches_high_claim_scene: bool) -> str:
    if candidate.get("claim_domain") == "entity" and quality_flagged:
        return "P9_ENTITY_QUALITY_FLAGGED"
    if touches_high_claim_scene:
        return "P0_HIGH_CLAIM"
    if candidate.get("claim_domain") == "environment":
        return "P1_ENVIRONMENT"
    if candidate.get("claim_domain") == "entity" and candidate.get("predicate") == "present_in":
        return "P2_CLEAN_ENTITY"
    return "P3_OTHER"


def _queue_item(
    candidate: dict[str, Any],
    priority_bucket: str,
    bucket_rank: int,
    global_rank: int,
    quality_flagged: bool,
    quality_match: str,
    quality_reasons: list[str],
    matched_quality_claim_ids: list[str],
    touches_high_claim_scene: bool,
) -> dict[str, Any]:
    return {
        "queue_id": f"quality_aware_review_queue.{priority_bucket.lower()}.{bucket_rank:04d}",
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
        "entity_quality_flagged": quality_flagged,
        "quality_flag_match": quality_match,
        "quality_reasons": quality_reasons,
        "matched_quality_claim_ids": matched_quality_claim_ids,
        "review_flags": list(candidate.get("review_flags", [])) + (["ENTITY_CANDIDATE_QUALITY_REVIEW_REQUIRED"] if quality_flagged else []),
        "reasons": candidate.get("reasons", []),
        "status": "QUALITY_AWARE_REVIEW_QUEUED",
        "candidate_altered": False,
        "claim_promoted": False,
        "claim_rejected": False,
        "contradiction_resolved": False,
        "canon_written": False,
    }


def _write_markdown(path: Path, queue_items: list[dict[str, Any]], bucket_counts: Counter[str]) -> None:
    lines = [
        "# MrLore Quality-Aware Contradiction Review Queue",
        "",
        "Scope: quality-aware display queue only. No deletion, claim rejection, claim promotion, contradiction resolution, canon write, ZONJ compile, Godot touch, or runtime touch.",
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
            reasons = ",".join(item.get("quality_reasons", []))
            lines.append(
                f"- {item['queue_id']} | {item['candidate_id']} | {item['claim_domain']} | "
                f"{item['predicate']} | {item['subject']} | scenes={len(item.get('source_scenes', []))}{quality} {reasons}".rstrip()
            )
        lines.append("")
    lines.extend(["## Bucket Counts", ""])
    lines.extend(f"- {bucket}: {bucket_counts[bucket]}" for bucket in PRIORITY_BUCKETS)
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def run_quality_aware_review_queue_builder(
    candidates_path: Path | str,
    quality_flags_path: Path | str,
    high_claim_manifest_path: Path | str,
) -> dict[str, Any]:
    candidates_file = Path(candidates_path).resolve()
    quality_flags_file = Path(quality_flags_path).resolve()
    high_claim_file = Path(high_claim_manifest_path).resolve()
    engain_dir = _infer_engain_dir_from_candidates_path(candidates_file)
    review_dir = engain_dir / "mrlore" / "review"
    queue_jsonl = review_dir / "quality_aware_contradiction_review_queue.jsonl"
    queue_md = review_dir / "quality_aware_contradiction_review_queue.md"
    manifest_path = engain_dir / "manifests" / "quality_aware_review_queue_manifest.json"
    review_dir.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    candidates, candidate_read_errors = _read_jsonl(candidates_file, "candidate")
    quality_flags, quality_read_errors = _read_jsonl(quality_flags_file, "quality flag")
    high_claim_scenes, high_claim_errors = _read_high_claim_scenes(high_claim_file)
    by_claim_id, by_subject = _quality_indexes(quality_flags)

    selected_by_bucket: dict[str, list[dict[str, Any]]] = {bucket: [] for bucket in PRIORITY_BUCKETS}
    quality_flagged_items_marked = 0
    for candidate in candidates:
        flagged, match_kind, reasons, matched_claim_ids = _quality_match(candidate, by_claim_id, by_subject)
        touches_high = _touches_high_claim_scene(candidate, high_claim_scenes)
        bucket = _priority_bucket(candidate, flagged, touches_high)
        if flagged:
            quality_flagged_items_marked += 1
        selected_by_bucket[bucket].append(
            {
                "candidate": candidate,
                "quality_flagged": flagged,
                "quality_match": match_kind,
                "quality_reasons": reasons,
                "matched_quality_claim_ids": matched_claim_ids,
                "touches_high_claim_scene": touches_high,
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

    read_errors = candidate_read_errors + quality_read_errors
    errors: list[str] = []
    if candidate_read_errors:
        errors.append("contradiction candidate JSONL had read errors")
    if quality_read_errors:
        errors.append("entity candidate quality flag JSONL had read errors")
    errors.extend(high_claim_errors)

    manifest: dict[str, Any] = {
        "contract": "engain.mrlore_quality_aware_review_queue_builder.v1",
        "run_timestamp": datetime.now(timezone.utc).isoformat(),
        "source_candidates_jsonl": str(candidates_file),
        "source_quality_flags_jsonl": str(quality_flags_file),
        "source_high_claim_scene_review_manifest": str(high_claim_file),
        "queue_jsonl_path": str(queue_jsonl),
        "queue_markdown_path": str(queue_md),
        "manifest_path": str(manifest_path),
        "MRLORE_QUALITY_AWARE_REVIEW_QUEUE_BUILDER_COMPLETE": len(errors) == 0,
        "CANDIDATES_READ": len(candidates),
        "QUALITY_FLAGS_READ": len(quality_flags),
        "HIGH_CLAIM_SCENES_READ": len(high_claim_scenes),
        "QUEUE_ITEMS_WRITTEN": len(queue_items),
        "QUALITY_FLAGGED_ITEMS_MARKED": quality_flagged_items_marked,
        "P0_HIGH_CLAIM_ITEMS": bucket_counts["P0_HIGH_CLAIM"],
        "P1_ENVIRONMENT_ITEMS": bucket_counts["P1_ENVIRONMENT"],
        "P2_CLEAN_ENTITY_ITEMS": bucket_counts["P2_CLEAN_ENTITY"],
        "P3_OTHER_ITEMS": bucket_counts["P3_OTHER"],
        "P9_ENTITY_QUALITY_FLAGGED_ITEMS": bucket_counts["P9_ENTITY_QUALITY_FLAGGED"],
        "CANDIDATES_ALTERED": False,
        "QUALITY_FLAGS_ALTERED": False,
        "CLAIMS_REJECTED": False,
        "CLAIMS_PROMOTED": False,
        "CONTRADICTIONS_RESOLVED": False,
        "CANON_WRITTEN": False,
        "RUNTIME_TOUCHED": False,
        "GODOT_TOUCHED": False,
        "ZONJ_COMPILED": False,
        "ACCEPTED_LORE_PACKET_EXISTS": False,
        "selection_policy": "write all candidates; down-rank entity candidates with quality flags to P9; preserve environment candidates in P1; mark quality sidecar evidence without authority effect",
        "read_errors_count": len(read_errors),
        "read_errors": read_errors[:100],
        "errors": errors,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="MrLore quality-aware review queue builder — no authority writes.")
    parser.add_argument("--candidates", default=None, help="Path to contradiction_candidates.jsonl.")
    parser.add_argument("--quality-flags", default=None, help="Path to entity_candidate_quality_flags.jsonl.")
    parser.add_argument("--high-claim-manifest", default=None, help="Path to high_claim_scene_review_manifest.json.")
    parser.add_argument("--manifest", default=None, help="Path to engain_manifest.json.")
    parser.add_argument("--engain-dir", default=None, help="Direct path to vault/.engain.")
    args = parser.parse_args()

    try:
        manifest_path = Path(args.manifest) if args.manifest else None
        engain_dir = Path(args.engain_dir) if args.engain_dir else None
        candidates_path = Path(args.candidates) if args.candidates else default_candidates_path(manifest_path, engain_dir)
        quality_flags_path = Path(args.quality_flags) if args.quality_flags else default_quality_flags_path(manifest_path, engain_dir)
        high_claim_manifest_path = Path(args.high_claim_manifest) if args.high_claim_manifest else default_high_claim_manifest_path(manifest_path, engain_dir)
        manifest = run_quality_aware_review_queue_builder(candidates_path, quality_flags_path, high_claim_manifest_path)
    except Exception as exc:
        print(f"[QUALITY_AWARE_REVIEW_QUEUE] ERROR: {exc}", file=sys.stderr)
        return 1

    print(
        "[QUALITY_AWARE_REVIEW_QUEUE] "
        f"MRLORE_QUALITY_AWARE_REVIEW_QUEUE_BUILDER_COMPLETE={manifest['MRLORE_QUALITY_AWARE_REVIEW_QUEUE_BUILDER_COMPLETE']}"
    )
    print(f"[QUALITY_AWARE_REVIEW_QUEUE] CANDIDATES_READ={manifest['CANDIDATES_READ']}")
    print(f"[QUALITY_AWARE_REVIEW_QUEUE] QUALITY_FLAGS_READ={manifest['QUALITY_FLAGS_READ']}")
    print(f"[QUALITY_AWARE_REVIEW_QUEUE] QUEUE_ITEMS_WRITTEN={manifest['QUEUE_ITEMS_WRITTEN']}")
    print(f"[QUALITY_AWARE_REVIEW_QUEUE] QUALITY_FLAGGED_ITEMS_MARKED={manifest['QUALITY_FLAGGED_ITEMS_MARKED']}")
    print(f"[QUALITY_AWARE_REVIEW_QUEUE] CLAIMS_REJECTED={manifest['CLAIMS_REJECTED']}")
    print(f"[QUALITY_AWARE_REVIEW_QUEUE] CLAIMS_PROMOTED={manifest['CLAIMS_PROMOTED']}")
    print(f"[QUALITY_AWARE_REVIEW_QUEUE] CONTRADICTIONS_RESOLVED={manifest['CONTRADICTIONS_RESOLVED']}")
    print(f"[QUALITY_AWARE_REVIEW_QUEUE] CANON_WRITTEN={manifest['CANON_WRITTEN']}")
    print(f"[QUALITY_AWARE_REVIEW_QUEUE] RUNTIME_TOUCHED={manifest['RUNTIME_TOUCHED']}")
    print(f"[QUALITY_AWARE_REVIEW_QUEUE] GODOT_TOUCHED={manifest['GODOT_TOUCHED']}")
    print(f"[QUALITY_AWARE_REVIEW_QUEUE] ZONJ_COMPILED={manifest['ZONJ_COMPILED']}")
    print(f"[QUALITY_AWARE_REVIEW_QUEUE] QUEUE={manifest['queue_jsonl_path']}")
    print(f"[QUALITY_AWARE_REVIEW_QUEUE] MANIFEST={manifest['manifest_path']}")
    return 0 if manifest["MRLORE_QUALITY_AWARE_REVIEW_QUEUE_BUILDER_COMPLETE"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
