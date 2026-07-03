#!/usr/bin/env python3
"""
mrlore_temporal_collision_classification.py — sidecar temporal classification for contradiction candidates.

PURPOSE:
    Read temporal-enriched proposed claims and existing contradiction candidates,
    then write a sidecar classifying whether each candidate looks concurrent,
    sequential, durable-continuity review, unknown, or non-conflicting by object.

INPUTS:
    vault/.engain/mrlore/claims/proposed_claims.temporal_enriched.jsonl
    vault/.engain/mrlore/contradictions/contradiction_candidates.jsonl

OUTPUTS:
    vault/.engain/mrlore/contradictions/temporal_collision_classifications.jsonl
    vault/.engain/manifests/mrlore_temporal_collision_classification_manifest.json

DOES NOT:
    alter contradiction_candidates.jsonl
    alter claims
    promote/reject claims
    resolve contradictions
    write canon
    compile ZONJ
    touch Godot or runtime
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tier1.mrlore.mrlore_predicate_collision_policy_registry_gate import load_predicate_collision_policy

TEMPORAL_BASIS = "CHAPTERROOM_SCENE_ORDER"
UNRESOLVED_TEMPORAL_BASIS = "UNRESOLVED_SCENE_ORDER"
AUTHORITY_EFFECT = "NONE"

CLASSIFICATIONS = (
    "ENVIRONMENT_MULTI_HINT_ACCUMULATION",
    "CONCURRENT_OBJECT_COLLISION",
    "SEQUENTIAL_STATE_CHANGE",
    "DURABLE_STATE_CONTINUITY_REVIEW",
    "TEMPORAL_ORDER_UNKNOWN_REVIEW",
    "REVIEW_REQUIRED",
    "NO_CONFLICT_SAME_OBJECT",
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


def _infer_engain_dir_from_candidates_path(candidates_path: Path) -> Path:
    resolved = candidates_path.resolve()
    for parent in resolved.parents:
        if parent.name == ".engain":
            return parent
    return resolved.parents[2]


def _read_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, 1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"{path.name} line {line_number}: invalid JSON: {exc.msg}")
                continue
            if not isinstance(record, dict):
                errors.append(f"{path.name} line {line_number}: record is not a JSON object")
                continue
            records.append(record)
    return records, errors


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records), encoding="utf-8")


def _classification_id(candidate_id: str, classification: str) -> str:
    digest = hashlib.sha256(f"{candidate_id}\u241f{classification}".encode("utf-8")).hexdigest()[:24]
    return f"temporal_collision_classification.{digest}"


def _claim_index(enriched_claims: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for claim in enriched_claims:
        claim_id = claim.get("claim_id")
        if isinstance(claim_id, str) and claim_id:
            index[claim_id] = claim
    return index


def _extract_candidate_refs(candidate: dict[str, Any], claims_by_id: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    refs: list[dict[str, Any]] = []
    errors: list[str] = []
    object_claim_refs = candidate.get("object_claim_refs", {})
    if not isinstance(object_claim_refs, dict):
        return refs, [f"candidate {candidate.get('candidate_id', '<missing>')} has non-object object_claim_refs"]

    for obj, raw_refs in object_claim_refs.items():
        if not isinstance(raw_refs, list):
            errors.append(f"candidate {candidate.get('candidate_id', '<missing>')} object {obj} refs is not a list")
            continue
        for raw_ref in raw_refs:
            if not isinstance(raw_ref, dict):
                errors.append(f"candidate {candidate.get('candidate_id', '<missing>')} object {obj} ref is not an object")
                continue
            claim_id = str(raw_ref.get("claim_id", ""))
            claim = claims_by_id.get(claim_id, {})
            source_scene = raw_ref.get("SOURCE_SCENE") or raw_ref.get("source_scene") or claim.get("source_scene_id") or claim.get("SOURCE_SCENE")
            temporal_index = claim.get("temporal_index")
            if isinstance(temporal_index, str):
                try:
                    temporal_index = float(temporal_index)
                except ValueError:
                    temporal_index = None
            elif not isinstance(temporal_index, (int, float)):
                temporal_index = None
            ref: dict[str, Any] = {
                "claim_id": claim_id,
                "object": str(obj),
                "SOURCE_SCENE": str(source_scene or ""),
                "temporal_index": temporal_index,
                "temporal_basis": claim.get("temporal_basis", UNRESOLVED_TEMPORAL_BASIS),
            }
            if raw_ref.get("source_line") is not None:
                ref["source_line"] = raw_ref.get("source_line")
            refs.append(ref)
    return refs, errors


def _objects_for_candidate(candidate: dict[str, Any], refs: list[dict[str, Any]]) -> list[str]:
    raw_objects = candidate.get("objects")
    if isinstance(raw_objects, list):
        return [str(obj) for obj in raw_objects]
    return sorted({str(ref.get("object", "")) for ref in refs if str(ref.get("object", ""))})


def _has_concurrent_overlap(refs: list[dict[str, Any]]) -> bool:
    by_temporal_index: dict[float, set[str]] = {}
    for ref in refs:
        temporal_index = ref.get("temporal_index")
        if isinstance(temporal_index, (int, float)):
            by_temporal_index.setdefault(float(temporal_index), set()).add(str(ref.get("object", "")))
    return any(len(objects) > 1 for objects in by_temporal_index.values())


def _has_missing_temporal_index(refs: list[dict[str, Any]]) -> bool:
    return any(not isinstance(ref.get("temporal_index"), (int, float)) for ref in refs)


def classify_candidate(
    candidate: dict[str, Any],
    claims_by_id: dict[str, dict[str, Any]],
    predicate_to_class: dict[str, str],
) -> tuple[dict[str, Any], list[str]]:
    refs, errors = _extract_candidate_refs(candidate, claims_by_id)
    candidate_id = str(candidate.get("candidate_id", ""))
    predicate = str(candidate.get("predicate", ""))
    predicate_class = predicate_to_class.get(predicate, "UNKNOWN_REVIEW")
    domain = str(candidate.get("claim_domain", candidate.get("domain", "")))
    subject = str(candidate.get("subject", ""))
    objects = _objects_for_candidate(candidate, refs)
    unique_objects = sorted({obj for obj in objects if obj != ""})

    if domain == "environment" and predicate_class == "MULTI_VALUED_HINT":
        classification = "ENVIRONMENT_MULTI_HINT_ACCUMULATION"
        reason = "environment multi-valued hint predicates accumulate review context and are not contradictions by default"
    elif len(unique_objects) <= 1:
        classification = "NO_CONFLICT_SAME_OBJECT"
        reason = "candidate has the same object across source claim refs"
    elif not refs or _has_missing_temporal_index(refs):
        classification = "TEMPORAL_ORDER_UNKNOWN_REVIEW"
        reason = "one or more source claim refs lacks temporal_index"
    elif _has_concurrent_overlap(refs) and predicate_class == "EXCLUSIVE_STATE":
        classification = "CONCURRENT_OBJECT_COLLISION"
        reason = "exclusive-state predicate has different objects with equal or overlapping temporal indexes"
    elif _has_concurrent_overlap(refs) and predicate_class in {"TRANSIENT_STATE", "DURABLE_STATE", "UNKNOWN_REVIEW"}:
        classification = "CONCURRENT_OBJECT_COLLISION"
        reason = "different objects have equal or overlapping temporal indexes"
    elif predicate_class == "TRANSIENT_STATE":
        classification = "SEQUENTIAL_STATE_CHANGE"
        reason = "ordered transient-state claims indicate chronological movement/state change"
    elif predicate_class == "DURABLE_STATE":
        classification = "DURABLE_STATE_CONTINUITY_REVIEW"
        reason = "ordered durable-state claims require explicit continuity/reversal review"
    elif predicate_class == "EXCLUSIVE_STATE":
        classification = "REVIEW_REQUIRED"
        reason = "exclusive-state predicate has ordered different objects and needs policy review"
    else:
        classification = "REVIEW_REQUIRED"
        reason = "predicate has no temporal behavior class"

    temporal_indexes = sorted(
        {float(ref["temporal_index"]) for ref in refs if isinstance(ref.get("temporal_index"), (int, float))}
    )
    all_resolved = bool(refs) and not _has_missing_temporal_index(refs)
    temporal_basis = TEMPORAL_BASIS if all_resolved else UNRESOLVED_TEMPORAL_BASIS
    record = {
        "classification_id": _classification_id(candidate_id, classification),
        "candidate_id": candidate_id,
        "subject": subject,
        "predicate": predicate,
        "predicate_class": predicate_class,
        "domain": domain,
        "classification": classification,
        "temporal_basis": temporal_basis,
        "temporal_indexes": temporal_indexes,
        "source_claim_refs": refs,
        "source_scenes": sorted({str(ref.get("SOURCE_SCENE", "")) for ref in refs if str(ref.get("SOURCE_SCENE", ""))}),
        "reason": reason,
        "authority_effect": AUTHORITY_EFFECT,
    }
    return record, errors


def _base_manifest() -> dict[str, Any]:
    return {
        "contract": "engain.mrlore_temporal_collision_classification_manifest.v1",
        "run_timestamp": datetime.now(timezone.utc).isoformat(),
        "MRLORE_TEMPORAL_COLLISION_CLASSIFICATION_COMPLETE": False,
        "CANDIDATES_READ": 0,
        "CLASSIFICATIONS_WRITTEN": 0,
        "ENVIRONMENT_MULTI_HINT_ACCUMULATION_COUNT": 0,
        "CONCURRENT_OBJECT_COLLISION_COUNT": 0,
        "SEQUENTIAL_STATE_CHANGE_COUNT": 0,
        "DURABLE_STATE_CONTINUITY_REVIEW_COUNT": 0,
        "TEMPORAL_ORDER_UNKNOWN_REVIEW_COUNT": 0,
        "REVIEW_REQUIRED_COUNT": 0,
        "NO_CONFLICT_SAME_OBJECT_COUNT": 0,
        "SIDE_CAR_ONLY": True,
        "CANDIDATES_ALTERED": False,
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
        "errors": [],
        "errors_count": 0,
    }


def _write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    manifest["errors_count"] = len(manifest.get("errors", []))
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def run_temporal_collision_classification(
    enriched_claims_path: Path | str,
    candidates_path: Path | str,
    output_path: Path | str | None = None,
    manifest_path: Path | str | None = None,
    policy_registry_path: Path | str | None = None,
) -> dict[str, Any]:
    enriched_claims_path = Path(enriched_claims_path).resolve()
    candidates_path = Path(candidates_path).resolve()
    engain_dir = _infer_engain_dir_from_candidates_path(candidates_path)
    output_path = Path(output_path).resolve() if output_path else engain_dir / "mrlore" / "contradictions" / "temporal_collision_classifications.jsonl"
    manifest_path = Path(manifest_path).resolve() if manifest_path else engain_dir / "manifests" / "mrlore_temporal_collision_classification_manifest.json"
    policy_registry_path = Path(policy_registry_path).resolve() if policy_registry_path else engain_dir / "mrlore" / "lexicon" / "predicate_collision_policy.json"

    manifest = _base_manifest()
    manifest["source_enriched_claims_path"] = str(enriched_claims_path)
    manifest["source_candidates_path"] = str(candidates_path)
    manifest["source_predicate_collision_policy_registry"] = str(policy_registry_path)
    manifest["output_path"] = str(output_path)

    if not enriched_claims_path.exists():
        manifest["errors"].append(f"temporal-enriched proposed claims file not found: {enriched_claims_path}")
        _write_manifest(manifest_path, manifest)
        raise FileNotFoundError(f"temporal-enriched proposed claims file not found: {enriched_claims_path}")
    if not candidates_path.exists():
        manifest["errors"].append(f"contradiction candidates file not found: {candidates_path}")
        _write_manifest(manifest_path, manifest)
        raise FileNotFoundError(f"contradiction candidates file not found: {candidates_path}")

    try:
        predicate_to_class, _policy = load_predicate_collision_policy(policy_registry_path)
    except Exception as exc:
        manifest["errors"].append(f"predicate collision policy registry is not consumable: {exc}")
        _write_manifest(manifest_path, manifest)
        raise

    enriched_claims, claim_read_errors = _read_jsonl(enriched_claims_path)
    candidates, candidate_read_errors = _read_jsonl(candidates_path)
    manifest["errors"].extend(claim_read_errors)
    manifest["errors"].extend(candidate_read_errors)
    manifest["CANDIDATES_READ"] = len(candidates)

    claims_by_id = _claim_index(enriched_claims)
    classifications: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    for candidate in candidates:
        record, classification_errors = classify_candidate(candidate, claims_by_id, predicate_to_class)
        classifications.append(record)
        counts[record["classification"]] += 1
        manifest["errors"].extend(classification_errors)

    _write_jsonl(output_path, classifications)
    manifest["CLASSIFICATIONS_WRITTEN"] = len(classifications)
    for classification in CLASSIFICATIONS:
        manifest[f"{classification}_COUNT"] = counts[classification]
    manifest["MRLORE_TEMPORAL_COLLISION_CLASSIFICATION_COMPLETE"] = not claim_read_errors and not candidate_read_errors
    _write_manifest(manifest_path, manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Classify MrLore contradiction candidates by temporal relationship as a sidecar.")
    parser.add_argument("--manifest", default=None, help="Path to engain_manifest.json for active .engain discovery.")
    parser.add_argument("--engain-dir", default=None, help="Direct path to vault/.engain (overrides --manifest).")
    parser.add_argument("--enriched-claims", default=None, help="Path to proposed_claims.temporal_enriched.jsonl.")
    parser.add_argument("--candidates", default=None, help="Path to contradiction_candidates.jsonl.")
    parser.add_argument("--output", default=None, help="Path to temporal_collision_classifications.jsonl.")
    parser.add_argument("--policy-registry", default=None, help="Path to predicate_collision_policy.json.")
    args = parser.parse_args()

    try:
        if args.engain_dir:
            engain_dir = Path(args.engain_dir).resolve()
        else:
            manifest_path = Path(args.manifest) if args.manifest else _default_manifest_path()
            engain_dir = _resolve_engain_dir(manifest_path)
        enriched_claims_path = Path(args.enriched_claims).resolve() if args.enriched_claims else engain_dir / "mrlore" / "claims" / "proposed_claims.temporal_enriched.jsonl"
        candidates_path = Path(args.candidates).resolve() if args.candidates else engain_dir / "mrlore" / "contradictions" / "contradiction_candidates.jsonl"
        output_path = Path(args.output).resolve() if args.output else None
        policy_registry_path = Path(args.policy_registry).resolve() if args.policy_registry else None
        manifest = run_temporal_collision_classification(enriched_claims_path, candidates_path, output_path=output_path, policy_registry_path=policy_registry_path)
    except Exception as exc:
        print(f"[TEMPORAL-COLLISION] ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"MRLORE_TEMPORAL_COLLISION_CLASSIFICATION_COMPLETE={manifest['MRLORE_TEMPORAL_COLLISION_CLASSIFICATION_COMPLETE']}")
    print(f"CANDIDATES_READ={manifest['CANDIDATES_READ']}")
    print(f"CLASSIFICATIONS_WRITTEN={manifest['CLASSIFICATIONS_WRITTEN']}")
    print(f"ENVIRONMENT_MULTI_HINT_ACCUMULATION_COUNT={manifest['ENVIRONMENT_MULTI_HINT_ACCUMULATION_COUNT']}")
    print(f"CONCURRENT_OBJECT_COLLISION_COUNT={manifest['CONCURRENT_OBJECT_COLLISION_COUNT']}")
    print(f"SEQUENTIAL_STATE_CHANGE_COUNT={manifest['SEQUENTIAL_STATE_CHANGE_COUNT']}")
    print(f"DURABLE_STATE_CONTINUITY_REVIEW_COUNT={manifest['DURABLE_STATE_CONTINUITY_REVIEW_COUNT']}")
    print(f"TEMPORAL_ORDER_UNKNOWN_REVIEW_COUNT={manifest['TEMPORAL_ORDER_UNKNOWN_REVIEW_COUNT']}")
    print(f"REVIEW_REQUIRED_COUNT={manifest['REVIEW_REQUIRED_COUNT']}")
    print(f"NO_CONFLICT_SAME_OBJECT_COUNT={manifest['NO_CONFLICT_SAME_OBJECT_COUNT']}")
    print(f"SIDE_CAR_ONLY={manifest['SIDE_CAR_ONLY']}")
    print(f"CANDIDATES_ALTERED={manifest['CANDIDATES_ALTERED']}")
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
    return 0 if manifest["MRLORE_TEMPORAL_COLLISION_CLASSIFICATION_COMPLETE"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
