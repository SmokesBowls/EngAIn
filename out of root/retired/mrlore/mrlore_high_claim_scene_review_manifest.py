#!/usr/bin/env python3
"""
mrlore_high_claim_scene_review_manifest.py — flag dense proposed-claim scenes.

PURPOSE:
    Read proposed_claim_audit_summary.json and create a review manifest for
    scenes whose proposed-claim count is above the audit high-claim threshold.

INPUT:
    vault/.engain/manifests/proposed_claim_audit_summary.json

OUTPUT:
    vault/.engain/manifests/high_claim_scene_review_manifest.json

DOES NOT:
    remove claims
    alter proposed_claims.jsonl
    resolve contradictions
    write canon
    compile ZONJ
    touch runtime
"""

from __future__ import annotations

import argparse
import json
import sys
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


def default_audit_summary_path(manifest_path: Path | None = None, engain_dir: Path | None = None) -> Path:
    if engain_dir is None:
        engain_dir = _resolve_engain_dir_from_manifest(manifest_path or _default_manifest_path())
    return engain_dir / "manifests" / "proposed_claim_audit_summary.json"


def _infer_engain_dir_from_summary_path(summary_path: Path) -> Path:
    resolved = summary_path.resolve()
    for parent in resolved.parents:
        if parent.name == ".engain":
            return parent
    if resolved.parent.name == "manifests":
        return resolved.parent.parent
    return resolved.parent


def _base_manifest(summary_file: Path, out_path: Path) -> dict[str, Any]:
    return {
        "contract": "engain.mrlore_high_claim_scene_review_manifest.v1",
        "run_timestamp": datetime.now(timezone.utc).isoformat(),
        "source_audit_summary": str(summary_file),
        "review_manifest_path": str(out_path),
        "MRLORE_HIGH_CLAIM_SCENE_REVIEW_MANIFEST_COMPLETE": False,
        "CLAIM_DENSITY_REVIEW_REQUIRED": False,
        "HIGH_CLAIM_SCENES_SELECTED": 0,
        "CLAIMS_REMOVED": False,
        "PROPOSED_CLAIMS_ALTERED": False,
        "CANON_WRITTEN": False,
        "RUNTIME_TOUCHED": False,
        "GODOT_TOUCHED": False,
        "ZONJ_COMPILED": False,
        "CONTRADICTIONS_RESOLVED": False,
        "CLAIM_AUDIT_DECIDED_TRUTH": False,
        "CONTRADICTION_DETECTION_READY_AFTER_REVIEW_FLAGGING": False,
        "review_policy": "not failed; not accepted blindly; review required before canon promotion",
        "review_required_status": "CLAIM_DENSITY_REVIEW_REQUIRED",
        "high_claim_threshold": None,
        "review_required_scenes": [],
        "errors": [],
    }


def run_high_claim_scene_review_manifest(audit_summary_path: Path | str) -> dict[str, Any]:
    summary_file = Path(audit_summary_path).resolve()
    engain_dir = _infer_engain_dir_from_summary_path(summary_file)
    out_path = engain_dir / "manifests" / "high_claim_scene_review_manifest.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    manifest = _base_manifest(summary_file, out_path)
    try:
        summary = json.loads(summary_file.read_text(encoding="utf-8"))
    except FileNotFoundError:
        manifest["errors"].append(f"audit summary not found: {summary_file}")
        out_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        return manifest
    except json.JSONDecodeError as exc:
        manifest["errors"].append(f"invalid audit summary JSON: {exc.msg}")
        out_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        return manifest

    if not summary.get("MRLORE_PROPOSED_CLAIM_AUDIT_SUMMARY_COMPLETE", False):
        manifest["errors"].append("proposed claim audit summary is incomplete")
        out_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        return manifest

    threshold_info = summary.get("high_claim_scene_threshold", {})
    source_scene_counts = summary.get("source_scene_counts", {})
    if not isinstance(threshold_info, dict) or "threshold" not in threshold_info:
        manifest["errors"].append("audit summary missing high_claim_scene_threshold.threshold")
    if not isinstance(source_scene_counts, dict):
        manifest["errors"].append("audit summary source_scene_counts must be an object")
    if manifest["errors"]:
        out_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        return manifest

    try:
        threshold = float(threshold_info["threshold"])
    except (TypeError, ValueError):
        manifest["errors"].append("audit summary high_claim_scene_threshold.threshold must be numeric")
        out_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        return manifest

    review_required_scenes: list[dict[str, Any]] = []
    for source_scene, raw_count in source_scene_counts.items():
        try:
            count = int(raw_count)
        except (TypeError, ValueError):
            manifest["errors"].append(f"source_scene_counts value is not numeric for {source_scene}")
            continue
        if count > threshold:
            review_required_scenes.append(
                {
                    "SOURCE_SCENE": str(source_scene),
                    "claim_count": count,
                    "high_claim_threshold": threshold,
                    "review_status": "CLAIM_DENSITY_REVIEW_REQUIRED",
                    "canon_promotion_blocked_until_review": True,
                }
            )

    review_required_scenes.sort(key=lambda item: (-int(item["claim_count"]), item["SOURCE_SCENE"]))

    manifest.update(
        {
            "MRLORE_HIGH_CLAIM_SCENE_REVIEW_MANIFEST_COMPLETE": len(manifest["errors"]) == 0,
            "CLAIM_DENSITY_REVIEW_REQUIRED": len(review_required_scenes) > 0,
            "HIGH_CLAIM_SCENES_SELECTED": len(review_required_scenes),
            "CONTRADICTION_DETECTION_READY_AFTER_REVIEW_FLAGGING": len(manifest["errors"]) == 0,
            "high_claim_threshold": threshold_info,
            "review_required_scenes": review_required_scenes,
        }
    )
    out_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(
        description="MrLore high-claim scene review manifest — flag density only, no canon judgment."
    )
    parser.add_argument("--audit-summary", default=None, help="Path to proposed_claim_audit_summary.json.")
    parser.add_argument("--manifest", default=None, help="Path to engain_manifest.json.")
    parser.add_argument("--engain-dir", default=None, help="Direct path to vault/.engain.")
    args = parser.parse_args()

    try:
        if args.audit_summary:
            audit_summary_path = Path(args.audit_summary)
        else:
            manifest_path = Path(args.manifest) if args.manifest else None
            engain_dir = Path(args.engain_dir) if args.engain_dir else None
            audit_summary_path = default_audit_summary_path(manifest_path, engain_dir)
        review_manifest = run_high_claim_scene_review_manifest(audit_summary_path)
    except Exception as exc:
        print(f"[HIGH_CLAIM_SCENE_REVIEW] ERROR: {exc}", file=sys.stderr)
        return 1

    print(
        "[HIGH_CLAIM_SCENE_REVIEW] "
        f"MRLORE_HIGH_CLAIM_SCENE_REVIEW_MANIFEST_COMPLETE={review_manifest['MRLORE_HIGH_CLAIM_SCENE_REVIEW_MANIFEST_COMPLETE']}"
    )
    print(f"[HIGH_CLAIM_SCENE_REVIEW] HIGH_CLAIM_SCENES_SELECTED={review_manifest['HIGH_CLAIM_SCENES_SELECTED']}")
    print(f"[HIGH_CLAIM_SCENE_REVIEW] CLAIM_DENSITY_REVIEW_REQUIRED={review_manifest['CLAIM_DENSITY_REVIEW_REQUIRED']}")
    print(f"[HIGH_CLAIM_SCENE_REVIEW] CLAIMS_REMOVED={review_manifest['CLAIMS_REMOVED']}")
    print(f"[HIGH_CLAIM_SCENE_REVIEW] PROPOSED_CLAIMS_ALTERED={review_manifest['PROPOSED_CLAIMS_ALTERED']}")
    print(f"[HIGH_CLAIM_SCENE_REVIEW] CANON_WRITTEN={review_manifest['CANON_WRITTEN']}")
    print(f"[HIGH_CLAIM_SCENE_REVIEW] RUNTIME_TOUCHED={review_manifest['RUNTIME_TOUCHED']}")
    print(f"[HIGH_CLAIM_SCENE_REVIEW] MANIFEST={review_manifest['review_manifest_path']}")
    return 0 if review_manifest["MRLORE_HIGH_CLAIM_SCENE_REVIEW_MANIFEST_COMPLETE"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
