#!/bin/bash
# Fix tools/trixel/__init__.py to match actual classes
# Run from: ~/Downloads/EngAIn/godotengain/engainos/

echo "======================================================================"
echo "FIXING TRIXEL __init__.py IMPORTS"
echo "======================================================================"

INIT_FILE="tools/trixel/__init__.py"
COMPOSER_FILE="tools/trixel/trixel_composer.py"

if [ ! -f "$COMPOSER_FILE" ]; then
    echo "Error: $COMPOSER_FILE not found"
    exit 1
fi

echo ""
echo "Detecting actual classes in trixel_composer.py..."

# Extract class names
CLASSES=$(grep "^class " "$COMPOSER_FILE" | awk '{print $2}' | sed 's/(.*//' | sed 's/://')

echo "Found classes:"
echo "$CLASSES" | sed 's/^/  - /'

echo ""
echo "Creating corrected __init__.py..."

# Backup
if [ -f "$INIT_FILE" ]; then
    cp "$INIT_FILE" "$INIT_FILE.backup"
    echo "  Backup: $INIT_FILE.backup"
fi

# Create new __init__.py with actual classes
cat > "$INIT_FILE" << 'EOF'
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
EOF

echo "✓ Created new __init__.py"

echo ""
echo "Testing import..."

cd tools/trixel
if python3 -c "import sys; sys.path.insert(0, '../..'); from tools.trixel import AutonomousCreativeMemory; print('✓ Import successful')" 2>&1; then
    echo ""
    echo "======================================================================"
    echo "FIX APPLIED SUCCESSFULLY"
    echo "======================================================================"
else
    echo ""
    echo "⚠ Import still has issues - may need dependency installation"
    echo "   Common missing dependencies:"
    echo "   - PyQt5: sudo apt-get install python3-pyqt5"
    echo "   - PIL: pip3 install Pillow"
    echo "   - numpy: pip3 install numpy"
fi

cd ../..

echo ""
echo "You can now import with:"
echo "  from tools.trixel import AutonomousCreativeMemory"
echo "  from tools.trixel import CreativePhase, CreativeAction"
