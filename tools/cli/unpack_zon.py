#!/usr/bin/env python3
"""
Unpack ZON Files

Convert .zonb (binary packed) to .zonj.json (canonical JSON)

Usage:
    python3 unpack_zon.py input.zonb output.zonj.json
"""

import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.zon import unpack_zonb


def main():
    if len(sys.argv) != 3:
        print("Usage: unpack_zon.py <input.zonb> <output.zonj.json>")
        sys.exit(1)
    
    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    
    if not input_path.exists():
        print(f"Error: Input file '{input_path}' not found")
        sys.exit(1)
    
    # Load binary
    print(f"Loading {input_path}...")
    with open(input_path, 'rb') as f:
        binary_data = f.read()
    
    # Unpack from binary
    print(f"Unpacking from binary format...")
    data = unpack_zonb(binary_data)
    
    # Write JSON
    print(f"Writing {output_path}...")
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"✅ Unpacked to JSON")
    print(f"   {input_path} → {output_path}")


if __name__ == "__main__":
    main()
