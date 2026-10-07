"""artifact_assembler (GEN2_MODULES.md §2.17).

Input:   reconciled annotations, metadata constraints, run metadata.
Output:  `mettaext.parse_artifact.v2` (GEN2_OUTPUT_CONTRACT.md §4/§5a).
Allowed: mapping and packaging, nothing else. It is deliberately boring.
Forbidden: reinterpreting, adding, dropping or upgrading any annotation.
Failure: schema or lane-line validation failure means no artifact
         (AssemblyError lists every violation).
Sections whose producing modules are not implemented yet are emitted empty,
with a warning saying so. Empty is never evidence of absence.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List

from ..lib.annotations import AnnotationView, SceneInput, thaw
from ..lib.artifact_schema import CONTRACT, validate_parse_artifact_v2
from ..lib.source import SourceDocument

NAME = "artifact_assembler"
VERSION = "0.1.0"

# Sections owned by modules not yet implemented in this build (GEN2_MODULES.md §2).
UNIMPLEMENTED_SECTIONS = {
    "declared_events": "event_extractor",
    "speech": "dialogue_extractor",
    "spatial_signals": "spatial_cue_extractor",
    "distance_cues": "distance_cue_extractor",
    "temporal_cues": "temporal_cue_extractor",
    "affect_cues": "affect_cue_extractor",
    "terrain_descriptions": "terrain_cue_extractor",
    "continuity_flags": "reconciler (cross-span continuity)",
}


class AssemblyError(RuntimeError):
    def __init__(self, errors: List[str]):
        super().__init__("parse_artifact.v2 failed validation:\n  " + "\n  ".join(errors))
        self.errors = errors


def _run_id(doc: SourceDocument, scene: SceneInput, modules: List[Dict[str, str]]) -> str:
    blob = json.dumps([doc.sha256, scene.chapterroom_scene_id, modules], sort_keys=True).encode()
    return "gen2run_" + hashlib.sha256(blob).hexdigest()[:16]


def assemble(doc: SourceDocument, scene: SceneInput, view: AnnotationView,
             modules: List[Dict[str, str]], warnings: List[str],
             challenges: List[Dict[str, str]]) -> Dict[str, Any]:
    def declarations(kind: str) -> List[Dict[str, Any]]:
        items = []
        for a in view.by_kind(kind):
            value = thaw(a.value)
            evidence = value.pop("evidence")
            items.append({**value, "source_span": a.span.to_dict(), "evidence": evidence,
                          "confidence": a.confidence})
        return sorted(items, key=lambda d: d["local_ref"])

    aliases = []
    for a in view.by_kind("alias_candidate"):
        value = thaw(a.value)
        aliases.append({**value, "confidence": a.confidence})

    constraints = []
    for a in view.by_kind("metadata_constraint"):
        value = thaw(a.value)
        constraints.append({
            "kind": value["kind"], "key": value["key"], "subject": value.get("subject"),
            "text": value["text"], **({"qualifier": value["qualifier"]} if "qualifier" in value else {}),
            "source_span": a.span.to_dict(),
        })

    all_warnings = list(warnings) + [
        f"section_not_produced: {section} (module {module} not implemented in this build; empty is not evidence of absence)"
        for section, module in UNIMPLEMENTED_SECTIONS.items()
    ] + ["input_packet_has_no_source_hash: Chapterroom packets do not record the source sha256; "
         "source_sha256 here is the hash read by source_loader"]

    artifact: Dict[str, Any] = {
        "contract": CONTRACT,
        "source": "mettaext",
        "authority_lane": "prose_to_structure",
        "authority_tier": 3,
        "source_text_id": doc.source_text_id,
        "source_sha256": doc.sha256,
        "parse_stage": "gen2",
        "scene": {
            "source_scene_label": scene.source_scene_label,
            "chapterroom_scene_id": scene.chapterroom_scene_id,
            "chapter_id": scene.chapter_id,
            "boundary_method": scene.boundary_method,
            "authored_scene_boundaries_proven": scene.authored_scene_boundaries_proven,
            "runtime_stage_id": None,
        },
        "run": {"run_id": _run_id(doc, scene, modules), "modules": modules},
        "declared_entities": declarations("reconciled_entity"),
        "declared_locations": declarations("reconciled_location"),
        "declared_events": [],
        "alias_candidates": aliases,
        "speech": [],
        "spatial_signals": [],
        "distance_cues": [],
        "temporal_cues": [],
        "affect_cues": [],
        "terrain_descriptions": [],
        "metadata_constraints": constraints,
        "continuity_flags": [],
        "challenges": challenges,
        "warnings": all_warnings,
        "canon_claims": [],
    }
    errors = validate_parse_artifact_v2(artifact, source_text=doc.text)
    if errors:
        raise AssemblyError(errors)
    return artifact
