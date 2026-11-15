#!/usr/bin/env python3
"""
mrlore_cosmic_year_context_enrichment.py — attach Coming/CY context to temporal claim copies.

Reads proposed_claims.temporal_enriched.jsonl plus the author-declared Coming
calendar registry, then writes a new derived proposed_claims.cosmic_enriched.jsonl.
This is temporal context only: no canon writes, claim promotion/rejection,
contradiction resolution, runtime/Godot/ZONJ effects, or source mutation.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

COSMIC_CONTEXT_BASIS = "COMING_CALENDAR_REGISTRY"
UNRESOLVED_COSMIC_CONTEXT_BASIS = "UNRESOLVED_COMING_CALENDAR_REGISTRY"


@dataclass(frozen=True)
class ChapterRef:
    book: int
    chapter: int


@dataclass(frozen=True)
class ComingManifestationContext:
    coming_id: str
    coming_number: int
    cosmic_year_start: int
    shared_event_id: str
    region: str
    regional_name: str
    cosmic_year_end: int | None = None
    cosmic_year_start_approx: bool = False
    cosmic_year_end_approx: bool = False


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


def _infer_engain_dir_from_claims_path(claims_path: Path) -> Path:
    resolved = claims_path.resolve()
    if len(resolved.parents) >= 3 and resolved.parent.name == "claims" and resolved.parent.parent.name == "mrlore":
        return resolved.parent.parent.parent
    return resolved.parent.parent.parent


def _manifest_path_for_claims(claims_path: Path) -> Path:
    return _infer_engain_dir_from_claims_path(claims_path) / "manifests" / "mrlore_cosmic_year_context_manifest.json"


def _read_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                record = json.loads(stripped)
            except json.JSONDecodeError as exc:
                errors.append(f"line {line_number}: invalid JSON claim record: {exc}")
                continue
            if not isinstance(record, dict):
                errors.append(f"line {line_number}: claim record is not a JSON object")
                continue
            records.append(record)
    return records, errors


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records), encoding="utf-8")


def _write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    manifest["errors_count"] = len(manifest.get("errors", []))
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _base_manifest() -> dict[str, Any]:
    return {
        "contract": "engain.mrlore_cosmic_year_context_manifest.v1",
        "run_timestamp": datetime.now(timezone.utc).isoformat(),
        "MRLORE_COSMIC_YEAR_CONTEXT_ENRICHMENT_COMPLETE": False,
        "CLAIMS_READ": 0,
        "CLAIMS_WRITTEN": 0,
        "CLAIMS_COSMIC_ENRICHED": 0,
        "CLAIMS_COSMIC_UNRESOLVED": 0,
        "COMING_REGISTRY_READ": False,
        "COMING_CONTEXTS_LOADED": 0,
        "COSMIC_CONTEXT_BASIS": COSMIC_CONTEXT_BASIS,
        "ENGINE_AGNOSTIC": True,
        "CLAIMS_ALTERED": False,
        "TEMPORAL_CLAIMS_ALTERED": False,
        "COMING_REGISTRY_ALTERED": False,
        "CANDIDATES_ALTERED": False,
        "QUEUES_ALTERED": False,
        "CLAIMS_PROMOTED": False,
        "CLAIMS_REJECTED": False,
        "CONTRADICTIONS_RESOLVED": False,
        "CANON_WRITTEN": False,
        "RUNTIME_TOUCHED": False,
        "GODOT_TOUCHED": False,
        "ZONJ_COMPILED": False,
        "errors": [],
        "errors_count": 0,
    }


def _parse_chapter_ref(value: Any) -> ChapterRef | None:
    if not isinstance(value, str):
        return None
    # Supports chapter.book020.105_garden_grove and compact B20.C105 forms.
    patterns = (
        r"chapter\.book0*(?P<book>\d+)\.0*(?P<chapter>\d+)(?:_|$)",
        r"book0*(?P<book>\d+)\.0*(?P<chapter>\d+)(?:_|$)",
        r"B0*(?P<book>\d+)\.C0*(?P<chapter>\d+)$",
    )
    for pattern in patterns:
        match = re.search(pattern, value, re.IGNORECASE)
        if match:
            return ChapterRef(book=int(match.group("book")), chapter=int(match.group("chapter")))
    return None


def _parse_range(value: Any) -> tuple[ChapterRef, ChapterRef] | None:
    if not isinstance(value, str) or not value.strip():
        return None
    cleaned = value.strip()
    if "-" not in cleaned:
        ref = _parse_chapter_ref(cleaned)
        return (ref, ref) if ref else None
    left, right = cleaned.split("-", 1)
    start = _parse_chapter_ref(left.strip())
    end = _parse_chapter_ref(right.strip())
    if start is None:
        return None
    if end is None:
        # Accept compact same-book suffix ranges such as B3.C10-C15.
        suffix = re.fullmatch(r"C0*(\d+)", right.strip(), re.IGNORECASE)
        if suffix:
            end = ChapterRef(book=start.book, chapter=int(suffix.group(1)))
    if end is None:
        return None
    return start, end


def _contains_chapter(chapter: ChapterRef, start: ChapterRef, end: ChapterRef) -> bool:
    if chapter.book != start.book or chapter.book != end.book:
        return False
    low = min(start.chapter, end.chapter)
    high = max(start.chapter, end.chapter)
    return low <= chapter.chapter <= high


def _build_coming_contexts(registry: dict[str, Any]) -> tuple[list[tuple[tuple[ChapterRef, ChapterRef], ComingManifestationContext]], list[str]]:
    contexts: list[tuple[tuple[ChapterRef, ChapterRef], ComingManifestationContext]] = []
    errors: list[str] = []
    comings = registry.get("comings", [])
    if not isinstance(comings, list):
        return contexts, ["coming calendar registry comings is not a list"]
    for coming_index, coming in enumerate(comings, 1):
        if not isinstance(coming, dict):
            errors.append(f"coming entry {coming_index} is not an object")
            continue
        coming_id = coming.get("coming_id")
        coming_number = coming.get("coming_number")
        cosmic_year_start = coming.get("cosmic_year_start")
        shared_event_id = coming.get("shared_event_id")
        if not isinstance(coming_id, str) or not isinstance(coming_number, int) or not isinstance(cosmic_year_start, int) or not isinstance(shared_event_id, str):
            errors.append(f"coming entry {coming_index} missing valid coming_id/coming_number/cosmic_year_start/shared_event_id")
            continue
        manifestations = coming.get("regional_manifestations", [])
        if not isinstance(manifestations, list):
            errors.append(f"coming {coming_id} regional_manifestations is not a list")
            continue
        for manifestation_index, manifestation in enumerate(manifestations, 1):
            if not isinstance(manifestation, dict):
                errors.append(f"coming {coming_id} manifestation {manifestation_index} is not an object")
                continue
            region = manifestation.get("region")
            regional_name = manifestation.get("regional_name")
            if not isinstance(region, str) or not isinstance(regional_name, str):
                errors.append(f"coming {coming_id} manifestation {manifestation_index} missing region/regional_name")
                continue
            excluded_refs = {
                ref
                for excluded in manifestation.get("excluded_chapters", [])
                if (ref := _parse_chapter_ref(excluded)) is not None
            }
            chapter_ranges = manifestation.get("manuscript_chapter_ranges", [])
            if not isinstance(chapter_ranges, list):
                errors.append(f"coming {coming_id} manifestation {manifestation_index} manuscript_chapter_ranges is not a list")
                continue
            context = ComingManifestationContext(
                coming_id=coming_id,
                coming_number=coming_number,
                cosmic_year_start=cosmic_year_start,
                cosmic_year_end=coming.get("cosmic_year_end") if isinstance(coming.get("cosmic_year_end"), int) else None,
                cosmic_year_start_approx=coming.get("cosmic_year_start_approx") is True,
                cosmic_year_end_approx=coming.get("cosmic_year_end_approx") is True,
                shared_event_id=shared_event_id,
                region=region,
                regional_name=regional_name,
            )
            for raw_range in chapter_ranges:
                parsed_range = _parse_range(raw_range)
                if parsed_range is None:
                    errors.append(f"coming {coming_id} has unparseable chapter range: {raw_range!r}")
                    continue
                start, end = parsed_range
                # Represent single excluded chapters by omitting that exact range only when range is a singleton.
                # Multi-chapter ranges keep the range and exclusion is checked during lookup.
                contexts.append(((start, end), context))
            if excluded_refs:
                # Store excluded refs on context through a private side table by duplicating impossible negative ranges is messy;
                # lookup recomputes exclusions from registry via a separate table below.
                pass
    return contexts, errors


def _build_exclusions(registry: dict[str, Any]) -> dict[tuple[str, str], set[ChapterRef]]:
    exclusions: dict[tuple[str, str], set[ChapterRef]] = {}
    comings = registry.get("comings", [])
    if not isinstance(comings, list):
        return exclusions
    for coming in comings:
        if not isinstance(coming, dict):
            continue
        coming_id = coming.get("coming_id")
        manifestations = coming.get("regional_manifestations", [])
        if not isinstance(coming_id, str) or not isinstance(manifestations, list):
            continue
        for manifestation in manifestations:
            if not isinstance(manifestation, dict):
                continue
            region = manifestation.get("region")
            if not isinstance(region, str):
                continue
            refs: set[ChapterRef] = set()
            for raw in manifestation.get("excluded_chapters", []):
                ref = _parse_chapter_ref(raw)
                if ref is not None:
                    refs.add(ref)
            if refs:
                exclusions[(coming_id, region)] = refs
    return exclusions


def _lookup_context(
    chapter_id: Any,
    contexts: list[tuple[tuple[ChapterRef, ChapterRef], ComingManifestationContext]],
    exclusions: dict[tuple[str, str], set[ChapterRef]],
) -> ComingManifestationContext | None:
    chapter_ref = _parse_chapter_ref(chapter_id)
    if chapter_ref is None:
        return None
    for (start, end), context in contexts:
        if not _contains_chapter(chapter_ref, start, end):
            continue
        if chapter_ref in exclusions.get((context.coming_id, context.region), set()):
            continue
        return context
    return None


def _enrich_claim(
    claim: dict[str, Any],
    contexts: list[tuple[tuple[ChapterRef, ChapterRef], ComingManifestationContext]],
    exclusions: dict[tuple[str, str], set[ChapterRef]],
) -> tuple[dict[str, Any], bool]:
    enriched = dict(claim)
    context = _lookup_context(claim.get("chapter_id"), contexts, exclusions)
    if context is None:
        enriched["cosmic_context_basis"] = UNRESOLVED_COSMIC_CONTEXT_BASIS
        return enriched, False
    enriched.update(
        {
            "coming_id": context.coming_id,
            "coming_number": context.coming_number,
            "cosmic_year_start": context.cosmic_year_start,
            "shared_event_id": context.shared_event_id,
            "region": context.region,
            "regional_name": context.regional_name,
            "cosmic_context_basis": COSMIC_CONTEXT_BASIS,
        }
    )
    if context.cosmic_year_end is not None:
        enriched["cosmic_year_end"] = context.cosmic_year_end
    if context.cosmic_year_start_approx:
        enriched["cosmic_year_start_approx"] = True
    if context.cosmic_year_end_approx:
        enriched["cosmic_year_end_approx"] = True
    return enriched, True


def run_cosmic_year_context_enrichment(
    temporal_claims_path: Path | str,
    coming_registry_path: Path | str,
    output_path: Path | str | None = None,
    manifest_path: Path | str | None = None,
) -> dict[str, Any]:
    temporal_claims_path = Path(temporal_claims_path)
    coming_registry_path = Path(coming_registry_path)
    output_path = Path(output_path) if output_path else temporal_claims_path.with_name("proposed_claims.cosmic_enriched.jsonl")
    manifest_path = Path(manifest_path) if manifest_path else _manifest_path_for_claims(temporal_claims_path)

    manifest = _base_manifest()
    manifest["source_temporal_claims_path"] = str(temporal_claims_path)
    manifest["coming_registry_path"] = str(coming_registry_path)
    manifest["output_path"] = str(output_path)

    if not temporal_claims_path.exists():
        manifest["errors"].append(f"temporal-enriched claims file not found: {temporal_claims_path}")
        _write_manifest(manifest_path, manifest)
        raise FileNotFoundError(f"temporal-enriched claims file not found: {temporal_claims_path}")
    if not coming_registry_path.exists():
        manifest["errors"].append(f"Coming calendar registry not found: {coming_registry_path}")
        _write_manifest(manifest_path, manifest)
        raise FileNotFoundError(f"Coming calendar registry not found: {coming_registry_path}")

    claims, read_errors = _read_jsonl(temporal_claims_path)
    manifest["CLAIMS_READ"] = len(claims)
    manifest["errors"].extend(read_errors)

    try:
        registry = json.loads(coming_registry_path.read_text(encoding="utf-8"))
    except Exception as exc:
        manifest["errors"].append(f"failed to parse Coming calendar registry: {exc}")
        _write_manifest(manifest_path, manifest)
        raise
    if not isinstance(registry, dict):
        manifest["errors"].append("Coming calendar registry root is not an object")
        _write_manifest(manifest_path, manifest)
        raise ValueError("Coming calendar registry root is not an object")
    manifest["COMING_REGISTRY_READ"] = True

    contexts, context_errors = _build_coming_contexts(registry)
    exclusions = _build_exclusions(registry)
    manifest["COMING_CONTEXTS_LOADED"] = len(contexts)
    manifest["errors"].extend(context_errors)

    enriched_claims: list[dict[str, Any]] = []
    enriched_count = 0
    unresolved_count = 0
    for claim in claims:
        enriched_claim, resolved = _enrich_claim(claim, contexts, exclusions)
        enriched_claims.append(enriched_claim)
        if resolved:
            enriched_count += 1
        else:
            unresolved_count += 1

    _write_jsonl(output_path, enriched_claims)
    manifest["CLAIMS_WRITTEN"] = len(enriched_claims)
    manifest["CLAIMS_COSMIC_ENRICHED"] = enriched_count
    manifest["CLAIMS_COSMIC_UNRESOLVED"] = unresolved_count
    manifest["MRLORE_COSMIC_YEAR_CONTEXT_ENRICHMENT_COMPLETE"] = len(read_errors) == 0 and manifest["COMING_REGISTRY_READ"] is True
    _write_manifest(manifest_path, manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Enrich temporal MrLore proposed claim copies with Coming/CY context.")
    parser.add_argument("--manifest", default=None, help="Path to engain_manifest.json for active .engain discovery.")
    parser.add_argument("--engain-dir", default=None, help="Direct path to vault/.engain (overrides --manifest).")
    parser.add_argument("--claims", default=None, help="Path to proposed_claims.temporal_enriched.jsonl.")
    parser.add_argument("--coming-registry", default=None, help="Path to coming_calendar.json.")
    parser.add_argument("--output", default=None, help="Path for proposed_claims.cosmic_enriched.jsonl.")
    args = parser.parse_args()

    try:
        if args.engain_dir:
            engain_dir = Path(args.engain_dir).resolve()
        else:
            manifest_path = Path(args.manifest) if args.manifest else _default_manifest_path()
            engain_dir = _resolve_engain_dir(manifest_path)

        claims_path = Path(args.claims).resolve() if args.claims else engain_dir / "mrlore" / "claims" / "proposed_claims.temporal_enriched.jsonl"
        coming_registry_path = (
            Path(args.coming_registry).resolve()
            if args.coming_registry
            else engain_dir / "mrlore" / "timeline" / "coming_calendar.json"
        )
        output_path = Path(args.output).resolve() if args.output else None
        manifest = run_cosmic_year_context_enrichment(claims_path, coming_registry_path, output_path=output_path)
    except Exception as exc:
        print(f"[COSMIC_YEAR_CONTEXT] ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"MRLORE_COSMIC_YEAR_CONTEXT_ENRICHMENT_COMPLETE={manifest['MRLORE_COSMIC_YEAR_CONTEXT_ENRICHMENT_COMPLETE']}")
    print(f"CLAIMS_READ={manifest['CLAIMS_READ']}")
    print(f"CLAIMS_WRITTEN={manifest['CLAIMS_WRITTEN']}")
    print(f"CLAIMS_COSMIC_ENRICHED={manifest['CLAIMS_COSMIC_ENRICHED']}")
    print(f"CLAIMS_COSMIC_UNRESOLVED={manifest['CLAIMS_COSMIC_UNRESOLVED']}")
    print(f"COMING_REGISTRY_READ={manifest['COMING_REGISTRY_READ']}")
    print(f"COMING_CONTEXTS_LOADED={manifest['COMING_CONTEXTS_LOADED']}")
    print(f"COSMIC_CONTEXT_BASIS={manifest['COSMIC_CONTEXT_BASIS']}")
    print(f"ENGINE_AGNOSTIC={manifest['ENGINE_AGNOSTIC']}")
    print(f"CLAIMS_ALTERED={manifest['CLAIMS_ALTERED']}")
    print(f"TEMPORAL_CLAIMS_ALTERED={manifest['TEMPORAL_CLAIMS_ALTERED']}")
    print(f"COMING_REGISTRY_ALTERED={manifest['COMING_REGISTRY_ALTERED']}")
    print(f"CANDIDATES_ALTERED={manifest['CANDIDATES_ALTERED']}")
    print(f"QUEUES_ALTERED={manifest['QUEUES_ALTERED']}")
    print(f"CLAIMS_PROMOTED={manifest['CLAIMS_PROMOTED']}")
    print(f"CLAIMS_REJECTED={manifest['CLAIMS_REJECTED']}")
    print(f"CONTRADICTIONS_RESOLVED={manifest['CONTRADICTIONS_RESOLVED']}")
    print(f"CANON_WRITTEN={manifest['CANON_WRITTEN']}")
    print(f"RUNTIME_TOUCHED={manifest['RUNTIME_TOUCHED']}")
    print(f"GODOT_TOUCHED={manifest['GODOT_TOUCHED']}")
    print(f"ZONJ_COMPILED={manifest['ZONJ_COMPILED']}")
    print(f"errors_count={manifest['errors_count']}")
    return 0 if manifest["MRLORE_COSMIC_YEAR_CONTEXT_ENRICHMENT_COMPLETE"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
