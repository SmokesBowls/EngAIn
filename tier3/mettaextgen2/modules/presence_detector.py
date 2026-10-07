"""presence_detector (GEN2_MODULES.md §2.8).

Input:   `metadata_constraint` presence_qualifier annotations (author metadata).
Output:  `presence` per participant: present / referenced / absent / unknown,
         with the qualifier text it was read from.
Allowed: presence evidence only.
Forbidden: spawn, position or "spawnable" decisions (GodotSim / EngAInOS).
Failure: a qualifier it cannot classify yields `unknown`, never `present`.

Rule (the one the 3D Dragon applied by judgement on 2026-09-20, now data):
  no qualifier                                  -> present
  qualifier says absent                         -> absent
  qualifier limits the entity to memory, a grave,
  remote watching, reference or recollection    -> referenced
  any other qualifier                           -> unknown
Prose-only entities get no presence annotation here. The reconciler reports
them as `unknown`, because presence is never inferred from a name appearing.
"""

from __future__ import annotations

import re

from ..lib.annotations import AnnotationView, Module, ModuleOutput, NewAnnotation, SceneInput
from ..lib.source import SourceDocument

_ABSENT = re.compile(r"\babsent\b|\bnot present\b|\boff-?stage\b", re.IGNORECASE)
_REFERENCED = re.compile(
    r"\bonly\b|\bmemory\b|\bmemories\b|\bgrave\b|\bremote\b|\bwatchers?\b|\breferenced?\b"
    r"|\brecalled\b|\bremembered\b|\bmentioned\b|\binterstitial\b|\bvoice only\b|\bvision\b",
    re.IGNORECASE,
)


def classify_qualifier(qualifier: str | None) -> str:
    if qualifier is None or not qualifier.strip():
        return "present"
    if _ABSENT.search(qualifier):
        return "absent"
    if _REFERENCED.search(qualifier):
        return "referenced"
    return "unknown"


class PresenceDetector(Module):
    name = "presence_detector"
    version = "0.1.0"
    implementation_kind = "rules"
    requires = frozenset({"metadata_constraint"})
    produces = frozenset({"presence"})

    def run(self, doc: SourceDocument, scene: SceneInput, view: AnnotationView) -> ModuleOutput:
        out = ModuleOutput()
        for c in view.by_kind("metadata_constraint"):
            if c.value["kind"] != "presence_qualifier":
                continue
            qualifier = c.value.get("qualifier")
            presence = classify_qualifier(qualifier)
            out.annotations.append(NewAnnotation("presence", c.span, {
                "subject": c.value["subject"],
                "presence": presence,
                "qualifier": qualifier,
            }, confidence=0.95 if qualifier else 0.85))
        return out
