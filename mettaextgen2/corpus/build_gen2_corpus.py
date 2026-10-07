#!/usr/bin/env python3
"""Build / check the frozen Mettaext Gen2 hard-passage regression corpus.

One corpus for the whole manuscript. Cases are added when a source exposes a
new failure mode; the case id prefix names the source that supplied it
(e.g. B09-13). The builder has no notion of "book": it resolves
(source key, file, line range) references and freezes the excerpts.

Scope is deliberately narrow:

    sources + case spec  ->  verbatim excerpts + provenance + spec expectations

This tool never interprets text. Expectations (constraints, non-results,
review state) are hand-authored in gen2_cases_v1.json and copied through
unchanged. The only structural parsing is yaml.safe_load of fenced ```yaml
blocks inside AUTHOR_METADATA spans, so metadata reaches Gen2 as structure
rather than as prose.

Freezing:
  * every referenced source file is pinned by sha256 (spec `sources`);
  * every case must contain its `anchor` text (guards line drift);
  * the excerpt set is pinned by `frozen_passages_sha256` in the spec.
Expectations and review state may change without unfreezing. Changing or
adding excerpts changes the fingerprint and requires a deliberate re-pin
(new corpus_version when existing excerpts change).

Usage:
    python3 build_gen2_corpus.py           # (re)write gen2_hard_passages_v1.json
    python3 build_gen2_corpus.py --check   # exit 1 if the file on disk is stale
    python3 build_gen2_corpus.py --print-fingerprint

A source root can be overridden per key with METTAEXT_GEN2_SOURCE_ROOT_<KEY>
(e.g. METTAEXT_GEN2_SOURCE_ROOT_B09).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
SPEC_PATH = HERE / "gen2_cases_v1.json"
OUT_PATH = HERE / "gen2_hard_passages_v1.json"

EVIDENCE_CLASSES = {"PROSE", "AUTHOR_METADATA"}
CONSTRAINT_KEYS = {
    "entities", "items", "locations", "aliases", "coreference", "item_transfers",
    "relations", "movement", "speech", "metadata_presence", "continuity_flags",
    "events", "scene_assignment", "spatial_signals", "distance_cues", "temporal",
    "affect_cues", "terrain_cues",
}
NON_RESULT_KEYS = {
    "must_not_create_entity", "must_not_create_item", "must_not_create_location",
    "must_not_alias", "must_not_globalize_alias", "must_not_resolve",
    "must_not_emit_transfer", "must_not_emit_movement", "must_not_mark_present",
    "must_not_split_entity", "must_not_infer_state", "must_not_treat_as_fact",
    "must_not_treat_as_dialogue",
    # contract-derived (METTAEXT_TIER3_PARSE_AUTHORITY_CONTRACT_v1 §6, lane ownership)
    "must_not_emit_position", "must_not_emit_affect_state", "must_not_emit_terrain_profile",
    "must_not_claim_canon", "must_not_invent_scene_id", "must_not_mint_canonical_id",
}
REVIEW_STATUSES = {"DRAFT_UNREVIEWED", "REVIEWED", "DISPUTED"}
CASE_KEYS = {
    "id", "spans", "anchor", "evidence_classes_present", "problem_being_tested",
    "expected_constraints", "expected_non_results", "notes", "review",
}
SPAN_KEYS = {"source", "file", "line_start", "line_end"}
CASE_ID = re.compile(r"^([A-Z][A-Z0-9]*)-(\d+)$")
YAML_FENCE = re.compile(r"^```yaml[ \t]*\n(.*?)^```[ \t]*$", re.MULTILINE | re.DOTALL)


class SpecError(ValueError):
    pass


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_spec(spec: dict) -> None:
    for key in ("corpus_id", "corpus_version", "sources", "cases"):
        if key not in spec:
            raise SpecError(f"spec missing top-level key: {key}")
    for skey, source in spec["sources"].items():
        if not CASE_ID.match(f"{skey}-0"):
            raise SpecError(f"source key must be uppercase alphanumeric: {skey!r}")
        for key in ("root", "files"):
            if key not in source:
                raise SpecError(f"source {skey} missing {key!r}")
        for fname, meta in source["files"].items():
            if "sha256" not in meta:
                raise SpecError(f"source {skey}: {fname} has no sha256 pin")

    bad_g = set(spec.get("global_expected_non_results", {})) - NON_RESULT_KEYS
    if bad_g:
        raise SpecError(f"unknown global_expected_non_results keys {sorted(bad_g)}")

    seen_ids: set[str] = set()
    seen_numbers: set[int] = set()
    for case in spec["cases"]:
        cid = case.get("id", "<no id>")
        missing = CASE_KEYS - case.keys()
        extra = case.keys() - CASE_KEYS
        if missing or extra:
            raise SpecError(f"{cid}: missing keys {sorted(missing)}, unknown keys {sorted(extra)}")
        m = CASE_ID.match(cid)
        if not m:
            raise SpecError(f"{cid}: id must look like <SOURCEKEY>-<number>")
        prefix, number = m.group(1), int(m.group(2))
        if prefix not in spec["sources"]:
            raise SpecError(f"{cid}: id prefix {prefix!r} is not a declared source")
        if cid in seen_ids or number in seen_numbers:
            raise SpecError(f"{cid}: duplicate case id or case number (numbers are corpus-global)")
        seen_ids.add(cid)
        seen_numbers.add(number)

        if not case["spans"]:
            raise SpecError(f"{cid}: no spans")
        for span in case["spans"]:
            if span.keys() != SPAN_KEYS:
                raise SpecError(f"{cid}: span keys must be {sorted(SPAN_KEYS)}")
            source = spec["sources"].get(span["source"])
            if source is None:
                raise SpecError(f"{cid}: unknown span source {span['source']!r}")
            if span["file"] not in source["files"]:
                raise SpecError(f"{cid}: {span['source']}/{span['file']} is not pinned")

        bad_ev = set(case["evidence_classes_present"]) - EVIDENCE_CLASSES
        if bad_ev or not case["evidence_classes_present"]:
            raise SpecError(f"{cid}: invalid evidence_classes_present {sorted(bad_ev)}")
        bad_c = case["expected_constraints"].keys() - CONSTRAINT_KEYS
        if bad_c:
            raise SpecError(f"{cid}: unknown expected_constraints keys {sorted(bad_c)}")
        bad_n = case["expected_non_results"].keys() - NON_RESULT_KEYS
        if bad_n:
            raise SpecError(f"{cid}: unknown expected_non_results keys {sorted(bad_n)}")
        if case["review"].get("status") not in REVIEW_STATUSES:
            raise SpecError(f"{cid}: review.status must be one of {sorted(REVIEW_STATUSES)}")


def _source_root(skey: str, source: dict) -> Path:
    return Path(os.environ.get(f"METTAEXT_GEN2_SOURCE_ROOT_{skey}", source["root"]))


def load_sources(spec: dict) -> dict[tuple[str, str], list[str]]:
    """Read and hash-check every file referenced by at least one case."""
    referenced = {(s["source"], s["file"]) for c in spec["cases"] for s in c["spans"]}
    lines: dict[tuple[str, str], list[str]] = {}
    errors = []
    for skey, fname in sorted(referenced):
        source = spec["sources"][skey]
        path = _source_root(skey, source) / fname
        if not path.is_file():
            errors.append(f"missing source: {skey}/{fname} ({path})")
            continue
        raw = path.read_bytes()
        if _sha256_bytes(raw) != source["files"][fname]["sha256"]:
            errors.append(f"source changed since freeze: {skey}/{fname}")
            continue
        lines[(skey, fname)] = raw.decode("utf-8").splitlines()
    if errors:
        raise SpecError("; ".join(errors))
    return lines


def _parse_metadata_blocks(cid: str, text: str) -> list:
    blocks = YAML_FENCE.findall(text)
    if not blocks:
        raise SpecError(f"{cid}: AUTHOR_METADATA case contains no fenced yaml block")
    parsed = []
    for body in blocks:
        try:
            parsed.append(yaml.safe_load(body))
        except yaml.YAMLError as exc:
            raise SpecError(f"{cid}: metadata yaml does not parse: {exc}") from exc
    return parsed


def build(spec: dict, lines: dict[tuple[str, str], list[str]]) -> dict:
    passages = []
    for case in spec["cases"]:
        cid = case["id"]
        spans = []
        for span in case["spans"]:
            skey, fname = span["source"], span["file"]
            first, last = span["line_start"], span["line_end"]
            flines = lines[(skey, fname)]
            if not (1 <= first <= last <= len(flines)):
                raise SpecError(f"{cid}: span {skey}/{fname}:{first}-{last} out of range")
            source = spec["sources"][skey]
            fmeta = source["files"][fname]
            spans.append({
                "source": skey,
                "source_book": source.get("book"),
                "source_chapter": fmeta.get("chapter"),
                "file": fname,
                "source_sha256": fmeta["sha256"],
                "line_start": first,
                "line_end": last,
                "text": "\n".join(flines[first - 1:last]),
            })
        if not any(case["anchor"] in s["text"] for s in spans):
            raise SpecError(f"{cid}: anchor not found in excerpt: {case['anchor']!r}")

        record = {
            "id": cid,
            "origin_source": CASE_ID.match(cid).group(1),
            "source_anchor": case["anchor"],
            "spans": spans,
            "evidence_classes_present": case["evidence_classes_present"],
            "problem_being_tested": case["problem_being_tested"],
            "expected_constraints": case["expected_constraints"],
            "expected_non_results": case["expected_non_results"],
            "notes": case["notes"],
            "review": case["review"],
        }
        if "AUTHOR_METADATA" in case["evidence_classes_present"]:
            record["structured_metta_blocks"] = _parse_metadata_blocks(
                cid, "\n".join(s["text"] for s in spans)
            )
        passages.append(record)

    return {
        "corpus_id": spec["corpus_id"],
        "corpus_version": spec["corpus_version"],
        "generated_by": "mettaextgen2/corpus/build_gen2_corpus.py",
        "generated_from": SPEC_PATH.name,
        "sources": {k: {"book": v.get("book"), "title": v.get("title"), "root": v["root"]}
                    for k, v in spec["sources"].items()},
        "frozen_passages_sha256": passages_fingerprint(passages),
        "scoring_policy": "Extractors are scored only against cases whose review.status is REVIEWED.",
        "global_expected_non_results": spec.get("global_expected_non_results", {}),
        "passages": passages,
    }


def passages_fingerprint(passages: list[dict]) -> str:
    excerpt_set = [
        {"id": p["id"],
         "spans": [(s["source"], s["file"], s["line_start"], s["line_end"], s["text"])
                   for s in p["spans"]]}
        for p in passages
    ]
    blob = json.dumps(excerpt_set, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return _sha256_bytes(blob)


def render(corpus: dict) -> str:
    return json.dumps(corpus, ensure_ascii=False, indent=2) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="exit 1 if the corpus on disk is stale")
    mode.add_argument("--print-fingerprint", action="store_true",
                      help="print the excerpt-set fingerprint (used when re-pinning)")
    args = parser.parse_args()

    try:
        spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
        validate_spec(spec)
        corpus = build(spec, load_sources(spec))
    except SpecError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.print_fingerprint:
        print(corpus["frozen_passages_sha256"])
        return 0

    pinned = spec.get("frozen_passages_sha256")
    if not pinned:
        print("ERROR: spec has no frozen_passages_sha256; run --print-fingerprint and pin it.",
              file=sys.stderr)
        return 2
    if pinned != corpus["frozen_passages_sha256"]:
        print("ERROR: excerpt set differs from the frozen fingerprint. Spans, cases or source "
              "text changed; re-pin deliberately (new corpus_version if existing excerpts changed).",
              file=sys.stderr)
        return 2

    rendered = render(corpus)
    if args.check:
        if not OUT_PATH.is_file() or OUT_PATH.read_text(encoding="utf-8") != rendered:
            print(f"STALE: {OUT_PATH.name} does not match spec + sources; rebuild it.", file=sys.stderr)
            return 1
        print(f"OK: {len(corpus['passages'])} passages, fingerprint {pinned[:16]}…")
        return 0

    OUT_PATH.write_text(rendered, encoding="utf-8")
    print(f"wrote {OUT_PATH.name} ({len(corpus['passages'])} passages)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
