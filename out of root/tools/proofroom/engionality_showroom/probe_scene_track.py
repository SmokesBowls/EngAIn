from __future__ import annotations

from typing import Any

from tools.proofroom.engionality_showroom.showroom_fake_env import (
    FAKE_PERFORMANCE_TASK,
    fake_output_capture,
    is_json_serializable,
    no_authority_claim,
    print_gate_results,
    to_jsonable,
)


def run_probe() -> dict[str, bool]:
    result: Any = None
    imported = False
    accepts = False
    timing_valid = False
    metadata_preserved = False
    with fake_output_capture():
        try:
            from tier2.engionality.controlroom.task_types import Clip, ClipType, PerformanceTask, PerformanceTaskType  # noqa: F401
            from tier2.engionality.showroom.scene_track import SceneTrack

            imported = True
            track = SceneTrack(id="scene.fake_showroom_probe")
            clip_late = Clip(
                id="clip_late",
                type=ClipType.DIALOGUE,
                start_time=1.0,
                duration=0.8,
                payload={"metadata": dict(FAKE_PERFORMANCE_TASK["metadata"]), "task_id": FAKE_PERFORMANCE_TASK["task_id"]},
                tags=["probe", "dialogue"],
            )
            clip_early = Clip(
                id="clip_early",
                type=ClipType.AUDIO,
                start_time=0.25,
                duration=0.5,
                payload={"metadata": dict(FAKE_PERFORMANCE_TASK["metadata"]), "task_id": FAKE_PERFORMANCE_TASK["task_id"]},
                tags=["probe", "audio"],
            )
            track.add_clip("dialogue", clip_late)
            track.add_clip("dialogue", clip_early)
            result = track.tracks["dialogue"].clips
            accepts = len(result) == 2
            starts = [clip.start_time for clip in result]
            timing_valid = starts == sorted(starts)
            metadata_preserved = all(
                clip.payload.get("metadata", {}).get("probe") is True
                and clip.payload.get("metadata", {}).get("real_runtime") is False
                for clip in result
            )
        except Exception as exc:
            result = {"error": repr(exc)}
    checks = {
        "SCENE_TRACK_IMPORT": imported,
        "SCENE_TRACK_ACCEPTS_CLIPS": accepts,
        "SCENE_TRACK_TIMING_ORDER_VALID": timing_valid,
        "SCENE_TRACK_METADATA_PRESERVED": metadata_preserved,
        "SCENE_TRACK_OUTPUT_SERIALIZABLE": is_json_serializable(result),
        "SCENE_TRACK_NO_RENDER_AUTHORITY": no_authority_claim(to_jsonable(result)),
    }
    checks["SCENE_TRACK_ALL_GATES"] = all(checks.values())
    return checks


if __name__ == "__main__":
    print_gate_results(run_probe())
