"""
Cartographer Metric Layout Artifact.

This module defines only the engine-agnostic metric proposal contract.
It does not parse prose, validate topology, render art, create Godot nodes,
or mutate runtime state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class MetricLayoutLifecycle(str, Enum):
    DRAFT = "DRAFT"
    PROPOSED = "PROPOSED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class MetricPosition:
    x: float
    y: float
    z: float

    def to_dict(self) -> dict[str, float]:
        return {
            "x": float(self.x),
            "y": float(self.y),
            "z": float(self.z),
        }


@dataclass(frozen=True)
class MetricLayoutEntity:
    entity_id: str
    position: MetricPosition
    placement_source: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "position": self.position.to_dict(),
            "placement_source": self.placement_source,
        }


@dataclass(frozen=True)
class AppliedConstraint:
    link_id: str
    link_type: str
    figure: str
    ground: str
    relation: str
    resolution: str

    def to_dict(self) -> dict[str, str]:
        return {
            "link_id": self.link_id,
            "link_type": self.link_type,
            "figure": self.figure,
            "ground": self.ground,
            "relation": self.relation,
            "resolution": self.resolution,
        }


@dataclass
class MetricLayoutArtifact:
    artifact_id: str
    source_artifact_id: str
    source_packet_hash: str
    anchor_entity_id: str
    entities: list[MetricLayoutEntity] = field(default_factory=list)
    applied_constraints: list[AppliedConstraint] = field(default_factory=list)
    unresolved_constraints: list[dict[str, Any]] = field(default_factory=list)
    lifecycle: MetricLayoutLifecycle = MetricLayoutLifecycle.DRAFT
    contract: str = "engain.cartographer_metric_layout.v1"
    coordinate_space: str = "world_cell_y_up"
    unit: str = "meter"

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract": self.contract,
            "artifact_id": self.artifact_id,
            "source_artifact_id": self.source_artifact_id,
            "source_packet_hash": self.source_packet_hash,
            "lifecycle": self.lifecycle.value,
            "coordinate_space": self.coordinate_space,
            "unit": self.unit,
            "axis_contract": {
                "x": "east_west",
                "y": "vertical_up",
                "z": "north_south_depth",
            },
            "anchor_entity_id": self.anchor_entity_id,
            "entities": [entity.to_dict() for entity in self.entities],
            "applied_constraints": [
                constraint.to_dict() for constraint in self.applied_constraints
            ],
            "unresolved_constraints": list(self.unresolved_constraints),
        }
