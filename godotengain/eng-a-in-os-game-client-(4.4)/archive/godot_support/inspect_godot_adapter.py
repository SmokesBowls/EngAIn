#!/usr/bin/env python3
"""
Inspect what godot_adapter.py actually exports
"""

import sys
from pathlib import Path

# Add core to path
core = Path("core")
sys.path.insert(0, str(core))

print("=" * 70)
print("INSPECTING godot_adapter.py")
print("=" * 70)
print()

# Read the file
godot_adapter_file = core / "godot_adapter.py"

if not godot_adapter_file.exists():
    print(f"❌ File not found: {godot_adapter_file}")
    sys.exit(1)

print(f"File: {godot_adapter_file}")
print()

# Find all classes
print("Classes defined:")
with open(godot_adapter_file, 'r') as f:
    for line_num, line in enumerate(f, 1):
        if line.strip().startswith('class '):
            print(f"  Line {line_num}: {line.strip()}")

print()

# Find all functions
print("Functions defined:")
with open(godot_adapter_file, 'r') as f:
    for line_num, line in enumerate(f, 1):
        if line.strip().startswith('def ') and not line.strip().startswith('def _'):
            print(f"  Line {line_num}: {line.strip()}")

print()

# Try to import and see what's available
print("Attempting import...")
try:
    import godot_adapter
    print("✓ Module imports successfully")
    print()
    
    print("Available symbols:")
    for name in dir(godot_adapter):
        if not name.startswith('_'):
            obj = getattr(godot_adapter, name)
            obj_type = type(obj).__name__
            print(f"  {name}: {obj_type}")
    
except ImportError as e:
    print(f"✗ Import failed: {e}")
    print()
    print("This means godot_adapter.py has syntax errors or missing dependencies")

print()
print("=" * 70)
print("RECOMMENDATION")
print("=" * 70)
print()

print("Based on the file structure, update launch_engine.py to import")
print("what actually exists, not what we assume should exist.")
print()
print("For example, if the file defines:")
print("  - A function: main()")
print("  - A class: Adapter (not GodotAdapter)")
print()
print("Then change launch_engine.py to:")
print("  from godot_adapter import main")
print("  # or")
print("  from godot_adapter import Adapter")
