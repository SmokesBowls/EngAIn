from __future__ import annotations

from typing import Any

from tools.proofroom.engionality_showroom.showroom_fake_env import (
    clip_to_cue,
    fake_output_capture,
    is_json_serializable,
    make_domain_views_from_fake_task,
    no_authority_claim,
    no_mutation_claim,
    print_gate_results,
    to_jsonable,
)


def run_probe() -> dict[str, bool]:
    result: Any = None
    imported = False
    accepts = False
    emits_cue = False
    has_timing = False
    with fake_output_capture():
        try:
            from tier2.engionality.controlroom.task_types import Clip, ClipType, PerformanceTask, PerformanceTaskType  # noqa: F401
            from tier2.engionality.showroom.animation_engine import AnimationEngine, AnimationEngineConfig
            from tier2.engionality.showroom.scene_track import SceneTrack

            imported = True
            track = SceneTrack(id="scene.fake_showroom_probe")
            engine = AnimationEngine(AnimationEngineConfig())
            view = make_domain_views_from_fake_task()["animation_view"]
            engine.update_from_animation_view(track, 1042, 0.0, view)
            animation_track = track.tracks.get("animation")
            clips = animation_track.clips if animation_track is not None else []
            accepts = True
            result = [clip_to_cue(clip, "animation") for clip in clips]
            emits_cue = any(cue.get("cue") == "gesture_guarded" for cue in result)
            has_timing = any(cue.get("duration_ms") == 1800 and cue.get("start_ms") == 0 for cue in result)
        except Exception as exc:
            result = {"error": repr(exc)}
    checks = {
        "ANIMATION_IMPORT": imported,
        "ANIMATION_ACCEPTS_TASK": accepts,
        "ANIMATION_EMITS_CUE": emits_cue,
        "ANIMATION_HAS_TIMING": has_timing,
        "ANIMATION_NO_MECHANIMATION_CLAIM": no_authority_claim(to_jsonable(result)) and no_mutation_claim(to_jsonable(result)),
        "ANIMATION_NO_RENDER_AUTHORITY": no_authority_claim(to_jsonable(result)),
        "ANIMATION_OUTPUT_SERIALIZABLE": is_json_serializable(result),
    }
    checks["ANIMATION_ALL_GATES"] = all(checks.values())
    return checks


if __name__ == "__main__":
    print_gate_results(run_probe())
