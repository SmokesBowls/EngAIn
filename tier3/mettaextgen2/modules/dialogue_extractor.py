"""dialogue_extractor (GEN2_MODULES.md §2.10), v0.1.

Input:   `quote_region`, `attribution_frame`, `predication` (linguistic
         facts), `reconciled_entity` and `alias_candidate` (run-local refs),
         `region` (paragraph order).
Output:  `speech` per quotation: {kind: dialogue | recalled, speaker_ref,
         alternatives[]}. Confidence is proposal strength:
           0.90  a speech tag names the speaker of this quotation
           0.75  continuation: the previous quotation in the paragraph has a
                 named speaker and at most one sentence, with no other named
                 subject, stands between them
           0.60  action beat: the narration sentence right before or right
                 after the quotation has a named clause subject (only one
                 name between the two)
           0.30  pronoun or descriptive tag ("she observed", "someone asked"):
                 speaker_ref null, nearby names kept as alternatives
           0.20  no tag and no beat: speaker_ref null, alternatives kept
Allowed: speaker attribution the paragraph supports.
Forbidden: attributing from scene context the span does not contain; picking
         a pronoun's referent (coreference is deferred, so the speaker stays
         null); filtering candidates by pronoun gender (spec §2.6); merging
         candidates.
Failure: a quotation whose paragraph quotes do not pair gets no record (the
         linguistic layer reports it unanalysed).
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional

from ..lib.annotations import AnnotationView, Module, ModuleOutput, NewAnnotation, SceneInput
from ..lib.source import SourceDocument

ALTERNATIVE_WINDOW = 2   # prose paragraphs before the quotation's own paragraph


def _sentences(text: str) -> int:
    """Sentence ends in a stretch of narration."""
    return len(re.findall(r"[.!?…]+", text))


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("’", "'")).strip().lower()


class DialogueExtractor(Module):
    name = "dialogue_extractor"
    version = "0.1.0"
    implementation_kind = "rules"
    requires = frozenset({"quote_region", "attribution_frame", "predication", "reconciled_entity",
                          "alias_candidate", "region"})
    produces = frozenset({"speech"})

    def run(self, doc: SourceDocument, scene: SceneInput, view: AnnotationView) -> ModuleOutput:
        out = ModuleOutput()
        refs: Dict[str, str] = {}
        mention_lines: Dict[str, List[int]] = {}
        for e in view.by_kind("reconciled_entity"):
            if e.value["status"] == "REJECTED":
                continue
            refs[_norm(e.value["surface"])] = e.value["local_ref"]
            mention_lines[e.value["local_ref"]] = [s.line for s in e.value["evidence"]] + [e.span.line]
        for a in view.by_kind("alias_candidate"):
            refs.setdefault(_norm(a.value["surface"]), a.value["candidate_ref"])

        prose = {r.span.line: r.span for r in view.by_kind("region") if r.value["region_type"] == "prose"}
        paragraphs = list(prose)
        frames = {f.value["quote_id"]: f for f in view.by_kind("attribution_frame")}
        subjects: Dict[int, list] = {}   # narration clause subjects per paragraph, in text order
        for p in sorted(view.by_kind("predication"), key=lambda a: a.span.char_start):
            if not p.value["in_quote"]:
                subjects.setdefault(p.value["paragraph_line"], []).append(p)

        quotes_by_paragraph: Dict[int, list] = {}
        for q in view.by_kind("quote_region"):
            if not q.value["embedded_term"]:   # a quoted term is not speech
                quotes_by_paragraph.setdefault(q.value["paragraph_line"], []).append(q)

        for line, quotes in quotes_by_paragraph.items():
            quotes.sort(key=lambda a: a.span.char_start)
            para = prose[line]
            names = subjects.get(line, [])
            previous: Optional[str] = None    # named speaker of the previous quotation, by surface
            for i, q in enumerate(quotes):
                frame = frames.get(q.value["quote_id"])
                kind = "recalled" if frame is not None and frame.value["recalled"] else "dialogue"
                surface: Optional[str] = None
                if frame is not None and frame.value["speaker_kind"] == "name":
                    surface, confidence = _norm(frame.value["speaker_text"]), 0.90
                elif frame is not None:
                    confidence = 0.30
                else:
                    gap_start = quotes[i - 1].span.char_end if i else para.char_start
                    gap = doc.text[gap_start:q.span.char_start]
                    others = {_norm(p.value["surface"]) for p in names
                              if gap_start <= p.span.char_start < q.span.char_start} - {previous}
                    if previous and _sentences(gap) <= 1 and not others:
                        surface, confidence = previous, 0.75
                    else:
                        surface = self._beat(doc, q, quotes, i, para, names)
                        confidence = 0.60 if surface else 0.20
                speaker = refs.get(surface) if surface else None
                previous = surface if speaker else None
                if speaker is None:
                    confidence = min(confidence, 0.30)   # a name with no accepted entity stays unresolved
                alternatives = [] if speaker else self._nearby(line, paragraphs, mention_lines)
                out.annotations.append(NewAnnotation("speech", q.span, {
                    "kind": kind, "speaker_ref": speaker, "alternatives": alternatives,
                }, confidence=confidence))
        return out

    @staticmethod
    def _beat(doc: SourceDocument, q, quotes, i: int, para, names) -> Optional[str]:
        """The named subject of the narration sentence right before or right after quotation i, if only one."""
        lo = quotes[i - 1].span.char_end if i else para.char_start
        hi = quotes[i + 1].span.char_start if i + 1 < len(quotes) else para.char_end
        before = [p for p in names if lo <= p.span.char_start < q.span.char_start
                  and _sentences(doc.text[p.span.char_end:q.span.char_start]) <= 1]
        after = [p for p in names if q.span.char_end <= p.span.char_start < hi
                 and _sentences(doc.text[q.span.char_end:p.span.char_start]) == 0]
        found = {_norm(p.value["surface"]) for p in before[-1:] + after[:1]}
        return found.pop() if len(found) == 1 else None

    @staticmethod
    def _nearby(line: int, paragraphs: List[int], mention_lines: Dict[str, List[int]]) -> List[str]:
        """Refs named in this paragraph or the ALTERNATIVE_WINDOW paragraphs before it, most recent first."""
        index = paragraphs.index(line) if line in paragraphs else 0
        window = set(paragraphs[max(0, index - ALTERNATIVE_WINDOW):index + 1])
        recent = {ref: max(l for l in lines if l in window)
                  for ref, lines in mention_lines.items() if any(l in window for l in lines)}
        return sorted(recent, key=lambda r: (-recent[r], r))
