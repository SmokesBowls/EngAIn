from __future__ import annotations

from typing import Any

from tools.proofroom.engionality_showroom.showroom_fake_env import (
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
    emits_cue = False
    timing_valid = False
    no_file_write_required = False
    with fake_output_capture() as fake_dir:
        before = set(fake_dir.iterdir())
        try:
            from tier2.engionality.controlroom.task_types import Clip, ClipType, PerformanceTask, PerformanceTaskType  # noqa: F401
            from tier2.engionality.showroom.audio_engine import AudioEngine, AudioEngineConfig
            from tier2.engionality.showroom.scene_track import SceneTrack

            imported = True
            track = SceneTrack(id="scene.fake_showroom_probe")
            engine = AudioEngine(AudioEngineConfig())
            view = make_domain_views_from_fake_task()["audio_view"]
            engine.update_from_audio_view(track, 1042, 0.0, view)
            sfx_track = track.tracks.get("sfx")
            clips = sfx_track.clips if sfx_track is not None else []
            accepts = True
            result = [clip_to_cue(clip, "audio") for clip in clips]
            emits_cue = any(cue.get("cue") == "voice_guarded_low" for cue in result)
            timing_valid = any(cue.get("duration_ms") == 1800 and cue.get("start_ms") == 0 for cue in result)
            no_file_write_required = set(fake_dir.iterdir()) == before
        except Exception as exc:
            result = {"error": repr(exc)}
    checks = {
        "AUDIO_IMPORT": imported,
        "AUDIO_ACCEPTS_TASK": accepts,
        "AUDIO_EMITS_CUE": emits_cue,
        "AUDIO_TIMING_VALID": timing_valid,
        "AUDIO_NO_FILE_WRITE_REQUIRED": no_file_write_required,
        "AUDIO_NO_RUNTIME_AUTHORITY": no_authority_claim(to_jsonable(result)),
        "AUDIO_OUTPUT_SERIALIZABLE": is_json_serializable(result),
    }
    checks["AUDIO_ALL_GATES"] = all(checks.values())
    return checks


if __name__ == "__main__":
    print_gate_results(run_probe())
