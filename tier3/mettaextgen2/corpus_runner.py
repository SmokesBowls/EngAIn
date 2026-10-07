#!/usr/bin/env python3
"""Run Gen2 over the frozen hard-passage corpus and report failures.

Diagnostic, not a score: the corpus scoring policy counts only REVIEWED
cases, and expectations are draft gold until the author reviews them. Each
case's spans are mapped to the Chapterroom scene that contains them. Gen2 runs
on that scene, and only checks the implemented modules can be judged on are
evaluated, restricted to evidence inside the case's own lines. Every other
expectation is reported as not_evaluable, with the module that would own it.

Usage (repo root, PYTHONPATH=.):
  python3 -m tier3.mettaextgen2.corpus_runner [--corpus FILE] [--json]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from .lib.lane_line import find_forbidden
from .modules.source_loader import SourceLoadError
from .orchestrator import DEFAULT_CHAPTERROOM_ROOT, run_scene

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CORPUS = REPO_ROOT / "mettaextgen2" / "corpus" / "gen2_hard_passages_v1.json"

EVALUABLE_CONSTRAINTS = {"entities", "locations", "metadata_presence"}
EVALUABLE_NON_RESULTS = {"must_not_create_entity", "must_not_create_location", "must_not_mark_present"}
OWNER = {
    "aliases": "alias_resolver", "coreference": "coreference_linker", "item_transfers": "event_extractor",
    "events": "event_extractor", "relations": "event_extractor", "movement": "event_extractor",
    "speech": "dialogue_extractor", "spatial_signals": "spatial_cue_extractor",
    "distance_cues": "distance_cue_extractor", "temporal": "temporal_cue_extractor",
    "affect_cues": "affect_cue_extractor", "terrain_cues": "terrain_cue_extractor",
    "items": "entity_extractor (item typing)", "scene_assignment": "multi-scene spans",
    "continuity_flags": "reconciler (continuity)", "must_not_alias": "alias_resolver",
    "must_not_globalize_alias": "alias_resolver", "must_not_resolve": "alias_resolver/coreference_linker",
    "must_not_emit_transfer": "event_extractor", "must_not_emit_movement": "event_extractor",
    "must_not_split_entity": "coreference_linker", "must_not_infer_state": "reconciler (state)",
    "must_not_treat_as_fact": "temporal/metadata", "must_not_treat_as_dialogue": "dialogue_extractor",
    "must_not_create_item": "entity_extractor (item typing)", "must_not_invent_scene_id": "(global check)",
    "must_not_emit_position": "(global check)", "must_not_emit_affect_state": "(global check)",
}


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("’", "'")).strip().lower()


def _head(text: str) -> str:
    """Name key of an expectation: drop parenthetical notes and a leading article
    ('the Herald' -> 'herald'), since articles are never part of a Gen2 surface."""
    return re.sub(r"^(?:the|a|an) ", "", _norm(re.sub(r"\(.*?\)", "", text)))


def _names_match(expected: str, surface: str) -> bool:
    """Whole-name match: 'Mika' matches 'Mika' or 'Mika Covenant', never 'Red Mika'."""
    e, s = _head(expected), _head(surface)
    return s == e or s.startswith(e + " ")


@lru_cache(maxsize=None)
def _chapter_for(chapterroom_root: Path, source_file: str) -> Optional[str]:
    for path in sorted(chapterroom_root.glob("out_passA_*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("source_file") == source_file:
            return data["chapter_id"]
    return None


@lru_cache(maxsize=None)
def _scenes(chapterroom_root: Path, chapter_id: str) -> Tuple[Tuple[str, int, int], ...]:
    data = json.loads((chapterroom_root / f"out_passB_{chapter_id}.json").read_text(encoding="utf-8"))
    return tuple((s["scene_id"], s["boundary_start_line"], s["boundary_end_line"]) for s in data["scenes"])


_artifacts: Dict[Tuple[str, str], dict] = {}


def _artifact(chapterroom_root: Path, chapter_id: str, scene_id: str) -> dict:
    key = (chapter_id, scene_id)
    if key not in _artifacts:
        _artifacts[key] = run_scene(chapterroom_root, chapter_id, scene_id)
    return _artifacts[key]


def _in_lines(span: dict, first: int, last: int) -> bool:
    return first <= span["line"] <= last


def _declared_in(artifact: dict, first: int, last: int) -> List[dict]:
    items = []
    for section in ("declared_entities", "declared_locations"):
        for d in artifact[section]:
            spans = [d["source_span"]] + d["evidence"]
            if any(_in_lines(s, first, last) for s in spans):
                items.append({**d, "_section": section})
    for a in artifact["alias_candidates"]:
        if any(_in_lines(s, first, last) for s in a["evidence"]):
            target = next(e for e in artifact["declared_entities"] if e["local_ref"] == a["candidate_ref"])
            items.append({**target, "surface": a["surface"], "_section": "alias", "_target": target["surface"]})
    return items


def evaluate_case(case: dict, sources: dict, chapterroom_root: Path) -> dict:
    result = {"id": case["id"], "checks": [], "not_evaluable": [], "errors": []}
    declared: List[dict] = []
    artifacts = []
    for span in case["spans"]:
        root = sources[span["source"]]["root"]
        chapter_id = _chapter_for(chapterroom_root, str(Path(root) / span["file"]))
        if chapter_id is None:
            result["errors"].append(f"{span['source']}/{span['file']} not ingested by Chapterroom")
            continue
        scenes = [s for s in _scenes(chapterroom_root, chapter_id)
                  if s[1] <= span["line_start"] <= s[2]]
        if not scenes:
            result["errors"].append(f"no scene contains {span['file']}:{span['line_start']}")
            continue
        scene_id = scenes[0][0]
        try:
            artifact = _artifact(chapterroom_root, chapter_id, scene_id)
        except (SourceLoadError, RuntimeError) as exc:
            result["errors"].append(f"{scene_id}: {exc}")
            continue
        artifacts.append(artifact)
        for w in artifact["warnings"]:
            if w.startswith(("module_failed", "module_skipped")):
                result["errors"].append(f"{scene_id}: {w.splitlines()[0]}")
        declared.extend(_declared_in(artifact, span["line_start"], span["line_end"]))
    if not artifacts:
        return result

    accepted = [d for d in declared if d["status"] != "REJECTED"]

    def check(name: str, ok: bool, detail: str) -> None:
        result["checks"].append({"check": name, "ok": ok, "detail": detail})

    for name in case["expected_non_results"].get("must_not_create_entity", []):
        hits = [d["surface"] for d in accepted if _head(d["surface"]) == _head(name)]
        check(f"must_not_create_entity {name!r}", not hits, f"accepted as {hits}" if hits else "not accepted")
    for name in case["expected_non_results"].get("must_not_create_location", []):
        hits = [d["surface"] for d in declared if d["_section"] == "declared_locations" and _norm(d["surface"]) == _norm(name)]
        check(f"must_not_create_location {name!r}", not hits, f"declared {hits}" if hits else "not declared")
    for name in case["expected_non_results"].get("must_not_mark_present", []):
        hits = [d["surface"] for d in accepted if _names_match(name, d.get("_target", d["surface"])) and d.get("presence") == "present"]
        check(f"must_not_mark_present {name!r}", not hits, f"present: {hits}" if hits else "not present")

    for name in case["expected_constraints"].get("entities", {}):
        hits = [d["surface"] for d in accepted
                if _names_match(name, d["surface"]) or _names_match(name, d.get("_target", d["surface"]))]
        check(f"discover {name!r}", bool(hits), f"found {sorted(set(hits))}" if hits else "missing")
    for name in case["expected_constraints"].get("locations", []):
        hits = [d["surface"] for d in accepted if _head(d["surface"]) == _head(name)]
        check(f"location {name!r}", bool(hits), "found" if hits else "missing")
    for name, expected in case["expected_constraints"].get("metadata_presence", {}).items():
        want = "present" if expected.startswith("present") else ("absent" if expected.startswith("absent") else "referenced")
        hits = [d.get("presence") for d in accepted if _head(d["surface"]) == _head(name)]
        check(f"presence {name!r}={want}", want in hits, f"got {hits}")

    for artifact in artifacts:
        forbidden = find_forbidden(artifact)
        if forbidden:
            check("global lane line", False, ", ".join(forbidden))

    for key in case["expected_constraints"]:
        if key not in EVALUABLE_CONSTRAINTS:
            result["not_evaluable"].append(f"{key} ({OWNER.get(key, 'unowned')})")
    for key in case["expected_non_results"]:
        if key not in EVALUABLE_NON_RESULTS:
            result["not_evaluable"].append(f"{key} ({OWNER.get(key, 'unowned')})")
    return result


def run(corpus_path: Path, chapterroom_root: Path) -> List[dict]:
    corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
    sources = {k: v for k, v in corpus["sources"].items()}
    return [evaluate_case(case, sources, chapterroom_root) for case in corpus["passages"]]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--chapterroom-root", type=Path, default=DEFAULT_CHAPTERROOM_ROOT)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    results = run(args.corpus, args.chapterroom_root)
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return 0
    total = sum(len(r["checks"]) for r in results)
    failed = sum(1 for r in results for c in r["checks"] if not c["ok"])
    print("DIAGNOSTIC against DRAFT_UNREVIEWED gold, not a score.\n")
    for r in results:
        bad = [c for c in r["checks"] if not c["ok"]]
        status = "ERROR" if r["errors"] else ("FAIL" if bad else ("ok" if r["checks"] else "n/a"))
        print(f"{r['id']:7} {status:5} checks={len(r['checks'])} failed={len(bad)} not_evaluable={len(r['not_evaluable'])}")
        for e in r["errors"]:
            print(f"          error: {e}")
        for c in bad:
            print(f"          FAIL {c['check']}: {c['detail']}")
    print(f"\n{total - failed}/{total} evaluable checks passed; "
          f"{sum(len(r['not_evaluable']) for r in results)} expectations not evaluable yet.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
