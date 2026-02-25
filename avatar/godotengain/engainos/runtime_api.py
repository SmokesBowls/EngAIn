# engainos/runtime_api.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .runtime_client import NGATRuntimeClient, RuntimeError


@dataclass(frozen=True)
class EngineSummary:
    protocol: str
    epoch: str
    kernels: List[str]
    server_ok: bool


@dataclass(frozen=True)
class QuestSummary:
    quest_id: str
    title: str
    state: str
    current_objective: Optional[str] = None


@dataclass(frozen=True)
class CombatState:
    entity: str
    hp: float
    hp_max: float
    alive: bool


def _safe_get(d: Dict[str, Any], key: str, default: Any = None) -> Any:
    return d.get(key, default) if isinstance(d, dict) else default


class EngAInRuntimeAPI:
    """
    Stable EngAInOS surface.

    Godot should conceptually depend on THIS layer.
    This layer depends on NGAT-RT (external server).
    """

    def __init__(self, client: Optional[NGATRuntimeClient] = None):
        self.client = client or NGATRuntimeClient()

    def get_engine_summary(self) -> EngineSummary:
        ok, text = self.client.probe()
        # If your runtime exposes /engine/summary, you can switch to it here.
        # For now we keep summary minimal and non-breaking.
        protocol = "NGAT-RT v1.0"
        epoch = "unknown"
        kernels: List[str] = []
        if ok:
            # opportunistic parse if runtime returns JSON on /health
            try:
                r = self.client.get(self.client.routes.health)
                if 200 <= r.status < 300:
                    j = r.json()
                    protocol = _safe_get(j, "protocol", protocol)
                    epoch = _safe_get(j, "epoch", epoch)
                    kernels = _safe_get(j, "kernels", kernels) or kernels
            except Exception:
                pass

        return EngineSummary(protocol=protocol, epoch=epoch, kernels=kernels, server_ok=ok)

    def register_quest(self, quest_payload: Dict[str, Any]) -> None:
        r = self.client.quest_register(quest_payload)
        if not (200 <= r.status < 300):
            raise RuntimeError(f"quest_register failed: HTTP {r.status} {r.text()[:800]}")

    def get_quest_summaries(self) -> List[QuestSummary]:
        r = self.client.quest_active()
        if not (200 <= r.status < 300):
            raise RuntimeError(f"quest_active failed: HTTP {r.status} {r.text()[:800]}")

        data = r.json()
        # Accept common shapes:
        # { "quests": [ ... ] } OR [ ... ]
        quests = data.get("quests") if isinstance(data, dict) else data
        if not isinstance(quests, list):
            return []

        out: List[QuestSummary] = []
        for q in quests:
            if not isinstance(q, dict):
                continue
            out.append(
                QuestSummary(
                    quest_id=str(_safe_get(q, "id", _safe_get(q, "quest_id", "unknown"))),
                    title=str(_safe_get(q, "title", _safe_get(q, "name", ""))),
                    state=str(_safe_get(q, "state", _safe_get(q, "status", "unknown"))),
                    current_objective=_safe_get(q, "current_objective", _safe_get(q, "objective", None)),
                )
            )
        return out

    def send_tick(self, dt: float) -> None:
        r = self.client.tick(dt)
        if not (200 <= r.status < 300):
            raise RuntimeError(f"tick failed: HTTP {r.status} {r.text()[:800]}")

    def combat_hit(self, attacker: str, target: str, amount: float, damage_type: str = "physical") -> None:
        r = self.client.combat_hit(attacker, target, amount, damage_type)
        if not (200 <= r.status < 300):
            raise RuntimeError(f"combat_hit failed: HTTP {r.status} {r.text()[:800]}")

    def get_combat_state(self, entity: str) -> CombatState:
        r = self.client.combat_state(entity)
        if not (200 <= r.status < 300):
            raise RuntimeError(f"combat_state failed: HTTP {r.status} {r.text()[:800]}")

        j = r.json()
        # Accept either {entity,hp,hp_max} or {state:{...}}
        s = j.get("state") if isinstance(j, dict) and "state" in j else j
        hp = float(_safe_get(s, "hp", 0.0))
        hp_max = float(_safe_get(s, "hp_max", _safe_get(s, "max_hp", 100.0)))
        alive = bool(_safe_get(s, "alive", hp > 0))
        return CombatState(entity=entity, hp=hp, hp_max=hp_max, alive=alive)
