#!/usr/bin/env python3
"""
mrlore_entity_candidate_quality_gate.py — flag likely bad entity presence subjects.

PURPOSE:
    Read proposed_claims.jsonl, check only entity/entity_presence claims, and
    write a sidecar stream of likely extraction-noise entity subjects. This is a
    quality signal only. It never alters proposed_claims.jsonl and never rejects,
    promotes, resolves, writes canon, compiles ZONJ, or touches Godot/runtime.

INPUT:
    vault/.engain/mrlore/claims/proposed_claims.jsonl

OUTPUTS:
    vault/.engain/mrlore/claims/entity_candidate_quality_flags.jsonl
    vault/.engain/manifests/mrlore_entity_candidate_quality_gate_manifest.json
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

from tier1.mrlore.mrlore_preserve_entity_allowlist_registry_gate import (
    PreserveEntityAllowlistRegistryError,
    load_consumable_preserve_terms,
)

COMMON_SINGLE_WORDS = {
    "a",
    "about",
    "above",
    "accepted",
    "again",
    "all",
    "am",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "but",
    "by",
    "can",
    "did",
    "do",
    "for",
    "from",
    "had",
    "has",
    "have",
    "he",
    "her",
    "him",
    "his",
    "i",
    "if",
    "in",
    "is",
    "it",
    "its",
    "no",
    "not",
    "of",
    "on",
    "one",
    "or",
    "our",
    "she",
    "so",
    "that",
    "the",
    "their",
    "them",
    "then",
    "there",
    "they",
    "this",
    "to",
    "was",
    "we",
    "were",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "will",
    "with",
    "you",
    "your",
}

VERB_OR_ADJECTIVE_CANDIDATES = {
    "accepted",
    "accessing",
    "aligned",
    "annihilated",
    "arriving",
    "ascending",
    "becoming",
    "burning",
    "closing",
    "connected",
    "descending",
    "emerging",
    "entering",
    "falling",
    "floating",
    "formed",
    "forming",
    "fractured",
    "glowing",
    "hidden",
    "holding",
    "moving",
    "opening",
    "revealed",
    "rising",
    "shattered",
    "standing",
    "waiting",
}

GENERIC_ABSTRACT_NOUNS = {
    "absence",
    "acceptance",
    "access",
    "agreement",
    "alignment",
    "anger",
    "attention",
    "awareness",
    "chaos",
    "choice",
    "consciousness",
    "darkness",
    "fear",
    "memory",
    "presence",
    "silence",
    "truth",
    "vision",
}

QUESTION_STARTERS = {"am", "are", "can", "could", "did", "do", "does", "have", "is", "may", "should", "was", "were", "will", "would"}

SINGLE_WORD_ADVERBS = {
    "Absolutely",
    "Actually",
    "Eventually",
    "Finally",
    "Immediately",
    "Obviously",
    "Occasionally",
    "Precisely",
    "Probably",
    "Quickly",
    "Quietly",
    "Simply",
    "Slowly",
    "Suddenly",
    "Truly",
    "Usually",
}

PROSE_CONNECTORS = {
    "According",
    "Additional",
    "Also",
    "Although",
    "Because",
    "Before",
    "Between",
    "During",
    "However",
    "Instead",
    "Meanwhile",
    "Therefore",
    "Though",
    "Unless",
    "Until",
    "Whether",
}

VERB_LIKE_SINGLE_WORDS = {
    "Accepting",
    "Acknowledge",
    "Acknowledged",
    "Acknowledging",
    "Add",
    "Adjusted",
    "Adjusting",
    "Adapting",
    "Analyzing",
    "Approached",
    "Asking",
    "Attempting",
    "Awakening",
    "Became",
    "Beginning",
    "Breathing",
    "Building",
    "Carrying",
    "Cataloging",
    "Checking",
    "Choosing",
    "Confirming",
    "Creating",
    "Drawing",
    "Entering",
    "Establishing",
    "Feeling",
    "Following",
    "Giving",
    "Guarding",
    "Holding",
    "Keeping",
    "Landing",
    "Learning",
    "Looking",
    "Moving",
    "Preparing",
    "Processing",
    "Reading",
    "Refusing",
    "Returning",
    "Searching",
    "Seeing",
    "Speaking",
    "Standing",
    "Taking",
    "Teaching",
    "Testing",
    "Touching",
    "Trying",
    "Walking",
    "Watching",
}

ABSTRACT_OR_QUALITY_WORDS = {
    "Acceptable",
    "Acidic",
    "Acknowledgment",
    "Acknowledgement",
    "Active",
    "Advanced",
    "Affirmative",
    "Afraid",
    "Agency",
    "Agreement",
    "Alive",
    "Alternative",
    "Ambient",
    "Analysis",
    "Anger",
    "Approval",
    "Architecture",
    "Attention",
    "Awareness",
    "Balance",
    "Beautiful",
    "Better",
    "Cautious",
    "Certainty",
    "Clarity",
    "Clean",
    "Coherence",
    "Communication",
    "Compassion",
    "Complexity",
    "Conclusion",
    "Confirmation",
    "Confusion",
    "Consciousness",
    "Consistency",
    "Curiosity",
    "Danger",
    "Decision",
    "Defiance",
    "Desperation",
    "Documentation",
    "Efficiency",
    "Excellent",
    "Failure",
    "Fear",
    "Freedom",
    "Gratitude",
    "Harmony",
    "Hope",
    "Information",
    "Integration",
    "Intelligence",
    "Knowledge",
    "Logic",
    "Meaningless",
    "Memory",
    "Momentum",
    "Patience",
    "Precision",
    "Presence",
    "Probability",
    "Progress",
    "Recommendation",
    "Responsibility",
    "Safety",
    "Silence",
    "Stability",
    "Structure",
    "Success",
    "Truth",
    "Unity",
    "Victory",
    "Wisdom",
}

SINGLE_WORD_ADVERBS_NORMALIZED = {word.lower() for word in SINGLE_WORD_ADVERBS}
PROSE_CONNECTORS_NORMALIZED = {word.lower() for word in PROSE_CONNECTORS}
VERB_LIKE_SINGLE_WORDS_NORMALIZED = {word.lower() for word in VERB_LIKE_SINGLE_WORDS}
ABSTRACT_OR_QUALITY_WORDS_NORMALIZED = {word.lower() for word in ABSTRACT_OR_QUALITY_WORDS}


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


def _normalize_subject(subject: Any) -> str:
    return str(subject or "").strip()


def _words(subject: str) -> list[str]:
    return re.findall(r"[A-Za-z]+(?:['’][A-Za-z]+)?", subject.lower())


def _canonical(subject: str) -> str:
    return re.sub(r"\s+", " ", _normalize_subject(subject)).lower()


def quality_reasons_for_entity_subject(subject: Any, preserve_entity_allowlist_normalized: set[str]) -> list[str]:
    normalized = _normalize_subject(subject)
    canonical = _canonical(normalized)
    words = _words(normalized)
    reasons: list[str] = []

    if not normalized:
        return ["empty_subject"]
    if canonical in preserve_entity_allowlist_normalized:
        return []
    possessive_stem = re.sub(r"['’]s\s*$", "", canonical).strip()
    if possessive_stem in preserve_entity_allowlist_normalized:
        return []
    if "\n" in normalized or "\r" in normalized:
        reasons.append("contains_newline_fragment")
    if len(words) == 1 and words[0] in SINGLE_WORD_ADVERBS_NORMALIZED:
        reasons.append("single_word_adverb")
    if len(words) == 1 and words[0] in PROSE_CONNECTORS_NORMALIZED:
        reasons.append("prose_connector")
    if len(words) == 1 and words[0] in VERB_LIKE_SINGLE_WORDS_NORMALIZED:
        reasons.append("verb_like_single_word")
    if len(words) == 1 and words[0] in ABSTRACT_OR_QUALITY_WORDS_NORMALIZED:
        reasons.append("abstract_or_quality_word")
    if len(words) == 1 and words[0] in COMMON_SINGLE_WORDS:
        reasons.append("single_common_word")
    if len(words) == 1 and words[0] in VERB_OR_ADJECTIVE_CANDIDATES:
        reasons.append("verb_or_adjective_candidate")
    if len(words) == 1 and words[0] in GENERIC_ABSTRACT_NOUNS:
        reasons.append("generic_abstract_noun")
    if re.search(r"['’]s\s*$", normalized):
        reasons.append("possessive_fragment")
    if len(words) >= 2 and words[0] in QUESTION_STARTERS and words[1] in {"i", "we", "you", "he", "she", "they", "it"}:
        reasons.append("question_fragment")
    if len(words) == 1 and len(words[0]) <= 2:
        reasons.append("too_short_token")
    return reasons


def _read_claims(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    claims: list[dict[str, Any]] = []
    read_errors: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
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


def _is_entity_presence_claim(claim: dict[str, Any]) -> bool:
    return claim.get("claim_domain") == "entity" and claim.get("claim_type") == "entity_presence"


def _flag_for(claim: dict[str, Any], reasons: list[str]) -> dict[str, Any]:
    return {
        "claim_id": str(claim.get("claim_id", "")),
        "SOURCE_SCENE": str(claim.get("SOURCE_SCENE") or claim.get("source_scene") or ""),
        "source_line": claim.get("source_line"),
        "claim_domain": str(claim.get("claim_domain", "")),
        "claim_type": str(claim.get("claim_type", "")),
        "subject": str(claim.get("subject", "")),
        "predicate": str(claim.get("predicate", "")),
        "object": str(claim.get("object", "")),
        "quality_reasons": reasons,
        "status": "QUALITY_REVIEW_FLAGGED",
        "sidecar_only": True,
        "proposed_claim_altered": False,
        "claim_rejected": False,
        "claim_promoted": False,
        "canon_written": False,
    }


def _write_registry_failure_manifest(
    manifest_path: Path,
    claims_file: Path,
    flags_path: Path,
    registry_path: Path,
    registry_gate_manifest_path: Path,
    error: str,
) -> dict[str, Any]:
    manifest: dict[str, Any] = {
        "contract": "engain.mrlore_entity_candidate_quality_gate.v2",
        "run_timestamp": datetime.now(timezone.utc).isoformat(),
        "source_proposed_claims_jsonl": str(claims_file),
        "quality_flags_jsonl_path": str(flags_path),
        "manifest_path": str(manifest_path),
        "preserve_entity_allowlist_registry_path": str(registry_path),
        "preserve_entity_allowlist_registry_gate_manifest": str(registry_gate_manifest_path),
        "MRLORE_ENTITY_CANDIDATE_QUALITY_GATE_COMPLETE": False,
        "QUALITY_GATE_CAN_CONSUME": False,
        "PROPOSED_CLAIMS_READ": 0,
        "ENTITY_PRESENCE_CLAIMS_CHECKED": 0,
        "QUALITY_FLAGS_WRITTEN": 0,
        "SIDE_CAR_FLAGS_ONLY": True,
        "PROPOSED_CLAIMS_ALTERED": False,
        "CLAIMS_REJECTED": False,
        "CLAIMS_PROMOTED": False,
        "CONTRADICTIONS_RESOLVED": False,
        "CANON_WRITTEN": False,
        "RUNTIME_TOUCHED": False,
        "GODOT_TOUCHED": False,
        "ZONJ_COMPILED": False,
        "ACCEPTED_LORE_PACKET_EXISTS": False,
        "quality_reason_counts": {},
        "preserve_entity_allowlist_terms_loaded": 0,
        "read_errors_count": 0,
        "read_errors": [],
        "errors": [error],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def _load_preserve_entity_allowlist_for_quality_gate(engain_dir: Path) -> tuple[set[str], Path, Path]:
    registry_path = engain_dir / "mrlore" / "lexicon" / "preserve_entity_allowlist.json"
    registry_gate_manifest_path = engain_dir / "manifests" / "preserve_entity_allowlist_registry_gate_manifest.json"
    preserve_terms = load_consumable_preserve_terms(registry_path, registry_gate_manifest_path)
    return {_canonical(term) for term in preserve_terms}, registry_path, registry_gate_manifest_path


def run_entity_candidate_quality_gate(claims_path: Path | str) -> dict[str, Any]:
    claims_file = Path(claims_path).resolve()
    engain_dir = _infer_engain_dir_from_claims_path(claims_file)
    flags_path = engain_dir / "mrlore" / "claims" / "entity_candidate_quality_flags.jsonl"
    manifest_path = engain_dir / "manifests" / "mrlore_entity_candidate_quality_gate_manifest.json"
    flags_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    registry_path = engain_dir / "mrlore" / "lexicon" / "preserve_entity_allowlist.json"
    registry_gate_manifest_path = engain_dir / "manifests" / "preserve_entity_allowlist_registry_gate_manifest.json"
    try:
        preserve_entity_allowlist_normalized, registry_path, registry_gate_manifest_path = _load_preserve_entity_allowlist_for_quality_gate(engain_dir)
    except PreserveEntityAllowlistRegistryError as exc:
        message = (
            "Preserve entity allowlist registry is invalid. "
            "Fix JSON or run: PYTHONPATH=. python -m tier1.mrlore.mrlore_preserve_entity_allowlist_registry_gate. "
            "QUALITY_GATE_CAN_CONSUME=False PROPOSED_CLAIMS_ALTERED=False CLAIMS_REJECTED=False "
            "CLAIMS_PROMOTED=False CANON_WRITTEN=False"
        )
        _write_registry_failure_manifest(manifest_path, claims_file, flags_path, registry_path, registry_gate_manifest_path, f"{message}; {exc}")
        raise RuntimeError(message) from exc

    claims, read_errors = _read_claims(claims_file)
    flags: list[dict[str, Any]] = []
    reason_counts: Counter[str] = Counter()
    entity_claims_checked = 0

    for claim in claims:
        if not _is_entity_presence_claim(claim):
            continue
        entity_claims_checked += 1
        reasons = quality_reasons_for_entity_subject(claim.get("subject"), preserve_entity_allowlist_normalized)
        if reasons:
            flags.append(_flag_for(claim, reasons))
            reason_counts.update(reasons)

    with flags_path.open("w", encoding="utf-8") as handle:
        for flag in flags:
            handle.write(json.dumps(flag, ensure_ascii=False, sort_keys=True) + "\n")

    manifest: dict[str, Any] = {
        "contract": "engain.mrlore_entity_candidate_quality_gate.v2",
        "run_timestamp": datetime.now(timezone.utc).isoformat(),
        "source_proposed_claims_jsonl": str(claims_file),
        "quality_flags_jsonl_path": str(flags_path),
        "manifest_path": str(manifest_path),
        "preserve_entity_allowlist_registry_path": str(registry_path),
        "preserve_entity_allowlist_registry_gate_manifest": str(registry_gate_manifest_path),
        "MRLORE_ENTITY_CANDIDATE_QUALITY_GATE_COMPLETE": len(read_errors) == 0,
        "QUALITY_GATE_CAN_CONSUME": True,
        "PROPOSED_CLAIMS_READ": len(claims),
        "ENTITY_PRESENCE_CLAIMS_CHECKED": entity_claims_checked,
        "QUALITY_FLAGS_WRITTEN": len(flags),
        "SIDE_CAR_FLAGS_ONLY": True,
        "PROPOSED_CLAIMS_ALTERED": False,
        "CLAIMS_REJECTED": False,
        "CLAIMS_PROMOTED": False,
        "CONTRADICTIONS_RESOLVED": False,
        "CANON_WRITTEN": False,
        "RUNTIME_TOUCHED": False,
        "GODOT_TOUCHED": False,
        "ZONJ_COMPILED": False,
        "ACCEPTED_LORE_PACKET_EXISTS": False,
        "quality_reason_counts": {key: reason_counts[key] for key in sorted(reason_counts)},
        "preserve_entity_allowlist_terms_loaded": len(preserve_entity_allowlist_normalized),
        "read_errors_count": len(read_errors),
        "read_errors": read_errors[:100],
        "errors": ["proposed_claims JSONL had read errors"] if read_errors else [],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="MrLore entity candidate quality gate — sidecar flags only.")
    parser.add_argument("--claims", default=None, help="Path to proposed_claims.jsonl.")
    parser.add_argument("--manifest", default=None, help="Path to engain_manifest.json.")
    parser.add_argument("--engain-dir", default=None, help="Direct path to vault/.engain.")
    args = parser.parse_args()

    try:
        manifest_path = Path(args.manifest) if args.manifest else None
        engain_dir = Path(args.engain_dir) if args.engain_dir else None
        claims_path = Path(args.claims) if args.claims else default_claims_path(manifest_path, engain_dir)
        manifest = run_entity_candidate_quality_gate(claims_path)
    except Exception as exc:
        print(f"[ENTITY_CANDIDATE_QUALITY_GATE] ERROR: {exc}", file=sys.stderr)
        return 1

    print(
        "[ENTITY_CANDIDATE_QUALITY_GATE] "
        f"MRLORE_ENTITY_CANDIDATE_QUALITY_GATE_COMPLETE={manifest['MRLORE_ENTITY_CANDIDATE_QUALITY_GATE_COMPLETE']}"
    )
    print(f"[ENTITY_CANDIDATE_QUALITY_GATE] PROPOSED_CLAIMS_READ={manifest['PROPOSED_CLAIMS_READ']}")
    print(
        "[ENTITY_CANDIDATE_QUALITY_GATE] "
        f"ENTITY_PRESENCE_CLAIMS_CHECKED={manifest['ENTITY_PRESENCE_CLAIMS_CHECKED']}"
    )
    print(f"[ENTITY_CANDIDATE_QUALITY_GATE] QUALITY_FLAGS_WRITTEN={manifest['QUALITY_FLAGS_WRITTEN']}")
    print(f"[ENTITY_CANDIDATE_QUALITY_GATE] SIDE_CAR_FLAGS_ONLY={manifest['SIDE_CAR_FLAGS_ONLY']}")
    print(f"[ENTITY_CANDIDATE_QUALITY_GATE] PROPOSED_CLAIMS_ALTERED={manifest['PROPOSED_CLAIMS_ALTERED']}")
    print(f"[ENTITY_CANDIDATE_QUALITY_GATE] CLAIMS_REJECTED={manifest['CLAIMS_REJECTED']}")
    print(f"[ENTITY_CANDIDATE_QUALITY_GATE] CLAIMS_PROMOTED={manifest['CLAIMS_PROMOTED']}")
    print(f"[ENTITY_CANDIDATE_QUALITY_GATE] CANON_WRITTEN={manifest['CANON_WRITTEN']}")
    print(f"[ENTITY_CANDIDATE_QUALITY_GATE] CONTRADICTIONS_RESOLVED={manifest['CONTRADICTIONS_RESOLVED']}")
    print(f"[ENTITY_CANDIDATE_QUALITY_GATE] RUNTIME_TOUCHED={manifest['RUNTIME_TOUCHED']}")
    print(f"[ENTITY_CANDIDATE_QUALITY_GATE] GODOT_TOUCHED={manifest['GODOT_TOUCHED']}")
    print(f"[ENTITY_CANDIDATE_QUALITY_GATE] ZONJ_COMPILED={manifest['ZONJ_COMPILED']}")
    print(f"[ENTITY_CANDIDATE_QUALITY_GATE] FLAGS={manifest['quality_flags_jsonl_path']}")
    print(f"[ENTITY_CANDIDATE_QUALITY_GATE] MANIFEST={manifest['manifest_path']}")
    return 0 if manifest["MRLORE_ENTITY_CANDIDATE_QUALITY_GATE_COMPLETE"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
