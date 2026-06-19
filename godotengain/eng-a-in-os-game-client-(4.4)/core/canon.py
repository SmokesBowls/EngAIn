"""
canon.py - Scene Lifecycle & Canonization

Scene states: DRAFT → IMBUED → FINALIZED

DRAFT: Editable, no AP enforcement
IMBUED: Has ZW/AP context, testable
FINALIZED: Locked, canonical, immutable

This prevents:
- Editing canon during replay
- Treating dream mutations as history
- Category errors between modes
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, List
from datetime import datetime

@dataclass
class SceneMeta:
    """
    Metadata for a scene's lifecycle state.
    
    Tracks: state, timestamps, AP profile, violations
    """
    scene_id: str
    state: str = "DRAFT"  # DRAFT, IMBUED, FINALIZED
    created_at: datetime = field(default_factory=datetime.now)
    imbued_at: Optional[datetime] = None
    finalized_at: Optional[datetime] = None
    ap_profile: str = "default"  # Which AP rules apply
    violations: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)

class CanonSystem:
    """
    Manages scene lifecycle and canonization.
    
    Enforces state transitions.
    Prevents edits to finalized scenes.
    """
    
    def __init__(self):
        self.scenes: Dict[str, SceneMeta] = {}
    
    def create_scene(self, scene_id: str, ap_profile: str = "default") -> SceneMeta:
        """Create a new scene in DRAFT state"""
        if scene_id in self.scenes:
            raise ValueError(f"Scene {scene_id} already exists")
        
        scene = SceneMeta(
            scene_id=scene_id,
            state="DRAFT",
            ap_profile=ap_profile
        )
        self.scenes[scene_id] = scene
        return scene
    
    def imbue_scene(self, scene_id: str) -> SceneMeta:
        """
        Transition DRAFT → IMBUED
        
        IMBUED scenes have ZW context and AP rules bound.
        """
        scene = self.scenes.get(scene_id)
        if not scene:
            raise ValueError(f"Unknown scene: {scene_id}")
        
        if scene.state != "DRAFT":
            raise ValueError(f"Scene {scene_id} is not in DRAFT state")
        
        scene.state = "IMBUED"
        scene.imbued_at = datetime.now()
        return scene
    
    def finalize_scene(self, scene_id: str, 
                       violations_ok: bool = False) -> SceneMeta:
        """
        Transition IMBUED → FINALIZED
        
        FINALIZED scenes are:
        - Locked (no more edits)
        - Canonical (part of official timeline)
        - Immutable (can only be read or replayed)
        
        Requires: No AP violations (unless violations_ok=True)
        """
        scene = self.scenes.get(scene_id)
        if not scene:
            raise ValueError(f"Unknown scene: {scene_id}")
        
        if scene.state != "IMBUED":
            raise ValueError(f"Scene {scene_id} must be IMBUED before finalization")
        
        # Check for violations
        if scene.violations and not violations_ok:
            raise ValueError(
                f"Scene {scene_id} has violations: {scene.violations}. "
                f"Cannot finalize. Set violations_ok=True to force."
            )
        
        scene.state = "FINALIZED"
        scene.finalized_at = datetime.now()
        return scene
    
    def can_edit(self, scene_id: str) -> bool:
        """Check if scene can be edited"""
        scene = self.scenes.get(scene_id)
        if not scene:
            return True  # New scene, can create
        
        return scene.state != "FINALIZED"
    
    def is_canonical(self, scene_id: str) -> bool:
        """Check if scene is canonical (finalized)"""
        scene = self.scenes.get(scene_id)
        if not scene:
            return False
        
        return scene.state == "FINALIZED"
    
    def add_violation(self, scene_id: str, violation: str):
        """Record an AP violation for this scene"""
        scene = self.scenes.get(scene_id)
        if not scene:
            raise ValueError(f"Unknown scene: {scene_id}")
        
        scene.violations.append(violation)
    
    def clear_violations(self, scene_id: str):
        """Clear all violations for a scene"""
        scene = self.scenes.get(scene_id)
        if not scene:
            raise ValueError(f"Unknown scene: {scene_id}")
        
        scene.violations = []
    
    def get_scene(self, scene_id: str) -> Optional[SceneMeta]:
        """Get scene metadata"""
        return self.scenes.get(scene_id)

# Global canon system
_global_canon = CanonSystem()

def create_scene(scene_id: str, ap_profile: str = "default") -> SceneMeta:
    return _global_canon.create_scene(scene_id, ap_profile)

def imbue_scene(scene_id: str) -> SceneMeta:
    return _global_canon.imbue_scene(scene_id)

def finalize_scene(scene_id: str, violations_ok: bool = False) -> SceneMeta:
    return _global_canon.finalize_scene(scene_id, violations_ok)

def can_edit(scene_id: str) -> bool:
    return _global_canon.can_edit(scene_id)

def is_canonical(scene_id: str) -> bool:
    return _global_canon.is_canonical(scene_id)

def add_violation(scene_id: str, violation: str):
    _global_canon.add_violation(scene_id, violation)

def get_scene(scene_id: str) -> Optional[SceneMeta]:
    return _global_canon.get_scene(scene_id)
