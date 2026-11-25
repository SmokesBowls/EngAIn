"""
artifactroom/occupancy_evidence.py
──────────────────────────────────────────────────────────────────────────────
Populate the existing TopologyEntity fields `semantic_type` and `pgt_envelope`
from explicit classification records, using PGT_SCALE_POLICY_v0.1
(tier2/topologist/research/topological spacing.txt).

Rules
  - No record → the entity stays semantic_type=unknown, pgt_envelope=None.
  - A semantic_type other than unknown must cite text present in the
    artifact's source_prose (the manuscript excerpt).
  - An envelope is only the policy's own numbers; dimensions the policy does
    not declare (structure width/depth) are never filled in.
  - Every envelope says whether it is evidence-backed or provisional:
      basis="evidence"    occupancy_evidence must cite source_prose
      basis="provisional" provisional_reason required; never evidence
  - PGT units only; no pixels (the validator forbids "px").

Enrichment happens on a DRAFT artifact, before the reckoningroom.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from .topology_artifact import ArtifactLifecycle, ProseTopologyArtifact, SemanticType

PGT_SCALE_POLICY_ID = "PGT_SCALE_POLICY_v0.1"
PGT_SCALE_POLICY_SOURCE = "tier2/topologist/research/topological spacing.txt"

# Values copied from the policy's JSON block. Height-only classes stay height-only.
OCCUPANCY_CLASSES: dict[str, dict[str, Any]] = {
    "human_standard":             {"envelope": {"h": 10, "w": 4, "d": 3}, "types": {"person"}},
    "human_slim":                 {"envelope": {"h": 9, "w": 3, "d": 2}, "types": {"person"}},
    "minimum_walkable_structure": {"envelope": {"h": 15}, "types": {"structure"}},
    "standard_house":             {"envelope": {"h": 20}, "types": {"structure"}},
    "large_hall":                 {"envelope": {"h": 30}, "types": {"structure"}},
    "cathedral_or_temple":        {"envelope": {"h": 40}, "types": {"structure"}},
    "monumental_or_tower":        {"envelope": {"h_min": 60}, "types": {"structure"}},
    "small_giant":                {"envelope": {"h": 28}, "types": {"person", "creature"}},
    "standard_giant":             {"envelope": {"h": 32}, "types": {"person", "creature"}},
}

_BASES = {"evidence", "provisional"}


def _cited(text: Any, source_prose: str) -> bool:
    return isinstance(text, str) and text.strip() != "" and text.strip() in source_prose


def apply_occupancy_evidence(
    artifact: ProseTopologyArtifact,
    records: dict[str, dict[str, Any]],
) -> ProseTopologyArtifact:
    """Return a new DRAFT artifact with classified entities. Raises ValueError."""
    if artifact.lifecycle is not ArtifactLifecycle.DRAFT:
        raise ValueError(f"occupancy enrichment requires DRAFT; got {artifact.lifecycle.value}")
    known = set(artifact.entity_ids())
    unknown_ids = sorted(set(records) - known)
    if unknown_ids:
        raise ValueError(f"records name entities not in artifact: {unknown_ids}")

    entities = []
    for entity in artifact.entities:
        rec = records.get(entity.entity_id)
        if rec is None:
            entities.append(entity)
            continue
        where = entity.entity_id
        try:
            stype = SemanticType(rec.get("semantic_type", "unknown"))
        except ValueError:
            raise ValueError(f"{where}: unknown semantic_type {rec.get('semantic_type')!r}") from None
        if stype is not SemanticType.UNKNOWN and not _cited(rec.get("semantic_evidence"), artifact.source_prose):
            raise ValueError(f"{where}: semantic_type {stype.value} needs semantic_evidence quoted from source_prose")

        envelope = None
        cls = rec.get("occupancy_class")
        if cls is not None:
            spec = OCCUPANCY_CLASSES.get(cls)
            if spec is None:
                raise ValueError(f"{where}: occupancy_class {cls!r} not in {PGT_SCALE_POLICY_ID}")
            if stype.value not in spec["types"]:
                raise ValueError(f"{where}: occupancy_class {cls} does not apply to semantic_type {stype.value}")
            basis = rec.get("occupancy_basis")
            if basis not in _BASES:
                raise ValueError(f"{where}: occupancy_basis must be one of {sorted(_BASES)}")
            envelope = {**spec["envelope"], "policy_id": PGT_SCALE_POLICY_ID,
                        "occupancy_class": cls, "basis": basis}
            if basis == "evidence":
                if not _cited(rec.get("occupancy_evidence"), artifact.source_prose):
                    raise ValueError(f"{where}: evidence basis needs occupancy_evidence quoted from source_prose")
                envelope["evidence_ref"] = rec["occupancy_evidence"].strip()
            else:
                reason = rec.get("provisional_reason")
                if not isinstance(reason, str) or not reason.strip():
                    raise ValueError(f"{where}: provisional basis needs provisional_reason")
                envelope["provisional_reason"] = reason.strip()
        entities.append(replace(entity, semantic_type=stype, pgt_envelope=envelope))

    return ProseTopologyArtifact(
        artifact_id=artifact.artifact_id,
        source_prose=artifact.source_prose,
        entities=entities,
        qslinks=list(artifact.qslinks),
        olinks=list(artifact.olinks),
        movelinks=list(artifact.movelinks),
        lifecycle=ArtifactLifecycle.DRAFT,
        schema_version=artifact.schema_version,
    )
