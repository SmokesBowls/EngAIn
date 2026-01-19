"""
Trixel Composer - EngAIn Mesh Authoring Tools
Location: tools/trixel/

Trixel's role: Semantic authority, visual validation, annotation
NOT authoritative enforcement (that's mesh_intake in core/)
"""

# Import what actually exists in trixel_composer.py
from .trixel_composer import (
    CreativePhase,
    CreativeAction,
    AutonomousCreativeMemory,
    OptimizedTrixelCanvas,
    RealTimeCreativeFeedback
)

# Try to import terminal_trixel components
try:
    from .terminal_trixel import TerminalTrixel
    TERMINAL_AVAILABLE = True
except (ImportError, AttributeError):
    TERMINAL_AVAILABLE = False
    print("Warning: terminal_trixel components not available")

# Try to import learning validator
try:
    from .learning_validator_agent import LearningValidator
    VALIDATOR_AVAILABLE = True
except (ImportError, AttributeError):
    VALIDATOR_AVAILABLE = False
    print("Warning: learning_validator_agent not available")

# Export what's actually available
__all__ = [
    'CreativePhase',
    'CreativeAction', 
    'AutonomousCreativeMemory',
    'OptimizedTrixelCanvas',
    'RealTimeCreativeFeedback'
]

if TERMINAL_AVAILABLE:
    __all__.append('TerminalTrixel')
    
if VALIDATOR_AVAILABLE:
    __all__.append('LearningValidator')
