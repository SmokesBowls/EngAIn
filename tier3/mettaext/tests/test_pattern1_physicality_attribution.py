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

No vocabulary changes in this patch -- PHYSICAL_MANIFESTATION_KEYWORDS
and NONPHYSICAL_MANIFESTATION_KEYWORDS are untouched, and the speech-
verb exception only fires for verbs already in _SPEECH_VERBS. A verb
outside that list (this file's own audit found "mused" as a concrete
example) is not covered and correctly falls back to plain sentence
scoping -- reported honestly as a known, un-widened limit, not silently
patched by expanding the verb list.
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
        segments = [
            _seg(1, "Vaelith projected her awareness through the Veil, sensing distant shifts."),
        ]
        characters = {"Vaelith": _local_char("Vaelith")}
        pass2_enhanced.infer_physicality_enhanced(segments, characters)
        self.assertEqual(characters["Vaelith"].physicality, "nonphysical")


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
        segments = [
            _seg(1, 'Torhh said, "Three consciousness sharing single host. You, me, and the construct."'),
        ]
        characters = {"Torhh": _local_char("Torhh")}
        pass2_enhanced.infer_physicality_enhanced(segments, characters)
        self.assertEqual(characters["Torhh"].physicality, "nonphysical")

    def test_verb_outside_speech_verb_list_is_not_covered_by_the_exception(self):
        """Honest, documented limit: 'mused' is not in _SPEECH_VERBS,
        so this case is not rescued by the exception and correctly
        falls back to plain sentence scoping, landing on unknown."""
        segments = [
            _seg(1, 'Zaron mused. "Three consciousness sharing single host, you, me, and this construct."'),
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


if __name__ == "__main__":
    unittest.main()
