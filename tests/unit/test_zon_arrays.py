#!/usr/bin/env python3
"""
Test script for ZON Binary root array handling
"""

import json
import sys
from pathlib import Path
from zon_binary_pack import pack_zonj, unpack_zonb, pack_file, unpack_file


def test_root_array():
    """Test that root arrays are properly preserved through pack/unpack cycle"""
    print("=" * 60)
    print("Testing Root Array Preservation")
    print("=" * 60)
    
    # Test data - array at root level (like your Zork data)
    test_data = [
        {
            "type": "object",
            "id": "RUBBLE",
            "description": "rubble",
            "flags": ["NDESCBIT"]
        },
        {
            "type": "object",
            "id": "DEBRIS",
            "description": "dust and debris",
            "flags": ["NDESCBIT"]
        },
        {
            "type": "object",
            "id": "CHASM",
            "description": "chasm",
            "flags": ["NDESCBIT"]
        }
    ]
    
    print("\n1. Original data (root array):")
    print(json.dumps(test_data, indent=2)[:200] + "...")
    
    # Pack with root array preservation
    print("\n2. Packing with root array preservation...")
    binary_preserved = pack_zonj(test_data, preserve_root_array=True)
    print(f"   Binary size (preserved): {len(binary_preserved)} bytes")
    print(f"   Header: {binary_preserved[:10].hex()}")
    
    # Unpack
    print("\n3. Unpacking...")
    unpacked = unpack_zonb(binary_preserved)
    
    # Verify it's still an array
    print(f"   Result type: {type(unpacked).__name__}")
    print(f"   Is array preserved? {isinstance(unpacked, list)}")
    print(f"   Data matches? {unpacked == test_data}")
    
    # Test without preservation (old behavior)
    print("\n4. Testing OLD behavior (wrapping in field_0)...")
    binary_wrapped = pack_zonj({"field_0": test_data}, preserve_root_array=False)
    unpacked_wrapped = unpack_zonb(binary_wrapped, auto_unwrap=False)
    print(f"   Result keys: {list(unpacked_wrapped.keys()) if isinstance(unpacked_wrapped, dict) else 'N/A'}")
    
    # Test auto-unwrap
    print("\n5. Testing auto-unwrap on wrapped data...")
    unwrapped = unpack_zonb(binary_wrapped, auto_unwrap=True)
    print(f"   Auto-unwrapped type: {type(unwrapped).__name__}")
    print(f"   Data matches original? {unwrapped == test_data}")
    
    return unpacked == test_data


def test_roundtrip_file(input_json: str):
    """Test roundtrip conversion of an actual file"""
    print("\n" + "=" * 60)
    print(f"Testing File Roundtrip: {input_json}")
    print("=" * 60)
    
    input_path = Path(input_json)
    if not input_path.exists():
        print(f"File not found: {input_json}")
        return False
    
    # Read original
    with open(input_path, 'r') as f:
        original = json.load(f)
    
    print(f"\n1. Original data type: {type(original).__name__}")
    if isinstance(original, list):
        print(f"   Array length: {len(original)}")
    elif isinstance(original, dict):
        print(f"   Keys: {list(original.keys())[:5]}")
    
    # Pack to binary
    temp_zonb = input_path.with_suffix('.test.zonb')
    print(f"\n2. Packing to {temp_zonb}...")
    size = pack_file(str(input_path), str(temp_zonb), preserve_root_array=True)
    print(f"   Binary size: {size} bytes")
    
    # Unpack back to JSON
    temp_json = input_path.with_suffix('.test.json')
    print(f"\n3. Unpacking to {temp_json}...")
    result = unpack_file(str(temp_zonb), str(temp_json), auto_unwrap=True)
    
    # Compare
    match = result == original
    print(f"\n4. Roundtrip successful? {match}")
    
    if not match:
        print("\n   Differences found:")
        if type(result) != type(original):
            print(f"   - Type mismatch: {type(original).__name__} -> {type(result).__name__}")
        elif isinstance(result, list) and isinstance(original, list):
            print(f"   - Length: {len(original)} -> {len(result)}")
        elif isinstance(result, dict) and isinstance(original, dict):
            missing = set(original.keys()) - set(result.keys())
            extra = set(result.keys()) - set(original.keys())
            if missing:
                print(f"   - Missing keys: {missing}")
            if extra:
                print(f"   - Extra keys: {extra}")
    
    # Cleanup
    temp_zonb.unlink(missing_ok=True)
    temp_json.unlink(missing_ok=True)
    
    return match


def main():
    print("ZON Binary Root Array Test Suite")
    print("=" * 60)
    
    # Run basic test
    if test_root_array():
        print("\n✅ Basic root array test PASSED")
    else:
        print("\n❌ Basic root array test FAILED")
        sys.exit(1)
    
    # Test with file if provided
    if len(sys.argv) > 1:
        json_file = sys.argv[1]
        if test_roundtrip_file(json_file):
            print(f"\n✅ File roundtrip test PASSED: {json_file}")
        else:
            print(f"\n❌ File roundtrip test FAILED: {json_file}")
            sys.exit(1)
    
    print("\n" + "=" * 60)
    print("All tests completed successfully! 🎉")
    print("=" * 60)


if __name__ == "__main__":
    main()
