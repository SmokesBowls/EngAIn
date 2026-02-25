"""
zw_core.py - ZW Semantic Ontology

The vocabulary of the world.
Concepts, relations, meaning - NOT logic or state.

"warden", "tower", "guards_at" are ZW concepts.
Combat damage calculations are NOT ZW.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional

@dataclass
class ZwConcept:
    """
    A semantic concept in the world.
    
    Examples:
    - "warden" (entity type)
    - "tower" (location type)
    - "guards_at" (relation type)
    """
    id: str                           # "warden", "tower", "guards_at"
    labels: List[str] = field(default_factory=list)  # ["guardian", "keeper"]
    tags: Set[str] = field(default_factory=set)      # {"npc", "faction_red"}
    relations: Dict[str, List[str]] = field(default_factory=dict)
    # {"guards_at": ["tower"], "loyal_to": ["faction_red"]}
    
    metadata: Dict = field(default_factory=dict)

class ZwRegistry:
    """
    In-memory concept registry.
    
    Lookup, link, and query ZW concepts.
    """
    
    def __init__(self):
        self.concepts: Dict[str, ZwConcept] = {}
    
    def register_concept(self, concept_id: str, 
                        labels: List[str] = None,
                        tags: Set[str] = None) -> ZwConcept:
        """Register a new concept"""
        if concept_id in self.concepts:
            return self.concepts[concept_id]
        
        concept = ZwConcept(
            id=concept_id,
            labels=labels or [],
            tags=tags or set()
        )
        self.concepts[concept_id] = concept
        return concept
    
    def lookup_zw(self, concept_id: str) -> Optional[ZwConcept]:
        """Lookup a concept by ID"""
        return self.concepts.get(concept_id)
    
    def link_zw(self, subject: str, relation: str, object: str):
        """
        Create a semantic link between concepts.
        
        Example: link_zw("warden", "guards_at", "tower")
        """
        subject_concept = self.lookup_zw(subject)
        if not subject_concept:
            raise ValueError(f"Unknown concept: {subject}")
        
        if relation not in subject_concept.relations:
            subject_concept.relations[relation] = []
        
        if object not in subject_concept.relations[relation]:
            subject_concept.relations[relation].append(object)
    
    def query_relations(self, subject: str, relation: str) -> List[str]:
        """Query: what does subject relate to via relation?"""
        concept = self.lookup_zw(subject)
        if not concept:
            return []
        return concept.relations.get(relation, [])

# Global registry (for now - can be per-world later)
_global_registry = ZwRegistry()

def register_concept(concept_id: str, **kwargs) -> ZwConcept:
    return _global_registry.register_concept(concept_id, **kwargs)

def lookup_zw(concept_id: str) -> Optional[ZwConcept]:
    return _global_registry.lookup_zw(concept_id)

def link_zw(subject: str, relation: str, object: str):
    _global_registry.link_zw(subject, relation, object)

def query_relations(subject: str, relation: str) -> List[str]:
    return _global_registry.query_relations(subject, relation)
