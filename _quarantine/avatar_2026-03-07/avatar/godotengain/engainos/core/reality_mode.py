"""
reality_mode.py - Reality Mode Context

Prevents category errors between different reality states.

The same command behaves DIFFERENTLY depending on mode:
- DRAFT: Soft validation, editable, no permanence
- IMBUED: Has ZW/AP context, testable
- FINALIZED: Hard enforcement, canonical, immutable
- DREAM: Symbolic, non-causal, sandbox
- REPLAY: Read-only, deterministic reconstruction

This prevents:
- Editing canon during replay
- Treating dream mutations as history
- AP violations in draft mode leaking to canon
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional
from contextlib import contextmanager

class RealityMode(Enum):
    """
    Reality states the system can be in.
    
    Each mode has different rules and behaviors.
    """
    DRAFT = "DRAFT"           # Editable, no enforcement
    IMBUED = "IMBUED"         # Has context, testable
    FINALIZED = "FINALIZED"   # Locked, canonical
    DREAM = "DREAM"           # Symbolic, sandbox
    REPLAY = "REPLAY"         # Read-only reconstruction
    TEST = "TEST"             # Experimental, non-canonical

@dataclass
class RealityContext:
    """
    Current reality state context.
    
    Tracks what mode we're in and enforces rules accordingly.
    """
    mode: RealityMode = RealityMode.DRAFT
    scene_id: Optional[str] = None
    metadata: dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def is_editable(self) -> bool:
        """Can world state be modified?"""
        return self.mode not in [RealityMode.FINALIZED, RealityMode.REPLAY]
    
    def is_canonical(self) -> bool:
        """Is this canonical history?"""
        return self.mode == RealityMode.FINALIZED
    
    def is_sandbox(self) -> bool:
        """Is this a sandbox (dream/test)?"""
        return self.mode in [RealityMode.DREAM, RealityMode.TEST]
    
    def requires_ap_enforcement(self) -> bool:
        """Should AP rules be strictly enforced?"""
        return self.mode in [RealityMode.IMBUED, RealityMode.FINALIZED]
    
    def allows_mutation(self) -> bool:
        """Can state be mutated?"""
        return self.mode != RealityMode.REPLAY
    
    def get_history_mode(self) -> str:
        """What mode should history record events under?"""
        if self.mode == RealityMode.FINALIZED:
            return "CANON"
        elif self.mode == RealityMode.DREAM:
            return "DREAM"
        elif self.mode == RealityMode.TEST:
            return "TEST"
        else:
            return "DRAFT"

class RealityManager:
    """
    Manages current reality mode context.
    
    Provides context manager for temporary mode changes.
    """
    
    def __init__(self):
        self.current: RealityContext = RealityContext()
        self._stack = []
    
    def set_mode(self, mode: RealityMode, scene_id: Optional[str] = None):
        """Set current reality mode"""
        self.current = RealityContext(mode=mode, scene_id=scene_id)
    
    def get_mode(self) -> RealityMode:
        """Get current reality mode"""
        return self.current.mode
    
    @contextmanager
    def reality(self, mode: RealityMode, scene_id: Optional[str] = None):
        """
        Context manager for temporary mode changes.
        
        Example:
            with reality_manager.reality(RealityMode.DREAM):
                # Do dream state stuff
                pass
            # Automatically restores previous mode
        """
        # Save current context
        self._stack.append(self.current)
        
        # Set new context
        self.current = RealityContext(mode=mode, scene_id=scene_id)
        
        try:
            yield self.current
        finally:
            # Restore previous context
            self.current = self._stack.pop()

# Global reality manager
_global_reality = RealityManager()

def set_mode(mode: RealityMode, scene_id: Optional[str] = None):
    """Set global reality mode"""
    _global_reality.set_mode(mode, scene_id)

def get_mode() -> RealityMode:
    """Get global reality mode"""
    return _global_reality.get_mode()

def get_context() -> RealityContext:
    """Get global reality context"""
    return _global_reality.current

@contextmanager
def reality(mode: RealityMode, scene_id: Optional[str] = None):
    """Global reality context manager"""
    with _global_reality.reality(mode, scene_id) as ctx:
        yield ctx
