from schemas.temporal_artifact import (
    ProseTemporalArtifact,
    TemporalEvent,
    TemporalExpression,
    TemporalLink,
)


class NaiveTemporalExtractor:
    """
    Fake extractor for Game Proof #007.

    This does not claim to be real NLP.
    This exists so the pipeline can be tested before ISO-TimeML parsing,
    dependency selection, or LLM-assisted extraction.
    """

    def extract_gate_example(self) -> ProseTemporalArtifact:
        source_text = (
            "The guard closed the heavy gate. "
            "Later, the player approached. "
            "He was standing on the other side."
        )

        artifact = ProseTemporalArtifact(
            artifact_id="proof_007_gate_example",
            source_text=source_text,
        )

        artifact.events.extend(
            [
                TemporalEvent(
                    event_id="e1",
                    text="guard closed gate",
                    event_type="OCCURRENCE",
                    source_sentence_index=0,
                    discourse_order=1,
                ),
                TemporalEvent(
                    event_id="e2",
                    text="player approached",
                    event_type="OCCURRENCE",
                    source_sentence_index=1,
                    discourse_order=2,
                ),
                TemporalEvent(
                    event_id="e3",
                    text="player standing on other side",
                    event_type="STATE",
                    source_sentence_index=2,
                    discourse_order=3,
                ),
            ]
        )

        artifact.timexes.append(
            TemporalExpression(
                timex_id="t1",
                text="Later",
                timex_type="SIGNAL",
                source_sentence_index=1,
            )
        )

        artifact.tlinks.extend(
            [
                TemporalLink(
                    link_id="l1",
                    source_id="e1",
                    target_id="e2",
                    rel_type="BEFORE",
                ),
                TemporalLink(
                    link_id="l2",
                    source_id="e2",
                    target_id="e3",
                    rel_type="BEFORE",
                ),
            ]
        )

        artifact.syuzhet_order = ["e1", "e2", "e3"]
        artifact.fabula_order_hint = ["e1", "e2", "e3"]
        artifact.notes.append("Naive proof artifact. ISO-TimeML-shaped, not full ISO-TimeML XML.")

        return artifact