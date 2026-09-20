"""
test_pattern1_physicality_attribution.py -- Regression tests for the
2026-09-20 Pattern 1 attribution fix (engain-avatar-audit:
09-20-2026-pattern1-physicality-attribution-audit.md and the follow-up
implementation receipt).

Two evidence-scope narrowings to infer_physicality_enhanced(), in this
order of what they fix:

  1. ALL scene-metadata segments (not just participants:, unlike the
     narrower exclusion Pattern 4 uses for frequency counting) are
     excluded from physicality keyword scanning entirely. Metadata
     establishes scene facts, never narrative evidence of any one
     entity's physical state. Control case: Saresh was classified
     nonphysical purely because "consciousness" (describing Torrhen
     and the Aeon Keepers) sat in the same participants: segment as
     his name.

  2. Ordinary prose evidence must share a SENTENCE with the entity's
     name, not merely a segment/paragraph -- with a narrow exception
     reusing this file's own existing speech-verb attribution regexes
     (_CONT_NAME_VERB_RE / _CONT_VERB_NAME_RE) so a resolved "<Name>
     <speech-verb>" attribution still counts the whole segment
     (attribution + quote) as that entity's evidence, even when the
     quote itself falls in an adjacent sentence.

The speech-verb exception only fires for verbs already in
_SPEECH_VERBS. A verb outside that list (this file's own audit found
"mused" as a concrete example) is not covered and correctly falls back
to plain sentence scoping -- reported honestly as a known, un-widened
limit, not silently patched by expanding the verb list.

2026-09-20 follow-up correction (engain-avatar-audit's 09-20-2026-
nonphysical-keyword-safety-audit.md and implementation receipt): the
attribution-scope fix above was necessary but not sufficient. Even
correctly-scoped-to-the-right-entity evidence was unsafe, because bare
"consciousness"/"awareness"/"ethereal"/"projected <pronoun> awareness"
describe a MODE OF MENTAL ACTIVITY an otherwise-embodied character
exercises, not a claim that the entity lacks a body (confirmed via
Zephyr: "closed his eyes, letting his consciousness expand" -- he has
eyes). NONPHYSICAL_MANIFESTATION_KEYWORDS (the bare-noun set) is
removed entirely, replaced by _NONPHYSICAL_ENTITY_STATE_PATTERNS --
phrases that actually predicate a bodiless/noncorporeal state ("no
body", "had no physical form", "existed only as consciousness", "'s
form was ethereal"), still same-sentence scoped. Bare mental-life nouns
now cast no vote in either direction; if physicality isn't otherwise
established, the correct result is "unknown", not "nonphysical" --
"no evidence of a body" is not "evidence of no body". Evidence is also
now ranked rather than tie-broken: an explicit entity-state claim wins
outright over an ordinary physical action verb in the same sentence,
not the reverse.
"""

from __future__ import annotations

import unittest

from tier3.mettaext.passroom import pass2_enhanced
from tier3.mettaext.passroom.pass2_enhanced import Character, Segment


def _seg(line_no: int, text: str, seg_type: str = "narration", speaker=None) -> Segment:
    return Segment(tag_line_no=line_no, text_line_no=line_no, type=seg_type, speaker=speaker, text=text)


def _local_char(name: str) -> Character:
    c = Character(name=name)
    c.presence = "local"
    c.presence_confidence = 1.0
    return c


class TestSaresh(unittest.TestCase):
    """The confirmed control case: a name that only ever appears in the
    participants: metadata line, alongside another entity's
    parenthetical "consciousness" description in the same segment,
    must no longer be classified nonphysical."""

    def test_saresh_no_longer_receives_false_nonphysical(self):
        segments = [
            _seg(1, "@scene_meta_participants: Torhh, Saresh, Torrhen (embedded consciousness), Aeon Keepers (consciousness contact)"),
            _seg(2, "scene meta:"),
            _seg(3, "participants: Torhh, Saresh, Torrhen (embedded consciousness), Aeon Keepers (consciousness contact)"),
            _seg(4, "The valley was quiet under the ash-grey sky."),
        ]
        characters = {"Saresh": _local_char("Saresh")}
        pass2_enhanced.infer_physicality_enhanced(segments, characters)
        self.assertEqual(characters["Saresh"].physicality, "unknown")


class TestMetadataTriggersEliminatedUnlessIndependentlySupported(unittest.TestCase):
    def test_metadata_only_keyword_does_not_classify(self):
        """A physical keyword appearing only in a metadata line, next
        to an entity's name, must not classify that entity either --
        confirms the exclusion isn't one-sided toward nonphysical."""
        segments = [
            _seg(1, "@scene_meta_focus: Elyraen stood at the threshold, watching."),
            _seg(2, "scene meta:"),
            _seg(3, "focus: Elyraen stood at the threshold, watching."),
            _seg(4, "Nothing else happened in this scene's prose body."),
        ]
        characters = {"Elyraen": _local_char("Elyraen")}
        pass2_enhanced.infer_physicality_enhanced(segments, characters)
        self.assertEqual(characters["Elyraen"].physicality, "unknown")

    def test_metadata_keyword_ignored_but_real_prose_evidence_still_counts(self):
        """The same entity, same metadata noise, but with genuine prose
        evidence elsewhere -- must classify correctly from the prose,
        proving the fix removes metadata as a source without removing
        real evidence."""
        segments = [
            _seg(1, "@scene_meta_focus: Elyraen's consciousness reached outward."),
            _seg(2, "scene meta:"),
            _seg(3, "focus: Elyraen's consciousness reached outward."),
            _seg(4, "Elyraen stood at the threshold, watching the tide come in."),
        ]
        characters = {"Elyraen": _local_char("Elyraen")}
        pass2_enhanced.infer_physicality_enhanced(segments, characters)
        self.assertEqual(characters["Elyraen"].physicality, "physical")


class TestExistingSameSentenceClassificationsUnchanged(unittest.TestCase):
    def test_same_sentence_physical_evidence_still_classifies(self):
        segments = [
            _seg(1, "Senareth tried to stand and immediately fell onto the sand."),
        ]
        characters = {"Senareth": _local_char("Senareth")}
        pass2_enhanced.infer_physicality_enhanced(segments, characters)
        self.assertEqual(characters["Senareth"].physicality, "physical")

    def test_same_sentence_nonphysical_evidence_still_classifies(self):
        """2026-09-20 correction: 'projected her awareness' no longer
        counts (it's an action, not an entity-state claim) -- this uses
        a genuine entity-state construction instead, grounded directly
        in real corpus phrasing (Lyaris: 'existed as distributed
        awareness across probability matrices')."""
        segments = [
            _seg(1, "Vaelith existed as distributed awareness across probability matrices."),
        ]
        characters = {"Vaelith": _local_char("Vaelith")}
        pass2_enhanced.infer_physicality_enhanced(segments, characters)
        self.assertEqual(characters["Vaelith"].physicality, "nonphysical")

    def test_action_verb_alone_no_longer_establishes_nonphysical(self):
        """Direct regression pin for the corrected rule: 'projects
        awareness' != 'is nonphysical'."""
        segments = [
            _seg(1, "Vaelith projected her awareness through the Veil, sensing distant shifts."),
        ]
        characters = {"Vaelith": _local_char("Vaelith")}
        pass2_enhanced.infer_physicality_enhanced(segments, characters)
        self.assertEqual(characters["Vaelith"].physicality, "unknown")


class TestCrossSentenceWithinSegmentNoLongerBorrowsEvidence(unittest.TestCase):
    """The general form of the attribution-radius problem, in real
    prose rather than metadata: two names in the same paragraph/
    segment, only one of them actually linked to the keyword."""

    def test_unknown_preferred_over_borrowed_cross_sentence_evidence(self):
        segments = [
            _seg(1, "Elyraen challenged their assumptions, arguing late into the night. Something the Aeon Keepers hadn't fully predicted was falling toward the surface."),
        ]
        characters = {"Elyraen": _local_char("Elyraen")}
        pass2_enhanced.infer_physicality_enhanced(segments, characters)
        # "falling" is in the second sentence, which never names Elyraen --
        # must not attach to her.
        self.assertEqual(characters["Elyraen"].physicality, "unknown")


class TestSpeechVerbAttributionException(unittest.TestCase):
    """The narrow exception: a resolved '<Name> <speech-verb>' opening
    lets the whole segment (attribution + quote) count as that
    entity's evidence, even when the actual keyword falls in a
    different sentence than the name itself."""

    def test_name_verb_attribution_extends_evidence_to_whole_segment(self):
        """Uses a genuine entity-state construction in the quote ('had
        no physical form'), grounded in the same phrase family as the
        real corpus's 'had no physical mass'/'had no physical
        substance' -- bare 'consciousness' in a quote no longer counts
        on its own, per the 2026-09-20 correction."""
        segments = [
            _seg(1, 'Torhh said, "I had no physical form before the ritual bound me here."'),
        ]
        characters = {"Torhh": _local_char("Torhh")}
        pass2_enhanced.infer_physicality_enhanced(segments, characters)
        self.assertEqual(characters["Torhh"].physicality, "nonphysical")

    def test_verb_outside_speech_verb_list_is_not_covered_by_the_exception(self):
        """Honest, documented limit: 'mused' is not in _SPEECH_VERBS,
        so this case is not rescued by the exception and correctly
        falls back to plain sentence scoping, landing on unknown."""
        segments = [
            _seg(1, 'Zaron mused. "I had no physical form before the ritual bound me here."'),
        ]
        characters = {"Zaron": _local_char("Zaron")}
        pass2_enhanced.infer_physicality_enhanced(segments, characters)
        self.assertEqual(characters["Zaron"].physicality, "unknown")

    def test_verb_first_attribution_form_also_extends_evidence(self):
        segments = [
            _seg(1, 'said Torhh, "I have stood here since the beginning."'),
        ]
        characters = {"Torhh": _local_char("Torhh")}
        pass2_enhanced.infer_physicality_enhanced(segments, characters)
        self.assertEqual(characters["Torhh"].physicality, "physical")


class TestBareMentalVocabularyNoLongerVotes(unittest.TestCase):
    """The corrected rule's core cases, directly from the audit."""

    def test_expanded_consciousness_alone_is_unknown(self):
        segments = [_seg(1, "Zephyr expanded his consciousness into the mathematical space.")]
        characters = {"Zephyr": _local_char("Zephyr")}
        pass2_enhanced.infer_physicality_enhanced(segments, characters)
        self.assertEqual(characters["Zephyr"].physicality, "unknown")

    def test_consciousness_touching_another_consciousness_is_unknown(self):
        segments = [_seg(1, "Zephyr's consciousness touched Torrhen's, and understanding passed between them.")]
        characters = {"Zephyr": _local_char("Zephyr")}
        pass2_enhanced.infer_physicality_enhanced(segments, characters)
        self.assertEqual(characters["Zephyr"].physicality, "unknown")

    def test_ethereal_describing_an_object_not_the_entity_does_not_make_it_nonphysical(self):
        """The confirmed real corpus case: 'ethereal' modifying
        something the entity is physically interacting with (Oreck
        tearing 'furrows in ethereal matter' with his claws) must not
        attach to the entity as nonphysical evidence.

        2026-09-20 vocabulary expansion note: this sentence now
        correctly classifies Oreck as physical instead of unknown --
        "grabbed" (added to _AMBIGUOUS_CONTACT_VERBS) fires because he
        is, per this exact sentence, physically grabbing and tearing
        something. That's a genuine improvement, not a regression: the
        point of this test was always that "ethereal" shouldn't make
        him nonphysical, and it still doesn't."""
        segments = [_seg(1, "Oreck grabbed the spectral chain and tore it free with claws that left furrows in ethereal matter.")]
        characters = {"Oreck": _local_char("Oreck")}
        pass2_enhanced.infer_physicality_enhanced(segments, characters)
        self.assertEqual(characters["Oreck"].physicality, "physical")

    def test_ethereal_blade_does_not_establish_entity_nonphysical(self):
        segments = [_seg(1, "Oreck swung an ethereal blade in a wide arc.")]
        characters = {"Oreck": _local_char("Oreck")}
        pass2_enhanced.infer_physicality_enhanced(segments, characters)
        self.assertEqual(characters["Oreck"].physicality, "unknown")


class TestGenuineEntityStatePatterns(unittest.TestCase):
    """Each pattern the corrected lexicon actually recognizes."""

    def _check(self, name: str, sentence: str, expected: str):
        segments = [_seg(1, sentence)]
        characters = {name: _local_char(name)}
        pass2_enhanced.infer_physicality_enhanced(segments, characters)
        self.assertEqual(characters[name].physicality, expected, sentence)

    def test_no_body(self):
        self._check("Vaelith", "Vaelith had no body, only presence.", "nonphysical")

    def test_without_a_body(self):
        self._check("Vaelith", "Vaelith existed without a body in the space between thoughts.", "nonphysical")

    def test_existed_only_as_consciousness_grounded_in_real_corpus_phrasing(self):
        self._check("Lyaris", "Lyaris existed as distributed awareness across probability matrices.", "nonphysical")

    def test_had_no_physical_mass_grounded_in_real_corpus_phrasing(self):
        self._check("Zaron", "Zaron was a presence that had no physical mass but occupied space nonetheless.", "nonphysical")

    def test_form_was_ethereal_construction(self):
        self._check("Oreck", "Oreck's form was ethereal, drifting rather than walking.", "nonphysical")

    def test_bodiless(self):
        self._check("Vaelith", "Vaelith remained bodiless, a presence without form.", "nonphysical")


class TestEntityStateEvidenceOutranksPhysicalAction(unittest.TestCase):
    """Ranking, not tie-breaking: an explicit entity-state claim wins
    even when ordinary physical-action vocabulary appears too."""

    def test_no_body_wins_over_physical_action_in_same_sentence(self):
        segments = [_seg(1, "Vaelith had no body, yet somehow she stood at the threshold.")]
        characters = {"Vaelith": _local_char("Vaelith")}
        pass2_enhanced.infer_physicality_enhanced(segments, characters)
        self.assertEqual(characters["Vaelith"].physicality, "nonphysical")


class TestPhysicalVocabularyExpansion(unittest.TestCase):
    """2026-09-20 corpus-backed physical vocabulary expansion, scoped
    only to the positive side of infer_physicality_enhanced(), after
    the nonphysical side was already fixed (f0f0698)."""

    def _check(self, name: str, sentence: str, expected: str):
        segments = [_seg(1, sentence)]
        characters = {name: _local_char(name)}
        pass2_enhanced.infer_physicality_enhanced(segments, characters)
        self.assertEqual(characters[name].physicality, expected, sentence)

    def test_locomotion_approached(self):
        self._check("Pazuzu", "Pazuzu approached Torhh slowly, his elongated form diminished with age.", "physical")

    def test_locomotion_ventured(self):
        self._check("Giant", "The jade-green Giant had ventured closer than any Giant since the landing.", "physical")

    def test_body_formation_solidified(self):
        self._check("Korrhan", "Korrhan's stone-flesh had solidified unevenly after the ritual.", "physical")

    def test_body_description_stone_flesh_phrase(self):
        self._check("Giants", "Giants bore wounds that even their stone-flesh struggled to heal.", "physical")

    def test_body_part_possessive_eyes(self):
        self._check("Torhh", "Torhh's ocean-deep eyes carried grief that geological patience couldn't absorb.", "physical")

    def test_body_part_possessive_fingers(self):
        self._check("Zephyr", "Zephyr pressed his elongated fingers against the crystalline calculation matrix.", "physical")

    def test_bare_body_part_noun_alone_does_not_count(self):
        """The construction requirement matters: a bare body-part noun
        with no possessive tying it to the entity must not fire."""
        segments = [_seg(1, "Zephyr studied the eyes of the storm on the horizon.")]
        characters = {"Zephyr": _local_char("Zephyr")}
        pass2_enhanced.infer_physicality_enhanced(segments, characters)
        self.assertEqual(characters["Zephyr"].physicality, "unknown")

    def test_physical_sensation_against_skin(self):
        self._check("Nameless", "Nameless felt it warm against their skin, responsive to touch in ways the old technology never was.", "physical")

    def test_felt_emotion_alone_does_not_count_as_physical_sensation(self):
        """Bare 'felt' remains unsafe -- this corpus uses it constantly
        for emotional/mental states, not bodily sensation."""
        segments = [_seg(1, "Pazuzu felt violated in ways his mathematical mind struggled to process.")]
        characters = {"Pazuzu": _local_char("Pazuzu")}
        pass2_enhanced.infer_physicality_enhanced(segments, characters)
        self.assertEqual(characters["Pazuzu"].physicality, "unknown")

    def test_ambiguous_contact_verb_counts_when_unguarded(self):
        self._check("Pazuzu", "Pazuzu gripped the ledge and pulled himself upward toward the surface.", "physical")

    def test_ambiguous_contact_verb_excluded_near_consciousness_language(self):
        """The confirmed real corpus contamination: 'gripped' also
        serves as a metaphor for mental/psychic effect in this text
        ('the glacial cold that still gripped its consciousness') --
        must not count as physical evidence when consciousness/
        awareness/mind shares the sentence."""
        segments = [_seg(1, "Torhh screamed through the glacial cold that still gripped its consciousness.")]
        characters = {"Torhh": _local_char("Torhh")}
        pass2_enhanced.infer_physicality_enhanced(segments, characters)
        self.assertEqual(characters["Torhh"].physicality, "unknown")

    def test_touch_deliberately_not_added_due_to_consciousness_touch_compound(self):
        """Confirms the deliberate exclusion: this corpus's own
        'consciousness-touch' compound term (telepathic communication)
        must not be picked up as physical contact just because 'touch'
        appears near an entity's name."""
        segments = [_seg(1, "Pazuzu extended consciousness-touch toward Torhh, tentative and respectful.")]
        characters = {"Pazuzu": _local_char("Pazuzu")}
        pass2_enhanced.infer_physicality_enhanced(segments, characters)
        self.assertEqual(characters["Pazuzu"].physicality, "unknown")

    def test_struck_as_simile_deliberately_not_added(self):
        """Confirms the deliberate exclusion: 'struck ... like a
        physical force' is this corpus's own figurative usage for
        mental impact, not literal contact -- 'struck' was not added
        to the physical lexicon specifically because of this pattern."""
        segments = [_seg(1, "Understanding struck Zephyr like a physical force.")]
        characters = {"Zephyr": _local_char("Zephyr")}
        pass2_enhanced.infer_physicality_enhanced(segments, characters)
        self.assertEqual(characters["Zephyr"].physicality, "unknown")

    def test_sage_transcendence_regression_control_survives_vocabulary_expansion(self):
        """The explicit regression control: Sage's sole surviving
        nonphysical classification must not be overturned merely
        because physical vocabulary grew -- nonphysical still ranks
        above physical even when both could theoretically fire."""
        segments = [_seg(
            1,
            "The Sage existed as consciousness recognizing itself through every form it "
            "encountered, his elongated fingers pressed against the mathematical matrix "
            "one final time.",
        )]
        characters = {"Sage": _local_char("Sage")}
        pass2_enhanced.infer_physicality_enhanced(segments, characters)
        self.assertEqual(characters["Sage"].physicality, "nonphysical")


if __name__ == "__main__":
    unittest.main()
