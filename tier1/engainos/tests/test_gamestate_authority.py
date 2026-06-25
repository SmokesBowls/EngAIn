from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tier1.engainos.gates.gate_gamestate_draft_review_ready import build_draft_review_result


FORBIDDEN_GATE_NAMES = {
    "GATE_NO_COMMITTED_GAMESTATE_FIELDS",
    "GATE_NO_WORKER_START_FIELDS",
}


def clean_payload() -> dict[str, Any]:
    return {
        "contract": "tier1.engainos.gamestate_draft.v1",
        "source": "tier1.engainos.zonj_runtime_acceptance_adapter",
        "authority_tier": 1,
        "authority_lane": "zonj_runtime_acceptance_adapter",
        "scene_id": "scene.gamestate_authority_toxic_test",
        "draft_status": "PENDING_ACCEPTANCE",
        "accepted_for_runtime": False,
        "declaration_count": 1,
        "draft_empty": False,
        "runtime_meaningful": True,
        "gate_results": [
            {
                "gate_name": "GATE_TEST_ADAPTER_READY",
                "status": "TRUE",
                "message": "test adapter gate passed",
                "details": {},
            }
        ],
        "entities": [
            {
                "entity_id": "hero",
                "entity_type": "character",
                "metadata": {},
                "tags": ["valid_tag", "still_valid"],
            }
        ],
        "proposed_changes": [],
        "validated_packets": [],
        "safe_note": "not_worker_start",
    }


def gate_by_name(result: Any, gate_name: str) -> dict[str, Any]:
    for gate in result.gate_results:
        if gate["gate_name"] == gate_name:
            return gate
    raise AssertionError(f"missing gate result: {gate_name}")


def failing_forbidden_gate(result: Any) -> dict[str, Any]:
    for gate in result.gate_results:
        if gate["gate_name"] in FORBIDDEN_GATE_NAMES and gate["status"] == "FALSE":
            return gate
    raise AssertionError("no forbidden authority gate failed")


def assert_review_fail_with_violation(payload: dict[str, Any], expected_path: str) -> None:
    result = build_draft_review_result(payload)

    assert result.review_status == "GAMESTATE_DRAFT_REVIEW_REJECTED"
    assert result.accepted_for_runtime is False
    assert result.committed_gamestate is False
    assert result.starts_workers is False

    gate = failing_forbidden_gate(result)
    assert expected_path in gate["details"]["violations"]


def test_01_top_level_worker_start_key_makes_gate_result_fail() -> None:
    payload = clean_payload()
    payload["worker_start"] = True

    assert_review_fail_with_violation(payload, "worker_start")


def test_02_nested_worker_start_key_makes_gate_result_fail() -> None:
    payload = clean_payload()
    payload["entities"][0]["metadata"]["worker_start"] = True

    assert_review_fail_with_violation(payload, "entities[0].metadata.worker_start")


def test_03_worker_start_string_inside_list_makes_gate_result_fail() -> None:
    payload = clean_payload()
    payload["entities"][0]["tags"][1] = "worker_start"

    assert_review_fail_with_violation(payload, "entities[0].tags[1]")


def test_04_committed_gamestate_string_nested_five_levels_deep_makes_gate_result_fail() -> None:
    payload = clean_payload()
    payload["a"] = {"b": {"c": {"d": {"e": "committed_gamestate"}}}}

    assert_review_fail_with_violation(payload, "a.b.c.d.e")


def test_05_runtime_execute_key_mixed_with_valid_payload_makes_gate_result_fail() -> None:
    payload = clean_payload()
    payload["runtime_execute"] = {"allowed_payload": deepcopy(payload["entities"])}

    assert_review_fail_with_violation(payload, "runtime_execute")


def test_06_clean_payload_makes_gate_result_pass() -> None:
    result = build_draft_review_result(clean_payload())

    assert result.review_status == "GAMESTATE_DRAFT_REVIEW_READY"
    assert result.accepted_for_runtime is False
    assert result.committed_gamestate is False
    assert result.starts_workers is False
    assert gate_by_name(result, "GATE_NO_COMMITTED_GAMESTATE_FIELDS")["status"] == "TRUE"
    assert gate_by_name(result, "GATE_NO_WORKER_START_FIELDS")["status"] == "TRUE"
