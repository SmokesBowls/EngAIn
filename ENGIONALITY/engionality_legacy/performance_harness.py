# performance_harness.py
from __future__ import annotations

from typing import Dict, Any, List
from pprint import pprint
import json
import os
import tempfile
import time

from .performer_engine import PerformerEngine


OUT_LATEST = "/tmp/engain_performance_tick.latest.json"
OUT_TICK_FMT = "/tmp/engain_performance_tick.{tick:04d}.json"


def atomic_write_json(path: str, data: Dict[str, Any]) -> None:
    out_dir = os.path.dirname(path) or "."
    os.makedirs(out_dir, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix=".engain_tick_", dir=out_dir)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=True)
        os.replace(tmp_path, path)
    finally:
        try:
            os.remove(tmp_path)
        except FileNotFoundError:
            pass



def fake_domain_views_for_tick(tick_id: int) -> Dict[str, Any]:
    """
    Minimal synthetic domain views to exercise PerformerEngine.
    """
    views: Dict[str, Any] = {}

    # Simple narrative script:
    if tick_id == 1:
        views["narrative_view"] = {
            "active_conversations": [
                {
                    "conversation_id": "intro",
                    "speaker_id": "keen",
                    "line_id": "intro_001",
                    "emotion": "curious",
                    "intensity": 0.7,
                    "duration": 2.5,
                }
            ]
        }
    elif tick_id == 3:
        views["narrative_view"] = {
            "active_conversations": [
                {
                    "conversation_id": "intro",
                    "speaker_id": "tran",
                    "line_id": "intro_002",
                    "emotion": "wary",
                    "intensity": 0.8,
                    "duration": 3.0,
                }
            ]
        }

    # Simple audio script:
    if tick_id == 0:
        views["audio_view"] = {
            "music_events": [
                {"asset_id": "bgm_theme_01", "action": "play", "duration": 30.0}
            ]
        }
    elif tick_id == 2:
        views.setdefault("audio_view", {})
        views["audio_view"].setdefault("sfx_events", []).append(
            {"asset_id": "ui_ping_01", "duration": 1.0}
        )

    # Simple animation script:
    if tick_id == 1:
        views["animation_view"] = {
            "body_events": [
                {
                    "rig_id": "keen_rig",
                    "pose_id": "idle_listen",
                    "duration": 1.5,
                    "layer": "base",
                }
            ]
        }
    elif tick_id == 3:
        views["animation_view"] = {
            "body_events": [
                {
                    "rig_id": "tran_rig",
                    "pose_id": "speak_emphatic",
                    "duration": 2.0,
                    "layer": "upper_body",
                }
            ],
            "facial_events": [
                {
                    "rig_id": "tran_rig",
                    "viseme_curve_id": "intro_002_visemes",
                    "duration": 2.0,
                    "audio_clip_id": "voice_intro_002",
                }
            ],
        }

    return views


def tasks_to_dicts(tasks) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for t in tasks:
        out.append(
            {
                "id": t.id,
                "tick_id": t.tick_id,
                "scene_time": t.scene_time,
                "type": t.task_type.value,
                "priority": t.priority,
                "payload": t.payload,
            }
        )
    return out


def run_performance_sim() -> None:
    print("[BOOT] performance_harness:", os.path.abspath(__file__))
    print(f"[OUT] Writing tick packets to: {OUT_LATEST} and {OUT_TICK_FMT}")


    performer = PerformerEngine()
    tick_delta_time = 0.5  # half a second per Tick for demo
    epoch = f"perf_{int(time.time())}"

    for tick_id in range(0, 6):
        domain_views = fake_domain_views_for_tick(tick_id)
        tasks = performer.step(
            tick_id=tick_id,
            delta_time=tick_delta_time,
            domain_views=domain_views,
        )

        packet: Dict[str, Any] = {
            "epoch": epoch,
            "tick": tick_id,
            "delta_time": tick_delta_time,
            "scene_time": (tick_id + 1) * tick_delta_time,
            "domain_views": domain_views,  # keep for debug; remove later if too noisy
            "tasks": tasks_to_dicts(tasks),
            "trace": {"source": "ENGINALITY.performance_harness"},
        }

        atomic_write_json(OUT_LATEST, packet)
        atomic_write_json(OUT_TICK_FMT.format(tick=tick_id), packet)

        print("\n===============================")
        print(f"Tick {tick_id} – generated {len(tasks)} PerformanceTasks")
        print("===============================")
        for t in packet["tasks"]:
            pprint(t)


if __name__ == "__main__":
    run_performance_sim()

