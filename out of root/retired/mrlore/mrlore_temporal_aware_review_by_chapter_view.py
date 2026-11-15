#!/usr/bin/env python3
"""
mrlore_temporal_aware_review_by_chapter_view.py — chapter-first temporal review view.

PURPOSE:
    Convert temporal_aware_quality_review_queue.jsonl from a bucket-first queue
    into a human-reviewable chapter -> scene -> bucket view. The output is
    non-authoritative and review-only. It preserves queue items in display form
    and does not alter the source queue, claims, candidates, classifications,
    quality flags, canon, runtime, Godot, or ZONJ.

INPUTS:
    vault/.engain/mrlore/review/temporal_aware_quality_review_queue.jsonl
    vault/.engain/mrlore/claims/proposed_claims.temporal_enriched.jsonl
    vault/.engain/manifests/mrlore_temporal_claim_context_manifest.json
    vault/.engain/manifests/mrlore_scene_intake_manifest.json

OUTPUTS:
    vault/.engain/mrlore/review/by_chapter/temporal_aware_review_by_chapter.md
    vault/.engain/mrlore/review/by_chapter/temporal_aware_review_by_chapter.json
    vault/.engain/manifests/temporal_aware_review_by_chapter_manifest.json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BUCKET_ORDER = (
    "P0_CONCURRENT_CONFLICT",
    "P1_DURABLE_STATE_CONTINUITY_REVIEW",
    "P2_TEMPORAL_ORDER_UNKNOWN",
    "P3_SEQUENTIAL_STATE_CHANGE",
    "P8_SECOND_PASS_ENTITY_QUALITY_REVIEW",
    "P4_ENVIRONMENT_REVIEW",
    "P5_CLEAN_ENTITY_REVIEW",
    "P9_ENTITY_QUALITY_FLAGGED",
)
BUCKET_RANK = {bucket: index for index, bucket in enumerate(BUCKET_ORDER)}
REVIEW_SCOPE = "CHAPTER_FIRST_SCENE_SECOND"
CONTRACT = "engain.mrlore_temporal_aware_review_by_chapter.v1"


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


def _infer_engain_dir_from_queue_path(queue_path: Path) -> Path:
    resolved = queue_path.resolve()
    for parent in resolved.parents:
        if parent.name == ".engain":
            return parent
    return resolved.parents[2]


def default_paths(manifest_path: Path | None = None, engain_dir: Path | None = None) -> dict[str, Path]:
    if engain_dir is None:
        engain_dir = _resolve_engain_dir_from_manifest(manifest_path or _default_manifest_path())
    return {
        "queue": engain_dir / "mrlore" / "review" / "temporal_aware_quality_review_queue.jsonl",
        "second_pass_flags": engain_dir / "mrlore" / "review" / "temporal_aware_p3_second_pass_quality_flags.jsonl",
        "claims": engain_dir / "mrlore" / "claims" / "proposed_claims.temporal_enriched.jsonl",
        "temporal_manifest": engain_dir / "manifests" / "mrlore_temporal_claim_context_manifest.json",
        "intake_manifest": engain_dir / "manifests" / "mrlore_scene_intake_manifest.json",
    }


def _read_jsonl(path: Path, noun: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    records: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, 1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append({"path": str(path), "line": line_number, "error": f"invalid JSON: {exc.msg}"})
                continue
            if not isinstance(record, dict):
                errors.append({"path": str(path), "line": line_number, "error": f"{noun} must be a JSON object"})
                continue
            records.append(record)
    return records, errors


def _read_optional_jsonl(path: Path, noun: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not path.exists():
        return [], []
    return _read_jsonl(path, noun)


def _read_json_object(path: Path, noun: str) -> tuple[dict[str, Any], list[str]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}, [f"{noun} not found: {path}"]
    except json.JSONDecodeError as exc:
        return {}, [f"invalid {noun} JSON: {exc.msg}"]
    if not isinstance(data, dict):
        return {}, [f"{noun} must be a JSON object"]
    return data, []


def _scene_id_from_claim(claim: dict[str, Any]) -> str:
    for key in ("source_scene_id", "source_scene", "SOURCE_SCENE"):
        value = claim.get(key)
        if value:
            return str(value)
    return ""


def _chapter_slug(chapter_id: str) -> str:
    return chapter_id.removeprefix("chapter.")


def _chapter_display(chapter_sequence_index: int) -> str:
    return f"C{chapter_sequence_index:03d}"


def _temporal_display_id(global_scene_sequence_index: int, chapter_sequence_index: int, scene_index: int) -> str:
    return f"T{global_scene_sequence_index:06d}.{scene_index:03d}-C{chapter_sequence_index:03d}-S{scene_index:03d}"


def _source_scenes(item: dict[str, Any]) -> list[str]:
    scenes = item.get("source_scenes", [])
    if not isinstance(scenes, list):
        return []
    return [str(scene) for scene in scenes if scene]


def _as_int(value: Any, fallback: int = 0) -> int:
    try:
        if value is None or value == "":
            return fallback
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _as_float(value: Any, fallback: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return fallback
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _scene_order_from_intake(intake_manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    scene_order: dict[str, dict[str, Any]] = {}
    global_counter = 1
    chapters = intake_manifest.get("chapters", [])
    if not isinstance(chapters, list):
        return scene_order
    for chapter_position, chapter in enumerate(chapters, 1):
        if not isinstance(chapter, dict):
            continue
        chapter_id = str(chapter.get("chapter_id", "") or "")
        scenes = chapter.get("scenes", [])
        if not isinstance(scenes, list):
            continue
        for scene_position, scene in enumerate(scenes, 1):
            if not isinstance(scene, dict):
                continue
            scene_id = str(scene.get("scene_id", "") or scene.get("source_scene_id", "") or "")
            if not scene_id:
                continue
            scene_index = _as_int(scene.get("scene_index"), scene_position)
            global_scene_sequence_index = _as_int(scene.get("global_scene_sequence_index"), global_counter)
            scene_order[scene_id] = {
                "chapter_id": chapter_id,
                "chapter_sequence_index": _as_int(chapter.get("chapter_sequence_index"), chapter_position),
                "source_scene_id": scene_id,
                "scene_index": scene_index,
                "global_scene_sequence_index": global_scene_sequence_index,
                "temporal_index": _as_float(scene.get("temporal_index"), float(f"{global_scene_sequence_index}.{scene_index:03d}")),
                "temporal_basis": str(scene.get("temporal_basis", "CHAPTERROOM_SCENE_ORDER") or "CHAPTERROOM_SCENE_ORDER"),
            }
            global_counter += 1
    return scene_order


def _scene_metadata_from_claims(claims: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    metadata: dict[str, dict[str, Any]] = {}
    for claim in claims:
        scene_id = _scene_id_from_claim(claim)
        if not scene_id or scene_id in metadata:
            continue
        scene_index = _as_int(claim.get("scene_index"), 0)
        global_scene_sequence_index = _as_int(claim.get("global_scene_sequence_index"), 0)
        chapter_sequence_index = _as_int(claim.get("chapter_sequence_index"), 0)
        metadata[scene_id] = {
            "chapter_id": str(claim.get("chapter_id", "") or ""),
            "chapter_sequence_index": chapter_sequence_index,
            "source_scene_id": scene_id,
            "scene_index": scene_index,
            "global_scene_sequence_index": global_scene_sequence_index,
            "temporal_index": _as_float(
                claim.get("temporal_index"),
                float(f"{global_scene_sequence_index}.{scene_index:03d}") if global_scene_sequence_index and scene_index else 0.0,
            ),
            "temporal_basis": str(claim.get("temporal_basis", "") or ""),
        }
    return metadata


def _claim_by_id(claims: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(claim.get("claim_id")): claim for claim in claims if claim.get("claim_id")}


def _merge_scene_metadata(
    scene_id: str,
    scene_order: dict[str, dict[str, Any]],
    scene_claims: dict[str, dict[str, Any]],
    temporal_basis: str,
) -> dict[str, Any]:
    base = dict(scene_order.get(scene_id, {}))
    claim = scene_claims.get(scene_id, {})
    for key in (
        "chapter_id",
        "chapter_sequence_index",
        "source_scene_id",
        "scene_index",
        "global_scene_sequence_index",
        "temporal_index",
        "temporal_basis",
    ):
        value = claim.get(key)
        if value not in (None, "", 0, 0.0):
            base[key] = value
    if not base:
        base = {
            "chapter_id": "UNKNOWN_CHAPTER",
            "chapter_sequence_index": 999999,
            "source_scene_id": scene_id or "UNKNOWN_SCENE",
            "scene_index": 999999,
            "global_scene_sequence_index": 999999,
            "temporal_index": 999999.0,
            "temporal_basis": temporal_basis or "UNKNOWN_TEMPORAL_BASIS",
        }
    base.setdefault("source_scene_id", scene_id or "UNKNOWN_SCENE")
    base.setdefault("chapter_id", "UNKNOWN_CHAPTER")
    base.setdefault("chapter_sequence_index", 999999)
    base.setdefault("scene_index", 999999)
    base.setdefault("global_scene_sequence_index", 999999)
    base.setdefault("temporal_index", float(f"{_as_int(base['global_scene_sequence_index'], 999999)}.{_as_int(base['scene_index'], 999):03d}"))
    base.setdefault("temporal_basis", temporal_basis or "UNKNOWN_TEMPORAL_BASIS")
    return base


def _primary_scene_id(
    item: dict[str, Any],
    scene_order: dict[str, dict[str, Any]],
    scene_claims: dict[str, dict[str, Any]],
    claims_by_id: dict[str, dict[str, Any]],
) -> str:
    scene_ids = _source_scenes(item)
    if not scene_ids:
        for claim_id in item.get("matched_quality_claim_ids", []) or []:
            claim = claims_by_id.get(str(claim_id))
            if claim:
                scene_id = _scene_id_from_claim(claim)
                if scene_id:
                    scene_ids.append(scene_id)
    if not scene_ids:
        return "UNKNOWN_SCENE"

    def scene_sort_key(scene_id: str) -> tuple[int, int, str]:
        metadata = scene_claims.get(scene_id) or scene_order.get(scene_id) or {}
        return (
            _as_int(metadata.get("global_scene_sequence_index"), 999999),
            _as_int(metadata.get("scene_index"), 999999),
            scene_id,
        )

    return sorted(scene_ids, key=scene_sort_key)[0]


def _item_for_view(
    item: dict[str, Any],
    scene_metadata: dict[str, Any],
    second_pass_flags_by_queue_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    objects = item.get("objects", [])
    if not isinstance(objects, list):
        objects = []
    queue_id = str(item.get("queue_id", "") or "")
    source_priority_bucket = str(item.get("priority_bucket", "UNKNOWN") or "UNKNOWN")
    second_pass_flag = second_pass_flags_by_queue_id.get(queue_id, {})
    second_pass_quality_flagged = bool(second_pass_flag.get("second_pass_quality_flagged", False))
    priority_bucket = (
        "P8_SECOND_PASS_ENTITY_QUALITY_REVIEW"
        if second_pass_quality_flagged and source_priority_bucket == "P3_SEQUENTIAL_STATE_CHANGE"
        else source_priority_bucket
    )
    second_pass_reasons = second_pass_flag.get("second_pass_reasons", [])
    if not isinstance(second_pass_reasons, list):
        second_pass_reasons = []
    return {
        "queue_id": queue_id,
        "candidate_id": str(item.get("candidate_id", "") or ""),
        "priority_bucket": priority_bucket,
        "source_priority_bucket": source_priority_bucket,
        "claim_domain": str(item.get("claim_domain", "") or ""),
        "predicate": str(item.get("predicate", "") or ""),
        "temporal_classification": str(item.get("temporal_classification", "") or ""),
        "subject": str(item.get("subject", "") or ""),
        "objects": [str(obj) for obj in objects],
        "source_scenes": _source_scenes(item),
        "source_scene_id": scene_metadata["source_scene_id"],
        "chapter_id": scene_metadata["chapter_id"],
        "chapter_sequence_index": _as_int(scene_metadata["chapter_sequence_index"]),
        "scene_index": _as_int(scene_metadata["scene_index"]),
        "global_scene_sequence_index": _as_int(scene_metadata["global_scene_sequence_index"]),
        "temporal_index": _as_float(scene_metadata["temporal_index"]),
        "temporal_basis": str(scene_metadata.get("temporal_basis", "") or ""),
        "temporal_display_id": _temporal_display_id(
            _as_int(scene_metadata["global_scene_sequence_index"]),
            _as_int(scene_metadata["chapter_sequence_index"]),
            _as_int(scene_metadata["scene_index"]),
        ),
        "entity_quality_flagged": bool(item.get("entity_quality_flagged", False)),
        "quality_reasons": item.get("quality_reasons", []) if isinstance(item.get("quality_reasons", []), list) else [],
        "second_pass_quality_flagged": second_pass_quality_flagged,
        "second_pass_reasons": [str(reason) for reason in second_pass_reasons if reason],
        "second_pass_flag_id": str(second_pass_flag.get("flag_id", "") or ""),
        "status": str(item.get("status", "") or ""),
        "authority_effect": str(item.get("authority_effect", "NONE") or "NONE"),
    }


def _sorted_counter_dict(counter: Counter[str]) -> dict[str, int]:
    return {key: counter[key] for key in sorted(counter, key=lambda bucket: (BUCKET_RANK.get(bucket, 999), bucket))}


def _build_view(
    queue_items: list[dict[str, Any]],
    scene_order: dict[str, dict[str, Any]],
    scene_claims: dict[str, dict[str, Any]],
    claims_by_id: dict[str, dict[str, Any]],
    second_pass_flags_by_queue_id: dict[str, dict[str, Any]],
    temporal_basis: str,
    queue_path: Path,
) -> tuple[dict[str, Any], int, int, bool, Counter[str], int]:
    grouped: dict[tuple[int, str], dict[tuple[int, int, str], list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    display_ids_written = True
    display_bucket_counts: Counter[str] = Counter()
    second_pass_p3_items_displayed_in_p8 = 0

    for item in queue_items:
        scene_id = _primary_scene_id(item, scene_order, scene_claims, claims_by_id)
        scene_metadata = _merge_scene_metadata(scene_id, scene_order, scene_claims, temporal_basis)
        view_item = _item_for_view(item, scene_metadata, second_pass_flags_by_queue_id)
        if not view_item["temporal_display_id"]:
            display_ids_written = False
        display_bucket_counts[view_item["priority_bucket"]] += 1
        if (
            view_item["priority_bucket"] == "P8_SECOND_PASS_ENTITY_QUALITY_REVIEW"
            and view_item["source_priority_bucket"] == "P3_SEQUENTIAL_STATE_CHANGE"
        ):
            second_pass_p3_items_displayed_in_p8 += 1
        chapter_key = (view_item["chapter_sequence_index"], view_item["chapter_id"])
        scene_key = (view_item["global_scene_sequence_index"], view_item["scene_index"], view_item["source_scene_id"])
        grouped[chapter_key][scene_key].append(view_item)

    chapters: list[dict[str, Any]] = []
    scenes_written = 0
    for chapter_key in sorted(grouped):
        chapter_sequence_index, chapter_id = chapter_key
        scene_entries: list[dict[str, Any]] = []
        chapter_total_items = 0
        for scene_key in sorted(grouped[chapter_key]):
            scene_items = grouped[chapter_key][scene_key]
            scene_items.sort(
                key=lambda item: (
                    BUCKET_RANK.get(item["priority_bucket"], 999),
                    item.get("candidate_id", ""),
                    item.get("queue_id", ""),
                )
            )
            bucket_counts = Counter(item["priority_bucket"] for item in scene_items)
            first = scene_items[0]
            scene_entries.append(
                {
                    "source_scene_id": first["source_scene_id"],
                    "scene_index": first["scene_index"],
                    "global_scene_sequence_index": first["global_scene_sequence_index"],
                    "temporal_index": first["temporal_index"],
                    "temporal_basis": first["temporal_basis"],
                    "temporal_display_id": first["temporal_display_id"],
                    "scene_total_items": len(scene_items),
                    "bucket_counts": _sorted_counter_dict(bucket_counts),
                    "items": scene_items,
                }
            )
            chapter_total_items += len(scene_items)
            scenes_written += 1
        chapters.append(
            {
                "chapter_id": chapter_id,
                "chapter_sequence_index": chapter_sequence_index,
                "chapter_total_items": chapter_total_items,
                "scenes": scene_entries,
            }
        )

    view = {
        "contract": CONTRACT,
        "review_scope": REVIEW_SCOPE,
        "source_queue": str(queue_path),
        "authority_effect": "NONE",
        "chapters": chapters,
    }
    return view, len(chapters), scenes_written, display_ids_written, display_bucket_counts, second_pass_p3_items_displayed_in_p8


def _write_markdown(path: Path, view: dict[str, Any]) -> None:
    lines: list[str] = [
        "# MrLore Temporal-Aware Review By Chapter",
        "",
        "Generated from temporal-aware queue.",
        "This file is non-authoritative and review-only.",
        "",
    ]
    for chapter in view["chapters"]:
        chapter_sequence_index = _as_int(chapter["chapter_sequence_index"])
        chapter_id = str(chapter["chapter_id"])
        lines.extend(
            [
                f"## Chapter {_chapter_display(chapter_sequence_index)} — {_chapter_slug(chapter_id)}",
                "",
                f"chapter_sequence_index: {chapter_sequence_index}",
                f"chapter_id: {chapter_id}",
                f"chapter_total_items: {chapter['chapter_total_items']}",
                "",
            ]
        )
        for scene in chapter["scenes"]:
            lines.extend(
                [
                    f"### Scene {scene['temporal_display_id']} — {scene['source_scene_id']}",
                    "",
                    f"source_scene_id: {scene['source_scene_id']}",
                    f"scene_index: {scene['scene_index']}",
                    f"global_scene_sequence_index: {scene['global_scene_sequence_index']}",
                    f"temporal_index: {scene['temporal_index']}",
                    f"temporal_basis: {scene['temporal_basis']}",
                    f"scene_total_items: {scene['scene_total_items']}",
                    "",
                ]
            )
            items_by_bucket: dict[str, list[dict[str, Any]]] = defaultdict(list)
            for item in scene["items"]:
                items_by_bucket[item["priority_bucket"]].append(item)
            for bucket in BUCKET_ORDER:
                bucket_items = items_by_bucket.get(bucket, [])
                if not bucket_items:
                    continue
                lines.extend([f"#### {bucket}", ""])
                for item in bucket_items:
                    objects = item.get("objects", [])
                    subject_object = item["subject"]
                    if objects:
                        subject_object = f"{subject_object} -> {', '.join(str(obj) for obj in objects[:3])}"
                    quality = " QUALITY_FLAGGED" if item.get("entity_quality_flagged") else ""
                    second_pass = " SECOND_PASS_QUALITY" if item.get("second_pass_quality_flagged") else ""
                    lines.append(
                        f"- {item['candidate_id']} | {item['claim_domain']} | {item['predicate']} | "
                        f"{item['temporal_classification']} | {subject_object} | scenes={len(item.get('source_scenes', []))}{quality}{second_pass}"
                    )
                lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def run_temporal_aware_review_by_chapter_view(
    queue_path: Path | str,
    temporal_enriched_claims_path: Path | str,
    temporal_context_manifest_path: Path | str,
    scene_intake_manifest_path: Path | str,
    second_pass_flags_path: Path | str | None = None,
) -> dict[str, Any]:
    queue_file = Path(queue_path).resolve()
    claims_file = Path(temporal_enriched_claims_path).resolve()
    temporal_manifest_file = Path(temporal_context_manifest_path).resolve()
    intake_manifest_file = Path(scene_intake_manifest_path).resolve()
    engain_dir = _infer_engain_dir_from_queue_path(queue_file)
    second_pass_flags_file = (
        Path(second_pass_flags_path).resolve()
        if second_pass_flags_path
        else engain_dir / "mrlore" / "review" / "temporal_aware_p3_second_pass_quality_flags.jsonl"
    )
    by_chapter_dir = engain_dir / "mrlore" / "review" / "by_chapter"
    json_path = by_chapter_dir / "temporal_aware_review_by_chapter.json"
    markdown_path = by_chapter_dir / "temporal_aware_review_by_chapter.md"
    manifest_path = engain_dir / "manifests" / "temporal_aware_review_by_chapter_manifest.json"
    by_chapter_dir.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    queue_items, queue_read_errors = _read_jsonl(queue_file, "temporal-aware queue item")
    second_pass_flags, second_pass_flag_read_errors = _read_optional_jsonl(second_pass_flags_file, "second-pass P3 quality flag")
    claims, claim_read_errors = _read_jsonl(claims_file, "temporal-enriched claim")
    temporal_manifest, temporal_manifest_errors = _read_json_object(temporal_manifest_file, "temporal context manifest")
    intake_manifest, intake_manifest_errors = _read_json_object(intake_manifest_file, "scene intake manifest")

    temporal_basis = str(temporal_manifest.get("TEMPORAL_BASIS", "CHAPTERROOM_SCENE_ORDER") or "CHAPTERROOM_SCENE_ORDER")
    errors: list[str] = []
    if queue_read_errors:
        errors.append("temporal-aware queue JSONL had read errors")
    if claim_read_errors:
        errors.append("temporal-enriched claims JSONL had read errors")
    if second_pass_flag_read_errors:
        errors.append("second-pass P3 quality flags JSONL had read errors")
    errors.extend(temporal_manifest_errors)
    errors.extend(intake_manifest_errors)
    if temporal_manifest and not temporal_manifest.get("MRLORE_TEMPORAL_CLAIM_CONTEXT_ENRICHMENT_COMPLETE", False):
        errors.append("temporal claim context manifest is incomplete")

    scene_order = _scene_order_from_intake(intake_manifest)
    scene_claims = _scene_metadata_from_claims(claims)
    claims_index = _claim_by_id(claims)
    second_pass_flags_by_queue_id = {
        str(flag.get("queue_id")): flag
        for flag in second_pass_flags
        if flag.get("queue_id") and flag.get("second_pass_quality_flagged") is True
    }
    view, chapters_written, scenes_written, display_ids_written, display_bucket_counts, second_pass_p3_items_displayed_in_p8 = _build_view(
        queue_items,
        scene_order,
        scene_claims,
        claims_index,
        second_pass_flags_by_queue_id,
        temporal_basis,
        queue_file,
    )

    json_path.write_text(json.dumps(view, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    _write_markdown(markdown_path, view)

    queue_ids_written = {
        item.get("queue_id")
        for chapter in view["chapters"]
        for scene in chapter["scenes"]
        for item in scene["items"]
        if item.get("queue_id")
    }
    queue_item_ids = {str(item.get("queue_id", "")) for item in queue_items if item.get("queue_id")}
    if queue_ids_written != queue_item_ids:
        errors.append("not all queue items were represented in by-chapter view")

    manifest: dict[str, Any] = {
        "contract": "engain.mrlore_temporal_aware_review_by_chapter_manifest.v1",
        "run_timestamp": datetime.now(timezone.utc).isoformat(),
        "source_queue": str(queue_file),
        "source_temporal_enriched_claims": str(claims_file),
        "source_temporal_context_manifest": str(temporal_manifest_file),
        "source_scene_intake_manifest": str(intake_manifest_file),
        "source_second_pass_p3_quality_flags": str(second_pass_flags_file),
        "json_view_path": str(json_path),
        "markdown_view_path": str(markdown_path),
        "manifest_path": str(manifest_path),
        "MRLORE_TEMPORAL_AWARE_REVIEW_BY_CHAPTER_VIEW_COMPLETE": len(errors) == 0,
        "MRLORE_TEMPORAL_AWARE_REVIEW_BY_CHAPTER_VIEW_V2": True,
        "QUEUE_ITEMS_READ": len(queue_items),
        "SECOND_PASS_FLAGS_READ": len(second_pass_flags),
        "SECOND_PASS_P3_ITEMS_DISPLAYED_IN_P8": second_pass_p3_items_displayed_in_p8,
        "display_bucket_counts": _sorted_counter_dict(display_bucket_counts),
        "QUEUE_ITEMS_WRITTEN_TO_VIEW": len(queue_ids_written),
        "CHAPTERS_WRITTEN": chapters_written,
        "SCENES_WRITTEN": scenes_written,
        "TEMPORAL_DISPLAY_IDS_WRITTEN": display_ids_written,
        "REVIEW_SCOPE": REVIEW_SCOPE,
        "SOURCE_QUEUE_ALTERED": False,
        "SECOND_PASS_FLAGS_ALTERED": False,
        "CLAIMS_ALTERED": False,
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
        "ENGINE_AGNOSTIC": True,
        "GODOT_USED_AS_TEMPORAL_AUTHORITY": False,
        "authority_effect": "NONE",
        "read_errors_count": len(queue_read_errors) + len(claim_read_errors) + len(second_pass_flag_read_errors),
        "read_errors": (queue_read_errors + claim_read_errors + second_pass_flag_read_errors)[:100],
        "errors": errors,
        "errors_count": len(errors),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Build MrLore temporal-aware review by-chapter view without mutation.")
    parser.add_argument("--queue", default=None, help="Path to temporal_aware_quality_review_queue.jsonl.")
    parser.add_argument("--temporal-enriched-claims", default=None, help="Path to proposed_claims.temporal_enriched.jsonl.")
    parser.add_argument("--temporal-context-manifest", default=None, help="Path to mrlore_temporal_claim_context_manifest.json.")
    parser.add_argument("--scene-intake-manifest", default=None, help="Path to mrlore_scene_intake_manifest.json.")
    parser.add_argument("--second-pass-flags", default=None, help="Path to temporal_aware_p3_second_pass_quality_flags.jsonl.")
    parser.add_argument("--manifest", default=None, help="Path to engain_manifest.json.")
    parser.add_argument("--engain-dir", default=None, help="Direct path to vault/.engain.")
    args = parser.parse_args()

    try:
        manifest_path = Path(args.manifest) if args.manifest else None
        engain_dir = Path(args.engain_dir) if args.engain_dir else None
        paths = default_paths(manifest_path, engain_dir)
        queue_path = Path(args.queue) if args.queue else paths["queue"]
        claims_path = Path(args.temporal_enriched_claims) if args.temporal_enriched_claims else paths["claims"]
        temporal_context_manifest_path = Path(args.temporal_context_manifest) if args.temporal_context_manifest else paths["temporal_manifest"]
        scene_intake_manifest_path = Path(args.scene_intake_manifest) if args.scene_intake_manifest else paths["intake_manifest"]
        second_pass_flags_path = Path(args.second_pass_flags) if args.second_pass_flags else paths["second_pass_flags"]
        manifest = run_temporal_aware_review_by_chapter_view(
            queue_path,
            claims_path,
            temporal_context_manifest_path,
            scene_intake_manifest_path,
            second_pass_flags_path=second_pass_flags_path,
        )
    except Exception as exc:
        print(f"[TEMPORAL_AWARE_REVIEW_BY_CHAPTER] ERROR: {exc}", file=sys.stderr)
        return 1

    print(
        "[TEMPORAL_AWARE_REVIEW_BY_CHAPTER] "
        f"MRLORE_TEMPORAL_AWARE_REVIEW_BY_CHAPTER_VIEW_COMPLETE={manifest['MRLORE_TEMPORAL_AWARE_REVIEW_BY_CHAPTER_VIEW_COMPLETE']}"
    )
    print(f"[TEMPORAL_AWARE_REVIEW_BY_CHAPTER] QUEUE_ITEMS_READ={manifest['QUEUE_ITEMS_READ']}")
    print(f"[TEMPORAL_AWARE_REVIEW_BY_CHAPTER] SECOND_PASS_FLAGS_READ={manifest['SECOND_PASS_FLAGS_READ']}")
    print(f"[TEMPORAL_AWARE_REVIEW_BY_CHAPTER] SECOND_PASS_P3_ITEMS_DISPLAYED_IN_P8={manifest['SECOND_PASS_P3_ITEMS_DISPLAYED_IN_P8']}")
    print(f"[TEMPORAL_AWARE_REVIEW_BY_CHAPTER] display_bucket_counts={manifest['display_bucket_counts']}")
    print(f"[TEMPORAL_AWARE_REVIEW_BY_CHAPTER] QUEUE_ITEMS_WRITTEN_TO_VIEW={manifest['QUEUE_ITEMS_WRITTEN_TO_VIEW']}")
    print(f"[TEMPORAL_AWARE_REVIEW_BY_CHAPTER] CHAPTERS_WRITTEN={manifest['CHAPTERS_WRITTEN']}")
    print(f"[TEMPORAL_AWARE_REVIEW_BY_CHAPTER] SCENES_WRITTEN={manifest['SCENES_WRITTEN']}")
    print(f"[TEMPORAL_AWARE_REVIEW_BY_CHAPTER] TEMPORAL_DISPLAY_IDS_WRITTEN={manifest['TEMPORAL_DISPLAY_IDS_WRITTEN']}")
    print(f"[TEMPORAL_AWARE_REVIEW_BY_CHAPTER] REVIEW_SCOPE={manifest['REVIEW_SCOPE']}")
    print(f"[TEMPORAL_AWARE_REVIEW_BY_CHAPTER] SOURCE_QUEUE_ALTERED={manifest['SOURCE_QUEUE_ALTERED']}")
    print(f"[TEMPORAL_AWARE_REVIEW_BY_CHAPTER] CLAIMS_ALTERED={manifest['CLAIMS_ALTERED']}")
    print(f"[TEMPORAL_AWARE_REVIEW_BY_CHAPTER] CANDIDATES_ALTERED={manifest['CANDIDATES_ALTERED']}")
    print(f"[TEMPORAL_AWARE_REVIEW_BY_CHAPTER] CLASSIFICATIONS_ALTERED={manifest['CLASSIFICATIONS_ALTERED']}")
    print(f"[TEMPORAL_AWARE_REVIEW_BY_CHAPTER] QUALITY_FLAGS_ALTERED={manifest['QUALITY_FLAGS_ALTERED']}")
    print(f"[TEMPORAL_AWARE_REVIEW_BY_CHAPTER] CLAIMS_PROMOTED={manifest['CLAIMS_PROMOTED']}")
    print(f"[TEMPORAL_AWARE_REVIEW_BY_CHAPTER] CLAIMS_REJECTED={manifest['CLAIMS_REJECTED']}")
    print(f"[TEMPORAL_AWARE_REVIEW_BY_CHAPTER] CONTRADICTIONS_RESOLVED={manifest['CONTRADICTIONS_RESOLVED']}")
    print(f"[TEMPORAL_AWARE_REVIEW_BY_CHAPTER] CANON_WRITTEN={manifest['CANON_WRITTEN']}")
    print(f"[TEMPORAL_AWARE_REVIEW_BY_CHAPTER] RUNTIME_TOUCHED={manifest['RUNTIME_TOUCHED']}")
    print(f"[TEMPORAL_AWARE_REVIEW_BY_CHAPTER] GODOT_TOUCHED={manifest['GODOT_TOUCHED']}")
    print(f"[TEMPORAL_AWARE_REVIEW_BY_CHAPTER] ZONJ_COMPILED={manifest['ZONJ_COMPILED']}")
    print(f"[TEMPORAL_AWARE_REVIEW_BY_CHAPTER] ENGINE_AGNOSTIC={manifest['ENGINE_AGNOSTIC']}")
    print(f"[TEMPORAL_AWARE_REVIEW_BY_CHAPTER] GODOT_USED_AS_TEMPORAL_AUTHORITY={manifest['GODOT_USED_AS_TEMPORAL_AUTHORITY']}")
    print(f"[TEMPORAL_AWARE_REVIEW_BY_CHAPTER] errors_count={manifest['errors_count']}")
    print(f"[TEMPORAL_AWARE_REVIEW_BY_CHAPTER] JSON_VIEW={manifest['json_view_path']}")
    print(f"[TEMPORAL_AWARE_REVIEW_BY_CHAPTER] MARKDOWN_VIEW={manifest['markdown_view_path']}")
    print(f"[TEMPORAL_AWARE_REVIEW_BY_CHAPTER] MANIFEST={manifest['manifest_path']}")
    return 0 if manifest["MRLORE_TEMPORAL_AWARE_REVIEW_BY_CHAPTER_VIEW_COMPLETE"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
