"""
test_pattern4_participant_seeding.py -- Regression tests for the
2026-09-20 Pattern 4 fix (engain-avatar-audit:
09-20-2026-pattern4-silent-omission-traced.md and the follow-up
implementation receipt).

Root cause, traced and confirmed against the real Books 1-5 corpus: an
authored participant with fewer than 3 prose mentions (and no explicit
speaker tag) never became a Character candidate at all in
pass2_enhanced.py's extract_characters() -- a threshold entirely
separate from, and untouched by, 3f58af9's earlier removal of the old
mentions<3 exclusion in pass2_entity_filter.py. Worse, the exact count
that fell short of 3 was itself partly a metadata artifact: the same
participants: text is represented twice in a packet (the structured
@scene_meta_participants: header Pass C adds, and the original raw
participants: line), so a participant with zero real prose mentions
still scored 2 -- one short of the old threshold, but for the wrong
reason entirely.

Two independent behaviors, kept separate per instruction:
  1. Every authored participant now seeds a Character candidate
     unconditionally, regardless of prose mention count.
  2. Metadata-line representations (both forms) are excluded from the
     PROSE mention count used for frequency-based discovery, so a
     zero-prose-mention participant is correctly recorded as
     mentions=0, not artificially inflated to 2.

Scope: pass2_enhanced.py candidate construction only. Physicality
inference, remote inference, world_rules, aliases, and Pattern 3 noise
(title fragments like "Aeon"/"Nameless") are explicitly untouched by
this patch and not tested here.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tier3.mettaext.passroom import pass1_explicit, pass2_enhanced, pass2_entity_filter
from tier3.mettaext.passroom.pass2_enhanced import Segment


def _seg(line_no: int, seg_type: str, text: str, speaker=None) -> Segment:
    return Segment(tag_line_no=line_no, text_line_no=line_no, type=seg_type, speaker=speaker, text=text)


class TestParticipantSeededAtZeroProseMentions(unittest.TestCase):
    """Requirement 1 + acceptance case: a participant named only in
    metadata, never in narrative prose, must still survive."""

    def test_zero_prose_mention_participant_becomes_a_candidate(self):
        segments = [
            _seg(1, "narration", "@scene_meta_participants: The Nameless One, The Five, Mika"),
            _seg(2, "narration", "participants: The Nameless One, The Five, Mika"),
            _seg(3, "narration", "The compound stretched toward the horizon, quiet in the early light."),
            _seg(4, "narration", "Slaves moved between the rows, carrying tools nobody had named."),
            _seg(5, "narration", "The overseer watched from the tower without speaking."),
        ]
        characters = pass2_enhanced.extract_characters(segments)
        self.assertIn("Mika", characters)

    def test_zero_prose_mention_participant_has_mentions_zero_not_two(self):
        """Requirement 4 / the exact metadata-duplication artifact
        traced in the corpus: two metadata representations of the same
        line must not be counted as two prose mentions. The raw
        'participants:' line is only recognized as metadata when
        anchored to a preceding 'scene meta:' header, exactly as real
        packets are shaped (passB's own _parse_scene_meta uses the
        same anchor)."""
        segments = [
            _seg(1, "narration", "@scene_meta_participants: The Nameless One, The Five, Mika"),
            _seg(2, "narration", "scene meta:"),
            _seg(3, "narration", "participants: The Nameless One, The Five, Mika"),
            _seg(4, "narration", "The compound stretched toward the horizon, quiet in the early light."),
        ]
        characters = pass2_enhanced.extract_characters(segments)
        self.assertEqual(characters["Mika"].mentions, 0)


class TestExclusionScopedToParticipantsLineOnly(unittest.TestCase):
    """Requirement 4 is scoped exactly to the participants: line's own
    duplication (@scene_meta_participants: + raw participants:), not
    to scene_meta generally. Verified against the real Books 1-5
    corpus that a broader exclusion (also covering focus:/cutscene
    purpose:/etc.) caused real, previously-correct known_spawnable
    characters (Tran, Geralt, Torrhen) to disappear from
    entities_observed entirely in scenes where they're discussed only
    in focus:/cutscene purpose: prose, never listed in participants: --
    an even worse outcome than presence:unknown. This test locks in
    the narrower, correct scope so that regression doesn't return."""

    def test_participants_duplication_excluded_but_focus_text_still_counts(self):
        segments = [
            _seg(1, "narration", "@scene_meta_participants: Elyraen"),
            _seg(2, "narration", "@scene_meta_focus: Torrhen teaches the first lesson to Torrhen's own delight."),
            _seg(3, "narration", "scene meta:"),
            _seg(4, "narration", "participants: Elyraen"),
            _seg(5, "narration", "focus: Torrhen teaches the first lesson to Torrhen's own delight."),
            _seg(6, "narration", "The ice cave was silent, save for the wind."),
        ]
        characters = pass2_enhanced.extract_characters(segments)
        # Torrhen is not a participant here, and never appears in prose --
        # but "focus:" text is not excluded, so its 4 raw+header occurrences
        # (2 in @scene_meta_focus, 2 in the raw focus: line) still
        # legitimately reach the frequency threshold, exactly as this
        # pipeline already behaved before this patch.
        self.assertIn("Torrhen", characters)
        self.assertEqual(characters["Torrhen"].mentions, 4)

    def test_only_participants_representations_are_excluded(self):
        """Direct confirmation of the narrowed helper's exact scope."""
        segments = [
            _seg(1, "narration", "@scene_meta_participants: Elyraen"),
            _seg(2, "narration", "@scene_meta_focus: The garden bloomed."),
            _seg(3, "narration", "scene meta:"),
            _seg(4, "narration", "participants: Elyraen"),
            _seg(5, "narration", "focus: The garden bloomed."),
        ]
        excluded = pass2_enhanced._metadata_segment_indices(segments)
        self.assertEqual(excluded, {0, 3})


class TestNonParticipantStillDiscoveredByFrequency(unittest.TestCase):
    """Requirement 3: the existing frequency path must remain fully
    additive -- a real character never listed in participants: must
    still be discoverable from prose alone."""

    def test_unlisted_character_with_three_prose_mentions_is_extracted(self):
        segments = [
            _seg(1, "narration", "@scene_meta_participants: Mika"),
            _seg(2, "narration", "participants: Mika"),
            _seg(3, "narration", "Dren approached quietly, watching the gate."),
            _seg(4, "narration", "Dren said nothing at first, only listened."),
            _seg(5, "narration", "Dren finally spoke, low and even."),
        ]
        characters = pass2_enhanced.extract_characters(segments)
        self.assertIn("Dren", characters)
        self.assertEqual(characters["Dren"].mentions, 3)


class TestParticipantSeedingDoesNotImplyClassification(unittest.TestCase):
    """Requirement 5: authored participant presence, prose mention
    count, known, spawnable, and presence/physicality inference must
    stay independently derived -- seeding a candidate must not
    pre-decide any of the others."""

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp_dir.name)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_seeded_unknown_participant_stays_unknown_not_spawnable(self):
        """An entirely made-up name, seeded only via participants:,
        must classify as known:false, spawnable:false through the
        existing entity filter -- seeding is not an identity or
        capability claim."""
        source_text = (
            "# Chapter 999: Seeding Test\n"
            "participants: Zzyzarax\n"
            "The corridor stretched onward, unremarkable and dim.\n"
        )
        ch_file = self.tmp_path / "999_seed.txt"
        ch_file.write_text(source_text, encoding="utf-8")
        pass1_out = self.tmp_path / "out_pass1_999_seed.txt"
        pass1_explicit.process_file(ch_file, pass1_out)
        segments = pass2_enhanced.load_segments(str(pass1_out))
        characters = pass2_enhanced.extract_characters(segments)
        self.assertIn("Zzyzarax", characters)
        filtered = pass2_entity_filter.filter_entities(characters)
        self.assertIn("Zzyzarax", filtered)
        self.assertFalse(filtered["Zzyzarax"].known)
        self.assertFalse(filtered["Zzyzarax"].spawnable)


if __name__ == "__main__":
    unittest.main()
