from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from schemas.temporal_artifact import ProseTemporalArtifact
from reasoning.allen_relations import normalize_relation, is_supported_relation, INVERSE_RELATION


@dataclass
class TemporalValidationIssue:
    severity: str
    code: str
    message: str
    link_ids: List[str] = field(default_factory=list)


@dataclass
class TemporalValidationResult:
    is_consistent: bool
    issues: List[TemporalValidationIssue] = field(default_factory=list)
    normalized_relations: Dict[Tuple[str, str], str] = field(default_factory=dict)


class TemporalValidator:
    """
    MVP validator for Game Proof #007.

    This is intentionally small:
    - validates relation names
    - detects direct pair contradictions
    - detects basic BEFORE cycles such as A BEFORE B and B BEFORE A
    - does not yet implement full Allen path consistency
    """

    def validate(self, artifact: ProseTemporalArtifact) -> TemporalValidationResult:
        issues: List[TemporalValidationIssue] = []
        relations: Dict[Tuple[str, str], str] = {}

        for link in artifact.tlinks:
            rel = normalize_relation(link.rel_type)

            if not is_supported_relation(rel):
                issues.append(
                    TemporalValidationIssue(
                        severity="ERROR",
                        code="UNSUPPORTED_RELATION",
                        message=f"Unsupported temporal relation: {link.rel_type}",
                        link_ids=[link.link_id],
                    )
                )
                continue

            pair = (link.source_id, link.target_id)
            inverse_pair = (link.target_id, link.source_id)

            if pair in relations and relations[pair] != rel:
                issues.append(
                    TemporalValidationIssue(
                        severity="ERROR",
                        code="DIRECT_RELATION_CONFLICT",
                        message=(
                            f"Conflicting relations for {pair}: "
                            f"{relations[pair]} versus {rel}"
                        ),
                        link_ids=[link.link_id],
                    )
                )

            if inverse_pair in relations:
                expected_inverse = INVERSE_RELATION.get(rel)
                existing_inverse = relations[inverse_pair]

                if expected_inverse and existing_inverse != expected_inverse:
                    issues.append(
                        TemporalValidationIssue(
                            severity="ERROR",
                            code="INVERSE_RELATION_CONFLICT",
                            message=(
                                f"Relation {rel} from {pair} conflicts with "
                                f"{existing_inverse} from {inverse_pair}."
                            ),
                            link_ids=[link.link_id],
                        )
                    )

            relations[pair] = rel

        before_graph = self._build_before_graph(relations)
        cycle = self._find_cycle(before_graph)

        if cycle:
            issues.append(
                TemporalValidationIssue(
                    severity="ERROR",
                    code="BEFORE_CYCLE",
                    message=f"Temporal cycle detected: {' -> '.join(cycle)}",
                    link_ids=[],
                )
            )

        return TemporalValidationResult(
            is_consistent=not any(issue.severity == "ERROR" for issue in issues),
            issues=issues,
            normalized_relations=relations,
        )

    def _build_before_graph(self, relations: Dict[Tuple[str, str], str]) -> Dict[str, List[str]]:
        graph: Dict[str, List[str]] = {}

        for (source_id, target_id), rel in relations.items():
            if rel == "BEFORE":
                graph.setdefault(source_id, []).append(target_id)
            elif rel == "AFTER":
                graph.setdefault(target_id, []).append(source_id)

        return graph

    def _find_cycle(self, graph: Dict[str, List[str]]) -> List[str]:
        visited = set()
        stack = set()
        path: List[str] = []

        def visit(node: str) -> bool:
            visited.add(node)
            stack.add(node)
            path.append(node)

            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if visit(neighbor):
                        return True
                elif neighbor in stack:
                    path.append(neighbor)
                    return True

            stack.remove(node)
            path.pop()
            return False

        for node in graph:
            if node not in visited:
                if visit(node):
                    return path[:]

        return []
