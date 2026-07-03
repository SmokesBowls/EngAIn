from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class TemporalEvent:
    event_id: str
    text: str
    event_type: str = "OCCURRENCE"
    tense: Optional[str] = None
    aspect: Optional[str] = None
    polarity: str = "POS"
    source_sentence_index: Optional[int] = None
    discourse_order: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TemporalExpression:
    timex_id: str
    text: str
    timex_type: str
    value: Optional[str] = None
    source_sentence_index: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TemporalLink:
    link_id: str
    source_id: str
    target_id: str
    rel_type: str
    confidence: float = 1.0
    source: str = "manual_or_naive_extractor"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProseTemporalArtifact:
    artifact_id: str
    source_text: str
    status: str = "PROPOSED"
    events: List[TemporalEvent] = field(default_factory=list)
    timexes: List[TemporalExpression] = field(default_factory=list)
    tlinks: List[TemporalLink] = field(default_factory=list)
    fabula_order_hint: List[str] = field(default_factory=list)
    syuzhet_order: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "source_text": self.source_text,
            "status": self.status,
            "events": [event.__dict__ for event in self.events],
            "timexes": [timex.__dict__ for timex in self.timexes],
            "tlinks": [link.__dict__ for link in self.tlinks],
            "fabula_order_hint": self.fabula_order_hint,
            "syuzhet_order": self.syuzhet_order,
            "notes": self.notes,
        }
