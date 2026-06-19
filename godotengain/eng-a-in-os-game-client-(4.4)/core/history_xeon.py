"""
history_xeon.py - Canonical Timeline & Causality Ledger

Records what DID happen and WHY.

Distinguishes:
- Canon history (what actually happened)
- Test runs (experimental, non-canonical)
- Dream runs (sandbox, symbolic)

This is NOT just replay logs (mechanical).
This is canonical history (meaningful) with causality.

Answers: "Why did this specific outcome occur?"
Not just: "What happened?"
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime

@dataclass
class HistoricalEvent:
    """
    A canonical event that actually happened.
    
    Records:
    - What happened (event)
    - Why it happened (cause)
    - State before/after (snapshots)
    - Context (scene, mode, metadata)
    """
    event_id: str
    scene_id: str
    event_data: Dict                  # The actual event
    snapshot_before: Dict             # State before event
    snapshot_after: Dict              # State after event
    cause: str                        # WHY this happened
    timestamp: datetime = field(default_factory=datetime.now)
    mode: str = "CANON"               # CANON, TEST, DREAM
    metadata: Dict = field(default_factory=dict)

class HistoryXeon:
    """
    Canonical timeline storage.
    
    Stores historical events with causality.
    Separates canon from test runs from dreams.
    """
    
    def __init__(self):
        self.events: List[HistoricalEvent] = []
        self._next_id = 0
    
    def commit_event(self,
                    scene_id: str,
                    event_data: Dict,
                    snapshot_before: Dict,
                    snapshot_after: Dict,
                    cause: str,
                    mode: str = "CANON",
                    **metadata) -> HistoricalEvent:
        """
        Commit an event to canonical history.
        
        Args:
            scene_id: Which scene this happened in
            event_data: The event that occurred
            snapshot_before: World state before
            snapshot_after: World state after
            cause: WHY this happened (causality)
            mode: CANON, TEST, or DREAM
        
        Returns: The historical record
        """
        event = HistoricalEvent(
            event_id=f"history_{self._next_id}",
            scene_id=scene_id,
            event_data=event_data,
            snapshot_before=snapshot_before,
            snapshot_after=snapshot_after,
            cause=cause,
            mode=mode,
            metadata=metadata
        )
        
        self.events.append(event)
        self._next_id += 1
        
        return event
    
    def get_history(self, 
                   scene_id: Optional[str] = None,
                   mode: Optional[str] = None) -> List[HistoricalEvent]:
        """
        Get historical events.
        
        Filters:
        - scene_id: Events from specific scene
        - mode: CANON, TEST, or DREAM
        """
        results = self.events
        
        if scene_id:
            results = [e for e in results if e.scene_id == scene_id]
        
        if mode:
            results = [e for e in results if e.mode == mode]
        
        return results
    
    def get_canonical_history(self, scene_id: Optional[str] = None) -> List[HistoricalEvent]:
        """Get only canonical events (exclude tests/dreams)"""
        return self.get_history(scene_id=scene_id, mode="CANON")
    
    def get_causality_chain(self, event_id: str) -> List[HistoricalEvent]:
        """
        Get the chain of causality leading to an event.
        
        (Simple version: just events in same scene before this one)
        """
        event = next((e for e in self.events if e.event_id == event_id), None)
        if not event:
            return []
        
        # Get all events in same scene before this one
        event_index = self.events.index(event)
        return [e for e in self.events[:event_index] 
                if e.scene_id == event.scene_id and e.mode == event.mode]
    
    def query_by_cause(self, cause_contains: str) -> List[HistoricalEvent]:
        """Search for events by causality explanation"""
        return [e for e in self.events 
                if cause_contains.lower() in e.cause.lower()]
    
    def get_timeline_summary(self, scene_id: str) -> Dict:
        """
        Get summary of what happened in a scene.
        
        Returns: event count by mode, key causes
        """
        scene_events = self.get_history(scene_id=scene_id)
        
        return {
            "total_events": len(scene_events),
            "canon_events": len([e for e in scene_events if e.mode == "CANON"]),
            "test_events": len([e for e in scene_events if e.mode == "TEST"]),
            "dream_events": len([e for e in scene_events if e.mode == "DREAM"]),
            "causes": list(set(e.cause for e in scene_events))
        }
    
    def clear(self, mode: Optional[str] = None):
        """
        Clear history.
        
        If mode specified, only clear that mode.
        Otherwise clear everything.
        """
        if mode:
            self.events = [e for e in self.events if e.mode != mode]
        else:
            self.events = []
            self._next_id = 0

# Global history
_global_history = HistoryXeon()

def commit_event(scene_id: str, event_data: Dict, 
                snapshot_before: Dict, snapshot_after: Dict,
                cause: str, mode: str = "CANON", **metadata) -> HistoricalEvent:
    """Commit event to global history"""
    return _global_history.commit_event(
        scene_id, event_data, snapshot_before, snapshot_after, 
        cause, mode, **metadata
    )

def get_history(scene_id: Optional[str] = None, 
               mode: Optional[str] = None) -> List[HistoricalEvent]:
    """Get history globally"""
    return _global_history.get_history(scene_id, mode)

def get_canonical_history(scene_id: Optional[str] = None) -> List[HistoricalEvent]:
    """Get canonical history globally"""
    return _global_history.get_canonical_history(scene_id)

def query_by_cause(cause_contains: str) -> List[HistoricalEvent]:
    """Query by causality globally"""
    return _global_history.query_by_cause(cause_contains)

def get_timeline_summary(scene_id: str) -> Dict:
    """Get timeline summary globally"""
    return _global_history.get_timeline_summary(scene_id)
