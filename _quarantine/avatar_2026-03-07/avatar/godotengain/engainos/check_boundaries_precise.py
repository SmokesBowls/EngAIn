#!/usr/bin/env python3
"""
Precise boundary violation checker

Distinguishes:
- "from godot_adapter import X" ✅ (core module)
- "import godot" ❌ (godot directory)
- "from godot import X" ❌ (godot directory)
"""

import re
from pathlib import Path
import sys

def check_file_for_godot_violations(filepath: Path) -> list:
    """Check a single file for godot directory imports"""
    violations = []
    
    try:
        with open(filepath, 'r') as f:
            for line_num, line in enumerate(f, 1):
                stripped = line.strip()
                
                # Skip comments
                if stripped.startswith('#'):
                    continue
                
                # Check for violations
                # Pattern 1: "import godot" or "import godot.something"
                if re.match(r'^\s*import\s+godot\b', line):
                    violations.append({
                        'file': filepath,
                        'line': line_num,
                        'content': line.rstrip(),
                        'type': 'direct_import'
                    })
                
                # Pattern 2: "from godot import" or "from godot.something import"
                if re.match(r'^\s*from\s+godot\b', line):
                    violations.append({
                        'file': filepath,
                        'line': line_num,
                        'content': line.rstrip(),
                        'type': 'from_import'
                    })
                
                # NOT violations (core modules with "godot" in name):
                # - from godot_adapter import X
                # - import godot_adapter
                # These are fine - godot_adapter is a core module
    
    except Exception as e:
        print(f"Error reading {filepath}: {e}", file=sys.stderr)
    
    return violations

def check_directory(directory: Path, forbidden_dir: str) -> dict:
    """Check all Python files in directory for forbidden imports"""
    all_violations = {}
    
    for py_file in directory.rglob("*.py"):
        if forbidden_dir == "godot":
            violations = check_file_for_godot_violations(py_file)
        elif forbidden_dir == "tools":
            violations = check_file_for_tools_violations(py_file)
        else:
            violations = []
        
        if violations:
            all_violations[py_file] = violations
    
    return all_violations

def check_file_for_tools_violations(filepath: Path) -> list:
    """Check a single file for tools directory imports"""
    violations = []
    
    try:
        with open(filepath, 'r') as f:
            for line_num, line in enumerate(f, 1):
                stripped = line.strip()
                
                if stripped.startswith('#'):
                    continue
                
                # Pattern: "import tools" or "from tools import"
                if re.match(r'^\s*import\s+tools\b', line):
                    violations.append({
                        'file': filepath,
                        'line': line_num,
                        'content': line.rstrip(),
                        'type': 'direct_import'
                    })
                
                if re.match(r'^\s*from\s+tools\b', line):
                    violations.append({
                        'file': filepath,
                        'line': line_num,
                        'content': line.rstrip(),
                        'type': 'from_import'
                    })
    
    except Exception as e:
        print(f"Error reading {filepath}: {e}", file=sys.stderr)
    
    return violations

if __name__ == '__main__':
    print("=" * 70)
    print("PRECISE BOUNDARY VIOLATION CHECKER")
    print("=" * 70)
    print()
    
    # Determine root
    script_dir = Path(__file__).parent
    
    # Assume we're in engainos/
    if (script_dir / "core").exists():
        root = script_dir
    else:
        root = script_dir.parent
    
    core = root / "core"
    tools = root / "tools"
    
    print(f"Checking: {core}")
    print()
    
    # Check core/ for godot imports
    print("[1/2] Checking core/ for 'godot' directory imports...")
    godot_violations = check_directory(core, "godot")
    
    if godot_violations:
        print(f"  ✗ Found {len(godot_violations)} files with violations")
        print()
        for filepath, violations in godot_violations.items():
            rel_path = filepath.relative_to(core)
            print(f"  File: core/{rel_path}")
            for v in violations:
                print(f"    Line {v['line']}: {v['content']}")
            print()
    else:
        print("  ✓ No godot directory imports found")
    
    print()
    
    # Check core/ for tools imports
    print("[2/2] Checking core/ for 'tools' directory imports...")
    tools_violations = check_directory(core, "tools")
    
    if tools_violations:
        print(f"  ✗ Found {len(tools_violations)} files with violations")
        print()
        for filepath, violations in tools_violations.items():
            rel_path = filepath.relative_to(core)
            print(f"  File: core/{rel_path}")
            for v in violations:
                print(f"    Line {v['line']}: {v['content']}")
            print()
    else:
        print("  ✓ No tools directory imports found")
    
    print()
    print("=" * 70)
    
    total_violations = len(godot_violations) + len(tools_violations)
    
    if total_violations == 0:
        print("✓ ALL BOUNDARY CHECKS PASSED")
        print("=" * 70)
        sys.exit(0)
    else:
        print(f"✗ FOUND {total_violations} VIOLATION(S)")
        print("=" * 70)
        print()
        print("Fix these before proceeding:")
        print("  1. Remove the import if unused")
        print("  2. Move file to correct directory")
        print("  3. Refactor to eliminate dependency")
        sys.exit(1)
