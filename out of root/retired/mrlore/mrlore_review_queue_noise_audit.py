#!/usr/bin/env python3
"""
mrlore_review_queue_noise_audit.py — flag likely extraction-noise queue subjects.

PURPOSE:
    Read contradiction_review_queue.jsonl and write a separate noise flag stream
    for likely extraction noise subjects. This is review support only: no queue
    item, candidate, claim, canon, ZONJ, Godot, or runtime authority changes.

INPUT:
    vault/.engain/mrlore/review/contradiction_review_queue.jsonl

OUTPUTS:
    vault/.engain/manifests/review_queue_noise_audit_manifest.json
    vault/.engain/mrlore/review/contradiction_review_queue_noise_flags.jsonl

DOES NOT:
    delete queue items
    alter candidates
    reject claims
    write canon
    compile ZONJ
    touch Godot/runtime
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

COMMON_WORDS = {
    "a",
    "about",
    "above",
    "accept",
    "access",
    "across",
    "after",
    "again",
    "against",
    "ahead",
    "all",
    "almost",
    "alone",
    "along",
    "already",
    "also",
    "always",
    "among",
    "and",
    "another",
    "any",
    "anyone",
    "anything",
    "apart",
    "are",
    "as",
    "at",
    "away",
    "back",
    "be",
    "because",
    "been",
    "before",
    "behind",
    "below",
    "between",
    "but",
    "by",
    "can",
    "could",
    "did",
    "do",
    "does",
    "down",
    "each",
    "for",
    "from",
    "had",
    "has",
    "have",
    "he",
    "her",
    "here",
    "him",
    "his",
    "how",
    "i",
    "if",
    "in",
    "into",
    "is",
    "it",
    "its",
    "just",
    "like",
    "may",
    "more",
    "most",
    "no",
    "not",
    "of",
    "on",
    "once",
    "one",
    "only",
    "or",
    "our",
    "out",
    "over",
    "she",
    "so",
    "some",
    "than",
    "that",
    "the",
    "their",
    "them",
    "then",
    "there",
    "these",
    "they",
    "this",
    "those",
    "through",
    "to",
    "under",
    "up",
    "upon",
    "was",
    "we",
    "were",
    "what",
    "when",
    "where",
    "which",
    "while",
    "who",
    "why",
    "will",
    "with",
    "within",
    "without",
    "would",
    "you",
    "your",
}

PREPOSITIONS = {
    "about",
    "above",
    "across",
    "after",
    "against",
    "along",
    "among",
    "around",
    "at",
    "before",
    "behind",
    "below",
    "beneath",
    "beside",
    "between",
    "beyond",
    "by",
    "down",
    "during",
    "for",
    "from",
    "in",
    "inside",
    "into",
    "near",
    "of",
    "off",
    "on",
    "onto",
    "out",
    "outside",
    "over",
    "through",
    "to",
    "toward",
    "under",
    "until",
    "up",
    "upon",
    "with",
    "within",
    "without",
}

ABSTRACT_SENTENCE_STARTERS = {
    "absence",
    "absolute",
    "absolutely",
    "acceptance",
    "accepted",
    "accepting",
    "according",
    "acknowledge",
    "acknowledged",
    "acknowledgement",
    "acknowledging",
    "acknowledgment",
    "active",
    "actually",
    "adapt",
    "adaptation",
    "adapting",
    "additional",
    "adjusted",
    "adjusting",
    "adjustment",
    "advanced",
    "affirmative",
    "afraid",
    "agreed",
    "agreement",
    "aligned",
    "alignment",
    "alive",
    "allow",
    "alternative",
    "amplified",
    "amplify",
    "analysis",
    "analyzing",
    "anchored",
    "ancient",
    "answers",
    "application",
    "approach",
    "arrival",
    "becoming",
    "beginning",
    "conclusion",
    "continuation",
    "echo",
    "ending",
    "evidence",
    "memory",
    "presence",
    "recognition",
    "resonance",
    "response",
    "silence",
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
    return engain_dir / "mrlore" / "review" / "contradiction_review_queue.jsonl"


def _infer_engain_dir_from_queue_path(queue_path: Path) -> Path:
    resolved = queue_path.resolve()
    for parent in resolved.parents:
        if parent.name == ".engain":
            return parent
    return resolved.parents[2]


def _read_queue(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    items: list[dict[str, Any]] = []
    read_errors: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, 1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                read_errors.append({"line": line_number, "error": f"invalid JSON: {exc.msg}"})
                continue
            if not isinstance(item, dict):
                read_errors.append({"line": line_number, "error": "queue item must be a JSON object"})
                continue
            items.append(item)
    return items, read_errors


def _normalize_subject(subject: Any) -> str:
    return str(subject or "").strip()


def _words(subject: str) -> list[str]:
    return re.findall(r"[A-Za-z']+", subject.lower())


def _noise_reasons(subject: str) -> list[str]:
    normalized = _normalize_subject(subject)
    lower = normalized.lower()
    words = _words(normalized)
    reasons: list[str] = []
    if not normalized:
        reasons.append("empty_subject")
        return reasons
    if len(normalized) <= 2 or (len(words) == 1 and len(words[0]) <= 2):
        reasons.append("too_short_token")
    if lower in COMMON_WORDS:
        reasons.append("common_word_or_sentence_starter")
    if lower in PREPOSITIONS:
        reasons.append("preposition")
    if lower in ABSTRACT_SENTENCE_STARTERS:
        reasons.append("abstract_sentence_starter")
    if words and words[0] in COMMON_WORDS and lower not in COMMON_WORDS:
        reasons.append("starts_with_stopword")
    if len(words) == 1 and words[0] in COMMON_WORDS:
        reasons.append("stopword_like_entity")
    return reasons


def _flag_for(item: dict[str, Any], reasons: list[str]) -> dict[str, Any]:
    return {
        "queue_id": str(item.get("queue_id", "")),
        "candidate_id": str(item.get("candidate_id", "")),
        "priority_bucket": str(item.get("priority_bucket", "")),
        "claim_domain": str(item.get("claim_domain", "")),
        "subject": str(item.get("subject", "")),
        "predicate": str(item.get("predicate", "")),
        "noise_reasons": reasons,
        "status": "NOISE_REVIEW_FLAGGED",
        "queue_item_altered": False,
        "candidate_altered": False,
        "claim_rejected": False,
        "canon_written": False,
    }


def run_review_queue_noise_audit(queue_path: Path | str) -> dict[str, Any]:
    queue_file = Path(queue_path).resolve()
    engain_dir = _infer_engain_dir_from_queue_path(queue_file)
    flags_path = engain_dir / "mrlore" / "review" / "contradiction_review_queue_noise_flags.jsonl"
    manifest_path = engain_dir / "manifests" / "review_queue_noise_audit_manifest.json"
    flags_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    queue_items, read_errors = _read_queue(queue_file)
    flags: list[dict[str, Any]] = []
    reason_counts: Counter[str] = Counter()
    for item in queue_items:
        reasons = _noise_reasons(str(item.get("subject", "")))
        if reasons:
            flags.append(_flag_for(item, reasons))
            reason_counts.update(reasons)

    with flags_path.open("w", encoding="utf-8") as handle:
        for flag in flags:
            handle.write(json.dumps(flag, ensure_ascii=False, sort_keys=True) + "\n")

    manifest: dict[str, Any] = {
        "contract": "engain.mrlore_review_queue_noise_audit.v1",
        "run_timestamp": datetime.now(timezone.utc).isoformat(),
        "source_review_queue_jsonl": str(queue_file),
        "noise_flags_jsonl_path": str(flags_path),
        "manifest_path": str(manifest_path),
        "MRLORE_REVIEW_QUEUE_NOISE_AUDIT_COMPLETE": len(read_errors) == 0,
        "QUEUE_ITEMS_READ": len(queue_items),
        "NOISE_FLAGS_WRITTEN": len(flags),
        "QUEUE_ITEMS_ALTERED": False,
        "CANDIDATES_ALTERED": False,
        "CLAIMS_REJECTED": False,
        "CLAIMS_PROMOTED": False,
        "CONTRADICTIONS_RESOLVED": False,
        "CANON_WRITTEN": False,
        "RUNTIME_TOUCHED": False,
        "GODOT_TOUCHED": False,
        "ZONJ_COMPILED": False,
        "ACCEPTED_LORE_PACKET_EXISTS": False,
        "noise_reason_counts": {key: reason_counts[key] for key in sorted(reason_counts)},
        "read_errors_count": len(read_errors),
        "read_errors": read_errors[:100],
        "errors": ["review queue JSONL had read errors"] if read_errors else [],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="MrLore review queue noise audit — flags only, no deletion or rejection.")
    parser.add_argument("--queue", default=None, help="Path to contradiction_review_queue.jsonl.")
    parser.add_argument("--manifest", default=None, help="Path to engain_manifest.json.")
    parser.add_argument("--engain-dir", default=None, help="Direct path to vault/.engain.")
    args = parser.parse_args()

    try:
        manifest_path = Path(args.manifest) if args.manifest else None
        engain_dir = Path(args.engain_dir) if args.engain_dir else None
        queue_path = Path(args.queue) if args.queue else default_queue_path(manifest_path, engain_dir)
        manifest = run_review_queue_noise_audit(queue_path)
    except Exception as exc:
        print(f"[REVIEW_QUEUE_NOISE_AUDIT] ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"[REVIEW_QUEUE_NOISE_AUDIT] MRLORE_REVIEW_QUEUE_NOISE_AUDIT_COMPLETE={manifest['MRLORE_REVIEW_QUEUE_NOISE_AUDIT_COMPLETE']}")
    print(f"[REVIEW_QUEUE_NOISE_AUDIT] QUEUE_ITEMS_READ={manifest['QUEUE_ITEMS_READ']}")
    print(f"[REVIEW_QUEUE_NOISE_AUDIT] NOISE_FLAGS_WRITTEN={manifest['NOISE_FLAGS_WRITTEN']}")
    print(f"[REVIEW_QUEUE_NOISE_AUDIT] QUEUE_ITEMS_ALTERED={manifest['QUEUE_ITEMS_ALTERED']}")
    print(f"[REVIEW_QUEUE_NOISE_AUDIT] CLAIMS_REJECTED={manifest['CLAIMS_REJECTED']}")
    print(f"[REVIEW_QUEUE_NOISE_AUDIT] CANON_WRITTEN={manifest['CANON_WRITTEN']}")
    print(f"[REVIEW_QUEUE_NOISE_AUDIT] MANIFEST={manifest['manifest_path']}")
    return 0 if manifest["MRLORE_REVIEW_QUEUE_NOISE_AUDIT_COMPLETE"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
