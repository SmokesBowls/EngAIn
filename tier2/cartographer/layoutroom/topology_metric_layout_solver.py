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
