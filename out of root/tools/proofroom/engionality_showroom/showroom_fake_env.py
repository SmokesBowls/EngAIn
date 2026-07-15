from __future__ import annotations

import json
import tempfile
from contextlib import contextmanager
from dataclasses import asdict, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Iterator, cast

FAKE_PERFORMANCE_TASK = {
    "task_id": "showroom_probe_task_001",
    "task_type": "dialogue_line",
    "scene_id": "scene.fake_showroom_probe",
    "tick": 1042,
    "actor_id": "mika_01",
    "target_id": "geralt_01",
    "line": "I heard the gate move.",
    "emotion": "guarded",
    "intensity": 0.72,
    "duration_ms": 1800,
    "metadata": {
        "probe": True,
        "real_runtime": False,
    },
}

FAKE_STATE = {
    "scene_id": "scene.fake_showroom_probe",
    "tick": 1042,
    "entities": {
        "mika_01": {
            "position": [1, 0, 2],
            "affect_state": "guarded",
            "dialogue_state": "ready",
        }
    },
    "performance": {
        "pending": [
            {
                "task_id": "task_001",
                "type": "dialogue_line",
                "actor_id": "mika_01",
            }
        ]
    },
}

AUTHORITY_REJECT_KEYS = {
    "authoritative",
    "canon_claim",
    "branch_authority",
    "render_authority",
    "runtime_authority",
    "engainos_authority",
    "godot_authority",
    "godotsim_authority",
    "mrlore_authority",
    "trixel_authority",
    "mechanimation_authority",
    "motion_proof",
    "audio_file_written",
}

AUTHORITY_TEXT_TOKENS = (
    "render authority",
    "canon authority",
    "runtime authority",
    "engainos authority",
    "godot authority",
    "godotsim authority",
    "mrlore authority",
    "trixel authority",
    "mechanimation authority",
    "motion proof",
    "joint validation",
    "final sprite",
    "final render",
    "final mix authority",
    "quest complete",
    "branch permission",
)

MUTATION_REJECT_KEYS = {
    "position",
    "velocity",
    "collision",
    "world_position",
    "joint_validation",
    "sprite_asset",
    "render_asset",
    "quest_complete",
    "final_branch_permission",
}


def to_jsonable(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return to_jsonable(asdict(cast(Any, value)))
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(to_jsonable(k)): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [to_jsonable(v) for v in value]
    return value


def is_json_serializable(value: Any) -> bool:
    try:
        json.dumps(to_jsonable(value), sort_keys=True)
    except (TypeError, ValueError):
        return False
    return True


def flatten_values(value: Any) -> list[Any]:
    value = to_jsonable(value)
    if isinstance(value, dict):
        out: list[Any] = []
        for k, v in value.items():
            out.append(k)
            out.extend(flatten_values(v))
        return out
    if isinstance(value, list):
        out = []
        for item in value:
            out.extend(flatten_values(item))
        return out
    return [value]


def no_authority_claim(value: Any) -> bool:
    value = to_jsonable(value)
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key).lower()
            if key_text in AUTHORITY_REJECT_KEYS and item is True:
                return False
            if not no_authority_claim(item):
                return False
        return True
    if isinstance(value, list):
        return all(no_authority_claim(item) for item in value)
    if isinstance(value, str):
        lower = value.lower().replace("_", " ")
        return not any(token in lower for token in AUTHORITY_TEXT_TOKENS)
    return True


def no_mutation_claim(value: Any) -> bool:
    value = to_jsonable(value)
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).lower() in MUTATION_REJECT_KEYS:
                return False
            if not no_mutation_claim(item):
                return False
        return True
    if isinstance(value, list):
        return all(no_mutation_claim(item) for item in value)
    return True


def make_performance_task() -> Any:
    from tier2.engionality.controlroom.task_types import PerformanceTask, PerformanceTaskType

    payload = dict(FAKE_PERFORMANCE_TASK)
    payload["duration"] = payload["duration_ms"] / 1000.0
    return PerformanceTask(
        id=payload["task_id"],
        tick_id=int(payload["tick"]),
        scene_time=0.0,
        task_type=PerformanceTaskType.DIALOGUE,
        payload=payload,
        priority=1,
    )


def make_domain_views_from_fake_task() -> dict[str, Any]:
    task = dict(FAKE_PERFORMANCE_TASK)
    duration = task["duration_ms"] / 1000.0
    return {
        "narrative_view": {
            "active_conversations": [
                {
                    "conversation_id": "fake_showroom_probe",
                    "speaker_id": task["actor_id"],
                    "target_id": task["target_id"],
                    "line_id": task["task_id"],
                    "line": task["line"],
                    "emotion": task["emotion"],
                    "intensity": task["intensity"],
                    "duration": duration,
                    "metadata": task["metadata"],
                }
            ]
        },
        "audio_view": {
            "music_events": [],
            "sfx_events": [
                {
                    "asset_id": "voice_guarded_low",
                    "duration": duration,
                    "volume_db": 0.0,
                    "volume_hint": task["intensity"],
                    "actor_id": task["actor_id"],
                    "scene_id": task["scene_id"],
                    "metadata": task["metadata"],
                }
            ],
        },
        "animation_view": {
            "body_events": [
                {
                    "rig_id": task["actor_id"],
                    "pose_id": "gesture_guarded",
                    "duration": duration,
                    "layer": "upper_body",
                    "emotion": task["emotion"],
                    "metadata": task["metadata"],
                }
            ],
            "facial_events": [],
        },
    }


def clip_to_cue(clip: Any, engine: str, scene_id: str = "scene.fake_showroom_probe") -> dict[str, Any]:
    clip_data = to_jsonable(clip)
    payload = dict(clip_data.get("payload", {}))
    cue = payload.get("pose_asset_id") or payload.get("asset_id") or payload.get("line") or payload.get("line_id") or clip_data.get("id")
    return {
        "engine": engine,
        "scene_id": scene_id,
        "actor_id": payload.get("speaker_id") or payload.get("rig_id") or FAKE_PERFORMANCE_TASK["actor_id"],
        "target_id": payload.get("target_id") or FAKE_PERFORMANCE_TASK["target_id"],
        "line": payload.get("line") or FAKE_PERFORMANCE_TASK["line"],
        "cue": cue,
        "start_ms": int(float(clip_data.get("start_time", 0.0)) * 1000),
        "duration_ms": int(float(clip_data.get("duration", 0.0)) * 1000),
        "emotion": payload.get("emotion") or FAKE_PERFORMANCE_TASK["emotion"],
        "tone": payload.get("emotion") or FAKE_PERFORMANCE_TASK["emotion"],
        "volume_hint": payload.get("volume_hint") or FAKE_PERFORMANCE_TASK["intensity"],
        "authoritative": False,
        "motion_proof": False,
        "audio_file_written": False,
        "canon_claim": False,
        "raw_clip": clip_data,
    }


@contextmanager
def fake_output_capture() -> Iterator[Path]:
    """Provide an isolated fake output directory for probes.

    The current showroom engines are in-memory coordinators. This context gives
    probes an explicit fake output root if a future engine asks where to write,
    without granting permission to touch runtime, ports, Godot, or EngAInOS.
    """
    with tempfile.TemporaryDirectory(prefix="engionality_showroom_probe_") as tmp:
        yield Path(tmp)


def run_gate(label: str, checks: dict[str, Callable[[], bool]]) -> dict[str, bool]:
    results: dict[str, bool] = {}
    for name, fn in checks.items():
        try:
            results[name] = bool(fn())
        except Exception:
            results[name] = False
    results[f"{label}_ALL_GATES"] = all(results.values())
    return results


def print_gate_results(results: dict[str, bool]) -> None:
    for name, passed in results.items():
        if name.endswith("ALL_GATES"):
            value = "true" if passed else "false"
        else:
            value = "TRUE" if passed else "FALSE"
        print(f"[{name}] {value}")
