#!/usr/bin/env python3
import sys
from pathlib import Path

# Add repo root to PYTHONPATH to ensure correct imports
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from tier1.paradox_machine.schemas.temporal_artifact import (
    ProseTemporalArtifact,
    TemporalEvent,
    TemporalLink,
)
from tier1.paradox_machine.reasoning.temporal_validator import TemporalValidator

# 1. Hardcode the two claims
claim_1 = {"subject": "Bret", "predicate": "dies", "scene": "book012.ch12", "order": 12}
claim_2 = {"subject": "Bret", "predicate": "appears", "scene": "book017.ch17", "order": 17}

print(f"Claim 1: {claim_1}")
print(f"Claim 2: {claim_2}")

# 2. Build ProseTemporalArtifact
artifact = ProseTemporalArtifact(
    artifact_id="scratch_claim_test",
    source_text="Bret dies in chapter 12. Bret appears in chapter 17.",
)

# Add events
artifact.events.append(
    TemporalEvent(
        event_id="e1",
        text=f"{claim_1['subject']} {claim_1['predicate']}",
        metadata=claim_1,
    )
)

artifact.events.append(
    TemporalEvent(
        event_id="e2",
        text=f"{claim_2['subject']} {claim_2['predicate']}",
        metadata=claim_2,
    )
)

# Infer BEFORE/AFTER link based on chronology 'order'
if claim_1["order"] < claim_2["order"]:
    artifact.tlinks.append(
        TemporalLink(
            link_id="link_1_before_2",
            source_id="e1",
            target_id="e2",
            rel_type="BEFORE",
        )
    )
else:
    artifact.tlinks.append(
        TemporalLink(
            link_id="link_2_before_1",
            source_id="e2",
            target_id="e1",
            rel_type="BEFORE",
        )
    )

# 3. Validate temporal structure using existing TemporalValidator
validator = TemporalValidator()
validation_result = validator.validate(artifact)

print(f"\nValidator is_consistent: {validation_result.is_consistent}")
print(f"Normalized relations: {validation_result.normalized_relations}")

# 4. Implement terminal event logic
TERMINAL_PREDICATES = {"dies", "perishes", "destroyed"}

# Build adjacency list of BEFORE relations for traversal
before_graph = validator._build_before_graph(validation_result.normalized_relations)

def has_path(start: str, end: str, visited=None) -> bool:
    if visited is None:
        visited = set()
    if start == end:
        return True
    visited.add(start)
    for neighbor in before_graph.get(start, []):
        if neighbor not in visited:
            if has_path(neighbor, end, visited):
                return True
    return False

# Detect if a terminal event occurs BEFORE another event for the same subject
contradiction_found = False
reason = ""

for event_a in artifact.events:
    sub_a = event_a.metadata.get("subject")
    pred_a = event_a.metadata.get("predicate")
    
    if pred_a in TERMINAL_PREDICATES:
        # A terminal event occurred! Check if there is any event_b that happens AFTER event_a
        for event_b in artifact.events:
            if event_a.event_id == event_b.event_id:
                continue
                
            sub_b = event_b.metadata.get("subject")
            if sub_a == sub_b:
                # Same subject! Does event_b happen after event_a?
                if has_path(event_a.event_id, event_b.event_id):
                    contradiction_found = True
                    reason = (
                        f"CONTRADICTION DETECTED: Subject '{sub_a}' has terminal event "
                        f"'{pred_a}' at scene {event_a.metadata.get('scene')} (order {event_a.metadata.get('order')}), "
                        f"but subsequently '{event_b.metadata.get('predicate')}' at scene "
                        f"{event_b.metadata.get('scene')} (order {event_b.metadata.get('order')})."
                    )
                    break
    if contradiction_found:
        break

if contradiction_found:
    print(f"\nVerdict: REJECTED\nReason: {reason}")
else:
    print("\nVerdict: ACCEPTED\nReason: No contradictions detected.")
