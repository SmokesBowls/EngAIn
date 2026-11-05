"""presence_detector (GEN2_MODULES.md §2.8), v0.2.

Input:   `metadata_constraint` presence_qualifier annotations (author metadata);
         prose `entity_mention`, `predication`, `attribution_frame` and
         `sentence` annotations.
Output:  `presence` per participant: present / referenced / absent / unknown,
         with the qualifier text it was read from (author metadata).
         `presence_evidence` per prose cue, low confidence, one of:
           physical       clause subject of a bodily action outside a quotation,
                          not negated ("Torhh stood by the entrance")
           communication  the named speaker of a speech tag. Speaking is never
                          physical presence: ethereal beings speak by resonance
           absence        explicit absence ("Torhh was not there", "had left")
           referenced     the object of a memory cue, within a few words of it and
                          not its subject ("She remembered Torhh's laugh",
                          "the Pelagor they remembered", "memories of the Giants")
         A plain mention produces no evidence (it stays a mention).
Allowed: presence evidence only.
Forbidden: spawn, position or "spawnable" decisions (GodotSim / EngAInOS).
         Deciding between metadata and prose: the reconciler weighs them.
Failure: a qualifier it cannot classify yields `unknown`, never `present`.

Metadata rule (the one the 3D Dragon applied by judgement on 2026-09-20, now data):
  no qualifier                                  -> present
  qualifier says absent                         -> absent
  qualifier limits the entity to memory, a grave,
  remote watching, reference or recollection    -> referenced
  any other qualifier                           -> unknown
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
_MEMORY_CUE = re.compile(r"\b(?:remember(?:ed|ing|s)?|recall(?:ed|ing|s)?|memor(?:y|ies)|grave|mourn(?:ed|ing)?|missed)\b",
                         re.IGNORECASE)
PROSE_EVIDENCE_CONFIDENCE = 0.4
MEMORY_WINDOW_CHARS = 40
MEMORY_MAX_WORDS_BETWEEN = 3


def _near_cue(text: str, at_end: bool):
    """A memory cue at most MEMORY_MAX_WORDS_BETWEEN words from the mention, with no clause punctuation between."""
    cues = list(_MEMORY_CUE.finditer(text))
    if not cues:
        return None
    cue = cues[-1] if at_end else cues[0]
    between = text[cue.end():] if at_end else text[:cue.start()]
    if re.search(r"[,;:.!?—]", between) or len(between.split()) > MEMORY_MAX_WORDS_BETWEEN:
        return None
    return cue.group(0)


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
    version = "0.2.0"
    implementation_kind = "rules"
    requires = frozenset({"metadata_constraint", "entity_mention", "predication", "attribution_frame", "sentence"})
    produces = frozenset({"presence", "presence_evidence"})

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

        def evidence(span, surface: str, kind: str, cue: str) -> None:
            out.annotations.append(NewAnnotation("presence_evidence", span,
                                                 {"surface": surface, "kind": kind, "cue": cue},
                                                 confidence=PROSE_EVIDENCE_CONFIDENCE))

        speaker_starts = set()
        for f in view.by_kind("attribution_frame"):
            if f.value["speaker_kind"] == "name":
                speaker_starts.add(f.value["speaker_span"].char_start)
                if not f.value["recalled"]:
                    evidence(f.value["speaker_span"], f.value["speaker_text"], "communication", f.value["verb"])
        subject_starts = set()
        for p in view.by_kind("predication"):
            subject_starts.add(p.span.char_start)
            if p.value["in_quote"]:
                continue  # what a character says about someone is reported, not observed
            if "absence" in p.value["verb_classes"]:
                evidence(p.span, p.value["surface"], "absence", p.value["verb"])
            elif ("physical" in p.value["verb_classes"] and not p.value["negated"]
                  and p.span.char_start not in speaker_starts):
                evidence(p.span, p.value["surface"], "physical", p.value["verb"])

        for m in view.by_kind("entity_mention"):
            if m.value["evidence_class"] != "PROSE" or m.span.char_start in subject_starts:
                continue
            before = doc.text[max(0, m.span.char_start - MEMORY_WINDOW_CHARS):m.span.char_start]
            after = doc.text[m.span.char_end:m.span.char_end + MEMORY_WINDOW_CHARS]
            cue = _near_cue(before, at_end=True) or _near_cue(after, at_end=False)
            if cue:
                evidence(m.span, m.value["surface"], "referenced", cue)
        return out
