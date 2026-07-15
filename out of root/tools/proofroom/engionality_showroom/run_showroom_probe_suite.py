from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Callable, cast

PROBES = [
    ("PERFORMER", "tools.proofroom.engionality_showroom.probe_performer_engine"),
    ("SCENE_TRACK", "tools.proofroom.engionality_showroom.probe_scene_track"),
    ("ANIMATION", "tools.proofroom.engionality_showroom.probe_animation_engine"),
    ("AUDIO", "tools.proofroom.engionality_showroom.probe_audio_engine"),
    ("DIALOGUE", "tools.proofroom.engionality_showroom.probe_dialogue_engine"),
    ("DOMAIN_VIEWS", "tools.proofroom.engionality_showroom.probe_domain_views"),
]


@dataclass(frozen=True)
class ProbeResult:
    name: str
    passed: bool
    gates: dict[str, bool]


def load_probe(module_name: str) -> Callable[[], dict[str, bool]]:
    module = importlib.import_module(module_name)
    run_probe = getattr(module, "run_probe")
    if not callable(run_probe):
        raise TypeError(f"{module_name}.run_probe is not callable")
    return cast(Callable[[], dict[str, bool]], run_probe)


def run_suite() -> list[ProbeResult]:
    results: list[ProbeResult] = []
    for name, module_name in PROBES:
        try:
            gates = load_probe(module_name)()
            passed = bool(gates.get(f"{name}_ALL_GATES", False))
        except Exception as exc:
            gates = {f"{name}_IMPORT": False, f"{name}_ALL_GATES": False, "error": False}
            print(f"[SHOWROOM_SUITE][{name}][ERROR] {exc!r}")
            passed = False
        results.append(ProbeResult(name=name, passed=passed, gates=gates))
    return results


def main() -> int:
    results = run_suite()
    for result in results:
        print(f"[SHOWROOM_SUITE][{result.name}] {'TRUE' if result.passed else 'FALSE'}")
    all_gates = all(result.passed for result in results)
    print(f"[SHOWROOM_SUITE][ALL_GATES] {'true' if all_gates else 'false'}")
    return 0 if all_gates else 1


if __name__ == "__main__":
    raise SystemExit(main())
