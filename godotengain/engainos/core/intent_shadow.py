"""
intent_shadow.py - Shadow Memory Layer

Records what ALMOST happened but didn't.
Never mutates world state - only logs pressure.

Examples:
- Rejected commands (failed authority check)
- Vetoed actions (human override)
- Failed pre-conditions (AP violations)
- Abandoned AI plans

This is "negative space memory" - the things that DIDN'T happen
but tell you about the forces acting on the world.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime

@dataclass
class Intent:
    """
    A record of something that was attempted but didn't happen.
    
    Captures: who, what, when, why it failed
    """
    intent_id: str                    # Unique ID
    issuer: str                       # Who tried this
    command: Dict                     # What they tried to do
    reason_rejected: str              # Why it failed
    timestamp: datetime = field(default_factory=datetime.now)
    scene_id: Optional[str] = None   # Where it was attempted
    metadata: Dict = field(default_factory=dict)

class IntentShadow:
    """
    Shadow memory system.
    
    Logs rejected commands, vetoes, failed plans.
    Never touches world state.
    """
    
    def __init__(self):
        self.intents: List[Intent] = []
        self._next_id = 0
    
    def record_intent(self, 
                     issuer: str,
                     command: Dict,
                     reason_rejected: str,
                     scene_id: Optional[str] = None,
                     **metadata) -> Intent:
        """
        Record an intent that didn't happen.
        
        Returns: The created Intent record
        """
        intent = Intent(
            intent_id=f"intent_{self._next_id}",
            issuer=issuer,
            command=command,
            reason_rejected=reason_rejected,
            scene_id=scene_id,
            metadata=metadata
        )
        
        self.intents.append(intent)
        self._next_id += 1
        
        return intent
    
    def query_intents(self, 
                     issuer: Optional[str] = None,
                     scene_id: Optional[str] = None,
                     reason_contains: Optional[str] = None) -> List[Intent]:
        """
        Query shadow memory for intents.
        
        Filters:
        - issuer: who attempted it
        - scene_id: where it was attempted
        - reason_contains: text search in rejection reason
        """
        results = self.intents
        
        if issuer:
            results = [i for i in results if i.issuer == issuer]
        
        if scene_id:
            results = [i for i in results if i.scene_id == scene_id]
        
        if reason_contains:
            results = [i for i in results 
                      if reason_contains.lower() in i.reason_rejected.lower()]
        
        return results
    
    def get_failure_count(self, issuer: Optional[str] = None) -> int:
        """Count how many intents failed (optionally by issuer)"""
        if issuer:
            return len([i for i in self.intents if i.issuer == issuer])
        return len(self.intents)
    
    def get_recent_intents(self, n: int = 10) -> List[Intent]:
        """Get the N most recent intents"""
        return self.intents[-n:]
    
    def clear(self):
        """Clear all shadow memory (for testing or memory pressure)"""
        self.intents = []
        self._next_id = 0

# Global shadow memory
_global_shadow = IntentShadow()

def record_intent(issuer: str, command: Dict, reason_rejected: str, 
                 scene_id: Optional[str] = None, **metadata) -> Intent:
    """Record a rejected intent globally"""
    return _global_shadow.record_intent(issuer, command, reason_rejected, 
                                       scene_id, **metadata)

def query_intents(**filters) -> List[Intent]:
    """Query shadow memory globally"""
    return _global_shadow.query_intents(**filters)

def get_failure_count(issuer: Optional[str] = None) -> int:
    """Get failure count globally"""
    return _global_shadow.get_failure_count(issuer)

def get_recent_intents(n: int = 10) -> List[Intent]:
    """Get recent intents globally"""
    return _global_shadow.get_recent_intents(n)
