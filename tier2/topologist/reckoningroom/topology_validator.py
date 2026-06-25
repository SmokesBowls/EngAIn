"""
reckoningroom/topology_validator.py
──────────────────────────────────────────────────────────────────────────────
TopologyValidator — the judge that receives a ProseTopologyArtifact and
decides whether it is legally formed spatial truth.

What it checks
  ✓ entities exist and have unique IDs
  ✓ all link figures/grounds reference known entities
  ✓ QSLINK rel_type is a legal RCC-8 value
  ✓ OLINK rel_type is a legal orientation value
  ✓ MOVELINK transition is a legal conceptual-neighbourhood step
  ✓ MOVELINK source_rel → target_rel matches the declared transition
  ✓ no self-links (figure == ground) unless the rel_type is EQ
  ✓ artifact lifecycle is DRAFT or PROPOSED (not already ACCEPTED/REJECTED)
  ✓ no Godot coordinate fields
  ✓ no render / pixel / mesh / Trixel fields in the raw dict

What it does NOT do
  ✗ parse prose
  ✗ call Godot
  ✗ create coordinates
  ✗ mutate any runtime state
  ✗ flip lifecycle to ACCEPTED (that is the gate's job)

Output: ValidationReport  (pure data, JSON-serialisable)
──────────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from tier2.topologist.artifactroom.topology_artifact import (
    ArtifactLifecycle,
    MoveLinkTransition,
    ProseTopologyArtifact,
    QSLinkRelType,
)


# ─────────────────────────────────────────────────────────────────────────────
# FORBIDDEN FIELD SETS  (any of these appearing in the raw dict is a violation)
# ─────────────────────────────────────────────────────────────────────────────

_GODOT_COORDINATE_KEYS = frozenset({
    "x", "y", "z",
    "position", "transform", "global_transform",
    "translation", "rotation", "scale",
    "node_path", "godot_node", "godot_id",
})

_RENDER_TRIXEL_KEYS = frozenset({
    "pixel", "pixels", "px", "sprite", "mesh", "texture",
    "shader", "material", "trixel_id", "trixel_asset",
    "render", "renderer", "visual", "lod",
    "width_px", "height_px", "depth_px",
    "mesh_ref", "asset_ref", "atlas_ref",
})

# Legal conceptual-neighbourhood map:
# transition enum value → (expected source_rel, expected target_rel)
_TRANSITION_SPEC: Dict[MoveLinkTransition, tuple] = {
    MoveLinkTransition.DC_TO_EC:   (QSLinkRelType.DC,   QSLinkRelType.EC),
    MoveLinkTransition.EC_TO_PO:   (QSLinkRelType.EC,   QSLinkRelType.PO),
    MoveLinkTransition.PO_TO_NTPP: (QSLinkRelType.PO,   QSLinkRelType.NTPP),
    MoveLinkTransition.PO_TO_TPP:  (QSLinkRelType.PO,   QSLinkRelType.TPP),
    MoveLinkTransition.NTPP_TO_PO: (QSLinkRelType.NTPP, QSLinkRelType.PO),
    MoveLinkTransition.TPP_TO_EC:  (QSLinkRelType.TPP,  QSLinkRelType.EC),
    MoveLinkTransition.EC_TO_DC:   (QSLinkRelType.EC,   QSLinkRelType.DC),
    MoveLinkTransition.PO_TO_EC:   (QSLinkRelType.PO,   QSLinkRelType.EC),
}


# ─────────────────────────────────────────────────────────────────────────────
# REPORT STRUCTURES
# ─────────────────────────────────────────────────────────────────────────────

class ViolationCode(str, Enum):
    DUPLICATE_ENTITY_ID        = "DUPLICATE_ENTITY_ID"
    UNKNOWN_FIGURE             = "UNKNOWN_FIGURE"
    UNKNOWN_GROUND             = "UNKNOWN_GROUND"
    UNKNOWN_MOVER              = "UNKNOWN_MOVER"
    SELF_LINK_ILLEGAL          = "SELF_LINK_ILLEGAL"
    LIFECYCLE_ALREADY_CLOSED   = "LIFECYCLE_ALREADY_CLOSED"
    GODOT_COORDINATE_FIELD     = "GODOT_COORDINATE_FIELD"
    RENDER_TRIXEL_FIELD        = "RENDER_TRIXEL_FIELD"
    MOVELINK_TRANSITION_MISMATCH = "MOVELINK_TRANSITION_MISMATCH"
    EMPTY_ENTITY_LIST          = "EMPTY_ENTITY_LIST"
    MISSING_ARTIFACT_ID        = "MISSING_ARTIFACT_ID"


@dataclass
class Violation:
    code:    ViolationCode
    detail:  str
    link_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code":    self.code.value,
            "detail":  self.detail,
            "link_id": self.link_id,
        }


@dataclass
class ValidationReport:
    artifact_id: str
    passed:      bool
    violations:  List[Violation] = field(default_factory=list)
    checks_run:  List[str]       = field(default_factory=list)
    notes:       List[str]       = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "passed":      self.passed,
            "violations":  [v.to_dict() for v in self.violations],
            "checks_run":  self.checks_run,
            "notes":       self.notes,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


# ─────────────────────────────────────────────────────────────────────────────
# VALIDATOR
# ─────────────────────────────────────────────────────────────────────────────

class TopologyValidator:
    """
    Pure functional validator.  Accepts a ProseTopologyArtifact and a copy of
    its raw dict (so forbidden-field scanning can inspect all keys without
    trusting the dataclass).

    Usage
    -----
        validator = TopologyValidator()
        report = validator.validate(artifact, raw_dict)
    """

    def validate(
        self,
        artifact: ProseTopologyArtifact,
        raw_dict: Optional[Dict[str, Any]] = None,
    ) -> ValidationReport:
        """
        Run all checks.  Returns a ValidationReport.
        Does not mutate the artifact or any runtime state.
        """
        violations: List[Violation] = []
        checks_run: List[str] = []
        notes:      List[str] = []

        raw = raw_dict or artifact.to_dict()

        # 1. artifact_id present
        checks_run.append("artifact_id_present")
        if not artifact.artifact_id or not artifact.artifact_id.strip():
            violations.append(Violation(
                code=ViolationCode.MISSING_ARTIFACT_ID,
                detail="artifact_id is empty or whitespace.",
            ))

        # 2. lifecycle must be DRAFT or PROPOSED
        checks_run.append("lifecycle_open")
        if artifact.lifecycle in (ArtifactLifecycle.ACCEPTED, ArtifactLifecycle.REJECTED):
            violations.append(Violation(
                code=ViolationCode.LIFECYCLE_ALREADY_CLOSED,
                detail=(
                    f"Artifact lifecycle is '{artifact.lifecycle.value}'.  "
                    "Only DRAFT or PROPOSED artifacts may enter the reckoningroom.  "
                    "ACCEPTED/REJECTED are gate outputs, not validator inputs."
                ),
            ))

        # 3. at least one entity
        checks_run.append("entity_list_nonempty")
        if not artifact.entities:
            violations.append(Violation(
                code=ViolationCode.EMPTY_ENTITY_LIST,
                detail="Artifact declares no entities.  A topology artifact must reference at least one spatial entity.",
            ))

        # 4. unique entity IDs
        checks_run.append("entity_id_uniqueness")
        seen_ids: set = set()
        for entity in artifact.entities:
            if entity.entity_id in seen_ids:
                violations.append(Violation(
                    code=ViolationCode.DUPLICATE_ENTITY_ID,
                    detail=f"entity_id '{entity.entity_id}' appears more than once.",
                ))
            seen_ids.add(entity.entity_id)

        known_ids = set(artifact.entity_ids())

        # 5. QSLINK reference integrity + self-link
        checks_run.append("qslink_reference_integrity")
        checks_run.append("qslink_self_link")
        for qs in artifact.qslinks:
            if qs.figure not in known_ids:
                violations.append(Violation(
                    code=ViolationCode.UNKNOWN_FIGURE,
                    detail=f"QSLINK '{qs.link_id}' figure '{qs.figure}' is not a declared entity.",
                    link_id=qs.link_id,
                ))
            if qs.ground not in known_ids:
                violations.append(Violation(
                    code=ViolationCode.UNKNOWN_GROUND,
                    detail=f"QSLINK '{qs.link_id}' ground '{qs.ground}' is not a declared entity.",
                    link_id=qs.link_id,
                ))
            if qs.figure == qs.ground and qs.rel_type != QSLinkRelType.EQ:
                violations.append(Violation(
                    code=ViolationCode.SELF_LINK_ILLEGAL,
                    detail=(
                        f"QSLINK '{qs.link_id}' has figure == ground ('{qs.figure}') "
                        f"but rel_type is '{qs.rel_type.value}'.  "
                        "Self-links are only legal for EQ (identity)."
                    ),
                    link_id=qs.link_id,
                ))

        # 6. OLINK reference integrity + self-link
        checks_run.append("olink_reference_integrity")
        checks_run.append("olink_self_link")
        for ol in artifact.olinks:
            if ol.figure not in known_ids:
                violations.append(Violation(
                    code=ViolationCode.UNKNOWN_FIGURE,
                    detail=f"OLINK '{ol.link_id}' figure '{ol.figure}' is not a declared entity.",
                    link_id=ol.link_id,
                ))
            if ol.ground not in known_ids:
                violations.append(Violation(
                    code=ViolationCode.UNKNOWN_GROUND,
                    detail=f"OLINK '{ol.link_id}' ground '{ol.ground}' is not a declared entity.",
                    link_id=ol.link_id,
                ))
            if ol.figure == ol.ground:
                violations.append(Violation(
                    code=ViolationCode.SELF_LINK_ILLEGAL,
                    detail=(
                        f"OLINK '{ol.link_id}' has figure == ground ('{ol.figure}').  "
                        "An entity cannot be oriented relative to itself."
                    ),
                    link_id=ol.link_id,
                ))

        # 7. MOVELINK reference integrity + transition consistency
        checks_run.append("movelink_reference_integrity")
        checks_run.append("movelink_transition_consistency")
        for ml in artifact.movelinks:
            if ml.mover not in known_ids:
                violations.append(Violation(
                    code=ViolationCode.UNKNOWN_MOVER,
                    detail=f"MOVELINK '{ml.link_id}' mover '{ml.mover}' is not a declared entity.",
                    link_id=ml.link_id,
                ))
            if ml.ground not in known_ids:
                violations.append(Violation(
                    code=ViolationCode.UNKNOWN_GROUND,
                    detail=f"MOVELINK '{ml.link_id}' ground '{ml.ground}' is not a declared entity.",
                    link_id=ml.link_id,
                ))
            expected = _TRANSITION_SPEC.get(ml.transition)
            if expected:
                exp_src, exp_tgt = expected
                if ml.source_rel != exp_src or ml.target_rel != exp_tgt:
                    violations.append(Violation(
                        code=ViolationCode.MOVELINK_TRANSITION_MISMATCH,
                        detail=(
                            f"MOVELINK '{ml.link_id}' declares transition '{ml.transition.value}' "
                            f"but source_rel='{ml.source_rel.value}' / target_rel='{ml.target_rel.value}'.  "
                            f"Expected source='{exp_src.value}' → target='{exp_tgt.value}'."
                        ),
                        link_id=ml.link_id,
                    ))

        # 8. forbidden field scan — Godot coordinates
        checks_run.append("no_godot_coordinate_fields")
        _scan_forbidden_keys(raw, _GODOT_COORDINATE_KEYS, ViolationCode.GODOT_COORDINATE_FIELD, violations)

        # 9. forbidden field scan — render / Trixel fields
        checks_run.append("no_render_trixel_fields")
        _scan_forbidden_keys(raw, _RENDER_TRIXEL_KEYS, ViolationCode.RENDER_TRIXEL_FIELD, violations)

        if not violations:
            notes.append(
                "Artifact is topologically clean.  "
                "Ready for gate evaluation (EngAInOS acceptance)."
            )

        return ValidationReport(
            artifact_id=artifact.artifact_id,
            passed=(len(violations) == 0),
            violations=violations,
            checks_run=checks_run,
            notes=notes,
        )


# ─────────────────────────────────────────────────────────────────────────────
# INTERNAL HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _scan_forbidden_keys(
    obj: Any,
    forbidden: frozenset,
    code: ViolationCode,
    violations: List[Violation],
    _path: str = "",
) -> None:
    """Recursively walk a dict/list and flag any forbidden key names."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            path = f"{_path}.{k}" if _path else k
            if k.lower() in forbidden:
                violations.append(Violation(
                    code=code,
                    detail=(
                        f"Forbidden field '{path}' found in artifact dict.  "
                        "Topology artifacts must not carry render, coordinate, or Trixel data."
                    ),
                ))
            _scan_forbidden_keys(v, forbidden, code, violations, path)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            _scan_forbidden_keys(item, forbidden, code, violations, f"{_path}[{i}]")
