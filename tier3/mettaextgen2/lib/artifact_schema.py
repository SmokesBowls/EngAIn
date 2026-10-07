"""Structural validator for `mettaext.parse_artifact.v2` (draft schema).

The schema is GEN2_OUTPUT_CONTRACT.md §4/§5a. This validator is the gate the
assembler applies before anything is emitted. EngAInOS intake would apply the
same checks. With `source_text`, every span is re-checked byte-for-byte
against the raw source.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Optional

from .lane_line import find_forbidden

CONTRACT = "mettaext.parse_artifact.v2"
ENTITY_STATUS = {"KNOWN", "OBSERVED", "CANDIDATE", "ALIAS_CANDIDATE", "REJECTED"}
PRESENCE = {"present", "referenced", "absent", "unknown"}
EVIDENCE_CLASS = {"PROSE", "AUTHOR_METADATA", "REGISTRY_PRIOR"}
METADATA_KINDS = {"assertion", "presence_qualifier", "editorial_placement", "unresolved_state", "non_inference"}
ALIAS_SCOPE = {"span", "scene", "chapter", "arc", "global"}
SPAN_KEYS = {"source_text_id", "file", "line", "char_start", "char_end", "text"}
LIST_SECTIONS = (
    "declared_entities", "declared_locations", "declared_events", "alias_candidates",
    "speech", "spatial_signals", "distance_cues", "temporal_cues", "affect_cues",
    "terrain_descriptions", "metadata_constraints", "continuity_flags", "challenges",
    "warnings", "canon_claims",
)
ENTITY_KEYS = {"local_ref", "surface", "entity_type", "status", "presence", "evidence_class",
               "source_span", "evidence", "confidence", "alternatives", "notes"}
LOCATION_KEYS = {"local_ref", "surface", "status", "evidence_class", "source_span", "evidence",
                 "confidence", "alternatives"}
_ENT_REF = re.compile(r"^ent_\d{3}$")
_LOC_REF = re.compile(r"^loc_\d{3}$")


class _Errors:
    def __init__(self) -> None:
        self.items: List[str] = []

    def add(self, path: str, msg: str) -> None:
        self.items.append(f"{path}: {msg}")


def _check_span(span: Any, path: str, artifact_id: str, source_text: Optional[str], err: _Errors) -> None:
    if not isinstance(span, dict) or set(span) != SPAN_KEYS:
        err.add(path, f"span must have exactly {sorted(SPAN_KEYS)}")
        return
    if span["source_text_id"] != artifact_id:
        err.add(path, "span source_text_id differs from artifact source_text_id")
    s, e = span["char_start"], span["char_end"]
    if not (isinstance(s, int) and isinstance(e, int) and 0 <= s < e):
        err.add(path, "invalid char offsets")
        return
    if not isinstance(span["text"], str) or not span["text"].strip():
        err.add(path, "span text empty")
    if source_text is not None:
        if e > len(source_text) or source_text[s:e] != span["text"]:
            err.add(path, "span text does not match raw source at offsets")
        elif source_text.count("\n", 0, s) + 1 != span["line"]:
            err.add(path, "span line does not match char_start")


def _check_conf(value: Any, path: str, err: _Errors) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not (0.0 <= value <= 1.0):
        err.add(path, "confidence must be a number in 0..1")


def _check_spans(items: Iterable[Any], path: str, artifact_id: str, source_text: Optional[str], err: _Errors) -> None:
    for i, sp in enumerate(items):
        _check_span(sp, f"{path}[{i}]", artifact_id, source_text, err)


def validate_parse_artifact_v2(artifact: Dict[str, Any], source_text: Optional[str] = None) -> List[str]:
    err = _Errors()
    for path in find_forbidden(artifact):
        err.add(path, "forbidden key (lane line / authority)")

    fixed = {"contract": CONTRACT, "source": "mettaext", "authority_lane": "prose_to_structure",
             "authority_tier": 3, "parse_stage": "gen2"}
    for key, expected in fixed.items():
        if artifact.get(key) != expected:
            err.add(f"$.{key}", f"must be {expected!r}")
    sid = artifact.get("source_text_id")
    if not isinstance(sid, str) or "@" not in sid:
        err.add("$.source_text_id", "required, '<file>@<sha256>'")
        sid = ""
    if not re.fullmatch(r"[0-9a-f]{64}", str(artifact.get("source_sha256", ""))):
        err.add("$.source_sha256", "required sha256 hex")
    elif not sid.endswith("@" + artifact["source_sha256"]):
        err.add("$.source_text_id", "must end with @source_sha256")

    scene = artifact.get("scene")
    if not isinstance(scene, dict):
        err.add("$.scene", "required object")
    else:
        for key in ("source_scene_label", "chapterroom_scene_id", "chapter_id", "boundary_method",
                    "authored_scene_boundaries_proven", "runtime_stage_id"):
            if key not in scene:
                err.add(f"$.scene.{key}", "required")
        if scene.get("runtime_stage_id") is not None:
            err.add("$.scene.runtime_stage_id", "must be null (set only at EngAInOS promotion)")
        if not isinstance(scene.get("chapterroom_scene_id"), str) or not str(scene.get("chapterroom_scene_id")).startswith("scene."):
            err.add("$.scene.chapterroom_scene_id", "must be the inherited Chapterroom scene id")

    run = artifact.get("run")
    if not isinstance(run, dict) or not run.get("run_id") or not isinstance(run.get("modules"), list):
        err.add("$.run", "requires run_id and modules[]")

    for section in LIST_SECTIONS:
        if not isinstance(artifact.get(section), list):
            err.add(f"$.{section}", "required list")
    if artifact.get("canon_claims") != []:
        err.add("$.canon_claims", "must be empty (canon is MrLore's domain)")

    refs = set()
    for i, ent in enumerate(artifact.get("declared_entities") or []):
        p = f"$.declared_entities[{i}]"
        if not isinstance(ent, dict) or not set(ent) <= ENTITY_KEYS or not {"local_ref", "source_span", "status"} <= set(ent):
            err.add(p, f"keys must be within {sorted(ENTITY_KEYS)} incl. local_ref/source_span/status")
            continue
        if not _ENT_REF.match(str(ent["local_ref"])) or ent["local_ref"] in refs:
            err.add(f"{p}.local_ref", "must be unique run-local 'ent_NNN'")
        refs.add(ent["local_ref"])
        if ent["status"] not in ENTITY_STATUS:
            err.add(f"{p}.status", f"must be one of {sorted(ENTITY_STATUS)}")
        if ent.get("presence") not in PRESENCE:
            err.add(f"{p}.presence", f"must be one of {sorted(PRESENCE)}")
        if ent.get("evidence_class") not in EVIDENCE_CLASS:
            err.add(f"{p}.evidence_class", f"must be one of {sorted(EVIDENCE_CLASS)}")
        _check_conf(ent.get("confidence"), f"{p}.confidence", err)
        _check_span(ent["source_span"], f"{p}.source_span", sid, source_text, err)
        _check_spans(ent.get("evidence", []), f"{p}.evidence", sid, source_text, err)

    for i, loc in enumerate(artifact.get("declared_locations") or []):
        p = f"$.declared_locations[{i}]"
        if not isinstance(loc, dict) or not set(loc) <= LOCATION_KEYS or not {"local_ref", "source_span", "status"} <= set(loc):
            err.add(p, f"keys must be within {sorted(LOCATION_KEYS)} incl. local_ref/source_span/status")
            continue
        if not _LOC_REF.match(str(loc["local_ref"])) or loc["local_ref"] in refs:
            err.add(f"{p}.local_ref", "must be unique run-local 'loc_NNN'")
        refs.add(loc["local_ref"])
        if loc["status"] not in ENTITY_STATUS:
            err.add(f"{p}.status", "invalid status")
        _check_conf(loc.get("confidence"), f"{p}.confidence", err)
        _check_span(loc["source_span"], f"{p}.source_span", sid, source_text, err)
        _check_spans(loc.get("evidence", []), f"{p}.evidence", sid, source_text, err)

    for i, al in enumerate(artifact.get("alias_candidates") or []):
        p = f"$.alias_candidates[{i}]"
        if not isinstance(al, dict):
            err.add(p, "must be object")
            continue
        if al.get("candidate_ref") not in refs:
            err.add(f"{p}.candidate_ref", "must reference a declared local_ref")
        for alt in al.get("alternatives", []):
            if alt not in refs:
                err.add(f"{p}.alternatives", f"unknown ref {alt}")
        if al.get("scope") not in ALIAS_SCOPE:
            err.add(f"{p}.scope", f"must be one of {sorted(ALIAS_SCOPE)}")
        if al.get("status") != "ALIAS_CANDIDATE":
            err.add(f"{p}.status", "must be ALIAS_CANDIDATE (Gen2 never commits aliases)")
        _check_conf(al.get("confidence"), f"{p}.confidence", err)
        _check_spans(al.get("evidence", []), f"{p}.evidence", sid, source_text, err)
        if not al.get("evidence"):
            err.add(f"{p}.evidence", "at least one span required")

    for i, mc in enumerate(artifact.get("metadata_constraints") or []):
        p = f"$.metadata_constraints[{i}]"
        if not isinstance(mc, dict) or mc.get("kind") not in METADATA_KINDS:
            err.add(p, f"kind must be one of {sorted(METADATA_KINDS)}")
            continue
        _check_span(mc.get("source_span"), f"{p}.source_span", sid, source_text, err)

    return err.items
