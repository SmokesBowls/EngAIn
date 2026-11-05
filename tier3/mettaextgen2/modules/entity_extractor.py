"""entity_extractor (GEN2_MODULES.md §2.5).

Input:   `token` / `sentence` annotations (prose only) and
         `metadata_constraint` annotations.
Output:  `entity_mention`: a prose name group (possibly multi-word, e.g.
         "Falcon Ridge", "Five Mikas"), or a metadata participant name
         (evidence_class AUTHOR_METADATA).
         `entity_rejection`: a capitalised group with no name evidence,
         with the reason.
Allowed: proposing mentions. No identity, no types beyond hints, no ids.
Forbidden: promoting a token whose only capital is sentence- or
         quote-initial unless corroborated; treating metadata keys or values
         as prose.

Grouping: consecutive capitalised, non-closed-class tokens separated by
exactly one space, within one sentence. A possessive ends its group. Leading
closed-class words are dropped ("The Five Mikas" -> "Five Mikas"). A lone
number word is never a name.

A group whose capitals are all positional (sentence_initial, quote_initial,
post_quote) needs evidence beyond its capital. In order:
  Grammar (v0.2), only when the words are not also used as common words in
  the chapter's prose (a lowercase use shows a capitalised common noun):
  (g1) speech_tag_speaker: the speaker slot of an attribution frame;
  (g2) grammatical_subject: the clause subject of a verb that selects an
       agent (speech, cognition, perception, physical, deliberate, absence);
  (g3) possessor_of_subject: "Name's consciousness/voice/... <verb>".
  Corroboration:
  (a) the same surface appears as a proper_candidate elsewhere in the scene, or
  (b) it is a word of a metadata participant name, or
  (c) it appears capitalised mid-text in a metadata value, or
  (d) chapter_corroboration: a single word used mid-sentence elsewhere in the
      chapter's prose (context line recorded; no span outside the scene).
Otherwise the group is rejected (reason "initial_capital_only").
"""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Dict, List, Set

from ..lib.annotations import Annotation, AnnotationView, Module, ModuleOutput, NewAnnotation, SceneInput
from ..lib.source import SourceDocument
from .linguistic_annotator import chapter_context

_MIDTEXT_CAPITAL = re.compile(r"(?<=[a-z,;:)\]]\s)([A-Z][a-z’']+)")


def _norm(word: str) -> str:
    return word.replace("’", "'").lower()


class EntityExtractor(Module):
    name = "entity_extractor"
    version = "0.2.0"
    implementation_kind = "rules"
    requires = frozenset({"token", "sentence", "metadata_constraint", "predication", "attribution_frame"})
    produces = frozenset({"entity_mention", "entity_rejection"})

    def run(self, doc: SourceDocument, scene: SceneInput, view: AnnotationView) -> ModuleOutput:
        out = ModuleOutput()
        context = chapter_context(doc)
        speakers = {f.value["speaker_span"].char_start for f in view.by_kind("attribution_frame")
                    if f.value["speaker_kind"] == "name"}
        roles = {p.span.char_start: p.value["role"] for p in view.by_kind("predication")}
        constraints = view.by_kind("metadata_constraint")
        participants = [c for c in constraints if c.value["kind"] == "presence_qualifier"]

        participant_words: Set[str] = set()
        for c in participants:
            participant_words.update(_norm(w) for w in c.value["subject"].split())
        metadata_capitals: Set[str] = set()
        for c in constraints:
            metadata_capitals.update(_norm(w) for w in _MIDTEXT_CAPITAL.findall(c.value["text"]))

        tokens = view.by_kind("token")
        proper_surfaces = {_norm(t.value["surface"]) for t in tokens
                           if t.value["capitalization_reason"] == "proper_candidate" and not t.value["closed_class"]}

        for group in self._groups(doc, tokens):
            words = [t.value["surface"] for t in group]
            surface = " ".join(words)
            span = doc.span(group[0].span.char_start, group[-1].span.char_end)
            if len(group) == 1 and group[0].value["number_word"]:
                out.annotations.append(NewAnnotation("entity_rejection", span,
                                                     {"surface": surface, "reason": "number_word"}))
                continue
            context_line = None
            if any(t.value["capitalization_reason"] == "proper_candidate" for t in group):
                basis = "proper_capital"
            else:
                key = _norm(surface)
                start = group[0].span.char_start
                common = all(context.is_common(w) for w in words)
                if not common and start in speakers:
                    basis = "speech_tag_speaker"
                elif not common and roles.get(start) == "subject":
                    basis = "grammatical_subject"
                elif not common and roles.get(start) == "possessor":
                    basis = "possessor_of_subject"
                elif key in proper_surfaces:
                    basis = "corroborated_by_prose"
                elif all(_norm(w) in participant_words for w in words):
                    basis = "corroborated_by_metadata_participant"
                elif key in metadata_capitals:
                    basis = "corroborated_by_metadata_text"
                elif not common and len(words) == 1 and key in context.proper_lines:
                    basis, context_line = "chapter_corroboration", context.proper_lines[key]
                else:
                    out.annotations.append(NewAnnotation("entity_rejection", span,
                                                         {"surface": surface, "reason": "initial_capital_only"}))
                    continue
            out.annotations.append(NewAnnotation("entity_mention", span, {
                "surface": surface,
                "evidence_class": "PROSE",
                "basis": basis,
                "possessive": bool(group[-1].value["possessive"]),
                "number_headed": bool(group[0].value["number_word"] and len(group) > 1),
                **({"context_line": context_line} if context_line else {}),
            }))

        for c in participants:
            out.annotations.append(NewAnnotation("entity_mention", c.span, {
                "surface": c.value["subject"],
                "evidence_class": "AUTHOR_METADATA",
                "basis": "metadata_participant",
                "possessive": False,
                "number_headed": c.value["subject"].split()[0].lower() in {
                    "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"},
            }))
        return out

    @staticmethod
    def _groups(doc: SourceDocument, tokens) -> List[List[Annotation]]:
        by_sentence: Dict[int, List[Annotation]] = defaultdict(list)
        for t in tokens:
            by_sentence[t.value["sentence_id"]].append(t)
        groups: List[List[Annotation]] = []
        for sid in sorted(by_sentence):
            current: List[Annotation] = []
            for t in sorted(by_sentence[sid], key=lambda a: a.span.char_start):
                if t.value["closed_class"] or t.value["all_caps"]:
                    if current:
                        groups.append(current)
                    current = []
                    continue
                adjacent = bool(current) and (
                    current[-1].value["token_index"] + 1 == t.value["token_index"]
                    and doc.text[current[-1].span.char_end:t.span.char_start] == " "
                    and not current[-1].value["possessive"]
                )
                if current and not adjacent:
                    groups.append(current)
                    current = []
                current.append(t)
            if current:
                groups.append(current)
        return groups
