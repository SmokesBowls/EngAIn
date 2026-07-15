from __future__ import annotations

import copy
from typing import Any

from tools.proofroom.engionality_showroom.showroom_fake_env import (
    FAKE_STATE,
    fake_output_capture,
    is_json_serializable,
    no_authority_claim,
    print_gate_results,
    to_jsonable,
)

EXPECTED_DOMAIN_KEYS = {"narrative_view", "audio_view", "animation_view", "spatial_view", "ap_rules_view"}


def run_probe() -> dict[str, bool]:
    result: Any = None
    imported = False
    accepts = False
    has_domains = False
    does_not_mutate = False
    no_invented_entities = False
    with fake_output_capture():
        state = copy.deepcopy(FAKE_STATE)
        before = copy.deepcopy(state)
        try:
            from tier2.engionality.showroom.domain_views import generate_domain_views_from_state

            imported = True
            result = generate_domain_views_from_state(state, int(state["tick"]))
            accepts = isinstance(result, dict)
            has_domains = bool(EXPECTED_DOMAIN_KEYS.intersection(set(result.keys())))
            does_not_mutate = state == before
            result_entities = set()
            for value in to_jsonable(result).values() if isinstance(to_jsonable(result), dict) else []:
                if isinstance(value, dict) and "entities" in value and isinstance(value["entities"], dict):
                    result_entities.update(value["entities"].keys())
            no_invented_entities = result_entities.issubset(set(before.get("entities", {}).keys()))
        except Exception as exc:
            result = {"error": repr(exc)}
    checks = {
        "DOMAIN_VIEWS_IMPORT": imported,
        "DOMAIN_VIEWS_ACCEPTS_STATE": accepts,
        "DOMAIN_VIEWS_OUTPUT_HAS_DOMAINS": has_domains,
        "DOMAIN_VIEWS_DOES_NOT_MUTATE_INPUT": does_not_mutate,
        "DOMAIN_VIEWS_OUTPUT_SERIALIZABLE": is_json_serializable(result),
        "DOMAIN_VIEWS_NO_AUTHORITY_CLAIM": no_authority_claim(to_jsonable(result)) and no_invented_entities,
    }
    checks["DOMAIN_VIEWS_ALL_GATES"] = all(checks.values())
    return checks


if __name__ == "__main__":
    print_gate_results(run_probe())
