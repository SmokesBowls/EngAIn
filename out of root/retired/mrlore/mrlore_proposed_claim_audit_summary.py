#!/usr/bin/env python3
"""
mrlore_proposed_claim_audit_summary.py — summarize proposed MrLore claims.

PURPOSE:
    Read proposed_claims.jsonl and produce a distribution/reporting map before
    any contradiction, canon, or promotion work.

INPUT:
    vault/.engain/mrlore/claims/proposed_claims.jsonl

OUTPUT:
    vault/.engain/manifests/proposed_claim_audit_summary.json

DOES NOT:
    resolve contradictions
    write canon
    compile ZONJ
    touch runtime
"""

from __future__ import annotations

import argparse
import json
import math
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


def default_claims_path(manifest_path: Path | None = None, engain_dir: Path | None = None) -> Path:
    if engain_dir is None:
        engain_dir = _resolve_engain_dir_from_manifest(manifest_path or _default_manifest_path())
    return engain_dir / "mrlore" / "claims" / "proposed_claims.jsonl"


def _infer_engain_dir_from_claims_path(claims_path: Path) -> Path:
    resolved = claims_path.resolve()
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


def _claim_count_threshold(counts: list[int]) -> dict[str, Any]:
    if not counts:
        return {"mean": 0.0, "standard_deviation": 0.0, "threshold": 0.0}
    mean = sum(counts) / len(counts)
    variance = sum((count - mean) ** 2 for count in counts) / len(counts)
    stdev = math.sqrt(variance)
    threshold = mean + (2 * stdev)
    return {
        "mean": round(mean, 4),
        "standard_deviation": round(stdev, 4),
        "threshold": round(threshold, 4),
    }


def run_claim_audit_summary(claims_path: Path | str) -> dict[str, Any]:
    claims_file = Path(claims_path).resolve()
    engain_dir = _infer_engain_dir_from_claims_path(claims_file)
    out_path = engain_dir / "manifests" / "proposed_claim_audit_summary.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    domain_counts: Counter[str] = Counter()
    claim_type_counts: Counter[str] = Counter()
    predicate_counts: Counter[str] = Counter()
    source_scene_counts: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    read_errors: list[dict[str, Any]] = []
    claims_read = 0

    with claims_file.open("r", encoding="utf-8") as handle:
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

            claims_read += 1
            domain_counts[str(claim.get("claim_domain", "<missing>"))] += 1
            claim_type_counts[str(claim.get("claim_type", "<missing>"))] += 1
            predicate_counts[str(claim.get("predicate", "<missing>"))] += 1
            source_scene_counts[str(claim.get("SOURCE_SCENE", "<missing>"))] += 1
            status_counts[str(claim.get("status", "<missing>"))] += 1

    scene_count_values = list(source_scene_counts.values())
    threshold_info = _claim_count_threshold(scene_count_values)
    threshold = float(threshold_info["threshold"])
    statistically_unusual_scenes = [
        {"SOURCE_SCENE": scene, "count": count}
        for scene, count in sorted(source_scene_counts.items(), key=lambda item: (-item[1], item[0]))
        if count >= threshold and count > 0
    ]

    summary: dict[str, Any] = {
        "contract": "engain.mrlore_proposed_claim_audit_summary.v1",
        "run_timestamp": datetime.now(timezone.utc).isoformat(),
        "source_claims_jsonl": str(claims_file),
        "summary_path": str(out_path),
        "MRLORE_PROPOSED_CLAIM_AUDIT_SUMMARY_COMPLETE": len(read_errors) == 0,
        "CLAIMS_READ": claims_read,
        "DOMAINS_COUNTED": True,
        "PREDICATES_COUNTED": True,
        "SOURCE_SCENES_COUNTED": True,
        "CLAIM_TYPES_COUNTED": True,
        "CANON_WRITTEN": False,
        "RUNTIME_TOUCHED": False,
        "GODOT_TOUCHED": False,
        "ZONJ_COMPILED": False,
        "CONTRADICTIONS_RESOLVED": False,
        "domain_counts": _counter_to_sorted_dict(domain_counts),
        "claim_type_counts": _counter_to_sorted_dict(claim_type_counts),
        "predicate_counts": _counter_to_sorted_dict(predicate_counts),
        "source_scene_counts": _counter_to_sorted_dict(source_scene_counts),
        "status_counts": _counter_to_sorted_dict(status_counts),
        "top_noisy_predicates": _top_items(predicate_counts, "predicate"),
        "top_claim_types": _top_items(claim_type_counts, "claim_type"),
        "top_claim_domains": _top_items(domain_counts, "claim_domain"),
        "high_claim_scene_threshold": threshold_info,
        "statistically_unusual_high_claim_scenes": statistically_unusual_scenes[:50],
        "high_claim_scenes": _top_items(source_scene_counts, "SOURCE_SCENE", limit=50),
        "read_errors_count": len(read_errors),
        "read_errors": read_errors,
    }
    out_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(
        description="MrLore proposed claim audit summary — distribution only, no canon judgment."
    )
    parser.add_argument("--claims", default=None, help="Path to proposed_claims.jsonl.")
    parser.add_argument("--manifest", default=None, help="Path to engain_manifest.json.")
    parser.add_argument("--engain-dir", default=None, help="Direct path to vault/.engain.")
    args = parser.parse_args()

    try:
        if args.claims:
            claims_path = Path(args.claims)
        else:
            manifest_path = Path(args.manifest) if args.manifest else None
            engain_dir = Path(args.engain_dir) if args.engain_dir else None
            claims_path = default_claims_path(manifest_path, engain_dir)
        if not claims_path.exists():
            print(f"[CLAIM_AUDIT_SUMMARY] ERROR: proposed claims not found: {claims_path}", file=sys.stderr)
            return 1
        summary = run_claim_audit_summary(claims_path)
    except Exception as exc:
        print(f"[CLAIM_AUDIT_SUMMARY] ERROR: {exc}", file=sys.stderr)
        return 1

    print(
        "[CLAIM_AUDIT_SUMMARY] "
        f"MRLORE_PROPOSED_CLAIM_AUDIT_SUMMARY_COMPLETE={summary['MRLORE_PROPOSED_CLAIM_AUDIT_SUMMARY_COMPLETE']}"
    )
    print(f"[CLAIM_AUDIT_SUMMARY] CLAIMS_READ={summary['CLAIMS_READ']}")
    print(f"[CLAIM_AUDIT_SUMMARY] DOMAINS_COUNTED={summary['DOMAINS_COUNTED']}")
    print(f"[CLAIM_AUDIT_SUMMARY] PREDICATES_COUNTED={summary['PREDICATES_COUNTED']}")
    print(f"[CLAIM_AUDIT_SUMMARY] SOURCE_SCENES_COUNTED={summary['SOURCE_SCENES_COUNTED']}")
    print(f"[CLAIM_AUDIT_SUMMARY] CANON_WRITTEN={summary['CANON_WRITTEN']}")
    print(f"[CLAIM_AUDIT_SUMMARY] RUNTIME_TOUCHED={summary['RUNTIME_TOUCHED']}")
    print(f"[CLAIM_AUDIT_SUMMARY] SUMMARY={summary['summary_path']}")
    return 0 if summary["MRLORE_PROPOSED_CLAIM_AUDIT_SUMMARY_COMPLETE"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
