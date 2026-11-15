#!/usr/bin/env python3
"""
mrlore_contradiction_candidate_grouper.py — group proposed claims into possible contradiction candidates.

PURPOSE:
    Read proposed_claims.jsonl plus the high-claim scene review manifest and
    write review-space contradiction candidates. This is grouping/flagging only.

INPUTS:
    vault/.engain/mrlore/claims/proposed_claims.jsonl
    vault/.engain/manifests/high_claim_scene_review_manifest.json

OUTPUTS:
    vault/.engain/mrlore/contradictions/contradiction_candidates.jsonl
    vault/.engain/manifests/mrlore_contradiction_candidate_manifest.json

DOES NOT:
    resolve contradictions
    promote claims
    reject claims
    write canon
    compile ZONJ
    touch runtime
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SINGLE_VALUE_STATE_PREDICATES = {
    "terrain_family",
    "region",
    "weather",
    "time_of_day",
    "season",
    "location",
    "state",
    "status",
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


def default_claims_path(manifest_path: Path | None = None, engain_dir: Path | None = None) -> Path:
    if engain_dir is None:
        engain_dir = _resolve_engain_dir_from_manifest(manifest_path or _default_manifest_path())
    return engain_dir / "mrlore" / "claims" / "proposed_claims.jsonl"


def default_high_claim_manifest_path(manifest_path: Path | None = None, engain_dir: Path | None = None) -> Path:
    if engain_dir is None:
        engain_dir = _resolve_engain_dir_from_manifest(manifest_path or _default_manifest_path())
    return engain_dir / "manifests" / "high_claim_scene_review_manifest.json"


def _infer_engain_dir_from_claims_path(claims_path: Path) -> Path:
    resolved = claims_path.resolve()
    for parent in resolved.parents:
        if parent.name == ".engain":
            return parent
    return resolved.parents[2]


def _candidate_id(parts: list[str]) -> str:
    digest = hashlib.sha256("\u241f".join(parts).encode("utf-8")).hexdigest()[:24]
    return f"contradiction_candidate.{digest}"


def _load_high_claim_scenes(high_claim_manifest_path: Path) -> tuple[set[str], dict[str, Any], list[str]]:
    errors: list[str] = []
    if not high_claim_manifest_path.exists():
        return set(), {}, [f"high claim scene review manifest not found: {high_claim_manifest_path}"]
    try:
        manifest = json.loads(high_claim_manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return set(), {}, [f"invalid high claim scene review manifest JSON: {exc.msg}"]
    if not manifest.get("MRLORE_HIGH_CLAIM_SCENE_REVIEW_MANIFEST_COMPLETE", False):
        errors.append("high claim scene review manifest is incomplete")
    scenes: set[str] = set()
    for item in manifest.get("review_required_scenes", []):
        if isinstance(item, dict) and item.get("SOURCE_SCENE"):
            scenes.add(str(item["SOURCE_SCENE"]))
    return scenes, manifest, errors


def _read_claims(claims_path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    claims: list[dict[str, Any]] = []
    read_errors: list[dict[str, Any]] = []
    with claims_path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, 1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                claim = json.loads(line)
            except json.JSONDecodeError as exc:
                read_errors.append({"line": line_number, "error": f"invalid JSON: {exc.msg}"})
                continue
            if not isinstance(claim, dict):
                read_errors.append({"line": line_number, "error": "claim must be a JSON object"})
                continue
            claims.append(claim)
    return claims, read_errors


def _claim_ref(claim: dict[str, Any]) -> dict[str, Any]:
    ref: dict[str, Any] = {
        "claim_id": str(claim.get("claim_id", "")),
        "SOURCE_SCENE": str(claim.get("SOURCE_SCENE", claim.get("source_scene", ""))),
    }
    if claim.get("source_line") is not None:
        ref["source_line"] = claim.get("source_line")
    return ref


def _group_claims(claims: list[dict[str, Any]]) -> dict[tuple[str, str, str], dict[str, Any]]:
    groups: dict[tuple[str, str, str], dict[str, Any]] = {}
    for claim in claims:
        subject = str(claim.get("subject", ""))
        predicate = str(claim.get("predicate", ""))
        claim_domain = str(claim.get("claim_domain", ""))
        obj = str(claim.get("object", ""))
        source_scene = str(claim.get("SOURCE_SCENE", claim.get("source_scene", "")))
        key = (claim_domain, subject, predicate)
        if key not in groups:
            groups[key] = {
                "claim_domain": claim_domain,
                "subject": subject,
                "predicate": predicate,
                "objects": defaultdict(list),
                "source_scenes": set(),
                "claim_refs": [],
            }
        groups[key]["objects"][obj].append(_claim_ref(claim))
        groups[key]["source_scenes"].add(source_scene)
        groups[key]["claim_refs"].append(_claim_ref(claim))
    return groups


def _build_candidates(groups: dict[tuple[str, str, str], dict[str, Any]], high_claim_scenes: set[str]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for _key, group in groups.items():
        objects_map: dict[str, list[dict[str, Any]]] = group["objects"]
        objects = sorted(obj for obj in objects_map if obj != "")
        if len(objects) < 2:
            continue

        source_scenes = sorted(scene for scene in group["source_scenes"] if scene)
        touches_high = any(scene in high_claim_scenes for scene in source_scenes)
        reasons = ["same_subject_same_predicate_different_object"]
        if str(group["predicate"]) in SINGLE_VALUE_STATE_PREDICATES:
            reasons.append("incompatible_state_predicate")
        if str(group["claim_domain"]) == "environment" and str(group["subject"]) in source_scenes:
            reasons.append("same_scene_conflicting_environment_state")

        candidate = {
            "candidate_id": _candidate_id(
                [
                    str(group["claim_domain"]),
                    str(group["subject"]),
                    str(group["predicate"]),
                    *objects,
                ]
            ),
            "candidate_type": "same_subject_predicate_different_object",
            "status": "CANDIDATE_REVIEW_REQUIRED",
            "resolved": False,
            "claim_domain": str(group["claim_domain"]),
            "subject": str(group["subject"]),
            "predicate": str(group["predicate"]),
            "objects": objects,
            "source_scenes": source_scenes,
            "group_key": {
                "claim_domain": str(group["claim_domain"]),
                "subject": str(group["subject"]),
                "predicate": str(group["predicate"]),
            },
            "object_claim_refs": {obj: objects_map[obj] for obj in objects},
            "reasons": reasons,
            "touches_high_claim_scene": touches_high,
            "review_flags": ["CLAIM_DENSITY_REVIEW_REQUIRED"] if touches_high else [],
            "CONTRADICTION_RESOLVED": False,
            "CANON_WRITTEN": False,
        }
        candidates.append(candidate)

    candidates.sort(
        key=lambda item: (
            item["candidate_type"],
            item["subject"],
            item["predicate"],
            item["claim_domain"],
            item["objects"],
        )
    )
    return candidates


def run_contradiction_candidate_grouper(
    claims_path: Path | str,
    high_claim_manifest_path: Path | str,
) -> dict[str, Any]:
    claims_file = Path(claims_path).resolve()
    high_manifest_file = Path(high_claim_manifest_path).resolve()
    engain_dir = _infer_engain_dir_from_claims_path(claims_file)
    candidates_path = engain_dir / "mrlore" / "contradictions" / "contradiction_candidates.jsonl"
    manifest_path = engain_dir / "manifests" / "mrlore_contradiction_candidate_manifest.json"
    candidates_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    errors: list[str] = []
    high_claim_scenes, high_manifest, high_errors = _load_high_claim_scenes(high_manifest_file)
    errors.extend(high_errors)
    claims, read_errors = _read_claims(claims_file)
    if read_errors:
        errors.append("proposed claims JSONL had read errors")

    claims_in_high_claim_scenes = sum(
        1
        for claim in claims
        if str(claim.get("SOURCE_SCENE", claim.get("source_scene", ""))) in high_claim_scenes
    )
    groups = _group_claims(claims)
    candidates = _build_candidates(groups, high_claim_scenes)

    with candidates_path.open("w", encoding="utf-8") as handle:
        for candidate in candidates:
            handle.write(json.dumps(candidate, ensure_ascii=False, sort_keys=True) + "\n")

    candidates_touching_high = sum(1 for candidate in candidates if candidate["touches_high_claim_scene"])
    manifest: dict[str, Any] = {
        "contract": "engain.mrlore_contradiction_candidate_grouper.v1",
        "run_timestamp": datetime.now(timezone.utc).isoformat(),
        "source_claims_jsonl": str(claims_file),
        "source_high_claim_scene_review_manifest": str(high_manifest_file),
        "candidate_jsonl_path": str(candidates_path),
        "manifest_path": str(manifest_path),
        "MRLORE_CONTRADICTION_CANDIDATE_GROUPER_COMPLETE": len(errors) == 0,
        "CLAIMS_READ": len(claims),
        "GROUPS_BUILT": len(groups),
        "HIGH_CLAIM_SCENES_FLAGGED": len(high_claim_scenes),
        "CLAIMS_IN_HIGH_CLAIM_SCENES": claims_in_high_claim_scenes,
        "CONTRADICTION_CANDIDATES_WRITTEN": len(candidates),
        "CANDIDATES_TOUCHING_HIGH_CLAIM_SCENES": candidates_touching_high,
        "CONTRADICTIONS_RESOLVED": False,
        "CLAIMS_PROMOTED": False,
        "CLAIMS_REJECTED": False,
        "CANON_WRITTEN": False,
        "RUNTIME_TOUCHED": False,
        "GODOT_TOUCHED": False,
        "ZONJ_COMPILED": False,
        "ACCEPTED_LORE_PACKET_EXISTS": False,
        "candidate_policy": "identify possible conflicts only; do not resolve, promote, reject, or decide canon",
        "high_claim_scene_policy": "high-claim scenes are review-required before canon promotion; candidates touching them remain flagged",
        "high_claim_manifest_complete": bool(
            high_manifest.get("MRLORE_HIGH_CLAIM_SCENE_REVIEW_MANIFEST_COMPLETE", False)
        )
        if isinstance(high_manifest, dict)
        else False,
        "read_errors_count": len(read_errors),
        "read_errors": read_errors[:100],
        "errors": errors,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(
        description="MrLore contradiction candidate grouper — candidates only, no resolution."
    )
    parser.add_argument("--claims", default=None, help="Path to proposed_claims.jsonl.")
    parser.add_argument("--high-claim-manifest", default=None, help="Path to high_claim_scene_review_manifest.json.")
    parser.add_argument("--manifest", default=None, help="Path to engain_manifest.json.")
    parser.add_argument("--engain-dir", default=None, help="Direct path to vault/.engain.")
    args = parser.parse_args()

    try:
        manifest_path = Path(args.manifest) if args.manifest else None
        engain_dir = Path(args.engain_dir) if args.engain_dir else None
        claims_path = Path(args.claims) if args.claims else default_claims_path(manifest_path, engain_dir)
        high_claim_manifest_path = (
            Path(args.high_claim_manifest)
            if args.high_claim_manifest
            else default_high_claim_manifest_path(manifest_path, engain_dir)
        )
        manifest = run_contradiction_candidate_grouper(claims_path, high_claim_manifest_path)
    except Exception as exc:
        print(f"[CONTRADICTION_CANDIDATE_GROUPER] ERROR: {exc}", file=sys.stderr)
        return 1

    print(
        "[CONTRADICTION_CANDIDATE_GROUPER] "
        f"MRLORE_CONTRADICTION_CANDIDATE_GROUPER_COMPLETE={manifest['MRLORE_CONTRADICTION_CANDIDATE_GROUPER_COMPLETE']}"
    )
    print(f"[CONTRADICTION_CANDIDATE_GROUPER] CLAIMS_READ={manifest['CLAIMS_READ']}")
    print(f"[CONTRADICTION_CANDIDATE_GROUPER] HIGH_CLAIM_SCENES_FLAGGED={manifest['HIGH_CLAIM_SCENES_FLAGGED']}")
    print(
        "[CONTRADICTION_CANDIDATE_GROUPER] "
        f"CONTRADICTION_CANDIDATES_WRITTEN={manifest['CONTRADICTION_CANDIDATES_WRITTEN']}"
    )
    print(f"[CONTRADICTION_CANDIDATE_GROUPER] CONTRADICTIONS_RESOLVED={manifest['CONTRADICTIONS_RESOLVED']}")
    print(f"[CONTRADICTION_CANDIDATE_GROUPER] CANON_WRITTEN={manifest['CANON_WRITTEN']}")
    print(f"[CONTRADICTION_CANDIDATE_GROUPER] RUNTIME_TOUCHED={manifest['RUNTIME_TOUCHED']}")
    print(f"[CONTRADICTION_CANDIDATE_GROUPER] MANIFEST={manifest['manifest_path']}")
    print(f"[CONTRADICTION_CANDIDATE_GROUPER] CANDIDATES={manifest['candidate_jsonl_path']}")
    return 0 if manifest["MRLORE_CONTRADICTION_CANDIDATE_GROUPER_COMPLETE"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
