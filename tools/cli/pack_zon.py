#!/usr/bin/env python3
"""
Pack ZON Files

Convert .zonj.json (canonical JSON) to .zonb (binary packed)

Usage:
    python3 pack_zon.py input.zonj.json output.zonb
"""

import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.zon import pack_zonj


def main():
    if len(sys.argv) != 3:
        print("Usage: pack_zon.py <input.zonj.json> <output.zonb>")
        sys.exit(1)
    
    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    
    if not input_path.exists():
        print(f"Error: Input file '{input_path}' not found")
        sys.exit(1)
    
    # Load JSON
    print(f"Loading {input_path}...")
    with open(input_path, 'r') as f:
        data = json.load(f)
    
    # Pack to binary
    print(f"Packing to binary format...")
    binary_data = pack_zonj(data)
    
    # Write output
    print(f"Writing {output_path}...")
    with open(output_path, 'wb') as f:
        f.write(binary_data)
    
    print(f"✅ Packed {len(binary_data)} bytes")
    print(f"   {input_path} → {output_path}")


if __name__ == "__main__":
    main()
