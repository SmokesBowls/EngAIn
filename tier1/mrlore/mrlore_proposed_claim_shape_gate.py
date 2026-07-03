#!/usr/bin/env python3
"""
mrlore_proposed_claim_shape_gate.py — MrLore proposed claim shape gate.

PURPOSE:
    Validate proposed_claims.jsonl before any truth/canon/conflict work.

INPUT:
    vault/.engain/mrlore/claims/proposed_claims.jsonl

OUTPUT:
    vault/.engain/manifests/claim_shape_gate_manifest.json

DOES NOT:
    decide canon
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
from typing import Any


REQUIRED_FIELDS = (
    "claim_id",
    "SOURCE_SCENE",
    "claim_domain",
    "claim_type",
    "subject",
    "predicate",
    "object",
    "status",
)
LEGAL_CLAIM_DOMAINS = ("entity", "environment")
_PRIMARY_AUTHORITY_FIELDS = (
    "primary_authority",
    "source_authority",
    "primary_source",
    "authority_source",
)
_RAW_CHAPTER_MARKERS = (
    "/raw/chapters/",
    "\\raw\\chapters\\",
    "raw/chapters/",
    "raw\\chapters\\",
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


def default_claims_path(manifest_path: Path | None = None, engain_dir: Path | None = None) -> Path:
    if engain_dir is None:
        engain_dir = _resolve_engain_dir_from_manifest(manifest_path or _default_manifest_path())
    return engain_dir / "mrlore" / "claims" / "proposed_claims.jsonl"


def _infer_engain_dir_from_claims_path(claims_path: Path) -> Path:
    resolved = claims_path.resolve()
    for parent in resolved.parents:
        if parent.name == ".engain":
            return parent
    # Expected shape is <engain_dir>/mrlore/claims/proposed_claims.jsonl.
    return resolved.parents[2]


def _is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _uses_raw_chapter_primary_authority(claim: dict[str, Any]) -> bool:
    for field in _PRIMARY_AUTHORITY_FIELDS:
        value = claim.get(field)
        if value is None:
            continue
        text = str(value)
        if any(marker in text for marker in _RAW_CHAPTER_MARKERS):
            return True
    return False


def validate_claim_shape(claim: Any, line_number: int) -> list[str]:
    if not isinstance(claim, dict):
        return ["claim must be a JSON object"]

    failures: list[str] = []
    for field in REQUIRED_FIELDS:
        if field not in claim:
            failures.append(f"missing required field: {field}")
        elif not _is_nonempty_string(claim[field]):
            failures.append(f"required field must be non-empty string: {field}")

    if claim.get("status") != "PROPOSED":
        failures.append("status must be PROPOSED")

    domain = claim.get("claim_domain")
    if domain not in LEGAL_CLAIM_DOMAINS:
        failures.append(f"illegal claim_domain: {domain}")

    if _uses_raw_chapter_primary_authority(claim):
        failures.append("raw chapter primary authority is not allowed")

    return failures


def run_claim_shape_gate(claims_path: Path | str) -> dict[str, Any]:
    claims_file = Path(claims_path).resolve()
    engain_dir = _infer_engain_dir_from_claims_path(claims_file)
    manifest_path = engain_dir / "manifests" / "claim_shape_gate_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    claims_checked = 0
    claims_passed = 0
    failures: list[dict[str, Any]] = []
    raw_chapter_primary_authority_used = False

    with claims_file.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, 1):
            line = raw_line.strip()
            if not line:
                continue
            claims_checked += 1
            claim_id = f"line:{line_number}"
            try:
                claim = json.loads(line)
                if isinstance(claim, dict) and claim.get("claim_id"):
                    claim_id = str(claim["claim_id"])
            except json.JSONDecodeError as exc:
                failures.append(
                    {
                        "line": line_number,
                        "claim_id": claim_id,
                        "errors": [f"invalid JSON: {exc.msg}"],
                    }
                )
                continue

            claim_failures = validate_claim_shape(claim, line_number)
            if isinstance(claim, dict) and _uses_raw_chapter_primary_authority(claim):
                raw_chapter_primary_authority_used = True
            if claim_failures:
                failures.append(
                    {
                        "line": line_number,
                        "claim_id": claim_id,
                        "SOURCE_SCENE": claim.get("SOURCE_SCENE") if isinstance(claim, dict) else None,
                        "errors": claim_failures,
                    }
                )
            else:
                claims_passed += 1

    claims_failed = len(failures)
    manifest: dict[str, Any] = {
        "contract": "engain.mrlore_claim_shape_gate_manifest.v1",
        "run_timestamp": datetime.now(timezone.utc).isoformat(),
        "source_claims_jsonl": str(claims_file),
        "gate_manifest": str(manifest_path),
        "MRLORE_CLAIM_SHAPE_GATE_COMPLETE": claims_failed == 0,
        "CLAIMS_CHECKED": claims_checked,
        "CLAIMS_PASSED": claims_passed,
        "CLAIMS_FAILED": claims_failed,
        "required_fields": list(REQUIRED_FIELDS),
        "legal_claim_domains": list(LEGAL_CLAIM_DOMAINS),
        "raw_chapter_primary_authority_used": raw_chapter_primary_authority_used,
        "CANON_WRITTEN": False,
        "RUNTIME_TOUCHED": False,
        "GODOT_TOUCHED": False,
        "ZONJ_COMPILED": False,
        "CONTRADICTIONS_RESOLVED": False,
        "failures": failures,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(
        description="MrLore proposed claim shape gate — structure only, no canon judgment."
    )
    parser.add_argument(
        "--claims",
        default=None,
        help="Path to proposed_claims.jsonl.",
    )
    parser.add_argument(
        "--manifest",
        default=None,
        help="Path to engain_manifest.json for resolving default claims path.",
    )
    parser.add_argument(
        "--engain-dir",
        default=None,
        help="Direct path to vault/.engain for resolving default claims path.",
    )
    args = parser.parse_args()

    try:
        if args.claims:
            claims_path = Path(args.claims)
        else:
            manifest_path = Path(args.manifest) if args.manifest else None
            engain_dir = Path(args.engain_dir) if args.engain_dir else None
            claims_path = default_claims_path(manifest_path, engain_dir)
        if not claims_path.exists():
            print(f"[CLAIM_SHAPE_GATE] ERROR: proposed claims not found: {claims_path}", file=sys.stderr)
            return 1
        manifest = run_claim_shape_gate(claims_path)
    except Exception as exc:
        print(f"[CLAIM_SHAPE_GATE] ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"[CLAIM_SHAPE_GATE] MRLORE_CLAIM_SHAPE_GATE_COMPLETE={manifest['MRLORE_CLAIM_SHAPE_GATE_COMPLETE']}")
    print(f"[CLAIM_SHAPE_GATE] CLAIMS_CHECKED={manifest['CLAIMS_CHECKED']}")
    print(f"[CLAIM_SHAPE_GATE] CLAIMS_PASSED={manifest['CLAIMS_PASSED']}")
    print(f"[CLAIM_SHAPE_GATE] CLAIMS_FAILED={manifest['CLAIMS_FAILED']}")
    print(f"[CLAIM_SHAPE_GATE] CANON_WRITTEN={manifest['CANON_WRITTEN']}")
    print(f"[CLAIM_SHAPE_GATE] RUNTIME_TOUCHED={manifest['RUNTIME_TOUCHED']}")
    print(f"[CLAIM_SHAPE_GATE] GATE_MANIFEST={manifest['gate_manifest']}")
    return 0 if manifest["MRLORE_CLAIM_SHAPE_GATE_COMPLETE"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
