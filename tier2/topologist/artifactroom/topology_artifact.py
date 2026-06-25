"""
artifactroom/topology_artifact.py
──────────────────────────────────────────────────────────────────────────────
ProseTopologyArtifact — the canonical shape of spatial truth.

This module defines ONLY the data contract.  No prose extraction.  No Godot.
No Trixel.  No rendering.  No coordinates.  PGT units are permitted as
abstract occupancy hints; pixel dimensions are forbidden.

Authority boundary (from PGT_SCALE_POLICY_v0.1)
  PGT owns  : spatial reasoning, occupancy envelope, clearance, fit,
               visibility, reachability, dominance, access, pathing,
               relative scale.
  Trixel/Godot own : sprite pixels, mesh shape, texture size, rendering
                     details, final visual proportions.

Lifecycle states
  DRAFT        — being assembled, not yet submitted for validation
  PROPOSED     — submitted to reckoningroom, validation pending
  ACCEPTED     — reckoningroom and gate have both cleared it
  REJECTED     — reckoningroom found one or more violations
──────────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


# ─────────────────────────────────────────────────────────────────────────────
# ENUMERATIONS
# ─────────────────────────────────────────────────────────────────────────────

class ArtifactLifecycle(str, Enum):
    DRAFT    = "DRAFT"
    PROPOSED = "PROPOSED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class SemanticType(str, Enum):
    """Broad ontological class of a spatial entity."""
    PERSON    = "person"
    CREATURE  = "creature"
    FURNITURE = "furniture"
    STRUCTURE = "structure"
    OBJECT    = "object"
    REGION    = "region"
    UNKNOWN   = "unknown"


class QSLinkRelType(str, Enum):
    """RCC-8 mereotopological relation set."""
    DC    = "DC"    # Disconnected
    EC    = "EC"    # Externally Connected
    PO    = "PO"    # Partially Overlapping
    EQ    = "EQ"    # Equal
    TPP   = "TPP"   # Tangential Proper Part  (figure on/against ground)
    TPPI  = "TPPI"  # Inverse TPP
    NTPP  = "NTPP"  # Non-Tangential Proper Part  (figure inside ground)
    NTPPI = "NTPPI" # Inverse NTPP


class OLinkRelType(str, Enum):
    """Directional / orientation relation types."""
    BESIDE = "beside"
    BEHIND = "behind"
    INFRONT = "inFront"
    ABOVE   = "above"
    BELOW   = "below"
    LEFT    = "left"
    RIGHT   = "right"
    NEAR    = "near"


class FrameOfReference(str, Enum):
    INTRINSIC  = "intrinsic"   # relative to the ground entity's own axes
    RELATIVE   = "relative"    # relative to an observer's viewpoint
    ABSOLUTE   = "absolute"    # relative to a fixed environmental frame


class MoveLinkTransition(str, Enum):
    """
    Legal conceptual-neighbourhood transitions only.
    Topology cannot teleport: DC → EC → PO → NTPP is valid; DC → NTPP is not.
    """
    DC_TO_EC    = "DC→EC"
    EC_TO_PO    = "EC→PO"
    PO_TO_NTPP  = "PO→NTPP"
    PO_TO_TPP   = "PO→TPP"
    NTPP_TO_PO  = "NTPP→PO"
    TPP_TO_EC   = "TPP→EC"
    EC_TO_DC    = "EC→DC"
    PO_TO_EC    = "PO→EC"


# ─────────────────────────────────────────────────────────────────────────────
# CORE RELATION DATACLASSES  (all frozen — spatial truth is immutable once set)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class TopologyEntity:
    """
    A spatially-referenceable actor in the topology artifact.

    entity_id   — unique within this artifact
    name        — human-readable label
    semantic_type — broad ontological class
    pgt_envelope  — optional HWD occupancy hint in PGT units
                    e.g. {"h": 10, "w": 4, "d": 3}
                    NEVER pixels; NEVER Godot coordinates.
    """
    entity_id:     str
    name:          str
    semantic_type: SemanticType = SemanticType.UNKNOWN
    pgt_envelope:  Optional[Dict[str, float]] = None  # {"h", "w", "d"} in PGT

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_id":     self.entity_id,
            "name":          self.name,
            "semantic_type": self.semantic_type.value,
            "pgt_envelope":  self.pgt_envelope,
        }


@dataclass(frozen=True)
class QSLINK:
    """
    Qualitative Spatial Link — mereotopological containment / connection.

    figure  — the entity whose position is being described
    ground  — the reference entity
    rel_type — RCC-8 relation between L(figure) and L(ground)
    trigger  — the spatial signal word from source prose (optional)
    """
    link_id:  str
    figure:   str           # entity_id
    ground:   str           # entity_id
    rel_type: QSLinkRelType
    trigger:  Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "link_id":  self.link_id,
            "type":     "QSLINK",
            "figure":   self.figure,
            "ground":   self.ground,
            "rel_type": self.rel_type.value,
            "trigger":  self.trigger,
        }


@dataclass(frozen=True)
class OLINK:
    """
    Orientation Link — directional / projective spatial relation.

    frame_of_reference — intrinsic / relative / absolute
    axis               — the projected axis label ("left", "north", etc.)
    """
    link_id:            str
    figure:             str
    ground:             str
    rel_type:           OLinkRelType
    frame_of_reference: FrameOfReference = FrameOfReference.INTRINSIC
    axis:               Optional[str] = None
    trigger:            Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "link_id":            self.link_id,
            "type":               "OLINK",
            "figure":             self.figure,
            "ground":             self.ground,
            "rel_type":           self.rel_type.value,
            "frame_of_reference": self.frame_of_reference.value,
            "axis":               self.axis,
            "trigger":            self.trigger,
        }


@dataclass(frozen=True)
class MOVELINK:
    """
    Movement Link — a topological transition over a temporal interval.

    Only conceptual-neighbourhood transitions are legal.
    The validator enforces that source_rel → target_rel is adjacent in
    the RCC-8 neighbourhood graph.

    path_trigger — the verb or motion phrase from source prose
    interval_id  — optional reference to a narrative temporal interval
    """
    link_id:      str
    mover:        str               # entity_id of the moving figure
    ground:       str               # entity_id of the reference landmark
    source_rel:   QSLinkRelType     # topology state BEFORE movement
    target_rel:   QSLinkRelType     # topology state AFTER movement
    transition:   MoveLinkTransition
    path_trigger: Optional[str] = None
    interval_id:  Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "link_id":      self.link_id,
            "type":         "MOVELINK",
            "mover":        self.mover,
            "ground":       self.ground,
            "source_rel":   self.source_rel.value,
            "target_rel":   self.target_rel.value,
            "transition":   self.transition.value,
            "path_trigger": self.path_trigger,
            "interval_id":  self.interval_id,
        }


# ─────────────────────────────────────────────────────────────────────────────
# TOP-LEVEL ARTIFACT
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ProseTopologyArtifact:
    """
    The coordinate-free spatial truth produced by the topologist.

    This is the object the reckoningroom validates, the gate accepts or
    rejects, and GodotSim's transform solver reads to produce node positions.

    FORBIDDEN FIELDS (enforced by reckoningroom):
      - No x/y/z coordinates
      - No pixel dimensions
      - No mesh references
      - No Trixel asset IDs
      - No Godot node paths
      - No render or texture data

    lifecycle must be DRAFT or PROPOSED when entering the reckoningroom.
    Only the gate may write ACCEPTED.
    """
    artifact_id:   str
    source_prose:  str                          # verbatim excerpt that produced this artifact
    entities:      List[TopologyEntity] = field(default_factory=list)
    qslinks:       List[QSLINK]         = field(default_factory=list)
    olinks:        List[OLINK]          = field(default_factory=list)
    movelinks:     List[MOVELINK]       = field(default_factory=list)
    lifecycle:     ArtifactLifecycle    = ArtifactLifecycle.DRAFT
    schema_version: str                 = "PGT_ARTIFACT_v0.1"

    # ── helpers ──────────────────────────────────────────────────────────────

    def entity_ids(self) -> List[str]:
        return [e.entity_id for e in self.entities]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "artifact_id":    self.artifact_id,
            "schema_version": self.schema_version,
            "lifecycle":      self.lifecycle.value,
            "source_prose":   self.source_prose,
            "entities":       [e.to_dict() for e in self.entities],
            "qslinks":        [q.to_dict() for q in self.qslinks],
            "olinks":         [o.to_dict() for o in self.olinks],
            "movelinks":      [m.to_dict() for m in self.movelinks],
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ProseTopologyArtifact":
        entities = [
            TopologyEntity(
                entity_id=e["entity_id"],
                name=e["name"],
                semantic_type=SemanticType(e.get("semantic_type", "unknown")),
                pgt_envelope=e.get("pgt_envelope"),
            )
            for e in d.get("entities", [])
        ]
        qslinks = [
            QSLINK(
                link_id=q["link_id"],
                figure=q["figure"],
                ground=q["ground"],
                rel_type=QSLinkRelType(q["rel_type"]),
                trigger=q.get("trigger"),
            )
            for q in d.get("qslinks", [])
        ]
        olinks = [
            OLINK(
                link_id=o["link_id"],
                figure=o["figure"],
                ground=o["ground"],
                rel_type=OLinkRelType(o["rel_type"]),
                frame_of_reference=FrameOfReference(
                    o.get("frame_of_reference", "intrinsic")
                ),
                axis=o.get("axis"),
                trigger=o.get("trigger"),
            )
            for o in d.get("olinks", [])
        ]
        movelinks = [
            MOVELINK(
                link_id=m["link_id"],
                mover=m["mover"],
                ground=m["ground"],
                source_rel=QSLinkRelType(m["source_rel"]),
                target_rel=QSLinkRelType(m["target_rel"]),
                transition=MoveLinkTransition(m["transition"]),
                path_trigger=m.get("path_trigger"),
                interval_id=m.get("interval_id"),
            )
            for m in d.get("movelinks", [])
        ]
        return cls(
            artifact_id=d["artifact_id"],
            source_prose=d.get("source_prose", ""),
            entities=entities,
            qslinks=qslinks,
            olinks=olinks,
            movelinks=movelinks,
            lifecycle=ArtifactLifecycle(d.get("lifecycle", "DRAFT")),
            schema_version=d.get("schema_version", "PGT_ARTIFACT_v0.1"),
        )
