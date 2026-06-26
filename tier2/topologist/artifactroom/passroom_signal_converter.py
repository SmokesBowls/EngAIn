"""
passroom_signal_converter.py — Topologist Artifactroom

Converts pass1_spatial output (spatial signal JSON) into a ProseTopologyArtifact.

Boundary doctrine:
  Producer describes. Consumer interprets.

  Passroom describes prose signals.
  The topologist (this module) interprets those signals into topology law.

  Passroom must not import topologist.
  This module consumes passroom signal records and decides:
    - which signals represent valid topological actors
    - which link type (QSLINK / OLINK / MOVELINK) applies
    - what the entity set is
    - what lifecycle state the artifact enters

This module does NOT:
  - parse prose
  - call Passroom
  - call Godot, Trixel, Blender, or Mechanimation
  - depend on the Chronicles ontology gate
  - mutate runtime

#005 scope:
  Narrow and intentional. Proves the seam:
    pass1_spatial output → ProseTopologyArtifact → TopologyValidator
  Not all signals convert. Unknown or ambiguous relations are skipped
  cleanly rather than guessed at.
"""

from __future__ import annotations

import re
from typing import Any

from tier2.topologist.artifactroom.topology_artifact import (
    ArtifactLifecycle,
    FrameOfReference,
    MOVELINK,
    MoveLinkTransition,
    OLINK,
    OLinkRelType,
    ProseTopologyArtifact,
    QSLINK,
    QSLinkRelType,
    SemanticType,
    TopologyEntity,
)


# ---------------------------------------------------------------------------
# Invalid entity hint filter
#
# Passroom's subject/object extraction is generous — it takes the nearest
# content word and sometimes produces hints that are prepositions (when a
# spatial trigger appears sentence-initially) or trigger verbs (when a
# multi-word trigger end is immediately followed by another action word).
#
# The topologist filters these before creating entities or links.
# ---------------------------------------------------------------------------

_INVALID_ENTITY_HINTS = frozenset({
    # Spatial prepositions — surface as subject when trigger is sentence-initial
    # e.g. "Behind the gate, ..." → subject_hint="behind" (nothing to the left)
    "before", "behind", "beside", "near", "above", "below",
    "within", "between", "through", "toward",
    # Trigger verbs — surface as object when a multi-word trigger ends
    # immediately before another action word
    # e.g. "raised one hand and blocked" → object_hint="blocked"
    "blocked", "raised", "closed", "barred", "sealed",
    "approached", "entered", "stood", "waited", "moved",
    "crossed", "retreated", "withdrew",
})


# ---------------------------------------------------------------------------
# Relation → topology link conversion tables
#
# The topologist decides these mappings. Passroom emits a relation name and
# a topology_link_hint but neither is binding here.
# ---------------------------------------------------------------------------

# spatial_signal / obstruction_signal relations → OLINK
_TO_OLINK: dict[str, OLinkRelType] = {
    "in_front_of": OLinkRelType.INFRONT,
    "behind":      OLinkRelType.BEHIND,
    "beside":      OLinkRelType.BESIDE,
    "above":       OLinkRelType.ABOVE,
    "below":       OLinkRelType.BELOW,
    "blocks_path": OLinkRelType.INFRONT,  # obstruction: figure is in front of path/ground
}

# spatial_signal / obstruction_signal relations → QSLINK
_TO_QSLINK: dict[str, QSLinkRelType] = {
    "near":             QSLinkRelType.EC,    # near = externally connected (following fixture)
    "within":           QSLinkRelType.NTPP,  # within = non-tangential proper part
    "closed_boundary":  QSLinkRelType.EC,    # closed gate = EC but not penetrable
}

# movement_signal relations → (source_rel, target_rel, transition)
_TO_MOVELINK: dict[str, tuple[QSLinkRelType, QSLinkRelType, MoveLinkTransition]] = {
    "approach": (QSLinkRelType.DC, QSLinkRelType.EC, MoveLinkTransition.DC_TO_EC),
    "enter":    (QSLinkRelType.EC, QSLinkRelType.PO, MoveLinkTransition.EC_TO_PO),
    "retreat":  (QSLinkRelType.EC, QSLinkRelType.DC, MoveLinkTransition.EC_TO_DC),
    "withdraw": (QSLinkRelType.EC, QSLinkRelType.DC, MoveLinkTransition.EC_TO_DC),
}

# Relations not listed above are skipped — ambiguous or not yet resolvable
# at #005 seam-proof scope:
#   "between"   — ternary, RCC-8 can't express directly
#   "through"   — complex traversal requiring intermediate states
#   "stand"     — stative, no topological transition
#   "wait"      — stative
#   "raise"     — gestural, not a spatial transition of the entity itself
#   "movement"  — too vague
#   "cross"     — requires multi-step transition


# ---------------------------------------------------------------------------
# Entity helpers
# ---------------------------------------------------------------------------

def _slugify(hint: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", hint.lower().strip()).strip("_")


def _is_valid_hint(hint: str | None) -> bool:
    return bool(hint and hint.lower() not in _INVALID_ENTITY_HINTS)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def convert_spatial_signals_to_artifact(
    spatial_payload: dict[str, Any],
    artifact_id: str,
    scene_id: str,
) -> ProseTopologyArtifact:
    """
    Convert a pass1_spatial output dict into a ProseTopologyArtifact.

    The topologist decides which signals are valid topology actors, which link
    type applies, and what the entity set is. Passroom does not make these
    decisions.

    Args:
        spatial_payload: Full dict produced by pass1_spatial.process_file().
        artifact_id:     Unique artifact identifier (caller assigns this).
        scene_id:        Scene identifier — used to namespace entity IDs.

    Returns:
        ProseTopologyArtifact in DRAFT lifecycle, ready for the reckoningroom.
        If no signals survive filtering and conversion, the artifact will have
        no entities or links — the validator will report this honestly.
    """
    signals: list[dict[str, Any]] = spatial_payload.get("signals", [])

    entities: dict[str, TopologyEntity] = {}
    qslinks: list[QSLINK] = []
    olinks:  list[OLINK]  = []
    movelinks: list[MOVELINK] = []
    source_texts: list[str] = []
    link_counter = 0

    def _ensure_entity(hint: str) -> str:
        eid = f"{scene_id}.{_slugify(hint)}"
        if eid not in entities:
            entities[eid] = TopologyEntity(
                entity_id=eid,
                name=hint,
                semantic_type=SemanticType.UNKNOWN,
            )
        return eid

    def _next_link_id(prefix: str) -> str:
        nonlocal link_counter
        link_counter += 1
        return f"{artifact_id}.{prefix}{link_counter:04d}"

    for sig in signals:
        subject  = sig.get("subject_hint")
        obj      = sig.get("object_hint")
        relation = sig.get("relation", "")
        src_text = sig.get("source_text", "")

        # Collect source prose regardless of whether this signal converts
        if src_text and src_text not in source_texts:
            source_texts.append(src_text)

        # Validate hints before creating any entity or link
        subject_ok = _is_valid_hint(subject)
        obj_ok     = _is_valid_hint(obj)

        # --- OLINK (directional / obstruction orientation) ---
        if relation in _TO_OLINK:
            if not subject_ok or not obj_ok:
                continue
            olinks.append(OLINK(
                link_id=_next_link_id("olink"),
                figure=_ensure_entity(subject),
                ground=_ensure_entity(obj),
                rel_type=_TO_OLINK[relation],
                frame_of_reference=FrameOfReference.INTRINSIC,
                trigger=relation,
            ))

        # --- QSLINK (mereotopological containment / proximity) ---
        elif relation in _TO_QSLINK:
            if not subject_ok or not obj_ok:
                continue
            qslinks.append(QSLINK(
                link_id=_next_link_id("qslink"),
                figure=_ensure_entity(subject),
                ground=_ensure_entity(obj),
                rel_type=_TO_QSLINK[relation],
                trigger=relation,
            ))

        # --- MOVELINK (topological transition) ---
        elif relation in _TO_MOVELINK:
            if not subject_ok or not obj_ok:
                continue
            source_rel, target_rel, transition = _TO_MOVELINK[relation]
            movelinks.append(MOVELINK(
                link_id=_next_link_id("movelink"),
                mover=_ensure_entity(subject),
                ground=_ensure_entity(obj),
                source_rel=source_rel,
                target_rel=target_rel,
                transition=transition,
                path_trigger=relation,
            ))

        # else: relation not in conversion scope for #005 — skip cleanly

    return ProseTopologyArtifact(
        artifact_id=artifact_id,
        source_prose="\n".join(source_texts),
        entities=list(entities.values()),
        qslinks=qslinks,
        olinks=olinks,
        movelinks=movelinks,
        lifecycle=ArtifactLifecycle.DRAFT,
    )
