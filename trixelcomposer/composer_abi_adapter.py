"""Thin ABI adapters for legacy Trixel composer/editor systems.

These adapters intentionally do not rewrite or mutate the historical composer
implementations. They normalize legacy methods and bridge payloads into the
TRIXEL_COMPOSER_ABI_v1 envelope shapes.
"""

from __future__ import annotations

import asyncio
import hashlib
import inspect
import json
import time
from dataclasses import asdict, is_dataclass, make_dataclass
from typing import Any, Dict, Optional, cast


NON_DETERMINISTIC_STATUS = "non_deterministic"


class ComposerABIError(RuntimeError):
    """Raised when a legacy composer cannot be adapted safely."""


def _jsonable(value: Any) -> Any:
    if not isinstance(value, type) and is_dataclass(value):
        return _jsonable(asdict(cast(Any, value)))
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(item) for item in value]
    if hasattr(value, "tolist"):
        try:
            return _jsonable(value.tolist())
        except Exception:
            pass
    if hasattr(value, "__dict__") and not isinstance(value, type):
        return _jsonable(vars(value))
    try:
        json.dumps(value)
        return value
    except TypeError:
        return repr(value)


def _digest(value: Any) -> str:
    payload = json.dumps(_jsonable(value), sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _session_id(owner: Any, fallback: str) -> str:
    return str(getattr(owner, "session_id", None) or fallback)


def _base_fields(
    *,
    schema_version: str,
    artifact_kind: str,
    source: str,
    session_id: str,
    status: str = NON_DETERMINISTIC_STATUS,
    deterministic_seed: Optional[int] = None,
    composer_id: Optional[str] = None,
) -> Dict[str, Any]:
    fields: Dict[str, Any] = {
        "schema_version": schema_version,
        "authority_level": "editor_only",
        "authoritative": False,
        "artifact_kind": artifact_kind,
        "source": source,
        "composer_id": composer_id or source,
        "session_id": session_id,
        "base_contract_version": None,
        "base_scene_id": None,
        "base_contract_digest": None,
        "deterministic_seed": deterministic_seed,
        "status": status,
    }
    if deterministic_seed is None:
        fields["status"] = status or NON_DETERMINISTIC_STATUS
    return fields


def _canvas_snapshot(composer: Any) -> Any:
    canvas = getattr(composer, "canvas", None)
    if canvas is None:
        return None
    if hasattr(canvas, "canvas"):
        return _jsonable(canvas.canvas)
    return _jsonable(canvas)


def _color_tuple(color: Any) -> tuple:
    if isinstance(color, tuple):
        return color
    if isinstance(color, list):
        return tuple(color)
    return (255, 255, 255)


def _action_to_legacy_dict(action_like: Any) -> Dict[str, Any]:
    if isinstance(action_like, dict):
        return dict(action_like)
    if not isinstance(action_like, type) and is_dataclass(action_like):
        return asdict(cast(Any, action_like))
    if hasattr(action_like, "__dict__"):
        return dict(vars(action_like))
    raise ComposerABIError(f"Cannot normalize action payload: {action_like!r}")


def _canonical_action(action_like: Any, *, source: str, session_id: str) -> Dict[str, Any]:
    legacy = _action_to_legacy_dict(action_like)
    tool = legacy.get("tool", legacy.get("action", "brush"))
    color = _jsonable(legacy.get("color", [255, 255, 255]))
    if isinstance(color, tuple):
        color = list(color)
    canonical = _base_fields(
        schema_version="trixel_editor_action.v1",
        artifact_kind="editor_action",
        source=source,
        session_id=session_id,
        status="proposed",
    )
    canonical.update(
        {
            "tool": tool,
            "x": int(legacy.get("x", 0)),
            "y": int(legacy.get("y", 0)),
            "color": color,
            "pressure": float(legacy.get("pressure", 1.0)),
            "reasoning": legacy.get("reasoning", "legacy action"),
            "legacy_payload": _jsonable(legacy),
        }
    )
    return canonical


def _legacy_action_from_plan(adapter: "_BaseComposerAdapter", plan: Dict[str, Any]) -> Any:
    action = plan.get("action", plan)
    legacy = action.get("legacy_payload") if isinstance(action, dict) else None
    if not isinstance(legacy, dict):
        legacy = action if isinstance(action, dict) else _action_to_legacy_dict(action)
    data = {
        "tool": legacy.get("tool", legacy.get("action", action.get("tool", "brush") if isinstance(action, dict) else "brush")),
        "x": int(legacy.get("x", action.get("x", 0) if isinstance(action, dict) else 0)),
        "y": int(legacy.get("y", action.get("y", 0) if isinstance(action, dict) else 0)),
        "color": _color_tuple(legacy.get("color", action.get("color", [255, 255, 255]) if isinstance(action, dict) else [255, 255, 255])),
        "pressure": float(legacy.get("pressure", action.get("pressure", 1.0) if isinstance(action, dict) else 1.0)),
        "reasoning": legacy.get("reasoning", action.get("reasoning", "adapter-normalized") if isinstance(action, dict) else "adapter-normalized"),
        "timestamp": legacy.get("timestamp", time.time()),
        "artistic_success": legacy.get("artistic_success", 0.5),
    }
    action_cls = adapter.action_class
    if action_cls is None:
        action_cls = make_dataclass(
            "AdapterCreativeAction",
            [
                ("tool", str),
                ("x", int),
                ("y", int),
                ("color", tuple),
                ("pressure", float),
                ("reasoning", str),
                ("timestamp", float),
                ("artistic_success", float),
            ],
        )
    return action_cls(**data)


def _run_coroutine_safely(awaitable: Any) -> Any:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(awaitable)
    raise ComposerABIError("Cannot run async legacy planner while an event loop is already running")


class _BaseComposerAdapter:
    source = "unknown"
    action_class = None

    def __init__(self, composer: Any = None, *, deterministic_seed: Optional[int] = None):
        self.composer = composer if composer is not None else self._create_default_composer()
        self.deterministic_seed = deterministic_seed
        self.session_id = _session_id(self.composer, f"{self.source}_adapter")

    def _create_default_composer(self) -> Any:
        raise NotImplementedError

    def _envelope(self, schema_version: str, artifact_kind: str, status: str = NON_DETERMINISTIC_STATUS) -> Dict[str, Any]:
        return _base_fields(
            schema_version=schema_version,
            artifact_kind=artifact_kind,
            source=self.source,
            session_id=self.session_id,
            status=status,
            deterministic_seed=self.deterministic_seed,
        )

    def perceive(self) -> Dict[str, Any]:
        legacy = self.composer.perceive()
        envelope = self._envelope("trixel_composer_perception.v1", "editor_perception")
        envelope.update(
            {
                "canvas_snapshot": _canvas_snapshot(self.composer),
                "tool_state": {
                    "tool": getattr(self.composer, "tool", None),
                    "color": _jsonable(getattr(self.composer, "color", None)),
                    "pressure": getattr(self.composer, "pressure", None),
                },
                "memory_context": _jsonable(
                    legacy.get("memory_context", legacy.get("memory_state", {})) if isinstance(legacy, dict) else {}
                ),
                "analysis": _jsonable(legacy),
                "legacy_payload": _jsonable(legacy),
            }
        )
        return envelope

    def persist(self) -> None:
        raise NotImplementedError


class TerminalTrixelComposerAdapter(_BaseComposerAdapter):
    """Adapter for trixelcomposer.terminal_trixel.TerminalTrixelComposer."""

    source = "terminal_trixel"

    def _create_default_composer(self) -> Any:
        from trixelcomposer.terminal_trixel import CreativeAction, TerminalTrixelComposer

        self.action_class = CreativeAction
        return TerminalTrixelComposer()

    def __init__(self, composer: Any = None, *, deterministic_seed: Optional[int] = None):
        super().__init__(composer, deterministic_seed=deterministic_seed)
        if self.action_class is None and composer is not None:
            self.action_class = None

    def plan(self) -> Dict[str, Any]:
        legacy_perception = self.composer.perceive()
        legacy_action = self.composer.plan_action(legacy_perception)
        action = _canonical_action(legacy_action, source=self.source, session_id=self.session_id)
        envelope = self._envelope("trixel_composer_plan.v1", "editor_action_plan", status="proposed")
        envelope.update(
            {
                "action": action,
                "legacy_payload": {
                    "perception": _jsonable(legacy_perception),
                    "action": _jsonable(legacy_action),
                },
            }
        )
        return envelope

    def act(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        try:
            legacy_action = _legacy_action_from_plan(self, plan)
            quality = self.composer.execute_action(legacy_action)
            status = "applied"
            errors = []
        except Exception as exc:  # return rejected envelope instead of authority leakage
            legacy_action = None
            quality = None
            status = "rejected"
            errors = [str(exc)]
        action_payload = _canonical_action(legacy_action, source=self.source, session_id=self.session_id) if legacy_action is not None else None
        envelope = self._envelope("trixel_composer_act_result.v1", "editor_action_result", status=status)
        envelope.update(
            {
                "input_plan_digest": _digest(plan),
                "applied_action": action_payload,
                "canvas_snapshot_after": _canvas_snapshot(self.composer),
                "quality": quality,
                "errors": errors,
                "legacy_payload": {"input_plan": _jsonable(plan)},
            }
        )
        return envelope

    def persist(self) -> None:
        self.composer.save_session()


class EnhancedTrixelComposerAdapter(_BaseComposerAdapter):
    """Adapter for trixelcomposer.enhanced_trixel_core.EnhancedTrixelComposer."""

    source = "enhanced_trixel_core"

    def _create_default_composer(self) -> Any:
        from trixelcomposer.enhanced_trixel_core import CreativeAction, EnhancedTrixelComposer

        self.action_class = CreativeAction
        return EnhancedTrixelComposer()

    def __init__(self, composer: Any = None, *, deterministic_seed: Optional[int] = None):
        super().__init__(composer, deterministic_seed=deterministic_seed)
        if self.action_class is None and composer is not None:
            self.action_class = None

    def plan(self) -> Dict[str, Any]:
        legacy_perception = self.composer.perceive()
        legacy_plan = self.composer._autonomous_plan(legacy_perception)
        if inspect.isawaitable(legacy_plan):
            legacy_plan = _run_coroutine_safely(legacy_plan)
        action = _canonical_action(legacy_plan, source=self.source, session_id=self.session_id)
        envelope = self._envelope("trixel_composer_plan.v1", "editor_action_plan", status="proposed")
        envelope.update(
            {
                "action": action,
                "legacy_payload": {
                    "perception": _jsonable(legacy_perception),
                    "plan": _jsonable(legacy_plan),
                },
            }
        )
        return envelope

    def act(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        try:
            legacy_action = _legacy_action_from_plan(self, plan)
            quality = self.composer._execute_action(legacy_action)
            status = "applied"
            errors = []
        except Exception as exc:
            legacy_action = None
            quality = None
            status = "rejected"
            errors = [str(exc)]
        action_payload = _canonical_action(legacy_action, source=self.source, session_id=self.session_id) if legacy_action is not None else None
        envelope = self._envelope("trixel_composer_act_result.v1", "editor_action_result", status=status)
        envelope.update(
            {
                "input_plan_digest": _digest(plan),
                "applied_action": action_payload,
                "canvas_snapshot_after": _canvas_snapshot(self.composer),
                "quality": quality,
                "errors": errors,
                "legacy_payload": {"input_plan": _jsonable(plan)},
            }
        )
        return envelope

    def persist(self) -> None:
        self.composer._save_autonomous_session()


class EmpireBridgeProposalAdapter:
    """Normalize EmpireBridge-style AI suggestions into proposal envelopes only."""

    source = "empire_bridge"

    def __init__(
        self,
        composer: Any = None,
        *,
        session_id: Optional[str] = None,
        deterministic_seed: Optional[int] = None,
    ):
        self.composer = composer
        self.session_id = session_id or _session_id(composer, f"{self.source}_adapter")
        self.deterministic_seed = deterministic_seed

    def _envelope(self, schema_version: str, artifact_kind: str, status: str = "proposed") -> Dict[str, Any]:
        return _base_fields(
            schema_version=schema_version,
            artifact_kind=artifact_kind,
            source=self.source,
            session_id=self.session_id,
            status=status,
            deterministic_seed=self.deterministic_seed,
        )

    def _extract_legacy_action(self, suggestion: Dict[str, Any]) -> Dict[str, Any]:
        if "!zw/art.action" in suggestion and isinstance(suggestion["!zw/art.action"], dict):
            return dict(suggestion["!zw/art.action"])
        if "plan" in suggestion and isinstance(suggestion["plan"], dict):
            plan = suggestion["plan"]
            if isinstance(plan.get("action"), dict):
                return dict(plan["action"])
            return dict(plan)
        if "action" in suggestion or "tool" in suggestion:
            return dict(suggestion)
        return {"tool": "brush", "x": 8, "y": 8, "color": [255, 255, 255], "reasoning": "AI suggestion"}

    def normalize_ai_suggestion(self, suggestion: Dict[str, Any]) -> Dict[str, Any]:
        legacy_action = self._extract_legacy_action(suggestion)
        action = _canonical_action(legacy_action, source=self.source, session_id=self.session_id)
        plan = self._envelope("trixel_composer_plan.v1", "editor_action_plan", status="proposed")
        plan.update(
            {
                "action": action,
                "legacy_payload": _jsonable(suggestion),
            }
        )
        ai_suggestion = self._envelope("trixel_ai_suggestion.v1", "ai_suggestion", status="proposed")
        ai_suggestion.update(
            {
                "raw_response_digest": _digest(suggestion),
                "plan": plan,
                "legacy_payload": _jsonable(suggestion),
            }
        )
        return ai_suggestion

    def parse_ai_suggestion(self, suggestion: Dict[str, Any]) -> Dict[str, Any]:
        return self.normalize_ai_suggestion(suggestion)
