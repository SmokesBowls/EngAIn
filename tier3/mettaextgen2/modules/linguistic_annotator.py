"""linguistic_annotator (GEN2_MODULES.md §2.4).

Input:   `prose` regions only. Metadata, headers and structural headings are
         never tokenised as language, which by itself removes the legacy
         failure where yaml words (Chapter, Core, Stage, ...) became entities.
Output:  `sentence` annotations, and a `token` annotation for every
         capitalised word: capitalization_reason (sentence_initial |
         quote_initial | proper_candidate), closed_class, possessive,
         number_word, and the in-sentence index.
Allowed: grammatical and structural facts only.
Forbidden: entity types, identities, relations. This module decides what a
         word *is*, never who it is.
"""

from __future__ import annotations

import re
from typing import List, Tuple

from ..lib.annotations import AnnotationView, Module, ModuleOutput, NewAnnotation, SceneInput
from ..lib.source import SourceDocument

# Closed-class English words: never names on their own, wherever they appear.
CLOSED_CLASS = frozenset("""
a an the this that these those some any each every no all both either neither such what which whose who whom whoever whatever
i me my mine myself you your yours yourself yourselves he him his himself she her hers herself it its itself
we us our ours ourselves they them their theirs themselves one ones someone somebody something anyone anything
everyone everything nobody nothing
and or but nor so yet for if then than because although though while whereas unless until since when whenever
where wherever why how whether once
of in on at by to from with without within into onto upon over under above below between among through across
along around behind beyond beside besides near toward towards against during before after about like as per via
is am are was were be been being do does did done have has had having will would shall should can could may
might must ought let
not yes no oh ah well now here there again also too very just only even still already always never ever
perhaps maybe instead indeed thus hence however therefore meanwhile otherwise somewhere nowhere everywhere
up down out off away back
""".split())

NUMBER_WORDS = frozenset("""
one two three four five six seven eight nine ten eleven twelve twenty thirty hundred thousand
first second third fourth fifth
""".split())

_TOKEN = re.compile(r"[A-Za-z]+(?:[’'][A-Za-z]+)*")
_SENT_END = re.compile(r"[.!?…]+[\"”’)\]]*(?=\s|$)")
_OPEN_QUOTES = "“\"‘"
_CONTRACTION_SUFFIXES = ("n’t", "n't", "’s", "'s", "’re", "'re", "’ll", "'ll", "’ve", "'ve", "’d", "'d", "’m", "'m")


def split_suffix(word: str) -> Tuple[str, str]:
    """('Mika’s') -> ('Mika', '’s'); ('Didn’t') -> ('Did', 'n’t')."""
    lower = word.lower()
    for suffix in _CONTRACTION_SUFFIXES:
        if lower.endswith(suffix) and len(word) > len(suffix):
            return word[: -len(suffix)], word[-len(suffix):]
    return word, ""


def sentence_bounds(text: str) -> List[Tuple[int, int]]:
    bounds, start = [], 0
    for m in _SENT_END.finditer(text):
        end = m.end()
        if text[start:end].strip():
            bounds.append((start, end))
        start = end
    if text[start:].strip():
        bounds.append((start, len(text)))
    return bounds


class LinguisticAnnotator(Module):
    name = "linguistic_annotator"
    version = "0.1.0"
    implementation_kind = "rules"
    requires = frozenset({"region"})
    produces = frozenset({"sentence", "token"})

    def run(self, doc: SourceDocument, scene: SceneInput, view: AnnotationView) -> ModuleOutput:
        out = ModuleOutput()
        sentence_no = 0
        for region in view.by_kind("region"):
            if region.value["region_type"] != "prose":
                continue
            base = region.span.char_start
            text = region.span.text
            for s_start, s_end in sentence_bounds(text):
                sentence_no += 1
                raw = text[s_start:s_end]
                lead = len(raw) - len(raw.lstrip())
                trail = len(raw) - len(raw.rstrip())
                out.annotations.append(NewAnnotation(
                    "sentence", doc.span(base + s_start + lead, base + s_end - trail),
                    {"sentence_id": sentence_no},
                ))
                self._tokens(doc, out, text, base, s_start, s_end, sentence_no)
        return out

    def _tokens(self, doc, out, text, base, s_start, s_end, sentence_no) -> None:
        first_word_seen = False
        for index, m in enumerate(_TOKEN.finditer(text, s_start, s_end)):
            word = m.group(0)
            preceding = text[s_start:m.start()]
            is_first = not first_word_seen
            first_word_seen = True
            if not word[0].isupper():
                continue
            # A capital right after an opening quote is a convention of dialogue, not a name signal.
            stripped = preceding.rstrip()
            after_quote = bool(stripped) and stripped[-1] in _OPEN_QUOTES and (
                len(stripped) == 1 or not stripped[-2].isalnum())
            if is_first:
                reason = "sentence_initial"
            elif after_quote:
                reason = "quote_initial"
            else:
                reason = "proper_candidate"
            base_word, suffix = split_suffix(word)
            closed = base_word.lower() in CLOSED_CLASS
            possessive = suffix in ("’s", "'s") and not closed
            surface = base_word if possessive else word
            out.annotations.append(NewAnnotation(
                "token", doc.span(base + m.start(), base + m.start() + len(surface)),
                {
                    "surface": surface,
                    "capitalization_reason": reason,
                    "closed_class": closed or word.lower() in CLOSED_CLASS,
                    "number_word": base_word.lower() in NUMBER_WORDS,
                    "possessive": possessive,
                    "sentence_id": sentence_no,
                    "token_index": index,
                    "all_caps": word.isupper() and len(word) > 1,
                },
            ))
