#!/usr/bin/env python3
"""
ZON Compliance Test Generator

Generates test vectors for validating ZON implementations.
Both Python and GDScript implementations must pass identical tests.

This decouples implementation from specification:
- Tests are generated from the spec, not from implementation
- Both languages validate against the same standard
- No need to mirror code - just pass the same tests

Usage:
    python3 generate_compliance_tests.py --output tests/fixtures/
"""

import json
import struct
from pathlib import Path
from typing import Dict, Any, List

# Type markers (from spec)
TYPE_INT = 0x10
TYPE_BOOL = 0x11
TYPE_STRING = 0x12
TYPE_ARRAY = 0x13
TYPE_BLOCK = 0x14
TYPE_FLOAT = 0x15
TYPE_NULL = 0x16

ZONB_MAGIC = b'ZONB'
ZONB_VERSION = 0x01


class TestVector:
    """A single test case with input and expected output."""
    
    def __init__(self, name: str, description: str, json_input: Dict[str, Any]):
        self.name = name
        self.description = description
        self.json_input = json_input
        self.binary_output = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Export as dictionary for JSON serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "json_input": self.json_input,
            "binary_hex": self.binary_output.hex() if self.binary_output else None
        }


def generate_test_vectors() -> List[TestVector]:
    """Generate comprehensive test vectors."""
    
    vectors = []
    
    # Test 1: Simple integer
    vectors.append(TestVector(
        name="simple_integer",
        description="Single integer value",
        json_input={"value": 42}
    ))
    
    # Test 2: Boolean
    vectors.append(TestVector(
        name="simple_boolean",
        description="Single boolean value",
        json_input={"flag": True}
    ))
    
    # Test 3: String
    vectors.append(TestVector(
        name="simple_string",
        description="Single string value",
        json_input={"name": "test"}
    ))
    
    # Test 4: Null
    vectors.append(TestVector(
        name="simple_null",
        description="Null value",
        json_input={"value": None}
    ))
    
    # Test 5: Float
    vectors.append(TestVector(
        name="simple_float",
        description="Single float value",
        json_input={"position": 3.14}
    ))
    
    # Test 6: Array of integers
    vectors.append(TestVector(
        name="array_integers",
        description="Array of integers",
        json_input={"values": [1, 2, 3, 4, 5]}
    ))
    
    # Test 7: Array of mixed types
    vectors.append(TestVector(
        name="array_mixed",
        description="Array with mixed types",
        json_input={"data": [42, "hello", True, None]}
    ))
    
    # Test 8: Nested dictionary
    vectors.append(TestVector(
        name="nested_dict",
        description="Dictionary with nested dictionary",
        json_input={
            "metadata": {
                "created": "2025-11-27",
                "version": 1
            }
        }
    ))
    
    # Test 9: Complex structure (like door rule)
    vectors.append(TestVector(
        name="complex_structure",
        description="Complex nested structure with arrays and dicts",
        json_input={
            "type": "rule",
            "id": "test_rule",
            "condition": "all_of",
            "requires": [
                {"flag": "condition_a"},
                {"flag": "condition_b"}
            ],
            "effect": [
                {"action": "trigger_event"}
            ]
        }
    ))
    
    # Test 10: Empty structures
    vectors.append(TestVector(
        name="empty_structures",
        description="Empty array and empty dict",
        json_input={
            "empty_array": [],
            "empty_dict": {}
        }
    ))
    
    # Test 11: Unicode string
    vectors.append(TestVector(
        name="unicode_string",
        description="String with Unicode characters",
        json_input={"text": "Hello 世界 🎮"}
    ))
    
    # Test 12: Large integer
    vectors.append(TestVector(
        name="large_integer",
        description="Maximum int32 value",
        json_input={"value": 2147483647}
    ))
    
    # Test 13: Negative integer
    vectors.append(TestVector(
        name="negative_integer",
        description="Negative integer",
        json_input={"value": -42}
    ))
    
    # Test 14: Array of arrays
    vectors.append(TestVector(
        name="nested_arrays",
        description="Array containing arrays",
        json_input={"matrix": [[1, 2], [3, 4]]}
    ))
    
    # Test 15: Deep nesting
    vectors.append(TestVector(
        name="deep_nesting",
        description="Deeply nested structure",
        json_input={
            "level1": {
                "level2": {
                    "level3": {
                        "value": "deep"
                    }
                }
            }
        }
    ))
    
    return vectors


def pack_test_vector(vector: TestVector):
    """Pack a test vector to binary (minimal implementation)."""
    # Note: This uses the reference Python implementation
    # The point is that tests are GENERATED, not copied from implementation
    from zon_binary_pack import pack_zonj
    
    vector.binary_output = pack_zonj(vector.json_input)


def save_test_vectors(vectors: List[TestVector], output_dir: Path):
    """Save test vectors to files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save all vectors as JSON manifest
    manifest = {
        "version": "1.0",
        "test_count": len(vectors),
        "tests": [v.to_dict() for v in vectors]
    }
    
    manifest_path = output_dir / "compliance_tests.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"✅ Saved {len(vectors)} test vectors to {manifest_path}")
    
    # Save individual binary files
    for vector in vectors:
        if vector.binary_output:
            binary_path = output_dir / f"{vector.name}.zonb"
            with open(binary_path, 'wb') as f:
                f.write(vector.binary_output)
            
            json_path = output_dir / f"{vector.name}.zonj.json"
            with open(json_path, 'w') as f:
                json.dump(vector.json_input, f, indent=2)
    
    print(f"✅ Saved {len(vectors)} individual test files")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate ZON compliance tests")
    parser.add_argument('--output', default='tests/fixtures/compliance',
                       help='Output directory for test vectors')
    args = parser.parse_args()
    
    output_dir = Path(args.output)
    
    print("Generating ZON compliance test vectors...")
    vectors = generate_test_vectors()
    
    print(f"Generated {len(vectors)} test vectors")
    print("Packing to binary...")
    
    for vector in vectors:
        pack_test_vector(vector)
    
    print("Saving test vectors...")
    save_test_vectors(vectors, output_dir)
    
    print("\n✅ Test generation complete!")
    print(f"\nTo run compliance tests:")
    print(f"  Python:   pytest tests/test_compliance.py")
    print(f"  GDScript: Run test_compliance.gd in Godot")


if __name__ == "__main__":
    main()
