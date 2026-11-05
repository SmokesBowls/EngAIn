"""linguistic_annotator (GEN2_MODULES.md §2.4), v0.2.

Input:   `prose` regions only (one region = one paragraph line). Metadata,
         headers and structural headings are never tokenised as language,
         which by itself removes the legacy failure where yaml words
         (Chapter, Core, Stage, ...) became entities.
Output:  `sentence` annotations.
         `token` for every capitalised word: capitalization_reason
         (sentence_initial | quote_initial | post_quote | proper_candidate),
         closed_class, possessive, number_word, the in-sentence index.
         `quote_region` per paired quotation: {quote_id, paragraph_line,
         embedded_term}. A quotation opened straight after a word with no
         punctuation between ("their "liberation"") is a term, not speech.
         Straight quotes alternate open/close within a paragraph; curly
         quotes pair by shape. A paragraph whose quotes do not pair is
         reported `unanalysed` (diagnostic) and gets no quote regions or
         frames; its tokens keep the v0.1 conservative reading.
         `predication`: the subject at the start of a clause, with its verb:
         {role: subject | possessor, surface, verb, verb_classes, negated,
         in_quote, sentence_id}. Span = the subject's name.
         `attribution_frame`: a speech tag beside a quotation:
         {pattern, speaker_kind: name | pronoun | descriptive, speaker_text,
         speaker_span?, verb, recalled, quote_id}. Span = the tag.
Allowed: grammatical and structural facts only. verb_classes is a lexical
         fact about the verb (speech, cognition, perception, physical,
         deliberate, absence), not a claim about the subject.
Forbidden: entity types, identities, relations, presence. This module
         decides what a word *is*, never who it is.
Not built yet (spec §2.4): voice, deixis, figurative markers. A name inside
         a simile ("moved like Torhh") is never a clause subject here, so it
         gets no predication.

chapter_context() reads the same facts over the whole chapter's prose for
modules that need wider linguistic context (decision 2026-10-29: chapter as
context, scene-level outputs). It takes the document, so a book-level
context can later merge several chapters.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

from ..lib.annotations import AnnotationView, Diagnostic, Module, ModuleOutput, NewAnnotation, SceneInput
from ..lib.source import SourceDocument
from .scene_segmenter import classify_lines

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


_STEMS: Set[str] = set()


def _forms(stems: str, extra: str = "") -> FrozenSet[str]:
    """Regular inflections of each stem, plus listed irregular forms."""
    out: Set[str] = set(extra.split())
    _STEMS.update(stems.split())
    for s in stems.split():
        out |= {s, s + "s", s + "es", s + "ed", s + "ing"}
        if s.endswith("e"):
            out |= {s + "d", s[:-1] + "ing"}
        if s.endswith("y"):
            out |= {s[:-1] + "ied", s[:-1] + "ies"}
    return frozenset(out)


# Verb lexicons: lexical facts used to read a clause, never to type an entity.
SPEECH = _forms(
    "say ask observe confirm add report note admit agree continue answer reply respond conclude insist "
    "correct explain suggest propose command instruct request urge warn promise announce state offer "
    "protest object clarify remind assure argue breathe mutter murmur whisper shout call summarize "
    "decide finish repeat caution counter point press realize declare acknowledge concede interrupt "
    "exclaim sigh resonate "
    # manner-of-speaking verbs (standard English class; added 2026-10-29 after the first held-out run)
    "growl rumble grumble bellow roar snarl challenge hiss snap bark yell scream groan grunt retort demand "
    "plead beg rasp whimper sneer stammer stutter chuckle laugh "
    # added after the second held-out run (Book 7 038), so that chapter is no longer blind for them
    "order gasp",
    "said told spoke cried")
COGNITION = _forms(
    "realize decide consider wonder sense understand remember notice recognize think know feel search "
    "study analyze calculate monitor process recall imagine believe hope suspect expect intend plan choose",
    "knew thought felt understood chose")
# Outside a speech tag only unambiguous verbs of saying count: "Debate continued" is not speech.
SPEECH_STRICT = _forms(
    "say ask reply answer whisper shout murmur mutter explain insist protest exclaim instruct command "
    "request urge warn promise announce declare acknowledge concede", "said told spoke")
PERCEPTION = _forms("watch see look hear observe perceive stare glance listen gaze regard scan", "saw heard")
# Verbs that select an animate agent. Verbs inanimate subjects also take (rise, move, sway, fall,
# shake, place, make, form, begin, work) are left out on purpose: "Waves rose", "Trees swayed".
PHYSICAL = _forms(
    "stand sit walk kneel run step turn reach touch gesture nod smile frown wave lift raise grab carry "
    "climb crouch lean approach retreat flee enter arrive return sleep wake pick throw dig swim wade grip "
    "stumble jump hurry pace shiver cough",
    "stood sat knelt ran stepped nodded slept woke dug swam threw grabbed gripped crept")
DELIBERATE = _forms(
    "extend project select organize prepare craft send guide teach lead order offer help wait try "
    "attempt create manipulate establish arrange accept refuse",
    "sent taught led")
VERB_CLASSES = (("speech", SPEECH_STRICT), ("cognition", COGNITION), ("perception", PERCEPTION),
                ("physical", PHYSICAL), ("deliberate", DELIBERATE))
# Nouns that make a possessor the agent of the clause ("Mordain's consciousness resonated").
MIND_NOUNS = frozenset("consciousness awareness mind thoughts thought voice attention gaze eyes face "
                       "expression hands hand body presence".split())
AUXILIARIES = frozenset("was were is are am be been had has have would could should might must will "
                        "shall did does do can may".split())
NEGATORS = frozenset({"not", "never", "no"})
BE_FORMS = frozenset({"was", "were", "is", "are", "am", "be", "been", "being"})
SOFT_ADVERBS = frozenset("already still just then now finally also even again once quietly softly "
                         "carefully slowly suddenly simply".split())
ABSENCE_AFTER_NEGATION = frozenset({"there", "here", "present"})
ABSENCE_WORDS = frozenset({"absent", "gone", "missing"})
DEPARTURE_AFTER_HAD = frozenset({"left", "gone", "departed", "vanished"})
PRONOUNS = frozenset({"he", "she", "they", "it", "we", "i", "you"})

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


def sentence_bounds(text: str, start: int = 0, end: Optional[int] = None) -> List[Tuple[int, int]]:
    end = len(text) if end is None else end
    bounds, s = [], start
    for m in _SENT_END.finditer(text, start, end):
        if text[s:m.end()].strip():
            bounds.append((s, m.end()))
        s = m.end()
    if text[s:end].strip():
        bounds.append((s, end))
    return bounds


def verb_classes(word: str) -> Tuple[str, ...]:
    w = word.lower()
    return tuple(name for name, lexicon in VERB_CLASSES if w in lexicon)


def embedded_term(text: str, open_at: int) -> bool:
    """A quotation opened right after a word with no punctuation between is a term, not speech
    (their "liberation", the "processing line,")."""
    before = text[:open_at]
    return bool(re.search(r"[A-Za-z]\s+$", before)) and not re.search(r"[,:;.!?—–]\s*$", before)


def quote_pairs(text: str) -> Optional[List[Tuple[int, int]]]:
    """(open, close) offsets of each quotation in a paragraph; None when quotes do not pair."""
    straight = [i for i, ch in enumerate(text) if ch == '"']
    if len(straight) % 2:
        return None
    pairs = list(zip(straight[0::2], straight[1::2]))
    stack: List[int] = []
    for i, ch in enumerate(text):
        if ch == "“":
            stack.append(i)
        elif ch == "”":
            if not stack:
                return None
            pairs.append((stack.pop(), i))
    if stack:
        return None
    return sorted(pairs)


@dataclass
class _Tok:
    start: int
    end: int
    word: str
    reason: str = ""


@dataclass
class _Predication:
    role: str
    name_start: int
    name_end: int
    verb: str
    classes: Tuple[str, ...]
    negated: bool


@dataclass
class _Frame:
    pattern: str
    speaker_kind: str
    tag_start: int
    tag_end: int
    verb: str
    recalled: bool
    speaker: Optional[Tuple[int, int]] = None


def _words(text: str, start: int, end: int) -> List[_Tok]:
    return [_Tok(m.start(), m.end(), m.group(0)) for m in _TOKEN.finditer(text, start, end)]


def _cap_group(text: str, words: List[_Tok], i: int) -> Tuple[List[_Tok], int]:
    """Consecutive capitalised, non-closed-class words joined by single spaces; a possessive ends it."""
    group: List[_Tok] = []
    j = i
    while j < len(words):
        w = words[j]
        base, suffix = split_suffix(w.word)
        if not w.word[0].isupper() or base.lower() in CLOSED_CLASS or (w.word.isupper() and len(w.word) > 1):
            break
        if group and text[group[-1].end:w.start] != " ":
            break
        group.append(w)
        j += 1
        if suffix in ("’s", "'s"):
            break
    return group, j


def _gap(text: str, a: _Tok, b: _Tok) -> str:
    return text[a.end:b.start]


def _clause_verb(text: str, words: List[_Tok], j: int, narration: bool = False, tag: bool = False
                 ) -> Optional[Tuple[int, str, Tuple[str, ...], bool]]:
    """From words[j], skip auxiliaries, soft adverbs and negation; return (index, verb, classes, negated)."""
    negated, saw_aux, saw_had, saw_be, start = False, False, False, False, j
    while j < len(words):
        w = words[j].word.lower()
        if j > start and _gap(text, words[j - 1], words[j]).strip():
            return None
        if w in NEGATORS or w.endswith("n't") or w.endswith("n’t"):
            negated = True
        elif w in AUXILIARIES:
            saw_aux, saw_had = True, saw_had or w == "had"
            saw_be = saw_be or w in BE_FORMS
        elif w in SOFT_ADVERBS or (w.endswith("ly") and len(w) > 4):
            pass
        else:
            break
        j += 1
    if j >= len(words) or (j > start and _gap(text, words[j - 1], words[j]).strip()):
        return None
    verb = words[j].word.lower()
    if (negated and verb in ABSENCE_AFTER_NEGATION) or verb in ABSENCE_WORDS or (saw_had and verb in DEPARTURE_AFTER_HAD):
        return j, verb, ("absence",), negated
    # A bare stem after a singular name is a noun ("Physical form"), unless an auxiliary licenses it.
    if verb in _STEMS and not saw_aux:
        return None
    # A participle with no auxiliary is not a finite clause ("Wind moving through air").
    if verb.endswith("ing") and not saw_aux:
        return None
    # be/been + past participle is passive: its subject is not the agent ("Sacrifices had been made").
    if saw_be and not verb.endswith("ing"):
        return None
    # shortcut: narration is read as past tense, so a bare -s form there is a plural noun
    # ("Affirmative gestures rippled"), not a verb; revisit for present-tense narration.
    if narration and not saw_aux and verb.endswith("s") and not verb.endswith("ss"):
        return None
    classes = verb_classes(verb)
    if tag and verb in SPEECH and "speech" not in classes:
        classes += ("speech",)   # in a speech tag the broad list applies ("Lyaris continued")
    return (j, verb, classes, negated) if classes else None


def _subject_at(text: str, words: List[_Tok], i: int, narration: bool = False,
                tag: bool = False) -> Optional[_Predication]:
    """A capitalised subject starting at words[i], read through an appositive or a possessive head."""
    group, j = _cap_group(text, words, i)
    if not group:
        return None
    base, suffix = split_suffix(group[-1].word)
    name_end = group[-1].start + len(base)
    role = "subject"
    if suffix in ("’s", "'s"):
        if j >= len(words) or words[j].word.lower() not in MIND_NOUNS or _gap(text, group[-1], words[j]) != " ":
            return None
        role, j = "possessor", j + 1
    elif j < len(words) and _gap(text, group[-1], words[j]).strip() in (",", "—"):
        # Appositive or relative clause: "Theron, whose ..., extended" -> the verb after the closing comma.
        k = j + 1
        while k < len(words):
            if _gap(text, words[k - 1], words[k]).strip() in (",", "—") and verb_classes(words[k].word):
                break
            k += 1
        else:
            return None
        j = k
    elif j < len(words) and _gap(text, group[-1], words[j]).strip():
        return None
    found = _clause_verb(text, words, j, narration, tag)
    if not found and role == "possessor" and j < len(words) and words[j].word.endswith("ed") \
            and _gap(text, words[j - 1], words[j]) == " ":
        # "Vaelith's awareness rippled": a mind noun makes its possessor the agent whatever the past-tense verb.
        found = (j, words[j].word.lower(), ("mind",), False)
    if not found:
        return None
    _, verb, classes, negated = found
    return _Predication(role, group[0].start, name_end, verb, classes, negated)


def _clause_starts(text: str, start: int, end: int) -> List[int]:
    """Offsets where a clause may begin: sentence starts inside [start, end)."""
    starts = []
    for s, _ in sentence_bounds(text, start, end):
        m = re.compile(r"[\s,;:—–\-\"“”‘’(*_]*").match(text, s)   # * and _ are markdown emphasis
        starts.append(m.end())
    return starts


def _tag_after(text: str, start: int, end: int) -> Optional[_Frame]:
    """Speech tag right after a closing quote: name+verb, verb+name, pronoun+verb, or a description+verb."""
    words = _words(text, start, end)
    if not words or text[start:words[0].start].strip(" ,—") or len(text[start:words[0].start]) > 3:
        return None
    first = words[0]
    pred = _subject_at(text, words, 0, narration=True, tag=True)
    if pred and "speech" in pred.classes:
        return _Frame("Q_NAME_VERB", "name", first.start, _verb_end(text, words, pred.verb, first.start),
                      pred.verb, _recalled(text, first.start, end), (pred.name_start, pred.name_end))
    if first.word.lower() in SPEECH and len(words) > 1 and _gap(text, first, words[1]) == " ":
        group, _ = _cap_group(text, words, 1)
        if group:
            base, _s = split_suffix(group[-1].word)
            return _Frame("Q_VERB_NAME", "name", first.start, group[-1].start + len(base), first.word.lower(),
                          False, (group[0].start, group[-1].start + len(base)))
    if first.word.lower() in PRONOUNS:
        found = _clause_verb(text, words, 1, narration=True, tag=True)
        if found and "speech" in found[2]:
            return _Frame("Q_PRONOUN_VERB", "pronoun", first.start, words[found[0]].end, found[1],
                          _recalled(text, first.start, end))
    if first.word[0].islower():
        for k in range(1, min(5, len(words))):
            if words[k].word.lower() in SPEECH and not text[first.start:words[k].start].count(","):
                return _Frame("Q_DESCRIPTION_VERB", "descriptive", first.start, words[k].end,
                              words[k].word.lower(), False)
    return None


_TAG_BEFORE = re.compile(r"(?P<name>[A-Z][A-Za-z’']+(?: [A-Z][A-Za-z’']+)*)\s+(?:(?:\w+ly)\s+)?(?P<verb>[a-z]+)"
                         r"(?:\s+(?:back|out|up|again|aloud))?\s*[,:]\s*$")


def _tag_before(text: str, start: int, end: int) -> Optional[_Frame]:
    """Speech tag ending right before an opening quote: '... Korath observed, "'."""
    m = _TAG_BEFORE.search(text, start, end)
    if not m or m.group("verb") not in SPEECH or m.group("name").split()[0].lower() in CLOSED_CLASS:
        return None
    return _Frame("NAME_VERB_Q", "name", m.start("name"), m.end("verb"), m.group("verb"),
                  False, (m.start("name"), m.end("name")))


def _verb_end(text: str, words: List[_Tok], verb: str, after: int) -> int:
    for w in words:
        if w.start >= after and w.word.lower() == verb:
            return w.end
    return words[-1].end


def _recalled(text: str, start: int, end: int) -> bool:
    return bool(re.match(r"\s*(?:\w+\s+){0,2}had\s+\w+", text[start:end]))


@dataclass
class ParagraphFacts:
    quotes: Optional[List[Tuple[int, int]]]
    tokens: List[_Tok] = field(default_factory=list)
    predications: List[Tuple[_Predication, bool, int]] = field(default_factory=list)  # (pred, in_quote, sentence index)
    frames: List[Tuple[_Frame, int]] = field(default_factory=list)                   # (frame, quote index)
    sentences: List[Tuple[int, int]] = field(default_factory=list)


def paragraph_facts(text: str) -> ParagraphFacts:
    """Every grammatical fact this module knows about one paragraph, in paragraph offsets."""
    quotes = quote_pairs(text)
    facts = ParagraphFacts(quotes, sentences=sentence_bounds(text))
    closes = {c for _, c in quotes or []}

    for s_start, s_end in facts.sentences:
        first_word_seen = False
        for m in _TOKEN.finditer(text, s_start, s_end):
            word = m.group(0)
            is_first = not first_word_seen
            first_word_seen = True
            if not word[0].isupper():
                continue
            stripped = text[s_start:m.start()].rstrip()
            q = s_start + len(stripped) - 1
            after_quote = bool(stripped) and stripped[-1] in _OPEN_QUOTES and (
                len(stripped) == 1 or not stripped[-2].isalnum())
            if is_first:
                reason = "sentence_initial"
            elif after_quote:
                # Only a quote known to close is post_quote; unpaired or opening quotes keep v0.1's reading.
                reason = "post_quote" if quotes is not None and q in closes else "quote_initial"
            else:
                reason = "proper_candidate"
            facts.tokens.append(_Tok(m.start(), m.end(), word, reason))

    if quotes is None:
        return facts
    # Pieces: quoted text and the narration between quotations.
    pieces: List[Tuple[int, int, bool]] = []
    cursor = 0
    for o, c in quotes:
        if o > cursor:
            pieces.append((cursor, o, False))
        pieces.append((o + 1, c, True))
        cursor = c + 1
    if cursor < len(text):
        pieces.append((cursor, len(text), False))
    for p_start, p_end, in_quote in pieces:
        words = _words(text, p_start, p_end)
        for clause_start in _clause_starts(text, p_start, p_end):
            i = next((n for n, w in enumerate(words) if w.start >= clause_start), None)
            if i is None or words[i].start != clause_start:
                continue
            pred = _subject_at(text, words, i, narration=not in_quote)
            if pred:
                sid = next(n for n, (a, b) in enumerate(facts.sentences) if a <= pred.name_start < b)
                facts.predications.append((pred, in_quote, sid))
    for qi, (o, c) in enumerate(quotes):
        next_open = quotes[qi + 1][0] if qi + 1 < len(quotes) else len(text)
        prev_close = quotes[qi - 1][1] + 1 if qi else 0
        frame = _tag_after(text, c + 1, next_open)
        # '"...ago!" Halvar rasped back, "Hours!"': after a quote that ends its own sentence, a tag
        # running on with a comma into the next quote introduces that next quote.
        if frame and qi + 1 < len(quotes) and re.search(r"[.!?…][*_]*$", text[o + 1:c]) \
                and re.search(r"[,:]\s*$", text[c + 1:next_open]):
            frame = None
        frame = frame or _tag_before(text, prev_close, o)
        if frame:
            facts.frames.append((frame, qi))
    return facts


@dataclass
class ChapterContext:
    """Linguistic facts over the whole chapter's prose (context only; no spans outside the scene)."""
    lowercase_words: Set[str]
    proper_lines: Dict[str, int]       # normalised single-word surface -> first line used mid-sentence

    def is_common(self, word: str) -> bool:
        """The word, or the singular of a plural, is used lowercase somewhere in the chapter's prose."""
        w = _norm(word)
        forms = {w}
        if w.endswith("ies"):
            forms.add(w[:-3] + "y")
        if w.endswith("es"):
            forms.add(w[:-2])
        if w.endswith("s") and not w.endswith("ss"):
            forms.add(w[:-1])
        return bool(forms & self.lowercase_words)


def _norm(word: str) -> str:
    return word.replace("’", "'").lower()


def chapter_context(doc: SourceDocument) -> ChapterContext:
    lowercase: Set[str] = set()
    proper: Dict[str, int] = {}
    for region_type, line, _end, _extra in classify_lines(doc, 1, len(doc.line_offsets)):
        if region_type != "prose":
            continue
        text = doc.line_text(line)
        lowercase.update(_norm(w) for w in _TOKEN.findall(text) if w[0].islower())
        for tok in paragraph_facts(text).tokens:
            base, _ = split_suffix(tok.word)
            if tok.reason == "proper_candidate" and base.lower() not in CLOSED_CLASS:
                proper.setdefault(_norm(base), line)
    return ChapterContext(lowercase, proper)


class LinguisticAnnotator(Module):
    name = "linguistic_annotator"
    version = "0.2.0"
    implementation_kind = "rules"
    requires = frozenset({"region"})
    produces = frozenset({"sentence", "token", "quote_region", "predication", "attribution_frame"})

    def run(self, doc: SourceDocument, scene: SceneInput, view: AnnotationView) -> ModuleOutput:
        out = ModuleOutput()
        sentence_no = quote_no = 0
        for region in view.by_kind("region"):
            if region.value["region_type"] != "prose":
                continue
            base = region.span.char_start
            text = region.span.text
            line = region.span.line
            facts = paragraph_facts(text)
            if facts.quotes is None:
                out.diagnostics.append(Diagnostic("info", f"unanalysed: quotes do not pair at line {line}"))
            sentence_ids = []
            for s_start, s_end in facts.sentences:
                sentence_no += 1
                sentence_ids.append(sentence_no)
                raw = text[s_start:s_end]
                lead = len(raw) - len(raw.lstrip())
                trail = len(raw) - len(raw.rstrip())
                out.annotations.append(NewAnnotation(
                    "sentence", doc.span(base + s_start + lead, base + s_end - trail),
                    {"sentence_id": sentence_no},
                ))
            for tok in facts.tokens:
                sid_index = next(n for n, (a, b) in enumerate(facts.sentences) if a <= tok.start < b)
                index = sum(1 for _ in _TOKEN.finditer(text, facts.sentences[sid_index][0], tok.start))
                base_word, suffix = split_suffix(tok.word)
                closed = base_word.lower() in CLOSED_CLASS
                possessive = suffix in ("’s", "'s") and not closed
                surface = base_word if possessive else tok.word
                out.annotations.append(NewAnnotation(
                    "token", doc.span(base + tok.start, base + tok.start + len(surface)),
                    {
                        "surface": surface,
                        "capitalization_reason": tok.reason,
                        "closed_class": closed or tok.word.lower() in CLOSED_CLASS,
                        "number_word": base_word.lower() in NUMBER_WORDS,
                        "possessive": possessive,
                        "sentence_id": sentence_ids[sid_index],
                        "token_index": index,
                        "all_caps": tok.word.isupper() and len(tok.word) > 1,
                    },
                ))
            quote_ids = []
            for o, c in facts.quotes or []:
                quote_no += 1
                quote_ids.append(quote_no)
                out.annotations.append(NewAnnotation("quote_region", doc.span(base + o, base + c + 1),
                                                     {"quote_id": quote_no, "paragraph_line": line,
                                                      "embedded_term": embedded_term(text, o)}))
            for pred, in_quote, sid_index in facts.predications:
                out.annotations.append(NewAnnotation(
                    "predication", doc.span(base + pred.name_start, base + pred.name_end),
                    {"role": pred.role, "surface": text[pred.name_start:pred.name_end], "verb": pred.verb,
                     "verb_classes": list(pred.classes), "negated": pred.negated, "in_quote": in_quote,
                     "sentence_id": sentence_ids[sid_index], "paragraph_line": line},
                ))
            for frame, qi in facts.frames:
                value = {"pattern": frame.pattern, "speaker_kind": frame.speaker_kind,
                         "speaker_text": text[frame.speaker[0]:frame.speaker[1]] if frame.speaker else
                         text[frame.tag_start:frame.tag_end],
                         "verb": frame.verb, "recalled": frame.recalled, "quote_id": quote_ids[qi],
                         "paragraph_line": line}
                if frame.speaker:
                    value["speaker_span"] = doc.span(base + frame.speaker[0], base + frame.speaker[1])
                out.annotations.append(NewAnnotation(
                    "attribution_frame", doc.span(base + frame.tag_start, base + frame.tag_end), value))
        return out
