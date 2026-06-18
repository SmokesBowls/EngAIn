# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/godotsim/gates/gate_no_narrative_meaning.py

from __future__ import annotations

from typing import Any

from engain_control.gate_result import GateResult


NARRATIVE_MEANING_KEYS = {
    "quest_complete",
    "quest_completion",
    "door_open",
    "door_closed",
    "event_triggered",
    "narrative_event",
    "story_progress",
    "dialogue_branch",
    "cutscene_trigger",
}


def _collect_keys(value: Any, found: set[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            found.add(str(key))
            _collect_keys(child, found)
    elif isinstance(value, list):
        for child in value:
            _collect_keys(child, found)


def gate_no_narrative_meaning_in_packet(packet: dict[str, Any]) -> GateResult:
    """
    GodotSim reports physical facts, not narrative meaning.
    It may not declare quest completion, door state changes, or story events.
    """
    all_keys: set[str] = set()
    _collect_keys(packet, all_keys)

    narrative_keys = sorted(all_keys.intersection(NARRATIVE_MEANING_KEYS))

    if narrative_keys:
        return GateResult(
            "gate_no_narrative_meaning_in_packet",
            "FALSE",
            f"HARD REJECT: narrative meaning keys found: {narrative_keys}",
        )

    return GateResult(
        "gate_no_narrative_meaning_in_packet",
        "TRUE",
        "Packet contains no narrative meaning (quest, door, event, story)",
    )