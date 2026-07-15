from __future__ import annotations

from typing import Any

from tools.proofroom.engionality_showroom.showroom_fake_env import (
    fake_output_capture,
    is_json_serializable,
    make_domain_views_from_fake_task,
    no_authority_claim,
    print_gate_results,
    to_jsonable,
)


def run_probe() -> dict[str, bool]:
    result: Any = None
    imported = False
    accepted = False
    routed = False
    with fake_output_capture():
        try:
            from tier2.engionality.controlroom.task_types import PerformanceTask  # noqa: F401
            from tier2.engionality.showroom.performer_engine import PerformerEngine

            imported = True
            engine = PerformerEngine()
            result = engine.step(
                tick_id=1042,
                delta_time=0.1,
                domain_views=make_domain_views_from_fake_task(),
            )
            accepted = isinstance(result, list)
            routed = accepted and len(result) >= 3
        except Exception as exc:
            result = {"error": repr(exc)}
    checks = {
        "PERFORMER_IMPORT": imported,
        "PERFORMER_ACCEPTS_TASK": accepted,
        "PERFORMER_ROUTES_TO_SUBENGINES": routed,
        "PERFORMER_OUTPUT_SERIALIZABLE": is_json_serializable(result),
        "PERFORMER_NO_AUTHORITY_CLAIM": no_authority_claim(to_jsonable(result)),
    }
    checks["PERFORMER_ALL_GATES"] = all(checks.values())
    return checks


if __name__ == "__main__":
    print_gate_results(run_probe())
