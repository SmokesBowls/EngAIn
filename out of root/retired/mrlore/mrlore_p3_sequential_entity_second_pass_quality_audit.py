#!/usr/bin/env python3
"""
mrlore_p3_sequential_entity_second_pass_quality_audit.py — second-pass P3 entity quality audit.

PURPOSE:
    Read temporal_aware_quality_review_queue.jsonl and write a sidecar stream of
    deterministic second-pass quality flags for only P3_SEQUENTIAL_STATE_CHANGE
    entity present_in rows. This does not alter the source queue, claims,
    candidates, contradictions, canon, runtime, Godot, or ZONJ.

INPUTS:
    vault/.engain/mrlore/review/temporal_aware_quality_review_queue.jsonl
    vault/.engain/mrlore/lexicon/preserve_entity_allowlist.json
    vault/.engain/manifests/preserve_entity_allowlist_registry_gate_manifest.json

OUTPUTS:
    vault/.engain/mrlore/review/temporal_aware_p3_second_pass_quality_flags.jsonl
    vault/.engain/manifests/temporal_aware_p3_second_pass_quality_manifest.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tier1.mrlore.mrlore_preserve_entity_allowlist_registry_gate import (
    PreserveEntityAllowlistRegistryError,
    default_registry_path,
    load_consumable_preserve_terms,
)

TARGET_BUCKET = "P3_SEQUENTIAL_STATE_CHANGE"
TARGET_DOMAIN = "entity"
TARGET_PREDICATE = "present_in"

PRONOUN_OR_CONTRACTION = {
    "i",
    "i'm",
    "i’m",
    "i've",
    "i’ve",
    "we're",
    "we’re",
    "they're",
    "they’re",
    "they've",
    "they’ve",
    "you're",
    "you’re",
    "you'll",
    "you’ll",
    "he",
    "she",
    "it",
    "we",
    "they",
    "you",
    "me",
    "him",
    "her",
    "them",
    "us",
    "my",
    "your",
    "his",
    "their",
    "our",
}

DETERMINER_OR_QUANTIFIER = {
    "all",
    "any",
    "each",
    "every",
    "few",
    "many",
    "more",
    "most",
    "some",
    "these",
    "those",
    "this",
    "that",
    "the",
    "a",
    "an",
}

CONNECTOR_OR_PREPOSITION = {
    "across",
    "after",
    "against",
    "before",
    "behind",
    "since",
    "through",
    "toward",
    "towards",
    "within",
    "into",
    "here",
    "there",
    "and",
    "or",
    "but",
    "because",
    "while",
    "during",
    "between",
    "from",
    "with",
    "without",
}

DIALOGUE_RESPONSE_TOKEN = {
    "yes",
    "yeah",
    "no",
    "sir",
    "sorry",
    "thank",
    "thanks",
    "okay",
    "ok",
}

MODAL_OR_COMMON_VERB = {
    "could",
    "would",
    "should",
    "can",
    "cannot",
    "let",
    "look",
    "see",
    "tell",
    "ask",
    "come",
    "go",
    "get",
    "do",
    "does",
    "did",
    "have",
    "has",
    "had",
    "is",
    "are",
    "was",
    "were",
    "be",
}

VAGUE_REFERENCE_WORD = {
    "something",
    "someone",
    "anything",
    "anyone",
    "everything",
    "nothing",
    "others",
    "another",
    "everyone",
    "everybody",
    "somebody",
}

NUMERIC_WORD = {
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
    "ten",
    "eleven",
    "twelve",
    "thirty",
}

SECTION_LABEL_PREFIXES = (
    "chapter ",
    "chapter:",
    "chapter_",
    "scene ",
    "scene:",
    "section ",
    "section:",
    "summary:",
    "report:",
    "metadata:",
    "claim:",
    "claims:",
    "entity report",
    "extraction report",
)

REPORT_FRAGMENT_RE = re.compile(
    r"\b(summary|manifest|report|metadata|extraction|jsonl|candidate_id|queue_id|claim_id|chapter summary)\b",
    re.IGNORECASE,
)

SENTENCE_FRAGMENT_STARTERS = {
    "this",
    "that",
    "these",
    "those",
    "there",
    "here",
    "when",
    "where",
    "while",
    "because",
    "although",
    "if",
    "as",
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


def default_queue_path(manifest_path: Path | None = None, engain_dir: Path | None = None) -> Path:
    if engain_dir is None:
        engain_dir = _resolve_engain_dir_from_manifest(manifest_path or _default_manifest_path())
    return engain_dir / "mrlore" / "review" / "temporal_aware_quality_review_queue.jsonl"


def _infer_engain_dir_from_queue_path(queue_path: Path) -> Path:
    resolved = queue_path.resolve()
    for parent in resolved.parents:
        if parent.name == ".engain":
            return parent
    return resolved.parents[2]


def _default_preserve_gate_manifest_path(registry_path: Path) -> Path:
    resolved = registry_path.resolve()
    for parent in resolved.parents:
        if parent.name == ".engain":
            return parent / "manifests" / "preserve_entity_allowlist_registry_gate_manifest.json"
    return resolved.parents[2] / "manifests" / "preserve_entity_allowlist_registry_gate_manifest.json"


def _normalize_term(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _normalize_key(value: Any) -> str:
    return _normalize_term(value).casefold()


def _read_queue(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    items: list[dict[str, Any]] = []
    errors: list[str] = []
    if not path.exists():
        return items, [f"queue not found: {path}"]
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, 1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"line {line_number}: invalid JSON: {exc.msg}")
                continue
            if not isinstance(item, dict):
                errors.append(f"line {line_number}: queue item must be a JSON object")
                continue
            items.append(item)
    return items, errors


def _item_bucket(item: dict[str, Any]) -> str:
    return str(item.get("bucket") or item.get("priority_bucket") or "")


def _item_domain(item: dict[str, Any]) -> str:
    return str(item.get("domain") or item.get("claim_domain") or "")


def _is_target_item(item: dict[str, Any]) -> bool:
    return (
        _item_bucket(item) == TARGET_BUCKET
        and _item_domain(item) == TARGET_DOMAIN
        and str(item.get("predicate") or "") == TARGET_PREDICATE
    )


def _second_pass_reasons(subject: str) -> list[str]:
    raw = str(subject or "")
    normalized = _normalize_term(raw)
    key = normalized.casefold()
    words = key.split()
    reasons: list[str] = []

    if "\n" in raw or "\r" in raw:
        reasons.append("source_markup_fragment")
    if key.startswith(SECTION_LABEL_PREFIXES) or REPORT_FRAGMENT_RE.search(normalized):
        reasons.append("source_markup_fragment")

    if key in PRONOUN_OR_CONTRACTION:
        reasons.append("pronoun_or_contraction")
    if key in DETERMINER_OR_QUANTIFIER:
        reasons.append("determiner_or_quantifier")
    if key in CONNECTOR_OR_PREPOSITION:
        reasons.append("connector_or_preposition")
    if key in DIALOGUE_RESPONSE_TOKEN:
        reasons.append("dialogue_response_token")
    if key in MODAL_OR_COMMON_VERB:
        reasons.append("modal_or_common_verb")
    if key in VAGUE_REFERENCE_WORD:
        reasons.append("vague_reference_word")
    if key in NUMERIC_WORD:
        reasons.append("numeric_word")

    if not reasons and len(words) >= 5 and words[0] in SENTENCE_FRAGMENT_STARTERS:
        reasons.append("likely_sentence_fragment")
    if not reasons and len(words) >= 7:
        reasons.append("likely_sentence_fragment")

    ordered_groups = [
        "pronoun_or_contraction",
        "determiner_or_quantifier",
        "connector_or_preposition",
        "dialogue_response_token",
        "modal_or_common_verb",
        "vague_reference_word",
        "numeric_word",
        "source_markup_fragment",
        "likely_sentence_fragment",
    ]
    return [reason for reason in ordered_groups if reason in set(reasons)]


def _flag_record(index: int, item: dict[str, Any], reasons: list[str]) -> dict[str, Any]:
    queue_id = str(item.get("queue_id") or f"queue_line_{index}")
    return {
        "flag_id": f"p3_second_pass_quality.{index:06d}.{queue_id}",
        "queue_id": queue_id,
        "candidate_id": str(item.get("candidate_id") or ""),
        "subject": str(item.get("subject") or ""),
        "bucket": TARGET_BUCKET,
        "domain": TARGET_DOMAIN,
        "predicate": TARGET_PREDICATE,
        "second_pass_quality_flagged": True,
        "second_pass_reasons": reasons,
        "authority_effect": "NONE",
    }


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records), encoding="utf-8")


def run_p3_sequential_entity_second_pass_quality_audit(
    queue_path: Path | str,
    preserve_registry_path: Path | str | None = None,
    preserve_gate_manifest_path: Path | str | None = None,
) -> dict[str, Any]:
    queue_file = Path(queue_path).resolve()
    engain_dir = _infer_engain_dir_from_queue_path(queue_file)
    flag_path = engain_dir / "mrlore" / "review" / "temporal_aware_p3_second_pass_quality_flags.jsonl"
    manifest_path = engain_dir / "manifests" / "temporal_aware_p3_second_pass_quality_manifest.json"

    registry_file = Path(preserve_registry_path).resolve() if preserve_registry_path else default_registry_path(engain_dir=engain_dir)
    gate_manifest_file = (
        Path(preserve_gate_manifest_path).resolve()
        if preserve_gate_manifest_path
        else _default_preserve_gate_manifest_path(registry_file)
    )

    manifest: dict[str, Any] = {
        "contract": "engain.mrlore_p3_sequential_entity_second_pass_quality_audit.v1",
        "run_timestamp": datetime.now(timezone.utc).isoformat(),
        "source_temporal_aware_queue_jsonl": str(queue_file),
        "preserve_registry_path": str(registry_file),
        "preserve_gate_manifest_path": str(gate_manifest_file),
        "flag_output_path": str(flag_path),
        "manifest_path": str(manifest_path),
        "MRLORE_P3_SEQUENTIAL_ENTITY_SECOND_PASS_QUALITY_AUDIT_COMPLETE": False,
        "QUEUE_ITEMS_READ": 0,
        "P3_ENTITY_ITEMS_CHECKED": 0,
        "SECOND_PASS_FLAGS_WRITTEN": 0,
        "PRESERVE_REGISTRY_USED": False,
        "PRESERVED_TERMS_SKIPPED": 0,
        "SOURCE_QUEUE_ALTERED": False,
        "CLAIMS_ALTERED": False,
        "CANDIDATES_ALTERED": False,
        "CLAIMS_REJECTED": False,
        "CLAIMS_PROMOTED": False,
        "CONTRADICTIONS_RESOLVED": False,
        "CANON_WRITTEN": False,
        "RUNTIME_TOUCHED": False,
        "GODOT_TOUCHED": False,
        "ZONJ_COMPILED": False,
        "errors": [],
        "errors_count": 0,
    }

    errors: list[str] = []
    try:
        preserve_terms = {
            _normalize_key(term)
            for term in load_consumable_preserve_terms(registry_file, gate_manifest_file)
        }
        manifest["PRESERVE_REGISTRY_USED"] = True
    except (PreserveEntityAllowlistRegistryError, OSError, json.JSONDecodeError) as exc:
        preserve_terms = set()
        errors.append(str(exc))

    queue_items, read_errors = _read_queue(queue_file)
    errors.extend(read_errors)
    manifest["QUEUE_ITEMS_READ"] = len(queue_items)

    flags: list[dict[str, Any]] = []
    preserved_skipped = 0
    checked = 0
    for item in queue_items:
        if not _is_target_item(item):
            continue
        checked += 1
        subject = str(item.get("subject") or "")
        if _normalize_key(subject) in preserve_terms:
            preserved_skipped += 1
            continue
        reasons = _second_pass_reasons(subject)
        if reasons:
            flags.append(_flag_record(len(flags) + 1, item, reasons))

    manifest["P3_ENTITY_ITEMS_CHECKED"] = checked
    manifest["PRESERVED_TERMS_SKIPPED"] = preserved_skipped
    manifest["SECOND_PASS_FLAGS_WRITTEN"] = len(flags)
    manifest["errors"] = errors
    manifest["errors_count"] = len(errors)
    manifest["MRLORE_P3_SEQUENTIAL_ENTITY_SECOND_PASS_QUALITY_AUDIT_COMPLETE"] = len(errors) == 0

    _write_jsonl(flag_path, flags)
    _write_json(manifest_path, manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="MrLore P3 sequential entity second-pass quality audit.")
    parser.add_argument("--queue", default=None, help="Path to temporal_aware_quality_review_queue.jsonl.")
    parser.add_argument("--preserve-registry", default=None, help="Path to preserve_entity_allowlist.json.")
    parser.add_argument("--preserve-gate-manifest", default=None, help="Path to preserve registry gate manifest.")
    parser.add_argument("--manifest", default=None, help="Path to engain_manifest.json.")
    parser.add_argument("--engain-dir", default=None, help="Direct path to vault/.engain.")
    args = parser.parse_args()

    try:
        manifest_path = Path(args.manifest) if args.manifest else None
        engain_dir = Path(args.engain_dir) if args.engain_dir else None
        queue_path = Path(args.queue) if args.queue else default_queue_path(manifest_path, engain_dir)
        audit = run_p3_sequential_entity_second_pass_quality_audit(
            queue_path=queue_path,
            preserve_registry_path=Path(args.preserve_registry) if args.preserve_registry else None,
            preserve_gate_manifest_path=Path(args.preserve_gate_manifest) if args.preserve_gate_manifest else None,
        )
    except Exception as exc:
        print(f"[P3_SECOND_PASS_QUALITY_AUDIT] ERROR: {exc}", file=sys.stderr)
        return 1

    print(
        "[P3_SECOND_PASS_QUALITY_AUDIT] "
        f"MRLORE_P3_SEQUENTIAL_ENTITY_SECOND_PASS_QUALITY_AUDIT_COMPLETE={audit['MRLORE_P3_SEQUENTIAL_ENTITY_SECOND_PASS_QUALITY_AUDIT_COMPLETE']}"
    )
    print(f"[P3_SECOND_PASS_QUALITY_AUDIT] QUEUE_ITEMS_READ={audit['QUEUE_ITEMS_READ']}")
    print(f"[P3_SECOND_PASS_QUALITY_AUDIT] P3_ENTITY_ITEMS_CHECKED={audit['P3_ENTITY_ITEMS_CHECKED']}")
    print(f"[P3_SECOND_PASS_QUALITY_AUDIT] SECOND_PASS_FLAGS_WRITTEN={audit['SECOND_PASS_FLAGS_WRITTEN']}")
    print(f"[P3_SECOND_PASS_QUALITY_AUDIT] PRESERVE_REGISTRY_USED={audit['PRESERVE_REGISTRY_USED']}")
    print(f"[P3_SECOND_PASS_QUALITY_AUDIT] PRESERVED_TERMS_SKIPPED={audit['PRESERVED_TERMS_SKIPPED']}")
    print(f"[P3_SECOND_PASS_QUALITY_AUDIT] SOURCE_QUEUE_ALTERED={audit['SOURCE_QUEUE_ALTERED']}")
    print(f"[P3_SECOND_PASS_QUALITY_AUDIT] CLAIMS_ALTERED={audit['CLAIMS_ALTERED']}")
    print(f"[P3_SECOND_PASS_QUALITY_AUDIT] CANDIDATES_ALTERED={audit['CANDIDATES_ALTERED']}")
    print(f"[P3_SECOND_PASS_QUALITY_AUDIT] CLAIMS_REJECTED={audit['CLAIMS_REJECTED']}")
    print(f"[P3_SECOND_PASS_QUALITY_AUDIT] CLAIMS_PROMOTED={audit['CLAIMS_PROMOTED']}")
    print(f"[P3_SECOND_PASS_QUALITY_AUDIT] CONTRADICTIONS_RESOLVED={audit['CONTRADICTIONS_RESOLVED']}")
    print(f"[P3_SECOND_PASS_QUALITY_AUDIT] CANON_WRITTEN={audit['CANON_WRITTEN']}")
    print(f"[P3_SECOND_PASS_QUALITY_AUDIT] RUNTIME_TOUCHED={audit['RUNTIME_TOUCHED']}")
    print(f"[P3_SECOND_PASS_QUALITY_AUDIT] GODOT_TOUCHED={audit['GODOT_TOUCHED']}")
    print(f"[P3_SECOND_PASS_QUALITY_AUDIT] ZONJ_COMPILED={audit['ZONJ_COMPILED']}")
    print(f"[P3_SECOND_PASS_QUALITY_AUDIT] errors_count={audit['errors_count']}")
    print(f"[P3_SECOND_PASS_QUALITY_AUDIT] FLAGS={audit['flag_output_path']}")
    print(f"[P3_SECOND_PASS_QUALITY_AUDIT] MANIFEST={audit['manifest_path']}")
    for error in audit.get("errors", [])[:20]:
        print(f"[P3_SECOND_PASS_QUALITY_AUDIT] ERROR: {error}")
    return 0 if audit["MRLORE_P3_SEQUENTIAL_ENTITY_SECOND_PASS_QUALITY_AUDIT_COMPLETE"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
