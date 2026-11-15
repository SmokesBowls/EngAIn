#!/usr/bin/env python3
"""
mrlore_revision_breathing_map.py — author-facing MrLore revision breathing map.

PURPOSE:
    Read the live vault/.engain/mrlore generated analysis body and emit a
    non-authoring revision guidance layer. This diagnostic identifies chapters
    where claim density, temporal/cosmic context, contradiction pressure, and
    review queue pressure are high. It never rewrites prose, promotes/rejects
    claims, resolves contradictions, writes canon, compiles ZONJ, or touches
    Godot/runtime systems.

PRIMARY INPUTS:
    vault/.engain/mrlore/claims/proposed_claims.jsonl
    vault/.engain/mrlore/claims/proposed_claims.temporal_enriched.jsonl
    vault/.engain/mrlore/claims/proposed_claims.cosmic_enriched.jsonl
    vault/.engain/mrlore/contradictions/contradiction_candidates.jsonl
    vault/.engain/mrlore/contradictions/temporal_collision_classifications.jsonl
    vault/.engain/mrlore/review/temporal_aware_quality_review_queue.jsonl
    vault/.engain/mrlore/review/by_chapter/temporal_aware_review_by_chapter.json
    vault/.engain/mrlore/timeline/coming_calendar.json
    vault/.engain/mrlore/lexicon/predicate_collision_policy.json
    vault/.engain/mrlore/lexicon/preserve_entity_allowlist.json

OUTPUTS:
    vault/.engain/mrlore/revision/breathing_map.jsonl
    vault/.engain/mrlore/revision/breathing_map.md
    vault/.engain/manifests/mrlore_revision_breathing_map_manifest.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CONTRACT = "engain.mrlore_revision_breathing_map.v2"
MANIFEST_CONTRACT = "engain.mrlore_revision_breathing_map_manifest.v2"
REVISION_SCOPE = "AUTHOR_FACING_BREATHING_GUIDANCE_ONLY"

BUCKET_WEIGHTS: dict[str, float] = {
    "P0_CONCURRENT_CONFLICT": 9.0,
    "P1_DURABLE_STATE_CONTINUITY_REVIEW": 8.0,
    "P2_TEMPORAL_ORDER_UNKNOWN": 6.0,
    "P8_SECOND_PASS_ENTITY_QUALITY_REVIEW": 5.0,
    "P3_SEQUENTIAL_STATE_CHANGE": 3.0,
    "P4_ENVIRONMENT_REVIEW": 2.0,
    "P5_CLEAN_ENTITY_REVIEW": 1.5,
    "P9_ENTITY_QUALITY_FLAGGED": 1.0,
}
CLASSIFICATION_WEIGHTS: dict[str, float] = {
    "CONCURRENT_OBJECT_COLLISION": 9.0,
    "DURABLE_STATE_CONTINUITY_REVIEW": 8.0,
    "TEMPORAL_ORDER_UNKNOWN_REVIEW": 6.0,
    "SEQUENTIAL_STATE_CHANGE": 3.0,
    "NO_CONFLICT_SAME_OBJECT": 0.25,
    "REVIEW_REQUIRED": 4.0,
}
NEGATIVE_AUTHORITY_FLAGS: dict[str, bool] = {
    "DIAGNOSTIC_REVISION_GUIDANCE_ONLY": True,
    "CHAPTERS_REWRITTEN": False,
    "REPLACEMENT_PROSE_GENERATED": False,
    "GENERATED_PROSE_CREATED": False,
    "REPLACEMENT_PROSE_CREATED": False,
    "CLAIMS_ALTERED": False,
    "TEMPORAL_CLAIMS_ALTERED": False,
    "COSMIC_CLAIMS_ALTERED": False,
    "CLAIMS_PROMOTED": False,
    "CLAIMS_REJECTED": False,
    "CONTRADICTIONS_ALTERED": False,
    "CONTRADICTIONS_RESOLVED": False,
    "CLASSIFICATIONS_ALTERED": False,
    "QUEUES_ALTERED": False,
    "BY_CHAPTER_REVIEW_ALTERED": False,
    "TIMELINE_REGISTRY_ALTERED": False,
    "LEXICON_REGISTRIES_ALTERED": False,
    "CANON_WRITTEN": False,
    "ACCEPTED_LORE_PACKETS_CREATED": False,
    "ZONJ_COMPILED": False,
    "RUNTIME_TOUCHED": False,
    "GODOT_TOUCHED": False,
    "NOTEBOOKLM_EXPORT_PRIMARY_SOURCE": False,
    "DUMPS_PRIMARY_SOURCE": False,
    "AUTHOR_REVISES_MANUALLY": True,
    "ENGINE_AGNOSTIC": True,
    "PRESSURE_SCORE_DIAGNOSTIC_NOT_QUALITY_JUDGMENT": True,
    "HIGH_PRESSURE_NOT_BAD_CHAPTER": True,
    "HIGH_PRESSURE_STATE_CHANGE_HUMAN_REVIEW": True,
}

TITLE_BASED_GUIDANCE_HINTS: tuple[dict[str, str], ...] = (
    {
        "needle": "ummade_army",
        "event_pressure": "unmaking / erased army aftermath",
        "breath_type": "GRIEF_WITHOUT_EVIDENCE",
        "feeling": "The witness should feel the horror of remembering what the world no longer confirms.",
    },
    {
        "needle": "crash_site",
        "event_pressure": "crash investigation / survivor triage / convergence",
        "breath_type": "TRIAGE_SEPARATION",
        "feeling": "The rescuers should process catastrophe before the next discovery overtakes it.",
    },
    {
        "needle": "march",
        "event_pressure": "rescue movement / command uncertainty",
        "breath_type": "COMMAND_DOUBT_PAUSE",
        "feeling": "Mika should have space to reassess what she knows before the next revelation.",
    },
    {
        "needle": "250",
        "event_pressure": "250 retrieval / restored survivors",
        "breath_type": "REINTEGRATION_PAUSE",
        "feeling": "The returned 250 should feel restored but not immediately whole or ready.",
    },
    {
        "needle": "sands_of_time",
        "event_pressure": "temporal mechanics / system learning",
        "breath_type": "DOCTRINE_LAW_PAUSE",
        "feeling": "Geralt should absorb each temporal law before the next mechanic arrives.",
    },
    {
        "needle": "highland_giants",
        "event_pressure": "Highland Giants / reintegration / awe / spire direction",
        "breath_type": "AWE_AND_REINTEGRATION_PAUSE",
        "feeling": "The chapter should distinguish returned warriors, Giant awe, and new responsibility before moving forward.",
    },
    {
        "needle": "luminaire_keeper",
        "event_pressure": "Luminaire keeper setup / responsibility transfer",
        "breath_type": "RESPONSIBILITY_SETTLING_PAUSE",
        "feeling": "The character should feel the weight of being directed toward a larger keeper role.",
    },
)


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


def default_paths(manifest_path: Path | None = None, engain_dir: Path | None = None) -> dict[str, Path]:
    if engain_dir is None:
        engain_dir = _resolve_engain_dir_from_manifest(manifest_path or _default_manifest_path())
    mrlore_dir = engain_dir / "mrlore"
    return {
        "engain_dir": engain_dir,
        "proposed_claims": mrlore_dir / "claims" / "proposed_claims.jsonl",
        "temporal_claims": mrlore_dir / "claims" / "proposed_claims.temporal_enriched.jsonl",
        "cosmic_claims": mrlore_dir / "claims" / "proposed_claims.cosmic_enriched.jsonl",
        "contradiction_candidates": mrlore_dir / "contradictions" / "contradiction_candidates.jsonl",
        "temporal_classifications": mrlore_dir / "contradictions" / "temporal_collision_classifications.jsonl",
        "review_queue": mrlore_dir / "review" / "temporal_aware_quality_review_queue.jsonl",
        "by_chapter_review": mrlore_dir / "review" / "by_chapter" / "temporal_aware_review_by_chapter.json",
        "coming_calendar": mrlore_dir / "timeline" / "coming_calendar.json",
        "predicate_collision_policy": mrlore_dir / "lexicon" / "predicate_collision_policy.json",
        "preserve_entity_allowlist": mrlore_dir / "lexicon" / "preserve_entity_allowlist.json",
        "breathing_jsonl": mrlore_dir / "revision" / "breathing_map.jsonl",
        "breathing_markdown": mrlore_dir / "revision" / "breathing_map.md",
        "manifest": engain_dir / "manifests" / "mrlore_revision_breathing_map_manifest.json",
        "focus_dir": mrlore_dir / "revision" / "focus",
    }


def _read_jsonl(path: Path, noun: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    records: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    try:
        handle = path.open("r", encoding="utf-8")
    except FileNotFoundError:
        return [], [{"path": str(path), "line": None, "error": f"{noun} not found"}]
    with handle:
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


def _read_json_object(path: Path, noun: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}, [{"path": str(path), "line": None, "error": f"{noun} not found"}]
    except json.JSONDecodeError as exc:
        return {}, [{"path": str(path), "line": None, "error": f"invalid {noun} JSON: {exc.msg}"}]
    if not isinstance(data, dict):
        return {}, [{"path": str(path), "line": None, "error": f"{noun} must be a JSON object"}]
    return data, []


def _scene_id_from_claim(claim: dict[str, Any]) -> str:
    for key in ("source_scene_id", "source_scene", "SOURCE_SCENE"):
        value = claim.get(key)
        if value:
            return str(value)
    return ""


def _as_int(value: Any, fallback: int = 0) -> int:
    try:
        if value is None or value == "":
            return fallback
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _chapter_slug(chapter_id: str) -> str:
    return chapter_id.removeprefix("chapter.")


def _book_id_from_chapter(chapter_id: str) -> str:
    match = re.search(r"chapter\.(book\d{3})\.", chapter_id)
    return match.group(1) if match else "book_unknown"


def _chapter_number_from_chapter(chapter_id: str) -> int:
    match = re.search(r"chapter\.book\d{3}\.(\d+)", chapter_id)
    return _as_int(match.group(1)) if match else 0


def _stable_id(prefix: str, *parts: Any) -> str:
    raw = "|".join(str(part) for part in parts)
    return f"{prefix}.{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:24]}"


def _sorted_counter(counter: Counter[str]) -> dict[str, int]:
    return {key: counter[key] for key in sorted(counter)}


def _append_unique(items: list[str], item: str) -> None:
    if item not in items:
        items.append(item)


def _title_guidance_hint(chapter_id: str) -> dict[str, str] | None:
    for hint in TITLE_BASED_GUIDANCE_HINTS:
        if hint["needle"] in chapter_id:
            return hint
    return None


def _chapter_display(record: dict[str, Any]) -> str:
    return f"CH{_as_int(record.get('chapter_number')):03d} — {record.get('chapter_slug')}"


def _chapter_from_scene(scene_id: str) -> str:
    if not scene_id.startswith("scene."):
        return ""
    parts = scene_id.split(".")
    if len(parts) < 3:
        return ""
    return f"chapter.{parts[1]}.{parts[2]}"


def _build_scene_chapter_map(claims: list[dict[str, Any]], by_chapter_review: dict[str, Any]) -> dict[str, dict[str, Any]]:
    scene_map: dict[str, dict[str, Any]] = {}
    for claim in claims:
        scene_id = _scene_id_from_claim(claim)
        chapter_id = str(claim.get("chapter_id") or "")
        if scene_id and chapter_id:
            scene_map.setdefault(
                scene_id,
                {
                    "chapter_id": chapter_id,
                    "chapter_sequence_index": _as_int(claim.get("chapter_sequence_index")),
                    "global_scene_sequence_index": _as_int(claim.get("global_scene_sequence_index")),
                    "scene_index": _as_int(claim.get("scene_index")),
                },
            )
    chapters = by_chapter_review.get("chapters", [])
    if isinstance(chapters, list):
        for chapter in chapters:
            if not isinstance(chapter, dict):
                continue
            chapter_id = str(chapter.get("chapter_id") or "")
            chapter_sequence_index = _as_int(chapter.get("chapter_sequence_index"))
            scenes = chapter.get("scenes", [])
            if not isinstance(scenes, list):
                continue
            for scene in scenes:
                if not isinstance(scene, dict):
                    continue
                scene_id = str(scene.get("source_scene_id") or "")
                if not scene_id:
                    continue
                scene_map.setdefault(
                    scene_id,
                    {
                        "chapter_id": chapter_id,
                        "chapter_sequence_index": chapter_sequence_index,
                        "global_scene_sequence_index": _as_int(scene.get("global_scene_sequence_index")),
                        "scene_index": _as_int(scene.get("scene_index")),
                    },
                )
    return scene_map


def _ensure_chapter(chapters: dict[str, dict[str, Any]], chapter_id: str, chapter_sequence_index: int = 0) -> dict[str, Any]:
    if not chapter_id:
        chapter_id = "chapter.unresolved"
    existing = chapters.get(chapter_id)
    if existing is not None:
        if chapter_sequence_index and not existing.get("chapter_sequence_index"):
            existing["chapter_sequence_index"] = chapter_sequence_index
        return existing
    record: dict[str, Any] = {
        "chapter_id": chapter_id,
        "chapter_sequence_index": chapter_sequence_index,
        "claim_counts": Counter(),
        "scene_ids": set(),
        "subjects": Counter(),
        "predicates": Counter(),
        "coming_ids": Counter(),
        "regions": Counter(),
        "review_bucket_counts": Counter(),
        "classification_counts": Counter(),
        "queue_items": 0,
        "candidate_items": 0,
        "source_queue_ids": set(),
        "source_candidate_ids": set(),
    }
    chapters[chapter_id] = record
    return record


def _index_claim_pressure(
    chapters: dict[str, dict[str, Any]],
    claims: list[dict[str, Any]],
    lane: str,
    *,
    collect_metadata: bool = False,
) -> None:
    for claim in claims:
        chapter_id = str(claim.get("chapter_id") or "") or _chapter_from_scene(_scene_id_from_claim(claim))
        chapter = _ensure_chapter(chapters, chapter_id, _as_int(claim.get("chapter_sequence_index")))
        chapter["claim_counts"][lane] += 1
        scene_id = _scene_id_from_claim(claim)
        if scene_id:
            chapter["scene_ids"].add(scene_id)
        if not collect_metadata:
            continue
        subject = str(claim.get("subject") or "")
        predicate = str(claim.get("predicate") or "")
        if subject:
            chapter["subjects"][subject] += 1
        if predicate:
            chapter["predicates"][predicate] += 1
        coming_id = str(claim.get("coming_id") or "")
        region = str(claim.get("region") or "")
        if coming_id:
            chapter["coming_ids"][coming_id] += 1
        if region:
            chapter["regions"][region] += 1


def _source_scenes(record: dict[str, Any]) -> list[str]:
    scenes = record.get("source_scenes")
    if isinstance(scenes, list):
        return [str(scene) for scene in scenes if scene]
    scene = record.get("source_scene_id") or record.get("source_scene") or record.get("SOURCE_SCENE")
    return [str(scene)] if scene else []


def _chapter_ids_for_record(record: dict[str, Any], scene_map: dict[str, dict[str, Any]]) -> list[tuple[str, int]]:
    chapter_id = str(record.get("chapter_id") or "")
    if chapter_id:
        return [(chapter_id, _as_int(record.get("chapter_sequence_index")))]
    resolved: dict[str, int] = {}
    for scene_id in _source_scenes(record):
        metadata = scene_map.get(scene_id, {})
        cid = str(metadata.get("chapter_id") or "") or _chapter_from_scene(scene_id)
        if cid:
            resolved[cid] = _as_int(metadata.get("chapter_sequence_index"))
    return sorted(resolved.items(), key=lambda item: (item[1] or 999999, item[0]))


def _index_review_queue(chapters: dict[str, dict[str, Any]], queue_items: list[dict[str, Any]], scene_map: dict[str, dict[str, Any]]) -> None:
    for item in queue_items:
        bucket = str(item.get("priority_bucket") or "UNBUCKETED")
        queue_id = str(item.get("queue_id") or "")
        for chapter_id, chapter_sequence_index in _chapter_ids_for_record(item, scene_map):
            chapter = _ensure_chapter(chapters, chapter_id, chapter_sequence_index)
            chapter["queue_items"] += 1
            chapter["review_bucket_counts"][bucket] += 1
            if queue_id:
                chapter["source_queue_ids"].add(queue_id)


def _index_classifications(
    chapters: dict[str, dict[str, Any]], classifications: list[dict[str, Any]], scene_map: dict[str, dict[str, Any]]
) -> None:
    for item in classifications:
        classification = str(item.get("classification") or "REVIEW_REQUIRED")
        candidate_id = str(item.get("candidate_id") or "")
        for chapter_id, chapter_sequence_index in _chapter_ids_for_record(item, scene_map):
            chapter = _ensure_chapter(chapters, chapter_id, chapter_sequence_index)
            chapter["classification_counts"][classification] += 1
            chapter["candidate_items"] += 1
            if candidate_id:
                chapter["source_candidate_ids"].add(candidate_id)


def _index_by_chapter_review(chapters: dict[str, dict[str, Any]], by_chapter_review: dict[str, Any]) -> None:
    raw_chapters = by_chapter_review.get("chapters", [])
    if not isinstance(raw_chapters, list):
        return
    for raw_chapter in raw_chapters:
        if not isinstance(raw_chapter, dict):
            continue
        chapter_id = str(raw_chapter.get("chapter_id") or "")
        chapter = _ensure_chapter(chapters, chapter_id, _as_int(raw_chapter.get("chapter_sequence_index")))
        for scene in raw_chapter.get("scenes", []) if isinstance(raw_chapter.get("scenes"), list) else []:
            if not isinstance(scene, dict):
                continue
            scene_id = str(scene.get("source_scene_id") or "")
            if scene_id:
                chapter["scene_ids"].add(scene_id)


def _pressure_score(chapter: dict[str, Any]) -> float:
    proposed_claims = chapter["claim_counts"].get("proposed", 0)
    temporal_claims = chapter["claim_counts"].get("temporal", 0)
    cosmic_claims = chapter["claim_counts"].get("cosmic", 0)
    claim_signal = max(proposed_claims, temporal_claims, cosmic_claims)
    scene_count = max(len(chapter["scene_ids"]), 1)
    density_score = (claim_signal / scene_count) * 0.08
    bucket_score = sum(BUCKET_WEIGHTS.get(bucket, 2.0) * count for bucket, count in chapter["review_bucket_counts"].items())
    classification_score = sum(
        CLASSIFICATION_WEIGHTS.get(classification, 4.0) * count
        for classification, count in chapter["classification_counts"].items()
    )
    context_score = 4.0 * len(chapter["coming_ids"]) + 1.5 * len(chapter["regions"])
    return round(density_score + bucket_score + classification_score + context_score, 3)


def _pressure_tier(score: float) -> str:
    if score >= 400:
        return "VERY_HIGH_BREATHING_PRESSURE"
    if score >= 160:
        return "HIGH_BREATHING_PRESSURE"
    if score >= 60:
        return "MODERATE_BREATHING_PRESSURE"
    return "LOW_BREATHING_PRESSURE"


def _guidance(chapter: dict[str, Any], score: float, tier: str) -> list[str]:
    guidance: list[str] = []
    buckets: Counter[str] = chapter["review_bucket_counts"]
    classifications: Counter[str] = chapter["classification_counts"]
    scene_count = max(len(chapter["scene_ids"]), 1)
    claim_signal = max(chapter["claim_counts"].values() or [0])
    claims_per_scene = claim_signal / scene_count
    if tier in {"VERY_HIGH_BREATHING_PRESSURE", "HIGH_BREATHING_PRESSURE"}:
        guidance.append("Slow the chapter revision pass here; this chapter carries unusually high event/review pressure.")
    if claims_per_scene >= 90:
        guidance.append("Check whether dense scene facts need more prose breathing room, transitions, or chapter-level pacing breaks.")
    elif claims_per_scene >= 45:
        guidance.append("Review scene transitions for readability; claim density is elevated but not automatically wrong.")
    if buckets.get("P0_CONCURRENT_CONFLICT", 0) or classifications.get("CONCURRENT_OBJECT_COLLISION", 0):
        guidance.append("Inspect concurrent-object pressure manually; do not auto-resolve contradictions from this map.")
    if buckets.get("P1_DURABLE_STATE_CONTINUITY_REVIEW", 0) or classifications.get("DURABLE_STATE_CONTINUITY_REVIEW", 0):
        guidance.append("Re-read durable-state continuity beats before revising surrounding passages.")
    if buckets.get("P2_TEMPORAL_ORDER_UNKNOWN", 0) or classifications.get("TEMPORAL_ORDER_UNKNOWN_REVIEW", 0):
        guidance.append("Clarify chronology cues if the manuscript intends a specific order.")
    if buckets.get("P3_SEQUENTIAL_STATE_CHANGE", 0) >= 20 or classifications.get("SEQUENTIAL_STATE_CHANGE", 0) >= 20:
        guidance.append("Sequential movement/state-change pressure is high; verify the motion reads as intentional progression.")
    if chapter["coming_ids"]:
        guidance.append("Cosmic/Coming context is present; preserve the event-scale rhythm while revising manually.")
    if buckets.get("P9_ENTITY_QUALITY_FLAGGED", 0):
        guidance.append("Some pressure may be extraction noise; separate lexical cleanup from story revision.")
    if not guidance:
        guidance.append("No heavy breathing intervention indicated; normal manual revision pass is sufficient.")
    guidance.append("Pressure score is diagnostic, not a quality judgment; high pressure does not mean bad chapter.")
    guidance.append("High pressure means the chapter carries many state changes and may need human breathing review.")
    guidance.append("Do not rewrite from this diagnostic directly; author revises manually after reading the map.")
    return guidance


def _pressure_percentile_global(rank: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round(((total - rank) / total) * 100.0, 2)


def _pressure_percentile_within_book(rank: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round(((total - rank + 1) / total) * 100.0, 2)


def _pressure_tier_within_book(rank: int, total: int) -> str:
    percentile = _pressure_percentile_within_book(rank, total)
    if rank == 1 or percentile >= 90.0:
        return "BOOK_EXTREME_PRESSURE"
    if percentile >= 75.0:
        return "BOOK_HIGH_PRESSURE"
    if percentile >= 50.0:
        return "BOOK_ELEVATED_PRESSURE"
    return "BOOK_BASELINE_PRESSURE"


def _primary_pressure_source(record: dict[str, Any]) -> str:
    claim_density = float(record["claim_density"].get("claims_per_scene", 0.0))
    classification_counts = record["contradiction_pressure"].get("classification_counts", {})
    review_counts = record["review_pressure"].get("review_bucket_counts", {})
    collision_load = sum(
        int(classification_counts.get(key, 0))
        for key in ("CONCURRENT_OBJECT_COLLISION", "DURABLE_STATE_CONTINUITY_REVIEW", "TEMPORAL_ORDER_UNKNOWN_REVIEW", "SEQUENTIAL_STATE_CHANGE")
    )
    high_review_load = sum(int(review_counts.get(key, 0)) for key in ("P0_CONCURRENT_CONFLICT", "P1_DURABLE_STATE_CONTINUITY_REVIEW", "P2_TEMPORAL_ORDER_UNKNOWN", "P3_SEQUENTIAL_STATE_CHANGE"))
    if claim_density >= 45.0 and (collision_load >= 20 or high_review_load >= 20):
        return "CLAIM_DENSITY_AND_TEMPORAL_COLLISION_LOAD"
    if collision_load >= high_review_load and collision_load > 0:
        return "TEMPORAL_COLLISION_LOAD"
    if high_review_load > 0:
        return "REVIEW_QUEUE_PRESSURE"
    if claim_density > 0:
        return "CLAIM_DENSITY"
    return "LOW_PRESSURE_BASELINE"


def _diagnostic_confidence(record: dict[str, Any], read_errors_count: int = 0) -> str:
    if read_errors_count:
        return "LOW"
    has_claims = record["claim_density"].get("cosmic_enriched_claims", 0) or record["claim_density"].get("temporal_enriched_claims", 0)
    has_review = bool(record["review_pressure"].get("review_bucket_counts"))
    has_classification = bool(record["contradiction_pressure"].get("classification_counts"))
    if has_claims and has_review and has_classification:
        return "HIGH"
    if has_claims and (has_review or has_classification):
        return "MEDIUM"
    return "LOW"


def _apply_pressure_rankings(records: list[dict[str, Any]], read_errors_count: int = 0) -> None:
    ordered = sorted(records, key=lambda item: (-float(item["event_pressure_score"]), _as_int(item["chapter_sequence_index"]), item["chapter_id"]))
    total = len(ordered)
    for rank, record in enumerate(ordered, 1):
        score = float(record["event_pressure_score"])
        record["pressure_score"] = score
        record["pressure_rank_global"] = rank
        record["pressure_percentile_global"] = _pressure_percentile_global(rank, total)
        record["pressure_tier_global"] = record["event_pressure_tier"]
        record["diagnostic_confidence"] = _diagnostic_confidence(record, read_errors_count)
        record["primary_pressure_source"] = _primary_pressure_source(record)
    by_book: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        record["book_id"] = _book_id_from_chapter(str(record["chapter_id"]))
        record["chapter_number"] = _chapter_number_from_chapter(str(record["chapter_id"]))
        by_book[record["book_id"]].append(record)
    for book_records in by_book.values():
        book_ordered = sorted(book_records, key=lambda item: (-float(item["pressure_score"]), _as_int(item["chapter_sequence_index"]), item["chapter_id"]))
        total_in_book = len(book_ordered)
        for rank, record in enumerate(book_ordered, 1):
            record["pressure_rank_within_book"] = rank
            record["pressure_percentile_within_book"] = _pressure_percentile_within_book(rank, total_in_book)
            record["pressure_tier_within_book"] = _pressure_tier_within_book(rank, total_in_book)


def _detected_event_pressure(chapter: dict[str, Any]) -> list[str]:
    pressures: list[str] = []
    buckets: Counter[str] = chapter["review_bucket_counts"]
    classifications: Counter[str] = chapter["classification_counts"]
    claim_signal = max(chapter["claim_counts"].values() or [0])
    scene_count = max(len(chapter["scene_ids"]), 1)
    claims_per_scene = claim_signal / scene_count
    if claims_per_scene >= 45.0:
        _append_unique(pressures, "HIGH_CLAIM_DENSITY")
    if claims_per_scene >= 125.0:
        _append_unique(pressures, "EXTREME_SCENE_COMPRESSION")
    if buckets.get("P0_CONCURRENT_CONFLICT", 0) or classifications.get("CONCURRENT_OBJECT_COLLISION", 0):
        _append_unique(pressures, "CONCURRENT_COLLISION_REVIEW_PRESSURE")
    if buckets.get("P1_DURABLE_STATE_CONTINUITY_REVIEW", 0) or classifications.get("DURABLE_STATE_CONTINUITY_REVIEW", 0):
        _append_unique(pressures, "DURABLE_STATE_CONTINUITY_PRESSURE")
    if buckets.get("P2_TEMPORAL_ORDER_UNKNOWN", 0) or classifications.get("TEMPORAL_ORDER_UNKNOWN_REVIEW", 0):
        _append_unique(pressures, "TEMPORAL_ORDER_AMBIGUITY_PRESSURE")
    if buckets.get("P3_SEQUENTIAL_STATE_CHANGE", 0) >= 20 or classifications.get("SEQUENTIAL_STATE_CHANGE", 0) >= 20:
        _append_unique(pressures, "SEQUENTIAL_STATE_CHANGE_LOAD")
    if buckets.get("P4_ENVIRONMENT_REVIEW", 0):
        _append_unique(pressures, "ENVIRONMENT_REACTION_PRESSURE")
    if chapter["coming_ids"]:
        _append_unique(pressures, "COSMIC_EVENT_CONTEXT_LOAD")
    if buckets.get("P9_ENTITY_QUALITY_FLAGGED", 0):
        _append_unique(pressures, "LEXICAL_EXTRACTION_NOISE_PRESSURE")
    hint = _title_guidance_hint(str(chapter.get("chapter_id", "")))
    if hint:
        _append_unique(pressures, hint["event_pressure"])
    if not pressures:
        pressures.append("BASELINE_REVISION_PRESSURE")
    return pressures


def _missing_breath_type(chapter: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    pressures = set(_detected_event_pressure(chapter))
    buckets: Counter[str] = chapter["review_bucket_counts"]
    classifications: Counter[str] = chapter["classification_counts"]
    if "HIGH_CLAIM_DENSITY" in pressures:
        _append_unique(missing, "TRANSITION_BREATH")
    if "EXTREME_SCENE_COMPRESSION" in pressures:
        _append_unique(missing, "SCENE_COMPRESSION_PAUSE")
    if "SEQUENTIAL_STATE_CHANGE_LOAD" in pressures:
        _append_unique(missing, "MOTION_AND_CAUSALITY_BREATH")
        _append_unique(missing, "TRANSITION_BREATH")
    if "CONCURRENT_COLLISION_REVIEW_PRESSURE" in pressures or "DURABLE_STATE_CONTINUITY_PRESSURE" in pressures:
        _append_unique(missing, "CONTINUITY_CHECK_BREATH")
    if "TEMPORAL_ORDER_AMBIGUITY_PRESSURE" in pressures:
        _append_unique(missing, "CHRONOLOGY_CLARITY_BREATH")
    if "ENVIRONMENT_REACTION_PRESSURE" in pressures:
        _append_unique(missing, "WORLD_REACTION_PAUSE")
    if "COSMIC_EVENT_CONTEXT_LOAD" in pressures:
        _append_unique(missing, "COSMIC_SCALE_INTEGRATION_BREATH")
    if "LEXICAL_EXTRACTION_NOISE_PRESSURE" in pressures:
        _append_unique(missing, "LEXICAL_REVIEW_BREATH")
    if buckets.get("P9_ENTITY_QUALITY_FLAGGED", 0) >= 20 or classifications.get("P9_ENTITY_QUALITY_FLAGGED", 0) >= 20:
        _append_unique(missing, "LEXICAL_NOISE_REVIEW")
    hint = _title_guidance_hint(str(chapter.get("chapter_id", "")))
    if hint:
        _append_unique(missing, hint["breath_type"])
    if not missing:
        missing.append("NORMAL_REVISION_BREATH")
    return missing


def _expected_internal_feeling(chapter: dict[str, Any]) -> str:
    hint = _title_guidance_hint(str(chapter.get("chapter_id", "")))
    if hint:
        return hint["feeling"]
    pressures = set(_detected_event_pressure(chapter))
    if "COSMIC_EVENT_CONTEXT_LOAD" in pressures and "SEQUENTIAL_STATE_CHANGE_LOAD" in pressures:
        return "Reader should feel large-scale events moving through character and scene experience, not just fact accumulation."
    if "CONCURRENT_COLLISION_REVIEW_PRESSURE" in pressures or "DURABLE_STATE_CONTINUITY_PRESSURE" in pressures:
        return "Reader should feel continuity as intentional and trackable while the author verifies canon order manually."
    if "HIGH_CLAIM_DENSITY" in pressures:
        return "Reader should have enough internal/emotional or transitional space to absorb the event load."
    return "Reader should experience normal scene continuity without forced diagnostic interpretation."


def _revision_guidance_items(chapter: dict[str, Any], score: float, tier: str) -> list[str]:
    guidance = list(_guidance(chapter, score, tier))
    buckets: Counter[str] = chapter["review_bucket_counts"]
    classifications: Counter[str] = chapter["classification_counts"]
    claim_signal = max(chapter["claim_counts"].values() or [0])
    scene_count = max(len(chapter["scene_ids"]), 1)
    claims_per_scene = claim_signal / scene_count
    if claims_per_scene >= 125.0:
        _append_unique(
            guidance,
            "Consider splitting or pausing inside the chapter because many state changes are concentrated into very few scene containers.",
        )
    if buckets.get("P3_SEQUENTIAL_STATE_CHANGE", 0) >= 20 or classifications.get("SEQUENTIAL_STATE_CHANGE", 0) >= 20:
        _append_unique(
            guidance,
            "Verify that each movement/state change has an observable transition before the next event begins.",
        )
    if buckets.get("P4_ENVIRONMENT_REVIEW", 0):
        _append_unique(guidance, "Let the environment react or settle before the next major event.")
    if buckets.get("P9_ENTITY_QUALITY_FLAGGED", 0) >= 20:
        _append_unique(guidance, "Separate extraction-noise cleanup from actual prose revision.")
    return guidance


def _revision_guidance_text(chapter: dict[str, Any], score: float, tier: str) -> str:
    return " ".join(_revision_guidance_items(chapter, score, tier))


def _do_not_change_list() -> list[str]:
    return [
        "Do not rewrite prose from this diagnostic.",
        "Do not reorder canon events automatically.",
        "Do not promote or reject claims.",
        "Do not resolve contradictions automatically.",
        "Do not create accepted lore packets.",
        "Do not compile ZONJ or touch runtime/Godot.",
    ]


def _top_counter(counter: Counter[str], limit: int = 10) -> list[dict[str, Any]]:
    return [
        {"value": value, "count": count}
        for value, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))[:limit]
    ]


def _build_records(chapters: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    ordered = sorted(
        chapters.values(),
        key=lambda chapter: (_as_int(chapter.get("chapter_sequence_index"), 999999) or 999999, str(chapter.get("chapter_id"))),
    )
    for chapter in ordered:
        score = _pressure_score(chapter)
        tier = _pressure_tier(score)
        scene_count = len(chapter["scene_ids"])
        claim_signal = max(chapter["claim_counts"].values() or [0])
        record = {
            "contract": CONTRACT,
            "revision_id": _stable_id("breathing_revision", chapter["chapter_id"], chapter.get("chapter_sequence_index"), score),
            "chapter_id": chapter["chapter_id"],
            "chapter_sequence_index": chapter.get("chapter_sequence_index", 0),
            "chapter_slug": _chapter_slug(chapter["chapter_id"]),
            "revision_scope": REVISION_SCOPE,
            "authority_effect": "NONE",
            "claim_density": {
                "proposed_claims": chapter["claim_counts"].get("proposed", 0),
                "temporal_enriched_claims": chapter["claim_counts"].get("temporal", 0),
                "cosmic_enriched_claims": chapter["claim_counts"].get("cosmic", 0),
                "scene_count": scene_count,
                "claims_per_scene": round(claim_signal / max(scene_count, 1), 3),
                "top_predicates": _top_counter(chapter["predicates"], 8),
                "top_subjects": _top_counter(chapter["subjects"], 8),
            },
            "temporal_cosmic_context": {
                "coming_ids": _sorted_counter(chapter["coming_ids"]),
                "regions": _sorted_counter(chapter["regions"]),
            },
            "contradiction_pressure": {
                "candidate_items_seen": chapter["candidate_items"],
                "classification_counts": _sorted_counter(chapter["classification_counts"]),
                "source_candidate_ids_sample": sorted(chapter["source_candidate_ids"])[:25],
            },
            "review_pressure": {
                "queue_items_seen": chapter["queue_items"],
                "review_bucket_counts": _sorted_counter(chapter["review_bucket_counts"]),
                "source_queue_ids_sample": sorted(chapter["source_queue_ids"])[:25],
            },
            "event_pressure_score": score,
            "event_pressure_tier": tier,
            "detected_event_pressure": _detected_event_pressure(chapter),
            "missing_breath_type": _missing_breath_type(chapter),
            "expected_internal_feeling": _expected_internal_feeling(chapter),
            "revision_guidance": _revision_guidance_text(chapter, score, tier),
            "do_not_change": _do_not_change_list(),
            "author_action_required": True,
            "breathing_guidance": _guidance(chapter, score, tier),
            "source_scene_ids_sample": sorted(chapter["scene_ids"])[:25],
            **NEGATIVE_AUTHORITY_FLAGS,
        }
        records.append(record)
    return records


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )


def _records_by_pressure(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(records, key=lambda item: (_as_int(item.get("pressure_rank_global"), 999999), _as_int(item.get("chapter_sequence_index")), item.get("chapter_id", "")))


def _records_by_chapter(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(records, key=lambda item: (_as_int(item.get("chapter_sequence_index"), 999999), item.get("chapter_id", "")))


def _format_target_line(record: dict[str, Any]) -> str:
    return (
        f"- #{_as_int(record.get('pressure_rank_global'))} global / "
        f"#{_as_int(record.get('pressure_rank_within_book'))} in {record.get('book_id')} — "
        f"{_chapter_display(record)} — "
        f"score {record.get('pressure_score')} — "
        f"{record.get('pressure_tier_global')} / {record.get('pressure_tier_within_book')} — "
        f"{record.get('primary_pressure_source')}"
    )


def _focus_records(
    records: list[dict[str, Any]],
    chapter_start: int | None = None,
    chapter_end: int | None = None,
    book_id: str | None = None,
) -> list[dict[str, Any]]:
    focused: list[dict[str, Any]] = []
    normalized_book = book_id.strip() if book_id else None
    for record in records:
        chapter_number = _as_int(record.get("chapter_number"))
        if normalized_book and record.get("book_id") != normalized_book:
            continue
        if chapter_start is not None and chapter_number < chapter_start:
            continue
        if chapter_end is not None and chapter_number > chapter_end:
            continue
        focused.append(record)
    return _records_by_chapter(focused)


def _append_markdown_list(lines: list[str], values: Any) -> None:
    if isinstance(values, list) and values:
        for value in values:
            lines.append(f"- {value}")
    else:
        lines.append("- none")


def _append_record_detail(lines: list[str], record: dict[str, Any], heading_level: str = "##") -> None:
    lines.extend(
        [
            f"{heading_level} {record['pressure_tier_global']} / {record['pressure_tier_within_book']} — {_chapter_display(record)}",
            "",
            "Pressure:",
            f"- Score: {record['pressure_score']}",
            f"- Global rank/percentile: {record['pressure_rank_global']} / {record['pressure_percentile_global']}",
            f"- Within-book rank/percentile: {record['pressure_rank_within_book']} / {record['pressure_percentile_within_book']}",
            f"- Claims: proposed={record['claim_density']['proposed_claims']}, temporal={record['claim_density']['temporal_enriched_claims']}, cosmic={record['claim_density']['cosmic_enriched_claims']}",
            f"- Scenes: {record['claim_density']['scene_count']}",
            f"- Claims/scene: {record['claim_density']['claims_per_scene']}",
            f"- Primary pressure source: {record['primary_pressure_source']}",
            f"- Diagnostic confidence: {record['diagnostic_confidence']}",
            f"- Review buckets: `{json.dumps(record['review_pressure']['review_bucket_counts'], sort_keys=True)}`",
            f"- Classifications: `{json.dumps(record['contradiction_pressure']['classification_counts'], sort_keys=True)}`",
            f"- Coming context: `{json.dumps(record['temporal_cosmic_context']['coming_ids'], sort_keys=True)}`",
            "",
            "Detected event pressure:",
        ]
    )
    _append_markdown_list(lines, record.get("detected_event_pressure"))
    lines.extend(["", "Missing breath type:"])
    _append_markdown_list(lines, record.get("missing_breath_type"))
    lines.extend(["", "Expected internal feeling:", str(record.get("expected_internal_feeling", "")), "", "Revision guidance:"])
    lines.append(str(record.get("revision_guidance", "")))
    lines.extend(["", "Do not change:"])
    _append_markdown_list(lines, record.get("do_not_change"))
    lines.extend(
        [
            "",
            "Author action required:",
            "true" if record.get("author_action_required") is True else "false",
            "",
            "Safety:",
            "- Pressure score is diagnostic, not a quality judgment.",
            "- Do not rewrite from this diagnostic directly.",
            "- Author revises manually.",
            "",
        ]
    )


def _write_focus_markdown(
    path: Path,
    records: list[dict[str, Any]],
    title: str,
    chapter_start: int | None = None,
    chapter_end: int | None = None,
    book_id: str | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# {title}",
        "",
        "Non-authoring focused view from the full MrLore Revision Breathing Map.",
        "Pressure score is diagnostic, not a quality judgment. High pressure does not mean bad chapter.",
        "",
        f"- Chapter start: {chapter_start if chapter_start is not None else 'ANY'}",
        f"- Chapter end: {chapter_end if chapter_end is not None else 'ANY'}",
        f"- Book id: {book_id or 'ANY'}",
        f"- Focus records: {len(records)}",
        "",
    ]
    if not records:
        lines.append("No chapters matched this focus filter.")
    for record in records:
        _append_record_detail(lines, record, "##")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _write_markdown(path: Path, records: list[dict[str, Any]], manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    by_pressure = _records_by_pressure(records)
    by_book: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in by_pressure:
        by_book[str(record.get("book_id", "book_unknown"))].append(record)
    arc_records = _focus_records(records, 30, 38)
    lines = [
        "# MrLore Revision Breathing Map",
        "",
        "Non-authoring diagnostic. This map guides manual author revision only.",
        "",
        "## Locks",
        "",
        "- Reads the live `.engain/mrlore` output body, not only repo-side project files.",
        "- Does not rewrite chapters or generate replacement prose.",
        "- Does not promote/reject claims, resolve contradictions, write canon, create accepted lore packets, compile ZONJ, or touch Godot/runtime.",
        "- Pressure score is diagnostic, not a quality judgment.",
        "- High pressure does not mean bad chapter.",
        "- High pressure means the chapter carries many state changes and may need human breathing review.",
        "- Author revises manually after reading the map.",
        "",
        "## Summary",
        "",
        f"- Chapters mapped: {manifest['CHAPTERS_WRITTEN']}",
        f"- Records written: {manifest['BREATHING_RECORDS_WRITTEN']}",
        f"- Highest pressure score: {manifest['highest_event_pressure_score']}",
        "",
        "# Top Revision Breathing Targets",
        "",
        "## Global Top 20",
        "",
    ]
    for record in by_pressure[:20]:
        lines.append(_format_target_line(record))
    lines.extend(["", "## Top 5 Per Book", ""])
    for book in sorted(by_book):
        lines.append(f"### {book}")
        for record in by_book[book][:5]:
            lines.append(_format_target_line(record))
        lines.append("")
    lines.extend(["## CH30–CH38 Arc Focus", ""])
    if not arc_records:
        lines.append("No chapters found in CH30–CH38.")
    else:
        for record in arc_records:
            lines.append(_format_target_line(record))
    lines.extend(["", "# Full Chapter Breathing Map", ""])
    for record in by_pressure:
        _append_record_detail(lines, record, "##")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _focus_filename(chapter_start: int | None = None, chapter_end: int | None = None, book_id: str | None = None) -> str:
    parts: list[str] = []
    if book_id:
        parts.append(book_id)
    if chapter_start is not None or chapter_end is not None:
        start = chapter_start if chapter_start is not None else "any"
        end = chapter_end if chapter_end is not None else "any"
        parts.append(f"ch{start}_ch{end}")
    if not parts:
        parts.append("focus")
    return "_".join(parts) + "_breathing_map.md"


def run_revision_breathing_map(
    proposed_claims_path: Path | str,
    temporal_claims_path: Path | str,
    cosmic_claims_path: Path | str,
    contradiction_candidates_path: Path | str,
    temporal_classifications_path: Path | str,
    review_queue_path: Path | str,
    by_chapter_review_path: Path | str,
    coming_calendar_path: Path | str,
    predicate_collision_policy_path: Path | str,
    preserve_entity_allowlist_path: Path | str,
    output_jsonl_path: Path | str,
    output_markdown_path: Path | str,
    manifest_path: Path | str,
    focus_dir_path: Path | str | None = None,
    chapter_start: int | None = None,
    chapter_end: int | None = None,
    book_id: str | None = None,
) -> dict[str, Any]:
    proposed_claims_file = Path(proposed_claims_path).resolve()
    temporal_claims_file = Path(temporal_claims_path).resolve()
    cosmic_claims_file = Path(cosmic_claims_path).resolve()
    contradiction_candidates_file = Path(contradiction_candidates_path).resolve()
    temporal_classifications_file = Path(temporal_classifications_path).resolve()
    review_queue_file = Path(review_queue_path).resolve()
    by_chapter_review_file = Path(by_chapter_review_path).resolve()
    coming_calendar_file = Path(coming_calendar_path).resolve()
    predicate_collision_policy_file = Path(predicate_collision_policy_path).resolve()
    preserve_entity_allowlist_file = Path(preserve_entity_allowlist_path).resolve()
    output_jsonl_file = Path(output_jsonl_path).resolve()
    output_markdown_file = Path(output_markdown_path).resolve()
    manifest_file = Path(manifest_path).resolve()
    focus_dir = Path(focus_dir_path).resolve() if focus_dir_path is not None else output_markdown_file.parent / "focus"

    proposed_claims, proposed_errors = _read_jsonl(proposed_claims_file, "proposed claim")
    temporal_claims, temporal_errors = _read_jsonl(temporal_claims_file, "temporal-enriched claim")
    cosmic_claims, cosmic_errors = _read_jsonl(cosmic_claims_file, "cosmic-enriched claim")
    contradiction_candidates, candidate_errors = _read_jsonl(contradiction_candidates_file, "contradiction candidate")
    temporal_classifications, classification_errors = _read_jsonl(temporal_classifications_file, "temporal collision classification")
    review_queue, queue_errors = _read_jsonl(review_queue_file, "temporal-aware review queue item")
    by_chapter_review, by_chapter_errors = _read_json_object(by_chapter_review_file, "temporal-aware review by-chapter view")
    coming_calendar, coming_errors = _read_json_object(coming_calendar_file, "Coming calendar")
    predicate_policy, predicate_policy_errors = _read_json_object(predicate_collision_policy_file, "predicate collision policy")
    preserve_allowlist, preserve_allowlist_errors = _read_json_object(preserve_entity_allowlist_file, "preserve entity allowlist")

    read_errors = (
        proposed_errors
        + temporal_errors
        + cosmic_errors
        + candidate_errors
        + classification_errors
        + queue_errors
        + by_chapter_errors
        + coming_errors
        + predicate_policy_errors
        + preserve_allowlist_errors
    )

    chapters: dict[str, dict[str, Any]] = {}
    scene_map = _build_scene_chapter_map(temporal_claims or cosmic_claims or proposed_claims, by_chapter_review)
    _index_claim_pressure(chapters, proposed_claims, "proposed", collect_metadata=not temporal_claims and not cosmic_claims)
    _index_claim_pressure(chapters, temporal_claims, "temporal", collect_metadata=bool(temporal_claims and not cosmic_claims))
    _index_claim_pressure(chapters, cosmic_claims, "cosmic", collect_metadata=bool(cosmic_claims))
    _index_by_chapter_review(chapters, by_chapter_review)
    _index_review_queue(chapters, review_queue, scene_map)
    _index_classifications(chapters, temporal_classifications, scene_map)

    records = _build_records(chapters)
    _apply_pressure_rankings(records, len(read_errors))
    _write_jsonl(output_jsonl_file, records)

    pressure_counts = Counter(record["pressure_tier_global"] for record in records)
    pressure_within_book_counts = Counter(record["pressure_tier_within_book"] for record in records)
    primary_pressure_source_counts = Counter(record["primary_pressure_source"] for record in records)
    highest_score = max((float(record["pressure_score"]) for record in records), default=0.0)
    highest_records = [record for record in records if math.isclose(float(record["pressure_score"]), highest_score)]
    focus_records = _focus_records(records, chapter_start, chapter_end, book_id) if (chapter_start is not None or chapter_end is not None or book_id) else []
    focus_markdown_path = focus_dir / _focus_filename(chapter_start, chapter_end, book_id) if (chapter_start is not None or chapter_end is not None or book_id) else None

    manifest: dict[str, Any] = {
        "contract": MANIFEST_CONTRACT,
        "run_timestamp": datetime.now(timezone.utc).isoformat(),
        "MRLORE_REVISION_BREATHING_MAP_COMPLETE": len(read_errors) == 0,
        "MRLORE_REVISION_BREATHING_MAP_READS_FULL_MRLORE_BODY": True,
        "revision_scope": REVISION_SCOPE,
        "source_proposed_claims": str(proposed_claims_file),
        "source_temporal_enriched_claims": str(temporal_claims_file),
        "source_cosmic_enriched_claims": str(cosmic_claims_file),
        "source_contradiction_candidates": str(contradiction_candidates_file),
        "source_temporal_collision_classifications": str(temporal_classifications_file),
        "source_temporal_aware_quality_review_queue": str(review_queue_file),
        "source_temporal_aware_review_by_chapter": str(by_chapter_review_file),
        "source_coming_calendar": str(coming_calendar_file),
        "source_predicate_collision_policy": str(predicate_collision_policy_file),
        "source_preserve_entity_allowlist": str(preserve_entity_allowlist_file),
        "output_jsonl_path": str(output_jsonl_file),
        "output_markdown_path": str(output_markdown_file),
        "focus_markdown_path": str(focus_markdown_path) if focus_markdown_path else "",
        "manifest_path": str(manifest_file),
        "PROPOSED_CLAIMS_READ": len(proposed_claims),
        "TEMPORAL_ENRICHED_CLAIMS_READ": len(temporal_claims),
        "COSMIC_ENRICHED_CLAIMS_READ": len(cosmic_claims),
        "CONTRADICTION_CANDIDATES_READ": len(contradiction_candidates),
        "TEMPORAL_COLLISION_CLASSIFICATIONS_READ": len(temporal_classifications),
        "TEMPORAL_AWARE_REVIEW_QUEUE_ITEMS_READ": len(review_queue),
        "BY_CHAPTER_REVIEW_CHAPTERS_READ": len(by_chapter_review.get("chapters", [])) if isinstance(by_chapter_review.get("chapters"), list) else 0,
        "COMING_CONTEXTS_LOADED": len(coming_calendar.get("comings", [])) if isinstance(coming_calendar.get("comings"), list) else 0,
        "PREDICATE_CLASSES_LOADED": len(predicate_policy.get("predicate_classes", {})) if isinstance(predicate_policy.get("predicate_classes"), dict) else 0,
        "PRESERVE_ALLOWLIST_TERMS_LOADED": len(preserve_allowlist.get("terms", [])) if isinstance(preserve_allowlist.get("terms"), list) else 0,
        "CHAPTERS_WRITTEN": len(records),
        "BREATHING_RECORDS_WRITTEN": len(records),
        "MRLORE_REVISION_BREATHING_MAP_CALIBRATION_V2": True,
        "MRLORE_REVISION_BREATHING_MAP_AUTHOR_USEFULNESS_V3": True,
        "MARKDOWN_GUIDANCE_FIELDS_WRITTEN": True,
        "CHAPTER_HEADING_DISPLAY_FIXED": True,
        "TITLE_BASED_GUIDANCE_HINTS_WRITTEN": True,
        "PRESSURE_RANKINGS_WRITTEN": True,
        "WITHIN_BOOK_RANKINGS_WRITTEN": True,
        "FOCUS_FILTER_CHAPTER_START": chapter_start,
        "FOCUS_FILTER_CHAPTER_END": chapter_end,
        "FOCUS_FILTER_BOOK_ID": book_id or "",
        "FOCUS_RECORDS_WRITTEN": len(focus_records),
        "pressure_tier_counts": _sorted_counter(pressure_counts),
        "pressure_tier_within_book_counts": _sorted_counter(pressure_within_book_counts),
        "primary_pressure_source_counts": _sorted_counter(primary_pressure_source_counts),
        "highest_event_pressure_score": highest_score,
        "highest_pressure_chapter_ids": [record["chapter_id"] for record in highest_records[:25]],
        "read_errors_count": len(read_errors),
        "read_errors": read_errors[:100],
        "errors": [] if not read_errors else ["one or more input files could not be fully read"],
        "errors_count": 0 if not read_errors else 1,
        **NEGATIVE_AUTHORITY_FLAGS,
    }
    _write_markdown(output_markdown_file, records, manifest)
    if focus_markdown_path is not None:
        title = "MrLore Revision Breathing Map Focus"
        _write_focus_markdown(focus_markdown_path, focus_records, title, chapter_start, chapter_end, book_id)
    manifest_file.parent.mkdir(parents=True, exist_ok=True)
    manifest_file.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Build MrLore revision breathing map from live .engain/mrlore outputs.")
    parser.add_argument("--manifest", default=None, help="Path to engain_manifest.json.")
    parser.add_argument("--engain-dir", default=None, help="Direct path to vault/.engain.")
    parser.add_argument("--proposed-claims", default=None)
    parser.add_argument("--temporal-claims", default=None)
    parser.add_argument("--cosmic-claims", default=None)
    parser.add_argument("--contradiction-candidates", default=None)
    parser.add_argument("--temporal-classifications", default=None)
    parser.add_argument("--review-queue", default=None)
    parser.add_argument("--by-chapter-review", default=None)
    parser.add_argument("--coming-calendar", default=None)
    parser.add_argument("--predicate-collision-policy", default=None)
    parser.add_argument("--preserve-entity-allowlist", default=None)
    parser.add_argument("--output-jsonl", default=None)
    parser.add_argument("--output-markdown", default=None)
    parser.add_argument("--output-manifest", default=None)
    parser.add_argument("--chapter-start", type=int, default=None)
    parser.add_argument("--chapter-end", type=int, default=None)
    parser.add_argument("--book-id", default=None)
    args = parser.parse_args()

    try:
        paths = default_paths(
            Path(args.manifest) if args.manifest else None,
            Path(args.engain_dir) if args.engain_dir else None,
        )
        manifest = run_revision_breathing_map(
            args.proposed_claims or paths["proposed_claims"],
            args.temporal_claims or paths["temporal_claims"],
            args.cosmic_claims or paths["cosmic_claims"],
            args.contradiction_candidates or paths["contradiction_candidates"],
            args.temporal_classifications or paths["temporal_classifications"],
            args.review_queue or paths["review_queue"],
            args.by_chapter_review or paths["by_chapter_review"],
            args.coming_calendar or paths["coming_calendar"],
            args.predicate_collision_policy or paths["predicate_collision_policy"],
            args.preserve_entity_allowlist or paths["preserve_entity_allowlist"],
            args.output_jsonl or paths["breathing_jsonl"],
            args.output_markdown or paths["breathing_markdown"],
            args.output_manifest or paths["manifest"],
            paths["focus_dir"],
            args.chapter_start,
            args.chapter_end,
            args.book_id,
        )
    except Exception as exc:  # pragma: no cover - CLI guardrail
        print(f"MRLORE_REVISION_BREATHING_MAP_ERROR: {exc}")
        return 1
    print(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True))
    return 0 if manifest.get("MRLORE_REVISION_BREATHING_MAP_COMPLETE") else 1


if __name__ == "__main__":
    raise SystemExit(main())
