#!/usr/bin/env python3
"""
mrlore_temporal_claim_context_enrichment.py — enrich proposed claims with chapterroom scene order.

PURPOSE:
    Read proposed_claims.jsonl and the MrLore scene intake manifest, then write a
    copy of every proposed claim with deterministic temporal context derived only
    from chapterroom/MrLore scene packet order.

INPUTS:
    vault/.engain/mrlore/claims/proposed_claims.jsonl
    vault/.engain/manifests/mrlore_scene_intake_manifest.json

OUTPUTS:
    vault/.engain/mrlore/claims/proposed_claims.temporal_enriched.jsonl
    vault/.engain/manifests/mrlore_temporal_claim_context_manifest.json

DOES NOT:
    alter proposed_claims.jsonl
    promote/reject claims
    resolve contradictions
    write canon
    compile ZONJ
    touch Godot or runtime
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TEMPORAL_BASIS = "CHAPTERROOM_SCENE_ORDER"
UNRESOLVED_TEMPORAL_BASIS = "UNRESOLVED_SCENE_ORDER"
TEMPORAL_SCOPE = "SCENE_SEQUENTIAL"


@dataclass(frozen=True)
class SceneTemporalContext:
    source_scene_id: str
    chapter_id: str
    scene_index: int
    chapter_sequence_index: int
    global_scene_sequence_index: int
    temporal_index: float


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


def _resolve_engain_dir(manifest_path: Path) -> Path:
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


def _infer_engain_dir_from_claims_path(claims_path: Path) -> Path:
    resolved = claims_path.resolve()
    if len(resolved.parents) >= 3 and resolved.parent.name == "claims" and resolved.parent.parent.name == "mrlore":
        return resolved.parent.parent.parent
    return resolved.parent.parent.parent


def _manifest_path_for_claims(claims_path: Path) -> Path:
    return _infer_engain_dir_from_claims_path(claims_path) / "manifests" / "mrlore_temporal_claim_context_manifest.json"


def _read_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                record = json.loads(stripped)
            except json.JSONDecodeError as exc:
                errors.append(f"line {line_number}: invalid JSON claim record: {exc}")
                continue
            if not isinstance(record, dict):
                errors.append(f"line {line_number}: claim record is not a JSON object")
                continue
            records.append(record)
    return records, errors


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records), encoding="utf-8")


def _temporal_index(global_scene_sequence_index: int, scene_index: int) -> float:
    return float(f"{global_scene_sequence_index}.{scene_index:03d}")


def build_scene_ordering_table(scene_intake_manifest: dict[str, Any]) -> tuple[dict[str, SceneTemporalContext], list[str]]:
    """Build scene chronology strictly from mrlore_scene_intake_manifest chapter/scene order."""
    table: dict[str, SceneTemporalContext] = {}
    errors: list[str] = []
    chapters = scene_intake_manifest.get("chapters", [])
    if not isinstance(chapters, list):
        return table, ["mrlore_scene_intake_manifest.chapters is not a list"]

    global_scene_sequence_index = 0
    for chapter_sequence_index, chapter in enumerate(chapters, 1):
        if not isinstance(chapter, dict):
            errors.append(f"chapter entry {chapter_sequence_index} is not an object")
            continue
        chapter_id = chapter.get("chapter_id")
        if not isinstance(chapter_id, str) or not chapter_id:
            errors.append(f"chapter entry {chapter_sequence_index} missing chapter_id")
            continue
        scenes = chapter.get("scenes", [])
        if not isinstance(scenes, list):
            errors.append(f"chapter {chapter_id} scenes is not a list")
            continue
        for scene_order_within_chapter, scene in enumerate(scenes, 1):
            if not isinstance(scene, dict):
                errors.append(f"chapter {chapter_id} scene entry {scene_order_within_chapter} is not an object")
                continue
            scene_id = scene.get("scene_id")
            if not isinstance(scene_id, str) or not scene_id:
                errors.append(f"chapter {chapter_id} scene entry {scene_order_within_chapter} missing scene_id")
                continue
            raw_scene_index = scene.get("scene_index", scene_order_within_chapter)
            try:
                scene_index = int(raw_scene_index)
            except (TypeError, ValueError):
                scene_index = scene_order_within_chapter
                errors.append(f"scene {scene_id} has non-numeric scene_index; used manifest scene order")
            global_scene_sequence_index += 1
            context = SceneTemporalContext(
                source_scene_id=scene_id,
                chapter_id=chapter_id,
                scene_index=scene_index,
                chapter_sequence_index=chapter_sequence_index,
                global_scene_sequence_index=global_scene_sequence_index,
                temporal_index=_temporal_index(global_scene_sequence_index, scene_index),
            )
            if scene_id in table:
                errors.append(f"duplicate scene_id in scene intake manifest: {scene_id}")
                continue
            table[scene_id] = context
    return table, errors


def _claim_source_scene_id(claim: dict[str, Any]) -> str | None:
    for key in ("source_scene", "SOURCE_SCENE", "source_scene_id"):
        value = claim.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _enrich_claim(
    claim: dict[str, Any],
    scene_ordering_table: dict[str, SceneTemporalContext],
) -> tuple[dict[str, Any], bool, str | None]:
    enriched = dict(claim)
    source_scene_id = _claim_source_scene_id(claim)
    enriched["source_scene_id"] = source_scene_id
    enriched["temporal_scope"] = TEMPORAL_SCOPE

    if source_scene_id and source_scene_id in scene_ordering_table:
        context = scene_ordering_table[source_scene_id]
        enriched.update(
            {
                "source_scene_id": context.source_scene_id,
                "chapter_id": context.chapter_id,
                "scene_index": context.scene_index,
                "chapter_sequence_index": context.chapter_sequence_index,
                "global_scene_sequence_index": context.global_scene_sequence_index,
                "temporal_index": context.temporal_index,
                "temporal_basis": TEMPORAL_BASIS,
                "temporal_confidence": 1.0,
                "temporal_scope": TEMPORAL_SCOPE,
            }
        )
        return enriched, True, None

    enriched["temporal_basis"] = UNRESOLVED_TEMPORAL_BASIS
    enriched["temporal_confidence"] = 0.0
    claim_id = claim.get("claim_id", "<missing claim_id>")
    if source_scene_id:
        error = f"unresolved source scene for claim {claim_id}: {source_scene_id}"
    else:
        error = f"unresolved source scene for claim {claim_id}: missing source_scene/SOURCE_SCENE"
    return enriched, False, error


def _base_manifest() -> dict[str, Any]:
    return {
        "contract": "engain.mrlore_temporal_claim_context_manifest.v1",
        "run_timestamp": datetime.now(timezone.utc).isoformat(),
        "MRLORE_TEMPORAL_CLAIM_CONTEXT_ENRICHMENT_COMPLETE": False,
        "CLAIMS_READ": 0,
        "CLAIMS_WRITTEN": 0,
        "CLAIMS_TEMPORAL_ENRICHED": 0,
        "CLAIMS_TEMPORAL_UNRESOLVED": 0,
        "TEMPORAL_BASIS": TEMPORAL_BASIS,
        "ENGINE_AGNOSTIC": True,
        "GODOT_USED_AS_TEMPORAL_AUTHORITY": False,
        "PROPOSED_CLAIMS_ALTERED": False,
        "CLAIMS_PROMOTED": False,
        "CLAIMS_REJECTED": False,
        "CONTRADICTIONS_RESOLVED": False,
        "CANON_WRITTEN": False,
        "RUNTIME_TOUCHED": False,
        "GODOT_TOUCHED": False,
        "ZONJ_COMPILED": False,
        "errors": [],
        "errors_count": 0,
    }


def _write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    manifest["errors_count"] = len(manifest.get("errors", []))
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def run_temporal_claim_context_enrichment(
    claims_path: Path,
    scene_intake_manifest_path: Path,
    output_path: Path | None = None,
    manifest_path: Path | None = None,
) -> dict[str, Any]:
    claims_path = Path(claims_path)
    scene_intake_manifest_path = Path(scene_intake_manifest_path)
    output_path = Path(output_path) if output_path else claims_path.with_name("proposed_claims.temporal_enriched.jsonl")
    manifest_path = Path(manifest_path) if manifest_path else _manifest_path_for_claims(claims_path)

    manifest = _base_manifest()
    manifest["source_claims_path"] = str(claims_path)
    manifest["source_scene_intake_manifest"] = str(scene_intake_manifest_path)
    manifest["output_path"] = str(output_path)

    if not claims_path.exists():
        manifest["errors"].append(f"proposed claims file not found: {claims_path}")
        _write_manifest(manifest_path, manifest)
        raise FileNotFoundError(f"proposed claims file not found: {claims_path}")
    if not scene_intake_manifest_path.exists():
        manifest["errors"].append(f"mrlore scene intake manifest not found: {scene_intake_manifest_path}")
        _write_manifest(manifest_path, manifest)
        raise FileNotFoundError(f"mrlore scene intake manifest not found: {scene_intake_manifest_path}")

    claims, read_errors = _read_jsonl(claims_path)
    manifest["CLAIMS_READ"] = len(claims)
    manifest["errors"].extend(read_errors)

    try:
        scene_intake_manifest = json.loads(scene_intake_manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        manifest["errors"].append(f"failed to parse mrlore scene intake manifest: {exc}")
        _write_manifest(manifest_path, manifest)
        raise

    scene_ordering_table, table_errors = build_scene_ordering_table(scene_intake_manifest)
    manifest["SCENES_IN_ORDERING_TABLE"] = len(scene_ordering_table)
    manifest["errors"].extend(table_errors)

    enriched_claims: list[dict[str, Any]] = []
    enriched_count = 0
    unresolved_count = 0
    for claim in claims:
        enriched_claim, resolved, error = _enrich_claim(claim, scene_ordering_table)
        enriched_claims.append(enriched_claim)
        if resolved:
            enriched_count += 1
        else:
            unresolved_count += 1
            if error:
                manifest["errors"].append(error)

    _write_jsonl(output_path, enriched_claims)
    manifest["CLAIMS_WRITTEN"] = len(enriched_claims)
    manifest["CLAIMS_TEMPORAL_ENRICHED"] = enriched_count
    manifest["CLAIMS_TEMPORAL_UNRESOLVED"] = unresolved_count
    manifest["MRLORE_TEMPORAL_CLAIM_CONTEXT_ENRICHMENT_COMPLETE"] = len(read_errors) == 0 and bool(scene_ordering_table)
    _write_manifest(manifest_path, manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Enrich MrLore proposed claims with chapterroom scene-order temporal context.")
    parser.add_argument("--manifest", default=None, help="Path to engain_manifest.json for active .engain discovery.")
    parser.add_argument("--engain-dir", default=None, help="Direct path to vault/.engain (overrides --manifest).")
    parser.add_argument("--claims", default=None, help="Path to proposed_claims.jsonl.")
    parser.add_argument("--scene-intake-manifest", default=None, help="Path to mrlore_scene_intake_manifest.json.")
    parser.add_argument("--output", default=None, help="Path for proposed_claims.temporal_enriched.jsonl.")
    args = parser.parse_args()

    try:
        if args.engain_dir:
            engain_dir = Path(args.engain_dir).resolve()
        else:
            manifest_path = Path(args.manifest) if args.manifest else _default_manifest_path()
            engain_dir = _resolve_engain_dir(manifest_path)

        claims_path = Path(args.claims).resolve() if args.claims else engain_dir / "mrlore" / "claims" / "proposed_claims.jsonl"
        scene_intake_manifest_path = (
            Path(args.scene_intake_manifest).resolve()
            if args.scene_intake_manifest
            else engain_dir / "manifests" / "mrlore_scene_intake_manifest.json"
        )
        output_path = Path(args.output).resolve() if args.output else None
        manifest = run_temporal_claim_context_enrichment(claims_path, scene_intake_manifest_path, output_path=output_path)
    except Exception as exc:
        print(f"[TEMPORAL] ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"MRLORE_TEMPORAL_CLAIM_CONTEXT_ENRICHMENT_COMPLETE={manifest['MRLORE_TEMPORAL_CLAIM_CONTEXT_ENRICHMENT_COMPLETE']}")
    print(f"CLAIMS_READ={manifest['CLAIMS_READ']}")
    print(f"CLAIMS_WRITTEN={manifest['CLAIMS_WRITTEN']}")
    print(f"CLAIMS_TEMPORAL_ENRICHED={manifest['CLAIMS_TEMPORAL_ENRICHED']}")
    print(f"CLAIMS_TEMPORAL_UNRESOLVED={manifest['CLAIMS_TEMPORAL_UNRESOLVED']}")
    print(f"TEMPORAL_BASIS={manifest['TEMPORAL_BASIS']}")
    print(f"ENGINE_AGNOSTIC={manifest['ENGINE_AGNOSTIC']}")
    print(f"GODOT_USED_AS_TEMPORAL_AUTHORITY={manifest['GODOT_USED_AS_TEMPORAL_AUTHORITY']}")
    print(f"PROPOSED_CLAIMS_ALTERED={manifest['PROPOSED_CLAIMS_ALTERED']}")
    print(f"CLAIMS_PROMOTED={manifest['CLAIMS_PROMOTED']}")
    print(f"CLAIMS_REJECTED={manifest['CLAIMS_REJECTED']}")
    print(f"CONTRADICTIONS_RESOLVED={manifest['CONTRADICTIONS_RESOLVED']}")
    print(f"CANON_WRITTEN={manifest['CANON_WRITTEN']}")
    print(f"RUNTIME_TOUCHED={manifest['RUNTIME_TOUCHED']}")
    print(f"GODOT_TOUCHED={manifest['GODOT_TOUCHED']}")
    print(f"ZONJ_COMPILED={manifest['ZONJ_COMPILED']}")
    print(f"errors_count={manifest['errors_count']}")
    return 0 if manifest["MRLORE_TEMPORAL_CLAIM_CONTEXT_ENRICHMENT_COMPLETE"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
