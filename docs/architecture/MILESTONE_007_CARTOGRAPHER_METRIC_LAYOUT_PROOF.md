# MILESTONE 007 — CARTOGRAPHER METRIC LAYOUT PROOF

## 1. Task identity

```text
TASK_ID: MILESTONE_007_CARTOGRAPHER_METRIC_LAYOUT_PROOF
REPO_ROOT: /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn
TARGET_LANE: tier2/cartographer
PROOF_SCRIPT: tools/gameproof/run_gameproof_007.py
INPUT_PROOF: scratch/gameproof_006/output/accepted_spatial_truth_packet.json
OUTPUT_ROOT: scratch/gameproof_007/output
STATUS: READY_FOR_IMPLEMENTATION
```

This task adds the first real Cartographer slice to the existing proof chain.

Existing chain:

```text
Mettaext scene evidence
→ Game Proof #005 creates and validates ProseTopologyArtifact
→ Game Proof #006 advances coordinate-free topology to accepted_spatial_truth
```

This task adds:

```text
accepted_spatial_truth
→ deterministic Cartographer metric solver
→ DRAFT MetricLayoutArtifact
→ Cartographer technical validation
→ Cartographer proposal gate
→ proposed_metric_layout packet
```

This task stops before MrLore concurrence, EngAInOS authority verification, Trixel, GodotSim, or Godot.

---

## 2. Authority boundary

Cartographer owns only a deterministic metric proposal derived from accepted topology.

Cartographer may:

- choose one deterministic metric arrangement that satisfies or concretizes qualitative relations;
- assign engine-agnostic `world_cell_y_up` positions;
- declare the chosen anchor entity;
- record every applied relation and deterministic fallback;
- emit a `PROPOSED` metric-layout packet for later MrLore concurrence.

Cartographer must not:

- rewrite source prose;
- mutate MrLore memory or canon;
- declare final EngAInOS world truth;
- produce Trixel images, sprites, textures, palettes, materials, or atlases;
- create Godot nodes or `.tscn` files;
- start GodotSim or mutate runtime state;
- change Topologist files or accepted topology relations;
- infer elevation from WorldField;
- collapse `world_cell_y_up` into `worldfield_grid`;
- use hard-coded user-machine paths inside Python modules.

The coordinate contract for this proof is:

```text
coordinate_space = world_cell_y_up
unit             = meter
x                = east/west
z                = north/south / depth
 y               = vertical / up
```

The solver may choose metric coordinates. It may not change the accepted qualitative relation graph.

---

## 3. Files in scope

Create only these files:

```text
tier2/cartographer/__init__.py
tier2/cartographer/README.md

tier2/cartographer/artifactroom/__init__.py
tier2/cartographer/artifactroom/metric_layout_artifact.py

tier2/cartographer/layoutroom/__init__.py
tier2/cartographer/layoutroom/topology_metric_layout_solver.py

tier2/cartographer/reckoningroom/__init__.py
tier2/cartographer/reckoningroom/metric_layout_validator.py

tier2/cartographer/gates/__init__.py
tier2/cartographer/gates/gate_propose_metric_layout.py

tools/gameproof/run_gameproof_007.py

docs/contracts/CARTOGRAPHER_METRIC_LAYOUT_CONTRACT_v1.md
```

Do not edit:

```text
tier2/topologist/**
tier3/mettaext/**
tier1/engainos/**
tier2/godotsim/**
tier2/trixel3.2d/**
godotroot/**
tools/gameproof/run_gameproof_005.py
tools/gameproof/run_gameproof_006.py
```

If any required upstream file is missing, stop and report `MISSING_UPSTREAM_PROOF_DEPENDENCY`. Do not recreate, bypass, or fake it.

---

## 4. Create package marker files

Create these five files with the same minimal content:

```text
tier2/cartographer/__init__.py
tier2/cartographer/artifactroom/__init__.py
tier2/cartographer/layoutroom/__init__.py
tier2/cartographer/reckoningroom/__init__.py
tier2/cartographer/gates/__init__.py
```

Content:

```python
"""Cartographer package marker."""
```

---

## 5. Create `metric_layout_artifact.py`

Path:

```text
tier2/cartographer/artifactroom/metric_layout_artifact.py
```

Purpose:

- define the immutable metric-layout data contract;
- contain no solver logic;
- contain no validation logic;
- contain no Godot, Trixel, runtime, HTTP, or file I/O.

Exact content:

```python
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
```

---

## 6. Create `topology_metric_layout_solver.py`

Path:

```text
tier2/cartographer/layoutroom/topology_metric_layout_solver.py
```

Purpose:

- consume only `accepted_spatial_truth`;
- preserve the exact source entity IDs and relation records;
- choose a deterministic anchor;
- assign one metric position per entity;
- return a DRAFT `MetricLayoutArtifact`;
- never import Godot, Trixel, EngAInOS runtime, or Mettaext.

Exact content:

```python
"""
Deterministic topology-to-metric layout solver.

The solver concretizes accepted qualitative topology into one metric proposal.
It does not claim final world truth. Later lanes may concur, reject, or gate it.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from math import isfinite
from typing import Any

from tier2.cartographer.artifactroom.metric_layout_artifact import (
    AppliedConstraint,
    MetricLayoutArtifact,
    MetricLayoutEntity,
    MetricPosition,
)


BASE_CLEARANCE = 1.0
DEFAULT_HALF_EXTENT = 0.5


def _canonical_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _entity_map(packet: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for entity in packet.get("entities", []):
        entity_id = str(entity.get("entity_id", "")).strip()
        if not entity_id:
            continue
        result[entity_id] = entity
    return result


def _half_extent(entity: dict[str, Any], axis: str) -> float:
    envelope = entity.get("pgt_envelope") or {}
    envelope_key = {"x": "w", "y": "h", "z": "d"}[axis]
    raw_value = envelope.get(envelope_key)

    if raw_value is None:
        return DEFAULT_HALF_EXTENT

    try:
        value = float(raw_value)
    except (TypeError, ValueError):
        return DEFAULT_HALF_EXTENT

    if not isfinite(value) or value <= 0:
        return DEFAULT_HALF_EXTENT

    return value / 2.0


def _choose_anchor(packet: dict[str, Any], entity_ids: list[str]) -> str:
    ground_counts: Counter[str] = Counter()

    for link in packet.get("qslinks", []):
        ground = str(link.get("ground", ""))
        if ground:
            ground_counts[ground] += 1

    for link in packet.get("olinks", []):
        ground = str(link.get("ground", ""))
        if ground:
            ground_counts[ground] += 1

    for link in packet.get("movelinks", []):
        ground = str(link.get("ground", ""))
        if ground:
            ground_counts[ground] += 1

    if ground_counts:
        highest_count = max(ground_counts.values())
        candidates = sorted(
            entity_id
            for entity_id, count in ground_counts.items()
            if count == highest_count and entity_id in entity_ids
        )
        if candidates:
            return candidates[0]

    return sorted(entity_ids)[0]


def _axis_distance(
    figure_entity: dict[str, Any],
    ground_entity: dict[str, Any],
    axis: str,
    multiplier: float = 1.0,
) -> float:
    return multiplier * (
        _half_extent(figure_entity, axis)
        + _half_extent(ground_entity, axis)
        + BASE_CLEARANCE
    )


def _olink_offset(
    link: dict[str, Any],
    figure_entity: dict[str, Any],
    ground_entity: dict[str, Any],
) -> tuple[float, float, float, str]:
    relation = str(link.get("rel_type", "")).strip()
    axis_hint = str(link.get("axis", "")).strip().lower()

    dx = _axis_distance(figure_entity, ground_entity, "x")
    dy = _axis_distance(figure_entity, ground_entity, "y")
    dz = _axis_distance(figure_entity, ground_entity, "z")

    if relation == "left" or axis_hint == "left":
        return -dx, 0.0, 0.0, "olink_left"
    if relation == "right" or axis_hint == "right":
        return dx, 0.0, 0.0, "olink_right"
    if relation == "above":
        return 0.0, dy, 0.0, "olink_above"
    if relation == "below":
        return 0.0, -dy, 0.0, "olink_below"
    if relation == "behind":
        return 0.0, 0.0, -dz, "olink_behind"
    if relation == "inFront":
        return 0.0, 0.0, dz, "olink_in_front"
    if relation == "near":
        return dx, 0.0, dz, "olink_near_diagonal"
    if relation == "beside":
        if axis_hint == "left":
            return -dx, 0.0, 0.0, "olink_beside_left"
        if axis_hint == "right":
            return dx, 0.0, 0.0, "olink_beside_right"
        return dx, 0.0, 0.0, "olink_beside_deterministic_right"

    return dx, 0.0, 0.0, "olink_unknown_deterministic_right"


def _qslink_offset(
    link: dict[str, Any],
    figure_entity: dict[str, Any],
    ground_entity: dict[str, Any],
) -> tuple[float, float, float, str]:
    relation = str(link.get("rel_type", "")).strip()
    trigger = str(link.get("trigger", "")).strip().lower()

    touch_x = _half_extent(figure_entity, "x") + _half_extent(ground_entity, "x")
    separate_x = touch_x + BASE_CLEARANCE

    if relation == "EQ":
        return 0.0, 0.0, 0.0, "qslink_equal_same_origin"

    if relation == "NTPP":
        return 0.0, 0.0, 0.0, "qslink_inside_same_origin"

    if relation == "NTPPI":
        return 0.0, 0.0, 0.0, "qslink_contains_same_origin"

    if relation == "TPP" and trigger in {"on", "upon", "atop", "over"}:
        vertical = _half_extent(figure_entity, "y") + _half_extent(ground_entity, "y")
        return 0.0, vertical, 0.0, "qslink_on_vertical_contact"

    if relation == "TPP":
        return 0.0, 0.0, 0.0, "qslink_tangential_same_origin"

    if relation == "TPPI":
        return 0.0, 0.0, 0.0, "qslink_inverse_tangential_same_origin"

    if relation == "EC":
        return touch_x, 0.0, 0.0, "qslink_external_contact_positive_x"

    if relation == "PO":
        return max(touch_x * 0.5, 0.25), 0.0, 0.0, "qslink_partial_overlap_positive_x"

    if relation == "DC":
        return max(separate_x * 2.0, 4.0), 0.0, 0.0, "qslink_disconnected_positive_x"

    return separate_x, 0.0, 0.0, "qslink_unknown_deterministic_positive_x"


def _movelink_offset(
    link: dict[str, Any],
    figure_entity: dict[str, Any],
    ground_entity: dict[str, Any],
) -> tuple[float, float, float, str]:
    synthetic_qslink = {
        "rel_type": link.get("target_rel"),
        "trigger": link.get("path_trigger"),
    }
    dx, dy, dz, resolution = _qslink_offset(
        synthetic_qslink,
        figure_entity,
        ground_entity,
    )
    return dx, dy, dz, f"movelink_target_{resolution}"


def _add_position(
    base: tuple[float, float, float],
    offset: tuple[float, float, float],
) -> tuple[float, float, float]:
    return (
        base[0] + offset[0],
        base[1] + offset[1],
        base[2] + offset[2],
    )


def _negate(offset: tuple[float, float, float]) -> tuple[float, float, float]:
    return (-offset[0], -offset[1], -offset[2])


def _relation_records(packet: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []

    for link in packet.get("olinks", []):
        records.append(
            {
                "link_type": "OLINK",
                "link_id": str(link.get("link_id", "")),
                "figure": str(link.get("figure", "")),
                "ground": str(link.get("ground", "")),
                "relation": str(link.get("rel_type", "")),
                "raw": link,
            }
        )

    for link in packet.get("qslinks", []):
        records.append(
            {
                "link_type": "QSLINK",
                "link_id": str(link.get("link_id", "")),
                "figure": str(link.get("figure", "")),
                "ground": str(link.get("ground", "")),
                "relation": str(link.get("rel_type", "")),
                "raw": link,
            }
        )

    for link in packet.get("movelinks", []):
        records.append(
            {
                "link_type": "MOVELINK",
                "link_id": str(link.get("link_id", "")),
                "figure": str(link.get("mover", "")),
                "ground": str(link.get("ground", "")),
                "relation": str(link.get("target_rel", "")),
                "raw": link,
            }
        )

    priority = {"OLINK": 0, "QSLINK": 1, "MOVELINK": 2}
    return sorted(
        records,
        key=lambda item: (
            priority[item["link_type"]],
            item["link_id"],
            item["figure"],
            item["ground"],
        ),
    )


def build_metric_layout(
    accepted_spatial_truth: dict[str, Any],
) -> MetricLayoutArtifact:
    if accepted_spatial_truth.get("packet_type") != "accepted_spatial_truth":
        raise ValueError(
            "Cartographer requires packet_type='accepted_spatial_truth'."
        )

    entities_by_id = _entity_map(accepted_spatial_truth)
    entity_ids = sorted(entities_by_id)

    if not entity_ids:
        raise ValueError("accepted_spatial_truth contains no entities.")

    anchor_entity_id = _choose_anchor(accepted_spatial_truth, entity_ids)
    positions: dict[str, tuple[float, float, float]] = {
        anchor_entity_id: (0.0, 0.0, 0.0)
    }
    placement_sources: dict[str, str] = {
        anchor_entity_id: "anchor_origin"
    }
    applied_constraints: list[AppliedConstraint] = []

    pending = _relation_records(accepted_spatial_truth)
    progress = True

    while pending and progress:
        progress = False
        remaining: list[dict[str, Any]] = []

        for record in pending:
            figure = record["figure"]
            ground = record["ground"]

            if figure not in entities_by_id or ground not in entities_by_id:
                remaining.append(record)
                continue

            figure_entity = entities_by_id[figure]
            ground_entity = entities_by_id[ground]

            if record["link_type"] == "OLINK":
                dx, dy, dz, resolution = _olink_offset(
                    record["raw"], figure_entity, ground_entity
                )
            elif record["link_type"] == "QSLINK":
                dx, dy, dz, resolution = _qslink_offset(
                    record["raw"], figure_entity, ground_entity
                )
            else:
                dx, dy, dz, resolution = _movelink_offset(
                    record["raw"], figure_entity, ground_entity
                )

            offset = (dx, dy, dz)

            if ground in positions and figure not in positions:
                positions[figure] = _add_position(positions[ground], offset)
                placement_sources[figure] = record["link_id"] or record["link_type"]
                progress = True
            elif figure in positions and ground not in positions:
                positions[ground] = _add_position(positions[figure], _negate(offset))
                placement_sources[ground] = (
                    f"inverse:{record['link_id'] or record['link_type']}"
                )
                progress = True
            elif figure not in positions and ground not in positions:
                remaining.append(record)
                continue

            applied_constraints.append(
                AppliedConstraint(
                    link_id=record["link_id"],
                    link_type=record["link_type"],
                    figure=figure,
                    ground=ground,
                    relation=record["relation"],
                    resolution=resolution,
                )
            )

        pending = remaining

    fallback_index = 1
    for entity_id in entity_ids:
        if entity_id in positions:
            continue
        positions[entity_id] = (float(fallback_index * 4), 0.0, 0.0)
        placement_sources[entity_id] = "deterministic_disconnected_component_fallback"
        fallback_index += 1

    unresolved_constraints = [
        {
            "link_id": record["link_id"],
            "link_type": record["link_type"],
            "figure": record["figure"],
            "ground": record["ground"],
            "relation": record["relation"],
            "reason": "relation references missing entity or could not be traversed",
        }
        for record in pending
    ]

    metric_entities = [
        MetricLayoutEntity(
            entity_id=entity_id,
            position=MetricPosition(*positions[entity_id]),
            placement_source=placement_sources[entity_id],
        )
        for entity_id in entity_ids
    ]

    source_artifact_id = str(
        accepted_spatial_truth.get("source_artifact_id", "unknown")
    )

    return MetricLayoutArtifact(
        artifact_id=f"metric_layout.{source_artifact_id}",
        source_artifact_id=source_artifact_id,
        source_packet_hash=_canonical_hash(accepted_spatial_truth),
        anchor_entity_id=anchor_entity_id,
        entities=metric_entities,
        applied_constraints=applied_constraints,
        unresolved_constraints=unresolved_constraints,
    )
```

Important implementation note:

The fallback for disconnected components is not a claim that the prose said “east.” It is a deterministic candidate-layout choice. The `placement_source` records that distinction explicitly.

---

## 7. Create `metric_layout_validator.py`

Path:

```text
tier2/cartographer/reckoningroom/metric_layout_validator.py
```

Purpose:

- technical validation only;
- compare the layout proposal against the accepted topology packet;
- reject missing entities, extra entities, invalid coordinates, open unresolved constraints, render data, or wrong coordinate contract;
- never advance lifecycle itself.

Exact content:

```python
"""Technical validator for Cartographer metric-layout artifacts."""

from __future__ import annotations

from math import isfinite
from typing import Any


_FORBIDDEN_KEYS = frozenset(
    {
        "image",
        "image_path",
        "png",
        "sprite",
        "texture",
        "material",
        "palette",
        "atlas",
        "mesh",
        "scene_ref",
        "node_path",
        "render_plan",
        "trixel_payload",
        "godot_node",
        "runtime_mutation",
    }
)


def _walk_forbidden(value: Any, path: str = "root") -> list[str]:
    violations: list[str] = []

    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if str(key) in _FORBIDDEN_KEYS:
                violations.append(f"forbidden field present: {child_path}")
            violations.extend(_walk_forbidden(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            violations.extend(_walk_forbidden(child, f"{path}[{index}]"))

    return violations


def validate_metric_layout_artifact(
    artifact: dict[str, Any],
    accepted_spatial_truth: dict[str, Any],
) -> dict[str, Any]:
    violations: list[str] = []
    checks_run = 0

    checks_run += 1
    if artifact.get("contract") != "engain.cartographer_metric_layout.v1":
        violations.append("wrong or missing metric-layout contract")

    checks_run += 1
    if artifact.get("lifecycle") != "DRAFT":
        violations.append("validator input lifecycle must be DRAFT")

    checks_run += 1
    if artifact.get("coordinate_space") != "world_cell_y_up":
        violations.append("coordinate_space must be world_cell_y_up")

    checks_run += 1
    if artifact.get("unit") != "meter":
        violations.append("unit must be meter")

    checks_run += 1
    expected_axis_contract = {
        "x": "east_west",
        "y": "vertical_up",
        "z": "north_south_depth",
    }
    if artifact.get("axis_contract") != expected_axis_contract:
        violations.append("axis_contract does not match world_cell_y_up")

    checks_run += 1
    if accepted_spatial_truth.get("packet_type") != "accepted_spatial_truth":
        violations.append("upstream packet is not accepted_spatial_truth")

    source_entities = accepted_spatial_truth.get("entities", [])
    source_ids = [str(item.get("entity_id", "")) for item in source_entities]
    source_id_set = set(source_ids)

    layout_entities = artifact.get("entities", [])
    layout_ids = [str(item.get("entity_id", "")) for item in layout_entities]
    layout_id_set = set(layout_ids)

    checks_run += 1
    if len(layout_ids) != len(layout_id_set):
        violations.append("metric layout contains duplicate entity IDs")

    checks_run += 1
    if layout_id_set != source_id_set:
        missing = sorted(source_id_set - layout_id_set)
        extra = sorted(layout_id_set - source_id_set)
        violations.append(
            f"entity set mismatch; missing={missing}; extra={extra}"
        )

    checks_run += 1
    anchor_entity_id = str(artifact.get("anchor_entity_id", ""))
    if anchor_entity_id not in layout_id_set:
        violations.append("anchor_entity_id is not present in layout entities")

    anchor_position: dict[str, Any] | None = None

    for entity in layout_entities:
        entity_id = str(entity.get("entity_id", ""))
        position = entity.get("position")

        checks_run += 1
        if not isinstance(position, dict):
            violations.append(f"entity {entity_id} has no position object")
            continue

        for axis in ("x", "y", "z"):
            checks_run += 1
            value = position.get(axis)
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                violations.append(
                    f"entity {entity_id} position.{axis} is not numeric"
                )
                continue
            if not isfinite(float(value)):
                violations.append(
                    f"entity {entity_id} position.{axis} is not finite"
                )

        if entity_id == anchor_entity_id:
            anchor_position = position

    checks_run += 1
    if anchor_position != {"x": 0.0, "y": 0.0, "z": 0.0}:
        violations.append("anchor entity must be located at exact origin")

    checks_run += 1
    unresolved = artifact.get("unresolved_constraints", [])
    if unresolved:
        violations.append(
            f"unresolved_constraints is non-empty ({len(unresolved)})"
        )

    forbidden_violations = _walk_forbidden(artifact)
    checks_run += 1
    violations.extend(forbidden_violations)

    return {
        "validator": "cartographer.metric_layout_validator.v1",
        "passed": not violations,
        "checks_run": checks_run,
        "violations": violations,
        "source_entity_count": len(source_id_set),
        "layout_entity_count": len(layout_id_set),
    }
```

---

## 8. Create `gate_propose_metric_layout.py`

Path:

```text
tier2/cartographer/gates/gate_propose_metric_layout.py
```

Purpose:

- advance a technically valid Cartographer artifact from DRAFT to PROPOSED;
- not declare final EngAInOS truth;
- not perform MrLore concurrence;
- not mutate the input dictionary.

Exact content:

```python
"""Lifecycle gate for Cartographer metric-layout proposals."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


_GATE_ID = "gate_propose_metric_layout"


def evaluate_metric_layout_for_proposal(
    artifact: dict[str, Any],
    validation_report: dict[str, Any],
) -> dict[str, Any]:
    violations: list[str] = []

    if artifact.get("lifecycle") != "DRAFT":
        violations.append("metric-layout lifecycle must be DRAFT")

    if not validation_report.get("passed", False):
        violations.append("metric-layout validation did not pass")

    report_violations = validation_report.get("violations", [])
    if report_violations:
        violations.append(
            f"validation report contains {len(report_violations)} violation(s)"
        )

    decision = "PROPOSED" if not violations else "REJECTED"
    proposed_packet: dict[str, Any] | None = None

    if decision == "PROPOSED":
        proposed_packet = deepcopy(artifact)
        proposed_packet["packet_type"] = "proposed_metric_layout"
        proposed_packet["lifecycle"] = "PROPOSED"
        proposed_packet["authority_note"] = (
            "Cartographer metric proposal only. Requires MrLore narrative "
            "concurrence and EngAInOS contract/authority verification before use."
        )

    return {
        "gate_id": _GATE_ID,
        "decision": decision,
        "input_lifecycle": artifact.get("lifecycle"),
        "output_lifecycle": "PROPOSED" if decision == "PROPOSED" else artifact.get("lifecycle"),
        "proposed_metric_layout_packet": proposed_packet,
        "violations": violations,
    }
```

---

## 9. Create `run_gameproof_007.py`

Path:

```text
tools/gameproof/run_gameproof_007.py
```

Purpose:

- run the exact vertical proof;
- read Game Proof #006 output;
- write all #007 evidence under `scratch/gameproof_007/output`;
- fail honestly with exit code `2`;
- never start a server or renderer.

Exact content:

```python
#!/usr/bin/env python3
"""
EngAIn Game Proof #007 — Cartographer metric-layout proposal.

Input:
    scratch/gameproof_006/output/accepted_spatial_truth_packet.json

Output:
    scratch/gameproof_007/output/draft_metric_layout_artifact.json
    scratch/gameproof_007/output/metric_layout_validation_report.json
    scratch/gameproof_007/output/gate_report.json
    scratch/gameproof_007/output/proposed_metric_layout_packet.json
    scratch/gameproof_007/output/gameproof_report.json

This proof does not call MrLore, EngAInOS runtime, Trixel, GodotSim, or Godot.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
INPUT_PATH = (
    REPO_ROOT
    / "scratch"
    / "gameproof_006"
    / "output"
    / "accepted_spatial_truth_packet.json"
)
OUTPUT_DIR = REPO_ROOT / "scratch" / "gameproof_007" / "output"
PROOF_ID = "gameproof_007"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )


def run() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))

    print("=" * 72)
    print("EngAIn Game Proof #007 — Cartographer Metric Layout Proposal")
    print("=" * 72)
    print(f"Input : {INPUT_PATH}")
    print(f"Output: {OUTPUT_DIR}")
    print()

    violations: list[str] = []
    files_written: list[str] = []

    if not INPUT_PATH.exists():
        report = {
            "proof_id": PROOF_ID,
            "passed": False,
            "created_at": utc_now(),
            "violations": [
                "MISSING_UPSTREAM_PROOF_DEPENDENCY: "
                f"{INPUT_PATH}. Run tools/gameproof/run_gameproof_006.py first."
            ],
            "files_written": [],
        }
        write_json(OUTPUT_DIR / "gameproof_report.json", report)
        print(report["violations"][0])
        return 2

    accepted_spatial_truth = read_json(INPUT_PATH)

    from tier2.cartographer.gates.gate_propose_metric_layout import (
        evaluate_metric_layout_for_proposal,
    )
    from tier2.cartographer.layoutroom.topology_metric_layout_solver import (
        build_metric_layout,
    )
    from tier2.cartographer.reckoningroom.metric_layout_validator import (
        validate_metric_layout_artifact,
    )

    print("[1/4] Building DRAFT metric layout")
    try:
        draft_artifact_object = build_metric_layout(accepted_spatial_truth)
        draft_artifact = draft_artifact_object.to_dict()
    except Exception as exc:
        import traceback

        violations.append(
            "Cartographer solver failed:\n" + traceback.format_exc()
        )
        return _write_report(violations, files_written, None)

    draft_path = OUTPUT_DIR / "draft_metric_layout_artifact.json"
    write_json(draft_path, draft_artifact)
    files_written.append(str(draft_path.relative_to(REPO_ROOT)))
    print(f"      wrote: {draft_path}")

    print("[2/4] Validating metric layout")
    validation_report = validate_metric_layout_artifact(
        draft_artifact,
        accepted_spatial_truth,
    )
    validation_path = OUTPUT_DIR / "metric_layout_validation_report.json"
    write_json(validation_path, validation_report)
    files_written.append(str(validation_path.relative_to(REPO_ROOT)))
    print(f"      passed: {validation_report['passed']}")
    print(f"      wrote : {validation_path}")

    print("[3/4] Calling Cartographer proposal gate")
    gate_report = evaluate_metric_layout_for_proposal(
        draft_artifact,
        validation_report,
    )
    gate_path = OUTPUT_DIR / "gate_report.json"
    write_json(gate_path, gate_report)
    files_written.append(str(gate_path.relative_to(REPO_ROOT)))
    print(f"      decision: {gate_report['decision']}")
    print(f"      wrote   : {gate_path}")

    proposed_packet = gate_report.get("proposed_metric_layout_packet")
    if proposed_packet is not None:
        proposed_path = OUTPUT_DIR / "proposed_metric_layout_packet.json"
        write_json(proposed_path, proposed_packet)
        files_written.append(str(proposed_path.relative_to(REPO_ROOT)))
        print(f"      wrote   : {proposed_path}")

    print("[4/4] Checking proof conditions")

    if not validation_report.get("passed", False):
        violations.append(
            "metric-layout validation failed: "
            f"{validation_report.get('violations', [])}"
        )

    if gate_report.get("decision") != "PROPOSED":
        violations.append(
            f"gate decision was {gate_report.get('decision')}, expected PROPOSED"
        )

    if proposed_packet is None:
        violations.append("gate returned no proposed_metric_layout_packet")
    else:
        if proposed_packet.get("packet_type") != "proposed_metric_layout":
            violations.append("proposed packet has wrong packet_type")
        if proposed_packet.get("coordinate_space") != "world_cell_y_up":
            violations.append("proposed packet has wrong coordinate_space")
        if proposed_packet.get("lifecycle") != "PROPOSED":
            violations.append("proposed packet lifecycle is not PROPOSED")

        source_ids = {
            str(entity.get("entity_id"))
            for entity in accepted_spatial_truth.get("entities", [])
        }
        proposed_ids = {
            str(entity.get("entity_id"))
            for entity in proposed_packet.get("entities", [])
        }
        if source_ids != proposed_ids:
            violations.append(
                f"entity identity drift: source={sorted(source_ids)} "
                f"proposed={sorted(proposed_ids)}"
            )

    return _write_report(violations, files_written, gate_report)


def _write_report(
    violations: list[str],
    files_written: list[str],
    gate_report: dict[str, Any] | None,
) -> int:
    report = {
        "proof_id": PROOF_ID,
        "passed": not violations,
        "created_at": utc_now(),
        "input": str(INPUT_PATH.relative_to(REPO_ROOT)),
        "gate_id": gate_report.get("gate_id") if gate_report else None,
        "gate_decision": gate_report.get("decision") if gate_report else None,
        "violations": violations,
        "files_written": files_written,
        "boundaries": {
            "mrlore_called": False,
            "engainos_authority_called": False,
            "trixel_called": False,
            "godotsim_called": False,
            "godot_started": False,
            "runtime_mutated": False,
        },
        "next_required_stage": (
            "MrLore narrative concurrence over the combined accepted topology "
            "and proposed metric layout."
        ),
    }

    report_path = OUTPUT_DIR / "gameproof_report.json"
    write_json(report_path, report)

    print(f"      wrote: {report_path}")
    print()

    if violations:
        print("RESULT: FAILED HONESTLY")
        for violation in violations:
            print(f"  - {violation}")
        return 2

    print("RESULT: PASSED")
    print("Cartographer produced a deterministic PROPOSED metric layout.")
    print("The proposal has not yet received MrLore concurrence or EngAInOS authority.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
```

Make the proof executable:

```bash
chmod +x tools/gameproof/run_gameproof_007.py
```

---

## 10. Create `tier2/cartographer/README.md`

Exact content:

~~~~markdown
# Cartographer

Cartographer is an EngAIn-owned Tier 2 metric-layout system.

It consumes accepted coordinate-free topology and produces one deterministic,
engine-agnostic metric proposal in `world_cell_y_up` space.

Cartographer owns:

- metric placement proposals;
- deterministic anchor selection;
- entity positions in meters;
- traceable relation-to-coordinate resolutions;
- explicit deterministic fallbacks for under-specified layouts.

Cartographer does not own:

- source prose;
- canon or MrLore concurrence;
- final EngAInOS authority;
- WorldField elevation projection;
- Trixel visual truth;
- Godot nodes;
- GodotSim physics compatibility;
- runtime mutation.

Current proof:

```text
Game Proof #006 accepted_spatial_truth
→ Game Proof #007 proposed_metric_layout
```

The next stage is MrLore narrative concurrence over both artifacts.
~~~~

---

## 11. Create the active contract

Path:

```text
docs/contracts/CARTOGRAPHER_METRIC_LAYOUT_CONTRACT_v1.md
```

Exact content:

```markdown
# CARTOGRAPHER METRIC LAYOUT CONTRACT v1

## Input

`accepted_spatial_truth`

Required fields:

- `packet_type = accepted_spatial_truth`
- `source_artifact_id`
- `entities`
- `qslinks`
- `olinks`
- `movelinks`

## Output

`engain.cartographer_metric_layout.v1`

Required fields:

- `artifact_id`
- `source_artifact_id`
- `source_packet_hash`
- `lifecycle`
- `coordinate_space = world_cell_y_up`
- `unit = meter`
- `axis_contract`
- `anchor_entity_id`
- `entities`
- `applied_constraints`
- `unresolved_constraints`

## Authority

Cartographer may concretize accepted qualitative topology into one deterministic
metric proposal. The proposal remains non-canonical until MrLore narrative
concurrence and EngAInOS contract/authority verification both succeed.

## Coordinate seam

- `x` is east/west.
- `y` is vertical/up.
- `z` is north/south/depth.
- `worldfield_grid` is not accepted as this packet's coordinate space.
- WorldField elevation is not resolved by this contract.

## Forbidden output

- images;
- sprites;
- textures;
- palettes;
- atlases;
- materials;
- meshes;
- Trixel packet fields;
- Godot scene or node fields;
- runtime mutation commands;
- canon decisions.

## Lifecycle

- solver writes `DRAFT`;
- technical validator reports pass/fail;
- Cartographer gate may advance `DRAFT` to `PROPOSED`;
- only later lanes may concur with or authorize the proposal.
```

---

## 12. Verification commands

Run from the exact repository root:

```bash
cd /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn
```

First compile only the new Python files:

```bash
python3 -m py_compile \
  tier2/cartographer/artifactroom/metric_layout_artifact.py \
  tier2/cartographer/layoutroom/topology_metric_layout_solver.py \
  tier2/cartographer/reckoningroom/metric_layout_validator.py \
  tier2/cartographer/gates/gate_propose_metric_layout.py \
  tools/gameproof/run_gameproof_007.py
```

Then reproduce the upstream proof:

```bash
python3 tools/gameproof/run_gameproof_006.py
```

Then run the new proof:

```bash
python3 tools/gameproof/run_gameproof_007.py
```

Expected terminal ending:

```text
RESULT: PASSED
Cartographer produced a deterministic PROPOSED metric layout.
The proposal has not yet received MrLore concurrence or EngAInOS authority.
```

Inspect outputs:

```bash
find scratch/gameproof_007/output -maxdepth 1 -type f -printf '%f\n' | sort
```

Expected files:

```text
draft_metric_layout_artifact.json
gameproof_report.json
gate_report.json
metric_layout_validation_report.json
proposed_metric_layout_packet.json
```

Check proof status:

```bash
python3 - <<'PY'
import json
from pathlib import Path

root = Path("scratch/gameproof_007/output")
report = json.loads((root / "gameproof_report.json").read_text())
packet = json.loads((root / "proposed_metric_layout_packet.json").read_text())

assert report["passed"] is True, report
assert report["gate_decision"] == "PROPOSED", report
assert packet["packet_type"] == "proposed_metric_layout", packet
assert packet["coordinate_space"] == "world_cell_y_up", packet
assert packet["unit"] == "meter", packet
assert packet["lifecycle"] == "PROPOSED", packet
assert packet["unresolved_constraints"] == [], packet
assert all(
    set(entity["position"]) == {"x", "y", "z"}
    for entity in packet["entities"]
), packet

print("GAMEPROOF_007_PACKET_CHECK=PASS")
PY
```

---

## 13. Done means

The task is complete only when all of the following are true:

1. All new Python files compile.
2. Game Proof #006 still passes unchanged.
3. Game Proof #007 exits with code `0`.
4. The proposal contains exactly the same entity IDs as accepted topology.
5. The proposal uses `world_cell_y_up`, not Godot node coordinates and not WorldField grid coordinates.
6. The anchor entity is exactly at `(0.0, 0.0, 0.0)`.
7. `unresolved_constraints` is empty.
8. No Trixel, Godot, GodotSim, MrLore, EngAInOS runtime, network, or HTTP call occurs.
9. No existing file outside the declared scope is edited.
10. The result clearly says the metric layout is only `PROPOSED`.

---

## 14. Required completion report

The implementing agent must return:

```text
TASK_ID
FILES_CREATED
FILES_MODIFIED
PY_COMPILE_COMMAND
PY_COMPILE_RESULT
UPSTREAM_PROOF_COMMAND
UPSTREAM_PROOF_RESULT
NEW_PROOF_COMMAND
NEW_PROOF_RESULT
OUTPUT_FILES
GATE_DECISION
ENTITY_COUNT
ANCHOR_ENTITY_ID
COORDINATE_SPACE
UNRESOLVED_CONSTRAINT_COUNT
BOUNDARY_CONFIRMATION
GIT_DIFF_SUMMARY
```

Do not commit or push unless the human explicitly asks for a commit and push.
