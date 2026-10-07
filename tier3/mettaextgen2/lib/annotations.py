"""Append-only annotation store and the common module contract.

GEN2_MODULES.md §1: every module declares the annotation kinds it requires
and produces, reads prior annotations through a read-only view, and returns
new annotations, challenges and diagnostics. It never mutates another
module's annotations. The store enforces `produces` and freezes every value.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Dict, FrozenSet, List, Mapping, Optional, Tuple

from .source import SourceDocument, Span


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({k: _freeze(v) for k, v in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(v) for v in value)
    return value


def thaw(value: Any) -> Any:
    """Plain, JSON-ready copy of a frozen annotation value."""
    if isinstance(value, Mapping):
        return {k: thaw(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return [thaw(v) for v in value]
    if isinstance(value, Span):
        return value.to_dict()
    return value


@dataclass(frozen=True)
class NewAnnotation:
    kind: str
    span: Span
    value: Dict[str, Any]
    confidence: Optional[float] = None


@dataclass(frozen=True)
class Annotation:
    id: str
    kind: str
    module: str
    span: Span
    value: Mapping[str, Any]
    confidence: Optional[float]


@dataclass(frozen=True)
class Challenge:
    target_annotation_id: str
    reason: str


@dataclass(frozen=True)
class Diagnostic:
    level: str      # "info" | "warning" | "error"
    message: str


@dataclass
class ModuleOutput:
    annotations: List[NewAnnotation] = field(default_factory=list)
    challenges: List[Challenge] = field(default_factory=list)
    diagnostics: List[Diagnostic] = field(default_factory=list)


@dataclass(frozen=True)
class SceneInput:
    """Identity inherited from the Chapterroom input packet (never minted)."""

    chapter_id: str
    chapterroom_scene_id: str
    source_scene_label: Optional[str]
    source_scene_title: Optional[str]
    boundary_method: str
    authored_scene_boundaries_proven: bool
    packet_path: str


class AnnotationView:
    """Read-only snapshot of the store as of a module's start."""

    def __init__(self, annotations: Tuple[Annotation, ...]):
        self._annotations = annotations

    def by_kind(self, kind: str) -> Tuple[Annotation, ...]:
        return tuple(a for a in self._annotations if a.kind == kind)

    def all(self) -> Tuple[Annotation, ...]:
        return self._annotations


class AnnotationStore:
    def __init__(self) -> None:
        self._annotations: List[Annotation] = []
        self.challenges: List[Tuple[str, Challenge]] = []

    def view(self) -> AnnotationView:
        return AnnotationView(tuple(self._annotations))

    def add(self, module: "Module", output: ModuleOutput) -> None:
        """Validate the whole output first; append nothing if any item is invalid."""
        for new in output.annotations:
            if new.kind not in module.produces:
                raise ValueError(
                    f"{module.name} emitted kind {new.kind!r} not in produces {sorted(module.produces)}"
                )
            if not isinstance(new.span, Span):
                raise ValueError(f"{module.name} emitted {new.kind!r} without a Span")
            if new.confidence is not None and not (0.0 <= new.confidence <= 1.0):
                raise ValueError(f"{module.name} emitted confidence {new.confidence} outside 0..1")
        known_ids = {a.id for a in self._annotations}
        for ch in output.challenges:
            if ch.target_annotation_id not in known_ids:
                raise ValueError(f"{module.name} challenged unknown annotation {ch.target_annotation_id}")
        for new in output.annotations:
            self._annotations.append(Annotation(
                id=f"a{len(self._annotations) + 1:05d}",
                kind=new.kind,
                module=module.name,
                span=new.span,
                value=_freeze(new.value),
                confidence=new.confidence,
            ))
        self.challenges.extend((module.name, ch) for ch in output.challenges)


class Module(ABC):
    name: str
    version: str
    implementation_kind: str          # "rules" | "model" | "hybrid"
    requires: FrozenSet[str]
    produces: FrozenSet[str]

    @abstractmethod
    def run(self, doc: SourceDocument, scene: SceneInput, view: AnnotationView) -> ModuleOutput:
        raise NotImplementedError

    def describe(self) -> Dict[str, str]:
        return {"name": self.name, "version": self.version, "implementation_kind": self.implementation_kind}
