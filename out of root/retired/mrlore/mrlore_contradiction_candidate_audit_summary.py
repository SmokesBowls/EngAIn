#!/usr/bin/env python3
"""
mrlore_contradiction_candidate_audit_summary.py — summarize contradiction pressure.

PURPOSE:
    Read contradiction_candidates.jsonl and its candidate-grouper manifest, then
    write a deterministic pressure map for review planning. This is summary only.

INPUTS:
    vault/.engain/mrlore/contradictions/contradiction_candidates.jsonl
    vault/.engain/manifests/mrlore_contradiction_candidate_manifest.json

OUTPUT:
    vault/.engain/manifests/mrlore_contradiction_candidate_audit_summary.json

DOES NOT:
    resolve contradictions
    promote claims
    reject claims
    write canon
    compile ZONJ
    touch Godot/runtime
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
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


def default_candidates_path(manifest_path: Path | None = None, engain_dir: Path | None = None) -> Path:
    if engain_dir is None:
        engain_dir = _resolve_engain_dir_from_manifest(manifest_path or _default_manifest_path())
    return engain_dir / "mrlore" / "contradictions" / "contradiction_candidates.jsonl"


def default_grouper_manifest_path(manifest_path: Path | None = None, engain_dir: Path | None = None) -> Path:
    if engain_dir is None:
        engain_dir = _resolve_engain_dir_from_manifest(manifest_path or _default_manifest_path())
    return engain_dir / "manifests" / "mrlore_contradiction_candidate_manifest.json"


def _infer_engain_dir_from_candidates_path(candidates_path: Path) -> Path:
    resolved = candidates_path.resolve()
    for parent in resolved.parents:
        if parent.name == ".engain":
            return parent
    return resolved.parents[2]


def _counter_to_sorted_dict(counter: Counter[str]) -> dict[str, int]:
    return {key: counter[key] for key in sorted(counter.keys())}


def _top_items(counter: Counter[str], key_name: str, limit: int = 25) -> list[dict[str, Any]]:
    return [
        {key_name: key, "count": count}
        for key, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))[:limit]
    ]


def _read_grouper_manifest(path: Path) -> tuple[dict[str, Any], list[str]]:
    if not path.exists():
        return {}, [f"contradiction candidate grouper manifest not found: {path}"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {}, [f"invalid contradiction candidate grouper manifest JSON: {exc.msg}"]
    if not data.get("MRLORE_CONTRADICTION_CANDIDATE_GROUPER_COMPLETE", False):
        return data, ["contradiction candidate grouper manifest is incomplete"]
    return data, []


def _read_candidates(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    candidates: list[dict[str, Any]] = []
    read_errors: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, 1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                candidate = json.loads(line)
            except json.JSONDecodeError as exc:
                read_errors.append({"line": line_number, "error": f"invalid JSON: {exc.msg}"})
                continue
            if not isinstance(candidate, dict):
                read_errors.append({"line": line_number, "error": "candidate must be a JSON object"})
                continue
            candidates.append(candidate)
    return candidates, read_errors


def _bucket_for(candidate: dict[str, Any]) -> str:
    reasons = candidate.get("reasons", [])
    if not isinstance(reasons, list):
        reasons = []
    if bool(candidate.get("touches_high_claim_scene", False)):
        return "P0_HIGH_CLAIM_REVIEW_REQUIRED"
    if "incompatible_state_predicate" in {str(reason) for reason in reasons}:
        return "P1_INCOMPATIBLE_STATE_PREDICATE"
    if candidate.get("claim_domain") == "entity" and candidate.get("predicate") == "present_in":
        return "P2_CLEAN_ENTITY_PRESENCE"
    return "P3_OTHER_CLEAN_CANDIDATE"


def _empty_summary(candidates_file: Path, grouper_manifest_file: Path, out_path: Path) -> dict[str, Any]:
    return {
        "contract": "engain.mrlore_contradiction_candidate_audit_summary.v1",
        "run_timestamp": datetime.now(timezone.utc).isoformat(),
        "source_candidates_jsonl": str(candidates_file),
        "source_contradiction_candidate_manifest": str(grouper_manifest_file),
        "summary_path": str(out_path),
        "MRLORE_CONTRADICTION_CANDIDATE_AUDIT_SUMMARY_COMPLETE": False,
        "CANDIDATES_READ": 0,
        "HIGH_CLAIM_TOUCHING": 0,
        "CLEAN_SCENE_ONLY": 0,
        "DOMAIN_COUNTS_WRITTEN": False,
        "PREDICATE_COUNTS_WRITTEN": False,
        "SUBJECT_COUNTS_WRITTEN": False,
        "REVIEW_BUCKETS_WRITTEN": False,
        "CONTRADICTIONS_RESOLVED": False,
        "CLAIMS_PROMOTED": False,
        "CLAIMS_REJECTED": False,
        "CANON_WRITTEN": False,
        "RUNTIME_TOUCHED": False,
        "GODOT_TOUCHED": False,
        "ZONJ_COMPILED": False,
        "ACCEPTED_LORE_PACKET_EXISTS": False,
        "domain_counts": {},
        "predicate_counts": {},
        "subject_counts": {},
        "top_contradiction_heavy_subjects": [],
        "top_contradiction_heavy_predicates": [],
        "review_priority_buckets": {},
        "read_errors_count": 0,
        "read_errors": [],
        "errors": [],
    }


def run_contradiction_candidate_audit_summary(
    candidates_path: Path | str,
    grouper_manifest_path: Path | str,
) -> dict[str, Any]:
    candidates_file = Path(candidates_path).resolve()
    grouper_manifest_file = Path(grouper_manifest_path).resolve()
    engain_dir = _infer_engain_dir_from_candidates_path(candidates_file)
    out_path = engain_dir / "manifests" / "mrlore_contradiction_candidate_audit_summary.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    summary = _empty_summary(candidates_file, grouper_manifest_file, out_path)
    grouper_manifest, errors = _read_grouper_manifest(grouper_manifest_file)
    if errors:
        summary["errors"] = errors
        out_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        return summary

    candidates, read_errors = _read_candidates(candidates_file)
    domain_counts: Counter[str] = Counter()
    predicate_counts: Counter[str] = Counter()
    subject_counts: Counter[str] = Counter()
    review_buckets: Counter[str] = Counter(
        {
            "P0_HIGH_CLAIM_REVIEW_REQUIRED": 0,
            "P1_INCOMPATIBLE_STATE_PREDICATE": 0,
            "P2_CLEAN_ENTITY_PRESENCE": 0,
            "P3_OTHER_CLEAN_CANDIDATE": 0,
        }
    )
    high_claim_touching = 0

    for candidate in candidates:
        domain_counts[str(candidate.get("claim_domain", "<missing>"))] += 1
        predicate_counts[str(candidate.get("predicate", "<missing>"))] += 1
        subject_counts[str(candidate.get("subject", "<missing>"))] += 1
        if bool(candidate.get("touches_high_claim_scene", False)):
            high_claim_touching += 1
        review_buckets[_bucket_for(candidate)] += 1

    errors = []
    if read_errors:
        errors.append("contradiction candidate JSONL had read errors")
    expected_count = grouper_manifest.get("CONTRADICTION_CANDIDATES_WRITTEN")
    if isinstance(expected_count, int) and expected_count != len(candidates):
        errors.append(
            f"candidate count mismatch: manifest={expected_count} jsonl={len(candidates)}"
        )
    expected_high = grouper_manifest.get("CANDIDATES_TOUCHING_HIGH_CLAIM_SCENES")
    if isinstance(expected_high, int) and expected_high != high_claim_touching:
        errors.append(
            f"high-claim touching count mismatch: manifest={expected_high} jsonl={high_claim_touching}"
        )

    summary.update(
        {
            "MRLORE_CONTRADICTION_CANDIDATE_AUDIT_SUMMARY_COMPLETE": len(errors) == 0,
            "CANDIDATES_READ": len(candidates),
            "HIGH_CLAIM_TOUCHING": high_claim_touching,
            "CLEAN_SCENE_ONLY": len(candidates) - high_claim_touching,
            "DOMAIN_COUNTS_WRITTEN": True,
            "PREDICATE_COUNTS_WRITTEN": True,
            "SUBJECT_COUNTS_WRITTEN": True,
            "REVIEW_BUCKETS_WRITTEN": True,
            "domain_counts": _counter_to_sorted_dict(domain_counts),
            "predicate_counts": _counter_to_sorted_dict(predicate_counts),
            "subject_counts": _counter_to_sorted_dict(subject_counts),
            "top_contradiction_heavy_subjects": _top_items(subject_counts, "subject"),
            "top_contradiction_heavy_predicates": _top_items(predicate_counts, "predicate"),
            "review_priority_buckets": _counter_to_sorted_dict(review_buckets),
            "read_errors_count": len(read_errors),
            "read_errors": read_errors[:100],
            "errors": errors,
            "candidate_policy": "summarize contradiction pressure only; do not resolve, promote, reject, or decide canon",
        }
    )
    out_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(
        description="MrLore contradiction candidate audit summary — pressure map only, no resolution."
    )
    parser.add_argument("--candidates", default=None, help="Path to contradiction_candidates.jsonl.")
    parser.add_argument("--candidate-manifest", default=None, help="Path to mrlore_contradiction_candidate_manifest.json.")
    parser.add_argument("--manifest", default=None, help="Path to engain_manifest.json.")
    parser.add_argument("--engain-dir", default=None, help="Direct path to vault/.engain.")
    args = parser.parse_args()

    try:
        manifest_path = Path(args.manifest) if args.manifest else None
        engain_dir = Path(args.engain_dir) if args.engain_dir else None
        candidates_path = Path(args.candidates) if args.candidates else default_candidates_path(manifest_path, engain_dir)
        candidate_manifest_path = (
            Path(args.candidate_manifest)
            if args.candidate_manifest
            else default_grouper_manifest_path(manifest_path, engain_dir)
        )
        summary = run_contradiction_candidate_audit_summary(candidates_path, candidate_manifest_path)
    except Exception as exc:
        print(f"[CONTRADICTION_CANDIDATE_AUDIT] ERROR: {exc}", file=sys.stderr)
        return 1

    print(
        "[CONTRADICTION_CANDIDATE_AUDIT] "
        f"MRLORE_CONTRADICTION_CANDIDATE_AUDIT_SUMMARY_COMPLETE={summary['MRLORE_CONTRADICTION_CANDIDATE_AUDIT_SUMMARY_COMPLETE']}"
    )
    print(f"[CONTRADICTION_CANDIDATE_AUDIT] CANDIDATES_READ={summary['CANDIDATES_READ']}")
    print(f"[CONTRADICTION_CANDIDATE_AUDIT] HIGH_CLAIM_TOUCHING={summary['HIGH_CLAIM_TOUCHING']}")
    print(f"[CONTRADICTION_CANDIDATE_AUDIT] CLEAN_SCENE_ONLY={summary['CLEAN_SCENE_ONLY']}")
    print(f"[CONTRADICTION_CANDIDATE_AUDIT] DOMAIN_COUNTS_WRITTEN={summary['DOMAIN_COUNTS_WRITTEN']}")
    print(f"[CONTRADICTION_CANDIDATE_AUDIT] PREDICATE_COUNTS_WRITTEN={summary['PREDICATE_COUNTS_WRITTEN']}")
    print(f"[CONTRADICTION_CANDIDATE_AUDIT] SUBJECT_COUNTS_WRITTEN={summary['SUBJECT_COUNTS_WRITTEN']}")
    print(f"[CONTRADICTION_CANDIDATE_AUDIT] REVIEW_BUCKETS_WRITTEN={summary['REVIEW_BUCKETS_WRITTEN']}")
    print(f"[CONTRADICTION_CANDIDATE_AUDIT] CONTRADICTIONS_RESOLVED={summary['CONTRADICTIONS_RESOLVED']}")
    print(f"[CONTRADICTION_CANDIDATE_AUDIT] CANON_WRITTEN={summary['CANON_WRITTEN']}")
    print(f"[CONTRADICTION_CANDIDATE_AUDIT] SUMMARY={summary['summary_path']}")
    return 0 if summary["MRLORE_CONTRADICTION_CANDIDATE_AUDIT_SUMMARY_COMPLETE"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
