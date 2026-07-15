from __future__ import annotations

from typing import Any

from tools.proofroom.engionality_showroom.showroom_fake_env import (
    FAKE_PERFORMANCE_TASK,
    clip_to_cue,
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
    accepts = False
    emits_line = False
    preserves_text = False
    with fake_output_capture():
        try:
            from tier2.engionality.controlroom.task_types import Clip, ClipType, PerformanceTask, PerformanceTaskType  # noqa: F401
            from tier2.engionality.showroom.dialogue_engine import DialogueEngine, DialogueEngineConfig
            from tier2.engionality.showroom.scene_track import SceneTrack

            imported = True
            track = SceneTrack(id="scene.fake_showroom_probe")
            engine = DialogueEngine(DialogueEngineConfig())
            view = make_domain_views_from_fake_task()["narrative_view"]
            engine.update_from_narrative_view(track, 1042, 0.0, view)
            dialogue_track = track.tracks.get("dialogue")
            clips = dialogue_track.clips if dialogue_track is not None else []
            accepts = True
            result = [clip_to_cue(clip, "dialogue") for clip in clips]
            emits_line = len(result) > 0 and all(cue.get("engine") == "dialogue" for cue in result)
            preserves_text = any(
                cue.get("raw_clip", {}).get("payload", {}).get("line") == FAKE_PERFORMANCE_TASK["line"]
                for cue in result
            )
        except Exception as exc:
            result = {"error": repr(exc)}
    checks = {
        "DIALOGUE_IMPORT": imported,
        "DIALOGUE_ACCEPTS_TASK": accepts,
        "DIALOGUE_EMITS_LINE_CUE": emits_line,
        "DIALOGUE_PRESERVES_TEXT": preserves_text,
        "DIALOGUE_NO_CANON_CLAIM": no_authority_claim(to_jsonable(result)),
        "DIALOGUE_NO_BRANCH_AUTHORITY": no_authority_claim(to_jsonable(result)),
        "DIALOGUE_OUTPUT_SERIALIZABLE": is_json_serializable(result),
    }
    checks["DIALOGUE_ALL_GATES"] = all(checks.values())
    return checks


if __name__ == "__main__":
    print_gate_results(run_probe())
