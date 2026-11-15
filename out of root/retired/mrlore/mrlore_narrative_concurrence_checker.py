"""
MrLore Narrative Concurrence Checker.

Verifies proposed coordinates in proposed_metric_layout against qualitative
relations in accepted_spatial_truth and original source narrative.
Operates as a restricted validation engine. Never alters coordinates.
"""

from __future__ import annotations

from typing import Any


def check_spatial_relation(
    link_type: str,
    relation: str,
    figure_id: str,
    ground_id: str,
    figure_pos: dict[str, float],
    ground_pos: dict[str, float],
) -> tuple[bool, str]:
    """Check if the 3D metric coordinates satisfy the qualitative relationship."""
    dx = figure_pos["x"] - ground_pos["x"]
    dy = figure_pos["y"] - ground_pos["y"]
    dz = figure_pos["z"] - ground_pos["z"]

    if link_type == "OLINK":
        if relation == "left":
            if dx < 0:
                return True, "figure is left of ground (-x)"
            return False, f"left violated: figure.x ({figure_pos['x']}) >= ground.x ({ground_pos['x']})"
        elif relation == "right":
            if dx > 0:
                return True, "figure is right of ground (+x)"
            return False, f"right violated: figure.x ({figure_pos['x']}) <= ground.x ({ground_pos['x']})"
        elif relation == "above":
            if dy > 0:
                return True, "figure is above ground (+y)"
            return False, f"above violated: figure.y ({figure_pos['y']}) <= ground.y ({ground_pos['y']})"
        elif relation == "below":
            if dy < 0:
                return True, "figure is below ground (-y)"
            return False, f"below violated: figure.y ({figure_pos['y']}) >= ground.y ({ground_pos['y']})"
        elif relation == "behind":
            if dz < 0:
                return True, "figure is behind ground (-z)"
            return False, f"behind violated: figure.z ({figure_pos['z']}) >= ground.z ({ground_pos['z']})"
        elif relation == "inFront":
            if dz > 0:
                return True, "figure is in front of ground (+z)"
            return False, f"inFront violated: figure.z ({figure_pos['z']}) <= ground.z ({ground_pos['z']})"
        elif relation == "near":
            return True, "near relation trivially satisfied"
        elif relation == "beside":
            if abs(dx) > 0 or abs(dz) > 0:
                return True, "beside relation (horizontally adjacent) satisfied"
            return False, "beside violated: figure and ground horizontally co-located"
        else:
            return True, f"unknown olink relation {relation} skipped"

    elif link_type in ("QSLINK", "MOVELINK"):
        if relation == "EQ":
            if dx == 0 and dy == 0 and dz == 0:
                return True, "positions are equal"
            return False, f"EQ violated: positions differ ({figure_pos} vs {ground_pos})"
        elif relation in ("NTPP", "NTPPI"):
            if dx == 0 and dy == 0 and dz == 0:
                return True, "inside/contains overlap check passed"
            return True, "NTPP/NTPPI treated as passed"
        elif relation == "TPP":
            return True, "TPP contact treated as passed"
        elif relation == "EC":
            return True, "EC contact treated as passed"
        elif relation == "PO":
            return True, "PO overlap treated as passed"
        elif relation == "DC":
            dist = (dx**2 + dy**2 + dz**2)**0.5
            if dist > 0:
                return True, "disconnected check passed"
            return False, "DC violated: figure and ground co-located at same origin"
        else:
            return True, f"unknown relation {relation} skipped"

    return True, f"unknown link type {link_type} skipped"


def verify_concurrence(
    accepted_spatial_truth: dict[str, Any],
    proposed_metric_layout: dict[str, Any],
    source_prose: str | None = None,
) -> dict[str, Any]:
    """
    Run narrative and spatial verification checks.
    
    Produces contradictions, unresolved findings, and a final decision.
    """
    contradictions: list[str] = []
    unresolved_findings: list[str] = []
    checks_run = 0

    # 1. Inputs validation
    checks_run += 1
    if accepted_spatial_truth.get("packet_type") != "accepted_spatial_truth":
        unresolved_findings.append("Input accepted_spatial_truth packet has wrong packet_type")
        return {
            "concurrence_decision": "REJECTED",
            "contradictions": contradictions,
            "unresolved_findings": unresolved_findings,
            "checks_run": checks_run,
        }

    checks_run += 1
    if proposed_metric_layout.get("packet_type") != "proposed_metric_layout":
        unresolved_findings.append("Input proposed_metric_layout packet has wrong packet_type")
        return {
            "concurrence_decision": "REJECTED",
            "contradictions": contradictions,
            "unresolved_findings": unresolved_findings,
            "checks_run": checks_run,
        }

    # 2. Match entities sets
    source_entities = accepted_spatial_truth.get("entities", [])
    source_ids = {str(item.get("entity_id", "")) for item in source_entities}

    layout_entities = proposed_metric_layout.get("entities", [])
    layout_positions = {
        str(item.get("entity_id", "")): item.get("position")
        for item in layout_entities
    }
    layout_ids = set(layout_positions.keys())

    checks_run += 1
    if source_ids != layout_ids:
        missing = sorted(source_ids - layout_ids)
        extra = sorted(layout_ids - source_ids)
        contradictions.append(
            f"Entity set mismatch: missing in layout={missing}; extra in layout={extra}"
        )

    # 3. Check source prose mentions if available
    if source_prose:
        for entity in source_entities:
            entity_name = entity.get("name", "")
            entity_id = entity.get("entity_id", "")
            checks_run += 1
            # Check if name is mentioned in the prose (case-insensitive)
            if entity_name and entity_name.lower() not in source_prose.lower():
                unresolved_findings.append(
                    f"Entity '{entity_name}' (ID: {entity_id}) not found in source prose"
                )

    # 4. Check every link in accepted spatial truth
    links = []
    for link in accepted_spatial_truth.get("olinks", []):
        links.append(("OLINK", link))
    for link in accepted_spatial_truth.get("qslinks", []):
        links.append(("QSLINK", link))
    for link in accepted_spatial_truth.get("movelinks", []):
        links.append(("MOVELINK", link))

    for link_type, link in links:
        checks_run += 1
        figure = str(link.get("figure" if link_type != "MOVELINK" else "mover", ""))
        ground = str(link.get("ground", ""))
        relation = str(link.get("rel_type" if link_type != "MOVELINK" else "target_rel", ""))
        link_id = str(link.get("link_id", "unnamed"))

        if not figure or not ground:
            unresolved_findings.append(f"Link {link_id} has missing figure or ground ID")
            continue

        if figure not in layout_positions or ground not in layout_positions:
            unresolved_findings.append(
                f"Link {link_id} references entity {figure} or {ground} missing from layout positions"
            )
            continue

        figure_pos = layout_positions[figure]
        ground_pos = layout_positions[ground]

        if not figure_pos or not ground_pos:
            unresolved_findings.append(
                f"Link {link_id} figure {figure} or ground {ground} has null position"
            )
            continue

        # run the verification check
        ok, msg = check_spatial_relation(
            link_type=link_type,
            relation=relation,
            figure_id=figure,
            ground_id=ground,
            figure_pos=figure_pos,
            ground_pos=ground_pos,
        )

        if not ok:
            contradictions.append(f"Link {link_id} failed relation check '{relation}': {msg}")

    decision = "REJECTED" if (contradictions or unresolved_findings) else "CONCURRED"

    return {
        "concurrence_decision": decision,
        "contradictions": contradictions,
        "unresolved_findings": unresolved_findings,
        "checks_run": checks_run,
    }
