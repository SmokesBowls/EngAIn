from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

CONTRACT_RECORD = "engain.mrlore_major_event_internal_receipt_map.record.v1"
CONTRACT_MANIFEST = "engain.mrlore_major_event_internal_receipt_map_manifest.v1"
SOURCE_BASIS = "SEEDED_CH30_CH38_EVENT_MAP_V1"

_INTERNAL_RECEIPT_STATUSES_BASE = {
    "MISSING",
    "PRESENT",
    "PRESENT_BUT_COMPRESSED",
    "PRESENT_BUT_UNDER_SIGNALED",
    "PRESENT_BUT_NEEDS_PERSONAL_CUT",
    "PRESENT_BUT_WEAPONIZED",
    "NOT_REQUIRED",
}
INTERNAL_RECEIPT_STATUSES = _INTERNAL_RECEIPT_STATUSES_BASE | {"PRESENT_BUT_COULD_USE_PERSONAL_CUT"}

RECEIPT_KINDS = {
    "PRIVATE_INTERNAL_RECEIPT",
    "SHARED_EXTERNAL_RECEIPT",
    "WITNESS_VALIDATION",
    "GRIEF_RECEIPT",
    "COMMAND_REASSESSMENT",
    "BODY_COST_RECEIPT",
    "WORLD_REACTION_RECEIPT",
    "RESPONSIBILITY_SETTLING_RECEIPT",
    "DOCTRINE_ABSORPTION_RECEIPT",
}

EVENT_TYPES = {
    "MASS_UNMAKING_AFTERMATH",
    "REALITY_DENIAL_AFTER_UNMAKING",
    "SHIP_THEFT_DECISION",
    "CRASH_TRIAGE",
    "IMPOSSIBLE_SURVIVAL_DISCOVERY",
    "FIVE_BODY_DISCOVERY",
    "BODY_PROTECTION_FROM_SCAVENGERS",
    "ECHO_TOWER_ROUTING",
    "COMMAND_REASSESSMENT",
    "RESTORED_SURVIVOR_REINTEGRATION",
    "TEMPORAL_LAW_DISCOVERY",
    "GIANT_AWE_AND_RESPONSIBILITY",
    "KEEPER_RESPONSIBILITY_TRANSFER",
}

REVISION_PRIORITIES = {
    "PATCH_REQUIRED",
    "OPTIONAL_REVIEW",
    "NO_PATCH_EXPECTED",
}

AUTHOR_ACTION_REQUIRED_BY_STATUS = {
    "MISSING": True,
    "PRESENT_BUT_COMPRESSED": True,
    "PRESENT_BUT_UNDER_SIGNALED": True,
    "PRESENT_BUT_NEEDS_PERSONAL_CUT": True,
    "PRESENT_BUT_WEAPONIZED": True,
    "PRESENT_BUT_COULD_USE_PERSONAL_CUT": True,
    "PRESENT": False,
    "NOT_REQUIRED": False,
}

REVISION_PRIORITY_BY_STATUS = {
    "MISSING": "PATCH_REQUIRED",
    "PRESENT_BUT_COMPRESSED": "PATCH_REQUIRED",
    "PRESENT_BUT_UNDER_SIGNALED": "PATCH_REQUIRED",
    "PRESENT_BUT_NEEDS_PERSONAL_CUT": "PATCH_REQUIRED",
    "PRESENT_BUT_WEAPONIZED": "PATCH_REQUIRED",
    "PRESENT_BUT_COULD_USE_PERSONAL_CUT": "OPTIONAL_REVIEW",
    "PRESENT": "NO_PATCH_EXPECTED",
    "NOT_REQUIRED": "NO_PATCH_EXPECTED",
}

SAFETY_LOCKS = [
    "MRLORE_MAJOR_EVENT_INTERNAL_RECEIPT_MAP identifies only major state-changing events.",
    "The diagnostic is event-level receipt guidance only.",
    "The diagnostic does not give chapter-wide emotional advice.",
    "The diagnostic does not rewrite chapters.",
    "The diagnostic does not generate replacement prose.",
    "The diagnostic does not promote claims.",
    "The diagnostic does not reject claims.",
    "The diagnostic does not resolve contradictions.",
    "The diagnostic does not write canon.",
    "The diagnostic does not create accepted lore packets.",
    "The diagnostic does not compile ZONJ.",
    "The diagnostic does not touch Godot or runtime.",
    "Author revises manually after reading the map.",
]

NEGATIVE_FLAGS = {
    "CANON_WRITTEN": False,
    "CLAIMS_PROMOTED": False,
    "CLAIMS_REJECTED": False,
    "CONTRADICTIONS_RESOLVED": False,
    "ACCEPTED_LORE_PACKET_CREATED": False,
    "GENERATED_PROSE_CREATED": False,
    "REPLACEMENT_PROSE_CREATED": False,
    "ZONJ_COMPILED": False,
    "GODOT_TOUCHED": False,
    "RUNTIME_TOUCHED": False,
}

FORBIDDEN_FIELDS = {
    "rewritten_scene",
    "replacement_paragraph",
    "replacement_scene",
    "generated_prose",
    "suggested_rewrite",
    "new_chapter_text",
    "canon_patch",
    "accepted_lore_packet",
}

_HERE = Path(__file__).resolve()
_ENGAIN_ROOT = _HERE.parents[2]


def default_engain_dir(manifest_path: Path | None = None) -> Path:
    path = manifest_path or (_ENGAIN_ROOT / "tier1" / "engainos" / "assets" / "engain_manifest.json")
    if not path.exists():
        raise FileNotFoundError(f"engain_manifest.json not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    output_dir = data.get("output_dir")
    if output_dir:
        return Path(output_dir) / ".engain"
    active_vault = data.get("active_vault")
    if active_vault:
        return Path(active_vault) / ".engain"
    raise ValueError(f"engain manifest has no output_dir or active_vault: {path}")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if not path.exists():
        return records
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSONL at {path}:{line_number}: {exc}") from exc
        if not isinstance(item, dict):
            raise ValueError(f"Invalid JSONL at {path}:{line_number}: expected object")
        records.append(item)
    return records


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )


def _chapter_number_from_id(chapter_id: str) -> int | None:
    match = re.search(r"book\d{3}\.(\d+)", chapter_id)
    return int(match.group(1)) if match else None


def _book_id_from_chapter_id(chapter_id: str) -> str:
    match = re.search(r"(book\d{3})\.", chapter_id)
    return match.group(1) if match else "book_unknown"


def _load_breathing_map(engain_dir: Path) -> dict[str, dict[str, Any]]:
    path = engain_dir / "mrlore" / "revision" / "breathing_map.jsonl"
    index: dict[str, dict[str, Any]] = {}
    for record in _read_jsonl(path):
        chapter_id = str(record.get("chapter_id", ""))
        if chapter_id:
            index[chapter_id.removeprefix("chapter.")] = record
    return index


def _event_id(chapter_id: str, event_index: int, event_slug: str) -> str:
    chapter_number = _chapter_number_from_id(chapter_id)
    book_id = _book_id_from_chapter_id(chapter_id)
    chapter_part = f"{chapter_number:03d}" if chapter_number is not None else "unknown"
    return f"{book_id}.{chapter_part}.event{event_index:03d}.{event_slug}"


CH30_EVENTS = [
    {
        "chapter_id": "book006.030_ummade_army",
        "event_index": 1,
        "event_slug": "army_unmade_by_xalzirith",
        "event_label": "The 249 are unmade by Xal'Zirith",
        "event_type": "MASS_UNMAKING_AFTERMATH",
        "source_anchor_hint": "The Harbinger / warriors are retroactively unmade / Five witness",
        "existing_payoff_evidence": [
            "Geralt witnesses the army cease to exist",
            "Dragon Mail protects Geralt from conceptual erasure",
            "The Five witness and remember the erased warriors",
        ],
        "internal_receipt_status": "PRESENT_BUT_COULD_USE_PERSONAL_CUT",
        "receipt_kind": ["GRIEF_RECEIPT", "WITNESS_VALIDATION", "PRIVATE_INTERNAL_RECEIPT"],
        "missing_or_expected_receipt": "A personal human receipt tied to one remembered soldier, name, face, or ordinary detail may sharpen the loss.",
        "author_action": "Check the immediate aftermath of the unmaking and add one private Geralt receipt only if the loss feels too cosmic and not personal enough.",
        "do_not_change": [
            "Xal'Zirith unmakes the warriors",
            "Geralt survives through Dragon Mail",
            "The Five witness",
            "The erased warriors mattered even when reality forgets",
        ],
    },
    {
        "chapter_id": "book006.030_ummade_army",
        "event_index": 2,
        "event_slug": "camp_denies_249",
        "event_label": "Camp has no knowledge the 249 existed",
        "event_type": "REALITY_DENIAL_AFTER_UNMAKING",
        "source_anchor_hint": "The Return / Mika asks who Dren is / Oreck confirms no deployment records",
        "existing_payoff_evidence": [
            "Mika does not remember the deployment",
            "Oreck confirms logs show no missing warriors",
            "The Five validate Geralt's memory",
        ],
        "internal_receipt_status": "PRESENT_BUT_NEEDS_PERSONAL_CUT",
        "receipt_kind": ["PRIVATE_INTERNAL_RECEIPT", "WITNESS_VALIDATION", "GRIEF_RECEIPT"],
        "missing_or_expected_receipt": "Geralt privately registers that a named person has been erased from another loved one's memory.",
        "author_action": "Add or strengthen one private internal receipt near Mika's 'Who's Dren?' moment.",
        "do_not_change": [
            "Mika does not remember Dren",
            "Oreck finds no record",
            "The Five remember",
            "Geralt is telling the truth",
        ],
    },
    {
        "chapter_id": "book006.030_ummade_army",
        "event_index": 3,
        "event_slug": "heaven_ship_theft_decision",
        "event_label": "Geralt sees the heaven ship and decides to steal/crash it",
        "event_type": "SHIP_THEFT_DECISION",
        "source_anchor_hint": "The Vantage / mound scene / Anunnaki mobile city descends",
        "existing_payoff_evidence": [
            "Geralt isolates himself because shared mourning is impossible",
            "The massive vessel appears over the next compound",
            "Geralt converts grief into an impossible theft/crash plan",
        ],
        "internal_receipt_status": "PRESENT_BUT_WEAPONIZED",
        "receipt_kind": ["GRIEF_RECEIPT", "PRIVATE_INTERNAL_RECEIPT", "COMMAND_REASSESSMENT"],
        "missing_or_expected_receipt": "The emotional hinge should make clear that grief becomes defiance, not merely tactical recklessness.",
        "author_action": "Check the transition from isolation to decision and clarify grief -> defiance -> impossible plan if needed.",
        "do_not_change": [
            "The heaven ship arrives",
            "Geralt chooses theft",
            "The crash plan remains insane and intentional",
            "The erased 249 drive the decision",
        ],
    },
]

CH31_EVENTS = [
    {
        "chapter_id": "book006.031_the_crash_site",
        "event_index": 1,
        "event_slug": "zephyr_crash_triage",
        "event_label": "Zephyr begins crash-site survivor triage",
        "event_type": "CRASH_TRIAGE",
        "source_anchor_hint": "Zephyr enters the wreckage / rescues pinned and wounded survivors",
        "existing_payoff_evidence": [
            "Zephyr hears survivors screaming and crying",
            "He stabilizes wounded survivors",
            "He makes triage decisions under time pressure",
        ],
        "internal_receipt_status": "PRESENT",
        "receipt_kind": ["BODY_COST_RECEIPT", "WORLD_REACTION_RECEIPT"],
        "missing_or_expected_receipt": "No required insertion unless the author wants Zephyr's private burden emphasized.",
        "author_action": "Probably no patch required; triage pressure already reads on-page.",
        "do_not_change": [
            "Zephyr prioritizes living survivors",
            "He uses controlled magic",
            "The crash site remains active catastrophe",
        ],
    },
    {
        "chapter_id": "book006.031_the_crash_site",
        "event_index": 2,
        "event_slug": "kael_roric_survive_sleeping",
        "event_label": "Kael and Roric survive the crash while sleeping",
        "event_type": "IMPOSSIBLE_SURVIVAL_DISCOVERY",
        "source_anchor_hint": "Zephyr hears snoring in the wreckage / Kael and Roric wake",
        "existing_payoff_evidence": [
            "The absurdity of sleeping through the crash gives the scene release",
            "Kael and Roric realize they are free",
            "They see the valley and imagine building a home",
        ],
        "internal_receipt_status": "PRESENT",
        "receipt_kind": ["SHARED_EXTERNAL_RECEIPT", "WORLD_REACTION_RECEIPT"],
        "missing_or_expected_receipt": "No required insertion; the payoff is external and already visible.",
        "author_action": "Probably no patch required unless you want to deepen the first taste of freedom.",
        "do_not_change": ["Kael and Roric survive", "They were enslaved", "They choose the valley/home direction"],
    },
    {
        "chapter_id": "book006.031_the_crash_site",
        "event_index": 3,
        "event_slug": "zephyr_finds_five_bodies",
        "event_label": "Zephyr discovers Gerald's Five among the dead",
        "event_type": "FIVE_BODY_DISCOVERY",
        "source_anchor_hint": "Zephyr recognizes armor/symbol / gathers the Five bodies",
        "existing_payoff_evidence": [
            "Zephyr recognizes Gerald's symbol",
            "He remembers one warrior from Ashren Gate",
            "He gathers the bodies with respect",
        ],
        "internal_receipt_status": "PRESENT_BUT_UNDER_SIGNALED",
        "receipt_kind": ["PRIVATE_INTERNAL_RECEIPT", "BODY_COST_RECEIPT"],
        "missing_or_expected_receipt": "The event pivots Zephyr from saving the living to preserving dead warriors who still matter.",
        "author_action": "Consider one internal recognition receipt around the first body or the moment the pattern becomes clear.",
        "do_not_change": [
            "The Five are dead",
            "Zephyr recognizes their connection to Gerald",
            "He gathers them respectfully",
        ],
    },
    {
        "chapter_id": "book006.031_the_crash_site",
        "event_index": 4,
        "event_slug": "zephyr_protects_bodies_from_salvage",
        "event_label": "Zephyr protects the Five from being treated as salvage/evidence",
        "event_type": "BODY_PROTECTION_FROM_SCAVENGERS",
        "source_anchor_hint": "Scavengers demand the armor / Anunnaki security calls the bodies evidence",
        "existing_payoff_evidence": [
            "Zephyr refuses to let scavengers strip the dead",
            "Zephyr tells security the bodies deserve better than salvage",
            "Zephyr redirects guards toward living survivors",
        ],
        "internal_receipt_status": "PRESENT",
        "receipt_kind": ["BODY_COST_RECEIPT", "SHARED_EXTERNAL_RECEIPT"],
        "missing_or_expected_receipt": "No required insertion; the respect/payoff is already dramatized through conflict.",
        "author_action": "Probably no patch required unless the body-protection theme needs stronger continuity into Echo Tower.",
        "do_not_change": [
            "Zephyr protects the bodies",
            "The scavengers leave",
            "The Anunnaki guards are redirected",
            "The bodies remain with Zephyr",
        ],
    },
    {
        "chapter_id": "book006.031_the_crash_site",
        "event_index": 5,
        "event_slug": "echo_tower_resurrection_route",
        "event_label": "Zephyr decides the Five's journey continues through Echo Tower",
        "event_type": "ECHO_TOWER_ROUTING",
        "source_anchor_hint": "Cliffhanger / Zephyr senses potential in the bodies / turns toward Echo Tower",
        "existing_payoff_evidence": [
            "Zephyr senses lingering resonance",
            "He recognizes the bodies may become vessels for something beyond resurrection",
            "He turns toward Echo Tower",
        ],
        "internal_receipt_status": "PRESENT_BUT_COMPRESSED",
        "receipt_kind": ["RESPONSIBILITY_SETTLING_RECEIPT", "DOCTRINE_ABSORPTION_RECEIPT"],
        "missing_or_expected_receipt": "The chapter shifts from crash rescue to resurrection routing quickly; the responsibility of that choice may need one settling beat.",
        "author_action": "Check the cliffhanger for one beat showing Zephyr understands the cost/responsibility of taking the dead toward the Tower.",
        "do_not_change": [
            "The Five are dead",
            "Zephyr senses potential",
            "Echo Tower becomes the next route",
            "This is not simple resurrection yet",
        ],
    },
]

CH32_TO_CH38_EVENTS = [
    {
        "chapter_id": "book006.032_the_redo",
        "event_index": 1,
        "event_slug": "redo_transition_state_change",
        "event_label": "Redo/recovery state transition",
        "event_type": "COMMAND_REASSESSMENT",
        "source_anchor_hint": "CH032 / verify exact section manually",
        "existing_payoff_evidence": [],
        "internal_receipt_status": "PRESENT_BUT_UNDER_SIGNALED",
        "receipt_kind": ["COMMAND_REASSESSMENT", "PRIVATE_INTERNAL_RECEIPT"],
        "missing_or_expected_receipt": "The author should confirm whether the redo/recovery event has a nearby internal receipt.",
        "author_action": "Locate the major redo transition and add one internal receipt only if the event jumps too quickly.",
        "do_not_change": ["Do not reorder canon events", "Do not rewrite from diagnostic"],
    },
    {
        "chapter_id": "book006.033_the_march",
        "event_index": 1,
        "event_slug": "mika_command_uncertainty",
        "event_label": "Mika leads through rescue uncertainty",
        "event_type": "COMMAND_REASSESSMENT",
        "source_anchor_hint": "The March / Mika movement and rescue command",
        "existing_payoff_evidence": [],
        "internal_receipt_status": "PRESENT_BUT_UNDER_SIGNALED",
        "receipt_kind": ["COMMAND_REASSESSMENT", "PRIVATE_INTERNAL_RECEIPT"],
        "missing_or_expected_receipt": "Mika may need a private reassessment beat before the next revelation or movement change.",
        "author_action": "Locate Mika's command movement and add one decision-pressure receipt if needed.",
        "do_not_change": ["Mika leads the rescue force", "The march continues", "Canon route stays intact"],
    },
    {
        "chapter_id": "book006.034_the_250",
        "event_index": 1,
        "event_slug": "250_restored_survivors",
        "event_label": "The 250 return/restored survivors are not immediately whole",
        "event_type": "RESTORED_SURVIVOR_REINTEGRATION",
        "source_anchor_hint": "The 250 / restoration or retrieval moment",
        "existing_payoff_evidence": [],
        "internal_receipt_status": "MISSING",
        "receipt_kind": ["BODY_COST_RECEIPT", "SHARED_EXTERNAL_RECEIPT", "GRIEF_RECEIPT"],
        "missing_or_expected_receipt": "Restored survivors should feel present but not immediately whole, ready, or fully reassembled inside themselves.",
        "author_action": "Add a reintegration receipt near the restoration/retrieval moment if the 250 move too quickly into usefulness.",
        "do_not_change": ["The 250 are restored", "Geralt held the door", "The group continues"],
    },
    {
        "chapter_id": "book006.035_sands_of_time",
        "event_index": 1,
        "event_slug": "temporal_law_curriculum",
        "event_label": "Geralt learns temporal mechanics/laws",
        "event_type": "TEMPORAL_LAW_DISCOVERY",
        "source_anchor_hint": "Sands of Time / chroniton nodes, corrupted spires, sinkholes, loop anchors, fracture mechanics",
        "existing_payoff_evidence": [],
        "internal_receipt_status": "PRESENT_BUT_COMPRESSED",
        "receipt_kind": ["DOCTRINE_ABSORPTION_RECEIPT", "PRIVATE_INTERNAL_RECEIPT"],
        "missing_or_expected_receipt": "Each major temporal law may need a short absorption receipt before the next mechanic appears.",
        "author_action": "Locate each temporal law cluster and add only the receipts needed to separate mechanics.",
        "do_not_change": ["Temporal laws stay distinct", "Do not simplify canon mechanics", "Do not reorder training logic"],
    },
    {
        "chapter_id": "book006.036_highland_giants",
        "event_index": 1,
        "event_slug": "highland_giants_awe_spire_responsibility",
        "event_label": "Highland Giants, awe, and Spire responsibility converge",
        "event_type": "GIANT_AWE_AND_RESPONSIBILITY",
        "source_anchor_hint": "Highland Giants / Althurion / Giant trials / Buried Resonance / Needle Spire",
        "existing_payoff_evidence": [],
        "internal_receipt_status": "PRESENT_BUT_COMPRESSED",
        "receipt_kind": ["WORLD_REACTION_RECEIPT", "RESPONSIBILITY_SETTLING_RECEIPT"],
        "missing_or_expected_receipt": "Awe and responsibility should slow the scene before the next lore doorway opens.",
        "author_action": "Patch around the Giant/Spire transition if it moves directly from encounter to lore routing.",
        "do_not_change": ["Highland Giants remain significant", "Spire activation remains responsibility", "Do not remove canon events"],
    },
    {
        "chapter_id": "book007.037_the_circle_of_progress",
        "event_index": 1,
        "event_slug": "circle_progress_state_transition",
        "event_label": "Circle of Progress state transition",
        "event_type": "COMMAND_REASSESSMENT",
        "source_anchor_hint": "The Circle of Progress / verify exact event manually",
        "existing_payoff_evidence": [],
        "internal_receipt_status": "PRESENT_BUT_UNDER_SIGNALED",
        "receipt_kind": ["COMMAND_REASSESSMENT", "RESPONSIBILITY_SETTLING_RECEIPT"],
        "missing_or_expected_receipt": "The author should confirm whether the state transition has a nearby receipt before the next system movement.",
        "author_action": "Locate the main Circle of Progress event and add a receipt only if the transition feels abrupt.",
        "do_not_change": ["Do not rewrite from diagnostic", "Do not reorder canon events"],
    },
    {
        "chapter_id": "book007.038_luminaire_keeper",
        "event_index": 1,
        "event_slug": "luminaire_keeper_responsibility_transfer",
        "event_label": "Luminaire keeper responsibility transfer",
        "event_type": "KEEPER_RESPONSIBILITY_TRANSFER",
        "source_anchor_hint": "Luminaire Keeper / keeper setup and role direction",
        "existing_payoff_evidence": [],
        "internal_receipt_status": "PRESENT_BUT_COMPRESSED",
        "receipt_kind": ["RESPONSIBILITY_SETTLING_RECEIPT", "DOCTRINE_ABSORPTION_RECEIPT"],
        "missing_or_expected_receipt": "The character should feel the weight of being directed toward a larger keeper role.",
        "author_action": "Add or strengthen one responsibility-settling receipt near the keeper-direction moment if needed.",
        "do_not_change": ["Luminaire role remains", "Keeper responsibility remains", "Do not create replacement prose"],
    },
]


def _seed_ch30_ch38_events() -> list[dict[str, Any]]:
    return [dict(event) for event in [*CH30_EVENTS, *CH31_EVENTS, *CH32_TO_CH38_EVENTS]]


def _attach_pressure_signal(seed: dict[str, Any], breathing_index: dict[str, dict[str, Any]]) -> dict[str, Any]:
    record = dict(seed)
    chapter_id = str(record["chapter_id"])
    pressure = breathing_index.get(chapter_id, {})
    record["breathing_map_pressure_signal"] = {
        key: pressure[key]
        for key in [
            "pressure_score",
            "pressure_rank_global",
            "pressure_tier_global",
            "pressure_rank_within_book",
            "pressure_tier_within_book",
            "primary_pressure_source",
            "claim_density",
        ]
        if key in pressure
    }
    return record


def _iter_values(value: Any) -> Iterable[Any]:
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from _iter_values(item)
    elif isinstance(value, list):
        for item in value:
            yield from _iter_values(item)
    else:
        yield value


def _validate_record(record: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = [
        "contract",
        "chapter_id",
        "book_id",
        "chapter_number",
        "event_id",
        "event_index",
        "event_label",
        "event_type",
        "source_anchor_hint",
        "existing_payoff_evidence",
        "internal_receipt_status",
        "receipt_kind",
        "missing_or_expected_receipt",
        "author_action",
        "do_not_change",
        "revision_priority",
        "author_action_required",
        "source_basis",
        "breathing_map_pressure_signal",
        "safety_locks",
    ]
    for field in required:
        if field not in record:
            errors.append(f"missing required field: {field}")
    if record.get("contract") != CONTRACT_RECORD:
        errors.append("invalid contract")
    if record.get("event_type") not in EVENT_TYPES:
        errors.append(f"invalid event_type: {record.get('event_type')}")
    if record.get("internal_receipt_status") not in INTERNAL_RECEIPT_STATUSES:
        errors.append(f"invalid internal_receipt_status: {record.get('internal_receipt_status')}")
    status = str(record.get("internal_receipt_status"))
    if record.get("revision_priority") not in REVISION_PRIORITIES:
        errors.append(f"invalid revision_priority: {record.get('revision_priority')}")
    if status in REVISION_PRIORITY_BY_STATUS and record.get("revision_priority") != REVISION_PRIORITY_BY_STATUS[status]:
        errors.append(f"revision_priority must be {REVISION_PRIORITY_BY_STATUS[status]} for {status}")
    if not isinstance(record.get("receipt_kind"), list) or not record.get("receipt_kind"):
        errors.append("receipt_kind must be non-empty list")
    else:
        for kind in record["receipt_kind"]:
            if kind not in RECEIPT_KINDS:
                errors.append(f"invalid receipt_kind: {kind}")
    for list_field in ["existing_payoff_evidence", "do_not_change", "safety_locks"]:
        if not isinstance(record.get(list_field), list):
            errors.append(f"{list_field} must be list")
    if status in AUTHOR_ACTION_REQUIRED_BY_STATUS and record.get("author_action_required") is not AUTHOR_ACTION_REQUIRED_BY_STATUS[status]:
        errors.append(f"author_action_required must be {AUTHOR_ACTION_REQUIRED_BY_STATUS[status]} for {status}")
    if record.get("safety_locks") != SAFETY_LOCKS:
        errors.append("safety_locks mismatch")
    for flag, expected in NEGATIVE_FLAGS.items():
        if record.get(flag) is not expected:
            errors.append(f"{flag} must be {expected}")
    serialized_keys_and_values = {str(value) for value in _iter_values(record)}
    for forbidden in FORBIDDEN_FIELDS:
        if forbidden in serialized_keys_and_values:
            errors.append(f"forbidden rewrite field present: {forbidden}")
    return errors


def build_internal_receipt_records(engain_dir: Path) -> tuple[list[dict[str, Any]], list[str]]:
    errors: list[str] = []
    breathing_index = _load_breathing_map(engain_dir)
    records: list[dict[str, Any]] = []
    for seed in _seed_ch30_ch38_events():
        chapter_id = str(seed["chapter_id"])
        chapter_number = _chapter_number_from_id(chapter_id)
        record = _attach_pressure_signal(seed, breathing_index)
        status = str(record["internal_receipt_status"])
        record.update(
            {
                "contract": CONTRACT_RECORD,
                "book_id": _book_id_from_chapter_id(chapter_id),
                "chapter_number": chapter_number,
                "event_id": _event_id(chapter_id, int(seed["event_index"]), str(seed["event_slug"])),
                "source_basis": SOURCE_BASIS,
                "safety_locks": list(SAFETY_LOCKS),
                "revision_priority": REVISION_PRIORITY_BY_STATUS[status],
                "author_action_required": AUTHOR_ACTION_REQUIRED_BY_STATUS[status],
                **NEGATIVE_FLAGS,
            }
        )
        validation_errors = _validate_record(record)
        errors.extend(f"{record.get('event_id', '<unknown>')}: {error}" for error in validation_errors)
        records.append(record)
    records.sort(key=lambda item: (str(item["book_id"]), int(item["chapter_number"] or 0), int(item["event_index"])))
    return records, errors


def _chapter_heading(record: dict[str, Any]) -> str:
    return f"CH{int(record['chapter_number']):03d} — {record['chapter_id']}"


def _append_list(lines: list[str], title: str, values: list[str]) -> None:
    lines.extend(["", f"{title}:"])
    if values:
        lines.extend(f"- {value}" for value in values)
    else:
        lines.append("- none recorded in deterministic V1 seed")


def write_internal_receipt_markdown(records: list[dict[str, Any]], out_path: Path, title: str) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# {title}",
        "",
        "Event-level revision target map.",
        "This is not a rewrite tool.",
        "This is not chapter-wide emotional advice.",
        "",
        "## Safety locks",
        "",
    ]
    lines.extend(f"- {lock}" for lock in SAFETY_LOCKS)
    priority_titles = {
        "PATCH_REQUIRED": "Patch Required",
        "OPTIONAL_REVIEW": "Optional Review",
        "NO_PATCH_EXPECTED": "No Patch Expected",
    }
    for priority in ["PATCH_REQUIRED", "OPTIONAL_REVIEW", "NO_PATCH_EXPECTED"]:
        priority_records = [record for record in records if record.get("revision_priority") == priority]
        lines.extend(["", f"## {priority_titles[priority]}", ""])
        if priority_records:
            for record in priority_records:
                lines.append(
                    f"- {_chapter_heading(record).split(' — ', 1)[0]} Event {record['event_index']} — {record['event_label']}"
                )
        else:
            lines.append("- none")
    current_chapter = ""
    for record in records:
        heading = _chapter_heading(record)
        if heading != current_chapter:
            lines.extend(["", f"## {heading}", ""])
            current_chapter = heading
        lines.extend(
            [
                f"### Event {record['event_index']} — {record['event_label']}",
                f"- Event type: {record['event_type']}",
                f"- Receipt status: {record['internal_receipt_status']}",
                f"- Revision priority: {record['revision_priority']}",
                f"- Author action required: {str(record['author_action_required']).lower()}",
                f"- Receipt kind: {', '.join(record['receipt_kind'])}",
                f"- Source anchor: {record['source_anchor_hint']}",
                f"- Patch target: {record['source_anchor_hint']}",
            ]
        )
        pressure_signal = record.get("breathing_map_pressure_signal", {})
        if pressure_signal:
            lines.append(f"- Breathing pressure signal: {json.dumps(pressure_signal, ensure_ascii=False, sort_keys=True)}")
        _append_list(lines, "Existing payoff evidence", record["existing_payoff_evidence"])
        lines.extend(["", "Missing or expected receipt:", str(record["missing_or_expected_receipt"])])
        lines.extend(["", "Author action:", str(record["author_action"])])
        _append_list(lines, "Do not change", record["do_not_change"])
        lines.extend(["", "Author action required:", str(record["author_action_required"]).lower(), ""])
    out_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _paths(engain_dir: Path) -> dict[str, Path]:
    revision_dir = engain_dir / "mrlore" / "revision"
    return {
        "jsonl": revision_dir / "internal_receipt_map.jsonl",
        "markdown": revision_dir / "internal_receipt_map.md",
        "focus_markdown": revision_dir / "focus" / "ch30_ch38_internal_receipt_map.md",
        "manifest": engain_dir / "manifests" / "mrlore_major_event_internal_receipt_map_manifest.json",
    }


def _filter_records(
    records: list[dict[str, Any]],
    book_id: str | None = None,
    chapter_id: str | None = None,
    chapter_number: int | None = None,
) -> list[dict[str, Any]]:
    filtered = records
    if book_id is not None:
        filtered = [record for record in filtered if record.get("book_id") == book_id]
    if chapter_id is not None:
        filtered = [record for record in filtered if record.get("chapter_id") == chapter_id]
    if chapter_number is not None:
        filtered = [record for record in filtered if record.get("chapter_number") == chapter_number]
    return filtered


def run_major_event_internal_receipt_map(
    engain_dir: Path | str | None = None,
    book_id: str | None = None,
    chapter_id: str | None = None,
    chapter_number: int | None = None,
) -> dict[str, Any]:
    resolved_engain_dir = Path(engain_dir) if engain_dir is not None else default_engain_dir()
    paths = _paths(resolved_engain_dir)
    records, errors = build_internal_receipt_records(resolved_engain_dir)
    records = _filter_records(records, book_id=book_id, chapter_id=chapter_id, chapter_number=chapter_number)
    _write_jsonl(paths["jsonl"], records)
    title_suffix_parts = []
    if book_id is not None:
        title_suffix_parts.append(book_id)
    if chapter_id is not None:
        title_suffix_parts.append(chapter_id)
    if chapter_number is not None:
        title_suffix_parts.append(f"CH{chapter_number:03d}")
    title_suffix = f" — {' / '.join(title_suffix_parts)}" if title_suffix_parts else ""
    write_internal_receipt_markdown(records, paths["markdown"], f"MrLore Major Event Internal Receipt Map{title_suffix}")
    focus_records = [
        record
        for record in records
        if (record.get("chapter_number") is not None and 30 <= int(record["chapter_number"]) <= 38)
    ]
    write_internal_receipt_markdown(focus_records, paths["focus_markdown"], f"MrLore Major Event Internal Receipt Map — CH30–CH38 Focus{title_suffix}")
    breathing_read = bool(_load_breathing_map(resolved_engain_dir))
    chapters_covered = sorted({str(record["chapter_id"]) for record in records})
    manifest = {
        "contract": CONTRACT_MANIFEST,
        "MRLORE_MAJOR_EVENT_INTERNAL_RECEIPT_MAP_COMPLETE": len(errors) == 0,
        "MRLORE_MAJOR_EVENT_INTERNAL_RECEIPT_MAP_V1": True,
        "MRLORE_MAJOR_EVENT_INTERNAL_RECEIPT_MAP_V1_1_AUTHOR_PRIORITY_CLEANUP": True,
        "SEEDED_CH30_CH38_EVENT_MAP": True,
        "UNIVERSAL_EVENT_EXTRACTION_USED": False,
        "FILTER_BOOK_ID": book_id,
        "FILTER_CHAPTER_ID": chapter_id,
        "FILTER_CHAPTER_NUMBER": chapter_number,
        "EVENT_RECORDS_WRITTEN": len(records),
        "CHAPTERS_COVERED": chapters_covered,
        "FOCUS_CH30_CH38_WRITTEN": paths["focus_markdown"].exists(),
        "BREATHING_MAP_READ": breathing_read,
        "BREATHING_MAP_USED_AS_PRESSURE_SIGNAL_ONLY": True,
        "AUTHOR_ACTION_REQUIRED_RECORDS": sum(1 for record in records if record.get("author_action_required") is True),
        "SAFETY_LOCKS_PRESENT": all(record.get("safety_locks") == SAFETY_LOCKS for record in records),
        **NEGATIVE_FLAGS,
        "errors_count": len(errors),
        "errors": errors,
        "run_timestamp": datetime.now(timezone.utc).isoformat(),
        "engain_dir": str(resolved_engain_dir),
        "output_jsonl_path": str(paths["jsonl"]),
        "output_markdown_path": str(paths["markdown"]),
        "focus_markdown_path": str(paths["focus_markdown"]),
        "manifest_path": str(paths["manifest"]),
    }
    paths["manifest"].parent.mkdir(parents=True, exist_ok=True)
    paths["manifest"].write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Write MrLore major event internal receipt map V1.")
    parser.add_argument("--engain-dir", default=None, help="Direct path to vault/.engain.")
    parser.add_argument("--manifest", default=None, help="Path to tier1/engainos/assets/engain_manifest.json.")
    parser.add_argument("--book-id", default=None, help="Optional book filter, e.g. book006 or book007.")
    parser.add_argument("--chapter-id", default=None, help="Optional exact chapter_id filter, e.g. book006.031_the_crash_site.")
    parser.add_argument("--chapter-number", type=int, default=None, help="Optional chapter number filter, e.g. 31.")
    args = parser.parse_args()
    engain_dir = Path(args.engain_dir) if args.engain_dir else default_engain_dir(Path(args.manifest) if args.manifest else None)
    manifest = run_major_event_internal_receipt_map(
        engain_dir=engain_dir,
        book_id=args.book_id,
        chapter_id=args.chapter_id,
        chapter_number=args.chapter_number,
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if manifest.get("MRLORE_MAJOR_EVENT_INTERNAL_RECEIPT_MAP_COMPLETE") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
