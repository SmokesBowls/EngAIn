from dataclasses import dataclass, field
from typing import Any, Dict, List

from schemas.temporal_artifact import ProseTemporalArtifact
from reasoning.temporal_validator import TemporalValidationResult


@dataclass
class TemporalGateVerdict:
    verdict: str
    reason: str
    artifact_id: str
    issues: List[Dict[str, Any]] = field(default_factory=list)
    next_destination: str = "none"


class TemporalGate:
    """
    Converts validator output into EngAIn law status.

    ACCEPTED:
        Internally consistent and safe to become accepted temporal truth.

    REJECTED:
        Internally contradictory.

    SUSPENDED:
        Not internally broken, but cannot yet be accepted because it conflicts
        with existing accepted truth, spatial law, missing transition events,
        or paradox-sensitive context.
    """

    def decide(
        self,
        artifact: ProseTemporalArtifact,
        validation_result: TemporalValidationResult,
        conflicts_with_accepted_truth: bool = False,
        conflict_reason: str = "",
    ) -> TemporalGateVerdict:
        if not validation_result.is_consistent:
            return TemporalGateVerdict(
                verdict="REJECTED",
                reason="The proposed temporal artifact is internally inconsistent.",
                artifact_id=artifact.artifact_id,
                issues=[issue.__dict__ for issue in validation_result.issues],
                next_destination="rejected_temporal_claims",
            )

        if conflicts_with_accepted_truth:
            return TemporalGateVerdict(
                verdict="SUSPENDED",
                reason=conflict_reason or "The proposed temporal artifact conflicts with accepted truth.",
                artifact_id=artifact.artifact_id,
                issues=[issue.__dict__ for issue in validation_result.issues],
                next_destination="paradoxroom.PotentialTemporalStateSet",
            )

        return TemporalGateVerdict(
            verdict="ACCEPTED",
            reason="The proposed temporal artifact is internally consistent and does not conflict with accepted truth.",
            artifact_id=artifact.artifact_id,
            issues=[],
            next_destination="AcceptedTemporalTruthPacket",
        )