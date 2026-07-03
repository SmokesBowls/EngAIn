#!/usr/bin/env python3
"""
mrlore_review_rail_health_runner.py — run the non-authoritative MrLore review rail.

PURPOSE:
    Run every pre-canon MrLore review stage in order, verify each stage passes,
    verify safety flags remain false, and write one health manifest.

INPUT:
    vault/.engain/manifests/mrlore_scene_intake_manifest.json

OUTPUT:
    vault/.engain/manifests/mrlore_review_rail_health_manifest.json

DOES NOT:
    decide canon
    promote claims
    reject claims
    resolve contradictions
    compile ZONJ
    touch Godot
    touch runtime
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from tier1.mrlore.mrlore_claim_extraction_runner import (
    default_intake_manifest_path,
    run_claim_extraction,
)
from tier1.mrlore.mrlore_contradiction_candidate_audit_summary import (
    run_contradiction_candidate_audit_summary,
)
from tier1.mrlore.mrlore_contradiction_candidate_grouper import (
    run_contradiction_candidate_grouper,
)
from tier1.mrlore.mrlore_high_claim_scene_review_manifest import (
    run_high_claim_scene_review_manifest,
)
from tier1.mrlore.mrlore_entity_candidate_quality_gate import run_entity_candidate_quality_gate
from tier1.mrlore.mrlore_manual_review_decision_example_writer import (
    run_manual_review_decision_example_writer,
)
from tier1.mrlore.mrlore_manual_review_decision_schema import run_manual_review_decision_schema
from tier1.mrlore.mrlore_proposed_claim_audit_summary import run_claim_audit_summary
from tier1.mrlore.mrlore_proposed_claim_shape_gate import run_claim_shape_gate
from tier1.mrlore.mrlore_quality_aware_queue_summary import run_quality_aware_queue_summary
from tier1.mrlore.mrlore_quality_aware_review_queue_builder import (
    run_quality_aware_review_queue_builder,
)
from tier1.mrlore.mrlore_review_queue_builder import run_review_queue_builder
from tier1.mrlore.mrlore_review_queue_clean_view import run_review_queue_clean_view
from tier1.mrlore.mrlore_review_queue_noise_audit import run_review_queue_noise_audit
from tier1.mrlore.mrlore_revision_breathing_map import (
    default_paths as revision_breathing_map_default_paths,
    run_revision_breathing_map,
)
from tier1.mrlore.mrlore_revision_breathing_map_guidance_gate import run_revision_breathing_map_guidance_gate

StageFunc = Callable[[], dict[str, Any]]

_FALSE_SAFETY_FLAGS = (
    "CANON_WRITTEN",
    "RUNTIME_TOUCHED",
    "GODOT_TOUCHED",
    "ZONJ_COMPILED",
    "CONTRADICTIONS_RESOLVED",
    "CLAIMS_PROMOTED",
    "CLAIMS_REJECTED",
    "ACCEPTED_LORE_PACKET_CREATED",
    "ACCEPTED_LORE_PACKETS_CREATED",
    "GENERATED_PROSE_CREATED",
    "REPLACEMENT_PROSE_CREATED",
    "REPLACEMENT_PROSE_GENERATED",
    "REAL_DECISIONS_CREATED",
    "CLAIM_REJECTION_AUTHORITY_APPLIED",
)

_ACCEPTED_LORE_PACKET_NAMES = (
    "accepted_lore_packet.json",
    "accepted_lore_packet.jsonl",
)


def _engain_dir_from_intake(intake_path: Path) -> Path:
    try:
        intake = json.loads(intake_path.read_text(encoding="utf-8"))
    except Exception:
        return intake_path.parents[1]
    return Path(intake.get("engain_dir") or intake_path.parents[1]).resolve()


def _accepted_lore_packet_paths(engain_dir: Path) -> list[Path]:
    roots = [engain_dir / "mrlore" / "accepted", engain_dir / "mrlore" / "lore" / "accepted"]
    paths: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        for name in _ACCEPTED_LORE_PACKET_NAMES:
            paths.extend(sorted(root.rglob(name)))
    return sorted({path.resolve() for path in paths})


def _flag_violations(stage_name: str, stage_manifest: dict[str, Any]) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    for flag in _FALSE_SAFETY_FLAGS:
        if stage_manifest.get(flag) is True:
            violations.append({"stage": stage_name, "flag": flag, "value": True})
    return violations


def _stage_record(stage_name: str, pass_key: str, stage_manifest: dict[str, Any]) -> dict[str, Any]:
    passed = bool(stage_manifest.get(pass_key, False))
    return {
        "stage": stage_name,
        "pass_key": pass_key,
        "status": "PASS" if passed else "FAIL",
        "manifest_path": str(
            stage_manifest.get("manifest_path")
            or stage_manifest.get("summary_path")
            or stage_manifest.get("gate_manifest")
            or stage_manifest.get("review_manifest_path")
            or stage_manifest.get("source_intake_manifest")
            or ""
        ),
        "errors_count": len(stage_manifest.get("errors", []) or []),
        "errors": stage_manifest.get("errors", []) or [],
    }


def _run_revision_breathing_map_for_engain(engain_dir: Path) -> dict[str, Any]:
    paths = revision_breathing_map_default_paths(engain_dir=engain_dir)
    return run_revision_breathing_map(
        paths["proposed_claims"],
        paths["temporal_claims"],
        paths["cosmic_claims"],
        paths["contradiction_candidates"],
        paths["temporal_classifications"],
        paths["review_queue"],
        paths["by_chapter_review"],
        paths["coming_calendar"],
        paths["predicate_collision_policy"],
        paths["preserve_entity_allowlist"],
        paths["breathing_jsonl"],
        paths["breathing_markdown"],
        paths["manifest"],
        paths["focus_dir"],
    )


def _run_revision_breathing_map_guidance_gate_for_engain(engain_dir: Path) -> dict[str, Any]:
    return run_revision_breathing_map_guidance_gate(engain_dir=engain_dir)


def run_review_rail_health(intake_manifest_path: Path | str) -> dict[str, Any]:
    intake_path = Path(intake_manifest_path).resolve()
    engain_dir = _engain_dir_from_intake(intake_path)
    manifests_dir = engain_dir / "manifests"
    manifests_dir.mkdir(parents=True, exist_ok=True)
    health_manifest_path = manifests_dir / "mrlore_review_rail_health_manifest.json"

    claims_path = engain_dir / "mrlore" / "claims" / "proposed_claims.jsonl"
    claim_shape_manifest_path = manifests_dir / "claim_shape_gate_manifest.json"
    claim_audit_summary_path = manifests_dir / "proposed_claim_audit_summary.json"
    high_claim_manifest_path = manifests_dir / "high_claim_scene_review_manifest.json"
    candidates_path = engain_dir / "mrlore" / "contradictions" / "contradiction_candidates.jsonl"
    candidate_manifest_path = manifests_dir / "mrlore_contradiction_candidate_manifest.json"
    candidate_audit_path = manifests_dir / "mrlore_contradiction_candidate_audit_summary.json"
    review_queue_path = engain_dir / "mrlore" / "review" / "contradiction_review_queue.jsonl"
    noise_flags_path = engain_dir / "mrlore" / "review" / "contradiction_review_queue_noise_flags.jsonl"
    entity_quality_flags_path = engain_dir / "mrlore" / "claims" / "entity_candidate_quality_flags.jsonl"
    quality_aware_queue_path = engain_dir / "mrlore" / "review" / "quality_aware_contradiction_review_queue.jsonl"
    revision_dir = engain_dir / "mrlore" / "revision"
    breathing_map_jsonl_path = revision_dir / "breathing_map.jsonl"
    breathing_map_md_path = revision_dir / "breathing_map.md"
    breathing_guidance_gate_manifest_path = manifests_dir / "mrlore_revision_breathing_map_guidance_gate_manifest.json"
    manual_review_schema_path = engain_dir / "mrlore" / "review" / "manual_review_decisions.schema.json"
    manual_review_examples_path = engain_dir / "mrlore" / "review" / "manual_review_decisions.example.jsonl"

    stage_plan: list[tuple[str, str, StageFunc]] = [
        (
            "claim_extraction",
            "CLAIMS_EXTRACTED",
            lambda: run_claim_extraction(intake_path),
        ),
        (
            "proposed_claim_shape_gate",
            "MRLORE_CLAIM_SHAPE_GATE_COMPLETE",
            lambda: run_claim_shape_gate(claims_path),
        ),
        (
            "proposed_claim_audit_summary",
            "MRLORE_PROPOSED_CLAIM_AUDIT_SUMMARY_COMPLETE",
            lambda: run_claim_audit_summary(claims_path),
        ),
        (
            "high_claim_scene_review_manifest",
            "MRLORE_HIGH_CLAIM_SCENE_REVIEW_MANIFEST_COMPLETE",
            lambda: run_high_claim_scene_review_manifest(claim_audit_summary_path),
        ),
        (
            "contradiction_candidate_grouper",
            "MRLORE_CONTRADICTION_CANDIDATE_GROUPER_COMPLETE",
            lambda: run_contradiction_candidate_grouper(claims_path, high_claim_manifest_path),
        ),
        (
            "contradiction_candidate_audit_summary",
            "MRLORE_CONTRADICTION_CANDIDATE_AUDIT_SUMMARY_COMPLETE",
            lambda: run_contradiction_candidate_audit_summary(candidates_path, candidate_manifest_path),
        ),
        (
            "review_queue_builder",
            "MRLORE_REVIEW_QUEUE_BUILDER_COMPLETE",
            lambda: run_review_queue_builder(candidate_audit_path, candidates_path),
        ),
        (
            "review_queue_noise_audit",
            "MRLORE_REVIEW_QUEUE_NOISE_AUDIT_COMPLETE",
            lambda: run_review_queue_noise_audit(review_queue_path),
        ),
        (
            "review_queue_clean_view",
            "MRLORE_REVIEW_QUEUE_CLEAN_VIEW_COMPLETE",
            lambda: run_review_queue_clean_view(review_queue_path, noise_flags_path),
        ),
        (
            "entity_candidate_quality_gate",
            "MRLORE_ENTITY_CANDIDATE_QUALITY_GATE_COMPLETE",
            lambda: run_entity_candidate_quality_gate(claims_path),
        ),
        (
            "quality_aware_review_queue_builder",
            "MRLORE_QUALITY_AWARE_REVIEW_QUEUE_BUILDER_COMPLETE",
            lambda: run_quality_aware_review_queue_builder(candidates_path, entity_quality_flags_path, high_claim_manifest_path),
        ),
        (
            "quality_aware_queue_summary",
            "MRLORE_QUALITY_AWARE_QUEUE_SUMMARY_COMPLETE",
            lambda: run_quality_aware_queue_summary(quality_aware_queue_path),
        ),
        (
            "revision_breathing_map",
            "MRLORE_REVISION_BREATHING_MAP_COMPLETE",
            lambda: _run_revision_breathing_map_for_engain(engain_dir),
        ),
        (
            "revision_breathing_map_guidance_gate",
            "MRLORE_REVISION_BREATHING_MAP_GUIDANCE_GATE_COMPLETE",
            lambda: _run_revision_breathing_map_guidance_gate_for_engain(engain_dir),
        ),
        (
            "manual_review_decision_schema",
            "MRLORE_MANUAL_REVIEW_DECISION_SCHEMA_COMPLETE",
            lambda: run_manual_review_decision_schema(engain_dir=engain_dir),
        ),
        (
            "manual_review_decision_example_writer",
            "MRLORE_MANUAL_REVIEW_DECISION_EXAMPLE_WRITER_COMPLETE",
            lambda: run_manual_review_decision_example_writer(engain_dir=engain_dir),
        ),
    ]

    stages: list[dict[str, Any]] = []
    stage_manifests: dict[str, dict[str, Any]] = {}
    safety_violations: list[dict[str, Any]] = []

    for stage_name, pass_key, stage_func in stage_plan:
        try:
            stage_manifest = stage_func()
        except Exception as exc:
            stage_manifest = {pass_key: False, "errors": [str(exc)]}
        stage_manifests[stage_name] = stage_manifest
        stages.append(_stage_record(stage_name, pass_key, stage_manifest))
        safety_violations.extend(_flag_violations(stage_name, stage_manifest))

    accepted_paths = _accepted_lore_packet_paths(engain_dir)
    stages_run = len(stages)
    stages_passed = sum(1 for stage in stages if stage["status"] == "PASS")
    stage_names_passed = [str(stage["stage"]) for stage in stages if stage["status"] == "PASS"]
    extraction_manifest = stage_manifests.get("claim_extraction", {})

    health_complete = stages_passed == stages_run and not safety_violations and not accepted_paths
    health_manifest: dict[str, Any] = {
        "contract": "engain.mrlore_review_rail_health_manifest.v1",
        "run_timestamp": datetime.now(timezone.utc).isoformat(),
        "source_intake_manifest": str(intake_path),
        "engain_dir": str(engain_dir),
        "manifest_path": str(health_manifest_path),
        "MRLORE_REVIEW_RAIL_HEALTH_RUNNER_COMPLETE": health_complete,
        "STAGES_RUN": stages_run,
        "STAGES_PASSED": stages_passed,
        "STAGE_NAMES_PASSED": stage_names_passed,
        "CLAIMS_STATUS": extraction_manifest.get("CLAIMS_STATUS", "UNKNOWN"),
        "CLAIMS_EXTRACTED": bool(extraction_manifest.get("CLAIMS_EXTRACTED", False)),
        "ACCEPTED_LORE_PACKET_EXISTS": bool(accepted_paths),
        "MRLORE_REVISION_BREATHING_MAP_COMPLETE": bool(
            stage_manifests.get("revision_breathing_map", {}).get("MRLORE_REVISION_BREATHING_MAP_COMPLETE", False)
        ),
        "MRLORE_REVISION_BREATHING_MAP_GUIDANCE_GATE_COMPLETE": bool(
            stage_manifests.get("revision_breathing_map_guidance_gate", {}).get(
                "MRLORE_REVISION_BREATHING_MAP_GUIDANCE_GATE_COMPLETE", False
            )
        ),
        "CANON_WRITTEN": any(stage_manifests[name].get("CANON_WRITTEN") is True for name in stage_manifests),
        "RUNTIME_TOUCHED": any(stage_manifests[name].get("RUNTIME_TOUCHED") is True for name in stage_manifests),
        "GODOT_TOUCHED": any(stage_manifests[name].get("GODOT_TOUCHED") is True for name in stage_manifests),
        "ZONJ_COMPILED": any(stage_manifests[name].get("ZONJ_COMPILED") is True for name in stage_manifests),
        "CONTRADICTIONS_RESOLVED": any(
            stage_manifests[name].get("CONTRADICTIONS_RESOLVED") is True for name in stage_manifests
        ),
        "CLAIMS_PROMOTED": any(stage_manifests[name].get("CLAIMS_PROMOTED") is True for name in stage_manifests),
        "CLAIMS_REJECTED": any(stage_manifests[name].get("CLAIMS_REJECTED") is True for name in stage_manifests),
        "ACCEPTED_LORE_PACKET_CREATED": any(
            stage_manifests[name].get("ACCEPTED_LORE_PACKET_CREATED") is True
            or stage_manifests[name].get("ACCEPTED_LORE_PACKETS_CREATED") is True
            for name in stage_manifests
        ),
        "GENERATED_PROSE_CREATED": any(
            stage_manifests[name].get("GENERATED_PROSE_CREATED") is True for name in stage_manifests
        ),
        "REPLACEMENT_PROSE_CREATED": any(
            stage_manifests[name].get("REPLACEMENT_PROSE_CREATED") is True
            or stage_manifests[name].get("REPLACEMENT_PROSE_GENERATED") is True
            for name in stage_manifests
        ),
        "REAL_DECISIONS_CREATED": any(
            stage_manifests[name].get("REAL_DECISIONS_CREATED") is True for name in stage_manifests
        ),
        "CLAIM_REJECTION_AUTHORITY_APPLIED": any(
            stage_manifests[name].get("CLAIM_REJECTION_AUTHORITY_APPLIED") is True for name in stage_manifests
        ),
        "QUALITY_AWARE_REVIEW_QUEUE_EXISTS": quality_aware_queue_path.exists(),
        "REVISION_BREATHING_MAP_JSONL_EXISTS": breathing_map_jsonl_path.exists(),
        "REVISION_BREATHING_MAP_MD_EXISTS": breathing_map_md_path.exists(),
        "REVISION_BREATHING_MAP_GUIDANCE_GATE_MANIFEST_EXISTS": breathing_guidance_gate_manifest_path.exists(),
        "MANUAL_REVIEW_SCHEMA_EXISTS": manual_review_schema_path.exists(),
        "MANUAL_REVIEW_EXAMPLES_EXIST": manual_review_examples_path.exists(),
        "stages": stages,
        "safety_violations": safety_violations,
        "accepted_lore_packet_paths": [str(path) for path in accepted_paths],
        "outputs": {
            "proposed_claims_jsonl": str(claims_path),
            "claim_shape_gate_manifest": str(claim_shape_manifest_path),
            "proposed_claim_audit_summary": str(claim_audit_summary_path),
            "high_claim_scene_review_manifest": str(high_claim_manifest_path),
            "contradiction_candidates_jsonl": str(candidates_path),
            "contradiction_candidate_manifest": str(candidate_manifest_path),
            "contradiction_candidate_audit_summary": str(candidate_audit_path),
            "contradiction_review_queue_jsonl": str(review_queue_path),
            "review_queue_noise_flags_jsonl": str(noise_flags_path),
            "entity_candidate_quality_flags_jsonl": str(entity_quality_flags_path),
            "quality_aware_review_queue_jsonl": str(quality_aware_queue_path),
            "quality_aware_review_queue_summary": str(manifests_dir / "quality_aware_review_queue_summary.json"),
            "revision_breathing_map_jsonl": str(breathing_map_jsonl_path),
            "revision_breathing_map_md": str(breathing_map_md_path),
            "revision_breathing_map_manifest": str(manifests_dir / "mrlore_revision_breathing_map_manifest.json"),
            "revision_breathing_map_guidance_gate_manifest": str(breathing_guidance_gate_manifest_path),
            "manual_review_decision_schema": str(manual_review_schema_path),
            "manual_review_decision_examples": str(manual_review_examples_path),
        },
    }
    health_manifest_path.write_text(
        json.dumps(health_manifest, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    return health_manifest


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run MrLore non-authoritative review rail health check."
    )
    parser.add_argument("--intake-manifest", default=None, help="Path to mrlore_scene_intake_manifest.json.")
    parser.add_argument("--manifest", default=None, help="Path to engain_manifest.json for default intake resolution.")
    parser.add_argument("--engain-dir", default=None, help="Direct path to vault/.engain for default intake resolution.")
    args = parser.parse_args()

    try:
        if args.intake_manifest:
            intake_path = Path(args.intake_manifest)
        else:
            manifest_path = Path(args.manifest) if args.manifest else None
            engain_dir = Path(args.engain_dir) if args.engain_dir else None
            intake_path = default_intake_manifest_path(manifest_path, engain_dir)
        if not intake_path.exists():
            print(f"[REVIEW_RAIL_HEALTH] ERROR: intake manifest not found: {intake_path}", file=sys.stderr)
            return 1
        manifest = run_review_rail_health(intake_path)
    except Exception as exc:
        print(f"[REVIEW_RAIL_HEALTH] ERROR: {exc}", file=sys.stderr)
        return 1

    print(
        "[REVIEW_RAIL_HEALTH] "
        f"MRLORE_REVIEW_RAIL_HEALTH_RUNNER_COMPLETE={manifest['MRLORE_REVIEW_RAIL_HEALTH_RUNNER_COMPLETE']}"
    )
    print(f"[REVIEW_RAIL_HEALTH] STAGES_RUN={manifest['STAGES_RUN']}")
    print(f"[REVIEW_RAIL_HEALTH] STAGES_PASSED={manifest['STAGES_PASSED']}")
    print(f"[REVIEW_RAIL_HEALTH] CLAIMS_STATUS={manifest['CLAIMS_STATUS']}")
    print(f"[REVIEW_RAIL_HEALTH] ACCEPTED_LORE_PACKET_EXISTS={manifest['ACCEPTED_LORE_PACKET_EXISTS']}")
    print(f"[REVIEW_RAIL_HEALTH] CANON_WRITTEN={manifest['CANON_WRITTEN']}")
    print(f"[REVIEW_RAIL_HEALTH] RUNTIME_TOUCHED={manifest['RUNTIME_TOUCHED']}")
    print(f"[REVIEW_RAIL_HEALTH] GODOT_TOUCHED={manifest['GODOT_TOUCHED']}")
    print(f"[REVIEW_RAIL_HEALTH] ZONJ_COMPILED={manifest['ZONJ_COMPILED']}")
    print(f"[REVIEW_RAIL_HEALTH] MANIFEST={manifest['manifest_path']}")
    return 0 if manifest["MRLORE_REVIEW_RAIL_HEALTH_RUNNER_COMPLETE"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
