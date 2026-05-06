#!/bin/bash
# EngAIn Narrative Pipeline GUI Launcher

echo "================================================"
echo "  EngAIn Narrative Pipeline GUI"
echo "  AI Logic Built for AI, Not Humans"
echo "================================================"
echo ""

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo "❌ ERROR: python3 not found"
    echo "Please install Python 3 to run the GUI"
    exit 1
fi

# Check for tkinter
python3 -c "import tkinter" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ ERROR: tkinter not found"
    echo ""
    echo "Install tkinter:"
    echo "  Ubuntu/Debian: sudo apt-get install python3-tk"
    echo "  Fedora: sudo dnf install python3-tkinter"
    echo "  macOS: Should be included with Python"
    exit 1
fi

echo "✓ Python 3 found"
echo "✓ tkinter available"
echo ""
echo "Launching GUI..."
echo ""

# Launch the GUI
python3 narrative_pipeline_gui.py

echo ""
echo "GUI closed."
